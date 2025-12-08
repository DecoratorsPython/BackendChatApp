import jwt
import time
import pytest
import datetime
from unittest.mock import MagicMock, patch
from app.core import security
from app.auth import tokens
from app.core.exceptions import InvalidTokenError, ExpiredTokenError
from app.auth.tokens import InvalidRefreshTokenError, ExpiredRefreshTokenError, RevokedRefreshTokenError


def test_create_and_decode_access_token():
    user_id = "test-user-id"
    token = security.create_access_token(user_id)
    payload = security.decode_access_token(token)
    assert payload["sub"] == user_id
    assert "exp" in payload
    assert "iat" in payload


def test_verify_access_token_valid():
    user_id = "test-user-id"
    token = security.create_access_token(user_id)
    data = security.verify_access_token(token)
    assert data.sub == user_id


def test_verify_access_token_invalid():
    with pytest.raises(InvalidTokenError):
        security.verify_access_token("invalid.token.value")


def test_verify_access_token_expired(monkeypatch):
    user_id = "test-user-id"
    now = int(time.time())
    payload = {"sub": user_id, "iat": now - 100, "exp": now - 1}
    token = jwt.encode(payload, security.settings.jwt_secret, algorithm=security.settings.jwt_algorithm)
    with pytest.raises(ExpiredTokenError):
        security.verify_access_token(token)


@patch("app.auth.tokens.RefreshToken")
def test_verify_refresh_token_valid(mock_refresh_token):
    db = MagicMock()
    mock_rt = MagicMock()
    mock_rt.token = "token123"
    mock_rt.revoked_at = None
    mock_rt.expires_at = datetime.datetime.utcnow() + datetime.timedelta(days=1)
    mock_rt.token_id = "tid"
    mock_rt.user_id = "uid"
    db.query().filter().one_or_none.return_value = mock_rt
    data = tokens.verify_refresh_token(db, "token123")
    assert data.token_id == "tid"
    assert data.user_id == "uid"
    assert not data.revoked

@patch("app.auth.tokens.RefreshToken")
def test_verify_refresh_token_invalid(mock_refresh_token):
    db = MagicMock()
    db.query().filter().one_or_none.return_value = None
    with pytest.raises(InvalidRefreshTokenError):
        tokens.verify_refresh_token(db, "badtoken")

@patch("app.auth.tokens.RefreshToken")
def test_verify_refresh_token_revoked(mock_refresh_token):
    db = MagicMock()
    mock_rt = MagicMock()
    mock_rt.revoked_at = True
    db.query().filter().one_or_none.return_value = mock_rt
    with pytest.raises(RevokedRefreshTokenError):
        tokens.verify_refresh_token(db, "token123")

@patch("app.auth.tokens.RefreshToken")
def test_verify_refresh_token_expired(mock_refresh_token):
    db = MagicMock()
    mock_rt = MagicMock()
    mock_rt.revoked_at = None
    mock_rt.expires_at = datetime.datetime.utcnow() - datetime.timedelta(days=1)
    db.query().filter().one_or_none.return_value = mock_rt
    with pytest.raises(ExpiredRefreshTokenError):
        tokens.verify_refresh_token(db, "token123")
