#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON="${PYTHON:-.venv/bin/python}"
if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi
docker compose up -d --wait
"$PYTHON" src/validation/validate_data.py
"$PYTHON" src/validation/validate_data.py --input data/sample/portability_cases_incremental.csv
"$PYTHON" src/transformations/transform_cases.py
"$PYTHON" src/load_to_postgres.py --mode initial
"$PYTHON" src/transformations/transform_cases.py --input data/sample/portability_cases_incremental.csv --output data/processed/portability_cases_incremental_clean.csv
"$PYTHON" src/load_to_postgres.py --mode append --input data/processed/portability_cases_incremental_clean.csv
docker exec -i portability-postgres psql -v ON_ERROR_STOP=1 -U "${POSTGRES_USER:-data_user}" -d "${POSTGRES_DB:-portability_db}" < sql/analytics/01_operational_views.sql
docker exec -i portability-postgres psql -v ON_ERROR_STOP=1 -U "${POSTGRES_USER:-data_user}" -d "${POSTGRES_DB:-portability_db}" < sql/analytics/02_monthly_metrics.sql
"$PYTHON" -m pytest -q
