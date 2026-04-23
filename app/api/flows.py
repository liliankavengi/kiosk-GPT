"""
WhatsApp Flows data exchange endpoint.
Handles registration and other Flow form submissions.
"""

import json
from fastapi import APIRouter, Request
from app.db import insert_row, get_single_row
from app.utils import logger

router = APIRouter(prefix="/flows", tags=["flows"])


@router.post("/data-exchange")
async def flow_data_exchange(request: Request):
    """
    Handle WhatsApp Flow data exchange requests.
    This endpoint is called by WhatsApp Flows Engine when a user
    submits a form or navigates between screens.
    """
    body = await request.json()
    logger.info(f"Flow data exchange: {json.dumps(body, indent=2)}")

    action = body.get("action")
    screen = body.get("screen")
    data = body.get("data", {})
    flow_token = body.get("flow_token", "")

    # ── Health check (ping from Meta) ────────────────────
    if action == "ping":
        return {
            "version": "3.0",
            "data": {"status": "active"},
        }

    # ── Registration form submission ─────────────────────
    if action == "data_exchange" and screen == "REGISTRATION":
        duka_name = data.get("duka_name", "").strip()
        inventory_type = data.get("inventory_type", "general")
        lightning_address = data.get("lightning_address", "").strip()

        if not duka_name:
            return {
                "version": "3.0",
                "screen": "REGISTRATION",
                "data": {
                    "error_message": "Please enter your duka name.",
                },
            }

        # Extract phone number from flow_token (set during send_flow)
        # In production, the phone number is passed via the flow_token
        phone_number = flow_token  # We'll encode the phone in the token

        # Check if already registered
        existing = await get_single_row("dukas", {"phone_number": phone_number})
        if existing:
            return {
                "version": "3.0",
                "screen": "SUCCESS",
                "data": {
                    "message": f"Welcome back, {existing['duka_name']}! You're already registered. Just send your sales in Sheng or Swahili.",
                },
            }

        # Create the duka
        duka_data = {
            "phone_number": phone_number,
            "wa_phone_id": phone_number,
            "duka_name": duka_name,
            "inventory_type": inventory_type,
            "lightning_address": lightning_address or None,
        }

        try:
            duka = await insert_row("dukas", duka_data)
            logger.info(f"New duka registered: {duka_name} ({phone_number})")

            return {
                "version": "3.0",
                "screen": "SUCCESS",
                "data": {
                    "message": f"✅ {duka_name} registered successfully!\n\nYou can now send sales in Sheng or Swahili, e.g.:\n\"Nimeuza mkate tatu na maziwa mbili\"",
                },
            }
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            return {
                "version": "3.0",
                "screen": "REGISTRATION",
                "data": {
                    "error_message": "Registration failed. Please try again.",
                },
            }

    # ── Default: unknown action ──────────────────────────
    return {
        "version": "3.0",
        "data": {"status": "unknown_action"},
    }
