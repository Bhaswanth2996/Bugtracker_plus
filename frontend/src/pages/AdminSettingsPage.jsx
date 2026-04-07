import { useEffect, useState } from "react";

import { useAuth } from "../context/AuthContext";
import { api, parseApiError } from "../services/api";
import { formatDate } from "../utils/date";

const roles = ["admin", "project_manager", "developer", "tester"];

export default function AdminSettingsPage() {
  const { user } = useAuth();
  const [users, setUsers] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [error, setError] = useState("");

  async function loadData() {
    try {
      const [usersResp, auditResp] = await Promise.all([
        api.listUsers(),
        api.getAuditLogs({ limit: 100 }),
      ]);
      setUsers(usersResp.data);
      setAuditLogs(auditResp.data);
      setError("");
    } catch (err) {
      setError(parseApiError(err));
    }
  }

  useEffect(() => {
    if (user?.role === "admin" || user?.role === "project_manager") {
      loadData();
    }
  }, [user?.role]);

  async function onRoleChange(userId, role) {
    try {
      await api.updateUserRole(userId, role);
      loadData();
    } catch (err) {
      setError(parseApiError(err));
    }
  }

  if (!(user?.role === "admin" || user?.role === "project_manager")) {
    return <p className="text-sm text-slate-400">Admin settings require elevated role.</p>;
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">Admin Settings</h2>
      {error && <p className="text-sm text-rose-400">{error}</p>}

      <section className="rounded-md border border-slate-800 bg-slate-900 p-4">
        <h3 className="font-semibold mb-3">User Role Permissions</h3>
        <div className="space-y-2">
          {users.map((item) => (
            <div
              key={item.id}
              className="rounded-md border border-slate-800 bg-slate-950 p-3 flex flex-wrap justify-between items-center gap-2"
            >
              <div>
                <p className="font-medium">{item.name}</p>
                <p className="text-xs text-slate-400">{item.email}</p>
              </div>
              <select
                className="rounded-md border border-slate-700 bg-slate-900 px-2 py-1 text-sm"
                value={item.role}
                onChange={(event) => onRoleChange(item.id, event.target.value)}
                disabled={user.role !== "admin"}
              >
                {roles.map((role) => (
                  <option key={role} value={role}>
                    {role}
                  </option>
                ))}
              </select>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-md border border-slate-800 bg-slate-900 p-4">
        <h3 className="font-semibold mb-3">Activity Log</h3>
        <div className="space-y-2 max-h-[400px] overflow-y-auto">
          {auditLogs.map((log) => (
            <div
              key={log.id}
              className="rounded-md border border-slate-800 bg-slate-950 p-3"
            >
              <p className="text-sm font-medium">{log.action}</p>
              <p className="text-xs text-slate-400 mt-1">
                {log.entity_type}:{log.entity_id} • {formatDate(log.timestamp)}
              </p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
