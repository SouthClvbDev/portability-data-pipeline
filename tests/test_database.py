import os

import pandas as pd
import pytest
from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

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


def test_database_enforces_unique_case_ids(engine):
    with engine.connect() as connection:
        with pytest.raises(IntegrityError):
            connection.execute(text("INSERT INTO public.portability_cases SELECT * FROM public.portability_cases LIMIT 1"))
        connection.rollback()


def test_database_rejects_invalid_status(engine):
    with engine.connect() as connection:
        with pytest.raises(IntegrityError):
            connection.execute(text("INSERT INTO public.portability_cases SELECT 'PORT-INVALID', received_at, received_date, received_year, received_month, received_month_name, received_weekday, closed_at, 'Estado inválido', is_closed, is_pending, channel, team, documentation_status, has_documentation_pending, contact_status, has_contact_pending, rejection_reason, cancellation_reason, resolution_hours, sla_status FROM public.portability_cases LIMIT 1"))
        connection.rollback()


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
              'vw_monthly_operational_metrics',
              'vw_case_observed_events',
              'vw_daily_backlog'
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
        "vw_case_observed_events",
        "vw_daily_backlog",
    }

    assert views == expected_views


def test_observed_history_reconciles_with_snapshot(engine):
    with engine.connect() as connection:
        result = connection.execute(text("""
            SELECT
              (SELECT count(*) FROM public.vw_case_observed_events WHERE event_type = 'received') AS receipts,
              (SELECT count(*) FROM public.vw_case_observed_events WHERE event_type = 'closed') AS closures,
              (SELECT open_cases_eod FROM public.vw_daily_backlog ORDER BY day DESC LIMIT 1) AS final_open,
              (SELECT count(*) FROM public.portability_cases) AS total,
              (SELECT count(*) FROM public.portability_cases WHERE is_closed) AS closed,
              (SELECT count(*) FROM public.portability_cases WHERE is_pending) AS open
        """)).mappings().one()
    assert result['receipts'] == result['total']
    assert result['closures'] == result['closed']
    assert result['final_open'] == result['open']


def test_daily_backlog_matches_case_dates_at_cutoff(engine):
    with engine.connect() as connection:
        result = connection.execute(text("""
            SELECT
              (SELECT open_cases_eod FROM public.vw_daily_backlog WHERE day = DATE '2023-05-31') AS from_view,
              (SELECT count(*) FROM public.portability_cases
               WHERE received_at::timestamp < TIMESTAMP '2023-06-01'
                 AND (closed_at IS NULL OR closed_at::timestamp >= TIMESTAMP '2023-06-01')) AS from_cases
        """)).mappings().one()
    assert result['from_view'] == result['from_cases']
