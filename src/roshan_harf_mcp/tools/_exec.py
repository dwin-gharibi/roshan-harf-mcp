from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from ..client import RoshanClient
from ..config import get_settings


async def run_with_client(
    instance: str | None,
    func: Callable[[RoshanClient], Awaitable[Any]],
) -> Any:
    """Resolve ``instance``, run ``func`` with a client, and clean up.

    Args:
        instance: Name of the configured Harf instance (``None`` = default).
        func: Async callable receiving a :class:`RoshanClient` and returning
            the (already parsed) API result.

    Returns:
        Whatever ``func`` returns.
    """

    settings = get_settings()
    config = settings.resolve(instance)
    client = RoshanClient.from_config(config)
    try:
        return await func(client)
    finally:
        await client.aclose()
