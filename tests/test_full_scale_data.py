import gzip
import hashlib
import json
from datetime import date, datetime

import pytest

from src.generate_full_scale_data import FIELDS, daily_plan, generate, month_profile, records_for_day
from src.load_full_scale_to_postgres import load


def test_monthly_bands_and_daily_allocation_are_reproducible():
    bands = {"normal": (15_000, 25_000), "pico_positivo": (25_001, 40_000), "pico_negativo": (10_000, 14_999)}
    for year in (2023, 2024, 2025):
        categories = []
        for month in range(1, 13):
            category, target = month_profile(year, month)
            lower, upper = bands[category]
            assert lower <= target <= upper
            plan = daily_plan(year, month)
            assert (category, target) == plan[:2]
            assert sum(plan[2]) == target
            assert plan == daily_plan(year, month)
            categories.append(category)
        assert categories.count("pico_positivo") == 1
        assert categories.count("pico_negativo") == 1


def test_operational_episodes_create_visible_sla_change_without_invalid_closures():
    slow = list(records_for_day(date(2024, 5, 15), 2000, datetime(2024, 6, 1)))
    improved = list(records_for_day(date(2025, 8, 15), 2000, datetime(2025, 9, 1)))
    def rate(rows):
        assert all(row["closed_at"] and row["resolution_hours"] for row in rows)
        return sum(row["sla_status"] == "Dentro de SLA" for row in rows) / len(rows)
    assert rate(improved) - rate(slow) > .4


def test_compressed_dataset_has_correct_schema_cutoff_and_stable_bytes(tmp_path):
    path = tmp_path / "full.csv.gz"
    cutoff = datetime(2023, 2, 3, 12)
    first = generate(date(2023, 2, 1), cutoff, path)
    assert first["columns"] == FIELDS
    assert first["monthly"][0]["complete"] is False
    assert first["monthly"][0]["actual"] < first["monthly"][0]["plannedFullMonth"]
    assert first["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        lines = stream.readlines()
    assert len(lines) == first["rows"] + 1
    assert lines[0].strip().split(",") == FIELDS
    assert first["lastReceived"] <= cutoff.strftime("%Y-%m-%d %H:%M:%S")
    assert generate(date(2023, 2, 1), cutoff, path) == first
    assert hashlib.sha256(path.read_bytes()).hexdigest() == first["sha256"]
    path.with_name("full.manifest.json").write_text(json.dumps(first))
    with pytest.raises(ValueError, match="--mode sync"):
        load(path)
