"""Dictionary and schema discovery tools for u2-mcp."""

import logging
from typing import Any

from ..server import get_connection_manager, mcp
from ..utils.dynarray import parse_record

logger = logging.getLogger(__name__)


def _parse_dict_item(item_id: str, parsed: dict[str, Any]) -> dict[str, Any]:
    """Parse a dictionary item record into structured format.

    Universe dictionary items have standard field positions:
    - Field 1: Type (D, I, A, S, X, PH, etc.)
    - Field 2: Field number (for D-type) or expression (for I-type)
    - Field 3: Conversion code
    - Field 4: Column heading
    - Field 5: Format specification
    - Field 6: Single/Multi indicator (S or M)
    - Field 7: Association name

    Args:
        item_id: Dictionary item name
        parsed: Parsed record fields

    Returns:
        Structured dictionary item info
    """
    item_type = str(parsed.get("1", "")).upper()

    item: dict[str, Any] = {
        "name": item_id,
        "type": item_type,
    }

    # D-type: Data field with position number
    if item_type == "D":
        item["field_number"] = parsed.get("2", "")
        item["conversion"] = parsed.get("3", "")
        item["heading"] = parsed.get("4", "")
        item["format"] = parsed.get("5", "")
        item["single_multi"] = parsed.get("6", "S")
        item["association"] = parsed.get("7", "")

    # I-type: Correlative/calculated field
    elif item_type == "I":
        item["expression"] = parsed.get("2", "")
        item["conversion"] = parsed.get("3", "")
        item["heading"] = parsed.get("4", "")
        item["format"] = parsed.get("5", "")
        item["single_multi"] = parsed.get("6", "S")

    # A-type: Algebraic expression (similar to I-type)
    elif item_type == "A":
        item["expression"] = parsed.get("2", "")
        item["conversion"] = parsed.get("3", "")
        item["heading"] = parsed.get("4", "")
        item["format"] = parsed.get("5", "")

    # S-type: Synonym
    elif item_type == "S":
        item["synonym_of"] = parsed.get("2", "")

    # PH-type: Phrase
    elif item_type == "PH":
        item["phrase"] = parsed.get("2", "")

    # X-type: Reserved/unused
    elif item_type == "X":
        item["description"] = "Reserved field position"

    return item


@mcp.tool()
def list_dictionary(file_name: str, include_system: bool = False) -> dict[str, Any]:
    """List all dictionary items for a Universe file.

    Returns D-type (data), I-type (calculated), and other field definitions
    from the file's dictionary.

    Args:
        file_name: Name of the Universe file
        include_system: If True, include system dictionary items (@ prefixed)

    Returns:
        Dictionary containing file name, list of dictionary items with their
        types, and total count.
    """
    manager = get_connection_manager()

    try:
        dict_file_name = f"DICT {file_name}"

        # Use LIST to get dictionary item IDs - more reliable than SELECT
        list_output = manager.execute_command(f"LIST {dict_file_name} @ID SAMPLE 1000")

        # Parse the output to extract item IDs
        item_ids: list[str] = []
        for line in list_output.split("\n"):
            line = line.strip()
            # Skip empty lines, headers, and summary lines
            if not line or line.startswith("LIST") or "listed" in line.lower():
                continue
            if line.startswith("-") or line.startswith("=") or line.startswith("*"):
                continue
            # Extract the first word as the item ID
            parts = line.split()
            if parts:
                item_id = parts[0]
                # Skip system items unless requested
                if not include_system and item_id.startswith("@"):
                    continue
                item_ids.append(item_id)

        items: list[dict[str, Any]] = []
        dict_file = manager.open_file(dict_file_name)

        for item_id in item_ids:
            try:
                raw = dict_file.read(item_id)
                if raw:
                    parsed = parse_record(str(raw))
                    item = _parse_dict_item(item_id, parsed)
                    items.append(item)
            except Exception as e:
                items.append({"name": item_id, "type": "error", "error": str(e)})

        # Sort by type, then by field number for D-types
        def sort_key(item: dict[str, Any]) -> tuple[int, int, str]:
            type_order = {"D": 0, "I": 1, "A": 2, "S": 3, "PH": 4, "X": 5}
            t = type_order.get(item.get("type", ""), 99)
            fn = item.get("field_number", "999")
            try:
                fn_num = int(fn)
            except (ValueError, TypeError):
                fn_num = 999
            return (t, fn_num, item.get("name", ""))

        items.sort(key=sort_key)

        return {
            "file": file_name,
            "dictionary_items": items,
            "count": len(items),
        }

    except Exception as e:
        logger.error(f"Error listing dictionary: {e}")
        return {"error": str(e), "file": file_name}


