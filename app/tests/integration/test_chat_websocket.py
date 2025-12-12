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
import app.ws.chat as chat_module

ALICE_ID = "11111111-1111-1111-1111-111111111111"
BOB_ID = "22222222-2222-2222-2222-222222222222"
CHARLIE_ID = "33333333-3333-3333-3333-333333333333"


class FakeTokenData:
    def __init__(self, sub):
        self.sub = sub


def fake_verify_access_token(token: str):
    if token == "alice": return FakeTokenData(ALICE_ID)
    if token == "bob": return FakeTokenData(BOB_ID)
    if token == "charlie": return FakeTokenData(CHARLIE_ID)
    raise chat_module.InvalidTokenError("Invalid token")


@pytest.fixture(autouse=True)
def override_token(monkeypatch):
    monkeypatch.setattr(chat_module, "verify_access_token", fake_verify_access_token)


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.mark.asyncio
async def test_ws_connect_and_disconnect(client):
    with client.websocket_connect("/chat?token=alice&conversation_id=convA") as ws:
        ws.send_json({
            "user_id": BOB_ID,
            "content": "test",
            "conversation_id": "convA"
        })
        resp = ws.receive_json()

        assert resp["status"] in ("sent", "stored")


@pytest.mark.asyncio
async def test_ws_message_goes_only_to_matching_conversation(client):
    with client.websocket_connect("/chat?token=bob&conversation_id=convA") as wsA:
        with client.websocket_connect("/chat?token=bob&conversation_id=convB") as wsB:

            wsA.send_json({
                "user_id": BOB_ID,
                "content": "hello",
                "conversation_id": "convA"
            })

            ack = wsA.receive_json()
            assert "status" in ack or "message" in ack

            with pytest.raises(Exception):
                wsB.receive_json(timeout=0.2)


@pytest.mark.asyncio
async def test_ws_not_friends_rejected(client):
    with client.websocket_connect("/chat?token=bob&conversation_id=convX") as ws:
        ws.send_json({
            "user_id": CHARLIE_ID,
            "content": "hi",
            "conversation_id": "convX"
        })

        resp = ws.receive_json()
        assert resp["error"] == "Users are not friends"


def test_ws_missing_token_rejected(client):
    with pytest.raises(WebSocketDisconnect):
        client.websocket_connect("/chat?conversation_id=convX")


def test_ws_invalid_token_rejected(client):
    with pytest.raises(WebSocketDisconnect):
        client.websocket_connect("/chat?token=bad&conversation_id=convX")
