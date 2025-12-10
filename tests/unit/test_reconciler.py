"""Unit tests for Reconciler."""

import pytest

from src.models.reconciliation import (
    OutboundFunctionalGroup,
    OutboundTransaction,
    ReconciliationStatus,
)
from src.models.segments import (
    AK1Segment,
    AK9Segment,
    ISASegment,
)
from src.models.validation import (
    FunctionalGroupStatus,
    FunctionalGroupValidation,
    TransactionSetValidation,
    TransactionStatus,
    ValidationResult,
)
from src.reconciliation.reconciler import Reconciler


@pytest.fixture
def reconciler() -> Reconciler:
    """Reconciler fixture."""
    return Reconciler()


@pytest.fixture
def sample_outbound_transaction() -> OutboundTransaction:
    """Sample outbound transaction."""
    return OutboundTransaction(
        transaction_set_id="850",
        transaction_control_number="5678",
        group_control_number="1234",
        functional_id_code="PO",
    )


@pytest.fixture
def sample_outbound_group(
    sample_outbound_transaction: OutboundTransaction,
) -> OutboundFunctionalGroup:
    """Sample outbound functional group."""
    return OutboundFunctionalGroup(
        functional_id_code="PO",
        group_control_number="1234",
        transactions=[sample_outbound_transaction],
    )


@pytest.fixture
def sample_ack_transaction() -> TransactionSetValidation:
    """Sample acknowledgment transaction."""
    return TransactionSetValidation(
        transaction_set_id="850",
        transaction_control_number="5678",
        status=TransactionStatus.ACCEPTED,
        ack_code="A",
        error_count=0,
        errors=[],
    )


@pytest.fixture
def sample_validation_result(
    sample_ack_transaction: TransactionSetValidation,
) -> ValidationResult:
    """Sample validation result."""
    fg_validation = FunctionalGroupValidation(
        functional_id_code="PO",
        group_control_number="1234",
        status=FunctionalGroupStatus.ACCEPTED,
        ack_code="A",
        transaction_sets_included=1,
        transaction_sets_received=1,
        transaction_sets_accepted=1,
        transaction_validations=[sample_ack_transaction],
    )

    return ValidationResult(
        interchange_control_number="000000001",
        interchange_sender_id="SENDER",
        interchange_receiver_id="RECEIVER",
        functional_group=fg_validation,
        is_valid=True,
    )


def test_reconcile_transaction_matched(
    reconciler: Reconciler,
    sample_outbound_transaction: OutboundTransaction,
    sample_ack_transaction: TransactionSetValidation,
) -> None:
    """Test reconciling matched transaction."""
    result = reconciler.reconcile_transaction(
        sample_outbound_transaction, sample_ack_transaction
    )

    assert result.status == ReconciliationStatus.MATCHED
    assert result.is_matched is True
    assert result.outbound_transaction == sample_outbound_transaction
    assert result.acknowledgment == sample_ack_transaction
    assert result.mismatch_reason is None


def test_reconcile_transaction_missing_ack(
    reconciler: Reconciler,
    sample_outbound_transaction: OutboundTransaction,
) -> None:
    """Test reconciling transaction with missing acknowledgment."""
    result = reconciler.reconcile_transaction(sample_outbound_transaction, None)

    assert result.status == ReconciliationStatus.MISSING_ACK
    assert result.is_matched is False
    assert result.outbound_transaction == sample_outbound_transaction
    assert result.acknowledgment is None
    assert "No acknowledgment" in result.mismatch_reason


def test_reconcile_transaction_unexpected_ack(
    reconciler: Reconciler,
    sample_ack_transaction: TransactionSetValidation,
) -> None:
    """Test reconciling unexpected acknowledgment."""
    result = reconciler.reconcile_transaction(None, sample_ack_transaction)

    assert result.status == ReconciliationStatus.UNEXPECTED_ACK
    assert result.is_matched is False
    assert result.outbound_transaction is None
    assert result.acknowledgment == sample_ack_transaction
    assert "Unexpected" in result.mismatch_reason


