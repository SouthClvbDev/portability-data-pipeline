# Decisiones técnicas

## Propósito

Registrar las decisiones principales del proyecto, sus motivos y sus limitaciones. Esto permite comprender no solo qué se implementó, sino también por qué.

## Datos sintéticos

Se utilizan datos completamente ficticios para representar un proceso operativo realista sin exponer información de clientes ni sistemas internos.

Consecuencias:

- el repositorio puede publicarse;
- los resultados no representan desempeño real de una empresa;
- el SLA de 48 horas es una regla demostrativa.

## Python y pandas

Python separa generación, validación, transformación y carga. pandas facilita trabajar con CSV, tipos temporales y columnas derivadas.

La separación por responsabilidades permite probar cada etapa y reemplazar componentes más adelante.

## PostgreSQL en Docker

PostgreSQL proporciona SQL analítico, persistencia y una fuente compatible con Power BI. Docker garantiza una instalación reproducible y evita depender de una instalación manual del motor.

El volumen `postgres_data` persiste entre reinicios, pero no forma parte del repositorio. La base debe reconstruirse al mover el proyecto.

## Tabla detallada y vistas

`portability_cases` conserva una fila por trámite. Las vistas centralizan indicadores frecuentes y permiten validar resultados sin duplicar consultas.

Power BI utiliza principalmente la tabla detallada porque las vistas agregadas pierden granularidad y no reaccionan de manera uniforme a todos los segmentadores.

## Indicadores booleanos

La transformación crea `is_pending` e `is_closed` para centralizar la definición de abierto y cerrado.

Esto evita repetir listas de estados en Python, SQL y DAX, y reduce errores por diferencias de texto o codificación.

## Carga inicial mediante TRUNCATE

`if_exists="replace"` intenta eliminar y recrear la tabla. Esto falla cuando existen vistas dependientes.

La carga inicial actual:

1. verifica si la tabla existe;
2. ejecuta `TRUNCATE`;
3. inserta el dataset completo;
4. conserva las vistas.

## Carga incremental idempotente

El modo `append` consulta los `case_id` existentes y agrega solamente IDs nuevos.

Ventajas:

- repetir un lote no genera duplicados;
- se simula crecimiento de la base;
- el proceso es simple de explicar y probar.

Limitación: leer todos los IDs existentes con pandas no escala para millones de filas. En un escenario productivo se usaría staging, una clave primaria y `INSERT ... ON CONFLICT`, `MERGE` o una estrategia equivalente.

## Transformador parametrizable

`transform_cases.py` acepta `--input` y `--output`. Esto evita duplicar la lógica para cada lote y permite procesar nuevos archivos mediante el mismo código.

## SQL y UTF-8

PowerShell puede alterar caracteres acentuados al enviar un archivo mediante pipeline. Los scripts se ejecutan con:

```powershell
Get-Content -Raw -Encoding UTF8
```

Además, las vistas usan indicadores booleanos cuando existe una alternativa más segura que comparar textos.

## Power BI sobre la tabla base

Las medidas y visuales interactivos utilizan `portability_cases`. La tabla `Calendario` filtra `received_date` mediante una relación uno a muchos.

Las vistas se conservan para validación, consultas y posibles consumidores alternativos, pero no se relacionan entre sí ni con la tabla base dentro del modelo de Power BI.

## Importar frente a DirectQuery

Se eligió Importar porque el dataset es pequeño, local y orientado a portfolio. Ofrece interacción rápida y simplifica el desarrollo.

## Pruebas unitarias y de integración

- `test_pipeline.py` valida archivos y reglas sin depender de PostgreSQL.
- `test_database.py` valida el motor, la tabla y las vistas.

Las pruebas de base requieren Docker activo. Separarlas permite identificar si una falla pertenece al procesamiento o a la infraestructura.

## Archivos procesados fuera de Git

Los archivos de `data/processed` se regeneran y se excluyen de Git. Los datasets sintéticos de muestra sí se versionan para reproducibilidad.

## Credenciales

Las credenciales actuales tienen valores de desarrollo y pueden sobrescribirse mediante variables de entorno. Antes de publicar una versión productiva se recomienda usar `.env`, secretos del entorno o un gestor de secretos.

## Limitaciones temporales

`vw_daily_volume` agrupa por fecha de recepción y clasifica el estado actual. No reconstruye la historia del trámite ni mide cierres efectivos por día.

Para análisis histórico real serían necesarios:

- eventos de transición;
- snapshots periódicos;
- dimensión temporal de vigencia;
- backlog a fecha de corte.

