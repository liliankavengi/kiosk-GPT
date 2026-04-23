"""
Inventory management service.
Handles stock CRUD, low-stock detection, and sale recording.
"""

from app.db import get_rows, get_single_row, insert_row, update_row
from app.models.transaction import AIParseResult, ParsedItem
from app.utils import logger
from app.utils.constants import DEFAULT_REORDER_THRESHOLD


async def get_duka_inventory(duka_id: str) -> list[dict]:
    """Get all inventory items for a duka."""
    return await get_rows("inventory", {"duka_id": duka_id})


async def get_or_create_item(duka_id: str, item_name: str, item_name_local: str | None = None) -> dict:
    """
    Get an existing inventory item or create it with zero quantity.
    """
    item = await get_single_row("inventory", {"duka_id": duka_id, "item_name": item_name})
    if item:
        return item

    # Create new item with sensible defaults
    new_item = {
        "duka_id": duka_id,
        "item_name": item_name,
        "item_name_local": item_name_local,
        "quantity": 0,
        "unit_price_kes": 0,
        "reorder_threshold": DEFAULT_REORDER_THRESHOLD,
    }
    return await insert_row("inventory", new_item)


async def process_sale(duka_id: str, parse_result: AIParseResult, raw_message: str) -> dict:
    """
    Process a parsed sale: update inventory and record the sale.

    Returns a dict with:
        - sale_record: The saved sale
        - updated_items: List of updated inventory items
        - low_stock_items: Items that fell below reorder threshold
    """
    updated_items = []
    low_stock_items = []
    total_kes = 0.0

    for parsed_item in parse_result.items:
        item = await get_or_create_item(duka_id, parsed_item.name, parsed_item.name_local)

        if parsed_item.action == "sold":
            new_qty = max(0, item.get("quantity", 0) - parsed_item.quantity)
        elif parsed_item.action == "restocked":
            new_qty = item.get("quantity", 0) + parsed_item.quantity
        elif parsed_item.action == "damaged":
            new_qty = max(0, item.get("quantity", 0) - parsed_item.quantity)
        else:
            new_qty = item.get("quantity", 0)

        # Update quantity in DB
        updated = await update_row(
            "inventory",
            {"id": item["id"]},
            {"quantity": new_qty, "updated_at": "now()"},
        )

        # Calculate sale value
        unit_price = item.get("unit_price_kes", 0) or 0
        item_total = unit_price * parsed_item.quantity
        total_kes += item_total

        updated_items.append({
            "item_name": parsed_item.name,
            "item_name_local": parsed_item.name_local,
            "quantity_change": parsed_item.quantity,
            "action": parsed_item.action,
            "new_quantity": new_qty,
            "item_total_kes": item_total,
        })

        # Check low stock
        threshold = item.get("reorder_threshold", DEFAULT_REORDER_THRESHOLD)
        if new_qty <= threshold and parsed_item.action == "sold":
            low_stock_items.append({
                "item_name": parsed_item.name,
                "remaining": new_qty,
                "threshold": threshold,
                "bolt12_offer": item.get("wholesaler_bolt12_offer"),
            })

    # Record the sale
    sale_data = {
        "duka_id": duka_id,
        "raw_message": raw_message,
        "parsed_items": [item.model_dump() for item in parse_result.items],
        "total_kes": total_kes,
    }
    sale_record = await insert_row("sales", sale_data)

    logger.info(
        f"Sale processed: {len(updated_items)} items updated, "
        f"{len(low_stock_items)} low-stock alerts"
    )

    return {
        "sale_record": sale_record,
        "updated_items": updated_items,
        "low_stock_items": low_stock_items,
        "total_kes": total_kes,
    }


def format_sale_response(result: dict) -> str:
    """
    Format the sale processing result into a human-readable WhatsApp message.
    """
    lines = ["✅ *Sale Recorded!*\n"]

    for item in result["updated_items"]:
        action_emoji = "📦" if item["action"] == "restocked" else "🛒"
        price_str = f" (KES {item['item_total_kes']:,.0f})" if item["item_total_kes"] > 0 else ""
        lines.append(
            f"{action_emoji} {item['quantity_change']}x {item['item_name'].title()}{price_str}"
        )

    if result["total_kes"] > 0:
        lines.append(f"\n💰 *Total: KES {result['total_kes']:,.0f}*")

    if result["low_stock_items"]:
        lines.append("\n⚠️ *Low Stock Alert:*")
        for item in result["low_stock_items"]:
            lines.append(f"  → {item['item_name'].title()} has only {item['remaining']} left")

    return "\n".join(lines)
