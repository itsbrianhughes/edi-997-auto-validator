"""Unit tests for validation models."""

import pytest
from datetime import datetime

from src.models.validation import (
    ErrorDetail,
    ErrorSeverity,
    FunctionalGroupStatus,
    FunctionalGroupValidation,
    TransactionSetValidation,
    TransactionStatus,
    ValidationResult,
)


def test_error_detail_creation() -> None:
    """Test creating ErrorDetail."""
    error = ErrorDetail(
        segment_id="N1",
        segment_position=2,
        element_position=1,
        element_reference_number=66,
        error_code="1",
        error_description="Mandatory data element missing",
        severity=ErrorSeverity.ERROR,
        bad_data_element="BAD",
    )

    assert error.segment_id == "N1"
    assert error.segment_position == 2
    assert error.element_position == 1
    assert error.error_code == "1"
    assert error.severity == ErrorSeverity.ERROR


def test_error_detail_minimal() -> None:
    """Test creating ErrorDetail with minimal fields."""
    error = ErrorDetail(
        error_code="5",
        error_description="One or more segments in error",
    )

    assert error.error_code == "5"
    assert error.segment_id is None
    assert error.severity == ErrorSeverity.ERROR


def test_transaction_set_validation_accepted() -> None:
    """Test TransactionSetValidation for accepted transaction."""
    validation = TransactionSetValidation(
        transaction_set_id="850",
        transaction_control_number="5678",
        status=TransactionStatus.ACCEPTED,
        ack_code="A",
        error_count=0,
        errors=[],
        syntax_error_codes=[],
    )

    assert validation.status == TransactionStatus.ACCEPTED
    assert validation.ack_code == "A"
    assert validation.error_count == 0
    assert len(validation.errors) == 0


def test_transaction_set_validation_rejected_with_errors() -> None:
    """Test TransactionSetValidation for rejected transaction with errors."""
    errors = [
        ErrorDetail(
            error_code="1",
            error_description="Mandatory data element missing",
            element_position=1,
        ),
        ErrorDetail(
            error_code="5",
            error_description="Data element too long",
            element_position=2,
        ),
    ]

    validation = TransactionSetValidation(
        transaction_set_id="850",
        transaction_control_number="5678",
        status=TransactionStatus.REJECTED,
        ack_code="R",
        error_count=2,
        errors=errors,
        syntax_error_codes=["1", "5"],
    )

    assert validation.status == TransactionStatus.REJECTED
    assert validation.error_count == 2
    assert len(validation.errors) == 2
    assert validation.syntax_error_codes == ["1", "5"]


def test_functional_group_validation() -> None:
    """Test FunctionalGroupValidation."""
    transaction_validations = [
        TransactionSetValidation(
            transaction_set_id="850",
            transaction_control_number="5678",
            status=TransactionStatus.ACCEPTED,
            ack_code="A",
            error_count=0,
            errors=[],
        ),
    ]

    fg_validation = FunctionalGroupValidation(
        functional_id_code="PO",
        group_control_number="1234",
        status=FunctionalGroupStatus.ACCEPTED,
        ack_code="A",
        transaction_sets_included=1,
        transaction_sets_received=1,
        transaction_sets_accepted=1,
        transaction_validations=transaction_validations,
    )

    assert fg_validation.status == FunctionalGroupStatus.ACCEPTED
    assert fg_validation.ack_code == "A"
    assert fg_validation.transaction_sets_included == 1
    assert fg_validation.total_errors == 0


def test_functional_group_validation_total_errors() -> None:
    """Test FunctionalGroupValidation total_errors calculation."""
    transaction_validations = [
        TransactionSetValidation(
            transaction_set_id="850",
            transaction_control_number="5678",
            status=TransactionStatus.REJECTED,
            ack_code="R",
            error_count=3,
            errors=[],
        ),
        TransactionSetValidation(
            transaction_set_id="850",
            transaction_control_number="5679",
            status=TransactionStatus.ACCEPTED,
            ack_code="A",
            error_count=0,
            errors=[],
        ),
    ]

    fg_validation = FunctionalGroupValidation(
        functional_id_code="PO",
        group_control_number="1234",
        status=FunctionalGroupStatus.PARTIALLY_ACCEPTED,
        ack_code="P",
        transaction_sets_included=2,
        transaction_sets_received=2,
        transaction_sets_accepted=1,
        transaction_validations=transaction_validations,
    )

    assert fg_validation.total_errors == 3


def test_validation_result() -> None:
    """Test complete ValidationResult."""
    transaction_validations = [
        TransactionSetValidation(
            transaction_set_id="850",
            transaction_control_number="5678",
            status=TransactionStatus.ACCEPTED,
            ack_code="A",
            error_count=0,
            errors=[],
        ),
    ]

    fg_validation = FunctionalGroupValidation(
        functional_id_code="PO",
        group_control_number="1234",
        status=FunctionalGroupStatus.ACCEPTED,
        ack_code="A",
        transaction_sets_included=1,
        transaction_sets_received=1,
        transaction_sets_accepted=1,
        transaction_validations=transaction_validations,
    )

    result = ValidationResult(
        interchange_control_number="000000001",
        interchange_sender_id="SENDER",
        interchange_receiver_id="RECEIVER",
        functional_group=fg_validation,
        is_valid=True,
    )

    assert result.is_valid is True
    assert result.interchange_control_number == "000000001"
    assert result.overall_status == "ACCEPTED"
    assert "1/1" in result.summary
    assert "ACCEPTED" in result.summary


def test_validation_result_rejected() -> None:
    """Test ValidationResult for rejected functional group."""
    transaction_validations = [
        TransactionSetValidation(
            transaction_set_id="850",
            transaction_control_number="5678",
            status=TransactionStatus.REJECTED,
            ack_code="R",
            error_count=5,
            errors=[],
        ),
    ]

    fg_validation = FunctionalGroupValidation(
        functional_id_code="PO",
        group_control_number="1234",
        status=FunctionalGroupStatus.REJECTED,
        ack_code="R",
        transaction_sets_included=1,
        transaction_sets_received=1,
        transaction_sets_accepted=0,
        transaction_validations=transaction_validations,
    )

    result = ValidationResult(
        interchange_control_number="000000001",
        interchange_sender_id="SENDER",
        interchange_receiver_id="RECEIVER",
        functional_group=fg_validation,
        is_valid=False,
    )

    assert result.is_valid is False
    assert result.overall_status == "REJECTED"
    assert "0/1" in result.summary


def test_transaction_status_enum() -> None:
    """Test TransactionStatus enum values."""
    assert TransactionStatus.ACCEPTED == "ACCEPTED"
    assert TransactionStatus.PARTIALLY_ACCEPTED == "PARTIALLY_ACCEPTED"
    assert TransactionStatus.REJECTED == "REJECTED"
    assert TransactionStatus.UNKNOWN == "UNKNOWN"


def test_functional_group_status_enum() -> None:
    """Test FunctionalGroupStatus enum values."""
    assert FunctionalGroupStatus.ACCEPTED == "ACCEPTED"
    assert FunctionalGroupStatus.PARTIALLY_ACCEPTED == "PARTIALLY_ACCEPTED"
    assert FunctionalGroupStatus.REJECTED == "REJECTED"
    assert FunctionalGroupStatus.UNKNOWN == "UNKNOWN"


def test_error_severity_enum() -> None:
    """Test ErrorSeverity enum values."""
    assert ErrorSeverity.ERROR == "error"
    assert ErrorSeverity.WARNING == "warning"
    assert ErrorSeverity.INFO == "info"
