"""Reconciliation engine for matching 997s with outbound transactions."""

from typing import Optional

from src.models.reconciliation import (
    FunctionalGroupReconciliation,
    OutboundFunctionalGroup,
    OutboundTransaction,
    ReconciliationResult,
    ReconciliationStatus,
    TransactionReconciliation,
)
from src.models.validation import (
    FunctionalGroupValidation,
    TransactionSetValidation,
    ValidationResult,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class Reconciler:
    """Reconciles 997 acknowledgments with outbound transactions."""

    def __init__(self) -> None:
        """Initialize reconciler."""
        pass

    def reconcile(
        self,
        validation_result: ValidationResult,
        outbound_group: OutboundFunctionalGroup,
    ) -> ReconciliationResult:
        """Reconcile 997 validation result with outbound transactions.

        Args:
            validation_result: 997 validation result
            outbound_group: Outbound functional group to reconcile

        Returns:
            ReconciliationResult with matching details

        Example:
            >>> reconciler = Reconciler()
            >>> result = reconciler.reconcile(validation_result, outbound_group)
        """
        fg_validation = validation_result.functional_group

        # Verify group control numbers match
        if fg_validation.group_control_number != outbound_group.group_control_number:
            logger.warning(
                "group_control_number_mismatch",
                expected=outbound_group.group_control_number,
                actual=fg_validation.group_control_number,
            )

        # Reconcile functional group
        fg_reconciliation = self.reconcile_functional_group(
            fg_validation, outbound_group
        )

        # Build summary
        summary = self._build_summary(fg_reconciliation)

        # Determine if fully reconciled
        is_fully_reconciled = fg_reconciliation.is_fully_reconciled

        return ReconciliationResult(
            functional_group_reconciliation=fg_reconciliation,
            is_fully_reconciled=is_fully_reconciled,
            summary=summary,
        )

    def reconcile_functional_group(
        self,
        fg_validation: FunctionalGroupValidation,
        outbound_group: OutboundFunctionalGroup,
    ) -> FunctionalGroupReconciliation:
        """Reconcile functional group level.

        Args:
            fg_validation: 997 functional group validation
            outbound_group: Outbound functional group

        Returns:
            FunctionalGroupReconciliation result
        """
        transaction_reconciliations: list[TransactionReconciliation] = []

        # Create maps for quick lookup
        outbound_map = {
            tx.transaction_control_number: tx for tx in outbound_group.transactions
        }
        ack_map = {
            tx.transaction_control_number: tx
            for tx in fg_validation.transaction_validations
        }

        # Find all control numbers (union of both sets)
        all_control_numbers = set(outbound_map.keys()) | set(ack_map.keys())

        for control_number in sorted(all_control_numbers):
            outbound_tx = outbound_map.get(control_number)
            ack_tx = ack_map.get(control_number)

            reconciliation = self.reconcile_transaction(outbound_tx, ack_tx)
            transaction_reconciliations.append(reconciliation)

        return FunctionalGroupReconciliation(
            outbound_group=outbound_group,
            group_control_number=fg_validation.group_control_number,
            functional_id_code=fg_validation.functional_id_code,
            transaction_reconciliations=transaction_reconciliations,
        )

    def reconcile_transaction(
        self,
        outbound_tx: Optional[OutboundTransaction],
        ack_tx: Optional[TransactionSetValidation],
    ) -> TransactionReconciliation:
        """Reconcile a single transaction.

        Args:
            outbound_tx: Outbound transaction (may be None)
            ack_tx: Acknowledgment transaction (may be None)

        Returns:
            TransactionReconciliation result
        """
        # Case 1: Both present - matched
        if outbound_tx and ack_tx:
            # Verify transaction set IDs match
            if outbound_tx.transaction_set_id != ack_tx.transaction_set_id:
                return TransactionReconciliation(
                    outbound_transaction=outbound_tx,
                    acknowledgment=ack_tx,
                    status=ReconciliationStatus.CONTROL_NUMBER_MISMATCH,
                    mismatch_reason=(
                        f"Transaction set ID mismatch: expected "
                        f"{outbound_tx.transaction_set_id}, "
                        f"got {ack_tx.transaction_set_id}"
                    ),
                )

            return TransactionReconciliation(
                outbound_transaction=outbound_tx,
                acknowledgment=ack_tx,
                status=ReconciliationStatus.MATCHED,
            )

        # Case 2: Outbound present, no acknowledgment
        elif outbound_tx and not ack_tx:
            return TransactionReconciliation(
                outbound_transaction=outbound_tx,
                acknowledgment=None,
                status=ReconciliationStatus.MISSING_ACK,
                mismatch_reason=(
                    f"No acknowledgment received for transaction "
                    f"{outbound_tx.transaction_control_number}"
                ),
            )

        # Case 3: Acknowledgment present, no outbound transaction
        elif not outbound_tx and ack_tx:
            return TransactionReconciliation(
                outbound_transaction=None,
                acknowledgment=ack_tx,
                status=ReconciliationStatus.UNEXPECTED_ACK,
                mismatch_reason=(
                    f"Unexpected acknowledgment for transaction "
                    f"{ack_tx.transaction_control_number}"
                ),
            )

        # Case 4: Neither present (should not happen)
        else:
            raise ValueError("Both outbound_tx and ack_tx are None")

    def _build_summary(
        self, fg_reconciliation: FunctionalGroupReconciliation
    ) -> str:
        """Build human-readable summary.

        Args:
            fg_reconciliation: Functional group reconciliation

        Returns:
            Summary string
        """
        matched = fg_reconciliation.matched_count
        total = fg_reconciliation.total_count
        missing = fg_reconciliation.missing_ack_count
        unexpected = fg_reconciliation.unexpected_ack_count

        parts = [f"{matched}/{total} transactions matched"]

        if missing > 0:
            parts.append(f"{missing} missing acknowledgments")

        if unexpected > 0:
            parts.append(f"{unexpected} unexpected acknowledgments")

        return ", ".join(parts)
