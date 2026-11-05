"""Benchmark mode — compare token spend with vs without vibeplan."""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from vibeplan.adapters import get_adapter
from vibeplan.config import load_config
from vibeplan.runner import load_plan


BENCHMARK_FILENAME = "benchmark.json"


@dataclass
class BenchmarkResult:
    method: str
    tokens: int
    steps: int
    avg_per_step: float


def _get_benchmark_path(project_dir: Path) -> Path:
    return project_dir / ".vibeplan" / BENCHMARK_FILENAME


def run_baseline(task: str, project_dir: Path) -> Optional[BenchmarkResult]:
    """Run the raw task through the agent adapter once (simulates no-vibeplan)."""
    config = load_config(project_dir)
    agent_name = config.get("agent")
    if not agent_name:
        return None

    adapter_cls = get_adapter(agent_name)
    if not adapter_cls or not adapter_cls.check_available():
        return None

    agent_config = config.get("agent_config", {})
    step = {"id": "0", "name": "direct", "description": task, "tokens": None}
    result = adapter_cls.run(task, {}, step, project_dir, agent_config)

    if result.success and result.token_usage:
        return BenchmarkResult(
            method="without vibeplan",
            tokens=result.token_usage,
            steps=1,
            avg_per_step=float(result.token_usage),
        )
    return None


def collect_actual(project_dir: Path) -> Optional[BenchmarkResult]:
    """Read actual token spend from budget.json after vibeplan run."""
    data = load_plan(project_dir)
    steps = data.get("steps", [])
    if not steps:
        return None

    total_tokens = sum(s.get("spent", 0) or 0 for s in steps)
    done_steps = sum(1 for s in steps if s.get("status") == "done")

    return BenchmarkResult(
        method="with vibeplan",
        tokens=total_tokens,
        steps=done_steps,
        avg_per_step=total_tokens / done_steps if done_steps > 0 else 0,
    )


def save_baseline(project_dir: Path, result: BenchmarkResult) -> None:
    path = _get_benchmark_path(project_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "method": result.method,
        "tokens": result.tokens,
        "steps": result.steps,
        "avg_per_step": result.avg_per_step,
    }, indent=2), encoding="utf-8")


def load_baseline(project_dir: Path) -> Optional[BenchmarkResult]:
    path = _get_benchmark_path(project_dir)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return BenchmarkResult(**data)


def format_report(task: str, baseline: Optional[BenchmarkResult], actual: Optional[BenchmarkResult]) -> str:
    """Format comparison report as markdown."""
    lines: list[str] = []
    lines.append("## Benchmark: " + task)
    lines.append("")
    lines.append("| Method | Tokens | Steps | Avg/Step |")
    lines.append("|--------|--------|-------|----------|")

    if baseline:
        lines.append(f"| {baseline.method} | {baseline.tokens:,} | {baseline.steps} | {baseline.avg_per_step:,.0f} |")
    else:
        lines.append("| without vibeplan | — | — | — |")

    if actual:
        lines.append(f"| {actual.method} | {actual.tokens:,} | {actual.steps} | {actual.avg_per_step:,.0f} |")
    else:
        lines.append("| with vibeplan | — | — | — |")

    if baseline and actual and actual.tokens > 0:
        saved = baseline.tokens - actual.tokens
        pct = (saved / baseline.tokens * 100) if baseline.tokens > 0 else 0
        if saved > 0:
            lines.append("")
            lines.append(f"**{abs(saved):,} tokens saved ({abs(pct):.0f}%)**")
            lines.append("vibeplan saved tokens by structuring the work into focused steps.")
        else:
            lines.append("")
            lines.append(f"**{abs(saved):,} extra tokens ({abs(pct):.0f}%)** — the plan may need tuning.")

    return "\n".join(lines)
