"""
PCI DSS Continuous Monitoring Dashboard
Main Streamlit application entry point
"""

import streamlit as st
import json
import yaml
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Page config
st.set_page_config(
    page_title="PCI DSS Compliance Dashboard",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Data directory
DATA_DIR = Path(__file__).parent.parent / "data"


@st.cache_data
def load_requirements():
    """Load PCI DSS requirements from YAML."""
    with open(DATA_DIR / "pci_requirements.yaml") as f:
        return yaml.safe_load(f)["requirements"]


@st.cache_data
def load_control_status():
    """Load current control status."""
    with open(DATA_DIR / "simulated_control_status.json") as f:
        return json.load(f)


@st.cache_data
def load_findings():
    """Load all findings."""
    with open(DATA_DIR / "simulated_findings.json") as f:
        return json.load(f)["findings"]


@st.cache_data
def load_trend_data():
    """Load compliance trend data."""
    with open(DATA_DIR / "simulated_trend.json") as f:
        return json.load(f)


def get_requirement_name(req_id: str, requirements: list) -> str:
    """Get requirement name by ID."""
    for req in requirements:
        if req["id"] == req_id:
            return req["name"]
    return req_id


def severity_color(severity: str) -> str:
    """Return color for severity level."""
    colors = {
        "critical": "#dc3545",
        "high": "#fd7e14",
        "medium": "#ffc107",
        "low": "#28a745"
    }
    return colors.get(severity.lower(), "#6c757d")


def status_color(status: str) -> str:
    """Return color for status."""
    colors = {
        "pass": "#28a745",
        "fail": "#dc3545",
        "unknown": "#6c757d"
    }
    return colors.get(status.lower(), "#6c757d")


# Load data
requirements = load_requirements()
control_status = load_control_status()
findings = load_findings()
trend_data = load_trend_data()

# Sidebar
st.sidebar.title("🔒 PCI DSS 4.0")
st.sidebar.markdown("**Continuous Monitoring Dashboard**")
st.sidebar.divider()

page = st.sidebar.radio(
    "Navigation",
    ["Executive Summary", "Requirement Details", "Findings", "Trend Analysis"],
    index=0
)

st.sidebar.divider()
st.sidebar.markdown("**Last Updated**")
st.sidebar.markdown(f"📅 {control_status['snapshot_date']}")
st.sidebar.markdown(f"✅ {control_status['summary']['passing']} Passing")
st.sidebar.markdown(f"❌ {control_status['summary']['failing']} Failing")

# Main content
if page == "Executive Summary":
    st.title("📊 Executive Summary")
    st.markdown("Real-time PCI DSS 4.0 compliance posture for your cardholder data environment.")
    
    # Score card row
    col1, col2, col3, col4 = st.columns(4)
    
    score = control_status["summary"]["compliance_score"]
    with col1:
        st.metric(
            label="Compliance Score",
            value=f"{score:.0f}%",
            delta=f"+16.7%" if score > 33 else None,
            delta_color="normal"
        )
    
    with col2:
        st.metric(
            label="Requirements Passing",
            value=control_status["summary"]["passing"],
            delta="+1" if control_status["summary"]["passing"] > 2 else None
        )
    
    with col3:
        st.metric(
            label="Requirements Failing",
            value=control_status["summary"]["failing"],
            delta="-1" if control_status["summary"]["failing"] < 4 else None,
            delta_color="inverse"
        )
    
    open_findings = len([f for f in findings if f["status"] == "open"])
    critical_findings = len([f for f in findings if f["status"] == "open" and f["severity"] == "critical"])
    with col4:
        st.metric(
            label="Open Findings",
            value=open_findings,
            delta=f"{critical_findings} critical" if critical_findings > 0 else None,
            delta_color="off"
        )
    
    st.divider()
    
    # Requirement status cards
    st.subheader("📋 Requirement Status")
    
    cols = st.columns(3)
    for i, control in enumerate(control_status["controls"]):
        req_name = get_requirement_name(control["requirement_id"], requirements)
        with cols[i % 3]:
            status = control["status"]
            icon = "✅" if status == "pass" else "❌"
            color = "green" if status == "pass" else "red"
            
            st.markdown(f"""
            <div style="padding: 1rem; border-radius: 0.5rem; border: 1px solid #ddd; margin-bottom: 1rem; background: {'#d4edda' if status == 'pass' else '#f8d7da'};">
                <h4 style="margin: 0;">{icon} {control['requirement_id'].replace('_', ' ').upper()}</h4>
                <p style="margin: 0.5rem 0 0 0; font-weight: bold;">{req_name}</p>
                <p style="margin: 0.25rem 0 0 0; font-size: 0.9rem; color: #666;">{control['details']}</p>
                <p style="margin: 0.25rem 0 0 0; font-size: 0.8rem;">Findings: {control['finding_count']}</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.divider()
    
    # Quick trend chart
    st.subheader("📈 Compliance Trend (Last 16 Days)")
    df_trend = pd.DataFrame(trend_data["trend_data"])
    df_trend["date"] = pd.to_datetime(df_trend["date"])
    
    fig = px.line(
        df_trend, 
        x="date", 
        y="compliance_score",
        markers=True,
        labels={"compliance_score": "Compliance Score (%)", "date": "Date"}
    )
    fig.update_layout(
        yaxis_range=[0, 100],
        hovermode="x unified"
    )
    fig.update_traces(line_color="#0d6efd", marker_color="#0d6efd")
    st.plotly_chart(fig, use_container_width=True)

elif page == "Requirement Details":
    st.title("📋 Requirement Details")
    st.markdown("Drill into each PCI DSS requirement to see findings and evidence.")
    
    # Requirement selector
    req_options = {f"{r['id'].replace('_', ' ').upper()} - {r['name']}": r["id"] for r in requirements}
    selected_label = st.selectbox("Select Requirement", list(req_options.keys()))
    selected_req = req_options[selected_label]
    
    # Get control status for selected requirement
    control = next((c for c in control_status["controls"] if c["requirement_id"] == selected_req), None)
    req_info = next((r for r in requirements if r["id"] == selected_req), None)
    
    if control and req_info:
        st.divider()
        
        # Status header
        status = control["status"]
        icon = "✅" if status == "pass" else "❌"
        st.markdown(f"### {icon} Status: **{status.upper()}**")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Description:** {req_info['description']}")
            st.markdown(f"**Lab Source:** `{req_info['lab_source']}`")
            st.markdown(f"**AWS Service:** {req_info['aws_service']}")
        
        with col2:
            st.markdown(f"**Last Checked:** {control['last_checked']}")
            st.markdown(f"**Evidence Location:** `{control['evidence_location']}`")
            st.markdown(f"**Details:** {control['details']}")
        
        st.divider()
        
        # Findings for this requirement
        req_findings = [f for f in findings if f["requirement_id"] == selected_req]
        
        if req_findings:
            st.subheader(f"🔍 Findings ({len(req_findings)})")
            
            for finding in req_findings:
                severity = finding["severity"]
                status_icon = "🔴" if finding["status"] == "open" else "🟢"
                
                with st.expander(f"{status_icon} [{severity.upper()}] {finding['title']}"):
                    st.markdown(f"**ID:** {finding['id']}")
                    st.markdown(f"**Status:** {finding['status'].upper()}")
                    st.markdown(f"**Resource:** `{finding['resource_id']}`")
                    st.markdown(f"**Description:** {finding['description']}")
                    st.markdown(f"**Remediation:** {finding['remediation']}")
                    st.markdown(f"**Detected:** {finding['detected_at']}")
        else:
            st.success("No findings for this requirement. ✅")

elif page == "Findings":
    st.title("🔍 All Findings")
    st.markdown("View and filter all compliance findings across requirements.")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        severity_filter = st.multiselect(
            "Severity",
            ["critical", "high", "medium", "low"],
            default=["critical", "high", "medium", "low"]
        )
    
    with col2:
        status_filter = st.multiselect(
            "Status",
            ["open", "remediated"],
            default=["open"]
        )
    
    with col3:
        req_filter = st.multiselect(
            "Requirement",
            [r["id"] for r in requirements],
            default=[r["id"] for r in requirements]
        )
    
    # Filter findings
    filtered = [
        f for f in findings
        if f["severity"] in severity_filter
        and f["status"] in status_filter
        and f["requirement_id"] in req_filter
    ]
    
    st.divider()
    st.markdown(f"**Showing {len(filtered)} of {len(findings)} findings**")
    
    # Display as table
    if filtered:
        df = pd.DataFrame(filtered)
        df = df[["id", "severity", "status", "requirement_id", "title", "resource_id", "detected_at"]]
        df.columns = ["ID", "Severity", "Status", "Requirement", "Title", "Resource", "Detected"]
        
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Severity": st.column_config.TextColumn(width="small"),
                "Status": st.column_config.TextColumn(width="small"),
                "Requirement": st.column_config.TextColumn(width="small"),
            }
        )
        
        # Export button
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Export to CSV",
            data=csv,
            file_name=f"pci_findings_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No findings match the selected filters.")

elif page == "Trend Analysis":
    st.title("📈 Trend Analysis")
    st.markdown("Track compliance posture changes over time.")
    
    df_trend = pd.DataFrame(trend_data["trend_data"])
    df_trend["date"] = pd.to_datetime(df_trend["date"])
    
    # Main trend chart
    st.subheader("Compliance Score Over Time")
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df_trend["date"],
        y=df_trend["compliance_score"],
        mode="lines+markers",
        name="Compliance Score",
        line=dict(color="#0d6efd", width=3),
        marker=dict(size=8)
    ))
    
    # Add event annotations
    for event in trend_data["events"]:
        event_date = pd.to_datetime(event["date"])
        score_at_date = df_trend[df_trend["date"] == event_date]["compliance_score"].values
        if len(score_at_date) > 0:
            fig.add_annotation(
                x=event_date,
                y=score_at_date[0],
                text=event["event"],
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                ax=0,
                ay=-40,
                font=dict(size=10)
            )
    
    fig.update_layout(
        yaxis_range=[0, 100],
        yaxis_title="Compliance Score (%)",
        xaxis_title="Date",
        hovermode="x unified",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Pass/Fail breakdown
    st.subheader("Pass/Fail Breakdown Over Time")
    
    fig2 = go.Figure()
    
    fig2.add_trace(go.Bar(
        x=df_trend["date"],
        y=df_trend["passing"],
        name="Passing",
        marker_color="#28a745"
    ))
    
    fig2.add_trace(go.Bar(
        x=df_trend["date"],
        y=df_trend["failing"],
        name="Failing",
        marker_color="#dc3545"
    ))
    
    fig2.update_layout(
        barmode="stack",
        yaxis_title="Requirements",
        xaxis_title="Date",
        height=300
    )
    
    st.plotly_chart(fig2, use_container_width=True)
    
    st.divider()
    
    # Events log
    st.subheader("📝 Compliance Events")
    for event in trend_data["events"]:
        st.markdown(f"- **{event['date']}**: {event['event']}")

# Footer
st.sidebar.divider()
st.sidebar.markdown("---")
st.sidebar.markdown("Built for GRC Portfolio")
st.sidebar.markdown("[GitHub Repo](https://github.com/nelsonrosario89)")
