# Phase 1 Context: Shared Library & API Foundation

## Locked Decisions

### D1: Backend Framework — FastAPI
- FastAPI with Uvicorn for development, Gunicorn+UvicornWorker for production
- Auto-generated Swagger UI for testing
- BackgroundTasks for batch operations (Phase 2)

### D2: Code Structure — `lib/` directory
```
helloasso.py          # CLI entry point (refactored to import from lib/)
lib/
  __init__.py
  helloasso_client.py # HelloAsso API wrapper (auth, data fetching, pagination, filters)
  config.py           # Load and parse conf.json
  filesystem.py       # Read/write JSON files, scan for .pdf/.mail.log status
app/
  __init__.py
  main.py             # FastAPI app creation
  routes/
    __init__.py
    auth.py           # POST /api/auth/login, /logout
    members.py        # GET /api/members, /api/members/{id}, /api/members/export/csv
    campaigns.py      # POST /api/campaigns/refresh
    summary.py        # GET /api/summary
    health.py         # GET /api/health
```

### D3: HTTP Client — Keep `requests` (sync)
- Shared library uses `requests` (same as current CLI)
- FastAPI routes call lib functions via `asyncio.to_thread()` to avoid blocking
- No migration to httpx — minimizes regression risk
- Token refresh logic added to `lib/helloasso_client.py` (store refresh_token, auto-refresh on 401)

### D4: Authentication — Single shared password
- Environment variable: `DASHBOARD_PASSWORD=<secret>`
- No username concept — just a password to access the dashboard
- Session-based (secure cookie after login)
- If `DASHBOARD_PASSWORD` is not set, dashboard is unauthenticated (development mode)

### D5: File Paths — Same as CLI
- Web reads `CONF_PATH` env var (default: `conf.json`) to find the config file
- Data directory derived from conf.json location (same as CLI: `conf["dir"]`)
- JSON member files in `invoicing/<formSlug>/` relative to conf.json directory
- Status derived from filesystem:
  - `*.json` exists → member data dumped
  - `*.pdf` exists → invoice generated
  - `*.mail.log` exists → email sent

### D6: Single Season
- formSlug comes from conf.json `conf.helloasso.formSlug`
- No multi-season selector in Phase 1
- To change season: update conf.json (same as CLI workflow)

## What NOT to Build in Phase 1
- No database (SQLite or other)
- No email sending (Phase 2)
- No PDF generation (Phase 2)
- No Svelte frontend (Phase 3)
- No Docker production setup (Phase 3)
- No multi-season support
- No user management (single password)

## Key Technical Notes

### Token Refresh Pattern
Current code authenticates once per `HelloAsso.__init__()`. Must change to:
1. Store both `access_token` and `refresh_token` from initial auth
2. On 401 response: use `refresh_token` to get new tokens
3. Update stored tokens after refresh
4. If refresh fails: re-authenticate with client_credentials

### Member Data Flow (API)
1. `POST /api/campaigns/refresh` → calls `lib/helloasso_client.py` to fetch from HelloAsso API → dumps JSON files to `invoicing/<formSlug>/`
2. `GET /api/members` → calls `lib/filesystem.py` to scan JSON files → parses and returns member list with filters
3. Status fields (invoice_generated, email_sent) computed by checking `.pdf` and `.mail.log` file existence

### CLI Compatibility Contract
After refactoring, `helloasso.py` must produce **byte-identical** output for all existing command-line flags:
- `-m txt/csv/json` — member display
- `-s min/member/pattern` — summary display
- `-d` / `--dump` — JSON file dump
- All filter flags: `-r`, `-e`, `-u`, `-f`, `-t`, `-a`

## Dependencies on Existing Code
- `helloasso.py` — refactor into lib/ + CLI wrapper
- `conf.json` format — preserved exactly
- `invoicing/<formSlug>/` directory structure — preserved exactly
