"""Invoice API routes -- generate, download, preview, batch."""
import asyncio
import json
import os
import subprocess

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse

from app.routes.auth import require_auth
from lib.filesystem import (
    filter_members_by_ids, get_invoicing_dir, get_member_status,
    json_basename, scan_members, sibling_path,
)
from lib.invoicing import (
    cancel_batch_job, create_batch_job, ensure_symlinks, find_member_file,
    format_make_error, get_batch_job, render_invoice_html, run_make_pdf,
)

router = APIRouter()


def _validate_within_dir(filepath, base_dir):
    """Ensure filepath is within base_dir (prevent path traversal)."""
    real_base = os.path.realpath(base_dir)
    real_path = os.path.realpath(filepath)
    if not real_path.startswith(real_base + os.sep):
        raise HTTPException(status_code=403, detail="Access denied")


@router.post("/{member_id}/generate")
async def generate_invoice(
    member_id: int,
    request: Request,
    _: None = Depends(require_auth),
):
    """Generate a PDF invoice for a single member."""
    config = request.app.state.config
    invoicing_dir = get_invoicing_dir(config["conf"])
    filepath = find_member_file(invoicing_dir, member_id)
    if filepath is None:
        raise HTTPException(status_code=404, detail="Member not found")

    ensure_symlinks(invoicing_dir, config)

    try:
        await asyncio.to_thread(run_make_pdf, invoicing_dir, json_basename(filepath))
    except subprocess.CalledProcessError as exc:
        raise HTTPException(status_code=500, detail=format_make_error("G\u00e9n\u00e9ration PDF \u00e9chou\u00e9e", exc))

    return {"status": "generated", "member_id": member_id}


@router.get("/{member_id}/download")
def download_invoice(
    member_id: int,
    request: Request,
    _: None = Depends(require_auth),
):
    """Serve the generated PDF file for a member."""
    config = request.app.state.config
    invoicing_dir = get_invoicing_dir(config["conf"])
    filepath = find_member_file(invoicing_dir, member_id)
    if filepath is None:
        raise HTTPException(status_code=404, detail="Member not found")

    pdf_path = sibling_path(filepath, ".pdf")
    _validate_within_dir(pdf_path, invoicing_dir)
    if not os.path.isfile(pdf_path):
        raise HTTPException(status_code=404, detail="PDF not found -- generate invoice first")

    return FileResponse(pdf_path, media_type="application/pdf")


@router.get("/{member_id}/preview")
def preview_invoice(
    member_id: int,
    request: Request,
    _: None = Depends(require_auth),
):
    """Return an HTML preview of the invoice."""
    config = request.app.state.config
    invoicing_dir = get_invoicing_dir(config["conf"])
    filepath = find_member_file(invoicing_dir, member_id)
    if filepath is None:
        raise HTTPException(status_code=404, detail="Member not found")

    with open(filepath) as f:
        item_data = json.load(f)

    template_dir = os.path.dirname(invoicing_dir)
    signature_path = os.path.join(invoicing_dir, "signature.png")
    if not os.path.isfile(signature_path):
        signature_path = None

    return HTMLResponse(render_invoice_html(template_dir, item_data, signature_path))


def _run_batch_generation(job_id, invoicing_dir, pending_files, config):
    """Background task: generate PDFs for all pending members."""
    job = get_batch_job(job_id)
    ensure_symlinks(invoicing_dir, config)

    for filepath in pending_files:
        if job.get("cancelled"):
            break
        try:
            run_make_pdf(invoicing_dir, json_basename(filepath))
            job["completed"] += 1
        except subprocess.CalledProcessError as exc:
            job["errors"].append({"file": json_basename(filepath), "error": format_make_error("Erreur", exc)})
            job["completed"] += 1

    job["status"] = "cancelled" if job.get("cancelled") else "done"


@router.post("/batch")
def batch_generate(
    request: Request,
    background_tasks: BackgroundTasks,
    _: None = Depends(require_auth),
    member_ids: list[int] = Query(default=[]),
):
    """Start batch PDF generation. Optionally filter by member_ids."""
    config = request.app.state.config
    invoicing_dir = get_invoicing_dir(config["conf"])
    all_files = scan_members(invoicing_dir)

    if member_ids:
        all_files = filter_members_by_ids(all_files, member_ids)

    pending = [fp for fp in all_files if not get_member_status(fp)["invoice_generated"]]
    job_id = create_batch_job(len(pending))

    background_tasks.add_task(_run_batch_generation, job_id, invoicing_dir, pending, config)
    return {"job_id": job_id, "total": len(pending)}


@router.get("/batch/{job_id}/status")
def batch_status(job_id: str, _: None = Depends(require_auth)):
    """Poll batch generation progress."""
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


@router.delete("/{member_id}")
async def delete_invoice(
    member_id: int,
    request: Request,
    _: None = Depends(require_auth),
):
    """Delete a generated PDF invoice."""
    config = request.app.state.config
    invoicing_dir = get_invoicing_dir(config["conf"])
    filepath = find_member_file(invoicing_dir, member_id)
    if filepath is None:
        raise HTTPException(status_code=404, detail="Member not found")

    for ext in (".pdf", ".html"):
        path = sibling_path(filepath, ext)
        if os.path.isfile(path):
            os.remove(path)

    return {"status": "deleted", "member_id": member_id}
