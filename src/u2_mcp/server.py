"""Main MCP server entry point for u2-mcp."""

import argparse
import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from .config import U2Config
from .connection import ConnectionError, ConnectionManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastMCP server instance
mcp = FastMCP("U2 MCP Server")

# Global connection manager (initialized on first connect)
_connection_manager: ConnectionManager | None = None


def get_connection_manager() -> ConnectionManager:
    """Get or create the global connection manager.

    Returns:
        ConnectionManager instance configured from environment variables
    """
    global _connection_manager
    if _connection_manager is None:
        config = U2Config()  # type: ignore[call-arg]  # pydantic-settings loads from env
        _connection_manager = ConnectionManager(config)
    return _connection_manager


def reset_connection_manager() -> None:
    """Reset the global connection manager (useful for testing)."""
    global _connection_manager
    if _connection_manager is not None:
        _connection_manager.disconnect_all()
    _connection_manager = None


# =============================================================================
# Connection Management Tools
# =============================================================================


@mcp.tool()
def connect() -> dict[str, Any]:
    """Establish connection to the Universe/UniData server.

    Uses configuration from environment variables:
    - U2_HOST: Server hostname
    - U2_USER: Username
    - U2_PASSWORD: Password
    - U2_ACCOUNT: Account name
    - U2_SERVICE: Service type (uvcs/udcs), defaults to uvcs

    Returns:
        Connection status and details including host, account, service, and timestamp.
    """
    try:
        manager = get_connection_manager()
        info = manager.connect()
        return {
            "status": "connected",
            "host": info.host,
            "account": info.account,
            "service": info.service,
            "connected_at": info.connected_at.isoformat(),
        }
    except ConnectionError as e:
        return {"status": "error", "message": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error during connect: {e}")
        return {"status": "error", "message": f"Unexpected error: {e}"}


@mcp.tool()
def disconnect() -> dict[str, Any]:
    """Close all connections to the Universe/UniData server.

    Returns:
        Disconnection status and count of closed connections.
    """
    try:
        manager = get_connection_manager()
        closed = manager.disconnect_all()
        return {
            "status": "disconnected",
            "connections_closed": closed,
        }
    except Exception as e:
        logger.error(f"Error during disconnect: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def list_connections() -> dict[str, Any]:
    """List all active database connections.

    Returns:
        List of active connections with their details (name, host, account, service,
        connection time, and active status).
    """
    try:
        manager = get_connection_manager()
        connections = manager.list_connections()
        return {
            "connections": [
                {
                    "name": info.name,
                    "host": info.host,
                    "account": info.account,
                    "service": info.service,
                    "connected_at": info.connected_at.isoformat(),
                    "is_active": info.is_active,
                }
                for info in connections.values()
            ]
        }
    except Exception as e:
        logger.error(f"Error listing connections: {e}")
        return {"status": "error", "message": str(e)}


# =============================================================================
# Import and register tools from submodules
# =============================================================================

# These imports register the tools and resources with the mcp instance
from .resources import examples, knowledge, syntax_help  # noqa: E402, F401
from .tools import (  # noqa: E402, F401
    dictionary,
    files,
    query,
    subroutine,
    transaction,
)


def run_http_server() -> None:
    """Run the MCP server in HTTP/SSE mode for centralized deployment."""
    import uvicorn
    from starlette.middleware.cors import CORSMiddleware

    config = U2Config()  # type: ignore[call-arg]

    # Get the SSE app from FastMCP
    app = mcp.sse_app()

    # Add CORS middleware for browser clients
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.http_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    logger.info(f"Starting U2 MCP Server (HTTP/SSE) on {config.http_host}:{config.http_port}")
    logger.info(f"SSE endpoint: http://{config.http_host}:{config.http_port}/sse")
    logger.info(f"CORS origins: {config.http_cors_origins}")

    uvicorn.run(
        app,
        host=config.http_host,
        port=config.http_port,
        log_level="info",
    )


def main() -> None:
    """Entry point for the MCP server."""
    parser = argparse.ArgumentParser(
        description="U2 MCP Server - Connect AI assistants to Universe/UniData databases"
    )
    parser.add_argument(
        "--http",
        action="store_true",
        help="Run as HTTP/SSE server for centralized deployment (default: stdio mode)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="HTTP server host (overrides U2_HTTP_HOST env var)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="HTTP server port (overrides U2_HTTP_PORT env var)",
    )

    args = parser.parse_args()

    # Override config with CLI args if provided
    if args.host:
        import os

        os.environ["U2_HTTP_HOST"] = args.host
    if args.port:
        import os

        os.environ["U2_HTTP_PORT"] = str(args.port)

    if args.http:
        run_http_server()
    else:
        logger.info("Starting U2 MCP Server (stdio mode)")
        mcp.run()


if __name__ == "__main__":
    main()
