"""Configuration management for Chatmux."""

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # OpenAI Configuration
    openai_api_key: str | None = Field(None, description="OpenAI API key")
    openai_model_1: str = Field("gpt-4o", description="First OpenAI model")
    openai_model_2: str = Field("gpt-3.5-turbo", description="Second OpenAI model")

    # Anthropic Configuration
    anthropic_api_key: str | None = Field(None, description="Anthropic API key")
    anthropic_model_1: str = Field(
        "claude-3-5-sonnet-20241022", description="First Anthropic model"
    )
    anthropic_model_2: str = Field("claude-3-haiku-20240307", description="Second Anthropic model")

    # Google Gemini Configuration
    gemini_api_key: str | None = Field(None, description="Google Gemini API key")
    gemini_model: str = Field("gemini-1.5-pro", description="Gemini model")

    # Mistral Configuration
    mistral_api_key: str | None = Field(None, description="Mistral API key")
    mistral_model: str = Field("mistral-large-latest", description="Mistral model")

    # Ollama Configuration (Local)
    ollama_host: str = Field("http://localhost:11434", description="Ollama host URL")
    ollama_model: str = Field("llama3.2", description="Ollama model")

    # Application Settings
    debug: bool = Field(False, description="Debug mode")
    log_level: str = Field("INFO", description="Logging level")
    database_path: Path = Field(
        Path.home() / ".chatmux" / "conversations.db", description="Database file path"
    )
    prompt_library_path: Path = Field(
        Path.home() / ".chatmux" / "prompts.json", description="Prompt library file path"
    )

    # UI Settings
    theme: str = Field("dark", description="UI theme")
    grid_layout: str = Field("2x3", description="Grid layout configuration")
    default_temperature: float = Field(0.7, description="Default model temperature")
    default_max_tokens: int = Field(2000, description="Default max tokens")

    # Network Settings
    model_timeout: int = Field(30, description="Model request timeout in seconds")
    retry_attempts: int = Field(3, description="Number of retry attempts")
    retry_delay: float = Field(1.0, description="Delay between retries in seconds")

    @field_validator("database_path", "prompt_library_path", mode="before")
    @classmethod
    def expand_path(cls, v: str | Path) -> Path:
        """Expand ~ in paths."""
        if isinstance(v, str):
            v = Path(v)
        return v.expanduser()

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.upper()

    @field_validator("grid_layout")
    @classmethod
    def validate_grid_layout(cls, v: str) -> str:
        """Validate grid layout format."""
        if not v or "x" not in v:
            raise ValueError("Grid layout must be in format 'ROWSxCOLS' (e.g., '2x3')")
        try:
            rows, cols = v.split("x")
            int(rows), int(cols)
        except ValueError:
            raise ValueError("Grid layout must be in format 'ROWSxCOLS' with integers") from None
        return v

    @field_validator("default_temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Validate temperature is in valid range."""
        if not 0 <= v <= 2:
            raise ValueError("Temperature must be between 0 and 2")
        return v

    @field_validator("model_timeout", "retry_attempts")
    @classmethod
    def validate_positive_int(cls, v: int) -> int:
        """Validate positive integer values."""
        if v <= 0:
            raise ValueError("Value must be positive")
        return v

    @field_validator("retry_delay")
    @classmethod
    def validate_positive_float(cls, v: float) -> float:
        """Validate positive float values."""
        if v <= 0:
            raise ValueError("Value must be positive")
        return v

    def get_model_config(self, provider: str, model_id: str) -> dict[str, str | int | float | None]:
        """Get configuration for a specific model.

        Args:
            provider: Provider name (openai, anthropic, etc.)
            model_id: Model identifier (1, 2, or just the provider for single models)

        Returns:
            Dictionary with model configuration including api_key and model_name
        """
        provider = provider.lower()

        # Get API key
        api_key_field = f"{provider}_api_key"
        api_key = getattr(self, api_key_field, None)

        # Get model name
        if provider in ["gemini", "mistral", "ollama"]:
            model_field = f"{provider}_model"
        else:
            model_field = f"{provider}_model_{model_id}"

        model_name = getattr(self, model_field, None)

        config = {
            "provider": provider,
            "api_key": api_key,
            "model_name": model_name,
            "temperature": self.default_temperature,
            "max_tokens": self.default_max_tokens,
            "timeout": self.model_timeout,
            "retry_attempts": self.retry_attempts,
            "retry_delay": self.retry_delay,
        }

        # Add host for Ollama
        if provider == "ollama":
            config["host"] = self.ollama_host

        return config

    def validate_provider_config(self, provider: str) -> list[str]:
        """Validate configuration for a specific provider.

        Args:
            provider: Provider name to validate

        Returns:
            List of validation errors, empty if valid
        """
        errors = []
        provider = provider.lower()

        # Check API key (except for Ollama which doesn't need one)
        if provider != "ollama":
            api_key_field = f"{provider}_api_key"
            if not getattr(self, api_key_field, None):
                errors.append(f"Missing API key: {api_key_field.upper()}")

        # Check model configuration exists
        if provider in ["gemini", "mistral", "ollama"]:
            model_field = f"{provider}_model"
            if not getattr(self, model_field, None):
                errors.append(f"Missing model configuration: {model_field.upper()}")
        else:
            # Check both model slots for multi-model providers
            for i in [1, 2]:
                model_field = f"{provider}_model_{i}"
                if not getattr(self, model_field, None):
                    errors.append(f"Missing model configuration: {model_field.upper()}")

        return errors

    @property
    def grid_rows(self) -> int:
        """Get number of grid rows."""
        rows, _ = self.grid_layout.split("x")
        return int(rows)

    @property
    def grid_cols(self) -> int:
        """Get number of grid columns."""
        _, cols = self.grid_layout.split("x")
        return int(cols)


# Global config instance
# Note: mypy doesn't understand that pydantic-settings fields with defaults
# are optional. This is a known limitation. See:
# https://github.com/pydantic/pydantic-settings/issues/146
config = Config()  # type: ignore[call-arg]
