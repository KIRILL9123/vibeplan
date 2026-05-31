"""vibeplan CLI — structured pre-planner for vibe coding."""
import json
from pathlib import Path
import sys
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from vibeplan.questions import ask_questions
from vibeplan.planner import generate_plan
from vibeplan.runner import run_plan, resume_plan, generate_step_prompt, load_plan
from vibeplan.checkpoint import ensure_git_repo, list_checkpoints, rollback_to_step
from vibeplan.adapters import get_adapter, list_adapters
from vibeplan.config import get_config_path, get_budget_path, load_config, save_config
from vibeplan.llm import PROVIDER_DEFAULTS, resolve_llm_config
from vibeplan.mcp_server import run_mcp_server
from vibeplan.web_ui import run_web_server
from vibeplan.team import export_share, import_shared
from vibeplan.github import format_github_issue, publish_issue
from vibeplan.benchmark import run_baseline, collect_actual, save_baseline, load_baseline, format_report

app = typer.Typer(help="vibeplan — Plan first. Ship faster. Burn fewer tokens.")
console = Console()


@app.command()
def init(
    prompt: str = typer.Argument(..., help="Describe what you want to build or fix"),
    output_dir: Path = typer.Option(Path("."), "--output-dir", "-o", help="Project directory"),
    agent: str = typer.Option(None, "--agent", "-a", help="Agent adapter to use (e.g. opencode)"),
    llm: str = typer.Option(None, "--llm", help="LLM provider for AI-powered planning (openrouter, ollama, openai)"),
) -> None:
    """Create a new vibe plan from a task description."""
    console.print(Panel("[bold blue]vibeplan init[/]", border_style="blue"))

    if not ensure_git_repo(output_dir):
        console.print("[yellow]No git repository found. vibeplan requires git for checkpoints.[/]")
        console.print("[dim]Run: git init && git add . && git commit -m 'initial'[/]")
        raise typer.Exit(1)

    answers = ask_questions(prompt)
    if not answers:
        raise typer.Exit(0)

    config = load_config(output_dir)
    if llm:
        if llm in PROVIDER_DEFAULTS:
            config["llm"] = config.get("llm", {})
            config["llm"]["provider"] = llm
        else:
            console.print("[yellow]Unknown LLM provider '" + llm + "'. Available: " + ", ".join(PROVIDER_DEFAULTS.keys()) + "[/]")

    if agent:
        if get_adapter(agent):
            config["agent"] = agent
        else:
            console.print("[yellow]Unknown agent '" + agent + "'. Available: " + ", ".join(list_adapters()) + "[/]")

    llm_config = resolve_llm_config(config)
    save_config(output_dir, config)
    plan_path = generate_plan(answers, output_dir, llm_config)
    console.print("\n[bold green]Plan created:[/] " + str(plan_path))
    if llm_config.provider:
        console.print("[dim]Plan generated with " + llm_config.provider + "/" + llm_config.model + "[/]")
    console.print("[dim]Run 'vibeplan run' to execute step-by-step.[/]")


@app.command()
def run(
    project_dir: Path = typer.Option(Path("."), "--project-dir", "-d", help="Project directory"),
) -> None:
    """Execute the plan step-by-step with interactive checkpoints."""
    plan_path = project_dir / "plan.md"
    if not plan_path.exists():
        console.print("[red]Plan not found: plan.md[/]")
        console.print("[dim]Run 'vibeplan init <task>' first.[/]")
        raise typer.Exit(1)
    run_plan(plan_path, project_dir)


@app.command()
def resume(
    project_dir: Path = typer.Option(Path("."), "--project-dir", "-d", help="Project directory"),
) -> None:
    """Continue a paused session from the last incomplete step."""
    resume_plan(project_dir)


@app.command()
def status(
    project_dir: Path = typer.Option(Path("."), "--project-dir", "-d"),
) -> None:
    """Show current plan progress and token budget status."""
    budget_path = get_budget_path(project_dir)
    if not budget_path.exists():
        console.print("[red]No active vibeplan found. Run 'vibeplan init' first.[/]")
        raise typer.Exit(1)

    data = json.loads(budget_path.read_text(encoding="utf-8"))
    console.print(Panel("[bold]vibeplan status[/]", border_style="blue"))
    total = data.get("total_tokens")
    console.print("Task: " + data.get("original_prompt", "—"))
    console.print("Total budget: " + (str(total) if total else "unlimited"))
    for step in data.get("steps", []):
        icon = "[green]✅[/]" if step["status"] == "done" else "[yellow]⏳[/]"
        spent = step.get("spent", 0)
        budget = step.get("tokens")
        budget_str = str(budget) if budget else "unlimited"
        console.print("  " + icon + " Step " + step["id"] + " (" + step["name"] + ") — " + str(spent) + "/" + budget_str + " tokens")


