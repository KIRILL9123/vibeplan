"""Agent adapters — auto-spawn AI coding agents with step context."""
from typing import Dict, List, Optional, Type

from vibeplan.adapters.base import BaseAdapter
from vibeplan.adapters.opencode import OpenCodeAdapter
from vibeplan.adapters.codex import CodexAdapter
from vibeplan.adapters.antigravity import AntigravityAdapter
from vibeplan.adapters.claude_code import ClaudeCodeAdapter

ADAPTERS: Dict[str, Type[BaseAdapter]] = {
    "opencode": OpenCodeAdapter,
    "codex": CodexAdapter,
    "antigravity": AntigravityAdapter,
    "claude-code": ClaudeCodeAdapter,
}


def get_adapter(name: str) -> Optional[Type[BaseAdapter]]:
    return ADAPTERS.get(name)


def list_adapters() -> List[str]:
    return list(ADAPTERS.keys())
