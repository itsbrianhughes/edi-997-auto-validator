"""Main CLI entry point for EDI 997 Validator."""

import json
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from src.models.reconciliation import OutboundFunctionalGroup, OutboundTransaction
from src.reconciliation.reconciler import Reconciler
from src.reporting.markdown_generator import MarkdownReportGenerator
from src.serialization.json_serializer import JSONSerializer, OutputMode
from src.utils.config_loader import ConfigLoader
from src.utils.logger import get_logger, setup_logging
from src.utils.validation_pipeline import run_validation_pipeline

logger = get_logger(__name__)
console = Console()
console_err = Console(stderr=True)


@click.group()
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    default="INFO",
    help="Set logging level",
)
@click.version_option(version="0.1.0")
def cli(log_level: str) -> None:
    """EDI 997 Functional Acknowledgment Auto-Validator.

    Professional-grade tool for validating, reconciling, and reporting on
    EDI 997 Functional Acknowledgment documents.
    """
    from src.models.config_schemas import LogLevel

    # Map string to LogLevel enum
    level_map = {
        "DEBUG": LogLevel.DEBUG,
        "INFO": LogLevel.INFO,
        "WARNING": LogLevel.WARNING,
        "ERROR": LogLevel.ERROR,
    }
    setup_logging(log_level=level_map[log_level.upper()])


