"""Step runner — executes plan interactively with checkpoints."""
import json
from pathlib import Path
from typing import Dict
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from vibeplan.checkpoint import create_snapshot, rollback

console = Console()


def load_plan(plan_path: Path) -> Dict:
    """Load budget.json from the same directory as plan.md."""
    budget_path = plan_path.parent / ".vibeplan" / "budget.json"
    if budget_path.exists():
        return json.loads(budget_path.read_text(encoding="utf-8"))
    return {"steps": []}


def run_plan(plan_path: Path, project_dir: Path) -> None:
    """Execute all pending steps from the plan interactively."""
    data = load_plan(plan_path)
    steps = data.get("steps", [])

    if not steps:
        console.print("[red]No steps found in plan.[/]")
        return

    console.print(Panel("[bold green]Starting vibeplan execution[/]", border_style="green"))

    for step in steps:
        sid = step["id"]
        name = step["name"]
        budget = step.get("tokens")
        status = step.get("status", "pending")

        if status == "done":
            console.print("[dim]Step " + sid + " (" + name + ") already done — skipping.[/]")
            continue

        console.print("\n[bold blue]Step " + sid + ": " + name + "[/]")
        if budget:
            console.print("[dim]Token budget: " + f"{budget:,}" + "[/]")
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
        elif action == "edit":
            console.print("[yellow]Edit plan.md manually, then run 'vibeplan run' again.[/]")
            break
        elif action == "quit":
            console.print("[yellow]Paused. Resume with 'vibeplan run'[/]")
            break
        else:
            step["status"] = "done"

    budget_path = plan_path.parent / ".vibeplan" / "budget.json"
    budget_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    console.print("\n[bold green]All steps processed![/]")
