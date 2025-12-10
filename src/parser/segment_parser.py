"""Parse EDI segments into Pydantic models."""

from typing import Type, TypeVar, Union

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
from src.parser.element_parser import ElementParser
from src.parser.exceptions import TokenizationError
from src.utils.logger import get_logger
from src.utils.profiler import profile

logger = get_logger(__name__)

# Type variable for segment models
T = TypeVar("T")


class SegmentParser:
    """Parse EDI segments into Pydantic models."""

    def __init__(self, delimiters: Delimiters) -> None:
        """Initialize segment parser.

        Args:
            delimiters: Delimiters to use for parsing
        """
        self.delimiters = delimiters
        self.element_parser = ElementParser(delimiters)

    @profile(operation="parse_segment")
    def parse_segment(
        self, segment: str, segment_type: Type[T]
    ) -> T:
        """Parse a segment string into a Pydantic model.

        Args:
            segment: Raw segment string
            segment_type: Pydantic model class to parse into

        Returns:
            Parsed segment model instance

        Raises:
            TokenizationError: If parsing fails
        """
        elements = self.element_parser.split_segment(segment)

        # Map segment type to parser method
        parsers = {
            ISASegment: self._parse_isa,
            GSSegment: self._parse_gs,
            STSegment: self._parse_st,
            AK1Segment: self._parse_ak1,
            AK2Segment: self._parse_ak2,
            AK3Segment: self._parse_ak3,
            AK4Segment: self._parse_ak4,
            AK5Segment: self._parse_ak5,
            AK9Segment: self._parse_ak9,
            SESegment: self._parse_se,
            GESegment: self._parse_ge,
            IEASegment: self._parse_iea,
        }

        parser_func = parsers.get(segment_type)
        if not parser_func:
            raise TokenizationError(f"No parser available for segment type: {segment_type}")

        try:
            return parser_func(elements)
        except Exception as e:
            logger.error(
                "segment_parse_failed",
                segment_type=segment_type.__name__,
                segment=segment[:100],
                error=str(e),
            )
            raise TokenizationError(
                f"Failed to parse {segment_type.__name__}: {str(e)}"
            ) from e

    def _parse_isa(self, elements: list[str]) -> ISASegment:
        """Parse ISA segment."""
        return ISASegment(
            authorization_info_qualifier=self.element_parser.get_element(elements, 1),
            authorization_info=self.element_parser.get_element(elements, 2),
            security_info_qualifier=self.element_parser.get_element(elements, 3),
            security_info=self.element_parser.get_element(elements, 4),
            interchange_sender_qualifier=self.element_parser.get_element(elements, 5),
            interchange_sender_id=self.element_parser.get_element(elements, 6),
            interchange_receiver_qualifier=self.element_parser.get_element(elements, 7),
            interchange_receiver_id=self.element_parser.get_element(elements, 8),
            interchange_date=self.element_parser.get_element(elements, 9),
            interchange_time=self.element_parser.get_element(elements, 10),
            interchange_control_standards_id=self.element_parser.get_element(elements, 11),
            interchange_control_version_number=self.element_parser.get_element(elements, 12),
            interchange_control_number=self.element_parser.get_element(elements, 13),
            acknowledgment_requested=self.element_parser.get_element(elements, 14),
            test_indicator=self.element_parser.get_element(elements, 15),
            sub_element_separator=self.element_parser.get_element(elements, 16),
        )

    def _parse_gs(self, elements: list[str]) -> GSSegment:
        """Parse GS segment."""
        return GSSegment(
            functional_id_code=self.element_parser.get_element(elements, 1),
            application_sender_code=self.element_parser.get_element(elements, 2),
            application_receiver_code=self.element_parser.get_element(elements, 3),
            date=self.element_parser.get_element(elements, 4),
            time=self.element_parser.get_element(elements, 5),
            group_control_number=self.element_parser.get_element(elements, 6),
            responsible_agency_code=self.element_parser.get_element(elements, 7),
            version_release_industry_id=self.element_parser.get_element(elements, 8),
        )

    def _parse_st(self, elements: list[str]) -> STSegment:
        """Parse ST segment."""
        return STSegment(
            transaction_set_id=self.element_parser.get_element(elements, 1),
            transaction_set_control_number=self.element_parser.get_element(elements, 2),
            implementation_convention_reference=self.element_parser.get_element(
                elements, 3, required=False
            ),
        )

    def _parse_ak1(self, elements: list[str]) -> AK1Segment:
        """Parse AK1 segment."""
        return AK1Segment(
            functional_id_code=self.element_parser.get_element(elements, 1),
            group_control_number=self.element_parser.get_element(elements, 2),
            version_release_industry_id=self.element_parser.get_element(
                elements, 3, required=False
            ),
        )

    def _parse_ak2(self, elements: list[str]) -> AK2Segment:
        """Parse AK2 segment."""
        return AK2Segment(
            transaction_set_id=self.element_parser.get_element(elements, 1),
            transaction_set_control_number=self.element_parser.get_element(elements, 2),
            implementation_convention_reference=self.element_parser.get_element(
                elements, 3, required=False
            ),
        )

    def _parse_ak3(self, elements: list[str]) -> AK3Segment:
        """Parse AK3 segment."""
        return AK3Segment(
            segment_id=self.element_parser.get_element(elements, 1),
            segment_position_in_transaction_set=self.element_parser.get_element_as_int(
                elements, 2
            ),
            loop_identifier_code=self.element_parser.get_element(elements, 3, required=False),
            segment_syntax_error_code=self.element_parser.get_element(
                elements, 4, required=False
            ),
        )

    def _parse_ak4(self, elements: list[str]) -> AK4Segment:
        """Parse AK4 segment."""
        return AK4Segment(
            element_position_in_segment=self.element_parser.get_element_as_int(elements, 1),
            data_element_reference_number=self.element_parser.get_element_as_int(
                elements, 2, required=False
            ),
            data_element_syntax_error_code=self.element_parser.get_element(elements, 3),
            copy_of_bad_data_element=self.element_parser.get_element(
                elements, 4, required=False
            ),
        )

    def _parse_ak5(self, elements: list[str]) -> AK5Segment:
        """Parse AK5 segment."""
        return AK5Segment(
            transaction_set_ack_code=self.element_parser.get_element(elements, 1),
            transaction_set_syntax_error_code_1=self.element_parser.get_element(
                elements, 2, required=False
            ),
            transaction_set_syntax_error_code_2=self.element_parser.get_element(
                elements, 3, required=False
            ),
            transaction_set_syntax_error_code_3=self.element_parser.get_element(
                elements, 4, required=False
            ),
            transaction_set_syntax_error_code_4=self.element_parser.get_element(
                elements, 5, required=False
            ),
            transaction_set_syntax_error_code_5=self.element_parser.get_element(
                elements, 6, required=False
            ),
        )

    def _parse_ak9(self, elements: list[str]) -> AK9Segment:
        """Parse AK9 segment."""
        return AK9Segment(
            functional_group_ack_code=self.element_parser.get_element(elements, 1),
            number_of_transaction_sets_included=self.element_parser.get_element_as_int(
                elements, 2
            ),
            number_of_received_transaction_sets=self.element_parser.get_element_as_int(
                elements, 3
            ),
            number_of_accepted_transaction_sets=self.element_parser.get_element_as_int(
                elements, 4
            ),
            functional_group_syntax_error_code_1=self.element_parser.get_element(
                elements, 5, required=False
            ),
            functional_group_syntax_error_code_2=self.element_parser.get_element(
                elements, 6, required=False
            ),
            functional_group_syntax_error_code_3=self.element_parser.get_element(
                elements, 7, required=False
            ),
            functional_group_syntax_error_code_4=self.element_parser.get_element(
                elements, 8, required=False
            ),
            functional_group_syntax_error_code_5=self.element_parser.get_element(
                elements, 9, required=False
            ),
        )

    def _parse_se(self, elements: list[str]) -> SESegment:
        """Parse SE segment."""
        return SESegment(
            number_of_included_segments=self.element_parser.get_element_as_int(elements, 1),
            transaction_set_control_number=self.element_parser.get_element(elements, 2),
        )

    def _parse_ge(self, elements: list[str]) -> GESegment:
        """Parse GE segment."""
        return GESegment(
            number_of_transaction_sets=self.element_parser.get_element_as_int(elements, 1),
            group_control_number=self.element_parser.get_element(elements, 2),
        )

    def _parse_iea(self, elements: list[str]) -> IEASegment:
        """Parse IEA segment."""
        return IEASegment(
            number_of_included_groups=self.element_parser.get_element_as_int(elements, 1),
            interchange_control_number=self.element_parser.get_element(elements, 2),
        )

    def parse_segment_by_id(self, segment: str) -> Union[
        ISASegment,
        GSSegment,
        STSegment,
        AK1Segment,
        AK2Segment,
        AK3Segment,
        AK4Segment,
        AK5Segment,
        AK9Segment,
        SESegment,
        GESegment,
        IEASegment,
    ]:
        """Parse segment automatically based on segment ID.

        Args:
            segment: Raw segment string

        Returns:
            Parsed segment model

        Raises:
            TokenizationError: If segment ID is unknown or parsing fails
        """
        segment_id = self.element_parser.parse_segment_id(segment)

        segment_type_map = {
            "ISA": ISASegment,
            "GS": GSSegment,
            "ST": STSegment,
            "AK1": AK1Segment,
            "AK2": AK2Segment,
            "AK3": AK3Segment,
            "AK4": AK4Segment,
            "AK5": AK5Segment,
            "AK9": AK9Segment,
            "SE": SESegment,
            "GE": GESegment,
            "IEA": IEASegment,
        }

        segment_type = segment_type_map.get(segment_id)
        if not segment_type:
            raise TokenizationError(f"Unknown segment ID: {segment_id}")

        return self.parse_segment(segment, segment_type)
