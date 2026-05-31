"""Git-based checkpoint manager for safe rollbacks."""
import subprocess
from pathlib import Path
from typing import List
from rich.console import Console

console = Console()


def ensure_git_repo(path: Path) -> bool:
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--git-dir"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def create_snapshot(path: Path, step_id: str, step_name: str) -> str:
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


def rollback_to_commit(path: Path, commit_msg: str) -> bool:
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


def list_checkpoints(path: Path) -> List[dict]:
    result = subprocess.run(
        ["git", "-C", str(path), "log", "--oneline", "--grep", "vibeplan-step-"],
        capture_output=True,
        text=True,
    )
    checkpoints = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.strip().split(" ", 1)
        if len(parts) == 2:
            commit_hash = parts[0]
            msg = parts[1]
            step_info = msg.replace("vibeplan-step-", "")
            sid, sname = step_info.split("-", 1) if "-" in step_info else (step_info, "")
            checkpoints.append({
                "hash": commit_hash,
                "step_id": sid,
                "step_name": sname,
                "message": msg,
            })
    return checkpoints


def rollback_to_step(path: Path, step_id_or_name: str) -> bool:
    checkpoints = list_checkpoints(path)
    if not checkpoints:
        console.print("[red]No vibeplan checkpoints found.[/]")
        return False

    target = None
    for cp in checkpoints:
        if cp["step_id"] == step_id_or_name or cp["step_name"] == step_id_or_name:
            target = cp
            break

    if not target:
        console.print("[red]No checkpoint found for step: " + step_id_or_name + "[/]")
        console.print("[dim]Available steps: " + ", ".join(c["step_id"] + " (" + c["step_name"] + ")" for c in checkpoints) + "[/]")
        return False

    return rollback_to_commit(path, target["message"])


def rollback(path: Path, commit_msg: str) -> bool:
    return rollback_to_commit(path, commit_msg)
