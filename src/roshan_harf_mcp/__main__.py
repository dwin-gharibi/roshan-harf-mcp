from __future__ import annotations
import argparse
from .server import build_server


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="roshan-harf-mcp",
        description=(
            "MCP server for Roshan AI's Harf (حرف) Persian speech service "
            "(transcription, alignment, live streaming, speaker tasks)."
        ),
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="Transport to serve on (default: stdio).",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind for HTTP transports (default: 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind for HTTP transports (default: 8000).",
    )
    parser.add_argument(
        "--log-level",
        default=None,
        help="Log level (DEBUG/INFO/WARNING/ERROR). Overrides config.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Build the server and run it with the requested transport."""

    args = _parse_args(argv)

    options: dict[str, object] = {"host": args.host, "port": args.port}
    if args.log_level:
        options["log_level"] = args.log_level.upper()

    server = build_server(**options)
    server.run(transport=args.transport)


if __name__ == "__main__":
    main()
