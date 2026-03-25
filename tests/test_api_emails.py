"""Tests for email API routes -- TDD."""
import json
import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def emails_env(tmp_path, sample_helloasso_item, monkeypatch):
    """Set up environment with member JSON files and return TestClient + paths.

    Creates:
    - tmp_path/invoicing/adhesion-2024-2025/ with member JSON files
    - conf.json pointing to tmp_path as dir
    - No DASHBOARD_PASSWORD (dev mode) so auth is bypassed
    """
    form_slug = "adhesion-2024-2025"
    invoicing_dir = tmp_path / "invoicing" / form_slug
    invoicing_dir.mkdir(parents=True)

    # Write member item
    item1 = sample_helloasso_item.copy()
    filepath1 = invoicing_dir / "jeanpierre_delafontaine_2024-09-15_12345.json"
    filepath1.write_text(json.dumps(item1))

    # Write second member
    item2 = {
        "id": 67890,
        "name": "Adhesion simple",
        "user": {"firstName": "Marie", "lastName": "Dupont"},
        "payer": {"email": "marie@example.com"},
        "order": {"date": "2024-09-16T14:00:00+02:00", "formName": "Adhesion ACS 2024-2025"},
        "customFields": [],
        "options": [{"name": "Yoga", "amount": 0}],
        "payments": [{"amount": 10000, "refundOperations": []}],
        "amount": 10000,
    }
    filepath2 = invoicing_dir / "marie_dupont_2024-09-16_67890.json"
    filepath2.write_text(json.dumps(item2))

    # conf.json
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
    return client, invoicing_dir


# ---------------------------------------------------------------------------
# TDD Cycle 1: POST /api/emails/{id}/send returns success
# ---------------------------------------------------------------------------

class TestSendEmail:
    def test_send_returns_success(self, emails_env, monkeypatch):
        client, invoicing_dir = emails_env
        # Must have a PDF file to send email
        pdf_path = invoicing_dir / "jeanpierre_delafontaine_2024-09-15_12345.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 fake content")

        # Mock run_make_email at the usage site
        import unittest.mock as mock
        fake_result = mock.MagicMock()
        fake_result.returncode = 0
        monkeypatch.setattr(
            "app.routes.emails.run_make_email",
            mock.MagicMock(return_value=fake_result),
        )
        resp = client.post("/api/emails/12345/send")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "sent"
        assert data["member_id"] == 12345

    # -----------------------------------------------------------------------
    # TDD Cycle 2: send returns 404 for unknown member
    # -----------------------------------------------------------------------

    def test_send_returns_404_for_unknown_member(self, emails_env):
        client, _ = emails_env
        resp = client.post("/api/emails/99999/send")
        assert resp.status_code == 404

    # -----------------------------------------------------------------------
    # TDD Cycle 3: send returns 400 when PDF doesn't exist
    # -----------------------------------------------------------------------

    def test_send_returns_400_when_no_pdf(self, emails_env):
        client, _ = emails_env
        # Member exists but PDF hasn't been generated
        resp = client.post("/api/emails/12345/send")
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# TDD Cycle 4: POST /api/emails/batch returns job_id
# ---------------------------------------------------------------------------

class TestBatchEmail:
    def test_batch_returns_job_id(self, emails_env, monkeypatch):
        client, invoicing_dir = emails_env
        # Create PDFs for both members (eligible for email)
        pdf1 = invoicing_dir / "jeanpierre_delafontaine_2024-09-15_12345.pdf"
        pdf1.write_bytes(b"%PDF-1.4 fake")
        pdf2 = invoicing_dir / "marie_dupont_2024-09-16_67890.pdf"
        pdf2.write_bytes(b"%PDF-1.4 fake")

        import unittest.mock as mock
        fake_result = mock.MagicMock()
        fake_result.returncode = 0
        monkeypatch.setattr(
            "app.routes.emails.run_make_email",
            mock.MagicMock(return_value=fake_result),
        )
        resp = client.post("/api/emails/batch")
        assert resp.status_code == 200
        data = resp.json()
        assert "job_id" in data
        assert data["total"] == 2

    def test_batch_excludes_already_emailed(self, emails_env, monkeypatch):
        client, invoicing_dir = emails_env
        # Create PDFs for both members
        pdf1 = invoicing_dir / "jeanpierre_delafontaine_2024-09-15_12345.pdf"
        pdf1.write_bytes(b"%PDF-1.4 fake")
        pdf2 = invoicing_dir / "marie_dupont_2024-09-16_67890.pdf"
        pdf2.write_bytes(b"%PDF-1.4 fake")
        # Mark member 1 as already emailed
        mail_log = invoicing_dir / "jeanpierre_delafontaine_2024-09-15_12345.mail.log"
        mail_log.write_text("sent")

        import unittest.mock as mock
        fake_result = mock.MagicMock()
        fake_result.returncode = 0
        monkeypatch.setattr(
            "app.routes.emails.run_make_email",
            mock.MagicMock(return_value=fake_result),
        )
        resp = client.post("/api/emails/batch")
        data = resp.json()
        assert data["total"] == 1  # Only member 2

    # -----------------------------------------------------------------------
    # TDD Cycle 5: GET /api/emails/batch/{job_id}/status returns progress
    # -----------------------------------------------------------------------

    def test_batch_status_returns_progress(self, emails_env, monkeypatch):
        client, invoicing_dir = emails_env
        # Create PDFs
        pdf1 = invoicing_dir / "jeanpierre_delafontaine_2024-09-15_12345.pdf"
        pdf1.write_bytes(b"%PDF-1.4 fake")

        import unittest.mock as mock
        fake_result = mock.MagicMock()
        fake_result.returncode = 0
        monkeypatch.setattr(
            "app.routes.emails.run_make_email",
            mock.MagicMock(return_value=fake_result),
        )

        # Start batch
        resp = client.post("/api/emails/batch")
        job_id = resp.json()["job_id"]

        # Check status
        resp = client.get(f"/api/emails/batch/{job_id}/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "completed" in data
        assert "status" in data

    def test_batch_status_404_for_unknown_job(self, emails_env):
        client, _ = emails_env
        resp = client.get("/api/emails/batch/nonexistent-id/status")
        assert resp.status_code == 404
