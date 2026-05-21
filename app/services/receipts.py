"""
PDF receipt generation service.
Generates professional receipts for Lightning payment confirmations.
"""

import io
from datetime import datetime

from app.utils import logger
from reportlab.lib.pagesizes import A6
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


async def generate_receipt(
    duka_name: str,
    items: list[dict],
    total_sats: int,
    payment_hash: str,
    timestamp: datetime | None = None,
) -> bytes:
    """
    Generate a PDF receipt for a completed payment.

    Args:
        duka_name: Shop name.
        items: List of item dicts with 'name' and 'quantity'.
        total_sats: Total payment in satoshis.
        payment_hash: Lightning payment hash for verification.
        timestamp: Payment timestamp.

    Returns:
        PDF content as bytes.
    """
    if timestamp is None:
        timestamp = datetime.now()

    buffer = io.BytesIO()
    width, height = A6  # Small receipt size

    c = canvas.Canvas(buffer, pagesize=A6)

    # ── Header ──────────────────────────────────────────
    y = height - 15 * mm
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, y, "⚡ Kiosk-GPT Receipt")

    y -= 8 * mm
    c.setFont("Helvetica", 9)
    c.drawCentredString(width / 2, y, f"Powered by Lightning Network")

    # ── Shop Info ───────────────────────────────────────
    y -= 10 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(10 * mm, y, f"Duka: {duka_name}")

    y -= 6 * mm
    c.setFont("Helvetica", 8)
    c.drawString(10 * mm, y, f"Date: {timestamp.strftime('%Y-%m-%d %H:%M')}")

    # ── Divider ─────────────────────────────────────────
    y -= 5 * mm
    c.setLineWidth(0.5)
    c.line(10 * mm, y, width - 10 * mm, y)

    # ── Items ───────────────────────────────────────────
    y -= 7 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(10 * mm, y, "Item")
    c.drawRightString(width - 10 * mm, y, "Qty")

    y -= 5 * mm
    c.setFont("Helvetica", 9)
    for item in items:
        c.drawString(10 * mm, y, item.get("name", "Unknown").title())
        c.drawRightString(width - 10 * mm, y, str(item.get("quantity", 0)))
        y -= 5 * mm

    # ── Divider ─────────────────────────────────────────
    y -= 2 * mm
    c.line(10 * mm, y, width - 10 * mm, y)

    # ── Total ───────────────────────────────────────────
    y -= 7 * mm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(10 * mm, y, "Total:")
    c.drawRightString(width - 10 * mm, y, f"{total_sats:,} sats")

    # ── Payment Hash ────────────────────────────────────
    y -= 10 * mm
    c.setFont("Helvetica", 6)
    c.drawString(10 * mm, y, f"Payment Hash:")
    y -= 4 * mm
    c.drawString(10 * mm, y, payment_hash[:32])
    y -= 4 * mm
    c.drawString(10 * mm, y, payment_hash[32:])

    # ── Footer ──────────────────────────────────────────
    y -= 8 * mm
    c.setFont("Helvetica-Oblique", 7)
    c.drawCentredString(width / 2, y, "Thank you for using Kiosk-GPT!")

    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()

    logger.info(f"Receipt generated: {len(pdf_bytes)} bytes")
    return pdf_bytes
