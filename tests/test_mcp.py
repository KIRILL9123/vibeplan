"""Tests for MCP server handlers."""
from pathlib import Path
from vibeplan.mcp_server import (
    TOOL_DEFINITIONS,
    _handle_vibeplan_init,
    _handle_vibeplan_status,
    _handle_vibeplan_next_prompt,
    _handle_vibeplan_mark_done,
    _handle_vibeplan_rollback,
    _handle_vibeplan_export,
    HANDLERS,
)


def test_tool_definitions():
    names = [t["name"] for t in TOOL_DEFINITIONS]
    assert "vibeplan_init" in names
    assert "vibeplan_status" in names
    assert "vibeplan_next_prompt" in names
    assert "vibeplan_mark_done" in names
    assert "vibeplan_rollback" in names
    assert "vibeplan_export" in names


def test_tool_handlers_registered():
    assert "vibeplan_init" in HANDLERS
    assert "vibeplan_status" in HANDLERS
    assert "vibeplan_next_prompt" in HANDLERS
    assert "vibeplan_mark_done" in HANDLERS
    assert "vibeplan_rollback" in HANDLERS
    assert "vibeplan_export" in HANDLERS


def test_handle_status_no_plan():
    result = _handle_vibeplan_status({})
    assert "error" in result or "steps" in result


def test_handle_init_missing_git(tmp_path: Path):
    result = _handle_vibeplan_init({"task": "test", "project_dir": str(tmp_path)})
    assert "error" in result or "message" in result


def test_handle_next_prompt_no_plan():
    result = _handle_vibeplan_next_prompt({})
    assert "error" in result or "done" in result


def test_handle_mark_done_no_plan():
    result = _handle_vibeplan_mark_done({})
    assert "error" in result or "done" in result


def test_handle_rollback_no_checkpoint():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        result = _handle_vibeplan_rollback({"step": "1", "project_dir": tmp})
        assert result["success"] is False


def test_handle_export_no_plan():
    result = _handle_vibeplan_export({})
    assert "error" in result or "plan" in result


def test_vibeplan_init_with_all_params(tmp_path: Path):
    import subprocess
    subprocess.run(["git", "-C", str(tmp_path), "init"], capture_output=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.email", "t@t.com"], capture_output=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "T"], capture_output=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "--allow-empty", "-m", "init"], capture_output=True)

    result = _handle_vibeplan_init({
        "task": "add login page",
        "scope": "frontend",
        "stack": "React",
        "constraints": "none",
        "quality": "MVP",
        "budget": "10k",
        "project_dir": str(tmp_path),
    })
    assert "plan_path" in result
    assert result["plan_path"].endswith("plan.md")


def test_vibeplan_status_after_init(tmp_path: Path):
    import subprocess
    subprocess.run(["git", "-C", str(tmp_path), "init"], capture_output=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.email", "t@t.com"], capture_output=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "T"], capture_output=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "--allow-empty", "-m", "init"], capture_output=True)

    _handle_vibeplan_init({"task": "test", "project_dir": str(tmp_path)})
    result = _handle_vibeplan_status({"project_dir": str(tmp_path)})
    assert "steps" in result
    assert result["steps_total"] > 0
    assert result["steps_completed"] == 0


def test_tool_input_schemas():
    for tool in TOOL_DEFINITIONS:
        assert "name" in tool
        assert "description" in tool
        assert "inputSchema" in tool
        assert "properties" in tool["inputSchema"]
