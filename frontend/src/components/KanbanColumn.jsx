import { useDraggable, useDroppable } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";

import IssueCard from "./IssueCard";

export default function KanbanColumn({
  title,
  droppableId,
  issues,
  projectMap,
  userMap,
}) {
  const { setNodeRef, isOver } = useDroppable({ id: droppableId });

  return (
    <div
      ref={setNodeRef}
      className={`rounded-xl border p-3 min-h-[420px] transition ${
        isOver ? "border-brand-600 bg-slate-800/80" : "border-slate-800 bg-slate-900"
      }`}
    >
      <h3 className="text-sm font-semibold mb-3">{title}</h3>
      <div className="space-y-2">
        {issues.map((issue) => (
          <DraggableIssueCard
            key={issue.id}
            issue={issue}
            projectMap={projectMap}
            assigneeName={userMap?.[issue.assignee_id]?.name}
          />
        ))}
      </div>
    </div>
  );
}

function DraggableIssueCard({ issue, projectMap, assigneeName }) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: issue.id,
    data: { type: "issue", issueId: issue.id },
  });
  const style = {
    transform: CSS.Translate.toString(transform),
    opacity: isDragging ? 0.6 : 1,
  };

  return (
    <div ref={setNodeRef} style={style} {...listeners} {...attributes}>
      <IssueCard issue={issue} projectMap={projectMap} assigneeName={assigneeName} />
    </div>
  );
}
