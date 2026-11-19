-- Eventos observables derivados de las fechas del caso. No inventa estados intermedios.
CREATE OR REPLACE VIEW public.vw_case_observed_events AS
SELECT case_id, received_at AS event_at, 'received'::text AS event_type, NULL::text AS resulting_status
FROM public.portability_cases
UNION ALL
SELECT case_id, closed_at AS event_at, 'closed'::text AS event_type, status AS resulting_status
FROM public.portability_cases
WHERE closed_at IS NOT NULL;

-- Corte al final del día: ingresos acumulados menos cierres acumulados.
CREATE OR REPLACE VIEW public.vw_daily_backlog AS
WITH bounds AS (
    SELECT min(received_at)::date AS first_day,
           max(greatest(received_at, coalesce(closed_at, received_at)))::date AS last_day
    FROM public.portability_cases
), days AS (
    SELECT generate_series(first_day, last_day, interval '1 day')::date AS day
    FROM bounds
), daily AS (
    SELECT event_at::date AS day,
           count(*) FILTER (WHERE event_type = 'received') AS received_cases,
           count(*) FILTER (WHERE event_type = 'closed') AS closed_cases
    FROM public.vw_case_observed_events
    GROUP BY event_at::date
)
SELECT days.day,
       coalesce(daily.received_cases, 0) AS received_cases,
       coalesce(daily.closed_cases, 0) AS closed_cases,
       sum(coalesce(daily.received_cases, 0) - coalesce(daily.closed_cases, 0))
           OVER (ORDER BY days.day) AS open_cases_eod
FROM days
LEFT JOIN daily USING (day);
