"""OAuth Authorization Server Provider for u2-mcp.

Implements MCP SDK's OAuthAuthorizationServerProvider protocol,
bridging to external identity providers (Duo, Auth0, generic OIDC).
"""

import logging
import secrets
import time
from typing import TYPE_CHECKING

from mcp.server.auth.provider import (
    AccessToken,
    AuthorizationCode,
    AuthorizationParams,
    AuthorizeError,
    OAuthAuthorizationServerProvider,
    RefreshToken,
    RegistrationError,
    construct_redirect_uri,
)
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken

from .storage import (
    InMemoryAuthStorage,
    PendingAuthorization,
    StoredAuthCode,
    StoredClient,
    StoredToken,
)

if TYPE_CHECKING:
    from .idp.base import BaseIdPAdapter

logger = logging.getLogger(__name__)


class U2OAuthProvider(
    OAuthAuthorizationServerProvider[AuthorizationCode, RefreshToken, AccessToken]
):
    """OAuth provider that bridges Claude.ai DCR to external identity providers.

    This provider acts as an OAuth Authorization Server for Claude.ai clients
    while delegating actual user authentication to an external IdP (Duo, Auth0, etc.).

    Flow:
        1. Claude.ai registers via DCR -> stored in memory
        2. Claude.ai initiates /authorize -> redirects to external IdP
        3. User authenticates with IdP -> callback to /oauth/callback
        4. Callback generates auth code -> redirects to Claude callback
        5. Claude.ai exchanges code at /token -> returns access token
    """

    def __init__(
        self,
        idp_adapter: "BaseIdPAdapter",
        issuer_url: str,
        callback_path: str = "/oauth/callback",
        token_expiry: int = 3600,
        refresh_token_expiry: int = 86400 * 30,  # 30 days
        storage: InMemoryAuthStorage | None = None,
    ):
        """Initialize the OAuth provider.

        Args:
            idp_adapter: Adapter for the external identity provider
            issuer_url: Public URL of this server (e.g., https://u2-mcp.example.com)
            callback_path: Path for IdP callback (default /oauth/callback)
            token_expiry: Access token lifetime in seconds (default 1 hour)
            refresh_token_expiry: Refresh token lifetime in seconds (default 30 days)
            storage: Auth state storage (default InMemoryAuthStorage)
        """
        self.idp_adapter = idp_adapter
        self.issuer_url = issuer_url.rstrip("/")
        self.callback_path = callback_path
        self.token_expiry = token_expiry
        self.refresh_token_expiry = refresh_token_expiry
        self.storage = storage or InMemoryAuthStorage()

        # Internal callback URL for external IdP
        self.idp_callback_url = f"{self.issuer_url}{self.callback_path}"

    # -------------------------------------------------------------------------
    # Client Registration (DCR)
    # -------------------------------------------------------------------------

    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        """Retrieve registered client by ID."""
        stored = self.storage.get_client(client_id)
        if stored is None:
            return None

        return OAuthClientInformationFull(
            client_id=stored.client_id,
            client_secret=stored.client_secret,
            client_name=stored.client_name,
            redirect_uris=stored.redirect_uris,
            grant_types=stored.grant_types,
            response_types=stored.response_types,
            scope=stored.scope,
            token_endpoint_auth_method=stored.token_endpoint_auth_method,
            client_id_issued_at=int(stored.created_at),
        )

    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        """Register a new OAuth client (DCR).

        Claude.ai uses DCR to register itself as a client.
        """
        # Validate redirect URIs
        if not client_info.redirect_uris:
            raise RegistrationError(
                error="invalid_redirect_uri",
                error_description="At least one redirect_uri is required",
            )

        # Generate client credentials if not provided
        client_id = client_info.client_id or f"client_{secrets.token_urlsafe(16)}"
        client_secret = client_info.client_secret or secrets.token_urlsafe(32)

        stored = StoredClient(
            client_id=client_id,
            client_secret=client_secret,
            client_name=client_info.client_name,
            redirect_uris=[str(uri) for uri in client_info.redirect_uris],
            grant_types=list(client_info.grant_types),
            response_types=list(client_info.response_types),
            scope=client_info.scope,
            token_endpoint_auth_method=(
                client_info.token_endpoint_auth_method or "client_secret_post"
            ),
        )

        self.storage.store_client(stored)

        # Update client_info with generated credentials
        client_info.client_id = client_id
        client_info.client_secret = client_secret
        client_info.client_id_issued_at = int(stored.created_at)

        logger.info(f"Registered client: {client_id} ({client_info.client_name})")

    # -------------------------------------------------------------------------
    # Authorization
    # -------------------------------------------------------------------------

    async def authorize(
        self, client: OAuthClientInformationFull, params: AuthorizationParams
    ) -> str:
        """Start authorization flow by redirecting to external IdP.

        Returns a URL to redirect the user to the external IdP for authentication.
        After IdP auth, user is redirected to our callback which then redirects
        to Claude's callback with an auth code.
        """
        # Generate state for the IdP redirect (contains original request info)
        idp_state = secrets.token_urlsafe(32)

        # Store pending authorization state
        pending = PendingAuthorization(
            state=idp_state,
            client_id=client.client_id,
            redirect_uri=str(params.redirect_uri),
            scope=" ".join(params.scopes) if params.scopes else "",
            code_challenge=params.code_challenge,
            code_challenge_method="S256",  # We always use S256
            claude_redirect_uri=str(params.redirect_uri),
            claude_state=params.state,  # Store Claude's original state to return later
        )
        self.storage.store_pending_auth(pending)

        # Generate authorization URL for external IdP
        idp_auth_url = await self.idp_adapter.get_authorization_url(
            redirect_uri=self.idp_callback_url,
            state=idp_state,
            # We don't use PKCE with the IdP - we use it between Claude and us
        )

        logger.info(f"Redirecting to IdP for client {client.client_id}")
        return idp_auth_url

    # -------------------------------------------------------------------------
    # Authorization Code Exchange
    # -------------------------------------------------------------------------

    async def load_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: str
    ) -> AuthorizationCode | None:
        """Load an authorization code for validation."""
        stored = self.storage.get_auth_code(authorization_code)
        if stored is None:
            return None

        if stored.client_id != client.client_id:
            logger.warning(f"Auth code client mismatch: {stored.client_id} != {client.client_id}")
            return None

        return AuthorizationCode(
            code=stored.code,
            scopes=stored.scope.split() if stored.scope else [],
            expires_at=stored.expires_at,
            client_id=stored.client_id,
            code_challenge=stored.code_challenge or "",
            redirect_uri=stored.redirect_uri,
            redirect_uri_provided_explicitly=True,
        )

    async def exchange_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: AuthorizationCode
    ) -> OAuthToken:
        """Exchange authorization code for tokens."""
        # Generate tokens
        access_token = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(32)

        now = time.time()
        access_expires = now + self.token_expiry
        refresh_expires = now + self.refresh_token_expiry

        # Store access token
        self.storage.store_access_token(
            StoredToken(
                token=access_token,
                token_type="access",
                client_id=client.client_id,
                user_subject=authorization_code.client_id,  # Will be set properly in callback
                scope=" ".join(authorization_code.scopes),
                expires_at=access_expires,
            )
        )

        # Store refresh token
        self.storage.store_refresh_token(
            StoredToken(
                token=refresh_token,
                token_type="refresh",
                client_id=client.client_id,
                user_subject=authorization_code.client_id,
                scope=" ".join(authorization_code.scopes),
                expires_at=refresh_expires,
            )
        )

        logger.info(f"Issued tokens for client {client.client_id}")

        return OAuthToken(
            access_token=access_token,
            token_type="Bearer",
            expires_in=self.token_expiry,
            refresh_token=refresh_token,
            scope=" ".join(authorization_code.scopes) if authorization_code.scopes else None,
        )

    # -------------------------------------------------------------------------
    # Refresh Token Exchange
    # -------------------------------------------------------------------------

    async def load_refresh_token(
        self, client: OAuthClientInformationFull, refresh_token: str
    ) -> RefreshToken | None:
        """Load a refresh token for validation."""
        stored = self.storage.get_refresh_token(refresh_token)
        if stored is None:
            return None

        if stored.client_id != client.client_id:
            logger.warning("Refresh token client mismatch")
            return None

        return RefreshToken(
            token=stored.token,
            client_id=stored.client_id,
            scopes=stored.scope.split() if stored.scope else [],
            expires_at=int(stored.expires_at) if stored.expires_at else None,
        )

    async def exchange_refresh_token(
        self,
        client: OAuthClientInformationFull,
        refresh_token: RefreshToken,
        scopes: list[str],
    ) -> OAuthToken:
        """Exchange refresh token for new tokens (token rotation)."""
        # Revoke old refresh token
        self.storage.revoke_refresh_token(refresh_token.token)

        # Generate new tokens
        new_access_token = secrets.token_urlsafe(32)
        new_refresh_token = secrets.token_urlsafe(32)

        now = time.time()
        access_expires = now + self.token_expiry
        refresh_expires = now + self.refresh_token_expiry

        scope_str = " ".join(scopes) if scopes else " ".join(refresh_token.scopes)

        # Store new access token
        self.storage.store_access_token(
            StoredToken(
                token=new_access_token,
                token_type="access",
                client_id=client.client_id,
                user_subject="",  # Preserved from original auth
                scope=scope_str,
                expires_at=access_expires,
            )
        )

        # Store new refresh token
        self.storage.store_refresh_token(
            StoredToken(
                token=new_refresh_token,
                token_type="refresh",
                client_id=client.client_id,
                user_subject="",
                scope=scope_str,
                expires_at=refresh_expires,
            )
        )

        logger.info(f"Rotated tokens for client {client.client_id}")

        return OAuthToken(
            access_token=new_access_token,
            token_type="Bearer",
            expires_in=self.token_expiry,
            refresh_token=new_refresh_token,
            scope=scope_str,
        )

    # -------------------------------------------------------------------------
    # Token Validation
    # -------------------------------------------------------------------------

    async def load_access_token(self, token: str) -> AccessToken | None:
        """Validate and load an access token."""
        stored = self.storage.get_access_token(token)
        if stored is None:
            return None

        return AccessToken(
            token=stored.token,
            client_id=stored.client_id,
            scopes=stored.scope.split() if stored.scope else [],
            expires_at=int(stored.expires_at) if stored.expires_at else None,
        )

    # -------------------------------------------------------------------------
    # Token Revocation
    # -------------------------------------------------------------------------

    async def revoke_token(self, token: AccessToken | RefreshToken) -> None:
        """Revoke an access or refresh token."""
        if isinstance(token, AccessToken):
            self.storage.revoke_access_token(token.token)
        else:
            self.storage.revoke_refresh_token(token.token)
        logger.info(f"Revoked token for client {token.client_id}")

    # -------------------------------------------------------------------------
    # IdP Callback Handling
    # -------------------------------------------------------------------------

    async def handle_idp_callback(self, code: str, state: str) -> str:
        """Handle callback from external IdP after user authentication.

        This is called from the /oauth/callback route handler.

        Args:
            code: Authorization code from the IdP
            state: State parameter (our internal state with pending auth info)

        Returns:
            Redirect URL to Claude's callback with our authorization code

        Raises:
            AuthorizeError: If callback is invalid
        """
        # Retrieve pending authorization
        pending = self.storage.get_pending_auth(state)
        if pending is None:
            raise AuthorizeError(
                error="invalid_request",
                error_description="Invalid or expired state parameter",
            )

        # Exchange code with IdP for tokens
        try:
            idp_tokens = await self.idp_adapter.exchange_code(
                code=code,
                redirect_uri=self.idp_callback_url,
            )
        except Exception as e:
            logger.error(f"IdP code exchange failed: {e}")
            raise AuthorizeError(
                error="access_denied",
                error_description="Authentication failed with identity provider",
            ) from e

        # Validate IdP token to get user info
        try:
            user_info = await self.idp_adapter.validate_token(idp_tokens.access_token)
            if user_info is None:
                raise AuthorizeError(
                    error="access_denied",
                    error_description="Failed to validate identity",
                )
        except AuthorizeError:
            raise  # Re-raise our own errors
        except Exception as e:
            logger.error(f"IdP token validation failed: {e}")
            raise AuthorizeError(
                error="access_denied",
                error_description="Failed to validate identity",
            ) from e

        # Generate authorization code for Claude
        auth_code = secrets.token_urlsafe(32)

        stored_code = StoredAuthCode(
            code=auth_code,
            client_id=pending.client_id,
            redirect_uri=pending.claude_redirect_uri,
            scope=pending.scope,
            state=state,
            code_challenge=pending.code_challenge,
            code_challenge_method=pending.code_challenge_method,
            user_subject=user_info.subject,
            user_claims=user_info.raw_claims or {},
        )
        self.storage.store_auth_code(stored_code)

        # Build redirect URL to Claude's callback (use Claude's original state)
        redirect_url: str = construct_redirect_uri(
            pending.claude_redirect_uri,
            code=auth_code,
            state=pending.claude_state,
        )

        logger.info(f"IdP callback successful for user {user_info.subject}")
        return redirect_url
