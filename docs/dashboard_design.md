# Rediseño visual de Power BI

El archivo actual tiene tres páginas con contenido (`Resumen Operativo`, `Análisis de demoras`, `Evolución Mensual`) y una cuarta página vacía (`Página 1`). El PBIX se mantiene como fuente original; este documento y la maqueta SVG describen la edición visual para realizar en Power BI Desktop.

## Sistema visual común

- Lienzo 16:9 de 1920×1080, fondo `#F5F7FA`.
- Encabezado azul petróleo `#142C3E`, título blanco de 30–34 px y subtítulo de 16 px que diga “Datos sintéticos · Portabilidad”.
- Tarjetas blancas `#FFFFFF`, radio de 10 px, borde suave `#DDE5EC`, sin sombra fuerte. Márgenes exteriores de 48 px, separación de 16–24 px entre elementos.
- Texto principal `#213547`, secundario `#617483`. Azul `#2374AB` para volumen; verde `#19866B` para dentro de SLA; naranja `#D58A29` para pendiente; rojo `#BC4D55` para fuera de SLA o rechazo. Un mismo color conserva el significado en todas las páginas.
- Filtros en una sola fila bajo el encabezado: período, canal y equipo. Agregar botón “Restablecer filtros”. Mostrar en cada página el período seleccionado.
- Mantener rótulos y unidades consistentes: “Casos”, “Horas” y “%”. Formatear miles con separador local y porcentajes con un decimal. Evitar ejes truncados para barras de conteos.
- Añadir texto alternativo a los visuales y comprobar contraste. Los colores deben acompañarse de etiquetas, no ser el único indicador.

## Página 1 — Resumen Operativo

Pregunta principal: ¿cuál es el estado de la operación?

1. Fila de cuatro KPI: Total, Abiertos, Cerrados y Cumplimiento de SLA. El SLA debe usar solo casos resueltos como denominador.
2. Debajo, línea de casos recibidos por fecha a la izquierda y barras de casos por estado a la derecha.
3. Última fila: barras por canal y por equipo, con orden descendente y etiquetas de valor.
4. Eliminar tarjetas redundantes de aprobados/rechazados/anulados si ya aparecen en el gráfico por estado. Usar tooltip para detalle.

## Página 2 — Análisis de demoras

Pregunta principal: ¿dónde se concentran las demoras?

1. KPI: mediana de resolución, promedio de resolución, casos fuera de SLA y porcentaje fuera de SLA.
2. Barras horizontales de horas de resolución por equipo; línea o columnas de cumplimiento de SLA por canal.
3. Barras de motivos de rechazo y anulación, sin mezclar ambos conceptos en una misma serie.
4. Aclarar en un subtítulo que el SLA de 48 horas corridas es una regla sintética de la demo.

## Página 3 — Evolución Mensual

Pregunta principal: ¿cómo cambia el volumen y desempeño a lo largo del tiempo?

1. Columnas de casos recibidos por mes y línea de cumplimiento de SLA mensual en visuales separados; las unidades no deben compartir eje sin aviso.
2. Columnas apiladas de estado actual de casos recibidos por mes, con nota visible: esto no reconstruye el backlog histórico.
3. Comparación T1/T2 en una sola zona compacta con volumen, cerrados y SLA, usando la misma definición de período.
4. Reservar la fila superior para filtros y un resumen breve del período, sin tarjetas gigantes que quiten espacio a la tendencia.

## Orden de edición en Power BI Desktop

1. Guardar una copia del PBIX y quitar la página vacía “Página 1”.
2. Aplicar colores, tipografías y fondo; luego alinear visuales con una cuadrícula de 12 columnas.
3. Reubicar filtros y KPI; simplificar gráficos redundantes.
4. Verificar medidas y denominadores, interacciones de filtros y títulos dinámicos.
5. Actualizar desde PostgreSQL, revisar las tres páginas a 100 % y exportar PNG o PDF para el README.

La [maqueta del resumen](dashboard_mockup.svg) ilustra jerarquía y distribución. Sus números son ejemplos del conjunto sintético actual; la captura final debe salir del PBIX después de aplicar el diseño.
