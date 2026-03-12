import IssueCard from "./IssueCard";

export default function KanbanColumn({
  title,
  status,
  issues,
  projectMap,
  onDropIssue,
}) {
  return (
    <div
      className="rounded-md border border-slate-800 bg-slate-900 p-3 min-h-[360px]"
      onDragOver={(event) => event.preventDefault()}
      onDrop={(event) => {
        const issueId = event.dataTransfer.getData("issueId");
        if (issueId) {
          onDropIssue(issueId, status);
        }
      }}
    >
      <h3 className="text-sm font-semibold mb-3">{title}</h3>
      <div className="space-y-2">
        {issues.map((issue) => (
          <div
            key={issue.id}
            draggable
            onDragStart={(event) => event.dataTransfer.setData("issueId", issue.id)}
          >
            <IssueCard issue={issue} projectMap={projectMap} />
          </div>
        ))}
      </div>
    </div>
  );
}
