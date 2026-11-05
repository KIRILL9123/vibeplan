"""Codex CLI adapter — spawns codex CLI with step prompt."""
from vibeplan.adapters.base import BaseCliAdapter


class CodexAdapter(BaseCliAdapter):
    name = "codex"
    command = "codex"
