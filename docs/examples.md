# Usage Examples

This guide shows common usage patterns for interacting with Universe/UniData databases through Claude using u2-mcp.

## Getting Started

### Initial Connection

When you start a conversation, Claude will automatically connect to the database using your configured credentials. You can verify the connection:

> "Connect to the database and show me the current user"

Claude will:
1. Call `connect()` to establish the connection
2. Call `get_account_info()` to show user and account details

### Exploring the Account

> "What files are available in this account?"

```json
// Claude calls: list_files()
{
  "files": ["CUSTOMERS", "ORDERS", "PRODUCTS", "INVOICES"],
  "count": 4
}
```

> "List all files starting with AR"

```json
// Claude calls: list_files(pattern="AR*")
{
  "files": ["AR-CUST", "AR-TRANS", "AR-HIST"],
  "count": 3
}
```

---

## Reading Data

### Single Record

> "Read customer record CUST001"

```json
// Claude calls: read_record(file_name="CUSTOMERS", record_id="CUST001")
{
  "id": "CUST001",
  "fields": {
    "1": "Acme Corporation",
    "2": "123 Main Street",
    "3": "New York",
    "4": "NY",
    "5": ["555-1234", "555-5678"]
  }
}
```

### Multiple Records

> "Read records ORD001, ORD002, and ORD003 from ORDERS"

```json
// Claude calls: read_records(file_name="ORDERS", record_ids=["ORD001", "ORD002", "ORD003"])
{
  "file": "ORDERS",
  "records": [
    {"id": "ORD001", "fields": {...}},
    {"id": "ORD002", "fields": {...}},
    {"id": "ORD003", "fields": {...}}
  ],
  "count": 3
}
```

### Understanding File Structure

> "Describe the CUSTOMERS file"

Claude will call `describe_file("CUSTOMERS")` and explain:
- File statistics (record count, type)
- All defined fields with their meanings
- Which fields are multivalued
- Calculated fields (I-types)

---

## Querying Data

### Basic Queries

> "List all customers in California"

```
// Claude generates and executes:
LIST CUSTOMERS WITH STATE = "CA"
```

> "Count how many orders are open"

```
// Claude generates and executes:
COUNT ORDERS WITH STATUS = "OPEN"
```

> "Show me the top 10 invoices by amount"

```
// Claude generates and executes:
LIST INVOICES BY.DSND AMOUNT FIRST 10
```

### Filtering with Multiple Conditions

> "Find customers in NY or NJ with balance over 1000"

```
// Claude generates:
LIST CUSTOMERS WITH STATE = "NY" OR WITH STATE = "NJ" AND WITH BALANCE > 1000
```

### Working with Dates

> "List orders from January 2024"

```
// Claude generates (using internal date format):
LIST ORDERS WITH ORDER.DATE >= "01/01/2024" AND WITH ORDER.DATE <= "01/31/2024"
```

### Selecting Record IDs

> "Get all customer IDs in Texas for batch processing"

```json
// Claude calls: get_select_list(query='SELECT CUSTOMERS WITH STATE = "TX"')
{
  "record_ids": ["CUST001", "CUST045", "CUST089", ...],
  "count": 150,
  "truncated": false
}
```

---

## Understanding Data Structure

### Dictionary Exploration

> "What fields are in the ORDERS file?"

```json
// Claude calls: list_dictionary(file_name="ORDERS")
{
  "dictionary_items": [
    {"name": "CUST.ID", "type": "D", "field_number": "1", "heading": "Customer"},
    {"name": "ORDER.DATE", "type": "D", "field_number": "2", "conversion": "D2/"},
    {"name": "TOTAL", "type": "I", "expression": "SUM(LINE.AMT)"}
  ]
}
```

> "What is the ORDER.DATE field?"

```json
// Claude calls: get_field_definition(file_name="ORDERS", field_name="ORDER.DATE")
{
  "name": "ORDER.DATE",
  "type": "D",
  "field_number": "2",
  "conversion": "D2/",
  "heading": "Order Date",
  "format": "10R"
}
```

### Analyzing Actual Data

> "Analyze the CUSTOMERS file to see which fields are actually used"

```json
// Claude calls: analyze_file_structure(file_name="CUSTOMERS", sample_size=100)
{
  "records_analyzed": 100,
  "field_analysis": [
    {"field_number": "1", "usage_percent": 100.0, "has_multivalues": false},
    {"field_number": "2", "usage_percent": 98.0, "has_multivalues": false},
    {"field_number": "5", "usage_percent": 85.0, "has_multivalues": true, "max_values": 4}
  ]
}
```

---

## Writing Data

### Creating a Record

> "Create a new customer record CUST999 with name 'Test Company' in state CA"

Claude will first ask for confirmation:

```json
// Claude calls: write_record(file_name="CUSTOMERS", record_id="CUST999",
//   fields={"1": "Test Company", "4": "CA"}, confirm=false)
{
  "status": "confirmation_required",
  "message": "Set confirm=True to execute write operation"
}
```

After you confirm:

```json
// Claude calls with confirm=true
{
  "status": "success",
  "file": "CUSTOMERS",
  "id": "CUST999",
  "fields_written": 2
}
```

### Updating a Record

> "Update customer CUST001, change the phone number to 555-9999"

Same flow with confirmation required.

### Writing Multivalued Data

> "Add phone numbers 555-1111 and 555-2222 to customer CUST001"

```json
// Claude calls: write_record(file_name="CUSTOMERS", record_id="CUST001",
//   fields={"5": ["555-1111", "555-2222"]}, confirm=true)
```

