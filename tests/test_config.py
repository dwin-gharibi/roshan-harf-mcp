"""Tests for configuration loading and instance resolution."""

from __future__ import annotations

import pytest

from roshan_harf_mcp.config import (
    DEFAULT_BASE_URL,
    DEFAULT_INSTANCE_NAME,
    InstanceConfig,
    Settings,
    get_settings,
)


def _settings() -> Settings:
    """Build fresh settings with the env applied (shorthand etc.)."""
    return Settings()._apply_shorthand()


def test_shorthand_synthesizes_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ROSHAN_HARF_BASE_URL", "https://harf.short.example.ir")
    monkeypatch.setenv("ROSHAN_HARF_TOKEN", "short-token")
    settings = _settings()
    assert settings.default_instance == DEFAULT_INSTANCE_NAME
    default = settings.instances["default"]
    assert default.base_url == "https://harf.short.example.ir"
    assert default.token == "short-token"


def test_no_env_yields_public_default(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ("ROSHAN_HARF_BASE_URL", "ROSHAN_HARF_TOKEN"):
        monkeypatch.delenv(key, raising=False)
    settings = _settings()
    assert "default" in settings.instances
    assert settings.instances["default"].base_url == DEFAULT_BASE_URL
    assert settings.instances["default"].token is None


def test_nested_env_multiple_instances(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "ROSHAN_HARF__INSTANCES__TEHRAN__BASE_URL", "https://harf.tehran.example.ir"
    )
    monkeypatch.setenv("ROSHAN_HARF__INSTANCES__TEHRAN__TOKEN", "tok-tehran")
    monkeypatch.setenv(
        "ROSHAN_HARF__INSTANCES__SHIRAZ__BASE_URL", "https://harf.shiraz.example.ir"
    )
    monkeypatch.setenv("ROSHAN_HARF__INSTANCES__SHIRAZ__TOKEN", "tok-shiraz")
    monkeypatch.setenv("ROSHAN_HARF__DEFAULT_INSTANCE", "tehran")
    settings = _settings()
    assert settings.default_instance == "tehran"
    assert settings.resolve("tehran").base_url == "https://harf.tehran.example.ir"
    assert settings.resolve("tehran").token == "tok-tehran"
    assert settings.resolve("shiraz").token == "tok-shiraz"


def test_nested_verify_ssl_and_timeout_coercion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "ROSHAN_HARF__INSTANCES__ONPREM__BASE_URL", "https://harf.internal.local"
    )
    monkeypatch.setenv("ROSHAN_HARF__INSTANCES__ONPREM__VERIFY_SSL", "false")
    monkeypatch.setenv("ROSHAN_HARF__INSTANCES__ONPREM__TIMEOUT", "12.5")
    settings = _settings()
    onprem = settings.resolve("onprem")
    assert onprem.verify_ssl is False
    assert onprem.timeout == 12.5


def test_nested_takes_precedence_over_shorthand(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "ROSHAN_HARF__INSTANCES__DEFAULT__TOKEN", "nested-token"
    )
    monkeypatch.setenv("ROSHAN_HARF_TOKEN", "short-token")
    settings = _settings()
    assert settings.instances["default"].token == "nested-token"


def test_resolve_none_uses_default_instance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ROSHAN_HARF_BASE_URL", "https://harf.default.example.ir")
    settings = _settings()
    assert settings.resolve(None).base_url == "https://harf.default.example.ir"


def test_resolve_unknown_instance_raises_keyerror(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings()
    with pytest.raises(KeyError) as exc:
        settings.resolve("does-not-exist")
    message = str(exc.value)
    assert "Unknown Harf instance" in message
    assert "does-not-exist" in message
    assert "default" in message


def test_instance_config_defaults() -> None:
    cfg = InstanceConfig()
    assert cfg.base_url == DEFAULT_BASE_URL
    assert cfg.token is None
    assert cfg.username is None
    assert cfg.password is None
    assert cfg.verify_ssl is True
    assert cfg.timeout == 60.0


def test_shorthand_username_password(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ROSHAN_HARF_TOKEN", raising=False)
    monkeypatch.setenv("ROSHAN_HARF_BASE_URL", "https://harf.creds.example.ir")
    monkeypatch.setenv("ROSHAN_HARF_USERNAME", "svc-account")
    monkeypatch.setenv("ROSHAN_HARF_PASSWORD", "secret-pw")
    settings = _settings()
    default = settings.instances["default"]
    assert default.username == "svc-account"
    assert default.password == "secret-pw"
    assert default.token is None


def test_nested_username_password(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "ROSHAN_HARF__INSTANCES__TEHRAN__BASE_URL", "https://harf.tehran.example.ir"
    )
    monkeypatch.setenv("ROSHAN_HARF__INSTANCES__TEHRAN__USERNAME", "u-tehran")
    monkeypatch.setenv("ROSHAN_HARF__INSTANCES__TEHRAN__PASSWORD", "p-tehran")
    settings = _settings()
    tehran = settings.resolve("tehran")
    assert tehran.username == "u-tehran"
    assert tehran.password == "p-tehran"


def test_get_settings_cached() -> None:
    get_settings.cache_clear()
    a = get_settings()
    b = get_settings()
    assert a is b
