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

## What to Work On

See [docs/roadmap.md](docs/roadmap.md) for the backlog — pick any unstarted item.

Ideas that are always welcome:
- New agent adapters (Cursor, Windsurf, Continue, etc.)
- New LLM providers or model presets
- Benchmark mode (token comparison with/without vibeplan)
- Plugin system for custom question templates
- Plan history and analytics
- Slack / Discord notifications

## Reporting Issues

Open a GitHub Issue with:
- What you tried to do
- What happened
- Your OS, Python version, vibeplan version
