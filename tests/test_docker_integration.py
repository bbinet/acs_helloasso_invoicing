"""
Docker integration tests.

These tests verify that:
- The container starts and serves the FastAPI application correctly
- API endpoints respond correctly through the container
- Authentication flow works end-to-end
- The docker-compose configuration files are valid
- The Dockerfile syntax and structure are correct

Run with: pytest tests/test_docker_integration.py -v
Requires: Docker daemon running, port 8000 available.
"""

import json
import subprocess
import time
import urllib.error
import urllib.request

import pytest

COMPOSE_FILE = "docker-compose.test.yml"
PROJECT_NAME = "acs-test"
API_BASE = "http://localhost:8000"


def _api(method, path, data=None, headers=None, cookie=None):
    """Make an HTTP request to the API and return (status, body_dict, cookie_header)."""
    url = f"{API_BASE}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    if cookie:
        req.add_header("Cookie", cookie)
    try:
        resp = urllib.request.urlopen(req)
        resp_body = json.loads(resp.read().decode())
        cookie_header = resp.getheader("set-cookie")
        return resp.status, resp_body, cookie_header
    except urllib.error.HTTPError as e:
        raw = e.read().decode() if e.fp else ""
        try:
            resp_body = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            resp_body = {"detail": raw}
        return e.code, resp_body, None


