"""
WhatsApp webhook handler.
Handles verification (GET) and incoming messages (POST).
This is the main message router for the entire application.
"""

import hashlib
import hmac
import json
import uuid

from fastapi import APIRouter, Query, Request, Response

from app.config import get_settings
from app.db import get_single_row
from app.models.webhook import WhatsAppWebhookPayload
from app.services import whatsapp, ai_parser, inventory
from app.services.lightning import lightning_service
from app.services.receipts import generate_receipt
from app.utils import logger
from app.utils.constants import BTN_REORDER_YES, BTN_REORDER_NO

router = APIRouter(tags=["webhooks"])

# ── In-memory state for pending reorders ────────────────
# Maps phone_number → low_stock_items (for the YES/NO button flow)
_pending_reorders: dict[str, list[dict]] = {}


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """
    WhatsApp webhook verification (GET).
    Meta sends a GET request with a challenge to verify the webhook URL.
    """
    settings = get_settings()

    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        logger.info("Webhook verified successfully")
        return Response(content=hub_challenge, media_type="text/plain")

    logger.warning(f"Webhook verification failed: mode={hub_mode}")
    return Response(content="Forbidden", status_code=403)


@router.post("/webhook")
async def handle_webhook(request: Request):
    """
    WhatsApp webhook handler (POST).
    Processes incoming messages and routes them to the appropriate handler.
    """
    body = await request.json()
    logger.info(f"Webhook received: {json.dumps(body, indent=2)[:500]}")

    try:
        payload = WhatsAppWebhookPayload(**body)
    except Exception as e:
        logger.error(f"Failed to parse webhook payload: {e}")
        return {"status": "ok"}

    # Process each entry/change
    if payload.entry:
        for entry in payload.entry:
            if entry.changes:
                for change in entry.changes:
                    if change.value and change.value.messages:
                        for message in change.value.messages:
                            await _route_message(message)

    # Always return 200 to WhatsApp
    return {"status": "ok"}


async def _route_message(message):
    """Route an incoming message to the appropriate handler."""
    from_number = message.from_ or ""
    msg_type = message.type or ""
    msg_id = message.id or ""

    logger.info(f"Message from {from_number}: type={msg_type}")

    # Mark as read
    if msg_id:
        try:
            await whatsapp.mark_as_read(msg_id)
        except Exception:
            pass  # Non-critical

    # ── Text messages ────────────────────────────────────
    if msg_type == "text" and message.text:
        text = message.text.body.strip()
        await _handle_text_message(from_number, text)

    # ── Interactive replies (buttons / flows) ────────────
    elif msg_type == "interactive" and message.interactive:
        await _handle_interactive(from_number, message.interactive)

    else:
        logger.info(f"Unhandled message type: {msg_type}")


async def _handle_text_message(phone: str, text: str):
    """Handle incoming text messages."""
    text_lower = text.lower().strip()

    # ── Greeting → Registration / Welcome ────────────────
    if text_lower in ("hi", "hello", "hey", "habari", "sasa", "niaje"):
        duka = await get_single_row("dukas", {"phone_number": phone})

        if duka:
            await whatsapp.send_text(
                phone,
                f"👋 Karibu tena, *{duka['duka_name']}*!\n\n"
                f"Send your sales in Sheng or Swahili.\n"
                f"Example: \"Nimeuza mkate tatu na maziwa mbili\"",
            )
        else:
            # Send registration flow
            settings = get_settings()
            flow_id = settings.whatsapp_business_account_id  # Replace with actual Flow ID
            flow_token = phone  # Use phone as token for now

            try:
                await whatsapp.send_flow(
                    to=phone,
                    flow_id=flow_id,
                    flow_token=flow_token,
                    header="🏪 Register Your Duka",
                    body="Welcome to Kiosk-GPT! Fill in the form below to get started.",
                )
            except Exception as e:
                logger.error(f"Failed to send flow: {e}")
                # Fallback: text-based registration
                await whatsapp.send_text(
                    phone,
                    "👋 Welcome to *Kiosk-GPT*!\n\n"
                    "To register, send:\n"
                    "REGISTER <duka name> <type>\n\n"
                    "Example: REGISTER Kavengi's Kiosk grocery",
                )
        return

    # ── Text-based registration fallback ─────────────────
    if text_lower.startswith("register "):
        parts = text[9:].strip().rsplit(" ", 1)
        duka_name = parts[0] if parts else "My Duka"
        inv_type = parts[1].lower() if len(parts) > 1 else "general"

        if inv_type not in ("grocery", "electronics", "general"):
            inv_type = "general"

        from app.db import insert_row
        try:
            await insert_row("dukas", {
                "phone_number": phone,
                "wa_phone_id": phone,
                "duka_name": duka_name,
                "inventory_type": inv_type,
            })
            await whatsapp.send_text(
                phone,
                f"✅ *{duka_name}* registered!\n\n"
                f"Type: {inv_type.title()}\n\n"
                f"Now send sales like: \"Nimeuza mkate tatu\"",
            )
        except Exception as e:
            logger.error(f"Registration error: {e}")
            await whatsapp.send_text(phone, "⚠️ Registration failed. You may already be registered. Try sending a sale!")
        return

    # ── Sale message → AI Parser ─────────────────────────
    duka = await get_single_row("dukas", {"phone_number": phone})
    if not duka:
        await whatsapp.send_text(
            phone,
            "👋 You're not registered yet! Send *Hi* to get started.",
        )
        return

    # Parse with AI
    parse_result = await ai_parser.parse_sale_message(text)

    if not parse_result.items or parse_result.confidence < 0.5:
        await whatsapp.send_text(
            phone,
            "🤔 I couldn't understand that message.\n\n"
            "Try something like:\n"
            "• \"Nimeuza mkate tatu\"\n"
            "• \"Sold 5 sugar and 3 bread\"\n"
            "• \"Nimepokea maziwa kumi\" (restocked)",
        )
        return

    # Process the sale
    result = await inventory.process_sale(duka["id"], parse_result, text)

    # Send sale confirmation
    response_text = inventory.format_sale_response(result)
    await whatsapp.send_text(phone, response_text)

    # ── Low stock → Offer re-order ───────────────────────
    if result["low_stock_items"]:
        _pending_reorders[phone] = result["low_stock_items"]

        low_items = ", ".join(
            f"{i['item_name'].title()} ({i['remaining']} left)"
            for i in result["low_stock_items"]
        )

        await whatsapp.send_interactive_buttons(
            to=phone,
            body=f"⚠️ Low stock: {low_items}\n\nWould you like to re-order from your wholesaler via Lightning?",
            buttons=[
                {"id": BTN_REORDER_YES, "title": "⚡ Yes, Re-order"},
                {"id": BTN_REORDER_NO, "title": "Not now"},
            ],
        )


