"""Tests for configuration management."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from chatmux.config import Config


@pytest.fixture
def env_vars():
    """Fixture for test environment variables."""
    return {
        "OPENAI_API_KEY": "test-openai-key",
        "ANTHROPIC_API_KEY": "test-anthropic-key",
        "GEMINI_API_KEY": "test-gemini-key",
        "MISTRAL_API_KEY": "test-mistral-key",
        "DEBUG": "true",
        "LOG_LEVEL": "DEBUG",
        "MODEL_TIMEOUT": "60",
        "RETRY_ATTEMPTS": "5",
        "RETRY_DELAY": "2.5",
        "DEFAULT_TEMPERATURE": "0.8",
        "DEFAULT_MAX_TOKENS": "3000",
        "GRID_LAYOUT": "3x2",
    }


@pytest.fixture
def minimal_env():
    """Fixture for minimal environment (no API keys)."""
    return {
        "LOG_LEVEL": "INFO",
    }


class TestConfig:
    """Test configuration loading and validation."""

    def test_default_values(self, minimal_env):
        """Test configuration with default values."""
        with patch.dict(os.environ, minimal_env, clear=True):
            # Disable .env file loading for this test
            config = Config(_env_file=None)

            # Check defaults
            assert config.openai_api_key is None
            assert config.openai_model_1 == "gpt-4o"
            assert config.openai_model_2 == "gpt-3.5-turbo"
            assert config.debug is False
            assert config.log_level == "INFO"
            assert config.model_timeout == 30
            assert config.retry_attempts == 3
            assert config.retry_delay == 1.0
            assert config.default_temperature == 0.7
            assert config.default_max_tokens == 2000
            assert config.grid_layout == "2x3"
            assert config.theme == "dark"

    def test_env_loading(self, env_vars):
        """Test loading configuration from environment variables."""
        with patch.dict(os.environ, env_vars, clear=True):
            config = Config()

            assert config.openai_api_key == "test-openai-key"
            assert config.anthropic_api_key == "test-anthropic-key"
            assert config.gemini_api_key == "test-gemini-key"
            assert config.mistral_api_key == "test-mistral-key"
            assert config.debug is True
            assert config.log_level == "DEBUG"
            assert config.model_timeout == 60
            assert config.retry_attempts == 5
            assert config.retry_delay == 2.5
            assert config.default_temperature == 0.8
            assert config.default_max_tokens == 3000
            assert config.grid_layout == "3x2"

    def test_path_expansion(self):
        """Test path expansion for home directory."""
        config = Config()
        assert config.database_path == Path.home() / ".chatmux" / "conversations.db"
        assert config.prompt_library_path == Path.home() / ".chatmux" / "prompts.json"

    def test_log_level_validation(self):
        """Test log level validation."""
        # Valid log levels
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            with patch.dict(os.environ, {"LOG_LEVEL": level}, clear=True):
                config = Config()
                assert config.log_level == level.upper()

        # Invalid log level
        with patch.dict(os.environ, {"LOG_LEVEL": "INVALID"}, clear=True):
            with pytest.raises(ValueError, match="Invalid log level"):
                Config()

    def test_grid_layout_validation(self):
        """Test grid layout validation."""
        # Valid layouts
        for layout in ["2x3", "3x2", "1x6", "6x1"]:
            with patch.dict(os.environ, {"GRID_LAYOUT": layout}, clear=True):
                config = Config()
                assert config.grid_layout == layout

        # Invalid layouts
        invalid_layouts = ["invalid", "2-3", "ax3", "2xa", ""]
        for layout in invalid_layouts:
            with patch.dict(os.environ, {"GRID_LAYOUT": layout}, clear=True):
                with pytest.raises(ValueError, match="Grid layout must be"):
                    Config()

    def test_temperature_validation(self):
        """Test temperature validation."""
        # Valid temperatures
        for temp in ["0", "0.5", "1.0", "1.5", "2.0"]:
            with patch.dict(os.environ, {"DEFAULT_TEMPERATURE": temp}, clear=True):
                config = Config()
                assert config.default_temperature == float(temp)

        # Invalid temperatures
        for temp in ["-0.1", "2.1", "3.0"]:
            with patch.dict(os.environ, {"DEFAULT_TEMPERATURE": temp}, clear=True):
                with pytest.raises(ValueError, match="Temperature must be between"):
                    Config()

    def test_positive_validation(self):
        """Test positive integer/float validation."""
        # Test timeout (positive int)
        with patch.dict(os.environ, {"MODEL_TIMEOUT": "0"}, clear=True):
            with pytest.raises(ValueError, match="Value must be positive"):
                Config()

        # Test retry attempts (positive int)
        with patch.dict(os.environ, {"RETRY_ATTEMPTS": "-1"}, clear=True):
            with pytest.raises(ValueError, match="Value must be positive"):
                Config()

        # Test retry delay (positive float)
        with patch.dict(os.environ, {"RETRY_DELAY": "0.0"}, clear=True):
            with pytest.raises(ValueError, match="Value must be positive"):
                Config()

    def test_get_model_config(self, env_vars):
        """Test getting model-specific configuration."""
        with patch.dict(os.environ, env_vars, clear=True):
            config = Config()

            # OpenAI model 1
            openai_config = config.get_model_config("openai", "1")
            assert openai_config["api_key"] == "test-openai-key"
            assert openai_config["model_name"] == "gpt-4o"
            assert openai_config["temperature"] == 0.8
            assert openai_config["max_tokens"] == 3000
            assert openai_config["timeout"] == 60

            # Anthropic model 2
            anthropic_config = config.get_model_config("anthropic", "2")
            assert anthropic_config["api_key"] == "test-anthropic-key"
            assert anthropic_config["model_name"] == "claude-3-haiku-20240307"

            # Gemini (single model)
            gemini_config = config.get_model_config("gemini", "")
            assert gemini_config["api_key"] == "test-gemini-key"
            assert gemini_config["model_name"] == "gemini-1.5-pro"

            # Ollama (local, no API key)
            ollama_config = config.get_model_config("ollama", "")
            assert ollama_config["api_key"] is None
            assert ollama_config["model_name"] == "llama3.2"
            assert ollama_config["host"] == "http://localhost:11434"

    def test_validate_provider_config(self, env_vars):
        """Test provider configuration validation."""
        # With all API keys
        with patch.dict(os.environ, env_vars, clear=True):
            config = Config()

            # All should be valid
            assert config.validate_provider_config("openai") == []
            assert config.validate_provider_config("anthropic") == []
            assert config.validate_provider_config("gemini") == []
            assert config.validate_provider_config("mistral") == []
            assert config.validate_provider_config("ollama") == []

        # Without API keys
        with patch.dict(os.environ, {}, clear=True):
            # Disable .env file loading for this test
            config = Config(_env_file=None)

            # Should have errors for missing API keys (except Ollama)
            openai_errors = config.validate_provider_config("openai")
            assert "Missing API key: OPENAI_API_KEY" in openai_errors

            anthropic_errors = config.validate_provider_config("anthropic")
            assert "Missing API key: ANTHROPIC_API_KEY" in anthropic_errors

            gemini_errors = config.validate_provider_config("gemini")
            assert "Missing API key: GEMINI_API_KEY" in gemini_errors

            mistral_errors = config.validate_provider_config("mistral")
            assert "Missing API key: MISTRAL_API_KEY" in mistral_errors

            # Ollama should be valid (no API key needed)
            assert config.validate_provider_config("ollama") == []

    def test_case_insensitive(self):
        """Test that environment variables are case insensitive."""
        with patch.dict(
            os.environ,
            {
                "openai_api_key": "lowercase-key",
                "ANTHROPIC_API_KEY": "uppercase-key",
                "GeMiNi_ApI_kEy": "mixed-key",
            },
            clear=True,
        ):
            config = Config()
            assert config.openai_api_key == "lowercase-key"
            assert config.anthropic_api_key == "uppercase-key"
            assert config.gemini_api_key == "mixed-key"

    def test_extra_fields_ignored(self):
        """Test that extra environment variables are ignored."""
        with patch.dict(
            os.environ,
            {
                "EXTRA_FIELD": "should be ignored",
                "ANOTHER_EXTRA": "also ignored",
                "LOG_LEVEL": "INFO",
            },
            clear=True,
        ):
            config = Config()
            assert not hasattr(config, "extra_field")
            assert not hasattr(config, "another_extra")
            assert config.log_level == "INFO"
