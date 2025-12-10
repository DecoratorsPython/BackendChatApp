import os
import sys

# add project root to sys.path 
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.ws.deps import are_friends
from app.core.security import InvalidTokenError, ExpiredTokenError

import app.ws.chat as chat_module


from starlette.websockets import WebSocketDisconnect


ALICE_ID = "11111111-1111-1111-1111-111111111111"
BOB_ID = "22222222-2222-2222-2222-222222222222"
CHARLIE_ID = "33333333-3333-3333-3333-333333333333"


class FakeTokenData:
    def __init__(self, sub: str) -> None:
        self.sub = sub


def fake_verify_access_token(token: str) -> FakeTokenData:

    if token == "alice":
        return FakeTokenData(ALICE_ID)
    if token == "bob":
        return FakeTokenData(BOB_ID)
    if token == "charlie":
        return FakeTokenData(CHARLIE_ID)

    raise InvalidTokenError("Invalid token in tests")


@pytest.fixture(autouse=True)
def patch_verify_token(monkeypatch):

    monkeypatch.setattr(chat_module, "verify_access_token", fake_verify_access_token)
    yield


@pytest.fixture()
def client():
    
    with TestClient(app) as c:
        yield c


#  Integration tests 

def test_ws_chat_between_friends_message_delivered(client: TestClient):
    
    with client.websocket_connect("/chat?token=alice") as ws_alice:
        with client.websocket_connect("/chat?token=bob") as ws_bob:
            payload = {
                "to": BOB_ID,
                "message": {"text": "hello bob"},
            }
            ws_alice.send_json(payload)

            bob_recv = ws_bob.receive_json()
            assert bob_recv == {"text": "hello bob"}

            alice_recv = ws_alice.receive_json()
            assert alice_recv["status"] == "Sent"
            assert alice_recv["to"] == BOB_ID


def test_ws_chat_not_friends_returns_not_friends_status(client: TestClient):
    
    with client.websocket_connect("/chat?token=bob") as ws_bob:
        payload = {
            "to": CHARLIE_ID,
            "message": {"text": "hi charlie"},
        }
        ws_bob.send_json(payload)

        resp = ws_bob.receive_json()
        assert resp["status"] == "Not friends"



def test_ws_chat_missing_token_is_rejected(client: TestClient):
   
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect("/chat") as ws:
            ws.send_json({"text": "test"})

    assert exc_info.value.code == 1008


def test_ws_chat_invalid_token_is_rejected(client: TestClient):
    
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect("/chat?token=invalid") as ws:
            ws.send_json({"text": "test"})

    assert exc_info.value.code == 1008
