# u2-mcp

[![PyPI version](https://img.shields.io/pypi/v/u2-mcp.svg)](https://pypi.org/project/u2-mcp/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Registry-green.svg)](https://registry.modelcontextprotocol.io)

<!-- mcp-name: io.github.bpamiri/u2-mcp -->

**Connect Claude to your Universe/UniData database using natural language.**

u2-mcp is an MCP server that lets AI assistants like Claude query and interact with Rocket Universe and UniData MultiValue databases. Ask questions in plain English and get real answers from your data.

**The first MCP server for the Pick/MultiValue database family.**

## What Can You Do With This?

Instead of writing RetrieVe queries, just ask Claude:

| You Ask | Claude Does |
|---------|-------------|
| "How many customers are in California?" | Queries the database and tells you "1,247 customers" |
| "Show me order ORD001" | Reads the record and displays all fields |
| "What files are available?" | Lists all files in your account |
| "Describe the CUSTOMERS file" | Shows field definitions from the dictionary |

## How It Works

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Claude Desktop │◄───►│     u2-mcp      │◄───►│ Universe/UniData│
│  (You ask here) │     │  (Translates)   │     │   (Your data)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

1. You ask Claude a question about your database
2. Claude calls u2-mcp with the appropriate tool
3. u2-mcp queries your Universe/UniData server
4. Results come back through Claude in a readable format

**New to MCP?** See [What is MCP?](docs/what-is-mcp.md) for a complete explanation.

## Features

- **Connection Management** - Connect to Universe/UniData servers with connection pooling and SSL support
- **File Operations** - Read, write, and delete records while preserving MultiValue semantics
- **Query Execution** - Run RetrieVe/UniQuery statements with safety controls
- **Dictionary Access** - Explore file structures and field definitions
- **BASIC Subroutine Calls** - Execute cataloged BASIC programs
- **Transaction Support** - Full transaction management with commit/rollback
- **AI-Optimized** - Built-in query examples and syntax help for better LLM interactions

## Installation

```bash
pip install u2-mcp
```

Or using `uvx` for isolated execution:

```bash
uvx u2-mcp
```

## Quick Start

### Prerequisites

- Python 3.10+
- Access to a Rocket Universe or UniData server
- The `uopy` package (installed automatically as a dependency)

### Configuration

Set environment variables for your database connection:

```bash
export U2_HOST=server.example.com
export U2_USER=username
export U2_PASSWORD=password
export U2_ACCOUNT=MYACCOUNT
export U2_SERVICE=uvcs  # or 'udcs' for UniData
```

### Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "u2": {
      "command": "uvx",
      "args": ["u2-mcp"],
      "env": {
        "U2_HOST": "server.example.com",
        "U2_USER": "user",
        "U2_PASSWORD": "password",
        "U2_ACCOUNT": "MYACCOUNT"
      }
    }
  }
}
```

## Usage Examples

Once connected, you can use natural language to interact with your Universe database:

- "List all customers in California"
- "Read record CUST001 from the CUSTOMERS file"
- "Show me the dictionary for the ORDERS file"
- "Count all open invoices over $1000"

## Available Tools

### Connection Management
- `connect` - Establish connection to Universe/UniData server
- `disconnect` - Close connections
- `list_connections` - Show active connections

### File Operations
- `list_files` - List available files in the account
- `read_record` - Read a single record by ID
- `read_records` - Read multiple records
- `write_record` - Write/update a record
- `delete_record` - Delete a record
- `get_file_info` - Get file statistics

### Query Execution
- `execute_query` - Run RetrieVe/UniQuery statements
- `execute_tcl` - Run TCL/ECL commands
- `get_select_list` - Execute SELECT and return record IDs

### Dictionary Access
- `list_dictionary` - List dictionary items
- `get_field_definition` - Get field details
- `describe_file` - High-level file description

### Advanced Features
- `call_subroutine` - Call BASIC subroutines
- `begin_transaction` / `commit_transaction` / `rollback_transaction` - Transaction management

### Knowledge Persistence
- `save_knowledge` - Save learned information about the database
- `list_knowledge` - List all saved knowledge topics
- `get_knowledge_topic` - Retrieve specific topic
- `search_knowledge` - Search across saved knowledge
- `delete_knowledge` - Remove a knowledge topic

## Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `U2_HOST` | Server hostname or IP | Required |
| `U2_USER` | Username | Required |
| `U2_PASSWORD` | Password | Required |
| `U2_ACCOUNT` | Account name | Required |
| `U2_SERVICE` | Service type (`uvcs` or `udcs`) | `uvcs` |
| `U2_PORT` | Server port | `31438` |
| `U2_SSL` | Enable SSL | `false` |
| `U2_TIMEOUT` | Connection timeout (seconds) | `30` |
| `U2_READ_ONLY` | Disable write operations | `false` |
| `U2_MAX_RECORDS` | Maximum SELECT results | `10000` |
| `U2_BLOCKED_COMMANDS` | Comma-separated blocked TCL commands | `DELETE.FILE,CLEAR.FILE` |
| `U2_KNOWLEDGE_PATH` | Custom path for knowledge file | `~/.u2-mcp/knowledge.md` |

## Knowledge Persistence

The MCP server includes a knowledge persistence feature that allows Claude to save and recall learned information about your database across sessions. This eliminates repetitive discovery work and speeds up future interactions.

### How It Works

When Claude discovers useful information about your database (file purposes, field meanings, working queries), it can save this knowledge using the `save_knowledge` tool. This information is stored in a markdown file and automatically available in future conversations via the `u2://knowledge` resource.

