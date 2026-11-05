"""LLM client for plan generation and task decomposition."""
import json
import os
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


PROVIDER_DEFAULTS = {
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "model": "openai/gpt-4o",
        "api_key_env": "OPENROUTER_API_KEY",
    },
    "ollama": {
        "base_url": "http://localhost:11434",
        "model": "llama3",
        "api_key_env": None,
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o",
        "api_key_env": "OPENAI_API_KEY",
    },
}


@dataclass
class LLMConfig:
    provider: str = ""
    model: str = ""
    base_url: str = ""
    api_key: str = ""


@dataclass
class LLMResult:
    content: str = ""
    success: bool = False
    error: str = ""
    model: str = ""


def resolve_llm_config(config: Dict[str, Any]) -> LLMConfig:
    llm_config = config.get("llm", {})
    provider = llm_config.get("provider", "") or os.environ.get("VIBEPLAN_LLM_PROVIDER", "")

    if not provider:
        provider = os.environ.get("VIBEPLAN_LLM_PROVIDER", "")

    if not provider:
        return LLMConfig()

    defaults = PROVIDER_DEFAULTS.get(provider, PROVIDER_DEFAULTS["openai"])
    model = llm_config.get("model", "") or os.environ.get("VIBEPLAN_LLM_MODEL", "") or defaults["model"]
    base_url = llm_config.get("base_url", "") or os.environ.get("VIBEPLAN_LLM_BASE_URL", "") or defaults["base_url"]
    api_key_env = defaults["api_key_env"]
    api_key = llm_config.get("api_key", "") or (os.environ.get(api_key_env, "") if api_key_env else "")

    return LLMConfig(provider=provider, model=model, base_url=base_url.rstrip("/"), api_key=api_key)


def chat_completion(config: LLMConfig, system: str, user: str) -> LLMResult:
    if not config.provider:
        return LLMResult(error="No LLM provider configured. Set --llm or VIBEPLAN_LLM_PROVIDER.")

    if not config.api_key and config.provider != "ollama":
        return LLMResult(error=f"API key not found for {config.provider}. Set {PROVIDER_DEFAULTS[config.provider]['api_key_env']}.")

    url = config.base_url + "/chat/completions"
    body = json.dumps({
        "model": config.model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.3,
        "max_tokens": 4096,
    }).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
    }
    if config.api_key:
        headers["Authorization"] = "Bearer " + config.api_key

    req = urllib.request.Request(url, data=body, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            return LLMResult(content=content, success=True, model=config.model)
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = ": " + e.read().decode("utf-8")
        except Exception:
            pass
        return LLMResult(error=f"HTTP {e.code}{detail}")
    except urllib.error.URLError as e:
        return LLMResult(error=f"Connection failed: {e.reason}")
    except Exception as e:
        return LLMResult(error=str(e))


def build_planning_prompt(answers: Dict) -> str:
    return f"""Generate a structured execution plan for the following task.

## Task
{answers.get('original_prompt', '')}

## Context
- Scope: {answers.get('scope', 'fullstack')}
- Stack: {answers.get('stack', 'not specified')}
- Constraints: {answers.get('constraints', 'none')}
- Quality bar: {answers.get('quality', 'MVP')}

## Instructions
Create 3-6 steps that break down this task into logical execution phases.
Each step should have:
- A short name (single word: research, setup, implement, test, polish, deploy, etc.)
- A clear description of what to do in that step
- A weight (1-5) indicating relative complexity (higher = more token budget)

## Output Format
Respond with ONLY valid JSON (no markdown, no code fences):
{{
  "steps": [
    {{"name": "step_name", "description": "what to do in this step", "weight": 3}}
  ],
  "reasoning": "brief explanation of the plan structure"
}}

The weights will be used to allocate token budget proportionally.
Make steps focused and sequential — each step should build on the previous one."""


def parse_llm_steps(content: str) -> Optional[List[Dict]]:
    content = content.strip()
    if content.startswith("```"):
        lines = content.split("\n")
        content = "\n".join(lines[1:-1])

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        import re
        match = re.search(r"\{[\s\S]*\}", content)
        if match:
            try:
                data = json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
        else:
            return None

    steps = data.get("steps", [])
    if not steps:
        return None

    result = []
    for i, s in enumerate(steps):
        if not isinstance(s, dict) or "name" not in s:
            return None
        result.append({
            "id": str(i + 1),
            "name": s["name"],
            "description": s.get("description", ""),
            "weight": max(1, min(5, s.get("weight", 3))),
        })

    return result
