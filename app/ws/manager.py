import asyncio
from collections import defaultdict
from contextlib import suppress
from typing import Dict, Set, Optional

from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: Dict[str, Set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        websocket.scope["user_id"] = user_id
        websocket.scope.setdefault("conversation_id", None)

        async with self._lock:
          self._connections[user_id].add(websocket)


    async def disconnect(self, websocket: WebSocket) -> None:
        user_id = websocket.scope.get("user_id")
        async with self._lock:
            if user_id and websocket in self._connections.get(user_id, set()):
                self._connections[user_id].remove(websocket)
                if not self._connections[user_id]:
                    del self._connections[user_id]

        with suppress(RuntimeError, WebSocketDisconnect):
            await websocket.close()


    async def send_personal_message(
        self,
        message: dict,
        user_id: str,
        conversation_id: Optional[str] = None,
    ) -> bool:
        async with self._lock:
            targets = list(self._connections.get(user_id, set()))

        if conversation_id is not None:
            targets = [
                ws
                for ws in targets
                if ws.scope.get("conversation_id") == conversation_id
            ]

        if not targets:
            return False

        sent_any = False
        for target in targets:
            try:
                await target.send_json(message)
                sent_any = True
            except (RuntimeError, WebSocketDisconnect):
                with suppress(Exception):
                    await self.disconnect(target)

        return sent_any
