"""Step runner — executes plan interactively with checkpoints."""
import json
from pathlib import Path
from typing import Dict, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from vibeplan.adapters import get_adapter
from vibeplan.budget import redistribute_budget
from vibeplan.checkpoint import create_snapshot, rollback
from vibeplan.config import get_budget_path, get_plan_path, load_config

console = Console()


def load_plan(project_dir: Path) -> Dict:
    budget_path = get_budget_path(project_dir)
    if budget_path.exists():
        return json.loads(budget_path.read_text(encoding="utf-8"))
    return {"steps": []}


def generate_step_prompt(prompt: str, answers: Dict, step: Dict) -> str:
    budget_str = f"{step.get('tokens'):,} tokens" if step.get("tokens") else "unlimited"
    context_lines = []
    for k, v in answers.items():
        if k != "original_prompt":
            context_lines.append(f"- **{k}:** {v}")

    return f"""## vibeplan: Step {step['id']} — {step['name']}

### Original Task
{prompt}

### Context
{chr(10).join(context_lines)}

### Step Description
{step.get('description', 'Implement this step.')}

### Token Budget
{budget_str}

### Instructions
Follow the plan for this step. Do not skip ahead or implement future steps.
After completing, ensure all changes are saved before reporting back."""


def get_next_pending_step(steps: List[Dict]) -> Optional[Dict]:
    for step in steps:
        if step.get("status") != "done":
            return step
    return None


def run_plan(plan_path: Path, project_dir: Path) -> None:
    data = load_plan(project_dir)
    steps = data.get("steps", [])

    if not steps:
        console.print("[red]No steps found in plan.[/]")
        return

    console.print(Panel("[bold green]Starting vibeplan execution[/]", border_style="green"))

    remaining = [s for s in steps if s.get("status") != "done"]
    if not remaining:
        console.print("[yellow]All steps are already done. Nothing to execute.[/]")
        return

    config = load_config(project_dir)
    agent_name = config.get("agent")
    agent_config = config.get("agent_config", {})

    for step in steps:
        if step.get("status") == "done":
            continue

        sid = step["id"]
        name = step["name"]
        budget = step.get("tokens")

        adapter_cls = None
        if agent_name:
            adapter_cls = get_adapter(agent_name)
            if adapter_cls and not adapter_cls.check_available():
                console.print("[yellow]Agent '" + agent_name + "' not found on PATH. Falling back to manual mode for step " + sid + ".[/]")
                adapter_cls = None

        console.print("\n[bold blue]Step " + sid + ": " + name + "[/]")
        if budget:
            console.print("[dim]Token budget: " + f"{budget:,}" + "[/]")

        prompt_text = data.get("original_prompt", "")
        answers = data.get("answers", {})
        step_prompt = generate_step_prompt(prompt_text, answers, step)

        if adapter_cls:
            adapter_name = adapter_cls.name
            console.print("[dim]Running via " + adapter_name + "...[/]")
            result = adapter_cls.run(prompt_text, answers, step, project_dir, agent_config)

            if result.success:
                console.print("[green]Agent completed step " + sid + " (" + name + ").[/]")
                if result.token_usage:
                    console.print("[dim]Tokens used: " + str(result.token_usage) + "[/]")
                    step["spent"] = (step.get("spent", 0) or 0) + result.token_usage
            else:
                console.print("[red]Agent failed: " + (result.error or "exit code " + str(result.exit_code)) + "[/]")
                action = Prompt.ask(
                    "What now?",
                    choices=["retry", "manual", "rollback", "skip", "quit"],
                    default="retry",
                )
                if action == "retry":
                    continue
                elif action == "manual":
                    console.print("\n[bold]Prompt for your AI agent:[/]")
                    console.print(Panel(step_prompt, border_style="cyan"))
                    console.print("[dim]Run your AI agent for this step, then press Enter.[/]")
                    Prompt.ask("[bold]Press Enter when agent finishes this step[/]")
                elif action == "rollback":
                    rollback(project_dir, "vibeplan-step-" + sid + "-" + name)
                    step["status"] = "pending"
                    console.print("[yellow]Step reset. Run 'vibeplan run' to redo.[/]")
                    break
                elif action == "skip":
                    step["status"] = "done"
                    _save_progress(project_dir, data)
                    continue
                else:
                    _save_progress(project_dir, data)
                    return
        else:
            console.print("\n[bold]Prompt for your AI agent:[/]")
            console.print(Panel(step_prompt, border_style="cyan"))
            console.print("[dim]Run your AI agent for this step, then press Enter.[/]")
            Prompt.ask("[bold]Press Enter when agent finishes this step[/]")

        create_snapshot(project_dir, sid, name)

        action = Prompt.ask(
            "What next?",
            choices=["continue", "rollback", "edit", "quit"],
            default="continue",
        )

        if action == "rollback":
            rollback(project_dir, "vibeplan-step-" + sid + "-" + name)
            step["status"] = "pending"
            console.print("[yellow]Step reset to pending. Run 'vibeplan run' to redo it.[/]")
            break
        elif action == "edit":
            console.print("[yellow]Edit plan.md manually, then run 'vibeplan run' again.[/]")
            break
        elif action == "quit":
            console.print("[yellow]Paused. Resume with 'vibeplan run'[/]")
            break
        else:
            step["status"] = "done"
            data = redistribute_budget(data)

        _save_progress(project_dir, data)

    _save_progress(project_dir, data)
    remaining = [s for s in steps if s.get("status") != "done"]
    if not remaining:
        console.print("\n[bold green]All steps complete![/]")


def resume_plan(project_dir: Path) -> None:
    plan_path = get_plan_path(project_dir)
    if not plan_path.exists():
        console.print("[red]No plan found. Run 'vibeplan init' first.[/]")
        return
    run_plan(plan_path, project_dir)


def _save_progress(project_dir: Path, data: Dict) -> None:
    budget_path = get_budget_path(project_dir)
    budget_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
