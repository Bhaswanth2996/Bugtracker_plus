import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import ProjectWorkspaceTabs from "../components/ProjectWorkspaceTabs";
import { useAuth } from "../context/AuthContext";
import { api, parseApiError } from "../services/api";
import { useProjectResolver } from "../utils/useProjectResolver";

const managerRoles = new Set(["admin", "project_manager"]);

export default function ProjectMembersPage() {
  const { projectKey } = useParams();
  const { user } = useAuth();
  const { project, projectError } = useProjectResolver(null, projectKey);
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState("");
  const [selectedRole, setSelectedRole] = useState("developer");
  const [error, setError] = useState("");

  async function loadUsers() {
    try {
      if (!managerRoles.has(user?.role)) {
        return;
      }
      const response = await api.listUsers();
      setUsers(response.data);
    } catch (err) {
      setError(parseApiError(err));
    }
  }

  useEffect(() => {
    loadUsers();
  }, [user?.role]);

  useEffect(() => {
    if (projectError) {
      setError(projectError);
    }
  }, [projectError]);

  async function addMember(event) {
    event.preventDefault();
    try {
      await api.addProjectMember(project.id, { user_id: selectedUser, role: selectedRole });
      setSelectedUser("");
      setSelectedRole("developer");
      window.location.reload();
    } catch (err) {
      setError(parseApiError(err));
    }
  }

  if (!project) {
    return <div className="text-slate-300">Loading project members...</div>;
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">{project.key} Members</h2>
      <ProjectWorkspaceTabs projectKey={project.key} />
      {error && <p className="text-sm text-rose-400">{error}</p>}

      <section className="rounded-xl border border-slate-800 bg-slate-900 p-4">
        <h3 className="font-semibold mb-3">Current Members</h3>
        <div className="space-y-2">
          {(project.members || []).map((member) => (
            <div
              key={`${member.user_id}-${member.role}`}
              className="rounded-md border border-slate-800 bg-slate-950 p-3 flex justify-between text-sm"
            >
              <span>{member.user_id}</span>
              <span className="text-slate-400">{member.role}</span>
            </div>
          ))}
        </div>
      </section>

      {managerRoles.has(user?.role) && (
        <form
          onSubmit={addMember}
          className="rounded-xl border border-slate-800 bg-slate-900 p-4 grid md:grid-cols-3 gap-2"
        >
          <select
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
            value={selectedUser}
            onChange={(event) => setSelectedUser(event.target.value)}
            required
          >
            <option value="">Select user</option>
            {users.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name} ({item.email})
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
          <button className="rounded-md bg-brand-600 hover:bg-brand-700 px-3 py-2">
            Add Member
          </button>
        </form>
      )}
    </div>
  );
}
