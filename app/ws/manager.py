import asyncio
from contextlib import suppress

from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: list[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        websocket.scope["user_id"] = user_id

        async with self._lock:
            self._connections.append(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            if websocket in self._connections:
                self._connections.remove(websocket)

        with suppress(RuntimeError, WebSocketDisconnect):
            await websocket.close()

    async def send_personal_message(self, message: dict, user_id: str) -> bool:
        target = None

        async with self._lock:
            for websocket in self._connections:
                if websocket.scope.get("user_id") == user_id:
                    target = websocket
                    break

        if target is None:
            return False

        try:
            await target.send_json(message)
            return True
        except (RuntimeError, WebSocketDisconnect):
            with suppress(Exception):
                await self.disconnect(target)

            return False
