"""Unit tests for Validator997."""

import pytest

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
    FunctionalGroupStatus,
    TransactionStatus,
)
from src.validation.validator import Validator997


@pytest.fixture
def validator() -> Validator997:
    """Validator fixture."""
    return Validator997()


def test_classify_transaction_status_accepted(validator: Validator997) -> None:
    """Test classification of accepted transaction."""
    status = validator.classify_transaction_status("A")
    assert status == TransactionStatus.ACCEPTED


def test_classify_transaction_status_partial(validator: Validator997) -> None:
    """Test classification of partially accepted transaction."""
    status_e = validator.classify_transaction_status("E")
    assert status_e == TransactionStatus.PARTIALLY_ACCEPTED

    status_p = validator.classify_transaction_status("P")
    assert status_p == TransactionStatus.PARTIALLY_ACCEPTED


def test_classify_transaction_status_rejected(validator: Validator997) -> None:
    """Test classification of rejected transaction."""
    for code in ["R", "M", "W", "X"]:
        status = validator.classify_transaction_status(code)
        assert status == TransactionStatus.REJECTED


def test_classify_transaction_status_unknown(validator: Validator997) -> None:
    """Test classification of unknown transaction status."""
    status = validator.classify_transaction_status("Z")
    assert status == TransactionStatus.UNKNOWN


def test_classify_functional_group_status_accepted(validator: Validator997) -> None:
    """Test classification of accepted functional group."""
    status = validator.classify_functional_group_status("A")
    assert status == FunctionalGroupStatus.ACCEPTED


def test_classify_functional_group_status_partial(validator: Validator997) -> None:
    """Test classification of partially accepted functional group."""
    status_e = validator.classify_functional_group_status("E")
    assert status_e == FunctionalGroupStatus.PARTIALLY_ACCEPTED

    status_p = validator.classify_functional_group_status("P")
    assert status_p == FunctionalGroupStatus.PARTIALLY_ACCEPTED


def test_classify_functional_group_status_rejected(validator: Validator997) -> None:
    """Test classification of rejected functional group."""
    status = validator.classify_functional_group_status("R")
    assert status == FunctionalGroupStatus.REJECTED


def test_build_error_detail_from_ak4(validator: Validator997) -> None:
    """Test building ErrorDetail from AK4 segment."""
    ak3 = AK3Segment(
        segment_id="N1",
        segment_position_in_transaction_set=2,
    )

    ak4 = AK4Segment(
        element_position_in_segment=1,
        data_element_reference_number=66,
        data_element_syntax_error_code="1",
        copy_of_bad_data_element="BAD",
    )

    error = validator.build_error_detail_from_ak4(ak4, ak3)

    assert error.segment_id == "N1"
    assert error.segment_position == 2
    assert error.element_position == 1
    assert error.element_reference_number == 66
    assert error.error_code == "1"
    assert error.bad_data_element == "BAD"
    assert "Mandatory data element missing" in error.error_description


def test_build_error_detail_from_ak4_no_ak3(validator: Validator997) -> None:
    """Test building ErrorDetail from AK4 without AK3 context."""
    ak4 = AK4Segment(
        element_position_in_segment=1,
        data_element_reference_number=66,
        data_element_syntax_error_code="7",
    )

    error = validator.build_error_detail_from_ak4(ak4, None)

    assert error.segment_id is None
    assert error.segment_position is None
    assert error.element_position == 1
    assert error.error_code == "7"
    assert "Invalid code value" in error.error_description


def test_build_error_detail_from_ak3(validator: Validator997) -> None:
    """Test building ErrorDetail from AK3 segment."""
    ak3 = AK3Segment(
        segment_id="REF",
        segment_position_in_transaction_set=8,
        segment_syntax_error_code="8",
    )

    error = validator.build_error_detail_from_ak3(ak3)

    assert error.segment_id == "REF"
    assert error.segment_position == 8
    assert error.element_position is None
    assert error.error_code == "8"
    assert "data element errors" in error.error_description.lower()


def test_validate_transaction_set_accepted(validator: Validator997) -> None:
    """Test validating accepted transaction set."""
    ak2 = AK2Segment(
        transaction_set_id="850",
        transaction_set_control_number="5678",
    )

    ak5 = AK5Segment(transaction_set_ack_code="A")

    result = validator.validate_transaction_set(ak2, ak5, [], [])

    assert result.status == TransactionStatus.ACCEPTED
    assert result.ack_code == "A"
    assert result.transaction_set_id == "850"
    assert result.transaction_control_number == "5678"
    assert result.error_count == 0
    assert len(result.errors) == 0


def test_validate_transaction_set_rejected_with_errors(
    validator: Validator997,
) -> None:
    """Test validating rejected transaction set with errors."""
    ak2 = AK2Segment(
        transaction_set_id="850",
        transaction_set_control_number="5678",
    )

    ak3 = AK3Segment(
        segment_id="N1",
        segment_position_in_transaction_set=2,
        segment_syntax_error_code="8",
    )

    ak4 = AK4Segment(
        element_position_in_segment=1,
        data_element_reference_number=66,
        data_element_syntax_error_code="1",
    )

    ak5 = AK5Segment(
        transaction_set_ack_code="R",
        transaction_set_syntax_error_code_1="5",
    )

    result = validator.validate_transaction_set(ak2, ak5, [ak3], [ak4])

    assert result.status == TransactionStatus.REJECTED
    assert result.ack_code == "R"
    assert result.error_count == 3  # AK3 error + AK4 error + AK5 error
    assert len(result.errors) == 3
    assert result.syntax_error_codes == ["5"]


