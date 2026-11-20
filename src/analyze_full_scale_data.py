"""Resume el CSV de escala completa y dibuja su evolución con Matplotlib."""

import argparse
import csv
import gzip
import hashlib
import json
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

if __package__:
    from .operational_profile import resolution_profile
else:
    from operational_profile import resolution_profile


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data/generated/portability_cases_full.csv.gz"
DEFAULT_JSON = ROOT / "web/public/data/full-scale-analysis.json"
DEFAULT_SVG = ROOT / "web/public/analysis/full-scale-trends.svg"


def analyze(source: Path) -> dict:
    manifest_path = source.with_name(source.name.removesuffix(".csv.gz") + ".manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    with source.open("rb") as file:
        digest = hashlib.file_digest(file, "sha256").hexdigest()
    if digest != manifest["sha256"]:
        raise ValueError("El CSV no coincide con el SHA-256 del manifiesto")

    daily = Counter()
    closed = Counter()
    within = Counter()
    statuses = Counter()
    total = 0
    with gzip.open(source, "rt", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        required = {"received_date", "status", "sla_status"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("Faltan columnas necesarias para el análisis")
        for row in reader:
            day = row["received_date"]
            month = day[:7]
            daily[day] += 1
            statuses[row["status"]] += 1
            if row["sla_status"] in ("Dentro de SLA", "Fuera de SLA"):
                closed[month] += 1
                within[month] += row["sla_status"] == "Dentro de SLA"
            total += 1
    if total != manifest["rows"] or dict(sorted(statuses.items())) != manifest["statusCounts"]:
        raise ValueError("Los totales del CSV no coinciden con el manifiesto")
    months = []
    for entry in manifest["monthly"]:
        month = entry["month"]
        observed = sum(value for day, value in daily.items() if day.startswith(month))
        if observed != entry["actual"]:
            raise ValueError(f"Volumen mensual inconsistente: {month}")
        episode, _ = resolution_profile(date.fromisoformat(month + "-01"), entry["category"])
        months.append({"month": month, "cases": observed, "category": entry["category"], "episode": episode,
                       "complete": entry["complete"], "closed": closed[month], "withinSla": within[month],
                       "slaRate": round(100 * within[month] / closed[month], 1) if closed[month] else None})
    first = date.fromisoformat(manifest["start"])
    last = date.fromisoformat(manifest["asOf"][:10])
    days = []
    rolling = 0
    window = []
    current = first
    while current <= last:
        value = daily[current.isoformat()]
        window.append(value)
        rolling += value
        if len(window) > 7:
            rolling -= window.pop(0)
        days.append({"date": current.isoformat(), "cases": value, "average7d": round(rolling / len(window), 1)})
        current += timedelta(days=1)
    complete = [month for month in months if month["complete"]]
    return {"source": "CSV sintético de escala completa", "asOf": manifest["asOf"],
            "timezone": manifest["timezone"], "total": total, "monthly": months, "daily": days,
            "insights": {
                "lowestSla": min(complete, key=lambda month: month["slaRate"]),
                "highestSla": max(complete, key=lambda month: month["slaRate"]),
                "highestVolume": max(complete, key=lambda month: month["cases"]),
            }}


def plot(analysis: dict, output: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    months = analysis["monthly"]
    days = analysis["daily"]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "svg.fonttype": "none", "svg.hashsalt": "portability-analysis-v2"})
    fig, axes = plt.subplots(3, 1, figsize=(13, 11), constrained_layout=True)
    fig.patch.set_facecolor("#f7f9f6")
    for ax in axes:
        ax.set_facecolor("#ffffff")
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=.18)
        ax.set_axisbelow(True)
    colors = {"normal": "#3db6a5", "pico_positivo": "#102a36", "pico_negativo": "#d38b34"}
    axes[0].bar(range(len(months)), [m["cases"] for m in months],
                color=[colors[m["category"]] for m in months], width=.8)
    axes[0].set_title("Recepciones mensuales · picos destacados", loc="left", weight="bold")
    axes[0].set_ylabel("Trámites")
    axes[0].set_xticks(range(0, len(months), 3), [months[i]["month"] for i in range(0, len(months), 3)], rotation=45, ha="right")
    axes[1].plot(range(len(days)), [d["average7d"] for d in days], color="#0c9b87", linewidth=1.7)
    axes[1].set_title("Ingresos diarios · promedio móvil de 7 días", loc="left", weight="bold")
    axes[1].set_ylabel("Trámites por día")
    axes[1].set_xticks(range(0, len(days), max(1, len(days)//8)),
                       [days[i]["date"] for i in range(0, len(days), max(1, len(days)//8))], rotation=30, ha="right")
    complete = [m for m in months if m["complete"]]
    axes[2].plot(range(len(complete)), [m["slaRate"] for m in complete], marker="o", markersize=2.5,
                 color="#102a36", linewidth=1.4)
    axes[2].set_title("Casos recibidos en cada mes que cerraron dentro de 48 h", loc="left", weight="bold")
    axes[2].set_ylabel("% de casos resueltos")
    axes[2].set_ylim(0, 100)
    axes[2].set_xticks(range(0, len(complete), 3), [complete[i]["month"] for i in range(0, len(complete), 3)], rotation=45, ha="right")
    lowest = min(enumerate(complete), key=lambda pair: pair[1]["slaRate"])
    highest = max(enumerate(complete), key=lambda pair: pair[1]["slaRate"])
    for (index, month), color, offset in [(lowest, "#b6692e", 15), (highest, "#0c9b87", -24)]:
        axes[2].scatter([index], [month["slaRate"]], color=color, s=55, zorder=4)
        axes[2].annotate(f"{month['month']}: {month['slaRate']} %\n{month['episode']}",
                         (index, month["slaRate"]), xytext=(0, offset), textcoords="offset points",
                         ha="center", va="bottom" if offset > 0 else "top", fontsize=8, color=color)
    fig.suptitle(f"Portabilidad sintética · análisis con Python y Matplotlib\nCorte: {analysis['asOf'][:10]} (Argentina) · Mes en curso parcial", fontsize=14, weight="bold")
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, format="svg", facecolor=fig.get_facecolor(), metadata={"Date": None}, bbox_inches="tight", pad_inches=.25)
    plt.close(fig)
    output.write_text("\n".join(line.rstrip() for line in output.read_text(encoding="utf-8").splitlines()) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--svg", type=Path, default=DEFAULT_SVG)
    args = parser.parse_args()
    analysis = analyze(args.input)
    plot(analysis, args.svg)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(analysis, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Matplotlib: {analysis['total']:,} trámites, {len(analysis['monthly'])} meses → {args.svg}")


if __name__ == "__main__":
    main()
