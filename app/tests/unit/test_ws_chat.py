import os
import sys

import pytest

# add project root to sys.path 
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.ws.deps import are_friends
from app.ws.manager import ConnectionManager


ALICE_ID = "11111111-1111-1111-1111-111111111111"
BOB_ID = "22222222-2222-2222-2222-222222222222"
CHARLIE_ID = "33333333-3333-3333-3333-333333333333"



def test_are_friends_true_pairs():
    assert are_friends(ALICE_ID, BOB_ID) is True
    assert are_friends(BOB_ID, ALICE_ID) is True
    assert are_friends(ALICE_ID, CHARLIE_ID) is True
    assert are_friends(CHARLIE_ID, ALICE_ID) is True


def test_are_friends_false_pairs():
    assert are_friends(BOB_ID, CHARLIE_ID) is False
    assert are_friends(CHARLIE_ID, BOB_ID) is False
    assert are_friends(ALICE_ID, "99999999-9999-9999-9999-999999999999") is False


#  Fake WebSockets for ConnectionManager 


class FakeWebSocket:
    """Minimal fake WebSocket used to test ConnectionManager without real network."""

    def __init__(self) -> None:
        self.accepted = False
        self.closed = False
        self.scope: dict = {}
        self.sent_messages: list[dict] = []

    async def accept(self):
        self.accepted = True

    async def close(self):
        self.closed = True

    async def send_json(self, message: dict):
        self.sent_messages.append(message)


class FakeWebSocketFailSend(FakeWebSocket):
    """Fake WebSocket that raises on send_json, to test error handling."""

    async def send_json(self, message: dict):
        raise RuntimeError("Simulated send error")


#  ConnectionManager unit tests 


@pytest.mark.asyncio
async def test_connection_manager_connect_and_disconnect():
    manager = ConnectionManager()
    ws = FakeWebSocket()

    assert ws not in manager._connections

    await manager.connect(ALICE_ID, ws)
    assert ws.accepted is True
    assert ws in manager._connections
    assert ws.scope.get("user_id") == ALICE_ID

    await manager.disconnect(ws)
    assert ws.closed is True
    assert ws not in manager._connections


@pytest.mark.asyncio
async def test_send_personal_message_to_connected_user():
    manager = ConnectionManager()
    ws = FakeWebSocket()

    await manager.connect(BOB_ID, ws)

    message = {"text": "hello bob"}
    await manager.send_personal_message(message, BOB_ID)

    assert ws.sent_messages == [message]


@pytest.mark.asyncio
async def test_send_personal_message_to_not_connected_user_does_nothing():
    manager = ConnectionManager()
    ws = FakeWebSocket()

    await manager.connect(ALICE_ID, ws)

    message = {"text": "hello bob"}
    await manager.send_personal_message(message, BOB_ID)

    assert ws.sent_messages == []


@pytest.mark.asyncio
async def test_send_personal_message_removes_connection_on_error():
    manager = ConnectionManager()
    ws = FakeWebSocketFailSend()

    await manager.connect(ALICE_ID, ws)
    assert ws in manager._connections

    message = {"text": "test"}
    await manager.send_personal_message(message, ALICE_ID)

    assert ws not in manager._connections
    assert ws.closed is True
