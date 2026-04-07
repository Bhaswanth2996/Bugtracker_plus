from __future__ import annotations

from app.db.store import BaseStore
from app.models.schemas import Issue, IssuePriority, IssueSearchResult, IssueStatus, UserInDB, UserRole


def _resolve_project_id(store: BaseStore, project: str | None) -> str | None:
    if not project:
        return None
    direct = store.get_project(project)
    if direct:
        return direct.id
    by_key = store.get_project_by_key(project.upper())
    if by_key:
        return by_key.id
    return None


def _allowed_project_ids(store: BaseStore, current_user: UserInDB) -> set[str]:
    projects = store.list_projects()
    if current_user.role == UserRole.admin:
        return {project.id for project in projects}
    return {
        project.id
        for project in projects
        if project.created_by == current_user.id
        or any(member.user_id == current_user.id for member in project.members)
    }


def global_issue_search(
    store: BaseStore,
    *,
    current_user: UserInDB,
    q: str | None = None,
    status: IssueStatus | None = None,
    priority: IssuePriority | None = None,
    assignee_id: str | None = None,
    project: str | None = None,
    limit: int = 20,
) -> list[IssueSearchResult]:
    resolved_project_id = _resolve_project_id(store, project)
    allowed = _allowed_project_ids(store, current_user)
    if resolved_project_id and resolved_project_id not in allowed:
        return []
    if resolved_project_id:
        candidates = store.search_issues(
            q=q,
            project_id=resolved_project_id,
            status=status,
            priority=priority,
            assignee_id=assignee_id,
            limit=limit,
        )
    else:
        candidates = store.search_issues(
            q=q,
            status=status,
            priority=priority,
            assignee_id=assignee_id,
            limit=max(limit * 3, 40),
        )

    visible: list[Issue] = [issue for issue in candidates if issue.project_id in allowed]
    return [
        IssueSearchResult(
            id=issue.id,
            issue_key=issue.issue_key,
            project_id=issue.project_id,
            title=issue.title,
            status=issue.status,
            priority=issue.priority,
            assignee_id=issue.assignee_id,
            updated_at=issue.updated_at,
        )
        for issue in visible[:limit]
    ]
