from pathlib import Path
import os

import pandas as pd
from sqlalchemy import create_engine, text


BASE_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "portability_cases_clean.csv"
)

DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "portability_db")
DB_USER = os.getenv("POSTGRES_USER", "data_user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "data_password_dev")

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"No existe el archivo transformado: {INPUT_FILE}"
        )

    print("Leyendo archivo transformado...")
    df = pd.read_csv(INPUT_FILE)

    print(f"Registros leídos: {len(df)}")

    engine = create_engine(DATABASE_URL)

    with engine.begin() as connection:
        connection.execute(text("SELECT 1"))

    print("Conexión a PostgreSQL exitosa.")

    df.to_sql(
        "portability_cases",
        con=engine,
        if_exists="replace",
        index=False,
        schema="public",
    )

    print("Tabla portability_cases cargada correctamente.")

    with engine.connect() as connection:
        total_records = connection.execute(
            text("SELECT COUNT(*) FROM portability_cases")
        ).scalar()

    print(f"Registros en PostgreSQL: {total_records}")


if __name__ == "__main__":
    main()