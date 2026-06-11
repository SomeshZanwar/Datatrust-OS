import os

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


st.set_page_config(
    page_title="DataTrust OS",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def get_engine():
    load_dotenv()
    return create_engine(
        f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:"
        f"{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:"
        f"{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
    )


@st.cache_data(ttl=60)
def load_dataframe(query: str) -> pd.DataFrame:
    return pd.read_sql(text(query), get_engine())


def inject_css():
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at 12% 8%, rgba(245, 158, 11, 0.18), transparent 28%),
                radial-gradient(circle at 88% 0%, rgba(59, 130, 246, 0.12), transparent 30%),
                linear-gradient(135deg, #050814 0%, #0b1220 48%, #111827 100%);
            color: #f8fafc;
        }

        [data-testid="stHeader"] { background: transparent; }

        .block-container {
            max-width: 1500px;
            padding-top: 2rem;
            padding-bottom: 4rem;
        }

        .hero {
            border: 1px solid rgba(148, 163, 184, 0.20);
            background:
                linear-gradient(135deg, rgba(15, 23, 42, 0.96), rgba(30, 41, 59, 0.78)),
                radial-gradient(circle at top right, rgba(245, 158, 11, 0.18), transparent 35%);
            box-shadow: 0 30px 90px rgba(0,0,0,0.42);
            border-radius: 30px;
            padding: 2rem 2.2rem;
            margin-bottom: 1.4rem;
        }

        .hero-grid {
            display: grid;
            grid-template-columns: 1.35fr 0.65fr;
            gap: 1.2rem;
            align-items: center;
        }

        .eyebrow {
            color: #f59e0b;
            font-size: 0.72rem;
            font-weight: 900;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            margin-bottom: 0.7rem;
        }

        .hero-title {
            font-size: 3.15rem;
            line-height: 1;
            font-weight: 950;
            color: #f8fafc;
            margin-bottom: 0.7rem;
        }

        .hero-subtitle {
            color: #cbd5e1;
            font-size: 1.02rem;
            line-height: 1.7;
            max-width: 900px;
        }

        .hero-panel {
            border-radius: 22px;
            padding: 1.1rem 1.2rem;
            background: rgba(2, 6, 23, 0.46);
            border: 1px solid rgba(148, 163, 184, 0.18);
        }

        .hero-panel-label {
            color: #94a3b8;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            font-weight: 800;
        }

        .hero-panel-value {
            margin-top: 0.4rem;
            font-size: 1.4rem;
            font-weight: 900;
            color: #fecaca;
        }

        .risk-banner {
            padding: 1.4rem;
            border-radius: 24px;
            margin-bottom: 1.2rem;
            border: 1px solid rgba(248,113,113,0.35);
            background: linear-gradient(135deg, rgba(127,29,29,0.55), rgba(69,10,10,0.35));
            box-shadow: 0 20px 60px rgba(0,0,0,0.35);
        }

        .risk-label {
            color:#fecaca;
            font-size:0.75rem;
            font-weight:900;
            letter-spacing:0.15em;
            text-transform:uppercase;
        }

        .risk-title {
            font-size:2rem;
            font-weight:900;
            color:white;
            margin-top:0.4rem;
        }

        .risk-text {
            color:#e2e8f0;
            margin-top:0.6rem;
            font-size:1rem;
        }

        .risk-meta {
            margin-top:1rem;
            display:flex;
            gap:2rem;
            flex-wrap:wrap;
            color:white;
            font-weight:700;
        }

        .metric-card {
            border-radius: 24px;
            padding: 1.2rem 1.25rem;
            background: linear-gradient(180deg, rgba(15, 23, 42, 0.94), rgba(15, 23, 42, 0.70));
            border: 1px solid rgba(148, 163, 184, 0.18);
            box-shadow: 0 18px 55px rgba(0,0,0,0.28);
            min-height: 142px;
            position: relative;
            overflow: hidden;
        }

        .metric-card::after {
            content: "";
            position: absolute;
            right: -40px;
            top: -40px;
            width: 120px;
            height: 120px;
            border-radius: 999px;
            background: rgba(245, 158, 11, 0.08);
        }

        .metric-label {
            color: #94a3b8;
            font-size: 0.72rem;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            margin-bottom: 0.65rem;
        }

        .metric-value {
            font-size: 2.05rem;
            font-weight: 950;
            color: #f8fafc;
            line-height: 1.05;
        }

        .metric-note {
            margin-top: 0.55rem;
            color: #cbd5e1;
            font-size: 0.86rem;
        }

        .section-shell {
            border-radius: 26px;
            border: 1px solid rgba(148, 163, 184, 0.16);
            background: rgba(15, 23, 42, 0.52);
            padding: 1.25rem;
            margin-top: 1rem;
            box-shadow: 0 18px 60px rgba(0,0,0,0.22);
        }

        .section-title {
            font-size: 1.25rem;
            font-weight: 900;
            color: #f8fafc;
            margin-bottom: 0.25rem;
        }

        .section-caption {
            color: #94a3b8;
            margin-bottom: 1rem;
            font-size: 0.92rem;
        }

        div[data-testid="stDataFrame"] {
            border-radius: 18px;
            overflow: hidden;
            border: 1px solid rgba(148, 163, 184, 0.14);
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.6rem;
            border-bottom: 1px solid rgba(148, 163, 184, 0.14);
        }

        .stTabs [data-baseweb="tab"] {
            background: rgba(15, 23, 42, 0.75);
            border-radius: 999px 999px 0 0;
            color: #cbd5e1;
            border: 1px solid rgba(148, 163, 184, 0.14);
            padding: 0.55rem 1.1rem;
        }

        .stTabs [aria-selected="true"] {
            color: #f8fafc;
            background: rgba(245, 158, 11, 0.22);
            border-color: rgba(245, 158, 11, 0.55);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, note: str):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str, caption: str):
    st.markdown(
        f"""
        <div class="section-title">{title}</div>
        <div class="section-caption">{caption}</div>
        """,
        unsafe_allow_html=True,
    )


