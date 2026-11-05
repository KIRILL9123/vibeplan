"""MCP server — exposes vibeplan as tools for AI agents via stdio JSON-RPC."""
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from vibeplan.checkpoint import rollback_to_step, list_checkpoints
from vibeplan.config import get_budget_path, get_plan_path, load_config
from vibeplan.llm import resolve_llm_config
from vibeplan.planner import generate_plan
from vibeplan.questions import DEFAULT_QUESTIONS
from vibeplan.runner import generate_step_prompt, load_plan
from vibeplan.budget import redistribute_budget

TOOL_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "name": "vibeplan_init",
        "description": "Create a new vibeplan execution plan from a task description. Asks clarifying questions and generates a structured step-by-step plan with token budgets.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "What you want to build or fix"},
                "scope": {"type": "string", "description": f"Scope ({DEFAULT_QUESTIONS[0]['default']})"},
                "stack": {"type": "string", "description": "Tech stack"},
                "constraints": {"type": "string", "description": "Hard constraints"},
                "quality": {"type": "string", "description": f"Quality bar ({DEFAULT_QUESTIONS[3]['default']})"},
                "budget": {"type": "string", "description": "Token budget (e.g. 10k, 50k, unlimited)"},
                "project_dir": {"type": "string", "description": "Project directory (default: current dir)"},
            },
            "required": ["task"],
        },
    },
    {
        "name": "vibeplan_status",
        "description": "Get the current progress of an active vibeplan, including step status, token budget, and completion percentage.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_dir": {"type": "string", "description": "Project directory"},
            },
        },
    },
    {
        "name": "vibeplan_next_prompt",
        "description": "Get the ready-to-use prompt for the next incomplete step. The prompt includes context, constraints, and token budget.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_dir": {"type": "string", "description": "Project directory"},
            },
        },
    },
    {
        "name": "vibeplan_mark_done",
        "description": "Mark the current step as completed, create a git checkpoint, and redistribute remaining budget. Returns the next step prompt or completion message.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_dir": {"type": "string", "description": "Project directory"},
            },
        },
    },
    {
        "name": "vibeplan_rollback",
        "description": "Rollback to a specific step checkpoint via git reset. Requires a step number or name.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "step": {"type": "string", "description": "Step number (e.g. 2) or step name (e.g. implement)"},
                "project_dir": {"type": "string", "description": "Project directory"},
            },
            "required": ["step"],
        },
    },
    {
        "name": "vibeplan_export",
        "description": "Export the current plan as a portable handoff markdown file.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_dir": {"type": "string", "description": "Project directory"},
            },
        },
    },
]


def _resolve_dir(project_dir: Optional[str]) -> Path:
    return Path(project_dir).expanduser().resolve() if project_dir else Path.cwd()


def _handle_vibeplan_init(params: Dict) -> Dict:
    answers = {
        "original_prompt": params["task"],
        "scope": params.get("scope", "fullstack"),
        "stack": params.get("stack", ""),
        "constraints": params.get("constraints", "none"),
        "quality": params.get("quality", "MVP"),
        "budget": params.get("budget", "unlimited"),
    }
    project_dir = _resolve_dir(params.get("project_dir"))
    config = load_config(project_dir)
    llm_config = resolve_llm_config(config)
    plan_path = generate_plan(answers, project_dir, llm_config)
    return {"plan_path": str(plan_path), "message": "Plan created. Run vibeplan_status to see progress."}


def _handle_vibeplan_status(params: Dict) -> Dict:
    project_dir = _resolve_dir(params.get("project_dir"))
    data = load_plan(project_dir)
    if not data.get("steps"):
        return {"error": "No active vibeplan found.", "steps": []}
    total = data.get("total_tokens")
    steps = data["steps"]
    done = sum(1 for s in steps if s.get("status") == "done")
    return {
        "task": data.get("original_prompt", ""),
        "total_budget": total,
        "steps_completed": done,
        "steps_total": len(steps),
        "progress_pct": round(done / len(steps) * 100) if steps else 0,
        "steps": [
            {
                "id": s["id"],
                "name": s["name"],
                "status": s.get("status", "pending"),
                "budget": s.get("tokens"),
                "spent": s.get("spent", 0),
            }
            for s in steps
        ],
    }


