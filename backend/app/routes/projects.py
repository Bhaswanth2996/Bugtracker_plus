from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_store, require_roles
from app.db.store import BaseStore
from app.models.schemas import (
    Project,
    ProjectCreate,
    ProjectUpdate,
    UserInDB,
    UserRole,
)
from app.services.audit import log_action

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("", response_model=Project, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    current_user: UserInDB = Depends(require_roles({UserRole.admin, UserRole.manager})),
    store: BaseStore = Depends(get_store),
) -> Project:
    project = Project(
        name=payload.name,
        description=payload.description,
        created_by=current_user.id,
    )
    created = store.create_project(project)
    log_action(
        store,
        actor=current_user,
        action="project.created",
        entity_type="project",
        entity_id=created.id,
        details={"name": created.name},
    )
    return created


@router.get("", response_model=list[Project])
def list_projects(
    _: UserInDB = Depends(require_roles({UserRole.admin, UserRole.manager, UserRole.developer, UserRole.tester})),
    store: BaseStore = Depends(get_store),
) -> list[Project]:
    return store.list_projects()


@router.patch("/{project_id}", response_model=Project)
def update_project(
    project_id: str,
    payload: ProjectUpdate,
    current_user: UserInDB = Depends(require_roles({UserRole.admin, UserRole.manager})),
    store: BaseStore = Depends(get_store),
) -> Project:
    updated = store.update_project(
        project_id,
        name=payload.name,
        description=payload.description,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Project not found.")

    log_action(
        store,
        actor=current_user,
        action="project.updated",
        entity_type="project",
        entity_id=project_id,
        details=payload.model_dump(exclude_none=True),
    )
    return updated
