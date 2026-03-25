# Requirements: ACS HelloAsso Invoicing Web Dashboard

## Derived From
- PROJECT.md (vision, users, constraints)
- Research: HelloAsso API V5, Python backend, Svelte frontend, deployment
- User feedback: no DB, keep sendemail, shared library, flat files

---

## Functional Requirements

### FR-1: Authentication & Access Control
- **FR-1.1**: Dashboard requires login (username/password) to access any page
- **FR-1.2**: Simple auth for 3-5 users — no role-based access, all users have full access
- **FR-1.3**: Session-based authentication with secure cookies

### FR-2: Member Data Viewing
- **FR-2.1**: Display member list in a sortable, filterable data table
- **FR-2.2**: Filter by activity (regex), date range, refund status, Emile Allais membership
- **FR-2.3**: Search by member name or email
- **FR-2.4**: Display per member: name, company, email, phone, activities, order date, EA status
- **FR-2.5**: Export member list to CSV

### FR-3: Season/Campaign Management
- **FR-3.1**: Select active season (formSlug) from available campaigns
- **FR-3.2**: Fetch member data from HelloAsso API on demand ("Refresh" button) and dump to JSON files

### FR-4: Activity Summary
- **FR-4.1**: Display activity breakdown showing count of members per activity
- **FR-4.2**: Sort activities by member count (descending)
- **FR-4.3**: Expand activity to see member names

### FR-5: Invoice Generation
- **FR-5.1**: Generate PDF invoice for a single member (triggers existing Makefile pipeline)
- **FR-5.2**: Batch generate invoices for all members (or filtered subset)
- **FR-5.3**: Batch generation runs as background task with progress indicator
- **FR-5.4**: Preview invoice as HTML before generating PDF
- **FR-5.5**: Download generated PDF invoices
- **FR-5.6**: Invoice status derived from filesystem: `.pdf` exists = generated

### FR-6: Email Sending
- **FR-6.1**: Send invoice email to a single member (triggers existing sendemail via Makefile)
- **FR-6.2**: Batch send emails for all unsent invoices
- **FR-6.3**: Batch email sending runs as background task with progress indicator
- **FR-6.4**: Email status derived from filesystem: `.mail.log` exists = sent
- **FR-6.5**: Re-send individual emails on demand

### FR-7: Dashboard Overview
- **FR-7.1**: Show summary stats: total members, invoices generated, emails sent
- **FR-7.2**: Show activity distribution table

---

## Non-Functional Requirements

### NFR-1: Technology Stack
- **NFR-1.1**: Backend: FastAPI (Python 3.11+) with Uvicorn/Gunicorn
- **NFR-1.2**: Frontend: Svelte with TypeScript, Vite
- **NFR-1.3**: Data storage: Flat JSON files in `invoicing/<formSlug>/` (no database)
- **NFR-1.4**: PDF: WeasyPrint via existing Makefile pipeline
- **NFR-1.5**: Email: sendemail via existing Makefile pipeline (kept as-is)
- **NFR-1.6**: HTTP client: httpx (async, replacing requests in shared library)

### NFR-2: HelloAsso API Integration
- **NFR-2.1**: Proper OAuth2 token lifecycle — use refresh_token, never re-auth per request
- **NFR-2.2**: Member data dumped to JSON files (same as CLI `--dump`)
- **NFR-2.3**: Handle pagination correctly (continuationToken)
- **NFR-2.4**: Filter by payment state (not just refund operations)

### NFR-3: Code Architecture
- **NFR-3.1**: Shared Python library extracted from `helloasso.py` — importable by both CLI and web
- **NFR-3.2**: CLI (`helloasso.py`) continues to work exactly as before, importing shared library
- **NFR-3.3**: Web API uses same shared library, same file paths, same data format
- **NFR-3.4**: WeasyPrint runs in thread pool (asyncio.to_thread) — never blocks event loop

### NFR-4: Deployment
- **NFR-4.1**: Single Docker container (Nginx + Gunicorn/Uvicorn + Svelte static)
- **NFR-4.2**: Multi-stage Dockerfile (Node build + Python production)
- **NFR-4.3**: Docker Compose for development (hot reload on both frontend and backend)
- **NFR-4.4**: Credentials via existing conf.json (maintain compatibility)
- **NFR-4.5**: Health check endpoint at /api/health

### NFR-5: UI/UX
- **NFR-5.1**: French language UI (hardcoded French strings)
- **NFR-5.2**: Responsive design (desktop-first, usable on tablet)
- **NFR-5.3**: ACS branding (logo, colors)

### NFR-6: Backward Compatibility
- **NFR-6.1**: Existing CLI (`helloasso.py`) continues to work unchanged
- **NFR-6.2**: Existing invoice template design preserved
- **NFR-6.3**: Existing Makefile pipeline preserved (PDF generation + email sending)
- **NFR-6.4**: Same file arborescence: `invoicing/<formSlug>/*.json`, `*.pdf`, `*.mail.log`
- **NFR-6.5**: SSH access preserved during transition
- **NFR-6.6**: conf.json format preserved

---

## Anti-Requirements (Explicitly Out of Scope)
- Database (SQLite or other) — use flat files
- Migration away from sendemail — keep existing email pipeline
- Multi-tenant / multi-association support
- User self-registration
- Real-time HelloAsso webhooks (use manual refresh)
- Payment processing (read-only)
- Custom invoice template editor
- Mobile app (responsive web is sufficient)
- Role-based access control
- Internationalization beyond French

---

## Success Criteria
1. A volunteer can log in, view the member list, filter by activity, and export to CSV
2. A volunteer can generate PDF invoices for all members in one click
3. A volunteer can send invoice emails to all members and track send status
4. The tool runs in a single Docker container accessible via web browser
5. The existing CLI tool (`helloasso.py`) continues to work identically
6. Web and CLI share the same data files — changes from one are visible in the other