@mcp.tool()
def get_field_definition(file_name: str, field_name: str) -> dict[str, Any]:
    """Get detailed definition for a specific dictionary field.

    Returns the complete field definition including type, field number,
    conversion code, format, heading, and other attributes.

    Args:
        file_name: Name of the Universe file
        field_name: Dictionary field/item name

    Returns:
        Detailed field definition or error if not found.
    """
    manager = get_connection_manager()

    try:
        dict_file_name = f"DICT {file_name}"
        dict_file = manager.open_file(dict_file_name)

        raw = dict_file.read(field_name)

        if not raw or str(raw) == "":
            return {
                "error": f"Field '{field_name}' not found in dictionary",
                "file": file_name,
            }

        parsed = parse_record(str(raw))
        definition = _parse_dict_item(field_name, parsed)
        definition["file"] = file_name

        return definition

    except Exception as e:
        logger.error(f"Error getting field definition: {e}")
        return {"error": str(e), "file": file_name, "field": field_name}


@mcp.tool()
def describe_file(file_name: str) -> dict[str, Any]:
    """Get a comprehensive description of a Universe file.

    Combines file statistics with dictionary information to provide
    full context about the file structure. Useful for understanding
    data structure before querying.

    Args:
        file_name: Name of the Universe file

    Returns:
        Dictionary containing file stats, field definitions, and counts.
    """
    manager = get_connection_manager()

    try:
        # Get file statistics
        file_stat_output = manager.execute_command(f"FILE.STAT {file_name}")

        # Get dictionary items (D and I types only for cleaner output)
        dict_file_name = f"DICT {file_name}"
        dict_file = manager.open_file(dict_file_name)

        # Use LIST to get dictionary item IDs - more reliable than SELECT
        list_output = manager.execute_command(f"LIST {dict_file_name} @ID SAMPLE 1000")

        # Parse the output to extract item IDs
        item_ids: list[str] = []
        for line in list_output.split("\n"):
            line = line.strip()
            if not line or line.startswith("LIST") or "listed" in line.lower():
                continue
            if line.startswith("-") or line.startswith("=") or line.startswith("*"):
                continue
            parts = line.split()
            if parts:
                item_id = parts[0]
                if not item_id.startswith("@"):
                    item_ids.append(item_id)

        fields: list[dict[str, Any]] = []
        for item_id in item_ids:
            try:
                raw = dict_file.read(item_id)
                if raw:
                    parsed = parse_record(str(raw))
                    item_type = str(parsed.get("1", "")).upper()

                    # Only include data-defining items
                    if item_type in ("D", "I", "A"):
                        item = _parse_dict_item(item_id, parsed)
                        fields.append(item)
            except Exception:
                pass

        # Sort fields: D-types by field number first, then I-types
        def sort_key(f: dict[str, Any]) -> tuple[int, int, str]:
            type_order = 0 if f.get("type") == "D" else 1
            fn = f.get("field_number", "999")
            try:
                fn_num = int(fn)
            except (ValueError, TypeError):
                fn_num = 999
            return (type_order, fn_num, f.get("name", ""))

        fields.sort(key=sort_key)

        # Build description
        d_count = sum(1 for f in fields if f.get("type") == "D")
        i_count = sum(1 for f in fields if f.get("type") == "I")

        description = (
            f"Universe file '{file_name}' with {d_count} data fields "
            f"and {i_count} calculated fields"
        )
        return {
            "file": file_name,
            "description": description,
            "file_stats": file_stat_output,
            "fields": fields,
            "field_count": len(fields),
            "data_field_count": d_count,
            "calculated_field_count": i_count,
        }

    except Exception as e:
        logger.error(f"Error describing file: {e}")
        return {"error": str(e), "file": file_name}


# =============================================================================
# Phase 2: Advanced Schema Discovery
# =============================================================================


