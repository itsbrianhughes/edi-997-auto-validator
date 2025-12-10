"""Pydantic models for EDI 997 segments."""

from datetime import date, time
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ISASegment(BaseModel):
    """ISA - Interchange Control Header."""

    authorization_info_qualifier: str = Field(..., min_length=2, max_length=2)
    authorization_info: str = Field(..., max_length=10)
    security_info_qualifier: str = Field(..., min_length=2, max_length=2)
    security_info: str = Field(..., max_length=10)
    interchange_sender_qualifier: str = Field(..., min_length=2, max_length=2)
    interchange_sender_id: str = Field(..., max_length=15)
    interchange_receiver_qualifier: str = Field(..., min_length=2, max_length=2)
    interchange_receiver_id: str = Field(..., max_length=15)
    interchange_date: str = Field(..., min_length=6, max_length=6)  # YYMMDD
    interchange_time: str = Field(..., min_length=4, max_length=4)  # HHMM
    interchange_control_standards_id: str = Field(..., min_length=1, max_length=1)
    interchange_control_version_number: str = Field(..., min_length=5, max_length=5)
    interchange_control_number: str = Field(..., min_length=9, max_length=9)
    acknowledgment_requested: str = Field(..., min_length=1, max_length=1)
    test_indicator: str = Field(..., min_length=1, max_length=1)
    sub_element_separator: str = Field(..., min_length=1, max_length=1)

    class Config:
        """Pydantic configuration."""

        str_strip_whitespace = True


class GSSegment(BaseModel):
    """GS - Functional Group Header."""

    functional_id_code: str = Field(..., min_length=2, max_length=2)
    application_sender_code: str = Field(..., max_length=15)
    application_receiver_code: str = Field(..., max_length=15)
    date: str = Field(..., min_length=8, max_length=8)  # CCYYMMDD
    time: str = Field(..., min_length=4, max_length=8)  # HHMM or HHMMSS
    group_control_number: str = Field(..., min_length=1, max_length=9)
    responsible_agency_code: str = Field(..., min_length=1, max_length=2)
    version_release_industry_id: str = Field(..., max_length=12)

    class Config:
        """Pydantic configuration."""

        str_strip_whitespace = True


class STSegment(BaseModel):
    """ST - Transaction Set Header."""

    transaction_set_id: str = Field(..., min_length=3, max_length=3)
    transaction_set_control_number: str = Field(..., min_length=4, max_length=9)
    implementation_convention_reference: Optional[str] = Field(default=None, max_length=35)

    class Config:
        """Pydantic configuration."""

        str_strip_whitespace = True


class AK1Segment(BaseModel):
    """AK1 - Functional Group Response Header."""

    functional_id_code: str = Field(..., min_length=2, max_length=2)
    group_control_number: str = Field(..., min_length=1, max_length=9)
    version_release_industry_id: Optional[str] = Field(default=None, max_length=12)

    class Config:
        """Pydantic configuration."""

        str_strip_whitespace = True


class AK2Segment(BaseModel):
    """AK2 - Transaction Set Response Header."""

    transaction_set_id: str = Field(..., min_length=3, max_length=3)
    transaction_set_control_number: str = Field(..., min_length=4, max_length=9)
    implementation_convention_reference: Optional[str] = Field(default=None, max_length=35)

    class Config:
        """Pydantic configuration."""

        str_strip_whitespace = True


class AK3Segment(BaseModel):
    """AK3 - Data Segment Note."""

    segment_id: str = Field(..., min_length=2, max_length=3)
    segment_position_in_transaction_set: int = Field(..., ge=1)
    loop_identifier_code: Optional[str] = Field(default=None, max_length=6)
    segment_syntax_error_code: Optional[str] = Field(default=None, min_length=1, max_length=3)

    class Config:
        """Pydantic configuration."""

        str_strip_whitespace = True

    @field_validator("segment_position_in_transaction_set", mode="before")
    @classmethod
    def parse_position(cls, v: any) -> int:
        """Parse position as integer."""
        if isinstance(v, str):
            return int(v)
        return v


class AK4Segment(BaseModel):
    """AK4 - Data Element Note."""

    element_position_in_segment: int = Field(..., ge=1)
    data_element_reference_number: Optional[int] = Field(default=None, ge=1)
    data_element_syntax_error_code: str = Field(..., min_length=1, max_length=3)
    copy_of_bad_data_element: Optional[str] = Field(default=None, max_length=99)

    class Config:
        """Pydantic configuration."""

        str_strip_whitespace = True

    @field_validator("element_position_in_segment", "data_element_reference_number", mode="before")
    @classmethod
    def parse_int_fields(cls, v: any) -> Optional[int]:
        """Parse integer fields."""
        if v is None or v == "":
            return None
        if isinstance(v, str):
            return int(v)
        return v


