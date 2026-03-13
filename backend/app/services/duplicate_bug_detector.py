from __future__ import annotations

from collections import Counter
from math import sqrt
from re import findall

from app.db.store import BaseStore
from app.models.schemas import DuplicateMatch, Issue


def _tokenize(text: str) -> list[str]:
    return [token for token in findall(r"[a-z0-9_]+", text.lower()) if len(token) > 1]


def _vectorize(text: str) -> Counter[str]:
    return Counter(_tokenize(text))


def _cosine_similarity(left: Counter[str], right: Counter[str]) -> float:
    if not left or not right:
        return 0.0
    numerator = sum(value * right.get(term, 0) for term, value in left.items())
    left_norm = sqrt(sum(value * value for value in left.values()))
    right_norm = sqrt(sum(value * value for value in right.values()))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


def _issue_text(issue: Issue) -> str:
    return f"{issue.title} {issue.description}"


def find_duplicate_issues(
    store: BaseStore,
    *,
    title: str,
    description: str,
    project_id: str | None = None,
    threshold: float = 0.35,
    limit: int = 5,
) -> list[DuplicateMatch]:
    needle_vec = _vectorize(f"{title} {description}")
    issues = store.list_issues(project_id=project_id)
    scored: list[DuplicateMatch] = []
    for issue in issues:
        similarity = _cosine_similarity(needle_vec, _vectorize(_issue_text(issue)))
        if similarity < threshold:
            continue
        if not issue.issue_key:
            continue
        scored.append(DuplicateMatch(issueKey=issue.issue_key, similarity=round(float(similarity), 3)))
    scored.sort(key=lambda item: item.similarity, reverse=True)
    return scored[:limit]
