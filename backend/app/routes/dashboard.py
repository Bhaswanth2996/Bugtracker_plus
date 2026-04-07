from fastapi import APIRouter, Depends

from app.core.deps import get_current_user, get_store
from app.db.store import BaseStore
from app.models.schemas import DashboardStats, UserInDB
from app.services.permissions import ensure_project_access

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
project_router = APIRouter(prefix="/projects", tags=["dashboard"])


@router.get("", response_model=DashboardStats)
def get_global_dashboard_stats(
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> DashboardStats:
    return store.get_dashboard_stats(current_user_id=current_user.id)


@project_router.get("/{project_id}/dashboard", response_model=DashboardStats)
def get_project_dashboard_stats(
    project_id: str,
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> DashboardStats:
    ensure_project_access(store, current_user, project_id)
    return store.get_dashboard_stats(project_id=project_id, current_user_id=current_user.id)


@project_router.get("/{project_id}/reports")
def get_project_reports(
    project_id: str,
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> dict:
    ensure_project_access(store, current_user, project_id)
    issues = store.list_issues(project_id=project_id)
    sprints = store.list_sprints(project_id=project_id)

    status_counts: dict[str, int] = {"todo": 0, "in_progress": 0, "done": 0}
    priority_counts: dict[str, int] = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for issue in issues:
        status_counts[issue.status.value] = status_counts.get(issue.status.value, 0) + 1
        priority_counts[issue.priority.value] = priority_counts.get(issue.priority.value, 0) + 1

    active_sprint = next((item for item in sprints if item.status.value == "active"), None)
    burndown = []
    if active_sprint:
        sprint_issues = [issue for issue in issues if issue.sprint_id == active_sprint.id]
        total = len(sprint_issues)
        done = sum(1 for issue in sprint_issues if issue.status.value == "done")
        remaining = max(total - done, 0)
        burndown = [
            {"name": "Start", "remaining": total},
            {"name": "Today", "remaining": remaining},
            {"name": "Target", "remaining": 0},
        ]

    velocity = []
    for sprint in sprints[:6]:
        sprint_done = sum(
            1
            for issue in issues
            if issue.sprint_id == sprint.id and issue.status.value == "done"
        )
        velocity.append({"name": sprint.name, "completed": sprint_done})

    return {
        "issues_by_status": [{"name": key, "value": value} for key, value in status_counts.items()],
        "issues_by_priority": [{"name": key, "value": value} for key, value in priority_counts.items()],
        "sprint_burndown": burndown,
        "velocity": velocity,
    }
