"""Team mode — share and import plans."""
import json
from pathlib import Path
from typing import Dict

from vibeplan import __version__
from vibeplan.config import get_budget_path, get_config_path


def export_share(project_dir: Path) -> Path:
    """Export plan + budget + config into a single portable share file."""
    plan_path = project_dir / "plan.md"
    if not plan_path.exists():
        raise FileNotFoundError("No plan found. Run 'vibeplan init' first.")

    plan_content = plan_path.read_text(encoding="utf-8")
    budget_path = get_budget_path(project_dir)
    budget_data = json.loads(budget_path.read_text(encoding="utf-8")) if budget_path.exists() else {}
    config_path = get_config_path(project_dir)
    config_data = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}

    share: Dict = {
        "vibeplan_version": __version__,
        "plan_md": plan_content,
        "budget": budget_data,
        "config": config_data,
    }

    share_path = project_dir / "vibeplan-share.json"
    share_path.write_text(json.dumps(share, indent=2, ensure_ascii=False), encoding="utf-8")
    return share_path


def import_shared(share_file: Path, project_dir: Path) -> None:
    """Import a shared plan into a project directory."""
    if not share_file.exists():
        raise FileNotFoundError(f"Share file not found: {share_file}")

    data = json.loads(share_file.read_text(encoding="utf-8"))
    project_dir.mkdir(parents=True, exist_ok=True)

    plan_path = project_dir / "plan.md"
    plan_path.write_text(data.get("plan_md", ""), encoding="utf-8")

    budget_path = get_budget_path(project_dir)
    budget_path.parent.mkdir(parents=True, exist_ok=True)
    budget_data = data.get("budget", {})
    budget_path.write_text(json.dumps(budget_data, indent=2, ensure_ascii=False), encoding="utf-8")

    config_path = get_config_path(project_dir)
    config_data = data.get("config", {})
    config_path.write_text(json.dumps(config_data, indent=2, ensure_ascii=False), encoding="utf-8")
