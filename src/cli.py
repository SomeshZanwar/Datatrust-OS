import os
import subprocess
import sys
from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from sqlalchemy import create_engine, text
from src.lineage.blast_radius import analyze_blast_radius

app = typer.Typer()
console = Console()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DBT_PROJECT_DIR = PROJECT_ROOT / "dbt_project"


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


def run_command(command: list[str], cwd: Path | None = None, allow_failure: bool = False):
    console.print(f"\n[bold]Running:[/bold] {' '.join(command)}")

    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        shell=False,
    )

    if result.returncode != 0 and not allow_failure:
        raise typer.Exit(result.returncode)

    return result.returncode


def render_trust_scores():
    engine = get_engine()

    query = text(
        """
        SELECT
            asset_name,
            trust_label,
            composite_trust_score,
            tests_passed,
            tests_failed,
            tests_total,
            run_timestamp
        FROM governance.latest_trust_scores
        ORDER BY asset_name;
        """
    )

    with engine.connect() as conn:
        rows = conn.execute(query).fetchall()

    table = Table(title="Latest Data Trust Scores")
    table.add_column("Asset")
    table.add_column("Label")
    table.add_column("Score")
    table.add_column("Tests")
    table.add_column("Run Timestamp")

    for row in rows:
        table.add_row(
            row.asset_name,
            row.trust_label,
            f"{row.composite_trust_score:.4f}",
            f"{row.tests_passed} passed / {row.tests_failed} failed / {row.tests_total} total",
            str(row.run_timestamp),
        )

    console.print(table)


@app.command("trust-score")
def trust_score():
    render_trust_scores()


@app.command("incidents")
def incidents():
    engine = get_engine()

    query = text(
        """
        SELECT
            incident_id,
            severity,
            asset_name,
            incident_type,
            failure_count,
            status,
            last_seen_at
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
        """
    )

    with engine.connect() as conn:
        rows = conn.execute(query).fetchall()

    table = Table(title="Open Governance Incidents")
    table.add_column("ID")
    table.add_column("Severity")
    table.add_column("Asset")
    table.add_column("Type")
    table.add_column("Failures")
    table.add_column("Status")
    table.add_column("Last Seen")

    for row in rows:
        table.add_row(
            str(row.incident_id),
            row.severity,
            row.asset_name,
            row.incident_type,
            str(row.failure_count),
            row.status,
            str(row.last_seen_at),
        )

    console.print(table)

@app.command("governance-summary")
def governance_summary():
    engine = get_engine()

    summary_query = text(
        """
        SELECT
            COUNT(*) FILTER (WHERE status = 'OPEN') AS open_incidents,
            COUNT(DISTINCT asset_name) FILTER (WHERE status = 'OPEN') AS affected_assets,
            ROUND(
    AVG(incident_age_hours) FILTER (WHERE status = 'OPEN'),
    2
) AS avg_open_age_hours
        FROM marts.fct_governance_incidents;
        """
    )

    severity_query = text(
        """
        SELECT
            severity,
            COUNT(*) AS incident_count
        FROM marts.fct_governance_incidents
        WHERE status = 'OPEN'
        GROUP BY severity, severity_rank
        ORDER BY severity_rank;
        """
    )

    with engine.connect() as conn:
        summary = conn.execute(summary_query).one()
        severity_rows = conn.execute(severity_query).fetchall()

    console.print("\n[bold]Governance Health Summary[/bold]")
    console.print(f"Open incidents: {summary.open_incidents}")
    console.print(f"Affected assets: {summary.affected_assets}")
    console.print(f"Average open age: {summary.avg_open_age_hours} hours")

    table = Table(title="Open Incidents by Severity")
    table.add_column("Severity")
    table.add_column("Count")

    for row in severity_rows:
        table.add_row(row.severity, str(row.incident_count))

    console.print(table)

@app.command("zone-revenue")
def zone_revenue(limit: int = 10):
    engine = get_engine()

    query = text(
        """
        SELECT
            pickup_date,
            pickup_location_id,
            trip_count,
            ROUND(total_revenue::numeric, 2) AS total_revenue,
            ROUND(avg_fare::numeric, 2) AS avg_fare,
            ROUND(avg_trip_distance::numeric, 2) AS avg_trip_distance,
            trust_label,
            open_incident_count,
            highest_open_severity,
            data_reliability_status
        FROM marts.mart_zone_revenue
        ORDER BY trip_count DESC
        LIMIT :limit;
        """
    )

    with engine.connect() as conn:
        rows = conn.execute(query, {"limit": limit}).fetchall()

    table = Table(title="Zone Revenue with Data Reliability Context")
    table.add_column("Date")
    table.add_column("Pickup Zone")
    table.add_column("Trips")
    table.add_column("Revenue")
    table.add_column("Avg Fare")
    table.add_column("Avg Distance")
    table.add_column("Trust")
    table.add_column("Incidents")
    table.add_column("Highest Severity")
    table.add_column("Reliability Status")

    for row in rows:
        table.add_row(
            str(row.pickup_date),
            str(row.pickup_location_id),
            str(row.trip_count),
            f"${row.total_revenue}",
            f"${row.avg_fare}",
            str(row.avg_trip_distance),
            row.trust_label,
            str(row.open_incident_count),
            row.highest_open_severity,
            row.data_reliability_status,
        )

    console.print(table)

@app.command("blast-radius")
def blast_radius(asset_name: str):
    rows = analyze_blast_radius(asset_name)

    table = Table(title=f"Blast Radius — {asset_name}")
    table.add_column("Depth")
    table.add_column("Affected Asset")
    table.add_column("Type")
    table.add_column("Relationship")
    table.add_column("Trust")
    table.add_column("Open Incidents")
    table.add_column("Highest Severity")
    table.add_column("Reliability Status")

    for row in rows:
        table.add_row(
            str(row.depth),
            row.child_asset,
            row.child_asset_type,
            row.relationship_type,
            row.trust_label or "N/A",
            str(row.open_incident_count or 0),
            row.highest_open_severity or "N/A",
            row.data_reliability_status or "N/A",
        )

    console.print(table)

@app.command("run-pipeline")
def run_pipeline():
    run_command(
        ["dbt", "run", "--select", "stg_yellow_trips", "--profiles-dir", "."],
        cwd=DBT_PROJECT_DIR,
    )

    run_command(
        ["dbt", "test", "--select", "stg_yellow_trips", "--profiles-dir", "."],
        cwd=DBT_PROJECT_DIR,
        allow_failure=True,
    )

    run_command([sys.executable, "src\\trust\\scorer.py"], cwd=PROJECT_ROOT)

    run_command([sys.executable, "src\\policy\\incident_reporter.py"], cwd=PROJECT_ROOT)

    render_trust_scores()


if __name__ == "__main__":
    app()