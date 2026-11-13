# Dashboard de Power BI

## Objetivo

Presentar de forma interactiva el volumen, estado, SLA, demoras y evolución de los trámites sintéticos de portabilidad.

## Fuente y modelo

- Servidor: `localhost:5432`
- Base: `portability_db`
- Modo: Importar
- Tabla principal: `public.portability_cases`
- Tabla temporal: `Calendario`
- Vistas SQL: utilizadas como capa de control y consulta alternativa

La tabla base se usa para las medidas y visuales interactivos porque conserva el nivel de detalle y permite que fecha, equipo y canal filtren coherentemente el informe. Las vistas agregadas no deben relacionarse con la tabla base para evitar relaciones ambiguas y filtros inesperados.

## Relación principal

```text
Calendario[Date] 1 ──── * portability_cases[received_date]
```

Dirección de filtro: desde `Calendario` hacia `portability_cases`.

## Tabla calendario

La tabla contiene fecha, año, mes, año-mes, día y día de la semana. El campo utilizado en los ejes mensuales debe ser de tipo fecha o estar ordenado por una columna numérica `YYYYMM`.

## Medidas principales

```dax
Total trámites =
DISTINCTCOUNT(portability_cases[case_id])
```

```dax
Casos abiertos =
CALCULATE(
    [Total trámites],
    KEEPFILTERS(portability_cases[is_pending] = TRUE())
)
```

```dax
Casos cerrados =
CALCULATE(
    [Total trámites],
    KEEPFILTERS(portability_cases[is_closed] = TRUE())
)
```

```dax
Dentro de SLA =
CALCULATE(
    [Total trámites],
    KEEPFILTERS(portability_cases[sla_status] = "Dentro de SLA")
)
```

```dax
Fuera de SLA =
CALCULATE(
    [Total trámites],
    KEEPFILTERS(portability_cases[sla_status] = "Fuera de SLA")
)
```

```dax
Cumplimiento SLA % =
DIVIDE(
    [Dentro de SLA],
    [Dentro de SLA] + [Fuera de SLA]
)
```

```dax
Tiempo promedio de resolución =
AVERAGE(portability_cases[resolution_hours])
```

## Página 1: Resumen Operativo

### Tarjetas

- Total de trámites
- Casos abiertos
- Casos cerrados
- Aprobados
- Rechazados
- Anulados
- Dentro de SLA
- Fuera de SLA
- Cumplimiento de SLA

### Visuales

- Trámites por estado
- Evolución por fecha de recepción
- Volumen por equipo
- Fuera de SLA por equipo
- Fuera de SLA por canal

### Segmentadores

- Fecha de calendario
- Equipo
- Canal

## Página 2: Análisis de demoras

### Tarjetas

- Tiempo promedio de resolución
- Tiempo mediano de resolución
- Casos fuera de SLA %
- Porcentaje de rechazos
- Porcentaje de anulaciones

### Visuales

- Rechazos por motivo
- Anulaciones por motivo
- Tiempo promedio de resolución por equipo

Las medidas deben usar `portability_cases` y no las vistas agregadas para conservar el contexto de filtro.

## Página 3: Evolución Mensual

### Tarjetas generales

- Total
- Abiertos
- Cerrados
- Cumplimiento de SLA
- Tiempo promedio de resolución

### Visuales

- Total por mes: línea
- Abiertos y cerrados por mes: dos líneas
- SLA mensual: línea
- Estados por mes: columnas agrupadas o apiladas normales

No utilizar columnas 100 % apiladas si el título comunica volumen total. Ese visual muestra composición porcentual.

## Comparación trimestral

Períodos:

- T1: enero-marzo de 2023
- T2: abril-junio de 2023

Medidas implementadas:

- Trámites T1
- Trámites T2
- Variación de trámites %
- SLA T1
- SLA T2
- Variación de SLA en puntos porcentuales

Se utiliza una tabla desconectada `PeriodosComparacion` con los valores `T1` y `T2` para alimentar los ejes de los gráficos comparativos.

No conviene mezclar cantidad de trámites y porcentaje de SLA en el mismo eje debido a sus escalas diferentes.

## Resultados de referencia

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
| Promedio de resolución | 36,08 horas |

## Actualización

1. Iniciar PostgreSQL.
2. Cargar los datasets.
3. Crear las vistas.
4. Abrir el PBIX.
5. Seleccionar **Actualizar**.
6. Verificar las credenciales si se utiliza otra computadora.

## Validaciones funcionales

- Abiertos + cerrados = total.
- Dentro de SLA + fuera de SLA = cerrados con resolución.
- Los segmentadores afectan tarjetas y gráficos.
- Año-mes aparece en orden cronológico.
- Las medidas trimestrales ignoran el filtro mensual cuando usan `REMOVEFILTERS(Calendario)`.
- Los KPI principales coinciden con PostgreSQL.

## Pendientes visuales opcionales

- Uniformar paleta y tipografía.
- Ajustar títulos y nombres técnicos.
- Incorporar tooltips.
- Agregar navegación entre páginas.
- Exportar capturas para el README.

