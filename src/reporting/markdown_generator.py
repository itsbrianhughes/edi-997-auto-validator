"""Markdown report generator for 997 validation and reconciliation results."""

from datetime import datetime
from pathlib import Path
from typing import Optional, Union

from src.models.reconciliation import (
    FunctionalGroupReconciliation,
    ReconciliationResult,
    ReconciliationStatus,
    TransactionReconciliation,
)
from src.models.validation import (
    ErrorDetail,
    FunctionalGroupValidation,
    TransactionSetValidation,
    ValidationResult,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MarkdownReportGenerator:
    """Generate human-readable Markdown reports for 997 validation results."""

    def __init__(self, include_timestamps: bool = True) -> None:
        """Initialize Markdown report generator.

        Args:
            include_timestamps: Include generation timestamp in reports
        """
        self.include_timestamps = include_timestamps

    def generate_validation_report(
        self, validation_result: ValidationResult
    ) -> str:
        """Generate Markdown report for validation result.

        Args:
            validation_result: ValidationResult to report

        Returns:
            Markdown formatted report

        Example:
            >>> generator = MarkdownReportGenerator()
            >>> report = generator.generate_validation_report(result)
        """
        lines: list[str] = []

        # Header
        lines.append("# 997 Functional Acknowledgment Validation Report")
        lines.append("")

        # Timestamp
        if self.include_timestamps:
            timestamp = validation_result.validation_timestamp.strftime(
                "%Y-%m-%d %H:%M:%S UTC"
            )
            lines.append(f"**Generated:** {timestamp}")
            lines.append("")

        # Summary section
        lines.extend(self._build_summary_section(validation_result))

        # Interchange details
        lines.extend(self._build_interchange_section(validation_result))

        # Functional group details
        lines.extend(
            self._build_functional_group_section(validation_result.functional_group)
        )

        # Transaction sets
        lines.extend(self._build_transaction_sets_section(validation_result))

        # Error details (if any)
        if validation_result.functional_group.total_errors > 0:
            lines.extend(self._build_errors_section(validation_result))

        return "\n".join(lines)

    def generate_reconciliation_report(
        self,
        reconciliation_result: ReconciliationResult,
        validation_result: Optional[ValidationResult] = None,
    ) -> str:
        """Generate Markdown report for reconciliation result.

        Args:
            reconciliation_result: ReconciliationResult to report
            validation_result: Optional ValidationResult for additional context

        Returns:
            Markdown formatted report

        Example:
            >>> report = generator.generate_reconciliation_report(recon_result)
        """
        lines: list[str] = []

        # Header
        lines.append("# 997 Reconciliation Report")
        lines.append("")

        # Timestamp
        if self.include_timestamps and validation_result:
            timestamp = validation_result.validation_timestamp.strftime(
                "%Y-%m-%d %H:%M:%S UTC"
            )
            lines.append(f"**Generated:** {timestamp}")
            lines.append("")

        # Summary
        lines.extend(self._build_reconciliation_summary(reconciliation_result))

        # Detailed reconciliation
        lines.extend(
            self._build_reconciliation_details(
                reconciliation_result.functional_group_reconciliation
            )
        )

        return "\n".join(lines)

    def generate_combined_report(
        self,
        validation_result: ValidationResult,
        reconciliation_result: ReconciliationResult,
    ) -> str:
        """Generate combined validation + reconciliation report.

        Args:
            validation_result: ValidationResult
            reconciliation_result: ReconciliationResult

        Returns:
            Markdown formatted combined report
        """
        lines: list[str] = []

        # Header
        lines.append("# 997 Validation & Reconciliation Report")
        lines.append("")

        # Timestamp
        if self.include_timestamps:
            timestamp = validation_result.validation_timestamp.strftime(
                "%Y-%m-%d %H:%M:%S UTC"
            )
            lines.append(f"**Generated:** {timestamp}")
            lines.append("")

        # Validation summary
        lines.append("## Validation Summary")
        lines.append("")
        lines.extend(self._build_summary_section(validation_result))

        # Reconciliation summary
        lines.append("## Reconciliation Summary")
        lines.append("")
        lines.extend(self._build_reconciliation_summary(reconciliation_result))

        # Interchange details
        lines.extend(self._build_interchange_section(validation_result))

        # Transaction details with reconciliation status
        lines.extend(
            self._build_combined_transaction_section(
                validation_result, reconciliation_result
            )
        )

        # Errors (if any)
        if validation_result.functional_group.total_errors > 0:
            lines.extend(self._build_errors_section(validation_result))

        return "\n".join(lines)

    def write_report(
        self, report: str, output_path: Union[str, Path]
    ) -> None:
        """Write report to file.

        Args:
            report: Markdown report content
            output_path: Path to output file

        Example:
            >>> generator.write_report(report, "report.md")
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)

        logger.info("markdown_report_written", output_path=str(output_path))

    def _build_summary_section(
        self, validation_result: ValidationResult
    ) -> list[str]:
        """Build summary section."""
        lines: list[str] = []
        fg = validation_result.functional_group

        # Status badge
        status_emoji = "✅" if validation_result.is_valid else "❌"
        lines.append(f"**Status:** {status_emoji} {validation_result.overall_status}")
        lines.append("")

        # Key metrics
        lines.append(f"**Summary:** {validation_result.summary}")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(
            f"| Transaction Sets Included | {fg.transaction_sets_included} |"
        )
        lines.append(
            f"| Transaction Sets Received | {fg.transaction_sets_received} |"
        )
        lines.append(
            f"| Transaction Sets Accepted | {fg.transaction_sets_accepted} |"
        )
        lines.append(f"| Total Errors | {fg.total_errors} |")
        lines.append("")

        return lines

    def _build_interchange_section(
        self, validation_result: ValidationResult
    ) -> list[str]:
        """Build interchange details section."""
        lines: list[str] = []

        lines.append("## Interchange Details")
        lines.append("")
        lines.append("| Field | Value |")
        lines.append("|-------|-------|")
        lines.append(
            f"| Control Number | {validation_result.interchange_control_number} |"
        )
        lines.append(f"| Sender ID | {validation_result.interchange_sender_id} |")
        lines.append(f"| Receiver ID | {validation_result.interchange_receiver_id} |")
        lines.append("")

        return lines

    def _build_functional_group_section(
        self, fg_validation: FunctionalGroupValidation
    ) -> list[str]:
        """Build functional group details section."""
        lines: list[str] = []

        lines.append("## Functional Group Details")
        lines.append("")
        lines.append("| Field | Value |")
        lines.append("|-------|-------|")
        lines.append(f"| Functional ID Code | {fg_validation.functional_id_code} |")
        lines.append(
            f"| Group Control Number | {fg_validation.group_control_number} |"
        )
        lines.append(f"| Status | {fg_validation.status.value} |")
        lines.append(
            f"| Acknowledgment Code (AK9-01) | {fg_validation.ack_code} |"
        )
        lines.append("")

        return lines

    def _build_transaction_sets_section(
        self, validation_result: ValidationResult
    ) -> list[str]:
        """Build transaction sets section."""
        lines: list[str] = []
        fg = validation_result.functional_group

        lines.append("## Transaction Sets")
        lines.append("")

        if not fg.transaction_validations:
            lines.append("*No transaction sets found*")
            lines.append("")
            return lines

        # Table header
        lines.append("| Control # | Type | Status | Ack Code | Errors |")
        lines.append("|-----------|------|--------|----------|--------|")

        # Table rows
        for ts in fg.transaction_validations:
            status_emoji = "✅" if ts.status.value == "ACCEPTED" else "⚠️" if ts.status.value == "PARTIALLY_ACCEPTED" else "❌"
            lines.append(
                f"| {ts.transaction_control_number} | {ts.transaction_set_id} | "
                f"{status_emoji} {ts.status.value} | {ts.ack_code} | {ts.error_count} |"
            )

        lines.append("")

        return lines

    def _build_errors_section(
        self, validation_result: ValidationResult
    ) -> list[str]:
        """Build errors section."""
        lines: list[str] = []

        lines.append("## Error Details")
        lines.append("")

        for ts in validation_result.functional_group.transaction_validations:
            if ts.error_count > 0:
                lines.append(
                    f"### Transaction {ts.transaction_control_number} ({ts.transaction_set_id})"
                )
                lines.append("")

                if ts.errors:
                    lines.append("| Segment | Position | Element | Code | Description |")
                    lines.append("|---------|----------|---------|------|-------------|")

                    for error in ts.errors:
                        segment = error.segment_id or "-"
                        seg_pos = str(error.segment_position) if error.segment_position else "-"
                        elem_pos = str(error.element_position) if error.element_position else "-"
                        lines.append(
                            f"| {segment} | {seg_pos} | {elem_pos} | "
                            f"{error.error_code} | {error.error_description} |"
                        )

                    lines.append("")

                if ts.syntax_error_codes:
                    lines.append(f"**Syntax Error Codes:** {', '.join(ts.syntax_error_codes)}")
                    lines.append("")

        return lines

    def _build_reconciliation_summary(
        self, reconciliation_result: ReconciliationResult
    ) -> list[str]:
        """Build reconciliation summary section."""
        lines: list[str] = []
        fg_recon = reconciliation_result.functional_group_reconciliation

        # Status
        status_emoji = "✅" if reconciliation_result.is_fully_reconciled else "⚠️"
        status_text = "Fully Reconciled" if reconciliation_result.is_fully_reconciled else "Partial Reconciliation"
        lines.append(f"**Status:** {status_emoji} {status_text}")
        lines.append("")

        # Summary
        lines.append(f"**Summary:** {reconciliation_result.summary}")
        lines.append("")

        # Statistics table
        lines.append("| Metric | Count |")
        lines.append("|--------|-------|")
        lines.append(f"| Total Transactions | {fg_recon.total_count} |")
        lines.append(f"| Matched | {fg_recon.matched_count} |")
        lines.append(f"| Missing Acknowledgments | {fg_recon.missing_ack_count} |")
        lines.append(f"| Unexpected Acknowledgments | {fg_recon.unexpected_ack_count} |")
        lines.append("")

        return lines

    def _build_reconciliation_details(
        self, fg_reconciliation: FunctionalGroupReconciliation
    ) -> list[str]:
        """Build detailed reconciliation section."""
        lines: list[str] = []

        lines.append("## Reconciliation Details")
        lines.append("")

        if not fg_reconciliation.transaction_reconciliations:
            lines.append("*No transactions to reconcile*")
            lines.append("")
            return lines

        # Table header
        lines.append("| Control # | Type | Recon Status | Validation Status | Note |")
        lines.append("|-----------|------|--------------|-------------------|------|")

        # Table rows
        for tx_recon in fg_reconciliation.transaction_reconciliations:
            control_num = tx_recon.control_number or "-"

            # Get transaction type
            tx_type = "-"
            if tx_recon.outbound_transaction:
                tx_type = tx_recon.outbound_transaction.transaction_set_id
            elif tx_recon.acknowledgment:
                tx_type = tx_recon.acknowledgment.transaction_set_id

            # Status emoji
            if tx_recon.status == ReconciliationStatus.MATCHED:
                status_emoji = "✅"
            elif tx_recon.status == ReconciliationStatus.MISSING_ACK:
                status_emoji = "⚠️"
            else:
                status_emoji = "❌"

            # Validation status
            val_status = "-"
            if tx_recon.acknowledgment:
                val_status = tx_recon.acknowledgment.status.value

            # Note
            note = tx_recon.mismatch_reason if tx_recon.mismatch_reason else "-"

            lines.append(
                f"| {control_num} | {tx_type} | {status_emoji} {tx_recon.status.value} | "
                f"{val_status} | {note} |"
            )

        lines.append("")

        return lines

    def _build_combined_transaction_section(
        self,
        validation_result: ValidationResult,
        reconciliation_result: ReconciliationResult,
    ) -> list[str]:
        """Build combined transaction section with validation + reconciliation."""
        lines: list[str] = []

        lines.append("## Transaction Details")
        lines.append("")

        fg_recon = reconciliation_result.functional_group_reconciliation

        if not fg_recon.transaction_reconciliations:
            lines.append("*No transactions found*")
            lines.append("")
            return lines

        # Table header
        lines.append("| Control # | Type | Validation | Reconciliation | Errors |")
        lines.append("|-----------|------|------------|----------------|--------|")

        # Table rows
        for tx_recon in fg_recon.transaction_reconciliations:
            control_num = tx_recon.control_number or "-"

            # Get transaction type
            tx_type = "-"
            if tx_recon.outbound_transaction:
                tx_type = tx_recon.outbound_transaction.transaction_set_id
            elif tx_recon.acknowledgment:
                tx_type = tx_recon.acknowledgment.transaction_set_id

            # Validation status
            val_status = "-"
            error_count = 0
            if tx_recon.acknowledgment:
                val_emoji = "✅" if tx_recon.acknowledgment.status.value == "ACCEPTED" else "⚠️" if tx_recon.acknowledgment.status.value == "PARTIALLY_ACCEPTED" else "❌"
                val_status = f"{val_emoji} {tx_recon.acknowledgment.status.value}"
                error_count = tx_recon.acknowledgment.error_count

            # Reconciliation status
            if tx_recon.status == ReconciliationStatus.MATCHED:
                recon_emoji = "✅"
            elif tx_recon.status == ReconciliationStatus.MISSING_ACK:
                recon_emoji = "⚠️"
            else:
                recon_emoji = "❌"
            recon_status = f"{recon_emoji} {tx_recon.status.value}"

            lines.append(
                f"| {control_num} | {tx_type} | {val_status} | {recon_status} | {error_count} |"
            )

        lines.append("")

        return lines
