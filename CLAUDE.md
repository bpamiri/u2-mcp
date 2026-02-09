# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

u2-mcp is a Python MCP (Model Context Protocol) server that enables AI assistants to interact with Rocket Universe and UniData MultiValue databases. It uses Rocket's official `uopy` package and preserves native MultiValue semantics (multivalues, subvalues, dynamic arrays) rather than flattening to relational models.

## Development Commands

```bash
pip install -e ".[dev]"                     # Install with dev dependencies

pytest                                      # All tests
pytest tests/test_config.py                 # Single file
pytest tests/test_utils/test_safety.py -k "test_name"  # Single test
pytest --cov=u2_mcp --cov-report=html       # With coverage
pytest tests/integration/ --run-integration # Integration tests (requires DB)

ruff check .                                # Lint
ruff format .                               # Format
mypy src/                                   # Type check
```

## Architecture

### Transport Modes

The server (`server.py:main`) supports three transport modes via CLI args:
- **stdio** (default): `u2-mcp` — for Claude Desktop local connections
- **SSE** (legacy): `u2-mcp --http` — HTTP/SSE for centralized deployment
- **Streamable HTTP**: `u2-mcp --streamable-http` — for Claude.ai Integrations with OAuth

### Tool Registration Pattern

Tools are registered via `@mcp.tool()` decorators on the module-level `mcp` FastMCP instance defined in `server.py`. Each tool module (`tools/*.py`) imports `mcp` from `..server` and decorates its functions. The `server.py` bottom imports these modules to trigger registration:
```python
# server.py registers tools by importing tool modules
from .tools import dictionary, files, query, subroutine, transaction
```
New tools: create a function in the appropriate `tools/` module with `@mcp.tool()`. Resources use `@mcp.resource("u2://name")`.

### Global Singletons

Several subsystems use a module-level singleton + init/get pattern:
- `server.py`: `_connection_manager` → `get_connection_manager()` / `reset_connection_manager()`
- `utils/watchdog.py`: `_watchdog` → `init_watchdog()` / `get_watchdog()`
- `utils/audit.py`: `_audit_logger` → `init_audit_logger()` / `get_audit_logger()`
- `utils/knowledge.py`: `_knowledge_store` → `get_knowledge_store()`

### Module Layout

```
src/u2_mcp/
├── server.py           # FastMCP instance, connection/watchdog/audit tools, CLI entry, transport modes
├── connection.py       # ConnectionManager: connect/disconnect, file handle cache, TCL execution with timeout, transactions, health check
├── config.py           # U2Config (pydantic-settings): all env vars including auth, watchdog, audit
├── auth/               # OAuth for Claude.ai Integrations (Streamable HTTP mode only)
│   ├── provider.py     # U2OAuthProvider: bridges Claude.ai DCR to external IdPs
│   ├── callback.py     # /oauth/callback route handler
│   ├── storage.py      # In-memory auth state (clients, codes, tokens, pending auths)
│   └── idp/            # Identity provider adapters
│       ├── base.py     # BaseIdPAdapter ABC (get_authorization_url, exchange_code, validate_token)
│       ├── duo.py      # Cisco Duo adapter
│       ├── auth0.py    # Auth0 adapter
│       └── oidc.py     # Generic OIDC adapter
├── tools/              # MCP tool implementations (each imports mcp from server)
│   ├── files.py        # read_record, write_record, delete_record, list_files, get_file_info
│   ├── query.py        # execute_query, execute_tcl, get_select_list
│   ├── dictionary.py   # list_dictionary, get_field_definition, describe_file
│   ├── subroutine.py   # call_subroutine
│   ├── transaction.py  # begin/commit/rollback_transaction
│   └── knowledge.py    # save_knowledge, list/get/search/delete_knowledge
├── resources/          # MCP resources exposed to clients
│   ├── syntax_help.py  # u2://syntax/* - RetrieVe/UniQuery syntax reference
│   ├── examples.py     # u2://examples/* - query examples
│   └── knowledge.py    # u2://knowledge - previously learned DB knowledge
└── utils/
    ├── dynarray.py     # Dynamic array parsing (AM/VM/SM marks)
    ├── export.py       # records_to_json, records_to_csv, expand_multivalues
    ├── formatting.py   # Output formatting
    ├── safety.py       # Command validation, blocklist checking
    ├── knowledge.py    # KnowledgeStore: markdown-based persistence (~/.u2-mcp/knowledge.md)
    ├── audit.py        # AuditLogger: daily JSONL tool call logs
    └── watchdog.py     # ConnectionWatchdog: async health check loop, force reconnect
```

