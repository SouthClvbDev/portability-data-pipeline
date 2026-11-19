# Cómo funciona el Portability Data Pipeline

## 1. Explicación general

`Portability Data Pipeline` es un proyecto de portfolio que reproduce un flujo de datos para analizar trámites de portabilidad numérica gestionados por un área de Backoffice.

El proyecto parte de una experiencia laboral real —extracción desde BigQuery, modelado con SAS Enterprise Guide y visualización en Power BI— y la reconstruye con herramientas actuales de Data Development: Python, PostgreSQL, Docker, SQL, pytest y Power BI.

Los datos utilizados son completamente sintéticos. No se incluyen clientes, líneas, trámites ni información interna real.

El pipeline resuelve este recorrido:

```text
Datos sintéticos
      ↓
Validación de calidad
      ↓
Transformación analítica
      ↓
Carga inicial e incremental
      ↓
PostgreSQL
      ↓
Vistas analíticas SQL
      ↓
Power BI
      ↓
Indicadores operativos
```

Además, se incorporan pruebas automatizadas sobre los archivos, las reglas de negocio, la base de datos y las vistas.

## 2. Problema que representa

Un área de Backoffice recibe trámites de portabilidad por distintos canales y los distribuye entre equipos. Cada trámite atraviesa estados como recibido, en análisis, pendiente, aprobado, rechazado o anulado.

La operación necesita responder preguntas como:

- ¿Cuántos trámites se recibieron?
- ¿Cuántos continúan abiertos?
- ¿Cuántos finalizaron?
- ¿Qué porcentaje se resolvió dentro del SLA?
- ¿Qué equipos y canales concentran más casos?
- ¿Cuáles son los motivos principales de rechazo o anulación?
- ¿Cómo cambia el volumen y el desempeño mes a mes?

El pipeline transforma registros operativos en información apta para responder estas preguntas.

## 3. Arquitectura

```text
┌───────────────────────────────┐
│ Generación inicial            │
│ 5.000 trámites                │
│ ene-mar 2023                  │
└───────────────┬───────────────┘
                │
                ├───────────────┐
                │               │
┌───────────────▼───────────────▼┐
│ Validación y transformación    │
│ Python + pandas                │
└───────────────┬────────────────┘
                │
┌───────────────▼───────────────┐
│ Carga inicial                 │
│ PostgreSQL en Docker          │
└───────────────┬───────────────┘
                │
┌───────────────▼───────────────┐
│ Generación incremental        │
│ 2.500 trámites                │
│ abr-jun 2023                  │
└───────────────┬───────────────┘
                │
┌───────────────▼───────────────┐
│ Carga idempotente             │
│ Solo case_id nuevos           │
└───────────────┬───────────────┘
                │
┌───────────────▼───────────────┐
│ PostgreSQL: 7.500 trámites    │
│ Tabla base + 6 vistas         │
└───────────────┬───────────────┘
                │
┌───────────────▼───────────────┐
│ Power BI                      │
│ 3 páginas analíticas          │
└───────────────────────────────┘
```

## 4. Etapa 1: generación de datos

### Lote inicial

El archivo `src/generate_data.py` crea 5.000 trámites sintéticos con una semilla fija. La semilla hace que el resultado sea reproducible: ejecutar nuevamente el script produce el mismo conjunto de datos.

Cada trámite incluye:

- `case_id`;
- fecha de recepción y cierre;
- estado;
- canal de ingreso;
- equipo de Backoffice;
- estado de documentación;
- estado de contacto;
- motivo de rechazo o anulación;
- horas de resolución.

El generador también aplica reglas de negocio. Por ejemplo:

- un caso `Pendiente contacto` tiene el contacto pendiente;
- un caso `Pendiente documentación` tiene documentación incompleta;
- un caso finalizado tiene fecha de cierre y horas de resolución;
- un rechazo tiene motivo de rechazo;
- una anulación tiene motivo de anulación.

### Lote incremental

`src/generate_incremental_data.py` crea 2.500 registros adicionales con:

- IDs desde `PORT-005001` hasta `PORT-007500`;
- fechas entre abril y junio de 2023;
- las mismas columnas y reglas que el lote inicial.

Este segundo lote permite simular crecimiento de la base y comprobar que el pipeline no depende de una única carga estática.

## 5. Etapa 2: validación de calidad

`src/validation/validate_data.py` controla el dataset antes de transformarlo.

Las validaciones incluyen:

- columnas obligatorias;
- IDs vacíos o duplicados;
- fechas válidas;
- estados permitidos;
- fecha de cierre posterior a la recepción;
- casos finalizados con cierre;
- casos abiertos sin cierre;
- consistencia de documentación y contacto;
- motivos obligatorios para rechazo y anulación;
- presencia de horas de resolución cuando corresponde.

Esta etapa evita que datos incoherentes avancen hacia PostgreSQL y Power BI.

## 6. Etapa 3: transformación analítica

`src/transformations/transform_cases.py` convierte los datos operativos en un dataset preparado para análisis.

