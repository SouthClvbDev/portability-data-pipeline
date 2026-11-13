from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]

SAMPLE_FILE = (
    BASE_DIR
    / "data"
    / "sample"
    / "portability_cases.csv"
)

PROCESSED_FILE = (
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

OPEN_STATUSES = {
    "Recibido",
    "En análisis",
    "Pendiente documentación",
    "Pendiente contacto",
}

VALID_STATUSES = FINAL_STATUSES | OPEN_STATUSES


def load_sample_data():
    assert SAMPLE_FILE.exists(), (
        f"No existe el archivo de ejemplo: {SAMPLE_FILE}"
    )

    df = pd.read_csv(SAMPLE_FILE)

    df["received_at"] = pd.to_datetime(
        df["received_at"],
        errors="coerce",
    )

    df["closed_at"] = pd.to_datetime(
        df["closed_at"],
        errors="coerce",
    )

    return df


def test_sample_file_exists():
    assert SAMPLE_FILE.exists()


def test_sample_has_5000_records():
    df = load_sample_data()

    assert len(df) == 5000


def test_case_ids_are_unique_and_not_empty():
    df = load_sample_data()

    assert df["case_id"].notna().all()
    assert df["case_id"].is_unique


def test_statuses_are_valid():
    df = load_sample_data()

    statuses = set(df["status"].dropna())

    assert statuses.issubset(VALID_STATUSES)


def test_dates_are_valid():
    df = load_sample_data()

    assert df["received_at"].notna().all()

    invalid_closed_dates = df[
        df["closed_at"].notna()
        & (df["closed_at"] < df["received_at"])
    ]

    assert invalid_closed_dates.empty


def test_final_cases_have_close_date():
    df = load_sample_data()

    final_cases_without_close = df[
        df["status"].isin(FINAL_STATUSES)
        & df["closed_at"].isna()
    ]

    assert final_cases_without_close.empty


def test_open_cases_do_not_have_close_date():
    df = load_sample_data()

    open_cases_with_close = df[
        df["status"].isin(OPEN_STATUSES)
        & df["closed_at"].notna()
    ]

    assert open_cases_with_close.empty


def test_business_rules_for_pending_cases():
    df = load_sample_data()

    invalid_contact_cases = df[
        (df["status"] == "Pendiente contacto")
        & (df["contact_status"] != "Pendiente")
    ]

    invalid_documentation_cases = df[
        (df["status"] == "Pendiente documentación")
        & (df["documentation_status"] != "Incompleta")
    ]

    assert invalid_contact_cases.empty
    assert invalid_documentation_cases.empty


def test_rejected_and_cancelled_cases_have_reasons():
    df = load_sample_data()

    rejected_without_reason = df[
        (df["status"] == "Rechazado")
        & (df["rejection_reason"].isna())
    ]

    cancelled_without_reason = df[
        (df["status"] == "Anulado")
        & (df["cancellation_reason"].isna())
    ]

    assert rejected_without_reason.empty
    assert cancelled_without_reason.empty


def test_sla_rules_are_consistent():
    assert PROCESSED_FILE.exists(), (
        "No existe el archivo procesado. "
        "Ejecutá primero transform_cases.py."
    )

    df = pd.read_csv(PROCESSED_FILE)

    within_sla = df[
        (df["resolution_hours"].notna())
        & (df["resolution_hours"] <= 48)
        & (df["sla_status"] != "Dentro de SLA")
    ]

    outside_sla = df[
        (df["resolution_hours"].notna())
        & (df["resolution_hours"] > 48)
        & (df["sla_status"] != "Fuera de SLA")
    ]

    no_sla = df[
        df["resolution_hours"].isna()
        & (df["sla_status"] != "No aplica")
    ]

    assert within_sla.empty
    assert outside_sla.empty
    assert no_sla.empty