"""Carga el CSV comprimido de escala completa en una tabla separada para Power BI."""

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

from src.generate_full_scale_data import DEFAULT_OUTPUT, FIELDS, START_DATE


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load(source: Path, *, mode: str = "replace", allow_partial_replace: bool = False) -> dict:
    if mode not in {"replace", "sync"}:
        raise ValueError("Modo de carga inválido")
    manifest = source.with_name(source.name.removesuffix(".csv.gz") + ".manifest.json")
    metadata = json.loads(manifest.read_text(encoding="utf-8"))
    if sha256(source) != metadata["sha256"]:
        raise ValueError("El CSV comprimido no coincide con su manifiesto SHA-256")
    if metadata["rows"] <= 0 or metadata["columns"] != FIELDS or sum(month["actual"] for month in metadata["monthly"]) != metadata["rows"]:
        raise ValueError("El manifiesto no coincide con el esquema o el total mensual")
    if mode == "replace" and metadata["start"] != START_DATE.isoformat() and not allow_partial_replace:
        raise ValueError("El archivo no empieza en 2023-01-01; usá --mode sync para un lote incremental")

    connection = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "portability_db"),
        user=os.getenv("POSTGRES_USER", "data_user"),
        password=os.getenv("POSTGRES_PASSWORD", "data_password_dev"),
    )
    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute((BASE_DIR / "sql/full_scale_schema.sql").read_text(encoding="utf-8"))
                columns = ", ".join(FIELDS)
                if mode == "replace":
                    cursor.execute("TRUNCATE TABLE public.portability_cases_full")
                    destination = "public.portability_cases_full"
                else:
                    cursor.execute("CREATE TEMP TABLE portability_full_delta (LIKE public.portability_cases_full INCLUDING DEFAULTS) ON COMMIT DROP")
                    destination = "portability_full_delta"
                with gzip.open(source, "rt", encoding="utf-8", newline="") as stream:
                    cursor.copy_expert(f"COPY {destination} ({columns}) FROM STDIN WITH (FORMAT CSV, HEADER TRUE, NULL '')", stream)
                cursor.execute(f"SELECT count(*), min(received_at), max(received_at) FROM {destination}")
                count, first, last = cursor.fetchone()
                if count != metadata["rows"] or first.strftime("%Y-%m-%d %H:%M:%S") != metadata["firstReceived"] or last.strftime("%Y-%m-%d %H:%M:%S") != metadata["lastReceived"]:
                    raise ValueError("La carga no coincide con los totales y fechas del manifiesto")
                cursor.execute(f"SELECT to_char(received_date, 'YYYY-MM'), count(*) FROM {destination} GROUP BY 1")
                counts = dict(cursor.fetchall())
                if counts != {month["month"]: month["actual"] for month in metadata["monthly"]}:
                    raise ValueError("Los volúmenes mensuales cargados no coinciden con el manifiesto")
                if mode == "sync":
                    cursor.execute("SELECT count(*) FROM public.portability_cases_full")
                    before = cursor.fetchone()[0]
                    updates = ", ".join(f"{name} = EXCLUDED.{name}" for name in FIELDS if name != "case_id")
                    changed = " OR ".join(f"public.portability_cases_full.{name} IS DISTINCT FROM EXCLUDED.{name}" for name in FIELDS if name != "case_id")
                    cursor.execute(f"INSERT INTO public.portability_cases_full ({columns}) SELECT {columns} FROM portability_full_delta WHERE true ON CONFLICT (case_id) DO UPDATE SET {updates} WHERE {changed}")
                    affected = cursor.rowcount
                    cursor.execute("SELECT count(*) FROM public.portability_cases_full")
                    after = cursor.fetchone()[0]
                    inserted = after - before
                    updated = affected - inserted
                else:
                    inserted, updated = count, 0
        return {"rows": count, "inserted": inserted, "updated": updated, "firstReceived": first.isoformat(sep=" "), "lastReceived": last.isoformat(sep=" "), "months": len(counts)}
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--mode", choices=["replace", "sync"], default="replace")
    parser.add_argument("--allow-partial-replace", action="store_true", help="Solo para pruebas: permite reemplazar con una muestra parcial")
    args = parser.parse_args()
    result = load(args.input, mode=args.mode, allow_partial_replace=args.allow_partial_replace)
    print(f"Carga {args.mode} en public.portability_cases_full: {result['rows']:,} filas de entrada, {result['inserted']:,} nuevas, {result['updated']:,} actualizadas; {result['months']} meses ({result['firstReceived']} a {result['lastReceived']})")


if __name__ == "__main__":
    main()
