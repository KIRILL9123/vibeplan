"""Tests for budget tracking."""
import json
from pathlib import Path
from vibeplan.budget import save_budget, calculate_budget, redistribute_budget


def test_save_budget(tmp_path: Path):
    budget_path = tmp_path / ".vibeplan" / "budget.json"
    steps = [
        {"id": "1", "name": "research", "description": "Research phase", "tokens": 5000},
        {"id": "2", "name": "implement", "description": "Implement phase", "tokens": 10000},
    ]
    answers = {"original_prompt": "test task", "scope": "backend", "stack": "Python"}
    save_budget(budget_path, steps, 15000, answers)
    data = json.loads(budget_path.read_text(encoding="utf-8"))
    assert data["total_tokens"] == 15000
    assert len(data["steps"]) == 2
    assert data["steps"][0]["status"] == "pending"
    assert data["steps"][0]["spent"] == 0
    assert data["original_prompt"] == "test task"
    assert data["answers"]["scope"] == "backend"


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


def test_redistribute_budget_noop_unlimited():
    data = {"total_tokens": None, "steps": [{"id": "1", "status": "pending", "spent": 0, "tokens": None, "weight": 3}]}
    result = redistribute_budget(data)
    assert result["steps"][0]["tokens"] is None


def test_redistribute_budget_after_one_step():
    data = {
        "total_tokens": 10000,
        "steps": [
            {"id": "1", "name": "research", "status": "done", "spent": 2000, "tokens": 3000, "weight": 3},
            {"id": "2", "name": "implement", "status": "pending", "spent": 0, "tokens": 5000, "weight": 5},
            {"id": "3", "name": "test", "status": "pending", "spent": 0, "tokens": 2000, "weight": 2},
        ],
    }
    # 10000 total - 2000 spent = 8000 remaining
    # weights: 5 + 2 = 7, implement = 8000 * 5/7 ≈ 5714, test = 8000 * 2/7 ≈ 2285
    result = redistribute_budget(data)
    implement = result["steps"][1]
    test = result["steps"][2]
    assert implement["tokens"] + test["tokens"] <= 8000
    assert implement["tokens"] > test["tokens"]
    assert result["steps"][0]["tokens"] == 3000


def test_redistribute_budget_all_done():
    data = {
        "total_tokens": 10000,
        "steps": [
            {"id": "1", "status": "done", "spent": 10000, "tokens": 10000, "weight": 5},
        ],
    }
    result = redistribute_budget(data)
    assert result["steps"][0]["tokens"] == 10000


def test_redistribute_budget_no_pending():
    data = {
        "total_tokens": 10000,
        "steps": [
            {"id": "1", "status": "done", "spent": 5000, "tokens": 5000, "weight": 3},
            {"id": "2", "status": "done", "spent": 5000, "tokens": 5000, "weight": 5},
        ],
    }
    result = redistribute_budget(data)
    assert sum(s["tokens"] for s in result["steps"]) == 10000
