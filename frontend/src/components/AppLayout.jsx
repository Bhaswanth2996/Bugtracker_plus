import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { LayoutDashboard, PlusCircle, Settings, Shield, UserCircle } from "lucide-react";

import { useAuth } from "../context/AuthContext";
import NotificationBell from "./NotificationBell";
import UserAvatar from "./UserAvatar";

const navItems = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/projects", label: "Project List", icon: Settings },
  { to: "/create-issue", label: "Create Issue", icon: PlusCircle },
  { to: "/profile", label: "User Profile", icon: UserCircle },
  { to: "/admin", label: "Admin Settings", icon: Shield },
];

function getNavClassName({ isActive }) {
  return `flex items-center gap-2 rounded-md px-3 py-2 text-sm transition ${
    isActive
      ? "bg-brand-600 text-white shadow-sm"
      : "text-slate-200 hover:bg-slate-800/80"
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
              <item.icon className="h-4 w-4" />
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <section className="col-span-12 md:col-span-9 lg:col-span-10">
        <header className="border-b border-slate-800 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <UserAvatar name={user?.name} size="lg" />
            <div>
              <p className="text-sm text-slate-300">{user?.name}</p>
            </div>
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
