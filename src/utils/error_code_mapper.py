"""X12 997 error code lookup and mapping."""

from typing import Any, Dict, Optional

from src.utils.config_loader import ConfigLoader


class ErrorCodeInfo:
    """Container for error code information."""

    def __init__(
        self,
        code: str,
        description: str,
        severity: str = "error",
        classification: Optional[str] = None,
    ) -> None:
        """Initialize error code info.

        Args:
            code: Error code (e.g., '1', 'A', 'R')
            description: Human-readable description
            severity: Error severity (error, warning, info, success)
            classification: Classification (accepted, partial, rejected)
        """
        self.code = code
        self.description = description
        self.severity = severity
        self.classification = classification

    def __repr__(self) -> str:
        """String representation."""
        return f"ErrorCodeInfo(code='{self.code}', severity='{self.severity}')"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "code": self.code,
            "description": self.description,
            "severity": self.severity,
        }
        if self.classification:
            result["classification"] = self.classification
        return result


class ErrorCodeMapper:
    """Map X12 997 error codes to human-readable descriptions."""

    def __init__(self, config_loader: Optional[ConfigLoader] = None) -> None:
        """Initialize error code mapper.

        Args:
            config_loader: Optional ConfigLoader instance. If not provided, creates default.
        """
        self.config_loader = config_loader or ConfigLoader()
        self._error_codes = self.config_loader.load_error_codes()
        self._ak_codes = self._error_codes.get("ak_error_codes", {})

    def get_segment_error(self, code: str) -> ErrorCodeInfo:
        """Get segment syntax error information (AK403).

        Args:
            code: Error code (1-8)

        Returns:
            ErrorCodeInfo instance

        Example:
            >>> mapper.get_segment_error("3")
            ErrorCodeInfo(code='3', description='Required segment missing')
        """
        segment_errors = self._ak_codes.get("segment_syntax_errors", {})
        error_data = segment_errors.get(code, {})

        if not error_data:
            return ErrorCodeInfo(
                code=code,
                description=f"Unknown segment syntax error: {code}",
                severity="error",
            )

        return ErrorCodeInfo(
            code=error_data.get("code", code),
            description=error_data.get("description", "Unknown error"),
            severity=error_data.get("severity", "error"),
        )

    def get_element_error(self, code: str) -> ErrorCodeInfo:
        """Get data element syntax error information (AK503).

        Args:
            code: Error code (1-13)

        Returns:
            ErrorCodeInfo instance

        Example:
            >>> mapper.get_element_error("1")
            ErrorCodeInfo(code='1', description='Mandatory data element missing')
        """
        element_errors = self._ak_codes.get("element_syntax_errors", {})
        error_data = element_errors.get(code, {})

        if not error_data:
            return ErrorCodeInfo(
                code=code,
                description=f"Unknown element syntax error: {code}",
                severity="error",
            )

        return ErrorCodeInfo(
            code=error_data.get("code", code),
            description=error_data.get("description", "Unknown error"),
            severity=error_data.get("severity", "error"),
        )

    def get_functional_group_ack(self, code: str) -> ErrorCodeInfo:
        """Get functional group acknowledgment code information (AK901).

        Args:
            code: Acknowledgment code (A, E, M, P, R, W, X)

        Returns:
            ErrorCodeInfo instance with classification

        Example:
            >>> mapper.get_functional_group_ack("A")
            ErrorCodeInfo(code='A', description='Accepted', classification='accepted')
        """
        fg_ack_codes = self._ak_codes.get("functional_group_ack_codes", {})
        ack_data = fg_ack_codes.get(code, {})

        if not ack_data:
            return ErrorCodeInfo(
                code=code,
                description=f"Unknown functional group ack code: {code}",
                severity="error",
                classification="unknown",
            )

        return ErrorCodeInfo(
            code=ack_data.get("code", code),
            description=ack_data.get("description", "Unknown"),
            severity=ack_data.get("severity", "error"),
            classification=ack_data.get("classification"),
        )

    def get_transaction_set_error(self, code: str) -> ErrorCodeInfo:
        """Get transaction set syntax error information (AK502-AK506).

        Args:
            code: Error code (1-7)

        Returns:
            ErrorCodeInfo instance

        Example:
            >>> mapper.get_transaction_set_error("5")
            ErrorCodeInfo(code='5', description='One or more segments in error')
        """
        ts_errors = self._ak_codes.get("transaction_set_syntax_errors", {})
        error_data = ts_errors.get(code, {})

        if not error_data:
            return ErrorCodeInfo(
                code=code,
                description=f"Unknown transaction set syntax error: {code}",
                severity="error",
            )

        return ErrorCodeInfo(
            code=error_data.get("code", code),
            description=error_data.get("description", "Unknown error"),
            severity=error_data.get("severity", "error"),
        )

    def get_transaction_set_ack(self, code: str) -> ErrorCodeInfo:
        """Get transaction set acknowledgment code information (AK501).

        Args:
            code: Acknowledgment code (A, E, M, P, R, W, X)

        Returns:
            ErrorCodeInfo instance with classification

        Example:
            >>> mapper.get_transaction_set_ack("R")
            ErrorCodeInfo(code='R', description='Rejected', classification='rejected')
        """
        ts_ack_codes = self._ak_codes.get("transaction_set_ack_codes", {})
        ack_data = ts_ack_codes.get(code, {})

        if not ack_data:
            return ErrorCodeInfo(
                code=code,
                description=f"Unknown transaction set ack code: {code}",
                severity="error",
                classification="unknown",
            )

        return ErrorCodeInfo(
            code=ack_data.get("code", code),
            description=ack_data.get("description", "Unknown"),
            severity=ack_data.get("severity", "error"),
            classification=ack_data.get("classification"),
        )

    def get_custom_error(self, code: str) -> ErrorCodeInfo:
        """Get custom error code information.

        Args:
            code: Custom error code (e.g., 'PARSE_ERROR')

        Returns:
            ErrorCodeInfo instance
        """
        custom_errors = self._ak_codes.get("custom_errors", {})
        error_data = custom_errors.get(code, {})

        if not error_data:
            return ErrorCodeInfo(
                code=code,
                description=f"Unknown custom error: {code}",
                severity="error",
            )

        return ErrorCodeInfo(
            code=error_data.get("code", code),
            description=error_data.get("description", "Unknown error"),
            severity=error_data.get("severity", "error"),
        )

    def is_accepted_code(self, code: str) -> bool:
        """Check if acknowledgment code indicates acceptance.

        Args:
            code: Acknowledgment code

        Returns:
            True if code indicates acceptance
        """
        ack_info = self.get_transaction_set_ack(code)
        return ack_info.classification == "accepted"

    def is_rejected_code(self, code: str) -> bool:
        """Check if acknowledgment code indicates rejection.

        Args:
            code: Acknowledgment code

        Returns:
            True if code indicates rejection
        """
        ack_info = self.get_transaction_set_ack(code)
        return ack_info.classification == "rejected"

    def is_partial_code(self, code: str) -> bool:
        """Check if acknowledgment code indicates partial acceptance.

        Args:
            code: Acknowledgment code

        Returns:
            True if code indicates partial acceptance
        """
        ack_info = self.get_transaction_set_ack(code)
        return ack_info.classification == "partial"

    def get_all_segment_errors(self) -> Dict[str, ErrorCodeInfo]:
        """Get all segment syntax error codes.

        Returns:
            Dictionary mapping codes to ErrorCodeInfo instances
        """
        segment_errors = self._ak_codes.get("segment_syntax_errors", {})
        return {
            code: self.get_segment_error(code)
            for code in segment_errors.keys()
        }

    def get_all_element_errors(self) -> Dict[str, ErrorCodeInfo]:
        """Get all element syntax error codes.

        Returns:
            Dictionary mapping codes to ErrorCodeInfo instances
        """
        element_errors = self._ak_codes.get("element_syntax_errors", {})
        return {
            code: self.get_element_error(code)
            for code in element_errors.keys()
        }

    def get_severity_level(self, severity: str) -> int:
        """Get numeric severity level for sorting.

        Args:
            severity: Severity string (critical, error, warning, info, success)

        Returns:
            Numeric level (higher = more severe)
        """
        severity_map = {
            "critical": 50,
            "error": 40,
            "warning": 30,
            "info": 20,
            "success": 10,
        }
        return severity_map.get(severity.lower(), 0)
