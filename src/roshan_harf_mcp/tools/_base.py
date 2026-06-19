from __future__ import annotations

import functools
import logging
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from mcp.server.fastmcp import FastMCP

from ..client import RoshanError
from ..guardrails import ValidationError, redact_secrets

logger = logging.getLogger("roshan_harf_mcp")

F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


def _format_error(exc: Exception) -> str:
    """Convert an exception into a clean, user-facing, secret-free string."""

    if isinstance(exc, ValidationError):
        return f"Invalid input: {exc}"
    if isinstance(exc, KeyError):
        return redact_secrets(str(exc).strip("'\""))
    if isinstance(exc, RoshanError):
        return f"Harf request failed: {exc}"
    return redact_secrets(f"Unexpected error: {exc}")


def wrap_errors(func: F) -> F:
    """Wrap an async tool so exceptions become clean text results."""

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
        except Exception as exc:
            message = _format_error(exc)
            logger.debug("Tool %s failed: %s", func.__name__, message)
            return {"error": message}

    return wrapper


def register(mcp: FastMCP) -> Callable[[F], F]:
    """Return a decorator that wraps a tool and registers it on ``mcp``.

    Usage::

        @register(mcp)
        async def my_tool(...): ...

    The wrapped coroutine has its exceptions converted to clean, token-free
    error dicts (via :func:`wrap_errors`) before being registered as an MCP
    tool.
    """

    def decorator(func: F) -> F:
        wrapped = wrap_errors(func)
        mcp.tool()(wrapped)
        return wrapped

    return decorator
