"""Query execution tools for u2-mcp."""

import logging
from typing import Any

from ..server import get_connection_manager, mcp
from ..utils.safety import ALLOWED_QUERY_COMMANDS, CommandValidator

logger = logging.getLogger(__name__)


@mcp.tool()
def execute_query(query: str, max_rows: int | None = None) -> dict[str, Any]:
    """Execute a RetrieVe/UniQuery statement and return results.

    Supports read-only query commands: LIST, SELECT, SORT, COUNT, SUM, SSELECT.
    Results are limited by max_rows parameter or the U2_MAX_RECORDS configuration.

    Args:
        query: RetrieVe/UniQuery statement
               Examples:
               - 'LIST CUSTOMERS WITH STATE = "CA"'
               - 'SELECT ORDERS WITH ORDER.DATE >= "01/01/2024" BY ORDER.DATE'
               - 'COUNT INVOICES WITH STATUS = "OPEN"'
        max_rows: Maximum rows to return (optional, defaults to U2_MAX_RECORDS)

    Returns:
        Dictionary containing query, output, status, and row limit applied.
    """
    manager = get_connection_manager()
    config = manager.config

    # Validate query safety
    validator = CommandValidator(config.blocked_commands, config.read_only)
    is_safe, error_msg = validator.is_query_safe(query)

    if not is_safe:
        return {"error": error_msg, "query": query}

    # Apply row limit
    effective_max = min(max_rows or config.max_records, config.max_records)

    try:
        # Add SAMPLE clause for LIST commands to limit results
        query_upper = query.upper().strip()
        modified_query = query
        if query_upper.startswith("LIST") and "SAMPLE" not in query_upper:
            modified_query = f"{query} SAMPLE {effective_max}"

        output = manager.execute_command(modified_query)

        return {
            "query": query,
            "executed_query": modified_query if modified_query != query else None,
            "output": output,
            "status": "success",
            "max_rows": effective_max,
        }

    except Exception as e:
        logger.error(f"Error executing query: {e}")
        return {"error": str(e), "query": query}


@mcp.tool()
def execute_tcl(command: str) -> dict[str, Any]:
    """Execute a TCL/ECL command and return the output.

    TCL (Terminal Control Language) commands provide system-level operations.
    Dangerous commands are blocked by the safety validator. Some commands
    are disabled in read-only mode.

    Args:
        command: TCL/ECL command to execute
                 Examples:
                 - 'WHO' - Show current user info
                 - 'DATE' - Show current date
                 - 'LISTFILES' - List available files
                 - 'FILE.STAT CUSTOMERS' - Show file statistics

    Returns:
        Dictionary containing command, output, and status.
        Returns error if command is blocked.
    """
    manager = get_connection_manager()
    config = manager.config

    # Validate command safety
    validator = CommandValidator(config.blocked_commands, config.read_only)
    is_valid, error_msg = validator.validate(command)

    if not is_valid:
        return {"error": error_msg, "command": command}

    try:
        output = manager.execute_command(command)

        return {
            "command": command,
            "output": output,
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Error executing TCL command: {e}")
        return {"error": str(e), "command": command}


@mcp.tool()
def get_select_list(query: str, max_ids: int | None = None) -> dict[str, Any]:
    """Execute a SELECT statement and return the list of record IDs.

    This is useful for getting a list of matching records for further processing,
    without retrieving the full record data.

    Args:
        query: SELECT or SSELECT statement
               Example: 'SELECT CUSTOMERS WITH STATE = "CA"'
        max_ids: Maximum IDs to return (optional, defaults to U2_MAX_RECORDS)

    Returns:
        Dictionary containing query, list of record IDs, count,
        and whether results were truncated.
    """
    manager = get_connection_manager()
    config = manager.config

    # Validate query starts with SELECT or SSELECT
    query_upper = query.upper().strip()
    first_word = query_upper.split()[0] if query_upper else ""

    if first_word not in ("SELECT", "SSELECT"):
        return {"error": "Query must start with SELECT or SSELECT", "query": query}

    effective_max = min(max_ids or config.max_records, config.max_records)

    try:
        # Execute the SELECT query
        manager.execute_command(query)

        # Create a List object to iterate through results
        select = manager.create_select_list()

        record_ids: list[str] = []
        truncated = False
        count = 0

        while True:
            record_id = select.next()
            if record_id is None or str(record_id) == "":
                break
            count += 1
            record_ids.append(str(record_id))
            if count >= effective_max:
                truncated = True
                break

        return {
            "query": query,
            "record_ids": record_ids,
            "count": len(record_ids),
            "truncated": truncated,
            "max_ids": effective_max,
        }

    except Exception as e:
        logger.error(f"Error executing select: {e}")
        return {"error": str(e), "query": query}


# =============================================================================
# Phase 3: AI-Optimized Query Validation
# =============================================================================


@mcp.tool()
def validate_query(query: str) -> dict[str, Any]:
    """Validate a RetrieVe/UniQuery statement before execution.

    Checks query syntax and safety without executing it. Useful for
    validating AI-generated queries before running them.

    Args:
        query: Query statement to validate

    Returns:
        Dictionary containing validation results:
        - valid: Boolean indicating if query is valid
        - command: The query command detected (LIST, SELECT, etc.)
        - warnings: List of potential issues
        - suggestions: Helpful hints for common patterns
    """
    manager = get_connection_manager()
    config = manager.config

    result: dict[str, Any] = {
        "query": query,
        "valid": False,
        "command": None,
        "warnings": [],
        "suggestions": [],
        "error": None,
    }

    if not query or not query.strip():
        result["error"] = "Query cannot be empty"
        return result

    query_upper = query.upper().strip()
    parts = query_upper.split()
    first_word = parts[0] if parts else ""

    result["command"] = first_word

    # Check if command is allowed
    if first_word not in ALLOWED_QUERY_COMMANDS:
        result["error"] = (
            f"Command '{first_word}' not allowed. Use: LIST, SELECT, SORT, COUNT, etc."
        )
        return result

    # Validate with safety checks
    validator = CommandValidator(config.blocked_commands, config.read_only)
    is_safe, error_msg = validator.is_query_safe(query)

    if not is_safe:
        result["error"] = error_msg
        return result

    # Basic syntax validation
    warnings = []
    suggestions = []

    # Check for file name after command
    if len(parts) < 2:
        result["error"] = f"{first_word} requires a file name"
        return result

    file_name = parts[1]
    result["file"] = file_name

    # Check for common issues - proper quoting of string values
    if "WITH" in query_upper and "= " in query and '"' not in query and "'" not in query:
        warnings.append("String values should be quoted with double quotes")
        suggestions.append('Example: WITH STATE = "CA" (not WITH STATE = CA)')

    # Check for SELECT without output fields for LIST
    if first_word == "LIST" and "WITH" in query_upper:
        # Check if there are field names after file name but before WITH
        with_idx = query_upper.index("WITH")
        between = query_upper[len(first_word) : with_idx].strip()
        if between == file_name:
            suggestions.append(
                "Consider specifying output fields: LIST FILE field1 field2 WITH ..."
            )

    # Check for BY clause
    if first_word in ("LIST", "SELECT") and "BY" not in query_upper:
        suggestions.append("Consider adding BY clause for sorted results: ... BY field_name")

    # Check for potential multivalue explosion
    if "BY.EXP" not in query_upper and "BY-EXP" not in query_upper and first_word == "LIST":
        suggestions.append("Use BY.EXP to explode multivalues: ... BY.EXP mv_field")

    result["valid"] = True
    result["warnings"] = warnings
    result["suggestions"] = suggestions

    return result
