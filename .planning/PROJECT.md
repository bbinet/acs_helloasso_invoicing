# ACS HelloAsso Invoicing — Web Dashboard

## Vision
Transform the existing CLI-based HelloAsso invoicing tool into a full web application with a React frontend and Python API backend, enabling a small team of ACS volunteers to manage memberships, generate invoices, and send emails through a user-friendly dashboard.

## Problem Statement
The current tool is a CLI Python script that requires terminal knowledge to operate. ACS volunteers (small team) need to query HelloAsso data, generate PDF invoices, and email them to members. The CLI workflow is cumbersome for non-technical users and lacks visibility into operations.

## Users
- **Primary**: Small team of ACS Savoie Technolac volunteers/staff who manage memberships and invoicing
- **Use cases**: View members, filter by activity/season, generate PDF invoices, send invoices by email, track invoice status

## Current State
- `helloasso.py` — CLI tool that queries HelloAsso API V5, displays member data (txt/csv/json), dumps JSON files
- `invoicing/` — Makefile-based pipeline: JSON → Jinja2 HTML → WeasyPrint PDF → sendemail
- Docker container with SSH access for remote usage
- Config via JSON file with HelloAsso API credentials and SMTP settings

## Technical Context
- **Language**: Python 3
- **Dependencies**: requests, jinja2-cli, weasyprint, sendemail
- **API**: HelloAsso API V5 (OAuth2 client_credentials flow)
- **Invoice pipeline**: JSON data → Jinja2 template → HTML → WeasyPrint PDF
- **Email**: sendemail CLI tool via Makefile

## Target Architecture
- **Frontend**: Svelte SPA (Vite) — lightweight, compiled, no virtual DOM
- **Backend**: Python API (FastAPI) wrapping shared library extracted from helloasso.py
- **PDF generation**: WeasyPrint (keep existing Makefile pipeline)
- **Email**: sendemail CLI (keep existing Makefile pipeline)
- **Data storage**: Flat JSON files in `invoicing/<formSlug>/` (same as CLI)
- **No database** — status tracking via filesystem (presence of .pdf, .mail.log files)
- **Deployment**: Docker (extend existing Dockerfile)

## Architecture Principles
- **Shared library**: Extract core logic from `helloasso.py` into importable Python modules. CLI and web both import the same code.
- **Same file arborescence**: Web reads/writes the same `invoicing/<formSlug>/*.json` files as the CLI `--dump` command.
- **Keep sendemail**: Email sending stays via the existing Makefile/sendemail pipeline. Web triggers it, doesn't replace it.
- **No DB**: Invoice/email status derived from filesystem (`.pdf` exists = generated, `.mail.log` exists = sent).

## Scope
Small project (1-3 phases) focused on delivering a functional web dashboard.

## Constraints
- Must maintain full compatibility with existing CLI workflow
- Must preserve existing invoice template design and Makefile pipeline
- Must use same file arborescence as CLI (invoicing/<formSlug>/)
- Should work within the existing Docker deployment model
- ACS-specific branding and French language UI
- No database — flat files only
