"""Tests for the catalog / docs meta tool."""

from __future__ import annotations

import pytest

from roshan_harf_mcp import catalog
from roshan_harf_mcp.catalog import DOCS_BASE_URL, SERVICE, TOOLS, tool_by_name
from roshan_harf_mcp.tools.docs import roshan_harf_docs


def test_service_metadata() -> None:
    assert SERVICE["name"] == "Harf"
    assert SERVICE["persian_name"] == "حرف"
    assert SERVICE["docs"] == DOCS_BASE_URL


def test_catalog_tool_names_cover_expected() -> None:
    names = {t["name"] for t in TOOLS}
    expected = {
        "harf_transcribe",
        "harf_transcribe_upload",
        "harf_transcription_status",
        "harf_tts",
        "harf_download_original",
        "harf_align",
        "harf_live_transcribe",
        "harf_live_info",
        "harf_speaker_verification",
        "harf_speaker_identification",
        "harf_speaker_diarization",
        "harf_speaker_indexing",
        "healthcheck",
        "list_instances",
        "roshan_harf_docs",
    }
    assert expected <= names


def test_tool_by_name() -> None:
    entry = tool_by_name("harf_transcribe")
    assert entry is not None
    assert entry["endpoint"] == "/api/transcribe_files/"
    assert tool_by_name("nope") is None


def test_every_catalog_tool_has_summary() -> None:
    for tool in TOOLS:
        assert tool["summary"].strip(), f"{tool['name']} has empty summary"


@pytest.mark.asyncio
async def test_docs_overview() -> None:
    result = await roshan_harf_docs()
    assert result["service"]["name"] == "Harf"
    assert result["documentation"] == DOCS_BASE_URL
    assert "docs.roshan-ai.ir" in result["documentation"]
    assert len(result["tools"]) == len(catalog.TOOLS)


@pytest.mark.asyncio
async def test_docs_by_topic() -> None:
    result = await roshan_harf_docs("harf_align")
    assert result["tool"]["name"] == "harf_align"
    assert result["documentation"] == DOCS_BASE_URL


@pytest.mark.asyncio
async def test_docs_unknown_topic() -> None:
    result = await roshan_harf_docs("zzz-nope")
    assert "error" in result
    assert result["documentation"] == DOCS_BASE_URL
