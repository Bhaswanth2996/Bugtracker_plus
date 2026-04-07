export default function UserAvatar({ name, size = "sm" }) {
  const initials = (name || "U")
    .split(" ")
    .slice(0, 2)
    .map((item) => item[0]?.toUpperCase() || "")
    .join("");

  const sizeClass = size === "lg" ? "h-10 w-10 text-sm" : "h-7 w-7 text-[11px]";

  return (
    <span
      className={`${sizeClass} inline-flex items-center justify-center rounded-full bg-indigo-600/70 font-semibold text-white ring-1 ring-indigo-400/40`}
      title={name}
    >
      {initials}
    </span>
  );
}
