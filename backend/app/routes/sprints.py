from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import get_current_user, get_store
from app.db.store import BaseStore
from app.models.schemas import Issue, Sprint, SprintCreate, SprintStatus, SprintUpdate, UserInDB
from app.services.audit import log_action
from app.services.permissions import can_manage_project, ensure_project_access

router = APIRouter(prefix="/sprints", tags=["sprints"])
project_router = APIRouter(prefix="/projects", tags=["sprints"])


@router.post("", response_model=Sprint, status_code=status.HTTP_201_CREATED)
def create_sprint(
    payload: SprintCreate,
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> Sprint:
    ensure_project_access(store, current_user, payload.project_id)
    if not can_manage_project(current_user):
        raise HTTPException(status_code=403, detail="Only admin/project manager can create sprint.")
    sprint = Sprint(
        project_id=payload.project_id,
        name=payload.name,
        goal=payload.goal,
        start_date=payload.start_date,
        end_date=payload.end_date,
        created_by=current_user.id,
    )
    created = store.create_sprint(sprint)
    log_action(
        store,
        actor=current_user,
        action="sprint.created",
        entity_type="sprint",
        entity_id=created.id,
        details={"project_id": created.project_id, "name": created.name},
    )
    return created


@router.get("", response_model=list[Sprint])
def list_sprints(
    project_id: str | None = Query(default=None),
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> list[Sprint]:
    if project_id:
        ensure_project_access(store, current_user, project_id)
    return store.list_sprints(project_id=project_id)


@router.put("/{sprint_id}", response_model=Sprint)
def update_sprint(
    sprint_id: str,
    payload: SprintUpdate,
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> Sprint:
    sprint = store.get_sprint(sprint_id)
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found.")
    ensure_project_access(store, current_user, sprint.project_id)
    if not can_manage_project(current_user):
        raise HTTPException(status_code=403, detail="Only admin/project manager can update sprint.")
    updates = payload.model_dump(exclude_none=True)
    for field_name, value in updates.items():
        setattr(sprint, field_name, value)
    sprint.updated_at = datetime.now(tz=timezone.utc)
    updated = store.update_sprint(sprint)
    log_action(
        store,
        actor=current_user,
        action="sprint.updated",
        entity_type="sprint",
        entity_id=sprint_id,
        details={"project_id": sprint.project_id, **updates},
    )
    return updated


@router.post("/{sprint_id}/start", response_model=Sprint)
def start_sprint(
    sprint_id: str,
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> Sprint:
    sprint = store.get_sprint(sprint_id)
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found.")
    ensure_project_access(store, current_user, sprint.project_id)
    if not can_manage_project(current_user):
        raise HTTPException(status_code=403, detail="Only admin/project manager can start sprint.")
    sprint.status = SprintStatus.active
    if sprint.start_date is None:
        sprint.start_date = datetime.now(tz=timezone.utc)
    sprint.updated_at = datetime.now(tz=timezone.utc)
    updated = store.update_sprint(sprint)
    log_action(
        store,
        actor=current_user,
        action="sprint.started",
        entity_type="sprint",
        entity_id=sprint.id,
        details={"project_id": sprint.project_id},
    )
    return updated


@router.post("/{sprint_id}/close", response_model=Sprint)
def close_sprint(
    sprint_id: str,
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> Sprint:
    sprint = store.get_sprint(sprint_id)
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found.")
    ensure_project_access(store, current_user, sprint.project_id)
    if not can_manage_project(current_user):
        raise HTTPException(status_code=403, detail="Only admin/project manager can close sprint.")
    sprint.status = SprintStatus.closed
    sprint.updated_at = datetime.now(tz=timezone.utc)
    updated = store.update_sprint(sprint)
    log_action(
        store,
        actor=current_user,
        action="sprint.closed",
        entity_type="sprint",
        entity_id=sprint.id,
        details={"project_id": sprint.project_id},
    )
    return updated


@project_router.get("/{project_id}/backlog", response_model=list[Issue])
def get_backlog(
    project_id: str,
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> list[Issue]:
    ensure_project_access(store, current_user, project_id)
    return [issue for issue in store.list_issues(project_id=project_id) if issue.sprint_id is None]
