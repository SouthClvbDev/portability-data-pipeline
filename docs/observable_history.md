# Historia observable y backlog diario

Los casos sintéticos tienen `received_at` y, cuando se resuelven, `closed_at`. Esas marcas permiten reconstruir **ingresos, cierres y casos abiertos al final de cada día** sin inventar transiciones intermedias.

## Definición

Para una fecha de corte `D`:

```text
Backlog al cierre de D = casos con received_at::date <= D
                        y (closed_at es nulo o closed_at::date > D)
```

Un caso recibido y cerrado el mismo día no queda abierto al cierre. Un cierre posterior a la última recepción puede hacer que el backlog al final de junio sea distinto del total de estados abiertos en la instantánea final.

## Implementación

- [`sql/analytics/03_observable_history.sql`](../sql/analytics/03_observable_history.sql) crea `vw_case_observed_events` (recepción y cierre) y `vw_daily_backlog` (ingresos, cierres y abiertos al cierre de cada día). `scripts/demo.sh` las reconstruye junto con las otras vistas.
- [`web/lib/history.mjs`](../web/lib/history.mjs) calcula la misma serie desde los CSV versionados. El build publica `web/public/data/history.json` y conserva las fechas necesarias para que el asistente responda «backlog al 2023-05-31».
- La web permite recorrer los días y llevar la fecha seleccionada al asistente. Las cifras se regeneran con los CSV en cada despliegue.

## Límite

El archivo conserva solo el **estado actual** de cada caso. No registra cuándo pasó por «En análisis», «Pendiente documentación» u otros estados abiertos. Tampoco registra reaperturas; el cálculo supone que un cierre finaliza el caso. La vista de eventos contiene únicamente las dos marcas observables. Para analizar duración por etapa o reaperturas reales hará falta un registro de transiciones desde el origen.

`vw_daily_volume` sigue agrupando los estados actuales por fecha de recepción; no debe leerse como cierres diarios. Para cierres reales por día se usa `vw_daily_backlog.closed_cases`.

## Comprobaciones

- La suma de ingresos diarios coincide con la cantidad de casos.
- La suma de cierres diarios coincide con los casos finales.
- El último backlog coincide con los casos abiertos de la instantánea.
- SQL y web dan el mismo resultado para una misma fecha de corte.

Estas comprobaciones corren con `bash scripts/demo.sh` y `npm run test:web`.
