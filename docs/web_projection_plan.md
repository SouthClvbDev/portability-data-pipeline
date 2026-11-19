# Web con datos de escala completa y escenario 2028

## Estado implementado

La ruta de Power BI usa Docker/PostgreSQL y puede leer `public.portability_cases_full` sin cambiar la demo original. `src/analyze_full_scale_data.py` lee el CSV comprimido completo, verifica su hash y sus totales contra el manifiesto y calcula volúmenes diarios/mensuales y SLA por cohorte. Matplotlib exporta un SVG publicado en la web, junto a un JSON agregado con fecha de corte. La automatización diaria actualiza ambos al regenerar el dataset. Las tarjetas y el asistente de la web siguen vinculados a la muestra pequeña y lo declaran.

Para reconstruir el gráfico localmente después de generar el CSV:

```bash
python -m pip install -r requirements-viz.txt
MPLCONFIGDIR=/tmp/portability-matplotlib python src/analyze_full_scale_data.py
```

El resultado queda en `web/public/analysis/full-scale-trends.svg` y `web/public/data/full-scale-analysis.json`. El JSON contiene la serie diaria y mensual; el gráfico de SLA agrupa por mes de **recepción** y divide los casos cerrados dentro de 48 horas por todos los casos cerrados de esa cohorte al corte indicado. El mes en curso se marca como parcial y se excluye del gráfico de SLA.

## Siguiente integración: una fuente grande, sin PostgreSQL en Vercel

1. Construir durante CI un conjunto de **agregados** desde el CSV completo: conteos por fecha de recepción, estado, equipo y canal; resueltos dentro/fuera de SLA y suma de horas de resolución. Añadir eventos diarios de ingreso y cierre para calcular backlog a una fecha.
2. Hacer que tarjetas, gráficos, escenarios y asistente usen esos agregados. El motor debe sumar los conteos y conservar denominadores correctos de SLA. Las preguntas no soportadas deben responderlo explícitamente.
3. Publicar los agregados como JSON pequeño; la función de Vercel carga esos archivos, no el CSV de detalle ni PostgreSQL. Verificar que las respuestas coincidan con SQL sobre una misma fecha de corte.
4. Crear un **escenario 2028 separado**: horizonte sugerido `2028-01-31`, generación determinista con metadatos de proyección, y selector visible «Hasta hoy / Escenario 2028». Cambiar todas las métricas y el chat juntos para evitar mezclar fechas. La proyección debe mostrar una marca permanente «Simulación futura».
5. Mantener el PBIX en el recorrido SQL y con datos hasta el corte real. Si luego interesa analizar 2028 en BI, crear una tabla `portability_cases_projection` y una página de escenarios diferenciada.

Un CSV completo hasta enero de 2028 tendría más de un millón de filas, pero sería un **insumo de build**. Servirlo entero al navegador o empaquetarlo en la función haría lenta la web y el chat. El gráfico y los agregados ofrecen trazabilidad sin exponer la base local.
