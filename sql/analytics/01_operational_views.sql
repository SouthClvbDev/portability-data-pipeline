-- Vista general de indicadores
CREATE OR REPLACE VIEW vw_portability_kpis AS
SELECT
    COUNT(*) AS total_cases,
    COUNT(*) FILTER (
        WHERE is_pending = true
    ) AS open_cases,
    COUNT(*) FILTER (
        WHERE is_closed = true
    ) AS closed_cases,
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
    ) AS outside_sla_cases
FROM portability_cases;


-- Distribución por estado
CREATE OR REPLACE VIEW vw_cases_by_status AS
SELECT
    status,
    COUNT(*) AS total_cases,
    ROUND(
    (
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ()
    )::numeric,
    2
) AS percentage
FROM portability_cases
GROUP BY status
ORDER BY total_cases DESC;


-- Evolución diaria
CREATE OR REPLACE VIEW vw_daily_volume AS
SELECT
    received_date,
    COUNT(*) AS received_cases,
    COUNT(*) FILTER (
        WHERE is_closed = true
    ) AS closed_cases,
    COUNT(*) FILTER (
        WHERE is_pending = true
    ) AS pending_cases
FROM portability_cases
GROUP BY received_date
ORDER BY received_date;


-- Rendimiento por equipo
CREATE OR REPLACE VIEW vw_team_performance AS
SELECT
    team,
    COUNT(*) AS total_cases,
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
        WHERE status IN (
            'Recibido',
            'En análisis',
            'Pendiente documentación',
            'Pendiente contacto'
        )
    ) AS pending_cases,
    ROUND(
    (
        AVG(resolution_hours)
        FILTER (WHERE resolution_hours IS NOT NULL)
    )::numeric,
    2
) AS average_resolution_hours
FROM portability_cases
GROUP BY team
ORDER BY total_cases DESC;


-- Cumplimiento de SLA por canal
CREATE OR REPLACE VIEW vw_sla_by_channel AS
SELECT
    channel,
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
) AS sla_compliance_percentage
FROM portability_cases
GROUP BY channel
ORDER BY sla_compliance_percentage DESC;