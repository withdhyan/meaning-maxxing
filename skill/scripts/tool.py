"""
Hermes tool bridge for value extraction.

Registers a 'values' tool with the Hermes ToolRegistry, exposing
five actions: extract, show, upgrades, remove, tws.

The tool orchestrates the full pipeline:
  conversation context -> extraction -> deduplication -> upgrade detection
  -> graph mutation -> USER.md rendering

LLM calls go through Hermes's auxiliary_client so they use whatever
model the user has configured, respect rate limits, and appear in
usage tracking.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable, Coroutine, Optional

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

# Type alias for the LLM call function
LLMCall = Callable[[list[dict]], Coroutine[Any, Any, str]]

# -- Tool Schema (OpenAI function-calling format) --

TOOL_NAME = "values"
TOOL_DESCRIPTION = (
    "Maintain the user's moral graph \u2014 their deeply held sources of meaning. "
    "Use 'extract' when you notice a value-laden moment in conversation. "
    "Use 'show' to view the user's value landscape. "
    "Use 'upgrades' to see how their values have evolved. "
    "Use 'remove' to delete a value the user disowns. "
    "Use 'tws' to see The Wisdom Score."
)

TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": ["extract", "show", "upgrades", "remove", "tws"],
            "description": (
                "extract: Extract a value from conversation context. "
                "show: Display the current moral graph. "
                "upgrades: Show growth trajectories between values. "
                "remove: Remove a value by ID. "
                "tws: Show The Wisdom Score."
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
    registration bridge provides -- this decouples us from any specific
    LLM client.
    """

    def __init__(self, store: Optional[ValueStore] = None):
        self.store = store or ValueStore()

    async def handle(
        self,
        arguments: dict[str, Any],
        llm_call: Optional[LLMCall] = None,
    ) -> str:
        action = arguments.get("action", "show")

        dispatch = {
            "extract": lambda: self._extract(arguments, llm_call),
            "show": lambda: self._show(),
            "upgrades": lambda: self._upgrades(),
            "remove": lambda: self._remove(arguments),
            "tws": lambda: self._tws(),
        }

        handler = dispatch.get(action)
        if handler is None:
            return json.dumps({"error": f"Unknown action: {action}"})

        result = handler()
        # Await if coroutine
        if hasattr(result, "__await__"):
            return await result
        return result

    async def _extract(self, arguments: dict, llm_call: Optional[LLMCall]) -> str:
        context = arguments.get("context", "")
        if not context:
            return json.dumps({"error": "No context provided for extraction."})

        if llm_call is None:
            return json.dumps({
                "error": "LLM call function not available. Cannot extract values."
            })

        # Step 1: Extract
        response = await llm_call(extraction_messages(context))
        value = parse_extraction_response(response)

        if value is None:
            return json.dumps({
                "result": "No source of meaning detected in this passage.",
                "action": "none",
            })

        value.source_context = context[:500]

        # Step 2: Deduplicate
        existing = self.store.get_all_values()
        if existing:
            dup_response = await llm_call(duplicate_check_messages(value, existing))
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
            upg_response = await llm_call(
                upgrade_detection_messages(value, existing)
            )
            for edge, upgrade in parse_upgrade_response(upg_response, value.id):
                self.store.add_edge(edge)
                self.store.add_upgrade(upgrade)
                src = self.store.get_value(edge.source_id)
                upgrade_results.append({
                    "from": src.title if src else edge.source_id,
                    "to": value.title,
                    "clarification": upgrade.clarification,
                })

        # Step 5: Update USER.md
        self._render_user_md(llm_call)

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

        tws = self.store.compute_tws()
        result["tws"] = tws["tws"]

        return json.dumps(result)

    def _show(self) -> str:
        return self.store.format_graph_summary()

    def _upgrades(self) -> str:
        return self.store.format_upgrades_summary()

    def _tws(self) -> str:
        tws = self.store.compute_tws()
        if tws["tws"] == 0:
            return "No Wisdom Score yet — values and growth trajectories are needed."
        return (
            f"**The Wisdom Score: {tws['tws']:.2f}**\n\n"
            f"- Depth: {tws['depth']:.2f} — "
            f"how strongly your deepest commitments stand out\n"
            f"- Growth: {tws['growth']:.2f} — "
            f"how much moral evolution has occurred\n"
            f"- Coherence: {tws['coherence']:.2f} — "
            f"how interconnected your value landscape is\n\n"
            f"TWS is the geometric mean of all three. "
            f"All must be present for wisdom to register."
        )

    def _remove(self, arguments: dict) -> str:
        value_id = arguments.get("value_id", "")
        if not value_id:
            return json.dumps({"error": "No value_id provided."})

        value = self.store.get_value(value_id)
        if value is None:
            return json.dumps({"error": f"Value '{value_id}' not found."})

        title = value.title
        self.store.remove_value(value_id)
        update_user_md(self.store)

        return json.dumps({
            "result": f"Removed: {title}",
            "action": "removed",
            "value_id": value_id,
        })

    def _render_user_md(self, llm_call: Optional[LLMCall]) -> None:
        """Best-effort USER.md update. Falls back to deterministic if LLM fails."""
        top = self.store.top_values(5)
        recent_upgrades = self.store.get_recent_upgrades(3)
        total = len(self.store.get_all_values())

        # For now, deterministic rendering (LLM rendering requires await
        # which complicates the sync/async boundary here — the full LLM
        # render path is available via render_summary_messages for callers
        # who can await).
        update_user_md(self.store)
