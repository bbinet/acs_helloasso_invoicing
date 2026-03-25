"""Members API routes."""
import csv
import io
import json
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.routes.auth import require_auth
from lib.filesystem import get_invoicing_dir, scan_members, get_member_status
from lib.models import EA_NAME, has_refunds, parse_member

router = APIRouter()


def _load_members(config):
    """Load all member items from invoicing directory.

    Returns list of (filepath, item) tuples.
    """
    invoicing_dir = get_invoicing_dir(config["conf"])
    filepaths = scan_members(invoicing_dir)
    results = []
    for fp in filepaths:
        with open(fp) as f:
            item = json.load(f)
        results.append((fp, item))
    return results


def _member_to_response(filepath, item):
    """Convert a raw item + filepath into a response dict."""
    member = parse_member(item)
    status = get_member_status(filepath)
    return {
        "id": item["id"],
        "filepath": filepath,
        "order_date": item["order"]["date"].split("T")[0],
        **member,
        **status,
    }


@router.get("")
def list_members(
    request: Request,
    activity: Optional[str] = None,
    refund_filtered: Optional[bool] = None,
    ea_filter: Optional[bool] = None,
    _: None = Depends(require_auth),
):
    """Return list of all members with optional filtering."""
    config = request.app.state.config
    items = _load_members(config)
    results = []

    for filepath, item in items:
        if refund_filtered and has_refunds(item):
            continue

        if ea_filter and item["name"] != EA_NAME:
            continue

        member_resp = _member_to_response(filepath, item)

        # Activity filter (regex on activities list)
        if activity:
            if not any(re.search(activity, a, re.IGNORECASE) for a in member_resp.get("activities", [])):
                continue

        results.append(member_resp)

    return results


@router.get("/export/csv")
def export_csv(
    request: Request,
    _: None = Depends(require_auth),
):
    """Export members as CSV."""
    config = request.app.state.config
    items = _load_members(config)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Num", "HelloAssoID", "OrderDate", "FirstName", "LastName",
                     "Company", "EmileAllais", "Activities"])

    for idx, (filepath, item) in enumerate(items, 1):
        member = parse_member(item)
        order_date = item["order"]["date"].split("T")[0]
        writer.writerow([
            idx,
            item["id"],
            order_date,
            member["firstname"],
            member["lastname"],
            member.get("company", ""),
            "Oui" if member.get("ea") else "Non",
            " | ".join(member.get("activities", [])),
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=members.csv"},
    )


@router.get("/{member_id}")
def get_member(
    member_id: int,
    request: Request,
    _: None = Depends(require_auth),
):
    """Return a single member by ID."""
    config = request.app.state.config
    items = _load_members(config)

    for filepath, item in items:
        if item["id"] == member_id:
            return _member_to_response(filepath, item)

    raise HTTPException(status_code=404, detail="Member not found")
