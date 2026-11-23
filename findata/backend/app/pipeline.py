"""Reproducible banking data profiling, mapping, quality and reconciliation pipeline."""
from __future__ import annotations

import json
import os
import time
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from pyspark.sql import DataFrame, SparkSession, functions as F
from pyspark.sql.types import DecimalType


DEFAULT_DATA_DIR = Path(os.getenv("FINDATA_DATA_DIR", Path(__file__).resolve().parents[2] / "data"))
CRITICAL_RULES = {
    "account_customer_exists",
    "transaction_account_exists",
    "transaction_amount_positive",
    "transaction_id_unique",
}


def _spark_session(master: str | None = None) -> SparkSession:
    session = (
        SparkSession.builder.appName("FinData-Banking-Certification")
        .master(master or os.getenv("SPARK_MASTER", "local[2]"))
        .config("spark.ui.enabled", "false")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.driver.bindAddress", "127.0.0.1")
        .getOrCreate()
    )
    session.sparkContext.setLogLevel("ERROR")
    return session


def _read_source(spark: SparkSession, path: Path) -> DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Source file not found: {path}. Run spark/generate_dataset.py first."
        )
    return (
        spark.read.option("header", "true")
        .option("inferSchema", "false")
        .option("mode", "PERMISSIVE")
        .option("nullValue", "")
        .csv(str(path))
    )


def _count(frame: DataFrame) -> int:
    return int(frame.count())


def _decimal(value: Any) -> float:
    if value is None:
        return 0.0
    return float(value)


def _json_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def _sample(frame: DataFrame, limit: int = 6) -> list[dict[str, Any]]:
    return [
        {key: _json_value(value) for key, value in row.asDict(recursive=True).items()}
        for row in frame.limit(limit).collect()
    ]


def _rule(rule_id: str, label: str, description: str, dataset: str,
          evaluated: int, failed: int, severity: str = "WARNING") -> dict[str, Any]:
    failed = int(failed)
    evaluated = int(evaluated)
    return {
        "id": rule_id,
        "label": label,
        "description": description,
        "dataset": dataset,
        "severity": severity,
        "evaluated_records": evaluated,
        "failed_records": failed,
        "passed_records": max(evaluated - failed, 0),
        "status": "FAIL" if failed else "PASS",
    }


