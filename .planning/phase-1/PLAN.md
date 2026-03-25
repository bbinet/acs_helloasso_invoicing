# Phase 1 Plan: Shared Library & API Foundation

## Goal
Extract shared library from `helloasso.py`, build FastAPI backend with auth, reading/writing the same flat JSON files as the CLI.

## Success Criteria
1. CLI `helloasso.py` works identically after refactor (all flags, all output formats)
2. All API endpoints return correct data from JSON files
3. HelloAsso token refreshes automatically (refresh_token flow)
4. Auth blocks unauthenticated access (DASHBOARD_PASSWORD env var)
5. `POST /api/campaigns/refresh` creates same JSON files as CLI `--dump`

---

## Wave 1: Extract Shared Library (no behavior change)

### Task 1.1: Create `lib/config.py` — Config loading
**Files:** `lib/__init__.py`, `lib/config.py`
**What:**
- Create `lib/__init__.py` (empty)
- Create `lib/config.py` with a `load_config(config_path)` function that:
  - Reads and parses conf.json
  - Sets `conf["dir"]` to the directory of the config file (same as current `__init__`)
  - Returns the full config dict (with `credentials`, `conf` keys)
- Also include `conf_get(conf, *keys)` function (extracted from `HelloAsso.ConfGet`)

**Acceptance:** `load_config("conf.json")` returns same structure as current `json.load()` + dir injection.

### Task 1.2: Create `lib/helloasso_client.py` — API wrapper
**Files:** `lib/helloasso_client.py`
**What:**
- Extract `HelloAsso` class from `helloasso.py` into `lib/helloasso_client.py`
- Class takes config dict in `__init__` (not config_path — config loading is separate)
- Keep `Authenticate()` and `GetData()` methods exactly as-is for now
- Keep `requests` as HTTP client
- Import `requests` at module level
- Add `strip_accents_ponct()` helper function (used by CLI for filename generation)

**Key detail:** The class interface changes from `HelloAsso(config_path)` to `HelloAsso(config)` where config is the dict returned by `load_config()`. This separates config loading from API client creation.

**Acceptance:** `HelloAsso(config).GetData(...)` yields same items as current code.

### Task 1.3: Create `lib/models.py` — Member data transformation
**Files:** `lib/models.py`
**What:**
- `parse_member(item)` — extracts member dict from raw HelloAsso item (same logic as CLI lines 131-148):
  - `ea`, `firstname`, `lastname`, `email`, `activities` from item fields
  - `company`, `phone` from `customFields`
  - Filters out "oubliez pas" from activities
- `build_summary(members)` — builds activity breakdown from list of (item, member) tuples:
  - Groups members by activity (same logic as CLI lines 143-148)
  - Returns sorted list of `{"name": activity, "count": N, "members": [...]}`
- `get_member_filename(item)` — computes the JSON filename from item data (firstname_lastname_orderdate_id.json, same as CLI lines 125-128)
  - Uses `strip_accents_ponct()` for filename normalization

**Acceptance:** `parse_member(item)` returns same dict as CLI builds inline. `build_summary()` produces same grouping as CLI `-s member`.

### Task 1.4: Create `lib/filesystem.py` — File operations
**Files:** `lib/filesystem.py`
**What:**
- `get_invoicing_dir(conf)` — returns `os.path.join(conf_get(conf, 'dir'), 'invoicing', conf_get(conf, 'helloasso', 'formSlug'))`
- `get_member_filepath(conf, item)` — uses `get_member_filename(item)` from models.py + `get_invoicing_dir(conf)` to build full path
- `dump_item(filepath, item)` — write JSON file (same as CLI lines 178-181)
- `scan_members(invoicing_dir)` — list all `.json` files (excluding `conf.json`), parse each, return list of raw item dicts
- `get_member_status(json_filepath)` — check if corresponding `.pdf` and `.mail.log` exist, return `{"invoice_generated": bool, "email_sent": bool}`

**Acceptance:** `get_member_filepath()` produces same filenames as current CLI. `dump_item()` creates same JSON files.

### Task 1.5: Refactor `helloasso.py` to use `lib/`
**Files:** `helloasso.py`
**Depends on:** Tasks 1.1, 1.2, 1.3, 1.4
**What:**
- Replace inline `HelloAsso` class with `from lib.helloasso_client import HelloAsso`
- Replace inline config loading with `from lib.config import load_config, conf_get`
- Replace inline `strip_accents_ponct` with `from lib.models import strip_accents_ponct`
- Replace inline member data transformation with `from lib.models import parse_member, get_member_filename, build_summary`
- Replace inline file path computation with `from lib.filesystem import get_invoicing_dir, get_member_filepath, dump_item`
- Keep ALL argparse, display logic, and main loop in `helloasso.py` (this is CLI-specific)
- The `if __name__ == '__main__':` block stays, using imported functions for data transformation

