from __future__ import annotations

from typing import Any

import httpx

from .config import InstanceConfig
from .guardrails import redact_secrets

LOGIN_PATH = "/auth/glogin/"


class RoshanError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        payload: Any | None = None,
    ) -> None:
        super().__init__(redact_secrets(message))
        self.status_code = status_code
        self.payload = payload


class RoshanClient:
    def __init__(
        self,
        base_url: str,
        token: str | None = None,
        *,
        username: str | None = None,
        password: str | None = None,
        verify_ssl: bool = True,
        timeout: float = 60.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self._access_token: str | None = token
        self._static_token = token is not None
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            verify=verify_ssl,
            timeout=timeout,
        )

    @classmethod
    def from_config(cls, config: InstanceConfig) -> RoshanClient:
        """Build a client from an :class:`InstanceConfig`."""

        return cls(
            base_url=config.base_url,
            token=config.token,
            username=config.username,
            password=config.password,
            verify_ssl=config.verify_ssl,
            timeout=config.timeout,
        )

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        headers: dict[str, str] = {"Accept": "application/json"}
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        if extra:
            headers.update(extra)
        return headers

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    async def aclose(self) -> None:
        """Close the underlying HTTP client if we own it."""

        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> RoshanClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()

    async def _login(self) -> str:
        """Log in via ``POST /auth/glogin/`` and cache the access token.

        Returns:
            The freshly obtained Bearer access token.

        Raises:
            RoshanError: If credentials are missing or login fails.
        """

        if not self.username or not self.password:
            raise RoshanError(
                "Harf authentication requires either a static token or a "
                "username/password pair to log in via POST /auth/glogin/."
            )
        url = self._url(LOGIN_PATH)
        try:
            response = await self._client.post(
                url,
                json={"username": self.username, "password": self.password},
                headers={"Accept": "application/json"},
            )
        except httpx.HTTPError as exc:
            raise RoshanError(f"Harf login request failed: {exc}") from exc

        if not response.is_success:
            detail = _safe_detail(response)
            raise RoshanError(
                f"Harf login (POST {LOGIN_PATH}) returned HTTP "
                f"{response.status_code}: {detail}",
                status_code=response.status_code,
                payload=detail,
            )

        try:
            body = response.json()
        except ValueError as exc:
            raise RoshanError("Harf login returned a non-JSON response.") from exc

        token = body.get("access_token") if isinstance(body, dict) else None
        if not token:
            raise RoshanError(
                "Harf login response did not include an 'access_token'."
            )
        self._access_token = token
        return token

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> Any:
        if self._access_token is None and self.username and self.password:
            await self._login()

        response = await self._send(method, path, json=json, data=data, files=files)

        if (
            response.status_code == httpx.codes.UNAUTHORIZED
            and not self._static_token
            and self.username
            and self.password
        ):
            self._access_token = None
            await self._login()
            response = await self._send(
                method, path, json=json, data=data, files=files
            )

        return self._handle_response(response)

    async def _send(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> httpx.Response:
        url = self._url(path)
        try:
            return await self._client.request(
                method,
                url,
                json=json,
                data=data,
                files=files,
                headers=self._headers(),
            )
        except httpx.HTTPError as exc:
            raise RoshanError(f"HTTP request to Harf failed: {exc}") from exc

    @staticmethod
    def _handle_response(response: httpx.Response) -> Any:
        if response.is_success:
            if not response.content:
                return None
            try:
                return response.json()
            except ValueError:
                return {"raw": response.text}

        detail = _safe_detail(response)
        raise RoshanError(
            f"Harf API returned HTTP {response.status_code}: {detail}",
            status_code=response.status_code,
            payload=detail,
        )

    async def get(self, path: str) -> Any:
        """Issue a GET request and return parsed JSON."""

        return await self._request("GET", path)

    async def post_json(self, path: str, payload: dict[str, Any]) -> Any:
        """Issue a POST request with a JSON body and return parsed JSON."""

        return await self._request("POST", path, json=payload)

    async def post_multipart(
        self,
        path: str,
        *,
        files: dict[str, Any],
        data: dict[str, Any] | None = None,
    ) -> Any:
        """Issue a multipart/form-data POST (file upload) and return JSON."""

        return await self._request("POST", path, files=files, data=data)


def _safe_detail(response: httpx.Response) -> Any:
    """Return a JSON or text error detail without raising."""

    try:
        return response.json()
    except ValueError:
        return response.text or response.reason_phrase
