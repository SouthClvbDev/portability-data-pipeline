# Revisión de diseño y relato del portfolio

## Tesis de la página

El proyecto muestra cómo pasar de un dato operativo a una decisión que se puede justificar. La portada conecta la experiencia de Backoffice de Ezequiel Blanco con el trabajo técnico del portfolio. La pregunta de entrada es: **¿el mes con más trámites fue también el de peor SLA?** La web compara ambos meses desde el CSV sintético de escala completa. En el corte actual no coinciden; si una generación posterior cambia el resultado, la conclusión visible se adapta. El caso propone qué investigar antes de atribuir una causa. El pipeline aparece después como evidencia de cómo se obtuvieron las cifras.

## Recorrido de una persona visitante

1. **Problema y señal:** caso ejecutivo con volumen y SLA de dos meses, fecha de corte y fuente.
2. **Lectura operativa:** tarjetas, estados y backlog de la muestra liviana para explorar el seguimiento diario.
3. **Evidencia analítica:** serie Matplotlib del dataset grande, con episodios sintéticos y código reproducible.
4. **Método:** generación, calidad, transformación, PostgreSQL, SQL y Power BI; cada etapa del proyecto enlaza su archivo.
5. **Exploración:** escenarios guiados y asistente con cálculos verificables.
6. **Presentación BI:** público ejecutivo y operativo definidos; las capturas pendientes siguen marcadas como tales mientras se edita el PBIX.

El contraste entre el mes de mayor volumen y el de peor SLA es **descriptivo**. No prueba que el volumen cause o no cause demoras. Los episodios de capacidad fueron programados en una simulación, como se explica en [historia sintética](synthetic_story.md). La acción propuesta es una hipótesis de investigación para una operación real, no una recomendación basada en datos reales.

## Decisiones de interfaz

- El caso aparece antes del proceso técnico y usa un bloque visual propio para que la pregunta y la conclusión se lean juntas.
- Las cifras se insertan desde `full-scale-analysis.json`; la página muestra el corte y el alcance. No hay números históricos escritos a mano en la comparación.
- La sección operativa declara que usa la muestra pequeña. El gráfico de Matplotlib declara que usa el CSV de escala completa.
- La sección Power BI distingue las lecturas ejecutiva y operativa y señala que el diseño del PBIX sigue en evolución.
- La navegación móvil permite entrar directamente al caso, a la operación o a la evidencia, sin recorrer toda la página.

## Qué falta para un relato más fuerte

La mayor limitación sigue siendo la **doble fuente web**: caso y Matplotlib usan el dataset grande, mientras las tarjetas, escenarios y chat usan la muestra pequeña. El siguiente desarrollo de producto debería [migrar esas piezas a agregados del dataset grande](web_projection_plan.md), con un único selector de alcance y corte. Después de que el autor termine el PBIX, conviene incorporar capturas reales y una explicación de una decisión ejecutiva y una operativa tomada desde sus visuales. Esto cerraría la cadena entre pregunta, análisis, tablero y acción sin simular evidencia del informe.
