# Contributing to vibeplan

Thank you for your interest! vibeplan is an early-stage open-source project and contributions are very welcome.

## Getting Started

```bash
git clone https://github.com/KIRILL9123/vibeplan
cd vibeplan
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest
```

## Code Style

We use `ruff` for linting:

```bash
ruff check src/
ruff format src/
```

## How to Contribute

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Make your changes
4. Add tests for new functionality
5. Run `pytest` and `ruff check src/`
6. Open a Pull Request

## Ideas for Contributions

- Agent adapters (OpenCode, Codex, Antigravity, Claude Code)
- LLM-powered planner via OpenRouter
- Token usage tracking and logging
- Resume/rollback CLI commands
- Web UI for plan visualization
- MCP server integration
- Additional question templates per task type

## Reporting Issues

Open a GitHub Issue with:
- What you tried to do
- What happened
- Your OS, Python version, vibeplan version
