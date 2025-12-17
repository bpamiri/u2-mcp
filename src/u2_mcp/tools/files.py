"""File operation tools for u2-mcp."""

import logging
import re
from typing import Any

from ..connection import FileNotFoundError
from ..server import get_connection_manager, mcp
from ..utils.dynarray import build_record, format_record_for_display, parse_record
from ..utils.export import records_to_csv, records_to_json

logger = logging.getLogger(__name__)


def _parse_file_list(output: str) -> list[str]:
    """Parse LISTFILES or SELECT VOC output into file names.

    Args:
        output: Raw command output

    Returns:
        List of file names
    """
    lines = output.strip().split("\n")
    files: list[str] = []

    for line in lines:
        line = line.strip()
        # Skip empty lines, headers, and separator lines
        if not line or line.startswith("*") or line.startswith("-") or line.startswith("="):
            continue
        # Skip common header lines
        if any(
            header in line.upper()
            for header in ["FILE NAME", "FILENAME", "RECORDS", "LISTED", "SELECTED"]
        ):
            continue

        # Extract first word as file name
        parts = line.split()
        if parts:
            file_name = parts[0]
            # Skip if it looks like a count or number
            if not file_name.isdigit():
                files.append(file_name)

    return files


def _parse_file_stat(output: str) -> dict[str, Any]:
    """Parse FILE.STAT output into structured info.

    Args:
        output: Raw FILE.STAT command output

    Returns:
        Dictionary with file statistics
    """
    info: dict[str, Any] = {
        "type": None,
        "modulo": None,
        "separation": None,
        "record_count": None,
    }

    for line in output.split("\n"):
        line_lower = line.lower()
        if "type" in line_lower and ":" in line:
            info["type"] = line.split(":")[-1].strip()
        elif "modulo" in line_lower and ":" in line:
            try:
                info["modulo"] = int(line.split(":")[-1].strip())
            except ValueError:
                info["modulo"] = line.split(":")[-1].strip()
        elif "separation" in line_lower and ":" in line:
            try:
                info["separation"] = int(line.split(":")[-1].strip())
            except ValueError:
                info["separation"] = line.split(":")[-1].strip()
        elif "record" in line_lower and "count" in line_lower and ":" in line:
            try:
                info["record_count"] = int(line.split(":")[-1].strip())
            except ValueError:
                info["record_count"] = line.split(":")[-1].strip()
        # Also check for numeric values at end of lines
        elif "records" in line_lower:
            match = re.search(r"(\d+)\s*records?", line_lower)
            if match:
                info["record_count"] = int(match.group(1))

    return info


@mcp.tool()
def list_files(pattern: str = "*") -> dict[str, Any]:
    """List available files in the current Universe account.

    Args:
        pattern: File name pattern to match (supports * wildcard).
                 Default "*" lists all files.

    Returns:
        Dictionary containing list of matching file names and count.
    """
    manager = get_connection_manager()

    try:
        if pattern == "*":
            output = manager.execute_command("LISTFILES")
        else:
            # Convert simple wildcard to UniQuery LIKE pattern
            like_pattern = pattern.replace("*", "...")
            output = manager.execute_command(
                f'SELECT VOC WITH @ID LIKE "{like_pattern}" AND WITH F1 = "F"'
            )

        files = _parse_file_list(output)

        return {
            "files": files,
            "count": len(files),
            "pattern": pattern,
        }
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        return {"error": str(e), "pattern": pattern}


@mcp.tool()
def read_record(file_name: str, record_id: str) -> dict[str, Any]:
    """Read a single record from a Universe file.

    The record is returned with fields parsed into structured JSON,
    preserving multivalue and subvalue structure.

    Args:
        file_name: Name of the Universe file
        record_id: Record ID (key) to read

    Returns:
        Dictionary containing record id, fields (by number), and optionally
        the raw record data. Returns error if record not found.
    """
    manager = get_connection_manager()

    try:
        file_handle = manager.open_file(file_name)
        raw_data = file_handle.read(record_id)

        if raw_data is None or str(raw_data) == "":
            return {
                "error": "Record not found",
                "file": file_name,
                "id": record_id,
            }

        fields = parse_record(str(raw_data))
        return format_record_for_display(record_id, fields)

    except FileNotFoundError as e:
        return {"error": str(e), "file": file_name, "id": record_id}
    except Exception as e:
        logger.error(f"Error reading record: {e}")
        return {"error": str(e), "file": file_name, "id": record_id}


