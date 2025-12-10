"""Configuration loader with YAML support and environment variable overrides."""

from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv

from src.models.config_schemas import AppConfig, ValidationConfig


class ConfigLoader:
    """Load and manage configuration from YAML files and environment variables."""

    def __init__(self, config_dir: Optional[Path] = None, load_env: bool = True) -> None:
        """Initialize configuration loader.

        Args:
            config_dir: Directory containing configuration files (default: config/)
            load_env: Load environment variables from .env file (default: True)
        """
        self.config_dir = config_dir or Path("config")
        self._cache: Dict[str, Any] = {}

        # Load environment variables from .env file
        if load_env:
            load_dotenv()

        # Ensure config directory exists
        if not self.config_dir.exists():
            raise FileNotFoundError(f"Configuration directory not found: {self.config_dir}")

    def load_yaml(self, filename: str, use_cache: bool = True) -> Dict[str, Any]:
        """Load a YAML configuration file.

        Args:
            filename: Name of the YAML file (e.g., 'error_codes.yaml')
            use_cache: Use cached version if available (default: True)

        Returns:
            Dictionary containing configuration data

        Raises:
            FileNotFoundError: If configuration file doesn't exist
            yaml.YAMLError: If file contains invalid YAML
        """
        # Check cache first
        if use_cache and filename in self._cache:
            return self._cache[filename]

        # Build full path
        file_path = self.config_dir / filename

        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        # Load YAML file
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {filename}: {e}") from e

        # Cache the result
        if use_cache:
            self._cache[filename] = config_data

        return config_data

    def get_nested_value(
        self,
        config: Dict[str, Any],
        key_path: str,
        default: Any = None,
    ) -> Any:
        """Get a nested configuration value using dot notation.

        Args:
            config: Configuration dictionary
            key_path: Dot-separated key path (e.g., 'validation.strict_mode')
            default: Default value if key not found

        Returns:
            Configuration value or default

        Example:
            >>> config = {'validation': {'strict_mode': True}}
            >>> loader.get_nested_value(config, 'validation.strict_mode')
            True
        """
        keys = key_path.split(".")
        value = config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def load_validation_config(self) -> ValidationConfig:
        """Load and validate the validation rules configuration.

        Returns:
            Validated ValidationConfig instance

        Raises:
            FileNotFoundError: If validation_rules.yaml not found
            ValueError: If configuration is invalid
        """
        yaml_data = self.load_yaml("validation_rules.yaml")

        # Extract validation section
        validation_data = yaml_data.get("validation", {})

        if not validation_data:
            raise ValueError("Missing 'validation' section in validation_rules.yaml")

        # Parse and validate with Pydantic
        try:
            return ValidationConfig(**validation_data)
        except Exception as e:
            raise ValueError(f"Invalid validation configuration: {e}") from e

    def load_app_config(self) -> AppConfig:
        """Load application configuration from environment variables.

        Returns:
            Validated AppConfig instance with environment variable overrides
        """
        return AppConfig()

    def get_merged_config(self) -> ValidationConfig:
        """Get fully merged configuration (YAML + environment variables).

        Environment variables take precedence over YAML configuration.

        Returns:
            Merged ValidationConfig instance
        """
        # Load base configuration from YAML
        yaml_config = self.load_validation_config()

        # Load app config from environment
        app_config = self.load_app_config()

        # Merge configurations
        merged_config = app_config.merge_with_yaml_config(yaml_config)

        return merged_config

    def load_error_codes(self) -> Dict[str, Any]:
        """Load error code definitions.

        Returns:
            Dictionary containing error code mappings
        """
        return self.load_yaml("error_codes.yaml")

    def clear_cache(self) -> None:
        """Clear the configuration cache."""
        self._cache.clear()

    def reload_config(self, filename: str) -> Dict[str, Any]:
        """Reload a configuration file, bypassing cache.

        Args:
            filename: Name of the YAML file to reload

        Returns:
            Reloaded configuration data
        """
        # Remove from cache if present
        if filename in self._cache:
            del self._cache[filename]

        # Load fresh copy
        return self.load_yaml(filename, use_cache=False)

    def validate_config_structure(self) -> Dict[str, bool]:
        """Validate that all required configuration files exist and are valid.

        Returns:
            Dictionary with validation results for each config file
        """
        results: Dict[str, bool] = {}

        required_files = [
            "error_codes.yaml",
            "validation_rules.yaml",
            "logging_config.json",
        ]

        for filename in required_files:
            file_path = self.config_dir / filename
            try:
                if filename.endswith(".yaml"):
                    self.load_yaml(filename, use_cache=False)
                elif filename.endswith(".json"):
                    # JSON validation could be added here
                    results[filename] = file_path.exists()
                    continue
                results[filename] = True
            except Exception:
                results[filename] = False

        return results

    def get_environment_name(self) -> str:
        """Get the current environment name.

        Returns:
            Environment name (development, production, testing)
        """
        app_config = self.load_app_config()
        return app_config.app_env.value
