"""
Tests for the AI parser service.
"""

import pytest
from app.models.transaction import AIParseResult

# ── Test Pydantic model validation ───────────────────────

def test_parse_result_valid():
    """Test that a valid AI response parses correctly."""
    data = {
        "items": [
            {"name": "bread", "name_local": "mkate", "quantity": 3, "action": "sold"},
            {"name": "milk", "name_local": "maziwa", "quantity": 20, "action": "sold"},
        ],
        "confidence": 0.95,
    }
    result = AIParseResult(**data)
    assert len(result.items) == 2
    assert result.items[0].name == "bread"
    assert result.items[0].quantity == 3
    assert result.items[1].quantity == 20
    assert result.confidence == 0.95


def test_parse_result_empty():
    """Test empty parse result."""
    result = AIParseResult(items=[], confidence=0.0)
    assert len(result.items) == 0
    assert result.confidence == 0.0


def test_parse_result_restock():
    """Test restocked items parsing."""
    data = {
        "items": [
            {"name": "sugar", "name_local": "sukari", "quantity": 10, "action": "restocked"},
        ],
        "confidence": 0.90,
    }
    result = AIParseResult(**data)
    assert result.items[0].action == "restocked"


def test_parse_result_invalid_action():
    """Test that invalid action raises validation error."""
    data = {
        "items": [
            {"name": "bread", "quantity": 3, "action": "invalid_action"},
        ],
        "confidence": 0.5,
    }
    with pytest.raises(Exception):
        AIParseResult(**data)


# ── Sample Sheng/Swahili phrases for integration testing ─

SAMPLE_PHRASES = [
    ("Nimeuza mkate tatu na maziwa mbao", ["bread", "milk"], [3, 20]),
    ("Sold 5 sugar and 3 bread", ["sugar", "bread"], [5, 3]),
    ("Nimepokea sukari kumi na sabuni tano", ["sugar", "soap"], [10, 5]),
    ("Nimeuza soda mbili", ["soda"], [2]),
    ("Nime sell mchele kumi na tano", ["rice"], [15]),
]


@pytest.mark.parametrize("phrase,expected_items,expected_quantities", SAMPLE_PHRASES)
def test_sample_phrases_documented(phrase, expected_items, expected_quantities):
    """
    Document sample phrases and their expected outputs.
    These are integration test cases — run with GROQ_API_KEY set.
    """
    # This test just validates the test data structure
    assert len(expected_items) == len(expected_quantities)
    assert all(q > 0 for q in expected_quantities)
