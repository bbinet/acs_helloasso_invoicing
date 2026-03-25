# Research Summary: ACS HelloAsso Invoicing Web Dashboard

**Domain:** Internal tool / Association management dashboard
**Researched:** 2026-03-25
**Overall confidence:** HIGH

## Executive Summary

This project transforms an existing CLI-based HelloAsso invoicing tool into a web dashboard for a small team of French sports association volunteers. The existing codebase is well-structured: a Python script (`helloasso.py`) wrapping the HelloAsso API V5, a Jinja2 template for invoices, WeasyPrint for PDF generation, and `sendemail` CLI for delivery. The web conversion is straightforward -- the core business logic already exists in Python and just needs HTTP endpoints in front of it.

**FastAPI is the clear choice** over Flask for this project. Despite being a small internal tool (where Flask is traditionally recommended), FastAPI's built-in OAuth2 support, automatic OpenAPI docs, Pydantic validation, and the fact that the existing code already uses `requests` (easily swapped to `httpx`) make it the better fit. The auto-generated Swagger UI alone is valuable for a small team -- it serves as both documentation and a testing interface. FastAPI's dependency injection system also maps cleanly to the pattern of "authenticate with HelloAsso, then fetch data."

The biggest technical concern is WeasyPrint: it is synchronous, CPU-bound, and can accumulate memory. For single-invoice generation this is fine, but batch generation (the common use case -- generating invoices for all members) must be offloaded to a background task. FastAPI's `BackgroundTasks` or a simple task queue handles this well.

Email sending should migrate from the `sendemail` Perl CLI tool to Python's built-in `smtplib` + `email.message.EmailMessage`. This eliminates the Perl dependency, keeps everything in-process, and is trivially testable.

## Key Findings

**Stack:** FastAPI + SQLite (via SQLModel) + WeasyPrint + smtplib, served with Uvicorn in Docker
**Architecture:** Service-layer facade pattern wrapping existing HelloAsso logic, with FastAPI routes as thin HTTP adapters
**Critical pitfall:** WeasyPrint is synchronous and memory-hungry -- batch PDF generation must not block the API server

## Implications for Roadmap

Based on research, suggested phase structure:

1. **Phase 1: API Foundation** - Set up FastAPI project, migrate HelloAsso wrapper to a service class, add SQLite for caching, implement basic auth
   - Addresses: Core API endpoints (members list, filtering), authentication, data persistence
   - Avoids: Premature frontend work before API is stable

2. **Phase 2: Invoice Pipeline** - Migrate PDF generation and email sending into FastAPI endpoints with background task support
   - Addresses: PDF generation, email delivery, invoice tracking in DB
   - Avoids: WeasyPrint blocking issues by implementing background tasks from the start

3. **Phase 3: React Dashboard + Docker** - Build React SPA, serve from FastAPI, update Docker deployment
   - Addresses: User-facing dashboard, deployment
   - Avoids: Building UI before backend is complete and tested

**Phase ordering rationale:**
- Phase 1 first because all other features depend on the API layer and data access
- Phase 2 before Phase 3 because the invoice pipeline is the core value -- it should work via API before adding UI
- Phase 3 last because the React frontend is pure presentation over a working API

**Research flags for phases:**
- Phase 2: May need deeper research on WeasyPrint memory behavior under repeated calls and batch processing patterns
- Phase 3: Standard patterns for FastAPI + React SPA, unlikely to need further research

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack (FastAPI) | HIGH | Extensive docs, official tutorials, well-proven for API wrapping |
| Stack (SQLite/SQLModel) | HIGH | Official FastAPI recommendation, perfect for small-scale |
| WeasyPrint integration | MEDIUM | Known memory issues; single-invoice is fine, batch needs care |
| Email (smtplib) | HIGH | Standard library, well-documented, direct replacement for sendemail |
| Authentication | HIGH | FastAPI has built-in HTTP Basic Auth and session support |
| HelloAsso API | HIGH | Official Python SDK exists, but existing custom wrapper is simpler and sufficient |

## Gaps to Address

- WeasyPrint behavior under repeated calls in a long-running process (memory leaks) -- monitor in Phase 2
- HelloAsso API rate limits not documented in existing code -- should add retry/backoff logic
- Exact React SPA routing strategy with FastAPI catch-all -- straightforward but needs testing
