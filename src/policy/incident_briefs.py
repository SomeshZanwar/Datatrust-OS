import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


def get_engine():
    load_dotenv()

    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT")
    db = os.getenv("POSTGRES_DB")

    return create_engine(
        f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    )


def generate_incident_briefs():
    engine = get_engine()

    trust_query = text(
        """
        SELECT
            asset_name,
            composite_trust_score,
            trust_label
        FROM governance.latest_trust_scores;
        """
    )

    incident_query = text(
        """
        SELECT
            asset_name,
            incident_type,
            severity,
            failure_count
        FROM governance.governance_incidents
        WHERE status = 'OPEN'
        ORDER BY
            CASE severity
                WHEN 'CRITICAL' THEN 1
                WHEN 'HIGH' THEN 2
                WHEN 'MEDIUM' THEN 3
                ELSE 4
            END;
        """
    )

    policy_query = text(
        """
        SELECT DISTINCT
            data_reliability_status,
            highest_open_severity
        FROM marts.mart_zone_revenue;
        """
    )

    with engine.connect() as conn:
        trust_rows = conn.execute(trust_query).fetchall()
        incident_rows = conn.execute(incident_query).fetchall()
        policy_rows = conn.execute(policy_query).fetchall()

    briefs = []

    for trust in trust_rows:
        asset_incidents = [
            incident
            for incident in incident_rows
            if incident.asset_name == trust.asset_name
        ]

        brief = {
            "asset_name": trust.asset_name,
            "trust_score": float(trust.composite_trust_score),
            "trust_label": trust.trust_label,
            "incidents": asset_incidents,
            "policy_status": (
                policy_rows[0].data_reliability_status
                if policy_rows
                else "UNKNOWN"
            ),
        }

        briefs.append(brief)

    return briefs