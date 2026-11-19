# Propuesta de video: cómo se construye el pipeline

Duración sugerida: 90–120 segundos para portfolio y una versión de 30 segundos para redes. La historia debe partir de una pregunta operativa y mostrar una evidencia nueva en cada etapa. El recorrido progresivo de «Proyecto vivo» en la web ya puede servir como base grabable.

| Tiempo | Escena | Evidencia en pantalla |
|---|---|---|
| 0–10 s | Problema: seguimiento de trámites de portabilidad. | Preguntas: volumen, pendientes y SLA; aviso visible de datos sintéticos. |
| 10–25 s | Dos lotes llegan al pipeline. | 5.000 + 2.500 CSV; contador progresivo. |
| 25–40 s | Validación y transformación. | Reglas de negocio y 21 columnas; ejemplo de fila antes/después. |
| 40–60 s | PostgreSQL y carga incremental. | Tabla con clave primaria, primer total de 5.000 y final de 7.500; repetición con cero nuevos. |
| 60–75 s | Vistas SQL. | KPI 7.500 total, 3.676 abiertos, 3.824 cerrados. |
| 75–95 s | Nueva pregunta: backlog a una fecha. | Selector diario de la web, respuesta del asistente y consulta a `vw_daily_backlog`. |
| 95–110 s | Evidencia y cierre. | Recorrido por etapas de la web, pruebas actuales y enlace al repositorio. |

## Producción propuesta

1. Grabar la web en una ventana de 1920×1080: pulsar «Reproducir recorrido», seleccionar una fecha en la serie diaria y mostrar la respuesta del asistente. Identificarlo como **portfolio web**, no como Power BI.
2. Generar las escenas del flujo y los contadores desde los CSV y consultas SQL reales. Exportar gráficos y textos como SVG o PNG; animarlos con Remotion, Manim o una herramienta de edición como DaVinci Resolve.
3. Añadir locución sencilla y subtítulos; dejar 2–3 segundos finales para GitHub y el mensaje “datos sintéticos”.
4. Verificar cada cifra con `bash scripts/demo.sh` y con las consultas SQL antes de exportar el video final. Evitar un número fijo de pruebas en la locución, porque seguirá creciendo.
5. Cuando el autor termine de editar Power BI, grabar sus páginas en Desktop y añadirlas como segmento identificado. Antes de hacerlo, actualizar el PBIX contra la base reconstruida y ocultar credenciales, rutas personales y otras ventanas.

El PBIX guardado en Git no contiene capturas rasterizadas de sus páginas. La primera versión del video puede publicarse con evidencia de la web, Python y SQL. Las imágenes y la grabación del dashboard se incorporarán después desde Power BI Desktop; ninguna escena web debe presentarse como captura del PBIX.