def main():
    inject_css()

    trust_df = load_dataframe("""
        SELECT asset_name, trust_label, composite_trust_score, tests_passed,
               tests_failed, tests_total, run_timestamp
        FROM governance.latest_trust_scores
        ORDER BY asset_name;
    """)

    incidents_df = load_dataframe("""
        SELECT incident_id, severity, asset_name, incident_type, failure_count,
               status, detected_at, last_seen_at
        FROM governance.governance_incidents
        WHERE status = 'OPEN'
        ORDER BY
            CASE severity
                WHEN 'CRITICAL' THEN 1
                WHEN 'HIGH' THEN 2
                WHEN 'MEDIUM' THEN 3
                WHEN 'LOW' THEN 4
                ELSE 5
            END,
            last_seen_at DESC;
    """)

    summary_df = load_dataframe("""
        SELECT
            COUNT(*) FILTER (WHERE status = 'OPEN') AS open_incidents,
            COUNT(DISTINCT asset_name) FILTER (WHERE status = 'OPEN') AS affected_assets,
            ROUND(AVG(incident_age_hours) FILTER (WHERE status = 'OPEN'), 2) AS avg_open_age_hours
        FROM marts.fct_governance_incidents;
    """)

    zone_revenue_df = load_dataframe("""
        SELECT pickup_date, pickup_location_id, zone_name, borough, trip_count,
               ROUND(total_revenue::numeric, 2) AS total_revenue,
               trust_label, open_incident_count, highest_open_severity,
               data_reliability_status
        FROM marts.mart_zone_revenue
        ORDER BY trip_count DESC
        LIMIT 25;
    """)

    blast_radius_df = load_dataframe("""
        WITH RECURSIVE downstream_assets AS (
            SELECT parent_asset, child_asset, child_asset_type, relationship_type, 1 AS depth
            FROM lineage.asset_lineage
            WHERE parent_asset = 'staging.stg_yellow_trips'

            UNION ALL

            SELECT lineage.parent_asset, lineage.child_asset, lineage.child_asset_type,
                   lineage.relationship_type, downstream_assets.depth + 1 AS depth
            FROM lineage.asset_lineage AS lineage
            INNER JOIN downstream_assets
                ON lineage.parent_asset = downstream_assets.child_asset
        )
        SELECT depth, child_asset AS affected_asset, child_asset_type AS asset_type, relationship_type
        FROM downstream_assets
        ORDER BY depth, affected_asset;
    """)

    policy_df = load_dataframe("""
        SELECT DISTINCT
            'marts.mart_zone_revenue' AS asset_name,
            data_reliability_status AS policy_decision,
            trust_label,
            highest_open_severity,
            open_incident_count
        FROM marts.mart_zone_revenue;
    """)

    severity_df = load_dataframe("""
        SELECT
            severity,
            COUNT(*) AS incident_count
        FROM governance.governance_incidents
        WHERE status = 'OPEN'
        GROUP BY severity
        ORDER BY
            CASE severity
                WHEN 'CRITICAL' THEN 1
                WHEN 'HIGH' THEN 2
                WHEN 'MEDIUM' THEN 3
                WHEN 'LOW' THEN 4
                ELSE 5
            END;
    """)

    latest_trust = trust_df.iloc[0] if not trust_df.empty else None
    summary = summary_df.iloc[0] if not summary_df.empty else None
    policy = policy_df.iloc[0] if not policy_df.empty else None

    policy_decision = policy["policy_decision"] if policy is not None else "UNKNOWN"
    highest_severity = policy["highest_open_severity"] if policy is not None else "NONE"
    open_incidents = int(summary["open_incidents"]) if summary is not None else 0
    affected_assets = int(summary["affected_assets"]) if summary is not None else 0

    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-grid">
                <div>
                    <div class="eyebrow">Governance command center</div>
                    <div class="hero-title">DataTrust OS</div>
                    <div class="hero-subtitle">
                        A governance-aware analytics reliability layer that scores metric trust,
                        promotes quality failures into incidents, traces downstream blast radius,
                        and blocks unsafe business metrics before they reach decision-makers.
                    </div>
                </div>
                <div class="hero-panel">
                    <div class="hero-panel-label">Current metric consumption decision</div>
                    <div class="hero-panel-value">{policy_decision}</div>
                    <div class="metric-note">Applied to marts.mart_zone_revenue</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="risk-banner">
            <div class="risk-label">Governance Status</div>
            <div class="risk-title">{highest_severity}</div>
            <div class="risk-text">
                marts.mart_zone_revenue is currently blocked due to unresolved upstream governance incidents.
            </div>
            <div class="risk-meta">
                <span>Open Incidents: {open_incidents}</span>
                <span>Impacted Assets: {affected_assets}</span>
                <span>Decision: {policy_decision}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        metric_card(
            "Metric Reliability",
            latest_trust["trust_label"] if latest_trust is not None else "N/A",
            f"{latest_trust['composite_trust_score']:.1%}" if latest_trust is not None else "No score available",
        )

    with col2:
        metric_card(
            "Governance Decision",
            policy_decision,
            "Business metric consumption status",
        )

    with col3:
        metric_card(
            "Impacted Assets",
            str(affected_assets),
            "Downstream business assets",
        )

    with col4:
        metric_card(
            "Open Incidents",
            str(open_incidents),
            "Active governance issues",
        )

    tab1, tab2, tab3, tab4 = st.tabs(
        ["Command center", "Revenue reliability", "Blast radius", "Incident brief"]
    )

    with tab1:
        st.markdown('<div class="section-shell">', unsafe_allow_html=True)

        section_header(
            "Incident Severity Distribution",
            "Current unresolved governance issues by severity.",
        )

        severity_color_map = {
            "CRITICAL": "#ef4444",
            "HIGH": "#f97316",
            "MEDIUM": "#f59e0b",
            "LOW": "#22c55e",
        }

        fig = px.bar(
            severity_df,
            x="severity",
            y="incident_count",
            text="incident_count",
            color="severity",
            color_discrete_map=severity_color_map,
        )

        fig.update_traces(
            marker_line_width=0,
            textposition="outside",
            textfont=dict(
                color="#f8fafc",
                size=14,
            ),
        )

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=330,
            margin=dict(l=20, r=20, t=20, b=20),
            font=dict(color="#e2e8f0"),
            xaxis_title=None,
            yaxis_title=None,
            showlegend=False,
            bargap=0.38,
        )

        fig.update_xaxes(
            showgrid=False,
            linecolor="rgba(148,163,184,0.25)",
            tickfont=dict(color="#cbd5e1"),
        )

        fig.update_yaxes(
            showgrid=True,
            gridcolor="rgba(148,163,184,0.14)",
            zeroline=False,
            tickfont=dict(color="#94a3b8"),
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={"displayModeBar": False},
        )

        section_header(
            "Open governance incidents",
            "dbt test failures are promoted into severity-ranked governance incidents with operational status.",
        )

        st.dataframe(
            incidents_df,
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        section_header(
            "Latest trust scores",
            "Composite score derived from test pass rate, freshness, and ownership signals.",
        )

        st.dataframe(
            trust_df,
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="section-shell">', unsafe_allow_html=True)
        section_header(
            "Business metrics with reliability attached",
            "Revenue metrics are not shipped alone. Every row carries trust label, incidents, severity, and analyst-facing usability status.",
        )
        st.dataframe(
            zone_revenue_df,
            use_container_width=True,
            hide_index=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="section-shell">', unsafe_allow_html=True)
        section_header(
            "Downstream blast radius",
            "Shows which business-facing assets are impacted by degraded upstream data.",
        )
        st.dataframe(
            blast_radius_df,
            use_container_width=True,
            hide_index=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with tab4:
        st.markdown('<div class="section-shell">', unsafe_allow_html=True)
        section_header(
            "Governance incident brief",
            "A stakeholder-readable explanation of the current reliability failure and its downstream impact.",
        )

        if latest_trust is not None:
            st.markdown(
                f"""
                **Affected asset:** `{latest_trust['asset_name']}`  
                **Trust score:** `{latest_trust['composite_trust_score']:.4f}`  
                **Trust label:** `{latest_trust['trust_label']}`  
                **Policy decision:** `{policy_decision}`
                """
            )

        st.markdown("#### Open issues")
        for _, row in incidents_df.iterrows():
            st.markdown(
                f"- **{row['severity']}** — `{row['incident_type']}` "
                f"({int(row['failure_count'])} failing rows)"
            )

        st.markdown("#### Affected downstream assets")
        for _, row in blast_radius_df.iterrows():
            st.markdown(
                f"- `{row['affected_asset']}` through `{row['relationship_type']}`"
            )

        st.error(
            "Recommended action: investigate critical and high-severity upstream data quality failures before using dependent business metrics."
        )

        st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()