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
