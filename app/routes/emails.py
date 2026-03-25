"""Email API routes -- send single and batch emails."""
import asyncio
import os
import subprocess
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request

from app.routes.auth import require_auth
from lib.filesystem import get_invoicing_dir, get_member_status, scan_members
from lib.invoicing import ensure_symlinks, find_member_file, run_make_email

router = APIRouter()

# In-memory batch job tracking
_batch_jobs: dict = {}


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

    try:
        await asyncio.to_thread(run_make_email, invoicing_dir, json_basename)
    except subprocess.CalledProcessError as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": "Email sending failed", "stderr": exc.stderr},
        )

    return {"status": "sent", "member_id": member_id}


def _run_batch_emails(job_id: str, invoicing_dir: str, pending_files: list, config: dict):
    """Background task: send emails for all pending members."""
    job = _batch_jobs[job_id]
    ensure_symlinks(invoicing_dir, config)

    for filepath in pending_files:
        json_basename = os.path.splitext(os.path.basename(filepath))[0]
        try:
            run_make_email(invoicing_dir, json_basename)
            job["completed"] += 1
        except subprocess.CalledProcessError as exc:
            job["errors"].append({"file": json_basename, "error": exc.stderr})
            job["completed"] += 1

    job["status"] = "done"


@router.post("/batch")
def batch_send(
    request: Request,
    background_tasks: BackgroundTasks,
    _: None = Depends(require_auth),
):
    """Start batch email sending for members with PDFs but no mail log."""
    config = request.app.state.config
    invoicing_dir = get_invoicing_dir(config["conf"])
    all_files = scan_members(invoicing_dir)

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
