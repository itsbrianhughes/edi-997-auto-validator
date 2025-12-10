"""Pytest configuration and shared fixtures."""

import tempfile
from pathlib import Path
from typing import Any, Dict, Generator

import pytest
import yaml

from src.utils.config_loader import ConfigLoader
from src.utils.error_code_mapper import ErrorCodeMapper


@pytest.fixture
def temp_config_dir() -> Generator[Path, None, None]:
    """Create a temporary configuration directory for testing.

    Yields:
        Path to temporary config directory
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir)
        yield config_dir


@pytest.fixture
def sample_error_codes() -> Dict[str, Any]:
    """Sample error codes configuration for testing.

    Returns:
        Dictionary with sample error codes
    """
    return {
        "ak_error_codes": {
            "segment_syntax_errors": {
                "1": {
                    "code": "1",
                    "description": "Unrecognized segment ID",
                    "severity": "error",
                },
                "3": {
                    "code": "3",
                    "description": "Required segment missing",
                    "severity": "error",
                },
            },
            "element_syntax_errors": {
                "1": {
                    "code": "1",
                    "description": "Mandatory data element missing",
                    "severity": "error",
                },
                "7": {
                    "code": "7",
                    "description": "Invalid code value",
                    "severity": "error",
                },
            },
            "functional_group_ack_codes": {
                "A": {
                    "code": "A",
                    "description": "Accepted",
                    "severity": "success",
                    "classification": "accepted",
                },
                "R": {
                    "code": "R",
                    "description": "Rejected",
                    "severity": "error",
                    "classification": "rejected",
                },
            },
            "transaction_set_ack_codes": {
                "A": {
                    "code": "A",
                    "description": "Accepted",
                    "severity": "success",
                    "classification": "accepted",
                },
                "E": {
                    "code": "E",
                    "description": "Accepted but errors noted",
                    "severity": "warning",
                    "classification": "partial",
                },
                "R": {
                    "code": "R",
                    "description": "Rejected",
                    "severity": "error",
                    "classification": "rejected",
                },
            },
            "custom_errors": {
                "PARSE_ERROR": {
                    "code": "PARSE_ERROR",
                    "description": "Failed to parse EDI file",
                    "severity": "error",
                }
            },
        }
    }


@pytest.fixture
def sample_validation_rules() -> Dict[str, Any]:
    """Sample validation rules configuration for testing.

    Returns:
        Dictionary with sample validation rules
    """
    return {
        "validation": {
            "strict_mode": False,
            "max_errors_before_abort": 0,
            "behavior": {
                "require_isa_segment": True,
                "require_gs_segment": True,
                "require_st_segment": True,
                "require_ak1_segment": True,
                "require_ak9_segment": True,
                "allow_missing_ak2": False,
                "validate_control_numbers": True,
                "validate_segment_counts": True,
            },
            "classification": {
                "accepted_codes": ["A"],
                "partial_codes": ["E", "P"],
                "rejected_codes": ["R", "M", "W", "X"],
                "rejection_thresholds": {
                    "error": 1,
                    "warning": 0,
                    "info": 0,
                },
            },
            "reconciliation": {
                "require_outbound_match": False,
                "match_tolerance_seconds": 300,
                "match_fields": [
                    "st_control_number",
                    "gs_control_number",
                    "transaction_type",
                ],
                "report_unmatched": True,
                "report_orphaned": True,
            },
            "reporting": {
                "max_errors_per_transaction": 100,
                "include_accepted_in_report": False,
                "group_errors_by_segment": True,
                "sort_by_severity": True,
                "include_line_numbers": True,
                "include_summary": True,
                "formats": {
                    "json": True,
                    "markdown": True,
                    "html": False,
                    "excel": False,
                },
            },
            "parser": {
                "auto_detect_delimiters": True,
                "default_delimiters": {
                    "element": "*",
                    "segment": "~",
                    "sub_element": ":",
                    "repetition": "^",
                },
                "trim_whitespace": True,
                "preserve_line_breaks": False,
                "max_file_size_mb": 10,
            },
            "performance": {
                "enable_profiling": False,
                "slow_operation_threshold_seconds": 1.0,
                "enable_caching": False,
                "max_cache_size": 100,
            },
        }
    }


@pytest.fixture
def config_loader_with_files(
    temp_config_dir: Path,
    sample_error_codes: Dict[str, Any],
    sample_validation_rules: Dict[str, Any],
) -> ConfigLoader:
    """Create a ConfigLoader with sample configuration files.

    Args:
        temp_config_dir: Temporary config directory
        sample_error_codes: Sample error codes
        sample_validation_rules: Sample validation rules

    Returns:
        Configured ConfigLoader instance
    """
    # Write error codes
    error_codes_path = temp_config_dir / "error_codes.yaml"
    with open(error_codes_path, "w") as f:
        yaml.dump(sample_error_codes, f)

    # Write validation rules
    validation_rules_path = temp_config_dir / "validation_rules.yaml"
    with open(validation_rules_path, "w") as f:
        yaml.dump(sample_validation_rules, f)

    # Create config loader
    return ConfigLoader(config_dir=temp_config_dir, load_env=False)


@pytest.fixture
def error_code_mapper(config_loader_with_files: ConfigLoader) -> ErrorCodeMapper:
    """Create an ErrorCodeMapper instance for testing.

    Args:
        config_loader_with_files: ConfigLoader with sample files

    Returns:
        ErrorCodeMapper instance
    """
    return ErrorCodeMapper(config_loader_with_files)


@pytest.fixture
def sample_edi_997_accepted() -> str:
    """Sample 997 EDI file with accepted transaction.

    Returns:
        EDI 997 file content
    """
    return """ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *230101*1200*U*00401*000000001*0*P*>~
GS*FA*SENDER*RECEIVER*20230101*1200*1*X*004010~
ST*997*0001~
AK1*PO*1234~
AK9*A*1*1*1~
SE*4*0001~
GE*1*1~
IEA*1*000000001~"""


@pytest.fixture
def sample_edi_997_rejected() -> str:
    """Sample 997 EDI file with rejected transaction.

    Returns:
        EDI 997 file content
    """
    return """ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *230101*1200*U*00401*000000001*0*P*>~
GS*FA*SENDER*RECEIVER*20230101*1200*1*X*004010~
ST*997*0001~
AK1*PO*1234~
AK2*850*5678~
AK3*N1*2~
AK4*1*66*1*1~
AK5*R*5~
AK9*R*1*0*1~
SE*8*0001~
GE*1*1~
IEA*1*000000001~"""