@mcp.tool()
def read_records(file_name: str, record_ids: list[str]) -> dict[str, Any]:
    """Read multiple records from a Universe file efficiently.

    Args:
        file_name: Name of the Universe file
        record_ids: List of record IDs to read

    Returns:
        Dictionary containing file name, list of records, count, and any errors.
        Each record includes id and fields. Records not found are listed in errors.
    """
    manager = get_connection_manager()
    max_records = manager.config.max_records

    # Enforce limit
    if len(record_ids) > max_records:
        return {
            "error": f"Requested {len(record_ids)} records, maximum is {max_records}",
            "file": file_name,
        }

    try:
        file_handle = manager.open_file(file_name)
        records: list[dict[str, Any]] = []
        errors: list[dict[str, str]] = []

        for rid in record_ids:
            try:
                raw_data = file_handle.read(rid)
                if raw_data is not None and str(raw_data) != "":
                    fields = parse_record(str(raw_data))
                    records.append(format_record_for_display(rid, fields))
                else:
                    errors.append({"id": rid, "error": "Not found"})
            except Exception as e:
                errors.append({"id": rid, "error": str(e)})

        result: dict[str, Any] = {
            "file": file_name,
            "records": records,
            "count": len(records),
        }
        if errors:
            result["errors"] = errors

        return result

    except FileNotFoundError as e:
        return {"error": str(e), "file": file_name}
    except Exception as e:
        logger.error(f"Error reading records: {e}")
        return {"error": str(e), "file": file_name}


@mcp.tool()
def write_record(
    file_name: str,
    record_id: str,
    fields: dict[str, Any],
    confirm: bool = False,
) -> dict[str, Any]:
    """Write or update a record in a Universe file.

    Args:
        file_name: Target file name
        record_id: Record ID to create or update
        fields: Field values as JSON object. Keys are field numbers as strings,
                values can be strings (single value), lists (multivalues),
                or nested lists (subvalues).
        confirm: Must be True to execute the write. This is a safety measure.

    Returns:
        Status of the write operation. Requires confirm=True to execute.
        Disabled in read-only mode.

    Example fields:
        {"1": "John Doe", "2": ["555-1234", "555-5678"], "3": "CA"}
    """
    manager = get_connection_manager()

    # Safety checks
    if manager.config.read_only:
        return {"error": "Write operations disabled in read-only mode"}

    if not confirm:
        return {
            "status": "confirmation_required",
            "message": "Set confirm=True to execute write operation",
            "file": file_name,
            "id": record_id,
            "fields_to_write": len(fields),
        }

    try:
        file_handle = manager.open_file(file_name)
        raw_data = build_record(fields)
        file_handle.write(record_id, raw_data)

        return {
            "status": "success",
            "file": file_name,
            "id": record_id,
            "fields_written": len(fields),
        }

    except FileNotFoundError as e:
        return {"error": str(e), "file": file_name, "id": record_id}
    except Exception as e:
        logger.error(f"Error writing record: {e}")
        return {"error": str(e), "file": file_name, "id": record_id}


@mcp.tool()
def delete_record(
    file_name: str,
    record_id: str,
    confirm: bool = False,
) -> dict[str, Any]:
    """Delete a record from a Universe file.

    Args:
        file_name: Target file name
        record_id: Record ID to delete
        confirm: Must be True to execute the delete. This is a safety measure.

    Returns:
        Status of the delete operation. Requires confirm=True to execute.
        Disabled in read-only mode.
    """
    manager = get_connection_manager()

    # Safety checks
    if manager.config.read_only:
        return {"error": "Delete operations disabled in read-only mode"}

    if not confirm:
        return {
            "status": "confirmation_required",
            "message": "Set confirm=True to execute delete operation",
            "file": file_name,
            "id": record_id,
        }

    try:
        file_handle = manager.open_file(file_name)
        file_handle.delete(record_id)

        return {
            "status": "deleted",
            "file": file_name,
            "id": record_id,
        }

    except FileNotFoundError as e:
        return {"error": str(e), "file": file_name, "id": record_id}
    except Exception as e:
        logger.error(f"Error deleting record: {e}")
        return {"error": str(e), "file": file_name, "id": record_id}


