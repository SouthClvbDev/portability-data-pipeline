# Decisiones y trade-offs

| Decisión | Motivo | Límite |
|---|---|---|
| Datos sintéticos | Mostrar el proceso sin exponer datos de clientes ni sistemas internos. | Los indicadores no describen una operación real. |
| Python y pandas | Hacen visibles generación, validación y transformación. | Para volúmenes mayores convendría procesar por lotes o en SQL. |
| PostgreSQL 16 en Docker | Reproduce una base relacional y permite comprobar restricciones e indicadores. | Docker y el puerto 5432 son requisitos de la demo local. |
| Clave primaria y `ON CONFLICT` | Garantizan unicidad e idempotencia de la carga incremental. | Los lotes de 500 filas no reemplazan `COPY` y staging a gran escala. |
| `TRUNCATE` dentro de la transacción | Reconstruye la muestra conservando las vistas existentes. | Reemplaza los 7.500 casos de la demo, no sirve como estrategia de actualización histórica. |
| Tabla detallada en Power BI | Mantiene la interacción coherente de los filtros de fecha, equipo y canal. | Las vistas agregadas se usan para consultas y validación, no para relaciones del modelo. |
| Importar en Power BI | Respuesta rápida con un conjunto pequeño y local. | Requiere actualizar el PBIX tras reconstruir PostgreSQL. |

El modelo contiene una fila por caso con su estado actual. `vw_daily_volume` agrupa por fecha de recepción y no mide cierres diarios reales. Las marcas `received_at` y `closed_at` permiten calcular cierres diarios y backlog a fecha de corte en [`vw_daily_backlog`](../sql/analytics/03_observable_history.sql), bajo el supuesto de que no hay reaperturas. Siguen faltando las transiciones entre estados abiertos.
