"""Tests for benchmark mode."""
import json
from pathlib import Path
from vibeplan.benchmark import (
    BenchmarkResult,
    collect_actual,
    save_baseline,
    load_baseline,
    format_report,
)


def _setup_budget(tmp_path: Path, steps) -> Path:
    d = tmp_path / "project"
    (d / ".vibeplan").mkdir(parents=True)
    budget = {"steps": steps, "original_prompt": "test task"}
    (d / ".vibeplan" / "budget.json").write_text(json.dumps(budget))
    return d


def test_collect_actual_no_plan(tmp_path: Path):
    assert collect_actual(tmp_path / "empty") is None


def test_collect_actual_zero_steps(tmp_path: Path):
    d = _setup_budget(tmp_path, [])
    assert collect_actual(d) is None


def test_collect_actual_with_spend(tmp_path: Path):
    steps = [
        {"id": "1", "name": "a", "status": "done", "spent": 2000},
        {"id": "2", "name": "b", "status": "done", "spent": 3000},
    ]
    d = _setup_budget(tmp_path, steps)
    result = collect_actual(d)
    assert result is not None
    assert result.method == "with vibeplan"
    assert result.tokens == 5000
    assert result.steps == 2
    assert result.avg_per_step == 2500.0


def test_collect_actual_some_pending(tmp_path: Path):
    steps = [
        {"id": "1", "name": "a", "status": "done", "spent": 1500},
        {"id": "2", "name": "b", "status": "pending", "spent": 0},
    ]
    d = _setup_budget(tmp_path, steps)
    result = collect_actual(d)
    assert result.tokens == 1500
    assert result.steps == 1


def test_collect_actual_no_spent_field(tmp_path: Path):
    steps = [
        {"id": "1", "name": "a", "status": "done"},
        {"id": "2", "name": "b", "status": "done"},
    ]
    d = _setup_budget(tmp_path, steps)
    result = collect_actual(d)
    assert result.tokens == 0
    assert result.steps == 2


def test_save_and_load_baseline(tmp_path: Path):
    d = tmp_path / "project"
    result = BenchmarkResult(method="without vibeplan", tokens=10000, steps=1, avg_per_step=10000.0)
    save_baseline(d, result)
    loaded = load_baseline(d)
    assert loaded is not None
    assert loaded.tokens == 10000
    assert loaded.method == "without vibeplan"


def test_load_baseline_not_found(tmp_path: Path):
    assert load_baseline(tmp_path / "nope") is None


def test_format_report_both_present():
    baseline = BenchmarkResult("without vibeplan", 15000, 1, 15000.0)
    actual = BenchmarkResult("with vibeplan", 8000, 5, 1600.0)
    report = format_report("test task", baseline, actual)
    assert "without vibeplan" in report
    assert "with vibeplan" in report
    assert "15,000" in report
    assert "8,000" in report
    assert "saved" in report
    assert "46%" in report or "47%" in report  # 15000-8000/15000 = 46.67%


def test_format_report_baseline_only():
    baseline = BenchmarkResult("without vibeplan", 15000, 1, 15000.0)
    report = format_report("test", baseline, None)
    assert "without vibeplan" in report
    assert "15,000" in report
    assert "with vibeplan" not in report or "—" in report


def test_format_report_actual_only():
    actual = BenchmarkResult("with vibeplan", 8000, 5, 1600.0)
    report = format_report("test", None, actual)
    assert "with vibeplan" in report
    assert "without vibeplan" in report or "—" in report


def test_format_report_extra_tokens():
    baseline = BenchmarkResult("without vibeplan", 5000, 1, 5000.0)
    actual = BenchmarkResult("with vibeplan", 8000, 3, 2666.67)
    report = format_report("test", baseline, actual)
    assert "extra" in report
    assert "tuning" in report
