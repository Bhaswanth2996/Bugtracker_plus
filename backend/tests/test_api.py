from fastapi.testclient import TestClient

from app.main import app


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_end_to_end_issue_flow() -> None:
    with TestClient(app) as client:
        register_admin = client.post(
            "/api/auth/register",
            json={"name": "Admin User", "email": "admin@example.com", "password": "password123"},
        )
        assert register_admin.status_code == 201
        admin_token = register_admin.json()["access_token"]

        create_project = client.post(
            "/api/projects",
            json={"name": "Core API", "description": "Backend service work"},
            headers=auth_headers(admin_token),
        )
        assert create_project.status_code == 201
        project_id = create_project.json()["id"]

        register_tester = client.post(
            "/api/auth/register",
            json={"name": "QA Tester", "email": "qa@example.com", "password": "password123"},
        )
        assert register_tester.status_code == 201
        tester_token = register_tester.json()["access_token"]
        tester_id = register_tester.json()["user"]["id"]

        list_users = client.get("/api/users", headers=auth_headers(admin_token))
        assert list_users.status_code == 200
        assert len(list_users.json()) == 2

        assign_developer_role = client.patch(
            f"/api/users/{tester_id}/role",
            json={"role": "developer"},
            headers=auth_headers(admin_token),
        )
        assert assign_developer_role.status_code == 200
        assert assign_developer_role.json()["role"] == "developer"

        create_issue = client.post(
            "/api/issues",
            json={
                "project_id": project_id,
                "title": "Fix login refresh bug",
                "description": "Session token does not refresh before expiration.",
                "priority": "high",
                "assignee_id": tester_id,
                "tags": ["auth", "token"],
            },
            headers=auth_headers(admin_token),
        )
        assert create_issue.status_code == 201
        issue_id = create_issue.json()["id"]

        tester_update_issue = client.patch(
            f"/api/issues/{issue_id}",
            json={"status": "in_progress"},
            headers=auth_headers(tester_token),
        )
        assert tester_update_issue.status_code == 200
        assert tester_update_issue.json()["status"] == "in_progress"

        add_comment = client.post(
            "/api/comments",
            json={"issue_id": issue_id, "body": "Investigating token refresh middleware now."},
            headers=auth_headers(tester_token),
        )
        assert add_comment.status_code == 201

        comments = client.get(f"/api/comments/issue/{issue_id}", headers=auth_headers(admin_token))
        assert comments.status_code == 200
        assert len(comments.json()) == 1

        stats = client.get("/api/dashboard/stats", headers=auth_headers(admin_token))
        assert stats.status_code == 200
        assert stats.json()["in_progress_issues"] == 1

        audit = client.get("/api/audit", headers=auth_headers(admin_token))
        assert audit.status_code == 200
        assert len(audit.json()) >= 1
