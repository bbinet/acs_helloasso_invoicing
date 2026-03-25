"""Invoice API routes -- generate, download, preview, batch."""
import asyncio
import json
import os
import subprocess
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse

from app.routes.auth import require_auth
from lib.filesystem import get_invoicing_dir, get_member_status, scan_members
from lib.invoicing import ensure_symlinks, find_member_file, render_invoice_html, run_make_pdf

router = APIRouter()

# In-memory batch job tracking
_batch_jobs: dict = {}


def _format_make_error(prefix: str, exc: subprocess.CalledProcessError) -> str:
    """Format a subprocess error into a user-friendly message."""
    stderr = (exc.stderr or "").strip()
    if "libcairo" in stderr or "libpango" in stderr or "cannot open shared object" in stderr:
        return (
            f"{prefix}: bibliothèques système manquantes (cairo/pango). "
            "Installez-les avec: sudo apt install libpangocairo-1.0-0 "
            "(ou 'nix-shell -p cairo pango' sur NixOS)"
        )
    # Return last meaningful line of stderr
    lines = [l for l in stderr.splitlines() if l.strip() and not l.startswith("make")]
    msg = lines[-1] if lines else stderr[:200]
    return f"{prefix}: {msg}"


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
        detail = _format_make_error("Génération PDF échouée", exc)
        raise HTTPException(status_code=500, detail=detail)

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
        if job.get("cancelled"):
            break
        json_basename = os.path.splitext(os.path.basename(filepath))[0]
        try:
            run_make_pdf(invoicing_dir, json_basename)
            job["completed"] += 1
        except subprocess.CalledProcessError as exc:
            job["errors"].append({
                "file": json_basename,
                "error": _format_make_error("Erreur", exc),
            })
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

    pdf_path = filepath.rsplit(".json", 1)[0] + ".pdf"
    html_path = filepath.rsplit(".json", 1)[0] + ".html"
    for path in [pdf_path, html_path]:
        if os.path.isfile(path):
            os.remove(path)

    return {"status": "deleted", "member_id": member_id}
