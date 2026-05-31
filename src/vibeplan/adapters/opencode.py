"""OpenCode adapter — spawns opencode CLI with step prompt."""
from vibeplan.adapters.base import BaseCliAdapter


class OpenCodeAdapter(BaseCliAdapter):
    name = "opencode"
    command = "opencode"
