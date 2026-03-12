from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import get_current_user, get_store
from app.db.store import BaseStore
from app.models.schemas import Comment, CommentCreate, CommentUpdate, NotificationType, UserInDB, UserRole
from app.services.audit import log_action
from app.services.notifications import notify_user
from app.services.permissions import ensure_project_access

router = APIRouter(prefix="/comments", tags=["comments"])


@router.post("", response_model=Comment, status_code=201)
def create_comment(
    payload: CommentCreate,
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> Comment:
    issue = store.get_issue(payload.issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found.")
    ensure_project_access(store, current_user, issue.project_id)
    if payload.parent_id and not store.get_comment(payload.parent_id):
        raise HTTPException(status_code=404, detail="Parent comment not found.")
    comment = Comment(
        issue_id=payload.issue_id,
        author_id=current_user.id,
        parent_id=payload.parent_id,
        body=payload.body,
    )
    created = store.create_comment(comment)
    log_action(
        store,
        actor=current_user,
        action="comment.created",
        entity_type="comment",
        entity_id=created.id,
        details={"project_id": issue.project_id, "issue_id": created.issue_id, "parent_id": payload.parent_id},
    )

    notify_targets = {issue.reporter_id}
    if issue.assignee_id:
        notify_targets.add(issue.assignee_id)
    notify_targets.discard(current_user.id)
    for target in notify_targets:
        notify_user(
            store,
            user_id=target,
            type=NotificationType.comment,
            title="New comment on issue",
            message=f"{current_user.name} commented on {issue.title}",
            issue_id=issue.id,
            project_id=issue.project_id,
        )
    return created


@router.get("/{issue_id}", response_model=list[Comment])
def list_comments(
    issue_id: str,
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> list[Comment]:
    issue = store.get_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found.")
    ensure_project_access(store, current_user, issue.project_id)
    return store.list_comments(issue_id)


@router.put("/{comment_id}", response_model=Comment)
def edit_comment(
    comment_id: str,
    payload: CommentUpdate,
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> Comment:
    comment = store.get_comment(comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found.")
    issue = store.get_issue(comment.issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found.")
    ensure_project_access(store, current_user, issue.project_id)
    if comment.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only author can edit comment.")
    comment.body = payload.body
    comment.updated_at = datetime.now(tz=timezone.utc)
    updated = store.update_comment(comment)
    log_action(
        store,
        actor=current_user,
        action="comment.updated",
        entity_type="comment",
        entity_id=comment_id,
        details={"project_id": issue.project_id, "issue_id": issue.id},
    )
    return updated


@router.delete("/{comment_id}", response_model=Comment)
def delete_comment(
    comment_id: str,
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> Comment:
    comment = store.get_comment(comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found.")
    issue = store.get_issue(comment.issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found.")
    ensure_project_access(store, current_user, issue.project_id)
    if comment.author_id != current_user.id and current_user.role not in {UserRole.admin, UserRole.project_manager}:
        raise HTTPException(status_code=403, detail="Only author/admin can delete comment.")
    comment.deleted = True
    comment.body = "[deleted]"
    comment.updated_at = datetime.now(tz=timezone.utc)
    updated = store.update_comment(comment)
    log_action(
        store,
        actor=current_user,
        action="comment.deleted",
        entity_type="comment",
        entity_id=comment_id,
        details={"project_id": issue.project_id, "issue_id": issue.id},
    )
    return updated
