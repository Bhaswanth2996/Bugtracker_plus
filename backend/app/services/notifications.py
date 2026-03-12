from app.db.store import BaseStore
from app.models.schemas import Notification, NotificationType


def notify_user(
    store: BaseStore,
    *,
    user_id: str,
    type: NotificationType,
    title: str,
    message: str,
    issue_id: str | None = None,
    project_id: str | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        type=type,
        title=title,
        message=message,
        issue_id=issue_id,
        project_id=project_id,
    )
    return store.create_notification(notification)
