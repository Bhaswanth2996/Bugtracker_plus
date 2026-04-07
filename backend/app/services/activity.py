from app.db.store import BaseStore
from app.models.schemas import IssueActivity, UserInDB


def log_issue_activity(
    store: BaseStore,
    *,
    issue_id: str,
    actor: UserInDB,
    action: str,
    metadata: dict | None = None,
) -> IssueActivity:
    item = IssueActivity(
        issue_id=issue_id,
        user_id=actor.id,
        action=action,
        metadata=metadata or {},
    )
    return store.create_issue_activity(item)
