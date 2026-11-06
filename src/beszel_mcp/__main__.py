"""Main entry point for the Beszel MCP server."""

import os

from .server import mcp


def _run_http() -> None:
    import uvicorn
    from starlette.middleware import Middleware

    from .auth import BearerAuthMiddleware

    host = os.environ.get("MCP_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_PORT", "8000"))
    token = os.environ.get("MCP_AUTH_TOKEN") or None

    middleware = [Middleware(BearerAuthMiddleware, token=token)] if token else []
    app = mcp.http_app(path="/mcp", middleware=middleware)
    uvicorn.run(app, host=host, port=port)


def main():
    """Entry point for the beszel-mcp command.

    MCP_TRANSPORT selects the transport: ``stdio`` (default) or ``http``
    (Streamable HTTP at /mcp, plus GET /health).
    """
    transport = os.environ.get("MCP_TRANSPORT", "stdio").strip().lower()
    if transport == "stdio":
        mcp.run()
    elif transport == "http":
        _run_http()
    else:
        raise SystemExit(f"Unsupported MCP_TRANSPORT {transport!r}; use 'stdio' or 'http'")


if __name__ == "__main__":
    main()
