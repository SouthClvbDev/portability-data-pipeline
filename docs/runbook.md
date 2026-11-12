# Manual de ejecución

Proyecto local: `D:\DataDeveloper\proyectos\portability-data-pipeline`. Ejecutar estos comandos en **PowerShell** desde la raíz del proyecto.

## Después de reiniciar Windows

1. Abrir Docker Desktop y esperar a que indique que el motor está funcionando.
2. Abrir la carpeta del proyecto en VS Code y una terminal PowerShell.
3. Ejecutar:

```powershell
cd D:\DataDeveloper\proyectos\portability-data-pipeline
.\.venv\Scripts\Activate.ps1
python --version
docker compose up -d
docker compose ps
```

`python --version` debe indicar Python 3.13.x dentro de `.venv`. `docker compose ps` debe mostrar `portability-postgres` en ejecución. Si Docker no responde, esperar a que Docker Desktop termine de iniciar y repetir los dos últimos comandos.

## ¿Tengo que volver a ejecutar el pipeline?

Si ya cargaste la tabla y las vistas, **no**: el volumen de PostgreSQL persiste tras reiniciar. Comprobar primero:

```powershell
docker exec portability-postgres psql -U data_user -d portability_db -c "SELECT COUNT(*) FROM portability_cases;"
docker exec portability-postgres psql -U data_user -d portability_db -c "SELECT * FROM vw_portability_kpis;"
```

Si ambas consultas funcionan y el total es 5000, abrir `dashboard/portability_operations.pbix` en Power BI Desktop y pulsar **Inicio → Actualizar** si hace falta. El modo Importar conserva la última instantánea en el PBIX; actualizar requiere PostgreSQL activo.

## Reconstruir todo desde cero o después de copiar el proyecto a otra PC

Si la carpeta `.venv` no existe, instalar Python 3.13 y crear el entorno:

```powershell
cd D:\DataDeveloper\proyectos\portability-data-pipeline
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

En otra PC, reemplazar la ruta `D:\DataDeveloper\...` por la ubicación real. Iniciar Docker Desktop y ejecutar, en orden:

```powershell
docker compose up -d
python src\generate_data.py
python src\validation\validate_data.py
python src\transformations\transform_cases.py
python src\load_to_postgres.py
Get-Content sql\analytics\01_operational_views.sql | docker exec -i portability-postgres psql -v ON_ERROR_STOP=1 -U data_user -d portability_db
```

Esperar a que PostgreSQL acepte conexiones antes de la carga. La carga actual **reemplaza** `portability_cases`: úsala para reconstruir o actualizar la muestra, no para conservar modificaciones manuales. Después de cargar, ejecutar otra vez el SQL de las vistas. Si PostgreSQL impide reemplazar la tabla porque existen vistas dependientes, detenerse y revisar la dependencia; no borrar el volumen ni la base para resolverlo.

Verificar:

```powershell
docker exec portability-postgres psql -U data_user -d portability_db -c "SELECT COUNT(*) AS total, COUNT(DISTINCT case_id) AS unicos FROM portability_cases;"
docker exec portability-postgres psql -U data_user -d portability_db -c "SELECT * FROM vw_portability_kpis;"
```

## Power BI

- Origen: **PostgreSQL database**, servidor `localhost:5432`, base `portability_db`, modo **Importar**.
- Con el contenedor actual: usuario `data_user`; la contraseña local está configurada en `docker-compose.yml`. No poner credenciales en el repositorio público ni en capturas.
- Seleccionar `public.portability_cases` para las tarjetas y los segmentadores de la primera página. Las cinco vistas sirven para consultar agregados, pero no se filtran entre sí sin un modelo de relaciones.
- Si la conexión falla tras reiniciar, comprobar `docker compose ps`, el puerto `5432` y las credenciales en **Archivo → Opciones y configuración → Configuración de origen de datos**.
- Guardar el PBIX como `dashboard/portability_operations.pbix`.

## Diagnóstico rápido

| Síntoma | Comprobación / acción |
|---|---|
| `docker` no responde | Abrir Docker Desktop y esperar a que arranque. |
| `portability-postgres` no está activo | `docker compose up -d`; después `docker compose ps`. |
| `relation portability_cases does not exist` | Ejecutar generación, validación, transformación y carga en ese orden. |
| Falta una vista | Ejecutar `01_operational_views.sql` con `ON_ERROR_STOP=1`; revisar el primer error. |
| Power BI muestra datos antiguos | Con PostgreSQL activo, pulsar **Actualizar** en Power BI. |
| La activación de `.venv` está bloqueada | Usar `.\.venv\Scripts\python.exe` en los comandos; no es obligatorio activar el entorno. |

Para detener sin borrar los datos: `docker compose stop`. Para reiniciar: `docker compose up -d`. **No ejecutar `docker compose down -v`** salvo que realmente se quiera eliminar el volumen de la base.
