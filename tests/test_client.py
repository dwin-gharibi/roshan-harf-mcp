from __future__ import annotations

import json

import httpx
import pytest
import respx

from roshan_harf_mcp.client import LOGIN_PATH, RoshanClient, RoshanError
from roshan_harf_mcp.config import InstanceConfig

from .conftest import BASE_URL, TOKEN


def _static_client() -> RoshanClient:
    """Client with a pre-issued static Bearer token (no login needed)."""
    return RoshanClient.from_config(InstanceConfig(base_url=BASE_URL, token=TOKEN))


def _login_client() -> RoshanClient:
    """Client that must log in via /auth/glogin/ to get a token."""
    return RoshanClient.from_config(
        InstanceConfig(base_url=BASE_URL, username="svc", password="pw")
    )


@pytest.mark.asyncio
@respx.mock
async def test_static_token_sends_bearer_header() -> None:
    login = respx.post(f"{BASE_URL}{LOGIN_PATH}")
    route = respx.get(f"{BASE_URL}/api/healthcheck/").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    client = _static_client()
    try:
        result = await client.get("/api/healthcheck/")
    finally:
        await client.aclose()
    assert result == {"status": "ok"}
    assert route.calls[0].request.headers["authorization"] == f"Bearer {TOKEN}"
    assert not login.called


@pytest.mark.asyncio
@respx.mock
async def test_glogin_then_bearer_on_request() -> None:
    login = respx.post(f"{BASE_URL}{LOGIN_PATH}").mock(
        return_value=httpx.Response(
            200,
            json={
                "access_token": "fresh-access",
                "refresh_token": "r",
                "token_type": "Bearer",
                "expires_in": 300,
            },
        )
    )
    hc = respx.get(f"{BASE_URL}/api/healthcheck/").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    client = _login_client()
    try:
        result = await client.get("/api/healthcheck/")
    finally:
        await client.aclose()
    assert result == {"status": "ok"}
    assert login.call_count == 1
    body = json.loads(login.calls[0].request.content)
    assert body == {"username": "svc", "password": "pw"}
    assert hc.calls[0].request.headers["authorization"] == "Bearer fresh-access"


@pytest.mark.asyncio
@respx.mock
async def test_token_is_cached_across_calls() -> None:
    login = respx.post(f"{BASE_URL}{LOGIN_PATH}").mock(
        return_value=httpx.Response(200, json={"access_token": "cached-tok"})
    )
    respx.get(f"{BASE_URL}/api/healthcheck/").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    client = _login_client()
    try:
        await client.get("/api/healthcheck/")
        await client.get("/api/healthcheck/")
    finally:
        await client.aclose()
    assert login.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_relogin_on_401() -> None:
    login = respx.post(f"{BASE_URL}{LOGIN_PATH}").mock(
        side_effect=[
            httpx.Response(200, json={"access_token": "stale"}),
            httpx.Response(200, json={"access_token": "renewed"}),
        ]
    )
    hc = respx.get(f"{BASE_URL}/api/healthcheck/").mock(
        side_effect=[
            httpx.Response(401, json={"detail": "expired"}),
            httpx.Response(200, json={"status": "ok"}),
        ]
    )
    client = _login_client()
    try:
        result = await client.get("/api/healthcheck/")
    finally:
        await client.aclose()
    assert result == {"status": "ok"}
    assert login.call_count == 2
    assert hc.call_count == 2
    assert hc.calls[1].request.headers["authorization"] == "Bearer renewed"


@pytest.mark.asyncio
@respx.mock
async def test_static_token_does_not_relogin_on_401() -> None:
    login = respx.post(f"{BASE_URL}{LOGIN_PATH}")
    respx.get(f"{BASE_URL}/api/healthcheck/").mock(
        return_value=httpx.Response(401, json={"detail": "nope"})
    )
    client = _static_client()
    try:
        with pytest.raises(RoshanError) as exc:
            await client.get("/api/healthcheck/")
    finally:
        await client.aclose()
    assert exc.value.status_code == 401
    assert not login.called


