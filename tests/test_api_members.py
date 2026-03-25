"""Tests for members API routes — TDD."""
import csv
import io
import json
import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def members_env(tmp_path, sample_helloasso_item, monkeypatch):
    """Set up environment with member JSON files and return TestClient.

    Creates:
    - tmp_path/invoicing/adhesion-2024-2025/ with member JSON files
    - conf.json pointing to tmp_path as dir
    - No DASHBOARD_PASSWORD (dev mode) so auth is bypassed
    """
    # Create invoicing directory with member files
    form_slug = "adhesion-2024-2025"
    invoicing_dir = tmp_path / "invoicing" / form_slug
    invoicing_dir.mkdir(parents=True)

    # Write first member item
    item1 = sample_helloasso_item.copy()
    filepath1 = invoicing_dir / "jeanpierre_delafontaine_2024-09-15_12345.json"
    filepath1.write_text(json.dumps(item1))

    # Write second member item with different data
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

    # Write conf.json
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

    # Set env vars (dev mode — no password)
    monkeypatch.setenv("CONF_PATH", str(conf_path))
    monkeypatch.delenv("DASHBOARD_PASSWORD", raising=False)
    monkeypatch.setenv("SESSION_SECRET", "test-session-secret")

    # Reload app module with new config
    import importlib
    import app.main as main_module
    importlib.reload(main_module)
    client = TestClient(main_module.app)
    return client, invoicing_dir


# ---------------------------------------------------------------------------
# TDD Cycle 1: GET /api/members returns list of members
# ---------------------------------------------------------------------------

class TestListMembers:
    def test_get_members_returns_list(self, members_env):
        client, _ = members_env
        resp = client.get("/api/members")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 2

    # -----------------------------------------------------------------------
    # TDD Cycle 2: Members include status fields
    # -----------------------------------------------------------------------

    def test_members_include_status_fields(self, members_env):
        client, invoicing_dir = members_env
        # Create a .pdf file for member 1 to indicate invoice generated
        pdf_path = invoicing_dir / "jeanpierre_delafontaine_2024-09-15_12345.pdf"
        pdf_path.write_text("fake pdf")
        # Create a .mail.log file for member 1 to indicate email sent
        mail_path = invoicing_dir / "jeanpierre_delafontaine_2024-09-15_12345.mail.log"
        mail_path.write_text("sent")

        resp = client.get("/api/members")
        data = resp.json()
        # Find member with id 12345
        member1 = next(m for m in data if m["id"] == 12345)
        assert member1["invoice_generated"] is True
        assert member1["email_sent"] is True
        # Member 2 should have no status files
        member2 = next(m for m in data if m["id"] == 67890)
        assert member2["invoice_generated"] is False
        assert member2["email_sent"] is False

    # -----------------------------------------------------------------------
    # TDD Cycle 3: Filter by activity
    # -----------------------------------------------------------------------

    def test_filter_by_activity(self, members_env):
        client, _ = members_env
        resp = client.get("/api/members", params={"activity": "Football"})
        data = resp.json()
        # Only member 1 has Football
        assert len(data) == 1
        assert data[0]["id"] == 12345

    # -----------------------------------------------------------------------
    # TDD Cycle 4: Filter refunded orders
    # -----------------------------------------------------------------------

    def test_refund_filtered(self, members_env):
        client, invoicing_dir = members_env
        # Add a refunded member
        item_refunded = {
            "id": 99999,
            "name": "Adhesion simple",
            "user": {"firstName": "Refund", "lastName": "Person"},
            "payer": {"email": "refund@example.com"},
            "order": {"date": "2024-09-17T10:00:00+02:00", "formName": "Adhesion ACS 2024-2025"},
            "customFields": [],
            "options": [{"name": "Tennis"}],
            "payments": [{"amount": 5000, "refundOperations": [{"id": 1}]}],
            "amount": 5000,
        }
        filepath = invoicing_dir / "refund_person_2024-09-17_99999.json"
        filepath.write_text(json.dumps(item_refunded))

        # Without filter: should include refunded member
        resp = client.get("/api/members")
        assert len(resp.json()) == 3

        # With refund filter: should exclude refunded member
        resp = client.get("/api/members", params={"refund_filtered": "true"})
        data = resp.json()
        assert len(data) == 2
        assert all(m["id"] != 99999 for m in data)


# ---------------------------------------------------------------------------
# TDD Cycle 5-6: GET /api/members/{id}
# ---------------------------------------------------------------------------

class TestGetMember:
    def test_get_member_by_id(self, members_env):
        client, _ = members_env
        resp = client.get("/api/members/12345")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == 12345
        assert data["firstname"] == "Jean-Pierre"

    def test_get_member_not_found(self, members_env):
        client, _ = members_env
        resp = client.get("/api/members/00000")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# TDD Cycle 7: CSV export
# ---------------------------------------------------------------------------

class TestExportCSV:
    def test_export_csv(self, members_env):
        client, _ = members_env
        resp = client.get("/api/members/export/csv")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers.get("content-type", "")

        reader = csv.reader(io.StringIO(resp.text))
        rows = list(reader)
        header = rows[0]
        assert header == ["Num", "HelloAssoID", "OrderDate", "FirstName", "LastName",
                          "Company", "EmileAllais", "Activities"]
        # 2 data rows
        assert len(rows) == 3
