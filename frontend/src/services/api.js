import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "https://bugtracker-backend-je6w.onrender.com";

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
});

export function setAuthToken(token) {
  if (token) {
    client.defaults.headers.common.Authorization = `Bearer ${token}`;
  } else {
    delete client.defaults.headers.common.Authorization;
  }
}

export function parseApiError(error) {
  if (error?.response?.data?.detail) {
    return error.response.data.detail;
  }
  if (typeof error?.message === "string") {
    return error.message;
  }
  return "Request failed.";
}

export const api = {
  register: (payload) => client.post("/auth/register", payload),
  login: (payload) => client.post("/auth/login", payload),
  me: () => client.get("/auth/me"),

  listUsers: () => client.get("/users"),
  getUser: (userId) => client.get(`/users/${userId}`),
  updateProfile: (payload) => client.put("/users/me/profile", payload),
  updateUserRole: (userId, role) => client.put(`/users/${userId}/role`, { role }),

  createProject: (payload) => client.post("/projects", payload),
  listProjects: () => client.get("/projects"),
  getProject: (projectId) => client.get(`/projects/${projectId}`),
  getProjectByKey: (projectKey) => client.get(`/projects/key/${projectKey}`),
  updateProject: (projectId, payload) => client.put(`/projects/${projectId}`, payload),
  addProjectMember: (projectId, payload) =>
    client.post(`/projects/${projectId}/members`, payload),

  createIssue: (payload) => client.post("/issues", payload),
  listIssues: (params) => client.get("/issues", { params }),
  getIssue: (issueId) => client.get(`/issues/${issueId}`),
  getIssueByKey: (issueKey) => client.get(`/issues/key/${issueKey}`),
  updateIssue: (issueId, payload) => client.put(`/issues/${issueId}`, payload),
  deleteIssue: (issueId) => client.delete(`/issues/${issueId}`),
  searchIssues: (params) => client.get("/api/issues/search", { params }),
  moveIssueToSprint: (issueId, payload) => client.put(`/issues/${issueId}/sprint`, payload),
  listIssueActivity: (issueId) => client.get(`/issues/${issueId}/activity`),
  getIssueTimeline: (issueId, limit = 100) =>
    client.get(`/api/issues/${issueId}/timeline`, { params: { limit } }),
  listIssueLinks: (issueId) => client.get(`/issues/${issueId}/links`),
  createIssueLink: (issueId, payload) => client.post(`/issues/${issueId}/links`, payload),
  deleteIssueLink: (issueId, linkId) => client.delete(`/issues/${issueId}/links/${linkId}`),
  uploadAttachment: (issueId, file) => {
    const formData = new FormData();
    formData.append("file", file);
    return client.post(`/issues/${issueId}/attachments`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  listComments: (issueId) => client.get(`/comments/${issueId}`),
  createComment: (payload) => client.post("/comments", payload),
  updateComment: (commentId, payload) => client.put(`/comments/${commentId}`, payload),
  deleteComment: (commentId) => client.delete(`/comments/${commentId}`),

  createSprint: (payload) => client.post("/sprints", payload),
  listSprints: (projectId) => client.get("/sprints", { params: { project_id: projectId } }),
  updateSprint: (sprintId, payload) => client.put(`/sprints/${sprintId}`, payload),
  startSprint: (sprintId) => client.post(`/sprints/${sprintId}/start`),
  closeSprint: (sprintId) => client.post(`/sprints/${sprintId}/close`),
  getBacklog: (projectId) => client.get(`/projects/${projectId}/backlog`),
  reorderBacklog: (projectId, items) =>
    client.put(`/projects/${projectId}/backlog/reorder`, { items }),

  getProjectDashboard: (projectId) => client.get(`/projects/${projectId}/dashboard`),
  getProjectReports: (projectId) => client.get(`/projects/${projectId}/reports`),
  getGlobalDashboard: () => client.get("/dashboard"),
  getAdvancedDashboard: (projectId) =>
    client.get("/api/analytics/advanced-dashboard", {
      params: projectId ? { project_id: projectId } : {},
    }),
  getBugRiskPrediction: (projectId) =>
    client.get("/api/analytics/bug-risk", {
      params: projectId ? { project_id: projectId } : {},
    }),
  getAutomatedTestFailures: (projectId, limit = 6) =>
    client.get("/api/analytics/automated-test-failures", {
      params: { ...(projectId ? { project_id: projectId } : {}), limit },
    }),
  getRootCauseInsights: (limit = 6) =>
    client.get("/api/analytics/root-cause-insights", { params: { limit } }),
  getDeveloperWorkloadInsights: (projectId) =>
    client.get("/api/analytics/developer-workload", {
      params: projectId ? { project_id: projectId } : {},
    }),
  getAiInsights: (limit = 30) => client.get("/api/analytics/ai-insights", { params: { limit } }),
  getRecentActivityTimeline: (projectId, limit = 15) =>
    client.get("/api/analytics/recent-activity-timeline", {
      params: { ...(projectId ? { project_id: projectId } : {}), limit },
    }),
  analyzeBug: (payload, projectId, module) =>
    client.post("/api/ai/analyze-bug", payload, {
      params: {
        ...(projectId ? { project_id: projectId } : {}),
        ...(module ? { module } : {}),
      },
    }),
  findDuplicates: (payload, projectId) =>
    client.post("/api/ai/find-duplicates", payload, {
      params: projectId ? { project_id: projectId } : {},
    }),
  recommendAssignee: (payload, projectId) =>
    client.post("/api/ai/recommend-assignee", payload, {
      params: projectId ? { project_id: projectId } : {},
    }),
  getIssueRootCause: (issueId, refresh = false) =>
    client.get(`/api/issues/${issueId}/root-cause`, { params: { refresh } }),
  reportTestFailure: (payload, ciToken) =>
    client.post("/api/test-failure-report", payload, {
      headers: ciToken ? { "X-CI-Token": ciToken } : {},
    }),
  getAuditLogs: (params) => client.get("/audit", { params }),

  listNotifications: () => client.get("/notifications"),
  markNotificationRead: (notificationId) =>
    client.put(`/notifications/${notificationId}/read`),
};
