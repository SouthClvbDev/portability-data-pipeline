# Tablero Power BI: operaciones de portabilidad

## Estado y origen

La conexión a PostgreSQL ya está realizada. Falta completar las tarjetas de la página `Resumen Operativo`. Archivo de trabajo: `dashboard/portability_operations.pbix`.

Después de reiniciar la PC, seguir `docs/runbook.md`: abrir Docker Desktop, ejecutar `docker compose up -d`, confirmar que existe `portability_cases`, abrir el PBIX y pulsar **Actualizar**.

## Antes de crear tarjetas

En **Vista de datos** confirmar que `public.portability_cases` tiene 5000 filas y que `is_closed` e `is_pending` son booleanos. Si solo cargaste las cinco vistas, ir a **Inicio → Obtener datos → PostgreSQL database**, `localhost:5432`, `portability_db`, modo **Importar**, y seleccionar también `public.portability_cases`.

Para una página con filtros interactivos, crear tarjetas y gráficos a partir de **esa misma tabla de detalle**. Las vistas SQL agregadas sirven para comprobar totales; una tarjeta que viene de `vw_portability_kpis` no se filtra automáticamente por un segmentador de `portability_cases`.

## Crear las ocho medidas

En el panel **Datos**, clic derecho sobre `portability_cases` → **Nueva medida**. Introducir una medida por vez (si Power BI usa `;` como separador regional, cambiar las comas de los argumentos por punto y coma):

```dax
Total trámites = DISTINCTCOUNT(portability_cases[case_id])
```

```dax
Casos abiertos = CALCULATE([Total trámites], portability_cases[is_pending] = TRUE())
```

```dax
Casos cerrados = CALCULATE([Total trámites], portability_cases[is_closed] = TRUE())
```

```dax
Aprobados = CALCULATE([Total trámites], portability_cases[status] = "Aprobado")
```

```dax
Rechazados = CALCULATE([Total trámites], portability_cases[status] = "Rechazado")
```

```dax
Anulados = CALCULATE([Total trámites], portability_cases[status] = "Anulado")
```

```dax
Dentro de SLA = CALCULATE([Total trámites], portability_cases[sla_status] = "Dentro de SLA")
```

```dax
Fuera de SLA = CALCULATE([Total trámites], portability_cases[sla_status] = "Fuera de SLA")
```

Medida opcional para el porcentaje de cumplimiento:

```dax
Cumplimiento SLA % = DIVIDE([Dentro de SLA], [Dentro de SLA] + [Fuera de SLA])
```

Seleccionar esta última medida y establecer **Formato → Porcentaje**, con uno o dos decimales.

## Colocar las tarjetas

1. Crear o renombrar una página como `Resumen Operativo`.
2. En **Visualizaciones**, insertar **Tarjeta**. Arrastrar `Total trámites` al campo **Datos/Valores** de la tarjeta (el nombre varía según la versión de Power BI).
3. Duplicar la tarjeta siete veces con copiar/pegar y reemplazar la medida de cada copia por: `Casos abiertos`, `Casos cerrados`, `Aprobados`, `Rechazados`, `Anulados`, `Dentro de SLA` y `Fuera de SLA`.
4. Orden sugerido: primera fila Total, Abiertos, Cerrados, Aprobados; segunda fila Rechazados, Anulados, Dentro de SLA, Fuera de SLA. Activar **Título** en formato y usar nombres cortos.

Con la muestra actual, **sin filtros**, los valores esperados son:

| Tarjeta | Valor |
|---|---:|
| Total trámites | 5000 |
| Casos abiertos | 2430 |
| Casos cerrados | 2570 |
| Aprobados | 1652 |
| Rechazados | 610 |
| Anulados | 308 |
| Dentro de SLA | 1953 |
| Fuera de SLA | 617 |

Controles rápidos: Total = Abiertos + Cerrados; Cerrados = Aprobados + Rechazados + Anulados; Cerrados = Dentro de SLA + Fuera de SLA. La muestra no representa métricas de Telecom.

## Gráficos y filtros de la misma página

Usar `portability_cases` para que los segmentadores afecten también a las tarjetas:

| Visual | Eje / categoría | Valor |
|---|---|---|
| Barras: casos por estado | `status` | `Total trámites` |
| Línea: ingresos diarios | `received_date` | `Total trámites` |
| Barras: carga por equipo | `team` | `Total trámites` |
| Barras: fuera de SLA por canal | `channel` | `Fuera de SLA` |

Segmentadores: `received_date`, `team`, `channel`. Si se añade `status`, al seleccionar Aprobado las demás tarjetas mostrarán cero: ese comportamiento es esperable. Para ver la fecha como eje continuo, comprobar que `received_date` sea de tipo **Fecha**. No usar `received_month_name` aislado para ordenar meses; ordenarlo por `received_month` o usar una tabla calendario más adelante.

**Importante:** la línea por `received_date` muestra trámites **recibidos** cada día; no muestra cierres diarios. En el modelo actual no hay historial de cambios de estado.

## Prueba final

1. Sin filtros, comparar las ocho tarjetas con la tabla anterior.
2. Seleccionar un equipo: deben cambiar el total y las tarjetas relacionadas.
3. Quitar la selección: deben volver los valores generales.
4. Guardar con **Archivo → Guardar como** en `dashboard/portability_operations.pbix`.

Si una tarjeta no responde a un segmentador, revisar que ambos usan `portability_cases` y, en **Formato → Editar interacciones**, que el segmentador tiene activada la opción de filtrar esa tarjeta.
