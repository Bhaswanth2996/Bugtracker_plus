from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, EmailStr, Field


def now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


def new_id() -> str:
    return str(uuid4())


class UserRole(str, Enum):
    admin = "admin"
    manager = "manager"
    developer = "developer"
    tester = "tester"


class IssueStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


class IssuePriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class UserBase(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    role: UserRole = UserRole.tester


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserInDB(UserBase):
    id: str = Field(default_factory=new_id)
    password_hash: str
    created_at: datetime = Field(default_factory=now_utc)


class UserPublic(UserBase):
    id: str
    created_at: datetime


class UserRoleUpdate(BaseModel):
    role: UserRole


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class ProjectBase(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    description: str = Field(default="", max_length=1000)


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=100)
    description: str | None = Field(default=None, max_length=1000)


class Project(ProjectBase):
    id: str = Field(default_factory=new_id)
    created_by: str
    created_at: datetime = Field(default_factory=now_utc)


class IssueHistoryItem(BaseModel):
    at: datetime = Field(default_factory=now_utc)
    by: str
    field: str
    old_value: str | None = None
    new_value: str | None = None


class IssueBase(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=5, max_length=5000)
    priority: IssuePriority = IssuePriority.medium
    tags: list[str] = Field(default_factory=list, max_length=20)


class IssueCreate(IssueBase):
    project_id: str
    assignee_id: str | None = None


class IssueUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=150)
    description: str | None = Field(default=None, min_length=5, max_length=5000)
    priority: IssuePriority | None = None
    status: IssueStatus | None = None
    assignee_id: str | None = None
    tags: list[str] | None = Field(default=None, max_length=20)


class Issue(IssueBase):
    id: str = Field(default_factory=new_id)
    project_id: str
    reporter_id: str
    assignee_id: str | None = None
    status: IssueStatus = IssueStatus.open
    history: list[IssueHistoryItem] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class CommentCreate(BaseModel):
    issue_id: str
    body: str = Field(min_length=1, max_length=2000)


class Comment(BaseModel):
    id: str = Field(default_factory=new_id)
    issue_id: str
    author_id: str
    body: str = Field(min_length=1, max_length=2000)
    created_at: datetime = Field(default_factory=now_utc)


class AuditLog(BaseModel):
    id: str = Field(default_factory=new_id)
    actor_id: str
    action: str = Field(min_length=2, max_length=100)
    entity_type: str = Field(min_length=2, max_length=60)
    entity_id: str
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=now_utc)


class DashboardStats(BaseModel):
    total_issues: int = 0
    open_issues: int = 0
    in_progress_issues: int = 0
    resolved_issues: int = 0
    closed_issues: int = 0
    critical_issues: int = 0
