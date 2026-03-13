import { Link2, Plus } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import PriorityBadge from "../components/PriorityBadge";
import UserAvatar from "../components/UserAvatar";
import { api, parseApiError } from "../services/api";
import { formatDate } from "../utils/date";

export default function IssueDetailsPage() {
  const { issueId, issueKey } = useParams();
  const { user } = useAuth();
  const [issue, setIssue] = useState(null);
  const [comments, setComments] = useState([]);
  const [activity, setActivity] = useState([]);
  const [links, setLinks] = useState([]);
  const [users, setUsers] = useState([]);
  const [commentBody, setCommentBody] = useState("");
  const [replyParentId, setReplyParentId] = useState(null);
  const [newLinkTarget, setNewLinkTarget] = useState("");
  const [newLinkType, setNewLinkType] = useState("relates_to");
  const [error, setError] = useState("");
  const userMap = useMemo(
    () => Object.fromEntries(users.map((item) => [item.id, item])),
    [users]
  );

  async function loadIssue() {
    try {
      const issueResp = issueId
        ? await api.getIssue(issueId)
        : await api.getIssueByKey(issueKey);
      const currentIssue = issueResp.data;
      setIssue(currentIssue);
      const [commentsResp, usersResp, activityResp, linksResp] = await Promise.all([
        api.listComments(currentIssue.id),
        api.listUsers().catch(() => ({ data: [] })),
        api.listIssueActivity(currentIssue.id),
        api.listIssueLinks(currentIssue.id),
      ]);
      setComments(commentsResp.data);
      setUsers(usersResp.data);
      setActivity(activityResp.data);
      setLinks(linksResp.data);
      setError("");
    } catch (err) {
      setError(parseApiError(err));
    }
  }

  useEffect(() => {
    loadIssue();
  }, [issueId, issueKey]);

  async function updateField(field, value) {
    if (!issue) {
      return;
    }
    try {
      const response = await api.updateIssue(issue.id, { [field]: value });
      setIssue(response.data);
      await loadIssue();
    } catch (err) {
      setError(parseApiError(err));
    }
  }

  async function addComment(event) {
    event.preventDefault();
    try {
      await api.createComment({
        issue_id: issue.id,
        body: commentBody,
        parent_id: replyParentId,
      });
      setCommentBody("");
      setReplyParentId(null);
      loadIssue();
    } catch (err) {
      setError(parseApiError(err));
    }
  }

  async function softDeleteComment(commentId) {
    try {
      await api.deleteComment(commentId);
      loadIssue();
    } catch (err) {
      setError(parseApiError(err));
    }
  }

  async function uploadAttachment(event) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    try {
      const response = await api.uploadAttachment(issue.id, file);
      setIssue(response.data);
      await loadIssue();
    } catch (err) {
      setError(parseApiError(err));
    }
  }

  async function createLink(event) {
    event.preventDefault();
    if (!newLinkTarget.trim()) {
      return;
    }
    try {
      const target = await api.getIssueByKey(newLinkTarget.trim().toUpperCase());
      await api.createIssueLink(issue.id, {
        target_issue_id: target.data.id,
        link_type: newLinkType,
      });
      setNewLinkTarget("");
      setNewLinkType("relates_to");
      await loadIssue();
    } catch (err) {
      setError(parseApiError(err));
    }
  }

  async function removeLink(linkId) {
    try {
      await api.deleteIssueLink(issue.id, linkId);
      await loadIssue();
    } catch (err) {
      setError(parseApiError(err));
    }
  }

  if (!issue) {
    return <div className="text-slate-300">Loading issue...</div>;
  }

  const topLevel = comments.filter((comment) => !comment.parent_id);
  const children = comments.filter((comment) => comment.parent_id);

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">Issue Details</h2>
      <p className="text-sm text-slate-400">{issue.issue_key || issue.id}</p>
      {error && <p className="text-sm text-rose-400">{error}</p>}

      <section className="rounded-md border border-slate-800 bg-slate-900 p-4 space-y-3">
        <input
          className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-lg"
          value={issue.title}
          onChange={(event) => setIssue((prev) => ({ ...prev, title: event.target.value }))}
          onBlur={(event) => updateField("title", event.target.value)}
        />
        <textarea
          className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 min-h-28"
          value={issue.description}
          onChange={(event) =>
            setIssue((prev) => ({ ...prev, description: event.target.value }))
          }
          onBlur={(event) => updateField("description", event.target.value)}
        />
        <div className="grid md:grid-cols-4 gap-2">
          <select
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
            value={issue.status}
            onChange={(event) => updateField("status", event.target.value)}
          >
            <option value="todo">todo</option>
            <option value="in_progress">in_progress</option>
            <option value="done">done</option>
          </select>
          <select
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
            value={issue.priority}
            onChange={(event) => updateField("priority", event.target.value)}
          >
            <option value="low">low</option>
            <option value="medium">medium</option>
            <option value="high">high</option>
            <option value="critical">critical</option>
          </select>
          <select
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
            value={issue.issue_type}
            onChange={(event) => updateField("issue_type", event.target.value)}
          >
            <option value="bug">bug</option>
            <option value="task">task</option>
            <option value="story">story</option>
            <option value="epic">epic</option>
          </select>
          <select
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
            value={issue.assignee_id || ""}
            onChange={(event) => updateField("assignee_id", event.target.value || null)}
          >
            <option value="">Unassigned</option>
            {users.map((u) => (
              <option key={u.id} value={u.id}>
                {u.name}
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <PriorityBadge priority={issue.priority} />
          {(issue.labels || []).map((label) => (
            <span
              key={label}
              className="inline-flex rounded-full bg-cyan-500/20 border border-cyan-400/30 text-cyan-200 px-2 py-0.5 text-xs"
            >
              {label}
            </span>
          ))}
        </div>
        <div className="text-xs text-slate-400">
          Reporter: {userMap[issue.reporter_id]?.name || issue.reporter_id} • Assignee:{" "}
          {userMap[issue.assignee_id]?.name || "Unassigned"} • Updated{" "}
          {formatDate(issue.updated_at)}
        </div>
      </section>

      <section className="rounded-md border border-slate-800 bg-slate-900 p-4">
        <h3 className="font-semibold mb-2">Attachments</h3>
        <input
          type="file"
          className="mb-3 text-sm"
          onChange={uploadAttachment}
        />
        <div className="space-y-2">
          {(issue.attachments || []).map((attachment) => (
            <a
              key={attachment.id}
              href={attachment.blob_url}
              className="block rounded-md border border-slate-800 bg-slate-950 px-3 py-2 text-sm hover:underline"
              target="_blank"
              rel="noreferrer"
            >
              {attachment.filename}
            </a>
          ))}
        </div>
      </section>

      <section className="rounded-md border border-slate-800 bg-slate-900 p-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold flex items-center gap-2">
            <Link2 className="h-4 w-4" />
            Linked Issues
          </h3>
        </div>
        <form className="flex flex-wrap items-center gap-2 mb-3" onSubmit={createLink}>
          <input
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
            placeholder="Target issue key (e.g., AUTH-12)"
            value={newLinkTarget}
            onChange={(event) => setNewLinkTarget(event.target.value)}
          />
          <select
            className="rounded-md border border-slate-700 bg-slate-950 px-2 py-2 text-sm"
            value={newLinkType}
            onChange={(event) => setNewLinkType(event.target.value)}
          >
            <option value="relates_to">relates_to</option>
            <option value="blocks">blocks</option>
            <option value="blocked_by">blocked_by</option>
            <option value="duplicates">duplicates</option>
          </select>
          <button className="rounded-md bg-brand-600 hover:bg-brand-700 px-3 py-2 text-sm inline-flex items-center gap-1">
            <Plus className="h-4 w-4" /> Link
          </button>
        </form>
        <div className="space-y-2">
          {links.map((item) => (
            <div
              key={item.id}
              className="rounded-md border border-slate-800 bg-slate-950 p-2 flex items-center justify-between text-sm"
            >
              <span>
                {item.link_type}: {item.source_issue_id} ↔ {item.target_issue_id}
              </span>
              <button
                type="button"
                className="text-xs text-rose-400 hover:underline"
                onClick={() => removeLink(item.id)}
              >
                Remove
              </button>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-md border border-slate-800 bg-slate-900 p-4">
        <h3 className="font-semibold mb-2">Comments</h3>
        <div className="space-y-3">
          {topLevel.map((comment) => (
            <div key={comment.id} className="rounded-md border border-slate-800 bg-slate-950 p-3">
              <p className="text-sm">{comment.body}</p>
              <p className="text-xs text-slate-400 mt-1">
                <span className="inline-flex items-center gap-2">
                  <UserAvatar name={userMap[comment.author_id]?.name || comment.author_id} />
                  {userMap[comment.author_id]?.name || comment.author_id}
                </span>{" "}
                • {formatDate(comment.created_at)}
              </p>
              <div className="mt-2 flex gap-2 text-xs">
                <button
                  type="button"
                  className="text-blue-400 hover:underline"
                  onClick={() => setReplyParentId(comment.id)}
                >
                  Reply
                </button>
                {(comment.author_id === user?.id || user?.role === "admin") && (
                  <button
                    type="button"
                    className="text-rose-400 hover:underline"
                    onClick={() => softDeleteComment(comment.id)}
                  >
                    Delete
                  </button>
                )}
              </div>
              {children
                .filter((child) => child.parent_id === comment.id)
                .map((child) => (
                  <div
                    key={child.id}
                    className="mt-2 ml-4 rounded-md border border-slate-800 bg-slate-900 px-2 py-2"
                  >
                    <p className="text-sm">{child.body}</p>
                    <p className="text-xs text-slate-400">
                      {userMap[child.author_id]?.name || child.author_id}
                    </p>
                  </div>
                ))}
            </div>
          ))}
        </div>
        <form className="mt-3 space-y-2" onSubmit={addComment}>
          {replyParentId && (
            <p className="text-xs text-slate-400">
              Replying to comment {replyParentId}{" "}
              <button
                type="button"
                className="text-blue-400 hover:underline"
                onClick={() => setReplyParentId(null)}
              >
                cancel
              </button>
            </p>
          )}
          <textarea
            className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 min-h-24"
            value={commentBody}
            onChange={(event) => setCommentBody(event.target.value)}
            required
          />
          <button className="rounded-md bg-brand-600 hover:bg-brand-700 px-3 py-2 text-sm">
            Post Comment
          </button>
        </form>
      </section>

      <section className="rounded-md border border-slate-800 bg-slate-900 p-4">
        <h3 className="font-semibold mb-2">Activity History</h3>
        <div className="space-y-2">
          {(activity || []).map((item) => (
            <div key={item.id} className="text-sm rounded-md border border-slate-800 bg-slate-950 px-3 py-2">
              <span className="text-slate-200 font-medium">{item.action}</span>
              <span className="text-xs text-slate-500 ml-2">{formatDate(item.timestamp)}</span>
              {item.metadata && Object.keys(item.metadata).length ? (
                <pre className="text-xs text-slate-400 mt-1 overflow-x-auto">
                  {JSON.stringify(item.metadata)}
                </pre>
              ) : null}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
