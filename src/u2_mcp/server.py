"""Main MCP server entry point for u2-mcp."""

import argparse
import functools
import logging
import time
from collections.abc import Callable
from typing import Any, TypeVar

from mcp.server.fastmcp import FastMCP

from .config import U2Config
from .connection import ConnectionError, ConnectionManager
from .utils.audit import audit_tool_call, get_audit_logger, init_audit_logger
from .utils.watchdog import ConnectionWatchdog, get_watchdog, init_watchdog

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Type variable for generic function wrapping
F = TypeVar("F", bound=Callable[..., Any])

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


def _init_watchdog(config: U2Config) -> ConnectionWatchdog | None:
    """Initialize the connection watchdog.

    Args:
        config: U2Config with watchdog settings

    Returns:
        ConnectionWatchdog instance or None if disabled
    """
    if not config.watchdog_enabled:
        logger.info("Connection watchdog disabled")
        return None

    manager = get_connection_manager()

    def health_check() -> bool:
        return manager.health_check()

    def force_disconnect() -> None:
        manager.force_disconnect()

    watchdog = init_watchdog(config, health_check, force_disconnect)
    logger.info("Connection watchdog initialized")
    return watchdog


def _init_audit_logging(config: U2Config) -> None:
    """Initialize audit logging if enabled.

    Args:
        config: U2Config instance with audit settings
    """
    if config.audit_enabled:
        init_audit_logger(
            audit_path=config.audit_path,
            include_results=config.audit_include_results,
            max_result_size=config.audit_max_result_size,
        )
        logger.info(f"Audit logging enabled, writing to {config.audit_path}")


def _wrap_tools_with_audit(mcp_instance: FastMCP) -> None:
    """Wrap all registered tools with audit logging.

    Args:
        mcp_instance: The FastMCP instance with registered tools
    """
    audit_logger = get_audit_logger()
    if not audit_logger:
        return

    # Start a new audit session
    audit_logger.start_session()

    # Wrap each tool's function with audit logging
    for tool_name, tool in mcp_instance._tool_manager._tools.items():
        original_fn = tool.fn

        @functools.wraps(original_fn)
        def wrapped_fn(
            *args: Any,
            _original_fn: Callable[..., Any] = original_fn,
            _tool_name: str = tool_name,
            **kwargs: Any,
        ) -> Any:
            start_time = time.time()
            error_msg = None
            result = None

            try:
                result = _original_fn(*args, **kwargs)
                return result
            except Exception as e:
                error_msg = str(e)
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                audit_tool_call(
                    tool_name=_tool_name,
                    parameters=kwargs,
                    result=result,
                    error=error_msg,
                    duration_ms=duration_ms,
                )

        tool.fn = wrapped_fn


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
    from .utils.knowledge import get_knowledge_store

    try:
        manager = get_connection_manager()
        info = manager.connect()

        # Check for available knowledge
        store = get_knowledge_store()
        topics = store.list_topics()
        knowledge_hint = None
        if topics:
            topic_names = [t["topic"] for t in topics]
            knowledge_hint = (
                f"Previous knowledge available ({len(topics)} topics): {', '.join(topic_names)}. "
                "Call get_all_knowledge() to retrieve learned information about this database."
            )

        result: dict[str, Any] = {
            "status": "connected",
            "host": info.host,
            "account": info.account,
            "service": info.service,
            "connected_at": info.connected_at.isoformat(),
        }

        if knowledge_hint:
            result["knowledge_available"] = knowledge_hint

        return result
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


@mcp.tool()
def watchdog_status() -> dict[str, Any]:
    """Get the connection watchdog status and statistics.

    The watchdog monitors connection health and automatically recovers
    from hung database connections.

    Returns:
        Watchdog configuration and statistics including check counts,
        failure counts, and forced reconnects.
    """
    watchdog = get_watchdog()
    if watchdog is None:
        return {
            "status": "disabled",
            "message": "Watchdog not initialized or disabled",
        }
    return watchdog.get_status()


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

    # Initialize audit logging if enabled
    _init_audit_logging(config)
    _wrap_tools_with_audit(mcp)

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

    # Initialize audit logging if enabled
    _init_audit_logging(config)

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

    # Wrap tools with audit logging if enabled
    _wrap_tools_with_audit(mcp_streamable)

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

    # Initialize the connection watchdog
    watchdog = _init_watchdog(config)

    logger.info(
        f"Starting U2 MCP Server (Streamable HTTP) on {config.http_host}:{config.http_port}"
    )
    logger.info(f"MCP endpoint: http://{config.http_host}:{config.http_port}/")
    if config.auth_enabled:
        logger.info("OAuth endpoints: /authorize, /token, /register, /.well-known/*")
        logger.info("OAuth callback: /oauth/callback")
    logger.info(f"CORS origins: {config.http_cors_origins}")

    # Run uvicorn with watchdog in background
    import threading

    def run_watchdog_sync() -> None:
        """Run the watchdog in a separate thread with its own event loop."""
        import asyncio

        async def watchdog_main() -> None:
            if watchdog:
                await watchdog.start()
                # Keep running until stopped
                while watchdog.is_running:
                    await asyncio.sleep(1)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(watchdog_main())
        finally:
            loop.close()

    if watchdog:
        watchdog_thread = threading.Thread(target=run_watchdog_sync, daemon=True)
        watchdog_thread.start()
        logger.info("Watchdog thread started")

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
        # Initialize audit logging for stdio mode
        config = U2Config()
        _init_audit_logging(config)
        _wrap_tools_with_audit(mcp)

        logger.info("Starting U2 MCP Server (stdio mode)")
        mcp.run()


if __name__ == "__main__":
    main()
