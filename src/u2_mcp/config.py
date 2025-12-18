"""Configuration management for u2-mcp using pydantic-settings."""

from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings


class U2Config(BaseSettings):
    """Configuration for U2 MCP Server, loaded from environment variables.

    Required environment variables:
        U2_HOST: Universe/UniData server hostname
        U2_USER: Username for authentication
        U2_PASSWORD: Password for authentication
        U2_ACCOUNT: Account name to connect to

    Optional environment variables:
        U2_SERVICE: Service type (uvcs for Universe, udcs for UniData)
        U2_PORT: Server port
        U2_SSL: Enable SSL/TLS
        U2_TIMEOUT: Connection timeout in seconds
        U2_READ_ONLY: Disable write operations
        U2_MAX_RECORDS: Maximum SELECT results
        U2_BLOCKED_COMMANDS: Comma-separated list of blocked TCL commands
    """

    # Required connection settings
    host: str = Field(
        ...,
        alias="U2_HOST",
        description="Universe/UniData server hostname",
    )
    user: str = Field(
        ...,
        alias="U2_USER",
        description="Username for authentication",
    )
    password: str = Field(
        ...,
        alias="U2_PASSWORD",
        description="Password for authentication",
    )
    account: str = Field(
        ...,
        alias="U2_ACCOUNT",
        description="Account name to connect to",
    )

    # Optional connection settings
    service: str = Field(
        default="uvcs",
        alias="U2_SERVICE",
        description="Service type: uvcs (Universe) or udcs (UniData)",
    )
    port: int = Field(
        default=31438,
        alias="U2_PORT",
        description="Server port",
    )
    ssl: bool = Field(
        default=False,
        alias="U2_SSL",
        description="Enable SSL/TLS",
    )
    timeout: int = Field(
        default=30,
        alias="U2_TIMEOUT",
        description="Connection timeout in seconds",
    )

    # Safety settings
    read_only: bool = Field(
        default=False,
        alias="U2_READ_ONLY",
        description="Disable write operations",
    )
    max_records: int = Field(
        default=10000,
        alias="U2_MAX_RECORDS",
        description="Maximum SELECT results",
    )
    # Store as string to avoid pydantic-settings JSON parsing issues
    blocked_commands_str: str = Field(
        default="DELETE.FILE,CLEAR.FILE,CNAME,CREATE.FILE",
        alias="U2_BLOCKED_COMMANDS",
        description="Comma-separated list of blocked TCL commands",
    )

    # HTTP Server settings (for centralized deployment)
    http_host: str = Field(
        default="0.0.0.0",
        alias="U2_HTTP_HOST",
        description="Host to bind HTTP server to",
    )
    http_port: int = Field(
        default=8080,
        alias="U2_HTTP_PORT",
        description="Port for HTTP server",
    )
    http_cors_origins_str: str = Field(
        default="*",
        alias="U2_HTTP_CORS_ORIGINS",
        description="Comma-separated list of allowed CORS origins, or * for all",
    )

    # OAuth/Authentication settings (for Claude.ai Integrations)
    auth_enabled: bool = Field(
        default=False,
        alias="U2_AUTH_ENABLED",
        description="Enable OAuth authentication for Streamable HTTP endpoint",
    )
    auth_issuer_url: str | None = Field(
        default=None,
        alias="U2_AUTH_ISSUER_URL",
        description="OAuth issuer URL (this server's public URL, e.g., https://u2-mcp.example.com)",
    )

    # External Identity Provider settings
    idp_provider: str = Field(
        default="oidc",
        alias="U2_IDP_PROVIDER",
        description="Identity provider type: 'duo', 'auth0', or 'oidc'",
    )
    idp_discovery_url: str | None = Field(
        default=None,
        alias="U2_IDP_DISCOVERY_URL",
        description="OIDC discovery URL (.well-known/openid-configuration)",
    )
    idp_client_id: str | None = Field(
        default=None,
        alias="U2_IDP_CLIENT_ID",
        description="Client ID for external identity provider",
    )
    idp_client_secret: str | None = Field(
        default=None,
        alias="U2_IDP_CLIENT_SECRET",
        description="Client secret for external identity provider",
    )
    idp_scopes: str = Field(
        default="openid profile email",
        alias="U2_IDP_SCOPES",
        description="Scopes to request from external IdP (space-separated)",
    )

    # Duo-specific settings
    duo_api_host: str | None = Field(
        default=None,
        alias="U2_DUO_API_HOST",
        description="Duo API hostname (e.g., api-XXXXXXXX.duosecurity.com)",
    )

    # Token settings
    token_expiry_seconds: int = Field(
        default=3600,
        alias="U2_TOKEN_EXPIRY_SECONDS",
        description="Access token expiry time in seconds",
    )
    refresh_token_expiry_seconds: int = Field(
        default=2592000,  # 30 days
        alias="U2_REFRESH_TOKEN_EXPIRY_SECONDS",
        description="Refresh token expiry time in seconds",
    )

    # Connection watchdog settings
    watchdog_enabled: bool = Field(
        default=True,
        alias="U2_WATCHDOG_ENABLED",
        description="Enable connection health monitoring watchdog",
    )
    watchdog_interval: int = Field(
        default=30,
        alias="U2_WATCHDOG_INTERVAL",
        description="Watchdog check interval in seconds",
    )
    watchdog_timeout: int = Field(
        default=10,
        alias="U2_WATCHDOG_TIMEOUT",
        description="Timeout for health check operations in seconds",
    )
    watchdog_max_failures: int = Field(
        default=3,
        alias="U2_WATCHDOG_MAX_FAILURES",
        description="Max consecutive failures before forcing reconnect",
    )

    # Audit logging settings
    audit_enabled: bool = Field(
        default=False,
        alias="U2_AUDIT_ENABLED",
        description="Enable audit logging of all MCP tool calls",
    )
    audit_path: str = Field(
        default="/var/log/u2-mcp/audit",
        alias="U2_AUDIT_PATH",
        description="Directory path for audit log files",
    )
    audit_include_results: bool = Field(
        default=True,
        alias="U2_AUDIT_INCLUDE_RESULTS",
        description="Include tool results in audit logs (may contain sensitive data)",
    )
    audit_max_result_size: int = Field(
        default=10000,
        alias="U2_AUDIT_MAX_RESULT_SIZE",
        description="Maximum characters to log for tool results (truncates if larger)",
    )

    @computed_field  # type: ignore[prop-decorator]  # pydantic pattern
    @property
    def blocked_commands(self) -> list[str]:
        """Parse comma-separated string into list of commands."""
        return [cmd.strip().upper() for cmd in self.blocked_commands_str.split(",") if cmd.strip()]

    @computed_field  # type: ignore[prop-decorator]  # pydantic pattern
    @property
    def http_cors_origins(self) -> list[str]:
        """Parse comma-separated CORS origins into list."""
        origins = self.http_cors_origins_str.strip()
        if origins == "*":
            return ["*"]
        return [o.strip() for o in origins.split(",") if o.strip()]

    @field_validator("service")
    @classmethod
    def validate_service(cls, v: str) -> str:
        """Validate service type is uvcs or udcs."""
        v_lower = v.lower()
        if v_lower not in ("uvcs", "udcs"):
            raise ValueError("service must be 'uvcs' (Universe) or 'udcs' (UniData)")
        return v_lower

    model_config = {
        "env_prefix": "",
        "case_sensitive": False,
        "populate_by_name": True,
    }
