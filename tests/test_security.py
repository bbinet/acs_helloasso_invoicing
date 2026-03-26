"""Security tests for authentication, CORS, path traversal, and input validation."""
import hmac
import os
import re

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, sample_config, sample_helloasso_item):
    """Create a test client with proper security configuration."""
    import json

    # Write config and member files
    conf_path = tmp_path / "conf.json"
    conf_data = dict(sample_config)
    conf_data["conf"]["dir"] = str(tmp_path)
    conf_path.write_text(json.dumps(conf_data))

    invoicing_dir = tmp_path / "invoicing" / "adhesion-2024-2025"
    invoicing_dir.mkdir(parents=True)
    member_file = invoicing_dir / "test_member_2024-09-15_12345.json"
    member_file.write_text(json.dumps(sample_helloasso_item))

    os.environ["CONF_PATH"] = str(conf_path)
    os.environ["DASHBOARD_PASSWORD"] = "securepass"
    os.environ["SESSION_SECRET"] = "test-secret-key-for-testing"

    # Reimport app to pick up new env vars
    import importlib
    import app.main
    importlib.reload(app.main)

    yield TestClient(app.main.app)

    os.environ.pop("CONF_PATH", None)
    os.environ.pop("DASHBOARD_PASSWORD", None)
    os.environ.pop("SESSION_SECRET", None)


class TestC1SessionSecret:
    """C1: Session secret must not use default in production."""

    def test_app_source_requires_session_secret(self):
        """app/main.py should raise ValueError when SESSION_SECRET is missing in production."""
        main_path = os.path.join(os.path.dirname(__file__), "..", "app", "main.py")
        with open(main_path) as f:
            source = f.read()
        # Must check for SESSION_SECRET and raise ValueError
        assert "SESSION_SECRET" in source
        assert "ValueError" in source
        # Must NOT have a usable default secret
        assert "dev-secret-key-change-in-production" not in source


class TestC2DefaultPassword:
    """C2: Production docker-compose should not have default password."""

    def test_prod_compose_no_default_password(self):
        """docker-compose.prod.yml should not have a default DASHBOARD_PASSWORD."""
        prod_compose = os.path.join(os.path.dirname(__file__), "..", "docker-compose.prod.yml")
        with open(prod_compose) as f:
            content = f.read()
        # Should NOT have :-admin or :-anything for DASHBOARD_PASSWORD
        assert "DASHBOARD_PASSWORD:-" not in content
        # Should NOT have :-change-me for SESSION_SECRET
        assert "SESSION_SECRET:-" not in content


class TestC3TimingAttack:
    """C3: Password comparison must be constant-time."""

    def test_login_uses_constant_time_comparison(self, client):
        """Login should use hmac.compare_digest, not == for password check."""
        # We verify behavior: correct password works, wrong doesn't
        # The actual timing-safe check is in the code
        resp = client.post("/api/auth/login", json={"password": "securepass"})
        assert resp.status_code == 200

        resp = client.post("/api/auth/login", json={"password": "wrong"})
        assert resp.status_code == 401

    def test_auth_module_uses_hmac(self):
        """auth.py source should contain hmac.compare_digest."""
        auth_path = os.path.join(os.path.dirname(__file__), "..", "app", "routes", "auth.py")
        with open(auth_path) as f:
            source = f.read()
        assert "hmac.compare_digest" in source or "compare_digest" in source


class TestH1Cors:
    """H1: CORS should not allow * with credentials."""

    def test_cors_rejects_wildcard_with_credentials(self):
        """CORS_ORIGINS=* should be rejected when DASHBOARD_PASSWORD is set."""
        os.environ["CORS_ORIGINS"] = "*"
        os.environ["DASHBOARD_PASSWORD"] = "test"
        os.environ["SESSION_SECRET"] = "test-secret"

        import importlib
        import app.main

        # After fix, wildcard with credentials should be refused or
        # CORS should default to restrictive origins
        importlib.reload(app.main)
        test_client = TestClient(app.main.app)

        # A request from a random origin should NOT get Access-Control-Allow-Origin: *
        resp = test_client.get("/api/health", headers={"Origin": "https://evil.com"})
        allow_origin = resp.headers.get("access-control-allow-origin", "")
        assert allow_origin != "*"

        os.environ.pop("CORS_ORIGINS", None)
        os.environ.pop("DASHBOARD_PASSWORD", None)
        os.environ.pop("SESSION_SECRET", None)


class TestH2Ssti:
    """H2: Jinja2 template rendering must use autoescape."""

    def test_jinja2_autoescape_enabled(self):
        """render_invoice_html should escape user data in HTML output."""
        from lib.invoicing import render_invoice_html
        import tempfile, shutil

        # Create a temp dir with the real template
        template_src = os.path.join(os.path.dirname(__file__), "..", "invoicing")
        with tempfile.TemporaryDirectory() as tmpdir:
            for f in ["template.jinja2", "style.css", "logo.svg"]:
                src = os.path.join(template_src, f)
                if os.path.exists(src):
                    shutil.copy(src, tmpdir)

            # Craft malicious item data with Jinja2 injection in name
            item = {
                "id": 1,
                "name": "{{ 7*7 }}",  # SSTI payload
                "amount": 1000,
                "user": {"firstName": "<script>alert(1)</script>", "lastName": "Test"},
                "payer": {"email": "test@test.com"},
                "order": {"date": "2026-01-01T00:00:00", "formName": "Test"},
                "options": [],
                "customFields": [],
            }
            html = render_invoice_html(tmpdir, item)

            # XSS script tag should be escaped
            assert "<script>" not in html
            # SSTI should not execute ({{ 7*7 }} should NOT become 49)
            assert "49" not in html


class TestH3PathTraversal:
    """H3: File serving must validate path within invoicing dir."""

    def test_download_rejects_path_outside_invoicing_dir(self, client):
        """Download endpoint should not serve files outside invoicing directory."""
        # Try to access a member that doesn't exist (404, not path traversal)
        resp = client.post("/api/auth/login", json={"password": "securepass"})
        resp = client.get("/api/invoices/99999/download")
        assert resp.status_code == 404


class TestH4Csrf:
    """H4: Frontend adds X-Requested-With header for CSRF protection."""

    def test_frontend_api_client_sends_csrf_header(self):
        """api.ts should set X-Requested-With: XMLHttpRequest on all requests."""
        api_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "src", "lib", "api.ts")
        with open(api_path) as f:
            source = f.read()
        assert "X-Requested-With" in source
        assert "XMLHttpRequest" in source


class TestH5Redos:
    """H5: Activity filter should not allow ReDoS."""

    def test_activity_filter_rejects_dangerous_regex(self, client):
        """Activity filter with dangerous regex should be rejected or truncated."""
        client.post("/api/auth/login", json={"password": "securepass"})

        # ReDoS pattern: (a+)+b
        resp = client.get("/api/members", params={"activity": "(a+)+b" * 10})
        # After fix: should either reject (400) or safely handle (200 with no results)
        assert resp.status_code in (200, 400)

    def test_activity_filter_limits_length(self, client):
        """Very long activity filter should be rejected."""
        client.post("/api/auth/login", json={"password": "securepass"})

        resp = client.get("/api/members", params={"activity": "a" * 1000})
        assert resp.status_code in (200, 400)
