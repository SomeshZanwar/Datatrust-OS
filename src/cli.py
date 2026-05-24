import os

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from sqlalchemy import create_engine, text

app = typer.Typer()
console = Console()


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


@app.command("trust-score")
def trust_score():
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


if __name__ == "__main__":
    app()