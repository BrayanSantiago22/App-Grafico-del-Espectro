# FinData — Financial Data Integration & Certification Platform

FinData es un proyecto de portafolio que simula un proceso de integración bancaria **Legacy → Moderno**. Reúne exploración de fuentes, mapeo de esquemas, transformación con PySpark/Spark SQL, controles de calidad, conciliación financiera y generación de evidencia de certificación.

> **Datos ficticios:** todos los nombres, documentos, cuentas y movimientos son sintéticos. No se utiliza información real de clientes ni de entidades financieras.

## Demo pública

La demo se publica mediante GitHub Pages después de que el workflow `FinData · Test Spark SQL and deploy demo` complete correctamente. La URL esperada del sitio de este repositorio es:

`https://brayansantiago22.github.io/App-Grafico-del-Espectro/`

Si Pages todavía no está habilitado o el workflow no ha terminado, consulta la pestaña **Actions** del repositorio y el estado del despliegue.

## Capacidades

- Exploración de cuatro fuentes CSV y perfilamiento básico.
- Carga local de CSV desde el navegador.
- Diccionario de correspondencias Legacy → Moderno.
- Transformación de cuentas con PySpark y Spark SQL.
- 18 reglas demostrativas de calidad e integridad.
- Conciliación de conteos, llaves y saldos.
- Reporte JSON de ejecución Spark y exportación de hallazgos CSV.
- API FastAPI para ejecutar el pipeline Spark localmente.
- CI con ejecución real de Spark SQL, pruebas Python y publicación de la interfaz.

## Arquitectura

```text
findata/
├── src/                       # Lógica de interfaz en TypeScript
├── site/                      # Sitio estático y reporte Spark generado
├── data/                      # CSV sintéticos Legacy y Moderno
├── backend/app/               # API FastAPI y pipeline PySpark
├── backend/tests/             # Pruebas del pipeline
├── spark/                     # CLI, SQL y generador de datos a escala
├── sql/                       # DDL PostgreSQL y consultas analíticas
├── docs/                      # Arquitectura, diccionario y guía de entrevista
├── Dockerfile.web
├── docker-compose.yml
└── tsconfig.json
```

## Ejecución local con Docker

Requisitos: Docker Desktop con Docker Compose y al menos 4 GB de memoria disponibles.

```bash
docker compose up --build
```

- Interfaz: http://localhost:8080
- API: http://localhost:8000/api/health
- Documentación OpenAPI: http://localhost:8000/docs

La API ejecuta Spark en modo local `local[2]`. La interfaz pública es estática y consume el reporte producido por Spark en el workflow de GitHub Actions. No se expone una API pública sin autenticación.

## Ejecución manual del pipeline

Requisitos: Python 3.11, Java 17 y dependencias de `backend/requirements.txt`.

```bash
python -m pip install -r backend/requirements.txt
FINDATA_DATA_DIR=./data python spark/run_pipeline.py --output site/spark-results.json
PYTHONPATH=. FINDATA_DATA_DIR=./data pytest backend/tests -q
```

## Prueba con más volumen

Genera un conjunto sintético con un millón de transacciones y ejecuta Spark sobre ese directorio:

```bash
python spark/generate_dataset.py --transactions 1000000 --output data/generated
FINDATA_DATA_DIR=./data/generated python spark/run_pipeline.py --data-dir ./data/generated --output ./site/spark-results-large.json
```

El generador crea registros reproducibles con una semilla fija. El tamaño real de prueba dependerá de la memoria, CPU y almacenamiento disponibles.

## Automatización CI/CD

El workflow `.github/workflows/findata-pages.yml` se activa al recibir cambios en la rama `findata-mvp`. Ejecuta:

1. Configuración de Java 17 y Python 3.11.
2. Instalación de PySpark y dependencias.
3. Ejecución del pipeline Spark SQL y generación de `site/spark-results.json`.
4. Pruebas automatizadas con pytest.
5. Compilación TypeScript.
6. Publicación de la interfaz en GitHub Pages.

## Modelo de datos y consultas

- `sql/schema.sql`: modelo relacional destino en PostgreSQL.
- `sql/analysis_queries.sql`: CTE, JOIN, agregaciones y funciones de ventana.
- `spark/queries.sql`: consultas Spark SQL para profiling, integridad y conciliación.
- `docs/data-dictionary.md`: definición de los campos y anomalías intencionales.

## Alcance y limitaciones

- Spark corre en modo local en CI y en Docker. Esto demuestra ejecución real del motor Spark SQL, pero **no equivale a operar un clúster distribuido productivo**.
- La interfaz pública es una demo estática con un resultado Spark generado durante CI. La API interactiva PySpark se ejecuta localmente.
- No se incluye conexión a BBVA, Datum, Data Explora ni Data Contigo. Se simulan estructuras genéricas de productos financieros.
- El conjunto pequeño permite demostrar las reglas; el generador sirve para ensayos de volumen.
- Para producción se necesitarían autenticación, autorización, cifrado, gestión de secretos, observabilidad, controles de acceso y gobierno formal de datos.

## Presentación del proyecto

Consulta [`docs/interview-guide.md`](docs/interview-guide.md) para el recorrido de demostración, presentación de 90 segundos y preguntas técnicas. Consulta [`docs/architecture.md`](docs/architecture.md) para la arquitectura y decisiones técnicas.

## Licencia

MIT. Ver [`LICENSE`](LICENSE).
