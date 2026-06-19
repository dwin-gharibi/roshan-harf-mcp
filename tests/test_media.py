"""Tests for the Harf media tool (harf_download_original)."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from roshan_harf_mcp.tools.media import harf_download_original

from .conftest import BASE_URL

_ENDPOINT = f"{BASE_URL}/api/download_original/"


@pytest.mark.asyncio
@respx.mock
async def test_download_original_returns_link() -> None:
    route = respx.post(_ENDPOINT).mock(
        return_value=httpx.Response(
            200, json={"download_link": "https://harf.test/signed/abc?exp=30"}
        )
    )
    result = await harf_download_original(
        media_url="https://harf.test/media/clip.wav"
    )
    assert result["download_link"] == "https://harf.test/signed/abc?exp=30"
    sent = json.loads(route.calls[0].request.content)
    assert sent == {"media_url": "https://harf.test/media/clip.wav"}


@pytest.mark.asyncio
async def test_download_original_rejects_bad_url() -> None:
    result = await harf_download_original(media_url="ftp://x")
    assert "error" in result
    assert "Invalid input" in result["error"]


@pytest.mark.asyncio
async def test_download_original_rejects_empty_url() -> None:
    result = await harf_download_original(media_url="")
    assert "error" in result
