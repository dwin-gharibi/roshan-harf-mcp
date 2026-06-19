from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import RoshanClient
from ..guardrails import ValidationError, validate_urls
from ._base import register
from ._exec import run_with_client

_ENDPOINT = "/api/transcribe_files/"


def register_tools(mcp: FastMCP) -> None:
    """Register transcription tools on ``mcp``."""

    @register(mcp)
    async def harf_transcribe(
        media_urls: list[str],
        wait: bool = True,
        instance: str | None = None,
    ) -> Any:
        """Transcribe Persian audio/video files by URL using Harf (حرف).

        Performs automatic speech recognition (ASR / تبدیل گفتار به متن) on one
        or more remote media files. Uncertain words are wrapped in square
        brackets in the returned text.

        When ``wait`` is true (default) the call blocks until transcription
        finishes and returns the full result per file. When ``wait`` is false
        the call returns immediately with ``{"state", "task_ids"}``; pass those
        task IDs to ``harf_transcription_status`` to poll for completion.

        Args:
            media_urls: HTTP(S) URLs of the audio/video files to transcribe.
            wait: Block until done (true) or return task IDs to poll (false).
            instance: Name of the configured Harf instance (omit for default).

        Returns:
            If ``wait`` is true: a list of
            ``{media_url, duration, segments:[{start,end,text}], stats:{words,known_words}}``.
            If ``wait`` is false: ``{state, task_ids}``.
        """

        urls = validate_urls(media_urls, field="media_urls")
        payload = {"media_urls": urls, "wait": wait}
        return await run_with_client(
            instance, lambda client: client.post_json(_ENDPOINT, payload)
        )

    @register(mcp)
    async def harf_transcribe_upload(
        file_path: str,
        instance: str | None = None,
    ) -> Any:
        """Transcribe a local audio/video file by uploading it to Harf (حرف).

        Reads a file from the server's local filesystem and uploads it to
        Harf's transcription endpoint via multipart/form-data (field ``media``).
        Use this when the audio is not reachable by URL. Uncertain words are
        wrapped in square brackets.

        Args:
            file_path: Absolute path to a local audio/video file (e.g. WAV).
            instance: Name of the configured Harf instance (omit for default).

        Returns:
            A list of
            ``{media_url, duration, segments:[{start,end,text}], stats:{words,known_words}}``.
        """

        if not file_path or not os.path.isfile(file_path):
            raise ValidationError(f"file_path is not a readable file: {file_path!r}")
        filename = os.path.basename(file_path)

        async def _call(client: RoshanClient) -> Any:
            with open(file_path, "rb") as fh:
                files = {"media": (filename, fh.read())}
            return await client.post_multipart(_ENDPOINT, files=files)

        return await run_with_client(instance, _call)

    @register(mcp)
    async def harf_transcription_status(
        task_ids: list[str],
        instance: str | None = None,
    ) -> Any:
        """Poll the status of asynchronous Harf (حرف) transcription tasks.

        Use the ``task_ids`` returned by ``harf_transcribe`` with ``wait=false``
        to check whether transcription has finished. The state is one of
        ``PENDING``, ``FAILURE``, ``TIMEOUT`` (and similar). When complete, the
        endpoint returns the transcription result.

        Args:
            task_ids: Task IDs returned by an async ``harf_transcribe`` call.
            instance: Name of the configured Harf instance (omit for default).

        Returns:
            A status payload such as ``{"state": "PENDING"}`` while running, or
            the transcription result once finished.
        """

        if not isinstance(task_ids, list) or not task_ids:
            raise ValidationError("task_ids must be a non-empty list of task IDs.")
        if not all(isinstance(t, str) and t.strip() for t in task_ids):
            raise ValidationError("task_ids must all be non-empty strings.")
        payload = {"tasks_ids": task_ids, "wait": False}
        return await run_with_client(
            instance, lambda client: client.post_json(_ENDPOINT, payload)
        )

    globals()["harf_transcribe"] = harf_transcribe
    globals()["harf_transcribe_upload"] = harf_transcribe_upload
    globals()["harf_transcription_status"] = harf_transcription_status
