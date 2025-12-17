"""OAuth authentication module for u2-mcp.

This module provides OAuth 2.0 authentication support for Claude.ai Integrations,
implementing the MCP SDK's OAuthAuthorizationServerProvider protocol with support
for external identity providers (Duo, Auth0, generic OIDC).
"""

from .provider import U2OAuthProvider
from .storage import InMemoryAuthStorage

__all__ = ["U2OAuthProvider", "InMemoryAuthStorage"]
