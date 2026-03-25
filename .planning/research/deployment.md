# Deployment Research: React SPA + Python API in Docker

**Project:** ACS HelloAsso Invoicing
**Researched:** 2026-03-25
**Overall confidence:** HIGH

## Executive Summary

The current project runs a debian:trixie container that exposes only SSH (port 22) for CLI access to the `helloasso` Python tool. Evolving this into a full-stack web application (React frontend + FastAPI backend) requires a deliberate deployment architecture. The project already uses Docker secrets for SSH passwords and a `conf.json` file for credentials, so the secrets pattern is partially established.

Based on research, the recommended approach is a **single-container deployment using Nginx as a reverse proxy** that serves the React static build and proxies API requests to a Gunicorn+Uvicorn backend. This is the right tradeoff for this project's scale (small association tool, not high-traffic SaaS). A Docker Compose setup orchestrates development, while a multi-stage Dockerfile produces the production image.

SSH access can be preserved via a separate exposed port during the transition period, then deprecated once the web UI fully replaces CLI workflows.

---

## 1. Container Architecture: Single Container (Recommended)

### Why Single Container Over Multi-Container

This is a small-scale association management tool, not a microservices platform. Multi-container (separate frontend, backend, nginx containers via Docker Compose) adds operational complexity with no benefit at this scale. The project currently deploys as a single container, and staying with that model minimizes migration friction.

**Recommended architecture:**

```
                    +----------------------------------+
                    |       Single Container           |
  Port 80/443 ---->|  Nginx                           |
                    |    /          -> React static    |
                    |    /api/*     -> Gunicorn:8000   |
  Port 22 -------->|  SSHD (optional, backward compat)|
                    +----------------------------------+
```

### Multi-Stage Dockerfile

```dockerfile
# Stage 1: Build React frontend
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Production image
FROM debian:trixie-slim

# System dependencies
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -yq --no-install-recommends \
    nginx python3 python3-pip python3-venv \
    dumb-init openssh-server \
    ca-certificates libpangocairo-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Python app
COPY backend/ /app/backend/
RUN python3 -m venv /app/venv && \
    /app/venv/bin/pip install --no-cache-dir -r /app/backend/requirements.txt

# React build from stage 1
COPY --from=frontend-build /app/frontend/dist /usr/share/nginx/html

# Nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Entrypoint script that starts nginx + gunicorn + (optionally) sshd
COPY docker-entrypoint.sh /usr/local/sbin/
RUN chmod +x /usr/local/sbin/docker-entrypoint.sh

EXPOSE 80 22

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost/api/health || exit 1

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["/usr/local/sbin/docker-entrypoint.sh"]
```

**Confidence:** HIGH -- This pattern is well-documented across multiple sources and matches the project's existing single-container model.

---

## 2. Reverse Proxy: Nginx

### Why Nginx Over Caddy

- Nginx is the de facto standard for this exact use case (static SPA + API proxy).
- The project already uses Debian; Nginx is a single `apt-get install`.
- Caddy's automatic HTTPS is irrelevant here (TLS termination happens upstream, likely at the host/cloud level).
- Nginx is lighter on resources and the team is more likely to find help/examples.

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name _;

    # Serve React SPA
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to FastAPI/Gunicorn
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (if needed later)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Serve generated PDF invoices (if needed)
    location /invoices/ {
        alias /app/data/invoices/;
        internal;  # Only accessible via X-Accel-Redirect from API
    }
}
```

Key points:
- `try_files $uri $uri/ /index.html` ensures React Router handles client-side routing.
- `/api/` proxy eliminates all CORS issues since everything is same-origin.
- `internal` directive on `/invoices/` allows API-controlled access to generated PDFs via Nginx's X-Accel-Redirect (efficient file serving without loading files through Python).

**Confidence:** HIGH -- Standard, well-proven pattern.

---

## 3. Python ASGI Server: Gunicorn + Uvicorn Workers

### Recommendation: Gunicorn with UvicornWorker class

```bash
/app/venv/bin/gunicorn app.main:app \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --access-logfile - \
    --error-logfile - \
    --proxy-headers \
    --forwarded-allow-ips="127.0.0.1"
