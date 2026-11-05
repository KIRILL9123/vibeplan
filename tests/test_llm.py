"""Tests for LLM client, prompt building, and step parsing."""
from vibeplan.llm import (
    PROVIDER_DEFAULTS,
    LLMConfig,
    build_planning_prompt,
    parse_llm_steps,
    resolve_llm_config,
)


def test_provider_defaults():
    assert "openrouter" in PROVIDER_DEFAULTS
    assert "ollama" in PROVIDER_DEFAULTS
    assert "openai" in PROVIDER_DEFAULTS
    assert PROVIDER_DEFAULTS["openrouter"]["model"] == "openai/gpt-4o"
    assert PROVIDER_DEFAULTS["ollama"]["model"] == "llama3"


def test_resolve_llm_config_no_provider():
    config = resolve_llm_config({})
    assert config.provider == ""
    assert config.api_key == ""


def test_resolve_llm_config_with_config():
    cfg = {"llm": {"provider": "openrouter", "model": "anthropic/claude-3-opus", "api_key": "sk-test"}}
    config = resolve_llm_config(cfg)
    assert config.provider == "openrouter"
    assert config.model == "anthropic/claude-3-opus"
    assert config.api_key == "sk-test"


def test_resolve_llm_config_ollama():
    cfg = {"llm": {"provider": "ollama"}}
    config = resolve_llm_config(cfg)
    assert config.provider == "ollama"
    assert config.model == "llama3"
    assert config.api_key == ""


def test_build_planning_prompt():
    answers = {
        "original_prompt": "add JWT auth to FastAPI",
        "scope": "backend",
        "stack": "Python/FastAPI",
        "constraints": "no new deps",
        "quality": "MVP",
        "budget": "20k",
    }
    prompt = build_planning_prompt(answers)
    assert "add JWT auth to FastAPI" in prompt
    assert "backend" in prompt
    assert "Python/FastAPI" in prompt
    assert "no new deps" in prompt
    assert "weight" in prompt
    assert "steps" in prompt


def test_parse_llm_steps_valid():
    content = '{"steps": [{"name": "research", "description": "Explore", "weight": 3}, {"name": "implement", "description": "Build", "weight": 5}], "reasoning": "simple"}'
    steps = parse_llm_steps(content)
    assert steps is not None
    assert len(steps) == 2
    assert steps[0]["name"] == "research"
    assert steps[1]["id"] == "2"
    assert steps[0]["weight"] == 3
    assert steps[1]["weight"] == 5


def test_parse_llm_steps_with_code_fence():
    content = '```json\n{"steps": [{"name": "setup", "description": "Setup", "weight": 2}]}\n```'
    steps = parse_llm_steps(content)
    assert steps is not None
    assert len(steps) == 1
    assert steps[0]["name"] == "setup"


def test_parse_llm_steps_nested_markdown():
    content = 'Some text before\n{\n"steps": [{"name": "test", "description": "Test it", "weight": 4}]\n}\nand after'
    steps = parse_llm_steps(content)
    assert steps is not None
    assert steps[0]["name"] == "test"


def test_parse_llm_steps_invalid():
    assert parse_llm_steps("invalid json") is None
    assert parse_llm_steps('{"not_steps": []}') is None
    assert parse_llm_steps("") is None


def test_parse_llm_steps_empty():
    assert parse_llm_steps('{"steps": []}') is None


def test_parse_llm_steps_weight_clamp():
    content = '{"steps": [{"name": "a", "weight": 0}, {"name": "b", "weight": 10}, {"name": "c", "weight": 3}]}'
    steps = parse_llm_steps(content)
    assert steps is not None
    assert steps[0]["weight"] == 1
    assert steps[1]["weight"] == 5
    assert steps[2]["weight"] == 3


def test_llm_config_dataclass():
    c = LLMConfig(provider="test", model="m", base_url="https://example.com", api_key="key")
    assert c.provider == "test"
    assert c.model == "m"
    assert c.base_url == "https://example.com"
    assert c.api_key == "key"


def test_llm_config_defaults():
    c = LLMConfig()
    assert c.provider == ""
    assert c.model == ""
    assert c.base_url == ""
    assert c.api_key == ""
