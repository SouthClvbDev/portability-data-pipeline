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

---

## Estructura principal

```text
portability-data-pipeline/
├── data/
│   ├── sample/
│   ├── raw/
│   └── processed/
├── docs/
├── sql/
│   └── analytics/
├── src/
│   ├── ingestion/
│   ├── transformations/
│   └── validation/
├── tests/
├── dashboard/
├── docker-compose.yml
├── requirements.txt
├── README.md
└── .gitignore



 Archivos y responsabilidades
Archivo	Responsabilidad
src/generate_data.py	Genera trámites sintéticos de portabilidad
src/validation/validate_data.py	Valida la calidad y consistencia de los datos
src/transformations/transform_cases.py	Limpia y transforma los datos para análisis
src/load_to_postgres.py	Carga el archivo procesado en PostgreSQL
sql/analytics/01_operational_views.sql	Crea vistas analíticas para los indicadores
docker-compose.yml	Levanta PostgreSQL mediante Docker
requirements.txt	Registra las dependencias de Python
.gitignore	Excluye archivos temporales y sensibles
README.md	Presenta el objetivo y las características del proyecto
docs/progress.md	Registra el avance técnico del proyecto


Flujo general del pipeline
src/generate_data.py
        ↓
data/sample/portability_cases.csv
        ↓
src/validation/validate_data.py
        ↓
src/transformations/transform_cases.py
        ↓
data/processed/portability_cases_clean.csv
        ↓
src/load_to_postgres.py
        ↓
PostgreSQL: portability_cases
        ↓
sql/analytics/01_operational_views.sql
        ↓
Vistas analíticas
        ↓
Power BI

Hitos completados
1. Configuración inicial
Archivos relacionados:
- docker-compose.yml
- requirements.txt
- .gitignore
- README.md
Tareas realizadas:
- Python configurado mediante un entorno virtual.
- Git inicializado.
- Git configurado con identidad de usuario.
- Docker verificado correctamente.
- WSL2 verificado correctamente.
- PostgreSQL configurado mediante Docker Compose.
- Dependencias de Python registradas en requirements.txt.
2. Generación de datos sintéticos
Archivo principal:
src/generate_data.py

Archivo generado:
data/sample/portability_cases.csv

Tareas realizadas:
- Se creó un generador reproducible en Python.
- Se generaron 5000 trámites ficticios.
- Se utilizó una semilla fija para reproducir los resultados.
- Se incluyeron fechas de recepción y cierre.
- Se incluyeron estados operativos.
- Se incluyeron canales de ingreso.
- Se incluyeron equipos de Backoffice.
- Se incluyeron estados de documentación y contacto.
- Se incluyeron motivos de rechazo y anulación.
- Se incluyeron tiempos de resolución.
- No se utilizaron datos reales de Telecom.
Estados incluidos:
- Recibido
- En análisis
- Pendiente documentación
- Pendiente contacto
- Aprobado
- Rechazado
- Anulado
3. Validación de calidad
Archivo principal:
src/validation/validate_data.py

Tareas realizadas:
- Se validaron las columnas obligatorias.
- Se validaron identificadores vacíos.
- Se validaron identificadores duplicados.
- Se validaron fechas de recepción.
- Se validaron fechas de cierre.
- Se validaron estados permitidos.
- Se verificó que una fecha de cierre no sea anterior a la fecha de recepción.
- Se verificó que los casos finalizados tengan fecha de cierre.
- Se verificó que los casos abiertos no tengan fecha de cierre.
- Se verificaron las reglas de documentación pendiente.
- Se verificaron las reglas de contacto pendiente.
- Se controlaron motivos de rechazo.
- Se controlaron motivos de anulación.
- Se controló la existencia del tiempo de resolución.
Resultado esperado:
VALIDACIÓN EXITOSA
5000 registros validados
No se encontraron inconsistencias.

4. Transformación analítica
Archivo principal:
src/transformations/transform_cases.py

Archivo generado:
data/processed/portability_cases_clean.csv

Tareas realizadas:
- Se convirtieron las fechas a tipos temporales.
- Se agregó la fecha de recepción.
- Se agregó el año de recepción.
- Se agregó el número de mes.
- Se agregó el nombre del mes.
- Se agregó el día de la semana.
- Se agregó el indicador is_closed.
- Se agregó el indicador is_pending.
- Se agregó el indicador has_documentation_pending.
- Se agregó el indicador has_contact_pending.
- Se agregó la clasificación sla_status.
- Se ordenaron las columnas para facilitar el análisis.
- Se generó un archivo procesado con 21 columnas.
Clasificación de SLA:
- No aplica
- Dentro de SLA
- Fuera de SLA
5. Configuración de PostgreSQL
Archivo principal:
docker-compose.yml

Configuración utilizada:
- Imagen: PostgreSQL 16.
- Base de datos: portability_db.
- Usuario: data_user.
- Puerto local: 5432.
- Contenedor: portability-postgres.
- Volumen persistente: postgres_data.
Tareas realizadas:
- Se creó el servicio PostgreSQL con Docker Compose.
- Se verificó que el contenedor esté activo.
- Se verificó que PostgreSQL acepte conexiones.
- Se confirmó la disponibilidad del puerto 5432.
Comando utilizado:
docker compose up -d

6. Carga de datos en PostgreSQL
Archivo principal:
src/load_to_postgres.py

Tabla creada:
portability_cases

Tareas realizadas:
- Se leyó el archivo procesado.
- Se estableció conexión desde Python con PostgreSQL.
- Se utilizó SQLAlchemy para administrar la conexión.
- Se utilizó psycopg2-binary como controlador.
- Se cargaron 5000 registros.
- Se verificó la cantidad total de registros.
- Se verificó que no existan identificadores duplicados.
Resultado:
Registros cargados: 5000
Identificadores únicos: 5000
Duplicados: 0

7. Capa analítica SQL
Archivo principal:
sql/analytics/01_operational_views.sql

Vistas creadas:
vw_portability_kpis
vw_cases_by_status
vw_daily_volume
vw_team_performance
vw_sla_by_channel

vw_portability_kpis
Contiene indicadores generales:
- Total de trámites.
- Casos abiertos.
- Casos cerrados.
- Casos aprobados.
- Casos rechazados.
- Casos anulados.
- Casos dentro de SLA.
- Casos fuera de SLA.
vw_cases_by_status
Contiene:
- Cantidad de trámites por estado.
- Porcentaje que representa cada estado.
- Ordenamiento por volumen.
vw_daily_volume
Contiene:
- Trámites recibidos por día.
- Casos cerrados por día.
- Casos pendientes por día.
vw_team_performance
Contiene:
- Total de casos por equipo.
- Aprobaciones por equipo.
- Rechazos por equipo.
- Anulaciones por equipo.
- Pendientes por equipo.
- Tiempo promedio de resolución.
vw_sla_by_channel
Contiene:
- Casos dentro de SLA por canal.
- Casos fuera de SLA por canal.
- Porcentaje de cumplimiento de SLA por canal.
Durante la creación de las vistas se resolvieron conversiones de tipos numéricos de PostgreSQL utilizando conversiones explícitas a numeric.


Comandos principales
Activar el entorno virtual
.\.venv\Scripts\Activate.ps1

Generar datos sintéticos
python src\generate_data.py

Validar datos
python src\validation\validate_data.py

Transformar datos
python src\transformations\transform_cases.py

Levantar PostgreSQL
docker compose up -d

Verificar el contenedor
docker compose ps

Cargar datos en PostgreSQL
python src\load_to_postgres.py

Crear o actualizar vistas analíticas
Get-Content sql\analytics\01_operational_views.sql |
docker exec -i portability-postgres psql -U data_user -d portability_db

Consultar indicadores generales
docker exec -it portability-postgres psql -U data_user -d portability_db -c "SELECT * FROM vw_portability_kpis;"

Consultar distribución por estado
docker exec -it portability-postgres psql -U data_user -d portability_db -c "SELECT * FROM vw_cases_by_status;"

Consultar rendimiento por equipo
docker exec -it portability-postgres psql -U data_user -d portability_db -c "SELECT * FROM vw_team_performance;"

Consultar SLA por canal
docker exec -it portability-postgres psql -U data_user -d portability_db -c "SELECT * FROM vw_sla_by_channel;"


Buenas prácticas aplicadas
- Uso de entorno virtual de Python.
- Uso de Git para control de versiones.
- Uso de commits descriptivos.
- Generación reproducible mediante una semilla fija.
- Separación entre datos de ejemplo, datos procesados y código.
- Validación antes de transformar los datos.
- Separación entre generación, validación, transformación y carga.
- Uso de Docker para PostgreSQL.
- Uso de variables de configuración con valores de desarrollo.
- Exclusión de entornos virtuales y archivos sensibles mediante .gitignore.
- Uso de vistas SQL para centralizar indicadores.
- No utilización de datos reales ni información sensible de Telecom.



### 8. Conexión con Power BI

Archivos relacionados:

- `dashboard/portability_operations.pbix`
- `sql/analytics/01_operational_views.sql`

Tareas realizadas:

- Se conectó Power BI con PostgreSQL.
- Se utilizaron las vistas analíticas como fuentes.
- Se creó una página de resumen operativo.
- Se incorporaron indicadores de volumen y estados.
- Se incorporó la evolución diaria de trámites.
- Se agregó análisis por equipo.
- Se agregó análisis de cumplimiento de SLA por canal.