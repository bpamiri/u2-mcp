"""Tests for u2_mcp.config module."""

import os
from unittest.mock import patch

import pytest

from u2_mcp.config import U2Config


class TestU2Config:
    """Tests for U2Config settings class."""

    def test_config_loads_required_vars(self, mock_env):
        """Test that required environment variables are loaded."""
        config = U2Config()

        assert config.host == "test-host.example.com"
        assert config.user == "test-user"
        assert config.password == "test-password"
        assert config.account == "TEST"

    def test_config_loads_optional_vars(self, mock_env):
        """Test that optional environment variables are loaded."""
        config = U2Config()

        assert config.service == "uvcs"
        assert config.port == 31438
        assert config.ssl is False
        assert config.read_only is False
        assert config.max_records == 1000

    def test_config_default_values(self):
        """Test default values when optional vars not set."""
        env_vars = {
            "U2_HOST": "host",
            "U2_USER": "user",
            "U2_PASSWORD": "pass",
            "U2_ACCOUNT": "ACC",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = U2Config()

            assert config.service == "uvcs"
            assert config.port == 31438
            assert config.ssl is False
            assert config.timeout == 30
            assert config.read_only is False
            assert config.max_records == 10000

    def test_config_blocked_commands_parsing(self, mock_env):
        """Test parsing of blocked commands from comma-separated string."""
        config = U2Config()

        assert "DELETE.FILE" in config.blocked_commands
        assert "CLEAR.FILE" in config.blocked_commands

    def test_config_blocked_commands_uppercase(self):
        """Test that blocked commands are uppercased."""
        env_vars = {
            "U2_HOST": "host",
            "U2_USER": "user",
            "U2_PASSWORD": "pass",
            "U2_ACCOUNT": "ACC",
            "U2_BLOCKED_COMMANDS": "delete.file,clear.file",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = U2Config()

            assert "DELETE.FILE" in config.blocked_commands
            assert "CLEAR.FILE" in config.blocked_commands

    def test_config_service_validation_uvcs(self):
        """Test that uvcs service type is valid."""
        env_vars = {
            "U2_HOST": "host",
            "U2_USER": "user",
            "U2_PASSWORD": "pass",
            "U2_ACCOUNT": "ACC",
            "U2_SERVICE": "uvcs",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = U2Config()
            assert config.service == "uvcs"

    def test_config_service_validation_udcs(self):
        """Test that udcs service type is valid."""
        env_vars = {
            "U2_HOST": "host",
            "U2_USER": "user",
            "U2_PASSWORD": "pass",
            "U2_ACCOUNT": "ACC",
            "U2_SERVICE": "udcs",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = U2Config()
            assert config.service == "udcs"

    def test_config_service_validation_invalid(self):
        """Test that invalid service type raises error."""
        env_vars = {
            "U2_HOST": "host",
            "U2_USER": "user",
            "U2_PASSWORD": "pass",
            "U2_ACCOUNT": "ACC",
            "U2_SERVICE": "invalid",
        }
        with (
            patch.dict(os.environ, env_vars, clear=True),
            pytest.raises(ValueError, match="uvcs.*udcs"),
        ):
            U2Config()

    def test_config_missing_required_var(self):
        """Test that missing required variable raises error."""
        env_vars = {
            "U2_HOST": "host",
            # Missing U2_USER, U2_PASSWORD, U2_ACCOUNT
        }
        with patch.dict(os.environ, env_vars, clear=True), pytest.raises((ValueError, TypeError)):
            U2Config()
