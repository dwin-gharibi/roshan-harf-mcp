from __future__ import annotations
from typing import Any
from mcp.server.fastmcp import FastMCP

from ..guardrails import validate_named_urls, validate_url, validate_urls
from ._base import register
from ._exec import run_with_client

_VERIFICATION = "/api/speaker_tasks/verification/"
_IDENTIFICATION = "/api/speaker_tasks/identification/"
_DIARIZATION = "/api/speaker_tasks/diarization/"
_INDEXING = "/api/speaker_tasks/indexing/"


def register_tools(mcp: FastMCP) -> None:
    """Register the speaker tools on ``mcp``."""

    @register(mcp)
    async def harf_speaker_verification(
        media_url: str,
        target_urls: list[str],
        instance: str | None = None,
    ) -> Any:
        """Verify a speaker against reference audio using Harf (حرف).

        Speaker verification (تأیید گوینده): checks whether the speaker in
        ``media_url`` matches the claimed speaker represented by one or more
        reference recordings in ``target_urls``. The similarity threshold is
        ``0.65``.

        Args:
            media_url: HTTP(S) URL of the probe audio to check.
            target_urls: HTTP(S) URLs of reference audio for the claimed speaker.
            instance: Name of the configured Harf instance (omit for default).

        Returns:
            A list like ``[{"result": "Verified"|"Rejected", "similarity": float}]``.
        """

        url = validate_url(media_url, field="media_url")
        targets = validate_urls(target_urls, field="target_urls")
        payload = {"media_url": url, "target_urls": targets}
        return await run_with_client(
            instance, lambda client: client.post_json(_VERIFICATION, payload)
        )

    @register(mcp)
    async def harf_speaker_identification(
        media_url: str,
        target_urls: dict[str, list[str]],
        instance: str | None = None,
    ) -> Any:
        """Identify which known speaker a probe most resembles with Harf (حرف).

        Speaker identification (شناسایی گوینده): compares the probe audio in
        ``media_url`` against a set of named speakers (each with one or more
        reference recordings) and returns the best match.

        Args:
            media_url: HTTP(S) URL of the probe audio.
            target_urls: Mapping of speaker name to a list of reference audio
                URLs, e.g. ``{"Ali": ["https://.../ali1.wav"], "Sara": [...]}``.
            instance: Name of the configured Harf instance (omit for default).

        Returns:
            A list like ``[{"result": "Identified"|"Unknown",
            "most_similar_speaker": str, "similarity": float}]``.
        """

        url = validate_url(media_url, field="media_url")
        targets = validate_named_urls(target_urls, field="target_urls")
        payload = {"media_url": url, "target_urls": targets}
        return await run_with_client(
            instance, lambda client: client.post_json(_IDENTIFICATION, payload)
        )

    @register(mcp)
    async def harf_speaker_diarization(
        media_urls: list[str],
        instance: str | None = None,
    ) -> Any:
        """Diarize audio by speaker ("who spoke when") using Harf (حرف).

        Speaker diarization (تفکیک گویندگان): segments each media file by
        speaker and includes the transcribed text for every segment. Speakers
        are labelled generically (e.g. ``SPEAKER_00``).

        Args:
            media_urls: HTTP(S) URLs of the audio files to diarize.
            instance: Name of the configured Harf instance (omit for default).

        Returns:
            A list like
            ``[{"media_url": str, "segments": [{"start", "end", "speaker", "text"}]}]``.
        """

        urls = validate_urls(media_urls, field="media_urls")
        payload = {"media_urls": urls}
        return await run_with_client(
            instance, lambda client: client.post_json(_DIARIZATION, payload)
        )

    @register(mcp)
    async def harf_speaker_indexing(
        media_url: str,
        target_urls: dict[str, list[str]],
        instance: str | None = None,
    ) -> Any:
        """Index a media file against known speakers with Harf (حرف).

        Speaker indexing (نمایه‌سازی گویندگان): segments the audio in
        ``media_url`` and labels each timestamped, transcribed segment with the
        most similar known speaker from ``target_urls``.

        Args:
            media_url: HTTP(S) URL of the audio to index.
            target_urls: Mapping of speaker name to a list of reference audio
                URLs, e.g. ``{"Ali": ["https://.../ali1.wav"]}``.
            instance: Name of the configured Harf instance (omit for default).

        Returns:
            A list like
            ``[{"start", "end", "result", "most_similar_speaker", "similarity", "text"}]``.
        """

        url = validate_url(media_url, field="media_url")
        targets = validate_named_urls(target_urls, field="target_urls")
        payload = {"media_url": url, "target_urls": targets}
        return await run_with_client(
            instance, lambda client: client.post_json(_INDEXING, payload)
        )

    globals()["harf_speaker_verification"] = harf_speaker_verification
    globals()["harf_speaker_identification"] = harf_speaker_identification
    globals()["harf_speaker_diarization"] = harf_speaker_diarization
    globals()["harf_speaker_indexing"] = harf_speaker_indexing
