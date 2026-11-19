from pathlib import Path
import argparse
import os
from dotenv import load_dotenv

import pandas as pd
from sqlalchemy import create_engine, text, MetaData, Table, or_
from sqlalchemy.dialects.postgresql import insert


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

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

from sqlalchemy.engine import URL

DATABASE_URL = URL.create("postgresql+psycopg2", username=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=int(DB_PORT), database=DB_NAME)


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


def ensure_schema(engine):
    with engine.begin() as connection:
        connection.exec_driver_sql((BASE_DIR / "sql" / "schema.sql").read_text(encoding="utf-8"))


def insert_rows(df, connection, *, ignore_existing=False, update_existing=False):
    if ignore_existing and update_existing:
        raise ValueError("No se pueden ignorar y actualizar duplicados a la vez")
    table = Table("portability_cases", MetaData(), schema="public", autoload_with=connection)
    rows = df.astype(object).where(pd.notna(df), None).to_dict(orient="records")
    inserted = 0
    for offset in range(0, len(rows), 500):
        statement = insert(table).values(rows[offset:offset + 500])
        if ignore_existing:
            statement = statement.on_conflict_do_nothing(index_elements=["case_id"])
        elif update_existing:
            columns = [column.name for column in table.columns if column.name != "case_id"]
            statement = statement.on_conflict_do_update(
                index_elements=["case_id"],
                set_={name: statement.excluded[name] for name in columns},
                where=or_(*(table.c[name].is_distinct_from(statement.excluded[name]) for name in columns)),
            )
        inserted += connection.execute(statement).rowcount
    return inserted


def load_initial(df: pd.DataFrame, engine) -> None:
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE public.portability_cases"))
        insert_rows(df, connection)

    print("Carga inicial completada.")


def load_incremental(df: pd.DataFrame, engine) -> None:
    with engine.begin() as connection:
        inserted = insert_rows(df, connection, ignore_existing=True)
    if not inserted:
        print("No hay registros nuevos para cargar.")
        return
    print(f"Registros nuevos cargados: {inserted}")
    print(
        "Registros ignorados por estar repetidos: "
        f"{len(df) - inserted}"
    )


def load_sync(df: pd.DataFrame, engine) -> None:
    with engine.begin() as connection:
        before = connection.execute(text("SELECT COUNT(*) FROM public.portability_cases")).scalar_one()
        affected = insert_rows(df, connection, update_existing=True)
        after = connection.execute(text("SELECT COUNT(*) FROM public.portability_cases")).scalar_one()
    print(f"Sincronización completada: {after - before} nuevos, {affected - (after - before)} actualizados, {len(df) - affected} sin cambios.")


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
        choices=["initial", "append", "sync"],
        default="initial",
        help=(
            "initial reemplaza los datos. "
            "append agrega solo registros nuevos. "
            "sync inserta y actualiza solo los registros modificados."
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
    ensure_schema(engine)

    if args.mode == "initial":
        load_initial(df, engine)
    elif args.mode == "append":
        load_incremental(df, engine)
    else:
        load_sync(df, engine)

    show_total_records(engine)


if __name__ == "__main__":
    main()
