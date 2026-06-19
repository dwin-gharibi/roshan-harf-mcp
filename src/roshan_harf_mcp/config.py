from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_BASE_URL = "https://harf.roshan-ai.ir"
DEFAULT_INSTANCE_NAME = "default"
_ENV_PREFIX = "ROSHAN_HARF__"
_INSTANCE_FIELDS: dict[str, str] = {
    "BASE_URL": "base_url",
    "TOKEN": "token",
    "USERNAME": "username",
    "PASSWORD": "password",
    "VERIFY_SSL": "verify_ssl",
    "TIMEOUT": "timeout",
}


class InstanceConfig(BaseModel):
    """Connection settings for a single Harf deployment.

    Authentication is via Keycloak SSO: supply ``username`` + ``password`` and
    the client logs in at ``POST /auth/glogin/`` to obtain a Bearer access
    token (cached, refreshed on 401). Alternatively, supply a pre-issued
    ``token`` to skip login and send it as ``Authorization: Bearer <token>``.
    """

    base_url: str = Field(
        default=DEFAULT_BASE_URL,
        description="Base URL of the Harf deployment, e.g. https://harf.roshan-ai.ir",
    )
    token: str | None = Field(
        default=None,
        description=(
            "Pre-issued access token sent as 'Authorization: Bearer <token>'. "
            "Optional; if omitted, username/password are used to log in."
        ),
    )
    username: str | None = Field(
        default=None,
        description="SSO username for POST /auth/glogin/ (Keycloak).",
    )
    password: str | None = Field(
        default=None,
        description="SSO password for POST /auth/glogin/ (Keycloak).",
    )
    verify_ssl: bool = Field(
        default=True,
        description="Whether to verify TLS certificates for this instance.",
    )
    timeout: float = Field(
        default=60.0,
        description="Per-request timeout in seconds.",
    )


def _coerce_bool(value: str) -> bool:
    """Coerce a string env value to a bool."""

    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_instances_from_env(environ: dict[str, str]) -> dict[str, InstanceConfig]:
    """Build named instances from ``ROSHAN_HARF__INSTANCES__<NAME>__<FIELD>``.

    Parsed deterministically from ``environ`` (independent of pydantic's
    dict-from-env handling, which is order-sensitive when sibling scalar env
    vars share the prefix).
    """

    prefix = f"{_ENV_PREFIX}INSTANCES__"
    raw: dict[str, dict[str, Any]] = {}
    for key, value in environ.items():
        upper = key.upper()
        if not upper.startswith(prefix):
            continue
        remainder = upper[len(prefix):]
        name, _, field_token = remainder.partition("__")
        if not name or field_token not in _INSTANCE_FIELDS:
            continue
        attr = _INSTANCE_FIELDS[field_token]
        coerced: Any = value
        if attr == "verify_ssl":
            coerced = _coerce_bool(value)
        elif attr == "timeout":
            coerced = float(value)
        raw.setdefault(name.lower(), {})[attr] = coerced

    return {name: InstanceConfig(**fields) for name, fields in raw.items()}


class Settings(BaseSettings):
    """Top-level settings for the server.

    ``instances`` are parsed explicitly from the environment (see
    :func:`_parse_instances_from_env`) rather than by pydantic-settings, so the
    result is deterministic even when the shorthand ``ROSHAN_HARF_BASE_URL``
    env var is also present.
    """

    model_config = SettingsConfigDict(
        env_prefix=_ENV_PREFIX,
        env_nested_delimiter="__",
        extra="ignore",
    )

    instances: dict[str, InstanceConfig] = Field(default_factory=dict)
    default_instance: str = DEFAULT_INSTANCE_NAME
    log_level: str = "INFO"

    def _apply_shorthand(self) -> Settings:
        """Load instances from env and synthesize a ``default`` if needed.

        Instance precedence (highest first):

        1. Nested ``ROSHAN_HARF__INSTANCES__<NAME>__...`` env vars.
        2. The shorthand ``ROSHAN_HARF_BASE_URL`` / ``ROSHAN_HARF_TOKEN`` /
           ``ROSHAN_HARF_USERNAME`` / ``ROSHAN_HARF_PASSWORD`` set, synthesized
           as the ``default`` instance.
        3. A bare ``default`` instance pointing at the public Harf host, so the
           server can always start and answer docs/health queries.
        """

        parsed = _parse_instances_from_env(dict(os.environ))
        if parsed:
            self.instances = {**self.instances, **parsed}

        base_url = os.environ.get("ROSHAN_HARF_BASE_URL")
        token = os.environ.get("ROSHAN_HARF_TOKEN")
        username = os.environ.get("ROSHAN_HARF_USERNAME")
        password = os.environ.get("ROSHAN_HARF_PASSWORD")
        if (base_url or token or username or password) and (
            DEFAULT_INSTANCE_NAME not in self.instances
        ):
            self.instances[DEFAULT_INSTANCE_NAME] = InstanceConfig(
                base_url=base_url or DEFAULT_BASE_URL,
                token=token,
                username=username,
                password=password,
            )

        if not self.instances:
            self.instances[DEFAULT_INSTANCE_NAME] = InstanceConfig()

        return self

    def resolve(self, instance: str | None) -> InstanceConfig:
        """Return the :class:`InstanceConfig` for ``instance``.

        When ``instance`` is ``None`` the configured ``default_instance`` is
        used. A clear error listing the known instances is raised if the name
        is unknown.
        """

        name = instance or self.default_instance
        try:
            return self.instances[name]
        except KeyError:
            known = ", ".join(sorted(self.instances)) or "(none configured)"
            raise KeyError(
                f"Unknown Harf instance '{name}'. Known instances: {known}. "
                f"Configure it via ROSHAN_HARF__INSTANCES__{name.upper()}__BASE_URL "
                f"(and ...__USERNAME/...__PASSWORD or ...__TOKEN), or omit "
                f"'instance' to use the default ('{self.default_instance}')."
            ) from None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide :class:`Settings` (cached)."""

    return Settings()._apply_shorthand()
