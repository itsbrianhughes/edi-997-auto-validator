"""JSON serialization for 997 validation results."""

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Union

from pydantic import BaseModel

from src.models.validation import (
    ErrorDetail,
    FunctionalGroupValidation,
    TransactionSetValidation,
    ValidationResult,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class OutputMode(str, Enum):
    """JSON output modes."""

    FULL = "full"
    SUMMARY = "summary"
    COMPACT = "compact"


class JSONSerializer:
    """Serialize 997 validation results to JSON."""

    def __init__(
        self,
        pretty: bool = True,
        indent: int = 2,
        sort_keys: bool = True,
    ) -> None:
        """Initialize JSON serializer.

        Args:
            pretty: Enable pretty printing with indentation
            indent: Number of spaces for indentation (if pretty=True)
            sort_keys: Sort dictionary keys alphabetically
        """
        self.pretty = pretty
        self.indent = indent if pretty else None
        self.sort_keys = sort_keys

    def serialize_validation_result(
        self,
        result: ValidationResult,
        mode: OutputMode = OutputMode.FULL,
    ) -> str:
        """Serialize ValidationResult to JSON string.

        Args:
            result: ValidationResult to serialize
            mode: Output mode (full, summary, compact)

        Returns:
            JSON string

        Example:
            >>> serializer = JSONSerializer()
            >>> json_output = serializer.serialize_validation_result(result)
        """
        if mode == OutputMode.SUMMARY:
            data = self._build_summary(result)
        elif mode == OutputMode.COMPACT:
            data = self._build_compact(result)
        else:
            data = self._build_full(result)

        return self._dumps(data)

    def serialize_to_file(
        self,
        result: ValidationResult,
        output_path: Union[str, Path],
        mode: OutputMode = OutputMode.FULL,
    ) -> None:
        """Serialize ValidationResult to JSON file.

        Args:
            result: ValidationResult to serialize
            output_path: Path to output file
            mode: Output mode (full, summary, compact)

        Example:
            >>> serializer.serialize_to_file(result, "output.json")
        """
        json_output = self.serialize_validation_result(result, mode)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(json_output)

        logger.info(
            "validation_result_serialized",
            output_path=str(output_path),
            mode=mode.value,
        )

    def _build_full(self, result: ValidationResult) -> dict[str, Any]:
        """Build full detailed JSON output.

        Args:
            result: ValidationResult to serialize

        Returns:
            Dictionary for JSON serialization
        """
        # Use Pydantic's model_dump for base conversion
        data = result.model_dump(mode="json", exclude_none=False)

        # Add computed fields
        data["overall_status"] = result.overall_status
        data["summary"] = result.summary

        # Format timestamp consistently
        if isinstance(data.get("validation_timestamp"), str):
            # Already serialized by Pydantic
            pass
        elif isinstance(result.validation_timestamp, datetime):
            data["validation_timestamp"] = result.validation_timestamp.isoformat()

        return data

    def _build_summary(self, result: ValidationResult) -> dict[str, Any]:
        """Build summary JSON output (minimal details).

        Args:
            result: ValidationResult to serialize

        Returns:
            Dictionary for JSON serialization
        """
        fg = result.functional_group

        return {
            "interchange_control_number": result.interchange_control_number,
            "interchange_sender_id": result.interchange_sender_id,
            "interchange_receiver_id": result.interchange_receiver_id,
            "is_valid": result.is_valid,
            "overall_status": result.overall_status,
            "summary": result.summary,
            "validation_timestamp": result.validation_timestamp.isoformat(),
            "functional_group": {
                "functional_id_code": fg.functional_id_code,
                "group_control_number": fg.group_control_number,
                "status": fg.status.value,
                "ack_code": fg.ack_code,
                "transaction_sets_included": fg.transaction_sets_included,
                "transaction_sets_accepted": fg.transaction_sets_accepted,
                "total_errors": fg.total_errors,
            },
            "transaction_sets": [
                {
                    "transaction_set_id": ts.transaction_set_id,
                    "transaction_control_number": ts.transaction_control_number,
                    "status": ts.status.value,
                    "ack_code": ts.ack_code,
                    "error_count": ts.error_count,
                }
                for ts in fg.transaction_validations
            ],
        }

    def _build_compact(self, result: ValidationResult) -> dict[str, Any]:
        """Build compact JSON output (one-liner friendly).

        Args:
            result: ValidationResult to serialize

        Returns:
            Dictionary for JSON serialization
        """
        fg = result.functional_group

        return {
            "icn": result.interchange_control_number,
            "sender": result.interchange_sender_id,
            "receiver": result.interchange_receiver_id,
            "valid": result.is_valid,
            "status": result.overall_status,
            "accepted": fg.transaction_sets_accepted,
            "total": fg.transaction_sets_included,
            "errors": fg.total_errors,
            "timestamp": result.validation_timestamp.isoformat(),
        }

    def _dumps(self, data: dict[str, Any]) -> str:
        """Dump dictionary to JSON string with configured formatting.

        Args:
            data: Dictionary to serialize

        Returns:
            JSON string
        """
        return json.dumps(
            data,
            indent=self.indent,
            sort_keys=self.sort_keys,
            ensure_ascii=False,
        )

    def serialize_error_detail(self, error: ErrorDetail) -> dict[str, Any]:
        """Serialize ErrorDetail to dictionary.

        Args:
            error: ErrorDetail to serialize

        Returns:
            Dictionary representation
        """
        return error.model_dump(mode="json", exclude_none=True)

    def serialize_transaction_validation(
        self, validation: TransactionSetValidation
    ) -> dict[str, Any]:
        """Serialize TransactionSetValidation to dictionary.

        Args:
            validation: TransactionSetValidation to serialize

        Returns:
            Dictionary representation
        """
        return validation.model_dump(mode="json", exclude_none=True)

    def serialize_functional_group_validation(
        self, validation: FunctionalGroupValidation
    ) -> dict[str, Any]:
        """Serialize FunctionalGroupValidation to dictionary.

        Args:
            validation: FunctionalGroupValidation to serialize

        Returns:
            Dictionary representation
        """
        data = validation.model_dump(mode="json", exclude_none=True)
        # Add computed field
        data["total_errors"] = validation.total_errors
        return data


def create_serializer(
    pretty: bool = True,
    indent: int = 2,
    sort_keys: bool = True,
) -> JSONSerializer:
    """Create a JSON serializer with specified options.

    Args:
        pretty: Enable pretty printing
        indent: Indentation level (if pretty=True)
        sort_keys: Sort dictionary keys

    Returns:
        JSONSerializer instance

    Example:
        >>> serializer = create_serializer(pretty=False)
        >>> json_str = serializer.serialize_validation_result(result)
    """
    return JSONSerializer(pretty=pretty, indent=indent, sort_keys=sort_keys)
