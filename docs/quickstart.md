# Quickstart Guide

Get u2-mcp running with Claude Desktop in 10 minutes.

## What You'll Need

Before starting, make sure you have:

- [ ] **Claude Desktop** installed ([download here](https://claude.ai/download))
- [ ] **Python 3.10 or later** installed
- [ ] **Access to a Universe or UniData server** with:
  - Hostname or IP address
  - Username and password
  - Account name to connect to
  - Network access from your computer

## Step 1: Install u2-mcp

Open your terminal (Command Prompt on Windows, Terminal on Mac/Linux) and run:

```bash
pip install u2-mcp
```

To verify it installed correctly:

```bash
u2-mcp --help
```

You should see:
```
usage: u2-mcp [-h] [--http] [--host HOST] [--port PORT]

U2 MCP Server - Connect AI assistants to Universe/UniData databases
```

## Step 2: Find Your Claude Desktop Config File

Claude Desktop stores its configuration in a JSON file. Find it at:

| Operating System | Config File Location |
|------------------|---------------------|
| **macOS** | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| **Windows** | `%APPDATA%\Claude\claude_desktop_config.json` |
| **Linux** | `~/.config/Claude/claude_desktop_config.json` |

**Quick way to open on macOS:**
```bash
open ~/Library/Application\ Support/Claude/
```

**Quick way to open on Windows:**
```
explorer %APPDATA%\Claude
```

If the file doesn't exist, create it.

## Step 3: Configure Claude Desktop

Edit `claude_desktop_config.json` and add the u2-mcp configuration:

```json
{
  "mcpServers": {
    "u2": {
      "command": "u2-mcp",
      "env": {
        "U2_HOST": "your-server-hostname",
        "U2_USER": "your-username",
        "U2_PASSWORD": "your-password",
        "U2_ACCOUNT": "your-account-name",
        "U2_READ_ONLY": "true"
      }
    }
  }
}
```

**Replace the placeholder values:**

| Setting | Replace With | Example |
|---------|--------------|---------|
| `U2_HOST` | Your Universe/UniData server hostname | `universe.company.com` |
| `U2_USER` | Your database username | `appuser` |
| `U2_PASSWORD` | Your database password | `secretpassword` |
| `U2_ACCOUNT` | The account to connect to | `PRODUCTION` |

**Important:** We set `U2_READ_ONLY=true` for safety while you're learning. This prevents any accidental data changes.

### For UniData Users

If you're connecting to UniData instead of Universe, add:

```json
"U2_SERVICE": "udcs"
```

Universe uses `uvcs` (the default), UniData uses `udcs`.

## Step 4: Restart Claude Desktop

**Completely quit Claude Desktop** (not just close the window):

- **macOS:** Press Cmd+Q or right-click the dock icon and choose Quit
- **Windows:** Right-click the system tray icon and choose Exit

Then reopen Claude Desktop.

## Step 5: Verify It's Working

In Claude Desktop, you should see a **hammer icon** (🔨) in the input area, indicating tools are available.

Try asking Claude:

> "Connect to the database and tell me what account I'm connected to"

Claude should respond with your connection details:

> "I've connected to the Universe server. You're logged in as 'appuser' on the 'PRODUCTION' account on server 'universe.company.com'."

## Step 6: Start Exploring

Now you can ask Claude about your database:

### See What Files Exist
> "What files are available in this account?"

### Explore a File's Structure
> "Describe the CUSTOMERS file"

### Query Data
> "List the first 10 records from CUSTOMERS"

> "Count how many records are in ORDERS"

### Read Specific Records
> "Read record CUST001 from the CUSTOMERS file"

## Troubleshooting

### "Tool not found" or No Hammer Icon

1. Make sure you completely quit and reopened Claude Desktop
2. Check your config file for JSON syntax errors (missing commas, quotes)
3. Verify u2-mcp is installed: `u2-mcp --help`

### Connection Errors

1. **Verify your credentials** work with other Universe tools
2. **Check the hostname** is reachable from your computer
3. **Verify the service type** (uvcs for Universe, udcs for UniData)
4. **Check the port** - default is 31438, but your server may be different

### Check the Logs

Claude Desktop logs MCP server output. Check:

**macOS:**
```bash
cat ~/Library/Logs/Claude/mcp-server-u2.log
```

**Windows:**
```
%APPDATA%\Claude\Logs\mcp-server-u2.log
```

### Python Not Found

If Claude can't find Python or u2-mcp, use the full path:

```json
{
  "mcpServers": {
    "u2": {
      "command": "/usr/local/bin/u2-mcp",
      "env": { ... }
    }
  }
}
```

Find your u2-mcp path with: `which u2-mcp` (Mac/Linux) or `where u2-mcp` (Windows)

## What's Next?

Now that you're connected:

1. **Learn what Claude can do** - See [Usage Examples](examples.md)
2. **Understand the tools** - See [Tools Reference](tools.md)
3. **Configure more options** - See [Configuration Reference](configuration.md)
4. **Learn how it works** - See [What is MCP?](what-is-mcp.md)

## Quick Reference

### Common Questions to Ask Claude

| What You Want | Ask Claude |
|---------------|------------|
| List files | "What files are in this account?" |
| File structure | "Describe the ORDERS file" |
| Query data | "List customers in California" |
| Read record | "Read record ABC123 from PRODUCTS" |
| Count records | "How many open invoices are there?" |
| Field info | "What does field 5 in CUSTOMERS contain?" |

### Configuration Cheat Sheet

```json
{
  "mcpServers": {
    "u2": {
      "command": "u2-mcp",
      "env": {
        "U2_HOST": "server.example.com",
        "U2_USER": "username",
        "U2_PASSWORD": "password",
        "U2_ACCOUNT": "ACCOUNTNAME",
        "U2_SERVICE": "uvcs",
        "U2_READ_ONLY": "true",
        "U2_MAX_RECORDS": "1000"
      }
    }
  }
}
```

| Variable | Required | Description |
|----------|----------|-------------|
| `U2_HOST` | Yes | Server hostname |
| `U2_USER` | Yes | Username |
| `U2_PASSWORD` | Yes | Password |
| `U2_ACCOUNT` | Yes | Account name |
| `U2_SERVICE` | No | `uvcs` (Universe) or `udcs` (UniData) |
| `U2_READ_ONLY` | No | Set to `true` to prevent writes |
| `U2_MAX_RECORDS` | No | Limit query results (default: 10000) |
