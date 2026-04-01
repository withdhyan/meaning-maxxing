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

from .types import AttentionPolicy, Edge, Upgrade, Value

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text()


def _build_extraction_messages(context: str) -> list[dict]:
    system = _load_prompt("extract_value")
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": context},
    ]


def _build_duplicate_check_messages(
    new_value: Value, existing: list[Value]
) -> list[dict]:
    system = _load_prompt("check_duplicate")
    existing_text = json.dumps(
        [{"id": v.id, "title": v.title, "policies": [p.text for p in v.policies]}
         for v in existing],
        indent=2,
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


def _build_upgrade_detection_messages(
    new_value: Value, existing: list[Value]
) -> list[dict]:
    system = _load_prompt("detect_upgrade")
    existing_text = json.dumps(
        [{"id": v.id, "title": v.title, "policies": [p.text for p in v.policies]}
         for v in existing],
        indent=2,
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


def _build_render_messages(
    top_values: list[Value],
    upgrades: list[Upgrade],
    total_count: int,
) -> list[dict]:
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


def parse_extraction_response(response_text: str) -> Optional[Value]:
    """Parse the LLM's extraction response into a Value, or None if not found."""
    try:
        data = json.loads(response_text)
    except json.JSONDecodeError:
        # Try to find JSON in the response
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        if start == -1 or end == 0:
            return None
        try:
            data = json.loads(response_text[start:end])
        except json.JSONDecodeError:
            return None

    if not data.get("found", False):
        return None

    return Value(
        id=str(uuid.uuid4())[:8],
        title=data["title"],
        policies=[AttentionPolicy(text=p) for p in data["policies"]],
        description=data.get("description"),
    )


def parse_duplicate_check_response(response_text: str) -> Optional[str]:
    """Parse duplicate check. Returns the duplicate_of id, or None if not duplicate."""
    try:
        data = json.loads(response_text)
    except json.JSONDecodeError:
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        if start == -1 or end == 0:
            return None
        try:
            data = json.loads(response_text[start:end])
        except json.JSONDecodeError:
            return None

    if data.get("is_duplicate", False):
        return data.get("duplicate_of")
    return None


def parse_upgrade_response(
    response_text: str, new_value_id: str
) -> list[tuple[Edge, Upgrade]]:
    """Parse upgrade detection response into Edge + Upgrade pairs."""
    try:
        data = json.loads(response_text)
    except json.JSONDecodeError:
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        if start == -1 or end == 0:
            return []
        try:
            data = json.loads(response_text[start:end])
        except json.JSONDecodeError:
            return []

    results = []
    for u in data.get("upgrades", []):
        likelihood = u.get("likelihood", "C")
        # Only accept A or B grade upgrades
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


# -- Message builders are the public API. --
# The actual LLM calls happen in the tool bridge, which knows
# how to talk to whatever model Hermes is currently using.

def extraction_messages(context: str) -> list[dict]:
    """Build messages for value extraction."""
    return _build_extraction_messages(context)


def duplicate_check_messages(new_value: Value, existing: list[Value]) -> list[dict]:
    """Build messages for duplicate checking."""
    return _build_duplicate_check_messages(new_value, existing)


def upgrade_detection_messages(new_value: Value, existing: list[Value]) -> list[dict]:
    """Build messages for upgrade detection."""
    return _build_upgrade_detection_messages(new_value, existing)


def render_summary_messages(
    top_values: list[Value],
    upgrades: list[Upgrade],
    total_count: int,
) -> list[dict]:
    """Build messages for USER.md summary rendering."""
    return _build_render_messages(top_values, upgrades, total_count)
