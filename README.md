# vibeplan 🔮

> **Structured pre-planner for vibe coding sessions.**  
> **Plan first. Ship faster. Burn fewer tokens.**

vibeplan asks clarifying questions → generates an execution plan with token budgets → runs your AI agent step-by-step with checkpoints and rollback.

## The Problem

AI coding agents (Codex, OpenCode, Antigravity, Claude Code, Cursor) are fast, but:

- 🔥 **Burn tokens exploring** the codebase before doing anything useful
- 🤷 **No structure** — agent decides on the fly, often backtracks
- 💸 **One vague prompt** = unpredictable token spend
- 🔁 **Context lost** between sessions — starts from scratch every time
- ❌ **No safe rollback** when an agent goes in the wrong direction

## The Solution

**vibeplan** adds a lightweight workflow *before* the agent starts:

```
┌─────────────────────────────────────────────────────────────────┐
│  vibeplan init "add JWT auth to FastAPI app"                    │
│                                                                  │
│  1. Clarify intent (5 questions)                                │
│  2. Generate execution plan with token budgets                  │
│  3. Run agent step-by-step                                      │
│  4. Checkpoint after each step (git snapshot)                  │
│  5. Continue ✅ / Rollback ↩️ / Edit plan 📝                    │
└─────────────────────────────────────────────────────────────────┘
```

## Demo

```bash
$ vibeplan init "add JWT authentication to FastAPI project"

╭─ vibeplan ──────────────────────────────────────────────────────╮
│ Task: add JWT authentication to FastAPI project                 │
╰─────────────────────────────────────────────────────────────────╯

Answer a few questions to sharpen the plan:

Scope? [fullstack]: backend
Stack? []: Python/FastAPI + PostgreSQL
Constraints? [none]: no new deps except PyJWT
Quality bar? [MVP]: MVP
Token budget? [unlimited]: 20k

✅ Plan created: plan.md
   Run 'vibeplan run' to execute step-by-step.
```

Generated `plan.md`:

```markdown
# vibeplan: add JWT authentication to FastAPI project

## Context
- Scope: backend
- Stack: Python/FastAPI + PostgreSQL
- Constraints: no new deps except PyJWT
- Quality bar: MVP
- Total budget: 20,000 tokens

## Execution Plan

| Step | Name       | Description                            | Budget |
|------|------------|----------------------------------------|--------|
| 1    | research   | Explore codebase, choose approach      | 4,285  |
| 2    | setup      | Install dependencies if needed         | 2,857  |
| 3    | implement  | Core implementation                    | 7,142  |
| 4    | test       | Tests, manual check, edge cases        | 2,857  |
| 5    | polish     | Refactor, docs, cleanup                | 2,857  |
```

```bash
$ vibeplan run

Step 1: research [budget: 4,285 tokens]
Now run your AI agent for this step, then come back.
Press Enter when agent finishes...

✅ Checkpoint: vibeplan-step-1-research

What next? [continue/rollback/edit/quit]: continue

Step 2: setup [budget: 2,857 tokens]
...
```

## Installation

```bash
pip install vibeplan
```

From source:

```bash
git clone https://github.com/KIRILL9123/vibeplan
cd vibeplan
pip install -e ".[dev]"
```

## Requirements

- Python 3.10+
- Git (required for checkpoints)
- Any AI coding agent: Codex, OpenCode, Antigravity, Claude Code, Cursor...

## Usage

```bash
# Init git repo first (for checkpoints)
git init && git add . && git commit -m "initial"

# Create a plan
vibeplan init "add JWT authentication to FastAPI app"

# Execute step-by-step
vibeplan run

# Check progress and token budget
vibeplan status
```

## Commands

| Command | Description |
|---------|-------------|
| `vibeplan init "<task>"` | Create a new execution plan |
| `vibeplan run` | Execute plan step-by-step with checkpoints |
| `vibeplan status` | Show current plan and token budget status |

## Architecture

```
vibeplan/
├── cli.py          — CLI commands (Typer + Rich)
├── questions.py    — Interactive questionnaire
├── planner.py      — plan.md + budget.json generator
├── budget.py       — Token budget allocator per step
├── runner.py       — Step runner with checkpoint prompts
└── checkpoint.py   — Git snapshot and rollback
```

## Roadmap

- [x] **v0.1** — MVP: template-based planning, checkpoints, budget
- [ ] **v0.2** — Prompt generation per step, resume/rollback commands
- [ ] **v0.3** — OpenCode / Codex / Antigravity adapters (auto-spawn)
- [ ] **v0.4** — LLM-powered planner (OpenRouter / local model)
- [ ] **v0.5** — Dynamic budget redistribution, token usage tracking
- [ ] **v0.6** — MCP server, Web UI for plan visualization

## Contributing

PRs welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT — use freely, fork it, contribute.

---

*vibeplan — because vibe coding without a plan is just gambling.*
