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
    mark_messages_seen,
)
from app.repositories.conversation_repository import get_conversation_participants
from app.services.friendship_service import is_friend
from app.ws.manager import ConnectionManager


router = APIRouter()
manager = ConnectionManager()


@router.websocket("/chat")
async def user_chat(websocket: WebSocket):
    token = websocket.query_params.get("token")
    conversation_id = websocket.query_params.get("conversation_id")

    if not token or not conversation_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        token_data = verify_access_token(token)
    except (ExpiredTokenError, InvalidTokenError) as err:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    sender_id = str(token_data.sub)

    await manager.connect(sender_id, websocket)
    websocket.scope["conversation_id"] = conversation_id

    try:
        while True:
            data = await websocket.receive_json()

            event_type = data.get("type", "message")

            if event_type == "mark_seen":
                conv_id = data.get("conversation_id") or conversation_id
                if not conv_id:
                    await websocket.send_json(
                        {"error": "Missing conversation_id for mark_seen"}
                    )
                    continue

                try:
                    await mark_messages_seen(conv_id, sender_id)

                    await websocket.send_json(
                        {
                            "status": "seen",
                            "conversation_id": conv_id,
                            "by": sender_id,
                        }
                    )

                    participants = await get_conversation_participants(conv_id)
                    other_users = [u for u in participants if u != sender_id]

                    for user_id in other_users:
                        await manager.send_personal_message(
                            {
                                "status": "seen",
                                "conversation_id": conv_id,
                                "by": sender_id,
                            },
                            user_id,
                            conv_id,
                        )

                except Exception as err:
                    await websocket.send_json(
                        {
                            "error": "Failed to mark messages seen",
                            "details": str(err),
                        }
                    )

                continue

            try:
                message = MessageReceive(**data)
            except ValidationError as err:
                await websocket.send_json(
                    {"error": "Invalid data", "details": err.errors()}
                )
                continue

            recipient_id = str(message.user_id)
            if not recipient_id:
                await websocket.send_json({"error": "Missing target"})
                continue

            conv_id = str(message.conversation_id or conversation_id)
            if not conv_id:
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
                    sender_id, recipient_id, message.content, conv_id
                )
            except Exception as err:
                await websocket.send_json(
                    {
                        "error": "Failed to persist message",
                        "details": str(err),
                    }
                )
                continue

            payload = {
                "message": message.content,
                "from": sender_id,
                "conversation_id": conv_id,
            }

            delivered = await manager.send_personal_message(
                payload, recipient_id, conv_id
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
