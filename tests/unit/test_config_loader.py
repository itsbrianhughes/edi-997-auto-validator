"""Unit tests for ConfigLoader."""

from pathlib import Path
from typing import Any, Dict

import pytest
import yaml

from src.models.config_schemas import ValidationConfig
from src.utils.config_loader import ConfigLoader


def test_config_loader_initialization(temp_config_dir: Path) -> None:
    """Test ConfigLoader initialization."""
    loader = ConfigLoader(config_dir=temp_config_dir, load_env=False)
    assert loader.config_dir == temp_config_dir
    assert isinstance(loader._cache, dict)
    assert len(loader._cache) == 0


def test_config_loader_missing_directory() -> None:
    """Test ConfigLoader with non-existent directory."""
    with pytest.raises(FileNotFoundError, match="Configuration directory not found"):
        ConfigLoader(config_dir=Path("/nonexistent/path"), load_env=False)


def test_load_yaml_success(config_loader_with_files: ConfigLoader) -> None:
    """Test loading a valid YAML file."""
    config = config_loader_with_files.load_yaml("error_codes.yaml")
    assert "ak_error_codes" in config
    assert isinstance(config["ak_error_codes"], dict)


def test_load_yaml_caching(config_loader_with_files: ConfigLoader) -> None:
    """Test YAML file caching."""
    # First load
    config1 = config_loader_with_files.load_yaml("error_codes.yaml")

    # Should be cached
    assert "error_codes.yaml" in config_loader_with_files._cache

    # Second load should use cache
    config2 = config_loader_with_files.load_yaml("error_codes.yaml")

    # Should be same object (from cache)
    assert config1 is config2


def test_load_yaml_no_cache(config_loader_with_files: ConfigLoader) -> None:
    """Test loading YAML without caching."""
    config1 = config_loader_with_files.load_yaml("error_codes.yaml", use_cache=False)
    config2 = config_loader_with_files.load_yaml("error_codes.yaml", use_cache=False)

    # Should be different objects
    assert config1 is not config2
    # But should have same content
    assert config1 == config2


def test_load_yaml_missing_file(config_loader_with_files: ConfigLoader) -> None:
    """Test loading non-existent YAML file."""
    with pytest.raises(FileNotFoundError, match="Configuration file not found"):
        config_loader_with_files.load_yaml("nonexistent.yaml")


def test_load_yaml_invalid_yaml(temp_config_dir: Path) -> None:
    """Test loading invalid YAML file."""
    # Create invalid YAML file
    invalid_file = temp_config_dir / "invalid.yaml"
    with open(invalid_file, "w") as f:
        f.write("invalid: yaml: content:\n  bad indentation")

    loader = ConfigLoader(config_dir=temp_config_dir, load_env=False)

    with pytest.raises(ValueError, match="Invalid YAML"):
        loader.load_yaml("invalid.yaml")


def test_get_nested_value(sample_validation_rules: Dict[str, Any]) -> None:
    """Test retrieving nested configuration values."""
    loader = ConfigLoader(config_dir=Path("config"), load_env=False)

    # Test valid nested key
    value = loader.get_nested_value(
        sample_validation_rules,
        "validation.strict_mode",
    )
    assert value is False

    # Test deeper nesting
    value = loader.get_nested_value(
        sample_validation_rules,
        "validation.parser.auto_detect_delimiters",
    )
    assert value is True

    # Test missing key with default
    value = loader.get_nested_value(
        sample_validation_rules,
        "validation.nonexistent",
        default="default_value",
    )
    assert value == "default_value"

    # Test missing key without default
    value = loader.get_nested_value(
        sample_validation_rules,
        "validation.nonexistent",
    )
    assert value is None


def test_load_validation_config(config_loader_with_files: ConfigLoader) -> None:
    """Test loading and validating validation configuration."""
    config = config_loader_with_files.load_validation_config()

    assert isinstance(config, ValidationConfig)
    assert config.strict_mode is False
    assert config.parser.auto_detect_delimiters is True
    assert config.classification.accepted_codes == ["A"]


def test_load_validation_config_missing_file(temp_config_dir: Path) -> None:
    """Test loading validation config with missing file."""
    loader = ConfigLoader(config_dir=temp_config_dir, load_env=False)

    with pytest.raises(FileNotFoundError):
        loader.load_validation_config()


def test_load_validation_config_invalid_structure(temp_config_dir: Path) -> None:
    """Test loading validation config with invalid structure."""
    # Create file with missing validation section
    invalid_config = {"wrong_key": {"data": "value"}}
    config_path = temp_config_dir / "validation_rules.yaml"
    with open(config_path, "w") as f:
        yaml.dump(invalid_config, f)

    loader = ConfigLoader(config_dir=temp_config_dir, load_env=False)

    with pytest.raises(ValueError, match="Missing 'validation' section"):
        loader.load_validation_config()


def test_load_error_codes(config_loader_with_files: ConfigLoader) -> None:
    """Test loading error codes configuration."""
    error_codes = config_loader_with_files.load_error_codes()

    assert "ak_error_codes" in error_codes
    assert "segment_syntax_errors" in error_codes["ak_error_codes"]
    assert "element_syntax_errors" in error_codes["ak_error_codes"]


def test_clear_cache(config_loader_with_files: ConfigLoader) -> None:
    """Test clearing configuration cache."""
    # Load some configs
    config_loader_with_files.load_yaml("error_codes.yaml")
    config_loader_with_files.load_yaml("validation_rules.yaml")

    # Cache should have entries
    assert len(config_loader_with_files._cache) > 0

    # Clear cache
    config_loader_with_files.clear_cache()

    # Cache should be empty
    assert len(config_loader_with_files._cache) == 0


def test_reload_config(config_loader_with_files: ConfigLoader) -> None:
    """Test reloading configuration."""
    # Load config
    config1 = config_loader_with_files.load_yaml("error_codes.yaml")

    # Reload
    config2 = config_loader_with_files.reload_config("error_codes.yaml")

    # Should be different objects
    assert config1 is not config2
    # But same content
    assert config1 == config2


def test_validate_config_structure(config_loader_with_files: ConfigLoader) -> None:
    """Test validating configuration file structure."""
    # Add a JSON file for testing
    json_file = config_loader_with_files.config_dir / "logging_config.json"
    with open(json_file, "w") as f:
        f.write('{"version": 1}')

    results = config_loader_with_files.validate_config_structure()

    assert "error_codes.yaml" in results
    assert results["error_codes.yaml"] is True
    assert "validation_rules.yaml" in results
    assert results["validation_rules.yaml"] is True
    assert "logging_config.json" in results
    assert results["logging_config.json"] is True
