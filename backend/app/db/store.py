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
    AIAnalysisLog,
    AuditLog,
    Comment,
    DashboardStats,
    Issue,
    IssueActivity,
    IssueLink,
    IssuePriority,
    IssueTimelineEvent,
    IssueStatus,
    IssueType,
    Notification,
    Project,
    ProjectMember,
    RootCauseAnalysis,
    Sprint,
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
    def get_issue_by_key(self, issue_key: str) -> Issue | None: ...

    @abstractmethod
    def next_issue_sequence(self, project_id: str) -> int: ...

    @abstractmethod
    def list_issues(
        self,
        *,
        project_id: str | None = None,
        issue_type: IssueType | None = None,
        status: IssueStatus | None = None,
        priority: IssuePriority | None = None,
        assignee_id: str | None = None,
        sprint_id: str | None = None,
        labels: list[str] | None = None,
        search: str | None = None,
    ) -> list[Issue]: ...

    @abstractmethod
    def search_issues(
        self,
        *,
        q: str | None = None,
        project_id: str | None = None,
        status: IssueStatus | None = None,
        priority: IssuePriority | None = None,
        assignee_id: str | None = None,
        limit: int = 25,
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
    def create_issue_activity(self, activity: IssueActivity) -> IssueActivity: ...

    @abstractmethod
    def list_issue_activity(self, issue_id: str) -> list[IssueActivity]: ...

    @abstractmethod
    def create_issue_timeline_event(self, event: IssueTimelineEvent) -> IssueTimelineEvent: ...

    @abstractmethod
    def list_issue_timeline(self, issue_id: str, limit: int = 200) -> list[IssueTimelineEvent]: ...

    @abstractmethod
    def list_recent_timeline(self, project_id: str | None = None, limit: int = 40) -> list[IssueTimelineEvent]: ...

    @abstractmethod
    def create_ai_analysis_log(self, log: AIAnalysisLog) -> AIAnalysisLog: ...

    @abstractmethod
    def list_ai_analysis_logs(self, analysis_type: str | None = None, limit: int = 50) -> list[AIAnalysisLog]: ...

    @abstractmethod
    def upsert_root_cause_analysis(self, analysis: RootCauseAnalysis) -> RootCauseAnalysis: ...

    @abstractmethod
    def get_root_cause_analysis(self, issue_id: str) -> RootCauseAnalysis | None: ...

    @abstractmethod
    def list_root_cause_analysis(self, limit: int = 20) -> list[RootCauseAnalysis]: ...

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
    def create_issue_link(self, link: IssueLink) -> IssueLink: ...

    @abstractmethod
    def list_issue_links(self, issue_id: str) -> list[IssueLink]: ...

    @abstractmethod
    def delete_issue_link(self, link_id: str) -> bool: ...

    @abstractmethod
    def create_audit_log(self, log: AuditLog) -> AuditLog: ...

    @abstractmethod
    def list_audit_logs(self, *, project_id: str | None = None, limit: int = 100) -> list[AuditLog]: ...

    @abstractmethod
    def get_dashboard_stats(
        self,
        project_id: str | None = None,
        current_user_id: str | None = None,
    ) -> DashboardStats: ...


class InMemoryStore(BaseStore):
    def __init__(self) -> None:
        self.users: dict[str, UserInDB] = {}
        self.projects: dict[str, Project] = {}
        self.issues: dict[str, Issue] = {}
        self.comments: dict[str, Comment] = {}
        self.issue_activities: dict[str, IssueActivity] = {}
        self.issue_timeline_events: dict[str, IssueTimelineEvent] = {}
        self.ai_analysis_logs: dict[str, AIAnalysisLog] = {}
        self.root_cause_analyses: dict[str, RootCauseAnalysis] = {}
        self.issue_links: dict[str, IssueLink] = {}
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

    def get_issue_by_key(self, issue_key: str) -> Issue | None:
        for issue in self.issues.values():
            if issue.issue_key == issue_key:
                return deepcopy(issue)
        return None

    def next_issue_sequence(self, project_id: str) -> int:
        existing = [
            issue for issue in self.issues.values() if issue.project_id == project_id and issue.issue_key
        ]
        if not existing:
            return 1
        numbers: list[int] = []
        for issue in existing:
            try:
                numbers.append(int(str(issue.issue_key).split("-")[-1]))
            except Exception:
                continue
        return (max(numbers) + 1) if numbers else (len(existing) + 1)

    def list_issues(
        self,
        *,
        project_id: str | None = None,
        issue_type: IssueType | None = None,
        status: IssueStatus | None = None,
        priority: IssuePriority | None = None,
        assignee_id: str | None = None,
        sprint_id: str | None = None,
        labels: list[str] | None = None,
        search: str | None = None,
    ) -> list[Issue]:
        result: list[Issue] = []
        needle = (search or "").lower().strip()
        label_set = {label.lower() for label in (labels or [])}
        for issue in self.issues.values():
            if project_id and issue.project_id != project_id:
                continue
            if issue_type and issue.issue_type != issue_type:
                continue
            if status and issue.status != status:
                continue
            if priority and issue.priority != priority:
                continue
            if assignee_id and issue.assignee_id != assignee_id:
                continue
            if sprint_id is not None and issue.sprint_id != sprint_id:
                continue
            if label_set and not label_set.issubset({label.lower() for label in issue.labels}):
                continue
            if needle and needle not in f"{issue.title} {issue.description}".lower():
                continue
            result.append(deepcopy(issue))
        return sorted(result, key=lambda item: (item.backlog_order, item.created_at))

    def search_issues(
        self,
        *,
        q: str | None = None,
        project_id: str | None = None,
        status: IssueStatus | None = None,
        priority: IssuePriority | None = None,
        assignee_id: str | None = None,
        limit: int = 25,
    ) -> list[Issue]:
        needle = (q or "").strip().lower()
        scored: list[tuple[int, Issue]] = []
        for issue in self.issues.values():
            if project_id and issue.project_id != project_id:
                continue
            if status and issue.status != status:
                continue
            if priority and issue.priority != priority:
                continue
            if assignee_id and issue.assignee_id != assignee_id:
                continue

            score = 0
            if needle:
                title = issue.title.lower()
                description = issue.description.lower()
                labels_blob = " ".join(issue.labels).lower()
                if needle in title:
                    score += 8
                if needle in description:
                    score += 4
                if needle in labels_blob:
                    score += 6
                if score == 0:
                    continue
            scored.append((score, deepcopy(issue)))
        scored.sort(key=lambda item: (item[0], item[1].updated_at), reverse=True)
        return [item[1] for item in scored[:limit]]

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
        return sorted(values, key=lambda item: item.created_at, reverse=True)

    def get_comment(self, comment_id: str) -> Comment | None:
        value = self.comments.get(comment_id)
        return deepcopy(value) if value else None

    def update_comment(self, comment: Comment) -> Comment:
        self.comments[comment.id] = deepcopy(comment)
        return deepcopy(comment)

    def create_issue_activity(self, activity: IssueActivity) -> IssueActivity:
        self.issue_activities[activity.id] = deepcopy(activity)
        return deepcopy(activity)

    def list_issue_activity(self, issue_id: str) -> list[IssueActivity]:
        values = [deepcopy(item) for item in self.issue_activities.values() if item.issue_id == issue_id]
        return sorted(values, key=lambda item: item.timestamp, reverse=True)

    def create_issue_timeline_event(self, event: IssueTimelineEvent) -> IssueTimelineEvent:
        self.issue_timeline_events[event.id] = deepcopy(event)
        return deepcopy(event)

    def list_issue_timeline(self, issue_id: str, limit: int = 200) -> list[IssueTimelineEvent]:
        values = [deepcopy(item) for item in self.issue_timeline_events.values() if item.issue_id == issue_id]
        return sorted(values, key=lambda item: item.timestamp, reverse=True)[:limit]

    def list_recent_timeline(self, project_id: str | None = None, limit: int = 40) -> list[IssueTimelineEvent]:
        values = list(self.issue_timeline_events.values())
        if project_id:
            values = [item for item in values if item.project_id == project_id]
        return sorted([deepcopy(item) for item in values], key=lambda item: item.timestamp, reverse=True)[:limit]

    def create_ai_analysis_log(self, log: AIAnalysisLog) -> AIAnalysisLog:
        self.ai_analysis_logs[log.id] = deepcopy(log)
        return deepcopy(log)

    def list_ai_analysis_logs(self, analysis_type: str | None = None, limit: int = 50) -> list[AIAnalysisLog]:
        values = list(self.ai_analysis_logs.values())
        if analysis_type:
            values = [item for item in values if item.analysis_type == analysis_type]
        return sorted([deepcopy(item) for item in values], key=lambda item: item.created_at, reverse=True)[:limit]

    def upsert_root_cause_analysis(self, analysis: RootCauseAnalysis) -> RootCauseAnalysis:
        self.root_cause_analyses[analysis.issue_id] = deepcopy(analysis)
        return deepcopy(analysis)

    def get_root_cause_analysis(self, issue_id: str) -> RootCauseAnalysis | None:
        value = self.root_cause_analyses.get(issue_id)
        return deepcopy(value) if value else None

    def list_root_cause_analysis(self, limit: int = 20) -> list[RootCauseAnalysis]:
        values = sorted(
            [deepcopy(item) for item in self.root_cause_analyses.values()],
            key=lambda item: item.analyzed_at,
            reverse=True,
        )
        return values[:limit]

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

    def create_issue_link(self, link: IssueLink) -> IssueLink:
        self.issue_links[link.id] = deepcopy(link)
        return deepcopy(link)

    def list_issue_links(self, issue_id: str) -> list[IssueLink]:
        values = [
            deepcopy(item)
            for item in self.issue_links.values()
            if item.source_issue_id == issue_id or item.target_issue_id == issue_id
        ]
        return sorted(values, key=lambda item: item.created_at, reverse=True)

    def delete_issue_link(self, link_id: str) -> bool:
        if link_id not in self.issue_links:
            return False
        del self.issue_links[link_id]
        return True

    def create_audit_log(self, log: AuditLog) -> AuditLog:
        self.audit_logs[log.id] = deepcopy(log)
        return deepcopy(log)

    def list_audit_logs(self, *, project_id: str | None = None, limit: int = 100) -> list[AuditLog]:
        logs = list(self.audit_logs.values())
        if project_id:
            logs = [log for log in logs if log.details.get("project_id") == project_id]
        return sorted([deepcopy(item) for item in logs], key=lambda item: item.timestamp, reverse=True)[:limit]

    def get_dashboard_stats(
        self,
        project_id: str | None = None,
        current_user_id: str | None = None,
    ) -> DashboardStats:
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
            assigned_to_me=sum(1 for issue in issues if issue.assignee_id == current_user_id),
            status_breakdown=dict(status_counts),
            priority_breakdown=dict(priority_counts),
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
        self.issue_activity_col: Collection = self.db["issue_activity"]
        self.issue_history_col: Collection = self.db["issue_history"]
        self.ai_analysis_logs_col: Collection = self.db["ai_analysis_logs"]
        self.root_cause_analysis_col: Collection = self.db["root_cause_analysis"]
        self.issue_links_col: Collection = self.db["issue_links"]
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

    @staticmethod
    def _safe_create_index(collection: Collection, keys, **kwargs) -> None:
        try:
            collection.create_index(keys, **kwargs)
        except Exception:
            # Keep startup resilient when legacy/managed indexes already exist.
            pass

    def _ensure_indexes(self) -> None:
        self._safe_create_index(self.users_col, "email", unique=True)
        self._safe_create_index(self.projects_col, "key", unique=True)
        self._safe_create_index(self.projects_col, "members.user_id")
        self._safe_create_index(self.issues_col, "project_id")
        self._safe_create_index(self.issues_col, "status")
        self._safe_create_index(self.issues_col, "priority")
        self._safe_create_index(self.issues_col, "assignee_id")
        self._safe_create_index(self.issues_col, "source")
        self._safe_create_index(self.issues_col, "module")
        self._safe_create_index(self.issues_col, "issue_key", unique=True, sparse=True)
        self._safe_create_index(self.issues_col, "labels")
        self._safe_create_index(
            self.issues_col,
            [("title", "text"), ("description", "text"), ("labels", "text")],
            name="issue_search_text_idx",
        )
        self._safe_create_index(self.comments_col, "issue_id")
        self._safe_create_index(self.comments_col, "parent_id")
        self._safe_create_index(self.issue_activity_col, "issue_id")
        self._safe_create_index(self.issue_history_col, "issue_id")
        self._safe_create_index(self.issue_history_col, "project_id")
        self._safe_create_index(self.issue_history_col, "timestamp")
        self._safe_create_index(self.ai_analysis_logs_col, "analysis_type")
        self._safe_create_index(self.ai_analysis_logs_col, "created_at")
        self._safe_create_index(self.root_cause_analysis_col, "issue_id", unique=True)
        self._safe_create_index(self.root_cause_analysis_col, "analyzed_at")
        self._safe_create_index(self.issue_links_col, "source_issue_id")
        self._safe_create_index(self.issue_links_col, "target_issue_id")
        self._safe_create_index(self.sprints_col, "project_id")
        self._safe_create_index(self.notifications_col, "user_id")
        self._safe_create_index(self.audit_col, "timestamp")

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

    def get_issue_by_key(self, issue_key: str) -> Issue | None:
        return self._load(Issue, self.issues_col.find_one({"issue_key": issue_key}))

    def next_issue_sequence(self, project_id: str) -> int:
        project_issues = self.list_issues(project_id=project_id)
        if not project_issues:
            return 1
        numbers: list[int] = []
        for issue in project_issues:
            if not issue.issue_key:
                continue
            try:
                numbers.append(int(str(issue.issue_key).split("-")[-1]))
            except Exception:
                continue
        return (max(numbers) + 1) if numbers else (len(project_issues) + 1)

    def list_issues(
        self,
        *,
        project_id: str | None = None,
        issue_type: IssueType | None = None,
        status: IssueStatus | None = None,
        priority: IssuePriority | None = None,
        assignee_id: str | None = None,
        sprint_id: str | None = None,
        labels: list[str] | None = None,
        search: str | None = None,
    ) -> list[Issue]:
        query: dict[str, Any] = {}
        if project_id:
            query["project_id"] = project_id
        if issue_type:
            query["issue_type"] = issue_type.value
        if status:
            query["status"] = status.value
        if priority:
            query["priority"] = priority.value
        if assignee_id:
            query["assignee_id"] = assignee_id
        if sprint_id is not None:
            query["sprint_id"] = sprint_id
        if labels:
            query["labels"] = {"$all": labels}
        if search:
            query["$text"] = {"$search": search}
        cursor = self.issues_col.find(query).sort([("backlog_order", 1), ("created_at", 1)])
        return [self._load(Issue, row) for row in cursor]

    def search_issues(
        self,
        *,
        q: str | None = None,
        project_id: str | None = None,
        status: IssueStatus | None = None,
        priority: IssuePriority | None = None,
        assignee_id: str | None = None,
        limit: int = 25,
    ) -> list[Issue]:
        filters: dict[str, Any] = {}
        if project_id:
            filters["project_id"] = project_id
        if status:
            filters["status"] = status.value
        if priority:
            filters["priority"] = priority.value
        if assignee_id:
            filters["assignee_id"] = assignee_id

        if not q:
            cursor = self.issues_col.find(filters).sort("updated_at", -1).limit(limit)
            return [self._load(Issue, row) for row in cursor]

        text_query = {**filters, "$text": {"$search": q}}
        rows = list(
            self.issues_col.find(text_query, {"score": {"$meta": "textScore"}})
            .sort([("score", {"$meta": "textScore"}), ("updated_at", -1)])
            .limit(limit)
        )

        # Compatibility fallback when labels are not covered by an existing text index.
        regex_rows = list(
            self.issues_col.find({**filters, "labels": {"$elemMatch": {"$regex": q, "$options": "i"}}})
            .sort("updated_at", -1)
            .limit(limit)
        )
        deduped: dict[str, dict[str, Any]] = {}
        for row in rows + regex_rows:
            deduped[row.get("id")] = row
        return [self._load(Issue, row) for row in list(deduped.values())[:limit]]

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
        cursor = self.comments_col.find({"issue_id": issue_id}).sort("created_at", -1)
        return [self._load(Comment, row) for row in cursor]

    def get_comment(self, comment_id: str) -> Comment | None:
        return self._load(Comment, self.comments_col.find_one({"id": comment_id}))

    def update_comment(self, comment: Comment) -> Comment:
        self.comments_col.update_one({"id": comment.id}, {"$set": self._dump_for_update(comment)})
        return comment

    def create_issue_activity(self, activity: IssueActivity) -> IssueActivity:
        self.issue_activity_col.insert_one(self._dump(activity))
        return activity

    def list_issue_activity(self, issue_id: str) -> list[IssueActivity]:
        cursor = self.issue_activity_col.find({"issue_id": issue_id}).sort("timestamp", -1)
        return [self._load(IssueActivity, row) for row in cursor]

    def create_issue_timeline_event(self, event: IssueTimelineEvent) -> IssueTimelineEvent:
        self.issue_history_col.insert_one(self._dump(event))
        return event

    def list_issue_timeline(self, issue_id: str, limit: int = 200) -> list[IssueTimelineEvent]:
        cursor = self.issue_history_col.find({"issue_id": issue_id}).sort("timestamp", -1).limit(limit)
        return [self._load(IssueTimelineEvent, row) for row in cursor]

    def list_recent_timeline(self, project_id: str | None = None, limit: int = 40) -> list[IssueTimelineEvent]:
        query: dict[str, Any] = {}
        if project_id:
            query["project_id"] = project_id
        cursor = self.issue_history_col.find(query).sort("timestamp", -1).limit(limit)
        return [self._load(IssueTimelineEvent, row) for row in cursor]

    def create_ai_analysis_log(self, log: AIAnalysisLog) -> AIAnalysisLog:
        self.ai_analysis_logs_col.insert_one(self._dump(log))
        return log

    def list_ai_analysis_logs(self, analysis_type: str | None = None, limit: int = 50) -> list[AIAnalysisLog]:
        query: dict[str, Any] = {}
        if analysis_type:
            query["analysis_type"] = analysis_type
        cursor = self.ai_analysis_logs_col.find(query).sort("created_at", -1).limit(limit)
        return [self._load(AIAnalysisLog, row) for row in cursor]

    def upsert_root_cause_analysis(self, analysis: RootCauseAnalysis) -> RootCauseAnalysis:
        self.root_cause_analysis_col.update_one(
            {"issue_id": analysis.issue_id},
            {"$set": self._dump_for_update(analysis)},
            upsert=True,
        )
        return analysis

    def get_root_cause_analysis(self, issue_id: str) -> RootCauseAnalysis | None:
        return self._load(RootCauseAnalysis, self.root_cause_analysis_col.find_one({"issue_id": issue_id}))

    def list_root_cause_analysis(self, limit: int = 20) -> list[RootCauseAnalysis]:
        cursor = self.root_cause_analysis_col.find({}).sort("analyzed_at", -1).limit(limit)
        return [self._load(RootCauseAnalysis, row) for row in cursor]

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

    def create_issue_link(self, link: IssueLink) -> IssueLink:
        self.issue_links_col.insert_one(self._dump(link))
        return link

    def list_issue_links(self, issue_id: str) -> list[IssueLink]:
        cursor = self.issue_links_col.find(
            {"$or": [{"source_issue_id": issue_id}, {"target_issue_id": issue_id}]}
        ).sort("created_at", -1)
        return [self._load(IssueLink, row) for row in cursor]

    def delete_issue_link(self, link_id: str) -> bool:
        result = self.issue_links_col.delete_one({"id": link_id})
        return result.deleted_count > 0

    def create_audit_log(self, log: AuditLog) -> AuditLog:
        self.audit_col.insert_one(self._dump(log))
        return log

    def list_audit_logs(self, *, project_id: str | None = None, limit: int = 100) -> list[AuditLog]:
        query = {"details.project_id": project_id} if project_id else {}
        cursor = self.audit_col.find(query).sort("timestamp", -1).limit(limit)
        return [self._load(AuditLog, row) for row in cursor]

    def get_dashboard_stats(
        self,
        project_id: str | None = None,
        current_user_id: str | None = None,
    ) -> DashboardStats:
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
            assigned_to_me=sum(1 for issue in issues if issue.assignee_id == current_user_id),
            status_breakdown=dict(status_counts),
            priority_breakdown=dict(priority_counts),
            recent_activity=self.list_audit_logs(project_id=project_id, limit=12),
        )