@cli.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file path (default: stdout)",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "markdown", "both"], case_sensitive=False),
    default="json",
    help="Output format",
)
@click.option(
    "--json-mode",
    type=click.Choice(["full", "summary", "compact"], case_sensitive=False),
    default="full",
    help="JSON output mode (only for --format json)",
)
@click.option(
    "--pretty/--no-pretty",
    default=True,
    help="Pretty print JSON output",
)
def validate(
    input_file: Path,
    output: Optional[Path],
    format: str,
    json_mode: str,
    pretty: bool,
) -> None:
    """Validate a 997 Functional Acknowledgment file.

    Parses and validates an EDI 997 document, checking for errors and
    generating detailed validation reports.

    Example:

        edi997 validate sample.997 -o report.json

        edi997 validate sample.997 --format markdown -o report.md

        edi997 validate sample.997 --format json --json-mode summary
    """
    try:
        console.print(f"[bold blue]Validating:[/bold blue] {input_file}")

        # Read file
        content = input_file.read_text(encoding="utf-8")

        # Parse 997
        validation_result = parse_and_validate_997(content)

        # Generate output
        if format.lower() == "json":
            output_content = generate_json_output(
                validation_result, json_mode, pretty
            )
            extension = ".json"
        elif format.lower() == "markdown":
            output_content = generate_markdown_output(validation_result)
            extension = ".md"
        else:  # both
            # Generate both formats
            json_output = generate_json_output(validation_result, json_mode, pretty)
            md_output = generate_markdown_output(validation_result)

            if output:
                # Write both files
                json_path = output.with_suffix(".json")
                md_path = output.with_suffix(".md")
                json_path.write_text(json_output, encoding="utf-8")
                md_path.write_text(md_output, encoding="utf-8")
                console.print(f"[green]✓[/green] JSON output written to: {json_path}")
                console.print(f"[green]✓[/green] Markdown output written to: {md_path}")
            else:
                console.print("\n[bold]JSON Output:[/bold]")
                console.print(json_output)
                console.print("\n[bold]Markdown Output:[/bold]")
                console.print(md_output)
            return

        # Write or print output
        if output:
            if not output.suffix:
                output = output.with_suffix(extension)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(output_content, encoding="utf-8")
            console.print(f"[green]✓[/green] Output written to: {output}")
        else:
            console.print("\n" + output_content)

        # Print summary to stderr
        print_validation_summary(validation_result)

        # Exit with appropriate code
        sys.exit(0 if validation_result.is_valid else 1)

    except Exception as e:
        logger.error("validation_failed", error=str(e))
        console_err.print(f"[red]✗ Error:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.argument("edi_997_file", type=click.Path(exists=True, path_type=Path))
@click.argument("outbound_json", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file path (default: stdout)",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "markdown", "both"], case_sensitive=False),
    default="markdown",
    help="Output format",
)
def reconcile(
    edi_997_file: Path,
    outbound_json: Path,
    output: Optional[Path],
    format: str,
) -> None:
    """Reconcile a 997 with outbound transactions.

    Matches 997 acknowledgments with outbound transactions to identify
    missing acknowledgments, unexpected acknowledgments, and validation status.

    The OUTBOUND_JSON file should contain outbound transaction data in JSON format:

    \b
    {
      "functional_id_code": "PO",
      "group_control_number": "1234",
      "transactions": [
        {
          "transaction_set_id": "850",
          "transaction_control_number": "5678",
          "group_control_number": "1234",
          "functional_id_code": "PO"
        }
      ]
    }

    Example:

        edi997 reconcile sample.997 outbound.json -o reconciliation.md

        edi997 reconcile sample.997 outbound.json --format json
    """
    try:
        console.print(f"[bold blue]Reconciling:[/bold blue] {edi_997_file}")
        console.print(f"[bold blue]With outbound:[/bold blue] {outbound_json}")

        # Read and parse 997
        content = edi_997_file.read_text(encoding="utf-8")
        validation_result = parse_and_validate_997(content)

        # Load outbound transactions
        outbound_data = json.loads(outbound_json.read_text(encoding="utf-8"))
        outbound_group = parse_outbound_data(outbound_data)

        # Reconcile
        reconciler = Reconciler()
        reconciliation_result = reconciler.reconcile(validation_result, outbound_group)

        # Generate output
        if format.lower() == "json":
            # For JSON, generate combined validation + reconciliation
            serializer = JSONSerializer(pretty=True)
            output_data = {
                "validation": json.loads(
                    serializer.serialize_validation_result(
                        validation_result, mode=OutputMode.FULL
                    )
                ),
                "reconciliation": {
                    "is_fully_reconciled": reconciliation_result.is_fully_reconciled,
                    "summary": reconciliation_result.summary,
                    "matched_count": reconciliation_result.matched_count,
                    "total_count": reconciliation_result.total_count,
                    "functional_group": serializer.serialize_functional_group_validation(
                        reconciliation_result.functional_group_reconciliation
                    ),
                },
            }
            output_content = json.dumps(output_data, indent=2, sort_keys=True)
            extension = ".json"
        elif format.lower() == "markdown":
            generator = MarkdownReportGenerator()
            output_content = generator.generate_combined_report(
                validation_result, reconciliation_result
            )
            extension = ".md"
        else:  # both
            # Generate both formats
            serializer = JSONSerializer(pretty=True)
            output_data = {
                "validation": json.loads(
                    serializer.serialize_validation_result(
                        validation_result, mode=OutputMode.FULL
                    )
                ),
                "reconciliation": {
                    "is_fully_reconciled": reconciliation_result.is_fully_reconciled,
                    "summary": reconciliation_result.summary,
                },
            }
            json_output = json.dumps(output_data, indent=2, sort_keys=True)

            generator = MarkdownReportGenerator()
            md_output = generator.generate_combined_report(
                validation_result, reconciliation_result
            )

            if output:
                json_path = output.with_suffix(".json")
                md_path = output.with_suffix(".md")
                json_path.write_text(json_output, encoding="utf-8")
                md_path.write_text(md_output, encoding="utf-8")
                console.print(f"[green]✓[/green] JSON output written to: {json_path}")
                console.print(f"[green]✓[/green] Markdown output written to: {md_path}")
            else:
                console.print("\n[bold]JSON Output:[/bold]")
                console.print(json_output)
                console.print("\n[bold]Markdown Output:[/bold]")
                console.print(md_output)
            return

        # Write or print output
        if output:
            if not output.suffix:
                output = output.with_suffix(extension)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(output_content, encoding="utf-8")
            console.print(f"[green]✓[/green] Output written to: {output}")
        else:
            console.print("\n" + output_content)

        # Print summary
        print_reconciliation_summary(reconciliation_result)

        # Exit with appropriate code
        sys.exit(0 if reconciliation_result.is_fully_reconciled else 1)

    except Exception as e:
        logger.error("reconciliation_failed", error=str(e))
        console_err.print(f"[red]✗ Error:[/red] {e}")
        sys.exit(1)


def parse_and_validate_997(content: str):
    """Parse and validate a 997 document.

    This function is now a thin wrapper around the shared validation pipeline.
    """
    return run_validation_pipeline(content)


def parse_outbound_data(data: dict) -> OutboundFunctionalGroup:
    """Parse outbound transaction data from JSON."""
    transactions = [
        OutboundTransaction(**tx) for tx in data.get("transactions", [])
    ]

    return OutboundFunctionalGroup(
        functional_id_code=data["functional_id_code"],
        group_control_number=data["group_control_number"],
        transactions=transactions,
    )


def generate_json_output(
    validation_result, json_mode: str, pretty: bool
) -> str:
    """Generate JSON output."""
    serializer = JSONSerializer(pretty=pretty)

    mode_map = {
        "full": OutputMode.FULL,
        "summary": OutputMode.SUMMARY,
        "compact": OutputMode.COMPACT,
    }

    return serializer.serialize_validation_result(
        validation_result, mode=mode_map[json_mode.lower()]
    )


def generate_markdown_output(validation_result) -> str:
    """Generate Markdown output."""
    generator = MarkdownReportGenerator()
    return generator.generate_validation_report(validation_result)


def print_validation_summary(validation_result) -> None:
    """Print validation summary table to console."""
    fg = validation_result.functional_group

    # Create summary table
    table = Table(title="Validation Summary", show_header=False)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")

    status_emoji = "✅" if validation_result.is_valid else "❌"
    table.add_row("Status", f"{status_emoji} {validation_result.overall_status}")
    table.add_row("Summary", validation_result.summary)
    table.add_row("Transaction Sets Included", str(fg.transaction_sets_included))
    table.add_row("Transaction Sets Accepted", str(fg.transaction_sets_accepted))
    table.add_row("Total Errors", str(fg.total_errors))

    console_err.print(table)


def print_reconciliation_summary(reconciliation_result) -> None:
    """Print reconciliation summary table to console."""
    fg_recon = reconciliation_result.functional_group_reconciliation

    # Create summary table
    table = Table(title="Reconciliation Summary", show_header=False)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")

    status_emoji = "✅" if reconciliation_result.is_fully_reconciled else "⚠️"
    status_text = (
        "Fully Reconciled"
        if reconciliation_result.is_fully_reconciled
        else "Partial Reconciliation"
    )
    table.add_row("Status", f"{status_emoji} {status_text}")
    table.add_row("Summary", reconciliation_result.summary)
    table.add_row("Total Transactions", str(fg_recon.total_count))
    table.add_row("Matched", str(fg_recon.matched_count))
    table.add_row("Missing Acknowledgments", str(fg_recon.missing_ack_count))
    table.add_row("Unexpected Acknowledgments", str(fg_recon.unexpected_ack_count))

    console_err.print(table)


if __name__ == "__main__":
    cli()
