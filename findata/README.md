# FinData — Financial Data Integration & Certification Platform

FinData es un proyecto de portafolio que simula integración bancaria Legacy → Moderno. Reúne exploración de fuentes, mapeo de esquemas, transformación con PySpark/Spark SQL, controles de calidad, conciliación financiera y evidencia de certificación.

> **Datos ficticios:** clientes, documentos, cuentas y movimientos son sintéticos. No se utiliza información real ni datos de entidades financieras.

## Demo pública
URL esperada: https://brayansantiago22.github.io/App-Grafico-del-Espectro/

El sitio queda disponible después de que el workflow termine correctamente. Si Pages no está habilitado, selecciona GitHub Actions en Settings → Pages → Build and deployment → Source.

## Capacidades
- Exploración de tres fuentes CSV: clientes, cuentas y transacciones.
- Perfilamiento local en navegador de CSV cargados (sin transmitirlos).
- Diccionario de correspondencias Legacy → modelo moderno.
- Transformación real mediante PySpark y Spark SQL.
- 12 reglas demostrativas de calidad e integridad.
- Conciliación de conteos y saldos entre origen y modelo normalizado.
- Reporte JSON y exportación de hallazgos CSV.
- API FastAPI para ejecutar Spark localmente.
- CI con Spark, pruebas Python, compilación TypeScript y GitHub Pages.

## Ejecución local con Docker
Requisitos: Docker Desktop con Compose y 4 GB de memoria disponibles.

Desde la carpeta findata:

    docker compose up --build

Interfaz: http://localhost:8080  
API: http://localhost:8000/api/health  
OpenAPI: http://localhost:8000/docs

En la interfaz local pulsa “Ejecutar Spark local”. La API ejecuta Spark local[2] y devuelve un reporte nuevo.

## Ejecución manual
Requisitos: Python 3.11 y Java 17.

    python -m pip install -r backend/requirements.txt
    python spark/generate_dataset.py --output data
    python spark/run_pipeline.py --data-dir data --output site/spark-results.json
    PYTHONPATH=. python -m pytest backend/tests -q

Generar lote limpio:

    python spark/generate_dataset.py --clean --output data-clean
    python spark/run_pipeline.py --data-dir data-clean --output site/clean-report.json

Generar un millón de transacciones sintéticas:

    python spark/generate_dataset.py --transactions 1000000 --output data-large
    python spark/run_pipeline.py --data-dir data-large --output site/large-report.json

## CI/CD
El workflow instala Java 17 y Python 3.11, genera fixtures deterministas, ejecuta PySpark/Spark SQL, ejecuta pruebas, compila TypeScript y publica la demo en GitHub Pages.

## Modelo y documentación
- sql/schema.sql: modelo relacional PostgreSQL.
- sql/analysis_queries.sql: CTE, JOIN, agregaciones y ventanas.
- spark/queries.sql: consultas Spark SQL.
- docs/data-dictionary.md: campos, equivalencias y anomalías.
- docs/architecture.md: arquitectura y decisiones.
- docs/interview-guide.md: recorrido de demo y preparación técnica.

## Alcance y limitaciones
- Spark corre en modo local local[2] en CI y Docker; no equivale a un clúster distribuido productivo.
- GitHub Pages sirve una demo estática con el reporte generado por Spark durante CI; no expone API pública ni clúster.
- El perfilador de CSV del navegador es local; el pipeline Spark utiliza las tres fuentes de muestra.
- No hay conexión a BBVA, Datum, Data Explora ni Data Contigo; se simulan estructuras financieras genéricas.
- Producción requeriría autenticación, autorización, cifrado, secretos, gobierno de datos y observabilidad.

Licencia: MIT.
