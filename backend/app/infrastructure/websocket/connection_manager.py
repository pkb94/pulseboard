"""
LAYER 3 — INFRASTRUCTURE — app/infrastructure/websocket/connection_manager.py
────────────────────────────────────────────────────────────────────────────────
LESSON: The ConnectionManager is the WebSocket hub — it maintains a registry
of all connected browser clients and broadcasts messages to all of them.

WHY is this in infrastructure and not presentation (FastAPI route)?
  - The broadcast function is injected INTO the use case as a callback
  - The use case calls broadcast() without knowing it's a WebSocket
  - This means you could swap WebSockets for Server-Sent Events (SSE)
    or a message queue (Redis Pub/Sub) by changing only this file

Concurrency safety: asyncio is single-threaded so a plain list is safe
as long as we never `await` while iterating it (we snapshot first).
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Maintains all active WebSocket connections and broadcasts to all of them."""

    def __init__(self) -> None:
        self._active: list[WebSocket] = []
        self._sequence = 0

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._active.append(ws)
        logger.info("WebSocket connected. Total: %d", len(self._active))

    def disconnect(self, ws: WebSocket) -> None:
        self._active = [c for c in self._active if c is not ws]
        logger.info("WebSocket disconnected. Total: %d", len(self._active))

    async def broadcast(self, data: dict) -> None:
        """
        Send a message to ALL connected clients.
        Wraps the payload in a standard envelope with type, timestamp, sequence.
        Removes dead connections silently.
        """
        if not self._active:
            return

        self._sequence += 1
        envelope = {
            **data,
            "timestamp": datetime.utcnow().isoformat(),
            "sequence": self._sequence,
        }
        message = json.dumps(envelope)

        # Snapshot the list before iterating to avoid mutation issues
        dead: list[WebSocket] = []
        for ws in list(self._active):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)

        for ws in dead:
            self.disconnect(ws)

    async def send_heartbeat(self) -> None:
        """Send a keep-alive ping every 30s so clients know the stream is live."""
        await self.broadcast({"type": "heartbeat", "payload": {}})

    @property
    def connection_count(self) -> int:
        return len(self._active)
