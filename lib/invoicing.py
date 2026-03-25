import glob
import json
import os
import subprocess
from datetime import date
from uuid import uuid4

from jinja2 import Environment, FileSystemLoader, select_autoescape


def ensure_symlinks(invoicing_dir, config):
    """Create symlinks for Makefile, conf.json, and signature.png if missing."""
    makefile_link = os.path.join(invoicing_dir, "Makefile")
    if not os.path.islink(makefile_link):
        os.symlink("../Makefile", makefile_link)

    conf_link = os.path.join(invoicing_dir, "conf.json")
    if not os.path.islink(conf_link):
        conf_dir = config.get("conf", {}).get("dir", "")
        if conf_dir:
            conf_target = os.path.join(conf_dir, "conf.json")
            os.symlink(conf_target, conf_link)

    sig_link = os.path.join(invoicing_dir, "signature.png")
    if not os.path.islink(sig_link):
        parent_sig = os.path.join(os.path.dirname(invoicing_dir), "signature.png")
        if os.path.isfile(parent_sig):
            os.symlink("../signature.png", sig_link)


def find_member_file(invoicing_dir, member_id):
    """Scan JSON files in directory, return filepath where item id matches."""
    pattern = os.path.join(invoicing_dir, "*.json")
    for filepath in sorted(glob.glob(pattern)):
        if os.path.basename(filepath) == "conf.json":
            continue
        with open(filepath, "r") as f:
            data = json.load(f)
        if data.get("id") == int(member_id):
            return filepath
    return None


def run_make_pdf(invoicing_dir, json_basename):
    """Run make to generate PDF from a member JSON file."""
    return subprocess.run(
        ["make", f"{json_basename}.pdf"],
        cwd=invoicing_dir, capture_output=True, text=True, check=True,
    )


def run_make_email(invoicing_dir, json_basename):
    """Run make to send invoice email for a member."""
    return subprocess.run(
        ["make", f"{json_basename}.mail.log"],
        cwd=invoicing_dir, capture_output=True, text=True, check=True,
    )


def render_invoice_html(template_dir, item_data, signature_path=None):
    """Render the invoice Jinja2 template with item data."""
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(default_for_string=True, default=True),
    )
    template = env.get_template("template.jinja2")
    context = dict(item_data)
    context["date"] = date.today().strftime("%d/%m/%Y")
    context["signature"] = signature_path or ""
    return template.render(**context)


def format_make_error(prefix, exc):
    """Format a subprocess CalledProcessError into a user-friendly message."""
    stderr = (exc.stderr or "").strip()
    if "libcairo" in stderr or "libpango" in stderr or "cannot open shared object" in stderr:
        return (
            f"{prefix}: biblioth\u00e8ques syst\u00e8me manquantes (cairo/pango). "
            "Installez-les avec: sudo apt install libpangocairo-1.0-0 "
            "(ou 'nix-shell -p cairo pango' sur NixOS)"
        )
    lines = [l for l in stderr.splitlines() if l.strip() and not l.startswith("make")]
    msg = lines[-1] if lines else stderr[:200]
    return f"{prefix}: {msg}"


# Shared batch job management
_batch_jobs: dict = {}
_MAX_COMPLETED_JOBS = 50


def create_batch_job(total):
    """Create a new batch job and return its ID."""
    # Clean up old completed jobs if too many
    completed = [k for k, v in _batch_jobs.items() if v["status"] in ("done", "cancelled")]
    if len(completed) > _MAX_COMPLETED_JOBS:
        for k in completed[:len(completed) - _MAX_COMPLETED_JOBS]:
            del _batch_jobs[k]

    job_id = str(uuid4())
    _batch_jobs[job_id] = {
        "total": total,
        "completed": 0,
        "errors": [],
        "status": "running",
    }
    return job_id


def get_batch_job(job_id):
    """Get a batch job by ID, or None if not found."""
    return _batch_jobs.get(job_id)


def cancel_batch_job(job_id):
    """Mark a batch job as cancelled."""
    job = _batch_jobs.get(job_id)
    if job:
        job["cancelled"] = True
