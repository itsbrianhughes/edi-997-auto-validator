"""Unit tests for Markdown report generator."""

from pathlib import Path

import pytest

from src.models.reconciliation import (
    FunctionalGroupReconciliation,
    OutboundFunctionalGroup,
    OutboundTransaction,
    ReconciliationResult,
    ReconciliationStatus,
    TransactionReconciliation,
)
from src.models.validation import (
    ErrorDetail,
    ErrorSeverity,
    FunctionalGroupStatus,
    FunctionalGroupValidation,
    TransactionSetValidation,
    TransactionStatus,
    ValidationResult,
)
from src.reporting.markdown_generator import MarkdownReportGenerator


@pytest.fixture
def generator() -> MarkdownReportGenerator:
    """Markdown generator fixture."""
    return MarkdownReportGenerator(include_timestamps=False)


@pytest.fixture
def sample_validation_result() -> ValidationResult:
    """Sample validation result."""
    transaction_validation = TransactionSetValidation(
        transaction_set_id="850",
        transaction_control_number="5678",
        status=TransactionStatus.ACCEPTED,
        ack_code="A",
        error_count=0,
        errors=[],
    )

    fg_validation = FunctionalGroupValidation(
        functional_id_code="PO",
        group_control_number="1234",
        status=FunctionalGroupStatus.ACCEPTED,
        ack_code="A",
        transaction_sets_included=1,
        transaction_sets_received=1,
        transaction_sets_accepted=1,
        transaction_validations=[transaction_validation],
    )

    return ValidationResult(
        interchange_control_number="000000001",
        interchange_sender_id="SENDER",
        interchange_receiver_id="RECEIVER",
        functional_group=fg_validation,
        is_valid=True,
    )


