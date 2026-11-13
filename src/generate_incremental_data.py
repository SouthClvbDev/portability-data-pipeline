from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


SEED = 2024
NUMBER_OF_RECORDS = 2500
START_INDEX = 5001

BASE_DIR = Path(__file__).resolve().parents[1]

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "sample"
    / "portability_cases_incremental.csv"
)

rng = np.random.default_rng(SEED)

statuses = [
    "Recibido",
    "En análisis",
    "Pendiente documentación",
    "Pendiente contacto",
    "Aprobado",
    "Rechazado",
    "Anulado",
]

channels = [
    "Web",
    "App",
    "Sucursal",
    "Call Center",
    "Distribuidor",
]

teams = [
    "Backoffice Norte",
    "Backoffice Centro",
    "Backoffice Sur",
]

documentation_statuses = [
    "Completa",
    "Incompleta",
    "No requerida",
]

contact_statuses = [
    "Realizado",
    "Pendiente",
    "No corresponde",
]

rejection_reasons = [
    "Datos inconsistentes",
    "Deuda con operador actual",
    "Línea no elegible",
    "Documentación inválida",
    "Solicitud duplicada",
]

cancellation_reasons = [
    "Cancelación del cliente",
    "Error en la solicitud",
    "Vencimiento del trámite",
]

start_date = datetime(2023, 4, 1)
end_date = datetime(2023, 6, 30)

date_range_days = (end_date - start_date).days

rows = []

for index in range(START_INDEX, START_INDEX + NUMBER_OF_RECORDS):
    received_at = start_date + timedelta(
        days=int(rng.integers(0, date_range_days + 1)),
        hours=int(rng.integers(8, 20)),
        minutes=int(rng.integers(0, 60)),
    )

    status = rng.choice(
        statuses,
        p=[0.08, 0.18, 0.14, 0.10, 0.32, 0.12, 0.06],
    )

    documentation_status = rng.choice(
        documentation_statuses,
        p=[0.65, 0.25, 0.10],
    )

    contact_status = rng.choice(
        contact_statuses,
        p=[0.55, 0.25, 0.20],
    )

    if status == "Pendiente contacto":
        contact_status = "Pendiente"

    if status == "Pendiente documentación":
        documentation_status = "Incompleta"

    if status in ["Aprobado", "Rechazado", "Anulado"]:
        documentation_status = "Completa"

    resolution_hours = None
    closed_at = None

    if status in ["Aprobado", "Rechazado", "Anulado"]:
        resolution_hours = round(
            float(np.clip(rng.gamma(shape=3.0, scale=12.0), 2, 240)),
            2,
        )
        closed_at = received_at + timedelta(
            hours=resolution_hours
        )

    rejection_reason = None

    if status == "Rechazado":
        rejection_reason = rng.choice(rejection_reasons)

    cancellation_reason = None

    if status == "Anulado":
        cancellation_reason = rng.choice(cancellation_reasons)

    rows.append(
        {
            "case_id": f"PORT-{index:06d}",
            "received_at": received_at,
            "closed_at": closed_at,
            "status": status,
            "channel": rng.choice(channels),
            "team": rng.choice(teams),
            "documentation_status": documentation_status,
            "contact_status": contact_status,
            "rejection_reason": rejection_reason,
            "cancellation_reason": cancellation_reason,
            "resolution_hours": resolution_hours,
        }
    )

df = pd.DataFrame(rows)

df["received_at"] = pd.to_datetime(df["received_at"])
df["closed_at"] = pd.to_datetime(df["closed_at"])

df = df.sort_values("received_at").reset_index(drop=True)

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig",
)

print(f"Archivo generado correctamente: {OUTPUT_FILE}")
print(f"Cantidad de registros: {len(df)}")
print(f"Primer case_id: {df['case_id'].min()}")
print(f"Último case_id: {df['case_id'].max()}")
print("\nDistribución por estado:")
print(df["status"].value_counts())