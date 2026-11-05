"""Antigravity adapter — spawns antigravity CLI with step prompt."""
from vibeplan.adapters.base import BaseCliAdapter


class AntigravityAdapter(BaseCliAdapter):
    name = "antigravity"
    command = "antigravity"