El script acepta parámetros:

```powershell
--input
--output
```

Por eso puede procesar el lote inicial y cualquier lote incremental sin duplicar código.

Las principales columnas derivadas son:

- fecha, año, mes y día de la semana de recepción;
- `is_closed`;
- `is_pending`;
- documentación pendiente;
- contacto pendiente;
- `sla_status`.

### Clasificación de SLA

Para el proyecto se definió un umbral sintético de 48 horas:

```text
resolution_hours <= 48  → Dentro de SLA
resolution_hours > 48   → Fuera de SLA
sin resolución          → No aplica
```

El dataset transformado contiene 21 columnas.

## 7. Etapa 4: PostgreSQL en Docker

PostgreSQL 16 se ejecuta mediante `docker-compose.yml`.

Docker permite que la infraestructura sea reproducible: otra persona puede levantar una base compatible sin instalar ni configurar manualmente PostgreSQL.

La tabla principal es:

```text
public.portability_cases
```

Cada fila representa un trámite. Mantener esta granularidad permite analizar los datos desde distintos ángulos y construir medidas dinámicas en Power BI.

## 8. Etapa 5: carga inicial

`src/load_to_postgres.py --mode initial` carga el dataset completo.

La implementación no elimina la tabla cuando ya existe. En su lugar:

1. verifica la existencia de `portability_cases`;
2. ejecuta `TRUNCATE`;
3. inserta el dataset;
4. conserva las vistas que dependen de la tabla.

Esta decisión resolvió un problema real: `if_exists="replace"` intentaba borrar la tabla, pero PostgreSQL lo impedía porque las vistas dependían de ella.

## 9. Etapa 6: carga incremental

El modo `append` agrega únicamente registros cuyo `case_id` todavía no existe.

El proceso es:

1. leer el archivo transformado;
2. validar IDs dentro del lote;
3. consultar IDs existentes en PostgreSQL;
4. filtrar coincidencias;
5. insertar solamente filas nuevas;
6. informar registros insertados, ignorados y total final.

La carga es idempotente. Esto significa que ejecutar dos veces el mismo lote no cambia el resultado después de la primera ejecución.

Primera ejecución:

```text
Registros nuevos: 2.500
Total: 7.500
```

Segunda ejecución:

```text
Registros nuevos: 0
Total: 7.500
```

## 10. Etapa 7: capa analítica SQL

PostgreSQL contiene seis vistas:

| Vista | Propósito |
|---|---|
| `vw_portability_kpis` | KPI generales de volumen, estados y SLA. |
| `vw_cases_by_status` | Cantidad y porcentaje por estado. |
| `vw_daily_volume` | Volumen agrupado por fecha de recepción. |
| `vw_team_performance` | Desempeño y resolución por equipo. |
| `vw_sla_by_channel` | Cumplimiento de SLA por canal. |
| `vw_monthly_operational_metrics` | Evolución operativa mensual. |

Las vistas centralizan consultas frecuentes y sirven para validar que PostgreSQL y Power BI produzcan resultados coherentes.

La definición de abiertos y cerrados utiliza `is_pending` e `is_closed`. Esto evita repetir listas de estados y reduce errores provocados por diferencias de texto o codificación.

## 11. Etapa 8: Power BI

Power BI se conecta a PostgreSQL en modo Importar.

El modelo utiliza principalmente la tabla detallada `portability_cases` y una tabla calendario. Esta decisión permite que los segmentadores de fecha, equipo y canal afecten correctamente todos los visuales.

Las vistas agregadas se conservan como capa SQL de consulta y validación, pero no se relacionan con la tabla base dentro del modelo para evitar relaciones ambiguas.

### Página 1: Resumen Operativo

- total, abiertos y cerrados;
- aprobados, rechazados y anulados;
- dentro y fuera de SLA;
- cumplimiento de SLA;
- análisis por estado, equipo y canal.

### Página 2: Análisis de demoras

- promedio y mediana de resolución;
- porcentaje fuera de SLA;
- motivos de rechazo y anulación;
- tiempo de resolución por equipo.

### Página 3: Evolución Mensual

- volumen por mes;
- abiertos y cerrados;
- SLA mensual;
- estados por mes;
- comparación entre T1 y T2.

## 12. Etapa 9: pruebas automatizadas

El proyecto contiene 24 pruebas con pytest.

### Pruebas del pipeline: 16

Validan:

- archivos y cantidades;
- IDs únicos;
- estados y fechas;
- reglas de negocio;
- SLA;
- compatibilidad de los lotes;
- ausencia de IDs compartidos.

### Pruebas de PostgreSQL: 6

Validan:

- conexión a la base;
- 7.500 registros;
- IDs únicos;
- consistencia de la vista KPI;
- abiertos más cerrados igual a total;
- métricas mensuales y existencia de vistas.

Resultado actual:

```text
24 passed
```

## 13. Resultados del pipeline

