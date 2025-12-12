import os
import sys
import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from app.main import app
from app.ws.chat import manager  


client = TestClient(app)


def open_ws(token="alice", conv="convA"):
    """Open a REAL websocket connection via FastAPI TestClient."""
    return client.websocket_connect(
        f"/chat?token={token}&conversation_id={conv}"
    )


def test_manager_connect_and_disconnect_real_ws():
    ws = open_ws("alice", "convA")

    conns = manager._connections.get("alice")
    assert conns is not None
    assert len(conns) == 1

    ws.close()

    conns = manager._connections.get("alice")
    assert conns is not None


@pytest.mark.asyncio
async def test_manager_sends_message_to_conversation_specific_socket():
    wsA = open_ws("bob", "convA")
    wsB = open_ws("bob", "convB")

    payload = {"message": "hello", "conversation_id": "convA"}

    sent = await manager.send_personal_message(payload, "bob", "convA")
    assert sent is True

    recvA = wsA.receive_json()
    assert recvA["message"] == "hello"
    assert recvA["conversation_id"] == "convA"

    with pytest.raises(Exception):
        wsB.receive_json(timeout=0.2)

    wsA.close()
    wsB.close()
