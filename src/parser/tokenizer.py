"""EDI file tokenization."""

from pathlib import Path
from typing import List, Optional, Union

from src.models.config_schemas import ParserConfig
from src.parser.delimiter_detector import DelimiterDetector, Delimiters
from src.parser.exceptions import (
    EmptyFileError,
    FileSizeExceededError,
    TokenizationError,
)
from src.utils.logger import get_logger
from src.utils.profiler import profile

logger = get_logger(__name__)


class EDITokenizer:
    """Tokenize raw EDI file content into segments."""

    def __init__(
        self,
        config: Optional[ParserConfig] = None,
        delimiter_detector: Optional[DelimiterDetector] = None,
    ) -> None:
        """Initialize EDI tokenizer.

        Args:
            config: Parser configuration (default: ParserConfig())
            delimiter_detector: Delimiter detector instance (default: DelimiterDetector())
        """
        self.config = config or ParserConfig()
        self.delimiter_detector = delimiter_detector or DelimiterDetector(
            default_delimiters=self.config.default_delimiters
        )
        logger.debug("tokenizer_initialized", config=str(self.config))

    @profile(operation="tokenize_content")
    def tokenize_content(
        self,
        content: str,
        delimiters: Optional[Delimiters] = None,
    ) -> List[str]:
        """Tokenize raw EDI content into segments.

        Args:
            content: Raw EDI file content
            delimiters: Optional pre-detected delimiters (will auto-detect if not provided)

        Returns:
            List of segment strings

        Raises:
            EmptyFileError: If content is empty
            TokenizationError: If tokenization fails
        """
        # Validate content
        if not content or not content.strip():
            raise EmptyFileError("EDI content is empty")

        # Detect delimiters if not provided
        if delimiters is None:
            if self.config.auto_detect_delimiters:
                try:
                    delimiters = self.delimiter_detector.detect_from_file_content(content)
                    logger.info("delimiters_auto_detected", delimiters=str(delimiters))
                except Exception as e:
                    logger.warning(
                        "delimiter_detection_failed",
                        error=str(e),
                        using_defaults=True,
                    )
                    delimiters = self.delimiter_detector.use_default_delimiters()
            else:
                delimiters = self.delimiter_detector.use_default_delimiters()

        # Handle line breaks
        if not self.config.preserve_line_breaks:
            # Remove line breaks and carriage returns
            content = content.replace("\r\n", "").replace("\n", "").replace("\r", "")

        # Split on segment terminator
        segments = content.split(delimiters.segment)

        # Clean up segments
        cleaned_segments = []
        for segment in segments:
            # Trim whitespace if configured
            if self.config.trim_whitespace:
                segment = segment.strip()

            # Skip empty segments
            if not segment:
                continue

            cleaned_segments.append(segment)

        logger.info(
            "tokenization_complete",
            total_segments=len(cleaned_segments),
            segment_terminator=delimiters.segment,
        )

        return cleaned_segments

    @profile(operation="tokenize_file")
    def tokenize_file(
        self,
        file_path: Union[str, Path],
        encoding: str = "utf-8",
    ) -> List[str]:
        """Tokenize an EDI file into segments.

        Args:
            file_path: Path to EDI file
            encoding: File encoding (default: utf-8)

        Returns:
            List of segment strings

        Raises:
            FileNotFoundError: If file doesn't exist
            FileSizeExceededError: If file exceeds maximum size
            EmptyFileError: If file is empty
            TokenizationError: If tokenization fails
        """
        file_path = Path(file_path)

        # Check file exists
        if not file_path.exists():
            raise FileNotFoundError(f"EDI file not found: {file_path}")

        # Check file size
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.config.max_file_size_mb:
            raise FileSizeExceededError(
                f"File size ({file_size_mb:.2f} MB) exceeds maximum "
                f"({self.config.max_file_size_mb} MB)"
            )

        # Read file content
        try:
            with open(file_path, "r", encoding=encoding) as f:
                content = f.read()
        except Exception as e:
            raise TokenizationError(f"Failed to read file {file_path}: {str(e)}") from e

        logger.info("file_loaded", path=str(file_path), size_mb=round(file_size_mb, 2))

        # Tokenize content
        return self.tokenize_content(content)

    def get_segment_count(self, content: str) -> int:
        """Get the count of segments in EDI content without full tokenization.

        Args:
            content: Raw EDI content

        Returns:
            Number of segments
        """
        try:
            segments = self.tokenize_content(content)
            return len(segments)
        except Exception as e:
            logger.error("segment_count_failed", error=str(e))
            return 0

    def extract_isa_segment(self, content: str) -> Optional[str]:
        """Extract the ISA segment from EDI content.

        Args:
            content: Raw EDI content

        Returns:
            ISA segment string or None if not found
        """
        try:
            segments = self.tokenize_content(content)
            for segment in segments:
                if segment.startswith("ISA"):
                    return segment
            return None
        except Exception as e:
            logger.error("isa_extraction_failed", error=str(e))
            return None

    def validate_segment_structure(self, segment: str, delimiters: Delimiters) -> bool:
        """Validate that a segment has valid structure.

        Args:
            segment: Segment string
            delimiters: Delimiters to use for validation

        Returns:
            True if valid, False otherwise
        """
        # Check segment is not empty
        if not segment:
            return False

        # Check segment contains element separator
        if delimiters.element not in segment:
            return False

        # Check segment starts with 2-3 letter code
        if len(segment) < 2:
            return False

        # Segment ID should be 2-3 uppercase letters
        segment_id = segment.split(delimiters.element)[0]
        if not (2 <= len(segment_id) <= 3 and segment_id.isalpha() and segment_id.isupper()):
            return False

        return True

    def get_segment_statistics(self, segments: List[str]) -> dict:
        """Get statistics about tokenized segments.

        Args:
            segments: List of segment strings

        Returns:
            Dictionary with statistics
        """
        if not segments:
            return {
                "total_segments": 0,
                "unique_segment_types": 0,
                "segment_type_counts": {},
                "avg_segment_length": 0,
                "min_segment_length": 0,
                "max_segment_length": 0,
            }

        # Count segment types
        segment_type_counts: dict = {}
        for segment in segments:
            # Extract segment ID (first 2-3 characters before element separator)
            # We'll use a simple heuristic: find first non-letter character
            segment_id = ""
            for char in segment:
                if char.isalpha():
                    segment_id += char
                else:
                    break

            if segment_id:
                segment_type_counts[segment_id] = segment_type_counts.get(segment_id, 0) + 1

        # Calculate lengths
        segment_lengths = [len(seg) for seg in segments]

        return {
            "total_segments": len(segments),
            "unique_segment_types": len(segment_type_counts),
            "segment_type_counts": segment_type_counts,
            "avg_segment_length": sum(segment_lengths) / len(segment_lengths),
            "min_segment_length": min(segment_lengths),
            "max_segment_length": max(segment_lengths),
        }
