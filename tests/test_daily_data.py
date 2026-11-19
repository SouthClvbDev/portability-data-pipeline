from datetime import date, datetime

import json
from pathlib import Path

import pandas as pd

from src.generate_daily_data import generate_rows, write_metadata, write_rows


def test_daily_generation_is_reproducible_and_has_no_future_cases():
    cutoff = datetime(2023, 7, 3, 18, 0)
    first = generate_rows(date(2023, 7, 1), cutoff)
    assert first == generate_rows(date(2023, 7, 1), cutoff)
    assert len({row["case_id"] for row in first}) == len(first)
    assert all(datetime.fromisoformat(row["received_at"]) <= cutoff for row in first)
    assert all(not row["closed_at"] or datetime.fromisoformat(row["closed_at"]) <= cutoff for row in first)


def test_recent_cases_can_close_without_changing_identity_or_source_attributes():
    early = {row["case_id"]: row for row in generate_rows(date(2023, 7, 1), datetime(2023, 7, 1, 21))}
    later = {row["case_id"]: row for row in generate_rows(date(2023, 7, 1), datetime(2023, 7, 10, 23))}
    assert early.keys() <= later.keys()
    assert any(not row["closed_at"] and later[key]["closed_at"] for key, row in early.items())
    for key, row in early.items():
        assert (row["received_at"], row["channel"], row["team"]) == (
            later[key]["received_at"], later[key]["channel"], later[key]["team"]
        )


def test_writing_the_same_cutoff_is_a_noop(tmp_path):
    output = tmp_path / "daily.csv"
    rows = generate_rows(date(2023, 7, 1), datetime(2023, 7, 2, 23))
    assert write_rows(rows, output)
    original = output.read_bytes()
    assert not write_rows(rows, output)
    assert output.read_bytes() == original
    metadata = tmp_path / "daily.meta.json"
    cutoff = datetime(2023, 7, 2, 23)
    assert write_metadata(rows, cutoff, metadata)
    assert not write_metadata(rows, cutoff, metadata)


def test_versioned_daily_batch_matches_its_cutoff_and_base_ids():
    root = Path(__file__).resolve().parents[1] / "data/sample"
    daily = pd.read_csv(root / "portability_cases_daily.csv")
    metadata = json.loads((root / "portability_cases_daily.meta.json").read_text())
    base_ids = set(pd.read_csv(root / "portability_cases.csv")["case_id"])
    incremental_ids = set(pd.read_csv(root / "portability_cases_incremental.csv")["case_id"])
    assert len(daily) == metadata["records"]
    assert daily["case_id"].is_unique
    assert not set(daily["case_id"]) & (base_ids | incremental_ids)
    assert daily["received_at"].max().replace(" ", "T") <= metadata["asOf"]


def test_legacy_2023_cohorts_are_resolved_instead_of_remaining_open_forever():
    root = Path(__file__).resolve().parents[1] / "data/sample"
    for name in ("portability_cases.csv", "portability_cases_incremental.csv"):
        frame = pd.read_csv(root / name)
        assert frame["closed_at"].notna().all()
        assert frame["resolution_hours"].notna().all()
        assert (pd.to_datetime(frame["closed_at"]) >= pd.to_datetime(frame["received_at"])).all()
        assert pd.to_datetime(frame["closed_at"]).max() < pd.Timestamp("2024-01-01")
