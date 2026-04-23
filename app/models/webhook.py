"""
WhatsApp webhook payload models.
These model the incoming webhook payloads from WhatsApp Cloud API.
"""

from pydantic import BaseModel


class WhatsAppProfile(BaseModel):
    name: str | None = None


class WhatsAppContact(BaseModel):
    profile: WhatsAppProfile | None = None
    wa_id: str | None = None


class WhatsAppTextMessage(BaseModel):
    body: str


class WhatsAppButtonReply(BaseModel):
    id: str
    title: str


class WhatsAppInteractive(BaseModel):
    type: str | None = None
    button_reply: WhatsAppButtonReply | None = None
    nfm_reply: dict | None = None  # Flow reply


class WhatsAppMessage(BaseModel):
    from_: str | None = None
    id: str | None = None
    timestamp: str | None = None
    type: str | None = None
    text: WhatsAppTextMessage | None = None
    interactive: WhatsAppInteractive | None = None

    class Config:
        # "from" is a reserved word in Python, so we alias it
        populate_by_name = True
        fields = {"from_": {"alias": "from"}}


class WhatsAppMetadata(BaseModel):
    display_phone_number: str | None = None
    phone_number_id: str | None = None


class WhatsAppValue(BaseModel):
    messaging_product: str | None = None
    metadata: WhatsAppMetadata | None = None
    contacts: list[WhatsAppContact] | None = None
    messages: list[WhatsAppMessage] | None = None


class WhatsAppChange(BaseModel):
    value: WhatsAppValue | None = None
    field: str | None = None


class WhatsAppEntry(BaseModel):
    id: str | None = None
    changes: list[WhatsAppChange] | None = None


class WhatsAppWebhookPayload(BaseModel):
    """Top-level webhook payload from WhatsApp Cloud API."""
    object: str | None = None
    entry: list[WhatsAppEntry] | None = None
