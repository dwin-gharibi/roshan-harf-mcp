"""Tests for server assembly and tool registration."""

from __future__ import annotations

import pytest

from roshan_harf_mcp import __version__, build_server

EXPECTED_TOOLS = {
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

NO_INSTANCE = {"roshan_harf_docs", "list_instances"}


def test_version() -> None:
    assert __version__ == "0.1.0"


def test_server_name() -> None:
    server = build_server()
    assert server.name == "roshan-harf-mcp"


@pytest.mark.asyncio
async def test_all_tools_registered() -> None:
    server = build_server()
    tools = await server.list_tools()
    names = {t.name for t in tools}
    assert names == EXPECTED_TOOLS
    assert len(tools) == len(EXPECTED_TOOLS)


@pytest.mark.asyncio
async def test_every_tool_has_description_and_instance() -> None:
    server = build_server()
    tools = await server.list_tools()
    for tool in tools:
        assert tool.description and tool.description.strip(), (
            f"{tool.name} missing description"
        )
        props = (tool.inputSchema or {}).get("properties", {})
        if tool.name in NO_INSTANCE:
            assert "instance" not in props, (
                f"{tool.name} should not expose 'instance'"
            )
        else:
            assert "instance" in props, f"{tool.name} missing 'instance' param"


@pytest.mark.asyncio
async def test_build_server_forwards_kwargs() -> None:
    server = build_server(host="0.0.0.0", port=9100)
    assert server.settings.host == "0.0.0.0"
    assert server.settings.port == 9100
