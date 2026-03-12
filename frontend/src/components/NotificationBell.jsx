import { useEffect, useState } from "react";

import { api, parseApiError } from "../services/api";

export default function NotificationBell() {
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");
  const [open, setOpen] = useState(false);

  async function loadNotifications() {
    try {
      const response = await api.listNotifications();
      setItems(response.data);
      setError("");
    } catch (err) {
      setError(parseApiError(err));
    }
  }

  async function markRead(notificationId) {
    try {
      await api.markNotificationRead(notificationId);
      setItems((prev) =>
        prev.map((item) =>
          item.id === notificationId ? { ...item, read: true } : item
        )
      );
    } catch (err) {
      setError(parseApiError(err));
    }
  }

  useEffect(() => {
    loadNotifications();
    const interval = setInterval(loadNotifications, 25000);
    return () => clearInterval(interval);
  }, []);

  const unreadCount = items.filter((item) => !item.read).length;

  return (
    <div className="relative">
      <button
        type="button"
        className="rounded-md border border-slate-700 px-3 py-1 text-sm hover:bg-slate-800"
        onClick={() => setOpen((value) => !value)}
      >
        Notifications {unreadCount > 0 ? `(${unreadCount})` : ""}
      </button>
      {open && (
        <div className="absolute right-0 mt-2 w-96 max-h-96 overflow-y-auto rounded-md border border-slate-700 bg-slate-900 z-20">
          <div className="p-2 border-b border-slate-700 text-sm font-semibold">
            Recent notifications
          </div>
          {error && <p className="p-2 text-xs text-rose-400">{error}</p>}
          {items.length === 0 && (
            <p className="p-2 text-xs text-slate-400">No notifications yet.</p>
          )}
          {items.map((item) => (
            <button
              type="button"
              key={item.id}
              className={`w-full text-left p-3 border-b border-slate-800 hover:bg-slate-800 ${
                item.read ? "opacity-70" : "opacity-100"
              }`}
              onClick={() => markRead(item.id)}
            >
              <p className="text-sm font-medium">{item.title}</p>
              <p className="text-xs text-slate-400 mt-1">{item.message}</p>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
