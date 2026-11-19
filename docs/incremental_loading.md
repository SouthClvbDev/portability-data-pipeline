# Carga incremental

## Objetivo

Simular el crecimiento de una base operacional sin reemplazar los registros existentes y sin generar duplicados al repetir una ejecución.

## Datasets

| Lote | Archivo | IDs | Fechas | Registros |
|---|---|---|---|---:|
| Inicial | `portability_cases.csv` | `PORT-000001` a `PORT-005000` | ene-mar 2023 | 5.000 |
| Incremental | `portability_cases_incremental.csv` | `PORT-005001` a `PORT-007500` | abr-jun 2023 | 2.500 |
| Extensión diaria | `portability_cases_daily.csv` | `SIM-AAAAMMDD-NNNN` | jul 2023 hasta el corte actual | Variable |

## Generación

```powershell
python src\generate_incremental_data.py
```

El generador usa una semilla fija, aplica las mismas reglas de negocio y produce IDs no superpuestos.

## Transformación

```powershell
python src\transformations\transform_cases.py `
    --input data\sample\portability_cases_incremental.csv `
    --output data\processed\portability_cases_incremental_clean.csv
```

El resultado contiene las mismas 21 columnas analíticas que la carga inicial.

## Carga

```powershell
python src\load_to_postgres.py `
    --mode append `
    --input data\processed\portability_cases_incremental_clean.csv
```

## Algoritmo actual

1. Validar que el archivo exista.
2. Leer el CSV procesado.
3. Verificar presencia y unicidad de `case_id` dentro del lote.
4. Crear o actualizar el esquema y sus restricciones.
5. Insertar en lotes usando `ON CONFLICT (case_id) DO NOTHING`.
6. Informar insertados, ignorados y total final.

## Idempotencia

Primera ejecución:

```text
Registros leídos: 2500
Registros nuevos cargados: 2500
Registros ignorados por estar repetidos: 0
Registros totales en PostgreSQL: 7500
```

Segunda ejecución del mismo archivo:

```text
Registros leídos: 2500
No hay registros nuevos para cargar.
Registros totales en PostgreSQL: 7500
```

## Validaciones

```sql
SELECT COUNT(*) FROM portability_cases;
```

Esperado tras los dos lotes base: `7500`. Tras sincronizar la extensión diaria: `7500` más las filas de `portability_cases_daily.csv`.

```sql
SELECT MIN(received_date), MAX(received_date)
FROM portability_cases;
```

Esperado tras los dos lotes base: `2023-01-01` a `2023-06-30`. Con la extensión diaria, el máximo llega a la fecha de corte declarada en `portability_cases_daily.meta.json`.

```sql
SELECT case_id, COUNT(*)
FROM portability_cases
GROUP BY case_id
HAVING COUNT(*) > 1;
```

Esperado: cero filas.

## Diferencia entre modos

### `--mode initial`

- destinado a reconstrucción completa;
- ejecuta `TRUNCATE` si la tabla existe;
- conserva las vistas dependientes;
- inserta todo el archivo indicado.

### `--mode append`

- destinado a nuevos lotes;
- no elimina datos existentes;
- inserta solamente IDs nuevos;
- puede repetirse de forma segura.

### `--mode sync`

- destinado al lote sintético diario;
- inserta IDs nuevos y actualiza solo las filas que cambiaron, por ejemplo cuando un caso reciente se cierra;
- una segunda ejecución con el mismo archivo informa cero cambios;
- el CSV y su hora de corte se regeneran de forma estable con `python src/generate_daily_data.py`.

La [guía de actualización diaria](daily_synthetic_updates.md) describe la programación de GitHub Actions y la relación con Vercel. La actualización de PostgreSQL solo ocurre al ejecutar la demo o la carga local; el sitio no consulta esa base.

## Limitaciones de la implementación

El enfoque actual crea sentencias SQL por lotes de 500 filas. Es adecuado para miles de filas, pero para volúmenes grandes convendría usar `COPY` hacia staging.

Una evolución productiva podría usar:

1. tabla staging;
2. carga masiva con `COPY`;
3. `INSERT ... ON CONFLICT DO NOTHING` o `MERGE` desde staging;
5. tabla de auditoría de lotes;
6. transacciones y conteos de control;
7. cuarentena para registros inválidos.

## Impacto en Power BI cuando el informe esté listo

El PBIX permanece bajo edición manual. Si se actualiza con la base local después de cargar solo los lotes base:

1. actualizar las vistas;
2. abrir el PBIX;
3. seleccionar **Actualizar**;
4. verificar que el calendario llegue a junio de 2023;
5. validar total, métricas mensuales y comparación T1/T2.

Si también se cargó la extensión diaria, revisar primero el calendario, filtros y métricas para el período ampliado. La tarea diaria no abre ni cambia el PBIX.

