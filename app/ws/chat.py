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


@router.websocket("/chat")
async def user_chat(websocket: WebSocket):
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

    await manager.connect(sender_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()

            recipient_id = data.get("to")
            message = data.get("message")

            if not are_friends(sender_id, recipient_id):
                await websocket.send_json({"status": "Not friends"})
            else:
                await manager.send_personal_message(message, recipient_id)
                await websocket.send_json(
                    {"status": "Sent", "to": recipient_id}
                )

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
