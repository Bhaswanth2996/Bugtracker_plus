from __future__ import annotations

from collections import Counter

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

from app.core.config import get_settings
from app.core.deps import get_current_user, get_realtime_publisher, get_store
from app.db.store import BaseStore
from app.models.schemas import (
    AIAnalysisLog,
    AIBugAnalyzeRequest,
    AIBugAnalyzeResponse,
    Attachment,
    DuplicateBugRequest,
    DuplicateBugResponse,
    Issue,
    IssueActivity,
    IssueHistoryItem,
    IssuePriority,
    IssueStatus,
    IssueType,
    IssueSearchResult,
    RecommendAssigneeRequest,
    RecommendAssigneeResponse,
    RootCauseAnalysis,
    TestFailureReport,
    UserInDB,
)
from app.services.ai_bug_analyzer import analyze_bug
from app.services.bug_prediction_engine import compute_bug_risk
from app.services.developer_recommendation_engine import (
    developer_workload_insights,
    recommend_assignee,
)
from app.services.duplicate_bug_detector import find_duplicate_issues
from app.services.issue_search import global_issue_search
from app.services.issue_timeline import record_issue_timeline
from app.services.root_cause_analyzer import analyze_root_cause
from app.services.permissions import ensure_project_access
from app.services.realtime import RealtimePublisher

router = APIRouter(prefix="/api", tags=["ai-platform"])


def _validate_ci_token(x_ci_token: str | None) -> None:
    settings = get_settings()
    if not settings.ci_ingest_token:
        return
    if x_ci_token != settings.ci_ingest_token:
        raise HTTPException(status_code=401, detail="Invalid CI ingest token.")


def _reporter_id_for_project(store: BaseStore, project_id: str) -> str:
    project = store.get_project(project_id)
    if not project:
        return "system-ci"
    if store.get_user_by_id(project.created_by):
        return project.created_by
    if project.members:
        first_member_id = project.members[0].user_id
        if store.get_user_by_id(first_member_id):
            return first_member_id
    return "system-ci"


def _infer_module_from_test(test_name: str, error_message: str) -> str:
    blob = f"{test_name} {error_message}".lower()
    if "auth" in blob or "token" in blob or "login" in blob:
        return "authentication"
    if "payment" in blob or "billing" in blob:
        return "payment"
    if "profile" in blob or "user" in blob:
        return "user-profile"
    return "core"


def _ensure_project_access_if_needed(
    store: BaseStore,
    current_user: UserInDB,
    project_id: str | None,
) -> None:
    if project_id:
        ensure_project_access(store, current_user, project_id)


def _visible_project_ids(store: BaseStore, current_user: UserInDB) -> set[str]:
    projects = store.list_projects()
    if current_user.role.value == "admin":
        return {item.id for item in projects}
    return {
        item.id
        for item in projects
        if item.created_by == current_user.id
        or any(member.user_id == current_user.id for member in item.members)
    }


@router.post("/test-failure-report", response_model=Issue, status_code=status.HTTP_201_CREATED)
def ingest_test_failure_report(
    payload: TestFailureReport,
    store: BaseStore = Depends(get_store),
    x_ci_token: str | None = Header(default=None, alias="X-CI-Token"),
    publisher: RealtimePublisher = Depends(get_realtime_publisher),
) -> Issue:
    _validate_ci_token(x_ci_token)

    project = store.get_project_by_key(payload.projectKey)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found for key.")

    reporter_id = _reporter_id_for_project(store, project.id)
    issue = Issue(
        project_id=project.id,
        title=f"Automated Test Failure: {payload.testName}",
        description=(
            f"Automated failure detected from CI/CD pipeline.\n\n"
            f"Error: {payload.errorMessage}\n\nStack Trace:\n{payload.stackTrace[:4000]}"
        ),
        issue_type=IssueType.bug,
        priority=IssuePriority.high,
        status=IssueStatus.todo,
        reporter_id=reporter_id,
        source="CI/CD Pipeline",
        module=_infer_module_from_test(payload.testName, payload.errorMessage),
        labels=["automated-failure", "ci-cd"],
        test_failure_data={
            "testName": payload.testName,
            "errorMessage": payload.errorMessage,
            "stackTrace": payload.stackTrace,
            "logs": payload.logs,
            "screenshotUrl": payload.screenshotUrl,
            "timestamp": payload.timestamp.isoformat(),
        },
    )
    if payload.logs:
        issue.attachments.append(
            Attachment(
                filename=f"{payload.testName}-logs.txt",
                content_type="text/plain",
                blob_url=f"inline://ci/{payload.projectKey}/{payload.testName}/logs",
                uploaded_by="system-ci",
            )
        )
    if payload.screenshotUrl:
        issue.attachments.append(
            Attachment(
                filename=f"{payload.testName}-screenshot.png",
                content_type="image/png",
                blob_url=payload.screenshotUrl,
                uploaded_by="system-ci",
            )
        )
    sequence = store.next_issue_sequence(project.id)
    issue.issue_key = f"{project.key}-{sequence}"
    issue.history.append(
        IssueHistoryItem(
            by=reporter_id,
            action="created.from_ci_failure",
            field="source",
            new_value="CI/CD Pipeline",
        )
    )
    created = store.create_issue(issue)
    store.create_issue_activity(
        IssueActivity(
            issue_id=created.id,
            user_id=reporter_id,
            action="automated_test_failure_ingested",
            metadata={"project_key": payload.projectKey, "test_name": payload.testName},
        )
    )
    record_issue_timeline(
        store,
        issue_id=created.id,
        action="issue_created",
        user_id=reporter_id,
        user_name="CI/CD Pipeline",
        new_value=created.title,
        project_id=created.project_id,
    )
    publisher.publish(
        {
            "event": "issue_created",
            "issueId": created.id,
            "issueKey": created.issue_key,
            "projectId": created.project_id,
            "status": created.status.value,
            "source": created.source,
        }
    )
    return created


