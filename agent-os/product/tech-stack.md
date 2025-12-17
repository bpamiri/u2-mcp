# Tech Stack

## Language & Runtime

| Component | Choice | Justification |
|-----------|--------|---------------|
| **Language** | Python 3.10+ | Required for `uopy` compatibility; strong MCP SDK support; familiar to MV developer community |
| **Runtime** | CPython | Standard runtime; required for `uopy` native bindings |
| **Package Manager** | uv / uvx | Modern Python package management; enables `uvx u2-mcp` execution pattern for MCP servers |

## Core Dependencies

| Component | Package | Justification |
|-----------|---------|---------------|
| **MCP Framework** | `mcp` (FastMCP) | Official MCP Python SDK; provides server scaffolding, tool registration, and resource handling |
| **Database Connectivity** | `uopy` | Rocket's official UniObjects for Python; native Universe/UniData protocol support; connection pooling; full API coverage |

## Development & Quality

| Component | Choice | Justification |
|-----------|--------|---------------|
| **Test Framework** | pytest | Standard Python testing; excellent fixture support for database mocking |
| **Test Coverage** | pytest-cov | Coverage reporting; target 80%+ per success metrics |
| **Mocking** | pytest-mock / unittest.mock | Database connection mocking for unit tests |
| **Linting** | ruff | Fast, comprehensive Python linter; replaces flake8 + isort + pyupgrade |
| **Formatting** | ruff format | Consistent code style; Black-compatible |
| **Type Checking** | mypy | Static type verification; catches errors before runtime |

## Build & Distribution

| Component | Choice | Justification |
|-----------|--------|---------------|
| **Build System** | hatchling | Modern Python build backend; pyproject.toml native |
| **Package Registry** | PyPI | Standard Python distribution; enables `uvx u2-mcp` installation |
| **Versioning** | Semantic Versioning | Clear compatibility expectations for consumers |

## CI/CD & Infrastructure

| Component | Choice | Justification |
|-----------|--------|---------------|
| **CI/CD** | GitHub Actions | Native GitHub integration; free for open source |
| **Workflows** | lint, test, publish | Standard quality gates; automated PyPI release on tags |

## Configuration & Environment

| Component | Approach | Justification |
|-----------|----------|---------------|
| **Configuration** | Environment variables | MCP server standard; secure credential handling; container-friendly |
| **Settings Management** | pydantic-settings | Type-safe config parsing; environment variable binding; validation |

## Documentation

| Component | Choice | Justification |
|-----------|--------|---------------|
| **Documentation** | README.md + inline docstrings | Lightweight; PyPI renders README; docstrings for API docs |
| **Changelog** | CHANGELOG.md | Track releases per conventions; Keep a Changelog format |

## Project Structure

```
u2-mcp/
├── src/
│   └── u2_mcp/
│       ├── __init__.py          # Package metadata, version
│       ├── server.py            # FastMCP server entry point
│       ├── connection.py        # Connection management, pooling
│       ├── config.py            # Pydantic settings, environment config
│       ├── tools/
│       │   ├── __init__.py      # Tool registration
│       │   ├── files.py         # File operation tools
│       │   ├── query.py         # Query execution tools
│       │   ├── dictionary.py    # Dictionary access tools
│       │   ├── subroutine.py    # BASIC subroutine tools
│       │   └── transaction.py   # Transaction management tools
│       ├── resources/
│       │   ├── __init__.py      # Resource registration
│       │   ├── syntax_help.py   # Query syntax documentation
│       │   └── examples.py      # Example queries resource
│       └── utils/
│           ├── __init__.py
│           ├── dynarray.py      # Dynamic array parsing/formatting
│           ├── formatting.py    # Output formatting utilities
│           └── safety.py        # Command validation, blocklist
├── tests/
│   ├── conftest.py              # Shared fixtures, mocked connections
│   ├── test_connection.py
│   ├── test_tools/
│   └── test_utils/
├── pyproject.toml               # Build config, dependencies, metadata
├── README.md                    # Installation, usage, configuration
├── CHANGELOG.md                 # Release history
├── LICENSE                      # Apache 2.0
└── .github/
    └── workflows/
        ├── ci.yml               # Lint + test on PR/push
        └── publish.yml          # PyPI release on tag
```

## Security Considerations

| Concern | Mitigation |
|---------|------------|
| **Credential Storage** | Environment variables only; never in code or config files |
| **Command Injection** | Blocklist for dangerous TCL commands; parameterized queries |
| **Read-Only Mode** | Optional configuration to disable all write operations |
| **Query Timeouts** | Configurable timeouts prevent runaway queries |
| **Connection Security** | uopy handles encryption per Universe server configuration |

## Compatibility Matrix

| Database | Version | Support Level |
|----------|---------|---------------|
| Rocket Universe | 11.x | Primary target |
| Rocket Universe | 12.x | Expected compatible |
| Rocket UniData | 8.x | Fast-follow (API nearly identical) |

## License

Apache 2.0 - Permissive open source; compatible with enterprise adoption and MCP ecosystem norms.
