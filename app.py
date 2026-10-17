import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config


# ============================================================
# PROJECT PATHS AND IMPORTS
# ============================================================

CURRENT_DIR = Path(__file__).resolve().parent

PROJECT_DIR = (
    CURRENT_DIR.parent
    if CURRENT_DIR.name.lower() == ".venv"
    else CURRENT_DIR
)

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from fraud_detector import FraudDetector
from ai_assistant import generate_investigation_report

from investigation_history import (
    initialize_database,
    save_investigation,
    get_investigation_history,
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="TraceGuard AI",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ TraceGuard AI")

st.caption(
    "Graph-powered financial investigation with "
    "explainable risk indicators and local AI assistance."
)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

try:
    initialize_database()
except Exception as error:
    st.warning(
        f"Investigation history initialization failed: {error}"
    )


# ============================================================
# GRAPH VISUALIZATION
# ============================================================

def display_investigation_graph(
    graph_data,
    selected_transaction=None,
):
    """Display account, device, and transaction relationships."""

    nodes = []
    edges = []

    added_nodes = set()
    added_edges = set()

    account_color = "#168BFF"
    device_color = "#F5A623"
    transaction_color = "#9B59B6"
    selected_color = "#F04452"

    def add_node(
        node_id,
        label,
        color,
        shape="dot",
        size=32,
    ):
        node_id = str(node_id)

        if node_id in added_nodes:
            return

        nodes.append(
            Node(
                id=node_id,
                label=label,
                title=label.replace("\n", " "),
                color=color,
                shape=shape,
                size=size,
                font={
                    "size": 18,
                    "face": "Arial",
                },
                borderWidth=2,
                physics=True,
            )
        )

        added_nodes.add(node_id)

    def add_edge(source, target, label):
        source = str(source)
        target = str(target)

        edge_key = (source, target, label)

        if edge_key in added_edges:
            return

        # Hide relationship text on graph lines.
        # Hover over a line to see the relationship.
        edges.append(
            Edge(
                source=source,
                target=target,
                label="",
                title=label,
                color="#9AA9B8",
                width=2,
                arrows="to",
                smooth={
                    "enabled": True,
                    "type": "curvedCW",
                    "roundness": 0.2,
                },
            )
        )

        added_edges.add(edge_key)

    # --------------------------------------------------------
    # ACCOUNT-DEVICE RELATIONSHIPS
    # --------------------------------------------------------

    for relation in graph_data.get(
        "account_device_links", []
    ):
        account_id = relation.get("account_id")
        device_id = relation.get("device_id")

        if account_id is None or device_id is None:
            continue

        add_node(
            f"account:{account_id}",
            f"Account\n{account_id}",
            account_color,
            "dot",
            34,
        )

        add_node(
            f"device:{device_id}",
            f"Device\n{device_id}",
            device_color,
            "diamond",
            38,
        )

        add_edge(
            f"account:{account_id}",
            f"device:{device_id}",
            "USES DEVICE",
        )

    # --------------------------------------------------------
    # ACCOUNT-TRANSACTION RELATIONSHIPS
    # --------------------------------------------------------

    for transaction in graph_data.get(
        "transactions", []
    ):
        transaction_id = transaction.get("transaction_id")
        account_id = transaction.get("account_id")

        if transaction_id is None or account_id is None:
            continue

        selected = (
            selected_transaction is not None
            and str(transaction_id)
            == str(selected_transaction)
        )

        node_color = (
            selected_color
            if selected
            else transaction_color
        )

        node_size = 40 if selected else 30

        add_node(
            f"account:{account_id}",
            f"Account\n{account_id}",
            account_color,
            "dot",
            34,
        )

        add_node(
            f"transaction:{transaction_id}",
            f"Transaction\n{transaction_id}",
            node_color,
            "box",
            node_size,
        )

        add_edge(
            f"account:{account_id}",
            f"transaction:{transaction_id}",
            "HAS TRANSACTION",
        )

    if not nodes:
        st.info("No graph relationships are available.")
        return

    st.markdown(
        """
        **Graph Legend**

        🔵 Account &nbsp;&nbsp;
        🟠 Device &nbsp;&nbsp;
        🟣 Transaction &nbsp;&nbsp;
        🔴 Selected transaction
        """
    )

    st.caption(
        "Hover over connecting lines to see relationship details. "
        "Drag nodes to explore the graph."
    )

    # --------------------------------------------------------
    # GRAPH CONFIGURATION
    # --------------------------------------------------------

    config = Config(
        width=1200,
        height=850,
        directed=True,
        physics=True,
        hierarchical=False,
        nodeHighlightBehavior=True,
        highlightColor="#F7A7A6",
        collapsible=False,
    )

    try:
        selected_node = agraph(
            nodes=nodes,
            edges=edges,
            config=config,
        )

        if selected_node:
            st.caption(
                f"Selected graph node: {selected_node}"
            )

    except Exception as error:
        st.error(
            f"Graph rendering failed: {error}"
        )
        return

    st.caption(
        "Shared devices and transaction relationships are "
        "investigative leads, not proof of fraud."
    )


# ============================================================
# LOAD INVESTIGATION DATA
# ============================================================

try:
    detector = FraudDetector()

    investigations = detector.investigate()
    shared_devices = detector.get_shared_devices()
    graph_data = detector.get_graph_data()

    df = pd.DataFrame(investigations)

    if df.empty:
        st.warning("No transactions were found.")
        st.stop()

    if "transaction_id" not in df.columns:
        st.error(
            "Investigation data does not contain transaction_id."
        )
        st.stop()

    df["transaction_id"] = (
        df["transaction_id"].astype(str)
    )

    # --------------------------------------------------------
    # DASHBOARD METRICS
    # --------------------------------------------------------

    high_risk = int(
        (df["risk_level"] == "HIGH").sum()
    )

    medium_risk = int(
        (df["risk_level"] == "MEDIUM").sum()
    )

    low_risk = int(
        (df["risk_level"] == "LOW").sum()
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Transactions", len(df))
    col2.metric("High Risk", high_risk)
    col3.metric("Medium Risk", medium_risk)
    col4.metric("Low Risk", low_risk)

    st.divider()

    # --------------------------------------------------------
    # DASHBOARD TABS
    # --------------------------------------------------------

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "📊 Risk Analysis",
            "🔗 Shared Devices",
            "🕸️ Graph Investigation",
            "🤖 AI Assistant",
            "🕒 Investigation History",
        ]
    )

    # ========================================================
    # TAB 1: RISK ANALYSIS
    # ========================================================

    with tab1:
        st.subheader("Transaction Risk Analysis")

        col1, col2 = st.columns(2)

        with col1:
            search_id = st.text_input(
                "Search Transaction ID",
                placeholder="Enter TXN001...",
            )

        with col2:
            risk_filter = st.selectbox(
                "Filter by Risk Level",
                ["ALL", "HIGH", "MEDIUM", "LOW"],
            )

        filtered_df = df.copy()

        if search_id:
            filtered_df = filtered_df[
                filtered_df["transaction_id"].str.contains(
                    search_id,
                    case=False,
                    na=False,
                    regex=False,
                )
            ]

        if risk_filter != "ALL":
            filtered_df = filtered_df[
                filtered_df["risk_level"] == risk_filter
            ]

        st.caption(
            f"Matching transactions: {len(filtered_df)}"
        )

        st.dataframe(
            filtered_df,
            width="stretch",
            hide_index=True,
        )

        st.download_button(
            "📥 Download Filtered Results (CSV)",
            data=filtered_df.to_csv(
                index=False
            ).encode("utf-8"),
            file_name="traceguard_filtered.csv",
            mime="text/csv",
            key="download_filtered",
        )

        st.download_button(
            "📥 Download All Investigations (CSV)",
            data=df.to_csv(
                index=False
            ).encode("utf-8"),
            file_name="traceguard_all_investigations.csv",
            mime="text/csv",
            key="download_all",
        )

    # ========================================================
    # TAB 2: SHARED DEVICES
    # ========================================================

    with tab2:
        st.subheader("🔗 Shared Device Investigation")

        if shared_devices:
            shared_df = pd.DataFrame(shared_devices)

            st.dataframe(
                shared_df,
                width="stretch",
                hide_index=True,
            )

            st.download_button(
                "📥 Download Shared Devices (CSV)",
                data=shared_df.to_csv(
                    index=False
                ).encode("utf-8"),
                file_name="traceguard_shared_devices.csv",
                mime="text/csv",
                key="download_shared",
            )

        else:
            st.info(
                "No shared-device relationships were found."
            )

        st.caption(
            "Sharing a device is an investigative lead, "
            "not proof of fraud."
        )

    # ========================================================
    # TAB 3: GRAPH INVESTIGATION
    # ========================================================

    with tab3:
        st.subheader(
            "🕸️ Account, Device and Transaction Graph"
        )

        transaction_ids = (
            df["transaction_id"]
            .dropna()
            .unique()
            .tolist()
        )

        graph_selection = st.selectbox(
            "Highlight a transaction",
            ["ALL"] + transaction_ids,
            key="graph_transaction",
        )

        display_investigation_graph(
            graph_data,
            selected_transaction=(
                None
                if graph_selection == "ALL"
                else graph_selection
            ),
        )

    # ========================================================
    # TAB 4: AI ASSISTANT
    # ========================================================

    with tab4:
        st.subheader("🤖 AI Investigation Assistant")

        transaction_ids = (
            df["transaction_id"]
            .dropna()
            .unique()
            .tolist()
        )

        if transaction_ids:
            selected = st.selectbox(
                "Select transaction to investigate",
                transaction_ids,
                key="ai_selected_transaction",
            )

            selected_rows = df[
                df["transaction_id"] == selected
            ]

            if selected_rows.empty:
                st.warning(
                    "The selected transaction was not found."
                )
            else:
                report = selected_rows.iloc[0]

                risk_score = int(
                    report.get("risk_score", 0)
                )

                risk_level = str(
                    report.get("risk_level", "UNKNOWN")
                )

                reasons = report.get("reasons", [])

                if isinstance(reasons, str):
                    reasons = [reasons] if reasons else []
                elif not isinstance(reasons, list):
                    reasons = []

                st.write(
                    f"**Transaction ID:** {selected}"
                )

                st.write(
                    f"**Risk level:** {risk_level}"
                )

                st.progress(
                    max(0, min(risk_score, 100)) / 100
                )

                st.write(
                    f"**Risk score:** {risk_score}/100"
                )

                st.write("**Investigation reasons:**")

                for reason in reasons:
                    st.write(f"- {reason}")

                if st.button(
                    "Generate AI Investigation Report",
                    type="primary",
                    key="generate_ai_report",
                ):
                    with st.spinner(
                        "Generating report with Ollama..."
                    ):
                        try:
                            ai_report = (
                                generate_investigation_report(
                                    transaction=report.to_dict(),
                                    shared_devices=shared_devices,
                                )
                            )

                            ai_report = str(ai_report)

                            st.session_state[
                                "latest_ai_report"
                            ] = ai_report

                            st.session_state[
                                "latest_ai_transaction"
                            ] = str(selected)

                            try:
                                record_id = save_investigation(
                                    transaction_id=selected,
                                    risk_score=risk_score,
                                    risk_level=risk_level,
                                    reasons=reasons,
                                    ai_report=ai_report,
                                )

                                st.session_state[
                                    "latest_history_id"
                                ] = record_id

                                st.success(
                                    "Investigation saved successfully. "
                                    f"Record ID: {record_id}"
                                )

                            except Exception as error:
                                st.warning(
                                    "The AI report was generated, "
                                    "but saving history failed: "
                                    f"{error}"
                                )

                        except Exception as error:
                            st.error(
                                "Unable to generate the AI report: "
                                f"{error}"
                            )

                last_report = st.session_state.get(
                    "latest_ai_report"
                )

                last_transaction = st.session_state.get(
                    "latest_ai_transaction"
                )

                if (
                    last_report
                    and last_transaction == str(selected)
                ):
                    st.markdown(
                        "### 📋 AI Investigation Report"
                    )

                    st.markdown(last_report)

                    safe_id = "".join(
                        character
                        if character.isalnum()
                        or character in "-_"
                        else "_"
                        for character in str(selected)
                    )

                    st.download_button(
                        "📄 Download AI Investigation Report",
                        data=last_report,
                        file_name=(
                            f"traceguard_report_{safe_id}.txt"
                        ),
                        mime="text/plain",
                        key="download_latest_ai_report",
                    )

        else:
            st.info(
                "No transactions are available for investigation."
            )

    # ========================================================
    # TAB 5: INVESTIGATION HISTORY
    # ========================================================

    with tab5:
        st.subheader("🕒 Investigation History")

        try:
            history = get_investigation_history(
                limit=500
            )

            if history:
                history_df = pd.DataFrame(history)
                display_df = history_df.copy()

                if "reasons" in display_df.columns:
                    display_df["reasons"] = (
                        display_df["reasons"].apply(
                            lambda value: (
                                "; ".join(map(str, value))
                                if isinstance(value, list)
                                else str(value)
                            )
                        )
                    )

                visible_columns = [
                    column
                    for column in [
                        "id",
                        "transaction_id",
                        "risk_score",
                        "risk_level",
                        "reasons",
                        "investigated_at",
                    ]
                    if column in display_df.columns
                ]

                st.dataframe(
                    display_df[visible_columns],
                    width="stretch",
                    hide_index=True,
                )

                st.download_button(
                    "📥 Download Investigation History (CSV)",
                    data=display_df.to_csv(
                        index=False
                    ).encode("utf-8"),
                    file_name="traceguard_history.csv",
                    mime="text/csv",
                    key="download_history",
                )

                saved_reports = [
                    item
                    for item in history
                    if item.get("ai_report")
                ]

                if saved_reports:
                    st.subheader("📋 Saved AI Reports")

                    selected_record_id = st.selectbox(
                        "Select a saved report",
                        options=[
                            item["id"]
                            for item in saved_reports
                        ],
                        format_func=lambda record_id: next(
                            (
                                f"Record {item['id']} — "
                                f"{item['transaction_id']}"
                                for item in saved_reports
                                if item["id"] == record_id
                            ),
                            str(record_id),
                        ),
                        key="saved_report_selector",
                    )

                    selected_record = next(
                        item
                        for item in saved_reports
                        if item["id"] == selected_record_id
                    )

                    st.markdown(
                        selected_record["ai_report"]
                    )

                    safe_transaction_id = "".join(
                        character
                        if character.isalnum()
                        or character in "-_"
                        else "_"
                        for character in str(
                            selected_record["transaction_id"]
                        )
                    )

                    st.download_button(
                        "📄 Download Saved AI Report",
                        data=selected_record["ai_report"],
                        file_name=(
                            "traceguard_saved_report_"
                            f"{safe_transaction_id}.txt"
                        ),
                        mime="text/plain",
                        key="download_saved_ai_report",
                    )

            else:
                st.info(
                    "No investigation history yet. "
                    "Generate an AI report to save your first record."
                )

        except Exception as error:
            st.error(
                f"Unable to load investigation history: {error}"
            )


# ============================================================
# ERROR HANDLING
# ============================================================

except Exception as error:
    st.error(
        "Unable to load the TraceGuard AI dashboard."
    )

    with st.expander("Technical error details"):
        st.exception(error)