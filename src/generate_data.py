from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


SEED = 42
NUMBER_OF_RECORDS = 5000

BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_FILE = BASE_DIR / "data" / "sample" / "portability_cases.csv"

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
    None,
]

cancellation_reasons = [
    "Cancelación del cliente",
    "Error en la solicitud",
    "Vencimiento del trámite",
    None,
]

start_date = datetime(2023, 1, 1)
end_date = datetime(2023, 3, 31)

date_range_days = (end_date - start_date).days

received_dates = [
    start_date + timedelta(
        days=int(rng.integers(0, date_range_days + 1)),
        hours=int(rng.integers(8, 20)),
        minutes=int(rng.integers(0, 60)),
    )
    for _ in range(NUMBER_OF_RECORDS)
]

rows = []

for index, received_at in enumerate(received_dates, start=1):
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

    resolution_hours = None
    closed_at = None

    if status in ["Aprobado", "Rechazado", "Anulado"]:
        resolution_hours = round(
            float(np.clip(rng.gamma(shape=3.0, scale=12.0), 2, 240)),
            2,
        )
        closed_at = received_at + timedelta(hours=resolution_hours)

    rejection_reason = None
    if status == "Rechazado":
        rejection_reason = rng.choice(rejection_reasons[:-1])

    cancellation_reason = None
    if status == "Anulado":
        cancellation_reason = rng.choice(cancellation_reasons[:-1])

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

df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

print(f"Archivo generado correctamente: {OUTPUT_FILE}")
print(f"Cantidad de registros: {len(df)}")
print("\nDistribución por estado:")
print(df["status"].value_counts())