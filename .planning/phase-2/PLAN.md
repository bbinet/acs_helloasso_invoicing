# Phase 2 Plan: Invoice Pipeline & Email

## Goal
API endpoints for invoice generation and email sending, using existing Makefile pipeline via subprocess. Batch operations via BackgroundTasks.

## Methodology: Test-Driven Development
Same as Phase 1:
- **Vertical slices**: RED → GREEN per behavior
- **Mock at system boundaries**: subprocess calls (make), filesystem
- **Integration tests**: FastAPI TestClient for API endpoints

## Success Criteria
1. Single invoice PDF generated via `make` matches CLI-generated output
2. Batch generation runs without blocking the API
3. Emails sent via same sendemail/Makefile pipeline as CLI
4. Status correctly reflects filesystem state (.pdf, .mail.log presence)
5. HTML preview renders correctly via Jinja2 Python
6. Symlinks created automatically when missing
7. All tests pass (`pytest` green)

---

## Wave 1: Invoicing Library (TDD)

### Task 1.1: `lib/invoicing.py` — Symlinks and Make wrappers (TDD)
**Files:** `tests/test_invoicing.py`, `lib/invoicing.py`
**What:**
- `ensure_symlinks(invoicing_dir, config)` — creates symlinks if missing:
  - `Makefile` → `../Makefile` (relative to invoicing_dir)
  - `conf.json` → symlink to the actual conf.json path from config
  - `signature.png` → symlink to signature.png in invoicing_dir's parent (if exists)
- `find_member_file(invoicing_dir, member_id)` — scan JSON files, find the one whose item `id` matches member_id, return filepath
- `run_make_pdf(invoicing_dir, json_basename)` — runs `subprocess.run(['make', f'{json_basename}.pdf'], cwd=invoicing_dir, capture_output=True, check=True)`
- `run_make_email(invoicing_dir, json_basename)` — runs `subprocess.run(['make', f'{json_basename}.mail.log'], cwd=invoicing_dir, capture_output=True, check=True)`
- `render_invoice_html(template_dir, item_data, signature_path=None)` — renders `template.jinja2` with Jinja2 Python directly, injecting `date` (today) and `signature`

**TDD cycles (mock subprocess at system boundary, use tmp_path for filesystem):**
1. RED: test `ensure_symlinks` creates Makefile symlink when missing → GREEN
2. RED: test `ensure_symlinks` creates conf.json symlink when missing → GREEN
3. RED: test `ensure_symlinks` does nothing when symlinks exist → GREEN
4. RED: test `find_member_file` finds correct file by item id → GREEN
5. RED: test `find_member_file` returns None for unknown id → GREEN
6. RED: test `run_make_pdf` calls subprocess with correct args and cwd → GREEN
7. RED: test `run_make_pdf` raises on subprocess failure → GREEN
8. RED: test `run_make_email` calls subprocess with correct args and cwd → GREEN
9. RED: test `render_invoice_html` returns HTML with member data → GREEN
10. RED: test `render_invoice_html` injects today's date → GREEN

**Mocking:** `@patch('lib.invoicing.subprocess.run')` for make calls. Real filesystem via `tmp_path` for symlinks and file finding.

**Commit:** "feat(2-1): Add lib/invoicing.py with TDD tests"

---

## Wave 2: Invoice API Routes (TDD)

### Task 2.1: Invoice routes (TDD)
**Files:** `tests/test_api_invoices.py`, `app/routes/invoices.py`
**What:**
Routes (all protected by `require_auth`):
- `POST /api/invoices/{member_id}/generate` — single PDF generation
  - Finds member JSON file via `find_member_file()`
  - Ensures symlinks via `ensure_symlinks()`
  - Calls `run_make_pdf()` in `asyncio.to_thread()`
  - Returns `{"status": "generated", "member_id": N}`
  - Returns 404 if member not found, 500 on make failure
- `GET /api/invoices/{member_id}/download` — serve PDF
  - Finds member file, checks .pdf exists
  - Returns `FileResponse` with the PDF
  - Returns 404 if PDF not found
- `GET /api/invoices/{member_id}/preview` — HTML preview
  - Finds member JSON, loads data
  - Calls `render_invoice_html()` with template from `invoicing/`
  - Returns HTML response
- `POST /api/invoices/batch` — batch generation
  - Scans all JSON files, generates PDFs for those without .pdf
  - Runs as BackgroundTasks
  - Returns `{"job_id": "uuid", "total": N}`
- `GET /api/invoices/batch/{job_id}/status` — batch progress
  - Returns `{"total": N, "completed": N, "errors": [...], "status": "running"|"done"}`

