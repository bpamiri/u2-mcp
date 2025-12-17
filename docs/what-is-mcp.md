# Understanding MCP and u2-mcp

This guide explains what MCP is, how it works, and how u2-mcp connects your Universe/UniData database to AI assistants like Claude.

## What is MCP?

**MCP (Model Context Protocol)** is an open standard created by Anthropic that allows AI assistants to connect to external tools and data sources. Think of it as a "plugin system" for AI.

### The Problem MCP Solves

Without MCP, AI assistants like Claude can only:
- Answer questions from their training data
- Help with text in the conversation
- Have no access to your specific systems or data

With MCP, AI assistants can:
- Connect to your databases and query real data
- Read and write files on your system
- Call APIs and web services
- Execute commands and run programs
- Remember information across conversations

### How MCP Works

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Claude Desktop │◄───►│   MCP Server    │◄───►│   Your System   │
│  (AI Assistant) │     │   (u2-mcp)      │     │   (Universe DB) │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
     You talk to             Translates            Your actual
     Claude here             requests              data lives here
```

1. **You** ask Claude a question like "Show me all customers in California"
2. **Claude** recognizes it needs database access and calls the MCP server
3. **The MCP server (u2-mcp)** translates this into a Universe query
4. **Universe** returns the data
5. **u2-mcp** formats the results and sends them back to Claude
6. **Claude** presents the information to you in a readable format

### MCP Components

| Component | What It Is | Example |
|-----------|------------|---------|
| **MCP Host** | The AI application that uses MCP | Claude Desktop, Claude Code |
| **MCP Server** | A program that provides tools/data | u2-mcp (this project) |
| **Tools** | Actions the AI can perform | `read_record`, `execute_query` |
| **Resources** | Data the AI can access | Database knowledge, syntax help |

## What is u2-mcp?

**u2-mcp** is an MCP server specifically for Rocket Universe and UniData databases (part of the Pick/MultiValue database family).

It allows Claude to:
- Query your Universe/UniData database using natural language
- Read and write records
- Explore file structures and dictionaries
- Call BASIC subroutines
- Learn and remember information about your database

### Why Use u2-mcp?

**Without u2-mcp:**
> You: "How many customers do we have in California?"
> Claude: "I don't have access to your database. You would need to run a query like `LIST CUSTOMERS WITH STATE = "CA"`..."

**With u2-mcp:**
> You: "How many customers do we have in California?"
> Claude: "You have 1,247 customers in California. The largest by revenue is Acme Corp (CUST001)."

Claude can actually connect to your database, run the query, and give you real answers.

## Where Does u2-mcp Run?

u2-mcp runs as a **local process** on your computer, alongside Claude Desktop.

### Local Mode (Default)

```
Your Computer
┌────────────────────────────────────────────────┐
│                                                │
│  ┌──────────────┐      ┌──────────────┐       │
│  │    Claude    │      │    u2-mcp    │       │
│  │   Desktop    │◄────►│   (local)    │       │
│  └──────────────┘      └──────┬───────┘       │
│                               │               │
└───────────────────────────────┼───────────────┘
                                │
                                ▼
                    ┌──────────────────────┐
                    │   Universe/UniData   │
                    │       Server         │
                    └──────────────────────┘
                    (Can be local or remote)
