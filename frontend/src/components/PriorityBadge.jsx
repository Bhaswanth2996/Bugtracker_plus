const colorMap = {
  low: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
  medium: "bg-amber-500/20 text-amber-300 border-amber-500/40",
  high: "bg-rose-500/20 text-rose-300 border-rose-500/40",
  critical: "bg-fuchsia-500/20 text-fuchsia-300 border-fuchsia-500/40",
};

export default function PriorityBadge({ priority }) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-semibold uppercase ${
        colorMap[priority] || "bg-slate-700 text-slate-200 border-slate-600"
      }`}
    >
      {priority}
    </span>
  );
}
