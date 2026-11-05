"""Claude Code adapter — spawns Claude Code CLI with step prompt."""
from vibeplan.adapters.base import BaseCliAdapter


class ClaudeCodeAdapter(BaseCliAdapter):
    name = "claude-code"
    command = "claude"