def test_validate_functional_group_accepted(validator: Validator997) -> None:
    """Test validating accepted functional group."""
    ak1 = AK1Segment(
        functional_id_code="PO",
        group_control_number="1234",
    )

    ak9 = AK9Segment(
        functional_group_ack_code="A",
        number_of_transaction_sets_included=1,
        number_of_received_transaction_sets=1,
        number_of_accepted_transaction_sets=1,
    )

    from src.models.validation import TransactionSetValidation

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

    result = validator.validate_functional_group(ak1, ak9, transaction_validations)

    assert result.status == FunctionalGroupStatus.ACCEPTED
    assert result.ack_code == "A"
    assert result.functional_id_code == "PO"
    assert result.group_control_number == "1234"
    assert result.transaction_sets_included == 1
    assert result.transaction_sets_accepted == 1
    assert len(result.transaction_validations) == 1


def test_validate_functional_group_partial(validator: Validator997) -> None:
    """Test validating partially accepted functional group."""
    ak1 = AK1Segment(
        functional_id_code="PO",
        group_control_number="1234",
    )

    ak9 = AK9Segment(
        functional_group_ack_code="P",
        number_of_transaction_sets_included=2,
        number_of_received_transaction_sets=2,
        number_of_accepted_transaction_sets=1,
        functional_group_syntax_error_code_1="5",
    )

    from src.models.validation import TransactionSetValidation

    transaction_validations = [
        TransactionSetValidation(
            transaction_set_id="850",
            transaction_control_number="5678",
            status=TransactionStatus.ACCEPTED,
            ack_code="A",
            error_count=0,
            errors=[],
        ),
        TransactionSetValidation(
            transaction_set_id="850",
            transaction_control_number="5679",
            status=TransactionStatus.REJECTED,
            ack_code="R",
            error_count=3,
            errors=[],
        ),
    ]

    result = validator.validate_functional_group(ak1, ak9, transaction_validations)

    assert result.status == FunctionalGroupStatus.PARTIALLY_ACCEPTED
    assert result.ack_code == "P"
    assert result.transaction_sets_included == 2
    assert result.transaction_sets_accepted == 1
    assert result.group_syntax_error_codes == ["5"]


def test_validate_997_accepted(validator: Validator997) -> None:
    """Test validating complete accepted 997 document."""
    isa = ISASegment(
        authorization_info_qualifier="00",
        authorization_info="          ",
        security_info_qualifier="00",
        security_info="          ",
        interchange_sender_qualifier="ZZ",
        interchange_sender_id="SENDER",
        interchange_receiver_qualifier="ZZ",
        interchange_receiver_id="RECEIVER",
        interchange_date="230101",
        interchange_time="1200",
        interchange_control_standards_id="U",
        interchange_control_version_number="00401",
        interchange_control_number="000000001",
        acknowledgment_requested="0",
        test_indicator="P",
        sub_element_separator=">",
    )

    ak1 = AK1Segment(
        functional_id_code="PO",
        group_control_number="1234",
    )

    ak9 = AK9Segment(
        functional_group_ack_code="A",
        number_of_transaction_sets_included=1,
        number_of_received_transaction_sets=1,
        number_of_accepted_transaction_sets=1,
    )

    from src.models.validation import TransactionSetValidation

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

    result = validator.validate_997(isa, ak1, ak9, transaction_validations)

    assert result.is_valid is True
    assert result.interchange_control_number == "000000001"
    assert result.interchange_sender_id == "SENDER"
    assert result.interchange_receiver_id == "RECEIVER"
    assert result.overall_status == "ACCEPTED"
    assert "1/1" in result.summary


def test_validate_997_rejected(validator: Validator997) -> None:
    """Test validating complete rejected 997 document."""
    isa = ISASegment(
        authorization_info_qualifier="00",
        authorization_info="          ",
        security_info_qualifier="00",
        security_info="          ",
        interchange_sender_qualifier="ZZ",
        interchange_sender_id="SENDER",
        interchange_receiver_qualifier="ZZ",
        interchange_receiver_id="RECEIVER",
        interchange_date="230101",
        interchange_time="1200",
        interchange_control_standards_id="U",
        interchange_control_version_number="00401",
        interchange_control_number="000000001",
        acknowledgment_requested="0",
        test_indicator="P",
        sub_element_separator=">",
    )

    ak1 = AK1Segment(
        functional_id_code="PO",
        group_control_number="1234",
    )

    ak9 = AK9Segment(
        functional_group_ack_code="R",
        number_of_transaction_sets_included=1,
        number_of_received_transaction_sets=1,
        number_of_accepted_transaction_sets=0,
    )

    from src.models.validation import TransactionSetValidation

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

    result = validator.validate_997(isa, ak1, ak9, transaction_validations)

    assert result.is_valid is False
    assert result.overall_status == "REJECTED"
    assert "0/1" in result.summary
