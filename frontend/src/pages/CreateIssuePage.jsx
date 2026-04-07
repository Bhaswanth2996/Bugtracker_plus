import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { api, parseApiError } from "../services/api";

export default function CreateIssuePage() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [users, setUsers] = useState([]);
  const [error, setError] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const [aiSuggestions, setAiSuggestions] = useState(null);
  const [duplicateMatches, setDuplicateMatches] = useState([]);
  const [assigneeRecommendation, setAssigneeRecommendation] = useState(null);
  const [form, setForm] = useState({
    project_id: "",
    title: "",
    description: "",
    issue_type: "bug",
    priority: "medium",
    module: "",
    assignee_id: "",
    labels: "",
  });

  useEffect(() => {
    async function loadData() {
      try {
        const projectResp = await api.listProjects();
        setProjects(projectResp.data);
        if (projectResp.data.length > 0) {
          setForm((prev) => ({ ...prev, project_id: projectResp.data[0].id }));
        }
        try {
          const usersResp = await api.listUsers();
          setUsers(usersResp.data);
        } catch {
          setUsers([]);
        }
      } catch (err) {
        setError(parseApiError(err));
      }
    }
    loadData();
  }, []);

  async function onSubmit(event) {
    event.preventDefault();
    try {
      const response = await api.createIssue({
        project_id: form.project_id,
        title: form.title,
        description: form.description,
        issue_type: form.issue_type,
        priority: form.priority,
        module: form.module || null,
        source: "Manual",
        assignee_id: form.assignee_id || null,
        labels: form.labels
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean),
      });
      navigate(response.data.issue_key ? `/issue/${response.data.issue_key}` : `/issues/${response.data.id}`);
    } catch (err) {
      setError(parseApiError(err));
    }
  }

  async function runAiSuggestions() {
    if (!form.title.trim() || !form.description.trim()) {
      setError("Title and description are required for AI analysis.");
      return;
    }
    setAiLoading(true);
    setError("");
    try {
      const [analysisResp, duplicatesResp, recommendationResp] = await Promise.all([
        api.analyzeBug(
          { title: form.title, description: form.description },
          form.project_id || undefined,
          form.module || undefined
        ),
        api.findDuplicates(
          { title: form.title, description: form.description },
          form.project_id || undefined
        ),
        api.recommendAssignee(
          { module: form.module || null, description: form.description },
          form.project_id || undefined
        ),
      ]);
      setAiSuggestions(analysisResp.data);
      setDuplicateMatches(duplicatesResp.data.duplicates || []);
      setAssigneeRecommendation(recommendationResp.data);
    } catch (err) {
      setError(parseApiError(err));
    } finally {
      setAiLoading(false);
    }
  }

  function applySuggestedLabels() {
    if (!aiSuggestions?.suggestedLabels?.length) {
      return;
    }
    const current = new Set(
      form.labels
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean)
        .map((item) => item.toLowerCase())
    );
    for (const label of aiSuggestions.suggestedLabels) {
      current.add(label.toLowerCase());
    }
    setForm((prev) => ({ ...prev, labels: Array.from(current).join(", ") }));
  }

  function applyAssigneeFromName(name) {
    if (!name) {
      return;
    }
    const matched = users.find((item) => item.name.toLowerCase() === String(name).toLowerCase());
    if (matched) {
      setForm((prev) => ({ ...prev, assignee_id: matched.id }));
    }
  }

  return (
    <div className="space-y-4 max-w-4xl">
      <h2 className="text-2xl font-semibold">Create Issue</h2>
      {error && <p className="text-sm text-rose-400">{error}</p>}

      <form
        className="rounded-md border border-slate-800 bg-slate-900 p-4 grid md:grid-cols-2 gap-3"
        onSubmit={onSubmit}
      >
        <select
          className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
          value={form.project_id}
          onChange={(event) =>
            setForm((prev) => ({ ...prev, project_id: event.target.value }))
          }
          required
        >
          {projects.map((project) => (
            <option key={project.id} value={project.id}>
              {project.key} - {project.name}
            </option>
          ))}
        </select>
        <input
          className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
          placeholder="Issue title"
          value={form.title}
          onChange={(event) => setForm((prev) => ({ ...prev, title: event.target.value }))}
          required
        />
        <textarea
          className="md:col-span-2 rounded-md border border-slate-700 bg-slate-950 px-3 py-2 min-h-40"
          placeholder="Issue description"
          value={form.description}
          onChange={(event) =>
            setForm((prev) => ({ ...prev, description: event.target.value }))
          }
          required
        />
        <select
          className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
          value={form.issue_type}
          onChange={(event) =>
            setForm((prev) => ({ ...prev, issue_type: event.target.value }))
          }
        >
          <option value="bug">Bug</option>
          <option value="task">Task</option>
          <option value="story">Story</option>
          <option value="epic">Epic</option>
        </select>
        <select
          className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
          value={form.priority}
          onChange={(event) =>
            setForm((prev) => ({ ...prev, priority: event.target.value }))
          }
        >
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="critical">Critical</option>
        </select>
        <input
          className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
          placeholder="Module (e.g., authentication)"
          value={form.module}
          onChange={(event) => setForm((prev) => ({ ...prev, module: event.target.value }))}
        />
        <select
          className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
          value={form.assignee_id}
          onChange={(event) =>
            setForm((prev) => ({ ...prev, assignee_id: event.target.value }))
          }
        >
          <option value="">Unassigned</option>
          {users.map((u) => (
            <option key={u.id} value={u.id}>
              {u.name}
            </option>
          ))}
        </select>
        <input
          className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
          placeholder="labels: api,auth"
          value={form.labels}
          onChange={(event) => setForm((prev) => ({ ...prev, labels: event.target.value }))}
        />
        <button
          type="button"
          className="rounded-md border border-cyan-500/50 bg-cyan-500/10 px-3 py-2 text-cyan-200 hover:bg-cyan-500/20"
          onClick={runAiSuggestions}
          disabled={aiLoading}
        >
          {aiLoading ? "Analyzing..." : "AI Suggestions"}
        </button>
        <button className="md:col-span-2 rounded-md bg-brand-600 hover:bg-brand-700 px-3 py-2">
          Create Issue
        </button>
      </form>

      <section className="rounded-md border border-slate-800 bg-slate-900 p-4 space-y-3">
        <h3 className="font-semibold">AI Suggestions</h3>
        {!aiSuggestions ? (
          <p className="text-sm text-slate-400">
            Run AI Suggestions to detect duplicates, priority, labels, and assignee recommendations.
          </p>
        ) : (
          <>
            <div className="rounded-md border border-slate-800 bg-slate-950 p-3 text-sm">
              <p>
                Suggested priority:{" "}
                <span className="font-medium text-cyan-300">{aiSuggestions.suggestedPriority}</span>
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                <button
                  type="button"
                  className="rounded-md border border-slate-700 px-2 py-1 text-xs hover:bg-slate-800"
                  onClick={() =>
                    setForm((prev) => ({ ...prev, priority: aiSuggestions.suggestedPriority }))
                  }
                >
                  Accept priority
                </button>
                <button
                  type="button"
                  className="rounded-md border border-slate-700 px-2 py-1 text-xs hover:bg-slate-800"
                  onClick={applySuggestedLabels}
                >
                  Accept labels
                </button>
                <button
                  type="button"
                  className="rounded-md border border-slate-700 px-2 py-1 text-xs hover:bg-slate-800"
                  onClick={() => applyAssigneeFromName(aiSuggestions.suggestedAssignee)}
                >
                  Accept suggested assignee
                </button>
              </div>
              <div className="mt-2 flex flex-wrap gap-2">
                {(aiSuggestions.suggestedLabels || []).map((label) => (
                  <span
                    key={label}
                    className="inline-flex rounded-full border border-cyan-400/30 bg-cyan-500/10 px-2 py-0.5 text-xs text-cyan-200"
                  >
                    {label}
                  </span>
                ))}
              </div>
              <p className="mt-2 text-xs text-slate-400">
                Suggested assignee: {aiSuggestions.suggestedAssignee || "No suggestion"}
              </p>
            </div>

            <div className="rounded-md border border-slate-800 bg-slate-950 p-3 text-sm">
              <p className="font-medium mb-2">Possible Duplicate Issues</p>
              {duplicateMatches.length === 0 ? (
                <p className="text-slate-400 text-xs">No likely duplicates detected.</p>
              ) : (
                <div className="space-y-2">
                  {duplicateMatches.map((item) => (
                    <a
                      key={item.issueKey}
                      href={`/issue/${item.issueKey}`}
                      className="block rounded border border-slate-700 px-2 py-1 hover:bg-slate-800"
                    >
                      {item.issueKey} • similarity {(item.similarity * 100).toFixed(0)}%
                    </a>
                  ))}
                </div>
              )}
            </div>

            <div className="rounded-md border border-slate-800 bg-slate-950 p-3 text-sm">
              <p className="font-medium">Recommended Assignee</p>
              <p className="text-slate-300 mt-1">
                {assigneeRecommendation?.recommendedDeveloper || "No recommendation"}
              </p>
              <p className="text-xs text-slate-400 mt-1">
                Confidence: {assigneeRecommendation?.confidence ?? 0} •{" "}
                {assigneeRecommendation?.reason || "No reason available"}
              </p>
              <button
                type="button"
                className="mt-2 rounded-md border border-slate-700 px-2 py-1 text-xs hover:bg-slate-800"
                onClick={() =>
                  applyAssigneeFromName(assigneeRecommendation?.recommendedDeveloper)
                }
              >
                Accept recommendation
              </button>
            </div>
          </>
        )}
      </section>
    </div>
  );
}