@app.command()
def doctor(
    project_dir: Path = typer.Option(Path("."), "--project-dir", "-d", help="Project directory to check"),
) -> None:
    """Check prerequisites for vibeplan."""
    console.print(Panel("[bold]vibeplan doctor[/]", border_style="blue"))

    checks = []

    git_ok = ensure_git_repo(project_dir)
    checks.append(("Git repository", git_ok, "Required for checkpoints and rollback"))

    py_version = sys.version_info
    py_ok = py_version.major == 3 and py_version.minor >= 10
    checks.append(("Python 3.10+", py_ok, "Current: " + sys.version.split()[0]))

    config_path = get_config_path(project_dir)
    config_ok = config_path.exists()
    checks.append(("Config file", config_ok, str(config_path) if config_ok else "Not found (auto-created on init)"))

    budget_path = get_budget_path(project_dir)
    plan_ok = budget_path.exists()
    checks.append(("Active plan", plan_ok, "Run 'vibeplan init' to create one" if not plan_ok else str(budget_path)))

    config = load_config(project_dir)
    agent_name = config.get("agent")
    if agent_name:
        adapter_cls = get_adapter(agent_name)
        if adapter_cls:
            agent_ok = adapter_cls.check_available()
            checks.append(("Agent: " + agent_name, agent_ok, "Available on PATH" if agent_ok else "Not installed"))
        else:
            checks.append(("Agent: " + agent_name, False, "Unknown adapter. Available: " + ", ".join(list_adapters())))
    else:
        checks.append(("Agent", True, "Manual mode (no agent configured)"))

    llm_config = resolve_llm_config(config)
    if llm_config.provider:
        llm_ok = bool(llm_config.api_key) or llm_config.provider == "ollama"
        checks.append(("LLM: " + llm_config.provider + "/" + llm_config.model, llm_ok, "API key: " + ("set" if llm_config.api_key else "missing") if llm_config.provider != "ollama" else "No key needed"))
    else:
        checks.append(("LLM planner", True, "Not configured (template-based)"))

    table = Table(show_header=True)
    table.add_column("Check", style="bold")
    table.add_column("Status")
    table.add_column("Details")

    for name, ok, detail in checks:
        icon = "[green]✅[/]" if ok else "[red]❌[/]"
        status = "[green]OK[/]" if ok else "[red]FAIL[/]"
        table.add_row(name, status + " " + icon, detail)

    console.print(table)

    if all(ok for _, ok, _ in checks):
        console.print("\n[bold green]All checks passed! Ready to vibe. ✨[/]")
    else:
        console.print("\n[yellow]Some checks failed. Fix the issues above.[/]")
        raise typer.Exit(1)


@app.command()
def rollback(
    step: str = typer.Argument(..., help="Step number (e.g. 2) or step name (e.g. implement) to rollback to"),
    project_dir: Path = typer.Option(Path("."), "--project-dir", "-d", help="Project directory"),
) -> None:
    """Rollback to the state before a specific step checkpoint."""
    console.print(Panel("[bold]vibeplan rollback[/]", border_style="blue"))
    if not rollback_to_step(project_dir, step):
        raise typer.Exit(1)


