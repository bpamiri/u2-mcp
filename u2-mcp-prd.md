# Product Requirements Document: u2-mcp

## Executive Summary

Build an open-source Model Context Protocol (MCP) server that enables AI assistants (Claude, Cursor, etc.) to interact with Rocket Universe (and UniData) MultiValue databases using natural language. This will be the first MCP server for the Pick/MultiValue database family, filling a significant gap in the MCP ecosystem.

**Project Name:** `u2-mcp`  
**PyPI Package:** `u2-mcp`  
**GitHub Repository:** `u2-mcp`

## Project Overview

### Problem Statement

The MCP ecosystem has strong coverage for mainstream databases (PostgreSQL, MySQL, MongoDB, etc.) but zero support for MultiValue databases like Rocket Universe, UniData, or D3. Organizations running mission-critical systems on these platforms cannot leverage AI assistants for database interaction, query generation, or data analysis.

### Solution

Create a Python-based MCP server using Rocket's official `uopy` (UniObjects for Python) package that exposes Universe's native capabilities through MCP tools, preserving MultiValue semantics rather than flattening to relational models.

### Target Users

- Developers working with Universe/UniData applications
- DBAs managing MultiValue databases
- Business analysts needing ad-hoc data access
- AI-assisted development tools (Claude Code, Cursor, Windsurf, etc.)

## Technical Foundation

### Core Dependency: UOPY

The `uopy` package (pip install uopy) provides:

```python
import uopy

# Connection
session = uopy.connect(
    host='server',
    user='username', 
    password='password',
    account='ACCOUNT_NAME',
    service='uvcs'  # or 'udcs' for UniData
)

# File operations
file = session.open('CUSTOMERS')
record = file.read('CUST001')
file.write('CUST002', record)

# TCL/ECL commands
cmd = session.command()
cmd.exec('LIST CUSTOMERS WITH STATE = "CA"')
output = cmd.response

# BASIC subroutine calls
sub = session.subroutine('GET.CUSTOMER.DATA', 3)  # 3 arguments
sub.args[0] = 'CUST001'
sub.call()
result = sub.args[1]

# SELECT lists
select = session.select()
select.exec('SELECT CUSTOMERS WITH BALANCE > 1000')
for record_id in select:
    # process each ID
    pass

# Dynamic arrays
from uopy import DynArray
da = DynArray(record)
field1 = da.extract(1)        # Get field 1
field2_mv3 = da.extract(2, 3) # Get field 2, multivalue 3
```

### MCP Server Framework

Use FastMCP (from the `mcp` package) for rapid development:

```python
from mcp.server import FastMCP

mcp = FastMCP("Universe MCP Server")

@mcp.tool()
def query_file(file_name: str, record_id: str) -> str:
    """Read a record from a Universe file"""
    # implementation
```

## Feature Requirements

### Phase 1: Core Connectivity (MVP)

#### 1.1 Connection Management

**Tool: `connect`**
- Establish connection to Universe/UniData server
- Support multiple simultaneous connections (named sessions)
- Connection pooling support via uopy.ini configuration
- SSL/TLS support

**Tool: `disconnect`**
- Close specific or all connections
- Clean up resources

**Tool: `list_connections`**
- Show active connections and their status

**Configuration via environment variables or config file:**
```
UV_HOST=server.example.com
UV_USER=username
UV_PASSWORD=password
UV_ACCOUNT=PRODUCTION
UV_SERVICE=uvcs
UV_PORT=31438
```

#### 1.2 File Operations

**Tool: `list_files`**
- List available files in the current account
- Filter by pattern (e.g., "CUST*")

**Tool: `read_record`**
- Read a single record by ID
- Return as structured data with field numbers or dictionary names
- Handle multivalues and subvalues properly

**Tool: `read_records`**
- Read multiple records by ID list
- Batch operation for efficiency

**Tool: `write_record`**
- Write/update a record
- Support field-level updates
- Optional locking

**Tool: `delete_record`**
- Delete a record by ID
- Require confirmation parameter

**Tool: `get_file_info`**
- Return file statistics (record count, modulo, separation, type)
- Dictionary information

