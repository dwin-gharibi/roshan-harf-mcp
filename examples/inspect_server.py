#!/usr/bin/env python3
"""Print the roshan-harf-mcp catalog and registered tools.

Useful for exploring the server without any credentials or network access::

    python examples/inspect_server.py
"""

from __future__ import annotations

import asyncio
import json


async def _run() -> None:
    from roshan_harf_mcp import __version__, build_server
    from roshan_harf_mcp import catalog

    print("=" * 70)
    print(f"roshan-harf-mcp {__version__}")
    print("=" * 70)

    svc = catalog.SERVICE
    print(f"\nService: {svc['name']} ({svc['persian_name']}) — {svc['vendor']}")
    print(f"  host: {svc['host']}")
    print(f"  docs: {svc['docs']}")
    print(f"  {svc['summary']}")

    server = build_server()
    tools = await server.list_tools()
    print(f"\nRegistered tools ({len(tools)}):")
    for tool in sorted(tools, key=lambda t: t.name):
        props = list((tool.inputSchema or {}).get("properties", {}).keys())
        summary = (tool.description or "").strip().splitlines()[0]
        print(f"  - {tool.name}")
        print(f"      params: {props}")
        print(f"      {summary}")

    print("\nCatalog (JSON):")
    print(
        json.dumps(
            {"service": catalog.SERVICE, "tools": catalog.TOOLS},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(_run())
