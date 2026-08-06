"""Per-channel WebSocket fan-out for live pipeline progress.

The frontend generates a channel id, opens /ws/progress/{channel}, then sends
that same id with its upload/query request. Stage events are pushed back so the
UI can show where the pipeline currently is.
"""
import asyncio
from typing import Any, Dict, Optional, Set

from fastapi import WebSocket


class ProgressHub:
    def __init__(self):
        self._channels: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, channel: str, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self._channels.setdefault(channel, set()).add(websocket)
        print(f"[progress] client connected to channel {channel}")

    async def disconnect(self, channel: str, websocket: WebSocket):
        async with self._lock:
            subscribers = self._channels.get(channel)
            if subscribers:
                subscribers.discard(websocket)
                if not subscribers:
                    self._channels.pop(channel, None)
        print(f"[progress] client disconnected from channel {channel}")

    async def publish(self, channel: str, event: Dict[str, Any]):
        async with self._lock:
            subscribers = list(self._channels.get(channel, ()))
        if not subscribers:
            return
        dead = []
        for ws in subscribers:
            try:
                await ws.send_json(event)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(channel, ws)


hub = ProgressHub()


def make_emitter(channel: Optional[str], loop: asyncio.AbstractEventLoop):
    """Build a progress callback safe to call from a worker thread.

    Ingestion runs in a threadpool so it doesn't block the event loop, so events
    have to be handed back to the loop thread explicitly.
    """

    def emit(stage: str, message: str, **extra: Any):
        print(f"[{stage}] {message}")
        if not channel:
            return
        event = {"stage": stage, "message": message, **extra}
        asyncio.run_coroutine_threadsafe(hub.publish(channel, event), loop)

    return emit
