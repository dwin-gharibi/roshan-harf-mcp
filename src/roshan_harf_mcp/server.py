"""Server factory for roshan-harf-mcp.

Builds a :class:`~mcp.server.fastmcp.FastMCP` instance with all Harf (حرف)
tools registered. A module-level ``mcp`` is also provided for ``mcp dev`` and
similar tooling that expects a top-level server object.
"""

from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP

from .config import get_settings
from .tools import register_all

SERVER_NAME = "roshan-harf-mcp"

INSTRUCTIONS = (
    "MCP server for Roshan AI's Harf (حرف) Persian speech service: "
    "transcription (ASR), forced alignment, real-time streaming, and speaker "
    "tasks (verification, identification, diarization, indexing). Harf is "
    "self-hosted; pass an optional 'instance' argument to route to a specific "
    "deployment, and call 'list_instances' to discover configured ones."
)


def build_server(**kwargs: object) -> FastMCP:
    """Create and configure the FastMCP server.

    Args:
        **kwargs: Extra FastMCP settings (e.g. ``host``, ``port``,
            ``log_level``) forwarded to the constructor. Anything not provided
            falls back to defaults / configured settings.

    Returns:
        A fully configured :class:`FastMCP` with all tools registered.
    """

    settings = get_settings()
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))

    options: dict[str, object] = {
        "instructions": INSTRUCTIONS,
        "log_level": settings.log_level.upper(),
    }
    options.update(kwargs)

    mcp = FastMCP(SERVER_NAME, **options)
    register_all(mcp)
    return mcp


mcp = build_server()
