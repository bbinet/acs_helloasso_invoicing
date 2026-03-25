"""Summary API routes."""
import json

from fastapi import APIRouter, Depends, Request

from app.routes.auth import require_auth
from lib.filesystem import get_invoicing_dir, scan_members
from lib.models import parse_member, build_summary

router = APIRouter()


@router.get("")
def get_summary(
    request: Request,
    _: None = Depends(require_auth),
):
    """Return activity breakdown summary."""
    config = request.app.state.config
    invoicing_dir = get_invoicing_dir(config["conf"])
    filepaths = scan_members(invoicing_dir)

    items_and_members = []
    for fp in filepaths:
        with open(fp) as f:
            item = json.load(f)
        member = parse_member(item)
        items_and_members.append((item, member))

    summary_data = build_summary(items_and_members)

    activities = []
    for name, members in summary_data:
        activities.append({
            "name": name,
            "count": len(members),
            "members": members,
        })

    return {
        "activities": activities,
        "total": len(items_and_members),
    }
