# Phase 3 Plan: Svelte Dashboard & Docker Deployment

## Goal
Build a Svelte SPA dashboard with Tailwind/DaisyUI and deploy the full stack (Nginx + API + SSH) via Docker Compose.

## Methodology
- Frontend: no TDD (Svelte components are UI — tested manually via browser)
- Docker: tested by building and running
- API client: tested via integration with existing backend tests

## Success Criteria
1. Volunteer can login, view members, filter, generate invoices, send emails via browser
2. Dashboard loads in < 3 seconds
3. Responsive on desktop and tablet
4. `docker compose up` starts the full stack (Nginx + API + SSH)
5. All existing 71 pytest tests still pass
6. CLI `helloasso.py` still works via SSH

---

## Wave 1: Svelte Project Scaffold

### Task 1.1: Create Svelte + Vite + Tailwind + DaisyUI project
**Files:** `frontend/` directory
**What:**
- Scaffold Svelte project with Vite: `npm create vite@latest frontend -- --template svelte-ts`
- Install Tailwind CSS + DaisyUI: `npm install -D tailwindcss @tailwindcss/vite daisyui`
- Configure `tailwind.config.js` with DaisyUI plugin and ACS theme
- Configure `vite.config.ts` with proxy to `http://localhost:8000` for `/api/`
- Install `svelte-spa-router` for client-side routing
- Create basic `src/App.svelte` with router setup
- Create `src/app.css` with Tailwind directives

### Task 1.2: Create API client and stores
**Files:** `frontend/src/lib/api.ts`, `frontend/src/lib/stores.ts`
**What:**
- `api.ts`: fetch wrapper with:
  - Base URL: relative `/api/` (works with Vite proxy in dev, Nginx in prod)
  - `credentials: 'include'` for cookie auth
  - `apiFetch(path, options)` — wraps fetch, handles JSON, redirects to `/login` on 401
  - Typed functions: `login(password)`, `logout()`, `checkAuth()`, `getMembers(filters?)`, `getMember(id)`, `exportCSV()`, `getCampaigns()`, `refreshCampaigns()`, `getSummary()`, `generateInvoice(id)`, `batchGenerateInvoices()`, `getBatchInvoiceStatus(jobId)`, `downloadInvoice(id)`, `previewInvoice(id)`, `sendEmail(id)`, `batchSendEmails()`, `getBatchEmailStatus(jobId)`
- `stores.ts`: Svelte writable stores:
  - `authenticated` (bool)
  - `members` (array)
  - `loading` (bool)

### Task 1.3: Create layout — Sidebar component
**Files:** `frontend/src/components/Sidebar.svelte`, `frontend/src/components/Layout.svelte`
**What:**
- `Layout.svelte`: DaisyUI drawer layout wrapping page content with sidebar
- `Sidebar.svelte`: navigation links with icons:
  - Dashboard (`/`)
  - Membres (`/members`)
  - Factures (`/invoices`)
  - Résumé (`/summary`)
  - Logout button at bottom
- ACS logo at top of sidebar
- Active link highlighting

**Commit:** "feat(3-1): Scaffold Svelte project with Tailwind, DaisyUI, routing, API client"

---

## Wave 2: Pages (Login, Dashboard, Members)

### Task 2.1: Login page
**Files:** `frontend/src/pages/Login.svelte`
**What:**
- Centered card with password input + submit button
- Calls `login(password)` from api.ts
- On success: redirect to `/`
- On error: show error message
- No sidebar on this page
- ACS logo above the form

### Task 2.2: Dashboard page
**Files:** `frontend/src/pages/Dashboard.svelte`
**What:**
- Stat cards (DaisyUI `stats` component):
  - Total membres
  - Factures générées (count of members with invoice_generated=true)
  - Emails envoyés (count with email_sent=true)
- Activity distribution table (from `/api/summary`)
- "Rafraîchir depuis HelloAsso" button → calls `refreshCampaigns()`
- Wrapped in Layout

### Task 2.3: Members page with data table
**Files:** `frontend/src/pages/Members.svelte`, `frontend/src/components/MemberTable.svelte`
**What:**
- `MemberTable.svelte` — custom DaisyUI data table:
  - Columns: #, Nom, Prénom, Entreprise, Email, Activités, Date, EA, Facture, Email
  - Click column header to sort (asc/desc toggle)
  - Search input above table (filters across name/email/company)
  - Activity dropdown filter
  - Pagination controls (20 per page)
  - Status badges: ✓ vert (done) / ✗ rouge (not done) for facture/email
  - Row action buttons: generate invoice, send email, download PDF
- `Members.svelte` — page wrapper:
  - Fetches members from API on mount
  - Passes data to MemberTable
  - Handles action callbacks (calls API, refreshes data)
  - "Exporter CSV" button

**Commit:** "feat(3-2): Add Login, Dashboard, Members pages with data table"

---

## Wave 3: Pages (Invoices, Summary)

