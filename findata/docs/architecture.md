# FinData — arquitectura técnica

## Propósito
Demostrar integración financiera desde estructuras legadas hacia un modelo moderno: exploración, mapeo, transformación, calidad, conciliación y certificación.

## Arquitectura lógica
Fuentes CSV (clientes, cuentas y transacciones)
→ exploración de esquema y perfilamiento
→ mapeo Legacy a modelo normalizado
→ PySpark y Spark SQL en modo local reproducible
→ reglas de calidad e integridad referencial
→ conciliación de conteos y saldos
→ reporte JSON de certificación
→ dashboard TypeScript (GitHub Pages) y API FastAPI (Docker local).

## Componentes
- Fuentes: tres CSV sintéticos que representan clientes, cuentas y transacciones de un core legado.
- Motor: PySpark 3.5.6 / Spark SQL, con ejecución local local[2].
- Modelo destino: DDL PostgreSQL en sql/schema.sql; la demo crea DataFrames normalizados en memoria.
- API: FastAPI expone health, sources, report y run.
- Frontend: TypeScript sin dependencias de runtime; consume el reporte Spark.
- CI/CD: GitHub Actions instala Java y Python, ejecuta Spark SQL, pruebas, compila TypeScript y despliega Pages.

## Flujo de certificación
1. Leer fuentes y perfilar filas, columnas y campos.
2. Homologar nombres, estados, productos, fechas y montos.
3. Ejecutar 12 reglas de calidad sobre clientes, cuentas y transacciones.
4. Comparar conteo de cuentas y saldo agregado del origen contra el modelo normalizado.
5. Clasificar el lote como CERTIFIED, PASS_WITH_OBSERVATIONS o REVIEW_REQUIRED.
6. Exportar reporte y conservar evidencia reproducible.

## Seguridad y límites
Los datos son sintéticos. No hay credenciales ni conexión bancaria real. La página pública es estática: muestra un reporte generado por Spark durante CI, no un clúster Spark ni una API pública. La ejecución interactiva se realiza con Docker local. El pipeline corre en modo local; no debe describirse como clúster distribuido productivo.

Para producción se añadirían autenticación, autorización, secretos gestionados, cifrado, catálogo y gobierno de datos, observabilidad, linaje, almacenamiento de resultados y runtime Spark distribuido.