@app.command()
def export(
    project_dir: Path = typer.Option(Path("."), "--project-dir", "-d", help="Project directory"),
    output: Path = typer.Option(None, "--output", "-o", help="Output file path"),
) -> None:
    """Export the plan as a portable handoff file."""
    console.print(Panel("[bold]vibeplan export[/]", border_style="blue"))

    plan_path = project_dir / "plan.md"
    if not plan_path.exists():
        console.print("[red]No plan found. Run 'vibeplan init' first.[/]")
        raise typer.Exit(1)

    data = load_plan(project_dir)
    plan_content = plan_path.read_text(encoding="utf-8")
    steps = data.get("steps", [])
    checkpoints = list_checkpoints(project_dir)

    export_lines = []
    export_lines.append("# vibeplan — Portable Handoff")
    export_lines.append("")
    export_lines.append("## Original Plan")
    export_lines.append("")
    export_lines.append(plan_content)
    export_lines.append("")
    export_lines.append("## Current Progress")
    export_lines.append("")
    export_lines.append("| Step | Name | Status | Tokens |")
    export_lines.append("|------|------|--------|--------|")
    for s in steps:
        status = "✅ Done" if s.get("status") == "done" else "⏳ Pending"
        t = str(s.get("tokens", "unlimited"))
        export_lines.append(f"| {s['id']} | {s['name']} | {status} | {t} |")

    export_lines.append("")
    export_lines.append("## Checkpoints")
    export_lines.append("")
    if checkpoints:
        export_lines.append("| Hash | Step |")
        export_lines.append("|------|------|")
        for cp in checkpoints:
            export_lines.append(f"| `{cp['hash']}` | Step {cp['step_id']} — {cp['step_name']} |")
    else:
        export_lines.append("No checkpoints recorded yet.")

    export_lines.append("")
    export_lines.append("## Prompts for Pending Steps")
    export_lines.append("")
    prompt = data.get("original_prompt", "")
    answers = data.get("answers", {})

    for s in steps:
        if s.get("status") != "done":
            export_lines.append(generate_step_prompt(prompt, answers, s))
            export_lines.append("")

    export_content = "\n".join(export_lines)

    if output is None:
        output = project_dir / "vibeplan-handoff.md"

    output.write_text(export_content, encoding="utf-8")
    console.print("[green]Handoff exported:[/] " + str(output))
    console.print("[dim]Share this file with anyone to pick up where you left off.[/]")


@app.command()
def prompt(
    step: str = typer.Argument(None, help="Step number (e.g. 2) or step name (e.g. implement)"),
    project_dir: Path = typer.Option(Path("."), "--project-dir", "-d", help="Project directory"),
) -> None:
    """Show the ready-to-paste prompt for a specific step."""
    data = load_plan(project_dir)
    steps = data.get("steps", [])
    if not steps:
        console.print("[red]No active plan found. Run 'vibeplan init' first.[/]")
        raise typer.Exit(1)

    target_step = None
    if step is None:
        target_step = None
        for s in steps:
            if s.get("status") != "done":
                target_step = s
                break
        if target_step is None:
            console.print("[yellow]All steps are done! Nothing to prompt for.[/]")
            return
    else:
        for s in steps:
            if s["id"] == step or s["name"] == step:
                target_step = s
                break
        if target_step is None:
            console.print("[red]Step not found: " + step + "[/]")
            console.print("[dim]Available steps: " + ", ".join(s["id"] + " (" + s["name"] + ")" for s in steps) + "[/]")
            raise typer.Exit(1)

    prompt_text = data.get("original_prompt", "")
    answers = data.get("answers", {})
    console.print(generate_step_prompt(prompt_text, answers, target_step))


@app.command()
def mcp(
    project_dir: Path = typer.Option(Path("."), "--project-dir", "-d", help="Project directory"),
) -> None:
    """Start MCP server for AI agent integration (stdio JSON-RPC)."""
    console.print("[dim]vibeplan MCP server starting...[/]")
    run_mcp_server()


@app.command()
def web(
    project_dir: Path = typer.Option(Path("."), "--project-dir", "-d", help="Project directory"),
    port: int = typer.Option(8080, "--port", "-p", help="HTTP port"),
    no_browser: bool = typer.Option(False, "--no-browser", help="Don't open browser automatically"),
) -> None:
    """Start the Web UI for plan visualization."""
    run_web_server(project_dir, port, open_browser=not no_browser)


@app.command(name="import")
def import_plan(
    share_file: Path = typer.Argument(..., help="Path to vibeplan-share.json file"),
    project_dir: Path = typer.Option(Path("."), "--project-dir", "-d", help="Project directory"),
) -> None:
    """Import a shared plan into the current project."""
    console.print(Panel("[bold]vibeplan import[/]", border_style="blue"))
    try:
        import_shared(share_file, project_dir)
        console.print("[green]Plan imported successfully![/]")
        console.print(f"[dim]  plan.md → {project_dir / 'plan.md'}[/]")
        console.print(f"[dim]  budget.json → {get_budget_path(project_dir)}[/]")
        console.print(f"[dim]  config.json → {get_config_path(project_dir)}[/]")
        console.print("[dim]Run 'vibeplan run' to start executing.[/]")
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/]")
        raise typer.Exit(1)