| Indicador | Resultado |
|---|---:|
| Registros iniciales | 5.000 |
| Registros incrementales | 2.500 |
| Total en PostgreSQL | 7.500 |
| Duplicados | 0 |
| Período | enero-junio 2023 |
| Columnas analíticas | 21 |
| Vistas SQL | 6 |
| Pruebas | 24 exitosas |
| Páginas de Power BI | 3 |

KPI generales del dataset:

| KPI | Valor |
|---|---:|
| Abiertos | 3.676 |
| Cerrados | 3.824 |
| Aprobados | 2.464 |
| Rechazados | 889 |
| Anulados | 471 |
| Dentro de SLA | 2.927 |
| Fuera de SLA | 897 |
| Cumplimiento SLA | 76,54 % |

## 14. Decisiones que muestran habilidades de Data Developer

El valor del proyecto no está solamente en el dashboard. También demuestra:

- separación de responsabilidades entre generación, validación, transformación y carga;
- diseño reproducible;
- reglas de calidad explícitas;
- cargas completas e incrementales;
- idempotencia;
- modelado detallado y capa analítica;
- SQL para indicadores;
- integración entre Python, PostgreSQL y Power BI;
- pruebas unitarias y de integración;
- documentación y control de versiones.

## 15. Limitaciones conocidas

### Escalabilidad de la carga

La implementación incremental actual lleva los IDs existentes a memoria. Es adecuada para miles de registros y un proyecto de portfolio, pero no para millones.

Una evolución productiva utilizaría:

- tabla staging;
- clave primaria sobre `case_id`;
- `COPY` para carga masiva;
- `INSERT ... ON CONFLICT` o `MERGE`;
- auditoría de lotes.

### Historial operativo

El dataset registra el estado actual del trámite, pero no todas sus transiciones. Por eso no permite reconstruir con precisión el backlog histórico a cualquier fecha.

Para hacerlo se necesitaría una tabla de eventos o snapshots periódicos.

### SLA

El límite de 48 horas es sintético y no representa un compromiso contractual real.

## 16. Evoluciones posibles

- Variables de entorno mediante `.env.example`.
- Constraints e índices en PostgreSQL.
- CI con GitHub Actions.
- Staging y upsert en SQL.
- Registro de auditoría de cargas.
- Orquestación con Airflow, Prefect o Dagster.
- Transformaciones administradas con dbt.
- Publicación de capturas y dashboard en el portfolio.

## 17. Cómo explicarlo en una entrevista

### Versión de 30 segundos

> Desarrollé un pipeline de datos sintéticos para analizar trámites de portabilidad de un Backoffice. Genera y valida los datos con Python, los transforma en un modelo analítico, realiza cargas iniciales e incrementales idempotentes en PostgreSQL sobre Docker y expone métricas mediante vistas SQL y un dashboard de Power BI. El proyecto maneja 7.500 registros, tiene seis vistas y 24 pruebas automatizadas.

### Versión de dos minutos

> El proyecto nace de una experiencia que tuve trabajando con trámites de portabilidad. Quise reconstruir ese flujo con herramientas actuales y sin utilizar datos reales. Primero genero un lote inicial de 5.000 trámites y otro incremental de 2.500. Antes de cargar, valido IDs, fechas, estados y reglas operativas, y después genero 21 columnas analíticas, incluyendo indicadores de casos abiertos, cerrados y SLA.
>
> PostgreSQL corre en Docker. La carga inicial usa TRUNCATE para conservar las vistas, y la incremental compara los case_id existentes para insertar únicamente registros nuevos. Si vuelvo a ejecutar el mismo lote, no genera duplicados. Sobre la tabla detallada construí seis vistas SQL y conecté Power BI para crear páginas de resumen, demoras y evolución mensual.
>
> Finalmente agregué 24 pruebas automatizadas: 16 sobre archivos y reglas del pipeline y 8 sobre PostgreSQL y sus vistas. También documenté decisiones y limitaciones, como la necesidad de staging y cargas masivas para millones de registros.

## 18. Preguntas que podrían hacer y respuestas

### ¿Por qué PostgreSQL?

Porque permite persistencia, SQL analítico, integración sencilla con Python y Power BI, y una evolución natural hacia constraints, índices y cargas con staging.

### ¿Por qué Docker?

Para que la infraestructura sea reproducible y no dependa de una instalación manual específica de PostgreSQL.

### ¿Por qué Power BI usa la tabla base?

Porque mantiene el detalle por trámite y permite que los segmentadores afecten todas las medidas. Las vistas agregadas sirven para centralizar consultas y validar resultados.

### ¿Cómo evitás duplicados?

El modo incremental compara los `case_id` del lote con los existentes y solo inserta IDs nuevos. Además, las pruebas verifican unicidad y ausencia de solapamiento.

### ¿Qué mejorarías para producción?

Agregaría clave primaria, staging, `ON CONFLICT` o `MERGE`, auditoría de lotes, secretos externos, índices, CI y orquestación.

### ¿Qué aprendiste?

Que un pipeline no termina en transformar datos: también necesita controles de calidad, estrategias de carga repetibles, consistencia entre capas, pruebas y documentación.
