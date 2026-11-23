# Diccionario y mapeo de datos

Todos los registros son sintéticos. Los nombres de origen difieren intencionalmente de los campos normalizados.

## Clientes
| Origen | Destino | Tipo | Regla |
|---|---|---|---|
| customer_code | customer_id | VARCHAR(32) | TRIM; llave |
| full_name | customer_name | VARCHAR(160) | TRIM |
| id_number | document_number | VARCHAR(32) | TRIM; obligatorio y único |
| email_address | email | VARCHAR(180) | LOWER + TRIM; validar formato |
| birth_date | birth_date | DATE | TO_DATE yyyy-MM-dd |
| customer_status | status | VARCHAR(16) | A → ACTIVE; I → INACTIVE |
| branch_code | branch_id | VARCHAR(16) | TRIM |

## Cuentas
| Origen | Destino | Tipo | Regla |
|---|---|---|---|
| acct_no | account_id | VARCHAR(32) | TRIM; llave |
| cust_code | customer_id | VARCHAR(32) | FK hacia customers |
| acct_type | product_type | VARCHAR(16) | AHO → SAVINGS; CTE → CHECKING; CHQ → CHECKS |
| currency | currency_code | CHAR(3) | UPPER |
| opening_dt | opened_at | DATE | TO_DATE yyyy-MM-dd |
| balance_amt | ledger_balance | DECIMAL(18,2) | CAST |
| account_status | status | VARCHAR(16) | A → ACTIVE; C → CLOSED |

## Transacciones
| Origen | Destino | Tipo | Regla |
|---|---|---|---|
| txn_id | transaction_id | VARCHAR(40) | TRIM; llave única |
| acct_no | account_id | VARCHAR(32) | FK hacia accounts |
| txn_datetime | transaction_at | TIMESTAMP | TO_TIMESTAMP |
| txn_type | transaction_type | VARCHAR(12) | UPPER; DEBIT/CREDIT |
| amount | amount | DECIMAL(18,2) | CAST; mayor que cero |
| currency | currency_code | CHAR(3) | UPPER; COP/USD en demo |
| channel | channel | VARCHAR(16) | UPPER |
| reference | reference | VARCHAR(40) | TRIM |

## Anomalías intencionales
El generador estándar inserta documento duplicado y faltante, correo inválido, cuenta huérfana, producto legado no homologado, transacción huérfana, identificador duplicado, importe cero y moneda no soportada. Se puede generar un lote limpio con el argumento --clean.

## Definición del score
100 × (evaluaciones - fallos) / evaluaciones. Es una tasa agregada de verificaciones registro-regla sin fallo. No equivale al porcentaje de clientes, cuentas o transacciones completamente correctos. Las reglas críticas bloquean la certificación.
