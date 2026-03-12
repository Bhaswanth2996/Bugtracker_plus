from app.db.store import BaseStore
from app.models.schemas import AuditLog, UserInDB


def log_action(
    store: BaseStore,
    *,
    actor: UserInDB,
    action: str,
    entity_type: str,
    entity_id: str,
    details: dict | None = None,
) -> AuditLog:
    log = AuditLog(
        actor_id=actor.id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details or {},
    )
    return store.create_audit_log(log)
