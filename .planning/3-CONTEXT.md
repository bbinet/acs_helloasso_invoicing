# Phase 3 Context: Svelte Dashboard & Docker Deployment

## Locked Decisions (from Phase 1 & 2)
- D1-D11 from 1-CONTEXT.md and 2-CONTEXT.md still apply
- FastAPI backend with all routes in place
- lib/ shared library, flat files, Makefile subprocess for PDF/email

## Phase 3 Decisions

### D12: CSS Framework — Tailwind + DaisyUI
- Use Tailwind CSS for utility classes
- DaisyUI on top for pre-styled components (buttons, modals, tables, cards, navbar)
- ACS branding via DaisyUI theme customization (primary color, logo)
- French labels hardcoded directly in Svelte components

### D13: Data Table — Custom DaisyUI table
- Build a custom Svelte component using DaisyUI `table` classes
- Features: column sorting (click header), text search (input above table), activity filter (dropdown), pagination (client-side)
- No external table library — ~200 rows is trivially handled client-side
- Row actions: generate invoice, send email, download PDF (icon buttons)

### D14: Navigation — Sidebar with 5 pages
- Sidebar layout (DaisyUI drawer) with logo + navigation links
- Hidden on login page

**Pages:**
1. **Login** (`/login`) — password input, no sidebar
2. **Dashboard** (`/`) — overview stats: total members, invoices generated, emails sent, activity distribution
3. **Membres** (`/members`) — data table with filters, search, per-member actions
4. **Factures** (`/invoices`) — batch actions (generate all, send all), per-member invoice status, preview, download
5. **Résumé** (`/summary`) — activity breakdown table with member counts, expandable member lists

### D15: Svelte Routing
- Use `svelte-routing` or `svelte-spa-router` for client-side SPA routing
- All routes under one SPA, served by Nginx
- Nginx `try_files $uri /index.html` for SPA catch-all

### D16: API Client
- Simple `fetch()` wrapper in `src/lib/api.ts`
- Base URL from environment or relative `/api/`
- Include credentials (cookies) for auth
- Handle 401 → redirect to login

### D17: Docker — Compose multi-container
**Container 1: Nginx**
- Serves Svelte static build from `/usr/share/nginx/html`
- Proxies `/api/*` to the API container
- Exposes port 80

**Container 2: API + SSH**
- Gunicorn + UvicornWorker serving FastAPI on port 8000
- SSHD for CLI access (port 22)
- Contains `helloasso.py` CLI, `lib/`, `invoicing/` assets
- Based on existing Dockerfile (debian:trixie) extended with Python API deps
- Runs entrypoint that starts both Gunicorn and SSHD (via dumb-init)

**docker-compose.prod.yml:**
```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - frontend_build:/usr/share/nginx/html:ro
    depends_on:
      - api
  api:
    build: .
    ports:
      - "22:22"
    environment:
      - CONF_PATH=/app/conf.json
      - DASHBOARD_PASSWORD=${DASHBOARD_PASSWORD}
    volumes:
      - ./conf.json:/app/conf.json:ro
      - invoicing_data:/app/invoicing
```

### D18: Svelte Build
- Vite build outputs to `frontend/dist/`
- Multi-stage Dockerfile: Node stage builds frontend, copies to nginx volume or shared build
- Or: build frontend separately, mount as volume

## What NOT to Build in Phase 3
- No i18n framework (hardcode French strings)
- No dark mode
- No WebSocket real-time updates (polling for batch status is fine)
- No user management (single password, already implemented)
- No multi-season selector
- No mobile-specific design (responsive is enough)

## New Files Expected
```
frontend/                    # Svelte app (Vite)
  package.json
  vite.config.ts
  svelte.config.js
  tailwind.config.js
  src/
    App.svelte              # Main app with router
    lib/
      api.ts                # Fetch wrapper
      stores.ts             # Svelte stores (auth state, members cache)
    pages/
      Login.svelte
      Dashboard.svelte
      Members.svelte
      Invoices.svelte
      Summary.svelte
    components/
      Sidebar.svelte
      MemberTable.svelte    # Custom DaisyUI data table
      BatchProgress.svelte  # Progress bar for batch jobs
      InvoicePreview.svelte # Modal with HTML preview
nginx.conf                  # Nginx reverse proxy config
docker-compose.prod.yml     # Production multi-container setup
Dockerfile                  # Updated with API server setup
```
