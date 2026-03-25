# Phase 1 Plan: Shared Library & API Foundation

## Goal
Extract shared library from `helloasso.py`, build FastAPI backend with auth, reading/writing the same flat JSON files as the CLI.

## Methodology: Test-Driven Development
Following the [TDD skill](https://github.com/bbinet/skills/tree/bbinet/tdd):
- **Vertical slices**: RED (write one failing test) → GREEN (minimal code to pass) → repeat
- **No horizontal slicing**: never write all tests first then all code
- **Test behavior, not implementation**: tests use public interfaces only
- **Mock at system boundaries only**: HelloAsso API (HTTP calls), filesystem (for fixtures)
- **Integration-style tests**: FastAPI TestClient for API endpoints, real lib/ calls for unit tests

## Test Infrastructure
- **Framework**: pytest
- **API testing**: `fastapi.testclient.TestClient`
- **HTTP mocking**: `unittest.mock.patch` on `requests.post`/`requests.get` (system boundary)
- **Filesystem**: `tmp_path` pytest fixture for isolated file operations
- **Structure**: `tests/` directory at project root
  ```
  tests/
    __init__.py
    conftest.py          # Shared fixtures (sample HelloAsso items, config dicts)
    test_config.py       # lib/config.py tests
    test_models.py       # lib/models.py tests
    test_filesystem.py   # lib/filesystem.py tests
    test_helloasso_client.py  # lib/helloasso_client.py tests (token refresh)
    test_api_auth.py     # Auth endpoints
    test_api_members.py  # Members endpoints
    test_api_campaigns.py # Campaigns endpoints
    test_api_summary.py  # Summary endpoint
  ```

## Success Criteria
1. CLI `helloasso.py` works identically after refactor (all flags, all output formats)
2. All API endpoints return correct data from JSON files
3. HelloAsso token refreshes automatically (refresh_token flow)
4. Auth blocks unauthenticated access (DASHBOARD_PASSWORD env var)
5. `POST /api/campaigns/refresh` creates same JSON files as CLI `--dump`
6. **All tests pass (`pytest` green)**

---

## Wave 1: Extract Shared Library (TDD)

### Task 1.0: Test infrastructure + fixtures
**Files:** `tests/__init__.py`, `tests/conftest.py`, `requirements-dev.txt`
**What:**
- Create `tests/__init__.py` (empty)
- Create `tests/conftest.py` with shared fixtures:
  - `sample_helloasso_item` — a realistic HelloAsso API item dict (with user, payer, order, customFields, options, payments)
  - `sample_config` — a minimal conf.json dict with HelloAsso + sendemail sections
  - `config_file` — writes sample_config to a tmp_path file, returns path
- Create `requirements-dev.txt`: `pytest`, `httpx` (for FastAPI TestClient)

### Task 1.1: `lib/config.py` — Config loading (TDD)
**Files:** `tests/test_config.py`, `lib/__init__.py`, `lib/config.py`
**TDD cycles:**
1. RED: test `load_config` returns config with `credentials` and `conf` keys → GREEN: implement
2. RED: test `load_config` injects `conf["dir"]` as directory of config file → GREEN: implement
3. RED: test `conf_get` navigates nested keys → GREEN: implement
4. RED: test `conf_get` returns last valid value on missing key → GREEN: implement

### Task 1.2: `lib/helloasso_client.py` — API wrapper (extract only)
**Files:** `lib/helloasso_client.py`
**What:**
- Extract `HelloAsso` class from `helloasso.py` (no tests yet — token refresh tested in Wave 2)
- Class takes config dict in `__init__` (not config_path)
- Keep `Authenticate()` and `GetData()` as-is
- Keep `requests` as HTTP client
- Move `strip_accents_ponct()` here temporarily (moves to models.py in Task 1.3)

**No tests for GetData/Authenticate here** — these hit external API (system boundary). Token refresh tested in Wave 2 with mocked HTTP.

### Task 1.3: `lib/models.py` — Member data transformation (TDD)
**Files:** `tests/test_models.py`, `lib/models.py`
**TDD cycles:**
1. RED: test `parse_member` extracts firstname/lastname/email/ea from item → GREEN: implement
2. RED: test `parse_member` extracts company/phone from customFields → GREEN: implement
3. RED: test `parse_member` filters out "oubliez pas" activities → GREEN: implement
4. RED: test `get_member_filename` produces normalized filename (accents stripped, spaces removed) → GREEN: implement
5. RED: test `build_summary` groups members by activity sorted by count desc → GREEN: implement
6. RED: test `build_summary` puts members with no activity in "[Aucune activité]" → GREEN: implement

Move `strip_accents_ponct()` from helloasso_client.py to models.py (used by `get_member_filename`).

### Task 1.4: `lib/filesystem.py` — File operations (TDD)
**Files:** `tests/test_filesystem.py`, `lib/filesystem.py`
**TDD cycles (using `tmp_path` fixture):**
1. RED: test `get_invoicing_dir` returns correct path from config → GREEN: implement
2. RED: test `get_member_filepath` combines invoicing dir + filename → GREEN: implement
3. RED: test `dump_item` writes JSON file with correct content → GREEN: implement
4. RED: test `scan_members` reads all .json files from directory (excluding conf.json) → GREEN: implement
5. RED: test `get_member_status` returns `{invoice_generated: True}` when .pdf exists → GREEN: implement
6. RED: test `get_member_status` returns `{email_sent: True}` when .mail.log exists → GREEN: implement
7. RED: test `get_member_status` returns both False when neither exists → GREEN: implement

### Task 1.5: Refactor `helloasso.py` to use `lib/`
**Files:** `helloasso.py`
**Depends on:** Tasks 1.1, 1.2, 1.3, 1.4
**What:**
- Replace inline classes/functions with imports from `lib/`
- Keep ALL argparse, display logic, and main loop in `helloasso.py`
- Run `pytest` to verify all lib/ tests still pass

**Critical:** Output must be byte-identical for all command combinations.

**Commit:** "Refactor: extract shared library from helloasso.py with TDD tests"

---

## Wave 2: Token Refresh (TDD)

### Task 2.1: Token refresh for HelloAsso client (TDD)
**Files:** `tests/test_helloasso_client.py`, `lib/helloasso_client.py`
**TDD cycles (mock `requests.post` and `requests.get` — system boundary):**
1. RED: test `Authenticate` stores both access_token and refresh_token → GREEN: implement
2. RED: test `_request` returns response on success (200) → GREEN: implement
3. RED: test `_request` refreshes token on 401, retries, succeeds → GREEN: implement
4. RED: test `_request` falls back to full re-auth if refresh fails → GREEN: implement

**Mocking pattern:** `@patch('lib.helloasso_client.requests.get')` and `@patch('lib.helloasso_client.requests.post')` — we mock at the system boundary (HTTP calls), not internal methods.

**Commit:** "Add OAuth2 token refresh to HelloAsso client"

---

## Wave 3a: FastAPI Skeleton & Auth (TDD)

### Task 3.1: FastAPI app skeleton + requirements
**Files:** `app/__init__.py`, `app/main.py`, `app/routes/__init__.py`, `requirements.txt`
**What:**
- Create FastAPI app with title "ACS HelloAsso Dashboard"
- Load config on startup via `CONF_PATH` env var
- Include all route modules, CORS middleware
- `requirements.txt`: requests, fastapi, uvicorn[standard], python-multipart, itsdangerous

### Task 3.2: Auth + Health routes (TDD)
**Files:** `tests/test_api_auth.py`, `app/routes/auth.py`, `app/routes/health.py`
**TDD cycles (via FastAPI TestClient):**
1. RED: test health returns 200 `{"status": "ok"}` → GREEN: implement health route
2. RED: test login with correct password returns 200 → GREEN: implement login
3. RED: test login with wrong password returns 401 → GREEN: implement validation
4. RED: test protected route without auth returns 401 → GREEN: implement `require_auth` dependency
5. RED: test protected route after login returns 200 → GREEN: wire auth cookie
6. RED: test logout clears session → GREEN: implement logout
7. RED: test no DASHBOARD_PASSWORD set = dev mode (no auth required) → GREEN: implement

**Commit:** "Add FastAPI skeleton with auth and health routes"

---

## Wave 3b: API Routes (TDD)

### Task 3.3: Members routes (TDD)
**Files:** `tests/test_api_members.py`, `app/routes/members.py`
**Setup:** Test fixtures create JSON member files in tmp_path, configure app to use that directory.
**TDD cycles:**
1. RED: test `GET /api/members` returns list of members from JSON files → GREEN: implement
2. RED: test `GET /api/members` includes status fields (invoice_generated, email_sent) → GREEN: implement
3. RED: test `GET /api/members?activity=football` filters by activity → GREEN: implement
4. RED: test `GET /api/members?refund_filtered=true` excludes refunded → GREEN: implement
5. RED: test `GET /api/members/{id}` returns single member → GREEN: implement
6. RED: test `GET /api/members/{id}` returns 404 for unknown id → GREEN: implement
7. RED: test `GET /api/members/export/csv` returns valid CSV with correct headers → GREEN: implement

### Task 3.4: Campaigns route (TDD)
**Files:** `tests/test_api_campaigns.py`, `app/routes/campaigns.py`
**TDD cycles:**
1. RED: test `GET /api/campaigns` returns formSlug/formType/organizationName from config → GREEN: implement
2. RED: test `POST /api/campaigns/refresh` creates JSON files (mock HelloAsso API) → GREEN: implement

### Task 3.5: Summary route (TDD)
**Files:** `tests/test_api_summary.py`, `app/routes/summary.py`
**TDD cycles:**
1. RED: test `GET /api/summary` returns activity breakdown from JSON files → GREEN: implement
2. RED: test summary total matches member count → GREEN: implement

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

### Task 4.2: Update .gitignore
**Files:** `.gitignore`
**What:**
- Add `__pycache__/`, `*.pyc`, `.venv/`
- Keep existing entries

**Commit:** "Add development setup (docker-compose, gitignore updates)"

---

## Verification Checklist
After all waves:

### Tests
- [ ] `pytest` runs green (all tests pass)
- [ ] Tests cover: config, models, filesystem, token refresh, auth, members, campaigns, summary

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
| `app/routes/auth.py` | Login/logout/auth check + require_auth dependency |
| `app/routes/health.py` | Health check |
| `app/routes/members.py` | Member listing, detail, CSV export |
| `app/routes/campaigns.py` | Campaign info + HelloAsso data refresh |
| `app/routes/summary.py` | Activity summary |
| `tests/__init__.py` | Package marker |
| `tests/conftest.py` | Shared test fixtures |
| `tests/test_config.py` | Config loading tests |
| `tests/test_models.py` | Member transformation tests |
| `tests/test_filesystem.py` | File operations tests |
| `tests/test_helloasso_client.py` | Token refresh tests |
| `tests/test_api_auth.py` | Auth endpoint tests |
| `tests/test_api_members.py` | Members endpoint tests |
| `tests/test_api_campaigns.py` | Campaigns endpoint tests |
| `tests/test_api_summary.py` | Summary endpoint tests |
| `requirements.txt` | Production Python dependencies |
| `requirements-dev.txt` | Test dependencies (pytest, httpx) |
| `docker-compose.yml` | Development setup |

### Modified Files
| File | Change |
|------|--------|
| `helloasso.py` | Refactored to import from `lib/` (same behavior) |
| `.gitignore` | Add Python cache entries |
