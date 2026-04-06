"""
Value extraction: the whole thing.

Extract values from conversation. Write them to USER.md. That's it.
"""

from __future__ import annotations

import json
import time
import uuid
import os
import tempfile
from pathlib import Path
from typing import Callable, Optional

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
VALUES_PATH = Path.home() / ".hermes" / "values" / "values.json"
USER_MD_PATH = Path.home() / ".hermes" / "USER.md"
SECTION_START = "<!-- values-start -->"
SECTION_END = "<!-- values-end -->"

MAX_SOURCE_CONTEXT = 500
MAX_DISPLAY_POLICIES = 4


# -- Data --

def make_value(title: str, policies: list[str], description: str = "",
               source_context: str = "") -> dict:
    return {
        "id": str(uuid.uuid4())[:8],
        "title": title,
        "policies": policies,
        "description": description,
        "source_context": source_context[:MAX_SOURCE_CONTEXT],
        "created_at": time.time(),
    }


# -- Storage --

def load_values(path: Path = VALUES_PATH) -> list[dict]:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, KeyError):
            return []
    return []


def save_values(values: list[dict], path: Path = VALUES_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(values, indent=2)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        os.write(fd, data.encode())
    finally:
        os.close(fd)
    try:
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def _update_values(
    path: Path, fn: Callable[[list[dict]], list[dict]]
) -> list[dict]:
    """Load values, apply mutation fn, save. Returns the mutated list."""
    values = load_values(path)
    new_values = fn(values)
    save_values(new_values, path)
    return new_values


def add_value(value: dict, path: Path = VALUES_PATH) -> None:
    _update_values(path, lambda vs: vs + [value])


def remove_value(value_id: str, path: Path = VALUES_PATH) -> Optional[dict]:
    values = load_values(path)
    removed = None
    kept = []
    for v in values:
        if v["id"] == value_id and removed is None:
            removed = v
        else:
            kept.append(v)
    if removed:
        save_values(kept, path)
    return removed


# -- LLM messages --

def extraction_messages(context: str,
                        existing_values: list[dict] | None = None) -> list[dict]:
    system = (PROMPTS_DIR / "extract_value.md").read_text()
    user_content = context
    if existing_values:
        user_content += "\n\n---\nExisting values (do not duplicate):\n"
        for v in existing_values:
            policies = "; ".join(v["policies"][:MAX_DISPLAY_POLICIES])
            user_content += f"- {v['title']}: {policies}\n"
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_content},
    ]


def parse_extraction(response_text: str) -> Optional[dict]:
    """Parse LLM response into a value dict, or None."""
    data = _parse_json(response_text)
    if data is None or not data.get("found", False):
        return None

    title = data.get("title")
    policies = data.get("policies")

    if not title or not isinstance(title, str):
        return None
    if not policies or not isinstance(policies, list) or len(policies) == 0:
        return None

    return make_value(
        title=title,
        policies=[str(p) for p in policies],
        description=data.get("description", ""),
    )


def _parse_json(text: str) -> Optional[dict]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end == 0:
            return None
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            return None


# -- USER.md --

def render_values_section(values: list[dict]) -> str:
    """Render values as a markdown section for USER.md."""
    if not values:
        return ""
    lines = []
    for v in values:
        lines.append(f"**{v['title']}**: "
                     + "; ".join(v["policies"][:MAX_DISPLAY_POLICIES]))
    return "\n".join(lines)


def write_to_user_md(values: list[dict],
                     user_md_path: Path = USER_MD_PATH) -> None:
    """Write values into USER.md between marker comments."""
    section_content = render_values_section(values)
    if not section_content:
        return

    # Strip markers from content to prevent injection
    section_content = section_content.replace(SECTION_START, "").replace(SECTION_END, "")
    section = f"{SECTION_START}\n{section_content}\n{SECTION_END}"

    if user_md_path.exists():
        content = user_md_path.read_text()
        if SECTION_START in content and SECTION_END in content:
            start_idx = content.index(SECTION_START)
            end_idx = content.index(SECTION_END) + len(SECTION_END)
            content = content[:start_idx] + section + content[end_idx:]
        else:
            content = content.rstrip() + "\n\n" + section + "\n"
    else:
        user_md_path.parent.mkdir(parents=True, exist_ok=True)
        content = section + "\n"

    user_md_path.write_text(content)


# -- Display --

def format_values(values: list[dict]) -> str:
    if not values:
        return "No values captured yet."
    lines = [f"{len(values)} sources of meaning:\n"]
    for i, v in enumerate(values, 1):
        lines.append(f"{i}. **{v['title']}**")
        for p in v["policies"]:
            lines.append(f"   - {p}")
        if v.get("description"):
            lines.append(f"   _{v['description']}_")
        lines.append("")
    return "\n".join(lines)