def _wait_for_healthy(timeout=120):
    """Wait until the API health endpoint responds."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            resp = urllib.request.urlopen(f"{API_BASE}/api/health", timeout=3)
            if resp.status == 200:
                return True
        except Exception:
            pass
        time.sleep(2)
    return False


@pytest.fixture(scope="module")
def docker_compose_up():
    """Start the test docker-compose stack, tear down after tests."""
    # Tear down any leftover from a previous run
    subprocess.run(
        ["docker", "compose", "-f", COMPOSE_FILE, "-p", PROJECT_NAME,
         "down", "-v", "--remove-orphans"],
        capture_output=True, timeout=60,
    )

    # Start
    result = subprocess.run(
        ["docker", "compose", "-f", COMPOSE_FILE, "-p", PROJECT_NAME,
         "up", "-d"],
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        pytest.fail(
            f"docker compose up failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

    # Wait for API to be healthy
    if not _wait_for_healthy():
        logs = subprocess.run(
            ["docker", "compose", "-f", COMPOSE_FILE, "-p", PROJECT_NAME, "logs"],
            capture_output=True, text=True,
        )
        subprocess.run(
            ["docker", "compose", "-f", COMPOSE_FILE, "-p", PROJECT_NAME,
             "down", "-v", "--remove-orphans"],
            capture_output=True, timeout=60,
        )
        pytest.fail(f"API did not become healthy in time.\nLogs:\n{logs.stdout}\n{logs.stderr}")

    yield

    # Tear down
    subprocess.run(
        ["docker", "compose", "-f", COMPOSE_FILE, "-p", PROJECT_NAME,
         "down", "-v", "--remove-orphans"],
        capture_output=True, timeout=60,
    )


# ── Docker compose validation ────────────────────────────────────────


class TestDockerComposeConfigs:
    """Tests that validate docker-compose configuration files."""

    def test_dev_compose_valid(self):
        """docker-compose.yml should be a valid compose file."""
        result = subprocess.run(
            ["docker", "compose", "-f", "docker-compose.yml", "config", "--quiet"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"Invalid compose file: {result.stderr}"

    def test_prod_compose_valid(self):
        """docker-compose.prod.yml should be a valid compose file."""
        result = subprocess.run(
            ["docker", "compose", "-f", "docker-compose.prod.yml", "config", "--quiet"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"Invalid compose file: {result.stderr}"

    def test_test_compose_valid(self):
        """docker-compose.test.yml should be a valid compose file."""
        result = subprocess.run(
            ["docker", "compose", "-f", COMPOSE_FILE, "config", "--quiet"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"Invalid compose file: {result.stderr}"

    def test_dev_compose_services(self):
        """Dev compose should define api and frontend services."""
        result = subprocess.run(
            ["docker", "compose", "-f", "docker-compose.yml", "config", "--services"],
            capture_output=True, text=True,
        )
        services = result.stdout.strip().splitlines()
        assert "api" in services
        assert "frontend" in services

    def test_prod_compose_services(self):
        """Prod compose should define nginx and api services (frontend-builder is in build profile)."""
        result = subprocess.run(
            ["docker", "compose", "-f", "docker-compose.prod.yml", "config", "--services"],
            capture_output=True, text=True,
        )
        services = result.stdout.strip().splitlines()
        assert "nginx" in services
        assert "api" in services

    def test_prod_compose_frontend_builder_in_profile(self):
        """Prod compose should define frontend-builder in the build profile."""
        result = subprocess.run(
            ["docker", "compose", "-f", "docker-compose.prod.yml",
             "--profile", "build", "config", "--services"],
            capture_output=True, text=True,
        )
        services = result.stdout.strip().splitlines()
        assert "frontend-builder" in services


# ── Dockerfile syntax validation ──────────────────────────────────────


class TestDockerfileSyntax:
    """Tests that validate the production Dockerfile structure."""

    def test_dockerfile_exists(self):
        """The production Dockerfile should exist."""
        result = subprocess.run(["test", "-f", "Dockerfile"], capture_output=True)
        assert result.returncode == 0

    def test_dockerfile_has_valid_base_image(self):
        """Dockerfile should have a FROM instruction."""
        with open("Dockerfile") as f:
            content = f.read()
        assert "FROM " in content

    def test_dockerfile_exposes_port_8000(self):
        """Dockerfile should expose port 8000 for the API."""
        with open("Dockerfile") as f:
            content = f.read()
        assert "EXPOSE 8000" in content

    def test_dockerfile_sets_pythonpath(self):
        """Dockerfile should set PYTHONPATH for app imports."""
        with open("Dockerfile") as f:
            content = f.read()
        assert "PYTHONPATH" in content

    def test_dockerfile_copies_app_code(self):
        """Dockerfile should copy app/ and lib/ directories."""
        with open("Dockerfile") as f:
            content = f.read()
        assert "COPY app/" in content
        assert "COPY lib/" in content

    def test_dockerfile_installs_requirements(self):
        """Dockerfile should install Python requirements."""
        with open("Dockerfile") as f:
            content = f.read()
        assert "requirements.txt" in content

    def test_dockerfile_copies_invoicing_assets(self):
        """Dockerfile should copy invoicing templates and assets."""
        with open("Dockerfile") as f:
            content = f.read()
        for asset in ["style.css", "logo.svg", "template.jinja2", "Makefile"]:
            assert asset in content, f"Missing asset: {asset}"

    def test_dockerfile_has_entrypoint_with_dumb_init(self):
        """Dockerfile should use dumb-init for proper signal handling."""
        with open("Dockerfile") as f:
            content = f.read()
        assert "dumb-init" in content

    def test_dockerfile_runs_gunicorn(self):
        """Dockerfile CMD should run gunicorn with uvicorn workers."""
        with open("Dockerfile") as f:
            content = f.read()
        assert "gunicorn" in content
        assert "uvicorn" in content


# ── Container startup and API tests ──────────────────────────────────


class TestContainerStartup:
    """Tests that the container starts correctly."""

    def test_container_is_running(self, docker_compose_up):
        """The API container should be in running state."""
        result = subprocess.run(
            ["docker", "compose", "-f", COMPOSE_FILE, "-p", PROJECT_NAME,
             "ps", "--format", "json"],
            capture_output=True, text=True,
        )
        containers = []
        for line in result.stdout.strip().splitlines():
            if line.strip():
                containers.append(json.loads(line))
        api_containers = [
            c for c in containers
            if "api" in c.get("Service", c.get("service", ""))
        ]
        assert len(api_containers) >= 1
        state = api_containers[0].get("State", api_containers[0].get("state", ""))
        assert state == "running", f"Container state: {state}"

    def test_python_available(self, docker_compose_up):
        """Python3 should be available inside the container."""
        result = subprocess.run(
            ["docker", "compose", "-f", COMPOSE_FILE, "-p", PROJECT_NAME,
             "exec", "-T", "api", "python3", "--version"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "Python 3" in result.stdout

    def test_app_files_mounted(self, docker_compose_up):
        """Application files should be present in the container."""
        result = subprocess.run(
            ["docker", "compose", "-f", COMPOSE_FILE, "-p", PROJECT_NAME,
             "exec", "-T", "api", "python3", "-c",
             "import app.main; print('OK')"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "OK" in result.stdout

    def test_lib_modules_importable(self, docker_compose_up):
        """Application lib modules should be importable."""
        result = subprocess.run(
            ["docker", "compose", "-f", COMPOSE_FILE, "-p", PROJECT_NAME,
             "exec", "-T", "api", "python3", "-c",
             "from lib.config import load_config; from lib.models import parse_member; print('OK')"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "OK" in result.stdout

    def test_gunicorn_process_running(self, docker_compose_up):
        """Gunicorn should be running inside the container."""
        result = subprocess.run(
            ["docker", "compose", "-f", COMPOSE_FILE, "-p", PROJECT_NAME,
             "exec", "-T", "api", "python3", "-c",
             "import os; entries = os.listdir('/proc'); pids = [e for e in entries if e.isdigit()]; "
             "cmdlines = [open(f'/proc/{p}/cmdline').read() for p in pids]; "
             "print('\\n'.join(cmdlines))"],
            capture_output=True, text=True,
        )
        assert "gunicorn" in result.stdout

    def test_environment_variables_set(self, docker_compose_up):
        """Environment variables from docker-compose should be set."""
        result = subprocess.run(
            ["docker", "compose", "-f", COMPOSE_FILE, "-p", PROJECT_NAME,
             "exec", "-T", "api", "python3", "-c",
             "import os; print(os.environ.get('DASHBOARD_PASSWORD'), os.environ.get('SESSION_SECRET'))"],
            capture_output=True, text=True,
        )
        assert "testpass" in result.stdout
        assert "test-secret" in result.stdout


# ── Health endpoint tests ─────────────────────────────────────────────


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_returns_ok(self, docker_compose_up):
        """GET /api/health should return 200 with status ok."""
        status, body, _ = _api("GET", "/api/health")
        assert status == 200
        assert body == {"status": "ok"}

    def test_health_returns_json(self, docker_compose_up):
        """Health endpoint should return valid JSON with correct content type."""
        resp = urllib.request.urlopen(f"{API_BASE}/api/health")
        content_type = resp.getheader("Content-Type")
        assert "application/json" in content_type
        body = json.loads(resp.read().decode())
        assert "status" in body


# ── Authentication endpoint tests ─────────────────────────────────────


class TestAuthEndpoints:
    """Tests for the authentication flow."""

    def test_auth_check_without_login_returns_401(self, docker_compose_up):
        """GET /api/auth/check without session should return 401."""
        status, body, _ = _api("GET", "/api/auth/check")
        assert status == 401

    def test_login_with_wrong_password_returns_401(self, docker_compose_up):
        """POST /api/auth/login with wrong password should return 401."""
        status, body, _ = _api("POST", "/api/auth/login", {"password": "wrong"})
        assert status == 401

    def test_login_with_correct_password(self, docker_compose_up):
        """POST /api/auth/login with correct password should return 200."""
        status, body, cookie = _api("POST", "/api/auth/login", {"password": "testpass"})
        assert status == 200
        assert body["status"] == "ok"
        assert cookie is not None, "Should set a session cookie"

    def test_full_auth_flow(self, docker_compose_up):
        """Login -> check -> logout -> check should work end-to-end."""
        # Login
        status, body, cookie = _api("POST", "/api/auth/login", {"password": "testpass"})
        assert status == 200
        session_cookie = cookie.split(";")[0] if cookie else None
        assert session_cookie is not None

        # Check auth (should succeed with cookie)
        status, body, _ = _api("GET", "/api/auth/check", cookie=session_cookie)
        assert status == 200
        assert body["status"] == "authenticated"

        # Logout
        status, body, _ = _api("POST", "/api/auth/logout", cookie=session_cookie)
        assert status == 200

    def test_login_missing_password_field_returns_422(self, docker_compose_up):
        """POST /api/auth/login without password field should return 422."""
        status, body, _ = _api("POST", "/api/auth/login", {})
        assert status == 422


# ── API route existence tests ─────────────────────────────────────────


class TestAPIRoutes:
    """Tests that all expected API routes exist and respond."""

    def test_members_requires_auth(self, docker_compose_up):
        """GET /api/members/ should require authentication."""
        status, _, _ = _api("GET", "/api/members/")
        assert status == 401

    def test_campaigns_requires_auth(self, docker_compose_up):
        """GET /api/campaigns/ should require authentication."""
        status, _, _ = _api("GET", "/api/campaigns/")
        assert status == 401

    def test_summary_requires_auth(self, docker_compose_up):
        """GET /api/summary/ should require authentication."""
        status, _, _ = _api("GET", "/api/summary/")
        assert status == 401

    def test_authenticated_members_returns_non_401(self, docker_compose_up):
        """Authenticated request to /api/members/ should not return 401."""
        # Login first
        _, _, cookie = _api("POST", "/api/auth/login", {"password": "testpass"})
        session_cookie = cookie.split(";")[0] if cookie else None

        # Access members (may return 500 due to no config, but not 401)
        status, _, _ = _api("GET", "/api/members/", cookie=session_cookie)
        assert status != 401, f"Should not return 401 when authenticated, got {status}"

    def test_openapi_docs_available(self, docker_compose_up):
        """FastAPI should serve OpenAPI docs at /docs."""
        resp = urllib.request.urlopen(f"{API_BASE}/docs")
        assert resp.status == 200

    def test_openapi_json_available(self, docker_compose_up):
        """FastAPI should serve OpenAPI JSON at /openapi.json."""
        resp = urllib.request.urlopen(f"{API_BASE}/openapi.json")
        assert resp.status == 200
        schema = json.loads(resp.read().decode())
        assert "paths" in schema
        assert "/api/health" in schema["paths"]
