"""
Duka (shop) model.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class DukaCreate(BaseModel):
    """Data required to register a new duka."""
    phone_number: str = Field(..., description="E.164 phone number")
    wa_phone_id: str = Field(..., description="WhatsApp phone number ID")
    duka_name: str = Field(..., min_length=1, max_length=100)
    inventory_type: str = Field(..., pattern="^(grocery|electronics|general)$")
    lightning_address: str | None = None


class Duka(DukaCreate):
    """Full duka record from database."""
    id: str
    ldk_node_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