### Key Data Flow

1. Client calls MCP tool → `server.py` dispatches to tool function
2. Tool calls `get_connection_manager()` → `ConnectionManager.get_session()` (auto-connects/reconnects)
3. `ConnectionManager` uses `uopy` to talk to Universe/UniData
4. For queries: `ConnectionManager.execute_command()` runs TCL in a thread with configurable timeout
5. Audit wrapper (if enabled) logs tool call parameters, result, and duration to JSONL files

### Streamable HTTP + OAuth Flow

When `--streamable-http` with auth enabled:
1. Claude.ai registers via DCR → `U2OAuthProvider.register_client()`
2. `/authorize` → redirects to external IdP (Duo/Auth0/OIDC)
3. User authenticates → IdP callbacks to `/oauth/callback`
4. Callback generates auth code → redirects to Claude's callback
5. Claude exchanges code at `/token` → returns access/refresh tokens

A second `FastMCP` instance is created for Streamable HTTP mode, and tools/resources are copied from the module-level `mcp` instance.

## Key Concepts

**MultiValue Data Structure**: Records use attribute marks (AM `chr(254)`), value marks (VM `chr(253)`), and subvalue marks (SM `chr(252)`) to create nested data. The `dynarray.py` module parses these into Python dicts/lists.

**Connection Pattern**: Single persistent connection via `ConnectionManager` with auto-reconnect. File handles are cached in `_open_files` dict. TCL commands run in a separate thread with `query_timeout` to prevent hangs.

**Connection Watchdog** (`utils/watchdog.py`): Runs async health checks at `U2_WATCHDOG_INTERVAL` seconds. After `U2_WATCHDOG_MAX_FAILURES` consecutive failures, forces a disconnect so the next request reconnects cleanly. Only active in HTTP modes.

**Safety Controls**: Command blocklist (default: `DELETE.FILE,CLEAR.FILE,CNAME,CREATE.FILE`), read-only mode, query timeouts, and record count limits.

## Testing

Tests do not require a live database. The `tests/mocks/mock_uopy.py` module provides `MockSession`, `MockFile`, `MockCommand`, `MockSelect`, and `MockSubroutine` that simulate `uopy` behavior. Key conftest fixtures:
- `mock_env` — patches required env vars (`U2_HOST`, `U2_USER`, etc.)
- `mock_config` / `mock_config_read_only` — creates `U2Config` from mock env
- `mock_uopy` — patches `uopy.connect` to return `MockSession`
- `sample_record_data` — provides AM/VM delimited test records

## Environment Variables

Required: `U2_HOST`, `U2_USER`, `U2_PASSWORD`, `U2_ACCOUNT`

Key optional groups:
- **Connection**: `U2_SERVICE` (uvcs/udcs), `U2_PORT`, `U2_SSL`, `U2_TIMEOUT`
- **Safety**: `U2_READ_ONLY`, `U2_MAX_RECORDS`, `U2_QUERY_TIMEOUT`, `U2_BLOCKED_COMMANDS`
- **HTTP**: `U2_HTTP_HOST`, `U2_HTTP_PORT`, `U2_HTTP_CORS_ORIGINS`
- **OAuth**: `U2_AUTH_ENABLED`, `U2_AUTH_ISSUER_URL`, `U2_IDP_PROVIDER`, `U2_IDP_DISCOVERY_URL`, `U2_IDP_CLIENT_ID`, `U2_IDP_CLIENT_SECRET`
- **Watchdog**: `U2_WATCHDOG_ENABLED`, `U2_WATCHDOG_INTERVAL`, `U2_WATCHDOG_TIMEOUT`, `U2_WATCHDOG_MAX_FAILURES`
- **Audit**: `U2_AUDIT_ENABLED`, `U2_AUDIT_PATH`

All config is in `config.py` (U2Config pydantic-settings class) using Field aliases matching env var names.

## Coding Standards

- Follow PEP 8; use ruff for linting/formatting
- Maximum line length: 100 characters
- Type hints required for all function signatures
- Google-style docstrings for public APIs
- Ruff rules: `select = ["E", "F", "I", "UP", "B", "SIM"]`
- mypy: `disallow_untyped_defs = true`, `ignore_missing_imports = true`
