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
├── src/u2_mcp/          # Main package source
│   ├── __init__.py
│   ├── server.py        # MCP server implementation
│   ├── connection.py    # Database connection handling
│   ├── tools/           # MCP tool implementations
│   └── utils/           # Utility functions
├── tests/               # Test suite
│   ├── unit/            # Unit tests
│   └── integration/     # Integration tests
├── docs/                # Documentation
└── examples/            # Usage examples
```

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
