from __future__ import annotations

from abc import ABC, abstractmethod
from collections import Counter
from copy import deepcopy

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
    Project,
    UserInDB,
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
    def create_project(self, project: Project) -> Project: ...

    @abstractmethod
    def list_projects(self) -> list[Project]: ...

    @abstractmethod
    def get_project(self, project_id: str) -> Project | None: ...

    @abstractmethod
    def update_project(
        self,
        project_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
    ) -> Project | None: ...

    @abstractmethod
    def create_issue(self, issue: Issue) -> Issue: ...

    @abstractmethod
    def get_issue(self, issue_id: str) -> Issue | None: ...

    @abstractmethod
    def list_issues(
        self,
        *,
        status: IssueStatus | None = None,
        priority: IssuePriority | None = None,
        project_id: str | None = None,
        assignee_id: str | None = None,
    ) -> list[Issue]: ...

    @abstractmethod
    def update_issue(self, issue: Issue) -> Issue: ...

    @abstractmethod
    def create_comment(self, comment: Comment) -> Comment: ...

    @abstractmethod
    def list_comments(self, issue_id: str) -> list[Comment]: ...

    @abstractmethod
    def create_audit_log(self, log: AuditLog) -> AuditLog: ...

    @abstractmethod
    def list_audit_logs(self, *, limit: int = 100) -> list[AuditLog]: ...

    @abstractmethod
    def get_dashboard_stats(self) -> DashboardStats: ...


class InMemoryStore(BaseStore):
    def __init__(self) -> None:
        self.users: dict[str, UserInDB] = {}
        self.projects: dict[str, Project] = {}
        self.issues: dict[str, Issue] = {}
        self.comments: dict[str, Comment] = {}
        self.audit_logs: dict[str, AuditLog] = {}

    def user_count(self) -> int:
        return len(self.users)

    def create_user(self, user: UserInDB) -> UserInDB:
        self.users[user.id] = deepcopy(user)
        return deepcopy(user)

    def get_user_by_email(self, email: str) -> UserInDB | None:
        email_l = email.lower()
        for user in self.users.values():
            if user.email.lower() == email_l:
                return deepcopy(user)
        return None

    def get_user_by_id(self, user_id: str) -> UserInDB | None:
        if user_id not in self.users:
            return None
        return deepcopy(self.users[user_id])

    def list_users(self) -> list[UserInDB]:
        return [deepcopy(user) for user in self.users.values()]

    def update_user_role(self, user_id: str, role: UserRole) -> UserInDB | None:
        user = self.users.get(user_id)
        if not user:
            return None
        user.role = role
        return deepcopy(user)

    def create_project(self, project: Project) -> Project:
        self.projects[project.id] = deepcopy(project)
        return deepcopy(project)

    def list_projects(self) -> list[Project]:
        return [deepcopy(p) for p in self.projects.values()]

    def get_project(self, project_id: str) -> Project | None:
        if project_id not in self.projects:
            return None
        return deepcopy(self.projects[project_id])

    def update_project(
        self,
        project_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
    ) -> Project | None:
        project = self.projects.get(project_id)
        if not project:
            return None
        if name is not None:
            project.name = name
        if description is not None:
            project.description = description
        return deepcopy(project)

    def create_issue(self, issue: Issue) -> Issue:
        self.issues[issue.id] = deepcopy(issue)
        return deepcopy(issue)

    def get_issue(self, issue_id: str) -> Issue | None:
        if issue_id not in self.issues:
            return None
        return deepcopy(self.issues[issue_id])

    def list_issues(
        self,
        *,
        status: IssueStatus | None = None,
        priority: IssuePriority | None = None,
        project_id: str | None = None,
        assignee_id: str | None = None,
    ) -> list[Issue]:
        issues = self.issues.values()
        result = []
        for issue in issues:
            if status is not None and issue.status != status:
                continue
            if priority is not None and issue.priority != priority:
                continue
            if project_id is not None and issue.project_id != project_id:
                continue
            if assignee_id is not None and issue.assignee_id != assignee_id:
                continue
            result.append(deepcopy(issue))
        return result

    def update_issue(self, issue: Issue) -> Issue:
        self.issues[issue.id] = deepcopy(issue)
        return deepcopy(issue)

    def create_comment(self, comment: Comment) -> Comment:
        self.comments[comment.id] = deepcopy(comment)
        return deepcopy(comment)

    def list_comments(self, issue_id: str) -> list[Comment]:
        return [deepcopy(c) for c in self.comments.values() if c.issue_id == issue_id]

    def create_audit_log(self, log: AuditLog) -> AuditLog:
        self.audit_logs[log.id] = deepcopy(log)
        return deepcopy(log)

    def list_audit_logs(self, *, limit: int = 100) -> list[AuditLog]:
        logs = sorted(
            self.audit_logs.values(),
            key=lambda item: item.timestamp,
            reverse=True,
        )
        return [deepcopy(log) for log in logs[:limit]]

    def get_dashboard_stats(self) -> DashboardStats:
        issues = list(self.issues.values())
        status_counts = Counter(issue.status.value for issue in issues)
        critical_issues = sum(1 for issue in issues if issue.priority == IssuePriority.critical)
        return DashboardStats(
            total_issues=len(issues),
            open_issues=status_counts.get(IssueStatus.open.value, 0),
            in_progress_issues=status_counts.get(IssueStatus.in_progress.value, 0),
            resolved_issues=status_counts.get(IssueStatus.resolved.value, 0),
            closed_issues=status_counts.get(IssueStatus.closed.value, 0),
            critical_issues=critical_issues,
        )


