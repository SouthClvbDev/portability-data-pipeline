CREATE OR REPLACE VIEW vw_monthly_operational_metrics AS
SELECT
    received_year,
    received_month,
    MIN(received_date) AS month_start,
    TO_CHAR(
        MIN(received_date)::date,
        'YYYY-MM'
    ) AS year_month,

    COUNT(*) AS total_cases,

    COUNT(*) FILTER (
        WHERE is_closed = true
    ) AS closed_cases,

    COUNT(*) FILTER (
        WHERE is_pending = true
    ) AS open_cases,

    COUNT(*) FILTER (
        WHERE status = 'Aprobado'
    ) AS approved_cases,

    COUNT(*) FILTER (
        WHERE status = 'Rechazado'
    ) AS rejected_cases,

    COUNT(*) FILTER (
        WHERE status = 'Anulado'
    ) AS cancelled_cases,

    COUNT(*) FILTER (
        WHERE sla_status = 'Dentro de SLA'
    ) AS within_sla_cases,

    COUNT(*) FILTER (
        WHERE sla_status = 'Fuera de SLA'
    ) AS outside_sla_cases,

    ROUND(
        (
            COUNT(*) FILTER (
                WHERE sla_status = 'Dentro de SLA'
            ) * 100.0
            / NULLIF(
                COUNT(*) FILTER (
                    WHERE sla_status IN (
                        'Dentro de SLA',
                        'Fuera de SLA'
                    )
                ),
                0
            )
        )::numeric,
        2
    ) AS sla_compliance_percentage,

    ROUND(
        AVG(resolution_hours)
        FILTER (WHERE resolution_hours IS NOT NULL)::numeric,
        2
    ) AS average_resolution_hours

FROM portability_cases
GROUP BY
    received_year,
    received_month
ORDER BY
    received_year,
    received_month;