"""Tests for the ValuesTool orchestrator: dispatch, action handling, TWS."""

import asyncio
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "skill"))

from scripts.store import ValueStore
from scripts.tool import ValuesTool, TOOL_SCHEMA
from scripts.types import AttentionPolicy, Edge, Upgrade, Value


def _tmp_store() -> ValueStore:
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmp.close()
    return ValueStore(path=Path(tmp.name))


def _run(coro):
    """Helper to run async tests."""
    return asyncio.get_event_loop().run_until_complete(coro)


# -- Schema validation --

def test_schema_has_required_fields():
    assert "action" in TOOL_SCHEMA["properties"]
    assert TOOL_SCHEMA["required"] == ["action"]
    actions = TOOL_SCHEMA["properties"]["action"]["enum"]
    assert "extract" in actions
    assert "show" in actions
    assert "upgrades" in actions
    assert "remove" in actions
    assert "tws" in actions


# -- Show --

def test_show_empty():
    tool = ValuesTool(store=_tmp_store())
    result = _run(tool.handle({"action": "show"}))
    assert "No values" in result


def test_show_with_values():
    store = _tmp_store()
    store.add_value(Value(
        id="a", title="Test",
        policies=[AttentionPolicy("WAYS of being")],
    ))
    tool = ValuesTool(store=store)
    result = _run(tool.handle({"action": "show"}))
    assert "Test" in result


# -- TWS --

def test_tws_empty():
    tool = ValuesTool(store=_tmp_store())
    result = _run(tool.handle({"action": "tws"}))
    assert "No Wisdom Score" in result


def test_tws_with_data():
    store = _tmp_store()
    store.add_value(Value(id="a", title="A", policies=[AttentionPolicy("WAYS")]))
    store.add_value(Value(id="b", title="B", policies=[AttentionPolicy("SIGNS")]))
    store.add_edge(Edge(source_id="a", wiser_id="b", context="x", confidence=0.9))
    tool = ValuesTool(store=store)
    result = _run(tool.handle({"action": "tws"}))
    assert "Wisdom Score" in result
    assert "Depth" in result
    assert "Growth" in result
    assert "Coherence" in result


# -- Upgrades --

def test_upgrades_empty():
    tool = ValuesTool(store=_tmp_store())
    result = _run(tool.handle({"action": "upgrades"}))
    assert "No growth" in result


def test_upgrades_with_data():
    store = _tmp_store()
    store.add_value(Value(id="a", title="Alpha", policies=[AttentionPolicy("WAYS")]))
    store.add_value(Value(id="b", title="Beta", policies=[AttentionPolicy("SIGNS")]))
    store.add_upgrade(Upgrade(
        source_id="a", wiser_id="b",
        clarification="Grew", story="Let go", mapping=[], likelihood="A",
    ))
    tool = ValuesTool(store=store)
    result = _run(tool.handle({"action": "upgrades"}))
    assert "Alpha" in result
    assert "Beta" in result


# -- Remove --

def test_remove_success():
    store = _tmp_store()
    store.add_value(Value(id="a", title="Alpha", policies=[AttentionPolicy("X")]))
    tool = ValuesTool(store=store)
    result = json.loads(_run(tool.handle({"action": "remove", "value_id": "a"})))
    assert result["action"] == "removed"
    assert result["result"] == "Removed: Alpha"
    assert store.get_value("a") is None


def test_remove_nonexistent():
    tool = ValuesTool(store=_tmp_store())
    result = json.loads(_run(tool.handle({"action": "remove", "value_id": "nope"})))
    assert "error" in result


def test_remove_no_id():
    tool = ValuesTool(store=_tmp_store())
    result = json.loads(_run(tool.handle({"action": "remove"})))
    assert "error" in result


# -- Extract --

def test_extract_no_context():
    tool = ValuesTool(store=_tmp_store())
    result = json.loads(_run(tool.handle({"action": "extract"})))
    assert "error" in result


def test_extract_no_llm():
    tool = ValuesTool(store=_tmp_store())
    result = json.loads(_run(tool.handle({"action": "extract", "context": "test"})))
    assert "error" in result
    assert "LLM" in result["error"]


def test_extract_no_value_found():
    async def mock_llm(messages):
        return json.dumps({"found": False})

    tool = ValuesTool(store=_tmp_store())
    result = json.loads(_run(tool.handle(
        {"action": "extract", "context": "I like pizza."},
        llm_call=mock_llm,
    )))
    assert result["action"] == "none"


def test_extract_value_found():
    call_count = 0

    async def mock_llm(messages):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # Extraction
            return json.dumps({
                "found": True,
                "title": "Quiet Stewardship",
                "policies": ["MOMENTS where care is given"],
                "description": "I tend things.",
            })
        return json.dumps({})  # Other calls

    tool = ValuesTool(store=_tmp_store())
    result = json.loads(_run(tool.handle(
        {"action": "extract", "context": "I spent the morning tending my garden."},
        llm_call=mock_llm,
    )))
    assert result["action"] == "extracted"
    assert result["value"]["title"] == "Quiet Stewardship"
    assert "tws" in result


def test_extract_deduplicates():
    store = _tmp_store()
    store.add_value(Value(
        id="existing",
        title="Quiet Stewardship",
        policies=[AttentionPolicy("MOMENTS where care is given")],
    ))
    call_count = 0

    async def mock_llm(messages):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return json.dumps({
                "found": True,
                "title": "Silent Caretaking",
                "policies": ["MOMENTS where care is given without asking"],
            })
        elif call_count == 2:
            return json.dumps({
                "is_duplicate": True,
                "duplicate_of": "existing",
                "reason": "Same thing",
            })
        return json.dumps({})

    tool = ValuesTool(store=store)
    result = json.loads(_run(tool.handle(
        {"action": "extract", "context": "I care for things silently."},
        llm_call=mock_llm,
    )))
    assert result["action"] == "deduplicated"
    # Should not have added a new value
    assert len(store.get_all_values()) == 1


# -- Unknown action --

def test_unknown_action():
    tool = ValuesTool(store=_tmp_store())
    result = json.loads(_run(tool.handle({"action": "bogus"})))
    assert "error" in result


# -- Default action --

def test_default_action_is_show():
    tool = ValuesTool(store=_tmp_store())
    result = _run(tool.handle({}))
    assert "No values" in result
