"""Genera una muestra sintética de escala mensual para PostgreSQL y Power BI."""

import argparse
import calendar
import csv
import gzip
import hashlib
import io
import json
import math
import os
import random
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

if __package__:
    from .operational_profile import resolution_profile
else:
    from operational_profile import resolution_profile


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = BASE_DIR / "data/generated/portability_cases_full.csv.gz"
START_DATE = date(2023, 1, 1)
FIELDS = [
    "case_id", "received_at", "received_date", "received_year", "received_month",
    "received_month_name", "received_weekday", "closed_at", "status", "is_closed",
    "is_pending", "channel", "team", "documentation_status",
    "has_documentation_pending", "contact_status", "has_contact_pending",
    "rejection_reason", "cancellation_reason", "resolution_hours", "sla_status",
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


def seed_for(*parts: object) -> int:
    value = ":".join(map(str, ("portability-full-v1", *parts)))
    return int.from_bytes(hashlib.sha256(value.encode()).digest()[:8], "big")


def month_profile(year: int, month: int) -> tuple[str, int]:
    peak_rng = random.Random(seed_for("peaks", year))
    positive = peak_rng.randint(1, 12)
    negative = peak_rng.choice([value for value in range(1, 13) if value != positive])
    rng = random.Random(seed_for("volume", year, month))
    if month == positive:
        return "pico_positivo", rng.randint(25_001, 40_000)
    if month == negative:
        return "pico_negativo", rng.randint(10_000, 14_999)
    return "normal", rng.randint(15_000, 25_000)


def daily_plan(year: int, month: int) -> tuple[str, int, list[int]]:
    category, target = month_profile(year, month)
    rng = random.Random(seed_for("days", year, month))
    days = calendar.monthrange(year, month)[1]
    weights = [
        (0.68 if date(year, month, day).weekday() >= 5 else 1.12) * rng.uniform(0.88, 1.12)
        for day in range(1, days + 1)
    ]
    total_weight = sum(weights)
    shares = [target * weight / total_weight for weight in weights]
    counts = [math.floor(share) for share in shares]
    remainder = target - sum(counts)
    ranking = sorted(range(days), key=lambda index: (-(shares[index] - counts[index]), index))
    for index in ranking[:remainder]:
        counts[index] += 1
    return category, target, counts


def month_range(start: date, end: date):
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        yield year, month
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)


def records_for_day(current: date, count: int, as_of: datetime):
    rng = random.Random(seed_for("cases", current.isoformat()))
    volume_category, _ = month_profile(current.year, current.month)
    _, resolution_scale = resolution_profile(current, volume_category)
    for index in range(1, count + 1):
        received = datetime(current.year, current.month, current.day, rng.randint(8, 20), rng.randint(0, 59), rng.randint(0, 59))
        final_status = rng.choices(["Aprobado", "Rechazado", "Anulado"], weights=[67, 22, 11])[0]
        resolution = round(max(2, min(240, rng.gammavariate(3.0, resolution_scale))), 2)
        planned_close = received + timedelta(hours=resolution)
        open_status = rng.choice(["En análisis", "Pendiente documentación", "Pendiente contacto"])
        documentation = rng.choice(["Completa", "Incompleta", "No requerida"])
        contact = rng.choice(["Realizado", "Pendiente", "No corresponde"])
        rejection = rng.choice(REJECTION_REASONS)
        cancellation = rng.choice(CANCELLATION_REASONS)
        channel = rng.choice(CHANNELS)
        team = rng.choice(TEAMS)
        if received > as_of:
            continue
        closed = planned_close <= as_of
        status = final_status if closed else ("Recibido" if as_of - received < timedelta(hours=4) else open_status)
        if closed:
            documentation = "Completa"
        if status == "Pendiente documentación":
            documentation = "Incompleta"
        if status == "Pendiente contacto":
            contact = "Pendiente"
        yield {
            "case_id": f"FULL-{current:%Y%m%d}-{index:05d}",
            "received_at": received.strftime("%Y-%m-%d %H:%M:%S"),
            "received_date": current.isoformat(),
            "received_year": current.year,
            "received_month": current.month,
            "received_month_name": calendar.month_name[current.month],
            "received_weekday": calendar.day_name[current.weekday()],
            "closed_at": planned_close.strftime("%Y-%m-%d %H:%M:%S") if closed else "",
            "status": status,
            "is_closed": "true" if closed else "false",
            "is_pending": "false" if closed else "true",
            "channel": channel,
            "team": team,
            "documentation_status": documentation,
            "has_documentation_pending": "true" if documentation == "Incompleta" else "false",
            "contact_status": contact,
            "has_contact_pending": "true" if contact == "Pendiente" else "false",
            "rejection_reason": rejection if status == "Rechazado" else "",
            "cancellation_reason": cancellation if status == "Anulado" else "",
            "resolution_hours": resolution if closed else "",
            "sla_status": ("Dentro de SLA" if resolution <= 48 else "Fuera de SLA") if closed else "No aplica",
        }


