from __future__ import annotations

from abc import ABC, abstractmethod
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from app.models.schemas import (
    AuditLog,
    Comment,
    DashboardStats,
    Issue,
    IssuePriority,
    IssueStatus,
    Notification,
    Project,
    ProjectMember,
    Sprint,
    SprintStatus,
    UserInDB,
    UserProfile,
    UserRole,
)


class BaseStore(ABC):
    @abstractmethod
    def user_count(self) -> int: ...

    @abstractmethod
    def create_user(self, user: UserInDB) -> UserInDB: ...

    @abstractmethod
    def get_user_by_email(self, email: str) -> UserInDB | None: ...

    @abstractmethod
    def get_user_by_id(self, user_id: str) -> UserInDB | None: ...

    @abstractmethod
    def list_users(self) -> list[UserInDB]: ...

    @abstractmethod
    def update_user_role(self, user_id: str, role: UserRole) -> UserInDB | None: ...

    @abstractmethod
    def update_user_profile(self, user_id: str, profile_updates: dict[str, Any], name: str | None = None) -> UserInDB | None: ...

    @abstractmethod
    def update_user_last_login(self, user_id: str) -> None: ...

    @abstractmethod
    def create_project(self, project: Project) -> Project: ...

    @abstractmethod
    def list_projects(self) -> list[Project]: ...

    @abstractmethod
    def get_project(self, project_id: str) -> Project | None: ...

    @abstractmethod
    def get_project_by_key(self, key: str) -> Project | None: ...

    @abstractmethod
    def update_project(self, project: Project) -> Project: ...

    @abstractmethod
    def add_project_member(self, project_id: str, member: ProjectMember) -> Project | None: ...

    @abstractmethod
    def create_issue(self, issue: Issue) -> Issue: ...

    @abstractmethod
    def get_issue(self, issue_id: str) -> Issue | None: ...

    @abstractmethod
    def list_issues(
        self,
        *,
        project_id: str | None = None,
        status: IssueStatus | None = None,
        priority: IssuePriority | None = None,
        assignee_id: str | None = None,
        sprint_id: str | None = None,
        search: str | None = None,
    ) -> list[Issue]: ...

    @abstractmethod
    def update_issue(self, issue: Issue) -> Issue: ...

    @abstractmethod
    def delete_issue(self, issue_id: str) -> bool: ...

    @abstractmethod
    def create_comment(self, comment: Comment) -> Comment: ...

    @abstractmethod
    def list_comments(self, issue_id: str) -> list[Comment]: ...

    @abstractmethod
    def get_comment(self, comment_id: str) -> Comment | None: ...

    @abstractmethod
    def update_comment(self, comment: Comment) -> Comment: ...

    @abstractmethod
    def create_sprint(self, sprint: Sprint) -> Sprint: ...

    @abstractmethod
    def list_sprints(self, project_id: str | None = None) -> list[Sprint]: ...

    @abstractmethod
    def get_sprint(self, sprint_id: str) -> Sprint | None: ...

    @abstractmethod
    def update_sprint(self, sprint: Sprint) -> Sprint: ...

    @abstractmethod
    def create_notification(self, notification: Notification) -> Notification: ...

    @abstractmethod
    def list_notifications(self, user_id: str) -> list[Notification]: ...

    @abstractmethod
    def mark_notification_read(self, notification_id: str, user_id: str) -> Notification | None: ...

    @abstractmethod
    def create_audit_log(self, log: AuditLog) -> AuditLog: ...

    @abstractmethod
    def list_audit_logs(self, *, project_id: str | None = None, limit: int = 100) -> list[AuditLog]: ...

    @abstractmethod
    def get_dashboard_stats(self, project_id: str | None = None) -> DashboardStats: ...


