"""Base class for Identity Provider adapters."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class TokenResponse:
    """Response from token exchange with IdP."""

    access_token: str
    token_type: str
    expires_in: int | None = None
    refresh_token: str | None = None
    id_token: str | None = None
    scope: str | None = None


@dataclass
class TokenInfo:
    """Information about a validated token."""

    subject: str  # User identifier
    email: str | None = None
    name: str | None = None
    groups: list[str] | None = None
    expires_at: int | None = None
    scopes: list[str] | None = None
    raw_claims: dict[str, Any] | None = None


class BaseIdPAdapter(ABC):
    """Abstract base class for external Identity Provider adapters.

    Subclasses implement the specific OAuth/OIDC flow for each provider
    (Duo, Auth0, generic OIDC, etc.).
    """

    def __init__(
        self,
        discovery_url: str | None,
        client_id: str | None,
        client_secret: str | None,
        scopes: list[str] | None = None,
    ):
        """Initialize the IdP adapter.

        Args:
            discovery_url: OIDC discovery URL (.well-known/openid-configuration)
            client_id: OAuth client ID registered with the IdP
            client_secret: OAuth client secret
            scopes: List of scopes to request (default: openid, profile, email)
        """
        self.discovery_url = discovery_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.scopes = scopes or ["openid", "profile", "email"]

        # Cached OIDC configuration (populated on first use)
        self._oidc_config: dict[str, Any] | None = None

    @abstractmethod
    async def get_authorization_url(
        self,
        redirect_uri: str,
        state: str,
        code_challenge: str | None = None,
        code_challenge_method: str | None = None,
        additional_params: dict[str, str] | None = None,
    ) -> str:
        """Generate the authorization URL to redirect users to for authentication.

        Args:
            redirect_uri: URL to redirect back to after authentication
            state: Opaque state value for CSRF protection
            code_challenge: PKCE code challenge (optional)
            code_challenge_method: PKCE method (S256 or plain)
            additional_params: Provider-specific additional parameters

        Returns:
            Full authorization URL to redirect the user to
        """
        pass

    @abstractmethod
    async def exchange_code(
        self,
        code: str,
        redirect_uri: str,
        code_verifier: str | None = None,
    ) -> TokenResponse:
        """Exchange an authorization code for tokens.

        Args:
            code: Authorization code from the IdP callback
            redirect_uri: Same redirect_uri used in authorization request
            code_verifier: PKCE code verifier (if PKCE was used)

        Returns:
            TokenResponse with access_token and optionally refresh_token, id_token

        Raises:
            AuthenticationError: If code exchange fails
        """
        pass

    @abstractmethod
    async def validate_token(self, access_token: str) -> TokenInfo | None:
        """Validate an access token and return user information.

        Args:
            access_token: The access token to validate

        Returns:
            TokenInfo with user details if valid, None if invalid
        """
        pass

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Use a refresh token to obtain new access token.

        Args:
            refresh_token: The refresh token

        Returns:
            TokenResponse with new access_token

        Raises:
            AuthenticationError: If refresh fails
        """
        pass

    async def get_oidc_config(self) -> dict[str, Any]:
        """Fetch and cache OIDC discovery configuration.

        Returns:
            OIDC configuration dict with endpoints

        Raises:
            ValueError: If discovery_url is not configured
            AuthenticationError: If fetch fails
        """
        if self._oidc_config is not None:
            return self._oidc_config

        if not self.discovery_url:
            raise ValueError("OIDC discovery URL not configured")

        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.get(self.discovery_url)
            response.raise_for_status()
            self._oidc_config = response.json()

        return self._oidc_config

    def clear_cache(self) -> None:
        """Clear cached OIDC configuration."""
        self._oidc_config = None


class AuthenticationError(Exception):
    """Raised when authentication with the IdP fails."""

    def __init__(self, message: str, error_code: str | None = None):
        super().__init__(message)
        self.error_code = error_code
