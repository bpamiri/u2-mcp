"""OAuth callback handler for external IdP redirects."""

import logging
from typing import TYPE_CHECKING

from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

if TYPE_CHECKING:
    from .provider import U2OAuthProvider

logger = logging.getLogger(__name__)


async def handle_oauth_callback(
    request: Request,
    provider: "U2OAuthProvider",
) -> Response:
    """Handle OAuth callback from external IdP.

    This route receives the callback after the user authenticates with the
    external IdP (Duo, Auth0, etc.) and generates an authorization code
    to send back to Claude.ai.

    Args:
        request: Starlette request object
        provider: U2OAuthProvider instance

    Returns:
        Redirect response to Claude's callback URL with auth code,
        or error response if callback is invalid
    """
    # Extract callback parameters
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    error = request.query_params.get("error")
    error_description = request.query_params.get("error_description")

    # Handle IdP error
    if error:
        logger.error(f"IdP returned error: {error} - {error_description}")
        # We need to redirect back to Claude with error
        # But we don't have the original redirect_uri without the state
        # Return a simple error page
        return Response(
            content=f"Authentication failed: {error_description or error}",
            status_code=400,
            media_type="text/plain",
        )

    # Validate required parameters
    if not code or not state:
        logger.error("Missing code or state in IdP callback")
        return Response(
            content="Invalid callback: missing code or state parameter",
            status_code=400,
            media_type="text/plain",
        )

    try:
        # Process the callback and get redirect URL
        redirect_url = await provider.handle_idp_callback(code=code, state=state)
        logger.info("Redirecting to Claude callback")
        return RedirectResponse(url=redirect_url, status_code=302)

    except Exception as e:
        logger.exception(f"Error processing IdP callback: {e}")
        return Response(
            content=f"Authentication error: {str(e)}",
            status_code=500,
            media_type="text/plain",
        )
