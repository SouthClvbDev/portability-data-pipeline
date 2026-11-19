from pathlib import Path
import argparse
import sys

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]
INPUT_FILE = BASE_DIR / "data" / "sample" / "portability_cases.csv"

REQUIRED_COLUMNS = [
    "case_id",
    "received_at",
    "closed_at",
    "status",
    "channel",
    "team",
    "documentation_status",
    "contact_status",
    "rejection_reason",
    "cancellation_reason",
    "resolution_hours",
]

VALID_STATUSES = {
    "Recibido",
    "En análisis",
    "Pendiente documentación",
    "Pendiente contacto",
    "Aprobado",
    "Rechazado",
    "Anulado",
}

FINAL_STATUSES = {
    "Aprobado",
    "Rechazado",
    "Anulado",
}

OPEN_STATUSES = {
    "Recibido",
    "En análisis",
    "Pendiente documentación",
    "Pendiente contacto",
}


def add_error(errors, message):
    errors.append(message)


def main():
    parser = argparse.ArgumentParser(description="Valida un lote de portabilidad.")
    parser.add_argument("--input", type=Path, default=INPUT_FILE)
    args = parser.parse_args()
    errors = []

    if not args.input.exists():
        print(f"ERROR: no existe el archivo {args.input}")
        sys.exit(1)

    df = pd.read_csv(args.input)

    missing_columns = [
        column for column in REQUIRED_COLUMNS if column not in df.columns
    ]

    if missing_columns:
        add_error(
            errors,
            f"Faltan columnas obligatorias: {missing_columns}",
        )
        print_errors(errors)
        sys.exit(1)

    df["received_at"] = pd.to_datetime(
        df["received_at"],
        errors="coerce",
    )

    df["closed_at"] = pd.to_datetime(
        df["closed_at"],
        errors="coerce",
    )

    # 1. Identificador obligatorio
    if df["case_id"].isna().any():
        add_error(errors, "Existen casos sin case_id.")

    # 2. Identificadores duplicados
    duplicated_ids = df[df["case_id"].duplicated()]["case_id"].tolist()

    if duplicated_ids:
        add_error(
            errors,
            f"Existen case_id duplicados: {duplicated_ids[:10]}",
        )

    # 3. Fechas obligatorias
    if df["received_at"].isna().any():
        add_error(errors, "Existen casos con received_at inválido o vacío.")

    # 4. Estados válidos
    invalid_statuses = set(df["status"].dropna()) - VALID_STATUSES

    if invalid_statuses:
        add_error(
            errors,
            f"Existen estados inválidos: {invalid_statuses}",
        )

    # 5. closed_at no puede ser anterior a received_at
    invalid_dates = df[
        df["closed_at"].notna()
        & df["received_at"].notna()
        & (df["closed_at"] < df["received_at"])
    ]

    if not invalid_dates.empty:
        add_error(
            errors,
            f"Existen {len(invalid_dates)} casos cerrados antes de su recepción.",
        )

    # 6. Casos finalizados deben tener fecha de cierre
    final_without_close = df[
        df["status"].isin(FINAL_STATUSES)
        & df["closed_at"].isna()
    ]

    if not final_without_close.empty:
        add_error(
            errors,
            f"Existen {len(final_without_close)} casos finalizados sin closed_at.",
        )

    # 7. Casos abiertos no deben tener fecha de cierre
    open_with_close = df[
        df["status"].isin(OPEN_STATUSES)
        & df["closed_at"].notna()
    ]

    if not open_with_close.empty:
        add_error(
            errors,
            f"Existen {len(open_with_close)} casos abiertos con closed_at.",
        )

    # 8. Casos pendientes de contacto
    invalid_contact_status = df[
        (df["status"] == "Pendiente contacto")
        & (df["contact_status"] != "Pendiente")
    ]

    if not invalid_contact_status.empty:
        add_error(
            errors,
            f"Existen {len(invalid_contact_status)} casos pendientes de contacto "
            "con contact_status incorrecto.",
        )

    # 9. Casos pendientes de documentación
    invalid_documentation_status = df[
        (df["status"] == "Pendiente documentación")
        & (df["documentation_status"] != "Incompleta")
    ]

    if not invalid_documentation_status.empty:
        add_error(
            errors,
            f"Existen {len(invalid_documentation_status)} casos pendientes "
            "de documentación con estado incorrecto.",
        )

    # 10. Rechazados deben tener motivo
    rejected_without_reason = df[
        (df["status"] == "Rechazado")
        & (df["rejection_reason"].isna())
    ]

    if not rejected_without_reason.empty:
        add_error(
            errors,
            f"Existen {len(rejected_without_reason)} casos rechazados sin motivo.",
        )

    # 11. Anulados deben tener motivo
    cancelled_without_reason = df[
        (df["status"] == "Anulado")
        & (df["cancellation_reason"].isna())
    ]

    if not cancelled_without_reason.empty:
        add_error(
            errors,
            f"Existen {len(cancelled_without_reason)} casos anulados sin motivo.",
        )

    # 12. Casos finalizados deben tener resolution_hours
    final_without_resolution = df[
        df["status"].isin(FINAL_STATUSES)
        & df["resolution_hours"].isna()
    ]

    if not final_without_resolution.empty:
        add_error(
            errors,
            f"Existen {len(final_without_resolution)} casos finalizados "
            "sin resolution_hours.",
        )

    if errors:
        print("VALIDACIÓN FALLIDA")
        print("-" * 40)
        print_errors(errors)
        sys.exit(1)

    print("VALIDACIÓN EXITOSA")
    print("-" * 40)
    print(f"Archivo: {args.input.name}")
    print(f"Registros validados: {len(df)}")
    print(f"Columnas validadas: {len(df.columns)}")
    print("No se encontraron inconsistencias.")


def print_errors(errors):
    for error in errors:
        print(f"- {error}")


if __name__ == "__main__":
    main()
