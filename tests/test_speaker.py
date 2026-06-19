"""Tests for the four speaker tools (verification, identification, diarization, indexing)."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from roshan_harf_mcp.tools.speaker import (
    harf_speaker_diarization,
    harf_speaker_identification,
    harf_speaker_indexing,
    harf_speaker_verification,
)

from .conftest import BASE_URL

_VERIFICATION = f"{BASE_URL}/api/speaker_tasks/verification/"
_IDENTIFICATION = f"{BASE_URL}/api/speaker_tasks/identification/"
_DIARIZATION = f"{BASE_URL}/api/speaker_tasks/diarization/"
_INDEXING = f"{BASE_URL}/api/speaker_tasks/indexing/"


@pytest.mark.asyncio
@respx.mock
async def test_verification() -> None:
    route = respx.post(_VERIFICATION).mock(
        return_value=httpx.Response(
            200, json=[{"result": "Verified", "similarity": 0.94}]
        )
    )
    result = await harf_speaker_verification(
        media_url="https://x.test/probe.mp3",
        target_urls=["https://x.test/ref1.mp3", "https://x.test/ref2.mp3"],
    )
    assert result == [{"result": "Verified", "similarity": 0.94}]
    sent = json.loads(route.calls[0].request.content)
    assert sent["media_url"] == "https://x.test/probe.mp3"
    assert sent["target_urls"] == [
        "https://x.test/ref1.mp3",
        "https://x.test/ref2.mp3",
    ]


@pytest.mark.asyncio
async def test_verification_rejects_bad_targets() -> None:
    result = await harf_speaker_verification(
        media_url="https://x.test/probe.mp3", target_urls=[]
    )
    assert "error" in result


@pytest.mark.asyncio
@respx.mock
async def test_identification_named_targets() -> None:
    route = respx.post(_IDENTIFICATION).mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "result": "Identified",
                    "most_similar_speaker": "spk1",
                    "similarity": 0.67,
                }
            ],
        )
    )
    result = await harf_speaker_identification(
        media_url="https://x.test/probe.mp3",
        target_urls={
            "spk1": ["https://x.test/a.mp3", "https://x.test/b.mp3"],
            "spk2": ["https://x.test/c.mp3"],
        },
    )
    assert result[0]["most_similar_speaker"] == "spk1"
    sent = json.loads(route.calls[0].request.content)
    assert sent["target_urls"]["spk1"] == [
        "https://x.test/a.mp3",
        "https://x.test/b.mp3",
    ]


@pytest.mark.asyncio
async def test_identification_rejects_empty_mapping() -> None:
    result = await harf_speaker_identification(
        media_url="https://x.test/probe.mp3", target_urls={}
    )
    assert "error" in result


@pytest.mark.asyncio
@respx.mock
async def test_diarization() -> None:
    route = respx.post(_DIARIZATION).mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "media_url": "https://x.test/panel.wav",
                    "segments": [
                        {
                            "start": 0.0,
                            "end": 3.5,
                            "speaker": "speaker_1",
                            "text": "سلام",
                        }
                    ],
                }
            ],
        )
    )
    result = await harf_speaker_diarization(media_urls=["https://x.test/panel.mp3"])
    assert result[0]["segments"][0]["speaker"] == "speaker_1"
    sent = json.loads(route.calls[0].request.content)
    assert sent["media_urls"] == ["https://x.test/panel.mp3"]


@pytest.mark.asyncio
async def test_diarization_rejects_empty() -> None:
    result = await harf_speaker_diarization(media_urls=[])
    assert "error" in result


@pytest.mark.asyncio
@respx.mock
async def test_indexing() -> None:
    route = respx.post(_INDEXING).mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "start": 0.12,
                    "end": 12.87,
                    "result": "Identified",
                    "most_similar_speaker": "فردوسی‌پور",
                    "similarity": 0.86,
                    "text": "سلام علیکم",
                }
            ],
        )
    )
    result = await harf_speaker_indexing(
        media_url="https://x.test/panel.mp3",
        target_urls={"فردوسی‌پور": ["https://x.test/f1.mp3"]},
    )
    assert result[0]["most_similar_speaker"] == "فردوسی‌پور"
    sent = json.loads(route.calls[0].request.content)
    assert "فردوسی‌پور" in sent["target_urls"]


@pytest.mark.asyncio
async def test_indexing_rejects_bad_media_url() -> None:
    result = await harf_speaker_indexing(
        media_url="ftp://x", target_urls={"a": ["https://x.test/1.mp3"]}
    )
    assert "error" in result
