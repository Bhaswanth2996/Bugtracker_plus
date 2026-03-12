from fastapi import APIRouter, Depends, Query

from app.core.deps import get_store, require_roles
from app.db.store import BaseStore
from app.models.schemas import AuditLog, UserInDB, UserRole

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("", response_model=list[AuditLog])
def list_audit_logs(
    limit: int = Query(default=100, ge=1, le=500),
    _: UserInDB = Depends(require_roles({UserRole.admin, UserRole.manager})),
    store: BaseStore = Depends(get_store),
) -> list[AuditLog]:
    return store.list_audit_logs(limit=limit)
