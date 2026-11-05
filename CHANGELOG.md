# Changelog

## v0.5.0 — 2026-05-31 (current)

### Added
- Benchmark mode: `vibeplan benchmark <task> --agent <name>` — runs baseline (raw agent) + creates plan, then compares token spend
- Benchmark report: `vibeplan benchmark` (no args) — shows saved baseline vs actual execution
- `benchmark.py` module — `run_baseline()`, `collect_actual()`, `format_report()`
- 11 new tests for benchmark module

### Added
- MCP server: stdio JSON-RPC with 6 tools (init, status, next_prompt, mark_done, rollback, export)
- Web UI: built-in HTTP dashboard with plan visualisation (progress, budget, steps, checkpoints)
- `vibeplan mcp` — start MCP server for AI agent integration
- `vibeplan web` — start Web UI dashboard on port 8080
- Team mode: `vibeplan share` / `vibeplan import` — portable share files for collaboration
- GitHub Issues: `vibeplan issue` — generate, preview, or `--publish` issues via `gh` CLI

### Changed
- `__init__.py` → `__version__ = "0.5.0"`

### Tests
- 76 tests, ruff clean

---

## v0.4.0 — 2026-04-15

### Added
- LLM client module — OpenRouter, Ollama, OpenAI-compatible (stdlib only, zero dependencies)
- `--llm provider` flag on `vibeplan init` for AI-powered plan generation
- JSON response parsing with code fence / markdown fallback
- Automatic fallback to template-based planning on LLM failure
- Dynamic budget redistribution after each completed step
- LLM config in `.vibeplan/config.json` + env var support (`OPENROUTER_API_KEY`, `OPENAI_API_KEY`)
- Doctor check for LLM config / API key

### Changed
- `generate_plan()` accepts optional `LLMConfig` — falls back to templates when LLM unavailable
- Config schema extended with `llm` section

### Tests
- 50 tests, ruff clean

---

## v0.3.0 — 2026-03-20

### Added
- Base adapter interface + adapter registry
- `BaseCliAdapter` — shared logic for arg/stdin/file pass methods
- Token usage parsing from agent CLI output
- `--agent` flag on `vibeplan init`
- Doctor check for configured agent
- Adapters: OpenCode, Codex CLI, Antigravity, Claude Code

### Changed
- Runner auto-detects and spawns configured agent per step
- Adapters are 5-line classes — trivial to add new ones

### Tests
- 33 tests, ruff clean

---

## v0.2.0 — 2026-02-25

### Added
- `vibeplan resume` — continue a paused session
- `vibeplan rollback <step>` — rollback to a specific step checkpoint
- `vibeplan doctor` — check prerequisites (git, config, agent)
- `vibeplan export` — export plan as a portable handoff markdown file
- Per-step prompt template generation (ready to paste into any AI agent)
- Config file support: `.vibeplan/config.json`

### Changed
- CLI consolidated under single `vibeplan` entry point

### Tests
- 20 tests, CI via GitHub Actions

---

## v0.1.0 — 2026-01-30

### Added
- Interactive questionnaire (5 clarifying questions)
- Template-based plan generation (feature / bugfix / refactor / setup)
- Token budget allocation per step (weighted by complexity)
- `plan.md` + `.vibeplan/budget.json` generation
- Git checkpoint creation after each step
- Interactive runner: continue / rollback / edit / quit
- CLI commands: `vibeplan init`, `vibeplan run`, `vibeplan status`
- 13-module Python project with tests

### Tests
- 9 tests, GitHub Actions CI setup
