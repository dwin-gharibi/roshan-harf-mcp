from __future__ import annotations
from typing import Any
from mcp.server.fastmcp import FastMCP

from .. import catalog
from ._base import register


def _overview() -> dict[str, Any]:
    return {
        "service": catalog.SERVICE,
        "documentation": catalog.DOCS_BASE_URL,
        "tools": catalog.TOOLS,
        "notes": [
            "Every service tool accepts an optional 'instance' argument to "
            "route to a specific self-hosted Harf deployment.",
            "Use 'list_instances' to discover configured instances.",
            "Uncertain transcribed words are wrapped in square brackets.",
        ],
    }


def register_tools(mcp: FastMCP) -> None:
    """Register the documentation tool on ``mcp``."""

    @register(mcp)
    async def roshan_harf_docs(topic: str | None = None) -> dict[str, Any]:
        """Return documentation about Harf (حرف) and this server's tools.

        Provides an offline, structured reference for the Roshan speech service
        and the MCP tools exposed here, including each tool's HTTP endpoint and
        a link to the official docs at https://docs.roshan-ai.ir. Call this
        first to understand available capabilities.

        Args:
            topic: Optional tool name (e.g. ``"harf_transcribe"``) to get
                details for just that tool. Omit for the full overview.

        Returns:
            A documentation payload. When ``topic`` names a known tool, returns
            that tool's metadata and a docs link; otherwise the full overview.
        """

        if topic:
            entry = catalog.tool_by_name(topic)
            if entry is None:
                return {
                    "error": (
                        f"Unknown topic '{topic}'. Known tools: "
                        + ", ".join(t["name"] for t in catalog.TOOLS)
                    ),
                    "documentation": catalog.DOCS_BASE_URL,
                }
            return {
                "tool": entry,
                "service": catalog.SERVICE["name"],
                "documentation": catalog.DOCS_BASE_URL,
            }
        return _overview()

    globals()["roshan_harf_docs"] = roshan_harf_docs
