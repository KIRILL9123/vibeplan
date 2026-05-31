"""Tests for plan generation."""
from vibeplan.planner import _template_plan, generate_plan
from vibeplan.budget import calculate_budget
from pathlib import Path


def test_template_plan_feature():
    steps = _template_plan("add new feature", "backend", "Python", "none", "MVP")
    names = [s["name"] for s in steps]
    assert "research" in names
    assert "implement" in names
    assert "test" in names


def test_template_plan_bugfix():
    steps = _template_plan("fix bug in auth", "fullstack", "", "none", "MVP")
    names = [s["name"] for s in steps]
    assert "research" in names
    assert "implement" in names
    assert len(steps) == 3


def test_template_plan_refactor():
    steps = _template_plan("refactor auth module", "backend", "Python", "none", "production-ready")
    names = [s["name"] for s in steps]
    assert "refactor" in names[2] or "implement" in names[2]
    assert len(steps) == 4


def test_budget_distribution():
    steps = [
        {"id": "1", "name": "research"},
        {"id": "2", "name": "implement"},
        {"id": "3", "name": "test"},
    ]
    budgeted = calculate_budget(10000, steps)
    assert budgeted[1]["tokens"] > budgeted[0]["tokens"]
    assert sum(s["tokens"] for s in budgeted) <= 10000


def test_budget_no_limit():
    steps = [{"id": "1", "name": "research"}]
    budgeted = calculate_budget(None, steps)
    assert budgeted[0]["tokens"] is None


def test_generate_plan_creates_files(tmp_path: Path):
    import subprocess
    subprocess.run(["git", "-C", str(tmp_path), "init"], capture_output=True)
    answers = {
        "original_prompt": "add login page",
        "scope": "frontend",
        "stack": "React",
        "constraints": "none",
        "quality": "MVP",
        "budget": "10k",
    }
    plan_path = generate_plan(answers, tmp_path)
    assert plan_path.exists()
    assert (tmp_path / ".vibeplan" / "budget.json").exists()
    content = plan_path.read_text()
    assert "add login page" in content


def test_generate_plan_saves_answers(tmp_path: Path):
    import json
    import subprocess
    subprocess.run(["git", "-C", str(tmp_path), "init"], capture_output=True)
    answers = {
        "original_prompt": "add login page",
        "scope": "frontend",
        "stack": "React",
        "constraints": "none",
        "quality": "MVP",
        "budget": "unlimited",
    }
    generate_plan(answers, tmp_path)
    budget_data = json.loads((tmp_path / ".vibeplan" / "budget.json").read_text())
    assert budget_data["original_prompt"] == "add login page"
    assert budget_data["answers"]["scope"] == "frontend"
