import { NavLink } from "react-router-dom";

const tabs = [
  { key: "overview", label: "Issues", suffix: "" },
  { key: "board", label: "Board", suffix: "/board" },
  { key: "backlog", label: "Backlog", suffix: "/backlog" },
  { key: "reports", label: "Reports", suffix: "/reports" },
  { key: "members", label: "Members", suffix: "/members" },
  { key: "settings", label: "Settings", suffix: "/settings" },
];

export default function ProjectWorkspaceTabs({ projectKey }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-1 flex flex-wrap gap-1">
      {tabs.map((tab) => (
        <NavLink
          key={tab.key}
          to={`/project/${projectKey}${tab.suffix}`}
          className={({ isActive }) =>
            `rounded-lg px-3 py-1.5 text-sm transition ${
              isActive
                ? "bg-brand-600 text-white shadow"
                : "text-slate-300 hover:bg-slate-800"
            }`
          }
          end={tab.key === "overview"}
        >
          {tab.label}
        </NavLink>
      ))}
    </div>
  );
}
