"""Unit tests for SegmentParser."""

import pytest

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
from src.parser.delimiter_detector import Delimiters
from src.parser.segment_parser import SegmentParser
from tests.fixtures.sample_segments import (
    AK1_VALID,
    AK2_VALID,
    AK3_VALID,
    AK4_VALID,
    AK5_ACCEPTED,
    AK9_ACCEPTED,
    GE_VALID,
    GS_VALID,
    IEA_VALID,
    ISA_VALID,
    SE_VALID,
    ST_VALID,
)


@pytest.fixture
def delimiters() -> Delimiters:
    """Standard delimiters fixture."""
    return Delimiters(element="*", segment="~", sub_element=">", repetition="^")


@pytest.fixture
def segment_parser(delimiters: Delimiters) -> SegmentParser:
    """Segment parser fixture."""
    return SegmentParser(delimiters)


def test_parse_isa_segment(segment_parser: SegmentParser) -> None:
    """Test parsing ISA segment."""
    isa = segment_parser.parse_segment(ISA_VALID, ISASegment)

    assert isinstance(isa, ISASegment)
    assert isa.interchange_sender_id == "SENDER"
    assert isa.interchange_control_number == "000000001"


def test_parse_gs_segment(segment_parser: SegmentParser) -> None:
    """Test parsing GS segment."""
    gs = segment_parser.parse_segment(GS_VALID, GSSegment)

    assert isinstance(gs, GSSegment)
    assert gs.functional_id_code == "FA"
    assert gs.group_control_number == "1"


def test_parse_st_segment(segment_parser: SegmentParser) -> None:
    """Test parsing ST segment."""
    st = segment_parser.parse_segment(ST_VALID, STSegment)

    assert isinstance(st, STSegment)
    assert st.transaction_set_id == "997"
    assert st.transaction_set_control_number == "0001"


def test_parse_ak1_segment(segment_parser: SegmentParser) -> None:
    """Test parsing AK1 segment."""
    ak1 = segment_parser.parse_segment(AK1_VALID, AK1Segment)

    assert isinstance(ak1, AK1Segment)
    assert ak1.functional_id_code == "PO"
    assert ak1.group_control_number == "1234"


def test_parse_ak2_segment(segment_parser: SegmentParser) -> None:
    """Test parsing AK2 segment."""
    ak2 = segment_parser.parse_segment(AK2_VALID, AK2Segment)

    assert isinstance(ak2, AK2Segment)
    assert ak2.transaction_set_id == "850"
    assert ak2.transaction_set_control_number == "5678"


def test_parse_ak3_segment(segment_parser: SegmentParser) -> None:
    """Test parsing AK3 segment."""
    ak3 = segment_parser.parse_segment(AK3_VALID, AK3Segment)

    assert isinstance(ak3, AK3Segment)
    assert ak3.segment_id == "N1"
    assert ak3.segment_position_in_transaction_set == 2


def test_parse_ak4_segment(segment_parser: SegmentParser) -> None:
    """Test parsing AK4 segment."""
    ak4 = segment_parser.parse_segment(AK4_VALID, AK4Segment)

    assert isinstance(ak4, AK4Segment)
    assert ak4.element_position_in_segment == 1
    assert ak4.data_element_reference_number == 66


def test_parse_ak5_segment(segment_parser: SegmentParser) -> None:
    """Test parsing AK5 segment."""
    ak5 = segment_parser.parse_segment(AK5_ACCEPTED, AK5Segment)

    assert isinstance(ak5, AK5Segment)
    assert ak5.transaction_set_ack_code == "A"


def test_parse_ak9_segment(segment_parser: SegmentParser) -> None:
    """Test parsing AK9 segment."""
    ak9 = segment_parser.parse_segment(AK9_ACCEPTED, AK9Segment)

    assert isinstance(ak9, AK9Segment)
    assert ak9.functional_group_ack_code == "A"
    assert ak9.number_of_transaction_sets_included == 1


def test_parse_se_segment(segment_parser: SegmentParser) -> None:
    """Test parsing SE segment."""
    se = segment_parser.parse_segment(SE_VALID, SESegment)

    assert isinstance(se, SESegment)
    assert se.number_of_included_segments == 4
    assert se.transaction_set_control_number == "0001"


def test_parse_ge_segment(segment_parser: SegmentParser) -> None:
    """Test parsing GE segment."""
    ge = segment_parser.parse_segment(GE_VALID, GESegment)

    assert isinstance(ge, GESegment)
    assert ge.number_of_transaction_sets == 1


def test_parse_iea_segment(segment_parser: SegmentParser) -> None:
    """Test parsing IEA segment."""
    iea = segment_parser.parse_segment(IEA_VALID, IEASegment)

    assert isinstance(iea, IEASegment)
    assert iea.number_of_included_groups == 1


def test_parse_segment_by_id_ak1(segment_parser: SegmentParser) -> None:
    """Test parsing segment automatically by ID."""
    segment = segment_parser.parse_segment_by_id(AK1_VALID)

    assert isinstance(segment, AK1Segment)
    assert segment.functional_id_code == "PO"


def test_parse_segment_by_id_ak9(segment_parser: SegmentParser) -> None:
    """Test parsing AK9 segment by ID."""
    segment = segment_parser.parse_segment_by_id(AK9_ACCEPTED)

    assert isinstance(segment, AK9Segment)
    assert segment.functional_group_ack_code == "A"


def test_parse_segment_by_id_st(segment_parser: SegmentParser) -> None:
    """Test parsing ST segment by ID."""
    segment = segment_parser.parse_segment_by_id(ST_VALID)

    assert isinstance(segment, STSegment)
    assert segment.transaction_set_id == "997"


def test_parse_all_segment_types(segment_parser: SegmentParser) -> None:
    """Test parsing all segment types."""
    segments = {
        "ISA": (ISA_VALID, ISASegment),
        "GS": (GS_VALID, GSSegment),
        "ST": (ST_VALID, STSegment),
        "AK1": (AK1_VALID, AK1Segment),
        "AK2": (AK2_VALID, AK2Segment),
        "AK3": (AK3_VALID, AK3Segment),
        "AK4": (AK4_VALID, AK4Segment),
        "AK5": (AK5_ACCEPTED, AK5Segment),
        "AK9": (AK9_ACCEPTED, AK9Segment),
        "SE": (SE_VALID, SESegment),
        "GE": (GE_VALID, GESegment),
        "IEA": (IEA_VALID, IEASegment),
    }

    for segment_id, (segment_str, expected_type) in segments.items():
        parsed = segment_parser.parse_segment(segment_str, expected_type)
        assert isinstance(parsed, expected_type), f"Failed to parse {segment_id}"
