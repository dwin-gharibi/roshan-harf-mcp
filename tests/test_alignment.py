"""Tests for the forced-alignment tool."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from roshan_harf_mcp.tools.alignment import harf_align

from .conftest import BASE_URL

_ENDPOINT = f"{BASE_URL}/api/alignment/"

_SAMPLE = {
    "media_url": "https://i.ganjoor.net/a2/41417.mp3",
    "text": "حکایت یکی را از حکما",
    "segments": [
        {"start": "0:00:00.240000", "end": "0:00:00.800000", "text": "حکایت"},
        {"start": "0:00:02.550000", "end": "0:00:02.830000", "text": "یکی"},
    ],
}


@pytest.mark.asyncio
@respx.mock
async def test_align_returns_segments() -> None:
    route = respx.post(_ENDPOINT).mock(return_value=httpx.Response(200, json=_SAMPLE))
    result = await harf_align(
        media_url="https://i.ganjoor.net/a2/41417.mp3", text="حکایت یکی را از حکما"
    )
    assert result["media_url"] == "https://i.ganjoor.net/a2/41417.mp3"
    assert result["segments"][0]["text"] == "حکایت"
    sent = json.loads(route.calls[0].request.content)
    assert sent["media_url"] == "https://i.ganjoor.net/a2/41417.mp3"
    assert sent["text"] == "حکایت یکی را از حکما"


@pytest.mark.asyncio
async def test_align_rejects_empty_text() -> None:
    result = await harf_align(media_url="https://x.test/a.mp3", text="   ")
    assert "error" in result
    assert "text must be a non-empty string" in result["error"]


@pytest.mark.asyncio
async def test_align_rejects_bad_url() -> None:
    result = await harf_align(media_url="ftp://x", text="hello")
    assert "error" in result
