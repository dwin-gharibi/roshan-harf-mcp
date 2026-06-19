from __future__ import annotations

import json
import os
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from mcp.server.fastmcp import FastMCP

from ..client import RoshanClient
from ..config import InstanceConfig, get_settings
from ..guardrails import ValidationError
from ._base import register

_WS_PATH = "/api/ws_api/transcribe_files/wav/sync/"
_CHUNK_SIZE = 32 * 1024


def _http_to_ws(base_url: str) -> str:
    """Convert an http(s) base URL to its ws(s) equivalent with the WS path."""

    parts = urlsplit(base_url)
    scheme = "wss" if parts.scheme == "https" else "ws"
    return urlunsplit((scheme, parts.netloc, _WS_PATH, "", ""))


async def _resolve_bearer_token(config: InstanceConfig) -> str | None:
    """Return a Bearer access token for ``config`` (static or via login).

    Reuses :class:`RoshanClient` so the WebSocket auth header matches the REST
    auth path exactly. Returns ``None`` when the instance is unauthenticated.
    """

    if config.token:
        return config.token
    if not (config.username and config.password):
        return None
    client = RoshanClient.from_config(config)
    try:
        return await client._login()
    finally:
        await client.aclose()


def register_tools(mcp: FastMCP) -> None:
    """Register the live transcription tools on ``mcp``."""

    @register(mcp)
    async def harf_live_info(instance: str | None = None) -> dict[str, Any]:
        """Describe Harf (حرف) real-time streaming transcription.

        Explains the WebSocket protocol used by ``harf_live_transcribe`` so an
        agent (or a human) can integrate live transcription directly if needed.

        Args:
            instance: Name of the configured Harf instance (omit for default).

        Returns:
            Protocol details including the resolved WebSocket URL for the
            instance, the expected message shapes, and the ``finalize`` signal.
        """

        settings = get_settings()
        config = settings.resolve(instance)
        return {
            "endpoint": _WS_PATH,
            "websocket_url": _http_to_ws(config.base_url),
            "protocol": [
                "Open a WebSocket and send an 'Authorization: Bearer "
                "<access_token>' header (obtain the token via POST "
                "/auth/glogin/ if only username/password are configured).",
                "Stream raw 16-bit PCM WAV audio bytes in binary frames.",
                "Receive JSON messages: {segment_id, text, start, end} for "
                "segments and {state: 'PENDING'} for progress.",
                "Send the text message 'finalize' to flush and end the stream.",
            ],
            "auth": "Authorization: Bearer <access_token>",
            "note": (
                "Uncertain words are wrapped in square brackets, as with batch "
                "transcription."
            ),
        }

    @register(mcp)
    async def harf_live_transcribe(
        file_path: str,
        instance: str | None = None,
    ) -> dict[str, Any]:
        """Stream a local WAV file to Harf (حرف) for real-time transcription.

        Opens a WebSocket to the Harf live endpoint, streams the WAV file in
        chunks, sends ``finalize``, and collects the transcription segments
        returned by the server. This demonstrates / drives the same realtime
        path a microphone client would use.

        If the ``websockets`` dependency or the connection is unavailable, a
        clear ``{"error": ...}`` with guidance is returned instead of raising.

        Args:
            file_path: Absolute path to a local WAV (16-bit PCM) file.
            instance: Name of the configured Harf instance (omit for default).

        Returns:
            ``{"segments": [{segment_id, text, start, end}, ...], "count": int}``
            on success, or ``{"error": ...}`` with guidance otherwise.
        """

        if not file_path or not os.path.isfile(file_path):
            raise ValidationError(f"file_path is not a readable file: {file_path!r}")

        try:
            import websockets
        except ImportError:
            return {
                "error": (
                    "The 'websockets' package is required for live transcription. "
                    "Install it with 'pip install websockets' and retry."
                ),
                "endpoint": _WS_PATH,
            }

        settings = get_settings()
        config = settings.resolve(instance)
        ws_url = _http_to_ws(config.base_url)

        segments: list[dict[str, Any]] = []
        try:
            token = await _resolve_bearer_token(config)
            headers = [("Authorization", f"Bearer {token}")] if token else []
            async with websockets.connect(
                ws_url, additional_headers=headers
            ) as ws:
                with open(file_path, "rb") as fh:
                    while chunk := fh.read(_CHUNK_SIZE):
                        await ws.send(chunk)
                await ws.send("finalize")
                async for message in ws:
                    if isinstance(message, bytes):
                        continue
                    try:
                        data = json.loads(message)
                    except json.JSONDecodeError:
                        continue
                    if data.get("state") == "PENDING":
                        continue
                    if "text" in data:
                        segments.append(data)
        except Exception as exc:
            return {
                "error": (
                    f"Live transcription connection failed: {exc}. Verify the "
                    f"instance base_url/credentials and that the deployment "
                    f"exposes {_WS_PATH}."
                ),
                "websocket_url": ws_url,
            }

        return {"segments": segments, "count": len(segments)}

    globals()["harf_live_info"] = harf_live_info
    globals()["harf_live_transcribe"] = harf_live_transcribe
