# Configuration Reference

All configuration is done via environment variables. These can be set in your shell, in the Claude Desktop config, or in a `.env` file.

## Required Settings

These must be set for the server to connect:

| Variable | Description | Example |
|----------|-------------|---------|
| `U2_HOST` | Universe/UniData server hostname or IP | `server.example.com` |
| `U2_USER` | Username for authentication | `myuser` |
| `U2_PASSWORD` | Password for authentication | `mypassword` |
| `U2_ACCOUNT` | Account name to connect to | `PRODUCTION` |

## Connection Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `U2_SERVICE` | Service type: `uvcs` (Universe) or `udcs` (UniData) | `uvcs` |
| `U2_PORT` | Server port | `31438` |
| `U2_SSL` | Enable SSL/TLS connection | `false` |
| `U2_TIMEOUT` | Connection timeout in seconds | `30` |

## Safety Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `U2_READ_ONLY` | Disable all write operations | `false` |
| `U2_MAX_RECORDS` | Maximum records returned by SELECT/LIST | `10000` |
| `U2_BLOCKED_COMMANDS` | Comma-separated TCL commands to block | `DELETE.FILE,CLEAR.FILE,CNAME,CREATE.FILE` |

## Knowledge Persistence

| Variable | Description | Default |
|----------|-------------|---------|
| `U2_KNOWLEDGE_PATH` | Path to knowledge file | `~/.u2-mcp/knowledge.md` |

## Audit Logging

Enable audit logging to capture all MCP tool calls for analysis and debugging. This is useful for:
- Analyzing Claude.ai session patterns and queries
- Identifying bugs or improvement opportunities
- Understanding database usage patterns
- Debugging integration issues

### Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `U2_AUDIT_ENABLED` | Enable audit logging | `false` |
| `U2_AUDIT_PATH` | Directory for audit log files | `/var/log/u2-mcp/audit` |
| `U2_AUDIT_INCLUDE_RESULTS` | Include tool results in logs | `true` |
| `U2_AUDIT_MAX_RESULT_SIZE` | Max characters for results (truncates if larger) | `10000` |

### Log Format

Audit logs are written as JSONL (JSON Lines) files, one per day (`audit-YYYY-MM-DD.jsonl`). Each line is a JSON object with the following fields:

| Field | Description |
|-------|-------------|
| `event` | Event type: `session_start`, `tool_call`, `session_end`, `error` |
| `timestamp` | ISO 8601 format timestamp |
| `session_id` | Unique session identifier |
| `tool` | Tool name (for `tool_call` events) |
| `parameters` | Tool parameters (sensitive values redacted) |
| `result` | Tool result (if `include_results` is enabled) |
| `duration_ms` | Execution time in milliseconds |
| `status` | `success` or `error` |
| `error` | Error message (if status is `error`) |

### Example Log Entries

**Session Start:**
```json
{"event": "session_start", "session_id": "20251217-224748-670325", "timestamp": "2025-12-17T22:47:48.670325"}
```

**Tool Call:**
```json
{"event": "tool_call", "timestamp": "2025-12-17T22:48:15.123456", "session_id": "20251217-224748-670325", "tool": "execute_query", "parameters": {"query": "LIST CUSTOMERS SAMPLE 10"}, "duration_ms": 45.23, "status": "success", "result": {"query": "LIST CUSTOMERS SAMPLE 10", "output": "...", "status": "success"}}
```

**Error:**
```json
{"event": "tool_call", "timestamp": "2025-12-17T22:49:00.000000", "session_id": "20251217-224748-670325", "tool": "read_record", "parameters": {"file_name": "CUSTOMERS", "record_id": "INVALID"}, "duration_ms": 12.5, "status": "error", "error": "Record not found"}
```

### Security

- Sensitive parameters (containing `password`, `secret`, `token`, `key`, `credential`) are automatically redacted
- Large results are truncated to `U2_AUDIT_MAX_RESULT_SIZE` to prevent huge log files
- Log files are owned by the u2mcp service user

### Setup

1. Create the audit directory:
   ```bash
   mkdir -p /var/log/u2-mcp/audit
   chown -R u2mcp:u2mcp /var/log/u2-mcp
   ```

2. If using systemd with `ProtectSystem=strict`, add the audit path to `ReadWritePaths`:
   ```ini
   ReadWritePaths=/var/log/u2-mcp/audit
   ```

3. Add to your `.env`:
   ```bash
   U2_AUDIT_ENABLED=true
   U2_AUDIT_PATH=/var/log/u2-mcp/audit
   ```

4. Restart the service:
   ```bash
   systemctl restart u2-mcp
   ```

### Analyzing Logs

Logs can be analyzed using standard tools:

```bash
# View today's log
cat /var/log/u2-mcp/audit/audit-$(date +%Y-%m-%d).jsonl

# Count tool calls by type
cat audit-*.jsonl | jq -r 'select(.event=="tool_call") | .tool' | sort | uniq -c | sort -rn

# Find slow queries (>1 second)
cat audit-*.jsonl | jq 'select(.event=="tool_call" and .duration_ms > 1000)'

# Find errors
cat audit-*.jsonl | jq 'select(.status=="error")'

# Export to CSV for analysis
cat audit-*.jsonl | jq -r 'select(.event=="tool_call") | [.timestamp, .tool, .duration_ms, .status] | @csv'
```

You can also feed the logs to Claude Code for analysis to identify patterns, bugs, or improvement opportunities in the u2-mcp codebase

## HTTP Server Settings

Used when running in HTTP/SSE mode (`--http` flag) or Streamable HTTP mode (`--streamable-http` flag):

