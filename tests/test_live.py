from __future__ import annotations
import pytest
from roshan_harf_mcp.tools.live import _http_to_ws, harf_live_info, harf_live_transcribe
from .conftest import BASE_URL


def test_http_to_ws_scheme_conversion() -> None:
    assert _http_to_ws("https://harf.example.ir").startswith("wss://")
    assert _http_to_ws("http://harf.example.ir").startswith("ws://")
    assert _http_to_ws("http://harf.example.ir").endswith(
        "/api/ws_api/transcribe_files/wav/sync/"
    )


@pytest.mark.asyncio
async def test_live_info_describes_protocol() -> None:
    result = await harf_live_info()
    assert result["endpoint"] == "/api/ws_api/transcribe_files/wav/sync/"
    assert result["websocket_url"].startswith("ws://test.local")
    assert any("finalize" in step for step in result["protocol"])
    assert "Bearer" in result["auth"]
    assert all("Token" not in step for step in result["protocol"])


@pytest.mark.asyncio
async def test_live_transcribe_missing_file() -> None:
    result = await harf_live_transcribe(file_path="/no/such/file.wav")
    assert "error" in result
    assert "not a readable file" in result["error"]


@pytest.mark.asyncio
async def test_live_transcribe_connection_failure_is_clean(tmp_path) -> None:
    wav = tmp_path / "a.wav"
    wav.write_bytes(b"RIFF....WAVEdata")
    result = await harf_live_transcribe(file_path=str(wav))
    assert "error" in result
    assert BASE_URL.split("//", 1)[1] in result.get("websocket_url", "") or (
        "websockets" in result["error"]
    )
