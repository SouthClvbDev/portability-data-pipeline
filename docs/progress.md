# Bitácora del proyecto: Portability Data Pipeline

## Objetivo

Construir un pipeline reproducible con datos **sintéticos** de trámites de portabilidad para analizar una operación de Backoffice. El proyecto retoma experiencia profesional previa con BigQuery, SAS Enterprise Guide y Power BI, pero utiliza Python, PostgreSQL y Docker en una implementación propia.

No se incorporan datos reales de Telecom ni información personal de clientes.

## Mapa de archivos

| Archivo | Responsabilidad |
|---|---|
| `src/generate_data.py` | Genera el lote inicial de 5.000 casos. |
| `src/generate_incremental_data.py` | Genera un segundo lote de 2.500 casos. |
| `data/sample/portability_cases.csv` | Dataset sintético inicial versionado. |
| `data/sample/portability_cases_incremental.csv` | Dataset incremental versionado. |
| `src/validation/validate_data.py` | Valida estructura y reglas de negocio. |
| `src/transformations/transform_cases.py` | Transforma cualquier lote mediante `--input` y `--output`. |
| `src/load_to_postgres.py` | Ejecuta cargas `initial` y `append`. |
| `sql/analytics/01_operational_views.sql` | Crea cinco vistas operativas. |
| `sql/analytics/02_monthly_metrics.sql` | Crea la vista de métricas mensuales. |
| `tests/test_pipeline.py` | Pruebas de archivos y reglas del pipeline. |
| `tests/test_database.py` | Pruebas de PostgreSQL y vistas. |
| `dashboard/portability_operations.pbix` | Dashboard de Power BI. |
| `docker-compose.yml` | PostgreSQL local y volumen persistente. |

## Flujo actual

1. Generación del lote inicial.
2. Validación de calidad.
3. Transformación analítica.
4. Carga inicial conservando las vistas existentes.
5. Generación y transformación del lote incremental.
6. Carga idempotente de IDs nuevos.
7. Construcción de vistas operativas y mensuales.
8. Consumo desde Power BI.
9. Pruebas automatizadas de archivos y PostgreSQL.

## Hitos completados

### 1. Configuración inicial

**Archivos:** `requirements.txt`, `.gitignore`, `README.md`.

- Se instalaron Git, Python, VS Code, Docker y WSL2 en Windows.
- Se creó el proyecto en `D:\DataDeveloper\proyectos\portability-data-pipeline`.
- Se inicializó Git y se configuró la identidad del repositorio.
- Se utilizó Python 3.13 en `.venv` tras detectar incompatibilidades de paquetes con Python 3.15.
- Se registraron las dependencias en `requirements.txt`.

### 2. Generación inicial

**Archivo:** `src/generate_data.py`.

- Se generaron 5.000 trámites con semilla `42`.
- Se incluyeron estados, fechas, canales, equipos, documentación, contacto, motivos y horas de resolución.
- Se implementaron reglas coherentes para pendientes y casos finalizados.
- La salida se guardó en `data/sample/portability_cases.csv`.

### 3. Validación de calidad

**Archivo:** `src/validation/validate_data.py`.

- Columnas obligatorias.
- IDs vacíos o duplicados.
- Estados permitidos.
- Coherencia de fechas de recepción y cierre.
- Casos abiertos y finalizados.
- Reglas de contacto y documentación.
- Motivos de rechazo y anulación.
- Horas de resolución.

### 4. Transformación analítica

**Archivo:** `src/transformations/transform_cases.py`.

- El script acepta `--input` y `--output` para transformar distintos lotes.
- Se crearon 21 columnas finales.
- Se agregaron dimensiones temporales e indicadores booleanos.
- Se clasificó el SLA con un umbral sintético de 48 horas.

Distribución inicial:

| SLA | Casos |
|---|---:|
| No aplica | 2.430 |
| Dentro de SLA | 1.953 |
| Fuera de SLA | 617 |

### 5. PostgreSQL local

**Archivo:** `docker-compose.yml`.

- PostgreSQL 16 en Docker.
- Base: `portability_db`.
- Usuario de desarrollo: `data_user`.
- Contenedor: `portability-postgres`.
- Puerto: `5432`.
- Volumen persistente: `postgres_data`.

