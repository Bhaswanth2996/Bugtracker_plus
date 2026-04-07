from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from app.core.security import hash_password
from app.db.store import BaseStore
from app.models.schemas import (
    Issue,
    IssuePriority,
    IssueStatus,
    IssueType,
    Project,
    ProjectMember,
    Sprint,
    SprintStatus,
    UserInDB,
    UserRole,
)

AUTH_ISSUE_TITLES = [
    "Fix login API bug",
    "Password reset failure",
    "OAuth token expiry issue",
    "Improve login UI validation",
    "Session timeout bug",
    "Add Google login",
    "Fix JWT refresh token bug",
    "Login page UI glitch",
    "Authentication middleware error",
    "Add audit logging",
    "Two-factor authentication setup",
    "Remember me checkbox regression",
    "Rate-limit brute force login attempts",
    "Fix malformed token parsing",
    "MFA backup code generation",
    "Improve auth service retries",
    "Repair logout endpoint race condition",
    "Token blacklist cleanup job",
    "Add email verification flow",
    "Password strength indicator bug",
    "Add SSO provider metadata sync",
    "Fix profile lockout edge case",
    "Recover account unlock flow",
    "Auth event logging to monitor",
    "Resolve CORS preflight on auth route",
    "Fix stale session cookie handling",
    "Improve captcha fallback on login",
    "Support multi-device signout",
    "Enhance account recovery journey",
    "Fix mobile keyboard login submit",
    "Add enterprise SAML mapping",
    "Auth service health endpoint docs",
    "Token revocation job timeout",
    "Fix silent auth renew failure",
    "OAuth callback redirect mismatch",
    "Improve auth error localization",
    "Fix remember-token encryption bug",
    "Reduce auth endpoint latency spikes",
    "Consolidate duplicated auth guards",
    "Add suspicious login alerting",
]

AUTH_EPIC_STORY_ISSUES: list[tuple[IssueType, str, str]] = [
    (
        IssueType.epic,
        "Identity Modernization Program",
        "Epic covering modernization of authentication architecture, security controls, and reliability.",
    ),
    (
        IssueType.story,
        "As a user, I can recover account with secure OTP",
        "Implement OTP-based recovery path with anti-abuse limits and UX validation.",
    ),
    (
        IssueType.epic,
        "Enterprise SSO Expansion",
        "Epic for onboarding enterprise identity providers (SAML/OIDC) with configuration governance.",
    ),
    (
        IssueType.story,
        "As an admin, I can enforce MFA for privileged accounts",
        "Add policy engine to enforce MFA requirement on selected role groups.",
    ),
    (
        IssueType.epic,
        "Session Management Hardening",
        "Epic focused on token revocation, idle timeout handling, and concurrent session controls.",
    ),
    (
        IssueType.story,
        "As a user, I can view active sessions and revoke them",
        "Expose account-level session inventory with secure revoke action.",
    ),
    (
        IssueType.epic,
        "Auth Observability and Compliance",
        "Epic for compliance-grade logs, alerting, and traceability across auth workflows.",
    ),
    (
        IssueType.story,
        "As an auditor, I can export auth event logs",
        "Provide filtered export for login and token lifecycle events with PII-safe masking.",
    ),
    (
        IssueType.epic,
        "Zero-Trust Access Initiative",
        "Epic introducing contextual access policies, anomaly checks, and risk-based auth flows.",
    ),
    (
        IssueType.story,
        "As a user, I receive risk alerts on suspicious login",
        "Notify users in-app/email when suspicious login behavior is detected.",
    ),
]

LABELS = [
    "auth",
    "api",
    "ui",
    "security",
    "middleware",
    "performance",
    "bugfix",
    "enhancement",
]


def _ensure_user(store: BaseStore, *, name: str, email: str, role: UserRole) -> UserInDB:
    existing = store.get_user_by_email(email)
    if existing:
        return existing
    now = datetime.now(tz=timezone.utc)
    created = UserInDB(
        name=name,
        email=email,
        role=role,
        password_hash=hash_password("Password123!"),
        created_at=now,
        updated_at=now,
    )
    return store.create_user(created)


