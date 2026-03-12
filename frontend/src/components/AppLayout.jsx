import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import NotificationBell from "./NotificationBell";

const navItems = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/projects", label: "Project List" },
  { to: "/create-issue", label: "Create Issue" },
  { to: "/profile", label: "User Profile" },
  { to: "/admin", label: "Admin Settings" },
];

function getNavClassName({ isActive }) {
  return `block rounded-md px-3 py-2 text-sm transition ${
    isActive ? "bg-brand-600 text-white" : "text-slate-200 hover:bg-slate-800"
  }`;
}

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 grid grid-cols-12">
      <aside className="col-span-12 md:col-span-3 lg:col-span-2 border-r border-slate-800 p-4">
        <h1 className="text-xl font-bold mb-6">BugTracker+</h1>
        <nav className="space-y-2">
          {navItems.map((item) => (
            <NavLink key={item.to} to={item.to} className={getNavClassName}>
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <section className="col-span-12 md:col-span-9 lg:col-span-10">
        <header className="border-b border-slate-800 px-4 py-3 flex items-center justify-between">
          <div>
            <p className="text-sm text-slate-300">{user?.name}</p>
            <p className="text-xs text-slate-400">{user?.role}</p>
          </div>
          <div className="flex gap-2 items-center">
            <NotificationBell />
            <button
              type="button"
              className="rounded-md border border-slate-700 px-3 py-1 text-sm hover:bg-slate-800"
              onClick={() => navigate("/projects")}
            >
              Workspace
            </button>
            <button
              type="button"
              className="rounded-md bg-rose-600 hover:bg-rose-500 px-3 py-1 text-sm"
              onClick={logout}
            >
              Logout
            </button>
          </div>
        </header>
        <main className="p-4">
          <Outlet />
        </main>
      </section>
    </div>
  );
}
