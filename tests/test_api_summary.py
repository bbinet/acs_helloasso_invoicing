"""Tests for summary API routes -- TDD."""
import json
import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def summary_env(tmp_path, sample_helloasso_item, monkeypatch):
    """Set up environment with member JSON files and return TestClient."""
    form_slug = "adhesion-2024-2025"
    invoicing_dir = tmp_path / "invoicing" / form_slug
    invoicing_dir.mkdir(parents=True)

    # Write first member (has Football and Tennis options)
    item1 = sample_helloasso_item.copy()
    filepath1 = invoicing_dir / "jeanpierre_delafontaine_2024-09-15_12345.json"
    filepath1.write_text(json.dumps(item1))

    # Write second member (has Yoga option)
    item2 = {
        "id": 67890,
        "name": "Adhesion simple",
        "user": {"firstName": "Marie", "lastName": "Dupont"},
        "payer": {"email": "marie@example.com"},
        "order": {"date": "2024-09-16T14:00:00+02:00", "formName": "Adhesion ACS 2024-2025"},
        "customFields": [],
        "options": [{"name": "Yoga"}],
        "payments": [{"amount": 10000, "refundOperations": []}],
        "amount": 10000,
    }
    filepath2 = invoicing_dir / "marie_dupont_2024-09-16_67890.json"
    filepath2.write_text(json.dumps(item2))

    config = {
        "credentials": {"helloasso": {"id": "test-id", "secret": "test-secret"}},
        "conf": {
            "helloasso": {
                "api_url": "https://api.helloasso.com",
                "organization_name": "acs-test",
                "formType": "MemberShip",
                "formSlug": form_slug,
            },
            "sendemail": {"from": "test@example.com"},
        },
    }
    conf_path = tmp_path / "conf.json"
    conf_path.write_text(json.dumps(config))

    monkeypatch.setenv("CONF_PATH", str(conf_path))
    monkeypatch.delenv("DASHBOARD_PASSWORD", raising=False)
    monkeypatch.setenv("SESSION_SECRET", "test-session-secret")

    import importlib
    import app.main as main_module
    importlib.reload(main_module)
    client = TestClient(main_module.app)
    return client


# ---------------------------------------------------------------------------
# TDD Cycle 1: GET /api/summary returns activity breakdown
# ---------------------------------------------------------------------------

class TestGetSummary:
    def test_summary_returns_activity_breakdown(self, summary_env):
        client = summary_env
        resp = client.get("/api/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "activities" in data
        assert "total" in data
        # Should have Football, Tennis, Yoga activities
        activity_names = [a["name"] for a in data["activities"]]
        assert "Football" in activity_names
        assert "Tennis" in activity_names
        assert "Yoga" in activity_names

    # -----------------------------------------------------------------------
    # TDD Cycle 2: Summary total matches member count
    # -----------------------------------------------------------------------

    def test_summary_total_matches_member_count(self, summary_env):
        client = summary_env
        resp = client.get("/api/summary")
        data = resp.json()
        assert data["total"] == 2
