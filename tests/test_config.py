"""Tests for config management."""
from pathlib import Path
from vibeplan.config import (
    load_config,
    save_config,
    get_config_path,
    get_plan_path,
    get_budget_path,
    get_vibeplan_dir,
    DEFAULT_CONFIG,
)


def test_get_paths(tmp_path: Path):
    assert get_vibeplan_dir(tmp_path) == tmp_path / ".vibeplan"
    assert get_config_path(tmp_path) == tmp_path / ".vibeplan" / "config.json"
    assert get_plan_path(tmp_path) == tmp_path / "plan.md"
    assert get_budget_path(tmp_path) == tmp_path / ".vibeplan" / "budget.json"


def test_default_config(tmp_path: Path):
    config = load_config(tmp_path)
    assert config == DEFAULT_CONFIG


def test_save_and_load_config(tmp_path: Path):
    custom = {"agent": "opencode", "default_budget": "50k"}
    save_config(tmp_path, custom)
    loaded = load_config(tmp_path)
    assert loaded["agent"] == "opencode"
    assert loaded["default_budget"] == "50k"
    assert loaded["default_quality"] == "MVP"


def test_config_merges_with_defaults(tmp_path: Path):
    save_config(tmp_path, {"agent": "codex"})
    loaded = load_config(tmp_path)
    assert loaded["agent"] == "codex"
    assert loaded["checkpoints_enabled"] is True
    assert loaded["default_budget"] is None
