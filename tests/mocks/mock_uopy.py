"""Mock implementations of uopy objects for testing.

These mocks simulate the behavior of Rocket's uopy package without
requiring an actual Universe/UniData server connection.
"""

from collections.abc import Iterator


class MockFile:
    """Mock Universe file object."""

    def __init__(self, records: dict[str, str] | None = None) -> None:
        self._records: dict[str, str] = records or {}

    def read(self, record_id: str) -> str | None:
        """Read a record by ID."""
        return self._records.get(record_id)

    def write(self, record_id: str, data: str) -> None:
        """Write a record."""
        self._records[record_id] = data

    def delete(self, record_id: str) -> None:
        """Delete a record."""
        self._records.pop(record_id, None)

    def add_record(self, record_id: str, data: str) -> None:
        """Helper to add test records."""
        self._records[record_id] = data


class MockCommand:
    """Mock TCL command object."""

    def __init__(self, responses: dict[str, str] | None = None) -> None:
        self._responses: dict[str, str] = responses or {}
        self._last_command: str = ""
        self._response: str = ""

    def exec(self, command: str) -> None:
        """Execute a command."""
        self._last_command = command

        # Check for predefined responses
        for pattern, response in self._responses.items():
            if pattern.upper() in command.upper():
                self._response = response
                return

        # Default responses based on command type
        cmd_upper = command.upper()
        if cmd_upper.startswith("WHO"):
            self._response = "User: test-user  Account: TEST"
        elif cmd_upper.startswith("DATE"):
            self._response = "12/17/2024"
        elif cmd_upper.startswith("TIME"):
            self._response = "10:30:00"
        elif cmd_upper.startswith("LISTFILES"):
            self._response = "CUSTOMERS\nORDERS\nPRODUCTS\n3 files listed."
        elif cmd_upper.startswith("FILE.STAT"):
            self._response = "File Type: Dynamic\nModulo: 101\nSeparation: 2\nRecord Count: 500"
        elif cmd_upper.startswith("LIST") or cmd_upper.startswith("SORT"):
            self._response = "ID001  Value1  Value2\nID002  Value3  Value4\n2 records listed."
        elif cmd_upper.startswith("COUNT"):
            self._response = "5 records counted."
        else:
            self._response = f"Command executed: {command}"

    @property
    def response(self) -> str:
        """Get command response."""
        return self._response


class MockSelect:
    """Mock SELECT list iterator."""

    def __init__(self, record_ids: list[str] | None = None) -> None:
        self._record_ids: list[str] = record_ids or []
        self._executed: bool = False

    def exec(self, query: str) -> None:
        """Execute a SELECT query."""
        self._executed = True
        # If no records set, provide some defaults
        if not self._record_ids:
            self._record_ids = ["ID001", "ID002", "ID003"]

    def __iter__(self) -> Iterator[str]:
        """Iterate over selected record IDs."""
        return iter(self._record_ids)


class MockSubroutine:
    """Mock BASIC subroutine object."""

    def __init__(self, name: str, num_args: int) -> None:
        self._name = name
        self._num_args = num_args
        self._args: list[str] = [""] * num_args

    @property
    def args(self) -> list[str]:
        """Get/set subroutine arguments."""
        return self._args

    def call(self) -> None:
        """Execute the subroutine."""
        # Simulate a subroutine that echoes args with prefix
        for i in range(len(self._args)):
            if self._args[i]:
                self._args[i] = f"RESULT:{self._args[i]}"


class MockSession:
    """Mock uopy session object."""

    def __init__(self) -> None:
        self._files: dict[str, MockFile] = {}
        self._command = MockCommand()
        self._select = MockSelect()
        self._connected = True
        self._in_transaction = False

    def open(self, file_name: str) -> MockFile:
        """Open a file."""
        if file_name not in self._files:
            self._files[file_name] = MockFile()
        return self._files[file_name]

    def command(self) -> MockCommand:
        """Get command object."""
        return self._command

    def select(self) -> MockSelect:
        """Get select object."""
        return MockSelect()

    def subroutine(self, name: str, num_args: int) -> MockSubroutine:
        """Create subroutine object."""
        return MockSubroutine(name, num_args)

    def disconnect(self) -> None:
        """Disconnect from server."""
        self._connected = False

    def transaction_start(self) -> None:
        """Start a transaction."""
        self._in_transaction = True

    def transaction_commit(self) -> None:
        """Commit transaction."""
        self._in_transaction = False

    def transaction_rollback(self) -> None:
        """Rollback transaction."""
        self._in_transaction = False

    def add_file(self, file_name: str, records: dict[str, str]) -> None:
        """Helper to add test file with records."""
        self._files[file_name] = MockFile(records)

    def set_command_responses(self, responses: dict[str, str]) -> None:
        """Helper to set command responses."""
        self._command._responses = responses


# Mock UOError exception
class UOError(Exception):
    """Mock uopy error."""

    pass
