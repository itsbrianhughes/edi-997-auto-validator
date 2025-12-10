"""997 Functional Acknowledgment validator."""

from typing import Optional

from src.models.segments import (
    AK1Segment,
    AK2Segment,
    AK3Segment,
    AK4Segment,
    AK5Segment,
    AK9Segment,
    ISASegment,
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
from src.utils.error_code_mapper import ErrorCodeMapper
from src.utils.logger import get_logger

logger = get_logger(__name__)


class Validator997:
    """Validates 997 Functional Acknowledgment documents."""

    def __init__(self, error_code_mapper: Optional[ErrorCodeMapper] = None) -> None:
        """Initialize validator.

        Args:
            error_code_mapper: Error code mapper for translating codes to descriptions
        """
        self.error_mapper = error_code_mapper or ErrorCodeMapper()

    def classify_transaction_status(self, ack_code: str) -> TransactionStatus:
        """Classify transaction set status from AK5-01 acknowledgment code.

        Args:
            ack_code: AK5-01 acknowledgment code (A/E/R/M/W/X/P)

        Returns:
            TransactionStatus enum value

        Reference:
            A = Accepted
            E = Accepted But Errors Were Noted
            M = Rejected, Message Authentication Code (MAC) Failed
            P = Partially Accepted
            R = Rejected
            W = Rejected, Assurance Failed Validity Tests
            X = Rejected, Content After Decryption Could Not Be Analyzed
        """
        ack_code = ack_code.upper()

        if ack_code == "A":
            return TransactionStatus.ACCEPTED
        elif ack_code in ("E", "P"):
            return TransactionStatus.PARTIALLY_ACCEPTED
        elif ack_code in ("R", "M", "W", "X"):
            return TransactionStatus.REJECTED
        else:
            logger.warning(f"Unknown AK5 acknowledgment code: {ack_code}")
            return TransactionStatus.UNKNOWN

    def classify_functional_group_status(self, ack_code: str) -> FunctionalGroupStatus:
        """Classify functional group status from AK9-01 acknowledgment code.

        Args:
            ack_code: AK9-01 acknowledgment code (A/E/R/P)

        Returns:
            FunctionalGroupStatus enum value

        Reference:
            A = Accepted
            E = Accepted But Errors Were Noted
            P = Partially Accepted, At Least One Transaction Set Was Rejected
            R = Rejected
        """
        ack_code = ack_code.upper()

        if ack_code == "A":
            return FunctionalGroupStatus.ACCEPTED
        elif ack_code in ("E", "P"):
            return FunctionalGroupStatus.PARTIALLY_ACCEPTED
        elif ack_code == "R":
            return FunctionalGroupStatus.REJECTED
        else:
            logger.warning(f"Unknown AK9 acknowledgment code: {ack_code}")
            return FunctionalGroupStatus.UNKNOWN

    def build_error_detail_from_ak4(
        self,
        ak4: AK4Segment,
        ak3: Optional[AK3Segment] = None,
    ) -> ErrorDetail:
        """Build ErrorDetail from AK4 segment.

        Args:
            ak4: AK4 segment with element-level error
            ak3: Optional AK3 segment providing segment context

        Returns:
            ErrorDetail model
        """
        # Look up error code description
        error_info = self.error_mapper.get_element_error(
            ak4.data_element_syntax_error_code
        )

        return ErrorDetail(
            segment_id=ak3.segment_id if ak3 else None,
            segment_position=ak3.segment_position_in_transaction_set if ak3 else None,
            element_position=ak4.element_position_in_segment,
            element_reference_number=ak4.data_element_reference_number,
            error_code=ak4.data_element_syntax_error_code,
            error_description=error_info.description,
            severity=ErrorSeverity.ERROR,
            bad_data_element=ak4.copy_of_bad_data_element,
        )

    def build_error_detail_from_ak3(self, ak3: AK3Segment) -> ErrorDetail:
        """Build ErrorDetail from AK3 segment (segment-level error).

        Args:
            ak3: AK3 segment with segment-level error

        Returns:
            ErrorDetail model
        """
        # AK3-04 contains the segment syntax error code
        error_code = ak3.segment_syntax_error_code or "8"  # 8 = Segment has errors
        error_info = self.error_mapper.get_segment_error(error_code)

        return ErrorDetail(
            segment_id=ak3.segment_id,
            segment_position=ak3.segment_position_in_transaction_set,
            element_position=None,
            element_reference_number=None,
            error_code=error_code,
            error_description=error_info.description,
            severity=ErrorSeverity.ERROR,
            bad_data_element=None,
        )

    def validate_transaction_set(
        self,
        ak2: AK2Segment,
        ak5: AK5Segment,
        ak3_segments: list[AK3Segment],
        ak4_segments: list[AK4Segment],
    ) -> TransactionSetValidation:
        """Validate a single transaction set (AK2 loop).

        Args:
            ak2: AK2 segment (transaction set header)
            ak5: AK5 segment (transaction set acknowledgment)
            ak3_segments: List of AK3 segments (segment errors)
            ak4_segments: List of AK4 segments (element errors)

        Returns:
            TransactionSetValidation result
        """
        # Classify status
        status = self.classify_transaction_status(ak5.transaction_set_ack_code)

        # Build error details from AK3/AK4 segments
        errors: list[ErrorDetail] = []

        # Process AK3 segments (segment-level errors)
        for ak3 in ak3_segments:
            # If AK3 has a syntax error code, it's a segment-level error
            if ak3.segment_syntax_error_code:
                errors.append(self.build_error_detail_from_ak3(ak3))

            # Find associated AK4 segments (element errors within this segment)
            # In practice, AK4 segments follow their parent AK3
            # For now, we'll process all AK4s and attribute them to the current AK3
            # A more sophisticated approach would track position

        # Process AK4 segments (element-level errors)
        # We need to associate AK4s with their parent AK3
        # For simplicity, we'll use the most recent AK3 as context
        current_ak3 = ak3_segments[-1] if ak3_segments else None
        for ak4 in ak4_segments:
            errors.append(self.build_error_detail_from_ak4(ak4, current_ak3))

        # Get AK5 syntax error codes
        syntax_error_codes = ak5.get_error_codes()

        # Add AK5-level errors if present
        for error_code in syntax_error_codes:
            error_info = self.error_mapper.get_transaction_set_error(error_code)
            errors.append(
                ErrorDetail(
                    segment_id=None,
                    segment_position=None,
                    element_position=None,
                    element_reference_number=None,
                    error_code=error_code,
                    error_description=error_info.description,
                    severity=ErrorSeverity.ERROR,
                    bad_data_element=None,
                )
            )

        return TransactionSetValidation(
            transaction_set_id=ak2.transaction_set_id,
            transaction_control_number=ak2.transaction_set_control_number,
            status=status,
            ack_code=ak5.transaction_set_ack_code,
            error_count=len(errors),
            errors=errors,
            syntax_error_codes=syntax_error_codes,
        )

    def validate_functional_group(
        self,
        ak1: AK1Segment,
        ak9: AK9Segment,
        transaction_validations: list[TransactionSetValidation],
    ) -> FunctionalGroupValidation:
        """Validate functional group (overall 997 result).

        Args:
            ak1: AK1 segment (functional group header)
            ak9: AK9 segment (functional group acknowledgment)
            transaction_validations: List of transaction set validation results

        Returns:
            FunctionalGroupValidation result
        """
        # Classify status
        status = self.classify_functional_group_status(ak9.functional_group_ack_code)

        # Get AK9 syntax error codes
        group_syntax_error_codes = ak9.get_error_codes()

        return FunctionalGroupValidation(
            functional_id_code=ak1.functional_id_code,
            group_control_number=ak1.group_control_number,
            status=status,
            ack_code=ak9.functional_group_ack_code,
            transaction_sets_included=ak9.number_of_transaction_sets_included,
            transaction_sets_received=ak9.number_of_received_transaction_sets,
            transaction_sets_accepted=ak9.number_of_accepted_transaction_sets,
            transaction_validations=transaction_validations,
            group_syntax_error_codes=group_syntax_error_codes,
        )

    def validate_997(
        self,
        isa: ISASegment,
        ak1: AK1Segment,
        ak9: AK9Segment,
        transaction_validations: list[TransactionSetValidation],
    ) -> ValidationResult:
        """Build complete validation result for 997 document.

        Args:
            isa: ISA segment (interchange header)
            ak1: AK1 segment (functional group header)
            ak9: AK9 segment (functional group acknowledgment)
            transaction_validations: List of transaction set validation results

        Returns:
            Complete ValidationResult
        """
        # Build functional group validation
        fg_validation = self.validate_functional_group(
            ak1, ak9, transaction_validations
        )

        # Determine if overall validation is successful
        # Consider it valid if functional group is ACCEPTED
        is_valid = fg_validation.status == FunctionalGroupStatus.ACCEPTED

        return ValidationResult(
            interchange_control_number=isa.interchange_control_number,
            interchange_sender_id=isa.interchange_sender_id,
            interchange_receiver_id=isa.interchange_receiver_id,
            functional_group=fg_validation,
            is_valid=is_valid,
        )