class InMemoryStore(BaseStore):
    def __init__(self) -> None:
        self.users: dict[str, UserInDB] = {}
        self.projects: dict[str, Project] = {}
        self.issues: dict[str, Issue] = {}
        self.comments: dict[str, Comment] = {}
        self.sprints: dict[str, Sprint] = {}
        self.notifications: dict[str, Notification] = {}
        self.audit_logs: dict[str, AuditLog] = {}

    def user_count(self) -> int:
        return len(self.users)

    def create_user(self, user: UserInDB) -> UserInDB:
        self.users[user.id] = deepcopy(user)
        return deepcopy(user)

    def get_user_by_email(self, email: str) -> UserInDB | None:
        needle = email.lower()
        for user in self.users.values():
            if user.email.lower() == needle:
                return deepcopy(user)
        return None

    def get_user_by_id(self, user_id: str) -> UserInDB | None:
        value = self.users.get(user_id)
        return deepcopy(value) if value else None

    def list_users(self) -> list[UserInDB]:
        return [deepcopy(value) for value in self.users.values()]

    def update_user_role(self, user_id: str, role: UserRole) -> UserInDB | None:
        user = self.users.get(user_id)
        if not user:
            return None
        user.role = role
        user.updated_at = datetime.now(tz=timezone.utc)
        return deepcopy(user)

    def update_user_profile(self, user_id: str, profile_updates: dict[str, Any], name: str | None = None) -> UserInDB | None:
        user = self.users.get(user_id)
        if not user:
            return None
        profile = user.profile.model_dump()
        profile.update(profile_updates)
        user.profile = UserProfile.model_validate(profile)
        if name is not None:
            user.name = name
        user.updated_at = datetime.now(tz=timezone.utc)
        return deepcopy(user)

    def update_user_last_login(self, user_id: str) -> None:
        user = self.users.get(user_id)
        if user:
            now = datetime.now(tz=timezone.utc)
            user.last_login_at = now
            user.updated_at = now

    def create_project(self, project: Project) -> Project:
        self.projects[project.id] = deepcopy(project)
        return deepcopy(project)

    def list_projects(self) -> list[Project]:
        return [deepcopy(value) for value in self.projects.values()]

    def get_project(self, project_id: str) -> Project | None:
        value = self.projects.get(project_id)
        return deepcopy(value) if value else None

    def get_project_by_key(self, key: str) -> Project | None:
        for project in self.projects.values():
            if project.key == key:
                return deepcopy(project)
        return None

    def update_project(self, project: Project) -> Project:
        self.projects[project.id] = deepcopy(project)
        return deepcopy(project)

    def add_project_member(self, project_id: str, member: ProjectMember) -> Project | None:
        project = self.projects.get(project_id)
        if not project:
            return None
        for existing in project.members:
            if existing.user_id == member.user_id:
                existing.role = member.role
                break
        else:
            project.members.append(member)
        project.updated_at = datetime.now(tz=timezone.utc)
        return deepcopy(project)

    def create_issue(self, issue: Issue) -> Issue:
        self.issues[issue.id] = deepcopy(issue)
        return deepcopy(issue)

    def get_issue(self, issue_id: str) -> Issue | None:
        value = self.issues.get(issue_id)
        return deepcopy(value) if value else None

    def list_issues(
        self,
        *,
        project_id: str | None = None,
        status: IssueStatus | None = None,
        priority: IssuePriority | None = None,
        assignee_id: str | None = None,
        sprint_id: str | None = None,
        search: str | None = None,
    ) -> list[Issue]:
        result: list[Issue] = []
        needle = (search or "").lower().strip()
        for issue in self.issues.values():
            if project_id and issue.project_id != project_id:
                continue
            if status and issue.status != status:
                continue
            if priority and issue.priority != priority:
                continue
            if assignee_id and issue.assignee_id != assignee_id:
                continue
            if sprint_id is not None and issue.sprint_id != sprint_id:
                continue
            if needle and needle not in f"{issue.title} {issue.description}".lower():
                continue
            result.append(deepcopy(issue))
        return sorted(result, key=lambda item: (item.backlog_order, item.created_at))

    def update_issue(self, issue: Issue) -> Issue:
        self.issues[issue.id] = deepcopy(issue)
        return deepcopy(issue)

    def delete_issue(self, issue_id: str) -> bool:
        if issue_id not in self.issues:
            return False
        del self.issues[issue_id]
        return True

    def create_comment(self, comment: Comment) -> Comment:
        self.comments[comment.id] = deepcopy(comment)
        return deepcopy(comment)

    def list_comments(self, issue_id: str) -> list[Comment]:
        values = [deepcopy(item) for item in self.comments.values() if item.issue_id == issue_id]
        return sorted(values, key=lambda item: item.created_at)

    def get_comment(self, comment_id: str) -> Comment | None:
        value = self.comments.get(comment_id)
        return deepcopy(value) if value else None

    def update_comment(self, comment: Comment) -> Comment:
        self.comments[comment.id] = deepcopy(comment)
        return deepcopy(comment)

    def create_sprint(self, sprint: Sprint) -> Sprint:
        self.sprints[sprint.id] = deepcopy(sprint)
        return deepcopy(sprint)

    def list_sprints(self, project_id: str | None = None) -> list[Sprint]:
        items = list(self.sprints.values())
        if project_id:
            items = [item for item in items if item.project_id == project_id]
        return sorted([deepcopy(item) for item in items], key=lambda item: item.created_at, reverse=True)

    def get_sprint(self, sprint_id: str) -> Sprint | None:
        value = self.sprints.get(sprint_id)
        return deepcopy(value) if value else None

    def update_sprint(self, sprint: Sprint) -> Sprint:
        self.sprints[sprint.id] = deepcopy(sprint)
        return deepcopy(sprint)

    def create_notification(self, notification: Notification) -> Notification:
        self.notifications[notification.id] = deepcopy(notification)
        return deepcopy(notification)

    def list_notifications(self, user_id: str) -> list[Notification]:
        values = [deepcopy(item) for item in self.notifications.values() if item.user_id == user_id]
        return sorted(values, key=lambda item: item.created_at, reverse=True)

    def mark_notification_read(self, notification_id: str, user_id: str) -> Notification | None:
        notification = self.notifications.get(notification_id)
        if not notification or notification.user_id != user_id:
            return None
        notification.read = True
        return deepcopy(notification)

    def create_audit_log(self, log: AuditLog) -> AuditLog:
        self.audit_logs[log.id] = deepcopy(log)
        return deepcopy(log)

    def list_audit_logs(self, *, project_id: str | None = None, limit: int = 100) -> list[AuditLog]:
        logs = list(self.audit_logs.values())
        if project_id:
            logs = [log for log in logs if log.details.get("project_id") == project_id]
        return sorted([deepcopy(item) for item in logs], key=lambda item: item.timestamp, reverse=True)[:limit]

    def get_dashboard_stats(self, project_id: str | None = None) -> DashboardStats:
        issues = list(self.issues.values())
        if project_id:
            issues = [issue for issue in issues if issue.project_id == project_id]
        status_counts = Counter(issue.status.value for issue in issues)
        priority_counts = Counter(issue.priority.value for issue in issues)
        return DashboardStats(
            total_issues=len(issues),
            todo_issues=status_counts.get(IssueStatus.todo.value, 0),
            in_progress_issues=status_counts.get(IssueStatus.in_progress.value, 0),
            done_issues=status_counts.get(IssueStatus.done.value, 0),
            low_priority=priority_counts.get(IssuePriority.low.value, 0),
            medium_priority=priority_counts.get(IssuePriority.medium.value, 0),
            high_priority=priority_counts.get(IssuePriority.high.value, 0),
            critical_priority=priority_counts.get(IssuePriority.critical.value, 0),
            recent_activity=self.list_audit_logs(project_id=project_id, limit=12),
        )


