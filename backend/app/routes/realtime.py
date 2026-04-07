from __future__ import annotations

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.security import decode_access_token
from app.db.store import BaseStore
from app.services.realtime import IssuesWebSocketHub

router = APIRouter(tags=["realtime"])


@router.websocket("/ws/issues")
async def issues_websocket(
    websocket: WebSocket,
    token: str | None = Query(default=None),
) -> None:
    store: BaseStore = websocket.app.state.store
    hub: IssuesWebSocketHub = websocket.app.state.issues_ws_hub

    if token:
        user_id = decode_access_token(token)
        if not user_id or not store.get_user_by_id(user_id):
            await websocket.close(code=1008, reason="Invalid token.")
            return

    await hub.connect(websocket)
    await websocket.send_json({"event": "connected", "message": "Issue updates stream connected."})
    try:
        while True:
            data = await websocket.receive_text()
            if data.strip().lower() == "ping":
                await websocket.send_json({"event": "pong"})
    except WebSocketDisconnect:
        await hub.disconnect(websocket)