---

## Exporting Data

### JSON Export

> "Export the first 10 customers to JSON"

```json
// Claude first gets record IDs, then exports
// Claude calls: get_select_list(query="SELECT CUSTOMERS SAMPLE 10")
// Claude calls: export_to_json(file_name="CUSTOMERS", record_ids=[...])
{
  "status": "success",
  "format": "json",
  "record_count": 10,
  "data": "[{\"id\": \"CUST001\", \"fields\": {...}}, ...]"
}
```

### CSV Export

> "Export California customers to CSV"

```json
// Claude calls: export_to_csv(file_name="CUSTOMERS", record_ids=[...], expand_mv=false)
{
  "status": "success",
  "format": "csv",
  "data": "id,field_1,field_2\nCUST001,Acme Corp,123 Main St\n..."
}
```

### Handling Multivalues in Export

> "Export customers to CSV with phone numbers on separate rows"

```json
// Claude calls: export_to_csv(..., expand_mv=true)
// Each multivalue becomes a separate row
```

---

## Calling BASIC Subroutines

### Simple Subroutine Call

> "Call the CALC.TAX subroutine with amount 100.00"

```json
// Claude calls: call_subroutine(name="CALC.TAX", args=["100.00"], num_args=2)
{
  "status": "success",
  "args_in": ["100.00"],
  "args_out": ["100.00", "8.25"]
}
```

### Subroutine with Output Arguments

> "Get customer data for CUST001 using the GET.CUSTOMER subroutine"

```json
// Claude calls: call_subroutine(name="GET.CUSTOMER", args=["CUST001", "", "", ""], num_args=4)
{
  "args_out": ["CUST001", "Acme Corp", "123 Main St", "CA"]
}
```

---

## Using Transactions

### Transaction Workflow

> "I need to update multiple records atomically"

```json
// Claude calls: begin_transaction()
{
  "status": "success",
  "message": "Transaction started",
  "in_transaction": true
}

// Claude performs multiple write operations...

// Claude calls: commit_transaction()
{
  "status": "success",
  "message": "Transaction committed successfully"
}
```

### Rolling Back

> "Cancel the current transaction"

```json
// Claude calls: rollback_transaction()
{
  "status": "success",
  "message": "Transaction rolled back successfully"
}
```

---

## Knowledge Persistence

### Saving Discoveries

When Claude discovers useful information about your database, it can save it:

> Claude: "I found that AR-CUST is your customer master file. Let me save this for future reference."

```json
// Claude calls: save_knowledge(
//   topic="AR-CUST file",
//   content="Customer master file. Key is customer number.\n- Field 1: Customer name\n- Field 2: Address\n- Field 5: Phone numbers (multivalued)"
// )
```

### Retrieving Knowledge

In future sessions, Claude can recall this information:

```json
// Claude calls: search_knowledge(query="customer")
{
  "results": [
    {"topic": "AR-CUST file", "matches": ["Customer master file"]}
  ]
}
```

### Managing Knowledge

> "What have you learned about this database?"

```json
// Claude calls: list_knowledge()
{
  "topics": [
    {"topic": "AR-CUST file", "summary": "Customer master file..."},
    {"topic": "Date formats", "summary": "Internal format, D2/ conversion..."},
    {"topic": "Status codes", "summary": "O=Open, C=Closed, P=Pending..."}
  ],
  "count": 3
}
```

---

## Complex Workflows

### Data Investigation

> "I need to understand the relationship between ORDERS and CUSTOMERS"

Claude will:
1. Call `describe_file("ORDERS")` to see order structure
2. Call `describe_file("CUSTOMERS")` to see customer structure
3. Look for linking fields (e.g., CUST.ID in orders)
4. Sample some records to verify the relationship
5. Save the discovered relationship for future reference

### Report Generation

> "Generate a summary of orders by customer for January 2024"

Claude will:
1. Build a query to select January orders
2. Use `get_select_list` to get matching order IDs
3. Read the records and group by customer
4. Present a formatted summary
5. Optionally export to CSV or JSON

### Data Cleanup Task

> "Find all customers without a state and show me what needs to be fixed"

Claude will:
1. Execute a query to find records with empty state
2. Sample the results to understand the data
3. Present findings with recommendations
4. (With your permission) help fix the data

---

## Best Practices

### Start with Exploration

Before querying, understand the file structure:
1. Use `describe_file` to see available fields
2. Use `analyze_file_structure` to see actual data patterns
3. Ask Claude to save what it learns

### Use Read-Only Mode for Exploration

Set `U2_READ_ONLY=true` when exploring to prevent accidental changes.

### Let Claude Learn

Encourage Claude to save useful discoveries:
> "Please save what you learned about this file for next time"

### Verify Before Writing

Always review Claude's proposed changes before confirming writes.

### Use Transactions for Related Changes

When updating multiple records that must succeed together, use transactions.

---

## Troubleshooting

### Query Returns No Results

> "My query isn't returning anything"

Claude will:
1. Validate the query syntax with `validate_query`
2. Check if the field names match the dictionary
3. Verify the data format (especially for dates)
4. Suggest corrections

### Field Not Found

> "It says 'CUSTOMER.NAME' is not found"

Claude will:
1. Check `list_dictionary` for the correct field name
2. Look for synonyms or alternative names
3. Suggest the correct field to use

### Connection Issues

> "I'm getting connection errors"

Check:
1. Server hostname and port are correct
2. Service type matches your database (uvcs vs udcs)
3. Credentials are valid
4. Network connectivity to the server
