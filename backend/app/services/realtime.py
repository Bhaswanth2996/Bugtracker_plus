from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket


class IssuesWebSocketHub:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)

    async def broadcast(self, message: dict[str, Any]) -> None:
        async with self._lock:
            targets = list(self._connections)
        if not targets:
            return
        dead: list[WebSocket] = []
        for socket in targets:
            try:
                await socket.send_json(message)
            except Exception:
                dead.append(socket)
        if dead:
            async with self._lock:
                for socket in dead:
                    self._connections.discard(socket)


class RealtimePublisher:
    def __init__(self, hub: IssuesWebSocketHub | None, event_loop: asyncio.AbstractEventLoop | None) -> None:
        self.hub = hub
        self.event_loop = event_loop

    def publish(self, message: dict[str, Any]) -> None:
        if not self.hub or not self.event_loop or self.event_loop.is_closed():
            return
        payload = {
            **message,
            "timestamp": message.get("timestamp") or datetime.now(tz=timezone.utc).isoformat(),
        }
        asyncio.run_coroutine_threadsafe(self.hub.broadcast(payload), self.event_loop)