**Batch job tracking:**
```python
# Module-level dict for in-memory job tracking
_batch_jobs: dict[str, dict] = {}
```

**TDD cycles (mock subprocess, use tmp_path for fixtures):**
1. RED: test `POST /api/invoices/{id}/generate` calls make and returns success → GREEN
2. RED: test generate returns 404 for unknown member → GREEN
3. RED: test `GET /api/invoices/{id}/download` serves PDF file → GREEN
4. RED: test download returns 404 when PDF doesn't exist → GREEN
5. RED: test `GET /api/invoices/{id}/preview` returns HTML with member data → GREEN
6. RED: test `POST /api/invoices/batch` starts job and returns job_id → GREEN
7. RED: test `GET /api/invoices/batch/{job_id}/status` returns progress → GREEN

**Commit:** "feat(2-2): Add invoice API routes (generate, download, preview, batch)"

---

## Wave 3: Email API Routes (TDD)

### Task 3.1: Email routes (TDD)
**Files:** `tests/test_api_emails.py`, `app/routes/emails.py`
**What:**
Routes (all protected by `require_auth`):
- `POST /api/emails/{member_id}/send` — single email
  - Finds member JSON file
  - Checks that .pdf exists (can't email without invoice)
  - Ensures symlinks
  - Calls `run_make_email()` in `asyncio.to_thread()`
  - Returns `{"status": "sent", "member_id": N}`
  - Returns 404 if member not found, 400 if no PDF generated yet
- `POST /api/emails/batch` — batch send
  - Scans all JSON files, sends emails for those with .pdf but without .mail.log
  - Runs as BackgroundTasks
  - Returns `{"job_id": "uuid", "total": N}`
- `GET /api/emails/batch/{job_id}/status` — batch progress
  - Returns `{"total": N, "completed": N, "errors": [...], "status": "running"|"done"}`

**Batch job tracking:** Same pattern as invoices, separate `_batch_jobs` dict in emails module.

**TDD cycles:**
1. RED: test `POST /api/emails/{id}/send` calls make and returns success → GREEN
2. RED: test send returns 404 for unknown member → GREEN
3. RED: test send returns 400 when PDF doesn't exist → GREEN
4. RED: test `POST /api/emails/batch` starts job and returns job_id → GREEN
5. RED: test `GET /api/emails/batch/{job_id}/status` returns progress → GREEN

### Task 3.2: Update app/main.py
- Add `from app.routes import invoices, emails`
- Add `app.include_router(invoices.router, prefix="/api/invoices")`
- Add `app.include_router(emails.router, prefix="/api/emails")`

**Commit:** "feat(2-3): Add email API routes (send, batch) and wire all Phase 2 routes"

---

## Verification Checklist

### Tests
- [ ] `pytest` runs green (all tests pass — Phase 1 + Phase 2)
- [ ] Tests cover: invoicing lib, invoice routes, email routes

### Invoice generation
- [ ] `POST /api/invoices/{id}/generate` calls make and creates .pdf
- [ ] `GET /api/invoices/{id}/download` serves the PDF
- [ ] `GET /api/invoices/{id}/preview` returns HTML invoice
- [ ] `POST /api/invoices/batch` starts background job
- [ ] `GET /api/invoices/batch/{job_id}/status` returns progress

### Email sending
- [ ] `POST /api/emails/{id}/send` calls make and creates .mail.log
- [ ] `POST /api/emails/{id}/send` returns 400 when no PDF exists
- [ ] `POST /api/emails/batch` starts background job
- [ ] `GET /api/emails/batch/{job_id}/status` returns progress

### Symlinks
- [ ] Symlinks created automatically when missing (Makefile, conf.json)

### CLI compatibility
- [ ] Existing CLI workflow unchanged — `make pdf` and `make sendemail` still work in invoicing/<formSlug>/

## File Inventory

### New Files
| File | Purpose |
|------|---------|
| `lib/invoicing.py` | Symlinks, make wrappers, HTML preview rendering |
| `app/routes/invoices.py` | Invoice generate, download, preview, batch |
| `app/routes/emails.py` | Email send, batch |
| `tests/test_invoicing.py` | lib/invoicing.py tests |
| `tests/test_api_invoices.py` | Invoice endpoint tests |
| `tests/test_api_emails.py` | Email endpoint tests |

### Modified Files
| File | Change |
|------|--------|
| `app/main.py` | Add invoices and emails routers |
| `requirements.txt` | Add `jinja2` (for HTML preview rendering) |