**Critical:** Output must be byte-identical for all command combinations. The refactor is purely structural.

**Acceptance:** Running `helloasso.py` with any combination of flags produces identical output to the original.

**Commit:** After Wave 1, commit with message "Refactor: extract shared library from helloasso.py"

---

## Wave 2: Token Refresh

### Task 2.1: Add OAuth2 token refresh to `lib/helloasso_client.py`
**Files:** `lib/helloasso_client.py`
**What:**
- Modify `Authenticate()` to store both `access_token` AND `refresh_token` from response
- Add `RefreshToken()` method:
  - POST to `/oauth2/token` with `grant_type=refresh_token` + `client_id` + `refresh_token`
  - Returns new `access_token` and `refresh_token`
  - Updates stored tokens
- Add `_request(method, url, **kwargs)` wrapper method:
  - Makes the HTTP request
  - On 401 response: calls `RefreshToken()`, retries once
  - If refresh fails: calls `Authenticate()` (full re-auth), retries once
  - Raises on other errors
- Update `GetData()` to use `self._request('get', url, params=payload)` instead of `requests.get()`

**Acceptance:** Token refresh works transparently. If access_token expires mid-pagination, data fetching continues.

**Commit:** "Add OAuth2 token refresh to HelloAsso client"

---

## Wave 3a: FastAPI Skeleton & Auth

### Task 3.1: Create FastAPI app skeleton + requirements.txt
**Files:** `app/__init__.py`, `app/main.py`, `app/routes/__init__.py`, `requirements.txt`
**What:**
- Create `app/__init__.py` (empty)
- Create `app/routes/__init__.py` (empty)
- Create `app/main.py`:
  - FastAPI app with title "ACS HelloAsso Dashboard"
  - Load config on startup: `config = load_config(os.environ.get('CONF_PATH', 'conf.json'))`
  - Store config in `app.state.config`
  - Include all route modules
  - CORS middleware (allow all origins in dev)
- Create `requirements.txt`:
  ```
  requests
  fastapi
  uvicorn[standard]
  python-multipart
  ```

**Acceptance:** `uvicorn app.main:app --reload` starts and shows Swagger UI at `/docs`.

### Task 3.2: Create auth routes
**Files:** `app/routes/auth.py`
**What:**
- Read `DASHBOARD_PASSWORD` from env var
- `POST /api/auth/login` — accepts JSON `{"password": "xxx"}`, sets session cookie if correct
- `POST /api/auth/logout` — clears session cookie
- `GET /api/auth/check` — returns 200 if authenticated, 401 if not
- Auth dependency function `require_auth(request)` that checks session cookie
- If `DASHBOARD_PASSWORD` is not set: all requests pass auth (dev mode)
- Session via signed cookies (FastAPI `Starlette` SessionMiddleware with a secret key)

**Acceptance:** Login with correct password sets cookie. Protected routes reject without cookie.

### Task 3.3: Create health route
**Files:** `app/routes/health.py`
**What:**
- `GET /api/health` — returns `{"status": "ok"}` (no auth required)

**Commit:** "Add FastAPI skeleton with auth and health routes"

---

## Wave 3b: API Routes (members, campaigns, summary)

### Task 3.4: Create members routes
**Files:** `app/routes/members.py`
**What:**
- `GET /api/members` — protected by auth
  - Reads JSON files from `invoicing/<formSlug>/` via `lib/filesystem.scan_members()`
  - Transforms each raw item to member dict via `lib/models.parse_member()`
  - Adds status via `lib/filesystem.get_member_status()`
  - Query params for filtering: `activity`, `user`, `from_date`, `to_date`, `refund_filtered`, `ea_filter`
  - Filtering applied in Python after loading (same logic as CLI)
  - Each member includes status: `{invoice_generated: bool, email_sent: bool}`
  - Returns JSON array of member objects
- `GET /api/members/{member_id}` — returns single member by HelloAsso item ID
- `GET /api/members/export/csv` — returns CSV file (same format as CLI `-m csv`)

**Key:** Filters are applied by parsing JSON files and filtering in Python, same as CLI does. No API call to HelloAsso for listing — data comes from dumped files.

**Acceptance:** `/api/members` returns same members as `helloasso.py -m json` (after dump).