```

- u2-mcp runs on your machine
- Credentials stay on your machine
- Connection goes directly to your database server
- Only you can access this instance

### Centralized Mode (Team Deployment)

For teams, u2-mcp can run as an HTTP server:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ User 1's Claude │     │                 │     │                 │
│     Desktop     │────►│                 │     │                 │
├─────────────────┤     │    u2-mcp       │     │    Universe     │
│ User 2's Claude │────►│  HTTP Server    │────►│     Server      │
│     Desktop     │     │                 │     │                 │
├─────────────────┤     │                 │     │                 │
│ User 3's Claude │────►│                 │     │                 │
│     Desktop     │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

- Single u2-mcp instance serves multiple users
- Shared knowledge base
- Centralized credential management

## How Claude Uses u2-mcp

When you install u2-mcp and configure Claude Desktop, Claude gains new abilities called **tools**. Here's what happens:

### 1. Tool Discovery

When Claude Desktop starts, it discovers what tools u2-mcp provides:
- `connect` - Connect to the database
- `execute_query` - Run RetrieVe queries
- `read_record` - Read database records
- `describe_file` - Explore file structure
- ...and 27 more tools

### 2. Natural Language Understanding

When you ask a question, Claude decides which tools to use:

> You: "What fields are in the CUSTOMERS file?"

Claude thinks: "The user wants to know about file structure. I should use the `describe_file` tool."

### 3. Tool Execution

Claude calls the tool with appropriate parameters:
```
describe_file(file_name="CUSTOMERS")
```

### 4. Response Formatting

Claude receives the raw data and presents it clearly:

> Claude: "The CUSTOMERS file has 12 fields:
> - NAME (field 1) - Customer name
> - ADDRESS (field 2) - Street address
> - PHONE (field 5) - Phone numbers (can have multiple)
> ..."

## The MultiValue Difference

Universe and UniData are **MultiValue databases**, which work differently from SQL databases:

| Concept | SQL Database | Universe/UniData |
|---------|--------------|------------------|
| Table | `customers` table | `CUSTOMERS` file |
| Row | Record with fixed columns | Record with dynamic fields |
| Column | Fixed field | Attribute (can have multiple values) |
| Query Language | SQL | RetrieVe / UniQuery |
| Schema | Strict, predefined | Flexible, in dictionary |

### MultiValue Data Structure

A customer record might look like:

```
Record ID: CUST001
Field 1: Acme Corporation          (single value)
Field 2: 123 Main St              (single value)
Field 5: 555-1234]555-5678]555-9999  (multiple values - 3 phone numbers)
```

u2-mcp preserves this structure when reading data:
```json
{
  "id": "CUST001",
  "fields": {
    "1": "Acme Corporation",
    "2": "123 Main St",
    "5": ["555-1234", "555-5678", "555-9999"]
  }
}
```

## Security Considerations

### What u2-mcp Can Access

u2-mcp connects to your database with the credentials you provide. It can:
- Read any file the user account can read
- Write to files (unless read-only mode is enabled)
- Execute TCL commands (with safety restrictions)
- Call BASIC subroutines

### Built-in Safety Features

- **Read-only mode** - Prevents all write operations
- **Command blocking** - Dangerous commands like `DELETE.FILE` are blocked
- **Query validation** - Only safe query commands are allowed
- **Confirmation required** - Write and delete operations require explicit confirmation
- **Result limiting** - Large queries are automatically limited

### Best Practices

1. **Use read-only mode** when exploring or for most users
2. **Create a dedicated database user** with minimal permissions
3. **Review the blocked commands** and add more if needed
4. **Keep credentials secure** - never commit them to source control

## Common Questions

### Do I need to learn RetrieVe/UniQuery?

No! That's the point of u2-mcp. You can ask questions in plain English:
- "Show me all open orders" instead of `LIST ORDERS WITH STATUS = "OPEN"`
- "Count customers by state" instead of `LIST CUSTOMERS BY STATE BREAK.ON STATE`

Claude will generate the appropriate queries.

### Does Claude understand my specific database?

Initially, no. But u2-mcp has a **knowledge persistence** feature. As Claude explores your database, it can save what it learns:
- "AR-CUST is the customer master file"
- "Field 5 contains phone numbers"
- "Status codes: O=Open, C=Closed"

This knowledge persists across sessions, so Claude gets smarter over time.

### Can multiple people use the same u2-mcp?

Yes, with HTTP mode. One u2-mcp server can serve multiple Claude Desktop users, and they can share a common knowledge base.

### Is my data sent to Anthropic?

Your database queries and results pass through Claude (Anthropic's AI), similar to if you typed the data into a chat. Review Anthropic's privacy policy if this is a concern for your data.

The u2-mcp server itself runs locally and doesn't send data anywhere except to Claude and your database.

### What Universe/UniData versions are supported?

u2-mcp uses the `uopy` package from Rocket Software, which supports:
- Universe 11.x and later
- UniData 8.x and later

## Next Steps

Ready to get started?

1. **[Installation Guide](installation.md)** - Install u2-mcp and configure Claude Desktop
2. **[Configuration Reference](configuration.md)** - All configuration options
3. **[Usage Examples](examples.md)** - See what you can do
4. **[Tools Reference](tools.md)** - Detailed tool documentation
