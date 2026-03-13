import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { useAuth } from "../context/AuthContext";
import { api, parseApiError } from "../services/api";
import { formatDate } from "../utils/date";

export default function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [advanced, setAdvanced] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const response = await api.getGlobalDashboard();
        const advancedResp = await api.getAdvancedDashboard();
        setStats(response.data);
        setAdvanced(advancedResp.data);
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
          <section className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <Stat title="Total Issues" value={stats.total_issues} />
            <Stat title="To Do" value={stats.todo_issues} />
            <Stat title="In Progress" value={stats.in_progress_issues} />
            <Stat title="Done" value={stats.done_issues} />
            <Stat title="Critical" value={stats.critical_priority} />
            <Stat title="High" value={stats.high_priority} />
            <Stat title="Medium" value={stats.medium_priority} />
            <Stat title="Low" value={stats.low_priority} />
            <Stat title={`${user?.name || "My"} Assigned`} value={stats.assigned_to_me || 0} />
          </section>
          <section className="grid lg:grid-cols-2 gap-4">
            <div className="rounded-md border border-slate-800 bg-slate-900 p-4">
              <h3 className="font-semibold mb-2">Issues by Status</h3>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={Object.entries(stats.status_breakdown || {}).map(([name, value]) => ({
                      name,
                      value,
                    }))}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="name" stroke="#94a3b8" />
                    <YAxis stroke="#94a3b8" />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="value" fill="#3b82f6" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
            <div className="rounded-md border border-slate-800 bg-slate-900 p-4">
              <h3 className="font-semibold mb-2">Issues by Priority</h3>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={Object.entries(stats.priority_breakdown || {}).map(
                        ([name, value]) => ({
                          name,
                          value,
                        })
                      )}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      outerRadius={100}
                      fill="#8b5cf6"
                      label
                    />
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
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

          <section className="grid lg:grid-cols-2 gap-4">
            <div className="rounded-md border border-slate-800 bg-slate-900 p-4">
              <h3 className="font-semibold mb-2">Recent Automated Test Failures</h3>
              <div className="space-y-2 text-sm">
                {(advanced?.automatedTestFailures || []).length === 0 ? (
                  <p className="text-slate-400">No CI/CD failure issues found.</p>
                ) : (
                  (advanced?.automatedTestFailures || []).map((item) => (
                    <Link
                      key={item.id}
                      to={item.issue_key ? `/issue/${item.issue_key}` : `/issues/${item.id}`}
                      className="block rounded-md border border-slate-800 bg-slate-950 px-3 py-2 hover:bg-slate-800"
                    >
                      <p className="font-medium">{item.title}</p>
                      <p className="text-xs text-slate-400 mt-1">
                        {item.issue_key || item.id} • {formatDate(item.created_at)}
                      </p>
                    </Link>
                  ))
                )}
              </div>
            </div>

            <div className="rounded-md border border-slate-800 bg-slate-900 p-4">
              <h3 className="font-semibold mb-2">AI Bug Insights</h3>
              <div className="space-y-2 text-sm">
                {Object.entries(advanced?.aiBugInsights || {}).map(([name, value]) => (
                  <div
                    key={name}
                    className="rounded-md border border-slate-800 bg-slate-950 px-3 py-2 flex items-center justify-between"
                  >
                    <span>{name}</span>
                    <span className="font-semibold">{value}</span>
                  </div>
                ))}
                {Object.keys(advanced?.aiBugInsights || {}).length === 0 && (
                  <p className="text-slate-400">No AI analytics available yet.</p>
                )}
              </div>
            </div>
          </section>

          <section className="grid lg:grid-cols-2 gap-4">
            <div className="rounded-md border border-slate-800 bg-slate-900 p-4">
              <h3 className="font-semibold mb-2">Bug Risk Prediction</h3>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={advanced?.bugRiskPrediction || []}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="module" stroke="#94a3b8" />
                    <YAxis stroke="#94a3b8" domain={[0, 1]} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="risk" fill="#f59e0b" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="rounded-md border border-slate-800 bg-slate-900 p-4">
              <h3 className="font-semibold mb-2">Developer Workload Insights</h3>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={advanced?.developerWorkloadInsights || []}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="developer" stroke="#94a3b8" />
                    <YAxis stroke="#94a3b8" />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="openIssues" fill="#ef4444" radius={[6, 6, 0, 0]} />
                    <Bar dataKey="resolvedIssues" fill="#22c55e" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </section>

          <section className="grid lg:grid-cols-2 gap-4">
            <div className="rounded-md border border-slate-800 bg-slate-900 p-4">
              <h3 className="font-semibold mb-2">Recent Root Cause Insights</h3>
              <div className="space-y-2 text-sm">
                {(advanced?.rootCauseInsights || []).length === 0 ? (
                  <p className="text-slate-400">No root-cause records yet.</p>
                ) : (
                  (advanced?.rootCauseInsights || []).map((item) => (
                    <div key={item.id} className="rounded-md border border-slate-800 bg-slate-950 px-3 py-2">
                      <p className="font-medium">{item.suspected_commit}</p>
                      <p className="text-xs text-slate-400">
                        {item.author} • {(Number(item.confidence || 0) * 100).toFixed(0)}%
                      </p>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="rounded-md border border-slate-800 bg-slate-900 p-4">
              <h3 className="font-semibold mb-2">Duplicate Bug Detection Stats</h3>
              <div className="space-y-2 text-sm">
                {Object.entries(advanced?.duplicateBugDetectionStats || {}).map(([name, value]) => (
                  <div
                    key={name}
                    className="rounded-md border border-slate-800 bg-slate-950 px-3 py-2 flex items-center justify-between"
                  >
                    <span>{name}</span>
                    <span className="font-semibold">{value}</span>
                  </div>
                ))}
                {Object.keys(advanced?.duplicateBugDetectionStats || {}).length === 0 && (
                  <p className="text-slate-400">No duplicate detection stats available yet.</p>
                )}
              </div>
            </div>
          </section>
        </>
      )}
    </div>
  );
}

function Stat({ title, value }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-3 shadow-sm">
      <p className="text-xs text-slate-400 uppercase">{title}</p>
      <p className="text-2xl font-semibold mt-1">{value}</p>
    </div>
  );
}
