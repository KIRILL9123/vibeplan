# vibeplan Roadmap

## v0.1.0 — MVP (current)
- [x] Interactive questionnaire (5 clarifying questions)
- [x] Template-based plan generation (feature / bugfix / refactor / setup)
- [x] Token budget allocation per step (weighted by complexity)
- [x] plan.md + budget.json generation
- [x] Git checkpoint creation after each step
- [x] Interactive runner: continue / rollback / edit / quit
- [x] CLI commands: init, run, status
- [x] Tests + GitHub Actions CI

## v0.2.0 — Better UX
- [x] `vibeplan resume` — continue paused session
- [x] `vibeplan rollback <step>` — rollback to specific step
- [x] `vibeplan doctor` — check prerequisites (git, config)
- [x] `vibeplan export` — export plan as portable handoff file
- [x] Per-step prompt template generation (ready to paste into agent)
- [x] Config file support: `.vibeplan/config.json`

## v0.3.0 — Agent Adapters (current)
- [x] Base adapter interface + registry
- [x] BaseCliAdapter — shared CLI logic (arg/stdin/file pass methods)
- [x] Token usage parsing from agent output
- [x] `--agent` flag on `vibeplan init`
- [x] Doctor check for configured agent
- [x] OpenCode adapter — `opencode`
- [x] Codex CLI adapter — `codex`
- [x] Antigravity adapter — `antigravity`
- [x] Claude Code adapter — `claude`

## v0.4.0 — LLM-Powered Planner (current)
- [x] LLM client module — OpenRouter, Ollama, OpenAI-compatible (stdlib only)
- [x] LLM-based plan generation via `--llm provider` flag on init
- [x] JSON response parsing with code fence / markdown fallback
- [x] Automatic fallback to template-based planning on LLM failure
- [x] Dynamic budget redistribution after each completed step
- [x] LLM config in `.vibeplan/config.json` + env var support
- [x] Doctor check for LLM config / API key

## v0.5.0 — Advanced Features (current)
- [x] MCP server — stdio JSON-RPC with 6 tools (init, status, next_prompt, mark_done, rollback, export)
- [x] Web UI — built-in HTTP server with plan visualization (progress, budget, steps, checkpoints)
- [x] `vibeplan mcp` — start MCP server for AI agent integration
- [x] `vibeplan web` — start Web UI dashboard
- [x] Team mode: `vibeplan share` + `vibeplan import` — portable share files
- [x] GitHub Issues: `vibeplan issue` — generate/preview/publish issues from plan

## Ideas / Backlog
- [ ] Benchmark mode: compare token spend with vs without vibeplan
- [ ] Plugin system for custom question templates
- [ ] Plan history and analytics
- [ ] Slack / Discord notifications on step completion