| Variable | Description | Default |
|----------|-------------|---------|
| `U2_HTTP_HOST` | Host to bind HTTP server to | `0.0.0.0` |
| `U2_HTTP_PORT` | Port for HTTP server | `8080` |
| `U2_HTTP_CORS_ORIGINS` | Allowed CORS origins (comma-separated or `*`) | `*` |

## OAuth / Claude.ai Integration Settings

Used when deploying as a Claude.ai Custom Connector with OAuth authentication. See [OAuth Guide](oauth.md) for detailed setup instructions.

| Variable | Description | Default |
|----------|-------------|---------|
| `U2_AUTH_ENABLED` | Enable OAuth authentication | `false` |
| `U2_AUTH_ISSUER_URL` | Public URL of this server (e.g., `https://u2-mcp.example.com`) | None |
| `U2_IDP_PROVIDER` | Identity provider type: `duo`, `auth0`, or `oidc` | `oidc` |
| `U2_IDP_DISCOVERY_URL` | OIDC discovery URL (`.well-known/openid-configuration`) | None |
| `U2_IDP_CLIENT_ID` | Client ID from your identity provider | None |
| `U2_IDP_CLIENT_SECRET` | Client secret from your identity provider | None |
| `U2_IDP_SCOPES` | Scopes to request from IdP (space-separated) | `openid profile email` |
| `U2_DUO_API_HOST` | Duo API hostname (alternative to discovery URL) | None |
| `U2_TOKEN_EXPIRY_SECONDS` | Access token lifetime in seconds | `3600` |
| `U2_REFRESH_TOKEN_EXPIRY_SECONDS` | Refresh token lifetime in seconds | `2592000` (30 days) |

## Configuration Examples

### Basic Setup

```bash
export U2_HOST=universe.example.com
export U2_USER=appuser
export U2_PASSWORD=secretpassword
export U2_ACCOUNT=MYACCOUNT
```

### Read-Only with Extended Blocking

```bash
export U2_HOST=universe.example.com
export U2_USER=readonly_user
export U2_PASSWORD=password
export U2_ACCOUNT=PRODUCTION
export U2_READ_ONLY=true
export U2_BLOCKED_COMMANDS=DELETE.FILE,CLEAR.FILE,CNAME,CREATE.FILE,ED,AE,COPY
export U2_MAX_RECORDS=1000
```

### UniData Connection

```bash
export U2_HOST=unidata.example.com
export U2_USER=uduser
export U2_PASSWORD=password
export U2_ACCOUNT=UDACCOUNT
export U2_SERVICE=udcs
```

### SSL Connection

```bash
export U2_HOST=secure-universe.example.com
export U2_USER=appuser
export U2_PASSWORD=password
export U2_ACCOUNT=SECURE
export U2_SSL=true
export U2_PORT=31439
```

### Team Shared Knowledge

```bash
export U2_HOST=universe.example.com
export U2_USER=team_user
export U2_PASSWORD=password
export U2_ACCOUNT=SHARED
export U2_KNOWLEDGE_PATH=/mnt/shared/team/u2-knowledge.md
```

### HTTP Server Deployment

```bash
export U2_HOST=universe.example.com
export U2_USER=api_user
export U2_PASSWORD=password
export U2_ACCOUNT=API
export U2_HTTP_HOST=0.0.0.0
export U2_HTTP_PORT=3000
export U2_HTTP_CORS_ORIGINS=https://app.example.com,https://admin.example.com
export U2_READ_ONLY=true
```

### Claude.ai Integration with Duo OAuth

```bash
# Database Connection
export U2_HOST=universe.example.com
export U2_USER=mcp_user
export U2_PASSWORD=password
export U2_ACCOUNT=PRODUCTION

# OAuth Configuration
export U2_AUTH_ENABLED=true
export U2_AUTH_ISSUER_URL=https://u2-mcp.example.com

# Duo Identity Provider
export U2_IDP_PROVIDER=duo
export U2_IDP_DISCOVERY_URL=https://sso-abc123.sso.duosecurity.com/oidc/YOUR_CLIENT_ID/.well-known/openid-configuration
export U2_IDP_CLIENT_ID=YOUR_CLIENT_ID
export U2_IDP_CLIENT_SECRET=YOUR_CLIENT_SECRET
export U2_IDP_SCOPES="openid profile email groups"

# CORS for Claude.ai
export U2_HTTP_CORS_ORIGINS=https://claude.ai,https://*.claude.ai
```

## Claude Desktop Config

Full example with all options:

```json
{
  "mcpServers": {
    "u2-mcp": {
      "command": "u2-mcp",
      "env": {
        "U2_HOST": "universe.example.com",
        "U2_USER": "myuser",
        "U2_PASSWORD": "mypassword",
        "U2_ACCOUNT": "MYACCOUNT",
        "U2_SERVICE": "uvcs",
        "U2_PORT": "31438",
        "U2_SSL": "false",
        "U2_TIMEOUT": "30",
        "U2_READ_ONLY": "true",
        "U2_MAX_RECORDS": "5000",
        "U2_BLOCKED_COMMANDS": "DELETE.FILE,CLEAR.FILE,CNAME,CREATE.FILE,ED",
        "U2_KNOWLEDGE_PATH": "/Users/shared/u2-knowledge.md"
      }
    }
  }
}
```

## Environment File (.env)

For local development, create a `.env` file:

```bash
# Database Connection
U2_HOST=localhost
U2_USER=devuser
U2_PASSWORD=devpassword
U2_ACCOUNT=DEV

# Safety
U2_READ_ONLY=true
U2_MAX_RECORDS=1000

# Knowledge
U2_KNOWLEDGE_PATH=./knowledge.md
```

Note: The `.env` file is loaded automatically by pydantic-settings when running from the command line, but Claude Desktop requires explicit environment variables in the config.
