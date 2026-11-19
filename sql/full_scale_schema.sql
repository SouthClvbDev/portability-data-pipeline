-- Tabla independiente para la muestra de escala completa. No altera la tabla usada por la demo.
CREATE TABLE IF NOT EXISTS public.portability_cases_full (
    case_id text PRIMARY KEY,
    received_at timestamp NOT NULL,
    received_date date NOT NULL,
    received_year integer NOT NULL,
    received_month integer NOT NULL,
    received_month_name text NOT NULL,
    received_weekday text NOT NULL,
    closed_at timestamp,
    status text NOT NULL,
    is_closed boolean NOT NULL,
    is_pending boolean NOT NULL,
    channel text NOT NULL,
    team text NOT NULL,
    documentation_status text NOT NULL,
    has_documentation_pending boolean NOT NULL,
    contact_status text NOT NULL,
    has_contact_pending boolean NOT NULL,
    rejection_reason text,
    cancellation_reason text,
    resolution_hours double precision,
    sla_status text NOT NULL,
    CONSTRAINT portability_full_status_check CHECK (status IN ('Recibido', 'En análisis', 'Pendiente documentación', 'Pendiente contacto', 'Aprobado', 'Rechazado', 'Anulado')),
    CONSTRAINT portability_full_flags_check CHECK (is_closed <> is_pending),
    CONSTRAINT portability_full_closure_check CHECK (
        (is_closed AND status IN ('Aprobado', 'Rechazado', 'Anulado') AND closed_at IS NOT NULL AND resolution_hours >= 0 AND sla_status IN ('Dentro de SLA', 'Fuera de SLA'))
        OR (is_pending AND status NOT IN ('Aprobado', 'Rechazado', 'Anulado') AND closed_at IS NULL AND resolution_hours IS NULL AND sla_status = 'No aplica')
    )
);

CREATE INDEX IF NOT EXISTS portability_full_received_date_idx ON public.portability_cases_full (received_date);
CREATE INDEX IF NOT EXISTS portability_full_closed_at_idx ON public.portability_cases_full (closed_at);
CREATE INDEX IF NOT EXISTS portability_full_team_channel_idx ON public.portability_cases_full (team, channel);
