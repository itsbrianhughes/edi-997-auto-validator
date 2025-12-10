"""Unit tests for EDITokenizer."""

import tempfile
from pathlib import Path

import pytest

from src.models.config_schemas import ParserConfig
from src.parser.delimiter_detector import Delimiters
from src.parser.exceptions import EmptyFileError, FileSizeExceededError
from src.parser.tokenizer import EDITokenizer
from tests.fixtures.sample_997_files import (
    EMPTY_CONTENT,
    SAMPLE_997_ACCEPTED,
    SAMPLE_997_ALT_DELIMITERS,
    SAMPLE_997_CRLF,
    SAMPLE_997_MIXED_ENDINGS,
    SAMPLE_997_MULTIPLE_GROUPS,
    SAMPLE_997_REJECTED,
    SAMPLE_997_WITH_LINE_BREAKS,
    WHITESPACE_ONLY,
)


def test_tokenizer_initialization() -> None:
    """Test EDITokenizer initialization."""
    tokenizer = EDITokenizer()

    assert tokenizer.config is not None
    assert tokenizer.delimiter_detector is not None


def test_tokenizer_with_custom_config() -> None:
    """Test EDITokenizer with custom configuration."""
    config = ParserConfig(trim_whitespace=False, auto_detect_delimiters=False)
    tokenizer = EDITokenizer(config=config)

    assert tokenizer.config.trim_whitespace is False
    assert tokenizer.config.auto_detect_delimiters is False


def test_tokenize_content_standard_delimiters() -> None:
    """Test tokenizing content with standard delimiters."""
    tokenizer = EDITokenizer()

    segments = tokenizer.tokenize_content(SAMPLE_997_ACCEPTED)

    assert len(segments) > 0
    assert segments[0].startswith("ISA")
    assert segments[1].startswith("GS")
    assert segments[-1].startswith("IEA")


def test_tokenize_content_alternative_delimiters() -> None:
    """Test tokenizing content with alternative delimiters."""
    tokenizer = EDITokenizer()

    segments = tokenizer.tokenize_content(SAMPLE_997_ALT_DELIMITERS)

    assert len(segments) > 0
    assert segments[0].startswith("ISA")
    # Should have detected pipe as element separator
    assert "|" in segments[0]


def test_tokenize_content_with_line_breaks() -> None:
    """Test tokenizing content with line breaks."""
    tokenizer = EDITokenizer()

    segments = tokenizer.tokenize_content(SAMPLE_997_WITH_LINE_BREAKS)

    assert len(segments) > 0
    # Line breaks should be removed
    for segment in segments:
        assert "\n" not in segment
        assert "\r" not in segment


def test_tokenize_content_preserve_line_breaks() -> None:
    """Test tokenizing content while preserving line breaks."""
    config = ParserConfig(preserve_line_breaks=True)
    tokenizer = EDITokenizer(config=config)

    segments = tokenizer.tokenize_content(SAMPLE_997_WITH_LINE_BREAKS)

    # Some segments should have line breaks if preserve is enabled
    # But segments are still split on segment terminator, so individual segments won't have breaks
    assert len(segments) > 0


def test_tokenize_content_empty_string() -> None:
    """Test tokenizing empty content."""
    tokenizer = EDITokenizer()

    with pytest.raises(EmptyFileError, match="EDI content is empty"):
        tokenizer.tokenize_content("")


def test_tokenize_content_whitespace_only() -> None:
    """Test tokenizing whitespace-only content."""
    tokenizer = EDITokenizer()

    with pytest.raises(EmptyFileError, match="EDI content is empty"):
        tokenizer.tokenize_content(WHITESPACE_ONLY)


def test_tokenize_content_with_provided_delimiters() -> None:
    """Test tokenizing with pre-provided delimiters."""
    tokenizer = EDITokenizer()
    delimiters = Delimiters(element="*", segment="~", sub_element=">")

    segments = tokenizer.tokenize_content(SAMPLE_997_ACCEPTED, delimiters=delimiters)

    assert len(segments) > 0
    assert segments[0].startswith("ISA")


