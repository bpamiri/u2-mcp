"""Generic OIDC adapter for standard OpenID Connect providers."""

import logging
from urllib.parse import urlencode

import httpx

from .base import AuthenticationError, BaseIdPAdapter, TokenInfo, TokenResponse

logger = logging.getLogger(__name__)


class GenericOIDCAdapter(BaseIdPAdapter):
    """Adapter for standard OpenID Connect providers.

    Works with any OIDC-compliant provider that supports:
    - OIDC Discovery (.well-known/openid-configuration)
    - Authorization Code flow
    - PKCE (optional but recommended)
    - Token introspection or userinfo endpoint
    """

    async def get_authorization_url(
        self,
        redirect_uri: str,
        state: str,
        code_challenge: str | None = None,
        code_challenge_method: str | None = None,
        additional_params: dict[str, str] | None = None,
    ) -> str:
        """Generate authorization URL for the OIDC provider."""
        config = await self.get_oidc_config()
        authorize_endpoint = config["authorization_endpoint"]

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(self.scopes),
            "state": state,
        }

        # Add PKCE if provided
        if code_challenge:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = code_challenge_method or "S256"

        # Add any provider-specific params
        if additional_params:
            params.update(additional_params)

        return f"{authorize_endpoint}?{urlencode(params)}"

    async def exchange_code(
        self,
        code: str,
        redirect_uri: str,
        code_verifier: str | None = None,
    ) -> TokenResponse:
        """Exchange authorization code for tokens."""
        config = await self.get_oidc_config()
        token_endpoint = config["token_endpoint"]

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        # Add PKCE verifier if provided
        if code_verifier:
            data["code_verifier"] = code_verifier

        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_endpoint,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get("error_description", response.text)
                error_code = error_data.get("error", "token_exchange_failed")
                logger.error(f"Token exchange failed: {error_msg}")
                raise AuthenticationError(f"Token exchange failed: {error_msg}", error_code)

            token_data = response.json()

        return TokenResponse(
            access_token=token_data["access_token"],
            token_type=token_data.get("token_type", "Bearer"),
            expires_in=token_data.get("expires_in"),
            refresh_token=token_data.get("refresh_token"),
            id_token=token_data.get("id_token"),
            scope=token_data.get("scope"),
        )

    async def validate_token(self, access_token: str) -> TokenInfo | None:
        """Validate token using userinfo endpoint or introspection."""
        config = await self.get_oidc_config()

        # Try userinfo endpoint first (standard OIDC)
        userinfo_endpoint = config.get("userinfo_endpoint")
        if userinfo_endpoint:
            try:
                return await self._validate_via_userinfo(access_token, userinfo_endpoint)
            except Exception as e:
                logger.debug(f"Userinfo validation failed: {e}")

        # Fall back to introspection if available
        introspection_endpoint = config.get("introspection_endpoint")
        if introspection_endpoint:
            try:
                return await self._validate_via_introspection(access_token, introspection_endpoint)
            except Exception as e:
                logger.debug(f"Introspection validation failed: {e}")

        logger.warning("No validation endpoint available")
        return None

    async def _validate_via_userinfo(
        self, access_token: str, userinfo_endpoint: str
    ) -> TokenInfo | None:
        """Validate token by calling userinfo endpoint."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                userinfo_endpoint,
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if response.status_code == 401:
                return None

            if response.status_code != 200:
                logger.error(f"Userinfo request failed: {response.status_code}")
                return None

            claims = response.json()

        return TokenInfo(
            subject=claims.get("sub", ""),
            email=claims.get("email"),
            name=claims.get("name"),
            groups=claims.get("groups"),
            scopes=claims.get("scope", "").split() if claims.get("scope") else None,
            raw_claims=claims,
        )

    async def _validate_via_introspection(
        self, access_token: str, introspection_endpoint: str
    ) -> TokenInfo | None:
        """Validate token via OAuth 2.0 Token Introspection (RFC 7662)."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                introspection_endpoint,
                data={"token": access_token},
                auth=(self.client_id, self.client_secret),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                logger.error(f"Introspection request failed: {response.status_code}")
                return None

            result = response.json()

        if not result.get("active", False):
            return None

        return TokenInfo(
            subject=result.get("sub", ""),
            email=result.get("email"),
            name=result.get("name") or result.get("username"),
            expires_at=result.get("exp"),
            scopes=result.get("scope", "").split() if result.get("scope") else None,
            raw_claims=result,
        )

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Use refresh token to get new access token."""
        config = await self.get_oidc_config()
        token_endpoint = config["token_endpoint"]

        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_endpoint,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get("error_description", response.text)
                error_code = error_data.get("error", "refresh_failed")
                logger.error(f"Token refresh failed: {error_msg}")
                raise AuthenticationError(f"Token refresh failed: {error_msg}", error_code)

            token_data = response.json()

        return TokenResponse(
            access_token=token_data["access_token"],
            token_type=token_data.get("token_type", "Bearer"),
            expires_in=token_data.get("expires_in"),
            refresh_token=token_data.get("refresh_token", refresh_token),
            id_token=token_data.get("id_token"),
            scope=token_data.get("scope"),
        )
