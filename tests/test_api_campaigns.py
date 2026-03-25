"""Tests for campaigns API routes -- TDD."""
import json
import os
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def campaigns_env(tmp_path, sample_config, monkeypatch):
    """Set up environment with config and return TestClient + paths."""
    form_slug = "adhesion-2024-2025"
    invoicing_dir = tmp_path / "invoicing" / form_slug
    invoicing_dir.mkdir(parents=True)

    conf_path = tmp_path / "conf.json"
    conf_path.write_text(json.dumps(sample_config))

    monkeypatch.setenv("CONF_PATH", str(conf_path))
    monkeypatch.delenv("DASHBOARD_PASSWORD", raising=False)
    monkeypatch.setenv("SESSION_SECRET", "test-session-secret")

    import importlib
    import app.main as main_module
    importlib.reload(main_module)
    client = TestClient(main_module.app)
    return client, invoicing_dir, tmp_path


# ---------------------------------------------------------------------------
# TDD Cycle 1: GET /api/campaigns returns config info
# ---------------------------------------------------------------------------

class TestGetCampaigns:
    def test_get_campaigns_returns_config_info(self, campaigns_env):
        client, _, _ = campaigns_env
        resp = client.get("/api/campaigns")
        assert resp.status_code == 200
        data = resp.json()
        assert data["formSlug"] == "adhesion-2024-2025"
        assert data["formType"] == "MemberShip"
        assert data["organizationName"] == "acs-test"


# ---------------------------------------------------------------------------
# TDD Cycle 2: POST /api/campaigns/refresh creates JSON files
# ---------------------------------------------------------------------------

class TestRefreshCampaign:
    def test_refresh_creates_json_files(self, campaigns_env, sample_helloasso_item):
        client, invoicing_dir, _ = campaigns_env

        mock_items = [sample_helloasso_item]

        with patch("app.routes.campaigns.HelloAssoClient") as MockClient:
            instance = MagicMock()
            instance.GetData.return_value = iter(mock_items)
            MockClient.return_value = instance

            resp = client.post("/api/campaigns/refresh")

        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert data["formSlug"] == "adhesion-2024-2025"

        # Check that JSON file was created in invoicing dir
        json_files = list(invoicing_dir.glob("*.json"))
        assert len(json_files) == 1
