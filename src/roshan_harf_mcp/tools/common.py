from __future__ import annotations
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..config import get_settings
from ._base import register
from ._exec import run_with_client


def register_tools(mcp: FastMCP) -> None:
    """Register the common meta tools on ``mcp``."""

    @register(mcp)
    async def healthcheck(instance: str | None = None) -> dict[str, Any]:
        """Check that a Harf (حرف) instance is up and ready.

        Calls Harf's ``GET /api/healthcheck/`` endpoint. Use this to confirm
        connectivity and credentials for a given self-hosted deployment before
        running heavier speech tasks.

        Args:
            instance: Name of the configured Harf instance to query. Omit to
                use the default instance.

        Returns:
            The service status payload, e.g.
            ``{"status": "ok", "message": "Server is up and ready"}``.
        """

        return await run_with_client(
            instance, lambda client: client.get("/api/healthcheck/")
        )

    @register(mcp)
    async def list_instances() -> dict[str, Any]:
        """List the configured Harf (حرف) instances available to this server.

        Returns only instance names and their base URLs together with the name
        of the default instance. Tokens and other secrets are never returned.
        Use the returned names as the ``instance`` argument of other tools to
        route a request to a specific self-hosted Harf deployment.

        Returns:
            ``{"default_instance": str, "instances": [{"name", "base_url"}, ...]}``
        """

        settings = get_settings()
        instances = [
            {"name": name, "base_url": cfg.base_url}
            for name, cfg in sorted(settings.instances.items())
        ]
        return {
            "default_instance": settings.default_instance,
            "instances": instances,
        }

    globals()["healthcheck"] = healthcheck
    globals()["list_instances"] = list_instances
