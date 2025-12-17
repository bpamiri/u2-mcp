"""Query examples resource for u2-mcp."""

from ..server import mcp

QUERY_EXAMPLES = """
RetrieVe/UniQuery Examples
==========================

These examples demonstrate common query patterns for Universe/UniData databases.
Adapt file and field names to match your actual data dictionary.


BASIC LISTING
-------------

List all records from a file:
    LIST CUSTOMERS

List specific fields:
    LIST CUSTOMERS NAME ADDRESS CITY STATE PHONE

List with record ID suppressed:
    LIST CUSTOMERS NAME ADDRESS ID.SUP


FILTERING (WITH clause)
-----------------------

Filter by exact value:
    LIST CUSTOMERS WITH STATE = "CA"

Filter by multiple values (OR):
    LIST CUSTOMERS WITH STATE = "CA" OR STATE = "NV" OR STATE = "AZ"

Filter by range:
    LIST INVOICES WITH AMOUNT >= "100" AND AMOUNT <= "1000"
    LIST INVOICES WITH AMOUNT BETWEEN "100" AND "1000"

Filter by date:
    LIST ORDERS WITH ORDER.DATE >= "01/01/2024"

Filter by pattern (starts with):
    LIST CUSTOMERS WITH NAME LIKE "ACME..."

Filter by pattern (contains):
    LIST CUSTOMERS WITH NAME LIKE "...CORP..."

Filter for non-empty values:
    LIST CUSTOMERS WITH PHONE

Filter for empty values:
    LIST CUSTOMERS WITH NO EMAIL


SORTING
-------

Sort ascending:
    LIST CUSTOMERS BY NAME

Sort descending:
    LIST CUSTOMERS BY.DSND BALANCE

Sort by multiple fields:
    LIST CUSTOMERS BY STATE BY NAME

Sort with output fields:
    SORT CUSTOMERS BY LAST.NAME FIRST.NAME LAST.NAME PHONE


COUNTING AND TOTALS
-------------------

Count records:
    COUNT CUSTOMERS WITH STATE = "CA"

Sum a field:
    SUM INVOICES WITH STATUS = "OPEN" AMOUNT

Show totals at end:
    LIST INVOICES AMOUNT TOTAL AMOUNT


GROUPING AND BREAKS
-------------------

Group by a field with subtotals:
    LIST INVOICES BY STATE BREAK.ON STATE AMOUNT TOTAL AMOUNT

Summary only (no detail):
    LIST INVOICES BY STATE BREAK.ON STATE AMOUNT TOTAL AMOUNT DET.SUP


MULTIVALUE QUERIES
------------------

Explode multivalues (one row per value):
    LIST CUSTOMERS BY.EXP PHONE NAME PHONE

Count items in multivalue field:
    LIST CUSTOMERS NAME COUNT(ORDERS)


SELECT LISTS
------------

Create a select list:
    SELECT CUSTOMERS WITH STATE = "CA"

Use select list in subsequent query:
    LIST CUSTOMERS NAME ADDRESS

Save select list:
    SSELECT CUSTOMERS WITH BALANCE > "10000"
    SAVE.LIST HIGHBALANCE

Retrieve saved list:
    GET.LIST HIGHBALANCE
    LIST CUSTOMERS NAME BALANCE


DATE QUERIES
------------

Records from this year:
    LIST ORDERS WITH ORDER.DATE >= "01/01/2024"

Records from last 30 days (requires date calculation):
    LIST ORDERS WITH ORDER.DATE >= "@DATE - 30"

Records for specific month:
    LIST ORDERS WITH ORDER.DATE >= "07/01/2024" AND ORDER.DATE <= "07/31/2024"


COMMON PATTERNS
---------------

Customer lookup by name:
    LIST CUSTOMERS WITH NAME LIKE "ACME..." NAME ADDRESS PHONE

Open invoices over threshold:
    LIST INVOICES WITH STATUS = "OPEN" AND AMOUNT > "1000"
        BY.DSND AMOUNT CUSTOMER INVOICE.DATE AMOUNT

Order history for customer:
    LIST ORDERS WITH CUSTOMER.ID = "CUST001" BY ORDER.DATE
        ORDER.DATE TOTAL ITEMS STATUS

Inventory low stock:
    LIST INVENTORY WITH QTY.ON.HAND < "10"
        BY PRODUCT.NAME PRODUCT.NAME QTY.ON.HAND REORDER.POINT

Sales by region:
    LIST ORDERS BY REGION BREAK.ON REGION ORDER.TOTAL TOTAL ORDER.TOTAL DET.SUP


ADVANCED PATTERNS
-----------------

Joining data (correlative/I-type required in dictionary):
    LIST ORDERS ORDER.DATE CUSTOMER.NAME ORDER.TOTAL

Top N records:
    LIST CUSTOMERS BY.DSND BALANCE BALANCE SAMPLE 10

Records with specific multivalue count:
    LIST CUSTOMERS WITH COUNT(ORDERS) > "5" NAME COUNT(ORDERS)


TIPS FOR SUCCESS
----------------

1. Start simple, add complexity incrementally
2. Use COUNT first to estimate result size
3. Use SAMPLE to limit large result sets
4. Check dictionary for available field names
5. Test date formats with small queries first
6. Quote all string values in conditions
"""


@mcp.resource("u2://query_examples")
def get_query_examples() -> str:
    """Example RetrieVe/UniQuery queries for common patterns.

    Provides a collection of example queries demonstrating common patterns
    for data retrieval, filtering, sorting, grouping, and multivalue handling
    in Universe/UniData databases.
    """
    return QUERY_EXAMPLES
