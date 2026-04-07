import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { parseApiError } from "../services/api";

export default function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function onSubmit(event) {
    event.preventDefault();
    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (err) {
      setError(parseApiError(err));
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center px-4">
      <div className="w-full max-w-md rounded-lg border border-slate-800 bg-slate-900 p-6">
        <h1 className="text-2xl font-bold text-slate-100">Login</h1>
        <p className="text-sm text-slate-400 mt-1">Sign in to BugTracker+</p>
        <form className="mt-6 space-y-4" onSubmit={onSubmit}>
          <input
            className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100"
            type="email"
            placeholder="Email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
          <input
            className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100"
            type="password"
            placeholder="Password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
          <button className="w-full rounded-md bg-brand-600 hover:bg-brand-700 px-3 py-2">
            Sign In
          </button>
        </form>
        {error && <p className="mt-3 text-sm text-rose-400">{error}</p>}
        <p className="mt-4 text-sm text-slate-400">
          No account?{" "}
          <Link to="/register" className="text-blue-400 hover:underline">
            Register
          </Link>
        </p>
      </div>
    </div>
  );
}