def _handle_vibeplan_next_prompt(params: Dict) -> Dict:
    project_dir = _resolve_dir(params.get("project_dir"))
    data = load_plan(project_dir)
    steps = data.get("steps", [])
    for s in steps:
        if s.get("status") != "done":
            prompt = data.get("original_prompt", "")
            answers = data.get("answers", {})
            return {
                "step_id": s["id"],
                "step_name": s["name"],
                "prompt": generate_step_prompt(prompt, answers, s),
                "tokens": s.get("tokens"),
            }
    return {"error": "All steps are complete.", "done": True}


def _handle_vibeplan_mark_done(params: Dict) -> Dict:
    project_dir = _resolve_dir(params.get("project_dir"))
    data = load_plan(project_dir)
    steps = data.get("steps", [])
    budget_path = get_budget_path(project_dir)

    for step in steps:
        if step.get("status") != "done":
            step["status"] = "done"
            data = redistribute_budget(data)
            budget_path.parent.mkdir(parents=True, exist_ok=True)
            budget_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

            remaining = [s for s in steps if s.get("status") != "done"]
            if remaining:
                nxt = remaining[0]
                prompt = data.get("original_prompt", "")
                answers = data.get("answers", {})
                return {
                    "completed": {"id": step["id"], "name": step["name"]},
                    "next_step": {"id": nxt["id"], "name": nxt["name"], "tokens": nxt.get("tokens")},
                    "next_prompt": generate_step_prompt(prompt, answers, nxt),
                    "steps_remaining": len(remaining),
                }
            return {
                "completed": {"id": step["id"], "name": step["name"]},
                "message": "All steps complete!",
                "done": True,
            }

    return {"error": "All steps already done.", "done": True}


def _handle_vibeplan_rollback(params: Dict) -> Dict:
    project_dir = _resolve_dir(params.get("project_dir"))
    step = params["step"]
    success = rollback_to_step(project_dir, step)
    return {"success": success, "step": step}


def _handle_vibeplan_export(params: Dict) -> Dict:
    project_dir = _resolve_dir(params.get("project_dir"))
    plan_path = get_plan_path(project_dir)
    if not plan_path.exists():
        return {"error": "No plan found."}
    content = plan_path.read_text(encoding="utf-8")
    data = load_plan(project_dir)
    checkpoints = list_checkpoints(project_dir)
    return {
        "plan": content,
        "steps": data.get("steps", []),
        "checkpoints": [{"hash": c["hash"], "step": c["step_id"] + " - " + c["step_name"]} for c in checkpoints],
    }


HANDLERS = {
    "vibeplan_init": _handle_vibeplan_init,
    "vibeplan_status": _handle_vibeplan_status,
    "vibeplan_next_prompt": _handle_vibeplan_next_prompt,
    "vibeplan_mark_done": _handle_vibeplan_mark_done,
    "vibeplan_rollback": _handle_vibeplan_rollback,
    "vibeplan_export": _handle_vibeplan_export,
}


def _send(msg: Dict) -> None:
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _read() -> Optional[Dict]:
    line = sys.stdin.readline()
    if not line:
        return None
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None


def run_mcp_server() -> None:
    while True:
        msg = _read()
        if msg is None:
            break

        msg_id = msg.get("id")
        method = msg.get("method", "")
        params = msg.get("params", {})

        if method == "initialize":
            _send({"jsonrpc": "2.0", "id": msg_id, "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "vibeplan", "version": "0.5.0"},
            }})

        elif method == "tools/list":
            _send({"jsonrpc": "2.0", "id": msg_id, "result": {"tools": TOOL_DEFINITIONS}})

        elif method == "tools/call":
            tool_name = params.get("name", "")
            tool_params = params.get("arguments", {})
            handler = HANDLERS.get(tool_name)
            if handler:
                try:
                    result = handler(tool_params)
                    _send({"jsonrpc": "2.0", "id": msg_id, "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2, ensure_ascii=False)}]}})
                except Exception as e:
                    _send({"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32603, "message": str(e)}})
            else:
                _send({"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": f"Tool not found: {tool_name}"}})

        else:
            _send({"jsonrpc": "2.0", "id": msg_id, "result": {}})