async def _handle_interactive(phone: str, interactive):
    """Handle interactive message replies (buttons and flows)."""

    # ── Button replies ───────────────────────────────────
    if interactive.type == "button_reply" and interactive.button_reply:
        button_id = interactive.button_reply.id

        if button_id == BTN_REORDER_YES:
            await _process_reorder(phone)

        elif button_id == BTN_REORDER_NO:
            if phone in _pending_reorders:
                del _pending_reorders[phone]
            await whatsapp.send_text(phone, "👍 No problem. I'll remind you next time stock is low.")

    # ── Flow replies (nfm_reply) ─────────────────────────
    elif interactive.type == "nfm_reply" and interactive.nfm_reply:
        logger.info(f"Flow reply from {phone}: {interactive.nfm_reply}")
        # Flow replies are handled by the /flows/data-exchange endpoint
        # This is just for logging


async def _process_reorder(phone: str):
    """Process a reorder request via Lightning Network."""
    low_stock_items = _pending_reorders.pop(phone, [])

    if not low_stock_items:
        await whatsapp.send_text(phone, "No pending reorder found.")
        return

    duka = await get_single_row("dukas", {"phone_number": phone})
    if not duka:
        return

    await whatsapp.send_text(phone, "⚡ Processing your Lightning payment...")

    total_sats = 0
    items_ordered = []

    for item in low_stock_items:
        bolt12_offer = item.get("bolt12_offer")
        if not bolt12_offer:
            # Use a default/demo offer
            bolt12_offer = "lno1demo_offer_placeholder"

        # Default reorder amount: 5000 sats per item type
        amount_sats = 5000
        total_sats += amount_sats
        items_ordered.append({"name": item["item_name"], "quantity": 50})  # Default reorder qty

    # Process payment
    payment_result = await lightning_service.pay_bolt12_offer(
        duka_id=duka["id"],
        bolt12_offer=bolt12_offer,
        amount_sats=total_sats,
        description=f"Reorder for {duka['duka_name']}",
    )

    if payment_result["success"]:
        # Generate receipt
        from datetime import datetime
        receipt_pdf = await generate_receipt(
            duka_name=duka["duka_name"],
            items=items_ordered,
            total_sats=total_sats,
            payment_hash=payment_result["payment_hash"],
            timestamp=datetime.now(),
        )

        # For now, send confirmation text (PDF upload requires media hosting)
        await whatsapp.send_text(
            phone,
            f"✅ *Payment Successful!*\n\n"
            f"⚡ {total_sats:,} sats sent to wholesaler\n"
            f"🧾 Hash: `{payment_result['payment_hash'][:16]}...`\n\n"
            f"Items on the way:\n"
            + "\n".join(f"  📦 {i['name'].title()} x{i['quantity']}" for i in items_ordered),
        )
    else:
        await whatsapp.send_text(
            phone,
            f"❌ Payment failed: {payment_result.get('error', 'Unknown error')}\n"
            f"Please try again or contact support.",
        )
