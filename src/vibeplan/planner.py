"""Plan generator — creates structured execution plan from clarified intent."""
from pathlib import Path
from typing import Dict, List, Optional

from vibeplan.budget import calculate_budget, save_budget
from vibeplan.llm import (
    LLMConfig,
    build_planning_prompt,
    chat_completion,
    parse_llm_steps,
)


def generate_plan(answers: Dict, output_dir: Path, llm_config: Optional[LLMConfig] = None) -> Path:
    prompt = answers["original_prompt"]
    scope = answers.get("scope", "fullstack")
    stack = answers.get("stack", "")
    constraints = answers.get("constraints", "none")
    quality = answers.get("quality", "MVP")
    budget_raw = answers.get("budget", "unlimited")

    total_budget = _parse_budget(budget_raw)

    if llm_config and llm_config.provider:
        steps = _generate_llm_plan(prompt, answers, llm_config)
        if not steps:
            steps = _template_plan(prompt, scope, stack, constraints, quality)
    else:
        steps = _template_plan(prompt, scope, stack, constraints, quality)

    steps = calculate_budget(total_budget, steps)

    budget_path = output_dir / ".vibeplan" / "budget.json"
    save_budget(budget_path, steps, total_budget, answers)

    plan_md = _render_plan_md(prompt, answers, steps, total_budget)
    plan_path = output_dir / "plan.md"
    plan_path.write_text(plan_md, encoding="utf-8")

    return plan_path


def _generate_llm_plan(prompt: str, answers: Dict, llm_config: LLMConfig) -> Optional[List[Dict]]:
    planning_prompt = build_planning_prompt(answers)
    result = chat_completion(llm_config, "You are a senior software architect. Generate concise execution plans.", planning_prompt)
    if not result.success:
        return None
    return parse_llm_steps(result.content)


def _parse_budget(budget_raw: str) -> Optional[int]:
    if budget_raw.lower() in ("unlimited", "no", "n/a", "", "inf"):
        return None
    try:
        return int(budget_raw.replace("k", "000").replace("K", "000"))
    except ValueError:
        return None


def _template_plan(prompt: str, scope: str, stack: str, constraints: str, quality: str) -> List[Dict]:
    prompt_lower = prompt.lower()

    is_bugfix = any(w in prompt_lower for w in ("fix", "bug", "repair", "broken", "crash", "error"))
    is_refactor = any(w in prompt_lower for w in ("refactor", "clean", "cleanup", "rewrite", "restructure"))
    is_setup = any(w in prompt_lower for w in ("setup", "init", "install", "configure", "create project", "bootstrap"))

    if is_setup:
        return [
            {"id": "1", "name": "research", "description": "Evaluate project structure and choose approach"},
            {"id": "2", "name": "setup", "description": "Initialize project and install dependencies"},
            {"id": "3", "name": "implement", "description": "Basic structure and hello-world"},
            {"id": "4", "name": "test", "description": "Verify build and basic tests pass"},
            {"id": "5", "name": "polish", "description": "README, .gitignore, final config"},
        ]
    elif is_bugfix:
        return [
            {"id": "1", "name": "research", "description": "Reproduce bug and locate root cause"},
            {"id": "2", "name": "implement", "description": "Minimal fix preserving existing behaviour"},
            {"id": "3", "name": "test", "description": "Verify fix and run regression tests"},
        ]
    elif is_refactor:
        return [
            {"id": "1", "name": "research", "description": "Analyse current code and define refactoring boundaries"},
            {"id": "2", "name": "setup", "description": "Prepare test coverage baseline"},
            {"id": "3", "name": "implement", "description": "Incremental refactoring preserving behaviour"},
            {"id": "4", "name": "test", "description": "Full test suite run and manual verification"},
        ]
    else:
        return [
            {"id": "1", "name": "research", "description": "Explore codebase and choose architectural approach"},
            {"id": "2", "name": "setup", "description": "Install new dependencies if needed"},
            {"id": "3", "name": "implement", "description": "Core feature implementation"},
            {"id": "4", "name": "test", "description": "Tests, manual check, edge cases"},
            {"id": "5", "name": "polish", "description": "Refactor, documentation, cleanup"},
        ]


def _render_plan_md(prompt: str, answers: Dict, steps: List[Dict], total: Optional[int]) -> str:
    budget_line = f"{total:,} tokens" if total else "unlimited"
    rows = ""
    for s in steps:
        rows += f"| {s['id']} | {s['name']} | {s['description']} | {s.get('tokens_formatted', 'unlimited')} |\n"

    return f"""# vibeplan: {prompt}

## Context
- **Scope:** {answers.get('scope', '-')}
- **Stack:** {answers.get('stack', '-')}
- **Constraints:** {answers.get('constraints', '-')}
- **Quality bar:** {answers.get('quality', 'MVP')}
- **Total budget:** {budget_line}

## Execution Plan

| Step | Name | Description | Budget |
|------|------|-------------|--------|
{rows}
## Checkpoints

After each step vibeplan will pause and ask:
- ✅ **continue** — proceed to next step
- ↩️ **rollback** — revert changes via git
- 📝 **edit** — modify plan and resume
- 🚪 **quit** — pause and resume later

## Git Strategy

Each step is committed automatically: `vibeplan-step-{{id}}-{{name}}`  
This allows rollback to any checkpoint at any time.
"""
