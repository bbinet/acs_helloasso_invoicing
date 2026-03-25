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
- **Frontend**: React (or Vue) SPA dashboard
- **Backend**: Python API (FastAPI or Flask) wrapping existing HelloAsso logic
- **PDF generation**: WeasyPrint (keep existing approach)
- **Database**: Optional — for caching members, tracking invoice/email status
- **Deployment**: Docker (extend existing Dockerfile)

## Scope
Small project (1-3 phases) focused on delivering a functional web dashboard.

## Constraints
- Must maintain compatibility with HelloAsso API V5
- Must preserve existing invoice template design
- Should work within the existing Docker deployment model
- ACS-specific branding and French language UI
