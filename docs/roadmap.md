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
- [ ] `vibeplan resume` — continue paused session
- [ ] `vibeplan rollback <step>` — rollback to specific step
- [ ] `vibeplan doctor` — check prerequisites (git, config)
- [ ] `vibeplan export` — export plan as portable handoff file
- [ ] Per-step prompt template generation (ready to paste into agent)
- [ ] Config file support: `.vibeplan/config.json`

## v0.3.0 — Agent Adapters
- [ ] OpenCode adapter (auto-spawn with step context)
- [ ] Codex CLI adapter
- [ ] Antigravity adapter
- [ ] Claude Code adapter
- [ ] Token usage logging from agent responses

## v0.4.0 — LLM-Powered Planner
- [ ] LLM-based plan generation (OpenRouter / local model / Ollama)
- [ ] Dynamic budget redistribution based on actual spend
- [ ] Automatic task decomposition for large prompts
- [ ] Context-aware step splitting

## v0.5.0 — Advanced Features
- [ ] MCP server mode (use vibeplan as an MCP tool from any agent)
- [ ] Web UI for plan visualization and editing
- [ ] Team mode: shared plans and budgets
- [ ] Integration with GitHub Issues

## Ideas / Backlog
- [ ] Benchmark mode: compare token spend with vs without vibeplan
- [ ] Plugin system for custom question templates
- [ ] Plan history and analytics
- [ ] Slack / Discord notifications on step completion
