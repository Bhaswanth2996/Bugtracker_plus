'use client';

import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react';

type UserRole = 'admin' | 'manager' | 'developer' | 'tester';
type IssueStatus = 'open' | 'in_progress' | 'resolved' | 'closed';
type IssuePriority = 'low' | 'medium' | 'high' | 'critical';

type User = {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  created_at: string;
};

type Project = {
  id: string;
  name: string;
  description: string;
  created_by: string;
  created_at: string;
};

type Issue = {
  id: string;
  project_id: string;
  title: string;
  description: string;
  priority: IssuePriority;
  tags: string[];
  assignee_id: string | null;
  reporter_id: string;
  status: IssueStatus;
  created_at: string;
  updated_at: string;
};

type Comment = {
  id: string;
  issue_id: string;
  author_id: string;
  body: string;
  created_at: string;
};

type DashboardStats = {
  total_issues: number;
  open_issues: number;
  in_progress_issues: number;
  resolved_issues: number;
  closed_issues: number;
  critical_issues: number;
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

async function apiRequest<T>(
  path: string,
  token?: string,
  init?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers || {}),
    },
  });

  if (!response.ok) {
    let message = 'Request failed.';
    try {
      const body = (await response.json()) as { detail?: string };
      message = body.detail || message;
    } catch {
      message = response.statusText || message;
    }
    throw new Error(message);
  }

  return (await response.json()) as T;
}

