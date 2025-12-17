# Tools Reference

This document provides a complete reference for all MCP tools available in u2-mcp.

## Overview

u2-mcp provides 31 tools organized into these categories:

| Category | Tools | Description |
|----------|-------|-------------|
| [Connection](#connection-management) | 3 | Connect/disconnect from database |
| [File Operations](#file-operations) | 8 | Read, write, delete, export records |
| [Query Execution](#query-execution) | 4 | Run RetrieVe/UniQuery and TCL commands |
| [Dictionary/Schema](#dictionaryschema-discovery) | 5 | Explore file structures and fields |
| [Subroutines](#basic-subroutines) | 2 | Call cataloged BASIC programs |
| [Transactions](#transaction-management) | 4 | Begin, commit, rollback transactions |
| [Knowledge](#knowledge-persistence) | 5 | Save and retrieve learned information |

---

## Connection Management

### connect

Establish connection to the Universe/UniData server.

**Parameters:** None (uses environment configuration)

**Returns:**
```json
{
  "status": "connected",
  "host": "server.example.com",
  "account": "MYACCOUNT",
  "service": "uvcs",
  "connected_at": "2024-01-15T10:30:00"
}
```

**Example usage:**
> "Connect to the database"

---

### disconnect

Close all connections to the Universe/UniData server.

**Parameters:** None

**Returns:**
```json
{
  "status": "disconnected",
  "connections_closed": 1
}
```

---

### list_connections

List all active database connections.

**Parameters:** None

**Returns:**
```json
{
  "connections": [
    {
      "name": "default",
      "host": "server.example.com",
      "account": "MYACCOUNT",
      "service": "uvcs",
      "connected_at": "2024-01-15T10:30:00",
      "is_active": true
    }
  ]
}
```

---

## File Operations

### list_files

List available files in the current Universe account.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `pattern` | string | `"*"` | File name pattern (supports `*` wildcard) |

**Returns:**
```json
{
  "files": ["CUSTOMERS", "ORDERS", "PRODUCTS"],
  "count": 3,
  "pattern": "*"
}
```

**Example usage:**
> "List all files starting with AR"

---

### read_record

Read a single record from a Universe file.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_name` | string | Yes | Name of the Universe file |
| `record_id` | string | Yes | Record ID (key) to read |

**Returns:**
```json
{
  "id": "CUST001",
  "fields": {
    "1": "John Doe",
    "2": ["555-1234", "555-5678"],
    "3": "CA"
  }
}
```

Note: Multivalues are returned as arrays, preserving Universe data structure.

**Example usage:**
> "Read record CUST001 from the CUSTOMERS file"

---

### read_records

Read multiple records from a Universe file efficiently.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_name` | string | Yes | Name of the Universe file |
| `record_ids` | list[string] | Yes | List of record IDs to read |

**Returns:**
```json
{
  "file": "CUSTOMERS",
  "records": [
    {"id": "CUST001", "fields": {...}},
    {"id": "CUST002", "fields": {...}}
  ],
  "count": 2,
  "errors": [{"id": "CUST999", "error": "Not found"}]
}
```

Limited by `U2_MAX_RECORDS` configuration.

---

### write_record

Write or update a record in a Universe file.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_name` | string | Yes | Target file name |
| `record_id` | string | Yes | Record ID to create/update |
| `fields` | object | Yes | Field values as JSON object |
| `confirm` | boolean | No | Must be `true` to execute (safety) |

**Field format:**
- Keys are field numbers as strings
- Values can be strings, arrays (multivalues), or nested arrays (subvalues)

**Example fields:**
```json
{
  "1": "John Doe",
  "2": ["555-1234", "555-5678"],
  "3": "CA"
}
```

**Note:** Disabled in read-only mode. Requires `confirm=true` to execute.

---

### delete_record

Delete a record from a Universe file.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_name` | string | Yes | Target file name |
| `record_id` | string | Yes | Record ID to delete |
| `confirm` | boolean | No | Must be `true` to execute (safety) |

**Note:** Disabled in read-only mode. Requires `confirm=true` to execute.

---

### get_file_info

Get information about a Universe file.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_name` | string | Yes | Name of the Universe file |

**Returns:**
```json
{
  "file": "CUSTOMERS",
  "type": "18",
  "modulo": 101,
  "separation": 4,
  "record_count": 1523,
  "raw_output": "..."
}
```

---

### export_to_json

Export records from a Universe file to JSON format.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `file_name` | string | Required | Name of the Universe file |
| `record_ids` | list[string] | Required | List of record IDs to export |
| `expand_mv` | boolean | `false` | Expand multivalues into separate objects |

**Returns:**
```json
{
  "status": "success",
  "file": "CUSTOMERS",
  "format": "json",
  "record_count": 10,
  "data": "[{\"id\": \"CUST001\", ...}]"
}
```

---

### export_to_csv

Export records from a Universe file to CSV format.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `file_name` | string | Required | Name of the Universe file |
| `record_ids` | list[string] | Required | List of record IDs to export |
| `expand_mv` | boolean | `false` | Expand multivalues into separate rows |
| `mv_delimiter` | string | `"|"` | Delimiter for multivalues when not expanding |

**Returns:**
```json
{
  "status": "success",
  "file": "CUSTOMERS",
  "format": "csv",
  "record_count": 10,
  "row_count": 10,
  "data": "id,field_1,field_2\nCUST001,John Doe,555-1234|555-5678\n..."
}
```

---

## Query Execution

### execute_query

Execute a RetrieVe/UniQuery statement and return results.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | Required | RetrieVe/UniQuery statement |
| `max_rows` | integer | `U2_MAX_RECORDS` | Maximum rows to return |

**Allowed commands:** LIST, SELECT, SORT, COUNT, SUM, SSELECT

**Returns:**
```json
{
  "query": "LIST CUSTOMERS WITH STATE = \"CA\"",
  "output": "CUST001  John Doe  CA\nCUST002  Jane Smith  CA\n...",
  "status": "success",
  "max_rows": 1000
}
```

**Example usage:**
> "List all customers in California"
> "Count open invoices over $1000"
> "Sort orders by date"

---

### execute_tcl

Execute a TCL/ECL command and return the output.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `command` | string | Yes | TCL/ECL command to execute |

**Common commands:**
- `WHO` - Show current user info
- `DATE` - Show current date
- `TIME` - Show current time
- `LISTFILES` - List available files
- `FILE.STAT FILENAME` - Show file statistics

**Note:** Dangerous commands are blocked by the safety validator. Additional commands can be blocked via `U2_BLOCKED_COMMANDS`.

---

### get_select_list

Execute a SELECT statement and return the list of record IDs.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | Required | SELECT or SSELECT statement |
| `max_ids` | integer | `U2_MAX_RECORDS` | Maximum IDs to return |

**Returns:**
```json
{
  "query": "SELECT CUSTOMERS WITH STATE = \"CA\"",
  "record_ids": ["CUST001", "CUST002", "CUST003"],
  "count": 3,
  "truncated": false,
  "max_ids": 10000
}
```

Useful for getting a list of matching records for further processing.

---

### validate_query

Validate a RetrieVe/UniQuery statement before execution.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Query statement to validate |

**Returns:**
```json
{
  "query": "LIST CUSTOMERS WITH STATE = CA",
  "valid": true,
  "command": "LIST",
  "file": "CUSTOMERS",
  "warnings": ["String values should be quoted with double quotes"],
  "suggestions": ["Example: WITH STATE = \"CA\" (not WITH STATE = CA)"]
}
```

Useful for validating AI-generated queries before running them.

---

## Dictionary/Schema Discovery

### list_dictionary

List all dictionary items for a Universe file.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `file_name` | string | Required | Name of the Universe file |
| `include_system` | boolean | `false` | Include system items (@ prefixed) |

**Returns:**
```json
{
  "file": "CUSTOMERS",
  "dictionary_items": [
    {"name": "NAME", "type": "D", "field_number": "1", "heading": "Customer Name"},
    {"name": "PHONE", "type": "D", "field_number": "2", "heading": "Phone"},
    {"name": "FULLADDR", "type": "I", "expression": "ADDR:' ':CITY:' ':STATE"}
  ],
  "count": 15
}
```

---

### get_field_definition

Get detailed definition for a specific dictionary field.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_name` | string | Yes | Name of the Universe file |
| `field_name` | string | Yes | Dictionary field/item name |

**Returns:**
```json
{
  "name": "ORDER.DATE",
  "type": "D",
  "field_number": "5",
  "conversion": "D2/",
  "heading": "Order Date",
  "format": "10R",
  "single_multi": "S",
  "file": "ORDERS"
}
```

---

### describe_file

Get a comprehensive description of a Universe file.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_name` | string | Yes | Name of the Universe file |

**Returns:**
```json
{
  "file": "CUSTOMERS",
  "description": "Universe file 'CUSTOMERS' with 12 data fields and 5 calculated fields",
  "file_stats": "...",
  "fields": [...],
  "field_count": 17,
  "data_field_count": 12,
  "calculated_field_count": 5
}
```

Combines file statistics with dictionary information.

---

### analyze_file_structure

Analyze file structure by sampling records to infer field usage patterns.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `file_name` | string | Required | Name of the Universe file |
| `sample_size` | integer | `100` | Number of records to sample |

**Returns:**
```json
{
  "file": "CUSTOMERS",
  "records_analyzed": 100,
  "fields_detected": 8,
  "field_analysis": [
    {
      "field_number": "1",
      "populated_count": 100,
      "usage_percent": 100.0,
      "has_multivalues": false,
      "max_values": 1,
      "sample_values": ["John Doe", "Jane Smith", ...]
    },
    {
      "field_number": "2",
      "populated_count": 85,
      "usage_percent": 85.0,
      "has_multivalues": true,
      "max_values": 3,
      "sample_values": ["555-1234", "555-5678", ...]
    }
  ]
}
```

Useful when dictionary is incomplete or for understanding actual data usage.

---

### get_account_info

Get information about the current Universe account.

**Parameters:** None

**Returns:**
```json
{
  "who": "MYUSER on MYACCOUNT",
  "date": "15 JAN 2024",
  "time": "10:30:00",
  "file_count": 45,
  "files": ["CUSTOMERS", "ORDERS", ...],
  "connection": {
    "host": "server.example.com",
    "account": "MYACCOUNT",
    "service": "uvcs",
    "connected_at": "2024-01-15T10:30:00"
  },
  "read_only_mode": false,
  "in_transaction": false
}
```

---

## BASIC Subroutines

### call_subroutine

Call a cataloged BASIC subroutine with arguments.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | string | Required | Name of the cataloged subroutine |
| `args` | list[string] | `[]` | List of input argument values |
| `num_args` | integer | `len(args)` | Total number of arguments expected |

**Returns:**
```json
{
  "status": "success",
  "subroutine": "GET.CUSTOMER.DATA",
  "args_in": ["CUST001", "", ""],
  "args_out": ["CUST001", "John Doe", "CA"],
  "num_args": 3
}
```

Arguments are passed by reference, so output values are returned in `args_out`.

**Example:**
```
call_subroutine("GET.CUSTOMER.DATA", ["CUST001", "", ""], num_args=3)
```

---

### list_catalog

List available cataloged programs in the account.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `pattern` | string | `"*"` | Program name pattern (supports `*` wildcard) |

**Returns:**
```json
{
  "pattern": "*",
  "programs": ["GET.CUSTOMER.DATA", "CALC.ORDER.TOTAL", ...],
  "count": 25
}
```

---

## Transaction Management

### begin_transaction

Begin a database transaction.

**Parameters:** None

**Returns:**
```json
{
  "status": "success",
  "message": "Transaction started",
  "in_transaction": true,
  "started_at": "2024-01-15T10:30:00"
}
```

**Note:** Only one transaction can be active at a time. Disabled in read-only mode.

---

### commit_transaction

Commit the current transaction.

**Parameters:** None

**Returns:**
```json
{
  "status": "success",
  "message": "Transaction committed successfully",
  "in_transaction": false
}
```

---

### rollback_transaction

Rollback the current transaction.

**Parameters:** None

**Returns:**
```json
{
  "status": "success",
  "message": "Transaction rolled back successfully",
  "in_transaction": false
}
```

---

### get_transaction_status

Get the current transaction status.

**Parameters:** None

**Returns:**
```json
{
  "in_transaction": true,
  "started_at": "2024-01-15T10:30:00",
  "read_only_mode": false
}
```

---

## Knowledge Persistence

These tools allow Claude to save and retrieve learned information about your database across sessions.

### save_knowledge

Save learned information about the Universe database.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `topic` | string | Required | Short descriptive name for this knowledge |
| `content` | string | Required | The knowledge to save (markdown supported) |
| `append` | boolean | `false` | If true, add to existing topic |

**Good things to save:**
- File purposes (e.g., "AR-CUST contains customer master records")
- Field meanings (e.g., "In CUSTOMERS, field 1 is name, field 5 is phone")
- Working query patterns that produced good results
- Relationships between files
- Data format notes (date formats, codes, etc.)

**Example:**
```
save_knowledge(
  "AR-CUST file",
  "Customer master file. Key is customer number.\n- Field 1: Customer name\n- Field 5: Phone numbers (multivalued)"
)
```

---

### list_knowledge

List all saved knowledge topics.

**Parameters:** None

**Returns:**
```json
{
  "topics": [
    {"topic": "AR-CUST file", "summary": "Customer master file..."},
    {"topic": "Date formats", "summary": "Dates stored as internal..."}
  ],
  "count": 2,
  "knowledge_file": "/Users/me/.u2-mcp/knowledge.md"
}
```

---

### get_knowledge_topic

Get saved knowledge for a specific topic.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `topic` | string | Yes | The topic name to retrieve |

**Returns:**
```json
{
  "status": "found",
  "topic": "AR-CUST file",
  "content": "Customer master file. Key is customer number..."
}
```

---

### search_knowledge

Search saved knowledge for specific information.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Text to search for (case-insensitive) |

**Returns:**
```json
{
  "query": "customer",
  "results": [
    {"topic": "AR-CUST file", "matches": ["Customer master file", "customer number"]}
  ],
  "match_count": 1
}
```

---

### delete_knowledge

Delete a saved knowledge topic.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `topic` | string | Required | The topic name to delete |
| `confirm` | boolean | `false` | Must be `true` to execute (safety) |

---

## MCP Resources

In addition to tools, u2-mcp exposes these MCP resources:

### u2://knowledge

Returns all saved knowledge about the database. This resource is automatically available in every conversation, allowing Claude to access previously learned information without explicit tool calls.

### u2://query_examples

Returns example RetrieVe/UniQuery statements for common operations, helping Claude generate correct queries.

### u2://retrieve_syntax

Returns RetrieVe/UniQuery syntax reference including conversion codes and correlative syntax.

---

## Safety Features

### Read-Only Mode

When `U2_READ_ONLY=true`:
- `write_record` returns an error
- `delete_record` returns an error
- Transaction tools return errors
- Query and read operations work normally

### Confirmation Requirements

These tools require `confirm=true` to execute:
- `write_record`
- `delete_record`
- `delete_knowledge`

### Command Blocking

TCL commands can be blocked via `U2_BLOCKED_COMMANDS`. Default blocked commands:
- `DELETE.FILE`
- `CLEAR.FILE`
- `CNAME`
- `CREATE.FILE`

### Query Restrictions

`execute_query` only allows these commands:
- LIST
- SELECT
- SSELECT
- SORT
- COUNT
- SUM

### Result Limiting

All queries and batch reads are limited by `U2_MAX_RECORDS` (default: 10,000).
