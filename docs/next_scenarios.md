# Próximos escenarios de evolución

El portfolio ya permite recorrer cuatro preguntas operativas con cifras calculadas desde la muestra. Estas son las siguientes líneas de trabajo, ordenadas por el valor que aportan a una demostración pública.

## Escenario A — Mostrar el dashboard real

**Situación:** una persona visita la web y quiere ver el resultado en Power BI sin instalar nada.

**Desarrollo:** aplicar la guía de `docs/dashboard_design.md` en Power BI Desktop, quitar la página vacía y exportar una captura fiel de cada una de las tres páginas de contenido. Incorporar las imágenes a la web con pie de figura y fecha de actualización. Si se graba video, usar el storyboard de `docs/demo_video_plan.md` y distinguir la captura real de los gráficos animados de apoyo.

**Terminado cuando:** las tres capturas coinciden con el PBIX actualizado, son legibles en móvil, muestran datos sintéticos y tienen texto alternativo. El video reproduce el recorrido desde CSV hasta visualización y sus cifras coinciden con la demo.

**Dependencia:** Power BI Desktop y una exportación hecha desde el archivo original. Una maqueta SVG no equivale a esa evidencia.

## Escenario B — Historia y backlog a fecha de corte

**Situación:** un analista pregunta cuántos casos estaban abiertos en una fecha pasada. La instantánea actual no puede contestarlo.

**Desarrollo:** generar eventos sintéticos de cambio de estado con marca temporal, clave del caso y estado anterior/nuevo. Crear una tabla de eventos y una consulta de estado a fecha de corte; definir qué pasa con anulaciones y reaperturas. Incorporar pruebas de secuencia y de conservación del total.

**Terminado cuando:** una fecha de corte reproduce un backlog verificable, la vista diaria distingue ingresos de cierres reales y el bot responde esas preguntas usando eventos, no el estado actual.

## Escenario C — Consultas más flexibles con costo controlado

**Situación:** una persona plantea una pregunta con sinónimos o varias condiciones que las reglas locales no reconocen.

**Desarrollo:** activar la interpretación opcional con Gemini u OpenAI, medir errores de interpretación y agregar una cuota global compartida y observabilidad antes de abrir el modo IA a visitantes. Ampliar el catálogo de métricas solo cuando haya definición y datos para probarlas. No permitir SQL libre ni respuestas numéricas redactadas por el modelo.

**Terminado cuando:** preguntas equivalentes producen la misma consulta estructurada, filtros inventados se rechazan, los conteos coinciden con el dataset y existe un techo de uso comprobable entre instancias de Vercel.

## Orden sugerido

Primero cerrar **A** para fortalecer la evidencia visual del portfolio; después **B** para demostrar modelado temporal y resolver una limitación real. **C** puede avanzar en paralelo como experimento, pero su apertura pública depende del control de cuota global. La sección de escenarios web seguirá creciendo cuando se incorporen datos y preguntas verificables; sus gráficos se regeneran en cada despliegue desde los CSV.
