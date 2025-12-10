"""Delimiter detection from ISA segment."""

from typing import Optional

from src.models.config_schemas import DelimitersConfig
from src.parser.exceptions import DelimiterDetectionError, InvalidISASegmentError
from src.utils.logger import get_logger

logger = get_logger(__name__)


class Delimiters:
    """Container for EDI delimiters."""

    def __init__(
        self,
        element: str,
        segment: str,
        sub_element: str,
        repetition: Optional[str] = None,
    ) -> None:
        """Initialize delimiters.

        Args:
            element: Element separator (typically '*')
            segment: Segment terminator (typically '~')
            sub_element: Sub-element separator (typically ':' or '>')
            repetition: Repetition separator (typically '^', optional)
        """
        self.element = element
        self.segment = segment
        self.sub_element = sub_element
        self.repetition = repetition

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Delimiters(element='{self.element}', segment='{self.segment}', "
            f"sub_element='{self.sub_element}', repetition='{self.repetition}')"
        )

    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, Delimiters):
            return False
        return (
            self.element == other.element
            and self.segment == other.segment
            and self.sub_element == other.sub_element
            and self.repetition == other.repetition
        )

    def to_config(self) -> DelimitersConfig:
        """Convert to Pydantic config model.

        Returns:
            DelimitersConfig instance
        """
        return DelimitersConfig(
            element=self.element,
            segment=self.segment,
            sub_element=self.sub_element,
            repetition=self.repetition or "^",
        )

    @classmethod
    def from_config(cls, config: DelimitersConfig) -> "Delimiters":
        """Create from Pydantic config model.

        Args:
            config: DelimitersConfig instance

        Returns:
            Delimiters instance
        """
        return cls(
            element=config.element,
            segment=config.segment,
            sub_element=config.sub_element,
            repetition=config.repetition,
        )


