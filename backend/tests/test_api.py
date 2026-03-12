from fastapi.testclient import TestClient

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

        backlog = client.get(f"/projects/{project_id}/backlog", headers=auth_headers(admin_token))
        assert backlog.status_code == 200
        assert len(backlog.json()) == 0

        audit = client.get("/audit", headers=auth_headers(admin_token))
        assert audit.status_code == 200
        assert len(audit.json()) >= 1

        notifications = client.get("/notifications", headers=auth_headers(tester_token))
        assert notifications.status_code == 200
        assert len(notifications.json()) >= 1

        close_sprint = client.post(f"/sprints/{sprint_id}/close", headers=auth_headers(admin_token))
        assert close_sprint.status_code == 200
