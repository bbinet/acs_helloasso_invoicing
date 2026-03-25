import glob
import json
import os
import subprocess
from datetime import date

from jinja2 import Environment, FileSystemLoader


def ensure_symlinks(invoicing_dir, config):
    """Create symlinks for Makefile, conf.json, and signature.png if missing."""
    # Makefile -> ../Makefile (relative)
    makefile_link = os.path.join(invoicing_dir, "Makefile")
    if not os.path.islink(makefile_link):
        os.symlink("../Makefile", makefile_link)

    # conf.json -> absolute path to the real conf.json
    conf_link = os.path.join(invoicing_dir, "conf.json")
    if not os.path.islink(conf_link):
        conf_dir = config.get("conf", {}).get("dir", "")
        if conf_dir:
            conf_target = os.path.join(conf_dir, "conf.json")
            os.symlink(conf_target, conf_link)

    # signature.png -> ../signature.png (relative) if parent has one
    sig_link = os.path.join(invoicing_dir, "signature.png")
    if not os.path.islink(sig_link):
        parent_sig = os.path.join(os.path.dirname(invoicing_dir), "signature.png")
        if os.path.isfile(parent_sig):
            os.symlink("../signature.png", sig_link)


def find_member_file(invoicing_dir, member_id):
    """Scan JSON files in directory, return filepath where item id matches.

    Skips conf.json. Returns None if not found.
    """
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
    """Run make to generate PDF from a member JSON file.

    Args:
        invoicing_dir: Directory containing the Makefile symlink.
        json_basename: Basename of the JSON file (without extension).

    Returns:
        subprocess.CompletedProcess result.
    """
    return subprocess.run(
        ["make", f"{json_basename}.pdf"],
        cwd=invoicing_dir,
        capture_output=True,
        text=True,
        check=True,
    )


def run_make_email(invoicing_dir, json_basename):
    """Run make to send invoice email for a member.

    Args:
        invoicing_dir: Directory containing the Makefile symlink.
        json_basename: Basename of the JSON file (without extension).

    Returns:
        subprocess.CompletedProcess result.
    """
    return subprocess.run(
        ["make", f"{json_basename}.mail.log"],
        cwd=invoicing_dir,
        capture_output=True,
        text=True,
        check=True,
    )


def render_invoice_html(template_dir, item_data, signature_path=None):
    """Render the invoice Jinja2 template with item data.

    Args:
        template_dir: Directory containing template.jinja2.
        item_data: HelloAsso item dict (spread as top-level template vars).
        signature_path: Optional path to signature image file.

    Returns:
        Rendered HTML string.
    """
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("template.jinja2")

    context = dict(item_data)
    context["date"] = date.today().strftime("%d/%m/%Y")
    context["signature"] = signature_path or ""

    return template.render(**context)