class MongoStore(BaseStore):
    def __init__(self, uri: str, db_name: str) -> None:
        self.client: MongoClient = MongoClient(uri)
        self.db: Database = self.client[db_name]
        self.users_col: Collection = self.db["users"]
        self.projects_col: Collection = self.db["projects"]
        self.issues_col: Collection = self.db["issues"]
        self.comments_col: Collection = self.db["comments"]
        self.sprints_col: Collection = self.db["sprints"]
        self.notifications_col: Collection = self.db["notifications"]
        self.audit_col: Collection = self.db["audit_logs"]
        self._ensure_indexes()

    @staticmethod
    def _dump(model: Any) -> dict[str, Any]:
        payload = model.model_dump(mode="json")
        payload["_id"] = payload["id"]
        return payload

    @staticmethod
    def _dump_for_update(model: Any) -> dict[str, Any]:
        payload = model.model_dump(mode="json")
        payload.pop("id", None)
        return payload

    @staticmethod
    def _load(model_type, doc: dict | None):
        if not doc:
            return None
        row = dict(doc)
        row.pop("_id", None)
        return model_type.model_validate(row)

    def _ensure_indexes(self) -> None:
        self.users_col.create_index("email", unique=True)
        self.projects_col.create_index("key", unique=True)
        self.projects_col.create_index("members.user_id")
        self.issues_col.create_index("project_id")
        self.issues_col.create_index("status")
        self.issues_col.create_index("priority")
        self.issues_col.create_index("assignee_id")
        self.issues_col.create_index([("title", "text"), ("description", "text")])
        self.comments_col.create_index("issue_id")
        self.comments_col.create_index("parent_id")
        self.sprints_col.create_index("project_id")
        self.notifications_col.create_index("user_id")
        self.audit_col.create_index("timestamp")

    def user_count(self) -> int:
        return self.users_col.count_documents({})

    def create_user(self, user: UserInDB) -> UserInDB:
        self.users_col.insert_one(self._dump(user))
        return user

    def get_user_by_email(self, email: str) -> UserInDB | None:
        return self._load(UserInDB, self.users_col.find_one({"email": email}))

    def get_user_by_id(self, user_id: str) -> UserInDB | None:
        return self._load(UserInDB, self.users_col.find_one({"id": user_id}))

    def list_users(self) -> list[UserInDB]:
        return [self._load(UserInDB, row) for row in self.users_col.find({})]

    def update_user_role(self, user_id: str, role: UserRole) -> UserInDB | None:
        self.users_col.update_one(
            {"id": user_id},
            {"$set": {"role": role.value, "updated_at": datetime.now(tz=timezone.utc)}},
        )
        return self.get_user_by_id(user_id)

    def update_user_profile(self, user_id: str, profile_updates: dict[str, Any], name: str | None = None) -> UserInDB | None:
        updates: dict[str, Any] = {
            "updated_at": datetime.now(tz=timezone.utc),
        }
        if name is not None:
            updates["name"] = name
        for key, value in profile_updates.items():
            updates[f"profile.{key}"] = value
        self.users_col.update_one({"id": user_id}, {"$set": updates})
        return self.get_user_by_id(user_id)

    def update_user_last_login(self, user_id: str) -> None:
        now = datetime.now(tz=timezone.utc)
        self.users_col.update_one({"id": user_id}, {"$set": {"last_login_at": now, "updated_at": now}})

    def create_project(self, project: Project) -> Project:
        self.projects_col.insert_one(self._dump(project))
        return project

    def list_projects(self) -> list[Project]:
        return [self._load(Project, row) for row in self.projects_col.find({})]

    def get_project(self, project_id: str) -> Project | None:
        return self._load(Project, self.projects_col.find_one({"id": project_id}))

    def get_project_by_key(self, key: str) -> Project | None:
        return self._load(Project, self.projects_col.find_one({"key": key}))

    def update_project(self, project: Project) -> Project:
        self.projects_col.update_one({"id": project.id}, {"$set": self._dump_for_update(project)})
        return project

    def add_project_member(self, project_id: str, member: ProjectMember) -> Project | None:
        project = self.get_project(project_id)
        if not project:
            return None
        for existing in project.members:
            if existing.user_id == member.user_id:
                existing.role = member.role
                break
        else:
            project.members.append(member)
        project.updated_at = datetime.now(tz=timezone.utc)
        return self.update_project(project)

    def create_issue(self, issue: Issue) -> Issue:
        self.issues_col.insert_one(self._dump(issue))
        return issue

    def get_issue(self, issue_id: str) -> Issue | None:
        return self._load(Issue, self.issues_col.find_one({"id": issue_id}))

    def list_issues(
        self,
        *,
        project_id: str | None = None,
        status: IssueStatus | None = None,
        priority: IssuePriority | None = None,
        assignee_id: str | None = None,
        sprint_id: str | None = None,
        search: str | None = None,
    ) -> list[Issue]:
        query: dict[str, Any] = {}
        if project_id:
            query["project_id"] = project_id
        if status:
            query["status"] = status.value
        if priority:
            query["priority"] = priority.value
        if assignee_id:
            query["assignee_id"] = assignee_id
        if sprint_id is not None:
            query["sprint_id"] = sprint_id
        if search:
            query["$text"] = {"$search": search}
        cursor = self.issues_col.find(query).sort([("backlog_order", 1), ("created_at", 1)])
        return [self._load(Issue, row) for row in cursor]

    def update_issue(self, issue: Issue) -> Issue:
        self.issues_col.update_one({"id": issue.id}, {"$set": self._dump_for_update(issue)})
        return issue

    def delete_issue(self, issue_id: str) -> bool:
        result = self.issues_col.delete_one({"id": issue_id})
        return result.deleted_count > 0

    def create_comment(self, comment: Comment) -> Comment:
        self.comments_col.insert_one(self._dump(comment))
        return comment

    def list_comments(self, issue_id: str) -> list[Comment]:
        cursor = self.comments_col.find({"issue_id": issue_id}).sort("created_at", 1)
        return [self._load(Comment, row) for row in cursor]

    def get_comment(self, comment_id: str) -> Comment | None:
        return self._load(Comment, self.comments_col.find_one({"id": comment_id}))

    def update_comment(self, comment: Comment) -> Comment:
        self.comments_col.update_one({"id": comment.id}, {"$set": self._dump_for_update(comment)})
        return comment

    def create_sprint(self, sprint: Sprint) -> Sprint:
        self.sprints_col.insert_one(self._dump(sprint))
        return sprint

    def list_sprints(self, project_id: str | None = None) -> list[Sprint]:
        query = {"project_id": project_id} if project_id else {}
        cursor = self.sprints_col.find(query).sort("created_at", -1)
        return [self._load(Sprint, row) for row in cursor]

    def get_sprint(self, sprint_id: str) -> Sprint | None:
        return self._load(Sprint, self.sprints_col.find_one({"id": sprint_id}))

    def update_sprint(self, sprint: Sprint) -> Sprint:
        self.sprints_col.update_one({"id": sprint.id}, {"$set": self._dump_for_update(sprint)})
        return sprint

    def create_notification(self, notification: Notification) -> Notification:
        self.notifications_col.insert_one(self._dump(notification))
        return notification

    def list_notifications(self, user_id: str) -> list[Notification]:
        cursor = self.notifications_col.find({"user_id": user_id}).sort("created_at", -1)
        return [self._load(Notification, row) for row in cursor]

    def mark_notification_read(self, notification_id: str, user_id: str) -> Notification | None:
        self.notifications_col.update_one({"id": notification_id, "user_id": user_id}, {"$set": {"read": True}})
        return self._load(Notification, self.notifications_col.find_one({"id": notification_id, "user_id": user_id}))

    def create_audit_log(self, log: AuditLog) -> AuditLog:
        self.audit_col.insert_one(self._dump(log))
        return log

    def list_audit_logs(self, *, project_id: str | None = None, limit: int = 100) -> list[AuditLog]:
        query = {"details.project_id": project_id} if project_id else {}
        cursor = self.audit_col.find(query).sort("timestamp", -1).limit(limit)
        return [self._load(AuditLog, row) for row in cursor]

    def get_dashboard_stats(self, project_id: str | None = None) -> DashboardStats:
        issues = self.list_issues(project_id=project_id)
        status_counts = Counter(issue.status.value for issue in issues)
        priority_counts = Counter(issue.priority.value for issue in issues)
        return DashboardStats(
            total_issues=len(issues),
            todo_issues=status_counts.get(IssueStatus.todo.value, 0),
            in_progress_issues=status_counts.get(IssueStatus.in_progress.value, 0),
            done_issues=status_counts.get(IssueStatus.done.value, 0),
            low_priority=priority_counts.get(IssuePriority.low.value, 0),
            medium_priority=priority_counts.get(IssuePriority.medium.value, 0),
            high_priority=priority_counts.get(IssuePriority.high.value, 0),
            critical_priority=priority_counts.get(IssuePriority.critical.value, 0),
            recent_activity=self.list_audit_logs(project_id=project_id, limit=12),
        )
