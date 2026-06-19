from __future__ import annotations
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..guardrails import ValidationError, validate_url
from ._base import register
from ._exec import run_with_client

_ENDPOINT = "/api/alignment/"


def register_tools(mcp: FastMCP) -> None:
    """Register the alignment tool on ``mcp``."""

    @register(mcp)
    async def harf_align(
        media_url: str,
        text: str,
        instance: str | None = None,
    ) -> Any:
        """Force-align a known Persian transcript to its audio with Harf (حرف).

        Given an audio/video URL and the text that is spoken in it, returns
        per-segment timestamps (هم‌ترازسازی متن و صدا). Useful for building
        subtitles/captions or word-level timing from an existing transcript.

        Args:
            media_url: HTTP(S) URL of the audio/video file.
            text: The transcript text to align to the audio.
            instance: Name of the configured Harf instance (omit for default).

        Returns:
            ``{media_url, text, segments:[{start, end, text}]}``.
        """

        url = validate_url(media_url, field="media_url")
        if not isinstance(text, str) or not text.strip():
            raise ValidationError("text must be a non-empty string.")
        payload = {"media_url": url, "text": text}
        return await run_with_client(
            instance, lambda client: client.post_json(_ENDPOINT, payload)
        )

    globals()["harf_align"] = harf_align
