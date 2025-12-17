# Installation Guide

This guide covers installing u2-mcp and configuring it to work with Claude Desktop.

**New to MCP?** Start with [What is MCP?](what-is-mcp.md) to understand how this all works.

**Want the fastest path?** See the [Quickstart Guide](quickstart.md) for a 10-minute setup.

## What Gets Installed

When you install u2-mcp, you get:

- **u2-mcp** - The MCP server that connects Claude to Universe/UniData
- **uopy** - Rocket Software's Python package for U2 database connectivity
- **FastMCP** - The framework for building MCP servers
- **Supporting libraries** - pydantic-settings, starlette (for HTTP mode)

The installation is about 50MB total.

## Prerequisites

Before installing, you need:

| Requirement | Why You Need It | How to Get It |
|-------------|-----------------|---------------|
| **Python 3.10+** | Runs the MCP server | [python.org/downloads](https://www.python.org/downloads/) |
| **Claude Desktop** | The AI assistant that uses MCP | [claude.ai/download](https://claude.ai/download) |
| **Universe/UniData access** | The database you're connecting to | Contact your DBA |

### Checking Python Version

```bash
python --version
# Should show Python 3.10.x or higher
```

If you see Python 2.x or an older 3.x version, install a newer Python first.

## Installation Methods

### Method 1: pip (Recommended)

```bash
pip install u2-mcp
```

### Method 2: uvx (Isolated Execution)

```bash
uvx u2-mcp
```

This runs u2-mcp in an isolated environment without permanent installation.

### Method 3: From Source

```bash
git clone https://github.com/bpamiri/u2-mcp.git
cd u2-mcp
pip install -e .
```

## Claude Desktop Setup

Claude Desktop needs to know about u2-mcp so it can start it and communicate with it. This is done through a JSON configuration file.

### Understanding the Config File

The config file tells Claude Desktop:
- **Where to find u2-mcp** (the `command` field)
- **How to connect to your database** (the `env` field with credentials)
- **What to call this server** (the key name, like "u2-mcp")

When Claude Desktop starts, it reads this config and launches u2-mcp in the background.

### 1. Locate the Config File

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

### 2. Add u2-mcp Configuration

Create or edit the config file. Here's what each part means:

```json
{
  "mcpServers": {
    "u2-mcp": {
      "command": "uvx",
      "args": ["u2-mcp"],
      "env": {
        "U2_HOST": "your-server.example.com",
        "U2_USER": "username",
        "U2_PASSWORD": "password",
        "U2_ACCOUNT": "ACCOUNTNAME",
        "U2_SERVICE": "uvcs"
      }
    }
  }
}
```

**Config breakdown:**

| Field | Purpose | Example |
|-------|---------|---------|
| `"u2-mcp"` | Name for this server (you choose) | `"u2-mcp"` or `"production-db"` |
| `command` | Program to run | `"uvx"` or `"u2-mcp"` |
| `args` | Command arguments | `["u2-mcp"]` for uvx |
| `U2_HOST` | Database server hostname | `"universe.company.com"` |
| `U2_USER` | Database username | `"appuser"` |
| `U2_PASSWORD` | Database password | `"secretpassword"` |
| `U2_ACCOUNT` | Account to connect to | `"PRODUCTION"` |
| `U2_SERVICE` | `uvcs` for Universe, `udcs` for UniData | `"uvcs"` |

### 3. Alternative: Using pip Installation

If you installed via pip:

```json
{
  "mcpServers": {
    "u2-mcp": {
      "command": "u2-mcp",
      "env": {
        "U2_HOST": "your-server.example.com",
        "U2_USER": "username",
        "U2_PASSWORD": "password",
        "U2_ACCOUNT": "ACCOUNTNAME"
      }
    }
  }
}
```

### 4. Alternative: From Source with Virtual Environment

If running from source:

```json
{
  "mcpServers": {
    "u2-mcp": {
      "command": "/bin/bash",
      "args": ["-c", "cd /path/to/u2-mcp && .venv/bin/python -m u2_mcp"],
      "env": {
        "U2_HOST": "your-server.example.com",
        "U2_USER": "username",
        "U2_PASSWORD": "password",
        "U2_ACCOUNT": "ACCOUNTNAME"
      }
    }
  }
}
```

### 5. Restart Claude Desktop

Quit Claude Desktop completely (Cmd+Q on macOS) and reopen it.

### 6. Verify Installation

In Claude Desktop, you should see a hammer icon indicating tools are available. Try asking:

> "Connect to the database and list available files"

## macOS-Specific Notes

### TCP_KEEPIDLE Issue

The `uopy` package may encounter a `TCP_KEEPIDLE` error on macOS. This is handled automatically by u2-mcp, but if you see this error with other U2 Python code, add this workaround:

```python
import socket
if not hasattr(socket, "TCP_KEEPIDLE"):
    socket.TCP_KEEPIDLE = socket.TCP_KEEPALIVE
```

### uopy Logs Directory

The `uopy` package creates a `./logs` directory in the current working directory. The Claude Desktop config should set a working directory where this is allowed, or use the bash wrapper approach shown above.

## Troubleshooting

### "Module not found" Error

Ensure u2-mcp is installed in the Python environment being used:

```bash
pip show u2-mcp
```

### Connection Refused

1. Verify your Universe/UniData server is running
2. Check the hostname and port are correct
3. Ensure the service (uvcs/udcs) matches your server type
4. Verify credentials are correct

### "Invalid character" in Output

This was fixed in version 0.1.0. Update to the latest version:

```bash
pip install --upgrade u2-mcp
```

### Check MCP Logs

Claude Desktop logs MCP server output to:

```
~/Library/Logs/Claude/mcp-server-u2-mcp.log
```

Review this file for detailed error messages.

## Next Steps

Now that you're installed:

1. **Test the connection** - Ask Claude "Connect to the database and show me the current user"
2. **Explore your data** - Ask "What files are available in this account?"
3. **Learn more:**
   - [Usage Examples](examples.md) - Common usage patterns
   - [Configuration Reference](configuration.md) - All environment variables
   - [Tools Reference](tools.md) - Available MCP tools
   - [What is MCP?](what-is-mcp.md) - Understanding how it all works
