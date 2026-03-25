"""Email API routes -- send single and batch emails."""
import asyncio
import os
import subprocess

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request

from app.routes.auth import require_auth
from lib.filesystem import (
    filter_members_by_ids, get_invoicing_dir, get_member_status,
    json_basename, scan_members, sibling_path,
)
from lib.invoicing import (
    cancel_batch_job, create_batch_job, ensure_symlinks, find_member_file,
    format_make_error, get_batch_job, run_make_email,
)

router = APIRouter()


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

    pdf_path = sibling_path(filepath, ".pdf")
    if not os.path.isfile(pdf_path):
        raise HTTPException(status_code=400, detail="PDF not found -- generate invoice first")

    ensure_symlinks(invoicing_dir, config)

    # Remove existing mail.log so make will actually re-send
    mail_log = sibling_path(filepath, ".mail.log")
    if os.path.isfile(mail_log):
        os.remove(mail_log)

    try:
        await asyncio.to_thread(run_make_email, invoicing_dir, json_basename(filepath))
    except subprocess.CalledProcessError as exc:
        raise HTTPException(status_code=500, detail=format_make_error("Envoi email \u00e9chou\u00e9", exc))

    return {"status": "sent", "member_id": member_id}


def _run_batch_emails(job_id, invoicing_dir, pending_files, config):
    """Background task: send emails for all pending members."""
    job = get_batch_job(job_id)
    ensure_symlinks(invoicing_dir, config)

    for filepath in pending_files:
        if job.get("cancelled"):
            break
        try:
            run_make_email(invoicing_dir, json_basename(filepath))
            job["completed"] += 1
        except subprocess.CalledProcessError as exc:
            job["errors"].append({"file": json_basename(filepath), "error": format_make_error("Erreur", exc)})
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

    if member_ids:
        all_files = filter_members_by_ids(all_files, member_ids)

    # Filter to members with PDF but without mail.log (single status call per file)
    pending = []
    for fp in all_files:
        status = get_member_status(fp)
        if status["invoice_generated"] and not status["email_sent"]:
            pending.append(fp)

    job_id = create_batch_job(len(pending))
    background_tasks.add_task(_run_batch_emails, job_id, invoicing_dir, pending, config)
    return {"job_id": job_id, "total": len(pending)}


@router.get("/batch/{job_id}/status")
def batch_status(job_id: str, _: None = Depends(require_auth)):
    """Poll batch email sending progress."""
    job = get_batch_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/batch/{job_id}/cancel")
def batch_cancel(job_id: str, _: None = Depends(require_auth)):
    """Cancel a running batch job."""
    job = get_batch_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    cancel_batch_job(job_id)
    return {"status": "cancelling"}
