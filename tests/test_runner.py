"""Tests for runner and prompt generation."""
from vibeplan.runner import generate_step_prompt, get_next_pending_step


def test_generate_step_prompt():
    prompt = "add JWT auth to FastAPI"
    answers = {"scope": "backend", "stack": "Python/FastAPI", "constraints": "none", "quality": "MVP", "budget": "20k"}
    step = {"id": "1", "name": "research", "description": "Explore codebase", "tokens": 4285}

    result = generate_step_prompt(prompt, answers, step)
    assert "add JWT auth to FastAPI" in result
    assert "Step 1 — research" in result
    assert "Explore codebase" in result
    assert "4,285 tokens" in result
    assert "backend" in result
    assert "Python/FastAPI" in result


def test_generate_step_prompt_unlimited():
    prompt = "test"
    answers = {"scope": "fullstack"}
    step = {"id": "1", "name": "research", "description": "Research", "tokens": None}

    result = generate_step_prompt(prompt, answers, step)
    assert "unlimited" in result.lower()


def test_get_next_pending_step():
    steps = [
        {"id": "1", "name": "research", "status": "done"},
        {"id": "2", "name": "implement", "status": "pending"},
        {"id": "3", "name": "test", "status": "pending"},
    ]
    next_step = get_next_pending_step(steps)
    assert next_step["id"] == "2"

    all_done = [{"id": "1", "name": "research", "status": "done"}]
    assert get_next_pending_step(all_done) is None
