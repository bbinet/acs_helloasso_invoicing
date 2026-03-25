"""Campaigns API routes."""
import asyncio
import json

from fastapi import APIRouter, Depends, Request

from app.routes.auth import require_auth
from lib.config import conf_get
from lib.filesystem import get_invoicing_dir, get_member_filepath, dump_item
from lib.helloasso_client import HelloAssoClient

router = APIRouter()


@router.get("")
def get_campaigns(
    request: Request,
    _: None = Depends(require_auth),
):
    """Return campaign config info."""
    config = request.app.state.config
    conf = config["conf"]
    ha = conf_get(conf, "helloasso")
    return {
        "formSlug": ha["formSlug"],
        "formType": ha["formType"],
        "organizationName": ha["organization_name"],
    }


def _sync_refresh(config):
    """Synchronous refresh: fetch items from HelloAsso and dump to JSON files."""
    client = HelloAssoClient(config)
    conf = config["conf"]
    count = 0
    for item in client.GetData():
        filepath = get_member_filepath(conf, item)
        dump_item(filepath, item)
        count += 1
    return count


@router.post("/refresh")
async def refresh_campaigns(
    request: Request,
    _: None = Depends(require_auth),
):
    """Fetch items from HelloAsso API and save as JSON files."""
    config = request.app.state.config
    count = await asyncio.to_thread(_sync_refresh, config)
    form_slug = conf_get(config["conf"], "helloasso", "formSlug")
    return {"count": count, "formSlug": form_slug}
