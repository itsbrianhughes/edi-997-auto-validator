"""Unit tests for segment models."""

import pytest
from pydantic import ValidationError

from src.models.segments import (
    AK1Segment,
    AK2Segment,
    AK3Segment,
    AK4Segment,
    AK5Segment,
    AK9Segment,
    GESegment,
    GSSegment,
    IEASegment,
    ISASegment,
    SESegment,
    STSegment,
)


def test_isa_segment_valid() -> None:
    """Test creating valid ISA segment."""
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

    assert isa.interchange_sender_id == "SENDER"
    assert isa.interchange_control_number == "000000001"


def test_gs_segment_valid() -> None:
    """Test creating valid GS segment."""
    gs = GSSegment(
        functional_id_code="FA",
        application_sender_code="SENDER",
        application_receiver_code="RECEIVER",
        date="20230101",
        time="1200",
        group_control_number="1",
        responsible_agency_code="X",
        version_release_industry_id="004010",
    )

    assert gs.functional_id_code == "FA"
    assert gs.group_control_number == "1"


def test_st_segment_valid() -> None:
    """Test creating valid ST segment."""
    st = STSegment(
        transaction_set_id="997",
        transaction_set_control_number="0001",
    )

    assert st.transaction_set_id == "997"
    assert st.transaction_set_control_number == "0001"


def test_ak1_segment_valid() -> None:
    """Test creating valid AK1 segment."""
    ak1 = AK1Segment(
        functional_id_code="PO",
        group_control_number="1234",
    )

    assert ak1.functional_id_code == "PO"
    assert ak1.group_control_number == "1234"


def test_ak3_segment_with_integer_position() -> None:
    """Test AK3 segment with integer position."""
    ak3 = AK3Segment(
        segment_id="N1",
        segment_position_in_transaction_set=2,
    )

    assert ak3.segment_id == "N1"
    assert ak3.segment_position_in_transaction_set == 2


def test_ak3_segment_with_string_position() -> None:
    """Test AK3 segment converting string position to int."""
    ak3 = AK3Segment(
        segment_id="N1",
        segment_position_in_transaction_set="5",
    )

    assert ak3.segment_position_in_transaction_set == 5


def test_ak4_segment_valid() -> None:
    """Test creating valid AK4 segment."""
    ak4 = AK4Segment(
        element_position_in_segment=1,
        data_element_reference_number=66,
        data_element_syntax_error_code="1",
    )

    assert ak4.element_position_in_segment == 1
    assert ak4.data_element_reference_number == 66


def test_ak5_segment_get_error_codes() -> None:
    """Test AK5 segment get_error_codes method."""
    ak5 = AK5Segment(
        transaction_set_ack_code="R",
        transaction_set_syntax_error_code_1="1",
        transaction_set_syntax_error_code_2="3",
        transaction_set_syntax_error_code_3="5",
    )

    errors = ak5.get_error_codes()
    assert errors == ["1", "3", "5"]


def test_ak9_segment_with_counts() -> None:
    """Test AK9 segment with count fields."""
    ak9 = AK9Segment(
        functional_group_ack_code="A",
        number_of_transaction_sets_included=1,
        number_of_received_transaction_sets=1,
        number_of_accepted_transaction_sets=1,
    )

    assert ak9.number_of_transaction_sets_included == 1


def test_ak9_segment_string_to_int_conversion() -> None:
    """Test AK9 segment converts string counts to integers."""
    ak9 = AK9Segment(
        functional_group_ack_code="A",
        number_of_transaction_sets_included="2",
        number_of_received_transaction_sets="2",
        number_of_accepted_transaction_sets="1",
    )

    assert ak9.number_of_transaction_sets_included == 2
    assert ak9.number_of_accepted_transaction_sets == 1


def test_ak9_segment_get_error_codes() -> None:
    """Test AK9 segment get_error_codes method."""
    ak9 = AK9Segment(
        functional_group_ack_code="E",
        number_of_transaction_sets_included=1,
        number_of_received_transaction_sets=1,
        number_of_accepted_transaction_sets=1,
        functional_group_syntax_error_code_1="1",
        functional_group_syntax_error_code_2="5",
    )

    errors = ak9.get_error_codes()
    assert errors == ["1", "5"]


def test_se_segment_valid() -> None:
    """Test creating valid SE segment."""
    se = SESegment(
        number_of_included_segments=4,
        transaction_set_control_number="0001",
    )

    assert se.number_of_included_segments == 4


def test_ge_segment_valid() -> None:
    """Test creating valid GE segment."""
    ge = GESegment(
        number_of_transaction_sets=1,
        group_control_number="1",
    )

    assert ge.number_of_transaction_sets == 1


def test_iea_segment_valid() -> None:
    """Test creating valid IEA segment."""
    iea = IEASegment(
        number_of_included_groups=1,
        interchange_control_number="000000001",
    )

    assert iea.number_of_included_groups == 1


def test_segment_validation_error() -> None:
    """Test segment validation error for invalid data."""
    with pytest.raises(ValidationError):
        AK1Segment(
            functional_id_code="TOOLONG",  # Too long
            group_control_number="1234",
        )


def test_segment_whitespace_stripping() -> None:
    """Test that whitespace is stripped from fields."""
    ak1 = AK1Segment(
        functional_id_code="  PO  ",
        group_control_number="  1234  ",
    )

    assert ak1.functional_id_code == "PO"
    assert ak1.group_control_number == "1234"
