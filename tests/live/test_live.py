"""Optional live integration tests against a real Harf deployment.

These are skipped by default and only run when real credentials are provided in
the environment. They make real network calls and may incur usage.

To run::

    export ROSHAN_HARF_BASE_URL=https://harf.roshan-ai.ir
    export ROSHAN_HARF_TOKEN=...
    export ROSHAN_HARF_LIVE=1
    pytest tests/live -q
"""

from __future__ import annotations

import os

import pytest

LIVE = os.environ.get("ROSHAN_HARF_LIVE") == "1"

pytestmark = pytest.mark.skipif(
    not LIVE, reason="set ROSHAN_HARF_LIVE=1 and real credentials to run"
)


@pytest.mark.asyncio
async def test_live_healthcheck() -> None:
    from roshan_harf_mcp.tools.common import healthcheck

    result = await healthcheck()
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_live_transcribe() -> None:
    media = os.environ.get("ROSHAN_HARF_LIVE_MEDIA_URL")
    if not media:
        pytest.skip("set ROSHAN_HARF_LIVE_MEDIA_URL to a Persian audio URL")
    from roshan_harf_mcp.tools.transcription import harf_transcribe

    result = await harf_transcribe(media_urls=[media], wait=True)
    assert isinstance(result, (list, dict))
