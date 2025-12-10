"""Shared validation pipeline for 997 files.

This module provides a reusable validation pipeline that can be used
by both the CLI and Streamlit UI.
"""

from typing import List

from src.models.segments import (
    AK1Segment,
    AK2Segment,
    AK3Segment,
    AK4Segment,
    AK5Segment,
    AK9Segment,
    ISASegment,
)
from src.models.validation import ValidationResult
from src.parser.delimiter_detector import DelimiterDetector
from src.parser.segment_parser import SegmentParser
from src.parser.tokenizer import EDITokenizer
from src.utils.error_code_mapper import ErrorCodeMapper
from src.validation.validator import Validator997


def run_validation_pipeline(content: str) -> ValidationResult:
    """Run complete validation pipeline on 997 EDI content.

    This is the single source of truth for validation logic, used by both
    CLI and Streamlit UI.

    Args:
        content: Raw EDI 997 file content

    Returns:
        ValidationResult: Complete validation results

    Raises:
        ValueError: If required segments are missing
        TokenizationError: If EDI parsing fails
    """
    # Detect delimiters first
    delimiter_detector = DelimiterDetector()
    delimiters = delimiter_detector.detect_from_file_content(content)

    # Initialize components with delimiters
    tokenizer = EDITokenizer()
    segment_parser = SegmentParser(delimiters)
    error_mapper = ErrorCodeMapper()
    validator = Validator997(error_mapper)

    # Tokenize
    segments = tokenizer.tokenize_content(content, delimiters)

    # Parse segments
    parsed_segments = []
    for segment in segments:
        if segment.strip():
            parsed_seg = segment_parser.parse_segment_by_id(segment)
            parsed_segments.append(parsed_seg)

    # Extract key segments
    isa = None
    ak1 = None
    ak9 = None
    transaction_validations: List = []

    # Current transaction context
    current_ak2 = None
    current_ak3_segments = []
    current_ak4_segments = []

    for seg in parsed_segments:
        if isinstance(seg, ISASegment):
            isa = seg
        elif isinstance(seg, AK1Segment):
            ak1 = seg
        elif isinstance(seg, AK2Segment):
            # Start new transaction
            if current_ak2:
                # Finish previous transaction
                ak5 = next(
                    (
                        s
                        for s in parsed_segments[parsed_segments.index(current_ak2) :]
                        if isinstance(s, AK5Segment)
                    ),
                    None,
                )
                if ak5:
                    ts_validation = validator.validate_transaction_set(
                        current_ak2, ak5, current_ak3_segments, current_ak4_segments
                    )
                    transaction_validations.append(ts_validation)

            current_ak2 = seg
            current_ak3_segments = []
            current_ak4_segments = []

        elif isinstance(seg, AK3Segment):
            current_ak3_segments.append(seg)
        elif isinstance(seg, AK4Segment):
            current_ak4_segments.append(seg)
        elif isinstance(seg, AK5Segment):
            # Process current transaction
            if current_ak2:
                ts_validation = validator.validate_transaction_set(
                    current_ak2, seg, current_ak3_segments, current_ak4_segments
                )
                transaction_validations.append(ts_validation)
                current_ak2 = None
                current_ak3_segments = []
                current_ak4_segments = []
        elif isinstance(seg, AK9Segment):
            ak9 = seg

    # Build validation result
    if not (isa and ak1 and ak9):
        raise ValueError("Missing required segments (ISA, AK1, or AK9)")

    validation_result = validator.validate_997(isa, ak1, ak9, transaction_validations)

    return validation_result