```

### Why Not Uvicorn Alone

- Uvicorn standalone lacks process management. If the process crashes, the app is offline.
- Gunicorn provides worker management, graceful restarts, and fault tolerance.
- The `--proxy-headers` flag is critical since Nginx sits in front.

### Worker Count

For this project: **2 workers** is sufficient. The formula `(2 * CPU cores) + 1` is for high-traffic apps. This is a low-traffic association tool. Two workers provide redundancy without wasting resources.

### Why Not Flask

The project description mentions Flask as an option. Use **FastAPI** instead because:
- Native async support (important for HelloAsso API calls that can be slow).
- Automatic OpenAPI documentation (useful for a small team).
- Pydantic validation built in (reduces boilerplate for API input validation).
- FastAPI is the modern standard; Flask is legacy for new projects in 2026.

**Confidence:** HIGH -- Gunicorn + UvicornWorker is the industry standard for FastAPI production.

---

## 4. Environment Variables and Secrets Management

### Current State

The project currently uses a `conf.json` file containing:
- HelloAsso API credentials (`credentials.helloasso.id`, `credentials.helloasso.secret`)
- SMTP credentials (`credentials.sendemail.username`, `credentials.sendemail.password`)
- Organization configuration (`conf.helloasso.*`, `conf.sendemail.*`)

The SSH setup already uses Docker secrets (`/run/secrets/${user}.password`).

### Recommended Approach

**Development:** `.env` file (gitignored, already partially in place).

```env
# .env (development only, NEVER committed)
HELLOASSO_CLIENT_ID=xxx
HELLOASSO_CLIENT_SECRET=xxx
SMTP_USERNAME=xxx
SMTP_PASSWORD=xxx
SMTP_HOST=smtp.example.com
SMTP_FROM=acs@example.com
HELLOASSO_API_URL=https://api.helloasso.com
HELLOASSO_ORG_NAME=acs
HELLOASSO_FORM_TYPE=MembershipForm
HELLOASSO_FORM_SLUG=adhesion
```

**Production:** Docker secrets (file-based), already supported by the existing setup pattern.

```yaml
# docker-compose.prod.yml
services:
  app:
    secrets:
      - helloasso_client_id
      - helloasso_client_secret
      - smtp_password

secrets:
  helloasso_client_id:
    file: ./secrets/helloasso_client_id.txt
  helloasso_client_secret:
    file: ./secrets/helloasso_client_secret.txt
  smtp_password:
    file: ./secrets/smtp_password.txt
```

**Application code pattern** for reading secrets:

```python
import os

def get_secret(name: str, env_fallback: str = None) -> str:
    """Read from Docker secret file, fall back to env var."""
    secret_path = f"/run/secrets/{name}"
    if os.path.isfile(secret_path):
        with open(secret_path, "r") as f:
            return f.read().strip()
    if env_fallback:
        return os.environ.get(env_fallback, "")
    return os.environ.get(name.upper(), "")
```

### Migration from conf.json

The existing `conf.json` pattern should be replaced with environment variables / secrets for credentials, while keeping a simplified config file for non-sensitive organization settings. This separates secrets from configuration, which is both more secure and more portable.

**Confidence:** HIGH -- Docker secrets pattern already partially in use; environment variables are standard.

---

## 5. Docker Compose for Development

### docker-compose.yml (development)

```yaml
version: "3.8"

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - ./backend:/app/backend
      - ./invoicing:/app/invoicing
    ports:
      - "8000:8000"
    env_file:
      - .env
    command: >
      /app/venv/bin/uvicorn app.main:app
      --host 0.0.0.0 --port 8000 --reload
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    volumes:
      - ./frontend/src:/app/frontend/src
    ports:
      - "5173:5173"
    environment:
      - VITE_API_URL=http://localhost:8000
    command: npm run dev -- --host 0.0.0.0

  # Optional: for invoice PDF generation testing
  # weasyprint needs system-level deps, runs in backend container
```

### Development Workflow

1. `docker compose up` starts both frontend (Vite dev server with HMR) and backend (Uvicorn with `--reload`).
2. Frontend hits backend directly at `localhost:8000` during development (no Nginx needed in dev).
3. Source code is volume-mounted for hot reload on both sides.
4. Production build uses multi-stage Dockerfile (no dev server, no volume mounts).

**Confidence:** HIGH -- Standard Docker Compose dev workflow.

---

## 6. Health Checks and Logging

### Health Check Endpoint

```python
from fastapi import FastAPI
from datetime import datetime

app = FastAPI()

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
```

### Dockerfile HEALTHCHECK

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost/api/health || exit 1
```

The `--start-period` gives the app time to initialize before health checks start failing.

### Logging Best Practices

- **Stdout/stderr only** -- Docker captures container output automatically. Do not write to log files inside the container.
- **Structured logging** -- Use Python's `logging` module with JSON formatter for machine-parseable logs.
- **Access logs** -- Gunicorn `--access-logfile -` sends access logs to stdout.
- **Log levels** -- Use `INFO` for production, `DEBUG` for development (controlled via environment variable).

```python
import logging
import sys

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","module":"%(module)s","message":"%(message)s"}'
)
```

**Confidence:** HIGH -- Standard Docker logging practices.

---

## 7. Migration Path from Current SSH-Only Container

