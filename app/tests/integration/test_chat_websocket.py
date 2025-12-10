import os
import sys

import pytest
from fastapi.testclient import TestClient

# add project root to sys.path 
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from app.main import app
import app.ws.chat as chat_module


class FakeTokenData:
    def __init__(self, sub: str) -> None:
        self.sub = sub


ALICE_ID = "11111111-1111-1111-1111-111111111111"
BOB_ID = "22222222-2222-2222-2222-222222222222"
CHARLIE_ID = "33333333-3333-3333-3333-333333333333"


def fake_verify_access_token(token: str) -> FakeTokenData:
    if token == "alice":
        return FakeTokenData(ALICE_ID)
    if token == "bob":
        return FakeTokenData(BOB_ID)
    if token == "charlie":
        return FakeTokenData(CHARLIE_ID)
    raise Exception("Invalid token")


@pytest.fixture(autouse=True)
def patch_verify_token(monkeypatch):
    monkeypatch.setattr(chat_module, "verify_access_token", fake_verify_access_token)
    yield


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def test_chat_between_friends_message_delivered(client):
    with client.websocket_connect("/chat?token=alice") as ws_alice:
        with client.websocket_connect("/chat?token=bob") as ws_bob:
            payload = {"to": BOB_ID, "message": {"text": "hello bob"}}
            ws_alice.send_json(payload)

            bob_recv = ws_bob.receive_json()
            assert bob_recv == {"text": "hello bob"}

            alice_recv = ws_alice.receive_json()
            assert alice_recv["status"] == "Sent"
            assert alice_recv["to"] == BOB_ID


def test_chat_not_friends_returns_not_friends_status(client):
    with client.websocket_connect("/chat?token=bob") as ws_bob:
        payload = {"to": CHARLIE_ID, "message": {"text": "hi charlie"}}
        ws_bob.send_json(payload)

        resp = ws_bob.receive_json()
        assert resp["status"] == "Not friends"
