import { useEffect, useMemo, useState } from "react";
import { Search } from "lucide-react";
import { useParams } from "react-router-dom";

import IssueCard from "../components/IssueCard";
import ProjectWorkspaceTabs from "../components/ProjectWorkspaceTabs";
import { api, parseApiError } from "../services/api";
import { useProjectResolver } from "../utils/useProjectResolver";

export default function ProjectIssuesPage() {
  const { projectKey } = useParams();
  const { project, projectError } = useProjectResolver(null, projectKey);
  const [issues, setIssues] = useState([]);
  const [users, setUsers] = useState([]);
  const [filters, setFilters] = useState({
    status: "",
    priority: "",
    assignee: "",
    label: "",
    search: "",
  });
  const [error, setError] = useState("");

  async function loadIssues() {
    try {
      if (!project?.id) {
        return;
      }
      const response = await api.listIssues({
        project_id: project.id,
        status: filters.status || undefined,
        priority: filters.priority || undefined,
        assignee_id: filters.assignee || undefined,
        labels: filters.label || undefined,
        search: filters.search || undefined,
      });
      setIssues(response.data);
      const usersResponse = await api.listUsers().catch(() => ({ data: [] }));
      setUsers(usersResponse.data);
      setError("");
    } catch (err) {
      setError(parseApiError(err));
    }
  }

  useEffect(() => {
    loadIssues();
  }, [project?.id, filters]);

  useEffect(() => {
    if (projectError) {
      setError(projectError);
    }
  }, [projectError]);

  const userMap = useMemo(
    () => Object.fromEntries(users.map((item) => [item.id, item])),
    [users]
  );
  const labelOptions = Array.from(
    new Set(issues.flatMap((issue) => issue.labels || []))
  ).sort((a, b) => a.localeCompare(b));

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">{project?.key} Workspace</h2>
      {project?.key ? <ProjectWorkspaceTabs projectKey={project.key} /> : null}
      {error && <p className="text-sm text-rose-400">{error}</p>}

      <section className="rounded-xl border border-slate-800 bg-slate-900 p-3 grid md:grid-cols-5 gap-2">
        <div className="relative md:col-span-2">
          <Search className="h-4 w-4 absolute left-2 top-2.5 text-slate-500" />
          <input
            className="w-full rounded-md border border-slate-700 bg-slate-950 pl-8 pr-2 py-2 text-sm"
            placeholder="JQL-like search (title/description)"
            value={filters.search}
            onChange={(event) =>
              setFilters((prev) => ({ ...prev, search: event.target.value }))
            }
          />
        </div>
        <select
          className="rounded-md border border-slate-700 bg-slate-950 px-2 py-2 text-sm"
          value={filters.status}
          onChange={(event) =>
            setFilters((prev) => ({ ...prev, status: event.target.value }))
          }
        >
          <option value="">Any status</option>
          <option value="todo">To Do</option>
          <option value="in_progress">In Progress</option>
          <option value="done">Done</option>
        </select>
        <select
          className="rounded-md border border-slate-700 bg-slate-950 px-2 py-2 text-sm"
          value={filters.priority}
          onChange={(event) =>
            setFilters((prev) => ({ ...prev, priority: event.target.value }))
          }
        >
          <option value="">Any priority</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="critical">Critical</option>
        </select>
        <select
          className="rounded-md border border-slate-700 bg-slate-950 px-2 py-2 text-sm"
          value={filters.assignee}
          onChange={(event) =>
            setFilters((prev) => ({ ...prev, assignee: event.target.value }))
          }
        >
          <option value="">Any assignee</option>
          {users.map((user) => (
            <option key={user.id} value={user.id}>
              {user.name}
            </option>
          ))}
        </select>
        <select
          className="rounded-md border border-slate-700 bg-slate-950 px-2 py-2 text-sm"
          value={filters.label}
          onChange={(event) =>
            setFilters((prev) => ({ ...prev, label: event.target.value }))
          }
        >
          <option value="">Any label</option>
          {labelOptions.map((label) => (
            <option key={label} value={label}>
              {label}
            </option>
          ))}
        </select>
      </section>

      <section className="grid md:grid-cols-2 xl:grid-cols-3 gap-3">
        {issues.map((issue) => (
          <IssueCard
            key={issue.id}
            issue={issue}
            projectMap={{ [project?.id]: project }}
            assigneeName={userMap[issue.assignee_id]?.name}
          />
        ))}
      </section>
    </div>
  );
}
