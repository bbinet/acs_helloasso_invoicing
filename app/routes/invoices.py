"""Invoice API routes -- generate, download, preview, batch."""
import asyncio
import json
import os
import subprocess
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse

from app.routes.auth import require_auth
from lib.filesystem import get_invoicing_dir, get_member_status, scan_members
from lib.invoicing import ensure_symlinks, find_member_file, render_invoice_html, run_make_pdf

router = APIRouter()

# In-memory batch job tracking
_batch_jobs: dict = {}


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
    json_basename = os.path.splitext(os.path.basename(filepath))[0]

    try:
        await asyncio.to_thread(run_make_pdf, invoicing_dir, json_basename)
    except subprocess.CalledProcessError as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": "PDF generation failed", "stderr": exc.stderr},
        )

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

    pdf_path = filepath.rsplit(".json", 1)[0] + ".pdf"
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

    # template.jinja2 lives in the parent of invoicing_dir (i.e. invoicing/)
    template_dir = os.path.dirname(invoicing_dir)

    signature_path = os.path.join(invoicing_dir, "signature.png")
    if not os.path.isfile(signature_path):
        signature_path = None

    html = render_invoice_html(template_dir, item_data, signature_path)
    return HTMLResponse(html)


def _run_batch_generation(job_id: str, invoicing_dir: str, pending_files: list, config: dict):
    """Background task: generate PDFs for all pending members."""
    job = _batch_jobs[job_id]
    ensure_symlinks(invoicing_dir, config)

    for filepath in pending_files:
        json_basename = os.path.splitext(os.path.basename(filepath))[0]
        try:
            run_make_pdf(invoicing_dir, json_basename)
            job["completed"] += 1
        except subprocess.CalledProcessError as exc:
            job["errors"].append({"file": json_basename, "error": exc.stderr})
            job["completed"] += 1

    job["status"] = "done"


@router.post("/batch")
def batch_generate(
    request: Request,
    background_tasks: BackgroundTasks,
    _: None = Depends(require_auth),
):
    """Start batch PDF generation for all members without invoices."""
    config = request.app.state.config
    invoicing_dir = get_invoicing_dir(config["conf"])
    all_files = scan_members(invoicing_dir)

    # Filter to members without a PDF
    pending = [fp for fp in all_files if not get_member_status(fp)["invoice_generated"]]

    job_id = str(uuid4())
    _batch_jobs[job_id] = {
        "total": len(pending),
        "completed": 0,
        "errors": [],
        "status": "running",
    }

    background_tasks.add_task(_run_batch_generation, job_id, invoicing_dir, pending, config)
    return {"job_id": job_id, "total": len(pending)}


@router.get("/batch/{job_id}/status")
def batch_status(
    job_id: str,
    _: None = Depends(require_auth),
):
    """Poll batch generation progress."""
    job = _batch_jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
