CREATE TABLE IF NOT EXISTS public.portability_cases (
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
    sla_status text NOT NULL
);

-- Permite actualizar una base creada por versiones anteriores de pandas.to_sql.
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid = 'public.portability_cases'::regclass AND contype = 'p') THEN
        ALTER TABLE public.portability_cases ADD CONSTRAINT portability_cases_pkey PRIMARY KEY (case_id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid = 'public.portability_cases'::regclass AND conname = 'portability_cases_status_check') THEN
        ALTER TABLE public.portability_cases ADD CONSTRAINT portability_cases_status_check CHECK (status IN ('Recibido', 'En análisis', 'Pendiente documentación', 'Pendiente contacto', 'Aprobado', 'Rechazado', 'Anulado'));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid = 'public.portability_cases'::regclass AND conname = 'portability_cases_resolution_check') THEN
        ALTER TABLE public.portability_cases ADD CONSTRAINT portability_cases_resolution_check CHECK (resolution_hours IS NULL OR resolution_hours >= 0);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid = 'public.portability_cases'::regclass AND conname = 'portability_cases_flags_check') THEN
        ALTER TABLE public.portability_cases ADD CONSTRAINT portability_cases_flags_check CHECK (is_closed <> is_pending);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS portability_cases_received_date_idx ON public.portability_cases (received_date);
CREATE INDEX IF NOT EXISTS portability_cases_closed_at_idx ON public.portability_cases (closed_at);
CREATE INDEX IF NOT EXISTS portability_cases_team_channel_idx ON public.portability_cases (team, channel);
