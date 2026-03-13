from __future__ import annotations

from app.db.store import BaseStore
from app.models.schemas import AIBugAnalyzeResponse, AIAnalysisLog, IssuePriority
from app.services.developer_recommendation_engine import recommend_assignee
from app.services.duplicate_bug_detector import find_duplicate_issues

PRIORITY_RULES: list[tuple[list[str], IssuePriority]] = [
    (["crash", "data loss", "outage", "security breach"], IssuePriority.critical),
    (["error", "failure", "token expired", "timeout"], IssuePriority.high),
    (["ui", "layout", "ux", "render"], IssuePriority.medium),
    (["minor", "typo", "cosmetic"], IssuePriority.low),
]

LABEL_RULES: dict[str, list[str]] = {
    "auth": ["authentication", "security"],
    "token": ["authentication", "session"],
    "payment": ["payments", "billing"],
    "ui": ["frontend", "ui"],
    "api": ["backend", "api"],
    "test": ["automation", "qa"],
}


def _detect_priority(title: str, description: str) -> IssuePriority:
    blob = f"{title} {description}".lower()
    for keywords, priority in PRIORITY_RULES:
        if any(keyword in blob for keyword in keywords):
            return priority
    return IssuePriority.medium


def _detect_labels(title: str, description: str) -> list[str]:
    blob = f"{title} {description}".lower()
    labels: set[str] = set()
    for keyword, mapped in LABEL_RULES.items():
        if keyword in blob:
            labels.update(mapped)
    return sorted(labels)


def analyze_bug(
    store: BaseStore,
    *,
    title: str,
    description: str,
    project_id: str | None = None,
    module: str | None = None,
) -> AIBugAnalyzeResponse:
    duplicates = find_duplicate_issues(
        store,
        title=title,
        description=description,
        project_id=project_id,
    )
    priority = _detect_priority(title, description)
    labels = _detect_labels(title, description)
    recommendation = recommend_assignee(
        store,
        module=module,
        description=description,
        project_id=project_id,
    )
    response = AIBugAnalyzeResponse(
        possibleDuplicates=[item.issueKey for item in duplicates],
        suggestedPriority=priority,
        suggestedLabels=labels,
        suggestedAssignee=recommendation.recommendedDeveloper,
    )
    store.create_ai_analysis_log(
        AIAnalysisLog(
            analysis_type="analyze_bug",
            payload={"title": title, "description": description[:250], "project_id": project_id},
            result=response.model_dump(mode="json"),
        )
    )
    return response
