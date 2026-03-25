import hmac
import os

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

router = APIRouter()


class LoginRequest(BaseModel):
    password: str


def _dashboard_password() -> str | None:
    """Return DASHBOARD_PASSWORD env var, or None if unset/empty."""
    val = os.environ.get("DASHBOARD_PASSWORD")
    return val if val else None


def require_auth(request: Request):
    """Dependency: allow if dev mode (no password set) or session is authenticated."""
    password = _dashboard_password()
    if password is None:
        return
    if not request.session.get("authenticated"):
        raise HTTPException(status_code=401, detail="Not authenticated")


@router.post("/login")
def login(body: LoginRequest, request: Request):
    """Authenticate with dashboard password and set session cookie."""
    expected = _dashboard_password()
    if expected is None:
        request.session["authenticated"] = True
        return {"status": "ok"}
    if not hmac.compare_digest(body.password, expected):
        raise HTTPException(status_code=401, detail="Invalid password")
    request.session["authenticated"] = True
    return {"status": "ok"}


@router.post("/logout")
def logout(request: Request):
    """Clear the session."""
    request.session.clear()
    return {"status": "ok"}


@router.get("/check")
def check_auth(request: Request, _: None = Depends(require_auth)):
    """Return 200 if authenticated, 401 if not."""
    return {"status": "authenticated"}
