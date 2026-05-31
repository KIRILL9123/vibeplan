"""Token budget envelope calculator and tracker."""
import json
from pathlib import Path
from typing import Dict, List, Optional


def calculate_budget(total_budget: Optional[int], steps: List[Dict]) -> List[Dict]:
    if total_budget is None or total_budget <= 0:
        for step in steps:
            step["tokens"] = None
            step["tokens_formatted"] = "unlimited"
        return steps

    weights = []
    for step in steps:
        name = step.get("name", "").lower()
        if any(w in name for w in ("implement", "core", "main", "build")):
            weights.append(5)
        elif any(w in name for w in ("research", "investigate", "explore", "choose")):
            weights.append(3)
        elif any(w in name for w in ("test", "verify", "check")):
            weights.append(2)
        elif any(w in name for w in ("setup", "install", "init", "config")):
            weights.append(2)
        else:
            weights.append(2)

    total_weight = sum(weights)
    for step, w in zip(steps, weights):
        allocated = int(total_budget * w / total_weight)
        step["tokens"] = allocated
        step["tokens_formatted"] = f"{allocated:,}"
        step["weight"] = w

    return steps


def save_budget(budget_path: Path, steps: List[Dict], total: Optional[int], answers: Optional[Dict] = None) -> None:
    data = {
        "original_prompt": answers.get("original_prompt", "") if answers else "",
        "answers": {k: v for k, v in (answers or {}).items() if k != "original_prompt"},
        "total_tokens": total,
        "steps": [
            {
                "id": s.get("id"),
                "name": s.get("name"),
                "description": s.get("description"),
                "tokens": s.get("tokens"),
                "weight": s.get("weight", 3),
                "spent": 0,
                "status": "pending",
            }
            for s in steps
        ],
    }
    budget_path.parent.mkdir(parents=True, exist_ok=True)
    budget_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def redistribute_budget(data: Dict) -> Dict:
    total = data.get("total_tokens")
    if total is None or total <= 0:
        return data

    steps = data.get("steps", [])
    pending = [s for s in steps if s.get("status") != "done"]

    if not pending:
        return data

    spent = sum(s.get("spent", 0) or 0 for s in steps)
    remaining = total - spent

    if remaining <= 0:
        return data

    total_weight = sum(s.get("weight", 3) for s in pending)
    if total_weight <= 0:
        return data

    for s in pending:
        w = s.get("weight", 3)
        allocated = int(remaining * w / total_weight)
        s["tokens"] = allocated
        s["tokens_formatted"] = f"{allocated:,}"

    return data