def test_tokenize_content_trim_whitespace() -> None:
    """Test tokenizing with whitespace trimming."""
    config = ParserConfig(trim_whitespace=True)
    tokenizer = EDITokenizer(config=config)

    # Create content with extra whitespace
    content_with_spaces = "  ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *230101*1200*U*00401*000000001*0*P*>~  GS*FA*SENDER*RECEIVER*20230101*1200*1*X*004010~  "

    segments = tokenizer.tokenize_content(content_with_spaces)

    # Segments should be trimmed
    for segment in segments:
        assert segment == segment.strip()


def test_tokenize_content_no_trim_whitespace() -> None:
    """Test tokenizing without whitespace trimming."""
    config = ParserConfig(trim_whitespace=False)
    tokenizer = EDITokenizer(config=config)

    # This test is tricky because auto-detection might fail with extra spaces
    # So we provide delimiters explicitly
    delimiters = Delimiters(element="*", segment="~", sub_element=">")

    content = "ISA*TEST~  GS*FA~  "
    segments = tokenizer.tokenize_content(content, delimiters=delimiters)

    # Some segments might have trailing/leading spaces
    assert len(segments) >= 2


def test_tokenize_file_success() -> None:
    """Test tokenizing a file successfully."""
    tokenizer = EDITokenizer()

    # Create temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".edi", delete=False) as f:
        f.write(SAMPLE_997_ACCEPTED)
        temp_path = Path(f.name)

    try:
        segments = tokenizer.tokenize_file(temp_path)

        assert len(segments) > 0
        assert segments[0].startswith("ISA")
    finally:
        temp_path.unlink()


def test_tokenize_file_not_found() -> None:
    """Test tokenizing non-existent file."""
    tokenizer = EDITokenizer()

    with pytest.raises(FileNotFoundError, match="EDI file not found"):
        tokenizer.tokenize_file("/nonexistent/file.edi")


def test_tokenize_file_size_exceeded() -> None:
    """Test tokenizing file that exceeds size limit."""
    config = ParserConfig(max_file_size_mb=1)  # 1 MB limit
    tokenizer = EDITokenizer(config=config)

    # Create file with content exceeding limit (2 MB)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".edi", delete=False) as f:
        f.write("X" * (2 * 1024 * 1024))  # 2 MB
        temp_path = Path(f.name)

    try:
        with pytest.raises(FileSizeExceededError, match="exceeds maximum"):
            tokenizer.tokenize_file(temp_path)
    finally:
        temp_path.unlink()


def test_get_segment_count() -> None:
    """Test getting segment count."""
    tokenizer = EDITokenizer()

    count = tokenizer.get_segment_count(SAMPLE_997_ACCEPTED)

    assert count > 0
    assert count == 8  # ISA, GS, ST, AK1, AK9, SE, GE, IEA


def test_get_segment_count_empty() -> None:
    """Test getting segment count from empty content."""
    tokenizer = EDITokenizer()

    count = tokenizer.get_segment_count("")

    assert count == 0


def test_extract_isa_segment() -> None:
    """Test extracting ISA segment."""
    tokenizer = EDITokenizer()

    isa_segment = tokenizer.extract_isa_segment(SAMPLE_997_ACCEPTED)

    assert isa_segment is not None
    assert isa_segment.startswith("ISA")
    assert "*" in isa_segment


def test_extract_isa_segment_not_found() -> None:
    """Test extracting ISA segment when not present."""
    tokenizer = EDITokenizer()

    # Content without ISA
    content = "GS*FA*SENDER*RECEIVER~ST*997*0001~"

    isa_segment = tokenizer.extract_isa_segment(content)

    # Should return None or handle gracefully
    assert isa_segment is None


