# Contributing to u2-mcp

Thank you for your interest in contributing to u2-mcp! This document provides guidelines and information for contributors.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- A clear, descriptive title
- Steps to reproduce the issue
- Expected behavior vs actual behavior
- Your environment (Python version, OS, Universe/UniData version)
- Any relevant logs or error messages

### Suggesting Enhancements

Enhancement suggestions are welcome! Please include:

- A clear description of the proposed feature
- The motivation and use case
- Any implementation ideas you might have

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Install development dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```
3. **Make your changes** following our coding standards
4. **Add tests** for any new functionality
5. **Run the test suite** to ensure nothing is broken:
   ```bash
   pytest
   ```
6. **Run linting and type checks**:
   ```bash
   ruff check .
   mypy src/
   ```
7. **Update documentation** if needed
8. **Submit your pull request**

## Development Setup

### Prerequisites

- Python 3.10+
- A Rocket Universe or UniData server for integration testing (optional)

### Setting Up Your Development Environment

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/u2-mcp.git
cd u2-mcp

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Set up pre-commit hooks (optional but recommended)
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=u2_mcp --cov-report=html

# Run specific test file
pytest tests/test_connection.py

# Run integration tests (requires database connection)
pytest tests/integration/ --run-integration
```

## Coding Standards

### Style Guide

- Follow [PEP 8](https://pep8.org/) style guidelines
- Use [ruff](https://github.com/astral-sh/ruff) for linting and formatting
- Maximum line length: 100 characters
- Use type hints for all function signatures

### Code Quality

- Write docstrings for public modules, classes, and functions
- Keep functions focused and single-purpose
- Prefer explicit over implicit
- Handle errors gracefully with meaningful messages

### Commit Messages

- Use clear, descriptive commit messages
- Start with a verb in present tense (e.g., "Add", "Fix", "Update")
- Reference related issues when applicable

Example:
```
Add connection pooling support

- Implement ConnectionPool class with configurable size
- Add pool_size configuration option
- Update documentation with pooling examples

Fixes #42
```

## Project Structure

```
u2-mcp/
├── src/u2_mcp/           # Main package source
│   ├── __init__.py       # Package init with version
│   ├── server.py         # MCP server entry point
│   ├── connection.py     # Database connection manager
│   ├── config.py         # Pydantic settings configuration
│   ├── tools/            # MCP tool implementations
│   │   ├── files.py      # File operations (read, write, export)
│   │   ├── query.py      # Query execution (RetrieVe, TCL)
│   │   ├── dictionary.py # Schema discovery tools
│   │   ├── subroutine.py # BASIC subroutine calls
│   │   ├── transaction.py# Transaction management
│   │   └── knowledge.py  # Knowledge persistence tools
│   ├── resources/        # MCP resources
│   │   ├── syntax_help.py    # RetrieVe syntax reference
│   │   ├── examples.py       # Query examples
│   │   └── knowledge.py      # Knowledge resource
│   └── utils/            # Utility functions
│       ├── safety.py     # Command validation
│       ├── dynarray.py   # MultiValue data handling
│       ├── export.py     # JSON/CSV export
│       └── knowledge.py  # Knowledge storage
├── tests/                # Test suite
│   ├── conftest.py       # Pytest fixtures
│   ├── mocks/            # Mock objects for testing
│   └── test_*.py         # Unit tests
├── docs/                 # Documentation
│   ├── installation.md   # Installation guide
│   ├── configuration.md  # Configuration reference
│   ├── tools.md          # Tools reference
│   └── examples.md       # Usage examples
└── pyproject.toml        # Project configuration
```

## Adding New Tools

MCP tools are defined using the `@mcp.tool()` decorator. To add a new tool:

1. **Choose the appropriate module** in `src/u2_mcp/tools/`
2. **Define the tool function** with the decorator:

```python
from ..server import mcp, get_connection_manager

@mcp.tool()
def my_new_tool(param1: str, param2: int = 10) -> dict[str, Any]:
    """Short description of what the tool does.

    Longer description with more details about the tool's behavior.

    Args:
        param1: Description of parameter 1
        param2: Description of parameter 2 (default: 10)

    Returns:
        Dictionary containing the result fields.
    """
    manager = get_connection_manager()

    try:
        # Tool implementation
        result = ...
        return {"status": "success", "data": result}
    except Exception as e:
        return {"error": str(e)}
```

3. **Follow these conventions:**
   - Return dictionaries (JSON-serializable)
   - Include `status` or `error` in responses
   - Use type hints for all parameters
   - Write comprehensive docstrings (shown to AI assistants)
   - Handle errors gracefully

4. **Add tests** in `tests/test_<module>.py`

5. **Update documentation** in `docs/tools.md`

## Adding New Resources

MCP resources provide context to AI assistants. To add a new resource:

```python
from ..server import mcp

@mcp.resource("u2://my-resource")
def get_my_resource() -> str:
    """Return helpful information as a string."""
    return "Resource content here..."
```

Resources should:
- Use the `u2://` URI scheme
- Return string content (markdown supported)
- Provide helpful context for AI interactions

## Testing Guidelines

- Write unit tests for all new functionality
- Use pytest fixtures for common setup
- Mock external dependencies (database connections)
- Aim for meaningful test coverage, not just high percentages

### Test Naming Convention

```python
def test_connect_with_valid_credentials_succeeds():
    """Test that connection succeeds with valid credentials."""
    ...

def test_connect_with_invalid_host_raises_connection_error():
    """Test that connection fails gracefully with invalid host."""
    ...
```

## Documentation

- Update README.md for user-facing changes
- Add docstrings following Google style
- Update docs/ for significant features
- Include code examples where helpful

## Questions?

Feel free to open an issue for any questions about contributing. We're happy to help!

## License

By contributing to u2-mcp, you agree that your contributions will be licensed under the Apache License 2.0.
