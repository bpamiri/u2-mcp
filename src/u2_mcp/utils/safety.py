"""Command validation and safety controls for u2-mcp."""

# Default blocklist of dangerous TCL commands
DEFAULT_BLOCKED_COMMANDS: set[str] = {
    "DELETE.FILE",
    "DELETE-FILE",
    "CLEAR.FILE",
    "CLEAR-FILE",
    "CNAME",
    "CREATE.FILE",
    "CREATE-FILE",
    "ED",
    "SED",
    "AE",
    "ACCOUNT.RESTORE",
    "T.LOAD",
}

# Commands that modify data (blocked in read-only mode)
WRITE_COMMANDS: set[str] = {
    "DELETE",
    "COPY",
    "CNAME",
    "ED",
    "SED",
    "AE",
    "REFORMAT",
    "T.DUMP",
    "T.LOAD",
    "ACCOUNT.RESTORE",
    "CLEARFILE",
}

# Allowed query commands (RetrieVe/UniQuery read operations)
ALLOWED_QUERY_COMMANDS: set[str] = {
    "LIST",
    "SELECT",
    "SSELECT",
    "SORT",
    "COUNT",
    "SUM",
    "GET.LIST",
    "QSELECT",
    "SEARCH",
}


class CommandValidator:
    """Validates TCL commands against blocklist and safety rules.

    Args:
        blocked_commands: List of TCL commands to block
        read_only: If True, also block write operations
    """

    def __init__(self, blocked_commands: list[str], read_only: bool = False) -> None:
        self._blocked: set[str] = {cmd.upper() for cmd in blocked_commands}
        self._blocked.update(DEFAULT_BLOCKED_COMMANDS)
        self._read_only = read_only

    def validate(self, command: str) -> tuple[bool, str]:
        """Validate a TCL command.

        Args:
            command: The TCL command string to validate

        Returns:
            Tuple of (is_valid, error_message). If valid, error_message is empty.
        """
        if not command or not command.strip():
            return False, "Command cannot be empty"

        cmd_upper = command.upper().strip()
        first_word = cmd_upper.split()[0] if cmd_upper else ""

        # Check blocklist
        if first_word in self._blocked:
            return False, f"Command '{first_word}' is blocked for safety"

        # Check read-only mode
        if self._read_only and first_word in WRITE_COMMANDS:
            return False, f"Command '{first_word}' not allowed in read-only mode"

        return True, ""

    def is_query_safe(self, query: str) -> tuple[bool, str]:
        """Validate a RetrieVe/UniQuery statement.

        Only allows read operations (LIST, SELECT, SORT, COUNT, etc.)

        Args:
            query: The query statement to validate

        Returns:
            Tuple of (is_valid, error_message). If valid, error_message is empty.
        """
        if not query or not query.strip():
            return False, "Query cannot be empty"

        query_upper = query.upper().strip()
        first_word = query_upper.split()[0] if query_upper else ""

        # Only allow read operations in queries
        if first_word not in ALLOWED_QUERY_COMMANDS:
            allowed_list = ", ".join(sorted(ALLOWED_QUERY_COMMANDS))
            return False, f"Query command '{first_word}' not allowed. Allowed: {allowed_list}"

        return True, ""

    def is_blocked(self, command: str) -> bool:
        """Check if a command is in the blocklist.

        Args:
            command: Command name to check

        Returns:
            True if command is blocked
        """
        return command.upper() in self._blocked

    @property
    def read_only(self) -> bool:
        """Return whether read-only mode is enabled."""
        return self._read_only