@mcp.tool()
def analyze_file_structure(
    file_name: str,
    sample_size: int = 100,
) -> dict[str, Any]:
    """Analyze file structure by sampling records to infer field usage patterns.

    Samples records from the file to detect:
    - Which fields are populated
    - Multivalue patterns
    - Data types and common values

    Useful when dictionary is incomplete or for understanding actual data usage.

    Args:
        file_name: Name of the Universe file to analyze
        sample_size: Number of records to sample (default 100)

    Returns:
        Analysis results including field usage statistics and patterns.
    """
    manager = get_connection_manager()
    max_records = min(sample_size, manager.config.max_records)

    try:
        file_handle = manager.open_file(file_name)

        # Get sample of record IDs
        manager.execute_command(f"SELECT {file_name} SAMPLE {max_records}")
        select = manager.create_select_list()

        field_stats: dict[str, dict[str, Any]] = {}
        records_analyzed = 0

        while True:
            record_id = select.next()
            if record_id is None or str(record_id) == "":
                break
            try:
                raw = file_handle.read(record_id)
                if raw:
                    parsed = parse_record(str(raw))
                    records_analyzed += 1

                    for field_num, value in parsed.items():
                        if field_num not in field_stats:
                            field_stats[field_num] = {
                                "field_number": field_num,
                                "populated_count": 0,
                                "has_multivalues": False,
                                "max_values": 0,
                                "sample_values": [],
                            }

                        stats = field_stats[field_num]
                        stats["populated_count"] += 1

                        # Check for multivalues
                        if isinstance(value, list):
                            stats["has_multivalues"] = True
                            stats["max_values"] = max(stats["max_values"], len(value))
                        else:
                            stats["max_values"] = max(stats["max_values"], 1)

                        # Collect sample values (up to 5)
                        if len(stats["sample_values"]) < 5:
                            if isinstance(value, list):
                                stats["sample_values"].append(value[0] if value else "")
                            else:
                                stats["sample_values"].append(str(value)[:50])

            except Exception:
                continue

        # Convert to list and sort by field number
        fields_list = list(field_stats.values())
        fields_list.sort(key=lambda f: int(f["field_number"]))

        # Calculate usage percentages
        for field in fields_list:
            field["usage_percent"] = (
                round(field["populated_count"] / records_analyzed * 100, 1)
                if records_analyzed > 0
                else 0
            )

        return {
            "file": file_name,
            "records_analyzed": records_analyzed,
            "sample_size": max_records,
            "fields_detected": len(fields_list),
            "field_analysis": fields_list,
        }

    except Exception as e:
        logger.error(f"Error analyzing file structure: {e}")
        return {"error": str(e), "file": file_name}


@mcp.tool()
def get_account_info() -> dict[str, Any]:
    """Get information about the current Universe account.

    Returns account-level metadata including available files,
    VOC entries, and system information.

    Returns:
        Dictionary containing account information, file list,
        and system details.
    """
    manager = get_connection_manager()

    try:
        # Get current account info
        who_output = manager.execute_command("WHO")

        # Get system date/time
        date_output = manager.execute_command("DATE")
        time_output = manager.execute_command("TIME")

        # Get file list
        files_output = manager.execute_command("LISTFILES")

        # Parse file list
        files = []
        for line in files_output.split("\n"):
            line = line.strip()
            if line and not line.startswith("*") and not line.startswith("-"):
                parts = line.split()
                if parts and not parts[0].isdigit():
                    files.append(parts[0])

        # Get connection info
        connections = manager.list_connections()
        conn_info = None
        if connections:
            conn = list(connections.values())[0]
            conn_info = {
                "host": conn.host,
                "account": conn.account,
                "service": conn.service,
                "connected_at": conn.connected_at.isoformat(),
            }

        return {
            "who": who_output.strip(),
            "date": date_output.strip(),
            "time": time_output.strip(),
            "file_count": len(files),
            "files": files[:50],  # Limit to first 50
            "files_truncated": len(files) > 50,
            "connection": conn_info,
            "read_only_mode": manager.config.read_only,
            "in_transaction": manager.in_transaction,
        }

    except Exception as e:
        logger.error(f"Error getting account info: {e}")
        return {"error": str(e)}
