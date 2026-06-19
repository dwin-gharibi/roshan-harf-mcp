from __future__ import annotations

import json
import wave

import httpx
import pytest
import respx

from roshan_harf_mcp.tools.tts import _write_wav, harf_tts

from .conftest import BASE_URL

_ENDPOINT = f"{BASE_URL}/api/tts/"

_SAMPLE = {
    "samplerate": 22050,
    "phonemes": "s a l A m",
    "audio_gen_time": [0.12],
    "phoneme_gen_time": [0.01],
    "waveform": [0.0, 0.5, -0.5, 1.0, -1.0],
}


@pytest.mark.asyncio
@respx.mock
async def test_tts_returns_waveform_and_sends_payload() -> None:
    route = respx.post(_ENDPOINT).mock(return_value=httpx.Response(200, json=_SAMPLE))
    result = await harf_tts(text_input="سلام")
    assert result["samplerate"] == 22050
    assert result["waveform"] == [0.0, 0.5, -0.5, 1.0, -1.0]
    assert "saved_to" not in result
    sent = json.loads(route.calls[0].request.content)
    assert sent == {"text_input": "سلام", "voice": "female"}


@pytest.mark.asyncio
@respx.mock
async def test_tts_male_voice_in_payload() -> None:
    route = respx.post(_ENDPOINT).mock(return_value=httpx.Response(200, json=_SAMPLE))
    await harf_tts(text_input="سلام", voice="male")
    sent = json.loads(route.calls[0].request.content)
    assert sent["voice"] == "male"


@pytest.mark.asyncio
async def test_tts_rejects_empty_text() -> None:
    result = await harf_tts(text_input="   ")
    assert "error" in result
    assert "text_input must be a non-empty string" in result["error"]


@pytest.mark.asyncio
async def test_tts_rejects_bad_voice() -> None:
    result = await harf_tts(text_input="hi", voice="robot")
    assert "error" in result
    assert "voice must be one of" in result["error"]


@pytest.mark.asyncio
@respx.mock
async def test_tts_writes_wav_when_save_path_given(tmp_path) -> None:
    respx.post(_ENDPOINT).mock(return_value=httpx.Response(200, json=_SAMPLE))
    out = tmp_path / "out.wav"
    result = await harf_tts(text_input="سلام", save_path=str(out))
    assert result["saved_to"] == str(out)
    assert result["samples_written"] == len(_SAMPLE["waveform"])
    assert out.is_file() and out.stat().st_size > 44

    with wave.open(str(out), "rb") as wav:
        assert wav.getnchannels() == 1
        assert wav.getsampwidth() == 2
        assert wav.getframerate() == 22050
        assert wav.getnframes() == len(_SAMPLE["waveform"])


@pytest.mark.asyncio
@respx.mock
async def test_tts_save_path_bad_dir_is_clean_error(tmp_path) -> None:
    respx.post(_ENDPOINT).mock(return_value=httpx.Response(200, json=_SAMPLE))
    bad = tmp_path / "nope" / "out.wav"
    result = await harf_tts(text_input="سلام", save_path=str(bad))
    assert "error" in result
    assert "directory does not exist" in result["error"]


def test_write_wav_clamps_and_scales(tmp_path) -> None:
    out = tmp_path / "clamp.wav"
    count = _write_wav(str(out), [2.0, -2.0, 0.0], 16000)
    assert count == 3
    with wave.open(str(out), "rb") as wav:
        frames = wav.readframes(3)
    import struct

    samples = struct.unpack("<3h", frames)
    assert samples[0] == 32767
    assert samples[1] == -32767
    assert samples[2] == 0