@pytest.mark.asyncio
@respx.mock
async def test_login_failure_surfaces_clean_error() -> None:
    respx.post(f"{BASE_URL}{LOGIN_PATH}").mock(
        return_value=httpx.Response(403, json={"detail": "bad creds"})
    )
    client = _login_client()
    try:
        with pytest.raises(RoshanError) as exc:
            await client.get("/api/healthcheck/")
    finally:
        await client.aclose()
    assert "login" in str(exc.value).lower()
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_missing_credentials_raise() -> None:
    client = RoshanClient.from_config(InstanceConfig(base_url=BASE_URL))
    try:
        with pytest.raises(RoshanError) as exc:
            await client._login()
    finally:
        await client.aclose()
    assert "username/password" in str(exc.value)


@pytest.mark.asyncio
@respx.mock
async def test_post_json_returns_parsed_body() -> None:
    route = respx.post(f"{BASE_URL}/api/alignment/").mock(
        return_value=httpx.Response(200, json={"media_url": "x", "segments": []})
    )
    client = _static_client()
    try:
        result = await client.post_json("/api/alignment/", {"media_url": "x"})
    finally:
        await client.aclose()
    assert result["media_url"] == "x"
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_post_multipart_uploads_file() -> None:
    route = respx.post(f"{BASE_URL}/api/transcribe_files/").mock(
        return_value=httpx.Response(200, json=[{"media_url": "u"}])
    )
    client = _static_client()
    try:
        result = await client.post_multipart(
            "/api/transcribe_files/", files={"media": ("a.wav", b"RIFFdata")}
        )
    finally:
        await client.aclose()
    assert result == [{"media_url": "u"}]
    sent = route.calls[0].request
    assert b"RIFFdata" in sent.content
    assert sent.headers["authorization"] == f"Bearer {TOKEN}"


@pytest.mark.asyncio
@respx.mock
async def test_no_credentials_omits_auth_header() -> None:
    route = respx.get(f"{BASE_URL}/api/healthcheck/").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    client = RoshanClient.from_config(InstanceConfig(base_url=BASE_URL))
    try:
        await client.get("/api/healthcheck/")
    finally:
        await client.aclose()
    assert "authorization" not in route.calls[0].request.headers


@pytest.mark.asyncio
@respx.mock
async def test_http_error_includes_status_and_payload() -> None:
    respx.get(f"{BASE_URL}/api/healthcheck/").mock(
        return_value=httpx.Response(503, json={"detail": "down"})
    )
    client = _static_client()
    try:
        with pytest.raises(RoshanError) as exc:
            await client.get("/api/healthcheck/")
    finally:
        await client.aclose()
    assert exc.value.status_code == 503
    assert exc.value.payload == {"detail": "down"}


@pytest.mark.asyncio
@respx.mock
async def test_network_error_is_wrapped() -> None:
    respx.get(f"{BASE_URL}/api/healthcheck/").mock(
        side_effect=httpx.ConnectError("boom")
    )
    client = _static_client()
    try:
        with pytest.raises(RoshanError) as exc:
            await client.get("/api/healthcheck/")
    finally:
        await client.aclose()
    assert "HTTP request to Harf failed" in str(exc.value)


def test_roshan_error_redacts_bearer_token() -> None:
    err = RoshanError("auth failed with Bearer super-secret-value")
    assert "super-secret-value" not in str(err)
    assert "<redacted>" in str(err)


def test_roshan_error_redacts_password() -> None:
    err = RoshanError('login body {"password": "hunter2"} rejected')
    assert "hunter2" not in str(err)
    assert "<redacted>" in str(err)


@pytest.mark.asyncio
async def test_client_context_manager_closes() -> None:
    async with RoshanClient.from_config(
        InstanceConfig(base_url=BASE_URL, token=TOKEN)
    ) as client:
        assert client.base_url == BASE_URL
