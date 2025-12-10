"""Unit tests for DelimiterDetector."""

import pytest

from src.parser.delimiter_detector import DelimiterDetector, Delimiters
from src.parser.exceptions import DelimiterDetectionError, InvalidISASegmentError
from tests.fixtures.sample_997_files import (
    INVALID_ISA_TOO_SHORT,
    INVALID_NO_ISA,
    MINIMAL_ISA,
    SAMPLE_997_ACCEPTED,
    SAMPLE_997_ALT_DELIMITERS,
)


def test_delimiters_creation() -> None:
    """Test Delimiters object creation."""
    delimiters = Delimiters(
        element="*",
        segment="~",
        sub_element=">",
        repetition="^",
    )

    assert delimiters.element == "*"
    assert delimiters.segment == "~"
    assert delimiters.sub_element == ">"
    assert delimiters.repetition == "^"


def test_delimiters_repr() -> None:
    """Test Delimiters string representation."""
    delimiters = Delimiters(element="*", segment="~", sub_element=">")
    repr_str = repr(delimiters)

    assert "Delimiters" in repr_str
    assert "element='*'" in repr_str
    assert "segment='~'" in repr_str
    assert "sub_element='>'" in repr_str


def test_delimiters_equality() -> None:
    """Test Delimiters equality comparison."""
    d1 = Delimiters(element="*", segment="~", sub_element=">")
    d2 = Delimiters(element="*", segment="~", sub_element=">")
    d3 = Delimiters(element="|", segment="!", sub_element=":")

    assert d1 == d2
    assert d1 != d3
    assert d1 != "not a delimiter object"


def test_detect_from_isa_standard_delimiters() -> None:
    """Test delimiter detection with standard delimiters."""
    detector = DelimiterDetector()
    isa_segment = "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *230101*1200*U*00401*000000001*0*P*>~"

    delimiters = detector.detect_from_isa(isa_segment)

    assert delimiters.element == "*"
    assert delimiters.segment == "~"
    assert delimiters.sub_element == ">"


def test_detect_from_isa_alternative_delimiters() -> None:
    """Test delimiter detection with alternative delimiters."""
    detector = DelimiterDetector()
    isa_segment = "ISA|00|          |00|          |ZZ|SENDER         |ZZ|RECEIVER       |230101|1200|U|00401|000000001|0|P|:!"

    delimiters = detector.detect_from_isa(isa_segment)

    assert delimiters.element == "|"
    assert delimiters.segment == "!"
    assert delimiters.sub_element == ":"


def test_detect_from_isa_with_whitespace() -> None:
    """Test delimiter detection with leading/trailing whitespace."""
    detector = DelimiterDetector()
    isa_segment = "  ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *230101*1200*U*00401*000000001*0*P*>~  "

    delimiters = detector.detect_from_isa(isa_segment)

    assert delimiters.element == "*"
    assert delimiters.segment == "~"
    assert delimiters.sub_element == ">"


def test_detect_from_isa_empty_string() -> None:
    """Test delimiter detection with empty string."""
    detector = DelimiterDetector()

    with pytest.raises(InvalidISASegmentError, match="ISA segment is empty"):
        detector.detect_from_isa("")


def test_detect_from_isa_too_short() -> None:
    """Test delimiter detection with too-short ISA segment."""
    detector = DelimiterDetector()

    with pytest.raises(InvalidISASegmentError, match="ISA segment too short"):
        detector.detect_from_isa(INVALID_ISA_TOO_SHORT)


def test_detect_from_isa_no_isa_prefix() -> None:
    """Test delimiter detection without ISA prefix."""
    detector = DelimiterDetector()

    with pytest.raises(InvalidISASegmentError, match="does not start with 'ISA'"):
        detector.detect_from_isa(INVALID_NO_ISA)


