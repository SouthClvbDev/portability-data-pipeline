# Dataset sintético de escala completa para Power BI

Este dataset es **independiente de la muestra pequeña que usa el portfolio web y su asistente**. Simula el flujo desde enero de 2023 hasta la hora de corte actual en Argentina, con volúmenes comparables a una operación de miles de trámites por mes. No contiene datos reales.

## Perfil de volumen

- Mes normal completo: **15.000–25.000** recepciones.
- Un pico positivo por año: **25.001–40.000**.
- Un pico negativo por año: **10.000–14.999**.
- Cada total mensual se reparte exactamente entre sus días con variación diaria y menor volumen en fines de semana. Por tanto, el promedio diario es coherente con el total mensual.
- El mes en curso es **parcial**: solo incluye recepciones hasta la hora de corte. No debe compararse con un mes completo sin ajustar el período.

Las semillas dependen del año, mes y día. Repetir el mismo `--as-of` produce el mismo CSV comprimido, los mismos IDs y las mismas cifras. Los casos recientes pueden pasar de abiertos a cerrados en un corte posterior; las fechas de cierre nunca superan el corte.

Las duraciones ya no siguen una única distribución constante: el [perfil operacional sintético](synthetic_story.md) representa meses de congestión y etapas de mejora. Por eso el SLA de 48 horas varía entre cohortes mensuales sin cambiar la regla del indicador ni el rango de volumen solicitado. Son escenarios de prueba diseñados para explorar decisiones; no describen episodios reales.

## Archivos y generación

```bash
.venv/bin/python src/generate_full_scale_data.py
```

Se generan en `data/generated/`:

- `portability_cases_full.csv.gz`: CSV comprimido con las **21 columnas** del modelo que utiliza PostgreSQL.
- `portability_cases_full.manifest.json`: fecha de corte, SHA-256, total, estado y volumen de cada mes.

La tarea diaria también genera `portability_cases_incremental.csv.gz` y su manifiesto con una **ventana de doce días hacia atrás, más el día de corte**. Supera la duración máxima simulada de 240 horas para no perder un cierre tardío entre ejecuciones. Esa ventana incluye nuevas recepciones y casos recientes que pudieron cambiar de abiertos a cerrados. Los IDs de un día son los mismos en el archivo completo y en el incremental.

`data/generated/` está excluido de Git para evitar añadir alrededor de un millón de filas al historial del repositorio. El workflow diario genera el archivo completo y el incremental con el mismo corte que la muestra pequeña y ofrece los cuatro archivos como artefacto **`portability-full-scale`** en GitHub Actions durante 7 días. También se pueden regenerar localmente cuando haga falta. Para un corte reproducible, usar `--as-of 2026-11-19T19:55:55` (hora de Argentina); no se aceptan fechas futuras.

## Cargar en PostgreSQL sin tocar la demo

```bash
docker compose up -d --wait
.venv/bin/python -m src.load_full_scale_to_postgres
```

La carga usa `COPY` desde el archivo `.csv.gz` en una transacción y crea `public.portability_cases_full` con tipos y restricciones explícitos. Verifica el SHA-256, total, fechas y conteos mensuales contra el manifiesto antes de confirmar. Si falla, revierte la carga. **No reemplaza `public.portability_cases`**, la tabla que usa la demo original.

Después de la primera carga, el lote reciente se puede aplicar sin reemplazar toda la tabla:

```bash
.venv/bin/python -m src.load_full_scale_to_postgres --mode sync --input data/generated/portability_cases_incremental.csv.gz
```

`sync` copia el lote a una tabla temporal, inserta IDs nuevos y actualiza solo las filas que realmente cambiaron. Repetir el mismo archivo informa **0 nuevas y 0 actualizadas**. Si se pierden varias ejecuciones, la ventana reciente recupera los días incluidos; para una pausa mayor, cargar de nuevo el archivo completo más reciente.

Consultas de control:

```sql
SELECT count(*), min(received_date), max(received_date)
FROM public.portability_cases_full;

SELECT to_char(received_date, 'YYYY-MM') AS mes, count(*) AS tramites
FROM public.portability_cases_full
GROUP BY 1 ORDER BY 1;
```

## Usarlo en el PBIX cuando termine su edición

1. Guardar una copia del PBIX antes de cambiar el origen.
2. En Power Query, localizar la consulta que navega a `public.portability_cases` y cambiar **solo su tabla de origen** a `public.portability_cases_full`. Mantener el nombre de la consulta y los tipos de sus 21 columnas para conservar las medidas y visuales.
3. Revisar la tabla `Calendario`: si termina en junio de 2023, extenderla hasta el máximo `received_date` de la nueva tabla. Mantener la relación `Calendario[Date]` → casos `[received_date]` y el orden cronológico de año-mes.
4. Actualizar, comparar el total y varios meses con el manifiesto/SQL y revisar los visuales de las tres páginas. El mes actual es parcial. Las medidas T1/T2 de 2023 siguen representando esos trimestres; ampliar su alcance sería una decisión aparte.

El PBIX no se modifica mediante estos scripts. La web incluye ahora un [análisis exploratorio hecho con Python y Matplotlib](web_projection_plan.md) sobre el CSV completo. Sus tarjetas y chatbot siguen usando la muestra pequeña y lo dicen explícitamente; no deben confundirse con los totales de este dataset completo.
