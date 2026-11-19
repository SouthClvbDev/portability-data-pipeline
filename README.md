# Portability Data Pipeline

[![CI](https://github.com/SouthClvbDev/portability-data-pipeline/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/SouthClvbDev/portability-data-pipeline/actions/workflows/ci.yml)

Proyecto de portfolio orientado a un perfil **Data Developer**, basado en un escenario operativo de trámites de portabilidad gestionados por un área de Backoffice.

El proyecto implementa un pipeline reproducible que genera datos sintéticos, valida reglas de calidad, transforma la información, carga PostgreSQL, crea una capa analítica SQL y alimenta un dashboard interactivo en Power BI. Una muestra diaria versionada permite que el portfolio web crezca con cada actualización. Un análisis Matplotlib muestra también la evolución del dataset de escala completa, mientras Docker/PostgreSQL sigue disponible para Power BI.

> El repositorio no utiliza información real de clientes, líneas telefónicas ni sistemas de Telecom. Todos los datos son ficticios.

## Objetivos

- Construir un pipeline de datos de punta a punta.
- Aplicar reglas de calidad y consistencia operativa.
- Implementar cargas completas e incrementales.
- Centralizar métricas mediante vistas de PostgreSQL.
- Crear indicadores y análisis temporales en Power BI.
- Incorporar pruebas automatizadas sobre archivos y base de datos.

## Tecnologías

- Python 3.13
- pandas y NumPy
- SQLAlchemy y psycopg2
- PostgreSQL 16
- Docker y Docker Compose
- SQL
- pytest
- Power BI Desktop
- Matplotlib (análisis visual opcional)
- Git
- PowerShell

## Arquitectura del flujo

```text
Lote inicial + incremental + muestra diaria versionada
                         │
                         v
              Validación y transformación
                         │
                         v
             PostgreSQL + vistas SQL + pruebas

CSV versionados ──> Build de Vercel ──> Portfolio web + asistente
CSV escala completa ──> Python/Matplotlib ──> Gráfico web agregado
CSV escala completa ──> PostgreSQL en Docker ──> Power BI
       ^
       │
GitHub Actions: generación diaria, validación y commit
```

## Estructura principal

```text
portability-data-pipeline/
├── dashboard/
│   └── portability_operations.pbix
├── data/
│   ├── processed/
│   └── sample/
│       ├── portability_cases.csv
│       ├── portability_cases_incremental.csv
│       ├── portability_cases_daily.csv
│       └── portability_cases_daily.meta.json
├── docs/
├── sql/
│   └── analytics/
│       ├── 01_operational_views.sql
│       ├── 02_monthly_metrics.sql
│       └── 03_observable_history.sql
├── src/
│   ├── generate_data.py
│   ├── generate_incremental_data.py
│   ├── generate_daily_data.py
│   ├── load_to_postgres.py
│   ├── transformations/
│   │   └── transform_cases.py
│   └── validation/
│       └── validate_data.py
├── tests/
│   ├── test_pipeline.py
│   ├── test_daily_data.py
│   └── test_database.py
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Flujo de ejecución

1. `src/generate_data.py` genera el lote inicial de 5.000 trámites.
2. `src/validation/validate_data.py` verifica estructura y reglas de negocio.
3. `src/transformations/transform_cases.py` crea 21 columnas analíticas.
4. `src/load_to_postgres.py --mode initial` realiza la carga inicial.
5. `src/generate_incremental_data.py` genera 2.500 trámites adicionales.
6. El transformador procesa el segundo lote mediante rutas configurables.
7. `src/load_to_postgres.py --mode append` incorpora solamente IDs nuevos.
8. `src/generate_daily_data.py` crea la extensión hasta la hora actual en Argentina; `--mode sync` agrega casos nuevos y actualiza cierres recientes.
9. Los scripts SQL crean vistas operativas, mensuales y de historia observable.
10. El build de Vercel calcula la web y el asistente desde los CSV versionados. Power BI consume la tabla local cuando el autor actualiza el informe.
11. pytest valida archivos, reglas, PostgreSQL y vistas.

## Muestra base y extensión diaria

| Indicador | Resultado |
|---|---:|
| Lote inicial | 5.000 |
| Lote incremental | 2.500 |
| Total tras la demo | 7.500 + casos del lote diario versionado |
| IDs duplicados | 0 |
| Período | 2023-01-01 hasta el corte declarado en `daily.meta.json` |
| Columnas analíticas | 21 |
| Vistas analíticas | Operativas, mensuales y de historia observable |
| Pruebas automatizadas | Pipeline y web; se ejecutan en CI |

## Inicio rápido

En Linux o macOS, desde la raíz del proyecto:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
bash scripts/demo.sh
```

La demo valida los tres CSV versionados, transforma y carga los casos, crea las vistas analíticas y ejecuta las pruebas. `bash scripts/demo.sh` puede repetirse; la carga inicial reconstruye los datos de muestra. Requiere Docker Compose y el puerto 5432 disponible. Para configurar las credenciales locales, copiá `.env.example` a `.env`; `.env` está excluido de Git. La [actualización diaria](docs/daily_synthetic_updates.md) explica la automatización y su fecha de corte.

En Windows PowerShell, seguí [el runbook](docs/runbook.md). Para ejecutar solo las pruebas, con PostgreSQL y los datos ya cargados:

```powershell
.\.venv\Scripts\Activate.ps1
docker compose up -d --wait
pytest -q
```

La arquitectura y sus límites están en [`docs/architecture.md`](docs/architecture.md). El flujo de GitHub Actions ejecuta esta misma demo en Python 3.13.

## Dashboard

El tablero `dashboard/portability_operations.pbix` contiene:

- **Resumen Operativo:** volumen, estados, backlog y SLA.
- **Análisis de demoras:** tiempos de resolución, motivos y desempeño.
- **Evolución Mensual:** tendencias y comparación T1 versus T2.

Power BI utiliza principalmente `public.portability_cases`, relacionada con una tabla calendario, para que los segmentadores afecten de forma coherente a todos los visuales. Las vistas SQL se conservan como capa analítica, validación y consumo alternativo.

El archivo PBIX requiere Power BI Desktop para verlo. La demo ejecutable y sus resultados se pueden comprobar sin Power BI. Las capturas de las tres páginas se incorporarán tras exportarlas desde Power BI Desktop; no se presentan imágenes reconstruidas como si fueran capturas del tablero.

La [guía de rediseño](docs/dashboard_design.md) detalla jerarquía, colores y distribución por página. Esta [maqueta del resumen](docs/dashboard_mockup.svg) muestra la dirección visual propuesta; no es una captura del PBIX.

## Portfolio web y asistente

La [web de portfolio](https://portability-data-pipeline.vercel.app/) explica el proyecto por etapas, calcula indicadores desde los CSV sintéticos e incluye cuatro escenarios guiados con cifras reproducibles. Un recorrido progresivo enlaza cada etapa con su código; un gráfico diario permite recorrer el backlog de 90 días, 12 meses o toda la historia. El análisis Matplotlib del dataset grande destaca [episodios sintéticos](docs/synthetic_story.md) de demora y recuperación. También presenta las tres páginas del informe Power BI y muestra capturas verificables cuando se exportan; por ahora indica cuáles están pendientes. El asistente responde preguntas con filtros combinados por mes, estado, canal y equipo, y backlog a una fecha; los números se calculan en el servidor. Funciona sin IA y admite interpretación opcional de preguntas con Gemini u OpenAI mediante una clave del servidor. La [documentación de la web](web/README.md) explica arquitectura, operación, límites y opciones de costo.

## Dataset de escala completa para Power BI

Además de la muestra ligera de la web, el proyecto puede generar desde enero de 2023 un [dataset sintético de escala completa](docs/full_scale_dataset.md). Los meses completos simulan entre 15.000 y 25.000 recepciones normales, con picos positivos y negativos. Se entrega como CSV comprimido con 21 columnas, un manifiesto de control y un lote incremental con solapamiento para capturar cierres recientes. Una carga con `COPY` lo coloca en `public.portability_cases_full` y el modo `sync` aplica los cambios recientes, sin alterar la tabla de la demo ni el PBIX. La tarea diaria ofrece los archivos como artefacto descargable de GitHub Actions; no se versiona el archivo grande en Git.

## Calidad y pruebas

Las pruebas verifican:

- estructura, columnas y cantidad de registros;
- IDs únicos y sin solapamiento entre lotes;
- fechas y estados permitidos;
- reglas de contacto, documentación, cierre y motivos;
- clasificación del SLA;
- conexión y cantidad de registros en PostgreSQL;
- consistencia entre tabla base y vistas;
- existencia de las vistas analíticas;
- restricciones de unicidad y estados en PostgreSQL.

## Documentación

- [`docs/architecture.md`](docs/architecture.md)
- [`docs/data_dictionary.md`](docs/data_dictionary.md)
- [`docs/data_quality.md`](docs/data_quality.md)
- [`docs/incremental_loading.md`](docs/incremental_loading.md)
- [`docs/powerbi_dashboard.md`](docs/powerbi_dashboard.md)
- [`docs/progress.md`](docs/progress.md)
- [`docs/runbook.md`](docs/runbook.md)
- [`docs/technical_decisions.md`](docs/technical_decisions.md)
- [`docs/demo_video_plan.md`](docs/demo_video_plan.md)
- [`docs/next_scenarios.md`](docs/next_scenarios.md)
- [`docs/observable_history.md`](docs/observable_history.md)
- [`docs/daily_synthetic_updates.md`](docs/daily_synthetic_updates.md)
- [`docs/full_scale_dataset.md`](docs/full_scale_dataset.md)
- [`docs/release_v1.0.md`](docs/release_v1.0.md)
- [`web/README.md`](web/README.md)

## Estado

El pipeline, la carga incremental y la extensión diaria, la capa SQL, el dashboard, la web y las pruebas automatizadas están implementados. CI y la generación diaria están configurados en GitHub Actions. La historia observable de ingresos y cierres permite calcular backlog diario; los cambios entre estados intermedios aún necesitan un registro propio. El PBIX sigue bajo edición del autor y no se modifica ni se refresca con la tarea diaria.

