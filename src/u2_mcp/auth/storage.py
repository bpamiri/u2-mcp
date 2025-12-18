"""Authentication state storage for OAuth flows."""

import logging
import secrets
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class StoredClient:
    """Registered OAuth client (from DCR)."""

    client_id: str
    client_secret: str | None
    client_name: str | None
    redirect_uris: list[str]
    grant_types: list[str]
    response_types: list[str]
    scope: str | None
    token_endpoint_auth_method: str = "client_secret_post"  # Default auth method
    created_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StoredAuthCode:
    """Authorization code pending exchange."""

    code: str
    client_id: str
    redirect_uri: str
    scope: str
    state: str
    code_challenge: str | None
    code_challenge_method: str | None
    user_subject: str  # User identifier from IdP
    user_claims: dict[str, Any]  # Claims from IdP
    created_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + 600)  # 10 min


@dataclass
class StoredToken:
    """Issued access or refresh token."""

    token: str
    token_type: str  # "access" or "refresh"
    client_id: str
    user_subject: str
    scope: str
    created_at: float = field(default_factory=time.time)
    expires_at: float | None = None
    user_claims: dict[str, Any] = field(default_factory=dict)


@dataclass
class PendingAuthorization:
    """State for in-progress authorization flow."""

    state: str  # Internal state for IdP redirect
    client_id: str
    redirect_uri: str
    scope: str
    code_challenge: str | None
    code_challenge_method: str | None
    claude_redirect_uri: str  # Where to redirect after IdP auth
    claude_state: str | None  # Claude's original state to return
    created_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + 600)


