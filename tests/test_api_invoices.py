"""Tests for invoice API routes -- TDD."""
import json
import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def invoices_env(tmp_path, sample_helloasso_item, monkeypatch):
    """Set up environment with member JSON files and return TestClient + paths.

    Creates:
    - tmp_path/invoicing/adhesion-2024-2025/ with member JSON files
    - conf.json pointing to tmp_path as dir
    - No DASHBOARD_PASSWORD (dev mode) so auth is bypassed
    """
    form_slug = "adhesion-2024-2025"
    invoicing_dir = tmp_path / "invoicing" / form_slug
    invoicing_dir.mkdir(parents=True)

    # Write member item (add amount to options for template rendering)
    item1 = sample_helloasso_item.copy()
    item1["options"] = [
        {"name": "Football", "amount": 0},
        {"name": "Tennis", "amount": 0},
        {"name": "N'oubliez pas de venir", "amount": 0},
    ]
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
# TDD Cycle 1: POST /api/invoices/{id}/generate returns success
# ---------------------------------------------------------------------------

class TestGenerateInvoice:
    def test_generate_returns_success(self, invoices_env, monkeypatch):
        client, invoicing_dir = invoices_env
        # Mock run_make_pdf at the usage site (the import in the routes module)
        import unittest.mock as mock
        fake_result = mock.MagicMock()
        fake_result.returncode = 0
        monkeypatch.setattr(
            "app.routes.invoices.run_make_pdf",
            mock.MagicMock(return_value=fake_result),
        )
        resp = client.post("/api/invoices/12345/generate")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "generated"
        assert data["member_id"] == 12345

    # -----------------------------------------------------------------------
    # TDD Cycle 2: generate returns 404 for unknown member
    # -----------------------------------------------------------------------

    def test_generate_returns_404_for_unknown_member(self, invoices_env):
        client, _ = invoices_env
        resp = client.post("/api/invoices/99999/generate")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# TDD Cycle 3: GET /api/invoices/{id}/download serves PDF
# ---------------------------------------------------------------------------

class TestDownloadInvoice:
    def test_download_serves_pdf(self, invoices_env):
        client, invoicing_dir = invoices_env
        # Create a fake PDF file
        pdf_path = invoicing_dir / "jeanpierre_delafontaine_2024-09-15_12345.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 fake content")

        resp = client.get("/api/invoices/12345/download")
        assert resp.status_code == 200
        assert "application/pdf" in resp.headers.get("content-type", "")
        assert b"%PDF-1.4" in resp.content

    # -----------------------------------------------------------------------
    # TDD Cycle 4: download returns 404 when PDF doesn't exist
    # -----------------------------------------------------------------------

    def test_download_returns_404_when_no_pdf(self, invoices_env):
        client, _ = invoices_env
        resp = client.get("/api/invoices/12345/download")
        assert resp.status_code == 404

    def test_download_returns_404_for_unknown_member(self, invoices_env):
        client, _ = invoices_env
        resp = client.get("/api/invoices/99999/download")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# TDD Cycle 5: GET /api/invoices/{id}/preview returns HTML
# ---------------------------------------------------------------------------

class TestPreviewInvoice:
    def test_preview_returns_html(self, invoices_env):
        client, invoicing_dir = invoices_env
        # Copy the real template to the expected location (parent of invoicing_dir = invoicing/)
        template_dir = invoicing_dir.parent  # tmp_path/invoicing/
        import shutil
        real_template = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "invoicing", "template.jinja2",
        )
        shutil.copy(real_template, str(template_dir / "template.jinja2"))

        resp = client.get("/api/invoices/12345/preview")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")
        assert "Facture" in resp.text
        assert "Jean-Pierre" in resp.text


# ---------------------------------------------------------------------------
# TDD Cycle 6: POST /api/invoices/batch returns job_id
# ---------------------------------------------------------------------------

class TestBatchGenerate:
    def test_batch_returns_job_id(self, invoices_env, monkeypatch):
        client, invoicing_dir = invoices_env
        # No PDFs exist, so both members need generation
        import unittest.mock as mock
        fake_result = mock.MagicMock()
        fake_result.returncode = 0
        monkeypatch.setattr(
            "app.routes.invoices.run_make_pdf",
            mock.MagicMock(return_value=fake_result),
        )
        resp = client.post("/api/invoices/batch")
        assert resp.status_code == 200
        data = resp.json()
        assert "job_id" in data
        assert data["total"] == 2

    # -----------------------------------------------------------------------
    # TDD Cycle 7: GET /api/invoices/batch/{job_id}/status returns progress
    # -----------------------------------------------------------------------

    def test_batch_status_returns_progress(self, invoices_env, monkeypatch):
        client, invoicing_dir = invoices_env
        import unittest.mock as mock
        fake_result = mock.MagicMock()
        fake_result.returncode = 0
        monkeypatch.setattr(
            "lib.invoicing.run_make_pdf",
            mock.MagicMock(return_value=fake_result),
        )

        # Start batch
        resp = client.post("/api/invoices/batch")
        job_id = resp.json()["job_id"]

        # Check status
        resp = client.get(f"/api/invoices/batch/{job_id}/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "completed" in data
        assert "status" in data

    def test_batch_status_404_for_unknown_job(self, invoices_env):
        client, _ = invoices_env
        resp = client.get("/api/invoices/batch/nonexistent-id/status")
        assert resp.status_code == 404
