"""Tests for checkpoint and git operations."""
from pathlib import Path
import subprocess
from vibeplan.checkpoint import ensure_git_repo, create_snapshot, list_checkpoints


def test_ensure_git_repo(tmp_path: Path):
    assert not ensure_git_repo(tmp_path)
    subprocess.run(["git", "-C", str(tmp_path), "init"], capture_output=True)
    assert ensure_git_repo(tmp_path)


def test_create_snapshot(tmp_path: Path):
    subprocess.run(["git", "-C", str(tmp_path), "init"], capture_output=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.email", "test@test.com"], capture_output=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "Test"], capture_output=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "--allow-empty", "-m", "initial"], capture_output=True)

    msg = create_snapshot(tmp_path, "1", "research")
    assert msg == "vibeplan-step-1-research"


def test_list_checkpoints(tmp_path: Path):
    subprocess.run(["git", "-C", str(tmp_path), "init"], capture_output=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.email", "test@test.com"], capture_output=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "Test"], capture_output=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "--allow-empty", "-m", "initial"], capture_output=True)

    create_snapshot(tmp_path, "1", "research")
    create_snapshot(tmp_path, "2", "implement")

    checkpoints = list_checkpoints(tmp_path)
    assert len(checkpoints) == 2
    assert checkpoints[0]["step_id"] == "2"
    assert checkpoints[0]["step_name"] == "implement"
    assert checkpoints[1]["step_id"] == "1"
    assert checkpoints[1]["step_name"] == "research"
