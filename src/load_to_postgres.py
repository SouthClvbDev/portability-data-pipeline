from pathlib import Path
import argparse
import os

import pandas as pd
from sqlalchemy import create_engine, text


BASE_DIR = Path(__file__).resolve().parents[1]

DEFAULT_INPUT_FILE = (
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


def load_dataframe(input_file: Path) -> pd.DataFrame:
    if not input_file.exists():
        raise FileNotFoundError(
            f"No existe el archivo transformado: {input_file}"
        )

    print(f"Leyendo archivo transformado: {input_file}")
    df = pd.read_csv(input_file)

    print(f"Registros leídos: {len(df)}")

    if "case_id" not in df.columns:
        raise ValueError("El archivo no contiene la columna case_id.")

    if df["case_id"].duplicated().any():
        raise ValueError("El archivo contiene case_id duplicados.")

    return df


def create_database_engine():
    engine = create_engine(DATABASE_URL)

    with engine.begin() as connection:
        connection.execute(text("SELECT 1"))

    print("Conexión a PostgreSQL exitosa.")

    return engine


def load_initial(df: pd.DataFrame, engine) -> None:
    with engine.begin() as connection:
        table_exists = connection.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_name = 'portability_cases'
                )
                """
            )
        ).scalar()

        if table_exists:
            connection.execute(
                text("TRUNCATE TABLE public.portability_cases")
            )
            print("Tabla existente vaciada correctamente.")

    df.to_sql(
        "portability_cases",
        con=engine,
        if_exists="append" if table_exists else "replace",
        index=False,
        schema="public",
    )

    print("Carga inicial completada.")


def load_incremental(df: pd.DataFrame, engine) -> None:
    with engine.connect() as connection:
        table_exists = connection.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_name = 'portability_cases'
                )
                """
            )
        ).scalar()

        if not table_exists:
            raise RuntimeError(
                "La tabla portability_cases no existe. "
                "Ejecutá primero una carga inicial."
            )

        existing_ids = pd.read_sql(
            text("SELECT case_id FROM public.portability_cases"),
            connection,
        )

    existing_case_ids = set(existing_ids["case_id"])

    new_rows = df[
        ~df["case_id"].isin(existing_case_ids)
    ].copy()

    if new_rows.empty:
        print("No hay registros nuevos para cargar.")
        return

    new_rows.to_sql(
        "portability_cases",
        con=engine,
        if_exists="append",
        index=False,
        schema="public",
    )

    print(f"Registros nuevos cargados: {len(new_rows)}")
    print(
        "Registros ignorados por estar repetidos: "
        f"{len(df) - len(new_rows)}"
    )


def show_total_records(engine) -> None:
    with engine.connect() as connection:
        total_records = connection.execute(
            text("SELECT COUNT(*) FROM public.portability_cases")
        ).scalar()

    print(f"Registros totales en PostgreSQL: {total_records}")


def main():
    parser = argparse.ArgumentParser(
        description="Carga datos de portabilidad en PostgreSQL."
    )

    parser.add_argument(
        "--mode",
        choices=["initial", "append"],
        default="initial",
        help=(
            "initial reemplaza los datos. "
            "append agrega solo registros nuevos."
        ),
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT_FILE,
        help="Archivo CSV procesado que se desea cargar.",
    )

    args = parser.parse_args()

    df = load_dataframe(args.input)
    engine = create_database_engine()

    if args.mode == "initial":
        load_initial(df, engine)
    else:
        load_incremental(df, engine)

    show_total_records(engine)


if __name__ == "__main__":
    main()