export default function Home() {
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isRegister, setIsRegister] = useState(true);

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [issues, setIssues] = useState<Issue[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [commentsByIssue, setCommentsByIssue] = useState<Record<string, Comment[]>>({});

  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDescription, setNewProjectDescription] = useState('');
  const [newIssueTitle, setNewIssueTitle] = useState('');
  const [newIssueDescription, setNewIssueDescription] = useState('');
  const [newIssuePriority, setNewIssuePriority] = useState<IssuePriority>('medium');
  const [newIssueAssigneeId, setNewIssueAssigneeId] = useState<string>('');
  const [newIssueTags, setNewIssueTags] = useState('');
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [selectedIssueId, setSelectedIssueId] = useState<string>('');
  const [newCommentBody, setNewCommentBody] = useState('');
  const [statusFilter, setStatusFilter] = useState<IssueStatus | 'all'>('all');
  const [priorityFilter, setPriorityFilter] = useState<IssuePriority | 'all'>('all');

  const projectLookup = useMemo(
    () => Object.fromEntries(projects.map(project => [project.id, project])),
    [projects]
  );
  const userLookup = useMemo(
    () => Object.fromEntries(users.map(user => [user.id, user])),
    [users]
  );

  const selectedIssue = useMemo(
    () => issues.find(issue => issue.id === selectedIssueId) || null,
    [issues, selectedIssueId]
  );

  const filteredIssues = useMemo(() => {
    return issues.filter(issue => {
      if (selectedProjectId && issue.project_id !== selectedProjectId) {
        return false;
      }
      if (statusFilter !== 'all' && issue.status !== statusFilter) {
        return false;
      }
      if (priorityFilter !== 'all' && issue.priority !== priorityFilter) {
        return false;
      }
      return true;
    });
  }, [issues, selectedProjectId, statusFilter, priorityFilter]);

  const canManageProjects =
    currentUser?.role === 'admin' || currentUser?.role === 'manager';
  const canManageUsers = currentUser?.role === 'admin';
  const canAssignIssues = canManageProjects;

  const hydrateApp = useCallback(async (activeToken: string): Promise<void> => {
    try {
      setError(null);
      setIsLoading(true);

      const me = await apiRequest<User>('/api/auth/me', activeToken);
      setCurrentUser(me);

      const [loadedProjects, loadedIssues, loadedStats] = await Promise.all([
        apiRequest<Project[]>('/api/projects', activeToken),
        apiRequest<Issue[]>('/api/issues', activeToken),
        apiRequest<DashboardStats>('/api/dashboard/stats', activeToken),
      ]);

      setProjects(loadedProjects);
      setIssues(loadedIssues);
      setStats(loadedStats);

      if (loadedProjects.length > 0) {
        setSelectedProjectId(previous => previous || loadedProjects[0].id);
      }

      try {
        const loadedUsers = await apiRequest<User[]>('/api/users', activeToken);
        setUsers(loadedUsers);
      } catch {
        // Non-admin/manager users may not have access to user listing.
        setUsers(me ? [me] : []);
      }
    } catch (err) {
      window.localStorage.removeItem('bugtracker_token');
      setToken(null);
      setCurrentUser(null);
      setError((err as Error).message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadComments = useCallback(async (activeToken: string, issueId: string): Promise<void> => {
    try {
      const comments = await apiRequest<Comment[]>(
        `/api/comments/issue/${issueId}`,
        activeToken
      );
      setCommentsByIssue(prev => ({ ...prev, [issueId]: comments }));
    } catch (err) {
      setError((err as Error).message);
    }
  }, []);

  useEffect(() => {
    const savedToken = window.localStorage.getItem('bugtracker_token');
    if (!savedToken) {
      setIsLoading(false);
      return;
    }

    setToken(savedToken);
    void hydrateApp(savedToken);
  }, [hydrateApp]);

  useEffect(() => {
    if (!token || !selectedIssueId) {
      return;
    }
    void loadComments(token, selectedIssueId);
  }, [token, selectedIssueId, loadComments]);

  async function handleAuthSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError(null);
    try {
      const path = isRegister ? '/api/auth/register' : '/api/auth/login';
      const payload = isRegister
        ? { name, email, password, role: 'tester' }
        : { email, password };
      const result = await apiRequest<{ access_token: string; user: User }>(path, undefined, {
        method: 'POST',
        body: JSON.stringify(payload),
      });

      setToken(result.access_token);
      window.localStorage.setItem('bugtracker_token', result.access_token);
      setName('');
      setPassword('');
      await hydrateApp(result.access_token);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  function handleLogout(): void {
    window.localStorage.removeItem('bugtracker_token');
    setToken(null);
    setCurrentUser(null);
    setUsers([]);
    setProjects([]);
    setIssues([]);
    setStats(null);
    setCommentsByIssue({});
    setSelectedIssueId('');
  }

  async function handleCreateProject(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (!token) {
      return;
    }
    try {
      const project = await apiRequest<Project>('/api/projects', token, {
        method: 'POST',
        body: JSON.stringify({
          name: newProjectName,
          description: newProjectDescription,
        }),
      });
      setProjects(prev => [project, ...prev]);
      setSelectedProjectId(project.id);
      setNewProjectName('');
      setNewProjectDescription('');
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function handleCreateIssue(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (!token || !selectedProjectId) {
      return;
    }
    try {
      const issue = await apiRequest<Issue>('/api/issues', token, {
        method: 'POST',
        body: JSON.stringify({
          project_id: selectedProjectId,
          title: newIssueTitle,
          description: newIssueDescription,
          priority: newIssuePriority,
          assignee_id: newIssueAssigneeId || null,
          tags: newIssueTags
            .split(',')
            .map(item => item.trim())
            .filter(Boolean),
        }),
      });
      setIssues(prev => [issue, ...prev]);
      setNewIssueTitle('');
      setNewIssueDescription('');
      setNewIssuePriority('medium');
      setNewIssueAssigneeId('');
      setNewIssueTags('');
      setSelectedIssueId(issue.id);
      await hydrateApp(token);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function updateIssue(
    issueId: string,
    patch: Partial<Pick<Issue, 'status' | 'priority' | 'assignee_id'>>
  ): Promise<void> {
    if (!token) {
      return;
    }
    try {
      const updated = await apiRequest<Issue>(`/api/issues/${issueId}`, token, {
        method: 'PATCH',
        body: JSON.stringify(patch),
      });
      setIssues(prev => prev.map(issue => (issue.id === issueId ? updated : issue)));
      await hydrateApp(token);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function handleAddComment(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (!token || !selectedIssueId || !newCommentBody.trim()) {
      return;
    }
    try {
      await apiRequest<Comment>('/api/comments', token, {
        method: 'POST',
        body: JSON.stringify({ issue_id: selectedIssueId, body: newCommentBody.trim() }),
      });
      setNewCommentBody('');
      await loadComments(token, selectedIssueId);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function handleUserRoleUpdate(userId: string, role: UserRole): Promise<void> {
    if (!token || !canManageUsers) {
      return;
    }
    try {
      const updatedUser = await apiRequest<User>(`/api/users/${userId}/role`, token, {
        method: 'PATCH',
        body: JSON.stringify({ role }),
      });
      setUsers(prev => prev.map(user => (user.id === userId ? updatedUser : user)));
    } catch (err) {
      setError((err as Error).message);
    }
  }

  if (isLoading) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-slate-950 text-slate-100">
        <p className="text-lg">Loading Bug Tracker+...</p>
      </main>
    );
  }

  if (!token || !currentUser) {
    return (
      <main className="min-h-screen bg-slate-950 text-slate-100 px-6 py-12">
        <section className="max-w-md mx-auto bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h1 className="text-2xl font-bold mb-2">Bug Tracker+</h1>
          <p className="text-slate-400 mb-6">
            Cloud-ready issue management for Agile and DevOps teams.
          </p>

          <form onSubmit={handleAuthSubmit} className="space-y-4">
            {isRegister && (
              <div>
                <label className="block text-sm mb-1" htmlFor="name">
                  Name
                </label>
                <input
                  id="name"
                  className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
                  value={name}
                  onChange={event => setName(event.target.value)}
                  required
                />
              </div>
            )}

            <div>
              <label className="block text-sm mb-1" htmlFor="email">
                Email
              </label>
              <input
                id="email"
                type="email"
                className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
                value={email}
                onChange={event => setEmail(event.target.value)}
                required
              />
            </div>

            <div>
              <label className="block text-sm mb-1" htmlFor="password">
                Password
              </label>
              <input
                id="password"
                type="password"
                minLength={8}
                className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
                value={password}
                onChange={event => setPassword(event.target.value)}
                required
              />
            </div>

            <button className="w-full rounded-md bg-indigo-600 hover:bg-indigo-500 px-3 py-2 font-semibold">
              {isRegister ? 'Create account' : 'Sign in'}
            </button>
          </form>

          <button
            className="mt-4 text-sm text-indigo-300 hover:text-indigo-200"
            onClick={() => setIsRegister(value => !value)}
          >
            {isRegister
              ? 'Already have an account? Sign in'
              : 'Need an account? Register'}
          </button>

          {error && <p className="mt-4 text-sm text-rose-400">{error}</p>}
        </section>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 px-4 md:px-8 py-6">
      <header className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-6">
        <div>
          <h1 className="text-3xl font-bold">Bug Tracker+</h1>
          <p className="text-slate-400 text-sm">
            Signed in as {currentUser.name} ({currentUser.role})
          </p>
        </div>
        <div className="flex gap-2">
          <button
            className="rounded-md border border-slate-700 px-3 py-2 text-sm hover:bg-slate-900"
            onClick={() => token && hydrateApp(token)}
          >
            Refresh
          </button>
          <button
            className="rounded-md bg-rose-600 hover:bg-rose-500 px-3 py-2 text-sm font-medium"
            onClick={handleLogout}
          >
            Logout
          </button>
        </div>
      </header>

      {error && (
        <div className="mb-4 rounded-md border border-rose-700 bg-rose-950/40 px-3 py-2 text-sm text-rose-300">
          {error}
        </div>
      )}

      <section className="grid grid-cols-2 md:grid-cols-6 gap-3 mb-6">
        <StatCard title="Total" value={stats?.total_issues ?? 0} />
        <StatCard title="Open" value={stats?.open_issues ?? 0} />
        <StatCard title="In Progress" value={stats?.in_progress_issues ?? 0} />
        <StatCard title="Resolved" value={stats?.resolved_issues ?? 0} />
        <StatCard title="Closed" value={stats?.closed_issues ?? 0} />
        <StatCard title="Critical" value={stats?.critical_issues ?? 0} />
      </section>

      <section className="grid lg:grid-cols-12 gap-4">
        <aside className="lg:col-span-3 space-y-4">
          <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
            <h2 className="font-semibold mb-3">Projects</h2>
            <select
              className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
              value={selectedProjectId}
              onChange={event => setSelectedProjectId(event.target.value)}
            >
              {projects.length === 0 && <option value="">No projects</option>}
              {projects.map(project => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
            {selectedProjectId && (
              <p className="mt-2 text-xs text-slate-400">
                {projectLookup[selectedProjectId]?.description}
              </p>
            )}
          </div>

          {canManageProjects && (
            <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
              <h2 className="font-semibold mb-3">Create project</h2>
              <form className="space-y-3" onSubmit={handleCreateProject}>
                <input
                  placeholder="Project name"
                  className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
                  value={newProjectName}
                  onChange={event => setNewProjectName(event.target.value)}
                  required
                />
                <textarea
                  placeholder="Description"
                  className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm min-h-[90px]"
                  value={newProjectDescription}
                  onChange={event => setNewProjectDescription(event.target.value)}
                />
                <button className="w-full rounded-md bg-indigo-600 hover:bg-indigo-500 px-3 py-2 text-sm font-medium">
                  Add project
                </button>
              </form>
            </div>
          )}

          {canManageUsers && (
            <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
              <h2 className="font-semibold mb-3">User roles</h2>
              <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                {users.map(user => (
                  <div
                    key={user.id}
                    className="rounded-md border border-slate-800 bg-slate-950 p-2"
                  >
                    <p className="text-sm font-medium">{user.name}</p>
                    <p className="text-xs text-slate-400 mb-2">{user.email}</p>
                    <select
                      className="w-full rounded-md border border-slate-700 bg-slate-900 px-2 py-1 text-xs"
                      value={user.role}
                      onChange={event =>
                        handleUserRoleUpdate(user.id, event.target.value as UserRole)
                      }
                    >
                      <option value="admin">admin</option>
                      <option value="manager">manager</option>
                      <option value="developer">developer</option>
                      <option value="tester">tester</option>
                    </select>
                  </div>
                ))}
              </div>
            </div>
          )}
        </aside>

        <section className="lg:col-span-6 space-y-4">
          <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
            <h2 className="font-semibold mb-3">Create issue</h2>
            <form onSubmit={handleCreateIssue} className="space-y-3">
              <input
                className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
                placeholder="Issue title"
                value={newIssueTitle}
                onChange={event => setNewIssueTitle(event.target.value)}
                required
              />
              <textarea
                className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm min-h-[110px]"
                placeholder="Issue description"
                value={newIssueDescription}
                onChange={event => setNewIssueDescription(event.target.value)}
                required
              />
              <div className="grid sm:grid-cols-3 gap-2">
                <select
                  className="rounded-md border border-slate-700 bg-slate-950 px-2 py-2 text-sm"
                  value={newIssuePriority}
                  onChange={event => setNewIssuePriority(event.target.value as IssuePriority)}
                >
                  <option value="low">low</option>
                  <option value="medium">medium</option>
                  <option value="high">high</option>
                  <option value="critical">critical</option>
                </select>
                <select
                  className="rounded-md border border-slate-700 bg-slate-950 px-2 py-2 text-sm"
                  value={newIssueAssigneeId}
                  onChange={event => setNewIssueAssigneeId(event.target.value)}
                >
                  <option value="">Unassigned</option>
                  {users.map(user => (
                    <option key={user.id} value={user.id}>
                      {user.name}
                    </option>
                  ))}
                </select>
                <input
                  className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
                  placeholder="tags: api,auth"
                  value={newIssueTags}
                  onChange={event => setNewIssueTags(event.target.value)}
                />
              </div>
              <button
                className="rounded-md bg-indigo-600 hover:bg-indigo-500 px-3 py-2 text-sm font-medium"
                disabled={!selectedProjectId}
              >
                Create issue
              </button>
            </form>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-3">
              <h2 className="font-semibold">Issue board</h2>
              <div className="flex gap-2">
                <select
                  className="rounded-md border border-slate-700 bg-slate-950 px-2 py-1 text-xs"
                  value={statusFilter}
                  onChange={event => setStatusFilter(event.target.value as IssueStatus | 'all')}
                >
                  <option value="all">all statuses</option>
                  <option value="open">open</option>
                  <option value="in_progress">in_progress</option>
                  <option value="resolved">resolved</option>
                  <option value="closed">closed</option>
                </select>
                <select
                  className="rounded-md border border-slate-700 bg-slate-950 px-2 py-1 text-xs"
                  value={priorityFilter}
                  onChange={event =>
                    setPriorityFilter(event.target.value as IssuePriority | 'all')
                  }
                >
                  <option value="all">all priorities</option>
                  <option value="low">low</option>
                  <option value="medium">medium</option>
                  <option value="high">high</option>
                  <option value="critical">critical</option>
                </select>
              </div>
            </div>

            <div className="space-y-3 max-h-[600px] overflow-y-auto pr-1">
              {filteredIssues.length === 0 && (
                <p className="text-sm text-slate-400">No issues found for current filters.</p>
              )}
              {filteredIssues.map(issue => (
                <button
                  key={issue.id}
                  type="button"
                  className={`w-full text-left rounded-lg border p-3 transition ${
                    selectedIssueId === issue.id
                      ? 'border-indigo-500 bg-indigo-950/30'
                      : 'border-slate-800 bg-slate-950 hover:bg-slate-900'
                  }`}
                  onClick={() => setSelectedIssueId(issue.id)}
                >
                  <p className="font-medium">{issue.title}</p>
                  <p className="text-xs text-slate-400 mt-1">
                    Project: {projectLookup[issue.project_id]?.name || issue.project_id}
                  </p>
                  <p className="text-xs text-slate-400 mt-1">
                    Status: {issue.status} | Priority: {issue.priority}
                  </p>
                  <p className="text-xs text-slate-400 mt-1">
                    Assignee: {issue.assignee_id ? userLookup[issue.assignee_id]?.name || 'Unknown' : 'Unassigned'}
                  </p>
                </button>
              ))}
            </div>
          </div>
        </section>

        <section className="lg:col-span-3">
          <div className="rounded-xl border border-slate-800 bg-slate-900 p-4 min-h-[340px]">
            <h2 className="font-semibold mb-3">Issue details</h2>
            {!selectedIssue && <p className="text-sm text-slate-400">Select an issue to inspect.</p>}
            {selectedIssue && (
              <div className="space-y-3">
                <div>
                  <p className="font-medium">{selectedIssue.title}</p>
                  <p className="text-xs text-slate-400 mt-1">{selectedIssue.description}</p>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <select
                    className="rounded-md border border-slate-700 bg-slate-950 px-2 py-2 text-xs"
                    value={selectedIssue.status}
                    onChange={event =>
                      updateIssue(selectedIssue.id, {
                        status: event.target.value as IssueStatus,
                      })
                    }
                  >
                    <option value="open">open</option>
                    <option value="in_progress">in_progress</option>
                    <option value="resolved">resolved</option>
                    <option value="closed">closed</option>
                  </select>
                  <select
                    className="rounded-md border border-slate-700 bg-slate-950 px-2 py-2 text-xs"
                    value={selectedIssue.priority}
                    onChange={event =>
                      updateIssue(selectedIssue.id, {
                        priority: event.target.value as IssuePriority,
                      })
                    }
                  >
                    <option value="low">low</option>
                    <option value="medium">medium</option>
                    <option value="high">high</option>
                    <option value="critical">critical</option>
                  </select>
                </div>

                {canAssignIssues && (
                  <select
                    className="w-full rounded-md border border-slate-700 bg-slate-950 px-2 py-2 text-xs"
                    value={selectedIssue.assignee_id || ''}
                    onChange={event =>
                      updateIssue(selectedIssue.id, {
                        assignee_id: event.target.value || null,
                      })
                    }
                  >
                    <option value="">Unassigned</option>
                    {users.map(user => (
                      <option key={user.id} value={user.id}>
                        {user.name}
                      </option>
                    ))}
                  </select>
                )}

                <div className="border-t border-slate-800 pt-3">
                  <h3 className="text-sm font-medium mb-2">Comments</h3>
                  <div className="space-y-2 max-h-52 overflow-y-auto pr-1">
                    {(commentsByIssue[selectedIssue.id] || []).map(comment => (
                      <div
                        key={comment.id}
                        className="rounded-md border border-slate-800 bg-slate-950 px-2 py-2"
                      >
                        <p className="text-xs text-slate-300">{comment.body}</p>
                        <p className="text-[11px] text-slate-500 mt-1">
                          {userLookup[comment.author_id]?.name || comment.author_id}
                        </p>
                      </div>
                    ))}
                  </div>
                  <form onSubmit={handleAddComment} className="mt-2 space-y-2">
                    <textarea
                      className="w-full rounded-md border border-slate-700 bg-slate-950 px-2 py-2 text-xs min-h-[70px]"
                      placeholder="Add comment..."
                      value={newCommentBody}
                      onChange={event => setNewCommentBody(event.target.value)}
                    />
                    <button className="w-full rounded-md bg-indigo-600 hover:bg-indigo-500 px-2 py-2 text-xs font-medium">
                      Post comment
                    </button>
                  </form>
                </div>
              </div>
            )}
          </div>
        </section>
      </section>
    </main>
  );
}

function StatCard({ title, value }: { title: string; value: number }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 px-3 py-3">
      <p className="text-xs uppercase tracking-wide text-slate-400">{title}</p>
      <p className="text-xl font-semibold mt-1">{value}</p>
    </div>
  );
}