#### 1.3 Query Execution

**Tool: `execute_query`**
- Run RetrieVe/UniQuery statements
- Return formatted results
- Support common query patterns:
  - `LIST file WITH criteria`
  - `SELECT file WITH criteria`
  - `SORT file BY field`
  - `COUNT file WITH criteria`

**Tool: `execute_tcl`**
- Run arbitrary TCL/ECL commands
- Return command output
- Safety controls for dangerous commands

**Tool: `get_select_list`**
- Execute SELECT and return list of record IDs
- Support pagination for large result sets

#### 1.4 Dictionary Access

**Tool: `list_dictionary`**
- List dictionary items for a file
- Show field definitions, conversions, correlatives

**Tool: `get_field_definition`**
- Get detailed definition for a specific field
- Include type, conversion, format, heading

**Tool: `describe_file`**
- High-level file description combining stats + dictionary
- Useful for LLM context about data structure

### Phase 2: Advanced Features

#### 2.1 BASIC Subroutine Integration

**Tool: `call_subroutine`**
- Call cataloged BASIC subroutines
- Pass arguments in/out
- Return results

**Tool: `list_catalog`**
- List available cataloged programs
- Filter by pattern

#### 2.2 Transaction Support

**Tool: `begin_transaction`**
- Start a transaction

**Tool: `commit_transaction`**
- Commit current transaction

**Tool: `rollback_transaction`**
- Rollback current transaction

#### 2.3 Schema Discovery

**Tool: `analyze_file_structure`**
- Sample records to infer field usage patterns
- Detect multivalue patterns
- Suggest field names if dictionary is incomplete

**Tool: `get_account_info`**
- List files, VOC entries, system info
- Account-level metadata

### Phase 3: AI-Optimized Features

#### 3.1 Natural Language Query Translation

**Resource: `query_examples`**
- Provide example RetrieVe queries for common patterns
- Help LLM generate correct syntax

**Tool: `validate_query`**
- Check query syntax before execution
- Return helpful error messages

#### 3.2 Data Export

**Tool: `export_to_json`**
- Export query results as JSON
- Handle MV field expansion options

**Tool: `export_to_csv`**
- Export with proper MV handling
- Configurable delimiter for MVs

#### 3.3 Contextual Help

**Resource: `retrieve_syntax`**
- RetrieVe/UniQuery command reference
- Conversion codes reference
- Correlative syntax

## Architecture

### Project Structure

```
u2-mcp/
├── src/
│   └── u2_mcp/
│       ├── __init__.py
│       ├── server.py           # Main MCP server entry point
│       ├── connection.py       # Connection management
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── files.py        # File operation tools
│       │   ├── query.py        # Query execution tools
│       │   ├── dictionary.py   # Dictionary tools
│       │   ├── subroutine.py   # BASIC subroutine tools
│       │   └── transaction.py  # Transaction tools
│       ├── resources/
│       │   ├── __init__.py
│       │   ├── syntax_help.py  # Query syntax resources
│       │   └── examples.py     # Example queries
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── dynarray.py     # Dynamic array helpers
│       │   ├── formatting.py   # Output formatting
│       │   └── safety.py       # Command validation
│       └── config.py           # Configuration management
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── test_connection.py
│   ├── test_files.py
│   ├── test_query.py
│   └── mocks/
│       └── mock_uopy.py        # Mock UOPY for testing
├── docs/
│   ├── installation.md
│   ├── configuration.md
│   ├── tools.md
│   └── examples.md
├── pyproject.toml
├── README.md
├── LICENSE                     # Apache 2.0
└── .github/
    └── workflows/
        └── test.yml
```

### Key Design Decisions

1. **Connection Pooling**: Leverage uopy's built-in connection pooling rather than implementing our own.

2. **MultiValue Handling**: Preserve MV structure in output. Default to JSON representation:
   ```json
   {
     "id": "CUST001",
     "fields": {
       "1": "ACME Corp",
       "2": ["John Smith", "Jane Doe"],  // Multivalue
       "3": [["555-1234", "555-5678"], ["555-9999"]]  // MV with subvalues
     },
     "named_fields": {
       "NAME": "ACME Corp",
       "CONTACTS": ["John Smith", "Jane Doe"]
     }
   }
   ```