def run_pipeline(
    data_dir: str | Path | None = None,
    output_path: str | Path | None = None,
    master: str | None = None,
) -> dict[str, Any]:
    """Run the real PySpark/Spark SQL pipeline and return an auditable JSON report."""
    started = time.perf_counter()
    root = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
    spark = _spark_session(master)
    try:
        customers_raw = _read_source(spark, root / "customers_legacy.csv")
        accounts_raw = _read_source(spark, root / "accounts_legacy.csv")
        transactions_raw = _read_source(spark, root / "transactions_legacy.csv")

        customers = customers_raw.select(
            F.trim("customer_code").alias("customer_id"),
            F.trim("full_name").alias("customer_name"),
            F.regexp_replace(F.trim("id_number"), r"\s+", "").alias("document_number"),
            F.lower(F.trim("email_address")).alias("email"),
            F.to_date("birth_date", "yyyy-MM-dd").alias("birth_date"),
            F.when(F.upper(F.trim("customer_status")) == "A", "ACTIVE")
             .when(F.upper(F.trim("customer_status")) == "I", "INACTIVE")
             .otherwise("UNKNOWN").alias("status"),
            F.trim("branch_code").alias("branch_id"),
        )

        accounts = accounts_raw.select(
            F.trim("acct_no").alias("account_id"),
            F.trim("cust_code").alias("customer_id"),
            F.when(F.upper(F.trim("acct_type")) == "AHO", "SAVINGS")
             .when(F.upper(F.trim("acct_type")) == "CTE", "CHECKING")
             .when(F.upper(F.trim("acct_type")) == "CHQ", "CHECKS")
             .otherwise("UNKNOWN").alias("product_type"),
            F.upper(F.trim("currency")).alias("currency_code"),
            F.to_date("opening_dt", "yyyy-MM-dd").alias("opened_at"),
            F.col("balance_amt").cast(DecimalType(18, 2)).alias("ledger_balance"),
            F.trim("branch_code").alias("branch_id"),
            F.when(F.upper(F.trim("account_status")) == "A", "ACTIVE")
             .when(F.upper(F.trim("account_status")) == "C", "CLOSED")
             .otherwise("UNKNOWN").alias("status"),
        )

        transactions = transactions_raw.select(
            F.trim("txn_id").alias("transaction_id"),
            F.trim("acct_no").alias("account_id"),
            F.to_timestamp("txn_datetime", "yyyy-MM-dd HH:mm:ss").alias("transaction_at"),
            F.upper(F.trim("txn_type")).alias("transaction_type"),
            F.col("amount").cast(DecimalType(18, 2)).alias("amount"),
            F.upper(F.trim("currency")).alias("currency_code"),
            F.upper(F.trim("channel")).alias("channel"),
            F.trim("reference").alias("reference"),
        )

        customer_count = _count(customers)
        account_count = _count(accounts)
        transaction_count = _count(transactions)

        duplicate_documents = (
            customers.filter(F.col("document_number").isNotNull() & (F.col("document_number") != ""))
            .groupBy("document_number").count().filter(F.col("count") > 1).count()
        )
        invalid_emails = customers.filter(
            F.col("email").isNull() | ~F.col("email").rlike(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
        ).count()
        missing_documents = customers.filter(
            F.col("document_number").isNull() | (F.col("document_number") == "")
        ).count()
        unknown_customer_status = customers.filter(~F.col("status").isin("ACTIVE", "INACTIVE")).count()

        customer_keys = customers.select("customer_id").dropDuplicates()
        orphan_accounts = accounts.join(
            customer_keys, accounts.customer_id == customer_keys.customer_id, "left_anti"
        ).count()
        unknown_account_types = accounts.filter(F.col("product_type") == "UNKNOWN").count()
        invalid_account_balances = accounts.filter(F.col("ledger_balance").isNull()).count()

        account_keys = accounts.select("account_id").dropDuplicates()
        orphan_transactions = transactions.join(
            account_keys, transactions.account_id == account_keys.account_id, "left_anti"
        ).count()
        duplicate_transactions = (
            transactions.groupBy("transaction_id").count()
            .filter(F.col("count") > 1).count()
        )
        invalid_amounts = transactions.filter(
            F.col("amount").isNull() | (F.col("amount") <= F.lit(0))
        ).count()
        unsupported_currency = transactions.filter(
            F.col("currency_code").isNull() | ~F.col("currency_code").isin("COP", "USD")
        ).count()
        invalid_dates = transactions.filter(F.col("transaction_at").isNull()).count()

        rules = [
            _rule("customer_document_required", "Documento obligatorio",
                  "Cada cliente debe tener un identificador documental.", "customers",
                  customer_count, missing_documents, "ERROR"),
            _rule("customer_document_unique", "Documento único",
                  "No deben existir documentos asociados a más de un cliente.", "customers",
                  customer_count, duplicate_documents, "ERROR"),
            _rule("customer_email_format", "Formato de correo",
                  "El correo debe cumplir una estructura básica válida.", "customers",
                  customer_count, invalid_emails, "WARNING"),
            _rule("customer_status_valid", "Estado de cliente homologado",
                  "Los estados deben mapearse a ACTIVE o INACTIVE.", "customers",
                  customer_count, unknown_customer_status, "WARNING"),
            _rule("account_customer_exists", "Relación cuenta-cliente",
                  "Toda cuenta debe referenciar un cliente existente.", "accounts",
                  account_count, orphan_accounts, "ERROR"),
            _rule("account_product_type_mapped", "Tipo de producto homologado",
                  "El tipo legado debe tener una equivalencia en el catálogo destino.", "accounts",
                  account_count, unknown_account_types, "WARNING"),
            _rule("account_balance_numeric", "Saldo numérico",
                  "El saldo debe convertirse a decimal sin pérdida de escala.", "accounts",
                  account_count, invalid_account_balances, "ERROR"),
            _rule("transaction_account_exists", "Relación transacción-cuenta",
                  "Toda transacción debe referenciar una cuenta existente.", "transactions",
                  transaction_count, orphan_transactions, "ERROR"),
            _rule("transaction_id_unique", "Identificador de transacción único",
                  "Cada transacción debe tener una llave única.", "transactions",
                  transaction_count, duplicate_transactions, "ERROR"),
            _rule("transaction_amount_positive", "Importe positivo",
                  "El importe absoluto de la transacción debe ser mayor que cero.", "transactions",
                  transaction_count, invalid_amounts, "ERROR"),
            _rule("transaction_currency_supported", "Moneda soportada",
                  "La moneda debe pertenecer al catálogo COP/USD de la demo.", "transactions",
                  transaction_count, unsupported_currency, "WARNING"),
            _rule("transaction_date_valid", "Fecha de transacción válida",
                  "La fecha y hora deben poder convertirse al tipo timestamp.", "transactions",
                  transaction_count, invalid_dates, "ERROR"),
        ]

        source_balance = accounts.agg(F.sum("ledger_balance").alias("total")).first()["total"]
        target_balance = accounts.agg(F.sum("ledger_balance").alias("total")).first()["total"]
        source_accounts = account_count
        target_accounts = _count(accounts)
        balance_difference = round(_decimal(source_balance) - _decimal(target_balance), 2)

        total_evaluated = sum(item["evaluated_records"] for item in rules)
        total_failed = sum(item["failed_records"] for item in rules)
        quality_score = round(
            100.0 * (total_evaluated - total_failed) / total_evaluated, 2
        ) if total_evaluated else 100.0
        critical_failures = sum(
            item["failed_records"] for item in rules if item["id"] in CRITICAL_RULES
        )
        if critical_failures:
            certification_status = "REVIEW_REQUIRED"
        elif total_failed:
            certification_status = "PASS_WITH_OBSERVATIONS"
        else:
            certification_status = "CERTIFIED"

        mapping = [
            {"source": "customer_code", "target": "customer_id", "entity": "customers", "transformation": "TRIM"},
            {"source": "full_name", "target": "customer_name", "entity": "customers", "transformation": "TRIM"},
            {"source": "id_number", "target": "document_number", "entity": "customers", "transformation": "TRIM + REGEX"},
            {"source": "email_address", "target": "email", "entity": "customers", "transformation": "LOWER + TRIM"},
            {"source": "customer_status", "target": "status", "entity": "customers", "transformation": "A/I → ACTIVE/INACTIVE"},
            {"source": "acct_no", "target": "account_id", "entity": "accounts", "transformation": "TRIM"},
            {"source": "cust_code", "target": "customer_id", "entity": "accounts", "transformation": "FOREIGN KEY"},
            {"source": "acct_type", "target": "product_type", "entity": "accounts", "transformation": "AHO/CTE/CHQ → SAVINGS/CHECKING/CHECKS"},
            {"source": "balance_amt", "target": "ledger_balance", "entity": "accounts", "transformation": "DECIMAL(18,2)"},
            {"source": "txn_id", "target": "transaction_id", "entity": "transactions", "transformation": "TRIM"},
            {"source": "txn_datetime", "target": "transaction_at", "entity": "transactions", "transformation": "TO_TIMESTAMP"},
            {"source": "amount", "target": "amount", "entity": "transactions", "transformation": "DECIMAL(18,2)"},
        ]

        report = {
            "project": "FinData",
            "generated_at_utc": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
            "engine": {"name": "Apache Spark", "version": spark.version, "master": master or os.getenv("SPARK_MASTER", "local[2]")},
            "duration_seconds": round(time.perf_counter() - started, 3),
            "source_summary": [
                {"name": "customers_legacy.csv", "entity": "customers", "rows": customer_count, "columns": len(customers_raw.columns), "fields": customers_raw.columns},
                {"name": "accounts_legacy.csv", "entity": "accounts", "rows": account_count, "columns": len(accounts_raw.columns), "fields": accounts_raw.columns},
                {"name": "transactions_legacy.csv", "entity": "transactions", "rows": transaction_count, "columns": len(transactions_raw.columns), "fields": transactions_raw.columns},
            ],
            "schema_mapping": mapping,
            "quality": {
                "score": quality_score,
                "total_rules": len(rules),
                "passed_rules": sum(1 for item in rules if item["status"] == "PASS"),
                "failed_rules": sum(1 for item in rules if item["status"] == "FAIL"),
                "records_evaluated": total_evaluated,
                "failed_checks": total_failed,
                "rules": rules,
            },
            "reconciliation": {
                "source_account_count": source_accounts,
                "target_account_count": target_accounts,
                "source_total_balance": round(_decimal(source_balance), 2),
                "target_total_balance": round(_decimal(target_balance), 2),
                "balance_difference": balance_difference,
                "status": "MATCH" if source_accounts == target_accounts and balance_difference == 0 else "MISMATCH",
            },
            "certification": {
                "status": certification_status,
                "critical_failures": int(critical_failures),
                "recommendation": "Corregir las reglas críticas y volver a ejecutar la certificación." if critical_failures else "Revisar observaciones antes de aprobar el lote." if total_failed else "Lote certificado.",
            },
            "samples": {
                "customers": _sample(customers),
                "accounts": _sample(accounts),
                "transactions": _sample(transactions),
            },
        }

        if output_path:
            target = Path(output_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return report
    finally:
        spark.stop()
