"""Tests for Web UI rendering."""
from vibeplan.web_ui import _render_html


def test_render_html_empty():
    html = _render_html({"steps": [], "total_tokens": None, "original_prompt": "test"}, "", [])
    assert "vibeplan" in html
    assert "0/0" in html
    assert "test" in html


def test_render_html_with_data():
    data = {
        "original_prompt": "add JWT auth",
        "total_tokens": 20000,
        "steps": [
            {"id": "1", "name": "research", "status": "done", "tokens": 5000, "spent": 4000},
            {"id": "2", "name": "implement", "status": "pending", "tokens": 10000, "spent": 0},
        ],
    }
    html = _render_html(data, "# plan content", [{"hash": "abc123", "step_id": "1", "step_name": "research"}])
    assert "add JWT auth" in html
    assert "research" in html
    assert "implement" in html
    assert "20,000" in html
    assert "abc123" in html
    assert "1/2" in html
    assert "50%" in html
    assert "plan content" in html


def test_render_html_no_checkpoints():
    data = {
        "original_prompt": "task",
        "total_tokens": None,
        "steps": [{"id": "1", "name": "test", "status": "pending", "tokens": None, "spent": 0}],
    }
    html = _render_html(data, "", [])
    assert "No checkpoints yet" in html
