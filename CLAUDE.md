# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

u2-mcp is a Python MCP (Model Context Protocol) server that enables AI assistants to interact with Rocket Universe and UniData MultiValue databases. It uses Rocket's official `uopy` package and preserves native MultiValue semantics (multivalues, subvalues, dynamic arrays) rather than flattening to relational models.

## Development Commands

```bash
# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest                                      # All tests
pytest tests/test_connection.py             # Single file
pytest --cov=u2_mcp --cov-report=html       # With coverage
pytest tests/integration/ --run-integration # Integration tests (requires DB)

# Linting and type checking
ruff check .
ruff format .
mypy src/
```

## Tech Stack

- **Language**: Python 3.10+
- **MCP Framework**: `mcp` (FastMCP)
- **Database Connectivity**: `uopy` (Rocket's UniObjects for Python)
- **Build System**: hatchling with pyproject.toml
- **Testing**: pytest, pytest-cov, pytest-mock
- **Linting/Formatting**: ruff
- **Type Checking**: mypy
- **Settings**: pydantic-settings (environment variable binding)

## Architecture

```
src/u2_mcp/
├── server.py           # FastMCP server entry point
├── connection.py       # Connection management, pooling
├── config.py           # Pydantic settings, environment config
├── tools/              # MCP tool implementations
│   ├── files.py        # File operations (read/write/delete records)
│   ├── query.py        # RetrieVe/UniQuery execution
│   ├── dictionary.py   # Dictionary access tools
│   ├── subroutine.py   # BASIC subroutine calls
│   └── transaction.py  # Transaction management
├── resources/          # MCP resources (syntax help, examples)
└── utils/
    ├── dynarray.py     # Dynamic array parsing/formatting
    ├── formatting.py   # Output formatting
    └── safety.py       # Command validation, blocklist
```

## Key Concepts

**MultiValue Data Structure**: Records use attribute marks (AM), value marks (VM), and subvalue marks (SM) to create nested data. The `uopy.DynArray` class handles extraction:
```python
da = uopy.DynArray(record)
field1 = da.extract(1)           # Get field 1
field2_mv3 = da.extract(2, 3)    # Get field 2, multivalue 3
```

**Connection Pattern**: Single persistent connection with auto-reconnect, leveraging uopy's built-in pooling.

**Safety Controls**: Command blocklist, read-only mode option, query timeouts, and record count limits prevent dangerous operations.

## Environment Variables

Required: `U2_HOST`, `U2_USER`, `U2_PASSWORD`, `U2_ACCOUNT`
Optional: `U2_SERVICE` (uvcs/udcs), `U2_PORT`, `U2_SSL`, `U2_TIMEOUT`, `U2_READ_ONLY`, `U2_MAX_RECORDS`, `U2_BLOCKED_COMMANDS`

## Coding Standards

- Follow PEP 8; use ruff for linting/formatting
- Maximum line length: 100 characters
- Type hints required for all function signatures
- Google-style docstrings for public APIs
