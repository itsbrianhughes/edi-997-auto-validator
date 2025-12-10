"""Validation result models for 997 processing."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TransactionStatus(str, Enum):
    """Transaction set acknowledgment status."""

    ACCEPTED = "ACCEPTED"
    PARTIALLY_ACCEPTED = "PARTIALLY_ACCEPTED"
    REJECTED = "REJECTED"
    UNKNOWN = "UNKNOWN"


class FunctionalGroupStatus(str, Enum):
    """Functional group acknowledgment status."""

    ACCEPTED = "ACCEPTED"
    PARTIALLY_ACCEPTED = "PARTIALLY_ACCEPTED"
    REJECTED = "REJECTED"
    UNKNOWN = "UNKNOWN"


class ErrorSeverity(str, Enum):
    """Error severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ErrorDetail(BaseModel):
    """Detailed error information from AK3/AK4 segments."""

    segment_id: Optional[str] = Field(
        default=None, description="Segment ID where error occurred (from AK3)"
    )
    segment_position: Optional[int] = Field(
        default=None, description="Position of segment in transaction set (from AK3)"
    )
    element_position: Optional[int] = Field(
        default=None, description="Position of element in segment (from AK4)"
    )
    element_reference_number: Optional[int] = Field(
        default=None,
        description="Data element reference number from X12 spec (from AK4)",
    )
    error_code: str = Field(..., description="Error code (from AK403, AK404, AK501)")
    error_description: str = Field(
        ..., description="Human-readable error description"
    )
    severity: ErrorSeverity = Field(
        default=ErrorSeverity.ERROR, description="Error severity"
    )
    bad_data_element: Optional[str] = Field(
        default=None, description="Copy of bad data element (from AK404)"
    )

    class Config:
        """Pydantic config."""

        str_strip_whitespace = True


class TransactionSetValidation(BaseModel):
    """Validation result for a single transaction set (AK2 loop)."""

    transaction_set_id: str = Field(
        ..., description="Transaction set identifier code (from AK2-01)"
    )
    transaction_control_number: str = Field(
        ..., description="Transaction set control number (from AK2-02)"
    )
    status: TransactionStatus = Field(
        ..., description="Overall transaction set status"
    )
    ack_code: str = Field(..., description="AK5-01 acknowledgment code (A/E/R/etc.)")
    error_count: int = Field(default=0, description="Number of errors detected")
    errors: list[ErrorDetail] = Field(
        default_factory=list, description="List of detailed errors"
    )
    syntax_error_codes: list[str] = Field(
        default_factory=list, description="Transaction set syntax error codes (AK5-02+)"
    )

    class Config:
        """Pydantic config."""

        str_strip_whitespace = True


class FunctionalGroupValidation(BaseModel):
    """Validation result for a functional group (997 document)."""

    functional_id_code: str = Field(
        ..., description="Functional identifier code (from AK1-01)"
    )
    group_control_number: str = Field(
        ..., description="Group control number (from AK1-02)"
    )
    status: FunctionalGroupStatus = Field(
        ..., description="Overall functional group status"
    )
    ack_code: str = Field(..., description="AK9-01 acknowledgment code (A/E/R/P)")
    transaction_sets_included: int = Field(
        ..., description="Number of transaction sets included (from AK9-02)"
    )
    transaction_sets_received: int = Field(
        ..., description="Number of transaction sets received (from AK9-03)"
    )
    transaction_sets_accepted: int = Field(
        ..., description="Number of transaction sets accepted (from AK9-04)"
    )
    transaction_validations: list[TransactionSetValidation] = Field(
        default_factory=list, description="Individual transaction set validations"
    )
    group_syntax_error_codes: list[str] = Field(
        default_factory=list,
        description="Functional group syntax error codes (AK9-05+)",
    )

    class Config:
        """Pydantic config."""

        str_strip_whitespace = True

    @property
    def total_errors(self) -> int:
        """Calculate total error count across all transaction sets."""
        return sum(ts.error_count for ts in self.transaction_validations)


class ValidationResult(BaseModel):
    """Complete validation result for a 997 document."""

    interchange_control_number: str = Field(
        ..., description="Interchange control number (from ISA-13)"
    )
    interchange_sender_id: str = Field(
        ..., description="Interchange sender ID (from ISA-06)"
    )
    interchange_receiver_id: str = Field(
        ..., description="Interchange receiver ID (from ISA-08)"
    )
    functional_group: FunctionalGroupValidation = Field(
        ..., description="Functional group validation result"
    )
    validation_timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp of validation"
    )
    is_valid: bool = Field(
        ..., description="Overall validation status (True if all accepted)"
    )

    class Config:
        """Pydantic config."""

        str_strip_whitespace = True

    @property
    def overall_status(self) -> str:
        """Get overall human-readable status."""
        return self.functional_group.status.value

    @property
    def summary(self) -> str:
        """Get summary string for quick display."""
        fg = self.functional_group
        return (
            f"{fg.status.value}: "
            f"{fg.transaction_sets_accepted}/{fg.transaction_sets_included} "
            f"transaction sets accepted"
        )
