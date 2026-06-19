from __future__ import annotations
from typing import Any
from mcp.server.fastmcp import FastMCP

from ..guardrails import validate_url
from ._base import register
from ._exec import run_with_client

_ENDPOINT = "/api/download_original/"


def register_tools(mcp: FastMCP) -> None:
    """Register the media tools on ``mcp``."""

    @register(mcp)
    async def harf_download_original(
        media_url: str,
        instance: str | None = None,
    ) -> dict[str, Any]:
        """Get a short-lived signed download link for a Harf (حرف) media file.

        Calls ``POST /api/download_original/`` to obtain a signed
        ``download_link`` for an original media file stored by the Harf
        deployment. The link is local to the deployment and expires quickly
        (about 30 seconds), so fetch it immediately after this call.

        Args:
            media_url: URL of the original media file held by the deployment.
            instance: Name of the configured Harf instance (omit for default).

        Returns:
            ``{"download_link": "<signed url>"}``.
        """

        url = validate_url(media_url, field="media_url")
        payload = {"media_url": url}
        return await run_with_client(
            instance, lambda client: client.post_json(_ENDPOINT, payload)
        )

    globals()["harf_download_original"] = harf_download_original
