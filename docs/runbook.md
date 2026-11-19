# Runbook: Portability Data Pipeline

Guía operativa para iniciar, reconstruir, validar y detener el proyecto desde Windows PowerShell.

## Requisitos

- Python 3.13
- Docker Desktop activo
- Power BI Desktop
- Git
- Puerto local `5432` disponible

## 1. Abrir el proyecto

```powershell
cd D:\DataDeveloper\proyectos\portability-data-pipeline
```

## 2. Activar el entorno virtual

```powershell
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la activación en la sesión actual:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 3. Instalar dependencias

Solo es necesario al crear o restaurar el entorno:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Iniciar PostgreSQL

```powershell
docker compose up -d
docker compose ps
```

El servicio esperado es `portability-postgres` en estado `Up`.

## 5. Reconstrucción completa

### 5.1 Generar el lote inicial

```powershell
python src\generate_data.py
```

### 5.2 Validar el lote inicial

```powershell
python src\validation\validate_data.py
```

### 5.3 Transformar el lote inicial

```powershell
python src\transformations\transform_cases.py
```

### 5.4 Ejecutar la carga inicial

```powershell
python src\load_to_postgres.py --mode initial
```

Si la tabla existe, el script utiliza `TRUNCATE` y conserva las vistas dependientes.

## 6. Carga incremental

### 6.1 Generar el lote

```powershell
python src\generate_incremental_data.py
```

### 6.2 Transformar el lote

```powershell
python src\transformations\transform_cases.py `
    --input data\sample\portability_cases_incremental.csv `
    --output data\processed\portability_cases_incremental_clean.csv
```

### 6.3 Cargar solamente registros nuevos

```powershell
python src\load_to_postgres.py `
    --mode append `
    --input data\processed\portability_cases_incremental_clean.csv
```

Resultado esperado tras la primera carga incremental:

```text
Registros nuevos cargados: 2500
Registros totales en PostgreSQL: 7500
```

Al repetirla:

```text
No hay registros nuevos para cargar.
Registros totales en PostgreSQL: 7500
```

## 7. Crear o actualizar vistas

Usar siempre `-Raw -Encoding UTF8` para preservar caracteres acentuados.

```powershell
Get-Content `
    -Path sql\analytics\01_operational_views.sql `
    -Raw `
    -Encoding UTF8 |
    docker exec -i portability-postgres psql `
    -v ON_ERROR_STOP=1 `
    -U data_user `
    -d portability_db
```

```powershell
Get-Content `
    -Path sql\analytics\02_monthly_metrics.sql `
    -Raw `
    -Encoding UTF8 |
    docker exec -i portability-postgres psql `
    -v ON_ERROR_STOP=1 `
    -U data_user `
    -d portability_db
```

## 8. Verificaciones SQL

Total:

```powershell
docker exec -it portability-postgres psql -U data_user -d portability_db -c "SELECT COUNT(*) FROM portability_cases;"
```

KPI:

```powershell
docker exec -it portability-postgres psql -U data_user -d portability_db -c "SELECT * FROM vw_portability_kpis;"
```

Rango temporal:

```powershell
docker exec -it portability-postgres psql -U data_user -d portability_db -c "SELECT MIN(received_date), MAX(received_date) FROM portability_cases;"
```

Duplicados:

```powershell
docker exec -it portability-postgres psql -U data_user -d portability_db -c "SELECT case_id, COUNT(*) FROM portability_cases GROUP BY case_id HAVING COUNT(*) > 1;"
```

Métricas mensuales:

```powershell
docker exec -it portability-postgres psql -U data_user -d portability_db -c "SELECT * FROM vw_monthly_operational_metrics;"
```

## 9. Ejecutar pruebas

PostgreSQL debe estar iniciado porque seis pruebas consultan la base.

```powershell
pytest -q
```

Resultado esperado:

```text
24 passed
```

## 10. Actualizar Power BI

1. Confirmar que PostgreSQL está activo.
2. Abrir `dashboard/portability_operations.pbix`.
3. Seleccionar **Actualizar**.
4. Verificar total `7500`, abiertos `3676` y cerrados `3824`.
5. Verificar el período enero-junio de 2023.

## 11. Verificar Git

```powershell
git status
```

Antes de finalizar una etapa:

```powershell
pytest -q
git add <archivos>
git commit -m "Descripción del cambio"
```

## 12. Detener servicios

Detener contenedores sin eliminar datos:

```powershell
docker compose stop
```

Volver a iniciarlos:

```powershell
docker compose start
```

Eliminar contenedores conservando el volumen:

```powershell
docker compose down
```

No usar `docker compose down -v` salvo que se desee eliminar deliberadamente la base persistida.

## Solución de problemas

### PostgreSQL no responde

```powershell
docker compose ps
docker compose logs postgres
```

### Una vista conserva una definición anterior

Volver a ejecutar el archivo SQL con `-Raw -Encoding UTF8`.

### La carga inicial intenta eliminar vistas

Usar la versión actual de `load_to_postgres.py`, que ejecuta `TRUNCATE` en lugar de `if_exists="replace"` cuando la tabla ya existe.

### Power BI muestra datos anteriores

Confirmar la base, ejecutar las vistas y luego seleccionar **Actualizar** dentro de Power BI.

