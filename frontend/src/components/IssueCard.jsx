import { Link } from "react-router-dom";
import { Bug, ClipboardList, Flag } from "lucide-react";

import PriorityBadge from "./PriorityBadge";
import UserAvatar from "./UserAvatar";

const issueTypeIcon = {
  bug: Bug,
  task: ClipboardList,
  story: ClipboardList,
  epic: Flag,
};

export default function IssueCard({ issue, projectMap, assigneeName }) {
  const Icon = issueTypeIcon[issue.issue_type] || ClipboardList;
  const issuePath = issue.issue_key
    ? `/issue/${issue.issue_key}`
    : `/issues/${issue.id}`;
  return (
    <Link
      to={issuePath}
      className="group block rounded-xl border border-slate-700 bg-slate-900/80 p-3 shadow-sm transition hover:-translate-y-0.5 hover:bg-slate-800 hover:shadow-md"
    >
      <div className="flex items-start justify-between gap-2">
        <p className="font-medium text-sm text-slate-100 leading-snug">{issue.title}</p>
        <Icon className="h-4 w-4 text-slate-400 group-hover:text-slate-200" />
      </div>
      <div className="mt-2 flex items-center gap-2 text-xs text-slate-400">
        <span className="font-mono">{issue.issue_key || projectMap?.[issue.project_id]?.key || "PRJ"}</span>
        <span className="text-slate-600">•</span>
        <span>{issue.issue_type}</span>
      </div>
      <div className="mt-3 flex items-center justify-between">
        <PriorityBadge priority={issue.priority} />
        {assigneeName ? <UserAvatar name={assigneeName} /> : null}
      </div>
    </Link>
  );
}
