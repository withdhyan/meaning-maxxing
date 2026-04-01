"""
Hermes ToolRegistry bridge.

This module registers the 'values' tool with Hermes's tool system.
Import this module from a Hermes startup hook or skill loader to
activate value extraction.

Integration pattern:
    # In a Hermes startup context:
    import skill.scripts.register  # auto-registers on import

Or manually:
    from skill.scripts.register import register_values_tool
    register_values_tool()
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

logger = logging.getLogger("hermes.values")


def register_values_tool() -> bool:
    """Register the values tool with Hermes's ToolRegistry.

    Returns True if registration succeeded, False if Hermes
    ToolRegistry is not available (e.g. running standalone).
    """
    try:
        from tools.registry import ToolRegistry
    except ImportError:
        logger.info(
            "Hermes ToolRegistry not found. "
            "Running in standalone mode — tool not registered."
        )
        return False

    from .store import ValueStore
    from .tool import TOOL_DESCRIPTION, TOOL_NAME, TOOL_SCHEMA, ValuesTool

    values_tool = ValuesTool(store=ValueStore())

    def check_fn() -> bool:
        """Always available — no external dependencies required."""
        return True

    async def handler(arguments: dict[str, Any], **kwargs: Any) -> str:
        """Tool handler that Hermes calls when the LLM invokes 'values'.

        Hermes passes an auxiliary_client in kwargs for making LLM calls.
        We wrap it into the llm_call interface our tool expects.
        """
        aux_client = kwargs.get("auxiliary_client")

        async def llm_call(messages: list[dict]) -> str:
            if aux_client is None:
                raise RuntimeError("No auxiliary client available")
            # Hermes auxiliary_client.chat() returns the response text
            return await aux_client.chat(messages=messages, temperature=0.2)

        return await values_tool.handle(
            arguments=arguments,
            llm_call=llm_call if aux_client else None,
        )

    registry = ToolRegistry()
    registry.register(
        name=TOOL_NAME,
        toolset="value-extraction",
        schema={
            "name": TOOL_NAME,
            "description": TOOL_DESCRIPTION,
            "parameters": TOOL_SCHEMA,
        },
        handler=handler,
        check_fn=check_fn,
        async_=True,
        description=TOOL_DESCRIPTION,
        emoji="💎",
    )

    logger.info("Values tool registered with Hermes ToolRegistry")
    return True


# Auto-register on import
_registered = register_values_tool()
