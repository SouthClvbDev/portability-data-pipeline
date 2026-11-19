# Historia operacional sintética

Estos episodios son **supuestos de diseño** para mostrar cómo cambian las métricas y permitir análisis en Power BI, SQL, Python y la web. No representan hechos de Telecom ni de ninguna operación real.

| Período simulado | Supuesto | Efecto en los datos |
|---|---|---|
| 2023 | Estabilización inicial | Resoluciones más lentas y una cohorte histórica que se cierra gradualmente durante 2023. |
| Octubre de 2023 | Sobrecarga de campaña | Aumentan las horas de resolución y baja el SLA. |
| Mayo de 2024 | Cambio de proceso | Episodio de demoras más intenso. |
| Segundo semestre de 2024 | Ajustes de capacidad | Mejora gradual del SLA. |
| Febrero de 2025 | Acumulación de pendientes | Caída temporal del SLA. |
| Segundo semestre de 2025 | Proceso optimizado | Menores tiempos de resolución. |
| Agosto de 2026 | Incidente de capacidad | Nueva demora temporal para explorar resiliencia. |

`src/operational_profile.py` define la escala de una distribución Gamma para las horas de resolución. `src/generate_full_scale_data.py` y `src/generate_daily_data.py` la aplican a cada caso; un mismo corte sigue siendo reproducible. El dataset de escala completa también ajusta la duración en meses de pico positivo o negativo de demanda. El máximo de resolución de los casos nuevos sigue siendo 240 horas, de modo que el incremental de doce días cubre las actualizaciones recientes.

Los 7.500 casos de los lotes base conservan ID y recepción. `src/legacy_cohort.py` asigna un cierre determinista a los que antes quedaban abiertos para siempre, con duraciones de aproximadamente 10 a 181 días. Los casos ya finalizados no se modifican. Las cifras históricas de estado y SLA cambian porque la instantánea ahora refleja ese cierre; no se inventa un registro de transiciones intermedias.

El [gráfico Matplotlib](../src/analyze_full_scale_data.py) calcula el SLA de cada cohorte de recepción con **cerrados dentro de 48 horas / cerrados** al corte. Sus tarjetas de hallazgos destacan los meses extremos desde el propio CSV, no con cifras escritas a mano. La web ofrece una ventana reciente para observar variaciones del backlog sin ocultar la opción de ver la historia completa.