class InMemoryAuthStorage:
    """In-memory storage for OAuth state.

    Suitable for single-instance deployments. For multi-instance deployments,
    use Redis or another distributed storage.

    Implements automatic cleanup of expired entries.
    """

    def __init__(self, cleanup_interval: int = 300):
        """Initialize storage.

        Args:
            cleanup_interval: Seconds between cleanup runs (default 5 min)
        """
        self._clients: dict[str, StoredClient] = {}
        self._auth_codes: dict[str, StoredAuthCode] = {}
        self._access_tokens: dict[str, StoredToken] = {}
        self._refresh_tokens: dict[str, StoredToken] = {}
        self._pending_auth: dict[str, PendingAuthorization] = {}
        self._cleanup_interval = cleanup_interval
        self._last_cleanup = time.time()

    # -------------------------------------------------------------------------
    # Client Management (DCR)
    # -------------------------------------------------------------------------

    def store_client(self, client: StoredClient) -> None:
        """Store a registered client."""
        self._clients[client.client_id] = client
        logger.info(f"Stored client: {client.client_id} ({client.client_name})")

    def get_client(self, client_id: str) -> StoredClient | None:
        """Retrieve a client by ID."""
        return self._clients.get(client_id)

    def delete_client(self, client_id: str) -> bool:
        """Delete a client and its tokens."""
        if client_id in self._clients:
            del self._clients[client_id]
            # Also clean up any tokens for this client
            self._access_tokens = {
                k: v for k, v in self._access_tokens.items() if v.client_id != client_id
            }
            self._refresh_tokens = {
                k: v for k, v in self._refresh_tokens.items() if v.client_id != client_id
            }
            logger.info(f"Deleted client: {client_id}")
            return True
        return False

    def validate_client_credentials(
        self, client_id: str, client_secret: str | None
    ) -> StoredClient | None:
        """Validate client credentials."""
        client = self._clients.get(client_id)
        if client is None:
            return None
        # Public clients have no secret
        if client.client_secret is None:
            return client
        # Confidential clients must match secret
        if secrets.compare_digest(client.client_secret or "", client_secret or ""):
            return client
        return None

    # -------------------------------------------------------------------------
    # Authorization Codes
    # -------------------------------------------------------------------------

    def store_auth_code(self, auth_code: StoredAuthCode) -> None:
        """Store an authorization code."""
        self._maybe_cleanup()
        self._auth_codes[auth_code.code] = auth_code
        logger.debug(f"Stored auth code for client {auth_code.client_id}")

    def get_auth_code(self, code: str) -> StoredAuthCode | None:
        """Retrieve and consume an authorization code (one-time use)."""
        auth_code = self._auth_codes.pop(code, None)
        if auth_code is None:
            return None
        if time.time() > auth_code.expires_at:
            logger.debug("Auth code expired")
            return None
        return auth_code

    # -------------------------------------------------------------------------
    # Access Tokens
    # -------------------------------------------------------------------------

    def store_access_token(self, token: StoredToken) -> None:
        """Store an access token."""
        self._maybe_cleanup()
        self._access_tokens[token.token] = token
        logger.debug(f"Stored access token for user {token.user_subject}")

    def get_access_token(self, token: str) -> StoredToken | None:
        """Retrieve an access token."""
        stored = self._access_tokens.get(token)
        if stored is None:
            return None
        if stored.expires_at and time.time() > stored.expires_at:
            del self._access_tokens[token]
            logger.debug("Access token expired")
            return None
        return stored

    def revoke_access_token(self, token: str) -> bool:
        """Revoke an access token."""
        if token in self._access_tokens:
            del self._access_tokens[token]
            return True
        return False

    # -------------------------------------------------------------------------
    # Refresh Tokens
    # -------------------------------------------------------------------------

    def store_refresh_token(self, token: StoredToken) -> None:
        """Store a refresh token."""
        self._maybe_cleanup()
        self._refresh_tokens[token.token] = token

    def get_refresh_token(self, token: str) -> StoredToken | None:
        """Retrieve a refresh token."""
        stored = self._refresh_tokens.get(token)
        if stored is None:
            return None
        if stored.expires_at and time.time() > stored.expires_at:
            del self._refresh_tokens[token]
            return None
        return stored

    def revoke_refresh_token(self, token: str) -> bool:
        """Revoke a refresh token."""
        if token in self._refresh_tokens:
            del self._refresh_tokens[token]
            return True
        return False

    # -------------------------------------------------------------------------
    # Pending Authorization State
    # -------------------------------------------------------------------------

    def store_pending_auth(self, pending: PendingAuthorization) -> None:
        """Store pending authorization state for IdP redirect."""
        self._maybe_cleanup()
        self._pending_auth[pending.state] = pending

    def get_pending_auth(self, state: str) -> PendingAuthorization | None:
        """Retrieve and consume pending authorization (one-time use)."""
        pending = self._pending_auth.pop(state, None)
        if pending is None:
            return None
        if time.time() > pending.expires_at:
            logger.debug("Pending auth expired")
            return None
        return pending

    # -------------------------------------------------------------------------
    # Cleanup
    # -------------------------------------------------------------------------

    def _maybe_cleanup(self) -> None:
        """Run cleanup if enough time has passed."""
        now = time.time()
        if now - self._last_cleanup < self._cleanup_interval:
            return
        self._cleanup()
        self._last_cleanup = now

    def _cleanup(self) -> None:
        """Remove expired entries."""
        now = time.time()
        expired_codes = [k for k, v in self._auth_codes.items() if now > v.expires_at]
        expired_access = [
            k for k, v in self._access_tokens.items() if v.expires_at and now > v.expires_at
        ]
        expired_refresh = [
            k for k, v in self._refresh_tokens.items() if v.expires_at and now > v.expires_at
        ]
        expired_pending = [k for k, v in self._pending_auth.items() if now > v.expires_at]

        for k in expired_codes:
            del self._auth_codes[k]
        for k in expired_access:
            del self._access_tokens[k]
        for k in expired_refresh:
            del self._refresh_tokens[k]
        for k in expired_pending:
            del self._pending_auth[k]

        total_cleaned = (
            len(expired_codes) + len(expired_access) + len(expired_refresh) + len(expired_pending)
        )
        if total_cleaned > 0:
            logger.debug(f"Cleaned up {total_cleaned} expired auth entries")

    def get_stats(self) -> dict[str, int]:
        """Get storage statistics."""
        return {
            "clients": len(self._clients),
            "auth_codes": len(self._auth_codes),
            "access_tokens": len(self._access_tokens),
            "refresh_tokens": len(self._refresh_tokens),
            "pending_auth": len(self._pending_auth),
        }
