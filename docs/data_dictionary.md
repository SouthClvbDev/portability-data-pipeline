# Diccionario de datos

Fuente: `data/sample/portability_cases.csv`. Salida transformada: `data/processed/portability_cases_clean.csv`. Tabla destino: `public.portability_cases`.

Los tipos físicos y restricciones se definen en [`sql/schema.sql`](../sql/schema.sql). Se pueden comprobar en PostgreSQL con `\d public.portability_cases`.

| Campo | Tipo lógico | Origen y significado |
|---|---|---|
| `case_id` | Texto | ID ficticio único, formato `PORT-000001`. |
| `received_at` | Fecha y hora | Recepción del trámite; generado entre enero y marzo de 2023. |
| `closed_at` | Fecha y hora, opcional | Cierre de un caso finalizado; vacío para casos abiertos. |
| `status` | Categoría | Estado actual del trámite. |
| `channel` | Categoría | Canal de ingreso: Web, App, Sucursal, Call Center o Distribuidor. |
| `team` | Categoría | Equipo ficticio: Backoffice Norte, Centro o Sur. |
| `documentation_status` | Categoría | Completa, Incompleta o No requerida. |
| `contact_status` | Categoría | Realizado, Pendiente o No corresponde. |
| `rejection_reason` | Texto, opcional | Motivo presente cuando `status = Rechazado`. |
| `cancellation_reason` | Texto, opcional | Motivo presente cuando `status = Anulado`. |
| `resolution_hours` | Decimal, opcional | Horas corridas entre recepción y cierre, generadas para casos finalizados. |
| `received_date` | Fecha | Día de `received_at`, sin hora; creado en la transformación. |
| `received_year` | Entero | Año de recepción. |
| `received_month` | Entero | Número de mes de recepción, 1 a 12. |
| `received_month_name` | Texto | Nombre del mes de recepción; depende de la configuración regional al generarlo. |
| `received_weekday` | Texto | Día de la semana de recepción; depende de la configuración regional. |
| `is_closed` | Booleano | Verdadero si el estado es Aprobado, Rechazado o Anulado. |
| `is_pending` | Booleano | Inverso de `is_closed`; indica que el caso sigue abierto. |
| `has_documentation_pending` | Booleano | Verdadero si `documentation_status = Incompleta`. |
| `has_contact_pending` | Booleano | Verdadero si `contact_status = Pendiente`. |
| `sla_status` | Categoría | Dentro de SLA (≤48 h), Fuera de SLA (>48 h), No aplica (sin resolución). |

## Reglas importantes

- `case_id` debe ser único y no nulo; `received_at` debe ser una fecha válida.
- Los estados permitidos son Recibido, En análisis, Pendiente documentación, Pendiente contacto, Aprobado, Rechazado y Anulado.
- Los casos finalizados deben tener `closed_at` y `resolution_hours`; los abiertos no deben tener `closed_at`.
- `closed_at` no puede ser anterior a `received_at`.
- Un caso `Pendiente contacto` debe tener `contact_status = Pendiente`; uno `Pendiente documentación` debe tener `documentation_status = Incompleta`.
- Un caso Rechazado debe tener `rejection_reason`; uno Anulado debe tener `cancellation_reason`.

## Granularidad y métricas

Cada fila de `portability_cases` es **un trámite**. Total de casos = cantidad de filas/IDs únicos. Abiertos = estados no finales; cerrados = estados finales. Tasa de aprobación puede significar aprobados/total o aprobados/cerrados: indicar siempre cuál denominador se usa. Porcentaje de SLA = dentro de SLA / (dentro + fuera), excluyendo `No aplica`.