@mcp.tool()
def get_file_info(file_name: str) -> dict[str, Any]:
    """Get information about a Universe file.

    Returns file statistics including type, modulo, separation, and record count.

    Args:
        file_name: Name of the Universe file

    Returns:
        Dictionary containing file statistics and metadata.
    """
    manager = get_connection_manager()

    try:
        output = manager.execute_command(f"FILE.STAT {file_name}")

        info = _parse_file_stat(output)
        info["file"] = file_name
        info["raw_output"] = output

        return info

    except Exception as e:
        logger.error(f"Error getting file info: {e}")
        return {"error": str(e), "file": file_name}


# =============================================================================
# Phase 3: Export Tools
# =============================================================================


@mcp.tool()
def export_to_json(
    file_name: str,
    record_ids: list[str],
    expand_mv: bool = False,
) -> dict[str, Any]:
    """Export records from a Universe file to JSON format.

    Reads the specified records and returns them as a JSON string.
    Useful for data analysis and integration with other tools.

    Args:
        file_name: Name of the Universe file
        record_ids: List of record IDs to export
        expand_mv: If True, expand multivalues into separate objects.
                   If False (default), preserve multivalue arrays.

    Returns:
        Dictionary containing:
        - status: success or error
        - format: "json"
        - record_count: Number of records exported
        - data: JSON string of the exported records
    """
    manager = get_connection_manager()
    max_records = manager.config.max_records

    if len(record_ids) > max_records:
        return {
            "error": f"Requested {len(record_ids)} records, maximum is {max_records}",
            "file": file_name,
        }

    try:
        file_handle = manager.open_file(file_name)
        records: list[dict[str, Any]] = []

        for rid in record_ids:
            try:
                raw_data = file_handle.read(rid)
                if raw_data is not None and str(raw_data) != "":
                    fields = parse_record(str(raw_data))
                    records.append(format_record_for_display(rid, fields))
            except Exception:
                continue

        json_output = records_to_json(records, expand_mv=expand_mv, pretty=True)

        return {
            "status": "success",
            "file": file_name,
            "format": "json",
            "record_count": len(records),
            "expand_mv": expand_mv,
            "data": json_output,
        }

    except FileNotFoundError as e:
        return {"error": str(e), "file": file_name}
    except Exception as e:
        logger.error(f"Error exporting to JSON: {e}")
        return {"error": str(e), "file": file_name}


@mcp.tool()
def export_to_csv(
    file_name: str,
    record_ids: list[str],
    expand_mv: bool = False,
    mv_delimiter: str = "|",
) -> dict[str, Any]:
    """Export records from a Universe file to CSV format.

    Reads the specified records and returns them as a CSV string.
    Useful for spreadsheet import and data analysis.

    Args:
        file_name: Name of the Universe file
        record_ids: List of record IDs to export
        expand_mv: If True, expand multivalues into separate rows.
                   If False (default), join multivalues with delimiter.
        mv_delimiter: Delimiter for multivalues when expand_mv=False.
                      Default is "|".

    Returns:
        Dictionary containing:
        - status: success or error
        - format: "csv"
        - record_count: Number of records exported
        - row_count: Number of rows in CSV (may differ if expand_mv=True)
        - data: CSV string of the exported records
    """
    manager = get_connection_manager()
    max_records = manager.config.max_records

    if len(record_ids) > max_records:
        return {
            "error": f"Requested {len(record_ids)} records, maximum is {max_records}",
            "file": file_name,
        }

    try:
        file_handle = manager.open_file(file_name)
        records: list[dict[str, Any]] = []

        for rid in record_ids:
            try:
                raw_data = file_handle.read(rid)
                if raw_data is not None and str(raw_data) != "":
                    fields = parse_record(str(raw_data))
                    records.append(format_record_for_display(rid, fields))
            except Exception:
                continue

        csv_output = records_to_csv(
            records,
            expand_mv=expand_mv,
            mv_delimiter=mv_delimiter,
            include_header=True,
        )

        # Count rows (excluding header)
        row_count = csv_output.count("\n") - 1 if csv_output else 0

        return {
            "status": "success",
            "file": file_name,
            "format": "csv",
            "record_count": len(records),
            "row_count": row_count,
            "expand_mv": expand_mv,
            "mv_delimiter": mv_delimiter if not expand_mv else None,
            "data": csv_output,
        }

    except FileNotFoundError as e:
        return {"error": str(e), "file": file_name}
    except Exception as e:
        logger.error(f"Error exporting to CSV: {e}")
        return {"error": str(e), "file": file_name}
