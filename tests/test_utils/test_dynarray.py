"""Tests for u2_mcp.utils.dynarray module."""

from u2_mcp.utils.dynarray import (
    AM,
    SM,
    VM,
    build_record,
    count_subvalues,
    count_values,
    extract_field,
    extract_subvalue,
    extract_value,
    format_record_for_display,
    parse_record,
)


class TestParseRecord:
    """Tests for parse_record function."""

    def test_parse_simple_record(self):
        """Test parsing a simple record with scalar fields."""
        raw = "John Doe" + AM + "123 Main St" + AM + "CA"
        fields = parse_record(raw)

        assert fields["1"] == "John Doe"
        assert fields["2"] == "123 Main St"
        assert fields["3"] == "CA"

    def test_parse_multivalue_record(self):
        """Test parsing a record with multivalues."""
        raw = "John Doe" + AM + "555-1234" + VM + "555-5678" + AM + "CA"
        fields = parse_record(raw)

        assert fields["1"] == "John Doe"
        assert fields["2"] == ["555-1234", "555-5678"]
        assert fields["3"] == "CA"

    def test_parse_subvalue_record(self):
        """Test parsing a record with subvalues."""
        raw = "Value1" + SM + "Value2"
        fields = parse_record(raw)

        # Single field with subvalues but no multivalues
        assert fields["1"] == [["Value1", "Value2"]]

    def test_parse_complex_record(self):
        """Test parsing a record with multivalues and subvalues."""
        raw = "ACME" + AM + "John" + VM + "Jane" + AM + "555-1111" + SM + "ext1" + VM + "555-2222"
        fields = parse_record(raw)

        assert fields["1"] == "ACME"
        assert fields["2"] == ["John", "Jane"]
        assert fields["3"] == [["555-1111", "ext1"], "555-2222"]

    def test_parse_empty_record(self):
        """Test parsing an empty record."""
        fields = parse_record("")
        assert fields == {}

    def test_parse_record_with_empty_fields(self):
        """Test parsing a record with some empty fields."""
        raw = "Value1" + AM + AM + "Value3"
        fields = parse_record(raw)

        assert fields["1"] == "Value1"
        assert "2" not in fields  # Empty field not included
        assert fields["3"] == "Value3"


class TestBuildRecord:
    """Tests for build_record function."""

    def test_build_simple_record(self):
        """Test building a simple record."""
        fields = {"1": "John Doe", "2": "123 Main St", "3": "CA"}
        raw = build_record(fields)

        assert raw == "John Doe" + AM + "123 Main St" + AM + "CA"

    def test_build_multivalue_record(self):
        """Test building a record with multivalues."""
        fields = {"1": "John Doe", "2": ["555-1234", "555-5678"], "3": "CA"}
        raw = build_record(fields)

        expected = "John Doe" + AM + "555-1234" + VM + "555-5678" + AM + "CA"
        assert raw == expected

    def test_build_subvalue_record(self):
        """Test building a record with subvalues."""
        fields = {"1": [["Value1", "Value2"]]}
        raw = build_record(fields)

        expected = "Value1" + SM + "Value2"
        assert raw == expected

    def test_build_empty_record(self):
        """Test building an empty record."""
        raw = build_record({})
        assert raw == ""

    def test_build_record_with_gaps(self):
        """Test building a record with non-consecutive field numbers."""
        fields = {"1": "First", "3": "Third"}
        raw = build_record(fields)

        # Field 2 should be empty
        assert raw == "First" + AM + "" + AM + "Third"


class TestRoundTrip:
    """Tests for parse/build round-trip consistency."""

    def test_round_trip_simple(self):
        """Test that parse then build returns original data."""
        original = "John Doe" + AM + "123 Main St" + AM + "CA"
        fields = parse_record(original)
        rebuilt = build_record(fields)

        assert rebuilt == original

    def test_round_trip_multivalue(self):
        """Test round-trip with multivalues."""
        original = "John Doe" + AM + "555-1234" + VM + "555-5678"
        fields = parse_record(original)
        rebuilt = build_record(fields)

        assert rebuilt == original


class TestFormatRecordForDisplay:
    """Tests for format_record_for_display function."""

    def test_format_basic(self):
        """Test basic formatting."""
        fields = {"1": "John Doe", "2": "CA"}
        result = format_record_for_display("CUST001", fields)

        assert result["id"] == "CUST001"
        assert result["fields"] == fields
        assert "named_fields" not in result

    def test_format_with_dictionary(self):
        """Test formatting with dictionary mapping."""
        fields = {"1": "John Doe", "2": "CA"}
        dictionary = {"1": "NAME", "2": "STATE"}
        result = format_record_for_display("CUST001", fields, dictionary)

        assert result["id"] == "CUST001"
        assert result["fields"] == fields
        assert result["named_fields"]["NAME"] == "John Doe"
        assert result["named_fields"]["STATE"] == "CA"


class TestExtractFunctions:
    """Tests for field/value/subvalue extraction functions."""

    def test_extract_field(self):
        """Test extracting a single field."""
        raw = "Field1" + AM + "Field2" + AM + "Field3"

        assert extract_field(raw, 1) == "Field1"
        assert extract_field(raw, 2) == "Field2"
        assert extract_field(raw, 3) == "Field3"
        assert extract_field(raw, 4) == ""

    def test_extract_value(self):
        """Test extracting a multivalue."""
        raw = "Field1" + AM + "Value1" + VM + "Value2" + VM + "Value3"

        assert extract_value(raw, 2, 1) == "Value1"
        assert extract_value(raw, 2, 2) == "Value2"
        assert extract_value(raw, 2, 3) == "Value3"
        assert extract_value(raw, 2, 4) == ""

    def test_extract_subvalue(self):
        """Test extracting a subvalue."""
        raw = "Field1" + AM + "Sub1" + SM + "Sub2" + SM + "Sub3"

        assert extract_subvalue(raw, 2, 1, 1) == "Sub1"
        assert extract_subvalue(raw, 2, 1, 2) == "Sub2"
        assert extract_subvalue(raw, 2, 1, 3) == "Sub3"

    def test_count_values(self):
        """Test counting multivalues."""
        raw = "Field1" + AM + "V1" + VM + "V2" + VM + "V3"

        assert count_values(raw, 1) == 1
        assert count_values(raw, 2) == 3
        assert count_values(raw, 3) == 0

    def test_count_subvalues(self):
        """Test counting subvalues."""
        raw = "Field1" + AM + "S1" + SM + "S2" + SM + "S3"

        assert count_subvalues(raw, 2, 1) == 3
        assert count_subvalues(raw, 1, 1) == 1
