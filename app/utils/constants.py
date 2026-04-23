"""
Shared constants for Kiosk-GPT.
"""

# WhatsApp message types we handle
MSG_TYPE_TEXT = "text"
MSG_TYPE_INTERACTIVE = "interactive"
MSG_TYPE_FLOW_REPLY = "interactive"  # Flow replies come as interactive type

# Interactive button payload IDs
BTN_REORDER_YES = "reorder_yes"
BTN_REORDER_NO = "reorder_no"

# Inventory types
INVENTORY_TYPES = ["grocery", "electronics", "general"]

# AI model
GROQ_MODEL = "llama-3.2-3b-preview"

# Low stock default threshold
DEFAULT_REORDER_THRESHOLD = 10

# WhatsApp API version
WA_API_VERSION = "v21.0"
WA_API_BASE = f"https://graph.facebook.com/{WA_API_VERSION}"
