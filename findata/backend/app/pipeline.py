"""Reproducible banking data profiling, mapping, quality and reconciliation with Spark SQL."""
from __future__ import annotations
import json, os, time
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from pyspark.sql import DataFrame, SparkSession, functions as F
from pyspark.sql.types import DecimalType

DEFAULT_DATA_DIR = Path(os.getenv("FINDATA_DATA_DIR", Path(__file__).resolve().parents[2] / "data"))
CRITICAL_RULES = {"account_customer_exists", "transaction_account_exists", "transaction_amount_positive", "transaction_id_unique"}

def _spark_session(master: str | None = None) -> SparkSession:
    session = (SparkSession.builder.appName("FinData-Banking-Certification")
        .master(master or os.getenv("SPARK_MASTER", "local[2]"))
        .config("spark.ui.enabled", "false")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.driver.bindAddress", "127.0.0.1").getOrCreate())
    session.sparkContext.setLogLevel("ERROR")
    return session

def _read_source(spark: SparkSession, path: Path) -> DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {path}")
    return (spark.read.option("header", "true").option("inferSchema", "false")
        .option("mode", "PERMISSIVE").option("nullValue", "").csv(str(path)))

def _json_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)): return value.isoformat()
    if isinstance(value, Decimal): return float(value)
    return value

def _sample(frame: DataFrame, limit: int = 6) -> list[dict[str, Any]]:
    return [{k: _json_value(v) for k, v in row.asDict(recursive=True).items()}
            for row in frame.limit(limit).collect()]

def _scalar(spark: SparkSession, query: str, field: str = "failures") -> int:
    return int(spark.sql(query).first()[field] or 0)

def _rule(rule_id: str, label: str, description: str, dataset: str,
          evaluated: int, failed: int, severity: str = "WARNING") -> dict[str, Any]:
    failed, evaluated = int(failed), int(evaluated)
    return {"id": rule_id, "label": label, "description": description,
            "dataset": dataset, "severity": severity, "evaluated_records": evaluated,
            "failed_records": failed, "passed_records": max(evaluated - failed, 0),
            "status": "FAIL" if failed else "PASS"}

