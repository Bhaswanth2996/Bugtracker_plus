import {
  DndContext,
  PointerSensor,
  closestCenter,
  useDroppable,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import {
  SortableContext,
  arrayMove,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { ArrowDown, ArrowUp, ListTree } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import PriorityBadge from "../components/PriorityBadge";
import ProjectWorkspaceTabs from "../components/ProjectWorkspaceTabs";
import { useAuth } from "../context/AuthContext";
import { api, parseApiError } from "../services/api";
import { useProjectResolver } from "../utils/useProjectResolver";

const managerRoles = new Set(["admin", "project_manager"]);

export default function BacklogPage() {
  const { projectId, projectKey } = useParams();
  const { user } = useAuth();
  const { project, projectError } = useProjectResolver(projectId, projectKey);
  const [backlogIssues, setBacklogIssues] = useState([]);
  const [sprints, setSprints] = useState([]);
  const [error, setError] = useState("");
  const [sprintForm, setSprintForm] = useState({ name: "", goal: "" });

  async function loadData() {
    try {
      if (!project?.id) {
        return;
      }
      const [backlogResp, sprintResp] = await Promise.all([
        api.getBacklog(project.id),
        api.listSprints(project.id),
      ]);
      setBacklogIssues(backlogResp.data);
      setSprints(sprintResp.data);
      setError("");
    } catch (err) {
      setError(parseApiError(err));
    }
  }

  useEffect(() => {
    loadData();
  }, [project?.id]);

  useEffect(() => {
    if (projectError) {
      setError(projectError);
    }
  }, [projectError]);

  async function persistOrder(next) {
    const payload = next.map((issue, index) => ({
      issue_id: issue.id,
      backlog_order: index + 1,
    }));
    try {
      await api.reorderBacklog(project.id, payload);
      setBacklogIssues(next.map((issue, index) => ({ ...issue, backlog_order: index + 1 })));
    } catch (err) {
      setError(parseApiError(err));
    }
  }

  async function reorder(direction, index) {
    const target = index + direction;
    if (target < 0 || target >= backlogIssues.length) {
      return;
    }
    const next = arrayMove(backlogIssues, index, target);
    await persistOrder(next);
  }

  async function assignIssueToSprint(issueId, sprintId) {
    try {
      await api.moveIssueToSprint(issueId, { sprint_id: sprintId, backlog_order: 0 });
      loadData();
    } catch (err) {
      setError(parseApiError(err));
    }
  }

  async function onCreateSprint(event) {
    event.preventDefault();
    try {
      await api.createSprint({
        project_id: project.id,
        name: sprintForm.name,
        goal: sprintForm.goal,
      });
      setSprintForm({ name: "", goal: "" });
      loadData();
    } catch (err) {
      setError(parseApiError(err));
    }
  }

  async function onSprintAction(sprintId, action) {
    try {
      if (action === "start") {
        await api.startSprint(sprintId);
      } else {
        await api.closeSprint(sprintId);
      }
      loadData();
    } catch (err) {
      setError(parseApiError(err));
    }
  }

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 6 } }));
  const sprintDropTargets = useMemo(
    () => sprints.filter((item) => item.status !== "closed"),
    [sprints]
  );

  async function onDragEnd(event) {
    const activeId = event.active?.id;
    const overId = event.over?.id;
    if (!activeId || !overId) {
      return;
    }

    const issueIndex = backlogIssues.findIndex((item) => item.id === activeId);
    if (issueIndex === -1) {
      return;
    }

    if (String(overId).startsWith("sprint:")) {
      const sprintId = String(overId).replace("sprint:", "");
      await assignIssueToSprint(activeId, sprintId);
      return;
    }

    const overIndex = backlogIssues.findIndex((item) => item.id === overId);
    if (overIndex === -1 || overIndex === issueIndex) {
      return;
    }
    const reordered = arrayMove(backlogIssues, issueIndex, overIndex);
    await persistOrder(reordered);
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold">Backlog - {project?.key || "PRJ"}</h2>
        <Link
          to={`/project/${project?.key || projectKey}/board`}
          className="rounded-md border border-slate-700 px-3 py-2 text-sm hover:bg-slate-800"
        >
          Open Board
        </Link>
      </div>
      {project?.key ? <ProjectWorkspaceTabs projectKey={project.key} /> : null}
      {error && <p className="text-sm text-rose-400">{error}</p>}

      {managerRoles.has(user?.role) && (
        <form
          onSubmit={onCreateSprint}
          className="rounded-md border border-slate-800 bg-slate-900 p-4 grid md:grid-cols-3 gap-2"
        >
          <input
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
            placeholder="Sprint name"
            value={sprintForm.name}
            onChange={(event) =>
              setSprintForm((prev) => ({ ...prev, name: event.target.value }))
            }
            required
          />
          <input
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
            placeholder="Sprint goal"
            value={sprintForm.goal}
            onChange={(event) =>
              setSprintForm((prev) => ({ ...prev, goal: event.target.value }))
            }
          />
          <button className="rounded-md bg-brand-600 hover:bg-brand-700 px-3 py-2 text-sm">
            Create Sprint
          </button>
        </form>
      )}

      <section className="rounded-md border border-slate-800 bg-slate-900 p-4">
        <h3 className="font-semibold mb-2">Sprints</h3>
        <div className="space-y-2">
          {sprints.map((sprint) => (
            <SprintDropTarget
              key={sprint.id}
              sprint={sprint}
              issueCountHint={0}
            >
              <div className="flex items-center gap-2">
                <ListTree className="h-4 w-4 text-slate-500" />
                <div>
                  <p className="font-medium">{sprint.name}</p>
                  <p className="text-xs text-slate-400">{sprint.status}</p>
                </div>
              </div>
              {managerRoles.has(user?.role) && (
                <div className="flex gap-2">
                  {sprint.status === "planned" && (
                    <button
                      type="button"
                      className="rounded-md border border-slate-700 px-2 py-1 text-xs hover:bg-slate-800"
                      onClick={() => onSprintAction(sprint.id, "start")}
                    >
                      Start Sprint
                    </button>
                  )}
                  {sprint.status === "active" && (
                    <button
                      type="button"
                      className="rounded-md border border-slate-700 px-2 py-1 text-xs hover:bg-slate-800"
                      onClick={() => onSprintAction(sprint.id, "close")}
                    >
                      Close Sprint
                    </button>
                  )}
                </div>
              )}
            </SprintDropTarget>
          ))}
        </div>
      </section>

      <section className="rounded-md border border-slate-800 bg-slate-900 p-4">
        <h3 className="font-semibold mb-2">Prioritized Backlog</h3>
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={onDragEnd}>
          <SortableContext items={backlogIssues.map((issue) => issue.id)} strategy={verticalListSortingStrategy}>
            <div className="space-y-2">
              {backlogIssues.map((issue, index) => (
                <SortableBacklogIssue
                  key={issue.id}
                  issue={issue}
                  managerCanEdit={managerRoles.has(user?.role)}
                  onReorderUp={() => reorder(-1, index)}
                  onReorderDown={() => reorder(1, index)}
                  onAssignIssueToSprint={assignIssueToSprint}
                  sprintDropTargets={sprintDropTargets}
                />
              ))}
            </div>
          </SortableContext>
        </DndContext>
      </section>
    </div>
  );
}

