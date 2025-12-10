"""Unit tests for JSON serializer."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from src.models.validation import (
    ErrorDetail,
    ErrorSeverity,
    FunctionalGroupStatus,
    FunctionalGroupValidation,
    TransactionSetValidation,
    TransactionStatus,
    ValidationResult,
)
from src.serialization.json_serializer import (
    JSONSerializer,
    OutputMode,
    create_serializer,
)


@pytest.fixture
def sample_error() -> ErrorDetail:
    """Sample error detail."""
    return ErrorDetail(
        segment_id="N1",
        segment_position=2,
        element_position=1,
        element_reference_number=66,
        error_code="1",
        error_description="Mandatory data element missing",
        severity=ErrorSeverity.ERROR,
        bad_data_element="BAD",
    )


@pytest.fixture
def sample_transaction_validation() -> TransactionSetValidation:
    """Sample transaction set validation."""
    return TransactionSetValidation(
        transaction_set_id="850",
        transaction_control_number="5678",
        status=TransactionStatus.ACCEPTED,
        ack_code="A",
        error_count=0,
        errors=[],
        syntax_error_codes=[],
    )


@pytest.fixture
def sample_functional_group_validation(
    sample_transaction_validation: TransactionSetValidation,
) -> FunctionalGroupValidation:
    """Sample functional group validation."""
    return FunctionalGroupValidation(
        functional_id_code="PO",
        group_control_number="1234",
        status=FunctionalGroupStatus.ACCEPTED,
        ack_code="A",
        transaction_sets_included=1,
        transaction_sets_received=1,
        transaction_sets_accepted=1,
        transaction_validations=[sample_transaction_validation],
        group_syntax_error_codes=[],
    )


@pytest.fixture
def sample_validation_result(
    sample_functional_group_validation: FunctionalGroupValidation,
) -> ValidationResult:
    """Sample validation result."""
    return ValidationResult(
        interchange_control_number="000000001",
        interchange_sender_id="SENDER",
        interchange_receiver_id="RECEIVER",
        functional_group=sample_functional_group_validation,
        is_valid=True,
    )


@pytest.fixture
def serializer() -> JSONSerializer:
    """JSON serializer fixture."""
    return JSONSerializer()


def test_serializer_initialization() -> None:
    """Test JSONSerializer initialization."""
    serializer = JSONSerializer(pretty=True, indent=4, sort_keys=False)
    assert serializer.pretty is True
    assert serializer.indent == 4
    assert serializer.sort_keys is False


def test_create_serializer() -> None:
    """Test create_serializer factory function."""
    serializer = create_serializer(pretty=False)
    assert serializer.pretty is False
    assert serializer.indent is None


def test_serialize_validation_result_full_mode(
    serializer: JSONSerializer,
    sample_validation_result: ValidationResult,
) -> None:
    """Test full mode serialization."""
    json_output = serializer.serialize_validation_result(
        sample_validation_result, mode=OutputMode.FULL
    )

    # Parse JSON to verify it's valid
    data = json.loads(json_output)

    # Verify top-level fields
    assert data["interchange_control_number"] == "000000001"
    assert data["interchange_sender_id"] == "SENDER"
    assert data["interchange_receiver_id"] == "RECEIVER"
    assert data["is_valid"] is True
    assert data["overall_status"] == "ACCEPTED"
    assert "1/1" in data["summary"]

    # Verify functional group
    assert "functional_group" in data
    fg = data["functional_group"]
    assert fg["functional_id_code"] == "PO"
    assert fg["group_control_number"] == "1234"
    assert fg["status"] == "ACCEPTED"
    assert fg["ack_code"] == "A"

    # Verify transaction validations
    assert len(fg["transaction_validations"]) == 1
    ts = fg["transaction_validations"][0]
    assert ts["transaction_set_id"] == "850"
    assert ts["status"] == "ACCEPTED"


def test_serialize_validation_result_summary_mode(
    serializer: JSONSerializer,
    sample_validation_result: ValidationResult,
) -> None:
    """Test summary mode serialization."""
    json_output = serializer.serialize_validation_result(
        sample_validation_result, mode=OutputMode.SUMMARY
    )

    data = json.loads(json_output)

    # Verify summary structure
    assert "interchange_control_number" in data
    assert "overall_status" in data
    assert "summary" in data
    assert "functional_group" in data
    assert "transaction_sets" in data

    # Verify functional group summary
    fg = data["functional_group"]
    assert fg["transaction_sets_included"] == 1
    assert fg["transaction_sets_accepted"] == 1
    assert fg["total_errors"] == 0

    # Verify transaction sets summary
    assert len(data["transaction_sets"]) == 1
    ts = data["transaction_sets"][0]
    assert ts["transaction_set_id"] == "850"
    assert ts["status"] == "ACCEPTED"
    assert ts["error_count"] == 0


def test_serialize_validation_result_compact_mode(
    serializer: JSONSerializer,
    sample_validation_result: ValidationResult,
) -> None:
    """Test compact mode serialization."""
    json_output = serializer.serialize_validation_result(
        sample_validation_result, mode=OutputMode.COMPACT
    )

    data = json.loads(json_output)

    # Verify compact structure (minimal fields)
    assert data["icn"] == "000000001"
    assert data["sender"] == "SENDER"
    assert data["receiver"] == "RECEIVER"
    assert data["valid"] is True
    assert data["status"] == "ACCEPTED"
    assert data["accepted"] == 1
    assert data["total"] == 1
    assert data["errors"] == 0
    assert "timestamp" in data


def test_serialize_rejected_transaction(serializer: JSONSerializer) -> None:
    """Test serialization of rejected transaction."""
    errors = [
        ErrorDetail(
            error_code="1",
            error_description="Mandatory data element missing",
            element_position=1,
        ),
    ]

    transaction_validation = TransactionSetValidation(
        transaction_set_id="850",
        transaction_control_number="5678",
        status=TransactionStatus.REJECTED,
        ack_code="R",
        error_count=1,
        errors=errors,
        syntax_error_codes=["5"],
    )

    fg_validation = FunctionalGroupValidation(
        functional_id_code="PO",
        group_control_number="1234",
        status=FunctionalGroupStatus.REJECTED,
        ack_code="R",
        transaction_sets_included=1,
        transaction_sets_received=1,
        transaction_sets_accepted=0,
        transaction_validations=[transaction_validation],
    )

    result = ValidationResult(
        interchange_control_number="000000001",
        interchange_sender_id="SENDER",
        interchange_receiver_id="RECEIVER",
        functional_group=fg_validation,
        is_valid=False,
    )

    json_output = serializer.serialize_validation_result(result, mode=OutputMode.FULL)
    data = json.loads(json_output)

    assert data["is_valid"] is False
    assert data["overall_status"] == "REJECTED"

    # Verify errors are included
    ts = data["functional_group"]["transaction_validations"][0]
    assert ts["status"] == "REJECTED"
    assert ts["error_count"] == 1
    assert len(ts["errors"]) == 1
    assert ts["errors"][0]["error_code"] == "1"


def test_serialize_to_file(
    serializer: JSONSerializer,
    sample_validation_result: ValidationResult,
    tmp_path: Path,
) -> None:
    """Test serialization to file."""
    output_file = tmp_path / "output.json"

    serializer.serialize_to_file(
        sample_validation_result, output_file, mode=OutputMode.FULL
    )

    # Verify file exists
    assert output_file.exists()

    # Verify file contents
    with open(output_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["interchange_control_number"] == "000000001"
    assert data["is_valid"] is True


def test_serialize_to_file_creates_parent_directories(
    serializer: JSONSerializer,
    sample_validation_result: ValidationResult,
    tmp_path: Path,
) -> None:
    """Test that serialize_to_file creates parent directories."""
    output_file = tmp_path / "nested" / "dir" / "output.json"

    serializer.serialize_to_file(
        sample_validation_result, output_file, mode=OutputMode.SUMMARY
    )

    # Verify file and parent directories exist
    assert output_file.exists()
    assert output_file.parent.exists()


def test_pretty_printing(sample_validation_result: ValidationResult) -> None:
    """Test pretty printing vs compact output."""
    pretty_serializer = JSONSerializer(pretty=True, indent=2)
    compact_serializer = JSONSerializer(pretty=False)

    pretty_output = pretty_serializer.serialize_validation_result(
        sample_validation_result, mode=OutputMode.COMPACT
    )
    compact_output = compact_serializer.serialize_validation_result(
        sample_validation_result, mode=OutputMode.COMPACT
    )

    # Pretty output should have newlines
    assert "\n" in pretty_output

    # Compact output should not have newlines
    assert "\n" not in compact_output

    # Both should parse to the same data
    assert json.loads(pretty_output) == json.loads(compact_output)


def test_sort_keys(sample_validation_result: ValidationResult) -> None:
    """Test key sorting."""
    sorted_serializer = JSONSerializer(sort_keys=True)
    unsorted_serializer = JSONSerializer(sort_keys=False)

    sorted_output = sorted_serializer.serialize_validation_result(
        sample_validation_result, mode=OutputMode.COMPACT
    )
    unsorted_output = unsorted_serializer.serialize_validation_result(
        sample_validation_result, mode=OutputMode.COMPACT
    )

    # Both should parse to the same data
    assert json.loads(sorted_output) == json.loads(unsorted_output)


def test_serialize_error_detail(
    serializer: JSONSerializer,
    sample_error: ErrorDetail,
) -> None:
    """Test serialization of ErrorDetail."""
    data = serializer.serialize_error_detail(sample_error)

    assert data["segment_id"] == "N1"
    assert data["segment_position"] == 2
    assert data["element_position"] == 1
    assert data["error_code"] == "1"
    assert data["severity"] == "error"
    assert data["bad_data_element"] == "BAD"


def test_serialize_transaction_validation(
    serializer: JSONSerializer,
    sample_transaction_validation: TransactionSetValidation,
) -> None:
    """Test serialization of TransactionSetValidation."""
    data = serializer.serialize_transaction_validation(sample_transaction_validation)

    assert data["transaction_set_id"] == "850"
    assert data["transaction_control_number"] == "5678"
    assert data["status"] == "ACCEPTED"
    assert data["ack_code"] == "A"
    assert data["error_count"] == 0


def test_serialize_functional_group_validation(
    serializer: JSONSerializer,
    sample_functional_group_validation: FunctionalGroupValidation,
) -> None:
    """Test serialization of FunctionalGroupValidation."""
    data = serializer.serialize_functional_group_validation(
        sample_functional_group_validation
    )

    assert data["functional_id_code"] == "PO"
    assert data["group_control_number"] == "1234"
    assert data["status"] == "ACCEPTED"
    assert data["total_errors"] == 0  # Computed field


def test_timestamp_serialization(
    serializer: JSONSerializer,
    sample_validation_result: ValidationResult,
) -> None:
    """Test that timestamps are serialized to ISO format."""
    json_output = serializer.serialize_validation_result(
        sample_validation_result, mode=OutputMode.FULL
    )

    data = json.loads(json_output)

    # Verify timestamp is in ISO format
    timestamp = data["validation_timestamp"]
    assert isinstance(timestamp, str)
    # Should be parseable as ISO format
    parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    assert isinstance(parsed, datetime)


def test_exclude_none_in_error_detail(serializer: JSONSerializer) -> None:
    """Test that None values are excluded in error detail serialization."""
    error = ErrorDetail(
        error_code="5",
        error_description="One or more segments in error",
        # All optional fields left as None
    )

    data = serializer.serialize_error_detail(error)

    # None fields should be excluded
    assert "segment_id" not in data
    assert "segment_position" not in data
    assert "element_position" not in data
    assert "bad_data_element" not in data

    # Required fields should be present
    assert data["error_code"] == "5"
    assert data["error_description"] == "One or more segments in error"


def test_output_mode_enum() -> None:
    """Test OutputMode enum values."""
    assert OutputMode.FULL == "full"
    assert OutputMode.SUMMARY == "summary"
    assert OutputMode.COMPACT == "compact"
