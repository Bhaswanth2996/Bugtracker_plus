from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import get_store, get_current_user
from app.db.store import BaseStore
from app.models.schemas import (
    Issue,
    IssueCreate,
    IssueHistoryItem,
    IssuePriority,
    IssueStatus,
    IssueUpdate,
    UserInDB,
    UserRole,
)
from app.services.audit import log_action

router = APIRouter(prefix="/api/issues", tags=["issues"])


def _can_update_issue(current_user: UserInDB, issue: Issue) -> bool:
    if current_user.role in {UserRole.admin, UserRole.manager}:
        return True
    return issue.reporter_id == current_user.id or issue.assignee_id == current_user.id


@router.post("", response_model=Issue, status_code=status.HTTP_201_CREATED)
def create_issue(
    payload: IssueCreate,
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> Issue:
    project = store.get_project(payload.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    if payload.assignee_id and not store.get_user_by_id(payload.assignee_id):
        raise HTTPException(status_code=404, detail="Assignee not found.")

    issue = Issue(
        project_id=payload.project_id,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        tags=payload.tags,
        assignee_id=payload.assignee_id,
        reporter_id=current_user.id,
    )
    created = store.create_issue(issue)

    log_action(
        store,
        actor=current_user,
        action="issue.created",
        entity_type="issue",
        entity_id=created.id,
        details={"project_id": created.project_id, "title": created.title},
    )
    return created


@router.get("", response_model=list[Issue])
def list_issues(
    status: IssueStatus | None = Query(default=None),
    priority: IssuePriority | None = Query(default=None),
    project_id: str | None = Query(default=None),
    assignee_id: str | None = Query(default=None),
    _: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> list[Issue]:
    return store.list_issues(
        status=status,
        priority=priority,
        project_id=project_id,
        assignee_id=assignee_id,
    )


@router.get("/{issue_id}", response_model=Issue)
def get_issue(
    issue_id: str,
    _: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> Issue:
    issue = store.get_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found.")
    return issue


@router.patch("/{issue_id}", response_model=Issue)
def update_issue(
    issue_id: str,
    payload: IssueUpdate,
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> Issue:
    issue = store.get_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found.")
    if not _can_update_issue(current_user, issue):
        raise HTTPException(status_code=403, detail="Insufficient permissions.")

    updates = payload.model_dump(exclude_none=True)
    if "assignee_id" in updates and updates["assignee_id"]:
        if not store.get_user_by_id(updates["assignee_id"]):
            raise HTTPException(status_code=404, detail="Assignee not found.")

    if current_user.role in {UserRole.developer, UserRole.tester} and "assignee_id" in updates:
        raise HTTPException(
            status_code=403,
            detail="Only managers/admin can reassign issues.",
        )

    for field_name, new_value in updates.items():
        old_value = getattr(issue, field_name)
        if old_value != new_value:
            issue.history.append(
                IssueHistoryItem(
                    by=current_user.id,
                    field=field_name,
                    old_value=str(old_value) if old_value is not None else None,
                    new_value=str(new_value) if new_value is not None else None,
                )
            )
            setattr(issue, field_name, new_value)

    issue.updated_at = datetime.now(tz=timezone.utc)
    updated = store.update_issue(issue)
    log_action(
        store,
        actor=current_user,
        action="issue.updated",
        entity_type="issue",
        entity_id=issue_id,
        details=updates,
    )
    return updated
