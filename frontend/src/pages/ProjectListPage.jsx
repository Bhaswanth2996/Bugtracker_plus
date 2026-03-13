import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { api, parseApiError } from "../services/api";

const managerRoles = new Set(["admin", "project_manager"]);

export default function ProjectListPage() {
  const { user } = useAuth();
  const [projects, setProjects] = useState([]);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ key: "", name: "", description: "" });

  async function loadProjects() {
    try {
      const response = await api.listProjects();
      setProjects(response.data);
      setError("");
    } catch (err) {
      setError(parseApiError(err));
    }
  }

  useEffect(() => {
    loadProjects();
  }, []);

  async function onCreateProject(event) {
    event.preventDefault();
    try {
      await api.createProject({
        key: form.key.toUpperCase(),
        name: form.name,
        description: form.description,
      });
      setForm({ key: "", name: "", description: "" });
      loadProjects();
    } catch (err) {
      setError(parseApiError(err));
    }
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">Project List</h2>
      {error && <p className="text-sm text-rose-400">{error}</p>}

      {managerRoles.has(user?.role) && (
        <form
          className="rounded-md border border-slate-800 bg-slate-900 p-4 grid md:grid-cols-4 gap-2"
          onSubmit={onCreateProject}
        >
          <input
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
            placeholder="KEY"
            value={form.key}
            onChange={(event) =>
              setForm((prev) => ({ ...prev, key: event.target.value }))
            }
            required
          />
          <input
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
            placeholder="Project Name"
            value={form.name}
            onChange={(event) =>
              setForm((prev) => ({ ...prev, name: event.target.value }))
            }
            required
          />
          <input
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
            placeholder="Description"
            value={form.description}
            onChange={(event) =>
              setForm((prev) => ({ ...prev, description: event.target.value }))
            }
          />
          <button className="rounded-md bg-brand-600 hover:bg-brand-700 px-3 py-2">
            Create Project
          </button>
        </form>
      )}

      <section className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
        {projects.map((project) => (
          <Link
            key={project.id}
            to={`/project/${project.key}`}
            className="rounded-md border border-slate-800 bg-slate-900 p-4 hover:bg-slate-800"
          >
            <p className="text-sm text-slate-400">{project.key}</p>
            <p className="text-lg font-semibold mt-1">{project.name}</p>
            <p className="text-sm text-slate-400 mt-2">{project.description}</p>
          </Link>
        ))}
      </section>
    </div>
  );
}
