from __future__ import annotations

import re
from urllib.parse import urlparse

MAX_URLS = 50

_AUTH_PATTERN = re.compile(r"(?i)((?:bearer|token)\s+)([A-Za-z0-9\-_.=]+)")
_PASSWORD_PATTERN = re.compile(
    r"(?i)(['\"]?password['\"]?\s*[:=]\s*['\"]?)([^'\"\s,}]+)"
)


class ValidationError(ValueError):
    """Raised when a tool input fails validation."""


def validate_url(url: str, *, field: str = "url") -> str:
    """Validate and normalize a single http(s) URL.

    Args:
        url: The URL to validate.
        field: Name of the field for error messages.

    Returns:
        The stripped URL.

    Raises:
        ValidationError: If the URL is empty or not http/https.
    """

    if not isinstance(url, str) or not url.strip():
        raise ValidationError(f"{field} must be a non-empty string.")
    cleaned = url.strip()
    parsed = urlparse(cleaned)
    if parsed.scheme not in ("http", "https"):
        raise ValidationError(
            f"{field} must be an http(s) URL, got '{cleaned}'."
        )
    if not parsed.netloc:
        raise ValidationError(f"{field} is missing a host, got '{cleaned}'.")
    return cleaned


def validate_urls(
    urls: list[str], *, field: str = "media_urls", max_items: int = MAX_URLS
) -> list[str]:
    """Validate a list of http(s) URLs and clamp the list size.

    Args:
        urls: URLs to validate.
        field: Name of the field for error messages.
        max_items: Maximum number of URLs permitted.

    Returns:
        The validated list of URLs.

    Raises:
        ValidationError: If the list is empty, not a list, exceeds ``max_items``,
            or contains an invalid URL.
    """

    if not isinstance(urls, list) or not urls:
        raise ValidationError(f"{field} must be a non-empty list of URLs.")
    if len(urls) > max_items:
        raise ValidationError(
            f"{field} accepts at most {max_items} URLs, got {len(urls)}."
        )
    return [validate_url(u, field=field) for u in urls]


def validate_named_urls(
    mapping: dict[str, list[str]],
    *,
    field: str = "target_urls",
    max_items: int = MAX_URLS,
) -> dict[str, list[str]]:
    """Validate a ``{speaker_name: [url, ...]}`` mapping.

    Used by speaker identification and indexing where references are grouped
    per named speaker. The total number of URLs across all speakers is clamped
    to ``max_items``.

    Raises:
        ValidationError: If the mapping is empty/invalid or any URL is invalid.
    """

    if not isinstance(mapping, dict) or not mapping:
        raise ValidationError(
            f"{field} must be a non-empty mapping of speaker name to a list of URLs."
        )
    total = sum(len(v) if isinstance(v, list) else 0 for v in mapping.values())
    if total > max_items:
        raise ValidationError(
            f"{field} accepts at most {max_items} URLs in total, got {total}."
        )
    result: dict[str, list[str]] = {}
    for name, value in mapping.items():
        if not isinstance(name, str) or not name.strip():
            raise ValidationError(f"{field} contains an empty speaker name.")
        if not isinstance(value, list) or not value:
            raise ValidationError(
                f"{field}['{name}'] must be a non-empty list of URLs."
            )
        result[name] = [validate_url(u, field=f"{field}['{name}']") for u in value]
    return result


def redact_secrets(text: str) -> str:
    """Redact ``Bearer``/``Token`` credentials and passwords in ``text``.

    Defends against accidentally surfacing credentials inside error strings or
    logs (e.g. a leaked ``Authorization`` header or a login body).
    """

    if not text:
        return text
    redacted = _AUTH_PATTERN.sub(r"\1<redacted>", text)
    return _PASSWORD_PATTERN.sub(r"\1<redacted>", redacted)


def redact_token(text: str) -> str:
    """Backward-compatible alias for :func:`redact_secrets`."""

    return redact_secrets(text)
