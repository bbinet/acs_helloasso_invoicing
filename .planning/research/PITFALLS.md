# Domain Pitfalls

**Domain:** Association management / invoicing web dashboard
**Researched:** 2026-03-25

## Critical Pitfalls

Mistakes that cause rewrites or major issues.

### Pitfall 1: Blocking the Event Loop with WeasyPrint
**What goes wrong:** WeasyPrint is a pure-Python CSS layout engine. It is synchronous and CPU-bound. Calling it directly in a FastAPI async route handler blocks the entire event loop, making ALL concurrent requests hang until the PDF is generated.
**Why it happens:** Developers treat WeasyPrint like a quick function call, but generating a single PDF can take 1-3 seconds. Batch generation for 200 members = 200-600 seconds of blocking.
**Consequences:** Dashboard becomes unresponsive during invoice generation. Other users cannot load pages. Requests time out.
**Prevention:** Always run WeasyPrint via `asyncio.to_thread()` for single PDFs. Use `BackgroundTasks` for batch operations. Never call WeasyPrint in the request-response cycle for batches.
**Detection:** Dashboard freezes when anyone clicks "Generate Invoice."

### Pitfall 2: WeasyPrint Memory Accumulation
**What goes wrong:** WeasyPrint has a known issue where memory from previous PDF generation calls accumulates and is not fully released. In a long-running web server process, this can lead to steadily growing memory usage.
**Why it happens:** Internal caching of fonts, CSS, and layout objects within the WeasyPrint library that are not garbage-collected between calls.
**Consequences:** Server runs out of memory over time, especially during batch operations (200+ PDFs in sequence).
**Prevention:** Monitor memory usage. For batch operations, consider generating PDFs in a subprocess (via `multiprocessing`) rather than in the main server process. Alternatively, restart the worker after batch jobs. Set memory limits in Docker.
**Detection:** Docker container OOM-killed after batch generation. Gradually increasing memory usage in monitoring.

### Pitfall 3: HelloAsso OAuth2 Token Expiry Mid-Batch
**What goes wrong:** The HelloAsso OAuth2 token expires (typically 30 minutes) during a long-running batch operation. Subsequent API calls fail with 401.
**Why it happens:** The existing code authenticates once at init and never refreshes. This works for CLI (short-lived), but not for a long-running server.
**Consequences:** Batch data fetch fails partway through. Incomplete member lists. Silent data loss if errors are swallowed.
**Prevention:** Implement token refresh logic: catch 401 responses, re-authenticate, retry the request. The `helloasso-apiv5` legacy SDK does this automatically -- study its approach. Store token expiry time and proactively refresh before expiry.
**Detection:** 401 errors in logs after the server has been running for a while.

## Moderate Pitfalls

### Pitfall 4: Sendemail CLI Dependency in Docker
**What goes wrong:** The existing Dockerfile installs `sendemail` (Perl-based) and its SSL dependencies. If email sending is migrated to Python `smtplib` but the old Makefile pipeline is kept as a fallback, you end up with two email paths and confusion about which is canonical.
**Prevention:** Fully remove `sendemail` from the Dockerfile once the Python email service is tested. Don't maintain two email paths. Clean break.

### Pitfall 5: SMTP Credentials Exposure
**What goes wrong:** SMTP credentials (currently in `conf.json`) are accidentally committed to git, logged in debug output, or exposed in error messages.
**Prevention:** Use environment variables for credentials (not JSON config file). Use Pydantic `SecretStr` for sensitive fields. Never log credential values. Use Docker secrets in production.

### Pitfall 6: SQLite Concurrent Write Conflicts
**What goes wrong:** Multiple simultaneous write operations to SQLite fail because SQLite uses file-level locking. This can happen when batch invoice generation and a user action both try to write to the database.
**Prevention:** Enable WAL (Write-Ahead Logging) mode on the SQLite connection: `PRAGMA journal_mode=WAL`. Use a single database session per request (FastAPI dependency injection pattern). For batch writes, use transactions.

