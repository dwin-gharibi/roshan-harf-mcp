from __future__ import annotations

import os
import struct
import wave
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import RoshanClient
from ..guardrails import ValidationError
from ._base import register
from ._exec import run_with_client

_ENDPOINT = "/api/tts/"
_VOICES = {"female", "male"}
_INT16_MAX = 32767


def _write_wav(path: str, waveform: list[float], samplerate: int) -> int:
    """Write ``waveform`` (floats in roughly [-1, 1]) to a 16-bit PCM WAV.

    Floats are clamped to [-1.0, 1.0] and scaled to signed 16-bit. Returns the
    number of samples written.
    """

    directory = os.path.dirname(os.path.abspath(path))
    if directory and not os.path.isdir(directory):
        raise ValidationError(f"save_path directory does not exist: {directory!r}")

    frames = bytearray()
    for sample in waveform:
        try:
            value = float(sample)
        except (TypeError, ValueError) as exc:
            raise ValidationError(
                "waveform must contain only numbers to write a WAV file."
            ) from exc
        clamped = max(-1.0, min(1.0, value))
        frames += struct.pack("<h", int(round(clamped * _INT16_MAX)))

    with wave.open(path, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(int(samplerate))
        wav.writeframes(bytes(frames))
    return len(waveform)


def register_tools(mcp: FastMCP) -> None:
    """Register the TTS tool on ``mcp``."""

    @register(mcp)
    async def harf_tts(
        text_input: str,
        voice: str = "female",
        save_path: str | None = None,
        instance: str | None = None,
    ) -> dict[str, Any]:
        """Synthesize Persian speech from text with Harf (حرف) TTS.

        Calls Harf's ``POST /api/tts/`` text-to-speech endpoint
        (تبدیل متن به گفتار). Returns the generated audio as a raw float
        ``waveform`` plus its ``samplerate`` and the predicted ``phonemes``.
        Optionally pass ``save_path`` to also write the waveform to a 16-bit
        PCM WAV file on the server's local filesystem (no extra dependency
        needed).

        Args:
            text_input: The Persian text to synthesize (required, non-empty).
            voice: Voice to use, ``"female"`` (default) or ``"male"``.
            save_path: Optional local path; if set, the returned waveform is
                written there as a mono 16-bit WAV.
            instance: Name of the configured Harf instance (omit for default).

        Returns:
            ``{samplerate, phonemes, audio_gen_time, phoneme_gen_time,
            waveform: [float, ...]}``. When ``save_path`` is given, the result
            also includes ``saved_to`` and ``samples_written``.
        """

        if not isinstance(text_input, str) or not text_input.strip():
            raise ValidationError("text_input must be a non-empty string.")
        if voice not in _VOICES:
            raise ValidationError(
                f"voice must be one of {sorted(_VOICES)}, got {voice!r}."
            )
        payload = {"text_input": text_input, "voice": voice}

        async def _call(client: RoshanClient) -> dict[str, Any]:
            return await client.post_json(_ENDPOINT, payload)

        result = await run_with_client(instance, _call)

        if save_path:
            if not isinstance(result, dict):
                raise ValidationError(
                    "Cannot write WAV: Harf TTS did not return a result object."
                )
            waveform = result.get("waveform")
            samplerate = result.get("samplerate")
            if not isinstance(waveform, list) or not waveform:
                raise ValidationError(
                    "Cannot write WAV: TTS response had no 'waveform' data."
                )
            if not isinstance(samplerate, (int, float)) or samplerate <= 0:
                raise ValidationError(
                    "Cannot write WAV: TTS response had no valid 'samplerate'."
                )
            written = _write_wav(save_path, waveform, int(samplerate))
            result = {
                **result,
                "saved_to": os.path.abspath(save_path),
                "samples_written": written,
            }
        return result

    globals()["harf_tts"] = harf_tts
