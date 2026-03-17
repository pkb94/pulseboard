"""
LAYER 4 — PRESENTATION — app/presentation/api/routes/websocket.py
────────────────────────────────────────────────────────────────────
LESSON: The WebSocket route is tiny — it just registers the connection
and waits. All the interesting work happens in the ConnectionManager
and the simulator (which calls broadcast() via the use case).

Client connection lifecycle:
  connect → receive messages (heartbeats) → disconnect on error/close

The try/finally guarantees we always remove the client from the registry
even if the connection drops without a proper close frame.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.dependencies import get_connection_manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/metrics")
async def metrics_websocket(ws: WebSocket) -> None:
    manager = get_connection_manager()
    """
    WebSocket endpoint that streams real-time metric updates and anomaly alerts.

    The client connects once and receives a continuous stream of JSON messages:
      { "type": "metrics_update",   "payload": {...}, "timestamp": "...", "sequence": N }
      { "type": "anomaly_detected", "payload": {...}, "timestamp": "...", "sequence": N }
      { "type": "heartbeat",        "payload": {},    "timestamp": "...", "sequence": N }
    """
    await manager.connect(ws)
    try:
        while True:
            # Keep the connection alive by waiting for any client message.
            # Clients send a ping every 30s; we just discard it.
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception:
        manager.disconnect(ws)
