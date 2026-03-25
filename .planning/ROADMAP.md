# Roadmap: ACS HelloAsso Invoicing Web Dashboard

## Overview
3 phases, dependency-ordered. Each phase delivers testable, standalone value.
Key constraint: no database, flat files only, keep sendemail, shared library between CLI and web.

---

## Phase 1: Shared Library & API Foundation
**Goal**: Extract shared library from `helloasso.py`, build FastAPI backend, basic auth.

**Delivers**: A working API (testable via Swagger UI) that reads/writes the same JSON files as the CLI.

### Scope
- Extract shared Python library from `helloasso.py`:
  - `lib/helloasso.py` — HelloAsso API wrapper (auth, data fetching, pagination, filters)
  - `lib/config.py` — Config loading from conf.json
  - `lib/models.py` — Data structures (member, invoice status)
  - `lib/filesystem.py` — File operations (read/write JSON, scan for PDFs/mail.logs)
- Refactor CLI `helloasso.py` to import from shared library (same behavior)
- Proper OAuth2 token lifecycle with refresh_token
- FastAPI application (`app/`):
  - `POST /api/auth/login`, `POST /api/auth/logout`
  - `GET /api/members` (reads JSON files from `invoicing/<formSlug>/`, with filters)
  - `GET /api/members/{id}`
  - `GET /api/members/export/csv`
  - `GET /api/campaigns` (list available formSlug directories)
  - `POST /api/campaigns/{slug}/refresh` (fetch from HelloAsso, dump JSON files)
  - `GET /api/summary` (activity breakdown computed from JSON files)
  - `GET /api/health`
- Status derived from filesystem:
  - `.json` exists → member data dumped
  - `.pdf` exists → invoice generated
  - `.mail.log` exists → email sent
- Config via existing conf.json format
- Development setup: requirements.txt, docker-compose.yml

### Success Criteria
- CLI `helloasso.py` works identically after refactor (no behavior change)
- All API endpoints return correct data from JSON files
- HelloAsso token refreshes automatically
- Auth blocks unauthenticated access
- `POST /api/campaigns/{slug}/refresh` creates same JSON files as CLI `--dump`

### Dependencies
- None (first phase)

### Key Risks
- Refactoring `helloasso.py` without breaking CLI behavior
- HelloAsso token refresh logic

---

## Phase 2: Invoice & Email Pipeline via API
**Goal**: API endpoints for invoice generation and email sending, using existing Makefile pipeline.

**Delivers**: Complete invoicing workflow accessible via API, reusing existing WeasyPrint + sendemail tooling.

### Scope
- API endpoints:
  - `POST /api/invoices/{member_id}/generate` (runs Makefile `%.pdf` target)
  - `POST /api/invoices/batch` (batch generation as background task)
  - `GET /api/invoices/batch/{job_id}/status` (progress polling)
  - `GET /api/invoices/{member_id}/download` (serve PDF file)
  - `GET /api/invoices/{member_id}/preview` (render Jinja2 to HTML)
  - `POST /api/emails/{member_id}/send` (runs Makefile `%.mail.log` target)
  - `POST /api/emails/batch` (batch send as background task)
  - `GET /api/emails/batch/{job_id}/status`
- Invoice generation via existing pipeline:
  - Call Makefile targets (or equivalent WeasyPrint calls) from Python
  - Reuse existing template.jinja2, style.css, logo.svg
  - Output to same `invoicing/<formSlug>/` directory
- Email sending via existing sendemail (Makefile `sendemail` target)
- Background tasks via FastAPI BackgroundTasks
- WeasyPrint in thread pool (asyncio.to_thread)

### Success Criteria
- Single invoice PDF matches existing Makefile-generated output (identical)
- Batch generation runs without blocking the API
- Emails sent via same sendemail pipeline as CLI
- Status correctly reflects filesystem state (.pdf, .mail.log presence)

### Dependencies
- Phase 1 (shared library, API foundation, auth)

### Key Risks
- WeasyPrint memory on batch (mitigate: thread pool, Docker memory limit)
- CSS/asset path resolution (mitigate: set base_url correctly)
- Subprocess management for Makefile targets

---

## Phase 3: Svelte Dashboard & Docker Deployment
**Goal**: Svelte SPA frontend and production Docker deployment.

**Delivers**: The complete web application accessible to volunteers via browser.

### Scope
- Svelte app (Vite + TypeScript):
  - Login page
  - Member list page (data table with filters, search, sort, pagination)
  - Activity summary view
  - Invoice management (generate, preview, download per member)
  - Batch actions (generate all invoices, send all emails)
  - Background task progress indicators
  - Email status tracking view
  - Season/campaign selector
- French language UI (hardcoded strings)
- ACS branding (logo, theme colors)
- Production Docker:
  - Multi-stage Dockerfile (Node build + Python production)
  - Nginx reverse proxy (static files + API proxy)
  - Gunicorn + UvicornWorker
  - Docker Compose for dev (Vite HMR + Uvicorn reload)
  - Health check

### Success Criteria
- Volunteer can complete full workflow via browser: login → view members → filter → generate invoices → send emails
- Dashboard loads in < 3 seconds
- Responsive on desktop and tablet
- Single `docker compose up` starts the entire stack in dev
- CLI and web coexist — same data files visible from both

### Dependencies
- Phase 1 (API endpoints)
- Phase 2 (invoice and email endpoints)

### Key Risks
- Svelte data table component selection (fewer options than React/Vue)
- SPA routing catch-all vs API routes (mitigate: Nginx routing, /api/ prefix)

---

## Phase Summary

| Phase | Name | Depends On | Key Deliverable |
|-------|------|-----------|-----------------|
| 1 | Shared Library & API Foundation | — | Refactored CLI + FastAPI + flat files + auth |
| 2 | Invoice & Email Pipeline via API | Phase 1 | PDF generation + sendemail via API |
| 3 | Svelte Dashboard & Docker | Phase 1, 2 | Full web UI + production deployment |
