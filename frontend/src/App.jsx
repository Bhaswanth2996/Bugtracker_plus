import { Navigate, Route, Routes } from "react-router-dom";

import AppLayout from "./components/AppLayout";
import ProtectedRoute from "./components/ProtectedRoute";
import AdminSettingsPage from "./pages/AdminSettingsPage";
import BacklogPage from "./pages/BacklogPage";
import CreateIssuePage from "./pages/CreateIssuePage";
import DashboardPage from "./pages/DashboardPage";
import IssueDetailsPage from "./pages/IssueDetailsPage";
import KanbanPage from "./pages/KanbanPage";
import LoginPage from "./pages/LoginPage";
import ProfilePage from "./pages/ProfilePage";
import ProjectDetailsPage from "./pages/ProjectDetailsPage";
import ProjectIssuesPage from "./pages/ProjectIssuesPage";
import ProjectListPage from "./pages/ProjectListPage";
import ProjectMembersPage from "./pages/ProjectMembersPage";
import ProjectReportsPage from "./pages/ProjectReportsPage";
import ProjectSettingsPage from "./pages/ProjectSettingsPage";
import RegisterPage from "./pages/RegisterPage";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/projects" element={<ProjectListPage />} />
          <Route path="/projects/:projectId" element={<ProjectDetailsPage />} />
          <Route path="/projects/:projectId/board" element={<KanbanPage />} />
          <Route path="/projects/:projectId/backlog" element={<BacklogPage />} />
          <Route path="/issues/:issueId" element={<IssueDetailsPage />} />
          <Route path="/project/:projectKey" element={<ProjectIssuesPage />} />
          <Route path="/project/:projectKey/board" element={<KanbanPage />} />
          <Route path="/project/:projectKey/backlog" element={<BacklogPage />} />
          <Route path="/project/:projectKey/reports" element={<ProjectReportsPage />} />
          <Route path="/project/:projectKey/members" element={<ProjectMembersPage />} />
          <Route path="/project/:projectKey/settings" element={<ProjectSettingsPage />} />
          <Route path="/issue/:issueKey" element={<IssueDetailsPage />} />
          <Route path="/create-issue" element={<CreateIssuePage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/admin" element={<AdminSettingsPage />} />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Route>
      </Route>
    </Routes>
  );
}
