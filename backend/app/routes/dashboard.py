from fastapi import APIRouter, Depends

from app.core.deps import get_current_user, get_store
from app.db.store import BaseStore
from app.models.schemas import DashboardStats, UserInDB

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    _: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> DashboardStats:
    return store.get_dashboard_stats()
