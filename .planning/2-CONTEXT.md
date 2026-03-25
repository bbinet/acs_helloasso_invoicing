# Phase 2 Context: Invoice Pipeline & Email

## Locked Decisions (from Phase 1)
- D1-D6 from 1-CONTEXT.md still apply
- lib/ structure, requests sync, flat files, same arborescence, single season

## Phase 2 Decisions

### D7: PDF Generation — Via Makefile subprocess
- Web calls `subprocess.run(['make', f'{basename}.pdf'], cwd=invoicing_dir)`
- Reuses the exact existing pipeline: JSON → jinja2-cli → HTML → weasyprint → PDF
- The Makefile creates a venv at `invoicing/.venv` with jinja2-cli and weasyprint==52.5
- Output goes to same `invoicing/<formSlug>/<member>.pdf` files
- Result is byte-identical to CLI-generated PDFs
- Runs in `asyncio.to_thread()` to avoid blocking the event loop

### D8: Email Sending — Via Makefile subprocess
- Web calls `subprocess.run(['make', f'{basename}.mail.log'], cwd=invoicing_dir)`
- Reuses sendemail exactly as the CLI Makefile does
- The Makefile reads SMTP credentials from conf.json via `jq`
- `.mail.log` file created on success (same as CLI)
- On error: Makefile renames to `error_<file>.mail.log`
- Runs in `asyncio.to_thread()`

### D9: HTML Preview — Jinja2 Python direct
- For the preview endpoint, render `template.jinja2` directly in Python using Jinja2
- No subprocess needed for preview — just HTML rendering
- Template loaded from `invoicing/template.jinja2`
- Variables: raw HelloAsso item JSON data + `date` (today) + `signature` path
- CSS linked via `style.css` relative path (served by the preview or inlined)

### D10: Batch Jobs — FastAPI BackgroundTasks + in-memory dict
- Use FastAPI `BackgroundTasks` for batch PDF generation and batch email sending
- Track progress in an in-memory dict: `{job_id: {"total": N, "completed": N, "errors": [...], "status": "running"|"done"|"error"}}`
- No external task queue (no Celery/Redis) — overkill for ~200 members
- Progress polled via `GET /api/invoices/batch/{job_id}/status` and `GET /api/emails/batch/{job_id}/status`

### D11: Symlinks — Created automatically
- Before running `make`, ensure the invoicing/<formSlug>/ directory has:
  - `Makefile` → symlink to `../../invoicing/Makefile` (or `../Makefile` depending on depth)
  - `conf.json` → symlink to the actual conf.json file
  - `signature.png` → symlink to the signature file (path from config or convention)
- If symlinks are missing, create them automatically
- Add a `lib/invoicing.py` (or extend `lib/filesystem.py`) with `ensure_symlinks(invoicing_dir, config)` function

## API Endpoints (Phase 2)

### Invoice endpoints
- `POST /api/invoices/{member_id}/generate` — generate single PDF via Makefile
- `POST /api/invoices/batch` — batch generate all PDFs as background task
- `GET /api/invoices/batch/{job_id}/status` — poll batch progress
- `GET /api/invoices/{member_id}/download` — serve the generated PDF file
- `GET /api/invoices/{member_id}/preview` — render Jinja2 to HTML (Python direct)

### Email endpoints
- `POST /api/emails/{member_id}/send` — send single email via Makefile
- `POST /api/emails/batch` — batch send all emails as background task
- `GET /api/emails/batch/{job_id}/status` — poll batch progress

## Key Technical Notes

### Makefile working directory
The Makefile must run in `invoicing/<formSlug>/` directory. It expects:
- `*.json` files (member data)
- `conf.json` symlink (for SMTP credentials via jq)
- `Makefile` symlink (to `../Makefile`)
- `signature.png` symlink (for invoice footer)
- `../.venv/` directory (created by Makefile on first run)

### Member ID mapping
- `member_id` in API URLs = HelloAsso item `id` field
- To find the JSON file: scan `invoicing/<formSlug>/` for files containing `_<id>.json`
- The filename format is: `firstname_lastname_orderdate_id.json`

### Subprocess error handling
- `subprocess.run()` with `check=True` — raises CalledProcessError on failure
- Capture stdout/stderr for error reporting
- For batch: log errors per member, continue processing rest

### Preview template variables
The Jinja2 template expects these top-level variables from the JSON item:
- `id`, `name`, `amount`, `user` (dict), `order` (dict), `options` (list), `payer` (dict)
- Plus injected: `date` (dd/mm/YYYY), `signature` (file path)

## What NOT to Build in Phase 2
- No Svelte frontend (Phase 3)
- No Docker production setup (Phase 3)
- No custom template editor
- No smtplib migration (keep sendemail via Makefile)
- No WeasyPrint Python-native integration (keep Makefile pipeline)

## New Files Expected
```
lib/invoicing.py          # ensure_symlinks(), run_make_pdf(), run_make_email()
app/routes/invoices.py    # Invoice generation, download, preview, batch
app/routes/emails.py      # Email sending, batch
tests/test_invoicing.py   # lib/invoicing.py tests
tests/test_api_invoices.py  # Invoice endpoint tests
tests/test_api_emails.py  # Email endpoint tests
```
