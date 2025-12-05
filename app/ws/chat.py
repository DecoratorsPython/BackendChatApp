from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.core.security import (
    ExpiredTokenError,
    InvalidTokenError,
    verify_access_token,
)
from app.ws.deps import are_friends
from app.ws.manager import ConnectionManager

router = APIRouter()
manager = ConnectionManager()


@router.websocket("/ws/chat/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: str):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        token_data = verify_access_token(token)
    except (InvalidTokenError, ExpiredTokenError):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    sender_id = str(token_data.sub)
    recipient_id = str(user_id)

    if not are_friends(sender_id, recipient_id):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(sender_id, websocket)

    try:
        while True:
            message = await websocket.receive_text()

            await manager.send_personal_message(message, recipient_id)

            await websocket.send_json({"status": "sent", "to": recipient_id})

    except WebSocketDisconnect:
        await manager.disconnect(user_id=sender_id)
