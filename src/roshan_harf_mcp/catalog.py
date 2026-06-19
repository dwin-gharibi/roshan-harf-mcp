from __future__ import annotations
from typing import TypedDict

DOCS_BASE_URL = "https://docs.roshan-ai.ir"
SERVICE_HOST = "https://harf.roshan-ai.ir"


class ToolDoc(TypedDict):
    """Metadata describing a single tool."""

    name: str
    endpoint: str
    method: str
    summary: str


SERVICE: dict[str, str] = {
    "name": "Harf",
    "persian_name": "حرف",
    "service": "speech",
    "vendor": "Roshan AI",
    "host": SERVICE_HOST,
    "docs": DOCS_BASE_URL,
    "summary": (
        "Harf (حرف) is Roshan's Persian speech service: audio/video "
        "transcription (ASR), forced text-to-audio alignment, real-time "
        "streaming transcription, and speaker tasks (verification, "
        "identification, diarization, and indexing)."
    ),
}


TOOLS: list[ToolDoc] = [
    {
        "name": "harf_transcribe",
        "endpoint": "/api/transcribe_files/",
        "method": "POST",
        "summary": (
            "Transcribe Persian audio/video by URL. Blocks when wait=true; "
            "with wait=false returns {state, task_ids} to poll later."
        ),
    },
    {
        "name": "harf_transcribe_upload",
        "endpoint": "/api/transcribe_files/",
        "method": "POST (multipart)",
        "summary": "Transcribe a local audio/video file uploaded via multipart.",
    },
    {
        "name": "harf_transcription_status",
        "endpoint": "/api/transcribe_files/",
        "method": "POST",
        "summary": (
            "Poll the state (PENDING/FAILURE/TIMEOUT/...) of async transcription "
            "tasks created with wait=false."
        ),
    },
    {
        "name": "harf_tts",
        "endpoint": "/api/tts/",
        "method": "POST",
        "summary": (
            "Synthesize Persian speech from text (voice=female|male); returns "
            "samplerate + waveform (+ optional WAV via save_path)."
        ),
    },
    {
        "name": "harf_download_original",
        "endpoint": "/api/download_original/",
        "method": "POST",
        "summary": (
            "Get a short-lived signed download link for an original media file "
            "(expires ~30s)."
        ),
    },
    {
        "name": "harf_align",
        "endpoint": "/api/alignment/",
        "method": "POST",
        "summary": (
            "Force-align a known transcript to its audio and return per-segment "
            "timestamps."
        ),
    },
    {
        "name": "harf_live_transcribe",
        "endpoint": "/api/ws_api/transcribe_files/wav/sync/",
        "method": "WebSocket",
        "summary": (
            "Stream a local WAV file over a WebSocket for real-time "
            "transcription segments."
        ),
    },
    {
        "name": "harf_live_info",
        "endpoint": "/api/ws_api/transcribe_files/wav/sync/",
        "method": "WebSocket",
        "summary": "Describe the live streaming protocol and how to use it.",
    },
    {
        "name": "harf_speaker_verification",
        "endpoint": "/api/speaker_tasks/verification/",
        "method": "POST",
        "summary": (
            "Verify whether a probe speaker matches reference audio "
            "(threshold 0.65)."
        ),
    },
    {
        "name": "harf_speaker_identification",
        "endpoint": "/api/speaker_tasks/identification/",
        "method": "POST",
        "summary": "Identify which known speaker a probe most resembles.",
    },
    {
        "name": "harf_speaker_diarization",
        "endpoint": "/api/speaker_tasks/diarization/",
        "method": "POST",
        "summary": "Segment audio by speaker ('who spoke when') with text per segment.",
    },
    {
        "name": "harf_speaker_indexing",
        "endpoint": "/api/speaker_tasks/indexing/",
        "method": "POST",
        "summary": (
            "Index a media file against known speakers, returning labelled, "
            "timestamped, transcribed segments."
        ),
    },
    {
        "name": "healthcheck",
        "endpoint": "/api/healthcheck/",
        "method": "GET",
        "summary": "Check that a Harf instance is up and ready.",
    },
    {
        "name": "list_instances",
        "endpoint": "(local)",
        "method": "-",
        "summary": "List configured Harf instances (names + base URLs only).",
    },
    {
        "name": "roshan_harf_docs",
        "endpoint": "(local)",
        "method": "-",
        "summary": "Return documentation about Harf and this server's tools.",
    },
]


def tool_by_name(name: str) -> ToolDoc | None:
    """Return the catalog entry for ``name`` or ``None``."""

    for tool in TOOLS:
        if tool["name"] == name:
            return tool
    return None
