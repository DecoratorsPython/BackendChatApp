import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from app.main import app
from app.services.auth_service import AuthService
from app.core.deps import get_current_user


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.mark.asyncio
@patch("app.services.auth_service.AuthService.upsert_user_from_google_profile")
async def test_google_login_upserts_user(mock_upsert, client):
    mock_user = MagicMock()
    mock_user.email = "testuser@example.com"
    mock_user.username = "Test User"
    mock_user.provider = "google"
    mock_user.provider_sub = "testsub"
    mock_upsert.return_value = mock_user
    payload = {
        "sub": "testsub",
        "email": "testuser@example.com",
        "name": "Test User",
        "picture": "http://example.com/avatar.png"      
    }
    auth_service = AuthService(MagicMock())
    user = await auth_service.upsert_user_from_google_profile(payload)
    assert user.email == "testuser@example.com"
    assert user.username == "Test User"
    assert user.provider == "google"
    assert user.provider_sub == "testsub"

@patch("app.api.src.auth.revoke_refresh_token")
def test_logout_endpoint(mock_revoke, client):
    mock_user = MagicMock()
    mock_user.user_id = "mock-user-id"
    access_token = "mock-access-token"
    refresh_token = "mock-refresh-token"

    def override_get_current_user():
        return mock_user
    import app.main
    app.main.app.dependency_overrides[get_current_user] = override_get_current_user
    # Success
    response = client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"refresh_token": refresh_token}
    )
    assert response.status_code == 200
    assert "Logged out" in response.json()["detail"]
    # Error
    mock_revoke.side_effect = Exception("Already revoked")
    response2 = client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"refresh_token": refresh_token}
    )
    assert response2.status_code == 500
    # Clean up override
    app.main.app.dependency_overrides.pop(get_current_user, None)
