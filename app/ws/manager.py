import asyncio
from contextlib import suppress

from fastapi import WebSocket, WebSocketDisconnect

import logging

logging.basicConfig(level=logging.INFO)

class ConnectionManager:
    def __init__(self) -> None:
        self._connections: list[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        logging.info(f"WebSocket connection accepted for user {user_id}")
        websocket.scope["user_id"] = user_id

        async with self._lock:
            logging.info("Adding websocket to active connections")
            self._connections.append(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            if websocket in self._connections:
                logging.info("Removing websocket from active connections")
                self._connections.remove(websocket)

        with suppress(RuntimeError, WebSocketDisconnect):
            await websocket.close()

    async def send_personal_message(self, message: dict, user_id: str) -> bool:
        target = None

        async with self._lock:
            for websocket in self._connections:
                logging.info("Checking active connection for target user")
                if websocket.scope.get("user_id") == user_id:
                    logging.info("Target user found, preparing to send message")
                    target = websocket
                    break

        if target is None:
            logging.info("Target user not connected")
            return False

        try:
            logging.info("Sending message to target user")
            await target.send_json(message)
            return True
        except (RuntimeError, WebSocketDisconnect):
            with suppress(Exception):
                await self.disconnect(target)

            return False
