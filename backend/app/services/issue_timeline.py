from __future__ import annotations

from typing import Any

from app.db.store import BaseStore
from app.models.schemas import IssueTimelineEvent


def _stringify(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return str(value)


def record_issue_timeline(
    store: BaseStore,
    *,
    issue_id: str,
    action: str,
    user_id: str,
    user_name: str | None = None,
    old_value: Any = None,
    new_value: Any = None,
    project_id: str | None = None,
) -> IssueTimelineEvent:
    event = IssueTimelineEvent(
        issue_id=issue_id,
        project_id=project_id,
        action=action,
        old_value=_stringify(old_value),
        new_value=_stringify(new_value),
        user_id=user_id,
        user_name=user_name,
    )
    return store.create_issue_timeline_event(event)
