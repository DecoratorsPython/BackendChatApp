import asyncio

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._conversations: dict[str, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(
        self, conversation_id: str, websocket: WebSocket
    ) -> None:
        await websocket.accept()
        async with self._lock:
            if conversation_id not in self._conversations:
                self._conversations[conversation_id] = set()
            self._conversations[conversation_id].add(websocket)

    async def disconnect(self, user_id: str) -> None:
        websocket = self._active_connections.pop(user_id, None)
        await websocket.close()

    async def send_personal_message(self, message: str, user_id: str) -> bool:
        websocket = self._active_connections.get(user_id)
        if websocket is None:
            return False
        try:
            await websocket.send_text(message)
            return True
        except Exception:
            await self.disconnect(user_id=user_id)
            return False
