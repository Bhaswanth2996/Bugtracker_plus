import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import ProjectWorkspaceTabs from "../components/ProjectWorkspaceTabs";
import { api, parseApiError } from "../services/api";
import { useProjectResolver } from "../utils/useProjectResolver";

export default function ProjectReportsPage() {
  const { projectKey } = useParams();
  const { project, projectError } = useProjectResolver(null, projectKey);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadReports() {
      try {
        if (!project?.id) {
          return;
        }
        const response = await api.getProjectReports(project.id);
        setData(response.data);
        setError("");
      } catch (err) {
        setError(parseApiError(err));
      }
    }
    loadReports();
  }, [project?.id]);

  useEffect(() => {
    if (projectError) {
      setError(projectError);
    }
  }, [projectError]);

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">{project?.key} Reports</h2>
      {project?.key ? <ProjectWorkspaceTabs projectKey={project.key} /> : null}
      {error && <p className="text-sm text-rose-400">{error}</p>}

      {data && (
        <div className="grid xl:grid-cols-2 gap-4">
          <ChartCard title="Issues by Status">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.issues_by_status}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="name" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip />
                <Legend />
                <Bar dataKey="value" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard title="Issues by Priority">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.issues_by_priority}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="name" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip />
                <Legend />
                <Bar dataKey="value" fill="#a855f7" />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard title="Sprint Burndown">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.sprint_burndown}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="name" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="remaining" stroke="#f43f5e" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard title="Velocity Chart">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.velocity}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="name" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip />
                <Legend />
                <Bar dataKey="completed" fill="#10b981" />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>
      )}
    </div>
  );
}

function ChartCard({ title, children }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
      <h3 className="font-semibold mb-3">{title}</h3>
      <div className="h-72">{children}</div>
    </div>
  );
}
