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
        config = U2Config()
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


def run_sse_server() -> None:
    """Run the MCP server in HTTP/SSE mode (legacy) for centralized deployment."""
    import uvicorn
    from starlette.middleware.cors import CORSMiddleware

    config = U2Config()

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


def run_streamable_http_server() -> None:
    """Run the MCP server in Streamable HTTP mode for Claude.ai Integrations.

    This mode supports:
    - Streamable HTTP transport (MCP 2025-06-18 spec)
    - OAuth authentication with external IdP (Duo, Auth0, OIDC)
    - Dynamic Client Registration (DCR) for Claude.ai
    """
    import uvicorn
    from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions, RevocationOptions
    from mcp.server.fastmcp import FastMCP as FastMCPAuth
    from starlette.middleware.cors import CORSMiddleware
    from starlette.routing import Route

    from .auth.callback import handle_oauth_callback
    from .auth.idp import create_idp_adapter
    from .auth.provider import U2OAuthProvider

    config = U2Config()

    # Create OAuth provider if auth is enabled
    auth_provider = None
    auth_settings = None

    if config.auth_enabled:
        if not config.auth_issuer_url:
            raise ValueError("U2_AUTH_ISSUER_URL is required when auth is enabled")
        if not config.idp_discovery_url and not config.duo_api_host:
            raise ValueError(
                "U2_IDP_DISCOVERY_URL (or U2_DUO_API_HOST for Duo) is required when auth is enabled"
            )

        # Create external IdP adapter
        idp_adapter = create_idp_adapter(config)

        # Create OAuth provider
        auth_provider = U2OAuthProvider(
            idp_adapter=idp_adapter,
            issuer_url=config.auth_issuer_url,
            token_expiry=config.token_expiry_seconds,
            refresh_token_expiry=config.refresh_token_expiry_seconds,
        )

        # Configure auth settings for FastMCP
        auth_settings = AuthSettings(
            issuer_url=config.auth_issuer_url,
            resource_server_url=config.auth_issuer_url,
            client_registration_options=ClientRegistrationOptions(
                enabled=True,  # Required for Claude.ai DCR
                valid_scopes=["u2:read", "u2:write"],
                default_scopes=["u2:read"],
            ),
            revocation_options=RevocationOptions(enabled=True),
            required_scopes=["u2:read"],
        )

        logger.info(f"OAuth enabled with {config.idp_provider} IdP")

    # Create new FastMCP instance with auth configured
    # Note: We need a new instance because the original 'mcp' was created without auth
    mcp_streamable = FastMCPAuth(
        name="U2 MCP Server",
        auth_server_provider=auth_provider,
        auth=auth_settings,
        host=config.http_host,
        port=config.http_port,
        streamable_http_path="/",  # Root path for Claude.ai compatibility
    )

    # Copy tools from the original mcp instance
    # Tools are registered via decorators on the module-level 'mcp' instance
    # We need to copy them to the new instance (directly copy the dict, not via add_tool
    # since add_tool expects functions, not Tool objects)
    mcp_streamable._tool_manager._tools.update(mcp._tool_manager._tools)

    # Copy resources (directly copy the dict)
    mcp_streamable._resource_manager._resources.update(mcp._resource_manager._resources)

    # Copy prompts if any (directly copy the dict)
    mcp_streamable._prompt_manager._prompts.update(mcp._prompt_manager._prompts)

    # Get the Streamable HTTP app
    app = mcp_streamable.streamable_http_app()

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.http_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add custom OAuth callback route for external IdP
    if auth_provider:
        from starlette.requests import Request
        from starlette.responses import Response

        async def oauth_callback_handler(request: Request) -> Response:
            return await handle_oauth_callback(request, auth_provider)

        # Add route to the app's router
        app.routes.append(Route("/oauth/callback", oauth_callback_handler, methods=["GET"]))

    logger.info(
        f"Starting U2 MCP Server (Streamable HTTP) on {config.http_host}:{config.http_port}"
    )
    logger.info(f"MCP endpoint: http://{config.http_host}:{config.http_port}/")
    if config.auth_enabled:
        logger.info("OAuth endpoints: /authorize, /token, /register, /.well-known/*")
        logger.info("OAuth callback: /oauth/callback")
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
        help="Run as HTTP/SSE server (legacy mode)",
    )
    parser.add_argument(
        "--streamable-http",
        action="store_true",
        help="Run as Streamable HTTP server for Claude.ai Integrations",
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

    if args.streamable_http:
        run_streamable_http_server()
    elif args.http:
        run_sse_server()
    else:
        logger.info("Starting U2 MCP Server (stdio mode)")
        mcp.run()


if __name__ == "__main__":
    main()
