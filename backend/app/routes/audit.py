from fastapi import APIRouter, Depends, Query

from app.core.deps import get_store, require_roles
from app.db.store import BaseStore
from app.models.schemas import AuditLog, UserInDB, UserRole

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=list[AuditLog])
def list_audit_logs(
    project_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    _: UserInDB = Depends(require_roles({UserRole.admin, UserRole.project_manager})),
    store: BaseStore = Depends(get_store),
) -> list[AuditLog]:
    return store.list_audit_logs(project_id=project_id, limit=limit)
