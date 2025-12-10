"""Unit tests for ErrorCodeMapper."""

import pytest

from src.utils.error_code_mapper import ErrorCodeInfo, ErrorCodeMapper


def test_error_code_info_creation() -> None:
    """Test ErrorCodeInfo initialization."""
    info = ErrorCodeInfo(
        code="1",
        description="Test error",
        severity="error",
        classification="rejected",
    )

    assert info.code == "1"
    assert info.description == "Test error"
    assert info.severity == "error"
    assert info.classification == "rejected"


def test_error_code_info_repr() -> None:
    """Test ErrorCodeInfo string representation."""
    info = ErrorCodeInfo(code="1", description="Test", severity="error")
    repr_str = repr(info)

    assert "ErrorCodeInfo" in repr_str
    assert "code='1'" in repr_str
    assert "severity='error'" in repr_str


def test_error_code_info_to_dict() -> None:
    """Test ErrorCodeInfo to dictionary conversion."""
    info = ErrorCodeInfo(
        code="A",
        description="Accepted",
        severity="success",
        classification="accepted",
    )

    info_dict = info.to_dict()

    assert info_dict["code"] == "A"
    assert info_dict["description"] == "Accepted"
    assert info_dict["severity"] == "success"
    assert info_dict["classification"] == "accepted"


def test_error_code_info_to_dict_no_classification() -> None:
    """Test ErrorCodeInfo to dict without classification."""
    info = ErrorCodeInfo(code="1", description="Test", severity="error")

    info_dict = info.to_dict()

    assert "code" in info_dict
    assert "description" in info_dict
    assert "severity" in info_dict
    assert "classification" not in info_dict


def test_get_segment_error_valid(error_code_mapper: ErrorCodeMapper) -> None:
    """Test getting valid segment error."""
    error_info = error_code_mapper.get_segment_error("1")

    assert error_info.code == "1"
    assert "Unrecognized segment ID" in error_info.description
    assert error_info.severity == "error"


def test_get_segment_error_invalid(error_code_mapper: ErrorCodeMapper) -> None:
    """Test getting invalid segment error code."""
    error_info = error_code_mapper.get_segment_error("999")

    assert error_info.code == "999"
    assert "Unknown" in error_info.description
    assert error_info.severity == "error"


def test_get_element_error_valid(error_code_mapper: ErrorCodeMapper) -> None:
    """Test getting valid element error."""
    error_info = error_code_mapper.get_element_error("1")

    assert error_info.code == "1"
    assert "Mandatory data element missing" in error_info.description
    assert error_info.severity == "error"


def test_get_element_error_invalid(error_code_mapper: ErrorCodeMapper) -> None:
    """Test getting invalid element error code."""
    error_info = error_code_mapper.get_element_error("999")

    assert error_info.code == "999"
    assert "Unknown" in error_info.description
    assert error_info.severity == "error"


def test_get_functional_group_ack_accepted(error_code_mapper: ErrorCodeMapper) -> None:
    """Test getting functional group acknowledgment for accepted."""
    ack_info = error_code_mapper.get_functional_group_ack("A")

    assert ack_info.code == "A"
    assert "Accepted" in ack_info.description
    assert ack_info.severity == "success"
    assert ack_info.classification == "accepted"


def test_get_functional_group_ack_rejected(error_code_mapper: ErrorCodeMapper) -> None:
    """Test getting functional group acknowledgment for rejected."""
    ack_info = error_code_mapper.get_functional_group_ack("R")

    assert ack_info.code == "R"
    assert "Rejected" in ack_info.description
    assert ack_info.severity == "error"
    assert ack_info.classification == "rejected"


def test_get_functional_group_ack_invalid(error_code_mapper: ErrorCodeMapper) -> None:
    """Test getting invalid functional group ack code."""
    ack_info = error_code_mapper.get_functional_group_ack("Z")

    assert ack_info.code == "Z"
    assert "Unknown" in ack_info.description
    assert ack_info.classification == "unknown"


