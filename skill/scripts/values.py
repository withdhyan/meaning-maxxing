"""
Value extraction: the whole thing.

Extract values from conversation. Write them to USER.md. That's it.

Run as a CLI:
    python values.py extract "<conversation passage>"   # print articulation prompt
    echo '<json>' | python values.py add --context "<passage>"
    python values.py show
    python values.py remove <id>
"""

from __future__ import annotations

import argparse
import json
import re
import sys
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

# Validation limits for LLM-extracted content. parse_extraction is the choke
# point between conversation-derived text and USER.md (which becomes standing
# context in every future session), so anything that doesn't match the
# documented attention-policy format is discarded.
MAX_TITLE_LEN = 80
MAX_POLICY_LEN = 200
MAX_POLICIES = 6
MAX_DESCRIPTION_LEN = 400
POLICY_RE = re.compile(r"^[A-Z]{2,}\s+\S")  # CAPITALIZED noun + qualifying phrase


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

def _atomic_write(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def load_values(path: Path = VALUES_PATH) -> list[dict]:
    if path.exists():
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError:
            return []
        if isinstance(data, list):
            return data
    return []


def save_values(values: list[dict], path: Path = VALUES_PATH) -> None:
    _atomic_write(path, json.dumps(values, indent=2))


def _update_values(
    path: Path, fn: Callable[[list[dict]], list[dict]]
) -> list[dict]:
    """Load values, apply mutation fn, save. Returns the mutated list.

    Not safe under concurrent writers — last save wins.
    """
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


def _valid_policy(policy: str) -> bool:
    return bool(POLICY_RE.match(policy)) and len(policy) <= MAX_POLICY_LEN


def parse_extraction(response_text: str,
                     source_context: str = "") -> Optional[dict]:
    """Parse and validate LLM response into a value dict, or None.

    Policies that don't match the attention-policy format are discarded;
    a value with no valid policies, or a missing/overlong title, is rejected.
    """
    data = _parse_json(response_text)
    if data is None or not data.get("found", False):
        return None

    title = data.get("title")
    if not isinstance(title, str):
        return None
    title = title.strip()
    if not title or len(title) > MAX_TITLE_LEN:
        return None

    policies = data.get("policies")
    if not isinstance(policies, list):
        return None
    policies = [p.strip() for p in policies if isinstance(p, str)]
    policies = [p for p in policies if _valid_policy(p)][:MAX_POLICIES]
    if not policies:
        return None

    description = data.get("description", "")
    if not isinstance(description, str):
        description = ""

    return make_value(
        title=title,
        policies=policies,
        description=description[:MAX_DESCRIPTION_LEN],
        source_context=source_context,
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
    """Write values into USER.md between marker comments.

    With no values, an existing marker section is emptied (so removals
    propagate), but a file or section is never created just to be empty.
    """
    section_content = render_values_section(values)
    # Strip markers from content to prevent injection
    section_content = section_content.replace(SECTION_START, "").replace(SECTION_END, "")
    if section_content:
        section = f"{SECTION_START}\n{section_content}\n{SECTION_END}"
    else:
        section = f"{SECTION_START}\n{SECTION_END}"

    if user_md_path.exists():
        content = user_md_path.read_text()
        start_idx = content.find(SECTION_START)
        end_match = content.find(SECTION_END, start_idx) if start_idx != -1 else -1
        if start_idx != -1 and end_match != -1:
            end_idx = end_match + len(SECTION_END)
            content = content[:start_idx] + section + content[end_idx:]
        elif section_content:
            content = content.rstrip() + "\n\n" + section + "\n"
        else:
            return
    elif section_content:
        content = section + "\n"
    else:
        return

    _atomic_write(user_md_path, content)


# -- Display --

def format_values(values: list[dict]) -> str:
    if not values:
        return "No values captured yet."
    lines = [f"{len(values)} sources of meaning:\n"]
    for i, v in enumerate(values, 1):
        lines.append(f"{i}. **{v['title']}** (id: {v['id']})")
        for p in v["policies"]:
            lines.append(f"   - {p}")
        if v.get("description"):
            lines.append(f"   _{v['description']}_")
        lines.append("")
    return "\n".join(lines)


# -- CLI --

def main(argv: list[str] | None = None,
         values_path: Path = VALUES_PATH,
         user_md_path: Path = USER_MD_PATH) -> int:
    parser = argparse.ArgumentParser(
        prog="values", description="Extract and manage sources of meaning.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_extract = sub.add_parser(
        "extract", help="Print the articulation prompt for a passage")
    p_extract.add_argument(
        "context", nargs="?", help="Conversation passage (or pipe via stdin)")

    p_add = sub.add_parser(
        "add", help="Validate and store an extraction JSON read from stdin")
    p_add.add_argument(
        "--context", default="", help="Source conversation passage")

    sub.add_parser("show", help="List captured values")

    p_remove = sub.add_parser("remove", help="Remove a value by id")
    p_remove.add_argument("id")

    args = parser.parse_args(argv)

    if args.command == "extract":
        context = args.context if args.context is not None else sys.stdin.read()
        msgs = extraction_messages(context, load_values(values_path))
        print(f"# system\n{msgs[0]['content']}\n\n# user\n{msgs[1]['content']}")

    elif args.command == "add":
        value = parse_extraction(sys.stdin.read(), source_context=args.context)
        if value is None:
            print("No value extracted.")
            return 1
        values = _update_values(values_path, lambda vs: vs + [value])
        write_to_user_md(values, user_md_path)
        print(f"Noted: {value['title']} ({len(values)} total). "
              "The user can review with `values show` "
              "or delete with `values remove <id>`.")

    elif args.command == "show":
        print(format_values(load_values(values_path)))

    elif args.command == "remove":
        removed = remove_value(args.id, values_path)
        if removed is None:
            print(f"No value with id {args.id}.")
            return 1
        write_to_user_md(load_values(values_path), user_md_path)
        print(f"Removed: {removed['title']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
