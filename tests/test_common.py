"""Tests for guardrails and meta tools (healthcheck, list_instances)."""

from __future__ import annotations

import httpx
import pytest
import respx

from roshan_harf_mcp.guardrails import (
    MAX_URLS,
    ValidationError,
    redact_secrets,
    redact_token,
    validate_named_urls,
    validate_url,
    validate_urls,
)
from roshan_harf_mcp.tools.common import healthcheck, list_instances

from .conftest import BASE_URL, TOKEN


def test_validate_url_ok() -> None:
    assert validate_url("https://x.test/a") == "https://x.test/a"
    assert validate_url("  http://y.test  ") == "http://y.test"


def test_validate_url_rejects_non_http() -> None:
    with pytest.raises(ValidationError):
        validate_url("ftp://x")
    with pytest.raises(ValidationError):
        validate_url("")
    with pytest.raises(ValidationError):
        validate_url("https://")


def test_validate_urls_empty_and_clamp() -> None:
    with pytest.raises(ValidationError):
        validate_urls([])
    with pytest.raises(ValidationError):
        validate_urls(["https://x.test"] * (MAX_URLS + 1))
    assert validate_urls(["https://x.test"]) == ["https://x.test"]


def test_validate_named_urls() -> None:
    out = validate_named_urls({"Ali": ["https://x.test/1"]})
    assert out == {"Ali": ["https://x.test/1"]}
    with pytest.raises(ValidationError):
        validate_named_urls({})
    with pytest.raises(ValidationError):
        validate_named_urls({"Ali": []})
    with pytest.raises(ValidationError):
        validate_named_urls({"": ["https://x.test"]})
    with pytest.raises(ValidationError):
        validate_named_urls({"Ali": ["ftp://x"]})


def test_redact_token() -> None:
    assert redact_token("Authorization: Token abc123") == "Authorization: Token <redacted>"
    assert redact_token("") == ""


def test_redact_secrets_bearer_and_password() -> None:
    assert (
        redact_secrets("Authorization: Bearer abc123")
        == "Authorization: Bearer <redacted>"
    )
    assert "hunter2" not in redact_secrets('{"password": "hunter2"}')
    assert redact_secrets("") == ""


@pytest.mark.asyncio
async def test_list_instances_hides_tokens() -> None:
    result = await list_instances()
    assert result["default_instance"] == "default"
    names = [i["name"] for i in result["instances"]]
    assert "default" in names
    default = next(i for i in result["instances"] if i["name"] == "default")
    assert default["base_url"] == BASE_URL
    assert TOKEN not in repr(result)
    assert all("token" not in i for i in result["instances"])


@pytest.mark.asyncio
async def test_list_instances_multiple(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "ROSHAN_HARF__INSTANCES__SHIRAZ__BASE_URL", "https://harf.shiraz.example.ir"
    )
    monkeypatch.setenv("ROSHAN_HARF__INSTANCES__SHIRAZ__TOKEN", "secret-shiraz")
    from roshan_harf_mcp import config

    config.get_settings.cache_clear()
    result = await list_instances()
    names = {i["name"] for i in result["instances"]}
    assert {"default", "shiraz"} <= names
    assert "secret-shiraz" not in repr(result)


@pytest.mark.asyncio
@respx.mock
async def test_healthcheck_ok() -> None:
    respx.get(f"{BASE_URL}/api/healthcheck/").mock(
        return_value=httpx.Response(
            200, json={"status": "ok", "message": "Server is up and ready"}
        )
    )
    result = await healthcheck()
    assert result["status"] == "ok"
    assert result["message"] == "Server is up and ready"


@pytest.mark.asyncio
@respx.mock
async def test_healthcheck_error_returns_clean_dict() -> None:
    respx.get(f"{BASE_URL}/api/healthcheck/").mock(
        return_value=httpx.Response(503, json={"detail": "down"})
    )
    result = await healthcheck()
    assert "error" in result
    assert TOKEN not in repr(result)


@pytest.mark.asyncio
async def test_healthcheck_unknown_instance_clean_error() -> None:
    result = await healthcheck(instance="nope")
    assert "error" in result
    assert "Unknown Harf instance" in result["error"]