def test_get_transaction_set_ack_accepted(error_code_mapper: ErrorCodeMapper) -> None:
    """Test getting transaction set acknowledgment for accepted."""
    ack_info = error_code_mapper.get_transaction_set_ack("A")

    assert ack_info.code == "A"
    assert "Accepted" in ack_info.description
    assert ack_info.severity == "success"
    assert ack_info.classification == "accepted"


def test_get_transaction_set_ack_partial(error_code_mapper: ErrorCodeMapper) -> None:
    """Test getting transaction set acknowledgment for partial."""
    ack_info = error_code_mapper.get_transaction_set_ack("E")

    assert ack_info.code == "E"
    assert "errors noted" in ack_info.description
    assert ack_info.severity == "warning"
    assert ack_info.classification == "partial"


def test_get_transaction_set_ack_rejected(error_code_mapper: ErrorCodeMapper) -> None:
    """Test getting transaction set acknowledgment for rejected."""
    ack_info = error_code_mapper.get_transaction_set_ack("R")

    assert ack_info.code == "R"
    assert "Rejected" in ack_info.description
    assert ack_info.severity == "error"
    assert ack_info.classification == "rejected"


def test_get_custom_error_valid(error_code_mapper: ErrorCodeMapper) -> None:
    """Test getting valid custom error."""
    error_info = error_code_mapper.get_custom_error("PARSE_ERROR")

    assert error_info.code == "PARSE_ERROR"
    assert "parse" in error_info.description.lower()
    assert error_info.severity == "error"


def test_get_custom_error_invalid(error_code_mapper: ErrorCodeMapper) -> None:
    """Test getting invalid custom error code."""
    error_info = error_code_mapper.get_custom_error("INVALID_CODE")

    assert error_info.code == "INVALID_CODE"
    assert "Unknown" in error_info.description


def test_is_accepted_code(error_code_mapper: ErrorCodeMapper) -> None:
    """Test checking if code indicates acceptance."""
    assert error_code_mapper.is_accepted_code("A") is True
    assert error_code_mapper.is_accepted_code("R") is False
    assert error_code_mapper.is_accepted_code("E") is False


def test_is_rejected_code(error_code_mapper: ErrorCodeMapper) -> None:
    """Test checking if code indicates rejection."""
    assert error_code_mapper.is_rejected_code("R") is True
    assert error_code_mapper.is_rejected_code("A") is False
    assert error_code_mapper.is_rejected_code("E") is False


def test_is_partial_code(error_code_mapper: ErrorCodeMapper) -> None:
    """Test checking if code indicates partial acceptance."""
    assert error_code_mapper.is_partial_code("E") is True
    assert error_code_mapper.is_partial_code("A") is False
    assert error_code_mapper.is_partial_code("R") is False


def test_get_all_segment_errors(error_code_mapper: ErrorCodeMapper) -> None:
    """Test getting all segment errors."""
    all_errors = error_code_mapper.get_all_segment_errors()

    assert isinstance(all_errors, dict)
    assert len(all_errors) > 0
    assert "1" in all_errors
    assert isinstance(all_errors["1"], ErrorCodeInfo)


def test_get_all_element_errors(error_code_mapper: ErrorCodeMapper) -> None:
    """Test getting all element errors."""
    all_errors = error_code_mapper.get_all_element_errors()

    assert isinstance(all_errors, dict)
    assert len(all_errors) > 0
    assert "1" in all_errors
    assert isinstance(all_errors["1"], ErrorCodeInfo)


def test_get_severity_level(error_code_mapper: ErrorCodeMapper) -> None:
    """Test getting numeric severity levels."""
    assert error_code_mapper.get_severity_level("critical") > error_code_mapper.get_severity_level(
        "error"
    )
    assert error_code_mapper.get_severity_level("error") > error_code_mapper.get_severity_level(
        "warning"
    )
    assert error_code_mapper.get_severity_level("warning") > error_code_mapper.get_severity_level(
        "info"
    )
    assert error_code_mapper.get_severity_level("info") > error_code_mapper.get_severity_level(
        "success"
    )


def test_get_severity_level_unknown(error_code_mapper: ErrorCodeMapper) -> None:
    """Test getting severity level for unknown severity."""
    level = error_code_mapper.get_severity_level("unknown")
    assert level == 0