### Task 3.5: Create campaigns route
**Files:** `app/routes/campaigns.py`
**What:**
- `GET /api/campaigns` — protected by auth
  - Returns current campaign info: `{"formSlug": "...", "formType": "...", "organizationName": "..."}`
  - Reads from config
- `POST /api/campaigns/refresh` — protected by auth
  - Creates `HelloAsso(config)` instance
  - Calls `GetData()` with no filters
  - Dumps each item to JSON file via `lib/filesystem.dump_item()`
  - Returns `{"count": N, "formSlug": "..."}` with number of members dumped
  - Runs in `asyncio.to_thread()` (sync requests + file I/O)

**Acceptance:** After calling refresh, `invoicing/<formSlug>/` contains same JSON files as CLI `--dump`.

### Task 3.6: Create summary route
**Files:** `app/routes/summary.py`
**What:**
- `GET /api/summary` — protected by auth
  - Reads JSON files via `lib/filesystem.scan_members()`
  - Transforms via `lib/models.parse_member()` for each item
  - Computes activity breakdown via `lib/models.build_summary()`
  - Returns `{"activities": [{"name": "...", "count": N, "members": [...]}], "total": N}`

**Acceptance:** Activity breakdown matches CLI `-s member` output.

**Commit:** "Add members, campaigns, and summary API routes"

---

## Wave 4: Development Setup

### Task 4.1: Create development docker-compose.yml
**Files:** `docker-compose.yml`
**What:**
```yaml
version: "3.8"
services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    environment:
      - CONF_PATH=/app/conf.json
      - DASHBOARD_PASSWORD=dev
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- Uses existing Dockerfile base or a simple python:3.11 image
- Mounts project directory for hot reload
- Sets CONF_PATH and DASHBOARD_PASSWORD

### Task 4.2: Update .gitignore
**Files:** `.gitignore`
**What:**
- Add `__pycache__/`, `*.pyc`, `.venv/`
- Keep existing entries

**Commit:** "Add development setup (docker-compose, gitignore updates)"

---

## Verification Checklist
After all waves:

### CLI backward compatibility
- [ ] `python3 helloasso.py --help` shows same help text
- [ ] `python3 helloasso.py conf.json -m txt` produces same output as before refactor
- [ ] `python3 helloasso.py conf.json -m csv` produces same output
- [ ] `python3 helloasso.py conf.json -s min -r` produces same output
- [ ] `python3 helloasso.py conf.json -s member` produces same output
- [ ] `python3 helloasso.py conf.json --dump` creates same files

### API server
- [ ] `uvicorn app.main:app` starts without error
- [ ] `GET /docs` shows Swagger UI
- [ ] `GET /api/health` returns 200

### Auth
- [ ] `POST /api/auth/login` with wrong password returns 401
- [ ] `POST /api/auth/login` with correct password returns 200 + cookie
- [ ] `POST /api/auth/logout` clears session
- [ ] `GET /api/auth/check` returns 200 when authenticated, 401 when not
- [ ] `GET /api/members` without auth returns 401

### API endpoints
- [ ] `GET /api/members` with auth returns member list from JSON files
- [ ] `GET /api/members?activity=football` returns filtered list
- [ ] `GET /api/members/{id}` returns single member
- [ ] `GET /api/members/export/csv` returns valid CSV
- [ ] `GET /api/campaigns` returns current campaign info
- [ ] `POST /api/campaigns/refresh` fetches from HelloAsso and dumps files
- [ ] `GET /api/summary` returns activity breakdown matching CLI

## File Inventory

### New Files
| File | Purpose |
|------|---------|
| `lib/__init__.py` | Package marker |
| `lib/config.py` | Config loading from conf.json |
| `lib/helloasso_client.py` | HelloAsso API wrapper (extracted from helloasso.py) |
| `lib/models.py` | Member data transformation, summary building |
| `lib/filesystem.py` | File operations (JSON read/write, status scanning) |
| `app/__init__.py` | Package marker |
| `app/main.py` | FastAPI app creation and startup |
| `app/routes/__init__.py` | Package marker |
| `app/routes/auth.py` | Login/logout/auth check |
| `app/routes/health.py` | Health check |
| `app/routes/members.py` | Member listing, detail, CSV export |
| `app/routes/campaigns.py` | Campaign info + HelloAsso data refresh |
| `app/routes/summary.py` | Activity summary |
| `requirements.txt` | Python dependencies |
| `docker-compose.yml` | Development setup |

### Modified Files
| File | Change |
|------|--------|
| `helloasso.py` | Refactored to import from `lib/` (same behavior) |
| `.gitignore` | Add Python cache entries |
