#!/usr/bin/env python3
"""Offline smoke test for roshan-harf-mcp.

Builds the server, lists its tools, and asserts every tool has a non-empty
description and (except the two meta tools that don't route) an ``instance``
parameter in its input schema. Exits non-zero on any problem. Requires no
network and no credentials.
"""

from __future__ import annotations

import asyncio
import sys

EXPECTED_TOOLS = {
    "harf_transcribe",
    "harf_transcribe_upload",
    "harf_transcription_status",
    "harf_tts",
    "harf_download_original",
    "harf_align",
    "harf_live_transcribe",
    "harf_live_info",
    "harf_speaker_verification",
    "harf_speaker_identification",
    "harf_speaker_diarization",
    "harf_speaker_indexing",
    "healthcheck",
    "list_instances",
    "roshan_harf_docs",
}

NO_INSTANCE = {"roshan_harf_docs", "list_instances"}


async def _run() -> int:
    from roshan_harf_mcp import __version__, build_server

    problems: list[str] = []
    server = build_server()
    tools = await server.list_tools()
    names = {t.name for t in tools}

    print(f"roshan-harf-mcp {__version__}")
    print(f"registered {len(tools)} tools")

    missing = EXPECTED_TOOLS - names
    extra = names - EXPECTED_TOOLS
    if missing:
        problems.append(f"missing tools: {sorted(missing)}")
    if extra:
        problems.append(f"unexpected tools: {sorted(extra)}")

    for tool in sorted(tools, key=lambda t: t.name):
        props = (tool.inputSchema or {}).get("properties", {})
        has_instance = "instance" in props
        flag = "ok" if tool.description else "NO-DESC"
        inst = "instance" if has_instance else "-"
        print(f"  - {tool.name:28s} [{flag}] ({inst})")
        if not tool.description:
            problems.append(f"{tool.name} has no description")
        if tool.name in NO_INSTANCE:
            if has_instance:
                problems.append(f"{tool.name} should NOT expose 'instance'")
        elif not has_instance:
            problems.append(f"{tool.name} is missing the 'instance' parameter")

    if problems:
        print("\nFAILED:")
        for p in problems:
            print(f"  * {p}")
        return 1

    print("\nOK: all tools present with descriptions and correct 'instance' usage.")
    return 0


def main() -> int:
    return asyncio.run(_run())


if __name__ == "__main__":
    sys.exit(main())
