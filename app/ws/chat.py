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
from app.services.chat_service import mark_messages_seen
from app.services.friendship_service import is_friend
from app.ws.manager import ConnectionManager

import logging

logging.basicConfig(level=logging.INFO)

router = APIRouter()
manager = ConnectionManager()


@router.websocket("/chat")
async def user_chat(websocket: WebSocket):
    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        logging.info("Verifying access token")
        token_data = verify_access_token(token)
    except (ExpiredTokenError, InvalidTokenError) as err:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    logging.info(f"User {token_data.sub} connected")
    sender_id = str(token_data.sub)

    await manager.connect(sender_id, websocket)

    try:
        while True:
            logging.info("Waiting to receive message data")
            data = await websocket.receive_json()

            event_type = data.get("type", "message")

            if event_type == "mark_seen":
                conversation_id = data.get("conversation_id")
                if not conversation_id:
                    await websocket.send_json({"error": "Missing conversation_id"})
                    continue

                try:
                    await mark_messages_seen(conversation_id, sender_id)
                    await websocket.send_json({
                        "status": "seen",
                        "conversation_id": conversation_id
                    })
                except Exception as err:
                    await websocket.send_json({
                        "error": "Failed to mark messages seen",
                        "details": str(err)
                    })
                continue

            try:
                logging.info(f"Received message data: {data}")
                logging.info("Validating message data")
                message = MessageReceive(**data)
            except ValidationError as err:
                await websocket.send_json(
                    {"error": "Invalid data", "details": err.errors()}
                )
                continue

            recipient_id = str(message.user_id)

            logging.info(f"Processing message from {sender_id} to {recipient_id}")
            if recipient_id is None:
                await websocket.send_json({"error": "Missing target"})
                continue

            logging.info("Retrieving conversation ID")
            conversation_id = str(message.conversation_id)

            if conversation_id is None:
                await websocket.send_json({"error": "Missing conversation ID"})
                continue

            try:
                logging.info("Verifying friendship status")
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
                logging.info("Users are not friends")
                await websocket.send_json({"error": "Users are not friends"})
                continue

            try:
                logging.info("Persisting outgoing message")
                await persist_outgoing_message(
                    sender_id, recipient_id, message.content, conversation_id
                )
            except Exception as err:
                await websocket.send_json(
                    {"error": "Failed to persist message", "details": str(err)}
                )
                continue

            payload = {
                "message": message.content,
                "from": sender_id,
                "conversation_id": conversation_id,
            }
            logging.info("Sending personal message")

            delivered = await manager.send_personal_message(
                payload, recipient_id
            )

            if delivered:
                logging.info("Message delivered to recipient")
                await websocket.send_json(
                    {"status": "sent", "to": recipient_id}
                )
            else:
                logging.info("Message stored for later delivery")
                await websocket.send_json(
                    {"status": "stored", "to": recipient_id}
                )

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
