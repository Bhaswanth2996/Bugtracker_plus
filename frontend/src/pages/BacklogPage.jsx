import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { api, parseApiError } from "../services/api";

const managerRoles = new Set(["admin", "project_manager"]);

export default function BacklogPage() {
  const { projectId } = useParams();
  const { user } = useAuth();
  const [backlogIssues, setBacklogIssues] = useState([]);
  const [sprints, setSprints] = useState([]);
  const [error, setError] = useState("");
  const [sprintForm, setSprintForm] = useState({ name: "", goal: "" });

  async function loadData() {
    try {
      const [backlogResp, sprintResp] = await Promise.all([
        api.getBacklog(projectId),
        api.listSprints(projectId),
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
  }, [projectId]);

  async function reorder(direction, index) {
    const next = [...backlogIssues];
    const target = index + direction;
    if (target < 0 || target >= next.length) {
      return;
    }
    [next[index], next[target]] = [next[target], next[index]];
    const payload = next.map((issue, idx) => ({
      issue_id: issue.id,
      backlog_order: idx + 1,
    }));
    try {
      await api.reorderBacklog(projectId, payload);
      setBacklogIssues(next.map((issue, idx) => ({ ...issue, backlog_order: idx + 1 })));
    } catch (err) {
      setError(parseApiError(err));
    }
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
        project_id: projectId,
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

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold">Backlog</h2>
        <Link
          to={`/projects/${projectId}/board`}
          className="rounded-md border border-slate-700 px-3 py-2 text-sm hover:bg-slate-800"
        >
          Open Board
        </Link>
      </div>
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
            <div
              key={sprint.id}
              className="rounded-md border border-slate-800 bg-slate-950 p-3 flex flex-wrap gap-2 items-center justify-between"
            >
              <div>
                <p className="font-medium">{sprint.name}</p>
                <p className="text-xs text-slate-400">{sprint.status}</p>
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
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-md border border-slate-800 bg-slate-900 p-4">
        <h3 className="font-semibold mb-2">Prioritized Backlog</h3>
        <div className="space-y-2">
          {backlogIssues.map((issue, index) => (
            <div
              key={issue.id}
              className="rounded-md border border-slate-800 bg-slate-950 p-3 flex flex-wrap gap-2 items-center justify-between"
            >
              <div>
                <Link to={`/issues/${issue.id}`} className="font-medium hover:underline">
                  {issue.title}
                </Link>
                <p className="text-xs text-slate-400">{issue.priority}</p>
              </div>
              <div className="flex gap-2 items-center">
                {managerRoles.has(user?.role) && (
                  <>
                    <button
                      type="button"
                      className="rounded-md border border-slate-700 px-2 py-1 text-xs hover:bg-slate-800"
                      onClick={() => reorder(-1, index)}
                    >
                      Up
                    </button>
                    <button
                      type="button"
                      className="rounded-md border border-slate-700 px-2 py-1 text-xs hover:bg-slate-800"
                      onClick={() => reorder(1, index)}
                    >
                      Down
                    </button>
                  </>
                )}
                <select
                  className="rounded-md border border-slate-700 bg-slate-900 px-2 py-1 text-xs"
                  onChange={(event) =>
                    event.target.value && assignIssueToSprint(issue.id, event.target.value)
                  }
                  defaultValue=""
                >
                  <option value="">Assign to sprint</option>
                  {sprints
                    .filter((sprint) => sprint.status !== "closed")
                    .map((sprint) => (
                      <option key={sprint.id} value={sprint.id}>
                        {sprint.name}
                      </option>
                    ))}
                </select>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