### 6. Carga inicial e incremental

**Archivo:** `src/load_to_postgres.py`.

Se implementaron dos modos:

- `initial`: vacía la tabla mediante `TRUNCATE` y carga el dataset sin eliminar las vistas dependientes.
- `append`: consulta IDs existentes y agrega solamente registros nuevos.

La estrategia incremental es idempotente. La segunda ejecución del mismo lote agregó cero registros.

| Carga | Registros |
|---|---:|
| Inicial | 5.000 |
| Incremental | 2.500 |
| Total | 7.500 |
| Duplicados | 0 |

### 7. Capa analítica SQL

**Archivos:** `sql/analytics/01_operational_views.sql` y `02_monthly_metrics.sql`.

| Vista | Contenido |
|---|---|
| `vw_portability_kpis` | KPI generales, abiertos, cerrados, estados y SLA. |
| `vw_cases_by_status` | Cantidad y porcentaje por estado. |
| `vw_daily_volume` | Casos agrupados por fecha de recepción. |
| `vw_team_performance` | Volumen, estados y resolución por equipo. |
| `vw_sla_by_channel` | Cumplimiento de SLA por canal. |
| `vw_monthly_operational_metrics` | Métricas operativas por mes. |

Decisiones y correcciones:

- Conversión explícita a `numeric` para `ROUND`.
- Uso de `is_pending` e `is_closed` para centralizar la definición de abierto/cerrado.
- Ejecución de scripts desde PowerShell con `-Raw -Encoding UTF8`.
- Las vistas se preservan durante la carga inicial.

### 8. Dashboard Power BI

**Archivo:** `dashboard/portability_operations.pbix`.

Se conectó Power BI a PostgreSQL en modo Importar. El modelo utiliza principalmente la tabla base `public.portability_cases` y una tabla `Calendario`.

Páginas implementadas:

1. **Resumen Operativo**
   - total, abiertos, cerrados, aprobados, rechazados y anulados;
   - casos dentro y fuera de SLA;
   - cumplimiento de SLA;
   - análisis por estado, fecha, equipo y canal.
2. **Análisis de demoras**
   - promedio y mediana de resolución;
   - porcentaje fuera de SLA;
   - rechazos y anulaciones;
   - motivos y desempeño por equipo.
3. **Evolución Mensual**
   - volumen mensual;
   - abiertos y cerrados;
   - SLA mensual;
   - estados por mes;
   - comparación T1 enero-marzo versus T2 abril-junio.

Resultados generales actuales:

| Indicador | Valor |
|---|---:|
| Total | 7.500 |
| Abiertos | 3.676 |
| Cerrados | 3.824 |
| Aprobados | 2.464 |
| Rechazados | 889 |
| Anulados | 471 |
| Dentro de SLA | 2.927 |
| Fuera de SLA | 897 |
| Cumplimiento SLA | 76,54 % |

### 9. Pruebas del pipeline

**Archivo:** `tests/test_pipeline.py`.

- Se agregaron 16 pruebas.
- Se validan los lotes inicial e incremental.
- Se comprueban cantidades, IDs, fechas, columnas, reglas de negocio y ausencia de solapamiento.

### 10. Pruebas de PostgreSQL

**Archivo:** `tests/test_database.py`.

- Se agregaron 6 pruebas de integración.
- Se valida conexión, total, unicidad, abiertos/cerrados, vista mensual y existencia de vistas.
- Resultado actual del proyecto: **24 pruebas exitosas**.

## Estado actual

- Pipeline reproducible: completo.
- Carga inicial: completa.
- Carga incremental idempotente: completa.
- Capa analítica SQL: completa.
- Dashboard de tres páginas: funcional.
- Pruebas automatizadas: 24 exitosas.
- Git: cambios versionados mediante commits descriptivos.

## Próximas mejoras

- Agregar CI para ejecutar pruebas automáticamente.
- Medir cierres diarios por `closed_at`, no solo por fecha de recepción.
- Modelar historial de transiciones para reconstruir backlog a una fecha de corte.
- Incorporar CI para ejecutar pytest automáticamente.
- Evaluar dbt u orquestación cuando el alcance lo justifique.
- Publicar el repositorio y preparar capturas del dashboard.

