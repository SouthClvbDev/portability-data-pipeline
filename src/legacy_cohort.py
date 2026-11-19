"""Resuelve la cohorte histórica de 2023 que había quedado abierta indefinidamente."""

import hashlib
import random
from datetime import timedelta

import pandas as pd


FINAL = {"Aprobado", "Rechazado", "Anulado"}
REJECTIONS = ["Datos inconsistentes", "Deuda con operador actual", "Línea no elegible", "Documentación inválida", "Solicitud duplicada"]
CANCELLATIONS = ["Cancelación del cliente", "Error en la solicitud", "Vencimiento del trámite"]


def close_legacy_cohort(frame: pd.DataFrame) -> pd.DataFrame:
    """Conserva IDs, recepciones y finales existentes; cierra los antiguos abiertos."""
    for index, row in frame.iterrows():
        if row["status"] in FINAL:
            continue
        seed = int.from_bytes(hashlib.sha256(f"legacy-closure-v1:{row['case_id']}".encode()).digest()[:8], "big")
        rng = random.Random(seed)
        # 10–90 días, con una cola pequeña de 91–180 días: un backlog que
        # primero crece y después se vacía dentro de 2023.
        days = rng.randint(10, 90) if rng.random() < .9 else rng.randint(91, 180)
        hours = round(days * 24 + rng.uniform(0, 23), 2)
        status = rng.choices(["Aprobado", "Rechazado", "Anulado"], weights=[67, 22, 11])[0]
        frame.at[index, "status"] = status
        frame.at[index, "closed_at"] = pd.Timestamp(row["received_at"]) + timedelta(hours=hours)
        frame.at[index, "resolution_hours"] = hours
        frame.at[index, "documentation_status"] = "Completa"
        frame.at[index, "rejection_reason"] = rng.choice(REJECTIONS) if status == "Rechazado" else None
        frame.at[index, "cancellation_reason"] = rng.choice(CANCELLATIONS) if status == "Anulado" else None
    return frame
