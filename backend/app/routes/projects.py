from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_user, get_store, require_roles
from app.db.store import BaseStore
from app.models.schemas import Project, ProjectAssignMember, ProjectCreate, ProjectMember, ProjectUpdate, UserInDB, UserRole
from app.services.audit import log_action
from app.services.permissions import ensure_project_access

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=Project, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    current_user: UserInDB = Depends(require_roles({UserRole.admin, UserRole.project_manager})),
    store: BaseStore = Depends(get_store),
) -> Project:
    if store.get_project_by_key(payload.key):
        raise HTTPException(status_code=409, detail="Project key already exists.")
    project = Project(
        key=payload.key,
        name=payload.name,
        description=payload.description,
        created_by=current_user.id,
        members=[ProjectMember(user_id=current_user.id, role=current_user.role)],
    )
    created = store.create_project(project)
    log_action(
        store,
        actor=current_user,
        action="project.created",
        entity_type="project",
        entity_id=created.id,
        details={"project_id": created.id, "key": created.key},
    )
    return created


@router.get("", response_model=list[Project])
def list_projects(
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> list[Project]:
    projects = store.list_projects()
    if current_user.role == UserRole.admin:
        return projects
    allowed = []
    for project in projects:
        if project.created_by == current_user.id or any(member.user_id == current_user.id for member in project.members):
            allowed.append(project)
    return allowed


@router.get("/key/{project_key}", response_model=Project)
def get_project_by_key(
    project_key: str,
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> Project:
    project = store.get_project_by_key(project_key)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    return ensure_project_access(store, current_user, project.id)


@router.get("/{project_id}", response_model=Project)
def get_project(
    project_id: str,
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> Project:
    return ensure_project_access(store, current_user, project_id)


@router.put("/{project_id}", response_model=Project)
def update_project(
    project_id: str,
    payload: ProjectUpdate,
    current_user: UserInDB = Depends(require_roles({UserRole.admin, UserRole.project_manager})),
    store: BaseStore = Depends(get_store),
) -> Project:
    project = ensure_project_access(store, current_user, project_id)
    updates = payload.model_dump(exclude_none=True)
    for field_name, value in updates.items():
        setattr(project, field_name, value)
    project.updated_at = datetime.now(tz=timezone.utc)
    updated = store.update_project(project)
    log_action(
        store,
        actor=current_user,
        action="project.updated",
        entity_type="project",
        entity_id=project_id,
        details={"project_id": project_id, **updates},
    )
    return updated


@router.post("/{project_id}/members", response_model=Project)
def add_project_member(
    project_id: str,
    payload: ProjectAssignMember,
    current_user: UserInDB = Depends(require_roles({UserRole.admin, UserRole.project_manager})),
    store: BaseStore = Depends(get_store),
) -> Project:
    ensure_project_access(store, current_user, project_id)
    if not store.get_user_by_id(payload.user_id):
        raise HTTPException(status_code=404, detail="User not found.")
    updated = store.add_project_member(project_id, ProjectMember(user_id=payload.user_id, role=payload.role))
    if not updated:
        raise HTTPException(status_code=404, detail="Project not found.")
    log_action(
        store,
        actor=current_user,
        action="project.member.assigned",
        entity_type="project",
        entity_id=project_id,
        details={"project_id": project_id, "user_id": payload.user_id, "role": payload.role.value},
    )
    return updated
