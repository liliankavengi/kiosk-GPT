"""
AI Parser service.
Converts Sheng/Swahili shopkeeper messages into structured JSON
using Llama 3.2 via the Groq API.
"""

import json
import os
from pathlib import Path

from groq import Groq
from app.config import get_settings
from app.models.transaction import AIParseResult
from app.utils import logger
from app.utils.constants import GROQ_MODEL


# Load the prompt template
_PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "sale_parser.txt"


def _load_prompt_template() -> str:
    """Load the one-shot prompt template from disk."""
    if _PROMPT_PATH.exists():
        return _PROMPT_PATH.read_text(encoding="utf-8")
    # Fallback inline prompt
    return """You are a Kenyan shop inventory assistant. Parse the shopkeeper's message
(which may be in Sheng, Swahili, or English) into structured JSON.

Rules:
1. Extract each item, its quantity, and the action (sold/restocked/damaged).
2. Use standard English names for items, but preserve the local name.
3. Handle common Sheng/Swahili number words (moja=1, mbili=2, tatu=3, nne=4,
   tano=5, sita=6, saba=7, nane=8, tisa=9, kumi=10, ishirini=20, etc.)
4. "Nimeuza" = I have sold, "Nimepokea" = I have received/restocked.
5. If uncertain, set confidence below 0.7.
6. RESPOND ONLY WITH VALID JSON. No explanations.

Example:
Input: "Nimeuza mkate tatu na maziwa ishirini"
Output: {"items": [{"name": "bread", "name_local": "mkate", "quantity": 3, "action": "sold"}, {"name": "milk", "name_local": "maziwa", "quantity": 20, "action": "sold"}], "confidence": 0.95}

Now parse this message:
"{user_message}"
"""


_PROMPT_TEMPLATE = _load_prompt_template()


def _get_groq_client() -> Groq:
    """Create a Groq client instance."""
    settings = get_settings()
    return Groq(api_key=settings.groq_api_key)


async def parse_sale_message(message: str) -> AIParseResult:
    """
    Parse a shopkeeper's message (Sheng/Swahili/English) into structured items.

    Args:
        message: The raw text from the shopkeeper.

    Returns:
        AIParseResult with parsed items and confidence score.
    """
    prompt = _PROMPT_TEMPLATE.replace("{user_message}", message)

    try:
        client = _get_groq_client()
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a JSON-only response bot. Never include explanations.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.1,  # Low temperature for deterministic parsing
            max_tokens=500,
            response_format={"type": "json_object"},
        )

        raw_response = completion.choices[0].message.content
        logger.info(f"AI raw response: {raw_response}")

        # Parse the JSON response
        parsed = json.loads(raw_response)
        result = AIParseResult(**parsed)

        logger.info(f"Parsed {len(result.items)} items with confidence {result.confidence}")
        return result

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response as JSON: {e}")
        return AIParseResult(items=[], confidence=0.0)
    except Exception as e:
        logger.error(f"AI parser error: {e}")
        return AIParseResult(items=[], confidence=0.0)
