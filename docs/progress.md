# Bitácora del proyecto

## Objetivo

Construir un pipeline de datos sintéticos para analizar trámites de portabilidad numérica gestionados por un área de Backoffice.

El proyecto busca demostrar experiencia en:

- Generación de datos.
- Validación de calidad.
- Transformación.
- Carga en PostgreSQL.
- Consultas SQL.
- Indicadores operativos.
- Visualización en Power BI.
- Automatización y buenas prácticas.

## Hitos completados

### 1. Configuración inicial

- Python configurado mediante entorno virtual.
- Git inicializado.
- Docker y WSL2 verificados.
- PostgreSQL ejecutándose en Docker.

### 2. Generación de datos

- Se creó un generador reproducible en Python.
- Se generaron 5000 trámites ficticios.
- Se utilizó una semilla fija para reproducir los resultados.
- No se utilizaron datos reales de Telecom.

### 3. Validación

- Se validaron identificadores duplicados.
- Se validaron fechas.
- Se validaron estados permitidos.
- Se verificaron reglas de documentación y contacto.
- Se controlaron motivos de rechazo y anulación.

### 4. Transformación

- Se agregaron campos de fecha.
- Se agregaron indicadores de casos abiertos y cerrados.
- Se clasificaron los casos según cumplimiento de SLA.
- Se generó un archivo analítico procesado.

### 5. Carga en PostgreSQL

- Se creó un contenedor PostgreSQL mediante Docker Compose.
- Se cargaron 5000 registros en la tabla `portability_cases`.
- Se verificó que no existan identificadores duplicados.

## Próximos pasos

- Crear vistas analíticas en PostgreSQL.
- Crear consultas de indicadores operativos.
- Conectar Power BI.
- Documentar decisiones de negocio.
- Incorporar pruebas automatizadas.
- Mejorar la carga para que sea incremental.