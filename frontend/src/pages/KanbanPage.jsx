import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";

import KanbanColumn from "../components/KanbanColumn";
import { api, parseApiError } from "../services/api";

export default function KanbanPage() {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const [issues, setIssues] = useState([]);
  const [error, setError] = useState("");
  const [assigneeFilter, setAssigneeFilter] = useState("");
  const [users, setUsers] = useState([]);

  async function loadBoard() {
    try {
      const [projectResp, issuesResp] = await Promise.all([
        api.getProject(projectId),
        api.listIssues({ project_id: projectId }),
      ]);
      setProject(projectResp.data);
      setIssues(issuesResp.data);
      setError("");

      try {
        const usersResp = await api.listUsers();
        setUsers(usersResp.data);
      } catch {
        setUsers([]);
      }
    } catch (err) {
      setError(parseApiError(err));
    }
  }

  useEffect(() => {
    loadBoard();
  }, [projectId]);

  const filtered = useMemo(() => {
    if (!assigneeFilter) {
      return issues;
    }
    return issues.filter((issue) => issue.assignee_id === assigneeFilter);
  }, [issues, assigneeFilter]);

  async function onDropIssue(issueId, newStatus) {
    try {
      const issue = issues.find((item) => item.id === issueId);
      if (!issue || issue.status === newStatus) {
        return;
      }
      const response = await api.updateIssue(issueId, { status: newStatus });
      setIssues((prev) =>
        prev.map((item) => (item.id === issueId ? response.data : item))
      );
    } catch (err) {
      setError(parseApiError(err));
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-2xl font-semibold">
          Kanban Board - {project?.key || "PRJ"}
        </h2>
        <div className="flex gap-2 items-center">
          <label className="text-sm text-slate-400" htmlFor="assignee-filter">
            Assignee
          </label>
          <select
            id="assignee-filter"
            className="rounded-md border border-slate-700 bg-slate-900 px-2 py-1 text-sm"
            value={assigneeFilter}
            onChange={(event) => setAssigneeFilter(event.target.value)}
          >
            <option value="">All</option>
            {users.map((user) => (
              <option key={user.id} value={user.id}>
                {user.name}
              </option>
            ))}
          </select>
        </div>
      </div>
      {error && <p className="text-sm text-rose-400">{error}</p>}
      <div className="grid md:grid-cols-3 gap-3">
        <KanbanColumn
          title="To Do"
          status="todo"
          issues={filtered.filter((item) => item.status === "todo")}
          onDropIssue={onDropIssue}
        />
        <KanbanColumn
          title="In Progress"
          status="in_progress"
          issues={filtered.filter((item) => item.status === "in_progress")}
          onDropIssue={onDropIssue}
        />
        <KanbanColumn
          title="Done"
          status="done"
          issues={filtered.filter((item) => item.status === "done")}
          onDropIssue={onDropIssue}
        />
      </div>
    </div>
  );
}
