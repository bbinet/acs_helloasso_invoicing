# Architecture Patterns

**Domain:** Association management / invoicing web dashboard
**Researched:** 2026-03-25

## Recommended Architecture

Single-container FastAPI application serving both the API and the React SPA.

```
[Browser]
    |
    v
[FastAPI (Uvicorn)]
    |
    +-- /api/*          --> API routes (JSON)
    |     |
    |     +-- HelloAssoService (wraps HelloAsso API V5)
    |     +-- InvoiceService (Jinja2 + WeasyPrint)
    |     +-- EmailService (smtplib)
    |     +-- SQLite DB (member cache, invoice tracking)
    |
    +-- /static/*       --> React built assets (JS, CSS, images)
    +-- /*              --> React index.html (SPA catch-all)
```

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| **API Routes** (`app/routes/`) | HTTP request handling, validation, response formatting | Services (via dependency injection) |
| **HelloAssoService** (`app/services/helloasso.py`) | OAuth2 auth, member data fetching, pagination, filtering | HelloAsso API V5 (via httpx) |
| **InvoiceService** (`app/services/invoice.py`) | Jinja2 template rendering, WeasyPrint PDF generation | Filesystem (templates, output PDFs) |
| **EmailService** (`app/services/email.py`) | SMTP connection, email construction, attachment handling | SMTP server (Gmail etc.) |
| **Database Models** (`app/models/`) | SQLModel definitions for Member, Invoice, EmailLog | SQLite via SQLModel |
| **Config** (`app/config.py`) | Load and validate conf.json, env vars | Filesystem, environment |
| **Auth** (`app/auth.py`) | Session management, login/logout | Database (user store) |

### Data Flow

**Member listing:**
1. User opens dashboard -> React fetches `GET /api/members?activity=football`
2. Route handler calls `HelloAssoService.get_members(filters)`
3. Service checks SQLite cache freshness; if stale, fetches from HelloAsso API
4. Returns member list as JSON

**Invoice generation (single):**
1. User clicks "Generate Invoice" -> React calls `POST /api/invoices/{member_id}`
2. Route handler calls `InvoiceService.generate(member_data)`
3. Service renders Jinja2 template to HTML, then WeasyPrint to PDF
4. Stores PDF path + status in SQLite, returns download URL

**Batch invoice generation:**
1. User clicks "Generate All" -> React calls `POST /api/invoices/batch`
2. Route handler spawns background task via FastAPI `BackgroundTasks`
3. Background task iterates members, generates PDFs, updates DB status
4. Frontend polls `GET /api/invoices/batch/{job_id}/status` for progress

**Email sending:**
1. User clicks "Send Invoice" -> React calls `POST /api/emails/{invoice_id}`
2. Route handler calls `EmailService.send(invoice, recipient)`
3. Service constructs EmailMessage with PDF attachment, sends via SMTP
4. Stores send result in SQLite (success/error + timestamp)

## Project Structure

```
app/
  __init__.py
  main.py              # FastAPI app creation, middleware, static files mount
  config.py            # Settings from conf.json + env vars (Pydantic BaseSettings)
  auth.py              # Login endpoint, session middleware, auth dependency
  database.py          # SQLite engine, session factory
  models/
    __init__.py
    member.py           # Member SQLModel (cache from HelloAsso)
    invoice.py          # Invoice SQLModel (tracking generation + status)
    email_log.py        # EmailLog SQLModel (send attempts + results)
    user.py             # User SQLModel (dashboard credentials)
  services/
    __init__.py
    helloasso.py        # HelloAsso API V5 wrapper (refactored from helloasso.py)
    invoice.py          # PDF generation (Jinja2 + WeasyPrint)
    email.py            # Email sending (smtplib)
  routes/
    __init__.py
    members.py          # GET /api/members, GET /api/members/{id}
    invoices.py         # POST /api/invoices/{id}, GET /api/invoices/{id}/download
    emails.py           # POST /api/emails/{invoice_id}
    auth.py             # POST /api/login, POST /api/logout
  templates/
    invoice.jinja2      # Existing template (migrated from invoicing/)
  static/
    style.css           # Existing invoice styles
    logo.svg            # Existing logo
frontend/              # React app (Vite)
  dist/                # Built output, served by FastAPI
```

## Patterns to Follow

