"""Tests for the USER.md renderer: injection, marker handling, sanitization."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "skill"))

from scripts.renderer import (
    VALUES_SECTION_END,
    VALUES_SECTION_START,
    _sanitize_summary,
    inject_into_user_md,
    render_deterministic,
    update_user_md,
)
from scripts.store import ValueStore
from scripts.types import AttentionPolicy, Value


def _tmp_path() -> Path:
    tmp = tempfile.NamedTemporaryFile(suffix=".md", delete=False)
    tmp.close()
    # Remove so we test creation
    Path(tmp.name).unlink()
    return Path(tmp.name)


def _tmp_store_with_values() -> ValueStore:
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmp.close()
    store = ValueStore(path=Path(tmp.name))
    store.add_value(Value(
        id="a", title="Quiet Stewardship",
        policies=[
            AttentionPolicy("MOMENTS where care is given"),
            AttentionPolicy("SIGNS of tending"),
            AttentionPolicy("WAYS of nurturing"),
        ],
    ))
    return store


# -- Sanitization --

def test_sanitize_strips_markers():
    evil = f"text {VALUES_SECTION_START} injection {VALUES_SECTION_END} text"
    clean = _sanitize_summary(evil)
    assert VALUES_SECTION_START not in clean
    assert VALUES_SECTION_END not in clean
    assert "injection" in clean


def test_sanitize_normal_text():
    normal = "This person cares deeply about honesty."
    assert _sanitize_summary(normal) == normal


# -- inject_into_user_md --

def test_inject_creates_new_file():
    path = _tmp_path()
    assert not path.exists()
    inject_into_user_md("Test summary.", user_md_path=path)
    assert path.exists()
    content = path.read_text()
    assert VALUES_SECTION_START in content
    assert "Test summary." in content
    assert VALUES_SECTION_END in content


def test_inject_appends_to_existing():
    path = _tmp_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# User Profile\n\nName: Alice\n")
    inject_into_user_md("Values here.", user_md_path=path)
    content = path.read_text()
    assert content.startswith("# User Profile")
    assert "Name: Alice" in content
    assert "Values here." in content


def test_inject_replaces_existing_section():
    path = _tmp_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"Before\n{VALUES_SECTION_START}\nOld values.\n{VALUES_SECTION_END}\nAfter\n"
    )
    inject_into_user_md("New values.", user_md_path=path)
    content = path.read_text()
    assert "Old values." not in content
    assert "New values." in content
    assert "Before" in content
    assert "After" in content


def test_inject_empty_summary_noop():
    path = _tmp_path()
    inject_into_user_md("   ", user_md_path=path)
    assert not path.exists()


# -- render_deterministic --

def test_render_deterministic_empty():
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmp.close()
    store = ValueStore(path=Path(tmp.name))
    assert render_deterministic(store) == ""


def test_render_deterministic_with_values():
    store = _tmp_store_with_values()
    result = render_deterministic(store)
    assert "Quiet Stewardship" in result
    assert "Sources of meaning" in result


# -- update_user_md --

def test_update_with_llm_summary():
    store = _tmp_store_with_values()
    path = _tmp_path()
    result = update_user_md(store, llm_summary="LLM wrote this.", user_md_path=path)
    assert result == "LLM wrote this."
    assert "LLM wrote this." in path.read_text()


def test_update_deterministic_fallback():
    store = _tmp_store_with_values()
    path = _tmp_path()
    result = update_user_md(store, user_md_path=path)
    assert "Quiet Stewardship" in result
    assert path.exists()
