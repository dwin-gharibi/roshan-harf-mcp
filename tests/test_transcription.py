from __future__ import annotations

import json

import httpx
import pytest
import respx

from roshan_harf_mcp.tools.transcription import (
    harf_transcribe,
    harf_transcribe_upload,
    harf_transcription_status,
)

from .conftest import BASE_URL

_ENDPOINT = f"{BASE_URL}/api/transcribe_files/"

_SAMPLE = [
    {
        "media_url": "https://i.ganjoor.net/a2/41417.mp3",
        "duration": "0:00:44",
        "segments": [
            {"start": "0:00:00", "end": "0:00:02", "text": "[حکایت]"},
            {"start": "0:00:02", "end": "0:00:06", "text": "یکی را از حکما شنیدم که می گفت"},
            {
                "start": "0:00:06",
                "end": "0:00:11",
                "text": "هرگز کسی به جهل خویش اقرار نکرده است",
            },
        ],
        "stats": {"words": 57, "known_words": 54},
    }
]


@pytest.mark.asyncio
@respx.mock
async def test_transcribe_wait_true_returns_segments_and_stats() -> None:
    route = respx.post(_ENDPOINT).mock(return_value=httpx.Response(200, json=_SAMPLE))
    result = await harf_transcribe(media_urls=["https://i.ganjoor.net/a2/41417.mp3"])
    assert isinstance(result, list)
    first = result[0]
    assert first["media_url"] == "https://i.ganjoor.net/a2/41417.mp3"
    assert first["duration"] == "0:00:44"
    assert first["segments"][0]["text"] == "[حکایت]"
    assert first["stats"] == {"words": 57, "known_words": 54}
    sent = json.loads(route.calls[0].request.content)
    assert sent["wait"] is True
    assert sent["media_urls"] == ["https://i.ganjoor.net/a2/41417.mp3"]


@pytest.mark.asyncio
@respx.mock
async def test_transcribe_wait_false_returns_task_ids() -> None:
    route = respx.post(_ENDPOINT).mock(
        return_value=httpx.Response(200, json={"state": "PENDING", "task_ids": ["t1"]})
    )
    result = await harf_transcribe(
        media_urls=["https://x.test/a.mp3"], wait=False
    )
    assert result == {"state": "PENDING", "task_ids": ["t1"]}
    sent = json.loads(route.calls[0].request.content)
    assert sent["wait"] is False


@pytest.mark.asyncio
async def test_transcribe_rejects_bad_url() -> None:
    result = await harf_transcribe(media_urls=["not-a-url"])
    assert "error" in result
    assert "Invalid input" in result["error"]


@pytest.mark.asyncio
async def test_transcribe_rejects_empty_list() -> None:
    result = await harf_transcribe(media_urls=[])
    assert "error" in result


@pytest.mark.asyncio
@respx.mock
async def test_transcribe_upload_sends_multipart(tmp_path) -> None:
    audio = tmp_path / "clip.wav"
    audio.write_bytes(b"RIFF....WAVEdata")
    route = respx.post(_ENDPOINT).mock(return_value=httpx.Response(200, json=_SAMPLE))
    result = await harf_transcribe_upload(file_path=str(audio))
    assert result[0]["stats"]["words"] == 57
    sent = route.calls[0].request
    assert "multipart/form-data" in sent.headers["content-type"]
    assert b"RIFF....WAVEdata" in sent.content
    assert b'name="media"' in sent.content
    assert b"clip.wav" in sent.content


@pytest.mark.asyncio
async def test_transcribe_upload_missing_file() -> None:
    result = await harf_transcribe_upload(file_path="/no/such/file.wav")
    assert "error" in result
    assert "not a readable file" in result["error"]


@pytest.mark.asyncio
@respx.mock
async def test_transcription_status_polls_state() -> None:
    route = respx.post(_ENDPOINT).mock(
        return_value=httpx.Response(200, json={"state": "PENDING"})
    )
    result = await harf_transcription_status(task_ids=["t1", "t2"])
    assert result == {"state": "PENDING"}
    sent = json.loads(route.calls[0].request.content)
    assert sent["tasks_ids"] == ["t1", "t2"]
    assert sent["wait"] is False


@pytest.mark.asyncio
async def test_transcription_status_rejects_empty() -> None:
    result = await harf_transcription_status(task_ids=[])
    assert "error" in result


@pytest.mark.asyncio
@respx.mock
async def test_transcribe_routes_to_named_instance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    other = "https://harf.other.example.ir"
    monkeypatch.setenv("ROSHAN_HARF__INSTANCES__OTHER__BASE_URL", other)
    monkeypatch.setenv("ROSHAN_HARF__INSTANCES__OTHER__TOKEN", "tok-other")
    from roshan_harf_mcp import config

    config.get_settings.cache_clear()
    route = respx.post(f"{other}/api/transcribe_files/").mock(
        return_value=httpx.Response(200, json=_SAMPLE)
    )
    result = await harf_transcribe(
        media_urls=["https://x.test/a.mp3"], instance="other"
    )
    assert result[0]["duration"] == "0:00:44"
    assert route.called
    assert route.calls[0].request.headers["authorization"] == "Bearer tok-other"
