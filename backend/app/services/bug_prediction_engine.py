from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from app.db.store import BaseStore
from app.models.schemas import IssuePriority, IssueStatus, ModuleRiskScore


def _resolution_hours(created_at: datetime, updated_at: datetime) -> float:
    seconds = max((updated_at - created_at).total_seconds(), 0.0)
    return seconds / 3600.0


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def compute_bug_risk(store: BaseStore, project_id: str | None = None, limit: int = 8) -> list[ModuleRiskScore]:
    issues = store.list_issues(project_id=project_id)
    grouped: dict[str, list] = defaultdict(list)
    for issue in issues:
        module = (issue.module or "").strip() or "General"
        grouped[module].append(issue)

    if not grouped:
        return []

    bug_counts = {module: sum(1 for item in items if item.issue_type.value == "bug") for module, items in grouped.items()}
    max_bug_count = max(bug_counts.values()) or 1

    results: list[ModuleRiskScore] = []
    for module, items in grouped.items():
        bug_count = bug_counts[module]
        high_priority_count = sum(
            1 for item in items if item.priority in {IssuePriority.high, IssuePriority.critical}
        )
        reopen_count = 0
        done_items = []
        for item in items:
            if item.status == IssueStatus.done:
                done_items.append(item)
            for history in item.history:
                if history.field == "status" and history.old_value == "done" and history.new_value != "done":
                    reopen_count += 1
        mean_resolution = (
            sum(_resolution_hours(item.created_at, item.updated_at) for item in done_items) / len(done_items)
            if done_items
            else 0.0
        )

        bug_factor = bug_count / max_bug_count
        priority_factor = high_priority_count / max(len(items), 1)
        reopen_factor = reopen_count / max(len(items), 1)
        resolution_factor = min(mean_resolution / 96.0, 1.0)
        risk = _clamp((bug_factor * 0.4) + (priority_factor * 0.25) + (reopen_factor * 0.2) + (resolution_factor * 0.15))
        results.append(ModuleRiskScore(module=module, risk=round(float(risk), 2)))

    results.sort(key=lambda item: item.risk, reverse=True)
    return results[:limit]