### What Gets Saved

- **File descriptions** - What each file contains (e.g., "AR-CUST is the customer master file")
- **Field mappings** - Which fields contain what data (e.g., "Field 1 is customer name")
- **Query patterns** - Queries that produced good results
- **Data formats** - Date formats, code meanings, conversion notes
- **Relationships** - How files relate to each other

### Storage Location

Knowledge is stored in `~/.u2-mcp/knowledge.md` by default. You can customize this location using the `U2_KNOWLEDGE_PATH` environment variable:

```json
{
  "env": {
    "U2_KNOWLEDGE_PATH": "/path/to/custom/knowledge.md"
  }
}
```

### Example Usage

After Claude discovers that `AR-CUST` contains customer records:

```
Claude: I found that AR-CUST is the customer master file. Let me save this for future reference.
[Calls save_knowledge("AR-CUST file", "Customer master file. Key is customer number. Field 1=name, Field 2=address...")]
```

In the next conversation, Claude will already know this and won't need to rediscover it.

## Centralized Deployment (HTTP/SSE Mode)

For team environments, you can run u2-mcp as a centralized HTTP server instead of local stdio mode. This allows:

- Single database connection for the whole team
- Shared knowledge base
- Centralized credential management
- Access from any MCP-compatible client

### Running the HTTP Server

```bash
# Basic HTTP server on default port 8080
u2-mcp --http

# Custom host and port
u2-mcp --http --host 0.0.0.0 --port 3000

# Or using environment variables
export U2_HTTP_HOST=0.0.0.0
export U2_HTTP_PORT=3000
u2-mcp --http
```

### Docker Deployment

```dockerfile
FROM python:3.12-slim

RUN pip install u2-mcp

ENV U2_HOST=your-universe-server
ENV U2_USER=username
ENV U2_PASSWORD=password
ENV U2_ACCOUNT=MYACCOUNT
ENV U2_HTTP_PORT=8080

EXPOSE 8080

CMD ["u2-mcp", "--http"]
```

```bash
docker build -t u2-mcp-server .
docker run -p 8080:8080 u2-mcp-server
```

### HTTP Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `U2_HTTP_HOST` | Host to bind HTTP server to | `0.0.0.0` |
| `U2_HTTP_PORT` | Port for HTTP server | `8080` |
| `U2_HTTP_CORS_ORIGINS` | Allowed CORS origins (comma-separated or `*`) | `*` |

### Connecting Clients

The HTTP server exposes an SSE (Server-Sent Events) endpoint at `/sse`. MCP clients that support remote servers can connect to:

```
http://your-server:8080/sse
```

**Note:** As of late 2024, Claude Desktop only supports local stdio MCP servers. HTTP/SSE mode is for:
- Custom MCP clients
- Future Claude Desktop versions with remote server support
- Integration with other AI tools that support MCP over HTTP

## Claude.ai Integration (Streamable HTTP + OAuth)

Deploy u2-mcp as a Custom Connector in Claude.ai with enterprise authentication via your identity provider (Duo, Auth0, Okta, etc.).

### Quick Setup

1. **Deploy u2-mcp** with OAuth enabled:

```bash
u2-mcp --streamable-http --host 0.0.0.0 --port 8080
```

2. **Configure OAuth** in your `.env`:

```bash
U2_AUTH_ENABLED=true
U2_AUTH_ISSUER_URL=https://u2-mcp.example.com
U2_IDP_PROVIDER=duo
U2_IDP_DISCOVERY_URL=https://sso-xxx.sso.duosecurity.com/oidc/CLIENT_ID/.well-known/openid-configuration
U2_IDP_CLIENT_ID=your_client_id
U2_IDP_CLIENT_SECRET=your_client_secret
```

3. **Add to Claude.ai**: Go to Settings → Connectors → Add Custom Connector → Enter your URL

Users authenticate through your IdP and can then query your database directly from Claude.ai.

### Supported Identity Providers

- **Cisco Duo** - Enterprise MFA and SSO
- **Auth0** - Flexible identity platform
- **Any OIDC Provider** - Okta, Azure AD, Google Workspace, Keycloak, etc.

See the [OAuth Guide](docs/oauth.md) for detailed setup instructions.

## Security

- Credentials are never logged
- Configurable command blocklist prevents dangerous operations
- Optional read-only mode for safe exploration
- Honors Universe's built-in security model

See [SECURITY.md](SECURITY.md) for reporting security vulnerabilities.

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Documentation

### Getting Started
- [Quickstart Guide](docs/quickstart.md) - Get running in 10 minutes
- [What is MCP?](docs/what-is-mcp.md) - Understanding MCP and how u2-mcp works
- [Installation Guide](docs/installation.md) - Detailed installation instructions

### Reference
- [Configuration Reference](docs/configuration.md) - All environment variables
- [Tools Reference](docs/tools.md) - Complete tool documentation
- [Usage Examples](docs/examples.md) - Common usage patterns
- [OAuth & Claude.ai Integration](docs/oauth.md) - Deploy as a Claude.ai Custom Connector

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Rocket Software](https://www.rocketsoftware.com/) for the `uopy` package
- [Anthropic](https://www.anthropic.com/) for the Model Context Protocol specification
- The MultiValue database community
