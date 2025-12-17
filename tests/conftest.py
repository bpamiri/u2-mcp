"""Pytest configuration and fixtures for u2-mcp tests."""

import os
from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from u2_mcp.config import U2Config


@pytest.fixture
def mock_env() -> Generator[dict[str, str], None, None]:
    """Provide mock environment variables for testing."""
    env_vars = {
        "U2_HOST": "test-host.example.com",
        "U2_USER": "test-user",
        "U2_PASSWORD": "test-password",
        "U2_ACCOUNT": "TEST",
        "U2_SERVICE": "uvcs",
        "U2_PORT": "31438",
        "U2_SSL": "false",
        "U2_READ_ONLY": "false",
        "U2_MAX_RECORDS": "1000",
        "U2_BLOCKED_COMMANDS": "DELETE.FILE,CLEAR.FILE",
    }
    with patch.dict(os.environ, env_vars, clear=False):
        yield env_vars


@pytest.fixture
def mock_config(mock_env: dict[str, str]) -> U2Config:
    """Provide a test configuration instance."""
    return U2Config()


@pytest.fixture
def mock_config_read_only(mock_env: dict[str, str]) -> U2Config:
    """Provide a read-only test configuration."""
    with patch.dict(os.environ, {"U2_READ_ONLY": "true"}):
        return U2Config()


@pytest.fixture
def mock_file() -> MagicMock:
    """Provide a mock Universe file object."""
    from tests.mocks.mock_uopy import MockFile

    return MockFile()


@pytest.fixture
def mock_session(mock_file: MagicMock) -> MagicMock:
    """Provide a mock uopy session."""
    from tests.mocks.mock_uopy import MockSession

    return MockSession()


@pytest.fixture
def mock_uopy(mock_session: MagicMock) -> Generator[MagicMock, None, None]:
    """Patch uopy.connect to return mock session."""
    with patch("uopy.connect", return_value=mock_session), patch("uopy.UOError", Exception):
        yield mock_session


@pytest.fixture
def sample_record_data() -> dict[str, Any]:
    """Provide sample record data for testing."""
    # AM = chr(254), VM = chr(253), SM = chr(252)
    AM = chr(254)
    VM = chr(253)

    return {
        "simple": "John Doe" + AM + "123 Main St" + AM + "CA",
        "multivalue": "John Doe" + AM + "555-1234" + VM + "555-5678" + AM + "CA",
        "complex": (
            "ACME Corp" + AM + "John Smith" + VM + "Jane Doe" + AM + "555-1111" + VM + "555-2222"
        ),
    }


@pytest.fixture
def sample_parsed_fields() -> dict[str, Any]:
    """Provide sample parsed field structures."""
    return {
        "simple": {"1": "John Doe", "2": "123 Main St", "3": "CA"},
        "multivalue": {"1": "John Doe", "2": ["555-1234", "555-5678"], "3": "CA"},
    }
