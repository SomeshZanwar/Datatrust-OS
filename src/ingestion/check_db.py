from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import os


def main():
    load_dotenv()

    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT")
    db = os.getenv("POSTGRES_DB")

    engine = create_engine(
        f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    )

    with engine.connect() as conn:
        result = conn.execute(text("SELECT current_database();"))
        print("Connected to:", result.scalar())


if __name__ == "__main__":
    main()