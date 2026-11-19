# Propuesta de video: cómo se construye el pipeline

Duración sugerida: 90–120 segundos para portfolio y una versión de 30 segundos para redes. La historia debe partir de una pregunta operativa y mostrar una evidencia nueva en cada etapa.

| Tiempo | Escena | Evidencia en pantalla |
|---|---|---|
| 0–10 s | Problema: seguimiento de trámites de portabilidad. | Preguntas: volumen, pendientes y SLA; aviso visible de datos sintéticos. |
| 10–25 s | Dos lotes llegan al pipeline. | 5.000 + 2.500 CSV; contador progresivo. |
| 25–40 s | Validación y transformación. | Reglas de negocio y 21 columnas; ejemplo de fila antes/después. |
| 40–60 s | PostgreSQL y carga incremental. | Tabla con clave primaria, primer total de 5.000 y final de 7.500; repetición con cero nuevos. |
| 60–75 s | Seis vistas SQL. | KPI 7.500 total, 3.676 abiertos, 3.824 cerrados. |
| 75–100 s | Dashboard real. | Grabación de las tres páginas de Power BI y un filtro aplicado. |
| 100–115 s | Calidad y cierre. | 24 pruebas y enlace al repositorio. |

## Producción propuesta

1. Grabar Power BI Desktop con OBS a 1920×1080. Antes de grabar, actualizar el PBIX contra la base reconstruida y ocultar credenciales, rutas personales y otras ventanas.
2. Generar las escenas del flujo y los contadores desde los CSV y consultas SQL reales. Exportar gráficos y textos como SVG o PNG; animarlos con Remotion, Manim o una herramienta de edición como DaVinci Resolve.
3. Montar la captura del dashboard como segmento propio, con rótulo “Power BI Desktop”. Los gráficos animados previos llevarán el rótulo “reconstrucción visual”.
4. Añadir locución sencilla y subtítulos; dejar 2–3 segundos finales para GitHub y el mensaje “datos sintéticos”.
5. Verificar cada cifra con `bash scripts/demo.sh` y con las consultas SQL antes de exportar el video final.

El PBIX guardado en Git no contiene capturas rasterizadas de sus páginas. Las imágenes finales y la grabación del dashboard deben exportarse desde Power BI Desktop. No conviene simular su interfaz y presentarla como una captura real.
