# Calidad de datos

## Objetivo

Definir las reglas que garantizan que los datasets sintéticos sean estructural y operativamente consistentes antes de cargarse en PostgreSQL.

## Capas de control

1. Generación reproducible mediante semillas fijas.
2. Validación explícita del CSV inicial.
3. Transformación controlada.
4. Prevención de duplicados en la carga incremental.
5. Pruebas automatizadas sobre archivos.
6. Pruebas de integración sobre PostgreSQL y vistas.

## Reglas estructurales

- Deben existir todas las columnas requeridas.
- `case_id` no puede estar vacío.
- `case_id` debe ser único dentro de cada lote.
- Los lotes inicial e incremental no deben compartir IDs.
- `received_at` debe ser una fecha válida.
- Los datasets inicial e incremental deben tener columnas compatibles.

## Estados permitidos

- Recibido
- En análisis
- Pendiente documentación
- Pendiente contacto
- Aprobado
- Rechazado
- Anulado

Estados finalizados:

- Aprobado
- Rechazado
- Anulado

## Reglas temporales

- `closed_at` no puede ser anterior a `received_at`.
- Los casos finalizados deben tener `closed_at`.
- Los casos abiertos no deben tener `closed_at`.
- Los casos con resolución deben tener `resolution_hours`.
- El lote incremental debe ubicarse entre abril y junio de 2023.

## Reglas operativas

### Documentación

- `Pendiente documentación` implica `documentation_status = Incompleta`.
- Los casos finalizados utilizan documentación completa en el generador actual.

### Contacto

- `Pendiente contacto` implica `contact_status = Pendiente`.

### Rechazos

- `Rechazado` debe tener `rejection_reason`.
- Otros estados no necesitan motivo de rechazo.

### Anulaciones

- `Anulado` debe tener `cancellation_reason`.
- Otros estados no necesitan motivo de anulación.

## Regla de SLA

Para casos con `resolution_hours`:

- hasta 48 horas: `Dentro de SLA`;
- más de 48 horas: `Fuera de SLA`.

Para casos sin resolución:

- `No aplica`.

El umbral es sintético y se utiliza solamente con fines demostrativos.

## Controles de carga

La carga incremental:

- consulta IDs ya cargados;
- filtra filas existentes;
- inserta solamente registros nuevos;
- informa insertados e ignorados;
- puede repetirse sin duplicar información.

## Pruebas automatizadas

### Archivos: 16 pruebas

- existencia y cantidad del lote inicial;
- IDs únicos;
- estados válidos;
- fechas y cierres;
- reglas de pendientes y motivos;
- consistencia del SLA;
- cantidad y rango del lote incremental;
- compatibilidad de columnas;
- ausencia de solapamiento entre lotes.

### Extensión diaria: 4 pruebas

- reproducción del mismo corte;
- ausencia de fechas futuras;
- actualización del estado sin cambiar la identidad;
- consistencia entre CSV, metadatos e IDs base.

### PostgreSQL: 11 pruebas

- conexión disponible;
- total igual a los tres CSV versionados;
- IDs únicos;
- vista KPI igual a tabla base;
- abiertos + cerrados = total;
- métricas mensuales y vistas esperadas.
- ingresos, cierres y backlog diario reconciliados con la tabla base.
- carga `sync` que actualiza cambios y omite filas idénticas.

Resultado actual:

```text
31 passed
```

## Verificaciones manuales de referencia

```sql
SELECT COUNT(*) FROM portability_cases;
```

Resultado esperado: `7500` tras los dos lotes base; con la extensión diaria se suman las filas de `portability_cases_daily.csv`.

```sql
SELECT case_id, COUNT(*)
FROM portability_cases
GROUP BY case_id
HAVING COUNT(*) > 1;
```

Resultado esperado: cero filas.

```sql
SELECT * FROM vw_portability_kpis;
```

Resultados de referencia de los dos lotes base, antes de la extensión diaria:

- total: 7.500;
- abiertos: 3.676;
- cerrados: 3.824.

## Mejoras futuras

- constraints `NOT NULL` y `CHECK` en PostgreSQL;
- clave primaria sobre `case_id`;
- índices sobre fechas, estado, equipo y canal;
- staging y control transaccional;
- auditoría de lotes cargados;
- reporte persistente de registros rechazados;
- validación de esquema mediante una herramienta especializada.

