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


def fetch_downstream_assets(conn, asset_name: str):
    query = text(
        """
        WITH RECURSIVE downstream_assets AS (
            SELECT
                parent_asset,
                child_asset,
                child_asset_type,
                relationship_type,
                1 AS depth
            FROM lineage.asset_lineage
            WHERE parent_asset = :asset_name

            UNION ALL

            SELECT
                lineage.parent_asset,
                lineage.child_asset,
                lineage.child_asset_type,
                lineage.relationship_type,
                downstream_assets.depth + 1 AS depth
            FROM lineage.asset_lineage AS lineage
            INNER JOIN downstream_assets
                ON lineage.parent_asset = downstream_assets.child_asset
        )

        SELECT
            downstream_assets.depth,
            downstream_assets.child_asset,
            downstream_assets.child_asset_type,
            downstream_assets.relationship_type,

            mart.data_reliability_status,
            mart.trust_label,
            mart.open_incident_count,
            mart.highest_open_severity

        FROM downstream_assets
        LEFT JOIN (
            SELECT DISTINCT
                'marts.mart_zone_revenue' AS asset_name,
                data_reliability_status,
                trust_label,
                open_incident_count,
                highest_open_severity
            FROM marts.mart_zone_revenue
        ) AS mart
            ON downstream_assets.child_asset = mart.asset_name
        ORDER BY downstream_assets.depth, downstream_assets.child_asset;
        """
    )

    return conn.execute(query, {"asset_name": asset_name}).fetchall()


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

            downstream_assets = fetch_downstream_assets(
                conn,
                f"staging.{trust.asset_name}",
            )

            brief = {
                "asset_name": trust.asset_name,
                "trust_score": float(trust.composite_trust_score),
                "trust_label": trust.trust_label,
                "incidents": asset_incidents,
                "downstream_assets": downstream_assets,
                "policy_status": (
                    policy_rows[0].data_reliability_status
                    if policy_rows
                    else "UNKNOWN"
                ),
            }

            briefs.append(brief)

    return briefs