### Task 3.1: Invoices page
**Files:** `frontend/src/pages/Invoices.svelte`, `frontend/src/components/BatchProgress.svelte`, `frontend/src/components/InvoicePreview.svelte`
**What:**
- `Invoices.svelte`:
  - Table showing all members with invoice/email status columns
  - Batch action buttons: "Générer toutes les factures", "Envoyer tous les emails"
  - Per-member actions: preview, download, generate, send email
  - Batch progress component shown during operations
- `BatchProgress.svelte`:
  - DaisyUI progress bar
  - Shows: completed/total, errors list
  - Polls batch status endpoint every 2 seconds while running
  - Auto-dismisses when done
- `InvoicePreview.svelte`:
  - DaisyUI modal
  - Loads HTML preview from `/api/invoices/{id}/preview`
  - Renders in an iframe
  - "Télécharger PDF" button in modal footer

### Task 3.2: Summary page
**Files:** `frontend/src/pages/Summary.svelte`
**What:**
- Calls `/api/summary`
- DaisyUI table showing activities sorted by member count
- Each row: activity name, member count
- Expandable: click to show member list for that activity (DaisyUI collapse)
- Total count at bottom

**Commit:** "feat(3-3): Add Invoices page with batch progress and Summary page"

---

## Wave 4: Docker Production Setup

### Task 4.1: Nginx configuration
**Files:** `nginx.conf`
**What:**
```nginx
server {
    listen 80;
    server_name _;

    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Task 4.2: Update Dockerfile for API server
**Files:** `Dockerfile`
**What:**
- Extend existing Dockerfile (debian:trixie base)
- Add Python API dependencies: `pip install -r requirements.txt`
- Copy `app/`, `lib/` directories
- Update entrypoint to start both Gunicorn and SSHD:
  ```bash
  # Start Gunicorn in background
  gunicorn app.main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 &
  # Start SSHD in foreground
  /usr/sbin/sshd -D
  ```
- Expose port 8000 (API) + 22 (SSH)

### Task 4.3: Production docker-compose
**Files:** `docker-compose.prod.yml`
**What:**
- Multi-stage build: Node stage builds frontend
- Nginx container serves static build + proxies API
- API container runs Python + SSH
- Shared volume for invoicing data
- Environment variables for config

### Task 4.4: Update dev docker-compose
**Files:** `docker-compose.yml`
**What:**
- Add frontend dev service (Vite dev server with HMR)
- API service stays as-is (Uvicorn with --reload)
- Frontend proxies `/api/` to API container

**Commit:** "feat(3-4): Add Docker production and dev setup with Nginx"

---

## Verification Checklist

### Frontend
- [ ] Login page works (correct/wrong password)
- [ ] Dashboard shows stats
- [ ] Members table displays data with sort/filter/search
- [ ] Members table pagination works
- [ ] Invoice generation from Members page works
- [ ] Invoices page batch generation works with progress
- [ ] Invoice preview in modal works
- [ ] PDF download works
- [ ] Email sending works
- [ ] Summary page shows activity breakdown
- [ ] Sidebar navigation works between all pages
- [ ] 401 redirects to login

### Docker
- [ ] `docker compose up` starts full stack (dev)
- [ ] `docker compose -f docker-compose.prod.yml up` starts production
- [ ] Nginx serves frontend on port 80
- [ ] Nginx proxies /api/ to backend
- [ ] SSH access works on port 22
- [ ] CLI helloasso.py works via SSH

### Existing tests
- [ ] `pytest` still passes (71 tests)

## File Inventory

### New Files
| File | Purpose |
|------|---------|
| `frontend/package.json` | Svelte project deps |
| `frontend/vite.config.ts` | Vite config with API proxy |
| `frontend/tailwind.config.js` | Tailwind + DaisyUI config |
| `frontend/src/App.svelte` | Root component with router |
| `frontend/src/app.css` | Tailwind directives |
| `frontend/src/lib/api.ts` | API client (fetch wrapper) |
| `frontend/src/lib/stores.ts` | Svelte stores |
| `frontend/src/components/Layout.svelte` | Sidebar layout wrapper |
| `frontend/src/components/Sidebar.svelte` | Navigation sidebar |
| `frontend/src/components/MemberTable.svelte` | Custom data table |
| `frontend/src/components/BatchProgress.svelte` | Batch job progress bar |
| `frontend/src/components/InvoicePreview.svelte` | Invoice preview modal |
| `frontend/src/pages/Login.svelte` | Login page |
| `frontend/src/pages/Dashboard.svelte` | Dashboard overview |
| `frontend/src/pages/Members.svelte` | Members page |
| `frontend/src/pages/Invoices.svelte` | Invoices management |
| `frontend/src/pages/Summary.svelte` | Activity summary |
| `nginx.conf` | Nginx reverse proxy config |
| `docker-compose.prod.yml` | Production Docker Compose |

### Modified Files
| File | Change |
|------|--------|
| `Dockerfile` | Add API server setup (gunicorn, requirements) |
| `docker-compose.yml` | Add frontend dev service |
| `docker-pre-start.sh` | Add gunicorn startup |