class DelimiterDetector:
    """Auto-detect EDI delimiters from ISA segment."""

    # ISA segment structure positions
    ISA_PREFIX = "ISA"
    ISA_MIN_LENGTH = 106  # Minimum length for valid ISA segment
    ELEMENT_SEPARATOR_POSITION = 3  # Position of element separator
    SUB_ELEMENT_SEPARATOR_POSITION = 104  # Position of sub-element separator (ISA16)

    def __init__(self, default_delimiters: Optional[DelimitersConfig] = None) -> None:
        """Initialize delimiter detector.

        Args:
            default_delimiters: Default delimiters to use if detection fails
        """
        self.default_delimiters = default_delimiters or DelimitersConfig()
        logger.debug("delimiter_detector_initialized", defaults=str(self.default_delimiters))

    def detect_from_isa(self, isa_segment: str) -> Delimiters:
        """Detect delimiters from ISA segment.

        The ISA segment has a fixed structure:
        ISA*00*          *00*          *...   (element separator at position 3)
        ...>~                                  (sub-element at 104, segment at end)

        Args:
            isa_segment: ISA segment string

        Returns:
            Delimiters instance with detected separators

        Raises:
            InvalidISASegmentError: If ISA segment is invalid
            DelimiterDetectionError: If delimiters cannot be detected
        """
        # Validate ISA segment
        if not isa_segment:
            raise InvalidISASegmentError("ISA segment is empty")

        # Remove any leading/trailing whitespace
        isa_segment = isa_segment.strip()

        # Check if it starts with ISA
        if not isa_segment.startswith(self.ISA_PREFIX):
            raise InvalidISASegmentError(
                f"Segment does not start with 'ISA': {isa_segment[:20]}..."
            )

        # Check minimum length
        if len(isa_segment) < self.ISA_MIN_LENGTH:
            raise InvalidISASegmentError(
                f"ISA segment too short (length {len(isa_segment)}, "
                f"minimum {self.ISA_MIN_LENGTH})"
            )

        try:
            # Extract element separator (position 3)
            element_separator = isa_segment[self.ELEMENT_SEPARATOR_POSITION]

            # Extract segment terminator (last character)
            segment_terminator = isa_segment[-1]

            # Extract sub-element separator (position 105, ISA16)
            sub_element_separator = isa_segment[self.SUB_ELEMENT_SEPARATOR_POSITION]

            # Validate separators are different
            separators = [element_separator, segment_terminator, sub_element_separator]
            if len(set(separators)) != len(separators):
                raise DelimiterDetectionError(
                    f"Delimiters are not unique: element='{element_separator}', "
                    f"segment='{segment_terminator}', sub_element='{sub_element_separator}'"
                )

            # Repetition separator is optional and not always present in ISA
            # It's typically '^' but we'll default to None and let the parser handle it
            repetition_separator = None

            delimiters = Delimiters(
                element=element_separator,
                segment=segment_terminator,
                sub_element=sub_element_separator,
                repetition=repetition_separator,
            )

            logger.info(
                "delimiters_detected",
                element=element_separator,
                segment=segment_terminator,
                sub_element=sub_element_separator,
            )

            return delimiters

        except IndexError as e:
            raise DelimiterDetectionError(
                f"Failed to extract delimiters from ISA segment: {str(e)}"
            ) from e

    def detect_from_file_content(self, content: str) -> Delimiters:
        """Detect delimiters from raw EDI file content.

        Finds the ISA segment and extracts delimiters.

        Args:
            content: Raw EDI file content

        Returns:
            Delimiters instance

        Raises:
            InvalidISASegmentError: If ISA segment not found or invalid
            DelimiterDetectionError: If delimiters cannot be detected
        """
        if not content:
            raise InvalidISASegmentError("File content is empty")

        # Find ISA segment
        # ISA segment should be at the beginning or after whitespace
        content = content.strip()

        if not content.startswith(self.ISA_PREFIX):
            raise InvalidISASegmentError(
                f"File does not start with ISA segment: {content[:50]}..."
            )

        # Extract ISA segment (up to first segment terminator or newline)
        # We need to find the segment terminator, but we don't know it yet
        # So we'll try common terminators: ~, !, |
        common_terminators = ["~", "!", "|"]
        isa_segment = None

        for terminator in common_terminators:
            if terminator in content:
                isa_segment = content.split(terminator)[0] + terminator
                break

        if not isa_segment:
            # Try newline as terminator
            if "\n" in content:
                isa_segment = content.split("\n")[0]
            else:
                # Take first 106+ characters
                isa_segment = content[: self.ISA_MIN_LENGTH + 10]

        logger.debug("isa_segment_extracted", length=len(isa_segment))

        return self.detect_from_isa(isa_segment)

    def use_default_delimiters(self) -> Delimiters:
        """Return default delimiters.

        Returns:
            Delimiters instance with default values
        """
        logger.warning("using_default_delimiters")
        return Delimiters.from_config(self.default_delimiters)

    def validate_delimiters(self, delimiters: Delimiters) -> bool:
        """Validate that delimiters are unique and valid.

        Args:
            delimiters: Delimiters instance to validate

        Returns:
            True if valid, False otherwise
        """
        # Check all separators are single characters
        if not all(
            len(sep) == 1
            for sep in [
                delimiters.element,
                delimiters.segment,
                delimiters.sub_element,
            ]
        ):
            logger.error("delimiter_validation_failed", reason="Not single characters")
            return False

        # Check all separators are unique
        separators = [
            delimiters.element,
            delimiters.segment,
            delimiters.sub_element,
        ]
        if delimiters.repetition:
            separators.append(delimiters.repetition)

        if len(set(separators)) != len(separators):
            logger.error("delimiter_validation_failed", reason="Not unique")
            return False

        # Check separators are printable ASCII
        if not all(32 <= ord(sep) <= 126 for sep in separators):
            logger.error("delimiter_validation_failed", reason="Not printable ASCII")
            return False

        return True