@app.command()
def share(
    project_dir: Path = typer.Option(Path("."), "--project-dir", "-d", help="Project directory"),
) -> None:
    """Export the plan as a portable share file for team collaboration."""
    console.print(Panel("[bold]vibeplan share[/]", border_style="blue"))
    try:
        share_path = export_share(project_dir)
        console.print(f"[green]Share file created:[/] {share_path}")
        console.print("[dim]Share this file with your team. They can import it with:[/]")
        console.print(f"[dim]  vibeplan import {share_path}[/]")
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/]")
        raise typer.Exit(1)


@app.command()
def issue(
    title: str = typer.Option(None, "--title", "-t", help="Issue title (defaults to first 72 chars of prompt)"),
    publish: bool = typer.Option(False, "--publish", "-p", help="Create the issue via gh CLI"),
    project_dir: Path = typer.Option(Path("."), "--project-dir", "-d", help="Project directory"),
) -> None:
    """Generate a GitHub Issue from the current plan."""
    console.print(Panel("[bold]vibeplan issue[/]", border_style="blue"))
    budget_path = get_budget_path(project_dir)
    if not budget_path.exists():
        console.print("[red]No active plan found. Run 'vibeplan init' first.[/]")
        raise typer.Exit(1)

    if publish:
        url = publish_issue(project_dir, title)
        if url:
            console.print(f"[green]Issue created:[/] {url}")
        else:
            raise typer.Exit(1)
    else:
        body = format_github_issue(project_dir)
        console.print(body)
        console.print("\n[dim]Preview above. Use --publish to create the issue on GitHub.[/]")


@app.command()
def benchmark(
    task: str = typer.Argument(None, help="Task description to benchmark"),
    project_dir: Path = typer.Option(Path("."), "--project-dir", "-d", help="Project directory"),
    agent: str = typer.Option(None, "--agent", "-a", help="Agent adapter for baseline run"),
) -> None:
    """Benchmark token savings: compare with vs without vibeplan.

    If TASK is provided: runs baseline (raw prompt through agent), creates plan, saves result.
    If TASK is omitted: shows report from saved baseline vs actual plan execution.
    """
    console.print(Panel("[bold]vibeplan benchmark[/]", border_style="blue"))

    if task:
        if not agent:
            config = load_config(project_dir)
            agent = config.get("agent")
        if not agent:
            console.print("[red]No agent configured. Set one with --agent or in .vibeplan/config.json[/]")
            console.print("[dim]Available: " + ", ".join(list_adapters()) + "[/]")
            raise typer.Exit(1)

        config = load_config(project_dir)
        config["agent"] = agent
        save_config(project_dir, config)

        console.print("[yellow]Running baseline (without vibeplan)...[/]")
        baseline = run_baseline(task, project_dir)
        if baseline:
            save_baseline(project_dir, baseline)
            console.print(f"[green]Baseline done: {baseline.tokens:,} tokens (single pass, no structure)[/]")
        else:
            console.print("[red]Baseline run failed. Make sure '" + agent + "' is installed and accessible.[/]")
            console.print("[dim]To configure: vibeplan init --agent " + agent + "[/]")
            raise typer.Exit(1)

        ensure_git = ensure_git_repo(project_dir)
        if not ensure_git:
            console.print("[yellow]No git repo. Run 'git init' for checkpoint support.[/]")

        from vibeplan.questions import ask_questions
        answers = ask_questions(task)
        if not answers:
            raise typer.Exit(0)

        from vibeplan.llm import resolve_llm_config
        llm_config = resolve_llm_config(config)
        from vibeplan.planner import generate_plan
        plan_path = generate_plan(answers, project_dir, llm_config)
        console.print(f"\n[bold green]Plan created:[/] {plan_path}")

        if llm_config.provider:
            console.print("[dim]Plan generated with " + llm_config.provider + "/" + llm_config.model + "[/]")

    actual = collect_actual(project_dir)
    baseline = load_baseline(project_dir) if not task else baseline

    if not baseline and not actual:
        console.print("[yellow]No benchmark data yet.[/]")
        console.print("[dim]Run 'vibeplan benchmark <task> --agent <name>' to start.[/]")
        return

    task_name = task or ""
    if not task_name and actual:
        data = load_plan(project_dir)
        task_name = data.get("original_prompt", "")
    if not task_name and baseline:
        task_name = "benchmark"

    report = format_report(task_name, baseline, actual)
    console.print(report)

    if actual and actual.steps > 0:
        console.print(f"\n[dim]Steps executed: {actual.steps} (run 'vibeplan run' to complete any remaining)[/]")
    if baseline and not actual:
        console.print("\n[dim]After running 'vibeplan run', run 'vibeplan benchmark' again to see the comparison.[/]")


if __name__ == "__main__":
    app()
