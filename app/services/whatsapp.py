"""
WhatsApp Cloud API service.
Handles sending messages, interactive buttons, templates, and media.
"""

import httpx
from app.config import get_settings
from app.utils import logger
from app.utils.constants import WA_API_BASE


async def _send_request(payload: dict) -> dict:
    """Send a request to the WhatsApp Cloud API."""
    settings = get_settings()
    url = f"{WA_API_BASE}/{settings.whatsapp_phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_token}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload, headers=headers)

    if response.status_code != 200:
        logger.error(f"WhatsApp API error: {response.status_code} — {response.text}")
        response.raise_for_status()

    logger.info(f"Message sent successfully to {payload.get('to', 'unknown')}")
    return response.json()


async def send_text(to: str, text: str) -> dict:
    """Send a plain text message."""
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": text},
    }
    return await _send_request(payload)


async def send_interactive_buttons(to: str, body: str, buttons: list[dict]) -> dict:
    """
    Send an interactive message with reply buttons.

    Args:
        to: Recipient phone number.
        body: Message body text.
        buttons: List of dicts with 'id' and 'title' keys.
                 Max 3 buttons, title max 20 chars.
    """
    button_objects = [
        {"type": "reply", "reply": {"id": btn["id"], "title": btn["title"]}}
        for btn in buttons[:3]
    ]

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body},
            "action": {"buttons": button_objects},
        },
    }
    return await _send_request(payload)


async def send_flow(to: str, flow_id: str, flow_token: str, header: str = "", body: str = "") -> dict:
    """
    Send a WhatsApp Flow message.

    Args:
        to: Recipient phone number.
        flow_id: The Flow ID from WhatsApp Manager.
        flow_token: A unique token for this flow session.
        header: Optional header text.
        body: Optional body text.
    """
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "flow",
            "header": {"type": "text", "text": header} if header else None,
            "body": {"text": body} if body else {"text": "Please fill in the form below."},
            "action": {
                "name": "flow",
                "parameters": {
                    "flow_message_version": "3",
                    "flow_id": flow_id,
                    "flow_token": flow_token,
                    "mode": "published",
                    "flow_cta": "Open Form",
                    "flow_action": "navigate",
                    "flow_action_payload": {
                        "screen": "REGISTRATION",
                    },
                },
            },
        },
    }
    # Remove None header
    if payload["interactive"]["header"] is None:
        del payload["interactive"]["header"]

    return await _send_request(payload)


async def send_document(to: str, document_url: str, filename: str, caption: str = "") -> dict:
    """Send a document (e.g., PDF receipt) via URL."""
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "document",
        "document": {
            "link": document_url,
            "filename": filename,
            "caption": caption,
        },
    }
    return await _send_request(payload)


async def mark_as_read(message_id: str) -> dict:
    """Mark a message as read (blue ticks)."""
    settings = get_settings()
    url = f"{WA_API_BASE}/{settings.whatsapp_phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(url, json=payload, headers=headers)

    return response.json()
