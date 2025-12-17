"""Main MCP server entry point for u2-mcp."""

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
    knowledge as knowledge_tools,
    query,
    subroutine,
    transaction,
)


def main() -> None:
    """Entry point for the MCP server."""
    logger.info("Starting U2 MCP Server")
    mcp.run()


if __name__ == "__main__":
    main()