def run_pipeline(data_dir: str | Path | None = None,
                 output_path: str | Path | None = None,
                 master: str | None = None) -> dict[str, Any]:
    """Execute Spark SQL transformations and return an auditable certification report."""
    started = time.perf_counter()
    root = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
    spark = _spark_session(master)
    try:
        customers_raw = _read_source(spark, root / "customers_legacy.csv")
        accounts_raw = _read_source(spark, root / "accounts_legacy.csv")
        transactions_raw = _read_source(spark, root / "transactions_legacy.csv")
        customers_raw.createOrReplaceTempView("legacy_customers")
        accounts_raw.createOrReplaceTempView("legacy_accounts")
        transactions_raw.createOrReplaceTempView("legacy_transactions")

        customers = spark.sql("""
            SELECT TRIM(customer_code) AS customer_id,
                   TRIM(full_name) AS customer_name,
                   REGEXP_REPLACE(TRIM(id_number), '[[:space:]]+', '') AS document_number,
                   LOWER(TRIM(email_address)) AS email,
                   TO_DATE(birth_date, 'yyyy-MM-dd') AS birth_date,
                   CASE UPPER(TRIM(customer_status))
                     WHEN 'A' THEN 'ACTIVE' WHEN 'I' THEN 'INACTIVE' ELSE 'UNKNOWN' END AS status,
                   TRIM(branch_code) AS branch_id
            FROM legacy_customers
        """)
        accounts = spark.sql("""
            SELECT TRIM(acct_no) AS account_id, TRIM(cust_code) AS customer_id,
                   CASE UPPER(TRIM(acct_type))
                     WHEN 'AHO' THEN 'SAVINGS' WHEN 'CTE' THEN 'CHECKING'
                     WHEN 'CHQ' THEN 'CHECKS' ELSE 'UNKNOWN' END AS product_type,
                   UPPER(TRIM(currency)) AS currency_code,
                   TO_DATE(opening_dt, 'yyyy-MM-dd') AS opened_at,
                   CAST(balance_amt AS DECIMAL(18,2)) AS ledger_balance,
                   TRIM(branch_code) AS branch_id,
                   CASE UPPER(TRIM(account_status))
                     WHEN 'A' THEN 'ACTIVE' WHEN 'C' THEN 'CLOSED' ELSE 'UNKNOWN' END AS status
            FROM legacy_accounts
        """)
        transactions = spark.sql("""
            SELECT TRIM(txn_id) AS transaction_id, TRIM(acct_no) AS account_id,
                   TO_TIMESTAMP(txn_datetime, 'yyyy-MM-dd HH:mm:ss') AS transaction_at,
                   UPPER(TRIM(txn_type)) AS transaction_type,
                   CAST(amount AS DECIMAL(18,2)) AS amount,
                   UPPER(TRIM(currency)) AS currency_code,
                   UPPER(TRIM(channel)) AS channel, TRIM(reference) AS reference
            FROM legacy_transactions
        """)
        customers.createOrReplaceTempView("mapped_customers")
        accounts.createOrReplaceTempView("mapped_accounts")
        transactions.createOrReplaceTempView("mapped_transactions")
        customer_count, account_count, transaction_count = customers.count(), accounts.count(), transactions.count()

        missing_documents = _scalar(spark, "SELECT COUNT(*) AS failures FROM mapped_customers WHERE document_number IS NULL OR document_number = ''")
        duplicate_documents = _scalar(spark, """SELECT COUNT(*) AS failures FROM (
            SELECT document_number FROM mapped_customers WHERE document_number IS NOT NULL AND document_number <> ''
            GROUP BY document_number HAVING COUNT(*) > 1) d""")
        invalid_emails = _scalar(spark, """SELECT COUNT(*) AS failures FROM mapped_customers
            WHERE email IS NULL OR email NOT RLIKE '^[^@ ]+@[^@ ]+[.][^@ ]+$'""")
        unknown_customer_status = _scalar(spark, "SELECT COUNT(*) AS failures FROM mapped_customers WHERE status NOT IN ('ACTIVE','INACTIVE')")
        orphan_accounts = _scalar(spark, """SELECT COUNT(*) AS failures FROM mapped_accounts a
            LEFT ANTI JOIN mapped_customers c ON a.customer_id = c.customer_id""")
        unknown_account_types = _scalar(spark, "SELECT COUNT(*) AS failures FROM mapped_accounts WHERE product_type = 'UNKNOWN'")
        invalid_account_balances = _scalar(spark, "SELECT COUNT(*) AS failures FROM mapped_accounts WHERE ledger_balance IS NULL")
        orphan_transactions = _scalar(spark, """SELECT COUNT(*) AS failures FROM mapped_transactions t
            LEFT ANTI JOIN mapped_accounts a ON t.account_id = a.account_id""")
        duplicate_transactions = _scalar(spark, """SELECT COUNT(*) AS failures FROM (
            SELECT transaction_id FROM mapped_transactions GROUP BY transaction_id HAVING COUNT(*) > 1) d""")
        invalid_amounts = _scalar(spark, "SELECT COUNT(*) AS failures FROM mapped_transactions WHERE amount IS NULL OR amount <= 0")
        unsupported_currency = _scalar(spark, "SELECT COUNT(*) AS failures FROM mapped_transactions WHERE currency_code IS NULL OR currency_code NOT IN ('COP','USD')")
        invalid_dates = _scalar(spark, "SELECT COUNT(*) AS failures FROM mapped_transactions WHERE transaction_at IS NULL")

        rules = [
            _rule("customer_document_required","Documento obligatorio","Cada cliente debe tener identificador documental.","customers",customer_count,missing_documents,"ERROR"),
            _rule("customer_document_unique","Documento único","Un documento no debe estar asociado a varios clientes.","customers",customer_count,duplicate_documents,"ERROR"),
            _rule("customer_email_format","Formato de correo","El correo debe cumplir una estructura básica válida.","customers",customer_count,invalid_emails,"WARNING"),
            _rule("customer_status_valid","Estado de cliente homologado","Los estados deben mapearse a ACTIVE o INACTIVE.","customers",customer_count,unknown_customer_status,"WARNING"),
            _rule("account_customer_exists","Relación cuenta-cliente","Toda cuenta debe referenciar un cliente existente.","accounts",account_count,orphan_accounts,"ERROR"),
            _rule("account_product_type_mapped","Tipo de producto homologado","El código legado debe tener equivalencia en el catálogo destino.","accounts",account_count,unknown_account_types,"WARNING"),
            _rule("account_balance_numeric","Saldo numérico","El saldo debe convertirse a DECIMAL(18,2).","accounts",account_count,invalid_account_balances,"ERROR"),
            _rule("transaction_account_exists","Relación transacción-cuenta","Toda transacción debe referenciar una cuenta existente.","transactions",transaction_count,orphan_transactions,"ERROR"),
            _rule("transaction_id_unique","Identificador de transacción único","Cada transacción debe tener una llave única.","transactions",transaction_count,duplicate_transactions,"ERROR"),
            _rule("transaction_amount_positive","Importe positivo","El importe debe ser mayor que cero.","transactions",transaction_count,invalid_amounts,"ERROR"),
            _rule("transaction_currency_supported","Moneda soportada","La moneda debe pertenecer al catálogo COP/USD de la demo.","transactions",transaction_count,unsupported_currency,"WARNING"),
            _rule("transaction_date_valid","Fecha de transacción válida","La fecha y hora deben convertirse a TIMESTAMP.","transactions",transaction_count,invalid_dates,"ERROR"),
        ]

        source_stats = accounts_raw.agg(
            F.count("*").alias("account_count"),
            F.sum(F.col("balance_amt").cast(DecimalType(18,2))).alias("total_balance")
        ).first()
        target_stats = accounts.agg(F.count("*").alias("account_count"), F.sum("ledger_balance").alias("total_balance")).first()
        source_balance, target_balance = float(source_stats["total_balance"] or 0), float(target_stats["total_balance"] or 0)
        source_accounts, target_accounts = int(source_stats["account_count"]), int(target_stats["account_count"])
        balance_difference = round(source_balance - target_balance, 2)
        total_evaluated = sum(x["evaluated_records"] for x in rules)
        total_failed = sum(x["failed_records"] for x in rules)
        quality_score = round(100 * (total_evaluated-total_failed)/total_evaluated, 2) if total_evaluated else 100.0
        critical_failures = sum(x["failed_records"] for x in rules if x["id"] in CRITICAL_RULES)
        cert_status = "REVIEW_REQUIRED" if critical_failures else ("PASS_WITH_OBSERVATIONS" if total_failed else "CERTIFIED")

        mapping = [
            {"source":"customer_code","target":"customer_id","entity":"customers","transformation":"TRIM"},
            {"source":"full_name","target":"customer_name","entity":"customers","transformation":"TRIM"},
            {"source":"id_number","target":"document_number","entity":"customers","transformation":"TRIM + REGEX"},
            {"source":"email_address","target":"email","entity":"customers","transformation":"LOWER + TRIM"},
            {"source":"customer_status","target":"status","entity":"customers","transformation":"A/I → ACTIVE/INACTIVE"},
            {"source":"acct_no","target":"account_id","entity":"accounts","transformation":"TRIM"},
            {"source":"cust_code","target":"customer_id","entity":"accounts","transformation":"FOREIGN KEY"},
            {"source":"acct_type","target":"product_type","entity":"accounts","transformation":"AHO/CTE/CHQ → SAVINGS/CHECKING/CHECKS"},
            {"source":"balance_amt","target":"ledger_balance","entity":"accounts","transformation":"DECIMAL(18,2)"},
            {"source":"txn_id","target":"transaction_id","entity":"transactions","transformation":"TRIM"},
            {"source":"txn_datetime","target":"transaction_at","entity":"transactions","transformation":"TO_TIMESTAMP"},
            {"source":"amount","target":"amount","entity":"transactions","transformation":"DECIMAL(18,2)"},
        ]
        report = {
            "project":"FinData",
            "generated_at_utc":datetime.utcnow().replace(microsecond=0).isoformat()+"Z",
            "engine":{"name":"Apache Spark SQL","version":spark.version,"master":master or os.getenv("SPARK_MASTER","local[2]"),"execution_mode":"local"},
            "duration_seconds":round(time.perf_counter()-started,3),
            "source_summary":[
                {"name":"customers_legacy.csv","entity":"customers","rows":customer_count,"columns":len(customers_raw.columns),"fields":customers_raw.columns},
                {"name":"accounts_legacy.csv","entity":"accounts","rows":account_count,"columns":len(accounts_raw.columns),"fields":accounts_raw.columns},
                {"name":"transactions_legacy.csv","entity":"transactions","rows":transaction_count,"columns":len(transactions_raw.columns),"fields":transactions_raw.columns}],
            "schema_mapping":mapping,
            "quality":{"score":quality_score,
                "score_definition":"Porcentaje agregado de verificaciones registro-regla sin fallo; no equivale al porcentaje de registros completamente correctos.",
                "total_rules":len(rules),"passed_rules":sum(x["status"]=="PASS" for x in rules),
                "failed_rules":sum(x["status"]=="FAIL" for x in rules),
                "records_evaluated":total_evaluated,"failed_checks":total_failed,"rules":rules},
            "reconciliation":{"source_account_count":source_accounts,"target_account_count":target_accounts,
                "source_total_balance":round(source_balance,2),"target_total_balance":round(target_balance,2),
                "balance_difference":balance_difference,
                "status":"MATCH" if source_accounts==target_accounts and balance_difference==0 else "MISMATCH"},
            "certification":{"status":cert_status,"critical_failures":int(critical_failures),
                "recommendation":"Corregir las reglas críticas y volver a ejecutar la certificación." if critical_failures else ("Revisar observaciones antes de aprobar el lote." if total_failed else "Lote certificado.")},
            "samples":{"customers":_sample(customers),"accounts":_sample(accounts),"transactions":_sample(transactions)}
        }
        if output_path:
            target = Path(output_path); target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
        return report
    finally:
        spark.stop()
