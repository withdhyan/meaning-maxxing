"""
USER.md renderer.

Takes the moral graph and produces a concise prose summary suitable
for injection into Hermes's USER.md. The summary is generated via
LLM but can fall back to a deterministic template if no LLM is available.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .store import ValueStore

HERMES_HOME = Path.home() / ".hermes"
USER_MD_PATH = HERMES_HOME / "USER.md"

# Marker comments to delimit the values section within USER.md
VALUES_SECTION_START = "<!-- values-start -->"
VALUES_SECTION_END = "<!-- values-end -->"


def render_deterministic(store: ValueStore) -> str:
    """Produce a deterministic (no LLM) summary of top values.

    Used as a fallback when no LLM call is possible, or as the
    initial render before the LLM summary is ready.
    """
    top = store.top_values(5)
    if not top:
        return ""

    parts = []
    for v in top:
        policies_str = "; ".join(str(p) for p in v.policies[:3])
        parts.append(f"{v.title} — {policies_str}")

    return "Sources of meaning: " + ". ".join(parts) + "."


def _sanitize_summary(summary: str) -> str:
    """Strip marker strings from summary to prevent injection."""
    return summary.replace(VALUES_SECTION_START, "").replace(VALUES_SECTION_END, "")


def inject_into_user_md(
    values_summary: str,
    user_md_path: Path = USER_MD_PATH,
) -> None:
    """Write the values summary into USER.md between marker comments.

    Preserves any existing USER.md content outside the markers.
    If USER.md doesn't exist, creates it with just the values section.
    If markers don't exist, appends the section at the end.
    """
    values_summary = _sanitize_summary(values_summary)
    if not values_summary.strip():
        return

    section = f"{VALUES_SECTION_START}\n{values_summary}\n{VALUES_SECTION_END}"

    if user_md_path.exists():
        content = user_md_path.read_text()

        if VALUES_SECTION_START in content and VALUES_SECTION_END in content:
            start_idx = content.index(VALUES_SECTION_START)
            end_idx = content.index(VALUES_SECTION_END) + len(VALUES_SECTION_END)
            content = content[:start_idx] + section + content[end_idx:]
        else:
            content = content.rstrip() + "\n\n" + section + "\n"
    else:
        user_md_path.parent.mkdir(parents=True, exist_ok=True)
        content = section + "\n"

    user_md_path.write_text(content)


def update_user_md(
    store: ValueStore,
    llm_summary: Optional[str] = None,
    user_md_path: Path = USER_MD_PATH,
) -> str:
    """Update USER.md with the current value landscape.

    If llm_summary is provided (from the render prompt), uses that.
    Otherwise falls back to the deterministic renderer.

    Returns the summary that was written.
    """
    summary = llm_summary if llm_summary else render_deterministic(store)
    inject_into_user_md(summary, user_md_path=user_md_path)
    return summary
