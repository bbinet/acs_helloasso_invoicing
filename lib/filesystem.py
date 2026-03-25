import glob
import json
import os

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


def get_member_status(json_filepath):
    """Check if invoice PDF and mail log exist for a member JSON file."""
    base = json_filepath.rsplit('.json', 1)[0]
    return {
        "invoice_generated": os.path.isfile(base + ".pdf"),
        "email_sent": os.path.isfile(base + ".mail.log"),
    }
