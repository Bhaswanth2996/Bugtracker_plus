import { Link } from "react-router-dom";

export default function IssueCard({ issue, projectMap }) {
  return (
    <Link
      to={`/issues/${issue.id}`}
      className="block rounded-md border border-slate-700 bg-slate-900 p-3 hover:bg-slate-800"
    >
      <p className="font-medium">{issue.title}</p>
      <p className="text-xs text-slate-400 mt-1">{issue.issue_type}</p>
      <div className="mt-2 flex justify-between text-xs text-slate-400">
        <span>{projectMap?.[issue.project_id]?.key || "PRJ"}</span>
        <span>{issue.priority}</span>
      </div>
    </Link>
  );
}
