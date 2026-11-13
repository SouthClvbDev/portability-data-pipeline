from pathlib import Path
import argparse

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

DEFAULT_INPUT_FILE = (
    BASE_DIR
    / "data"
    / "sample"
    / "portability_cases.csv"
)

DEFAULT_OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "portability_cases_clean.csv"
)

FINAL_STATUSES = {
    "Aprobado",
    "Rechazado",
    "Anulado",
}


def transform_file(input_file: Path, output_file: Path) -> None:
    if not input_file.exists():
        raise FileNotFoundError(
            f"No existe el archivo de entrada: {input_file}"
        )

    df = pd.read_csv(input_file)

    df["received_at"] = pd.to_datetime(df["received_at"])
    df["closed_at"] = pd.to_datetime(df["closed_at"])

    # Fechas útiles para análisis temporal
    df["received_date"] = df["received_at"].dt.date
    df["received_year"] = df["received_at"].dt.year
    df["received_month"] = df["received_at"].dt.month
    df["received_month_name"] = df["received_at"].dt.strftime("%B")
    df["received_weekday"] = df["received_at"].dt.day_name()

    # Indicadores operativos
    df["is_closed"] = df["status"].isin(FINAL_STATUSES)
    df["is_pending"] = ~df["is_closed"]

    df["has_documentation_pending"] = (
        df["documentation_status"] == "Incompleta"
    )

    df["has_contact_pending"] = (
        df["contact_status"] == "Pendiente"
    )

    # Clasificación de cumplimiento de SLA
    df["sla_status"] = "No aplica"

    df.loc[
        df["resolution_hours"].notna()
        & (df["resolution_hours"] <= 48),
        "sla_status",
    ] = "Dentro de SLA"

    df.loc[
        df["resolution_hours"].notna()
        & (df["resolution_hours"] > 48),
        "sla_status",
    ] = "Fuera de SLA"

    ordered_columns = [
        "case_id",
        "received_at",
        "received_date",
        "received_year",
        "received_month",
        "received_month_name",
        "received_weekday",
        "closed_at",
        "status",
        "is_closed",
        "is_pending",
        "channel",
        "team",
        "documentation_status",
        "has_documentation_pending",
        "contact_status",
        "has_contact_pending",
        "rejection_reason",
        "cancellation_reason",
        "resolution_hours",
        "sla_status",
    ]

    df = df[ordered_columns]

    output_file.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig",
    )

    print(f"Archivo transformado correctamente: {output_file}")
    print(f"Registros procesados: {len(df)}")
    print(f"Columnas finales: {len(df.columns)}")
    print("\nDistribución de SLA:")
    print(df["sla_status"].value_counts())


def main():
    parser = argparse.ArgumentParser(
        description="Transforma datos de trámites de portabilidad."
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT_FILE,
        help="Archivo CSV de entrada.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_FILE,
        help="Archivo CSV de salida.",
    )

    args = parser.parse_args()

    transform_file(
        input_file=args.input,
        output_file=args.output,
    )


if __name__ == "__main__":
    main()