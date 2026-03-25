# Research Summary: ACS HelloAsso Invoicing Dashboard

**Domain:** Internal admin dashboard for French sports association invoicing
**Researched:** 2026-03-25
**Overall confidence:** HIGH

## Executive Summary

This project transforms an existing CLI-based Python tool into a web dashboard for ACS volunteers. The frontend needs are well-defined: display member data in filterable tables, trigger PDF generation, send emails, and show statistics. This is a classic internal admin/dashboard use case with a small user base (handful of volunteers), meaning performance at scale is not a concern but developer productivity and maintainability are paramount.

The recommended stack is **Vite + React + TypeScript** for the SPA, **Mantine** as the UI component library, **Mantine React Table** (built on TanStack Table) for the data grid, **TanStack Query** for server state management, **React Hook Form + Zod** for forms, and **react-i18next** for French-first internationalization. This stack is modern, well-documented, and avoids over-engineering for what is fundamentally a small internal tool.

The backend (FastAPI) will serve the built SPA in production and expose a REST API. PDF generation stays server-side with WeasyPrint. The frontend simply fetches a PDF blob and displays it via `react-pdf` or an iframe. This architecture keeps the existing invoice pipeline intact while adding a modern UI layer.

The biggest risk is scope creep -- this should remain a focused dashboard, not a general-purpose admin framework. The second risk is over-engineering state management or introducing unnecessary complexity (Redux, SSR, microservices) for what serves 3-5 concurrent users.

## Key Findings

**Stack:** Vite + React 18 + TypeScript + Mantine 7 + TanStack Query v5 + React Hook Form/Zod
**Architecture:** SPA served by FastAPI in production, Vite dev proxy in development, single Docker container
**Critical pitfall:** Over-engineering for a small volunteer team -- keep it simple

## Implications for Roadmap

Based on research, suggested phase structure:

1. **Foundation & Member List** - Set up Vite/React/Mantine scaffold, implement member list with filtering/sorting/pagination against FastAPI endpoints
   - Addresses: Core data display, search/filter, table views
   - Avoids: Building too much before validating the API integration works

2. **Invoice Generation & PDF** - Add invoice generation triggers, PDF preview, and download
   - Addresses: PDF generation workflow, invoice preview
   - Avoids: Coupling PDF logic to frontend (stays server-side)

3. **Email, Statistics & Polish** - Email sending with status tracking, activity summaries/stats, French i18n polish
   - Addresses: Email workflow, statistics views, branding
   - Avoids: Premature optimization of features not yet validated

**Phase ordering rationale:**
- Member list is the core view that validates the full stack integration
- PDF generation depends on member selection (needs phase 1)
- Email and stats are additive features that build on working infrastructure

**Research flags for phases:**
- Phase 1: Standard patterns, low risk
- Phase 2: PDF preview in browser needs testing (worker setup quirks with react-pdf)
- Phase 3: Email status tracking may need a lightweight DB (SQLite) for persistence

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Vite+React+TS is the industry standard; well-documented |
| UI Library | HIGH | Mantine is well-suited for small dashboards; multiple sources agree |
| Data Table | HIGH | Mantine React Table wraps TanStack Table with Mantine styling |
| State Management | HIGH | TanStack Query v5 is the standard for server state |
| Forms | HIGH | React Hook Form + Zod is the dominant pattern |
| PDF Preview | MEDIUM | react-pdf works but has worker setup quirks |
| i18n | HIGH | react-i18next is the standard; French support is straightforward |

## Gaps to Address

- Exact FastAPI endpoint design (depends on backend research)
- Authentication approach (if needed -- may be unnecessary for internal tool behind VPN/Docker)
- Whether SQLite or similar is needed for email/invoice status tracking
- Mantine 7 vs upcoming Mantine 8 (Mantine 8 was recently released; evaluate stability)
