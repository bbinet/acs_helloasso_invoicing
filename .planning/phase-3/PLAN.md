# Phase 3 Plan: Svelte Dashboard & Docker Deployment

## Goal
Build a Svelte SPA dashboard with Tailwind/DaisyUI and deploy the full stack (Nginx + API + SSH) via Docker Compose.

## Methodology: Test-Driven Development
Following the [TDD skill](https://github.com/bbinet/skills/tree/bbinet/tdd):
- **Vertical slices**: RED → GREEN per behavior
- **@testing-library/svelte** for component tests
- **vitest** as test runner (native Vite integration)
- **Mock at system boundaries**: API calls (fetch) mocked in component tests
- **Test behavior, not implementation**: test what the user sees/interacts with

## Test Infrastructure
- **Framework**: vitest + @testing-library/svelte + jsdom
- **Mocking**: `vi.fn()` for fetch calls (system boundary)
- **Structure**: `frontend/src/__tests__/` directory
  ```
  frontend/src/__tests__/
    api.test.ts          # API client tests
    Login.test.ts        # Login component
    MemberTable.test.ts  # Data table (sort, filter, search)
    Dashboard.test.ts    # Dashboard stats
    Invoices.test.ts     # Invoice actions + batch
    Summary.test.ts      # Activity breakdown
    Sidebar.test.ts      # Navigation
  ```

## Success Criteria
1. Volunteer can login, view members, filter, generate invoices, send emails via browser
2. Dashboard loads in < 3 seconds
3. Responsive on desktop and tablet
4. `docker compose up` starts the full stack (Nginx + API + SSH)
5. All existing 71 pytest tests still pass
6. CLI `helloasso.py` still works via SSH
7. **All frontend tests pass (`npm test` green)**

---

## Wave 1: Svelte Project Scaffold + Test Setup (TDD)

### Task 1.1: Create Svelte + Vite + Tailwind + DaisyUI + Test infra
**Files:** `frontend/` directory
**What:**
- Scaffold Svelte project with Vite: `npm create vite@latest frontend -- --template svelte-ts`
- Install Tailwind CSS + DaisyUI: `npm install -D tailwindcss @tailwindcss/vite daisyui`
- Install test deps: `npm install -D vitest @testing-library/svelte @testing-library/jest-dom jsdom`
- Configure `tailwind.config.js` with DaisyUI plugin and ACS theme
- Configure `vite.config.ts` with proxy to `http://localhost:8000` for `/api/` and vitest config
- Install `svelte-spa-router` for client-side routing
- Create basic `src/App.svelte` with router setup
- Create `src/app.css` with Tailwind directives
- Create `vitest.config.ts` or configure in `vite.config.ts`:
  ```ts
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/__tests__/setup.ts'],
  }
  ```
- Create `src/__tests__/setup.ts` with `@testing-library/jest-dom` import

### Task 1.2: API client (TDD)
**Files:** `frontend/src/__tests__/api.test.ts`, `frontend/src/lib/api.ts`
**TDD cycles (mock global `fetch`):**
1. RED: test `apiFetch` makes GET request with credentials included → GREEN
2. RED: test `apiFetch` parses JSON response → GREEN
3. RED: test `apiFetch` throws on non-ok response → GREEN
4. RED: test `login(password)` POSTs to `/api/auth/login` → GREEN
5. RED: test `getMembers()` GETs `/api/members` → GREEN
6. RED: test `getMembers({activity: 'foot'})` adds query params → GREEN

### Task 1.3: Svelte stores
**Files:** `frontend/src/lib/stores.ts`
**What:**
- `authenticated` writable store (bool)
- `members` writable store (array)
- `loading` writable store (bool)
- No tests needed — stores are trivial writable declarations

### Task 1.4: Layout + Sidebar (TDD)
**Files:** `frontend/src/__tests__/Sidebar.test.ts`, `frontend/src/components/Sidebar.svelte`, `frontend/src/components/Layout.svelte`
**TDD cycles:**
1. RED: test Sidebar renders all navigation links (Dashboard, Membres, Factures, Résumé) → GREEN
2. RED: test Sidebar renders logout button → GREEN
3. RED: test Layout wraps content with sidebar → GREEN

**Commit:** "feat(3-1): Scaffold Svelte project with Tailwind, DaisyUI, tests, API client"

---

## Wave 2: Pages — Login, Dashboard, Members (TDD)

### Task 2.1: Login page (TDD)
**Files:** `frontend/src/__tests__/Login.test.ts`, `frontend/src/pages/Login.svelte`
**TDD cycles (mock fetch):**
1. RED: test Login renders password input and submit button → GREEN
2. RED: test Login calls login API on submit → GREEN
3. RED: test Login shows error on wrong password (API returns 401) → GREEN

### Task 2.2: Dashboard page (TDD)
**Files:** `frontend/src/__tests__/Dashboard.test.ts`, `frontend/src/pages/Dashboard.svelte`
**TDD cycles (mock fetch):**
1. RED: test Dashboard shows total members count → GREEN
2. RED: test Dashboard shows invoices generated count → GREEN
3. RED: test Dashboard shows emails sent count → GREEN
4. RED: test Dashboard shows refresh button → GREEN

### Task 2.3: Members page + MemberTable (TDD)
**Files:** `frontend/src/__tests__/MemberTable.test.ts`, `frontend/src/pages/Members.svelte`, `frontend/src/components/MemberTable.svelte`
**TDD cycles:**
1. RED: test MemberTable renders rows from data → GREEN
2. RED: test MemberTable sorts by column when header clicked → GREEN
3. RED: test MemberTable filters by search text (name/email) → GREEN
4. RED: test MemberTable filters by activity dropdown → GREEN
5. RED: test MemberTable paginates (shows 20 per page, next/prev buttons) → GREEN
6. RED: test MemberTable shows status badges (✓/✗) for invoice/email → GREEN
7. RED: test MemberTable row action buttons trigger callbacks → GREEN

**MemberTable.svelte** — custom DaisyUI data table:
- Columns: #, Nom, Prénom, Entreprise, Email, Activités, Date, EA, Facture, Email
- Props: `data` (member array), `onGenerateInvoice`, `onSendEmail`, `onDownload`
- Internal state: sortColumn, sortDirection, searchText, activityFilter, currentPage

**Members.svelte** — page wrapper:
- Fetches members from API on mount
- Passes data to MemberTable
- Handles action callbacks (calls API, refreshes data)
- "Exporter CSV" button

**Commit:** "feat(3-2): Add Login, Dashboard, Members pages with TDD tests"

---

## Wave 3: Pages — Invoices, Summary (TDD)

### Task 3.1: Invoices page + BatchProgress + InvoicePreview (TDD)
**Files:** `frontend/src/__tests__/Invoices.test.ts`, `frontend/src/pages/Invoices.svelte`, `frontend/src/components/BatchProgress.svelte`, `frontend/src/components/InvoicePreview.svelte`
**TDD cycles:**
1. RED: test Invoices page renders member list with status columns → GREEN
2. RED: test "Générer toutes les factures" button calls batch API → GREEN
3. RED: test BatchProgress shows progress bar with completed/total → GREEN
4. RED: test BatchProgress shows "Terminé" when done → GREEN
5. RED: test InvoicePreview modal renders iframe with preview URL → GREEN
6. RED: test per-member download button triggers download → GREEN

**Invoices.svelte:**
- Table showing all members with invoice/email status columns
- Batch action buttons: "Générer toutes les factures", "Envoyer tous les emails"
- Per-member actions: preview, download, generate, send email
- Batch progress component shown during operations

**BatchProgress.svelte:**
- DaisyUI progress bar
- Shows: completed/total, errors list
- Polls batch status endpoint every 2 seconds while running
- Auto-dismisses when done

**InvoicePreview.svelte:**
- DaisyUI modal
- Loads HTML preview from `/api/invoices/{id}/preview`
- Renders in an iframe
- "Télécharger PDF" button in modal footer

### Task 3.2: Summary page (TDD)
**Files:** `frontend/src/__tests__/Summary.test.ts`, `frontend/src/pages/Summary.svelte`
**TDD cycles:**
1. RED: test Summary renders activities with member counts → GREEN
2. RED: test Summary shows total at bottom → GREEN
3. RED: test Summary expands to show member list on click → GREEN

**Summary.svelte:**
- Calls `/api/summary`
- DaisyUI table showing activities sorted by member count
- Expandable rows: click to show member list (DaisyUI collapse)
- Total count at bottom

**Commit:** "feat(3-3): Add Invoices page with batch progress, Summary page, TDD tests"

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
- Nginx container with built frontend + reverse proxy
- API container with Python + SSH
- Shared volume for invoicing data
- Environment variables for config
- Frontend build: either multi-stage in Dockerfile or separate build step

### Task 4.4: Update dev docker-compose
**Files:** `docker-compose.yml`
**What:**
- Add frontend dev service (Vite dev server with HMR on port 5173)
- API service stays as-is (Uvicorn with --reload on port 8000)
- Frontend proxies `/api/` to API container

**Commit:** "feat(3-4): Add Docker production and dev setup with Nginx"

---

## Verification Checklist

### Frontend tests
- [ ] `npm test` passes all frontend tests (vitest green)
- [ ] Tests cover: API client, Login, Dashboard, MemberTable, Invoices, Summary, Sidebar

### Frontend manual
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

### Backend tests
- [ ] `pytest` still passes (71 tests)

## File Inventory

### New Files
| File | Purpose |
|------|---------|
| `frontend/package.json` | Svelte project deps |
| `frontend/vite.config.ts` | Vite config with API proxy + vitest |
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
| `frontend/src/__tests__/setup.ts` | Test setup (jest-dom) |
| `frontend/src/__tests__/api.test.ts` | API client tests |
| `frontend/src/__tests__/Login.test.ts` | Login tests |
| `frontend/src/__tests__/Dashboard.test.ts` | Dashboard tests |
| `frontend/src/__tests__/MemberTable.test.ts` | Data table tests |
| `frontend/src/__tests__/Invoices.test.ts` | Invoices tests |
| `frontend/src/__tests__/Summary.test.ts` | Summary tests |
| `frontend/src/__tests__/Sidebar.test.ts` | Sidebar tests |
| `nginx.conf` | Nginx reverse proxy config |
| `docker-compose.prod.yml` | Production Docker Compose |

### Modified Files
| File | Change |
|------|--------|
| `Dockerfile` | Add API server setup (gunicorn, requirements) |
| `docker-compose.yml` | Add frontend dev service |
| `docker-pre-start.sh` | Add gunicorn startup |
