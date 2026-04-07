from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import get_current_user, get_store
from app.db.store import BaseStore
from app.models.schemas import Notification, UserInDB

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[Notification])
def list_notifications(
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> list[Notification]:
    return store.list_notifications(current_user.id)


@router.put("/{notification_id}/read", response_model=Notification)
def mark_notification_read(
    notification_id: str,
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> Notification:
    notification = store.mark_notification_read(notification_id, current_user.id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found.")
    return notification
