"""Tests for team mode (share/import)."""
import json
from pathlib import Path
import pytest
from vibeplan.team import export_share, import_shared


def _setup_project(tmp_path: Path) -> Path:
    d = tmp_path / "project"
    (d / ".vibeplan").mkdir(parents=True)
    (d / "plan.md").write_text("# Plan\n## Step 1\nDetails here.")
    budget = {
        "steps": [{"id": "1", "name": "Setup", "status": "pending"}],
        "original_prompt": "Build something",
        "total_tokens": 10000,
    }
    (d / ".vibeplan" / "budget.json").write_text(json.dumps(budget))
    (d / ".vibeplan" / "config.json").write_text(json.dumps({"agent": "opencode"}))
    return d


def test_share_creates_file(tmp_path: Path):
    d = _setup_project(tmp_path)
    share_path = export_share(d)
    assert share_path.exists()
    assert share_path.name == "vibeplan-share.json"


def test_share_contains_all_data(tmp_path: Path):
    d = _setup_project(tmp_path)
    share_path = export_share(d)
    data = json.loads(share_path.read_text())
    assert data["plan_md"] == "# Plan\n## Step 1\nDetails here."
    assert data["budget"]["original_prompt"] == "Build something"
    assert data["config"]["agent"] == "opencode"
    assert data["vibeplan_version"] == "0.5.0"


def test_share_no_plan(tmp_path: Path):
    d = tmp_path / "empty"
    (d / ".vibeplan").mkdir(parents=True)
    with pytest.raises(FileNotFoundError):
        export_share(d)


def test_import_round_trip(tmp_path: Path):
    d = _setup_project(tmp_path)
    share_path = export_share(d)

    dest = tmp_path / "clone"
    import_shared(share_path, dest)

    assert (dest / "plan.md").exists()
    assert (dest / ".vibeplan" / "budget.json").exists()
    assert (dest / ".vibeplan" / "config.json").exists()

    assert (dest / "plan.md").read_text() == "# Plan\n## Step 1\nDetails here."
    config = json.loads((dest / ".vibeplan" / "config.json").read_text())
    assert config["agent"] == "opencode"


def test_import_missing_file(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        import_shared(tmp_path / "nope.json", tmp_path / "dest")


def test_import_creates_directories(tmp_path: Path):
    d = _setup_project(tmp_path)
    share_path = export_share(d)

    dest = tmp_path / "deep" / "nested" / "clone"
    import_shared(share_path, dest)
    assert (dest / "plan.md").exists()
