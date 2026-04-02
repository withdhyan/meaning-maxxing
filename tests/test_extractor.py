"""Tests for the extraction engine: JSON parsing, message building, response parsing."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "skill"))

from scripts.extractor import (
    _parse_json,
    _format_value_for_prompt,
    extraction_messages,
    duplicate_check_messages,
    upgrade_detection_messages,
    render_summary_messages,
    parse_extraction_response,
    parse_duplicate_check_response,
    parse_upgrade_response,
)
from scripts.types import AttentionPolicy, Upgrade, Value


# -- _parse_json --

def test_parse_json_clean():
    assert _parse_json('{"a": 1}') == {"a": 1}


def test_parse_json_markdown_wrapped():
    text = 'Here is the result:\n```json\n{"found": true}\n```\nDone.'
    assert _parse_json(text) == {"found": True}


def test_parse_json_with_preamble():
    text = 'I found a value:\n{"found": true, "title": "Test"}'
    result = _parse_json(text)
    assert result["found"] is True
    assert result["title"] == "Test"


def test_parse_json_garbage():
    assert _parse_json("no json here") is None


def test_parse_json_empty():
    assert _parse_json("") is None


def test_parse_json_nested_braces():
    text = '{"a": {"b": 1}}'
    result = _parse_json(text)
    assert result == {"a": {"b": 1}}


# -- _format_value_for_prompt --

def test_format_value_for_prompt():
    v = Value(
        id="abc", title="Test Value",
        policies=[AttentionPolicy("MOMENTS of joy"), AttentionPolicy("SIGNS of care")],
    )
    result = _format_value_for_prompt(v)
    assert result == {
        "id": "abc",
        "title": "Test Value",
        "policies": ["MOMENTS of joy", "SIGNS of care"],
    }


# -- Message builders --

def test_extraction_messages_structure():
    msgs = extraction_messages("User said something meaningful.")
    assert len(msgs) == 2
    assert msgs[0]["role"] == "system"
    assert msgs[1]["role"] == "user"
    assert msgs[1]["content"] == "User said something meaningful."
    # System prompt should contain the methodology
    assert "source of meaning" in msgs[0]["content"].lower()


def test_duplicate_check_messages_structure():
    new = Value(id="x", title="New", policies=[AttentionPolicy("WAYS of being")])
    existing = [
        Value(id="a", title="Old", policies=[AttentionPolicy("MOMENTS of truth")]),
    ]
    msgs = duplicate_check_messages(new, existing)
    assert len(msgs) == 2
    assert msgs[0]["role"] == "system"
    assert "New" in msgs[1]["content"]
    assert "Old" in msgs[1]["content"]


def test_upgrade_detection_messages_structure():
    new = Value(id="x", title="New", policies=[AttentionPolicy("WAYS of being")])
    existing = [
        Value(id="a", title="Old", policies=[AttentionPolicy("MOMENTS of truth")]),
    ]
    msgs = upgrade_detection_messages(new, existing)
    assert len(msgs) == 2
    assert "upgrade" in msgs[0]["content"].lower() or "wiser" in msgs[0]["content"].lower()


def test_render_summary_messages_structure():
    top = [Value(id="a", title="T", policies=[AttentionPolicy("WAYS of being")])]
    upgrades = [
        Upgrade(
            source_id="a", wiser_id="b", clarification="grew",
            story="", mapping=[], likelihood="A",
        ),
    ]
    msgs = render_summary_messages(top, upgrades, total_count=3)
    assert len(msgs) == 2
    assert "3 total" in msgs[1]["content"]


def test_render_summary_no_upgrades():
    top = [Value(id="a", title="T", policies=[AttentionPolicy("WAYS")])]
    msgs = render_summary_messages(top, [], total_count=1)
    assert "None yet." in msgs[1]["content"]


# -- Response parsers --

def test_parse_extraction_found():
    response = json.dumps({
        "found": True,
        "title": "Quiet Stewardship",
        "policies": [
            "MOMENTS where care is given without being asked",
            "SIGNS that something fragile is being tended",
        ],
        "description": "I'm watering the plants.",
    })
    value = parse_extraction_response(response)
    assert value is not None
    assert value.title == "Quiet Stewardship"
    assert len(value.policies) == 2
    assert value.description == "I'm watering the plants."
    assert len(value.id) == 8


def test_parse_extraction_not_found():
    response = json.dumps({"found": False})
    assert parse_extraction_response(response) is None


def test_parse_extraction_garbage():
    assert parse_extraction_response("not json at all!!!") is None


def test_parse_extraction_markdown_wrapped():
    inner = json.dumps({
        "found": True,
        "title": "Test",
        "policies": ["WAYS of being"],
    })
    response = f"Here's what I found:\n```json\n{inner}\n```"
    value = parse_extraction_response(response)
    assert value is not None
    assert value.title == "Test"


def test_parse_duplicate_is_duplicate():
    response = json.dumps({
        "is_duplicate": True,
        "duplicate_of": "abc123",
        "reason": "Same thing",
    })
    assert parse_duplicate_check_response(response) == "abc123"


def test_parse_duplicate_not_duplicate():
    response = json.dumps({"is_duplicate": False})
    assert parse_duplicate_check_response(response) is None


def test_parse_duplicate_garbage():
    assert parse_duplicate_check_response("broken") is None


def test_parse_upgrade_with_results():
    response = json.dumps({
        "upgrades": [
            {
                "source_id": "old1",
                "clarification": "Was about control.",
                "story": "I let go.",
                "mapping": [{"old_policy": "X", "new_understanding": "Y"}],
                "likelihood": "A",
            },
            {
                "source_id": "old2",
                "clarification": "Low confidence.",
                "likelihood": "D",  # Should be filtered out
            },
        ]
    })
    results = parse_upgrade_response(response, "new1")
    assert len(results) == 1
    edge, upgrade = results[0]
    assert edge.source_id == "old1"
    assert edge.wiser_id == "new1"
    assert edge.confidence == 0.9
    assert upgrade.clarification == "Was about control."
    assert upgrade.story == "I let go."


def test_parse_upgrade_empty():
    response = json.dumps({"upgrades": []})
    assert parse_upgrade_response(response, "x") == []


def test_parse_upgrade_garbage():
    assert parse_upgrade_response("broken", "x") == []


def test_parse_upgrade_b_grade():
    response = json.dumps({
        "upgrades": [{
            "source_id": "old",
            "clarification": "test",
            "likelihood": "B",
        }]
    })
    results = parse_upgrade_response(response, "new")
    assert len(results) == 1
    assert results[0][0].confidence == 0.7
