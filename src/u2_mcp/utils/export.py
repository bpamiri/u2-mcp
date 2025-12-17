"""Data export utilities for u2-mcp."""

import csv
import io
import json
from typing import Any

from .dynarray import FieldValue


def flatten_multivalue(value: FieldValue, delimiter: str = "|") -> str:
    """Flatten a multivalue field to a delimited string.

    Args:
        value: Field value (string, list, or nested list)
        delimiter: Delimiter for multivalues

    Returns:
        Flattened string representation
    """
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, list):
                # Subvalues - join with a different delimiter
                parts.append(";".join(str(sv) for sv in item))
            else:
                parts.append(str(item))
        return delimiter.join(parts)
    return str(value)


def expand_multivalues(record: dict[str, Any]) -> list[dict[str, Any]]:
    """Expand a record with multivalues into multiple rows.

    Each multivalue combination becomes a separate row.
    Useful for exporting to flat formats like CSV.

    Args:
        record: Record with fields that may contain multivalues

    Returns:
        List of expanded records (one per multivalue combination)
    """
    fields = record.get("fields", record)
    record_id = record.get("id", "")

    # Find maximum multivalue count across all fields
    max_count = 1
    for value in fields.values():
        if isinstance(value, list):
            max_count = max(max_count, len(value))

    # Generate expanded rows
    rows = []
    for i in range(max_count):
        row: dict[str, Any] = {"_id": record_id, "_mv_index": i + 1}
        for field_num, value in fields.items():
            if isinstance(value, list):
                if i < len(value):
                    cell = value[i]
                    # Handle subvalues
                    if isinstance(cell, list):
                        row[field_num] = ";".join(str(sv) for sv in cell)
                    else:
                        row[field_num] = str(cell)
                else:
                    row[field_num] = ""
            else:
                row[field_num] = str(value) if i == 0 else ""
        rows.append(row)

    return rows


def records_to_json(
    records: list[dict[str, Any]],
    expand_mv: bool = False,
    pretty: bool = True,
) -> str:
    """Convert records to JSON string.

    Args:
        records: List of record dictionaries
        expand_mv: If True, expand multivalues into separate objects
        pretty: If True, format JSON with indentation

    Returns:
        JSON string
    """
    if expand_mv:
        expanded = []
        for record in records:
            expanded.extend(expand_multivalues(record))
        data = expanded
    else:
        data = records

    if pretty:
        return json.dumps(data, indent=2, ensure_ascii=False)
    return json.dumps(data, ensure_ascii=False)


def records_to_csv(
    records: list[dict[str, Any]],
    expand_mv: bool = False,
    mv_delimiter: str = "|",
    include_header: bool = True,
    field_names: dict[str, str] | None = None,
) -> str:
    """Convert records to CSV string.

    Args:
        records: List of record dictionaries
        expand_mv: If True, expand multivalues into separate rows
        mv_delimiter: Delimiter for multivalues when not expanding
        include_header: If True, include header row
        field_names: Optional mapping of field numbers to names

    Returns:
        CSV string
    """
    if not records:
        return ""

    output = io.StringIO()

    if expand_mv:
        # Expand multivalues into rows
        expanded_records = []
        for record in records:
            expanded_records.extend(expand_multivalues(record))

        if not expanded_records:
            return ""

        # Get all field keys
        all_keys: set[str] = set()
        for rec in expanded_records:
            all_keys.update(rec.keys())

        # Sort keys: _id first, then _mv_index, then numeric field numbers
        def key_sort(k: str) -> tuple[int, int]:
            if k == "_id":
                return (0, 0)
            if k == "_mv_index":
                return (0, 1)
            try:
                return (1, int(k))
            except ValueError:
                return (2, 0)

        columns = sorted(all_keys, key=key_sort)

        # Apply field names if provided
        header = []
        for col in columns:
            if col == "_id":
                header.append("ID")
            elif col == "_mv_index":
                header.append("MV_INDEX")
            elif field_names and col in field_names:
                header.append(field_names[col])
            else:
                header.append(f"FIELD_{col}")

        writer = csv.writer(output)
        if include_header:
            writer.writerow(header)

        for rec in expanded_records:
            row = [rec.get(col, "") for col in columns]
            writer.writerow(row)

    else:
        # Flatten multivalues into delimited strings
        # Get all field keys from all records
        all_keys = set()
        for record in records:
            fields = record.get("fields", record)
            all_keys.update(fields.keys())

        # Sort field keys numerically
        columns = sorted(all_keys, key=lambda k: (int(k) if k.isdigit() else 999, k))

        # Build header
        header = ["ID"]
        for col in columns:
            if field_names and col in field_names:
                header.append(field_names[col])
            else:
                header.append(f"FIELD_{col}")

        writer = csv.writer(output)
        if include_header:
            writer.writerow(header)

        for record in records:
            fields = record.get("fields", record)
            record_id = record.get("id", "")
            row = [record_id]
            for col in columns:
                value = fields.get(col, "")
                row.append(flatten_multivalue(value, mv_delimiter))
            writer.writerow(row)

    return output.getvalue()


def format_for_display(
    records: list[dict[str, Any]],
    format_type: str = "json",
    **kwargs: Any,
) -> str:
    """Format records for display in specified format.

    Args:
        records: List of record dictionaries
        format_type: Output format ("json" or "csv")
        **kwargs: Additional arguments passed to format function

    Returns:
        Formatted string
    """
    if format_type.lower() == "csv":
        return records_to_csv(records, **kwargs)
    else:
        return records_to_json(records, **kwargs)
