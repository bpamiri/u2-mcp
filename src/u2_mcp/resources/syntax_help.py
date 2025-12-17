"""RetrieVe/UniQuery syntax help resource for u2-mcp."""

from ..server import mcp

RETRIEVE_SYNTAX = """
RetrieVe/UniQuery Quick Reference
=================================

BASIC COMMANDS
--------------

LIST file {selection} {sort} {output}
    Display records from a file with optional criteria, sorting, and field selection.
    Example: LIST CUSTOMERS WITH STATE = "CA" NAME PHONE BY NAME

SELECT file {selection} {sort}
    Create a select list of record IDs matching criteria.
    Example: SELECT ORDERS WITH ORDER.DATE >= "01/01/2024"

SSELECT file {selection} {sort}
    Same as SELECT but saves the list for later use.

SORT file {selection} BY field {output}
    List records sorted by specified field.
    Example: SORT CUSTOMERS BY LAST.NAME NAME ADDRESS

COUNT file {selection}
    Count records matching criteria.
    Example: COUNT INVOICES WITH STATUS = "OPEN"

SUM file {selection} field
    Sum numeric values in a field.
    Example: SUM INVOICES WITH STATUS = "OPEN" AMOUNT


SELECTION CRITERIA (WITH clause)
--------------------------------

Comparison Operators:
    WITH field = "value"       Equal to
    WITH field # "value"       Not equal to (or NE, <>)
    WITH field > "value"       Greater than (or GT)
    WITH field < "value"       Less than (or LT)
    WITH field >= "value"      Greater than or equal (or GE)
    WITH field <= "value"      Less than or equal (or LE)

Pattern Matching:
    WITH field LIKE "ABC..."   Starts with ABC
    WITH field LIKE "...XYZ"   Ends with XYZ
    WITH field LIKE "...MID..."  Contains MID

Range:
    WITH field BETWEEN "val1" AND "val2"

Sound-alike:
    WITH field SAID "soundex"  Sounds like (phonetic match)

Null/Empty:
    WITH NO field              Field is empty/null
    WITH field                 Field has a value (not empty)


LOGICAL OPERATORS
-----------------

AND - Both conditions must be true
    WITH STATE = "CA" AND BALANCE > "1000"

OR - Either condition can be true
    WITH STATE = "CA" OR STATE = "NV"

Parentheses for grouping:
    WITH (STATE = "CA" OR STATE = "NV") AND BALANCE > "1000"


SORT OPTIONS
------------

BY field              Sort ascending
BY.DSND field         Sort descending
BY.EXP field          Explode multivalues (one row per value)
BY-EXP field          Same as BY.EXP


OUTPUT OPTIONS
--------------

field1 field2 field3  Specify columns to display
TOTAL field           Show sum of numeric field
BREAK.ON field        Show subtotals when field value changes
HEADING "text"        Custom report heading
FOOTING "text"        Custom report footer
COL.HDG "text"        Custom column heading
LPTR                  Send to printer
NOPAGE                Suppress pagination
DET.SUP               Detail suppressed (totals only)
ID.SUP                Suppress record ID column
SAMPLE n              Limit to n records


COMMON CONVERSION CODES
-----------------------

Date Conversions (in dictionary):
    D2/              Date with 2-digit year (MM/DD/YY)
    D4/              Date with 4-digit year (MM/DD/YYYY)
    D-               Date with dashes (MM-DD-YYYY)
    D2-              Date with 2-digit year, dashes
    DM               Month only
    DY               Year only
    DW               Day of week
    DJ               Julian date

Numeric Conversions:
    MD2              Decimal, 2 places
    MD4              Decimal, 4 places
    MD2,             Decimal with comma separators
    MD2$             Decimal with dollar sign
    MR2              Right-justified, 2 decimal places

Text Conversions:
    MCU              Uppercase
    MCL              Lowercase
    MCT              Title case (capitalize words)
    ML               Left justify
    MR               Right justify
    MT               Time conversion (HH:MM:SS)


SPECIAL CHARACTERS
------------------

@ID                  Record ID (key)
@RECORD              Entire record
@VM                  Value mark (multivalue separator)
@SM                  Subvalue mark
@AM                  Attribute mark (field separator)


MULTIVALUE HANDLING
-------------------

BY.EXP field         Explode multivalues into separate rows
REFORMAT             Expand associated multivalues together

Example - List phone numbers (multivalue field) one per line:
    LIST CUSTOMERS BY.EXP PHONE.NUMBERS NAME PHONE.NUMBERS


DICTIONARY ITEM TYPES
---------------------

D-type: Data field
    Field 1: D
    Field 2: Field number (position in record)
    Field 3: Conversion code
    Field 4: Column heading
    Field 5: Format (e.g., 10L for 10 chars left-justified)
    Field 6: S (single) or M (multi)

I-type: Calculated/Correlative field
    Field 1: I
    Field 2: Expression (e.g., AMT * QTY)
    Field 3: Conversion code
    Field 4: Column heading
    Field 5: Format


TIPS FOR AI-GENERATED QUERIES
-----------------------------

1. Always quote string values with double quotes
   CORRECT: WITH STATE = "CA"
   WRONG: WITH STATE = CA

2. Use proper date format for your system (usually MM/DD/YYYY)
   WITH ORDER.DATE >= "01/01/2024"

3. When in doubt about field names, use describe_file first

4. For multivalues, consider if you need BY.EXP

5. Use SAMPLE to limit large result sets

6. COUNT is faster than LIST when you only need a count
"""


@mcp.resource("u2://retrieve_syntax")
def get_retrieve_syntax() -> str:
    """RetrieVe/UniQuery command reference and syntax help.

    Provides comprehensive documentation of the RetrieVe/UniQuery query language
    used in Universe and UniData databases. Includes command syntax, operators,
    conversion codes, and tips for generating correct queries.
    """
    return RETRIEVE_SYNTAX
