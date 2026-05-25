import os
import subprocess
import sys
from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from sqlalchemy import create_engine, text

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

    render_trust_scores()


if __name__ == "__main__":
    app()