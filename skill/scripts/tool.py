"""
Hermes tool bridge for value extraction.

Registers a 'values' tool with the Hermes ToolRegistry, exposing
four actions: extract, show, upgrades, remove.

The tool orchestrates the full pipeline:
  conversation context → extraction → deduplication → upgrade detection
  → graph mutation → USER.md rendering

LLM calls go through Hermes's auxiliary_client so they use whatever
model the user has configured, respect rate limits, and appear in
usage tracking.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from .extractor import (
    duplicate_check_messages,
    extraction_messages,
    parse_duplicate_check_response,
    parse_extraction_response,
    parse_upgrade_response,
    render_summary_messages,
    upgrade_detection_messages,
)
from .renderer import update_user_md
from .store import ValueStore

logger = logging.getLogger("hermes.values")

# -- Tool Schema (OpenAI function-calling format) --

TOOL_NAME = "values"
TOOL_DESCRIPTION = (
    "Maintain the user's moral graph — their deeply held sources of meaning. "
    "Use 'extract' when you notice a value-laden moment in conversation. "
    "Use 'show' to view the user's value landscape. "
    "Use 'upgrades' to see how their values have evolved. "
    "Use 'remove' to delete a value the user disowns."
)

TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": ["extract", "show", "upgrades", "remove"],
            "description": (
                "extract: Extract a value from conversation context. "
                "show: Display the current moral graph. "
                "upgrades: Show growth trajectories between values. "
                "remove: Remove a value by ID."
            ),
        },
        "context": {
            "type": "string",
            "description": (
                "For 'extract': the relevant conversation passage that "
                "contains a potential source of meaning. Required for extract."
            ),
        },
        "value_id": {
            "type": "string",
            "description": "For 'remove': the ID of the value to remove.",
        },
    },
    "required": ["action"],
}


class ValuesTool:
    """Orchestrator for the values tool.

    Designed to be instantiated once and registered with Hermes's ToolRegistry.
    LLM calls are delegated to a callable `llm_call` function that the
    registration bridge provides — this decouples us from any specific
    LLM client.
    """

    def __init__(self, store: ValueStore | None = None):
        self.store = store or ValueStore()

    async def handle(
        self,
        arguments: dict[str, Any],
        llm_call: Any = None,
    ) -> str:
        """Main dispatch for the values tool.

        Args:
            arguments: The tool call arguments from the LLM.
            llm_call: An async callable(messages) -> str that sends
                      messages to an LLM and returns the response text.
                      If None, LLM-dependent features degrade gracefully.
        """
        action = arguments.get("action", "show")

        if action == "extract":
            return await self._extract(arguments, llm_call)
        elif action == "show":
            return self._show()
        elif action == "upgrades":
            return self._upgrades()
        elif action == "remove":
            return self._remove(arguments)
        else:
            return json.dumps({"error": f"Unknown action: {action}"})

    async def _extract(self, arguments: dict, llm_call: Any) -> str:
        context = arguments.get("context", "")
        if not context:
            return json.dumps({"error": "No context provided for extraction."})

        if llm_call is None:
            return json.dumps({
                "error": "LLM call function not available. Cannot extract values."
            })

        # Step 1: Extract the value
        messages = extraction_messages(context)
        response = await llm_call(messages)
        value = parse_extraction_response(response)

        if value is None:
            return json.dumps({
                "result": "No source of meaning detected in this passage.",
                "action": "none",
            })

        value.source_context = context[:500]  # truncate for storage

        # Step 2: Check for duplicates
        existing = self.store.get_all_values()
        if existing:
            dup_messages = duplicate_check_messages(value, existing)
            dup_response = await llm_call(dup_messages)
            duplicate_of = parse_duplicate_check_response(dup_response)
            if duplicate_of:
                existing_value = self.store.get_value(duplicate_of)
                name = existing_value.title if existing_value else duplicate_of
                return json.dumps({
                    "result": f"Value already captured as '{name}'.",
                    "action": "deduplicated",
                    "duplicate_of": duplicate_of,
                })

        # Step 3: Add to graph
        self.store.add_value(value)

        # Step 4: Detect upgrades
        upgrade_results = []
        if existing:
            upg_messages = upgrade_detection_messages(value, existing)
            upg_response = await llm_call(upg_messages)
            pairs = parse_upgrade_response(upg_response, value.id)
            for edge, upgrade in pairs:
                self.store.add_edge(edge)
                self.store.add_upgrade(upgrade)
                src = self.store.get_value(edge.source_id)
                upgrade_results.append({
                    "from": src.title if src else edge.source_id,
                    "to": value.title,
                    "clarification": upgrade.clarification,
                })

        # Step 5: Update USER.md
        top = self.store.top_values(5)
        recent_upgrades = self.store.get_recent_upgrades(3)
        total = len(self.store.get_all_values())

        try:
            render_msgs = render_summary_messages(top, recent_upgrades, total)
            summary = await llm_call(render_msgs)
            update_user_md(self.store, llm_summary=summary)
        except Exception:
            # Fallback to deterministic rendering
            update_user_md(self.store)
            logger.warning("LLM render failed, using deterministic summary")

        result = {
            "result": f"Captured: {value.title}",
            "action": "extracted",
            "value": {
                "id": value.id,
                "title": value.title,
                "policies": [p.text for p in value.policies],
            },
        }
        if upgrade_results:
            result["upgrades_detected"] = upgrade_results

        return json.dumps(result)

    def _show(self) -> str:
        return self.store.format_graph_summary()

    def _upgrades(self) -> str:
        upgrades = self.store.graph.upgrades
        if not upgrades:
            return "No growth trajectories recorded yet."

        lines = ["Growth trajectories:\n"]
        for u in upgrades:
            src = self.store.get_value(u.source_id)
            wiser = self.store.get_value(u.wiser_id)
            src_name = src.title if src else u.source_id
            wiser_name = wiser.title if wiser else u.wiser_id
            lines.append(f"**{src_name}** → **{wiser_name}**")
            lines.append(f"  {u.clarification}")
            if u.story:
                lines.append(f"  _{u.story}_")
            lines.append("")

        return "\n".join(lines)

    def _remove(self, arguments: dict) -> str:
        value_id = arguments.get("value_id", "")
        if not value_id:
            return json.dumps({"error": "No value_id provided."})

        value = self.store.get_value(value_id)
        if value is None:
            return json.dumps({"error": f"Value '{value_id}' not found."})

        title = value.title
        self.store.remove_value(value_id)

        # Re-render USER.md after removal
        update_user_md(self.store)

        return json.dumps({
            "result": f"Removed: {title}",
            "action": "removed",
            "value_id": value_id,
        })
