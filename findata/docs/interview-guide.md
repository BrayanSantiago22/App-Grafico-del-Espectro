# Guía rápida para explicar FinData en entrevista

## Presentación de 90 segundos
“Construí FinData como una demostración de integración y certificación de información financiera entre un sistema legado y un modelo moderno. La solución recibe archivos de clientes, cuentas y transacciones, perfila sus estructuras y aplica un mapeo explícito de campos. Para transformar los datos utilicé PySpark y Spark SQL: normalizo identificadores, estados, productos, fechas y montos decimales. Después ejecuto reglas de calidad para detectar datos obligatorios, duplicados, dominios inválidos y relaciones huérfanas. Finalmente comparo conteos y saldos entre origen y destino y genero un reporte de certificación con hallazgos y evidencia. El proceso está automatizado con GitHub Actions: instala Java y Python, ejecuta Spark, corre pruebas y publica el dashboard. Los datos son sintéticos y Spark se ejecuta en modo local, por lo que es una demostración reproducible, no una integración bancaria productiva.”

## Recorrido de demostración
1. Dashboard: mostrar volumen de fuentes, score, fallos y conciliación.
2. Fuentes: abrir clientes, cuentas y transacciones; explicar el esquema legado.
3. Mapeo: mostrar acct_no → account_id y acct_type → product_type.
4. Calidad: explicar cuenta sin cliente y cómo se registra el hallazgo.
5. Conciliación: comparar cantidad de cuentas y saldo agregado origen/destino.
6. Certificación: explicar REVIEW_REQUIRED cuando fallan reglas críticas y descargar evidencia.

## Preguntas técnicas
**¿Qué hace Spark SQL?** Permite consultar y transformar datos con SQL sobre el motor Spark; el optimizador prepara el plan de ejecución.

**¿Transformación vs. acción?** Las transformaciones construyen un plan; acciones como count, collect o write disparan el cálculo.

**¿Por qué DECIMAL y no FLOAT para saldos?** Los importes financieros requieren precisión decimal fija; los flotantes pueden introducir aproximaciones binarias.

**¿Cómo detectas registros huérfanos?** Con LEFT ANTI JOIN entre la tabla hija y la padre; devuelve filas sin correspondencia.

**¿Cómo haces el mapeo?** Documento campo origen, campo destino, tipo, transformación, nulidad, dominio y relaciones; pruebo la conversión y concilio métricas.

**¿Cómo certificas una migración?** Defino reglas por entidad, valido esquema, calidad, unicidad, integridad referencial y conciliación de conteos y valores; guardo evidencia por lote.

**¿Qué significa REVIEW_REQUIRED?** Una o más reglas críticas fallaron. El lote no se aprueba automáticamente; se corrigen excepciones y se repite la ejecución.

**¿El proyecto usa un clúster distribuido?** No. La demo corre Spark local local[2] para ser reproducible y económica. El pipeline se puede adaptar a un clúster, pero no se ha desplegado uno.

**¿Los datos son reales?** No. Son datos sintéticos deterministas. No hay datos personales reales ni conexión a BBVA o herramientas internas de Inetum.

## Temas que debes dominar
JOIN, LEFT JOIN, LEFT ANTI JOIN, CTE, GROUP BY, HAVING; ROW_NUMBER y SUM OVER; DataFrames PySpark; vistas temporales; DECIMAL(18,2), DATE y TIMESTAMP; score, reglas fallidas y registros rechazados; conciliación de conteos y montos.
