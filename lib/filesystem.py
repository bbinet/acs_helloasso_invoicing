import glob
import json
import os
from datetime import datetime

from lib.config import conf_get
from lib.models import get_member_filename


def get_invoicing_dir(conf):
    """Return the invoicing directory path from config."""
    return os.path.join(conf_get(conf, 'dir'), 'invoicing',
                        conf_get(conf, 'helloasso', 'formSlug'))


def get_member_filepath(conf, item):
    """Return full filepath for a member's JSON data file."""
    return os.path.join(get_invoicing_dir(conf), get_member_filename(item))


def dump_item(filepath, item):
    """Write item data as JSON to filepath, creating directories as needed."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(item, f, indent=4)


def scan_members(invoicing_dir):
    """Read all .json files from directory, excluding conf.json."""
    pattern = os.path.join(invoicing_dir, "*.json")
    return [p for p in sorted(glob.glob(pattern))
            if os.path.basename(p) != "conf.json"]


def filter_members_by_ids(filepaths, member_ids):
    """Filter member filepaths to only those whose item ID is in member_ids."""
    id_set = set(member_ids)
    filtered = []
    for fp in filepaths:
        with open(fp) as f:
            item = json.load(f)
        if item["id"] in id_set:
            filtered.append(fp)
    return filtered


def json_basename(filepath):
    """Extract basename without .json extension from a filepath."""
    return os.path.splitext(os.path.basename(filepath))[0]


def sibling_path(json_filepath, ext):
    """Return path with a different extension for a .json filepath."""
    return json_filepath.rsplit('.json', 1)[0] + ext


def get_member_status(json_filepath):
    """Check invoice PDF and mail log status for a member JSON file.

    Returns dict with:
    - invoice_generated: bool (PDF file exists)
    - invoice_date: str|None (PDF file modification date)
    - email_sent: bool (mail.log exists and is not an error log)
    - email_error: bool (error_*.mail.log exists)
    - email_date: str|None (date extracted from mail.log first line)
    """
    base = json_filepath.rsplit('.json', 1)[0]
    basename = os.path.basename(base)
    dirpath = os.path.dirname(json_filepath)
    pdf_path = base + ".pdf"

    status = {
        "invoice_generated": os.path.isfile(pdf_path),
        "invoice_date": None,
        "email_sent": False,
        "email_error": False,
        "email_date": None,
    }

    if status["invoice_generated"]:
        try:
            mtime = os.path.getmtime(pdf_path)
            status["invoice_date"] = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
        except OSError:
            pass

    mail_log = base + ".mail.log"
    error_log = os.path.join(dirpath, f"error_{basename}.mail.log")

    if os.path.isfile(mail_log):
        status["email_sent"] = True
        try:
            with open(mail_log) as f:
                content = f.read()
            first_line = content.strip().split("\n")[0]
            date_part = first_line.split(" ")[0]
            if "T" in date_part or "-" in date_part:
                status["email_date"] = date_part.split("T")[0]
        except (OSError, IndexError):
            pass
    elif os.path.isfile(error_log):
        status["email_error"] = True

    return status
