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

## HTTP Server Settings

Used when running in HTTP/SSE mode (`--http` flag):

| Variable | Description | Default |
|----------|-------------|---------|
| `U2_HTTP_HOST` | Host to bind HTTP server to | `0.0.0.0` |
| `U2_HTTP_PORT` | Port for HTTP server | `8080` |
| `U2_HTTP_CORS_ORIGINS` | Allowed CORS origins (comma-separated or `*`) | `*` |

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