### Pitfall 7: React Router 404s on Direct URL Access
**What goes wrong:** User bookmarks `/dashboard/members`, refreshes the page, and gets a 404 because FastAPI tries to find a route matching `/dashboard/members` instead of serving the React SPA.
**Prevention:** Add a catch-all route AFTER all API routes that serves `index.html` for any non-API, non-static path. API routes must be under `/api/` prefix to avoid conflicts.

### Pitfall 8: HelloAsso API Pagination Missed Data
**What goes wrong:** The existing code handles pagination via `continuationToken`, but breaks out of the loop when `data` is empty or missing. If the API returns an empty page mid-sequence (transient issue), members are lost.
**Prevention:** Check for `continuationToken` being `null` or missing as the termination condition, not empty data. Add logging for pagination steps to detect anomalies.

## Minor Pitfalls

### Pitfall 9: WeasyPrint CSS File Resolution
**What goes wrong:** The Jinja2 template references `style.css` and `logo.svg` with relative paths. When rendered in a web server context (not from the filesystem via Makefile), WeasyPrint cannot resolve these paths.
**Prevention:** Pass `base_url` parameter to WeasyPrint's `HTML()` constructor pointing to the templates directory. Or embed CSS inline / use absolute file paths.

### Pitfall 10: French Characters in Email Subjects
**What goes wrong:** Email subject "Facture adhesion ACS" loses accents or breaks encoding.
**Prevention:** Use `EmailMessage` (modern API) which handles UTF-8 encoding correctly by default. Always set `charset='utf-8'`. Test with accented characters: "Facture adhesion a l'ACS".

### Pitfall 11: Timezone Issues in Dates
**What goes wrong:** HelloAsso API returns dates in ISO format with timezone. Invoice dates displayed inconsistently or compared incorrectly.
**Prevention:** Parse all dates with timezone awareness. Display in French locale format (`dd/mm/YYYY`). The existing template already does date formatting -- preserve that logic.

### Pitfall 12: Vite Build Output Path Mismatch
**What goes wrong:** FastAPI expects React build in `frontend/dist/` but Vite outputs to a different path, or asset paths use wrong base URL.
**Prevention:** Set `base: '/'` in `vite.config.ts`. Verify `outDir` matches what FastAPI mounts. Test the full build -> serve cycle early.

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| API Foundation (Phase 1) | Token expiry (#3) | Implement refresh logic from day one |
| API Foundation (Phase 1) | SQLite concurrency (#6) | Enable WAL mode in database setup |
| Invoice Pipeline (Phase 2) | Event loop blocking (#1) | Use `asyncio.to_thread()` + BackgroundTasks |
| Invoice Pipeline (Phase 2) | Memory accumulation (#2) | Add memory monitoring, consider subprocess for batches |
| Invoice Pipeline (Phase 2) | CSS path resolution (#9) | Set `base_url` in WeasyPrint HTML constructor |
| Email Migration (Phase 2) | Credential exposure (#5) | Use env vars + Pydantic SecretStr |
| Email Migration (Phase 2) | French encoding (#10) | Use modern EmailMessage API with UTF-8 |
| React Dashboard (Phase 3) | SPA 404s (#7) | Catch-all route after API routes |
| React Dashboard (Phase 3) | Vite build paths (#12) | Configure `base` and test build early |

## Sources

- [WeasyPrint Memory Issue #1104](https://github.com/Kozea/WeasyPrint/issues/1104)
- [WeasyPrint Performance Issue #545](https://github.com/Kozea/WeasyPrint/issues/545)
- [WeasyPrint Common Use Cases](https://doc.courtbouillon.org/weasyprint/stable/common_use_cases.html)
- [FastAPI HTTP Basic Auth](https://fastapi.tiangolo.com/advanced/security/http-basic-auth/)
- [SQLite WAL Mode](https://www.sqlite.org/wal.html)
- [Python email.message documentation](https://docs.python.org/3/library/email.message.html)