### Phase 1: Add API alongside SSH (backward compatible)

- Keep the existing SSH setup working (port 22).
- Add FastAPI backend that wraps the existing `helloasso.py` logic.
- Add Nginx to serve API on port 80.
- The existing `helloasso.py` CLI continues to work via SSH.
- Docker entrypoint starts both SSHD and Gunicorn+Nginx.

```bash
#!/bin/bash
# docker-entrypoint.sh

# Run pre-start (user creation for SSH)
/usr/local/sbin/docker-pre-start.sh

# Start Nginx
nginx

# Start Gunicorn (background)
/app/venv/bin/gunicorn app.main:app \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --access-logfile - \
    --error-logfile - &

# Start SSHD (foreground, keeps container alive)
/usr/sbin/sshd -D
```

### Phase 2: Add React frontend

- Build React SPA and serve via Nginx.
- Web UI provides all functionality that CLI offered.
- SSH still available but no longer the primary interface.

### Phase 3: Deprecate SSH

- Remove SSH server, related user creation scripts, and port 22 exposure.
- Switch foreground process to Gunicorn (Nginx runs as daemon).
- Simplify the Dockerfile significantly.

### Key Migration Considerations

- **Existing `helloasso.py` logic** should be refactored into importable modules that both the CLI and FastAPI endpoints can use. Do not duplicate business logic.
- **The `conf.json` file** should be replaced with environment variables / Docker secrets, but support both during transition.
- **Invoice generation** (WeasyPrint, Jinja2 templates) stays server-side. The web UI triggers it via API; PDFs are served via Nginx X-Accel-Redirect.
- **sendemail** CLI tool for sending invoices should be replaced with Python's `smtplib` or a library like `aiosmtplib` for async email sending from the API.

**Confidence:** HIGH -- Incremental migration is well-understood; the existing entrypoint pattern supports multiple processes.

---

## 8. Production Dockerfile Optimizations

### Use debian:trixie-slim instead of debian:trixie

The `-slim` variant is significantly smaller. The current image installs many packages; slim base + explicit dependencies is more efficient.

### .dockerignore

```
.git
.planning
.env
*.md
frontend/node_modules
__pycache__
*.pyc
```

### Non-root user

Run the application as a non-root user in production (except SSHD which requires root, but that gets removed in Phase 3).

```dockerfile
RUN useradd --system --no-create-home appuser
USER appuser
```

### Pin dependency versions

Pin all Python and Node dependencies. Use `pip freeze` and `package-lock.json` for reproducible builds.

---

## Anti-Patterns to Avoid

| Anti-Pattern | Why Bad | Do Instead |
|---|---|---|
| Running Uvicorn standalone in production | No process management, single point of failure | Use Gunicorn + UvicornWorker |
| Serving React from FastAPI's StaticFiles | Python handles every static file request unnecessarily | Use Nginx for static files |
| Using `docker exec` for debugging | Fragile, not reproducible | Use proper logging + health checks |
| Storing secrets in Dockerfile ENV/ARG | Persisted in image layers, visible in `docker inspect` | Use Docker secrets or runtime env vars |
| Running as root in production | Security risk | Use non-root USER directive |
| Using Alpine for Python + WeasyPrint | Alpine uses musl libc; WeasyPrint/Pango have compatibility issues | Stick with Debian |

---

## Sources

- [FastAPI Official Docker Deployment Guide](https://fastapi.tiangolo.com/deployment/docker/)
- [FastAPI Server Workers Documentation](https://fastapi.tiangolo.com/deployment/server-workers/)
- [Docker Compose Environment Variables Best Practices](https://docs.docker.com/compose/how-tos/environment-variables/best-practices/)
- [Docker Secrets in Compose](https://docs.docker.com/compose/how-tos/use-secrets/)
- [Better Stack: FastAPI Docker Best Practices](https://betterstack.com/community/guides/scaling-python/fastapi-docker-best-practices/)
- [Definitive Guide to FastAPI Production Deployment (2025)](https://blog.greeden.me/en/2025/09/02/the-definitive-guide-to-fastapi-production-deployment-with-dockeryour-one-stop-reference-for-uvicorn-gunicorn-nginx-https-health-checks-and-observability-2025-edition/)
- [FastAPI Deployment Guide for 2026](https://www.zestminds.com/blog/fastapi-deployment-guide/)
- [Miguel Grinberg: How to Dockerize a React + Flask Project](https://blog.miguelgrinberg.com/post/how-to-dockerize-a-react-flask-project)
- [GitGuardian: How to Handle Secrets in Docker](https://blog.gitguardian.com/how-to-handle-secrets-in-docker/)
- [Build with Matija: Dev Containers Guide](https://www.buildwithmatija.com/blog/configuring-development-containers-docker-guide)
