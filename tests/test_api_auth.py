"""Tests for FastAPI auth and health routes — TDD."""
import json
import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def app_env(tmp_path, sample_config, monkeypatch):
    """Set up environment: write conf.json, set env vars, return TestClient."""
    conf_path = tmp_path / "conf.json"
    conf_path.write_text(json.dumps(sample_config))
    monkeypatch.setenv("CONF_PATH", str(conf_path))
    monkeypatch.setenv("DASHBOARD_PASSWORD", "secret123")
    monkeypatch.setenv("SESSION_SECRET", "test-session-secret")
    # Must import AFTER env vars are set so config loading picks them up
    import importlib
    import app.main as main_module
    importlib.reload(main_module)
    from fastapi.testclient import TestClient as TC
    client = TC(main_module.app)
    return client


@pytest.fixture
def app_no_password(tmp_path, sample_config, monkeypatch):
    """TestClient with no DASHBOARD_PASSWORD set (dev mode)."""
    conf_path = tmp_path / "conf.json"
    conf_path.write_text(json.dumps(sample_config))
    monkeypatch.setenv("CONF_PATH", str(conf_path))
    monkeypatch.delenv("DASHBOARD_PASSWORD", raising=False)
    monkeypatch.setenv("SESSION_SECRET", "test-session-secret")
    import importlib
    import app.main as main_module
    importlib.reload(main_module)
    from fastapi.testclient import TestClient as TC
    client = TC(main_module.app)
    return client


# ---------------------------------------------------------------------------
# TDD Cycle 1: Health endpoint
# ---------------------------------------------------------------------------

class TestHealth:
    def test_health_returns_200_ok(self, app_env):
        response = app_env.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# TDD Cycle 2: Login with correct password
# ---------------------------------------------------------------------------

class TestLogin:
    def test_login_correct_password_returns_200(self, app_env):
        response = app_env.post("/api/auth/login", json={"password": "secret123"})
        assert response.status_code == 200

    # ---------------------------------------------------------------------------
    # TDD Cycle 3: Login with wrong password
    # ---------------------------------------------------------------------------

    def test_login_wrong_password_returns_401(self, app_env):
        response = app_env.post("/api/auth/login", json={"password": "wrongpass"})
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# TDD Cycle 4: Auth check without login returns 401
# ---------------------------------------------------------------------------

class TestAuthCheck:
    def test_check_without_login_returns_401(self, app_env):
        response = app_env.get("/api/auth/check")
        assert response.status_code == 401

    # ---------------------------------------------------------------------------
    # TDD Cycle 5: Auth check after login returns 200
    # ---------------------------------------------------------------------------

    def test_check_after_login_returns_200(self, app_env):
        app_env.post("/api/auth/login", json={"password": "secret123"})
        response = app_env.get("/api/auth/check")
        assert response.status_code == 200

    # ---------------------------------------------------------------------------
    # TDD Cycle 6: Logout clears session
    # ---------------------------------------------------------------------------

    def test_logout_clears_session(self, app_env):
        app_env.post("/api/auth/login", json={"password": "secret123"})
        app_env.post("/api/auth/logout")
        response = app_env.get("/api/auth/check")
        assert response.status_code == 401

    # ---------------------------------------------------------------------------
    # TDD Cycle 7: Dev mode — no password set means all pass
    # ---------------------------------------------------------------------------

    def test_dev_mode_no_password_check_returns_200(self, app_no_password):
        response = app_no_password.get("/api/auth/check")
        assert response.status_code == 200
