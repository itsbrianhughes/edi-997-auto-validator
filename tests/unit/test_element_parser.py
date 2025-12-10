"""Unit tests for ElementParser."""

import pytest

from src.parser.delimiter_detector import Delimiters
from src.parser.element_parser import ElementParser
from src.parser.exceptions import TokenizationError


@pytest.fixture
def delimiters() -> Delimiters:
    """Standard delimiters fixture."""
    return Delimiters(element="*", segment="~", sub_element=">", repetition="^")


@pytest.fixture
def element_parser(delimiters: Delimiters) -> ElementParser:
    """Element parser fixture."""
    return ElementParser(delimiters)


def test_split_segment(element_parser: ElementParser) -> None:
    """Test splitting segment into elements."""
    elements = element_parser.split_segment("ST*997*0001")
    assert elements == ["ST", "997", "0001"]


def test_get_element_valid(element_parser: ElementParser) -> None:
    """Test getting valid element."""
    elements = ["ST", "997", "0001"]
    value = element_parser.get_element(elements, 1)
    assert value == "997"


def test_get_element_required_missing(element_parser: ElementParser) -> None:
    """Test getting required element that's missing."""
    elements = ["ST", "997"]

    with pytest.raises(TokenizationError, match="Required element.*is missing"):
        element_parser.get_element(elements, 5, required=True)


def test_get_element_optional_missing(element_parser: ElementParser) -> None:
    """Test getting optional element that's missing."""
    elements = ["ST", "997"]
    value = element_parser.get_element(elements, 5, required=False, default="N/A")
    assert value == "N/A"


def test_get_element_as_int_valid(element_parser: ElementParser) -> None:
    """Test getting element as integer."""
    elements = ["AK9", "A", "1", "1", "1"]
    value = element_parser.get_element_as_int(elements, 2)
    assert value == 1
    assert isinstance(value, int)


def test_get_element_as_int_invalid(element_parser: ElementParser) -> None:
    """Test getting non-integer element as int."""
    elements = ["AK9", "A", "ABC", "1", "1"]

    with pytest.raises(TokenizationError, match="not a valid integer"):
        element_parser.get_element_as_int(elements, 2)


def test_parse_segment_id(element_parser: ElementParser) -> None:
    """Test parsing segment ID."""
    segment_id = element_parser.parse_segment_id("AK1*PO*1234")
    assert segment_id == "AK1"


def test_parse_segment_id_empty(element_parser: ElementParser) -> None:
    """Test parsing segment ID from empty segment."""
    with pytest.raises(TokenizationError, match="Cannot extract segment ID"):
        element_parser.parse_segment_id("")


def test_validate_segment_id_valid(element_parser: ElementParser) -> None:
    """Test validating matching segment ID."""
    element_parser.validate_segment_id("AK1*PO*1234", "AK1")
    # Should not raise


def test_validate_segment_id_invalid(element_parser: ElementParser) -> None:
    """Test validating non-matching segment ID."""
    with pytest.raises(TokenizationError, match="Expected segment ID"):
        element_parser.validate_segment_id("AK2*850*5678", "AK1")


def test_get_element_count(element_parser: ElementParser) -> None:
    """Test getting element count."""
    count = element_parser.get_element_count("ST*997*0001")
    assert count == 3


def test_split_composite_element(element_parser: ElementParser) -> None:
    """Test splitting composite element."""
    sub_elements = element_parser.split_composite_element("C040>020")
    assert sub_elements == ["C040", "020"]


def test_split_composite_element_no_separator(element_parser: ElementParser) -> None:
    """Test splitting element without sub-element separator."""
    sub_elements = element_parser.split_composite_element("SIMPLE")
    assert sub_elements == ["SIMPLE"]


def test_split_repeating_element(element_parser: ElementParser) -> None:
    """Test splitting repeating element."""
    repetitions = element_parser.split_repeating_element("A^B^C")
    assert repetitions == ["A", "B", "C"]


def test_split_repeating_element_no_separator(element_parser: ElementParser) -> None:
    """Test splitting element without repetition separator."""
    repetitions = element_parser.split_repeating_element("SINGLE")
    assert repetitions == ["SINGLE"]


def test_parse_segment_to_dict(element_parser: ElementParser) -> None:
    """Test parsing segment to dictionary."""
    result = element_parser.parse_segment_to_dict("AK1*PO*1234")

    assert result["segment_id"] == "AK1"
    assert result["elements"] == ["AK1", "PO", "1234"]
