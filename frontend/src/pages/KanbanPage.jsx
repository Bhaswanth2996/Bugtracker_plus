import { DndContext } from "@dnd-kit/core";
import { Filter, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";

import KanbanColumn from "../components/KanbanColumn";
import { api, parseApiError } from "../services/api";
import { useProjectResolver } from "../utils/useProjectResolver";

export default function KanbanPage() {
  const { projectId, projectKey } = useParams();
  const { project, projectError } = useProjectResolver(projectId, projectKey);
  const [issues, setIssues] = useState([]);
  const [error, setError] = useState("");
  const [assigneeFilter, setAssigneeFilter] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");
  const [labelFilter, setLabelFilter] = useState("");
  const [search, setSearch] = useState("");
  const [users, setUsers] = useState([]);

  async function loadBoard() {
    try {
      if (!project?.id) {
        return;
      }
      const issuesResp = await api.listIssues({
        project_id: project.id,
        assignee_id: assigneeFilter || undefined,
        priority: priorityFilter || undefined,
        labels: labelFilter || undefined,
        search: search || undefined,
      });
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
  }, [project?.id, assigneeFilter, priorityFilter, labelFilter, search]);

  useEffect(() => {
    if (projectError) {
      setError(projectError);
    }
  }, [projectError]);

  const userMap = useMemo(
    () => Object.fromEntries(users.map((user) => [user.id, user])),
    [users]
  );

  async function onMoveIssue(issueId, newStatus) {
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

  async function onDragEnd(event) {
    const issueId = event.active?.id;
    const destination = event.over?.id;
    if (!issueId || !destination) {
      return;
    }
    await onMoveIssue(issueId, destination);
  }

  const labels = Array.from(
    new Set(issues.flatMap((issue) => issue.labels || []))
  ).sort((a, b) => a.localeCompare(b));

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-2xl font-semibold">
          Kanban Board - {project?.key || "PRJ"}
        </h2>
        <div className="flex flex-wrap gap-2 items-center">
          <div className="relative">
            <Search className="h-4 w-4 absolute left-2 top-2.5 text-slate-500" />
            <input
              className="rounded-md border border-slate-700 bg-slate-900 pl-8 pr-2 py-1.5 text-sm"
              placeholder="Search issues..."
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </div>
          <Filter className="h-4 w-4 text-slate-400" />
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
          <select
            className="rounded-md border border-slate-700 bg-slate-900 px-2 py-1 text-sm"
            value={priorityFilter}
            onChange={(event) => setPriorityFilter(event.target.value)}
          >
            <option value="">Any priority</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
          <select
            className="rounded-md border border-slate-700 bg-slate-900 px-2 py-1 text-sm"
            value={labelFilter}
            onChange={(event) => setLabelFilter(event.target.value)}
          >
            <option value="">Any label</option>
            {labels.map((label) => (
              <option key={label} value={label}>
                {label}
              </option>
            ))}
          </select>
        </div>
      </div>
      {error && <p className="text-sm text-rose-400">{error}</p>}
      <DndContext onDragEnd={onDragEnd}>
        <div className="grid md:grid-cols-3 gap-3">
          <KanbanColumn
            title={`To Do (${issues.filter((item) => item.status === "todo").length})`}
            droppableId="todo"
            issues={issues.filter((item) => item.status === "todo")}
            projectMap={{ [project?.id]: project }}
            userMap={userMap}
          />
          <KanbanColumn
            title={`In Progress (${issues.filter((item) => item.status === "in_progress").length})`}
            droppableId="in_progress"
            issues={issues.filter((item) => item.status === "in_progress")}
            projectMap={{ [project?.id]: project }}
            userMap={userMap}
          />
          <KanbanColumn
            title={`Done (${issues.filter((item) => item.status === "done").length})`}
            droppableId="done"
            issues={issues.filter((item) => item.status === "done")}
            projectMap={{ [project?.id]: project }}
            userMap={userMap}
          />
        </div>
      </DndContext>
    </div>
  );
}
