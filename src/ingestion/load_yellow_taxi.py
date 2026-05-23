from pathlib import Path
from datetime import datetime, timezone
import hashlib
import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


TLC_YELLOW_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2023-01.parquet"
LOCAL_FILE = Path("data/raw/yellow_tripdata_2023-01.parquet")
TABLE_NAME = "yellow_trips"


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


def file_hash(path: Path) -> str:
    hasher = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


def download_file() -> None:
    LOCAL_FILE.parent.mkdir(parents=True, exist_ok=True)

    if LOCAL_FILE.exists():
        print(f"File already exists: {LOCAL_FILE}")
        return

    print(f"Downloading: {TLC_YELLOW_URL}")
    df = pd.read_parquet(TLC_YELLOW_URL)
    df.to_parquet(LOCAL_FILE, index=False)
    print(f"Saved to: {LOCAL_FILE}")


def load_to_postgres() -> None:
    engine = get_engine()

    print(f"Reading local file: {LOCAL_FILE}")
    df = pd.read_parquet(LOCAL_FILE)

    ingested_at = datetime.now(timezone.utc)
    source_file = LOCAL_FILE.name
    source_hash = file_hash(LOCAL_FILE)

    df["_ingested_at"] = ingested_at
    df["_source_file"] = source_file
    df["_source_file_hash"] = source_hash

    print(f"Rows to load: {len(df):,}")
    print(f"Columns to load: {len(df.columns):,}")

    df.to_sql(
        TABLE_NAME,
        engine,
        schema="raw",
        if_exists="replace",
        index=False,
        chunksize=50_000,
        method="multi",
    )

    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM raw.yellow_trips;")).scalar()
        min_date, max_date = conn.execute(
            text(
                """
                SELECT
                    MIN(tpep_pickup_datetime),
                    MAX(tpep_pickup_datetime)
                FROM raw.yellow_trips;
                """
            )
        ).one()

    print("Load complete.")
    print(f"Postgres table: raw.{TABLE_NAME}")
    print(f"Loaded rows: {count:,}")
    print(f"Pickup date range: {min_date} to {max_date}")


def main():
    download_file()
    load_to_postgres()


if __name__ == "__main__":
    main()