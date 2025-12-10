"""Reconciliation models for matching 997s with outbound transactions."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from src.models.validation import TransactionSetValidation


class ReconciliationStatus(str, Enum):
    """Reconciliation status for a transaction."""

    MATCHED = "MATCHED"
    MISSING_ACK = "MISSING_ACK"
    UNEXPECTED_ACK = "UNEXPECTED_ACK"
    CONTROL_NUMBER_MISMATCH = "CONTROL_NUMBER_MISMATCH"


class OutboundTransaction(BaseModel):
    """Represents an outbound EDI transaction that should be acknowledged."""

    transaction_set_id: str = Field(
        ..., description="Transaction set identifier code (e.g., '850', '856')"
    )
    transaction_control_number: str = Field(
        ..., description="Transaction set control number (ST-02)"
    )
    group_control_number: str = Field(
        ..., description="Functional group control number (GS-06)"
    )
    functional_id_code: str = Field(
        ..., description="Functional identifier code (GS-01)"
    )

    class Config:
        """Pydantic config."""

        str_strip_whitespace = True


class OutboundFunctionalGroup(BaseModel):
    """Represents an outbound functional group containing multiple transactions."""

    functional_id_code: str = Field(
        ..., description="Functional identifier code (GS-01)"
    )
    group_control_number: str = Field(
        ..., description="Functional group control number (GS-06)"
    )
    transactions: list[OutboundTransaction] = Field(
        default_factory=list, description="List of transactions in the group"
    )

    class Config:
        """Pydantic config."""

        str_strip_whitespace = True

    @property
    def transaction_count(self) -> int:
        """Get count of transactions in this group."""
        return len(self.transactions)


class TransactionReconciliation(BaseModel):
    """Reconciliation result for a single transaction set."""

    outbound_transaction: Optional[OutboundTransaction] = Field(
        default=None, description="Outbound transaction (if matched)"
    )
    acknowledgment: Optional[TransactionSetValidation] = Field(
        default=None, description="997 acknowledgment (if received)"
    )
    status: ReconciliationStatus = Field(
        ..., description="Reconciliation status"
    )
    mismatch_reason: Optional[str] = Field(
        default=None, description="Reason for mismatch (if status != MATCHED)"
    )

    class Config:
        """Pydantic config."""

        str_strip_whitespace = True

    @property
    def is_matched(self) -> bool:
        """Check if transaction is successfully matched."""
        return self.status == ReconciliationStatus.MATCHED

    @property
    def control_number(self) -> Optional[str]:
        """Get transaction control number from either side."""
        if self.outbound_transaction:
            return self.outbound_transaction.transaction_control_number
        elif self.acknowledgment:
            return self.acknowledgment.transaction_control_number
        return None


class FunctionalGroupReconciliation(BaseModel):
    """Reconciliation result for a functional group."""

    outbound_group: Optional[OutboundFunctionalGroup] = Field(
        default=None, description="Outbound functional group (if matched)"
    )
    group_control_number: str = Field(
        ..., description="Functional group control number"
    )
    functional_id_code: str = Field(
        ..., description="Functional identifier code"
    )
    transaction_reconciliations: list[TransactionReconciliation] = Field(
        default_factory=list, description="Individual transaction reconciliations"
    )

    class Config:
        """Pydantic config."""

        str_strip_whitespace = True

    @property
    def matched_count(self) -> int:
        """Count of successfully matched transactions."""
        return sum(1 for tr in self.transaction_reconciliations if tr.is_matched)

    @property
    def missing_ack_count(self) -> int:
        """Count of transactions missing acknowledgments."""
        return sum(
            1
            for tr in self.transaction_reconciliations
            if tr.status == ReconciliationStatus.MISSING_ACK
        )

    @property
    def unexpected_ack_count(self) -> int:
        """Count of unexpected acknowledgments."""
        return sum(
            1
            for tr in self.transaction_reconciliations
            if tr.status == ReconciliationStatus.UNEXPECTED_ACK
        )

    @property
    def total_count(self) -> int:
        """Total count of transactions."""
        return len(self.transaction_reconciliations)

    @property
    def is_fully_reconciled(self) -> bool:
        """Check if all transactions are successfully matched."""
        return (
            self.total_count > 0
            and self.matched_count == self.total_count
        )


class ReconciliationResult(BaseModel):
    """Complete reconciliation result."""

    functional_group_reconciliation: FunctionalGroupReconciliation = Field(
        ..., description="Functional group reconciliation"
    )
    is_fully_reconciled: bool = Field(
        ..., description="True if all transactions are matched"
    )
    summary: str = Field(
        ..., description="Human-readable reconciliation summary"
    )

    class Config:
        """Pydantic config."""

        str_strip_whitespace = True

    @property
    def matched_count(self) -> int:
        """Count of matched transactions."""
        return self.functional_group_reconciliation.matched_count

    @property
    def total_count(self) -> int:
        """Total count of transactions."""
        return self.functional_group_reconciliation.total_count