3. **Safety Controls**: 
   - Whitelist/blacklist for TCL commands
   - Read-only mode option
   - Query timeout limits
   - Record count limits on SELECT

4. **Error Handling**: Translate uopy exceptions into meaningful MCP errors with context.

## Configuration

### Environment Variables

```bash
# Required
U2_HOST=192.168.1.100
U2_USER=dbuser
U2_PASSWORD=secret
U2_ACCOUNT=PRODUCTION

# Optional
U2_SERVICE=uvcs              # uvcs (Universe) or udcs (UniData)
U2_PORT=31438                # Default U2 port
U2_SSL=true                  # Enable SSL
U2_TIMEOUT=30                # Connection timeout
U2_READ_ONLY=false           # Disable write operations
U2_MAX_RECORDS=10000         # Limit SELECT results
U2_BLOCKED_COMMANDS=DELETE.FILE,CLEAR.FILE  # Blocked TCL commands
```

### MCP Client Configuration

**Claude Desktop (claude_desktop_config.json):**
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

**Alternative with config file:**
```json
{
  "mcpServers": {
    "u2": {
      "command": "uvx",
      "args": ["u2-mcp", "--config", "/path/to/u2.yaml"]
    }
  }
}
```

## Testing Strategy

### Unit Tests
- Mock uopy connections
- Test dynamic array parsing
- Test query validation
- Test output formatting

### Integration Tests
- Require actual Universe instance
- Use dedicated test account
- Create/cleanup test files
- Mark as `@pytest.mark.integration`

### Test Data
- Provide sample Universe account setup scripts
- Standard test files: CUSTOMERS, ORDERS, PRODUCTS
- Known test records for validation

## Security Considerations

1. **Credential Storage**: Never log passwords; support environment variables and secure config files.

2. **Command Injection**: Validate and sanitize all user inputs before passing to TCL.

3. **Access Control**: 
   - Honor Universe's built-in security (file permissions, account restrictions)
   - Add configurable command blocklist
   - Optional read-only mode

4. **Audit Logging**: Log all commands executed (without sensitive data).

## Documentation Requirements

### README.md
- Quick start guide
- Installation instructions
- Basic usage examples
- Link to full documentation

### Tool Documentation
- Each tool needs:
  - Description
  - Parameters with types
  - Return value format
  - Example usage
  - Error conditions

### Tutorials
- Connecting to Universe
- Basic data queries
- Working with multivalues
- Calling BASIC subroutines
- Bulk data operations

## Success Metrics

1. **Functional**: All Phase 1 tools working with Universe 11.x
2. **Performance**: Query responses under 5 seconds for typical operations
3. **Adoption**: Published to PyPI, listed in awesome-mcp-servers
4. **Quality**: 80%+ test coverage, no critical security issues

## Timeline Estimate

- **Phase 1 (MVP)**: 2-3 weeks
  - Week 1: Connection management, basic file operations
  - Week 2: Query execution, dictionary access
  - Week 3: Testing, documentation, PyPI packaging

- **Phase 2**: 2 weeks
  - Subroutine calls, transactions, schema discovery

- **Phase 3**: 2 weeks
  - AI-optimized features, polish, community feedback

## Open Questions

1. **UniData Support**: Should we test/support UniData from day one, or Universe-first?
   - Recommendation: Universe first, UniData as fast-follow (APIs are nearly identical)

2. ~~**Licensing**: MIT or Apache 2.0?~~
   - **Decision: Apache 2.0** (matches most MCP servers)

3. ~~**Package Name**: `universe-mcp-server`, `u2-mcp-server`, `multivalue-mcp-server`?~~
   - **Decision: `u2-mcp`** — short, uses Rocket's official U2 branding

4. **Connection Model**: Single connection per server instance, or connection-per-request?
   - Recommendation: Single persistent connection with auto-reconnect, leveraging uopy pooling

## Appendix A: Sample Tool Implementations

### Basic File Read

