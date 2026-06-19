"""Shared pytest fixtures for roshan-harf-mcp tests.

Tests run fully offline. HTTP traffic to Harf is mocked with ``respx``; no real
credentials or network access are required.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest

BASE_URL = "http://test.local"
TOKEN = "TESTTOKEN"


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Provide a clean, deterministic environment for each test.

    Strips any ``ROSHAN_HARF*`` env vars the host may have set, configures a
    single ``default`` instance pointing at the mocked test host, and clears the
    cached settings before and after the test.

    When ``ROSHAN_HARF_LIVE=1`` the environment is left untouched so the opt-in
    live integration tests can use the real credentials provided by the caller.
    """
    if os.environ.get("ROSHAN_HARF_LIVE") == "1":
        from roshan_harf_mcp import config

        config.get_settings.cache_clear()
        yield
        config.get_settings.cache_clear()
        return

    for key in list(os.environ):
        if key.startswith("ROSHAN_HARF"):
            monkeypatch.delenv(key, raising=False)

    monkeypatch.setenv("ROSHAN_HARF_BASE_URL", BASE_URL)
    monkeypatch.setenv("ROSHAN_HARF_TOKEN", TOKEN)

    from roshan_harf_mcp import config

    config.get_settings.cache_clear()
    yield
    config.get_settings.cache_clear()


@pytest.fixture
def respx_router() -> Iterator[object]:
    """A respx router scoped to the test host."""
    import respx

    with respx.mock(base_url=BASE_URL, assert_all_called=False) as router:
        yield router


@pytest.fixture
def server() -> object:
    """A freshly built FastMCP server instance."""
    from roshan_harf_mcp import build_server

    return build_server()
