"""Tests for HelloAssoClient — token refresh and request wrapper."""
from unittest.mock import MagicMock, patch

import pytest

from lib.helloasso_client import HelloAssoClient


@pytest.fixture
def mock_auth_response():
    """Mock response for OAuth2 token endpoint."""
    resp = MagicMock()
    resp.json.return_value = {
        "access_token": "access-token-123",
        "refresh_token": "refresh-token-456",
        "token_type": "bearer",
        "expires_in": 3600,
    }
    resp.status_code = 200
    return resp


@pytest.fixture
def client(sample_config, mock_auth_response):
    """HelloAssoClient with mocked Authenticate call."""
    with patch("lib.helloasso_client.requests.post", return_value=mock_auth_response):
        return HelloAssoClient(sample_config)


# ---------------------------------------------------------------------------
# TDD Cycle 1: Authenticate stores both access_token and refresh_token
# ---------------------------------------------------------------------------

class TestAuthenticate:
    def test_stores_access_token(self, sample_config, mock_auth_response):
        with patch("lib.helloasso_client.requests.post", return_value=mock_auth_response):
            c = HelloAssoClient(sample_config)
        assert c.access_token == "access-token-123"

    def test_stores_refresh_token(self, sample_config, mock_auth_response):
        with patch("lib.helloasso_client.requests.post", return_value=mock_auth_response):
            c = HelloAssoClient(sample_config)
        assert c.refresh_token == "refresh-token-456"

    def test_sets_bearer_header(self, sample_config, mock_auth_response):
        with patch("lib.helloasso_client.requests.post", return_value=mock_auth_response):
            c = HelloAssoClient(sample_config)
        assert c.headers["Authorization"] == "Bearer access-token-123"


# ---------------------------------------------------------------------------
# TDD Cycle 2: _request returns response on 200
# ---------------------------------------------------------------------------

class TestRequestSuccess:
    def test_get_200_returns_response(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch("lib.helloasso_client.requests.get", return_value=mock_resp) as mock_get:
            result = client._request("get", "https://api.example.com/data", params={"k": "v"})

        assert result is mock_resp
        mock_get.assert_called_once_with(
            "https://api.example.com/data",
            params={"k": "v"},
            headers=client.headers,
        )


# ---------------------------------------------------------------------------
# TDD Cycle 3: _request refreshes token on 401, retries, succeeds
# ---------------------------------------------------------------------------

class TestRequestRefresh:
    def test_refreshes_on_401_and_retries(self, client):
        """On 401, _request should call RefreshToken then retry the request."""
        first_resp = MagicMock()
        first_resp.status_code = 401

        success_resp = MagicMock()
        success_resp.status_code = 200

        refresh_post = MagicMock()
        refresh_post.return_value.json.return_value = {
            "access_token": "new-access-token",
            "refresh_token": "new-refresh-token",
        }
        refresh_post.return_value.status_code = 200

        get_responses = [first_resp, success_resp]

        with patch("lib.helloasso_client.requests.get", side_effect=get_responses):
            with patch("lib.helloasso_client.requests.post", return_value=refresh_post.return_value):
                result = client._request("get", "https://api.example.com/data")

        assert result is success_resp
        assert client.access_token == "new-access-token"
        assert client.refresh_token == "new-refresh-token"

    def test_updates_header_after_refresh(self, client):
        """After token refresh, Authorization header should use new token."""
        first_resp = MagicMock()
        first_resp.status_code = 401
        success_resp = MagicMock()
        success_resp.status_code = 200

        refresh_resp = MagicMock()
        refresh_resp.json.return_value = {
            "access_token": "refreshed-token",
            "refresh_token": "refreshed-refresh",
        }
        refresh_resp.status_code = 200

        with patch("lib.helloasso_client.requests.get", side_effect=[first_resp, success_resp]):
            with patch("lib.helloasso_client.requests.post", return_value=refresh_resp):
                client._request("get", "https://api.example.com/data")

        assert client.headers["Authorization"] == "Bearer refreshed-token"


# ---------------------------------------------------------------------------
# TDD Cycle 4: _request falls back to full re-auth if refresh fails
# ---------------------------------------------------------------------------

class TestRequestFallbackAuth:
    def test_falls_back_to_full_auth_when_refresh_fails(self, client):
        """If RefreshToken fails (401), fall back to Authenticate() then retry."""
        first_resp = MagicMock()
        first_resp.status_code = 401

        success_resp = MagicMock()
        success_resp.status_code = 200

        # POST calls: first = refresh (fails), second = full auth (succeeds)
        refresh_fail_resp = MagicMock()
        refresh_fail_resp.status_code = 401
        refresh_fail_resp.json.return_value = {"error": "invalid_grant"}

        full_auth_resp = MagicMock()
        full_auth_resp.status_code = 200
        full_auth_resp.json.return_value = {
            "access_token": "reauthed-token",
            "refresh_token": "reauthed-refresh",
        }

        with patch("lib.helloasso_client.requests.get", side_effect=[first_resp, success_resp]):
            with patch(
                "lib.helloasso_client.requests.post",
                side_effect=[refresh_fail_resp, full_auth_resp],
            ):
                result = client._request("get", "https://api.example.com/data")

        assert result is success_resp
        assert client.access_token == "reauthed-token"