def test_reconcile_transaction_control_number_mismatch(
    reconciler: Reconciler,
    sample_outbound_transaction: OutboundTransaction,
) -> None:
    """Test reconciling transaction with mismatched transaction set ID."""
    # Create acknowledgment with different transaction set ID
    ack_tx = TransactionSetValidation(
        transaction_set_id="856",  # Different from 850
        transaction_control_number="5678",
        status=TransactionStatus.ACCEPTED,
        ack_code="A",
        error_count=0,
        errors=[],
    )

    result = reconciler.reconcile_transaction(sample_outbound_transaction, ack_tx)

    assert result.status == ReconciliationStatus.CONTROL_NUMBER_MISMATCH
    assert result.is_matched is False
    assert "Transaction set ID mismatch" in result.mismatch_reason
    assert "850" in result.mismatch_reason
    assert "856" in result.mismatch_reason


def test_reconcile_transaction_both_none(reconciler: Reconciler) -> None:
    """Test that reconciling with both None raises error."""
    with pytest.raises(ValueError, match="Both outbound_tx and ack_tx are None"):
        reconciler.reconcile_transaction(None, None)


def test_reconcile_functional_group_matched(
    reconciler: Reconciler,
    sample_outbound_group: OutboundFunctionalGroup,
    sample_validation_result: ValidationResult,
) -> None:
    """Test reconciling functional group with all matches."""
    fg_validation = sample_validation_result.functional_group

    result = reconciler.reconcile_functional_group(fg_validation, sample_outbound_group)

    assert result.group_control_number == "1234"
    assert result.functional_id_code == "PO"
    assert result.matched_count == 1
    assert result.missing_ack_count == 0
    assert result.unexpected_ack_count == 0
    assert result.total_count == 1
    assert result.is_fully_reconciled is True


def test_reconcile_functional_group_missing_ack(
    reconciler: Reconciler,
) -> None:
    """Test reconciling functional group with missing acknowledgment."""
    # Outbound group with 2 transactions
    outbound_tx1 = OutboundTransaction(
        transaction_set_id="850",
        transaction_control_number="5678",
        group_control_number="1234",
        functional_id_code="PO",
    )

    outbound_tx2 = OutboundTransaction(
        transaction_set_id="850",
        transaction_control_number="5679",
        group_control_number="1234",
        functional_id_code="PO",
    )

    outbound_group = OutboundFunctionalGroup(
        functional_id_code="PO",
        group_control_number="1234",
        transactions=[outbound_tx1, outbound_tx2],
    )

    # Functional group validation with only 1 acknowledgment
    ack_tx1 = TransactionSetValidation(
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
        status=FunctionalGroupStatus.PARTIALLY_ACCEPTED,
        ack_code="P",
        transaction_sets_included=2,
        transaction_sets_received=1,
        transaction_sets_accepted=1,
        transaction_validations=[ack_tx1],
    )

    result = reconciler.reconcile_functional_group(fg_validation, outbound_group)

    assert result.matched_count == 1
    assert result.missing_ack_count == 1
    assert result.unexpected_ack_count == 0
    assert result.total_count == 2
    assert result.is_fully_reconciled is False


def test_reconcile_functional_group_unexpected_ack(
    reconciler: Reconciler,
) -> None:
    """Test reconciling functional group with unexpected acknowledgment."""
    # Empty outbound group
    outbound_group = OutboundFunctionalGroup(
        functional_id_code="PO",
        group_control_number="1234",
        transactions=[],
    )

    # Functional group validation with 1 acknowledgment
    ack_tx1 = TransactionSetValidation(
        transaction_set_id="850",
        transaction_control_number="9999",
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
        transaction_validations=[ack_tx1],
    )

    result = reconciler.reconcile_functional_group(fg_validation, outbound_group)

    assert result.matched_count == 0
    assert result.missing_ack_count == 0
    assert result.unexpected_ack_count == 1
    assert result.total_count == 1
    assert result.is_fully_reconciled is False


def test_reconcile_complete_flow(
    reconciler: Reconciler,
    sample_outbound_group: OutboundFunctionalGroup,
    sample_validation_result: ValidationResult,
) -> None:
    """Test complete reconciliation flow."""
    result = reconciler.reconcile(sample_validation_result, sample_outbound_group)

    assert result.is_fully_reconciled is True
    assert result.matched_count == 1
    assert result.total_count == 1
    assert "1/1 transactions matched" in result.summary


