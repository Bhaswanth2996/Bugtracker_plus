from fastapi import APIRouter, Depends

from app.core.deps import get_current_user, get_store
from app.db.store import BaseStore
from app.models.schemas import DashboardStats, UserInDB
from app.services.permissions import ensure_project_access

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
project_router = APIRouter(prefix="/projects", tags=["dashboard"])


@router.get("", response_model=DashboardStats)
def get_global_dashboard_stats(
    _: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> DashboardStats:
    return store.get_dashboard_stats()


@project_router.get("/{project_id}/dashboard", response_model=DashboardStats)
def get_project_dashboard_stats(
    project_id: str,
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> DashboardStats:
    ensure_project_access(store, current_user, project_id)
    return store.get_dashboard_stats(project_id=project_id)
