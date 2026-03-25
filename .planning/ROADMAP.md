# Roadmap: ACS HelloAsso Invoicing Web Dashboard

## Overview
3 phases, dependency-ordered. Each phase delivers testable, standalone value.

---

## Phase 1: API Foundation
**Goal**: FastAPI backend with HelloAsso integration, SQLite persistence, and basic auth.

**Delivers**: A working API that the React frontend (Phase 3) will consume. Testable via Swagger UI.

### Scope
- FastAPI project structure (`app/` with routes, services, models, config)
- HelloAsso service class (refactored from `helloasso.py`)
  - Proper OAuth2 token lifecycle with refresh_token
  - Member data fetching with pagination and all filters
  - httpx async client (replacing requests)
- SQLite database with SQLModel
  - Member cache table
  - Invoice tracking table (status: not_generated / generated / error)
  - Email log table (status: not_sent / sent / error)
  - User table (dashboard credentials)
- API endpoints:
  - `POST /api/auth/login`, `POST /api/auth/logout`
  - `GET /api/members` (with query params for all filters)
  - `GET /api/members/{id}`
  - `GET /api/members/export/csv`
  - `GET /api/campaigns` (list available formSlugs)
  - `POST /api/campaigns/{slug}/refresh` (fetch from HelloAsso, update cache)
  - `GET /api/summary` (activity breakdown)
  - `GET /api/health`
- Config via Pydantic BaseSettings (env vars + Docker secrets support)
- Development setup: requirements.txt, Dockerfile.dev, docker-compose.yml

### Success Criteria
- All API endpoints return correct data (testable via Swagger UI)
- HelloAsso token refreshes automatically on expiry
- Member data is cached in SQLite after refresh
- Auth blocks unauthenticated access

### Dependencies
- None (first phase)

### Key Risks
- HelloAsso token refresh logic (mitigate: implement from day one per research)
- SQLite concurrent access (mitigate: WAL mode)

---

## Phase 2: Invoice Pipeline & Email
**Goal**: PDF invoice generation and email sending via API endpoints with background task support.

**Delivers**: Complete invoicing workflow accessible via API. Volunteers can generate and send invoices.

### Scope
- Invoice service class
  - Jinja2 template rendering (migrate existing `template.jinja2`)
  - WeasyPrint PDF generation via `asyncio.to_thread()`
  - PDF storage and download serving
- Email service class
  - Python smtplib replacing sendemail CLI
  - EmailMessage with UTF-8 support and PDF attachment
  - SMTP credentials via env vars / Docker secrets
- API endpoints:
  - `POST /api/invoices/{member_id}/generate` (single invoice)
  - `POST /api/invoices/batch` (batch generation as background task)
  - `GET /api/invoices/batch/{job_id}/status` (progress polling)
  - `GET /api/invoices/{member_id}/download` (PDF download)
  - `GET /api/invoices/{member_id}/preview` (HTML preview)
  - `POST /api/emails/{member_id}/send` (single email)
  - `POST /api/emails/batch` (batch send as background task)
  - `GET /api/emails/batch/{job_id}/status`
- Invoice and email status tracking in SQLite
- Migrate invoice assets (template, CSS, logo, signature) to `app/templates/`

### Success Criteria
- Single invoice PDF matches existing Makefile-generated output
- Batch generation runs without blocking the API
- Emails arrive with correct PDF attachment and French encoding
- Status tracking shows generated/sent/error per member

### Dependencies
- Phase 1 (API foundation, member data, SQLite, auth)

### Key Risks
- WeasyPrint memory on batch (mitigate: thread pool, monitor memory, Docker memory limit)
- CSS/asset path resolution in WeasyPrint (mitigate: set base_url correctly)
- French character encoding in emails (mitigate: use modern EmailMessage API)

---

## Phase 3: React Dashboard & Docker Deployment
**Goal**: React SPA frontend and production Docker deployment.

**Delivers**: The complete web application accessible to volunteers via browser.

### Scope
- React app (Vite + TypeScript + Mantine 7)
  - Login page
  - Member list page (Mantine React Table with filters, search, sort, pagination)
  - Activity summary view
  - Invoice management (generate, preview, download per member)
  - Batch actions (generate all invoices, send all emails)
  - Background task progress indicators
  - Email status tracking view
  - Season/campaign selector
  - Settings page (read-only config display)
- Mantine AppShell layout with sidebar navigation
- TanStack Query for API data fetching and caching
- French language UI (react-i18next or hardcoded)
- ACS branding (logo, theme colors)
- Production Docker:
  - Multi-stage Dockerfile (Node build + Python production)
  - Nginx reverse proxy (static files + API proxy)
  - Gunicorn + UvicornWorker (2 workers)
  - Docker Compose for dev (Vite HMR + Uvicorn reload)
  - Health check
  - Non-root user

### Success Criteria
- Volunteer can complete full workflow via browser: login → view members → filter → generate invoices → send emails
- Dashboard loads in < 3 seconds
- Responsive on desktop and tablet
- Single `docker compose up` starts the entire stack in dev
- Single `docker build && docker run` deploys production

### Dependencies
- Phase 1 (API endpoints)
- Phase 2 (invoice and email endpoints)

### Key Risks
- React Router catch-all vs API routes (mitigate: Nginx routing, /api/ prefix)
- Vite build path configuration (mitigate: test build early)
- PDF preview in browser (mitigate: start with iframe, upgrade to react-pdf if needed)

---

## Phase Summary

| Phase | Name | Depends On | Key Deliverable |
|-------|------|-----------|-----------------|
| 1 | API Foundation | — | FastAPI + HelloAsso + SQLite + Auth |
| 2 | Invoice Pipeline & Email | Phase 1 | PDF generation + email sending via API |
| 3 | React Dashboard & Docker | Phase 1, 2 | Full web UI + production deployment |
