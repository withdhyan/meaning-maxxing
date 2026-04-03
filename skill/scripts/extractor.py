"""
Value extraction engine.

Takes conversational context and produces articulated values
using LLM calls guided by the MAI methodology prompts.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Optional

from .types import AttentionPolicy, Value

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text()


def _parse_json(text: str) -> Optional[dict]:
    """Parse JSON from LLM response, tolerating markdown wrapping."""
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


def _format_value_for_prompt(v: Value) -> dict:
    """Serialize a value for inclusion in LLM prompts."""
    return {"id": v.id, "title": v.title, "policies": [p.text for p in v.policies]}


def _build_comparison_messages(
    prompt_name: str, new_value: Value, existing: list[Value]
) -> list[dict]:
    """Build messages that compare a new value against existing ones.

    Used by both duplicate checking and upgrade detection.
    """
    system = _load_prompt(prompt_name)
    existing_text = json.dumps(
        [_format_value_for_prompt(v) for v in existing], indent=2
    )
    user_content = (
        f"## New value\n"
        f"Title: {new_value.title}\n"
        f"Policies:\n"
        + "\n".join(f"- {p}" for p in new_value.policies)
        + f"\n\n## Existing values\n{existing_text}"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_content},
    ]


# -- Public API: message builders --

def extraction_messages(context: str) -> list[dict]:
    """Build messages for value extraction."""
    system = _load_prompt("extract_value")
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": context},
    ]


def duplicate_check_messages(new_value: Value, existing: list[Value]) -> list[dict]:
    """Build messages for duplicate checking."""
    return _build_comparison_messages("check_duplicate", new_value, existing)


def upgrade_detection_messages(new_value: Value, existing: list[Value]) -> list[dict]:
    """Build messages for upgrade detection."""
    return _build_comparison_messages("detect_upgrade", new_value, existing)


def render_summary_messages(
    top_values: list[Value],
    upgrades: list,
    total_count: int,
) -> list[dict]:
    """Build messages for USER.md summary rendering."""
    system = _load_prompt("render_user_summary")
    values_text = ""
    for v in top_values:
        values_text += f"\n### {v.title}\n"
        values_text += "\n".join(f"- {p}" for p in v.policies) + "\n"
        if v.description:
            values_text += f"_{v.description}_\n"

    upgrades_text = ""
    for u in upgrades:
        upgrades_text += (
            f"\n- Growth from value {u.source_id} to {u.wiser_id}: "
            f"{u.clarification}\n"
        )

    user_content = (
        f"## Top values (of {total_count} total)\n{values_text}"
        f"\n## Growth trajectories\n{upgrades_text or 'None yet.'}"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_content},
    ]


# -- Public API: response parsers --

def parse_extraction_response(response_text: str) -> Optional[Value]:
    """Parse the LLM's extraction response into a Value, or None if not found."""
    data = _parse_json(response_text)
    if data is None or not data.get("found", False):
        return None

    return Value(
        id=str(uuid.uuid4())[:8],
        title=data["title"],
        policies=[AttentionPolicy(text=p) for p in data["policies"]],
        description=data.get("description"),
    )


def parse_duplicate_check_response(response_text: str) -> Optional[str]:
    """Parse duplicate check. Returns the duplicate_of id, or None if not duplicate."""
    data = _parse_json(response_text)
    if data is None:
        return None
    if data.get("is_duplicate", False):
        return data.get("duplicate_of")
    return None


def parse_upgrade_response(
    response_text: str, new_value_id: str
) -> list[tuple]:
    """Parse upgrade detection response into (Edge, Upgrade) pairs.

    Only accepts A or B grade upgrades. Returns a list of
    (edge_dict, upgrade_dict) tuples — the caller constructs the types
    to avoid circular imports.
    """
    from .types import Edge, Upgrade

    data = _parse_json(response_text)
    if data is None:
        return []

    results = []
    for u in data.get("upgrades", []):
        likelihood = u.get("likelihood", "C")
        if likelihood not in ("A", "B"):
            continue

        edge = Edge(
            source_id=u["source_id"],
            wiser_id=new_value_id,
            context="conversation",
            confidence={"A": 0.9, "B": 0.7}.get(likelihood, 0.5),
        )
        upgrade = Upgrade(
            source_id=u["source_id"],
            wiser_id=new_value_id,
            clarification=u["clarification"],
            story=u.get("story", ""),
            mapping=u.get("mapping", []),
            likelihood=likelihood,
        )
        results.append((edge, upgrade))

    return results
