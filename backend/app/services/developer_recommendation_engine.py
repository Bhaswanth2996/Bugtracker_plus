from __future__ import annotations

from collections import defaultdict

from app.db.store import BaseStore
from app.models.schemas import (
    IssueStatus,
    RecommendAssigneeResponse,
    UserInDB,
    UserRole,
)


def _eligible_developers(store: BaseStore, project_id: str | None = None) -> list[UserInDB]:
    users = [
        user
        for user in store.list_users()
        if user.role in {UserRole.developer, UserRole.project_manager, UserRole.admin}
    ]
    if not project_id:
        return users
    project = store.get_project(project_id)
    if not project:
        return []
    member_ids = {member.user_id for member in project.members}
    member_ids.add(project.created_by)
    return [user for user in users if user.id in member_ids]


def recommend_assignee(
    store: BaseStore,
    *,
    module: str | None,
    description: str,
    project_id: str | None = None,
) -> RecommendAssigneeResponse:
    candidates = _eligible_developers(store, project_id=project_id)
    if not candidates:
        return RecommendAssigneeResponse(
            recommendedDeveloper=None,
            confidence=0.0,
            reason="No eligible developers were found for this project.",
        )

    issues = store.list_issues(project_id=project_id)
    module_lc = (module or "").strip().lower()
    description_lc = description.lower()
    scores: dict[str, float] = defaultdict(float)

    for user in candidates:
        resolved_count = 0
        module_experience = 0
        workload = 0
        for issue in issues:
            if issue.assignee_id != user.id:
                continue
            if issue.status == IssueStatus.done:
                resolved_count += 1
            else:
                workload += 1
            issue_module = (issue.module or "").lower()
            text_blob = f"{issue.title} {issue.description}".lower()
            if module_lc and (module_lc in issue_module or module_lc in text_blob):
                module_experience += 1
            elif not module_lc and description_lc and any(token in text_blob for token in description_lc.split()[:8]):
                module_experience += 0.2

        score = (resolved_count * 1.8) + (module_experience * 2.5) - (workload * 0.7)
        scores[user.id] = score

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    top_user_id, top_score = ranked[0]
    top_user = next((user for user in candidates if user.id == top_user_id), None)
    if not top_user:
        return RecommendAssigneeResponse(
            recommendedDeveloper=None,
            confidence=0.0,
            reason="Could not determine a suitable developer.",
        )

    total_positive = sum(max(value, 0.0) for _, value in ranked) or 1.0
    confidence = max(0.05, min(0.98, max(top_score, 0.0) / total_positive))
    return RecommendAssigneeResponse(
        recommendedDeveloper=top_user.name,
        confidence=round(float(confidence), 2),
        reason=(
            f"{top_user.name} has strong relevant ownership and manageable workload "
            "for similar issues."
        ),
    )


def developer_workload_insights(store: BaseStore, project_id: str | None = None) -> list[dict]:
    users = _eligible_developers(store, project_id=project_id)
    issues = store.list_issues(project_id=project_id)
    results: list[dict] = []
    for user in users:
        assigned = [item for item in issues if item.assignee_id == user.id]
        open_count = sum(1 for item in assigned if item.status != IssueStatus.done)
        done_count = sum(1 for item in assigned if item.status == IssueStatus.done)
        results.append(
            {
                "developer": user.name,
                "openIssues": open_count,
                "resolvedIssues": done_count,
                "totalAssigned": len(assigned),
            }
        )
    results.sort(key=lambda row: row["openIssues"], reverse=True)
    return results
