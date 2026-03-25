import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from lib.config import load_config
from app.routes import auth, health

app = FastAPI(title="ACS HelloAsso Dashboard")

# Session middleware (secret key for signed cookies)
_session_secret = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.add_middleware(SessionMiddleware, secret_key=_session_secret)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load config on startup — handle missing config gracefully
_conf_path = os.environ.get("CONF_PATH", "conf.json")
try:
    app.state.config = load_config(_conf_path)
except (FileNotFoundError, KeyError, Exception):
    app.state.config = None

# Include routers
app.include_router(health.router)
app.include_router(auth.router, prefix="/api/auth")