class MongoStore(BaseStore):
    def __init__(self, uri: str, db_name: str) -> None:
        self.client: MongoClient = MongoClient(uri)
        self.db: Database = self.client[db_name]
        self.users_col: Collection = self.db["users"]
        self.projects_col: Collection = self.db["projects"]
        self.issues_col: Collection = self.db["issues"]
        self.comments_col: Collection = self.db["comments"]
        self.audit_col: Collection = self.db["audit_logs"]
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        self.users_col.create_index("email", unique=True)
        self.projects_col.create_index("created_by")
        self.issues_col.create_index("project_id")
        self.issues_col.create_index("status")
        self.issues_col.create_index("priority")
        self.issues_col.create_index("assignee_id")
        self.comments_col.create_index("issue_id")
        self.audit_col.create_index("timestamp")

    @staticmethod
    def _dump(model) -> dict:
        data = model.model_dump(mode="json")
        data["_id"] = data["id"]
        return data

    @staticmethod
    def _dump_for_update(model) -> dict:
        return model.model_dump(mode="json")

    @staticmethod
    def _load(model_type, doc: dict | None):
        if not doc:
            return None
        materialized = dict(doc)
        materialized.pop("_id", None)
        return model_type.model_validate(materialized)

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
        return [self._load(UserInDB, doc) for doc in self.users_col.find({})]

    def update_user_role(self, user_id: str, role: UserRole) -> UserInDB | None:
        self.users_col.update_one({"id": user_id}, {"$set": {"role": role.value}})
        return self.get_user_by_id(user_id)

    def create_project(self, project: Project) -> Project:
        self.projects_col.insert_one(self._dump(project))
        return project

    def list_projects(self) -> list[Project]:
        return [self._load(Project, doc) for doc in self.projects_col.find({})]

    def get_project(self, project_id: str) -> Project | None:
        return self._load(Project, self.projects_col.find_one({"id": project_id}))

    def update_project(
        self,
        project_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
    ) -> Project | None:
        updates = {}
        if name is not None:
            updates["name"] = name
        if description is not None:
            updates["description"] = description
        if updates:
            self.projects_col.update_one({"id": project_id}, {"$set": updates})
        return self.get_project(project_id)

    def create_issue(self, issue: Issue) -> Issue:
        self.issues_col.insert_one(self._dump(issue))
        return issue

    def get_issue(self, issue_id: str) -> Issue | None:
        return self._load(Issue, self.issues_col.find_one({"id": issue_id}))

    def list_issues(
        self,
        *,
        status: IssueStatus | None = None,
        priority: IssuePriority | None = None,
        project_id: str | None = None,
        assignee_id: str | None = None,
    ) -> list[Issue]:
        query = {}
        if status is not None:
            query["status"] = status.value
        if priority is not None:
            query["priority"] = priority.value
        if project_id is not None:
            query["project_id"] = project_id
        if assignee_id is not None:
            query["assignee_id"] = assignee_id
        return [self._load(Issue, doc) for doc in self.issues_col.find(query)]

    def update_issue(self, issue: Issue) -> Issue:
        self.issues_col.update_one({"id": issue.id}, {"$set": self._dump_for_update(issue)})
        return issue

    def create_comment(self, comment: Comment) -> Comment:
        self.comments_col.insert_one(self._dump(comment))
        return comment

    def list_comments(self, issue_id: str) -> list[Comment]:
        return [
            self._load(Comment, doc)
            for doc in self.comments_col.find({"issue_id": issue_id})
        ]

    def create_audit_log(self, log: AuditLog) -> AuditLog:
        self.audit_col.insert_one(self._dump(log))
        return log

    def list_audit_logs(self, *, limit: int = 100) -> list[AuditLog]:
        cursor = self.audit_col.find({}).sort("timestamp", -1).limit(limit)
        return [self._load(AuditLog, doc) for doc in cursor]

    def get_dashboard_stats(self) -> DashboardStats:
        issues = self.list_issues()
        status_counts = Counter(issue.status.value for issue in issues)
        critical_issues = sum(1 for issue in issues if issue.priority == IssuePriority.critical)
        return DashboardStats(
            total_issues=len(issues),
            open_issues=status_counts.get(IssueStatus.open.value, 0),
            in_progress_issues=status_counts.get(IssueStatus.in_progress.value, 0),
            resolved_issues=status_counts.get(IssueStatus.resolved.value, 0),
            closed_issues=status_counts.get(IssueStatus.closed.value, 0),
            critical_issues=critical_issues,
        )
