import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { api, parseApiError } from "../services/api";

export default function CreateIssuePage() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [users, setUsers] = useState([]);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    project_id: "",
    title: "",
    description: "",
    issue_type: "bug",
    priority: "medium",
    assignee_id: "",
    labels: "",
  });

  useEffect(() => {
    async function loadData() {
      try {
        const projectResp = await api.listProjects();
        setProjects(projectResp.data);
        if (projectResp.data.length > 0) {
          setForm((prev) => ({ ...prev, project_id: projectResp.data[0].id }));
        }
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
    loadData();
  }, []);

  async function onSubmit(event) {
    event.preventDefault();
    try {
      const response = await api.createIssue({
        project_id: form.project_id,
        title: form.title,
        description: form.description,
        issue_type: form.issue_type,
        priority: form.priority,
        assignee_id: form.assignee_id || null,
        labels: form.labels
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean),
      });
      navigate(`/issues/${response.data.id}`);
    } catch (err) {
      setError(parseApiError(err));
    }
  }

  return (
    <div className="space-y-4 max-w-4xl">
      <h2 className="text-2xl font-semibold">Create Issue</h2>
      {error && <p className="text-sm text-rose-400">{error}</p>}

      <form
        className="rounded-md border border-slate-800 bg-slate-900 p-4 grid md:grid-cols-2 gap-3"
        onSubmit={onSubmit}
      >
        <select
          className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
          value={form.project_id}
          onChange={(event) =>
            setForm((prev) => ({ ...prev, project_id: event.target.value }))
          }
          required
        >
          {projects.map((project) => (
            <option key={project.id} value={project.id}>
              {project.key} - {project.name}
            </option>
          ))}
        </select>
        <input
          className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
          placeholder="Issue title"
          value={form.title}
          onChange={(event) => setForm((prev) => ({ ...prev, title: event.target.value }))}
          required
        />
        <textarea
          className="md:col-span-2 rounded-md border border-slate-700 bg-slate-950 px-3 py-2 min-h-40"
          placeholder="Issue description"
          value={form.description}
          onChange={(event) =>
            setForm((prev) => ({ ...prev, description: event.target.value }))
          }
          required
        />
        <select
          className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
          value={form.issue_type}
          onChange={(event) =>
            setForm((prev) => ({ ...prev, issue_type: event.target.value }))
          }
        >
          <option value="bug">Bug</option>
          <option value="task">Task</option>
          <option value="story">Story</option>
          <option value="epic">Epic</option>
        </select>
        <select
          className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
          value={form.priority}
          onChange={(event) =>
            setForm((prev) => ({ ...prev, priority: event.target.value }))
          }
        >
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="critical">Critical</option>
        </select>
        <select
          className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
          value={form.assignee_id}
          onChange={(event) =>
            setForm((prev) => ({ ...prev, assignee_id: event.target.value }))
          }
        >
          <option value="">Unassigned</option>
          {users.map((u) => (
            <option key={u.id} value={u.id}>
              {u.name}
            </option>
          ))}
        </select>
        <input
          className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
          placeholder="labels: api,auth"
          value={form.labels}
          onChange={(event) => setForm((prev) => ({ ...prev, labels: event.target.value }))}
        />
        <button className="md:col-span-2 rounded-md bg-brand-600 hover:bg-brand-700 px-3 py-2">
          Create Issue
        </button>
      </form>
    </div>
  );
}
