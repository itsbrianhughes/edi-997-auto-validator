"""Streamlit UI for EDI 997 Functional Acknowledgment Auto-Validator.

This app provides an interactive interface for validating 997 files,
viewing detailed error reports, and reconciling with outbound transactions.
"""

import io
import json
from datetime import datetime
from typing import Optional

import pandas as pd
import streamlit as st

from src.models.reconciliation import (
    OutboundFunctionalGroup,
    OutboundTransaction,
    ReconciliationResult,
)
from src.models.validation import ValidationResult
from src.reconciliation.reconciler import Reconciler
from src.reporting.markdown_generator import MarkdownReportGenerator
from src.serialization.json_serializer import JSONSerializer, OutputMode
from src.utils.validation_pipeline import run_validation_pipeline


# Page configuration
st.set_page_config(
    page_title="EDI 997 Auto-Validator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def parse_outbound_json(content: str) -> OutboundFunctionalGroup:
    """Parse outbound data from JSON string."""
    data = json.loads(content)
    transactions = [OutboundTransaction(**tx) for tx in data.get("transactions", [])]
    return OutboundFunctionalGroup(
        functional_id_code=data["functional_id_code"],
        group_control_number=data["group_control_number"],
        transactions=transactions,
    )


def parse_outbound_csv(df: pd.DataFrame) -> OutboundFunctionalGroup:
    """Parse outbound data from CSV DataFrame."""
    if df.empty:
        raise ValueError("CSV file is empty")

    required_columns = [
        "transaction_set_id",
        "transaction_control_number",
    ]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(
            f"CSV missing required columns: {', '.join(missing_columns)}"
        )

    # Extract functional group info from first row
    functional_id_code = df.iloc[0].get("functional_id_code", "PO")
    group_control_number = df.iloc[0].get("group_control_number", "1")

    # Parse transactions
    transactions = []
    for _, row in df.iterrows():
        tx = OutboundTransaction(
            transaction_set_id=str(row["transaction_set_id"]),
            transaction_control_number=str(row["transaction_control_number"]),
        )
        transactions.append(tx)

    return OutboundFunctionalGroup(
        functional_id_code=str(functional_id_code),
        group_control_number=str(group_control_number),
        transactions=transactions,
    )


def render_summary_tab(validation_result: ValidationResult):
    """Render the validation summary tab."""
    st.subheader("📋 Validation Summary")

    # Overall status badge
    status = validation_result.overall_status
    if status == "ACCEPTED":
        st.success(f"✅ Status: {status}")
    elif status == "PARTIALLY_ACCEPTED":
        st.warning(f"⚠️ Status: {status}")
    else:
        st.error(f"❌ Status: {status}")

    # Metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📦 Functional Groups", len(validation_result.functional_groups))

    with col2:
        total_transactions = sum(
            len(fg.transaction_sets) for fg in validation_result.functional_groups
        )
        st.metric("📄 Transactions", total_transactions)

    with col3:
        accepted_count = sum(
            1
            for fg in validation_result.functional_groups
            for ts in fg.transaction_sets
            if ts.status == "ACCEPTED"
        )
        st.metric("✅ Accepted", accepted_count)

    with col4:
        total_errors = sum(
            len(ts.errors)
            for fg in validation_result.functional_groups
            for ts in fg.transaction_sets
        )
        st.metric("❌ Errors", total_errors)

    # Interchange details
    st.subheader("Interchange Details")
    interchange_data = {
        "Control Number": validation_result.interchange_control_number,
        "Sender ID": validation_result.sender_id,
        "Receiver ID": validation_result.receiver_id,
        "Timestamp": validation_result.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
    }
    st.table(pd.DataFrame([interchange_data]).T)

    # Functional group details
    if validation_result.functional_groups:
        st.subheader("Functional Group Details")
        fg = validation_result.functional_groups[0]
        fg_data = {
            "Functional ID Code": fg.functional_id_code,
            "Group Control Number": fg.group_control_number,
            "Status": fg.status,
            "Acknowledgment Code": fg.functional_group_ack_code,
        }
        st.table(pd.DataFrame([fg_data]).T)


def render_transactions_tab(validation_result: ValidationResult):
    """Render the transactions details tab."""
    st.subheader("📑 Transaction Details")

    # Collect all transactions
    transactions_data = []
    for fg in validation_result.functional_groups:
        for ts in fg.transaction_sets:
            status_icon = (
                "✅"
                if ts.status == "ACCEPTED"
                else "⚠️" if ts.status == "PARTIALLY_ACCEPTED" else "❌"
            )
            transactions_data.append(
                {
                    "Control #": ts.transaction_control_number or "N/A",
                    "Type": ts.transaction_set_id or "N/A",
                    "Status": f"{status_icon} {ts.status}",
                    "Ack Code": ts.transaction_set_ack_code or "N/A",
                    "Errors": len(ts.errors),
                }
            )

    if transactions_data:
        df = pd.DataFrame(transactions_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No transaction sets found in this 997 file.")


def render_errors_tab(validation_result: ValidationResult):
    """Render the error details tab."""
    st.subheader("⚠️ Error Details")

    # Collect all transactions with errors
    has_errors = False
    for fg in validation_result.functional_groups:
        for ts in fg.transaction_sets:
            if ts.errors:
                has_errors = True
                status_icon = (
                    "❌" if ts.status == "REJECTED" else "⚠️"
                )
                with st.expander(
                    f"{status_icon} Transaction {ts.transaction_control_number or 'N/A'} "
                    f"({ts.transaction_set_id or 'N/A'}) - {ts.status} - {len(ts.errors)} Errors",
                    expanded=True,
                ):
                    error_data = []
                    for error in ts.errors:
                        error_data.append(
                            {
                                "Segment": error.segment_id or "-",
                                "Position": error.segment_position or "-",
                                "Element": error.element_position or "-",
                                "Code": error.error_code,
                                "Description": error.error_description or "N/A",
                            }
                        )

                    df = pd.DataFrame(error_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)

                    # Show syntax error codes
                    if ts.syntax_error_codes:
                        st.caption(
                            f"**Syntax Error Codes:** {', '.join(ts.syntax_error_codes)}"
                        )

    if not has_errors:
        st.success("🎉 No errors found! All transactions accepted.")


def render_reconciliation_tab(
    validation_result: ValidationResult, reconciliation_result: ReconciliationResult
):
    """Render the reconciliation tab."""
    st.subheader("🔄 Reconciliation Results")

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    matched = reconciliation_result.matched_count
    missing = reconciliation_result.missing_acknowledgment_count
    unexpected = reconciliation_result.unexpected_acknowledgment_count
    total_outbound = matched + missing

    with col1:
        st.metric("📤 Sent", total_outbound)

    with col2:
        st.metric("✅ Matched", matched)

    with col3:
        st.metric("⚠️ Missing ACK", missing)

    with col4:
        st.metric("❌ Unexpected", unexpected)

    # Reconciliation status
    if missing == 0 and unexpected == 0:
        st.success("✅ Reconciliation Status: Fully Reconciled")
    else:
        st.warning("⚠️ Reconciliation Status: Partial Reconciliation")

    # Reconciliation table
    st.subheader("Reconciliation Details")

    recon_data = []

    # Matched transactions
    for fg_recon in reconciliation_result.functional_groups:
        for ts_recon in fg_recon.transaction_sets:
            status_icon = "✅"
            recon_status = "MATCHED"

            # Determine 997 status
            ts_997_status = "N/A"
            for fg in validation_result.functional_groups:
                for ts in fg.transaction_sets:
                    if ts.transaction_control_number == ts_recon.outbound.transaction_control_number:
                        ts_997_status = ts.status
                        break

            recon_data.append(
                {
                    "Control #": ts_recon.outbound.transaction_control_number,
                    "Type": ts_recon.outbound.transaction_set_id,
                    "997 Status": ts_997_status,
                    "Reconciliation": f"{status_icon} {recon_status}",
                    "Notes": ts_recon.notes or "-",
                }
            )

    # Missing acknowledgments
    for fg_recon in reconciliation_result.functional_groups:
        for outbound_tx in fg_recon.missing_acknowledgments:
            recon_data.append(
                {
                    "Control #": outbound_tx.transaction_control_number,
                    "Type": outbound_tx.transaction_set_id,
                    "997 Status": "-",
                    "Reconciliation": "⚠️ MISSING_ACK",
                    "Notes": "No acknowledgment received",
                }
            )

    # Unexpected acknowledgments
    for fg_recon in reconciliation_result.functional_groups:
        for unexpected_ts in fg_recon.unexpected_acknowledgments:
            recon_data.append(
                {
                    "Control #": unexpected_ts.transaction_control_number or "N/A",
                    "Type": unexpected_ts.transaction_set_id or "N/A",
                    "997 Status": unexpected_ts.status,
                    "Reconciliation": "❌ UNEXPECTED",
                    "Notes": "Not in outbound data",
                }
            )

    if recon_data:
        df = pd.DataFrame(recon_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No reconciliation data available.")


def render_downloads_tab(
    validation_result: ValidationResult,
    reconciliation_result: Optional[ReconciliationResult] = None,
):
    """Render the downloads tab."""
    st.subheader("📥 Download Reports")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**JSON Reports**")

        # JSON mode selector
        json_mode = st.radio(
            "Select JSON mode:",
            ["Compact", "Summary", "Full"],
            horizontal=True,
        )

        mode_map = {
            "Compact": OutputMode.COMPACT,
            "Summary": OutputMode.SUMMARY,
            "Full": OutputMode.FULL,
        }

        serializer = JSONSerializer(pretty=True)
        json_output = serializer.serialize_validation_result(
            validation_result, mode=mode_map[json_mode]
        )

        st.download_button(
            label=f"📄 Download {json_mode} JSON",
            data=json_output,
            file_name=f"997_validation_{json_mode.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
        )

        # JSON preview
        with st.expander("Preview JSON"):
            st.json(json.loads(json_output))

    with col2:
        st.write("**Markdown Report**")

        generator = MarkdownReportGenerator()
        if reconciliation_result:
            markdown_output = generator.generate_combined_report(
                validation_result, reconciliation_result
            )
        else:
            markdown_output = generator.generate_validation_report(validation_result)

        st.download_button(
            label="📝 Download Markdown Report",
            data=markdown_output,
            file_name=f"997_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
        )

        # Markdown preview
        with st.expander("Preview Markdown"):
            st.markdown(markdown_output)


def main():
    """Main Streamlit app."""
    st.title("📊 EDI 997 Functional Acknowledgment Auto-Validator")
    st.markdown(
        "Upload a 997 EDI file or paste content to validate and analyze functional acknowledgments."
    )

    # Initialize session state
    if "validation_result" not in st.session_state:
        st.session_state.validation_result = None
    if "reconciliation_result" not in st.session_state:
        st.session_state.reconciliation_result = None
    if "outbound_group" not in st.session_state:
        st.session_state.outbound_group = None

    # Sidebar
    with st.sidebar:
        st.header("📤 Input Sources")

        # File uploader for 997 files
        uploaded_file = st.file_uploader(
            "Upload 997/EDI File",
            type=["997", "edi", "txt"],
            help="Upload one or more EDI 997 files",
        )

        st.markdown("**OR**")

        # Text area for pasting content
        pasted_content = st.text_area(
            "Paste Raw EDI Content",
            height=200,
            placeholder="ISA*00*...",
            help="Paste raw EDI 997 content here",
        )

        st.divider()

        # Reconciliation section
        st.header("📦 Reconciliation (Optional)")

        outbound_file = st.file_uploader(
            "Upload Outbound Reference",
            type=["json", "csv"],
            help="Upload outbound transactions for reconciliation",
        )

        st.divider()

        # Determine content source
        content = None
        if uploaded_file:
            content = uploaded_file.read().decode("utf-8")
        elif pasted_content.strip():
            content = pasted_content

        # Run validation button
        run_button = st.button(
            "▶️ Run Validation",
            type="primary",
            use_container_width=True,
            disabled=content is None,
        )

        if run_button and content:
            with st.spinner("🔄 Validating EDI 997 file..."):
                try:
                    # Run validation pipeline
                    validation_result = run_validation_pipeline(content)
                    st.session_state.validation_result = validation_result
                    st.success("✅ Validation complete!")

                    # Process outbound file if provided
                    if outbound_file:
                        try:
                            outbound_content = outbound_file.read().decode("utf-8")
                            if outbound_file.name.endswith(".json"):
                                outbound_group = parse_outbound_json(outbound_content)
                            else:  # CSV
                                df = pd.read_csv(io.StringIO(outbound_content))
                                outbound_group = parse_outbound_csv(df)

                            st.session_state.outbound_group = outbound_group

                            # Run reconciliation
                            reconciler = Reconciler()
                            reconciliation_result = reconciler.reconcile(
                                validation_result, outbound_group
                            )
                            st.session_state.reconciliation_result = (
                                reconciliation_result
                            )
                            st.success("✅ Reconciliation complete!")

                        except Exception as e:
                            st.error(f"❌ Reconciliation failed: {str(e)}")
                            st.session_state.reconciliation_result = None

                except Exception as e:
                    st.error(f"❌ Validation failed: {str(e)}")
                    st.session_state.validation_result = None

    # Main content area
    if st.session_state.validation_result:
        validation_result = st.session_state.validation_result
        reconciliation_result = st.session_state.reconciliation_result

        # Create tabs
        if reconciliation_result:
            tabs = st.tabs(
                [
                    "📋 Summary",
                    "📑 Transactions",
                    "⚠️ Errors",
                    "🔄 Reconciliation",
                    "📥 Downloads",
                ]
            )
        else:
            tabs = st.tabs(
                ["📋 Summary", "📑 Transactions", "⚠️ Errors", "📥 Downloads"]
            )

        with tabs[0]:
            render_summary_tab(validation_result)

        with tabs[1]:
            render_transactions_tab(validation_result)

        with tabs[2]:
            render_errors_tab(validation_result)

        if reconciliation_result:
            with tabs[3]:
                render_reconciliation_tab(validation_result, reconciliation_result)
            with tabs[4]:
                render_downloads_tab(validation_result, reconciliation_result)
        else:
            with tabs[3]:
                render_downloads_tab(validation_result)

    else:
        # Welcome message
        st.info(
            """
            👋 **Welcome to the EDI 997 Auto-Validator!**

            To get started:
            1. Upload a `.997` or `.edi` file, or paste raw EDI content in the sidebar
            2. (Optional) Upload outbound reference data for reconciliation
            3. Click **Run Validation** to analyze the file

            You'll see:
            - ✅ Validation summary with accept/reject counts
            - 📊 Transaction-level details and status
            - ⚠️ Detailed error reports with codes and descriptions
            - 🔄 Reconciliation results (if outbound data provided)
            - 📥 Downloadable JSON and Markdown reports
            """
        )


if __name__ == "__main__":
    main()
