# Bitácora del proyecto: Portability Data Pipeline

## Objetivo

Construir un pipeline reproducible con datos **sintéticos** de trámites de portabilidad para analizar la operación de Backoffice. El proyecto retoma la experiencia profesional con BigQuery, SAS Enterprise Guide y Power BI, pero utiliza Python, PostgreSQL y Docker en una implementación propia. No incorpora datos reales de Telecom.

## Mapa de archivos

| Archivo | Función |
|---|---|
| `src/generate_data.py` | Genera trámites ficticios de manera reproducible. |
| `data/sample/portability_cases.csv` | Muestra sintética generada, versionada en Git. |
| `src/validation/validate_data.py` | Comprueba estructura y reglas de calidad antes del procesamiento. |
| `src/transformations/transform_cases.py` | Prepara campos analíticos, indicadores y clasificación de SLA. |
| `data/processed/portability_cases_clean.csv` | Salida transformada; se regenera y está excluida de Git. |
| `src/load_to_postgres.py` | Carga la salida transformada en PostgreSQL. |
| `docker-compose.yml` | Define el servicio local de PostgreSQL y su volumen. |
| `sql/analytics/01_operational_views.sql` | Define las cinco vistas de consulta para indicadores. |
| `dashboard/portability_operations.pbix` | Tablero de Power BI conectado a PostgreSQL (hito 8, según el avance reportado). |
| `requirements.txt` | Dependencias del entorno Python. |
| `.gitignore` | Excluye entorno virtual, archivos locales y datos procesados. |
| `README.md` | Presentación general del proyecto. |
| `docs/progress.md` | Esta bitácora de avances y decisiones. |

## Flujo

1. `src/generate_data.py` genera `data/sample/portability_cases.csv`.
2. `src/validation/validate_data.py` comprueba la calidad de la muestra.
3. `src/transformations/transform_cases.py` genera `data/processed/portability_cases_clean.csv`.
4. `src/load_to_postgres.py` carga la tabla `portability_cases`.
5. `sql/analytics/01_operational_views.sql` crea las vistas para consulta.
6. `dashboard/portability_operations.pbix` consume los datos en Power BI.

## Hitos completados

### 1. Configuración inicial

**Archivos:** `requirements.txt`, `.gitignore`, `README.md`.

- Se instalaron Git, Python, VS Code, Docker y WSL2 en Windows.
- Se creó el proyecto en `D:\DataDeveloper\proyectos\portability-data-pipeline` y se inicializó Git.
- Se usó Python 3.13 en `.venv` tras encontrar un problema de compilación de PyYAML con Python 3.15.
- Se comprobaron las importaciones principales y se registraron dependencias en `requirements.txt`.

### 2. Generación de datos sintéticos

**Archivo:** `src/generate_data.py`. **Salida:** `data/sample/portability_cases.csv`.

- Se generaron 5000 casos ficticios con semilla fija (`42`).
- Cada caso contiene identificador, fechas, estado, canal, equipo, situación documental y de contacto, motivos y horas de resolución cuando corresponde.
- Se corrigieron las reglas para que `Pendiente contacto` implique contacto pendiente y `Pendiente documentación` implique documentación incompleta.
- Los casos finalizados reciben fecha de cierre y horas de resolución.

### 3. Validación de calidad

**Archivo:** `src/validation/validate_data.py`.

- Se comprueban columnas requeridas, identificadores vacíos o duplicados, fechas, estados válidos y coherencia entre estado, cierre y motivos.
- Se comprueban las reglas de contacto y documentación pendiente.
- La validación sobre el CSV regenerado no devolvió casos incoherentes para estas dos reglas.

### 4. Transformación analítica

**Archivo:** `src/transformations/transform_cases.py`. **Salida:** `data/processed/portability_cases_clean.csv`.

- Se añadieron fecha, año, mes, nombre del mes y día de la semana de recepción.
- Se añadieron indicadores de caso cerrado o pendiente, documentación y contacto pendientes.
- Se clasificó el SLA de los casos resueltos con umbral de 48 horas; los demás quedan como `No aplica`.
- La ejecución informó 5000 registros, 21 columnas y la distribución: 2430 `No aplica`, 1953 `Dentro de SLA` y 617 `Fuera de SLA`.

### 5. PostgreSQL local

