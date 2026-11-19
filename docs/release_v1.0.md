# v1.0 — Portability Data Pipeline

Primera versión de portfolio reproducible del pipeline analítico de portabilidad. Todos los casos son sintéticos.

## Incluye

- Dos lotes CSV de 5.000 y 2.500 casos, con validación de reglas operativas.
- Transformación a 21 columnas analíticas.
- PostgreSQL 16 con esquema explícito, clave primaria, restricciones e índices.
- Carga inicial transaccional e incremental idempotente con `ON CONFLICT`.
- Seis vistas SQL y dashboard Power BI de tres páginas de contenido.
- Demo local con `bash scripts/demo.sh` y 24 pruebas automatizadas.
- CI en GitHub Actions para reconstruir y validar la demo.

## Verificación local

`bash scripts/demo.sh` completó 24 pruebas y produjo 7.500 casos: 3.676 abiertos y 3.824 cerrados. Una segunda carga incremental informó cero registros nuevos.

## Limitaciones conocidas

- El PBIX requiere Power BI Desktop y refrescar la conexión local a PostgreSQL.
- El archivo también conserva una página vacía llamada “Página 1”, que se puede quitar desde Power BI Desktop antes de una futura exportación.
- La vista diaria agrupa por recepción y muestra estados actuales; el backlog histórico requiere eventos de cambio de estado.
- Las capturas reales del dashboard se incorporarán al exportarlas desde Power BI Desktop.
