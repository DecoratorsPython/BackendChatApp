from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from pydantic import ValidationError

from app.core.security import (
    ExpiredTokenError,
    InvalidTokenError,
    verify_access_token,
)
from app.schemas.message_receive import MessageReceive
from app.services.chat_service import (
    persist_outgoing_message,
)
from app.services.friendship_service import is_friend
from app.ws.manager import ConnectionManager

router = APIRouter()
manager = ConnectionManager()


@router.websocket("/chat")
async def user_chat(conversation_id: str, websocket: WebSocket):
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

            try:
                message = MessageReceive(**data)
            except ValidationError as err:
                await websocket.send_json(
                    {"error": "Invalid data", "details": err.errors()}
                )
                continue

            recipient_id = str(message.user_id)

            if recipient_id is None:
                await websocket.send_json({"error": "Missing target"})
                continue

            conversation_id = str(message.conversation_id)

            if conversation_id is None:
                await websocket.send_json({"error": "Missing conversation ID"})
                continue

            try:
                friends = await is_friend(sender_id, recipient_id)
            except Exception as err:
                await websocket.send_json(
                    {
                        "error": "Failed to verify friendship",
                        "details": str(err),
                    }
                )
                continue

            if not friends:
                await websocket.send_json({"error": "Users are not friends"})
                continue

            try:
                await persist_outgoing_message(
                    sender_id, recipient_id, message.content, conversation_id
                )
            except Exception as err:
                await websocket.send_json(
                    {"error": "Failed to persist message", "details": str(err)}
                )
                continue

            delivered = await manager.send_personal_message(
                {"message": message.content}, recipient_id
            )

            if delivered:
                await websocket.send_json(
                    {"status": "sent", "to": recipient_id}
                )
            else:
                await websocket.send_json(
                    {"status": "stored", "to": recipient_id}
                )

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
