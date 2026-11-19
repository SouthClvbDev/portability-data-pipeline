"""Extiende la muestra con casos diarios sintéticos, reproducibles a una fecha de corte."""

import argparse
import csv
import hashlib
import io
import json
import random
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


BASE_DIR = Path(__file__).resolve().parents[1]
START_DATE = date(2023, 7, 1)
OUTPUT_FILE = BASE_DIR / "data/sample/portability_cases_daily.csv"
METADATA_FILE = BASE_DIR / "data/sample/portability_cases_daily.meta.json"
FIELDS = [
    "case_id", "received_at", "closed_at", "status", "channel", "team",
    "documentation_status", "contact_status", "rejection_reason",
    "cancellation_reason", "resolution_hours",
]
CHANNELS = ["Web", "App", "Sucursal", "Call Center", "Distribuidor"]
TEAMS = ["Backoffice Norte", "Backoffice Centro", "Backoffice Sur"]
REJECTION_REASONS = [
    "Datos inconsistentes", "Deuda con operador actual", "Línea no elegible",
    "Documentación inválida", "Solicitud duplicada",
]
CANCELLATION_REASONS = [
    "Cancelación del cliente", "Error en la solicitud", "Vencimiento del trámite",
]


def now_argentina() -> datetime:
    return datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).replace(tzinfo=None, microsecond=0)


def generate_rows(start: date, as_of: datetime) -> list[dict]:
    if as_of.date() < start:
        raise ValueError("La fecha de corte debe ser igual o posterior al inicio")
    through = as_of.date()
    cutoff = as_of
    rows = []
    for offset in range((through - start).days + 1):
        current = start + timedelta(days=offset)
        seed = int.from_bytes(hashlib.sha256(f"portability-daily:{current}".encode()).digest()[:8], "big")
        rng = random.Random(seed)
        quantity = rng.randint(6, 16) if current.weekday() < 5 else rng.randint(2, 7)
        for index in range(1, quantity + 1):
            received = datetime.combine(current, time(rng.randint(8, 20), rng.randint(0, 59)))
            planned_status = rng.choices(["Aprobado", "Rechazado", "Anulado"], weights=[67, 22, 11])[0]
            resolution_hours = round(max(2, min(240, rng.gammavariate(3.0, 12.0))), 2)
            planned_close = received + timedelta(hours=resolution_hours)
            pending_status = rng.choice(["En análisis", "Pendiente documentación", "Pendiente contacto"])
            documentation = rng.choice(["Completa", "Incompleta", "No requerida"])
            contact = rng.choice(["Realizado", "Pendiente", "No corresponde"])
            rejection_reason = rng.choice(REJECTION_REASONS)
            cancellation_reason = rng.choice(CANCELLATION_REASONS)
            channel = rng.choice(CHANNELS)
            team = rng.choice(TEAMS)
            if received > cutoff:
                continue
            is_closed = planned_close <= cutoff
            if is_closed:
                status = planned_status
            elif (cutoff - received).total_seconds() < 4 * 3600:
                status = "Recibido"
            else:
                status = pending_status
            if is_closed:
                documentation = "Completa"
            if status == "Pendiente documentación":
                documentation = "Incompleta"
            if status == "Pendiente contacto":
                contact = "Pendiente"
            rows.append({
                "case_id": f"SIM-{current:%Y%m%d}-{index:04d}",
                "received_at": received.strftime("%Y-%m-%d %H:%M:%S"),
                "closed_at": planned_close.strftime("%Y-%m-%d %H:%M:%S") if is_closed else "",
                "status": status,
                "channel": channel,
                "team": team,
                "documentation_status": documentation,
                "contact_status": contact,
                "rejection_reason": rejection_reason if status == "Rechazado" else "",
                "cancellation_reason": cancellation_reason if status == "Anulado" else "",
                "resolution_hours": resolution_hours if is_closed else "",
            })
    return rows


def write_rows(rows: list[dict], output: Path) -> bool:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    content = stream.getvalue().encode("utf-8-sig")
    if output.exists() and output.read_bytes() == content:
        return False
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(content)
    return True


def write_metadata(rows: list[dict], as_of: datetime, output: Path) -> bool:
    metadata = {
        "asOf": as_of.isoformat(timespec="seconds"),
        "timezone": "America/Argentina/Buenos_Aires",
        "start": START_DATE.isoformat(),
        "records": len(rows),
    }
    content = (json.dumps(metadata, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if output.exists() and output.read_bytes() == content:
        return False
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(content)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", type=datetime.fromisoformat, default=now_argentina(), help="Fecha y hora de corte YYYY-MM-DDTHH:MM:SS en Argentina; por defecto, ahora")
    parser.add_argument("--output", type=Path, default=OUTPUT_FILE)
    parser.add_argument("--metadata", type=Path, default=METADATA_FILE)
    args = parser.parse_args()
    if args.as_of.tzinfo or args.as_of > now_argentina():
        parser.error("La fecha de corte debe ser una hora local de Argentina que no sea futura")
    rows = generate_rows(START_DATE, args.as_of)
    changed = write_rows(rows, args.output)
    meta_changed = write_metadata(rows, args.as_of, args.metadata)
    print(f"{len(rows)} casos sintéticos hasta {args.as_of}; CSV {'actualizado' if changed else 'sin cambios'}, metadatos {'actualizados' if meta_changed else 'sin cambios'}")


if __name__ == "__main__":
    main()
