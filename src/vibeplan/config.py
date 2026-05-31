"""Configuration management for vibeplan projects."""
import json
from pathlib import Path
from typing import Any, Dict

DEFAULT_CONFIG: Dict[str, Any] = {
    "agent": None,
    "agent_config": {
        "pass_method": "arg",
        "extra_args": [],
    },
    "llm": {
        "provider": None,
        "model": None,
        "base_url": None,
        "api_key": None,
    },
    "default_budget": None,
    "default_quality": "MVP",
    "checkpoints_enabled": True,
}


def get_vibeplan_dir(project_dir: Path) -> Path:
    return project_dir / ".vibeplan"


def get_config_path(project_dir: Path) -> Path:
    return get_vibeplan_dir(project_dir) / "config.json"


def get_plan_path(project_dir: Path) -> Path:
    return project_dir / "plan.md"


def get_budget_path(project_dir: Path) -> Path:
    return get_vibeplan_dir(project_dir) / "budget.json"


def load_config(project_dir: Path) -> Dict[str, Any]:
    path = get_config_path(project_dir)
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        return {**DEFAULT_CONFIG, **data}
    return dict(DEFAULT_CONFIG)


def save_config(project_dir: Path, config: Dict[str, Any]) -> Path:
    path = get_config_path(project_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
