# Próximos escenarios de evolución

El portfolio ya permite recorrer cuatro preguntas operativas con cifras calculadas desde la muestra. Estas son las siguientes líneas de trabajo, ordenadas por el valor que aportan a una demostración pública.

## Escenario A — Mostrar el dashboard real

**Situación:** una persona visita la web y quiere ver el resultado en Power BI sin instalar nada.

**Desarrollo:** aplicar la guía de `docs/dashboard_design.md` en Power BI Desktop, quitar la página vacía y exportar una captura fiel de cada una de las tres páginas de contenido. Incorporar las imágenes a la web con pie de figura y fecha de actualización. Si se graba video, usar el storyboard de `docs/demo_video_plan.md` y distinguir la captura real de los gráficos animados de apoyo.

**Terminado cuando:** las tres capturas coinciden con el PBIX actualizado, son legibles en móvil, muestran datos sintéticos y tienen texto alternativo. El video reproduce el recorrido desde CSV hasta visualización y sus cifras coinciden con la demo.

**Dependencia:** Power BI Desktop y una exportación hecha desde el archivo original. Una maqueta SVG no equivale a esa evidencia.

## Escenario B — Historia y backlog a fecha de corte

**Situación:** un analista pregunta cuántos casos estaban abiertos en una fecha pasada. Las fechas de recepción y cierre permiten responder al cierre del día, pero no muestran las etapas intermedias.

**Avance realizado:** `vw_case_observed_events`, `vw_daily_backlog`, gráfico diario y respuesta del bot a una fecha de corte. Solo se usan las marcas de recepción y cierre presentes en los CSV.

**Siguiente desarrollo:** registrar cambios entre estados abiertos con marca temporal, clave del caso y estado anterior/nuevo desde una fuente que realmente conserve esas transiciones. Definir reaperturas y agregar pruebas de secuencia.

**Terminado cuando:** se pueden responder también preguntas por estado intermedio y duración por etapa sin inferir marcas que no existen.

## Escenario C — Consultas más flexibles con costo controlado

**Situación:** una persona plantea una pregunta con sinónimos o varias condiciones que las reglas locales no reconocen.

**Avance realizado:** interpretación opcional con Gemini u OpenAI, validación de filtros y cuota compartida atómica con Redis REST cuando se configuran sus credenciales. El modo sin IA permanece disponible.

**Siguiente desarrollo:** configurar Redis y la clave del proveedor en Vercel, probar la cuota entre instancias, medir errores de interpretación y observar uso/costo real. Ampliar métricas solo con definiciones verificables. No permitir SQL libre ni cifras redactadas por el modelo.

**Terminado cuando:** preguntas equivalentes producen la misma consulta estructurada, filtros inventados se rechazan, los conteos coinciden con el dataset y se comprobó el techo de uso en el despliegue real.

## Orden sugerido

La historia observable de **B** y un recorrido progresivo de la web ya avanzaron sin editar el PBIX. El rediseño y las capturas reales de **A** quedan a cargo de la edición en Power BI Desktop. El código de cuota global de **C** ya está preparado; falta configurarlo y verificarlo en Vercel antes de abrir la IA públicamente. Las cifras web se regeneran en cada despliegue desde los CSV.
