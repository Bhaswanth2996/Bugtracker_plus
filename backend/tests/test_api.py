import os

from fastapi.testclient import TestClient

os.environ["BUGTRACKER_STORE_BACKEND"] = "memory"
os.environ["BUGTRACKER_ENABLE_DEMO_SEED"] = "false"

from app.core.config import get_settings
get_settings.cache_clear()

from app.main import app


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_jira_like_end_to_end_flow() -> None:
    with TestClient(app) as client:
        register_admin = client.post(
            "/auth/register",
            json={"name": "Admin User", "email": "admin@example.com", "password": "password123"},
        )
        assert register_admin.status_code == 201
        admin_token = register_admin.json()["access_token"]

        register_pm = client.post(
            "/auth/register",
            json={"name": "Project Manager", "email": "pm@example.com", "password": "password123"},
        )
        assert register_pm.status_code == 201
        pm_id = register_pm.json()["user"]["id"]

        promote_pm = client.put(
            f"/users/{pm_id}/role",
            json={"role": "project_manager"},
            headers=auth_headers(admin_token),
        )
        assert promote_pm.status_code == 200

        create_project = client.post(
            "/projects",
            json={"key": "BUG", "name": "Core API", "description": "Backend service work"},
            headers=auth_headers(admin_token),
        )
        assert create_project.status_code == 201
        project_id = create_project.json()["id"]

        register_tester = client.post(
            "/auth/register",
            json={"name": "QA Tester", "email": "qa@example.com", "password": "password123"},
        )
        assert register_tester.status_code == 201
        tester_token = register_tester.json()["access_token"]
        tester_id = register_tester.json()["user"]["id"]

        list_users = client.get("/users", headers=auth_headers(admin_token))
        assert list_users.status_code == 200
        assert len(list_users.json()) == 3

        assign_developer_role = client.put(
            f"/users/{tester_id}/role",
            json={"role": "developer"},
            headers=auth_headers(admin_token),
        )
        assert assign_developer_role.status_code == 200
        assert assign_developer_role.json()["role"] == "developer"

        assign_member = client.post(
            f"/projects/{project_id}/members",
            json={"user_id": tester_id, "role": "developer"},
            headers=auth_headers(admin_token),
        )
        assert assign_member.status_code == 200

        create_sprint = client.post(
            "/sprints",
            json={"project_id": project_id, "name": "Sprint 1", "goal": "Core issue fixes"},
            headers=auth_headers(admin_token),
        )
        assert create_sprint.status_code == 201
        sprint_id = create_sprint.json()["id"]

        start_sprint = client.post(f"/sprints/{sprint_id}/start", headers=auth_headers(admin_token))
        assert start_sprint.status_code == 200

        create_issue = client.post(
            "/issues",
            json={
                "project_id": project_id,
                "title": "Fix login refresh bug",
                "description": "Session token does not refresh before expiration.",
                "issue_type": "bug",
                "priority": "high",
                "assignee_id": tester_id,
                "labels": ["auth", "token"],
            },
            headers=auth_headers(admin_token),
        )
        assert create_issue.status_code == 201
        issue_id = create_issue.json()["id"]

        move_to_sprint = client.put(
            f"/issues/{issue_id}/sprint",
            json={"sprint_id": sprint_id, "backlog_order": 1},
            headers=auth_headers(admin_token),
        )
        assert move_to_sprint.status_code == 200

        tester_update_issue = client.put(
            f"/issues/{issue_id}",
            json={"status": "in_progress", "priority": "critical"},
            headers=auth_headers(tester_token),
        )
        assert tester_update_issue.status_code == 200
        assert tester_update_issue.json()["status"] == "in_progress"

        add_comment = client.post(
            "/comments",
            json={"issue_id": issue_id, "body": "Investigating token refresh middleware now."},
            headers=auth_headers(tester_token),
        )
        assert add_comment.status_code == 201
        comment_id = add_comment.json()["id"]

        edit_comment = client.put(
            f"/comments/{comment_id}",
            json={"body": "Investigating middleware + refresh edge cases."},
            headers=auth_headers(tester_token),
        )
        assert edit_comment.status_code == 200

        comments = client.get(f"/comments/{issue_id}", headers=auth_headers(admin_token))
        assert comments.status_code == 200
        assert len(comments.json()) == 1

        stats = client.get(f"/projects/{project_id}/dashboard", headers=auth_headers(admin_token))
        assert stats.status_code == 200
        assert stats.json()["in_progress_issues"] == 1

        ai_analysis = client.post(
            "/api/ai/analyze-bug",
            params={"project_id": project_id, "module": "authentication"},
            json={
                "title": "Login error with expired token",
                "description": "Users are seeing a token expired error and cannot continue.",
            },
            headers=auth_headers(admin_token),
        )
        assert ai_analysis.status_code == 200
        assert "suggestedPriority" in ai_analysis.json()

        duplicate_scan = client.post(
            "/api/ai/find-duplicates",
            params={"project_id": project_id},
            json={
                "title": "Login refresh bug",
                "description": "Session token does not refresh and users are logged out.",
            },
            headers=auth_headers(admin_token),
        )
        assert duplicate_scan.status_code == 200
        assert "duplicates" in duplicate_scan.json()

        assignee_reco = client.post(
            "/api/ai/recommend-assignee",
            params={"project_id": project_id},
            json={"module": "authentication", "description": "Need fix for token refresh flow"},
            headers=auth_headers(admin_token),
        )
        assert assignee_reco.status_code == 200
        assert "recommendedDeveloper" in assignee_reco.json()

        root_cause = client.get(
            f"/api/issues/{issue_id}/root-cause",
            headers=auth_headers(admin_token),
        )
        assert root_cause.status_code == 200
        assert "suspectedCommit" in root_cause.json()

        bug_risk = client.get(
            "/api/analytics/bug-risk",
            params={"project_id": project_id},
            headers=auth_headers(admin_token),
        )
        assert bug_risk.status_code == 200
        assert isinstance(bug_risk.json(), list)

        ci_issue = client.post(
            "/api/test-failure-report",
            json={
                "projectKey": "BUG",
                "testName": "LoginTest",
                "errorMessage": "TokenExpiredError",
                "stackTrace": "Traceback...",
                "logs": "pytest failure logs",
                "screenshotUrl": "https://example.com/screenshot.png",
                "timestamp": "2026-03-12T10:00:00Z",
            },
        )
        assert ci_issue.status_code == 201
        assert ci_issue.json()["source"] == "CI/CD Pipeline"

        advanced_dashboard = client.get(
            "/api/analytics/advanced-dashboard",
            params={"project_id": project_id},
            headers=auth_headers(admin_token),
        )
        assert advanced_dashboard.status_code == 200
        assert "bugRiskPrediction" in advanced_dashboard.json()

        timeline = client.get(
            f"/api/issues/{issue_id}/timeline",
            headers=auth_headers(admin_token),
        )
        assert timeline.status_code == 200
        assert any(item["action"] == "status_changed" for item in timeline.json())
        assert any(item["action"] == "comment_added" for item in timeline.json())

        search_results = client.get(
            "/api/issues/search",
            params={"q": "login", "priority": "critical"},
            headers=auth_headers(admin_token),
        )
        assert search_results.status_code == 200
        assert any(item["id"] == issue_id for item in search_results.json())

        recent_timeline = client.get(
            "/api/analytics/recent-activity-timeline",
            params={"project_id": project_id},
            headers=auth_headers(admin_token),
        )
        assert recent_timeline.status_code == 200
        assert isinstance(recent_timeline.json(), list)

        backlog = client.get(f"/projects/{project_id}/backlog", headers=auth_headers(admin_token))
        assert backlog.status_code == 200
        assert all(item["id"] != issue_id for item in backlog.json())

        audit = client.get("/audit", headers=auth_headers(admin_token))
        assert audit.status_code == 200
        assert len(audit.json()) >= 1

        notifications = client.get("/notifications", headers=auth_headers(tester_token))
        assert notifications.status_code == 200
        assert len(notifications.json()) >= 1

        close_sprint = client.post(f"/sprints/{sprint_id}/close", headers=auth_headers(admin_token))
        assert close_sprint.status_code == 200
