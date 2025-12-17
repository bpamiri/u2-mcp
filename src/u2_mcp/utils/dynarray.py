"""Dynamic array parsing and formatting for MultiValue data structures."""

from typing import Any

# MultiValue delimiters (standard Pick/Universe characters)
AM = chr(254)  # Attribute Mark (field separator)
VM = chr(253)  # Value Mark (multivalue separator)
SM = chr(252)  # Subvalue Mark

# Type alias for parsed field values
FieldValue = str | list[str] | list[list[str]]


def parse_record(raw_data: str) -> dict[str, FieldValue]:
    """Parse a raw Universe record into structured Python data.

    Preserves multivalue and subvalue structure:
    - Simple values become strings
    - Multivalues become lists of strings
    - Subvalues become lists of lists

    Args:
        raw_data: Raw record data with AM/VM/SM delimiters

    Returns:
        Dictionary mapping field numbers (as strings) to parsed values

    Example:
        >>> parse_record("John" + AM + "555-1234" + VM + "555-5678")
        {"1": "John", "2": ["555-1234", "555-5678"]}
    """
    fields: dict[str, FieldValue] = {}

    if not raw_data:
        return fields

    attributes = raw_data.split(AM)
    for idx, attr in enumerate(attributes, start=1):
        if not attr:
            continue

        if VM in attr:
            # Has multivalues
            multivalues: list[Any] = []
            for mv in attr.split(VM):
                if SM in mv:
                    # Has subvalues
                    multivalues.append(mv.split(SM))
                else:
                    multivalues.append(mv)
            fields[str(idx)] = multivalues
        elif SM in attr:
            # Has subvalues but no multivalues (rare but possible)
            fields[str(idx)] = [attr.split(SM)]
        else:
            # Simple scalar value
            fields[str(idx)] = attr

    return fields


def build_record(fields: dict[str, Any]) -> str:
    """Build a raw Universe record from structured Python data.

    Args:
        fields: Dictionary mapping field numbers (as strings) to values.
                Values can be strings, lists (multivalues), or nested lists (subvalues).

    Returns:
        Raw record string with AM/VM/SM delimiters

    Example:
        >>> build_record({"1": "John", "2": ["555-1234", "555-5678"]})
        "John\\xfe555-1234\\xfd555-5678"
    """
    if not fields:
        return ""

    # Find maximum field number
    max_field = max(int(k) for k in fields)
    attributes: list[str] = []

    for i in range(1, max_field + 1):
        value = fields.get(str(i), "")

        if isinstance(value, list):
            # Handle multivalues
            mv_parts: list[str] = []
            for mv in value:
                if isinstance(mv, list):
                    # Handle subvalues
                    mv_parts.append(SM.join(str(sv) for sv in mv))
                else:
                    mv_parts.append(str(mv))
            attributes.append(VM.join(mv_parts))
        else:
            attributes.append(str(value) if value else "")

    return AM.join(attributes)


def format_record_for_display(
    record_id: str,
    fields: dict[str, FieldValue],
    dictionary: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Format a parsed record for display, optionally mapping field numbers to names.

    Args:
        record_id: The record's ID/key
        fields: Parsed field data from parse_record()
        dictionary: Optional mapping of field numbers to field names

    Returns:
        Formatted record with id, fields, and optionally named_fields
    """
    result: dict[str, Any] = {
        "id": record_id,
        "fields": fields,
    }

    if dictionary:
        named_fields: dict[str, FieldValue] = {}
        for field_num, value in fields.items():
            name = dictionary.get(field_num, f"FIELD_{field_num}")
            named_fields[name] = value
        result["named_fields"] = named_fields

    return result


def extract_field(raw_data: str, field_num: int) -> str:
    """Extract a single field from raw record data.

    Args:
        raw_data: Raw record data
        field_num: Field number to extract (1-based)

    Returns:
        Raw field value (may contain VM/SM delimiters)
    """
    if not raw_data:
        return ""

    attributes = raw_data.split(AM)
    if field_num < 1 or field_num > len(attributes):
        return ""

    return attributes[field_num - 1]


def extract_value(raw_data: str, field_num: int, value_num: int = 1) -> str:
    """Extract a specific multivalue from raw record data.

    Args:
        raw_data: Raw record data
        field_num: Field number (1-based)
        value_num: Value number within the field (1-based)

    Returns:
        Raw value (may contain SM delimiters)
    """
    field = extract_field(raw_data, field_num)
    if not field:
        return ""

    values = field.split(VM)
    if value_num < 1 or value_num > len(values):
        return ""

    return values[value_num - 1]


def extract_subvalue(raw_data: str, field_num: int, value_num: int, subvalue_num: int) -> str:
    """Extract a specific subvalue from raw record data.

    Args:
        raw_data: Raw record data
        field_num: Field number (1-based)
        value_num: Value number (1-based)
        subvalue_num: Subvalue number (1-based)

    Returns:
        Subvalue string
    """
    value = extract_value(raw_data, field_num, value_num)
    if not value:
        return ""

    subvalues = value.split(SM)
    if subvalue_num < 1 or subvalue_num > len(subvalues):
        return ""

    return subvalues[subvalue_num - 1]


def count_values(raw_data: str, field_num: int) -> int:
    """Count the number of multivalues in a field.

    Args:
        raw_data: Raw record data
        field_num: Field number (1-based)

    Returns:
        Number of multivalues (0 if field is empty)
    """
    field = extract_field(raw_data, field_num)
    if not field:
        return 0

    return len(field.split(VM))


def count_subvalues(raw_data: str, field_num: int, value_num: int) -> int:
    """Count the number of subvalues in a multivalue.

    Args:
        raw_data: Raw record data
        field_num: Field number (1-based)
        value_num: Value number (1-based)

    Returns:
        Number of subvalues (0 if value is empty)
    """
    value = extract_value(raw_data, field_num, value_num)
    if not value:
        return 0

    return len(value.split(SM))