class AK5Segment(BaseModel):
    """AK5 - Transaction Set Response Trailer."""

    transaction_set_ack_code: str = Field(..., min_length=1, max_length=1)
    transaction_set_syntax_error_code_1: Optional[str] = Field(
        default=None, min_length=1, max_length=3
    )
    transaction_set_syntax_error_code_2: Optional[str] = Field(
        default=None, min_length=1, max_length=3
    )
    transaction_set_syntax_error_code_3: Optional[str] = Field(
        default=None, min_length=1, max_length=3
    )
    transaction_set_syntax_error_code_4: Optional[str] = Field(
        default=None, min_length=1, max_length=3
    )
    transaction_set_syntax_error_code_5: Optional[str] = Field(
        default=None, min_length=1, max_length=3
    )

    class Config:
        """Pydantic configuration."""

        str_strip_whitespace = True

    def get_error_codes(self) -> list[str]:
        """Get all non-None error codes.

        Returns:
            List of error codes
        """
        codes = [
            self.transaction_set_syntax_error_code_1,
            self.transaction_set_syntax_error_code_2,
            self.transaction_set_syntax_error_code_3,
            self.transaction_set_syntax_error_code_4,
            self.transaction_set_syntax_error_code_5,
        ]
        return [code for code in codes if code is not None]


class AK9Segment(BaseModel):
    """AK9 - Functional Group Response Trailer."""

    functional_group_ack_code: str = Field(..., min_length=1, max_length=1)
    number_of_transaction_sets_included: int = Field(..., ge=0)
    number_of_received_transaction_sets: int = Field(..., ge=0)
    number_of_accepted_transaction_sets: int = Field(..., ge=0)
    functional_group_syntax_error_code_1: Optional[str] = Field(
        default=None, min_length=1, max_length=3
    )
    functional_group_syntax_error_code_2: Optional[str] = Field(
        default=None, min_length=1, max_length=3
    )
    functional_group_syntax_error_code_3: Optional[str] = Field(
        default=None, min_length=1, max_length=3
    )
    functional_group_syntax_error_code_4: Optional[str] = Field(
        default=None, min_length=1, max_length=3
    )
    functional_group_syntax_error_code_5: Optional[str] = Field(
        default=None, min_length=1, max_length=3
    )

    class Config:
        """Pydantic configuration."""

        str_strip_whitespace = True

    @field_validator(
        "number_of_transaction_sets_included",
        "number_of_received_transaction_sets",
        "number_of_accepted_transaction_sets",
        mode="before",
    )
    @classmethod
    def parse_count_fields(cls, v: any) -> int:
        """Parse count fields as integers."""
        if isinstance(v, str):
            return int(v)
        return v

    def get_error_codes(self) -> list[str]:
        """Get all non-None error codes.

        Returns:
            List of error codes
        """
        codes = [
            self.functional_group_syntax_error_code_1,
            self.functional_group_syntax_error_code_2,
            self.functional_group_syntax_error_code_3,
            self.functional_group_syntax_error_code_4,
            self.functional_group_syntax_error_code_5,
        ]
        return [code for code in codes if code is not None]


class SESegment(BaseModel):
    """SE - Transaction Set Trailer."""

    number_of_included_segments: int = Field(..., ge=1)
    transaction_set_control_number: str = Field(..., min_length=4, max_length=9)

    class Config:
        """Pydantic configuration."""

        str_strip_whitespace = True

    @field_validator("number_of_included_segments", mode="before")
    @classmethod
    def parse_segment_count(cls, v: any) -> int:
        """Parse segment count as integer."""
        if isinstance(v, str):
            return int(v)
        return v


class GESegment(BaseModel):
    """GE - Functional Group Trailer."""

    number_of_transaction_sets: int = Field(..., ge=1)
    group_control_number: str = Field(..., min_length=1, max_length=9)

    class Config:
        """Pydantic configuration."""

        str_strip_whitespace = True

    @field_validator("number_of_transaction_sets", mode="before")
    @classmethod
    def parse_transaction_set_count(cls, v: any) -> int:
        """Parse transaction set count as integer."""
        if isinstance(v, str):
            return int(v)
        return v


class IEASegment(BaseModel):
    """IEA - Interchange Control Trailer."""

    number_of_included_groups: int = Field(..., ge=1)
    interchange_control_number: str = Field(..., min_length=9, max_length=9)

    class Config:
        """Pydantic configuration."""

        str_strip_whitespace = True

    @field_validator("number_of_included_groups", mode="before")
    @classmethod
    def parse_group_count(cls, v: any) -> int:
        """Parse group count as integer."""
        if isinstance(v, str):
            return int(v)
        return v