@router.post("/ai/analyze-bug", response_model=AIBugAnalyzeResponse)
def analyze_bug_endpoint(
    payload: AIBugAnalyzeRequest,
    project_id: str | None = Query(default=None),
    module: str | None = Query(default=None),
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> AIBugAnalyzeResponse:
    _ensure_project_access_if_needed(store, current_user, project_id)
    return analyze_bug(
        store,
        title=payload.title,
        description=payload.description,
        project_id=project_id,
        module=module,
    )


@router.post("/ai/find-duplicates", response_model=DuplicateBugResponse)
def find_duplicates_endpoint(
    payload: DuplicateBugRequest,
    project_id: str | None = Query(default=None),
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> DuplicateBugResponse:
    _ensure_project_access_if_needed(store, current_user, project_id)
    duplicates = find_duplicate_issues(
        store,
        title=payload.title,
        description=payload.description,
        project_id=project_id,
    )
    response = DuplicateBugResponse(duplicates=duplicates)
    store.create_ai_analysis_log(
        AIAnalysisLog(
            analysis_type="find_duplicates",
            payload={"title": payload.title, "description": payload.description[:250], "project_id": project_id},
            result=response.model_dump(mode="json"),
        )
    )
    return response


@router.post("/ai/recommend-assignee", response_model=RecommendAssigneeResponse)
def recommend_assignee_endpoint(
    payload: RecommendAssigneeRequest,
    project_id: str | None = Query(default=None),
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> RecommendAssigneeResponse:
    _ensure_project_access_if_needed(store, current_user, project_id)
    response = recommend_assignee(
        store,
        module=payload.module,
        description=payload.description,
        project_id=project_id,
    )
    store.create_ai_analysis_log(
        AIAnalysisLog(
            analysis_type="recommend_assignee",
            payload={"module": payload.module, "description": payload.description[:250], "project_id": project_id},
            result=response.model_dump(mode="json"),
        )
    )
    return response


@router.get("/issues/{issue_id}/root-cause")
def get_root_cause_endpoint(
    issue_id: str,
    refresh: bool = Query(default=False),
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> dict:
    issue = store.get_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found.")
    ensure_project_access(store, current_user, issue.project_id)
    try:
        analysis = analyze_root_cause(store, issue_id=issue_id, refresh=refresh)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "suspectedCommit": analysis.suspected_commit,
        "author": analysis.author,
        "filesModified": analysis.files_modified,
        "confidence": analysis.confidence,
        "analyzedAt": analysis.analyzed_at,
    }


@router.get("/issues/{issue_id}/timeline")
def issue_timeline_endpoint(
    issue_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> list[dict]:
    issue = store.get_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found.")
    ensure_project_access(store, current_user, issue.project_id)
    items = store.list_issue_timeline(issue_id, limit=limit)
    return [item.model_dump(mode="json") for item in items]


@router.get("/issues/search", response_model=list[IssueSearchResult])
def global_issue_search_endpoint(
    q: str | None = Query(default=None, min_length=1),
    status: IssueStatus | None = Query(default=None),
    priority: IssuePriority | None = Query(default=None),
    assignee: str | None = Query(default=None),
    project: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> list[IssueSearchResult]:
    return global_issue_search(
        store,
        current_user=current_user,
        q=q,
        status=status,
        priority=priority,
        assignee_id=assignee,
        project=project,
        limit=limit,
    )


@router.get("/analytics/bug-risk")
def bug_risk_analytics(
    project_id: str | None = Query(default=None),
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> list[dict]:
    _ensure_project_access_if_needed(store, current_user, project_id)
    return [item.model_dump(mode="json") for item in compute_bug_risk(store, project_id=project_id)]


@router.get("/analytics/automated-test-failures")
def recent_automated_failures(
    project_id: str | None = Query(default=None),
    limit: int = Query(default=6, ge=1, le=50),
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> list[Issue]:
    _ensure_project_access_if_needed(store, current_user, project_id)
    issues = store.list_issues(project_id=project_id)
    filtered = [issue for issue in issues if (issue.source or "").lower() == "ci/cd pipeline"]
    filtered.sort(key=lambda item: item.created_at, reverse=True)
    return filtered[:limit]


@router.get("/analytics/root-cause-insights")
def recent_root_cause_insights(
    limit: int = Query(default=6, ge=1, le=50),
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> list[RootCauseAnalysis]:
    _ = current_user
    return store.list_root_cause_analysis(limit=limit)


@router.get("/analytics/recent-activity-timeline")
def recent_activity_timeline(
    project_id: str | None = Query(default=None),
    limit: int = Query(default=15, ge=1, le=100),
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> list[dict]:
    _ensure_project_access_if_needed(store, current_user, project_id)
    visible_project_ids = _visible_project_ids(store, current_user)
    items = store.list_recent_timeline(project_id=project_id, limit=max(limit * 3, limit))
    visible = [item for item in items if (not item.project_id) or item.project_id in visible_project_ids]
    return [item.model_dump(mode="json") for item in visible[:limit]]


@router.get("/analytics/developer-workload")
def developer_workload_endpoint(
    project_id: str | None = Query(default=None),
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> list[dict]:
    _ensure_project_access_if_needed(store, current_user, project_id)
    return developer_workload_insights(store, project_id=project_id)


@router.get("/analytics/ai-insights")
def ai_insights_endpoint(
    limit: int = Query(default=30, ge=1, le=200),
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> dict:
    _ = current_user
    logs = store.list_ai_analysis_logs(limit=limit)
    counts = Counter(item.analysis_type for item in logs)
    duplicate_logs = [item for item in logs if item.analysis_type == "find_duplicates"]
    duplicate_hits = 0
    for row in duplicate_logs:
        duplicates = row.result.get("duplicates", []) if isinstance(row.result, dict) else []
        duplicate_hits += len(duplicates)
    return {
        "countsByType": dict(counts),
        "duplicateDetections": duplicate_hits,
        "recentLogs": [item.model_dump(mode="json") for item in logs[:8]],
    }


@router.get("/analytics/advanced-dashboard")
def advanced_dashboard(
    project_id: str | None = Query(default=None),
    current_user: UserInDB = Depends(get_current_user),
    store: BaseStore = Depends(get_store),
) -> dict:
    _ensure_project_access_if_needed(store, current_user, project_id)
    issues = store.list_issues(project_id=project_id)
    recent_failures = [item for item in issues if (item.source or "").lower() == "ci/cd pipeline"]
    recent_failures.sort(key=lambda item: item.created_at, reverse=True)
    ai_logs = store.list_ai_analysis_logs(limit=50)
    ai_counts = Counter(item.analysis_type for item in ai_logs)
    duplicate_detection_stats = {
        "totalAnalyses": len(ai_logs),
        "duplicateRequests": ai_counts.get("find_duplicates", 0),
        "analyzeBugRequests": ai_counts.get("analyze_bug", 0),
    }
    recent_timeline = store.list_recent_timeline(project_id=project_id, limit=12)
    return {
        "automatedTestFailures": [item.model_dump(mode="json") for item in recent_failures[:6]],
        "aiBugInsights": dict(ai_counts),
        "bugRiskPrediction": [item.model_dump(mode="json") for item in compute_bug_risk(store, project_id=project_id)],
        "rootCauseInsights": [item.model_dump(mode="json") for item in store.list_root_cause_analysis(limit=6)],
        "duplicateBugDetectionStats": duplicate_detection_stats,
        "developerWorkloadInsights": developer_workload_insights(store, project_id=project_id),
        "recentActivityTimeline": [item.model_dump(mode="json") for item in recent_timeline],
        "liveIssueUpdates": {
            "message": "Connected clients receive live updates on /ws/issues",
            "websocket": "/ws/issues",
        },
        "searchQuickAccess": {
            "endpoint": "/api/issues/search",
            "placeholder": "Search issues...",
        },
    }
