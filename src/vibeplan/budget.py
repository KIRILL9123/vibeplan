"""Token budget envelope calculator and tracker."""
import json
from pathlib import Path
from typing import List, Dict, Optional


def calculate_budget(total_budget: Optional[int], steps: List[Dict]) -> List[Dict]:
    """Distribute token budget across steps using weighted allocation."""
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

    return steps


def save_budget(budget_path: Path, steps: List[Dict], total: Optional[int]) -> None:
    """Save budget manifest to disk."""
    data = {
        "total_tokens": total,
        "steps": [
            {
                "id": s.get("id"),
                "name": s.get("name"),
                "tokens": s.get("tokens"),
                "spent": 0,
                "status": "pending",
            }
            for s in steps
        ],
    }
    budget_path.parent.mkdir(parents=True, exist_ok=True)
    budget_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
