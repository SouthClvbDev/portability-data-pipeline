# Actualización sintética diaria

La muestra base conserva los dos lotes originales de 2023. [`src/generate_daily_data.py`](../src/generate_daily_data.py) extiende el proyecto desde el 1 de julio de 2023 hasta la **hora de corte en Argentina**. Los datos siguen siendo ficticios; la fecha de corte significa que la simulación fue generada hasta ese momento, no que exista una fuente operativa en vivo.

## Cómo funciona

1. Para cada fecha se obtiene una semilla estable a partir del día. La cantidad de casos varía entre días y es menor los fines de semana. Repetir el mismo corte produce los mismos identificadores y atributos.
2. Los IDs `SIM-AAAAMMDD-NNNN` no se cruzan con los `PORT-` de la muestra base.
3. Cada caso tiene una duración de resolución sintética. Antes de su cierre figura abierto; en un corte posterior puede aparecer aprobado, rechazado o anulado. No se registra cuándo pasó entre estados abiertos.
4. El generador excluye recepciones y cierres posteriores a la hora de corte. [`data/sample/portability_cases_daily.meta.json`](../data/sample/portability_cases_daily.meta.json) declara esa hora y la cantidad de filas.
5. La carga `--mode sync` inserta IDs nuevos y actualiza solo filas que cambiaron. Una segunda ejecución del mismo archivo no modifica filas.

El lote diario se versiona junto con los dos lotes base. La web deriva sus métricas y respuestas de esos CSV en cada despliegue. PostgreSQL local se reconstruye con `bash scripts/demo.sh` o se sincroniza manualmente con el lote transformado. **No hay una base PostgreSQL permanente conectada a Vercel.** El PBIX sigue bajo edición del autor y no se actualiza automáticamente.

## Automatización

[`daily_data.yml`](../.github/workflows/daily_data.yml) se programa a las **23:00 UTC (20:00 de Argentina)** y también admite ejecución manual con `workflow_dispatch`. Regenera la muestra completa hasta la hora actual. Así recupera días omitidos sin duplicar IDs. Si cambian el CSV o sus metadatos, valida el pipeline y la web, commitea ambos archivos en `main` y los pushea.

Una integración Git de Vercel puede desplegar ese push. Si no lo hace, crear un deploy hook de Vercel y guardar su URL como secreto `VERCEL_DEPLOY_HOOK_URL` en GitHub Actions. El workflow llamará al hook después del push. Verificar en Vercel que la fecha mostrada en la web coincide con `daily.meta.json`. Los horarios de GitHub Actions son aproximados y una ejecución puede retrasarse; la siguiente recupera todo el intervalo.

## Uso manual

```bash
.venv/bin/python src/generate_daily_data.py
.venv/bin/python src/validation/validate_data.py --input data/sample/portability_cases_daily.csv
bash scripts/demo.sh
npm run build
npm run test:web
```

Para repetir un corte exacto, usar `--as-of AAAA-MM-DDTHH:MM:SS` en hora local de Argentina. Se rechazan fechas futuras. La automatización usa la hora actual. No hace falta regenerar los lotes base.

## Límites analíticos

- Los números diarios y el ritmo de llegada son simulados; no describen casos reales.
- El estado de un caso reciente puede cambiar cuando la simulación se regenera. El archivo versionado conserva la instantánea actual, no todas las versiones pasadas de cada fila.
- `received_at` y `closed_at` permiten calcular backlog al cierre de un día, bajo el supuesto de que no hay reaperturas. No permiten conocer duración por etapa intermedia.
- El archivo PBIX puede mostrar cifras distintas a la web hasta que el autor actualice su origen y revise el informe.
