import os

import pandas as pd
import pytest
from sqlalchemy import create_engine, text


DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "portability_db")
DB_USER = os.getenv("POSTGRES_USER", "data_user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "data_password_dev")

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


@pytest.fixture(scope="module")
def engine():
    database_engine = create_engine(DATABASE_URL)

    try:
        with database_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as error:
        pytest.fail(
            f"No se pudo conectar a PostgreSQL. "
            f"Verificá que Docker esté activo. Detalle: {error}"
        )

    return database_engine


def test_database_has_7500_records(engine):
    with engine.connect() as connection:
        total = connection.execute(
            text("SELECT COUNT(*) FROM public.portability_cases")
        ).scalar()

    assert total == 7500


def test_case_ids_are_unique_in_database(engine):
    query = text(
        """
        SELECT COUNT(*) - COUNT(DISTINCT case_id)
        FROM public.portability_cases
        """
    )

    with engine.connect() as connection:
        duplicated_ids = connection.execute(query).scalar()

    assert duplicated_ids == 0


def test_kpi_view_matches_base_table(engine):
    query = text(
        """
        SELECT
            (SELECT total_cases FROM vw_portability_kpis) AS view_total,
            (SELECT COUNT(*) FROM portability_cases) AS table_total
        """
    )

    with engine.connect() as connection:
        result = connection.execute(query).mappings().one()

    assert result["view_total"] == result["table_total"]


def test_open_and_closed_cases_sum_to_total(engine):
    query = text(
        """
        SELECT
            COUNT(*) AS total_cases,
            COUNT(*) FILTER (WHERE is_pending = true) AS open_cases,
            COUNT(*) FILTER (WHERE is_closed = true) AS closed_cases
        FROM public.portability_cases
        """
    )

    with engine.connect() as connection:
        result = connection.execute(query).mappings().one()

    assert (
        result["open_cases"] + result["closed_cases"]
        == result["total_cases"]
    )


def test_monthly_view_sums_to_total(engine):
    query = text(
        """
        SELECT SUM(total_cases) AS monthly_total
        FROM vw_monthly_operational_metrics
        """
    )

    with engine.connect() as connection:
        monthly_total = connection.execute(query).scalar()

    assert monthly_total == 7500


def test_expected_analytics_views_exist(engine):
    query = text(
        """
        SELECT table_name
        FROM information_schema.views
        WHERE table_schema = 'public'
          AND table_name IN (
              'vw_portability_kpis',
              'vw_cases_by_status',
              'vw_daily_volume',
              'vw_team_performance',
              'vw_sla_by_channel',
              'vw_monthly_operational_metrics'
          )
        """
    )

    with engine.connect() as connection:
        views = {
            row[0]
            for row in connection.execute(query).fetchall()
        }

    expected_views = {
        "vw_portability_kpis",
        "vw_cases_by_status",
        "vw_daily_volume",
        "vw_team_performance",
        "vw_sla_by_channel",
        "vw_monthly_operational_metrics",
    }

    assert views == expected_views