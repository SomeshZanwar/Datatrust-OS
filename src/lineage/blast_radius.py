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


def analyze_blast_radius(asset_name: str):
    engine = get_engine()

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

    with engine.connect() as conn:
        rows = conn.execute(query, {"asset_name": asset_name}).fetchall()

    return rows