# vibeplan

> **Structured pre-planner for vibe coding sessions.**  
> Plan first. Ship faster. Burn fewer tokens.

vibeplan asks clarifying questions, generates an execution plan with token budgets, then runs your AI agent step-by-step with git checkpoints, rollback, and budget tracking.

## The Problem

AI coding agents (OpenCode, Codex CLI, Antigravity, Claude Code) are fast, but:

- **🔥 Token waste** — agents explore the codebase before doing anything useful
- **🤷 No structure** — the agent decides on the fly, often backtracks
- **💸 Unpredictable cost** — one vague prompt = unknown token spend
- **🔁 Context lost** — every session starts from scratch
- **❌ No safe rollback** — when an agent goes wrong, you're stuck

## The Solution

```
┌─────────────────────────────────────────────────────────────────┐
│  vibeplan init "add JWT auth to FastAPI app"                   │
│                                                                 │
│  1. Clarify intent (5 clarifying questions)                    │
│  2. Generate execution plan with per-step token budgets        │
│  3. Auto-spawn your AI agent (or paste prompt manually)        │
│  4. Git checkpoint after each step                             │
│  5. Continue ✅ / Rollback ↩️ / Skip ⏭️ / Quit 💾              │
│  6. Dynamic budget redistribution after each step              │
└─────────────────────────────────────────────────────────────────┘
```

## Features

| Capability | Status |
|---|---|
| Template-based planning (feature/bugfix/refactor/setup) | ✅ |
| LLM-powered planning (OpenRouter, Ollama, OpenAI) | ✅ |
| Token budget allocation + dynamic redistribution | ✅ |
| Git checkpoints per step | ✅ |
| Agent adapters (OpenCode, Codex, Antigravity, Claude) | ✅ |
| Interactive runner with continue/rollback/edit/quit | ✅ |
| `vibeplan resume` — continue paused sessions | ✅ |
| `vibeplan rollback <step>` — revert to any checkpoint | ✅ |
| `vibeplan doctor` — check prerequisites | ✅ |
| `vibeplan export` — portable handoff file | ✅ |
| `vibeplan prompt` — ready-to-paste agent prompts | ✅ |
| MCP server — JSON-RPC for AI tool integration | ✅ |
| Web UI — built-in dashboard on `localhost:8080` | ✅ |
| Team mode — `share` / `import` portable plans | ✅ |
| GitHub Issues — generate or `--publish` issues | ✅ |

## Installation

**From source** (not yet on PyPI):

```bash
git clone https://github.com/KIRILL9123/vibeplan.git
cd vibeplan
pip install -e ".[dev]"
```

## Quick Start

```bash
# 1. Init a git repo (required for checkpoints)
git init && git add . && git commit -m "initial"

# 2. Create a plan
vibeplan init "add JWT authentication to FastAPI app"

# 3. Execute step-by-step
vibeplan run

# 4. Check progress
vibeplan status
```

### With an AI agent

```bash
# Configure an agent
vibeplan init "refactor auth module" --agent opencode

# Or use LLM-powered planning
vibeplan init "build REST API" --llm openrouter
```

### Team collaboration

```bash
# Export a shareable plan file
vibeplan share

# On another machine, import it
vibeplan import vibeplan-share.json
```

### Web UI

```bash
vibeplan web
# → http://localhost:8080
```

### MCP Server

```bash
vibeplan mcp
# → stdio JSON-RPC with 6 tools
```

## Commands

| Command | Description |
|---|---|
| `vibeplan init "<task>"` | Create a new plan (supports `--agent`, `--llm`) |
| `vibeplan run` | Execute plan step-by-step |
| `vibeplan status` | Show progress and token budget |
| `vibeplan resume` | Continue a paused session |
| `vibeplan rollback <step>` | Rollback to a specific step |
| `vibeplan doctor` | Check prerequisites |
| `vibeplan export` | Export plan as handoff file |
| `vibeplan prompt [step]` | Show ready-to-paste agent prompt |
| `vibeplan mcp` | Start MCP server (stdio JSON-RPC) |
| `vibeplan web` | Start Web UI dashboard |
| `vibeplan share` | Export plan as portable team file |
| `vibeplan import <file>` | Import a shared plan |
| `vibeplan issue [--publish]` | Generate or publish a GitHub Issue |

## Requirements

- Python 3.10+
- Git (required for checkpoints)
- Optional: OpenCode, Codex CLI, Antigravity, or Claude Code (for auto-spawn)

## Architecture

```
src/vibeplan/
├── cli.py          — 13 CLI commands (Typer + Rich)
├── questions.py    — Interactive questionnaire
├── planner.py      — plan.md + budget.json generator
├── budget.py       — Token budget allocation & redistribution
├── runner.py       — Step runner with checkpoint prompts
├── checkpoint.py   — Git snapshot create/list/rollback
├── config.py       — .vibeplan/config.json load/save
├── llm.py          — LLM client (OpenRouter/Ollama/OpenAI)
├── team.py         — Share/import portable plans
├── github.py       — GitHub Issue formatting & publishing
├── mcp_server.py   — JSON-RPC MCP server (6 tools)
├── web_ui.py       — Built-in HTTP dashboard
└── adapters/       — Agent adapters (opencode, codex, antigravity, claude)
```

## Roadmap

See [docs/roadmap.md](docs/roadmap.md) for completed releases and upcoming ideas.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

MIT — use freely, fork it, contribute.