def test_reconcile_with_mixed_results(reconciler: Reconciler) -> None:
    """Test reconciliation with mixed results."""
    # Outbound group with 3 transactions
    outbound_tx1 = OutboundTransaction(
        transaction_set_id="850",
        transaction_control_number="5678",
        group_control_number="1234",
        functional_id_code="PO",
    )

    outbound_tx2 = OutboundTransaction(
        transaction_set_id="850",
        transaction_control_number="5679",
        group_control_number="1234",
        functional_id_code="PO",
    )

    outbound_group = OutboundFunctionalGroup(
        functional_id_code="PO",
        group_control_number="1234",
        transactions=[outbound_tx1, outbound_tx2],
    )

    # Functional group validation with 2 acknowledgments (1 matched, 1 unexpected)
    ack_tx1 = TransactionSetValidation(
        transaction_set_id="850",
        transaction_control_number="5678",
        status=TransactionStatus.ACCEPTED,
        ack_code="A",
        error_count=0,
        errors=[],
    )

    ack_tx2 = TransactionSetValidation(
        transaction_set_id="850",
        transaction_control_number="9999",  # Unexpected
        status=TransactionStatus.ACCEPTED,
        ack_code="A",
        error_count=0,
        errors=[],
    )

    fg_validation = FunctionalGroupValidation(
        functional_id_code="PO",
        group_control_number="1234",
        status=FunctionalGroupStatus.PARTIALLY_ACCEPTED,
        ack_code="P",
        transaction_sets_included=2,
        transaction_sets_received=2,
        transaction_sets_accepted=2,
        transaction_validations=[ack_tx1, ack_tx2],
    )

    validation_result = ValidationResult(
        interchange_control_number="000000001",
        interchange_sender_id="SENDER",
        interchange_receiver_id="RECEIVER",
        functional_group=fg_validation,
        is_valid=True,
    )

    result = reconciler.reconcile(validation_result, outbound_group)

    assert result.is_fully_reconciled is False
    assert result.matched_count == 1
    assert result.total_count == 3  # 2 outbound + 1 unexpected ack
    fg_recon = result.functional_group_reconciliation
    assert fg_recon.matched_count == 1
    assert fg_recon.missing_ack_count == 1  # tx2 missing ack
    assert fg_recon.unexpected_ack_count == 1  # 9999 unexpected
    assert "1 missing" in result.summary
    assert "1 unexpected" in result.summary


def test_build_summary_all_matched(reconciler: Reconciler) -> None:
    """Test summary building for fully matched reconciliation."""
    from src.models.reconciliation import FunctionalGroupReconciliation

    fg_recon = FunctionalGroupReconciliation(
        group_control_number="1234",
        functional_id_code="PO",
        transaction_reconciliations=[
            pytest.helpers.create_matched_reconciliation() for _ in range(3)
        ]
        if hasattr(pytest, "helpers")
        else [],
    )

    # Manually create reconciliations
    outbound_tx = OutboundTransaction(
        transaction_set_id="850",
        transaction_control_number="5678",
        group_control_number="1234",
        functional_id_code="PO",
    )

    ack_tx = TransactionSetValidation(
        transaction_set_id="850",
        transaction_control_number="5678",
        status=TransactionStatus.ACCEPTED,
        ack_code="A",
        error_count=0,
        errors=[],
    )

    from src.models.reconciliation import TransactionReconciliation

    tx_recon = TransactionReconciliation(
        outbound_transaction=outbound_tx,
        acknowledgment=ack_tx,
        status=ReconciliationStatus.MATCHED,
    )

    fg_recon = FunctionalGroupReconciliation(
        group_control_number="1234",
        functional_id_code="PO",
        transaction_reconciliations=[tx_recon],
    )

    summary = reconciler._build_summary(fg_recon)

    assert "1/1 transactions matched" in summary
    assert "missing" not in summary.lower()
    assert "unexpected" not in summary.lower()