@pytest.fixture
def sample_validation_result_with_errors() -> ValidationResult:
    """Sample validation result with errors."""
    errors = [
        ErrorDetail(
            segment_id="N1",
            segment_position=2,
            element_position=1,
            error_code="1",
            error_description="Mandatory data element missing",
            severity=ErrorSeverity.ERROR,
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

    return ValidationResult(
        interchange_control_number="000000001",
        interchange_sender_id="SENDER",
        interchange_receiver_id="RECEIVER",
        functional_group=fg_validation,
        is_valid=False,
    )


@pytest.fixture
def sample_reconciliation_result() -> ReconciliationResult:
    """Sample reconciliation result."""
    outbound_tx = OutboundTransaction(
        transaction_set_id="850",
        transaction_control_number="5678",
        group_control_number="1234",
        functional_id_code="PO",
    )

    outbound_group = OutboundFunctionalGroup(
        functional_id_code="PO",
        group_control_number="1234",
        transactions=[outbound_tx],
    )

    ack_tx = TransactionSetValidation(
        transaction_set_id="850",
        transaction_control_number="5678",
        status=TransactionStatus.ACCEPTED,
        ack_code="A",
        error_count=0,
        errors=[],
    )

    tx_recon = TransactionReconciliation(
        outbound_transaction=outbound_tx,
        acknowledgment=ack_tx,
        status=ReconciliationStatus.MATCHED,
    )

    fg_recon = FunctionalGroupReconciliation(
        outbound_group=outbound_group,
        group_control_number="1234",
        functional_id_code="PO",
        transaction_reconciliations=[tx_recon],
    )

    return ReconciliationResult(
        functional_group_reconciliation=fg_recon,
        is_fully_reconciled=True,
        summary="1/1 transactions matched",
    )


def test_generator_initialization() -> None:
    """Test MarkdownReportGenerator initialization."""
    generator = MarkdownReportGenerator(include_timestamps=True)
    assert generator.include_timestamps is True

    generator2 = MarkdownReportGenerator(include_timestamps=False)
    assert generator2.include_timestamps is False


def test_generate_validation_report(
    generator: MarkdownReportGenerator,
    sample_validation_result: ValidationResult,
) -> None:
    """Test generating validation report."""
    report = generator.generate_validation_report(sample_validation_result)

    # Check for key sections
    assert "# 997 Functional Acknowledgment Validation Report" in report
    assert "Status:** ✅ ACCEPTED" in report
    assert "Summary:**" in report
    assert "## Interchange Details" in report
    assert "## Functional Group Details" in report
    assert "## Transaction Sets" in report

    # Check for key data
    assert "000000001" in report
    assert "SENDER" in report
    assert "RECEIVER" in report
    assert "5678" in report
    assert "850" in report


def test_generate_validation_report_with_errors(
    generator: MarkdownReportGenerator,
    sample_validation_result_with_errors: ValidationResult,
) -> None:
    """Test generating validation report with errors."""
    report = generator.generate_validation_report(sample_validation_result_with_errors)

    # Check for error section
    assert "## Error Details" in report
    assert "Mandatory data element missing" in report
    assert "Syntax Error Codes" in report

    # Check status is rejected
    assert "❌ REJECTED" in report


def test_generate_validation_report_with_timestamp() -> None:
    """Test validation report includes timestamp."""
    generator_with_ts = MarkdownReportGenerator(include_timestamps=True)

    transaction_validation = TransactionSetValidation(
        transaction_set_id="850",
        transaction_control_number="5678",
        status=TransactionStatus.ACCEPTED,
        ack_code="A",
        error_count=0,
        errors=[],
    )

    fg_validation = FunctionalGroupValidation(
        functional_id_code="PO",
        group_control_number="1234",
        status=FunctionalGroupStatus.ACCEPTED,
        ack_code="A",
        transaction_sets_included=1,
        transaction_sets_received=1,
        transaction_sets_accepted=1,
        transaction_validations=[transaction_validation],
    )

    validation_result = ValidationResult(
        interchange_control_number="000000001",
        interchange_sender_id="SENDER",
        interchange_receiver_id="RECEIVER",
        functional_group=fg_validation,
        is_valid=True,
    )

    report = generator_with_ts.generate_validation_report(validation_result)

    assert "**Generated:**" in report
    assert "UTC" in report


def test_generate_reconciliation_report(
    generator: MarkdownReportGenerator,
    sample_reconciliation_result: ReconciliationResult,
) -> None:
    """Test generating reconciliation report."""
    report = generator.generate_reconciliation_report(sample_reconciliation_result)

    # Check for key sections
    assert "# 997 Reconciliation Report" in report
    assert "Status:** ✅ Fully Reconciled" in report
    assert "## Reconciliation Details" in report

    # Check for key data
    assert "1/1 transactions matched" in report
    assert "5678" in report
    assert "✅ MATCHED" in report


def test_generate_combined_report(
    generator: MarkdownReportGenerator,
    sample_validation_result: ValidationResult,
    sample_reconciliation_result: ReconciliationResult,
) -> None:
    """Test generating combined validation + reconciliation report."""
    report = generator.generate_combined_report(
        sample_validation_result, sample_reconciliation_result
    )

    # Check for combined sections
    assert "# 997 Validation & Reconciliation Report" in report
    assert "## Validation Summary" in report
    assert "## Reconciliation Summary" in report
    assert "## Transaction Details" in report

    # Check for both validation and reconciliation data
    assert "✅ ACCEPTED" in report
    assert "✅ Fully Reconciled" in report
    assert "000000001" in report


def test_write_report(
    generator: MarkdownReportGenerator,
    sample_validation_result: ValidationResult,
    tmp_path: Path,
) -> None:
    """Test writing report to file."""
    report = generator.generate_validation_report(sample_validation_result)
    output_file = tmp_path / "report.md"

    generator.write_report(report, output_file)

    # Verify file exists
    assert output_file.exists()

    # Verify contents
    content = output_file.read_text(encoding="utf-8")
    assert "# 997 Functional Acknowledgment Validation Report" in content


def test_write_report_creates_directories(
    generator: MarkdownReportGenerator,
    sample_validation_result: ValidationResult,
    tmp_path: Path,
) -> None:
    """Test that write_report creates parent directories."""
    report = generator.generate_validation_report(sample_validation_result)
    output_file = tmp_path / "nested" / "dir" / "report.md"

    generator.write_report(report, output_file)

    # Verify file and directories exist
    assert output_file.exists()
    assert output_file.parent.exists()


def test_validation_report_table_formatting(
    generator: MarkdownReportGenerator,
    sample_validation_result: ValidationResult,
) -> None:
    """Test that tables are properly formatted."""
    report = generator.generate_validation_report(sample_validation_result)

    # Check for table headers and separators
    assert "| Metric | Value |" in report
    assert "|--------|-------|" in report
    assert "| Field | Value |" in report
    assert "|-------|-------|" in report


def test_reconciliation_report_with_missing_ack(
    generator: MarkdownReportGenerator,
) -> None:
    """Test reconciliation report with missing acknowledgment."""
    outbound_tx = OutboundTransaction(
        transaction_set_id="850",
        transaction_control_number="5678",
        group_control_number="1234",
        functional_id_code="PO",
    )

    outbound_group = OutboundFunctionalGroup(
        functional_id_code="PO",
        group_control_number="1234",
        transactions=[outbound_tx],
    )

    tx_recon = TransactionReconciliation(
        outbound_transaction=outbound_tx,
        acknowledgment=None,
        status=ReconciliationStatus.MISSING_ACK,
        mismatch_reason="No acknowledgment received",
    )

    fg_recon = FunctionalGroupReconciliation(
        outbound_group=outbound_group,
        group_control_number="1234",
        functional_id_code="PO",
        transaction_reconciliations=[tx_recon],
    )

    recon_result = ReconciliationResult(
        functional_group_reconciliation=fg_recon,
        is_fully_reconciled=False,
        summary="0/1 transactions matched, 1 missing acknowledgments",
    )

    report = generator.generate_reconciliation_report(recon_result)

    assert "⚠️ Partial Reconciliation" in report
    assert "⚠️ MISSING_ACK" in report
    assert "No acknowledgment received" in report


def test_reconciliation_report_with_unexpected_ack(
    generator: MarkdownReportGenerator,
) -> None:
    """Test reconciliation report with unexpected acknowledgment."""
    outbound_group = OutboundFunctionalGroup(
        functional_id_code="PO",
        group_control_number="1234",
        transactions=[],
    )

    ack_tx = TransactionSetValidation(
        transaction_set_id="850",
        transaction_control_number="9999",
        status=TransactionStatus.ACCEPTED,
        ack_code="A",
        error_count=0,
        errors=[],
    )

    tx_recon = TransactionReconciliation(
        outbound_transaction=None,
        acknowledgment=ack_tx,
        status=ReconciliationStatus.UNEXPECTED_ACK,
        mismatch_reason="Unexpected acknowledgment",
    )

    fg_recon = FunctionalGroupReconciliation(
        outbound_group=outbound_group,
        group_control_number="1234",
        functional_id_code="PO",
        transaction_reconciliations=[tx_recon],
    )

    recon_result = ReconciliationResult(
        functional_group_reconciliation=fg_recon,
        is_fully_reconciled=False,
        summary="0/1 transactions matched, 1 unexpected acknowledgments",
    )

    report = generator.generate_reconciliation_report(recon_result)

    assert "⚠️ Partial Reconciliation" in report
    assert "❌ UNEXPECTED_ACK" in report
    assert "Unexpected acknowledgment" in report


def test_error_details_formatting(
    generator: MarkdownReportGenerator,
    sample_validation_result_with_errors: ValidationResult,
) -> None:
    """Test error details are properly formatted."""
    report = generator.generate_validation_report(sample_validation_result_with_errors)

    # Check error table headers
    assert "| Segment | Position | Element | Code | Description |" in report
    assert "|---------|----------|---------|------|-------------|" in report

    # Check error data
    assert "| N1 | 2 | 1 | 1 | Mandatory data element missing |" in report


def test_multiple_transactions_in_report(
    generator: MarkdownReportGenerator,
) -> None:
    """Test report with multiple transaction sets."""
    tx1 = TransactionSetValidation(
        transaction_set_id="850",
        transaction_control_number="5678",
        status=TransactionStatus.ACCEPTED,
        ack_code="A",
        error_count=0,
        errors=[],
    )

    tx2 = TransactionSetValidation(
        transaction_set_id="850",
        transaction_control_number="5679",
        status=TransactionStatus.REJECTED,
        ack_code="R",
        error_count=2,
        errors=[],
    )

    fg_validation = FunctionalGroupValidation(
        functional_id_code="PO",
        group_control_number="1234",
        status=FunctionalGroupStatus.PARTIALLY_ACCEPTED,
        ack_code="P",
        transaction_sets_included=2,
        transaction_sets_received=2,
        transaction_sets_accepted=1,
        transaction_validations=[tx1, tx2],
    )

    validation_result = ValidationResult(
        interchange_control_number="000000001",
        interchange_sender_id="SENDER",
        interchange_receiver_id="RECEIVER",
        functional_group=fg_validation,
        is_valid=False,
    )

    report = generator.generate_validation_report(validation_result)

    # Check both transactions appear
    assert "5678" in report
    assert "5679" in report
    assert "✅ ACCEPTED" in report
    assert "❌ REJECTED" in report


def test_empty_transaction_sets(generator: MarkdownReportGenerator) -> None:
    """Test report with no transaction sets."""
    fg_validation = FunctionalGroupValidation(
        functional_id_code="PO",
        group_control_number="1234",
        status=FunctionalGroupStatus.ACCEPTED,
        ack_code="A",
        transaction_sets_included=0,
        transaction_sets_received=0,
        transaction_sets_accepted=0,
        transaction_validations=[],
    )

    validation_result = ValidationResult(
        interchange_control_number="000000001",
        interchange_sender_id="SENDER",
        interchange_receiver_id="RECEIVER",
        functional_group=fg_validation,
        is_valid=True,
    )

    report = generator.generate_validation_report(validation_result)

    assert "*No transaction sets found*" in report
