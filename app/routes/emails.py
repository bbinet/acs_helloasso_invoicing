"""Email API routes -- send single and batch emails."""
import asyncio
import os
import subprocess
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request

from app.routes.auth import require_auth
from lib.filesystem import get_invoicing_dir, get_member_status, scan_members
from lib.invoicing import ensure_symlinks, find_member_file, run_make_email

router = APIRouter()

# In-memory batch job tracking
_batch_jobs: dict = {}


def _format_make_error(prefix: str, exc: subprocess.CalledProcessError) -> str:
    """Format a subprocess error into a user-friendly message."""
    stderr = (exc.stderr or "").strip()
    lines = [l for l in stderr.splitlines() if l.strip() and not l.startswith("make")]
    msg = lines[-1] if lines else stderr[:200]
    return f"{prefix}: {msg}"


@router.post("/{member_id}/send")
async def send_email(
    member_id: int,
    request: Request,
    _: None = Depends(require_auth),
):
    """Send an invoice email for a single member."""
    config = request.app.state.config
    invoicing_dir = get_invoicing_dir(config["conf"])
    filepath = find_member_file(invoicing_dir, member_id)
    if filepath is None:
        raise HTTPException(status_code=404, detail="Member not found")

    # Check that PDF exists -- can't email without invoice
    pdf_path = filepath.rsplit(".json", 1)[0] + ".pdf"
    if not os.path.isfile(pdf_path):
        raise HTTPException(status_code=400, detail="PDF not found -- generate invoice first")

    ensure_symlinks(invoicing_dir, config)
    json_basename = os.path.splitext(os.path.basename(filepath))[0]

    # Remove existing mail.log so make will actually re-send
    mail_log = filepath.rsplit(".json", 1)[0] + ".mail.log"
    if os.path.isfile(mail_log):
        os.remove(mail_log)

    try:
        await asyncio.to_thread(run_make_email, invoicing_dir, json_basename)
    except subprocess.CalledProcessError as exc:
        detail = _format_make_error("Envoi email échoué", exc)
        raise HTTPException(status_code=500, detail=detail)

    return {"status": "sent", "member_id": member_id}


def _run_batch_emails(job_id: str, invoicing_dir: str, pending_files: list, config: dict):
    """Background task: send emails for all pending members."""
    job = _batch_jobs[job_id]
    ensure_symlinks(invoicing_dir, config)

    for filepath in pending_files:
        if job.get("cancelled"):
            break
        json_basename = os.path.splitext(os.path.basename(filepath))[0]
        try:
            run_make_email(invoicing_dir, json_basename)
            job["completed"] += 1
        except subprocess.CalledProcessError as exc:
            job["errors"].append({
                "file": json_basename,
                "error": _format_make_error("Erreur", exc),
            })
            job["completed"] += 1

    job["status"] = "cancelled" if job.get("cancelled") else "done"


@router.post("/batch")
def batch_send(
    request: Request,
    background_tasks: BackgroundTasks,
    _: None = Depends(require_auth),
    member_ids: list[int] = Query(default=[]),
):
    """Start batch email sending. Optionally filter by member_ids."""
    config = request.app.state.config
    invoicing_dir = get_invoicing_dir(config["conf"])
    all_files = scan_members(invoicing_dir)

    # Filter to specified member_ids if provided
    if member_ids and len(member_ids) > 0:
        id_set = set(member_ids)
        filtered = []
        for fp in all_files:
            with open(fp) as f:
                item = json.load(f)
            if item["id"] in id_set:
                filtered.append(fp)
        all_files = filtered

    # Filter to members with PDF but without mail.log
    pending = [
        fp for fp in all_files
        if get_member_status(fp)["invoice_generated"]
        and not get_member_status(fp)["email_sent"]
    ]

    job_id = str(uuid4())
    _batch_jobs[job_id] = {
        "total": len(pending),
        "completed": 0,
        "errors": [],
        "status": "running",
    }

    background_tasks.add_task(_run_batch_emails, job_id, invoicing_dir, pending, config)
    return {"job_id": job_id, "total": len(pending)}


@router.get("/batch/{job_id}/status")
def batch_status(
    job_id: str,
    _: None = Depends(require_auth),
):
    """Poll batch email sending progress."""
    job = _batch_jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/batch/{job_id}/cancel")
def batch_cancel(
    job_id: str,
    _: None = Depends(require_auth),
):
    """Cancel a running batch job."""
    job = _batch_jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    job["cancelled"] = True
    return {"status": "cancelling"}
