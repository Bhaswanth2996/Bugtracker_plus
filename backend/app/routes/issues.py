from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from app.core.deps import get_current_user, get_store
from app.db.store import BaseStore
from app.models.schemas import (
    Attachment,
    BacklogReorderRequest,
    Issue,
    IssueCreate,
    IssueHistoryItem,
    IssueLink,
    IssueLinkCreate,
    IssueLinkType,
    IssueMoveToSprint,
    IssuePriority,
    IssueStatus,
    IssueUpdate,
    NotificationType,
    UserInDB,
    UserRole,
)
from app.services.activity import log_issue_activity
from app.services.attachments import storage
from app.services.audit import log_action
from app.services.notifications import notify_user
from app.services.permissions import can_manage_project, ensure_project_access

router = APIRouter(prefix="/issues", tags=["issues"])
project_router = APIRouter(prefix="/projects", tags=["issues"])


def _can_update_issue(user: UserInDB, issue: Issue) -> bool:
    return user.role in {UserRole.admin, UserRole.project_manager} or issue.reporter_id == user.id or issue.assignee_id == user.id


@router.post("", response_model=Issue, status_code=status.HTTP_201_CREATED)
def create_issue(
    payload: IssueCreate,
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> Issue:
    ensure_project_access(store, current_user, payload.project_id)
    if payload.assignee_id and not store.get_user_by_id(payload.assignee_id):
        raise HTTPException(status_code=404, detail="Assignee not found.")

    issue = Issue(
        project_id=payload.project_id,
        title=payload.title,
        description=payload.description,
        issue_type=payload.issue_type,
        priority=payload.priority,
        assignee_id=payload.assignee_id,
        reporter_id=current_user.id,
        labels=payload.labels,
    )
    project = store.get_project(payload.project_id)
    sequence = store.next_issue_sequence(payload.project_id)
    issue.issue_key = f"{project.key}-{sequence}" if project else None
    issue.history.append(IssueHistoryItem(by=current_user.id, action="created"))
    created = store.create_issue(issue)
    log_issue_activity(
        store,
        issue_id=created.id,
        actor=current_user,
        action="issue_created",
        metadata={"issue_key": created.issue_key, "project_id": created.project_id},
    )
    log_action(
        store,
        actor=current_user,
        action="issue.created",
        entity_type="issue",
        entity_id=created.id,
        details={"project_id": created.project_id, "title": created.title},
    )
    if created.assignee_id:
        notify_user(
            store,
            user_id=created.assignee_id,
            type=NotificationType.assignment,
            title="Issue assigned",
            message=f"You were assigned issue {created.title}.",
            issue_id=created.id,
            project_id=created.project_id,
        )
    return created


@router.get("", response_model=list[Issue])
def list_issues(
    project_id: str | None = Query(default=None),
    status: IssueStatus | None = Query(default=None),
    priority: IssuePriority | None = Query(default=None),
    assignee_id: str | None = Query(default=None),
    sprint_id: str | None = Query(default=None),
    labels: str | None = Query(default=None, description="Comma separated labels."),
    search: str | None = Query(default=None),
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> list[Issue]:
    if project_id:
        ensure_project_access(store, current_user, project_id)
    parsed_labels = [label.strip() for label in (labels or "").split(",") if label.strip()]
    return store.list_issues(
        project_id=project_id,
        status=status,
        priority=priority,
        assignee_id=assignee_id,
        sprint_id=sprint_id,
        labels=parsed_labels or None,
        search=search,
    )


@router.get("/key/{issue_key}", response_model=Issue)
def get_issue_by_key(
    issue_key: str,
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> Issue:
    issue = store.get_issue_by_key(issue_key)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found.")
    ensure_project_access(store, current_user, issue.project_id)
    return issue


@router.get("/{issue_id}", response_model=Issue)
def get_issue(
    issue_id: str,
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> Issue:
    issue = store.get_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found.")
    ensure_project_access(store, current_user, issue.project_id)
    return issue


@router.put("/{issue_id}", response_model=Issue)
def update_issue(
    issue_id: str,
    payload: IssueUpdate,
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> Issue:
    issue = store.get_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found.")
    ensure_project_access(store, current_user, issue.project_id)
    if not _can_update_issue(current_user, issue):
        raise HTTPException(status_code=403, detail="Insufficient permissions.")

    updates = payload.model_dump(exclude_none=True)
    if "assignee_id" in updates and updates["assignee_id"] and not store.get_user_by_id(updates["assignee_id"]):
        raise HTTPException(status_code=404, detail="Assignee not found.")
    if "assignee_id" in updates and current_user.role in {UserRole.developer, UserRole.tester}:
        raise HTTPException(status_code=403, detail="Only admin/project manager can reassign issues.")

    old_status = issue.status
    old_assignee = issue.assignee_id
    for field_name, value in updates.items():
        old_value = getattr(issue, field_name)
        if old_value != value:
            issue.history.append(
                IssueHistoryItem(
                    by=current_user.id,
                    action="field.updated",
                    field=field_name,
                    old_value=str(old_value) if old_value is not None else None,
                    new_value=str(value) if value is not None else None,
                )
            )
            setattr(issue, field_name, value)
    issue.updated_at = datetime.now(tz=timezone.utc)
    updated = store.update_issue(issue)

    if old_assignee != updated.assignee_id and updated.assignee_id:
        notify_user(
            store,
            user_id=updated.assignee_id,
            type=NotificationType.assignment,
            title="Issue assigned",
            message=f"You were assigned issue {updated.title}.",
            issue_id=updated.id,
            project_id=updated.project_id,
        )
    if old_status != updated.status:
        notify_targets = {updated.reporter_id}
        if updated.assignee_id:
            notify_targets.add(updated.assignee_id)
        for target in notify_targets:
            notify_user(
                store,
                user_id=target,
                type=NotificationType.status_change,
                title="Issue status changed",
                message=f"{updated.title} moved to {updated.status.value.replace('_', ' ').title()}",
                issue_id=updated.id,
                project_id=updated.project_id,
            )

    log_action(
        store,
        actor=current_user,
        action="issue.updated",
        entity_type="issue",
        entity_id=updated.id,
        details={"project_id": updated.project_id, **updates},
    )
    log_issue_activity(
        store,
        issue_id=updated.id,
        actor=current_user,
        action="issue_updated",
        metadata=updates,
    )
    return updated


@router.delete("/{issue_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_issue(
    issue_id: str,
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> None:
    issue = store.get_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found.")
    ensure_project_access(store, current_user, issue.project_id)
    if not can_manage_project(current_user):
        raise HTTPException(status_code=403, detail="Only admin/project manager can delete issues.")
    store.delete_issue(issue_id)
    log_issue_activity(
        store,
        issue_id=issue_id,
        actor=current_user,
        action="issue_deleted",
        metadata={"project_id": issue.project_id},
    )
    log_action(
        store,
        actor=current_user,
        action="issue.deleted",
        entity_type="issue",
        entity_id=issue_id,
        details={"project_id": issue.project_id},
    )


@router.post("/{issue_id}/attachments", response_model=Issue)
async def upload_attachment(
    issue_id: str,
    file: UploadFile = File(...),
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> Issue:
    issue = store.get_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found.")
    ensure_project_access(store, current_user, issue.project_id)
    blob_url, filename = await storage.save_file(file)
    attachment = Attachment(
        filename=filename,
        content_type=file.content_type or "application/octet-stream",
        blob_url=blob_url,
        uploaded_by=current_user.id,
    )
    issue.attachments.append(attachment)
    issue.history.append(IssueHistoryItem(by=current_user.id, action="attachment.added", field="attachments", new_value=filename))
    issue.updated_at = datetime.now(tz=timezone.utc)
    updated = store.update_issue(issue)
    log_issue_activity(
        store,
        issue_id=issue.id,
        actor=current_user,
        action="attachment_added",
        metadata={"filename": filename, "attachment_id": attachment.id},
    )
    log_action(
        store,
        actor=current_user,
        action="issue.attachment.added",
        entity_type="issue",
        entity_id=issue.id,
        details={"project_id": issue.project_id, "attachment_id": attachment.id, "filename": filename},
    )
    return updated


@router.put("/{issue_id}/sprint", response_model=Issue)
def move_issue_to_sprint(
    issue_id: str,
    payload: IssueMoveToSprint,
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> Issue:
    issue = store.get_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found.")
    ensure_project_access(store, current_user, issue.project_id)
    if not can_manage_project(current_user):
        raise HTTPException(status_code=403, detail="Only admin/project manager can move issues to sprint.")
    if payload.sprint_id:
        sprint = store.get_sprint(payload.sprint_id)
        if not sprint or sprint.project_id != issue.project_id:
            raise HTTPException(status_code=404, detail="Sprint not found for project.")
    issue.sprint_id = payload.sprint_id
    issue.backlog_order = payload.backlog_order
    issue.updated_at = datetime.now(tz=timezone.utc)
    issue.history.append(
        IssueHistoryItem(
            by=current_user.id,
            action="sprint.updated",
            field="sprint_id",
            new_value=payload.sprint_id,
        )
    )
    updated = store.update_issue(issue)
    log_issue_activity(
        store,
        issue_id=issue.id,
        actor=current_user,
        action="issue_moved_to_sprint",
        metadata={"sprint_id": payload.sprint_id},
    )
    log_action(
        store,
        actor=current_user,
        action="issue.sprint.updated",
        entity_type="issue",
        entity_id=issue.id,
        details={"project_id": issue.project_id, "sprint_id": payload.sprint_id},
    )
    return updated


@project_router.put("/{project_id}/backlog/reorder")
def reorder_backlog(
    project_id: str,
    payload: BacklogReorderRequest,
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> dict[str, int]:
    ensure_project_access(store, current_user, project_id)
    if not can_manage_project(current_user):
        raise HTTPException(status_code=403, detail="Only admin/project manager can reorder backlog.")
    updated_count = 0
    for item in payload.items:
        issue = store.get_issue(item.issue_id)
        if not issue or issue.project_id != project_id:
            continue
        issue.backlog_order = item.backlog_order
        issue.updated_at = datetime.now(tz=timezone.utc)
        store.update_issue(issue)
        updated_count += 1
    log_action(
        store,
        actor=current_user,
        action="backlog.reordered",
        entity_type="project",
        entity_id=project_id,
        details={"project_id": project_id, "updated_count": updated_count},
    )
    return {"updated": updated_count}


@project_router.get("/{project_id}/board")
def get_project_board(
    project_id: str,
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> dict[str, list[Issue]]:
    ensure_project_access(store, current_user, project_id)
    issues = store.list_issues(project_id=project_id)
    return {
        "todo": [item for item in issues if item.status == IssueStatus.todo],
        "in_progress": [item for item in issues if item.status == IssueStatus.in_progress],
        "done": [item for item in issues if item.status == IssueStatus.done],
    }


@router.get("/{issue_id}/activity")
def list_issue_activity(
    issue_id: str,
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
):
    issue = store.get_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found.")
    ensure_project_access(store, current_user, issue.project_id)
    return store.list_issue_activity(issue_id)


@router.get("/{issue_id}/links", response_model=list[IssueLink])
def list_issue_links(
    issue_id: str,
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> list[IssueLink]:
    issue = store.get_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found.")
    ensure_project_access(store, current_user, issue.project_id)
    return store.list_issue_links(issue_id)


@router.post("/{issue_id}/links", response_model=IssueLink, status_code=201)
def create_issue_link(
    issue_id: str,
    payload: IssueLinkCreate,
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> IssueLink:
    source = store.get_issue(issue_id)
    target = store.get_issue(payload.target_issue_id)
    if not source or not target:
        raise HTTPException(status_code=404, detail="Issue not found.")
    ensure_project_access(store, current_user, source.project_id)
    if source.project_id != target.project_id:
        raise HTTPException(status_code=400, detail="Linked issues must belong to same project.")

    link = IssueLink(
        source_issue_id=source.id,
        target_issue_id=target.id,
        link_type=payload.link_type,
        created_by=current_user.id,
    )
    created = store.create_issue_link(link)
    # Create inverse link for blocks/blocked_by relationships.
    if payload.link_type in {IssueLinkType.blocks, IssueLinkType.blocked_by}:
        inverse_type = (
            IssueLinkType.blocked_by
            if payload.link_type == IssueLinkType.blocks
            else IssueLinkType.blocks
        )
        inverse = IssueLink(
            source_issue_id=target.id,
            target_issue_id=source.id,
            link_type=inverse_type,
            created_by=current_user.id,
        )
        store.create_issue_link(inverse)

    log_issue_activity(
        store,
        issue_id=source.id,
        actor=current_user,
        action="issue_link_added",
        metadata={"target_issue_id": target.id, "link_type": payload.link_type.value},
    )
    return created


@router.delete("/{issue_id}/links/{link_id}", status_code=204)
def delete_issue_link(
    issue_id: str,
    link_id: str,
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> None:
    issue = store.get_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found.")
    ensure_project_access(store, current_user, issue.project_id)
    if not store.delete_issue_link(link_id):
        raise HTTPException(status_code=404, detail="Issue link not found.")
    log_issue_activity(
        store,
        issue_id=issue_id,
        actor=current_user,
        action="issue_link_deleted",
        metadata={"link_id": link_id},
    )
