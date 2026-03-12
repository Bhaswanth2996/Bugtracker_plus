import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { api, parseApiError } from "../services/api";

const managerRoles = new Set(["admin", "project_manager"]);

export default function ProjectDetailsPage() {
  const { projectId } = useParams();
  const { user } = useAuth();
  const [project, setProject] = useState(null);
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState("");
  const [selectedRole, setSelectedRole] = useState("developer");
  const [error, setError] = useState("");

  async function loadData() {
    try {
      const [projectResp, statsResp] = await Promise.all([
        api.getProject(projectId),
        api.getProjectDashboard(projectId),
      ]);
      setProject(projectResp.data);
      setStats(statsResp.data);
      setError("");
      if (managerRoles.has(user?.role)) {
        const usersResp = await api.listUsers();
        setUsers(usersResp.data);
      }
    } catch (err) {
      setError(parseApiError(err));
    }
  }

  useEffect(() => {
    loadData();
  }, [projectId]);

  async function onAddMember(event) {
    event.preventDefault();
    try {
      await api.addProjectMember(projectId, { user_id: selectedUser, role: selectedRole });
      setSelectedUser("");
      setSelectedRole("developer");
      loadData();
    } catch (err) {
      setError(parseApiError(err));
    }
  }

  if (!project) {
    return <div className="text-slate-300">Loading project...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold">
            {project.key} - {project.name}
          </h2>
          <p className="text-slate-400 mt-1">{project.description}</p>
        </div>
        <div className="flex gap-2">
          <Link
            to={`/projects/${projectId}/board`}
            className="rounded-md bg-brand-600 hover:bg-brand-700 px-3 py-2 text-sm"
          >
            Open Board
          </Link>
          <Link
            to={`/projects/${projectId}/backlog`}
            className="rounded-md border border-slate-700 px-3 py-2 text-sm hover:bg-slate-800"
          >
            Open Backlog
          </Link>
        </div>
      </div>

      {error && <p className="text-sm text-rose-400">{error}</p>}

      {stats && (
        <section className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <Stat title="Total" value={stats.total_issues} />
          <Stat title="To Do" value={stats.todo_issues} />
          <Stat title="In Progress" value={stats.in_progress_issues} />
          <Stat title="Done" value={stats.done_issues} />
        </section>
      )}

      <section className="rounded-md border border-slate-800 bg-slate-900 p-4">
        <h3 className="font-semibold mb-2">Team Members</h3>
        <div className="space-y-2">
          {(project.members || []).map((member) => (
            <div
              key={`${member.user_id}-${member.role}`}
              className="rounded-md border border-slate-800 bg-slate-950 px-3 py-2 text-sm flex justify-between"
            >
              <span>{member.user_id}</span>
              <span className="text-slate-400">{member.role}</span>
            </div>
          ))}
        </div>
      </section>

      {managerRoles.has(user?.role) && (
        <form
          onSubmit={onAddMember}
          className="rounded-md border border-slate-800 bg-slate-900 p-4 grid md:grid-cols-3 gap-2"
        >
          <select
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
            value={selectedUser}
            onChange={(event) => setSelectedUser(event.target.value)}
            required
          >
            <option value="">Select user</option>
            {users.map((u) => (
              <option key={u.id} value={u.id}>
                {u.name} ({u.email})
              </option>
            ))}
          </select>
          <select
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
            value={selectedRole}
            onChange={(event) => setSelectedRole(event.target.value)}
          >
            <option value="project_manager">project_manager</option>
            <option value="developer">developer</option>
            <option value="tester">tester</option>
          </select>
          <button className="rounded-md bg-brand-600 hover:bg-brand-700 px-3 py-2 text-sm">
            Add Member
          </button>
        </form>
      )}
    </div>
  );
}

function Stat({ title, value }) {
  return (
    <div className="rounded-md border border-slate-800 bg-slate-900 p-3">
      <p className="text-xs text-slate-400">{title}</p>
      <p className="text-xl font-semibold">{value}</p>
    </div>
  );
}
