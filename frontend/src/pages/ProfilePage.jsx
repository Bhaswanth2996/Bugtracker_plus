import { useEffect, useState } from "react";

import { useAuth } from "../context/AuthContext";
import { api, parseApiError } from "../services/api";

export default function ProfilePage() {
  const { user, refreshMe } = useAuth();
  const [form, setForm] = useState({
    name: "",
    title: "",
    team: "",
    avatar_url: "",
    bio: "",
  });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!user) {
      return;
    }
    setForm({
      name: user.name || "",
      title: user.profile?.title || "",
      team: user.profile?.team || "",
      avatar_url: user.profile?.avatar_url || "",
      bio: user.profile?.bio || "",
    });
  }, [user]);

  async function onSubmit(event) {
    event.preventDefault();
    try {
      await api.updateProfile(form);
      await refreshMe();
      setMessage("Profile updated successfully.");
      setError("");
    } catch (err) {
      setError(parseApiError(err));
      setMessage("");
    }
  }

  return (
    <div className="space-y-4 max-w-3xl">
      <h2 className="text-2xl font-semibold">User Profile</h2>
      <form
        onSubmit={onSubmit}
        className="rounded-md border border-slate-800 bg-slate-900 p-4 grid md:grid-cols-2 gap-3"
      >
        <input
          className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
          placeholder="Name"
          value={form.name}
          onChange={(event) => setForm((prev) => ({ ...prev, name: event.target.value }))}
        />
        <input
          className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
          placeholder="Title"
          value={form.title}
          onChange={(event) => setForm((prev) => ({ ...prev, title: event.target.value }))}
        />
        <input
          className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
          placeholder="Team"
          value={form.team}
          onChange={(event) => setForm((prev) => ({ ...prev, team: event.target.value }))}
        />
        <input
          className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
          placeholder="Avatar URL"
          value={form.avatar_url}
          onChange={(event) =>
            setForm((prev) => ({ ...prev, avatar_url: event.target.value }))
          }
        />
        <textarea
          className="md:col-span-2 rounded-md border border-slate-700 bg-slate-950 px-3 py-2 min-h-24"
          placeholder="Bio"
          value={form.bio}
          onChange={(event) => setForm((prev) => ({ ...prev, bio: event.target.value }))}
        />
        <button className="md:col-span-2 rounded-md bg-brand-600 hover:bg-brand-700 px-3 py-2">
          Save Profile
        </button>
      </form>
      {message && <p className="text-sm text-emerald-400">{message}</p>}
      {error && <p className="text-sm text-rose-400">{error}</p>}
    </div>
  );
}
