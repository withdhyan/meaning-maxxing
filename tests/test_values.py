"""Tests for the simplified value extraction pipeline."""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "skill"))

from scripts.values import (
    make_value,
    load_values,
    save_values,
    add_value,
    remove_value,
    extraction_messages,
    parse_extraction,
    _parse_json,
    render_values_section,
    write_to_user_md,
    format_values,
    SECTION_START,
    SECTION_END,
)


def _tmp_path(suffix=".json") -> Path:
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    tmp.close()
    Path(tmp.name).unlink()
    return Path(tmp.name)


# -- make_value --

def test_make_value():
    v = make_value("Test", ["WAYS of being"], "desc", "ctx" * 200)
    assert v["title"] == "Test"
    assert v["policies"] == ["WAYS of being"]
    assert v["description"] == "desc"
    assert len(v["source_context"]) <= 500
    assert len(v["id"]) == 8
    assert v["created_at"] > 0


# -- Storage --

def test_save_and_load():
    path = _tmp_path()
    v = make_value("Alpha", ["MOMENTS of truth"])
    save_values([v], path)
    loaded = load_values(path)
    assert len(loaded) == 1
    assert loaded[0]["title"] == "Alpha"


def test_load_nonexistent():
    assert load_values(Path("/tmp/nonexistent_12345.json")) == []


def test_load_corrupt():
    path = _tmp_path()
    path.write_text("{{broken")
    assert load_values(path) == []


def test_add_value():
    path = _tmp_path()
    save_values([], path)
    v = make_value("Alpha", ["WAYS"])
    add_value(v, path)
    assert len(load_values(path)) == 1


def test_remove_value():
    path = _tmp_path()
    v = make_value("Alpha", ["WAYS"])
    save_values([v], path)
    removed = remove_value(v["id"], path)
    assert removed is not None
    assert removed["title"] == "Alpha"
    assert load_values(path) == []


def test_remove_nonexistent():
    path = _tmp_path()
    save_values([], path)
    assert remove_value("nope", path) is None


# -- JSON parsing --

def test_parse_json_clean():
    assert _parse_json('{"a": 1}') == {"a": 1}


def test_parse_json_markdown_wrapped():
    assert _parse_json('text\n```json\n{"a": 1}\n```')["a"] == 1


def test_parse_json_garbage():
    assert _parse_json("no json") is None


def test_parse_json_empty():
    assert _parse_json("") is None


# -- Extraction --

def test_extraction_messages():
    msgs = extraction_messages("User said something.")
    assert len(msgs) == 2
    assert msgs[0]["role"] == "system"
    assert msgs[1]["content"] == "User said something."
    assert "source of meaning" in msgs[0]["content"].lower()


def test_parse_extraction_found():
    resp = json.dumps({
        "found": True,
        "title": "Quiet Stewardship",
        "policies": ["MOMENTS where care is given", "SIGNS of tending"],
        "description": "I water the plants.",
    })
    v = parse_extraction(resp)
    assert v is not None
    assert v["title"] == "Quiet Stewardship"
    assert len(v["policies"]) == 2


def test_parse_extraction_not_found():
    assert parse_extraction('{"found": false}') is None


def test_parse_extraction_garbage():
    assert parse_extraction("broken!!!") is None


def test_parse_extraction_markdown_wrapped():
    inner = json.dumps({"found": True, "title": "T", "policies": ["WAYS"]})
    v = parse_extraction(f"Here:\n```json\n{inner}\n```")
    assert v is not None
    assert v["title"] == "T"


# -- USER.md --

def test_render_values_section_empty():
    assert render_values_section([]) == ""


def test_render_values_section():
    values = [make_value("Alpha", ["WAYS of being", "SIGNS of growth"])]
    section = render_values_section(values)
    assert "Alpha" in section
    assert "WAYS of being" in section


def test_write_creates_new_file():
    path = _tmp_path(".md")
    values = [make_value("Alpha", ["WAYS of being"])]
    write_to_user_md(values, user_md_path=path)
    content = path.read_text()
    assert SECTION_START in content
    assert "Alpha" in content
    assert SECTION_END in content


def test_write_appends_to_existing():
    path = _tmp_path(".md")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# Profile\nName: Alice\n")
    values = [make_value("Alpha", ["WAYS"])]
    write_to_user_md(values, user_md_path=path)
    content = path.read_text()
    assert content.startswith("# Profile")
    assert "Alpha" in content


def test_write_replaces_existing_section():
    path = _tmp_path(".md")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"Before\n{SECTION_START}\nOld\n{SECTION_END}\nAfter\n")
    values = [make_value("New", ["WAYS"])]
    write_to_user_md(values, user_md_path=path)
    content = path.read_text()
    assert "Old" not in content
    assert "New" in content
    assert "Before" in content
    assert "After" in content


def test_write_empty_values_noop():
    path = _tmp_path(".md")
    write_to_user_md([], user_md_path=path)
    assert not path.exists()


def test_write_sanitizes_markers():
    path = _tmp_path(".md")
    evil_value = make_value(f"Evil {SECTION_START}", ["WAYS"])
    write_to_user_md([evil_value], user_md_path=path)
    content = path.read_text()
    # Should have exactly one start and one end marker
    assert content.count(SECTION_START) == 1
    assert content.count(SECTION_END) == 1


# -- Display --

def test_format_values_empty():
    assert "No values" in format_values([])


def test_format_values():
    values = [make_value("Alpha", ["WAYS of being"], "I am being.")]
    result = format_values(values)
    assert "Alpha" in result
    assert "WAYS of being" in result
    assert "I am being." in result
    assert "1 sources" in result
