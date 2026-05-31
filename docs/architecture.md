# vibeplan Architecture

## Overview

vibeplan is a CLI-first Python tool. The core is intentionally simple and dependency-light (Typer + Rich + GitPython).

## Data Flow

```
User input (prompt)
    └─> questions.py           — clarify intent (5 questions)
            └─> planner.py         — classify task, generate steps
                    └─> budget.py      — allocate tokens per step (weighted)
                            └─> plan.md + .vibeplan/budget.json
                                         └─> config.json  — agent, LLM, preferences

User runs: vibeplan run
    └─> runner.py              — iterate over steps
            ├─> adapters/*.py     — auto-spawn AI agent (OpenCode, Codex, etc.)
            ├─> checkpoint.py     — git commit snapshot
            └─> redistribute_budget — reallocate unused tokens

Advanced paths:
    └─> mcp_server.py          — JSON-RPC stdio server (6 tools)
    └─> web_ui.py              — HTTP dashboard on localhost:8080
    └─> team.py                — share/import portable plan files
    └─> github.py              — generate/publish GitHub Issues
    └─> llm.py                 — LLM-powered planning (OpenRouter/Ollama/OpenAI)
```

## Module Responsibilities

| Module | Responsibility |
|--------|---------------|
| `cli.py` | Entry point, 13 Typer commands |
| `questions.py` | Rich interactive questionnaire |
| `planner.py` | Task classification + plan.md generation (template + LLM) |
| `budget.py` | Token budget calculation, persistence, redistribution |
| `runner.py` | Step-by-step interactive execution loop |
| `checkpoint.py` | Git add/commit/reset/rollback operations |
| `config.py` | `.vibeplan/config.json` load/save with defaults |
| `adapters/` | Agent adapter registry + BaseCliAdapter (OpenCode, Codex, Antigravity, Claude) |
| `llm.py` | LLM client for AI-powered plan generation |
| `mcp_server.py` | JSON-RPC MCP server (stdio transport, 6 tools) |
| `web_ui.py` | Built-in HTTP dashboard with plan visualization |
| `team.py` | Portable share file export/import |
| `github.py` | GitHub Issue formatting and `--publish` via `gh` |

## File Layout on Disk

```
project/
├── plan.md                  — human-readable execution plan
├── vibeplan-share.json      — portable team share file (from `vibeplan share`)
├── vibeplan-handoff.md      — exported handoff (from `vibeplan export`)
└── .vibeplan/
    ├── config.json           — agent, LLM, preferences
    └── budget.json           — step budget + progress + token tracking
```

## Agent Adapters

Each adapter is a class in `adapters/` extending `BaseCliAdapter`:

```
BaseCliAdapter
├── OpenCodeAdapter     →  opencode <prompt>
├── CodexAdapter        →  codex <prompt>
├── AntigravityAdapter  →  antigravity <prompt>
└── ClaudeCodeAdapter   →  claude <prompt>
```

Runner resolves the adapter per-step, so one step can run via agent and next manually.

## Key Design Decisions

- **Per-step adapter resolution** — user can switch between agent/manual mid-session
- **Weight-based budget** — steps get tokens proportional to complexity (5/3/2 scale)
- **Dynamic redistribution** — unused tokens from done steps go to remaining ones
- **MCP protocol** — server responds to `initialize`, `tools/list`, `tools/call`; never initiates
