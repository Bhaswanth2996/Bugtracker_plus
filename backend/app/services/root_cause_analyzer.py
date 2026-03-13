from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha1

from app.db.store import BaseStore
from app.models.schemas import RootCauseAnalysis

MODULE_FILE_MAP: dict[str, list[str]] = {
    "auth": ["auth/token_service.py", "auth/session_manager.py"],
    "payment": ["payments/payment_api.py", "payments/processor.py"],
    "profile": ["users/profile_service.py", "users/preferences.py"],
    "notification": ["notifications/dispatcher.py", "notifications/channels/email.py"],
}


def _infer_module(issue_text: str, explicit_module: str | None) -> str:
    if explicit_module:
        return explicit_module
    lowered = issue_text.lower()
    for key in MODULE_FILE_MAP:
        if key in lowered:
            return key
    return "core"


def analyze_root_cause(store: BaseStore, *, issue_id: str, refresh: bool = False) -> RootCauseAnalysis:
    if not refresh:
        cached = store.get_root_cause_analysis(issue_id)
        if cached:
            return cached

    issue = store.get_issue(issue_id)
    if not issue:
        raise ValueError("Issue not found.")

    module = _infer_module(f"{issue.title} {issue.description}", issue.module)
    related_files = MODULE_FILE_MAP.get(module.lower(), [f"{module}/module.py"])
    digest = sha1(f"{issue.id}:{issue.updated_at.isoformat()}".encode("utf-8")).hexdigest()
    suspected_commit = digest[:7]

    author_name = "System"
    if issue.assignee_id:
        assignee = store.get_user_by_id(issue.assignee_id)
        if assignee:
            author_name = assignee.name
    elif issue.reporter_id:
        reporter = store.get_user_by_id(issue.reporter_id)
        if reporter:
            author_name = reporter.name

    recency_boost = min(
        max((datetime.now(tz=timezone.utc) - issue.updated_at).total_seconds() / 86400.0, 0.0),
        30.0,
    )
    confidence = max(0.35, min(0.96, 0.85 - (recency_boost * 0.01)))

    analysis = RootCauseAnalysis(
        issue_id=issue.id,
        suspected_commit=suspected_commit,
        author=author_name,
        files_modified=related_files,
        confidence=round(float(confidence), 2),
    )
    return store.upsert_root_cause_analysis(analysis)