```python
from mcp.server import FastMCP
from pydantic import Field
import uopy
import os

mcp = FastMCP("U2 MCP Server")
_session = None

def get_session():
    global _session
    if _session is None:
        _session = uopy.connect(
            host=os.environ['U2_HOST'],
            user=os.environ['U2_USER'],
            password=os.environ['U2_PASSWORD'],
            account=os.environ['U2_ACCOUNT']
        )
    return _session

@mcp.tool()
def read_record(
    file_name: str = Field(description="Name of the Universe file"),
    record_id: str = Field(description="Record ID to read")
) -> dict:
    """Read a record from a Universe file and return its contents."""
    session = get_session()
    
    try:
        file = session.open(file_name)
        record = file.read(record_id)
        
        # Parse into structured format
        da = uopy.DynArray(record)
        fields = {}
        
        # Extract all fields (up to reasonable limit)
        for i in range(1, 100):
            try:
                value = da.extract(i)
                if value:
                    # Handle multivalues
                    if chr(253) in value:  # VM
                        value = value.split(chr(253))
                    fields[str(i)] = value
                else:
                    break
            except:
                break
        
        return {
            "file": file_name,
            "id": record_id,
            "fields": fields,
            "raw": str(record)
        }
        
    except uopy.UOError as e:
        return {"error": str(e), "file": file_name, "id": record_id}
```

### Query Execution

```python
@mcp.tool()
def execute_query(
    query: str = Field(description="RetrieVe/UniQuery statement (e.g., 'LIST CUSTOMERS WITH STATE = \"CA\"')")
) -> dict:
    """Execute a RetrieVe/UniQuery statement and return results."""
    session = get_session()
    
    # Basic safety check
    query_upper = query.upper().strip()
    dangerous = ['DELETE', 'CLEAR', 'CREATE', 'CNAME']
    if any(query_upper.startswith(cmd) for cmd in dangerous):
        return {"error": f"Command not allowed: {query_upper.split()[0]}"}
    
    try:
        cmd = session.command()
        cmd.exec(query)
        
        return {
            "query": query,
            "output": cmd.response,
            "status": "success"
        }
        
    except uopy.UOError as e:
        return {"error": str(e), "query": query}
```

## Appendix B: RetrieVe Quick Reference

Include as MCP resource for LLM context:

```
RetrieVe/UniQuery Quick Reference
=================================

Basic Syntax:
  LIST file {selects} {sort} {output}
  SELECT file {selects} {sort}
  COUNT file {selects}
  
Selection Criteria:
  WITH field = "value"
  WITH field # "value"        (not equal)
  WITH field > "value"
  WITH field < "value"
  WITH field >= "value"
  WITH field <= "value"
  WITH field LIKE "pattern..."
  WITH field BETWEEN "val1" AND "val2"
  WITH field SAID "soundex"   (sounds like)
  
Logical Operators:
  WITH field1 = "x" AND field2 = "y"
  WITH field1 = "x" OR field2 = "y"
  
Sort Options:
  BY field              (ascending)
  BY.DSND field         (descending)
  BY.EXP field          (explode multivalues)
  
Output Options:
  field1 field2 field3  (column names)
  TOTAL field           (sum numeric field)
  BREAK.ON field        (subtotals)
  HEADING "text"
  FOOTING "text"
  LPTR                  (to printer)
  
Common Conversions (in dictionary):
  D2/              (date, 2-digit year)
  D4/              (date, 4-digit year)
  MD2              (decimal, 2 places)
  MT               (time)
  MCU              (uppercase)
  MCL              (lowercase)
  
Examples:
  LIST CUSTOMERS WITH STATE = "CA" NAME PHONE BALANCE
  SELECT ORDERS WITH ORDER.DATE >= "01/01/2024" BY ORDER.DATE
  COUNT INVOICES WITH STATUS = "OPEN" AND AMOUNT > "1000"
  LIST PRODUCTS BY CATEGORY PRODUCT.NAME PRICE TOTAL QTY.ON.HAND
```

---

**Document Version**: 1.0  
**Created**: December 2024  
**Author**: [Your Name]  
**Status**: Draft
