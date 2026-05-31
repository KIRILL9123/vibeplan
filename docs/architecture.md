# vibeplan Architecture

## Overview

vibeplan is a CLI-first Python tool. The core is intentionally simple and dependency-light.

## Data Flow

```
User input (prompt)
    └─> questions.py       — clarify intent (5 questions)
            └─> planner.py     — classify task, generate steps
                    └─> budget.py  — allocate tokens per step
                            └─> plan.md + .vibeplan/budget.json

User runs: vibeplan run
    └─> runner.py          — iterate over steps
            ├─> user runs their AI agent manually (MVP)
            ├─> checkpoint.py  — git commit snapshot
            └─> user: continue / rollback / edit / quit
```

## Module Responsibilities

| Module | Responsibility |
|--------|---------------|
| `cli.py` | Entry point, Typer commands: init, run, status |
| `questions.py` | Rich interactive questionnaire |
| `planner.py` | Task classification + plan.md generation |
| `budget.py` | Token budget calculation and persistence |
| `runner.py` | Step-by-step interactive execution loop |
| `checkpoint.py` | Git add/commit/reset operations |
| `config.py` | Path constants |

## File Layout on Disk

```
project/
├── plan.md                  — human-readable execution plan
└── .vibeplan/
    └── budget.json          — machine-readable step budget + progress
```

## Future: Agent Adapters

The `adapters/` layer will allow auto-spawning agents with constrained context:

```
runner.py
    └─> adapters/opencode.py   — spawn opencode with step prompt
    └─> adapters/codex.py      — spawn codex CLI with step context
    └─> adapters/antigravity.py
```

For now (v0.1), user runs the agent manually between prompts.
