const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function resolveWsUrl() {
  const parsed = new URL(API_BASE_URL);
  const protocol = parsed.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${parsed.host}/ws/issues`;
}

class IssueWebSocketService {
  constructor() {
    this.socket = null;
    this.listeners = new Set();
    this.reconnectTimer = null;
    this.explicitlyClosed = false;
    this.token = null;
  }

  connect(token) {
    this.token = token || this.token || null;
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      return;
    }
    const baseUrl = resolveWsUrl();
    const url = this.token ? `${baseUrl}?token=${encodeURIComponent(this.token)}` : baseUrl;
    this.explicitlyClosed = false;
    this.socket = new WebSocket(url);

    this.socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        this.listeners.forEach((listener) => listener(payload));
      } catch {
        // Ignore malformed websocket messages.
      }
    };
    this.socket.onclose = () => {
      this.socket = null;
      if (!this.explicitlyClosed) {
        this.reconnectTimer = window.setTimeout(() => this.connect(this.token), 2000);
      }
    };
  }

  subscribe(listener, token) {
    if (typeof listener !== "function") {
      return () => {};
    }
    this.listeners.add(listener);
    this.connect(token);
    return () => {
      this.listeners.delete(listener);
      if (this.listeners.size === 0) {
        this.disconnect();
      }
    };
  }

  disconnect() {
    this.explicitlyClosed = true;
    if (this.reconnectTimer) {
      window.clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }
}

export const issueWebSocketService = new IssueWebSocketService();