### Pattern 1: Service Layer / Facade
**What:** Wrap all external API calls and complex logic in service classes. Routes are thin HTTP adapters.
**When:** Always. Every route should delegate to a service.
**Example:**
```python
# app/services/helloasso.py
class HelloAssoService:
    def __init__(self, config: Settings):
        self.config = config
        self.client = httpx.AsyncClient()
        self._token: str | None = None

    async def authenticate(self) -> str:
        """OAuth2 client_credentials flow."""
        resp = await self.client.post(
            f"{self.config.helloasso_api_url}/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.config.helloasso_client_id,
                "client_secret": self.config.helloasso_client_secret,
            },
        )
        resp.raise_for_status()
        self._token = resp.json()["access_token"]
        return self._token

    async def get_members(self, **filters) -> list[dict]:
        """Fetch members from HelloAsso API with pagination."""
        # ... pagination logic from existing GetData()
```

### Pattern 2: FastAPI Dependency Injection for Services
**What:** Use `Depends()` to inject services into route handlers.
**When:** For all service access in routes.
**Example:**
```python
# app/routes/members.py
from fastapi import APIRouter, Depends
from app.services.helloasso import HelloAssoService

router = APIRouter(prefix="/api/members")

@router.get("/")
async def list_members(
    activity: str | None = None,
    service: HelloAssoService = Depends(get_helloasso_service),
):
    return await service.get_members(activity_filter=activity)
```

### Pattern 3: Background Tasks for Heavy Operations
**What:** Use FastAPI `BackgroundTasks` for PDF batch generation and batch email sending.
**When:** Any operation touching WeasyPrint for multiple members or sending multiple emails.
**Example:**
```python
@router.post("/api/invoices/batch")
async def generate_batch(background_tasks: BackgroundTasks):
    job_id = str(uuid4())
    background_tasks.add_task(batch_generate_pdfs, job_id)
    return {"job_id": job_id, "status": "started"}
```

### Pattern 4: Thread Pool for WeasyPrint
**What:** Run WeasyPrint in `asyncio.to_thread()` since it is synchronous and CPU-bound.
**When:** Every WeasyPrint call.
**Example:**
```python
import asyncio
from weasyprint import HTML

async def generate_pdf(html_content: str, output_path: str):
    await asyncio.to_thread(
        HTML(string=html_content).write_pdf, output_path
    )
```

### Pattern 5: SPA Catch-All for React Router
**What:** Mount React static files, with a catch-all route falling back to `index.html`.
**When:** For serving the React frontend from FastAPI.
**Example:**
```python
from starlette.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Mount API routes first (they take priority)
app.include_router(api_router, prefix="/api")

# Mount static assets
app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")

# Catch-all for SPA routing
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    return FileResponse("frontend/dist/index.html")
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Blocking the Event Loop with WeasyPrint
**What:** Calling WeasyPrint directly in an async route handler
**Why bad:** WeasyPrint is synchronous CPU-bound work. It blocks the entire async event loop, making all other requests wait.
**Instead:** Use `asyncio.to_thread()` or `BackgroundTasks`

### Anti-Pattern 2: HelloAsso Token in Global State
**What:** Storing the OAuth2 token as a module-level variable
**Why bad:** Token expiry, race conditions on refresh, not testable
**Instead:** Store token in the service instance, refresh on 401 response, use dependency injection

### Anti-Pattern 3: Raw SQL for Simple CRUD
**What:** Writing raw SQL queries for member/invoice tracking
**Why bad:** SQLModel handles this with far less code and type safety
**Instead:** Use SQLModel for all database operations

### Anti-Pattern 4: Serving PDFs from Disk via Absolute Paths
**What:** Returning file paths that expose server filesystem structure
**Why bad:** Security risk, breaks if paths change
**Instead:** Use `FileResponse` with a managed output directory, or stream from memory

## Scalability Considerations

| Concern | Current (5 users) | If Growth (50 users) | Notes |
|---------|-------------------|---------------------|-------|
| Database | SQLite is perfect | SQLite still fine | WAL mode handles concurrent reads. Writes are infrequent. |
| PDF generation | Background tasks | Consider Celery + Redis | Only if generation volume exceeds ~500/batch |
| API performance | Single Uvicorn worker | Multiple workers (`--workers 4`) | SQLite handles this with WAL mode |
| Static files | FastAPI serves directly | Add nginx reverse proxy | Only if static file load becomes significant |

This app will likely never need to scale beyond SQLite and a single container. The user base is fixed at a handful of volunteers managing ~200 members per season.

## Sources

- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [FastAPI Static Files](https://fastapi.tiangolo.com/tutorial/static-files/)
- [Serving React SPA with FastAPI](https://davidmuraya.com/blog/serving-a-react-frontend-application-with-fastapi/)
- [Facade Pattern for API Wrappers](https://alysivji.com/clean-architecture-with-the-facade-pattern.html)
- [Python API Client Design Pattern](https://bhomnick.net/design-pattern-python-api-client/)
