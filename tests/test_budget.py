"""Tests for budget tracking."""
import json
from pathlib import Path
from vibeplan.budget import save_budget, calculate_budget


def test_save_budget(tmp_path: Path):
    budget_path = tmp_path / ".vibeplan" / "budget.json"
    steps = [
        {"id": "1", "name": "research", "tokens": 5000},
        {"id": "2", "name": "implement", "tokens": 10000},
    ]
    save_budget(budget_path, steps, 15000)
    data = json.loads(budget_path.read_text(encoding="utf-8"))
    assert data["total_tokens"] == 15000
    assert len(data["steps"]) == 2
    assert data["steps"][0]["status"] == "pending"
    assert data["steps"][0]["spent"] == 0


def test_calculate_budget_sum():
    steps = [{"id": str(i), "name": "implement"} for i in range(3)]
    budgeted = calculate_budget(9000, steps)
    assert sum(s["tokens"] for s in budgeted) <= 9000


def test_calculate_budget_implement_gets_most():
    steps = [
        {"id": "1", "name": "research"},
        {"id": "2", "name": "implement"},
        {"id": "3", "name": "test"},
    ]
    budgeted = calculate_budget(20000, steps)
    assert budgeted[1]["tokens"] >= budgeted[0]["tokens"]
    assert budgeted[1]["tokens"] >= budgeted[2]["tokens"]