def test_detect_from_isa_non_unique_delimiters() -> None:
    """Test delimiter detection with non-unique delimiters."""
    detector = DelimiterDetector()
    # Create ISA with same delimiter for sub-element and segment (both ~)
    # Position 104 (sub-element) and position 105 (segment) are both ~
    isa_segment = "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *230101*1200*U*00401*000000001*0*P*~~"

    with pytest.raises(DelimiterDetectionError, match="not unique"):
        detector.detect_from_isa(isa_segment)


def test_detect_from_file_content_standard() -> None:
    """Test delimiter detection from full file content."""
    detector = DelimiterDetector()

    delimiters = detector.detect_from_file_content(SAMPLE_997_ACCEPTED)

    assert delimiters.element == "*"
    assert delimiters.segment == "~"
    assert delimiters.sub_element == ">"


def test_detect_from_file_content_alt_delimiters() -> None:
    """Test delimiter detection from file with alternative delimiters."""
    detector = DelimiterDetector()

    delimiters = detector.detect_from_file_content(SAMPLE_997_ALT_DELIMITERS)

    assert delimiters.element == "|"
    assert delimiters.segment == "!"
    assert delimiters.sub_element == ":"


def test_detect_from_file_content_empty() -> None:
    """Test delimiter detection from empty content."""
    detector = DelimiterDetector()

    with pytest.raises(InvalidISASegmentError, match="File content is empty"):
        detector.detect_from_file_content("")


def test_detect_from_file_content_no_isa() -> None:
    """Test delimiter detection from content without ISA."""
    detector = DelimiterDetector()

    with pytest.raises(InvalidISASegmentError, match="does not start with ISA"):
        detector.detect_from_file_content("GS*FA*SENDER*RECEIVER~")


def test_use_default_delimiters() -> None:
    """Test using default delimiters."""
    detector = DelimiterDetector()

    delimiters = detector.use_default_delimiters()

    assert delimiters.element == "*"
    assert delimiters.segment == "~"
    assert delimiters.sub_element == ":"


def test_validate_delimiters_valid() -> None:
    """Test delimiter validation with valid delimiters."""
    detector = DelimiterDetector()
    delimiters = Delimiters(element="*", segment="~", sub_element=">", repetition="^")

    assert detector.validate_delimiters(delimiters) is True


def test_validate_delimiters_not_unique() -> None:
    """Test delimiter validation with non-unique delimiters."""
    detector = DelimiterDetector()
    delimiters = Delimiters(element="*", segment="*", sub_element=">")

    assert detector.validate_delimiters(delimiters) is False


def test_validate_delimiters_multi_character() -> None:
    """Test delimiter validation with multi-character delimiter."""
    detector = DelimiterDetector()
    delimiters = Delimiters(element="**", segment="~", sub_element=">")

    assert detector.validate_delimiters(delimiters) is False


def test_delimiters_to_config() -> None:
    """Test converting Delimiters to Pydantic config."""
    delimiters = Delimiters(element="*", segment="~", sub_element=">", repetition="^")

    config = delimiters.to_config()

    assert config.element == "*"
    assert config.segment == "~"
    assert config.sub_element == ">"
    assert config.repetition == "^"


def test_delimiters_from_config() -> None:
    """Test creating Delimiters from Pydantic config."""
    from src.models.config_schemas import DelimitersConfig

    config = DelimitersConfig(
        element="|",
        segment="!",
        sub_element=":",
        repetition="^",
    )

    delimiters = Delimiters.from_config(config)

    assert delimiters.element == "|"
    assert delimiters.segment == "!"
    assert delimiters.sub_element == ":"
    assert delimiters.repetition == "^"


def test_detect_from_minimal_isa() -> None:
    """Test delimiter detection from minimal ISA segment."""
    detector = DelimiterDetector()

    delimiters = detector.detect_from_isa(MINIMAL_ISA.strip())

    assert delimiters.element == "*"
    assert delimiters.segment == "~"
    assert delimiters.sub_element == ">"
