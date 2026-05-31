"""Interactive questionnaire to clarify intent before planning."""
from rich.prompt import Prompt, Confirm
from rich.console import Console
from rich.panel import Panel

console = Console()

DEFAULT_QUESTIONS = [
    {
        "id": "scope",
        "text": "What is the scope? (e.g. backend only, frontend only, fullstack)",
        "default": "fullstack",
    },
    {
        "id": "stack",
        "text": "What stack is used? (e.g. Python/FastAPI, Next.js, etc.)",
        "default": "",
    },
    {
        "id": "constraints",
        "text": "Any hard constraints? (e.g. no new deps, must be compatible with X)",
        "default": "none",
    },
    {
        "id": "quality",
        "text": "Expected quality level? (MVP / production-ready / refactor)",
        "default": "MVP",
    },
    {
        "id": "budget",
        "text": "Approximate token budget? (e.g. 10k, 50k, unlimited)",
        "default": "unlimited",
    },
]


def ask_questions(prompt: str) -> dict:
    """Ask clarifying questions and return answers dict."""
    console.print(Panel("[bold blue]Task:[/] " + prompt, title="vibeplan", border_style="blue"))
    console.print("\n[dim]Answer a few questions to sharpen the plan.[/]\n")

    answers = {"original_prompt": prompt}
    for q in DEFAULT_QUESTIONS:
        answer = Prompt.ask("[bold]" + q["text"] + "[/]", default=q["default"])
        answers[q["id"]] = answer

    console.print("\n[bold green]Summary:[/]")
    for k, v in answers.items():
        if k != "original_prompt":
            console.print("  - " + k + ": " + v)

    if not Confirm.ask("\nGenerate plan?", default=True):
        console.print("[red]Cancelled.[/]")
        return {}

    return answers