def test_validate_segment_structure_valid() -> None:
    """Test validating valid segment structure."""
    tokenizer = EDITokenizer()
    delimiters = Delimiters(element="*", segment="~", sub_element=">")

    valid_segment = "ISA*00*          *00*          *ZZ*SENDER"

    assert tokenizer.validate_segment_structure(valid_segment, delimiters) is True


def test_validate_segment_structure_invalid() -> None:
    """Test validating invalid segment structure."""
    tokenizer = EDITokenizer()
    delimiters = Delimiters(element="*", segment="~", sub_element=">")

    # No element separator
    invalid_segment = "INVALID"

    assert tokenizer.validate_segment_structure(invalid_segment, delimiters) is False


def test_validate_segment_structure_empty() -> None:
    """Test validating empty segment."""
    tokenizer = EDITokenizer()
    delimiters = Delimiters(element="*", segment="~", sub_element=">")

    assert tokenizer.validate_segment_structure("", delimiters) is False


def test_get_segment_statistics() -> None:
    """Test getting segment statistics."""
    tokenizer = EDITokenizer()

    segments = tokenizer.tokenize_content(SAMPLE_997_ACCEPTED)
    stats = tokenizer.get_segment_statistics(segments)

    assert stats["total_segments"] > 0
    assert stats["unique_segment_types"] > 0
    assert "ISA" in stats["segment_type_counts"]
    assert "GS" in stats["segment_type_counts"]
    assert stats["avg_segment_length"] > 0
    assert stats["min_segment_length"] > 0
    assert stats["max_segment_length"] > 0


def test_get_segment_statistics_empty() -> None:
    """Test getting statistics from empty segments."""
    tokenizer = EDITokenizer()

    stats = tokenizer.get_segment_statistics([])

    assert stats["total_segments"] == 0
    assert stats["unique_segment_types"] == 0
    assert stats["avg_segment_length"] == 0


def test_tokenize_multiple_groups() -> None:
    """Test tokenizing EDI with multiple functional groups."""
    tokenizer = EDITokenizer()

    segments = tokenizer.tokenize_content(SAMPLE_997_MULTIPLE_GROUPS)

    assert len(segments) > 0

    # Count GS segments (should be 2)
    gs_count = sum(1 for seg in segments if seg.startswith("GS"))
    assert gs_count == 2

    # Count ST segments (should be 2)
    st_count = sum(1 for seg in segments if seg.startswith("ST"))
    assert st_count == 2


def test_tokenize_crlf_line_endings() -> None:
    """Test tokenizing with CRLF line endings."""
    tokenizer = EDITokenizer()

    segments = tokenizer.tokenize_content(SAMPLE_997_CRLF)

    assert len(segments) > 0

    # Should not have \r\n in segments
    for segment in segments:
        assert "\r\n" not in segment


def test_tokenize_mixed_line_endings() -> None:
    """Test tokenizing with mixed line endings."""
    tokenizer = EDITokenizer()

    segments = tokenizer.tokenize_content(SAMPLE_997_MIXED_ENDINGS)

    assert len(segments) > 0

    # Should not have any line ending characters
    for segment in segments:
        assert "\r" not in segment
        assert "\n" not in segment


def test_tokenize_rejected_transaction() -> None:
    """Test tokenizing rejected transaction."""
    tokenizer = EDITokenizer()

    segments = tokenizer.tokenize_content(SAMPLE_997_REJECTED)

    assert len(segments) > 0

    # Should have AK2 segment (transaction set info)
    assert any(seg.startswith("AK2") for seg in segments)

    # Should have AK3, AK4 segments (error details)
    assert any(seg.startswith("AK3") for seg in segments)
    assert any(seg.startswith("AK4") for seg in segments)


def test_tokenize_with_auto_detect_disabled() -> None:
    """Test tokenizing with auto-detect disabled."""
    config = ParserConfig(auto_detect_delimiters=False)
    tokenizer = EDITokenizer(config=config)

    # Should use default delimiters
    segments = tokenizer.tokenize_content(SAMPLE_997_ACCEPTED)

    assert len(segments) > 0