def seed_demo_data(store: BaseStore) -> None:
    admin = _ensure_user(store, name="Admin User", email="admin@jira.com", role=UserRole.admin)
    pm = _ensure_user(
        store,
        name="Project Manager",
        email="pm@jira.com",
        role=UserRole.project_manager,
    )
    dev = _ensure_user(
        store,
        name="Developer One",
        email="dev@jira.com",
        role=UserRole.developer,
    )
    tester = _ensure_user(
        store,
        name="QA Tester",
        email="qa@jira.com",
        role=UserRole.tester,
    )

    project = store.get_project_by_key("AUTH")
    if not project:
        project = Project(
            key="AUTH",
            name="Authentication Platform",
            description="Jira-like sample project seeded for demo workflows.",
            created_by=pm.id,
            members=[
                ProjectMember(user_id=pm.id, role=pm.role),
                ProjectMember(user_id=dev.id, role=dev.role),
                ProjectMember(user_id=tester.id, role=tester.role),
            ],
        )
        project = store.create_project(project)

    target_issue_count = 50
    existing = store.list_issues(project_id=project.id)
    if len(existing) >= target_issue_count:
        return
    existing_keys = {issue.issue_key for issue in existing if issue.issue_key}

    rng = random.Random(42)
    statuses = [IssueStatus.todo, IssueStatus.in_progress, IssueStatus.done]
    priorities = [
        IssuePriority.low,
        IssuePriority.medium,
        IssuePriority.high,
        IssuePriority.critical,
    ]
    assignees = [pm.id, dev.id, tester.id, None]

    for index, title in enumerate(AUTH_ISSUE_TITLES, start=1):
        if len(store.list_issues(project_id=project.id)) >= target_issue_count:
            break
        issue_key = f"AUTH-{index}"
        if issue_key in existing_keys:
            continue
        priority = priorities[rng.randint(0, len(priorities) - 1)]
        status = statuses[rng.randint(0, len(statuses) - 1)]
        assignee = assignees[rng.randint(0, len(assignees) - 1)]
        created_at = datetime.now(tz=timezone.utc) - timedelta(days=60 - index)
        labels = rng.sample(LABELS, k=rng.randint(1, 3))
        issue = Issue(
            project_id=project.id,
            issue_key=issue_key,
            title=title,
            description=f"Seeded issue {index}: {title}. Includes realistic data for Jira-like board workflows.",
            issue_type=IssueType.bug if index % 4 != 0 else IssueType.task,
            priority=priority,
            status=status,
            reporter_id=pm.id,
            assignee_id=assignee,
            labels=labels,
            backlog_order=float(index),
            created_at=created_at,
            updated_at=created_at,
        )
        store.create_issue(issue)
        existing_keys.add(issue_key)

    epic_story_start = len(AUTH_ISSUE_TITLES) + 1
    for offset, (issue_type, title, description) in enumerate(AUTH_EPIC_STORY_ISSUES):
        if len(store.list_issues(project_id=project.id)) >= target_issue_count:
            break
        index = epic_story_start + offset
        issue_key = f"AUTH-{index}"
        if issue_key in existing_keys:
            continue
        priority = priorities[rng.randint(0, len(priorities) - 1)]
        status = statuses[rng.randint(0, len(statuses) - 1)]
        assignee = assignees[rng.randint(0, len(assignees) - 1)]
        created_at = datetime.now(tz=timezone.utc) - timedelta(days=20 - offset)
        labels = rng.sample(["auth", "epic", "story", "security", "platform"], k=2)
        issue = Issue(
            project_id=project.id,
            issue_key=issue_key,
            title=title,
            description=description,
            issue_type=issue_type,
            priority=priority,
            status=status,
            reporter_id=pm.id,
            assignee_id=assignee,
            labels=labels,
            backlog_order=float(index),
            created_at=created_at,
            updated_at=created_at,
        )
        store.create_issue(issue)
        existing_keys.add(issue_key)

    if not store.list_sprints(project.id):
        sprint = Sprint(
            project_id=project.id,
            name="Sprint 1 - Auth Stability",
            goal="Stabilize authentication module and close critical issues.",
            status=SprintStatus.active,
            start_date=datetime.now(tz=timezone.utc) - timedelta(days=4),
            end_date=datetime.now(tz=timezone.utc) + timedelta(days=10),
            created_by=pm.id,
        )
        store.create_sprint(sprint)
