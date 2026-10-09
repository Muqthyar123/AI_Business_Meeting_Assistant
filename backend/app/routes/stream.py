"""Real-time WebSocket and HTTP streaming router for live meeting and dictation transcription."""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(tags=["stream"])


class LiveSegmentPayload(BaseModel):
    """Payload for submitting or broadcasting a speech transcript segment."""

    text: str = Field(..., min_length=1, description="Transcribed speech segment text")
    timestamp: Optional[str] = Field(default=None, description="Time of speech capture (HH:MM:SS)")
    mode: str = Field(default="meeting", description="Source mode: 'meeting' or 'dictation'")
    segment_id: Optional[int] = Field(default=None, description="Sequential segment ID")


class ConnectionManager:
    """Thread-safe WebSocket connection manager with broadcast capabilities."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()
        self.recent_history: List[Dict[str, Any]] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
        logger.info("WebSocket client connected. Active clients: %d", len(self.active_connections))

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self.active_connections.discard(websocket)
        logger.info("WebSocket client disconnected. Active clients: %d", len(self.active_connections))

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Broadcasts a JSON message to all active WebSocket clients."""
        async with self._lock:
            # Store in recent history buffer (max 50)
            self.recent_history.append(message)
            if len(self.recent_history) > 50:
                self.recent_history = self.recent_history[-50:]

            disconnected = set()
            for connection in self.active_connections:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.debug("Failed sending to client: %s", str(e))
                    disconnected.add(connection)

            for conn in disconnected:
                self.active_connections.discard(conn)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_live_stream(websocket: WebSocket):
    """WebSocket endpoint for real-time speech streaming between Desktop Assistant and React Frontend."""
    await manager.connect(websocket)
    try:
        while True:
            data_text = await websocket.receive_text()
            try:
                data = json.loads(data_text)
                msg_type = data.get("type", "speech_segment")

                if msg_type == "ping":
                    await websocket.send_text(json.dumps({"type": "pong", "timestamp": datetime.now(timezone.utc).isoformat()}))
                    continue

                if msg_type == "speech_segment" or "text" in data:
                    payload = {
                        "type": "speech_segment",
                        "text": data.get("text", "").strip(),
                        "timestamp": data.get("timestamp") or datetime.now(timezone.utc).strftime("%H:%M:%S"),
                        "mode": data.get("mode", "meeting"),
                        "segment_id": data.get("segment_id"),
                        "received_at": datetime.now(timezone.utc).isoformat(),
                    }
                    if payload["text"]:
                        await manager.broadcast(payload)

            except json.JSONDecodeError:
                logger.warning("Received invalid non-JSON WebSocket message: %s", data_text)

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        logger.warning("WebSocket error: %s", str(e))
        await manager.disconnect(websocket)


@router.post(
    "/publish",
    status_code=status.HTTP_200_OK,
    summary="Publish speech segment via HTTP",
    description="HTTP fallback endpoint to broadcast transcribed speech segments to all connected web clients.",
)
async def publish_segment(payload: LiveSegmentPayload):
    """Publish a transcribed segment to all connected WebSocket clients."""
    clean_text = payload.text.strip()
    if not clean_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Segment text cannot be empty.")

    broadcast_msg = {
        "type": "speech_segment",
        "text": clean_text,
        "timestamp": payload.timestamp or datetime.now(timezone.utc).strftime("%H:%M:%S"),
        "mode": payload.mode,
        "segment_id": payload.segment_id,
        "received_at": datetime.now(timezone.utc).isoformat(),
    }
    await manager.broadcast(broadcast_msg)
    return {"status": "broadcasted", "active_clients": len(manager.active_connections)}


@router.get(
    "/history",
    summary="Get recent live stream history",
    description="Returns recent broadcasted speech segments from active meeting sessions.",
)
async def get_stream_history():
    """Retrieve recent streamed transcript segments."""
    return {
        "history": manager.recent_history,
        "active_clients": len(manager.active_connections),
    }
