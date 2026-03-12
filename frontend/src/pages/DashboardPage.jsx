import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api, parseApiError } from "../services/api";
import { formatDate } from "../utils/date";

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const response = await api.getGlobalDashboard();
        setStats(response.data);
      } catch (err) {
        setError(parseApiError(err));
      }
    }
    load();
  }, []);

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">Dashboard</h2>
      {error && <p className="text-sm text-rose-400">{error}</p>}
      {stats && (
        <>
          <section className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Stat title="Total Issues" value={stats.total_issues} />
            <Stat title="To Do" value={stats.todo_issues} />
            <Stat title="In Progress" value={stats.in_progress_issues} />
            <Stat title="Done" value={stats.done_issues} />
            <Stat title="Critical" value={stats.critical_priority} />
            <Stat title="High" value={stats.high_priority} />
            <Stat title="Medium" value={stats.medium_priority} />
            <Stat title="Low" value={stats.low_priority} />
          </section>
          <section className="rounded-md border border-slate-800 bg-slate-900 p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold">Recent Activity</h3>
              <Link className="text-sm text-blue-400 hover:underline" to="/projects">
                Open workspace
              </Link>
            </div>
            <div className="space-y-2">
              {(stats.recent_activity || []).map((item) => (
                <div
                  key={item.id}
                  className="rounded-md border border-slate-800 bg-slate-950 px-3 py-2"
                >
                  <p className="text-sm">{item.action}</p>
                  <p className="text-xs text-slate-400 mt-1">
                    {item.entity_type}:{item.entity_id} • {formatDate(item.timestamp)}
                  </p>
                </div>
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
}

function Stat({ title, value }) {
  return (
    <div className="rounded-md border border-slate-800 bg-slate-900 p-3">
      <p className="text-xs text-slate-400 uppercase">{title}</p>
      <p className="text-2xl font-semibold mt-1">{value}</p>
    </div>
  );
}