def generate(start: date, as_of: datetime, output: Path) -> dict:
    if as_of.date() < start:
        raise ValueError("La fecha de corte es anterior al inicio")
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_name(output.name + ".tmp")
    monthly = []
    total = 0
    statuses = Counter()
    first_received = last_received = None
    try:
        with temp.open("wb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=6) as compressed:
                with io.TextIOWrapper(compressed, encoding="utf-8", newline="") as stream:
                    writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
                    writer.writeheader()
                    for year, month in month_range(start, as_of.date()):
                        category, target, daily_counts = daily_plan(year, month)
                        episode, scale = resolution_profile(date(year, month, 1), category)
                        actual = 0
                        for day, count in enumerate(daily_counts, start=1):
                            current = date(year, month, day)
                            if current < start or current > as_of.date():
                                continue
                            for row in records_for_day(current, count, as_of):
                                writer.writerow(row)
                                actual += 1
                                total += 1
                                statuses[row["status"]] += 1
                                first_received = row["received_at"] if first_received is None or row["received_at"] < first_received else first_received
                                last_received = row["received_at"] if last_received is None or row["received_at"] > last_received else last_received
                        full_start = (year, month) != (start.year, start.month) or start.day == 1
                        monthly.append({"month": f"{year:04d}-{month:02d}", "category": category, "plannedFullMonth": target, "actual": actual, "complete": full_start and (year, month) < (as_of.year, as_of.month), "operationalEpisode": episode, "resolutionScaleHours": scale})
        with temp.open("rb") as generated_file:
            digest = hashlib.file_digest(generated_file, "sha256").hexdigest()
        same = False
        if output.exists():
            with output.open("rb") as previous_file:
                same = hashlib.file_digest(previous_file, "sha256").hexdigest() == digest
        if same:
            temp.unlink()
        else:
            os.replace(temp, output)
    finally:
        if temp.exists():
            temp.unlink()
    return {
        "generatorVersion": "full-v2-operational-profile",
        "asOf": as_of.isoformat(timespec="seconds"),
        "timezone": "America/Argentina/Buenos_Aires",
        "start": start.isoformat(),
        "rows": total,
        "firstReceived": first_received,
        "lastReceived": last_received,
        "sha256": digest,
        "columns": FIELDS,
        "monthly": monthly,
        "statusCounts": dict(sorted(statuses.items())),
        "source": "Simulación sintética reproducible; no representa una operación real",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", type=datetime.fromisoformat, default=now_argentina(), help="Corte YYYY-MM-DDTHH:MM:SS en Argentina; por defecto, ahora")
    parser.add_argument("--start", type=date.fromisoformat, default=START_DATE, help="Inicio de la simulación; por defecto, 2023-01-01")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if args.as_of.tzinfo or args.as_of > now_argentina():
        parser.error("La fecha de corte debe ser una hora local de Argentina que no sea futura")
    metadata = generate(args.start, args.as_of, args.output)
    manifest = args.output.with_name(args.output.name.removesuffix(".csv.gz") + ".manifest.json")
    manifest.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{metadata['rows']:,} casos sintéticos del {metadata['start']} al {metadata['asOf']}")
    print(f"CSV: {args.output}\nManifiesto: {manifest}")


if __name__ == "__main__":
    main()
