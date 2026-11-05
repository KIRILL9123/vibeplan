"""Tests for agent adapters."""
from pathlib import Path
from vibeplan.adapters import get_adapter, list_adapters
from vibeplan.adapters.base import AdapterResult, BaseCliAdapter
from vibeplan.adapters.opencode import OpenCodeAdapter
from vibeplan.adapters.codex import CodexAdapter
from vibeplan.adapters.antigravity import AntigravityAdapter
from vibeplan.adapters.claude_code import ClaudeCodeAdapter


def test_list_adapters():
    adapters = list_adapters()
    assert "opencode" in adapters
    assert "codex" in adapters
    assert "antigravity" in adapters
    assert "claude-code" in adapters


def test_get_adapter():
    assert get_adapter("opencode") is OpenCodeAdapter
    assert get_adapter("codex") is CodexAdapter
    assert get_adapter("antigravity") is AntigravityAdapter
    assert get_adapter("claude-code") is ClaudeCodeAdapter
    assert get_adapter("nonexistent") is None


def test_adapter_names():
    assert OpenCodeAdapter.name == "opencode"
    assert CodexAdapter.name == "codex"
    assert AntigravityAdapter.name == "antigravity"
    assert ClaudeCodeAdapter.name == "claude-code"


def test_adapter_commands():
    assert OpenCodeAdapter.command == "opencode"
    assert CodexAdapter.command == "codex"
    assert AntigravityAdapter.command == "antigravity"
    assert ClaudeCodeAdapter.command == "claude"


def test_adapter_result_defaults():
    r = AdapterResult()
    assert r.success is False
    assert r.exit_code == -1
    assert r.output == ""
    assert r.token_usage is None
    assert r.error == ""


def test_adapter_result_with_values():
    r = AdapterResult(success=True, exit_code=0, output="done", token_usage=1234)
    assert r.success is True
    assert r.token_usage == 1234


def test_all_adapters_check_available():
    for name in list_adapters():
        cls = get_adapter(name)
        assert cls.check_available() is False


def test_build_prompt():
    prompt = "add JWT auth"
    context = {"scope": "backend", "stack": "Python/FastAPI", "constraints": "none"}
    step = {"id": "1", "name": "research", "description": "Explore codebase", "tokens": 4285}

    full_prompt = BaseCliAdapter._build_full_prompt(prompt, context, step)
    assert "Step 1" in full_prompt
    assert "research" in full_prompt
    assert "Explore codebase" in full_prompt
    assert "add JWT auth" in full_prompt
    assert "4,285 tokens" in full_prompt
    assert "scope: backend" in full_prompt


def test_build_prompt_unlimited():
    prompt = "test"
    context = {"scope": "fullstack"}
    step = {"id": "1", "name": "test", "description": "Test", "tokens": None}

    full_prompt = BaseCliAdapter._build_full_prompt(prompt, context, step)
    assert "unlimited" in full_prompt.lower()


def test_parse_token_usage():
    assert BaseCliAdapter._parse_token_usage("Tokens: 1,234") == 1234
    assert BaseCliAdapter._parse_token_usage("~5,678 tokens used") == 5678
    assert BaseCliAdapter._parse_token_usage("Tokens: 500") == 500
    assert BaseCliAdapter._parse_token_usage("no tokens info") is None
    assert BaseCliAdapter._parse_token_usage("tokens: 999") == 999
    assert BaseCliAdapter._parse_token_usage("Tokens used: 1,234") == 1234
    assert BaseCliAdapter._parse_token_usage("~500 tokens total") == 500


def test_run_all_adapters_not_available(tmp_path: Path):
    for name in list_adapters():
        cls = get_adapter(name)
        result = cls.run("prompt", {"scope": "test"}, {"id": "1", "name": "test", "description": "T", "tokens": None}, tmp_path)
        assert result.success is False
        assert "not found" in result.error.lower() or "not on path" in result.error.lower()


def test_run_with_stdin_config(tmp_path: Path):
    result = OpenCodeAdapter.run("test", {"scope": "test"}, {"id": "1", "name": "test", "description": "T", "tokens": None}, tmp_path, agent_config={"pass_method": "stdin"})
    assert result.success is False
    assert "not found" in result.error.lower() or "not on path" in result.error.lower()


def test_run_with_file_config(tmp_path: Path):
    result = OpenCodeAdapter.run("test", {"scope": "test"}, {"id": "1", "name": "test", "description": "T", "tokens": None}, tmp_path, agent_config={"pass_method": "file"})
    assert result.success is False
    assert "not found" in result.error.lower() or "not on path" in result.error.lower()
