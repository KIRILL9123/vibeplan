"""vibeplan CLI — structured pre-planner for vibe coding."""
from pathlib import Path
import typer
from rich.console import Console
from rich.panel import Panel

from vibeplan.questions import ask_questions
from vibeplan.planner import generate_plan
from vibeplan.runner import run_plan
from vibeplan.checkpoint import ensure_git_repo

app = typer.Typer(help="vibeplan — Plan first. Ship faster. Burn fewer tokens.")
console = Console()


@app.command()
def init(
    prompt: str = typer.Argument(..., help="Describe what you want to build or fix"),
    output_dir: Path = typer.Option(Path("."), "--output-dir", "-o", help="Project directory"),
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

    plan_path = generate_plan(answers, output_dir)
    console.print("\n[bold green]Plan created:[/] " + str(plan_path))
    console.print("[dim]Run 'vibeplan run' to execute step-by-step.[/]")


@app.command()
def run(
    plan: Path = typer.Option(Path("plan.md"), "--plan", "-p", help="Path to plan.md"),
    project_dir: Path = typer.Option(Path("."), "--project-dir", "-d", help="Project directory"),
) -> None:
    """Execute the plan step-by-step with interactive checkpoints."""
    if not plan.exists():
        console.print("[red]Plan not found: " + str(plan) + "[/]")
        console.print("[dim]Run 'vibeplan init <task>' first.[/]")
        raise typer.Exit(1)
    run_plan(plan, project_dir)


@app.command()
def status(
    project_dir: Path = typer.Option(Path("."), "--project-dir", "-d"),
) -> None:
    """Show current plan progress and token budget status."""
    import json
    budget_path = project_dir / ".vibeplan" / "budget.json"
    if not budget_path.exists():
        console.print("[red]No active vibeplan found. Run 'vibeplan init' first.[/]")
        raise typer.Exit(1)

    data = json.loads(budget_path.read_text(encoding="utf-8"))
    console.print(Panel("[bold]vibeplan status[/]", border_style="blue"))
    total = data.get("total_tokens")
    console.print("Total budget: " + (str(total) if total else "unlimited"))
    for step in data.get("steps", []):
        icon = "[green]✅[/]" if step["status"] == "done" else "[yellow]⏳[/]"
        spent = step.get("spent", 0)
        budget = step.get("tokens")
        budget_str = str(budget) if budget else "unlimited"
        console.print("  " + icon + " Step " + step["id"] + " (" + step["name"] + ") — " + str(spent) + "/" + budget_str + " tokens")


if __name__ == "__main__":
    app()
