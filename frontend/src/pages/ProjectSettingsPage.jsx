import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import ProjectWorkspaceTabs from "../components/ProjectWorkspaceTabs";
import { useAuth } from "../context/AuthContext";
import { api, parseApiError } from "../services/api";
import { useProjectResolver } from "../utils/useProjectResolver";

const managerRoles = new Set(["admin", "project_manager"]);

export default function ProjectSettingsPage() {
  const { projectKey } = useParams();
  const { user } = useAuth();
  const { project, projectError } = useProjectResolver(null, projectKey);
  const [form, setForm] = useState({ name: "", description: "" });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!project) {
      return;
    }
    setForm({ name: project.name, description: project.description || "" });
  }, [project]);

  useEffect(() => {
    if (projectError) {
      setError(projectError);
    }
  }, [projectError]);

  async function saveSettings(event) {
    event.preventDefault();
    try {
      await api.updateProject(project.id, form);
      setMessage("Project settings saved.");
      setError("");
    } catch (err) {
      setError(parseApiError(err));
      setMessage("");
    }
  }

  if (!project) {
    return <div className="text-slate-300">Loading project settings...</div>;
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">{project.key} Settings</h2>
      <ProjectWorkspaceTabs projectKey={project.key} />
      {error && <p className="text-sm text-rose-400">{error}</p>}
      {message && <p className="text-sm text-emerald-400">{message}</p>}

      <form
        onSubmit={saveSettings}
        className="rounded-xl border border-slate-800 bg-slate-900 p-4 space-y-3 max-w-2xl"
      >
        <div>
          <label className="text-sm text-slate-400">Project Name</label>
          <input
            className="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
            value={form.name}
            onChange={(event) =>
              setForm((prev) => ({ ...prev, name: event.target.value }))
            }
            disabled={!managerRoles.has(user?.role)}
          />
        </div>
        <div>
          <label className="text-sm text-slate-400">Description</label>
          <textarea
            className="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 min-h-28"
            value={form.description}
            onChange={(event) =>
              setForm((prev) => ({ ...prev, description: event.target.value }))
            }
            disabled={!managerRoles.has(user?.role)}
          />
        </div>
        {managerRoles.has(user?.role) ? (
          <button className="rounded-md bg-brand-600 hover:bg-brand-700 px-3 py-2">
            Save
          </button>
        ) : (
          <p className="text-xs text-slate-500">
            You need project_manager/admin role to modify settings.
          </p>
        )}
      </form>
    </div>
  );
}