function SortableBacklogIssue({
  issue,
  managerCanEdit,
  onReorderUp,
  onReorderDown,
  onAssignIssueToSprint,
  sprintDropTargets,
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: issue.id,
  });
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.65 : 1,
  };
  return (
    <div
      ref={setNodeRef}
      style={style}
      className="rounded-md border border-slate-800 bg-slate-950 p-3 flex flex-wrap gap-2 items-center justify-between hover:bg-slate-900 transition"
    >
      <button
        type="button"
        className="flex-1 text-left cursor-grab active:cursor-grabbing"
        {...attributes}
        {...listeners}
      >
        <p className="font-medium">{issue.issue_key ? `${issue.issue_key} · ` : ""}{issue.title}</p>
        <div className="mt-1 flex items-center gap-2 text-xs text-slate-400">
          <PriorityBadge priority={issue.priority} />
          <span>{issue.issue_type}</span>
        </div>
      </button>
      <div className="flex gap-2 items-center">
        {managerCanEdit && (
          <>
            <button
              type="button"
              className="rounded-md border border-slate-700 px-2 py-1 text-xs hover:bg-slate-800"
              onClick={onReorderUp}
            >
              <ArrowUp className="h-3.5 w-3.5" />
            </button>
            <button
              type="button"
              className="rounded-md border border-slate-700 px-2 py-1 text-xs hover:bg-slate-800"
              onClick={onReorderDown}
            >
              <ArrowDown className="h-3.5 w-3.5" />
            </button>
          </>
        )}
        <select
          className="rounded-md border border-slate-700 bg-slate-900 px-2 py-1 text-xs"
          onChange={(event) =>
            event.target.value && onAssignIssueToSprint(issue.id, event.target.value)
          }
          defaultValue=""
        >
          <option value="">Assign to sprint</option>
          {sprintDropTargets.map((sprint) => (
            <option key={sprint.id} value={sprint.id}>
              {sprint.name}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}

function SprintDropTarget({ sprint, children }) {
  const { setNodeRef, isOver } = useDroppable({ id: `sprint:${sprint.id}` });
  return (
    <div
      ref={setNodeRef}
      className={`rounded-md border p-3 flex flex-wrap gap-2 items-center justify-between transition ${
        isOver ? "border-brand-500 bg-brand-600/10" : "border-slate-800 bg-slate-950"
      }`}
    >
      {children}
    </div>
  );
}
