"""WebSocket route for real-time progress updates."""
from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from fda_engine.api.deps import get_state
from fda_engine.api.models import WsProgressEvent

router = APIRouter(tags=["ws"])


class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active_connections.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active_connections.remove(ws)

    async def broadcast(self, event: WsProgressEvent):
        message = event.model_dump_json()
        for conn in self.active_connections:
            try:
                await conn.send_text(message)
            except Exception:
                pass


manager = ConnectionManager()


@router.websocket("/ws/status")
async def websocket_status(ws: WebSocket):
    """WebSocket endpoint for real-time generation progress."""
    await manager.connect(ws)
    try:
        while True:
            # Keep connection alive, receive client messages
            data = await ws.receive_text()
            # Client can send ping or subscribe to specific tasks
            msg = json.loads(data)
            if msg.get("type") == "ping":
                await ws.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        manager.disconnect(ws)


async def broadcast_progress(event: WsProgressEvent):
    """Broadcast a progress event to all connected clients."""
    await manager.broadcast(event)
