from fastapi import HTTPException

from app.db.store import BaseStore
from app.models.schemas import Project, UserInDB, UserRole


def can_manage_project(user: UserInDB) -> bool:
    return user.role in {UserRole.admin, UserRole.project_manager}


def can_admin_platform(user: UserInDB) -> bool:
    return user.role == UserRole.admin


def ensure_project_access(store: BaseStore, user: UserInDB, project_id: str) -> Project:
    project = store.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    if user.role == UserRole.admin:
        return project
    if project.created_by == user.id:
        return project
    if any(member.user_id == user.id for member in project.members):
        return project
    raise HTTPException(status_code=403, detail="User is not a member of this project.")
