"""Cisco Duo SSO adapter using OIDC."""

import logging

from .oidc import GenericOIDCAdapter

logger = logging.getLogger(__name__)


class DuoOIDCAdapter(GenericOIDCAdapter):
    """Adapter for Cisco Duo SSO using OpenID Connect.

    Duo supports standard OIDC with some Duo-specific configurations.
    Requires a "Web SDK" or "OIDC Relying Party" application in Duo Admin Panel.

    Configuration:
        - Discovery URL: https://sso-XXXXXXXX.sso.duosecurity.com/.well-known/openid-configuration
        - Or use duo_api_host to auto-construct the URL

    Duo-specific features:
        - Supports Duo Push for 2FA
        - Group membership via 'groups' claim
        - Duo session management
    """

    def __init__(
        self,
        discovery_url: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        scopes: list[str] | None = None,
        duo_api_host: str | None = None,
    ):
        """Initialize Duo OIDC adapter.

        Args:
            discovery_url: Full OIDC discovery URL (takes precedence)
            client_id: Duo OIDC client ID
            client_secret: Duo OIDC client secret
            scopes: Scopes to request (default includes Duo-recommended scopes)
            duo_api_host: Duo API hostname (e.g., api-XXXXXXXX.duosecurity.com)
                         Used to construct discovery_url if not provided
        """
        # Duo-specific default scopes
        if scopes is None:
            scopes = ["openid", "profile", "email", "groups"]

        # Construct discovery URL from Duo API host if not provided
        if not discovery_url and duo_api_host:
            # Duo SSO uses a different hostname pattern than the API
            # api-XXXXXXXX.duosecurity.com -> sso-XXXXXXXX.sso.duosecurity.com
            if duo_api_host.startswith("api-"):
                sso_host = duo_api_host.replace("api-", "sso-", 1)
                sso_host = sso_host.replace(".duosecurity.com", ".sso.duosecurity.com")
            else:
                sso_host = duo_api_host
            discovery_url = f"https://{sso_host}/.well-known/openid-configuration"

        super().__init__(
            discovery_url=discovery_url,
            client_id=client_id,
            client_secret=client_secret,
            scopes=scopes,
        )

        self.duo_api_host = duo_api_host

    async def get_authorization_url(
        self,
        redirect_uri: str,
        state: str,
        code_challenge: str | None = None,
        code_challenge_method: str | None = None,
        additional_params: dict[str, str] | None = None,
    ) -> str:
        """Generate Duo authorization URL.

        Adds Duo-specific parameters if needed.
        """
        # Duo supports standard OIDC, but we can add Duo-specific params
        duo_params = additional_params or {}

        # Optionally request specific Duo authentication methods
        # duo_params["duo_uname"] = "username"  # Pre-fill username
        # duo_params["prompt"] = "login"  # Force re-authentication

        return await super().get_authorization_url(
            redirect_uri=redirect_uri,
            state=state,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            additional_params=duo_params,
        )
