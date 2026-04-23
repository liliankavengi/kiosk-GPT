"""
Inventory item model.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class InventoryItemCreate(BaseModel):
    """Data to create/update an inventory item."""
    duka_id: str
    item_name: str
    item_name_local: str | None = None
    quantity: int = Field(default=0, ge=0)
    unit_price_kes: float = Field(default=0, ge=0)
    unit_price_sats: int | None = None
    reorder_threshold: int = Field(default=10, ge=0)
    wholesaler_bolt12_offer: str | None = None


class InventoryItem(InventoryItemCreate):
    """Full inventory item from database."""
    id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def is_low_stock(self) -> bool:
        """Check if item is below reorder threshold."""
        return self.quantity <= self.reorder_threshold
