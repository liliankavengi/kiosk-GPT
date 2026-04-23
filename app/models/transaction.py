"""
Transaction models for sales and payments.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class ParsedItem(BaseModel):
    """A single item parsed from a shopkeeper's message."""
    name: str
    name_local: str | None = None
    quantity: int = Field(..., ge=1)
    action: str = Field(default="sold", pattern="^(sold|restocked|damaged)$")


class AIParseResult(BaseModel):
    """Structured output from the AI parser."""
    items: list[ParsedItem]
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class SaleCreate(BaseModel):
    """Data for recording a sale."""
    duka_id: str
    raw_message: str
    parsed_items: list[dict]
    total_kes: float | None = None
    total_sats: int | None = None


class Sale(SaleCreate):
    """Full sale record from database."""
    id: str
    created_at: datetime | None = None


class PaymentCreate(BaseModel):
    """Data for creating a payment record."""
    duka_id: str
    sale_id: str | None = None
    payment_type: str = Field(..., pattern="^(reorder|customer_payment|withdrawal)$")
    amount_sats: int = Field(..., gt=0)
    bolt12_offer: str | None = None


class Payment(PaymentCreate):
    """Full payment record from database."""
    id: str
    payment_hash: str | None = None
    payment_preimage: str | None = None
    status: str = "pending"
    receipt_url: str | None = None
    created_at: datetime | None = None
