"""Tests for u2_mcp.utils.safety module."""

from u2_mcp.utils.safety import ALLOWED_QUERY_COMMANDS, CommandValidator


class TestCommandValidator:
    """Tests for CommandValidator class."""

    def test_validate_allowed_command(self):
        """Test that safe commands pass validation."""
        validator = CommandValidator([], read_only=False)

        is_valid, error = validator.validate("WHO")
        assert is_valid is True
        assert error == ""

    def test_validate_blocked_command(self):
        """Test that blocked commands fail validation."""
        validator = CommandValidator(["DELETE.FILE"], read_only=False)

        is_valid, error = validator.validate("DELETE.FILE MYFILE")
        assert is_valid is False
        assert "blocked" in error.lower()

    def test_validate_default_blocked_commands(self):
        """Test that default blocked commands are enforced."""
        validator = CommandValidator([], read_only=False)

        # DELETE.FILE is in DEFAULT_BLOCKED_COMMANDS
        is_valid, error = validator.validate("DELETE.FILE TEST")
        assert is_valid is False

    def test_validate_read_only_blocks_writes(self):
        """Test that read-only mode blocks write commands."""
        validator = CommandValidator([], read_only=True)

        is_valid, error = validator.validate("DELETE CUSTOMERS CUST001")
        assert is_valid is False
        assert "read-only" in error.lower()

    def test_validate_read_only_allows_reads(self):
        """Test that read-only mode allows read commands."""
        validator = CommandValidator([], read_only=True)

        is_valid, error = validator.validate("WHO")
        assert is_valid is True

    def test_validate_empty_command(self):
        """Test that empty commands fail validation."""
        validator = CommandValidator([], read_only=False)

        is_valid, error = validator.validate("")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_is_query_safe_list(self):
        """Test that LIST queries are safe."""
        validator = CommandValidator([], read_only=False)

        is_safe, error = validator.is_query_safe('LIST CUSTOMERS WITH STATE = "CA"')
        assert is_safe is True

    def test_is_query_safe_select(self):
        """Test that SELECT queries are safe."""
        validator = CommandValidator([], read_only=False)

        is_safe, error = validator.is_query_safe("SELECT ORDERS")
        assert is_safe is True

    def test_is_query_safe_count(self):
        """Test that COUNT queries are safe."""
        validator = CommandValidator([], read_only=False)

        is_safe, error = validator.is_query_safe("COUNT INVOICES")
        assert is_safe is True

    def test_is_query_safe_sort(self):
        """Test that SORT queries are safe."""
        validator = CommandValidator([], read_only=False)

        is_safe, error = validator.is_query_safe("SORT CUSTOMERS BY NAME")
        assert is_safe is True

    def test_is_query_unsafe_delete(self):
        """Test that DELETE command in query context is blocked."""
        validator = CommandValidator([], read_only=False)

        is_safe, error = validator.is_query_safe("DELETE CUSTOMERS")
        assert is_safe is False
        assert "not allowed" in error.lower()

    def test_is_query_unsafe_copy(self):
        """Test that COPY command is blocked as query."""
        validator = CommandValidator([], read_only=False)

        is_safe, error = validator.is_query_safe("COPY CUSTOMERS")
        assert is_safe is False

    def test_is_query_empty(self):
        """Test that empty query fails validation."""
        validator = CommandValidator([], read_only=False)

        is_safe, error = validator.is_query_safe("")
        assert is_safe is False

    def test_is_blocked(self):
        """Test is_blocked method."""
        validator = CommandValidator(["CUSTOM.CMD"], read_only=False)

        assert validator.is_blocked("CUSTOM.CMD") is True
        assert validator.is_blocked("custom.cmd") is True  # Case insensitive
        assert validator.is_blocked("OTHER") is False

    def test_read_only_property(self):
        """Test read_only property."""
        validator_rw = CommandValidator([], read_only=False)
        validator_ro = CommandValidator([], read_only=True)

        assert validator_rw.read_only is False
        assert validator_ro.read_only is True

    def test_allowed_query_commands_constant(self):
        """Test that expected commands are in allowed list."""
        assert "LIST" in ALLOWED_QUERY_COMMANDS
        assert "SELECT" in ALLOWED_QUERY_COMMANDS
        assert "SSELECT" in ALLOWED_QUERY_COMMANDS
        assert "SORT" in ALLOWED_QUERY_COMMANDS
        assert "COUNT" in ALLOWED_QUERY_COMMANDS
        assert "SUM" in ALLOWED_QUERY_COMMANDS
