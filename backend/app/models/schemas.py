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
    project_manager = "project_manager"
    developer = "developer"
    tester = "tester"


class IssueType(str, Enum):
    bug = "bug"
    task = "task"
    story = "story"
    epic = "epic"


class IssuePriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class IssueStatus(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


class SprintStatus(str, Enum):
    planned = "planned"
    active = "active"
    closed = "closed"


class NotificationType(str, Enum):
    assignment = "assignment"
    comment = "comment"
    status_change = "status_change"


class IssueLinkType(str, Enum):
    blocks = "blocks"
    blocked_by = "blocked_by"
    relates_to = "relates_to"
    duplicates = "duplicates"


class UserProfile(BaseModel):
    title: str | None = None
    team: str | None = None
    avatar_url: str | None = None
    bio: str | None = Field(default=None, max_length=1000)


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserUpdateProfile(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    title: str | None = Field(default=None, max_length=120)
    team: str | None = Field(default=None, max_length=120)
    avatar_url: str | None = None
    bio: str | None = Field(default=None, max_length=1000)


class UserRoleUpdate(BaseModel):
    role: UserRole


class UserInDB(BaseModel):
    id: str = Field(default_factory=new_id)
    name: str
    email: EmailStr
    role: UserRole = UserRole.tester
    profile: UserProfile = Field(default_factory=UserProfile)
    password_hash: str
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)
    last_login_at: datetime | None = None


class UserPublic(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: UserRole
    profile: UserProfile
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class ProjectMember(BaseModel):
    user_id: str
    role: UserRole
    joined_at: datetime = Field(default_factory=now_utc)


class ProjectCreate(BaseModel):
    key: str = Field(min_length=2, max_length=10, pattern=r"^[A-Z][A-Z0-9]+$")
    name: str = Field(min_length=3, max_length=120)
    description: str = Field(default="", max_length=1500)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=120)
    description: str | None = Field(default=None, max_length=1500)


class ProjectAssignMember(BaseModel):
    user_id: str
    role: UserRole = UserRole.developer


class Project(BaseModel):
    id: str = Field(default_factory=new_id)
    key: str
    name: str
    description: str = ""
    created_by: str
    members: list[ProjectMember] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class Attachment(BaseModel):
    id: str = Field(default_factory=new_id)
    filename: str
    content_type: str
    blob_url: str
    uploaded_by: str
    uploaded_at: datetime = Field(default_factory=now_utc)


class IssueHistoryItem(BaseModel):
    at: datetime = Field(default_factory=now_utc)
    by: str
    action: str
    field: str | None = None
    old_value: str | None = None
    new_value: str | None = None


class IssueCreate(BaseModel):
    project_id: str
    title: str = Field(min_length=3, max_length=160)
    description: str = Field(min_length=5, max_length=6000)
    issue_type: IssueType = IssueType.task
    priority: IssuePriority = IssuePriority.medium
    assignee_id: str | None = None
    labels: list[str] = Field(default_factory=list, max_length=30)


class IssueUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=160)
    description: str | None = Field(default=None, min_length=5, max_length=6000)
    issue_type: IssueType | None = None
    priority: IssuePriority | None = None
    status: IssueStatus | None = None
    assignee_id: str | None = None
    labels: list[str] | None = Field(default=None, max_length=30)
    sprint_id: str | None = None
    backlog_order: float | None = None


class Issue(BaseModel):
    id: str = Field(default_factory=new_id)
    issue_key: str | None = None
    project_id: str
    title: str
    description: str
    issue_type: IssueType
    priority: IssuePriority
    status: IssueStatus = IssueStatus.todo
    reporter_id: str
    assignee_id: str | None = None
    sprint_id: str | None = None
    backlog_order: float = 0
    labels: list[str] = Field(default_factory=list)
    attachments: list[Attachment] = Field(default_factory=list)
    history: list[IssueHistoryItem] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class IssueMoveToSprint(BaseModel):
    sprint_id: str | None = None
    backlog_order: float = 0


class BacklogReorderItem(BaseModel):
    issue_id: str
    backlog_order: float


class BacklogReorderRequest(BaseModel):
    items: list[BacklogReorderItem]


class CommentCreate(BaseModel):
    issue_id: str
    body: str = Field(min_length=1, max_length=4000)
    parent_id: str | None = None


class CommentUpdate(BaseModel):
    body: str = Field(min_length=1, max_length=4000)


class Comment(BaseModel):
    id: str = Field(default_factory=new_id)
    issue_id: str
    author_id: str
    parent_id: str | None = None
    body: str
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)
    deleted: bool = False


class IssueActivity(BaseModel):
    id: str = Field(default_factory=new_id)
    issue_id: str
    user_id: str
    action: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=now_utc)


class SprintCreate(BaseModel):
    project_id: str
    name: str = Field(min_length=2, max_length=120)
    goal: str = Field(default="", max_length=1500)
    start_date: datetime | None = None
    end_date: datetime | None = None


class SprintUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    goal: str | None = Field(default=None, max_length=1500)
    start_date: datetime | None = None
    end_date: datetime | None = None


class Sprint(BaseModel):
    id: str = Field(default_factory=new_id)
    project_id: str
    name: str
    goal: str = ""
    status: SprintStatus = SprintStatus.planned
    start_date: datetime | None = None
    end_date: datetime | None = None
    created_by: str
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class Notification(BaseModel):
    id: str = Field(default_factory=new_id)
    user_id: str
    type: NotificationType
    title: str
    message: str
    issue_id: str | None = None
    project_id: str | None = None
    created_at: datetime = Field(default_factory=now_utc)
    read: bool = False


class IssueLinkCreate(BaseModel):
    target_issue_id: str
    link_type: IssueLinkType = IssueLinkType.relates_to


class IssueLink(BaseModel):
    id: str = Field(default_factory=new_id)
    source_issue_id: str
    target_issue_id: str
    link_type: IssueLinkType
    created_by: str
    created_at: datetime = Field(default_factory=now_utc)


class AuditLog(BaseModel):
    id: str = Field(default_factory=new_id)
    actor_id: str
    action: str
    entity_type: str
    entity_id: str
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=now_utc)


class DashboardStats(BaseModel):
    total_issues: int = 0
    todo_issues: int = 0
    in_progress_issues: int = 0
    done_issues: int = 0
    low_priority: int = 0
    medium_priority: int = 0
    high_priority: int = 0
    critical_priority: int = 0
    assigned_to_me: int = 0
    status_breakdown: dict[str, int] = Field(default_factory=dict)
    priority_breakdown: dict[str, int] = Field(default_factory=dict)
    recent_activity: list[AuditLog] = Field(default_factory=list)
