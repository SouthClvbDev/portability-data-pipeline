# Portability Data Pipeline

[![CI](https://github.com/SouthClvbDev/portability-data-pipeline/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/SouthClvbDev/portability-data-pipeline/actions/workflows/ci.yml)

Proyecto de portfolio orientado a un perfil **Data Developer**, basado en un escenario operativo de trámites de portabilidad gestionados por un área de Backoffice.

El proyecto implementa un pipeline reproducible que genera datos sintéticos, valida reglas de calidad, transforma la información, carga PostgreSQL, crea una capa analítica SQL y alimenta un dashboard interactivo en Power BI.

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
- Git
- PowerShell

## Arquitectura del flujo

```text
Generador inicial (5.000 casos) ─┐
                                ├─> Validación y transformación
Generador incremental (2.500) ──┘              │
                                               v
                                    PostgreSQL: 7.500 casos
                                               │
                         ┌─────────────────────┴─────────────────────┐
                         v                                           v
                Vistas analíticas SQL                       Pruebas de base
                         │
                         v
                     Power BI
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
│       └── portability_cases_incremental.csv
├── docs/
├── sql/
│   └── analytics/
│       ├── 01_operational_views.sql
│       └── 02_monthly_metrics.sql
├── src/
│   ├── generate_data.py
│   ├── generate_incremental_data.py
│   ├── load_to_postgres.py
│   ├── transformations/
│   │   └── transform_cases.py
│   └── validation/
│       └── validate_data.py
├── tests/
│   ├── test_pipeline.py
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
8. Los scripts SQL crean vistas operativas y mensuales.
9. Power BI consume la tabla base y presenta tres páginas analíticas.
10. pytest valida archivos, reglas, PostgreSQL y vistas.

## Resultados actuales

| Indicador | Resultado |
|---|---:|
| Lote inicial | 5.000 |
| Lote incremental | 2.500 |
| Total en PostgreSQL | 7.500 |
| IDs duplicados | 0 |
| Período | 2023-01-01 a 2023-06-30 |
| Columnas analíticas | 21 |
| Vistas analíticas | 6 |
| Pruebas automatizadas | 24 exitosas |

## Inicio rápido

En Linux o macOS, desde la raíz del proyecto:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
bash scripts/demo.sh
```

La demo valida ambos CSV, transforma y carga 7.500 casos, crea las seis vistas y ejecuta las pruebas. `bash scripts/demo.sh` puede repetirse; la carga inicial reconstruye los datos de muestra. Requiere Docker Compose y el puerto 5432 disponible. Para configurar las credenciales locales, copiá `.env.example` a `.env`; `.env` está excluido de Git.

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

## Calidad y pruebas

Las pruebas verifican:

- estructura, columnas y cantidad de registros;
- IDs únicos y sin solapamiento entre lotes;
- fechas y estados permitidos;
- reglas de contacto, documentación, cierre y motivos;
- clasificación del SLA;
- conexión y cantidad de registros en PostgreSQL;
- consistencia entre tabla base y vistas;
- existencia de las seis vistas analíticas.
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
- [`docs/release_v1.0.md`](docs/release_v1.0.md)

## Estado

El pipeline, la carga incremental, la capa SQL, el dashboard y las pruebas automatizadas están implementados. Las próximas mejoras posibles son CI, historial de cambios de estado y capturas verificables del dashboard.

