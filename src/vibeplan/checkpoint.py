"""Git-based checkpoint manager for safe rollbacks."""
import subprocess
from pathlib import Path
from rich.console import Console

console = Console()


def ensure_git_repo(path: Path) -> bool:
    """Return True if path is inside a git repository."""
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--git-dir"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def create_snapshot(path: Path, step_id: str, step_name: str) -> str:
    """Stage all changes and create a named git commit checkpoint."""
    commit_msg = f"vibeplan-step-{step_id}-{step_name}"
    subprocess.run(["git", "-C", str(path), "add", "-A"], capture_output=True)
    result = subprocess.run(
        ["git", "-C", str(path), "commit", "-m", commit_msg, "--allow-empty"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        console.print("[dim]Checkpoint: " + commit_msg + "[/]")
    else:
        console.print("[dim]Checkpoint skipped (no changes): " + commit_msg + "[/]")
    return commit_msg


def rollback(path: Path, commit_msg: str) -> bool:
    """Roll back to the state before the given checkpoint commit."""
    result = subprocess.run(
        ["git", "-C", str(path), "log", "--oneline", "--grep", commit_msg, "-n", "1"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        console.print("[red]Commit not found: " + commit_msg + "[/]")
        return False

    commit_hash = result.stdout.strip().split()[0]
    parent = subprocess.run(
        ["git", "-C", str(path), "rev-parse", commit_hash + "^"],
        capture_output=True,
        text=True,
    )
    if parent.returncode != 0:
        console.print("[red]Cannot find parent commit.[/]")
        return False

    reset = subprocess.run(
        ["git", "-C", str(path), "reset", "--hard", parent.stdout.strip()],
        capture_output=True,
        text=True,
    )
    if reset.returncode == 0:
        console.print("[green]Rolled back to before " + commit_msg + "[/]")
        return True
    return False
