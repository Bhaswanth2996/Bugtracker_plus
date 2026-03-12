from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_user, get_store
from app.db.store import BaseStore
from app.models.schemas import Comment, CommentCreate, UserInDB
from app.services.audit import log_action

router = APIRouter(prefix="/api/comments", tags=["comments"])


@router.post("", response_model=Comment, status_code=status.HTTP_201_CREATED)
def create_comment(
    payload: CommentCreate,
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> Comment:
    if not store.get_issue(payload.issue_id):
        raise HTTPException(status_code=404, detail="Issue not found.")
    comment = Comment(
        issue_id=payload.issue_id,
        author_id=current_user.id,
        body=payload.body,
    )
    created = store.create_comment(comment)
    log_action(
        store,
        actor=current_user,
        action="comment.created",
        entity_type="comment",
        entity_id=created.id,
        details={"issue_id": created.issue_id},
    )
    return created


@router.get("/issue/{issue_id}", response_model=list[Comment])
def list_comments(
    issue_id: str,
    _: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> list[Comment]:
    if not store.get_issue(issue_id):
        raise HTTPException(status_code=404, detail="Issue not found.")
    return store.list_comments(issue_id)
