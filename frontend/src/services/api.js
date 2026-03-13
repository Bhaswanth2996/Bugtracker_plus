import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

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
  moveIssueToSprint: (issueId, payload) => client.put(`/issues/${issueId}/sprint`, payload),
  listIssueActivity: (issueId) => client.get(`/issues/${issueId}/activity`),
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
  getAuditLogs: (params) => client.get("/audit", { params }),

  listNotifications: () => client.get("/notifications"),
  markNotificationRead: (notificationId) =>
    client.put(`/notifications/${notificationId}/read`),
};
