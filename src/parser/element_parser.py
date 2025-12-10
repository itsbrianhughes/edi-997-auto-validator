"""Element parsing utilities for EDI segments."""

from typing import Any, Optional

from src.parser.delimiter_detector import Delimiters
from src.parser.exceptions import TokenizationError
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ElementParser:
    """Parse individual elements from EDI segments."""

    def __init__(self, delimiters: Delimiters) -> None:
        """Initialize element parser.

        Args:
            delimiters: Delimiters to use for parsing
        """
        self.delimiters = delimiters

    def split_segment(self, segment: str) -> list[str]:
        """Split a segment into elements.

        Args:
            segment: Raw segment string

        Returns:
            List of element strings

        Example:
            >>> parser = ElementParser(delimiters)
            >>> parser.split_segment("ST*997*0001")
            ['ST', '997', '0001']
        """
        if not segment:
            return []

        elements = segment.split(self.delimiters.element)
        return elements

    def get_element(
        self,
        elements: list[str],
        position: int,
        required: bool = True,
        default: Optional[str] = None,
    ) -> Optional[str]:
        """Get an element at a specific position.

        Args:
            elements: List of elements
            position: Element position (0-indexed)
            required: Whether element is required
            default: Default value if element missing

        Returns:
            Element value or None

        Raises:
            TokenizationError: If required element is missing
        """
        if position >= len(elements):
            if required:
                raise TokenizationError(
                    f"Required element at position {position} is missing. "
                    f"Segment has {len(elements)} elements"
                )
            return default

        # Get the element value (don't strip yet - let Pydantic handle it)
        value = elements[position] if elements[position] else ""

        # Only check for truly missing elements, not whitespace-only ones
        # (some EDI fields like ISA authorization_info can be all spaces)
        if value == "" and required:
            raise TokenizationError(f"Required element at position {position} is empty")

        return value if value else default

    def get_element_as_int(
        self,
        elements: list[str],
        position: int,
        required: bool = True,
        default: Optional[int] = None,
    ) -> Optional[int]:
        """Get an element as an integer.

        Args:
            elements: List of elements
            position: Element position (0-indexed)
            required: Whether element is required
            default: Default value if element missing

        Returns:
            Integer value or None

        Raises:
            TokenizationError: If required element is missing or invalid
        """
        value = self.get_element(elements, position, required, None)

        if value is None:
            return default

        try:
            return int(value)
        except ValueError as e:
            raise TokenizationError(
                f"Element at position {position} ('{value}') is not a valid integer"
            ) from e

    def parse_segment_id(self, segment: str) -> str:
        """Extract segment ID from segment string.

        Args:
            segment: Raw segment string

        Returns:
            Segment ID (e.g., 'ISA', 'GS', 'ST', 'AK1')

        Raises:
            TokenizationError: If segment ID cannot be extracted
        """
        elements = self.split_segment(segment)
        if not elements:
            raise TokenizationError("Cannot extract segment ID from empty segment")

        segment_id = elements[0].strip()
        if not segment_id:
            raise TokenizationError("Segment ID is empty")

        return segment_id

    def validate_segment_id(self, segment: str, expected_id: str) -> None:
        """Validate that segment has expected ID.

        Args:
            segment: Raw segment string
            expected_id: Expected segment ID

        Raises:
            TokenizationError: If segment ID doesn't match
        """
        actual_id = self.parse_segment_id(segment)
        if actual_id != expected_id:
            raise TokenizationError(
                f"Expected segment ID '{expected_id}' but got '{actual_id}'"
            )

    def get_element_count(self, segment: str) -> int:
        """Get the number of elements in a segment.

        Args:
            segment: Raw segment string

        Returns:
            Number of elements
        """
        return len(self.split_segment(segment))

    def split_composite_element(self, element: str) -> list[str]:
        """Split a composite element into sub-elements.

        Args:
            element: Composite element string

        Returns:
            List of sub-elements

        Example:
            >>> parser.split_composite_element("C040:020")
            ['C040', '020']
        """
        if not element or self.delimiters.sub_element not in element:
            return [element] if element else []

        return element.split(self.delimiters.sub_element)

    def split_repeating_element(self, element: str) -> list[str]:
        """Split a repeating element into repetitions.

        Args:
            element: Repeating element string

        Returns:
            List of repetitions

        Example:
            >>> parser.split_repeating_element("A^B^C")
            ['A', 'B', 'C']
        """
        if not element or not self.delimiters.repetition:
            return [element] if element else []

        if self.delimiters.repetition not in element:
            return [element]

        return element.split(self.delimiters.repetition)

    def parse_segment_to_dict(self, segment: str) -> dict[str, Any]:
        """Parse segment into a dictionary with segment ID and elements.

        Args:
            segment: Raw segment string

        Returns:
            Dictionary with 'segment_id' and 'elements' keys

        Example:
            >>> parser.parse_segment_to_dict("ST*997*0001")
            {'segment_id': 'ST', 'elements': ['ST', '997', '0001']}
        """
        elements = self.split_segment(segment)
        segment_id = elements[0] if elements else ""

        return {
            "segment_id": segment_id,
            "elements": elements,
        }
