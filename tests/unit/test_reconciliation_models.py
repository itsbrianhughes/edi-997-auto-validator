"""Unit tests for reconciliation models."""

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
    FunctionalGroupStatus,
    FunctionalGroupValidation,
    TransactionSetValidation,
    TransactionStatus,
)


def test_outbound_transaction_creation() -> None:
    """Test creating OutboundTransaction."""
    tx = OutboundTransaction(
        transaction_set_id="850",
        transaction_control_number="5678",
        group_control_number="1234",
        functional_id_code="PO",
    )

    assert tx.transaction_set_id == "850"
    assert tx.transaction_control_number == "5678"
    assert tx.group_control_number == "1234"
    assert tx.functional_id_code == "PO"


def test_outbound_functional_group_creation() -> None:
    """Test creating OutboundFunctionalGroup."""
    tx1 = OutboundTransaction(
        transaction_set_id="850",
        transaction_control_number="5678",
        group_control_number="1234",
        functional_id_code="PO",
    )

    tx2 = OutboundTransaction(
        transaction_set_id="850",
        transaction_control_number="5679",
        group_control_number="1234",
        functional_id_code="PO",
    )

    group = OutboundFunctionalGroup(
        functional_id_code="PO",
        group_control_number="1234",
        transactions=[tx1, tx2],
    )

    assert group.functional_id_code == "PO"
    assert group.group_control_number == "1234"
    assert group.transaction_count == 2
    assert len(group.transactions) == 2


def test_transaction_reconciliation_matched() -> None:
    """Test TransactionReconciliation for matched transaction."""
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

    reconciliation = TransactionReconciliation(
        outbound_transaction=outbound_tx,
        acknowledgment=ack_tx,
        status=ReconciliationStatus.MATCHED,
    )

    assert reconciliation.is_matched is True
    assert reconciliation.control_number == "5678"
    assert reconciliation.status == ReconciliationStatus.MATCHED
    assert reconciliation.mismatch_reason is None


def test_transaction_reconciliation_missing_ack() -> None:
    """Test TransactionReconciliation for missing acknowledgment."""
    outbound_tx = OutboundTransaction(
        transaction_set_id="850",
        transaction_control_number="5678",
        group_control_number="1234",
        functional_id_code="PO",
    )

    reconciliation = TransactionReconciliation(
        outbound_transaction=outbound_tx,
        acknowledgment=None,
        status=ReconciliationStatus.MISSING_ACK,
        mismatch_reason="No acknowledgment received for transaction 5678",
    )

    assert reconciliation.is_matched is False
    assert reconciliation.status == ReconciliationStatus.MISSING_ACK
    assert reconciliation.control_number == "5678"
    assert "No acknowledgment" in reconciliation.mismatch_reason


def test_transaction_reconciliation_unexpected_ack() -> None:
    """Test TransactionReconciliation for unexpected acknowledgment."""
    ack_tx = TransactionSetValidation(
        transaction_set_id="850",
        transaction_control_number="9999",
        status=TransactionStatus.ACCEPTED,
        ack_code="A",
        error_count=0,
        errors=[],
    )

    reconciliation = TransactionReconciliation(
        outbound_transaction=None,
        acknowledgment=ack_tx,
        status=ReconciliationStatus.UNEXPECTED_ACK,
        mismatch_reason="Unexpected acknowledgment for transaction 9999",
    )

    assert reconciliation.is_matched is False
    assert reconciliation.status == ReconciliationStatus.UNEXPECTED_ACK
    assert reconciliation.control_number == "9999"
    assert "Unexpected" in reconciliation.mismatch_reason


def test_functional_group_reconciliation() -> None:
    """Test FunctionalGroupReconciliation."""
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

    tx_reconciliation = TransactionReconciliation(
        outbound_transaction=outbound_tx,
        acknowledgment=ack_tx,
        status=ReconciliationStatus.MATCHED,
    )

    fg_reconciliation = FunctionalGroupReconciliation(
        outbound_group=outbound_group,
        group_control_number="1234",
        functional_id_code="PO",
        transaction_reconciliations=[tx_reconciliation],
    )

    assert fg_reconciliation.matched_count == 1
    assert fg_reconciliation.missing_ack_count == 0
    assert fg_reconciliation.unexpected_ack_count == 0
    assert fg_reconciliation.total_count == 1
    assert fg_reconciliation.is_fully_reconciled is True


def test_functional_group_reconciliation_partial() -> None:
    """Test FunctionalGroupReconciliation with partial reconciliation."""
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

    ack_tx = TransactionSetValidation(
        transaction_set_id="850",
        transaction_control_number="5678",
        status=TransactionStatus.ACCEPTED,
        ack_code="A",
        error_count=0,
        errors=[],
    )

    # First transaction matched
    tx_recon1 = TransactionReconciliation(
        outbound_transaction=outbound_tx1,
        acknowledgment=ack_tx,
        status=ReconciliationStatus.MATCHED,
    )

    # Second transaction missing ack
    tx_recon2 = TransactionReconciliation(
        outbound_transaction=outbound_tx2,
        acknowledgment=None,
        status=ReconciliationStatus.MISSING_ACK,
        mismatch_reason="No acknowledgment received",
    )

    fg_reconciliation = FunctionalGroupReconciliation(
        outbound_group=outbound_group,
        group_control_number="1234",
        functional_id_code="PO",
        transaction_reconciliations=[tx_recon1, tx_recon2],
    )

    assert fg_reconciliation.matched_count == 1
    assert fg_reconciliation.missing_ack_count == 1
    assert fg_reconciliation.unexpected_ack_count == 0
    assert fg_reconciliation.total_count == 2
    assert fg_reconciliation.is_fully_reconciled is False


def test_functional_group_reconciliation_unexpected() -> None:
    """Test FunctionalGroupReconciliation with unexpected acknowledgment."""
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

    fg_reconciliation = FunctionalGroupReconciliation(
        outbound_group=outbound_group,
        group_control_number="1234",
        functional_id_code="PO",
        transaction_reconciliations=[tx_recon],
    )

    assert fg_reconciliation.matched_count == 0
    assert fg_reconciliation.missing_ack_count == 0
    assert fg_reconciliation.unexpected_ack_count == 1
    assert fg_reconciliation.total_count == 1
    assert fg_reconciliation.is_fully_reconciled is False


def test_reconciliation_result() -> None:
    """Test ReconciliationResult."""
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

    tx_reconciliation = TransactionReconciliation(
        outbound_transaction=outbound_tx,
        acknowledgment=ack_tx,
        status=ReconciliationStatus.MATCHED,
    )

    fg_reconciliation = FunctionalGroupReconciliation(
        outbound_group=outbound_group,
        group_control_number="1234",
        functional_id_code="PO",
        transaction_reconciliations=[tx_reconciliation],
    )

    result = ReconciliationResult(
        functional_group_reconciliation=fg_reconciliation,
        is_fully_reconciled=True,
        summary="1/1 transactions matched",
    )

    assert result.is_fully_reconciled is True
    assert result.matched_count == 1
    assert result.total_count == 1
    assert "1/1" in result.summary


def test_reconciliation_status_enum() -> None:
    """Test ReconciliationStatus enum values."""
    assert ReconciliationStatus.MATCHED == "MATCHED"
    assert ReconciliationStatus.MISSING_ACK == "MISSING_ACK"
    assert ReconciliationStatus.UNEXPECTED_ACK == "UNEXPECTED_ACK"
    assert ReconciliationStatus.CONTROL_NUMBER_MISMATCH == "CONTROL_NUMBER_MISMATCH"
