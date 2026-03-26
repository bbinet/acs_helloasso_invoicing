import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from lib.config import load_config
from app.routes import auth, campaigns, emails, health, invoices, members, summary

app = FastAPI(title="ACS HelloAsso Dashboard")

# Session middleware — require SESSION_SECRET in production
_dashboard_password = os.environ.get("DASHBOARD_PASSWORD")
_session_secret = os.environ.get("SESSION_SECRET")
if _dashboard_password and not _session_secret:
    raise ValueError(
        "SESSION_SECRET environment variable is required when DASHBOARD_PASSWORD is set. "
        "Generate one with: python3 -c \"import secrets; print(secrets.token_hex(32))\""
    )
app.add_middleware(SessionMiddleware, secret_key=_session_secret or "dev-only-no-auth")

# CORS middleware — reject wildcard with credentials in production
_cors_origins = os.environ.get("CORS_ORIGINS", "")
if _dashboard_password and (not _cors_origins or _cors_origins == "*"):
    # Production mode: restrict to same-origin only (no CORS needed when served by Nginx)
    _cors_origins_list = []
else:
    _cors_origins_list = [o.strip() for o in _cors_origins.split(",") if o.strip()] if _cors_origins else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins_list,
    allow_credentials=bool(_cors_origins_list),
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "X-Requested-With"],
)

# Load config on startup
_conf_path = os.environ.get("CONF_PATH", "conf.json")
try:
    app.state.config = load_config(_conf_path)
except (FileNotFoundError, KeyError, Exception):
    app.state.config = None

# Include routers
app.include_router(health.router)
app.include_router(auth.router, prefix="/api/auth")
app.include_router(emails.router, prefix="/api/emails")
app.include_router(invoices.router, prefix="/api/invoices")
app.include_router(members.router, prefix="/api/members")
app.include_router(campaigns.router, prefix="/api/campaigns")
app.include_router(summary.router, prefix="/api/summary")
