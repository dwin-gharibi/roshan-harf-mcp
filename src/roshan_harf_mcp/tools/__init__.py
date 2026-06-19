from __future__ import annotations
from mcp.server.fastmcp import FastMCP
from . import alignment, common, docs, live, media, speaker, transcription, tts

__all__ = [
    "register_all",
    "alignment",
    "common",
    "docs",
    "live",
    "media",
    "speaker",
    "transcription",
    "tts",
]


def register_all(mcp: FastMCP) -> None:
    """Register every tool module on ``mcp``."""

    docs.register_tools(mcp)
    common.register_tools(mcp)
    transcription.register_tools(mcp)
    tts.register_tools(mcp)
    media.register_tools(mcp)
    alignment.register_tools(mcp)
    live.register_tools(mcp)
    speaker.register_tools(mcp)