**Archivo:** `docker-compose.yml`.

- Se inició PostgreSQL 16 en Docker con la base `portability_db`, el contenedor `portability-postgres` y el puerto local `5432`.
- Los logs confirmaron que la base aceptaba conexiones y `docker compose ps` mostró el servicio activo.
- El volumen de Docker conserva los datos entre reinicios del contenedor; no viaja automáticamente al copiar la carpeta del proyecto.

### 6. Carga en PostgreSQL

**Archivo:** `src/load_to_postgres.py`. **Tabla:** `portability_cases`.

- Se instaló `psycopg2-binary` y se actualizó `requirements.txt`.
- Se cargó el CSV procesado mediante pandas y SQLAlchemy.
- Una consulta a PostgreSQL devolvió los siete estados con recuentos que suman 5000 casos.
- La carga actual usa reemplazo completo de la tabla (`if_exists="replace"`); todavía no es incremental.

### 7. Vistas analíticas SQL

**Archivo:** `sql/analytics/01_operational_views.sql`.

| Vista | Contenido |
|---|---|
| `vw_portability_kpis` | Volumen total, abiertos, cerrados, aprobados, rechazados, anulados y SLA. |
| `vw_cases_by_status` | Cantidad y proporción de cada estado. |
| `vw_daily_volume` | Casos agrupados por fecha de **recepción**, separados según su estado actual. |
| `vw_team_performance` | Cantidades por equipo y promedio de horas para casos resueltos. |
| `vw_sla_by_channel` | Casos dentro y fuera de SLA y porcentaje de cumplimiento por canal. |

- Se corrigieron expresiones `ROUND` convirtiendo a `numeric` los cálculos que PostgreSQL obtenía como `double precision`.
- La última ejecución devolvió cinco mensajes `CREATE VIEW`.
- **Interpretación:** `vw_daily_volume.closed_cases` agrupa por día de recepción a casos que hoy están cerrados; no mide cuántos se cerraron ese día. La mejora para medir cierres diarios debe agrupar por `closed_at`.

### 8. Dashboard en Power BI

**Archivo:** `dashboard/portability_operations.pbix` (nombre acordado para el tablero). **Origen:** PostgreSQL y las vistas de `sql/analytics/01_operational_views.sql`.

- Se conectó Power BI Desktop a `localhost:5432`, base `portability_db`, en modo Importar, según el avance indicado.
- La página `Resumen Operativo` reúne tarjetas de volumen y estado, evolución por fecha de recepción, análisis por equipo y SLA por canal.
- El archivo PBIX se guarda dentro de `dashboard/` para acompañar el proyecto.
- Al actualizar en otra computadora, primero se debe levantar PostgreSQL, recargar la tabla y recrear las vistas; luego se actualizan las credenciales y la conexión local de Power BI si hace falta.

## Ejecución desde la raíz del proyecto (PowerShell)

```powershell
.\.venv\Scripts\Activate.ps1
docker compose up -d
python src\generate_data.py
python src\validation\validate_data.py
python src\transformations\transform_cases.py
python src\load_to_postgres.py
Get-Content sql\analytics\01_operational_views.sql | docker exec -i portability-postgres psql -v ON_ERROR_STOP=1 -U data_user -d portability_db
```

Abrir `dashboard/portability_operations.pbix` en Power BI Desktop y usar **Actualizar** después de cargar la base y crear las vistas. `-v ON_ERROR_STOP=1` hace que `psql` corte la ejecución si una sentencia SQL falla.

## Próximas mejoras

- Definir métricas temporales precisas: ingresos por `received_at`, cierres por `closed_at` y backlog a una fecha de corte. Los estados actuales de la muestra no reconstruyen por sí solos el historial de transiciones.
- Crear una tabla calendario y un modelo que permita filtrar Power BI de forma coherente. Las vistas agregadas no comparten una dimensión de fecha/equipo/canal para que todos los segmentadores afecten a todos los gráficos.
- Incorporar pruebas automáticas y verificar la integridad de los datos cargados.
- Mover las credenciales locales de `docker-compose.yml` y del script de carga a variables de entorno antes de publicar el repositorio.
- Reemplazar la carga con `replace` por una estrategia idempotente o incremental y evaluar dbt/orquestación posteriormente.
