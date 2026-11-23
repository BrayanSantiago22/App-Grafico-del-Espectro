-- Spark SQL examples; the PySpark pipeline creates these temporary views.
-- legacy_customers, legacy_accounts, legacy_transactions
-- mapped_customers, mapped_accounts, mapped_transactions
SELECT COUNT(*) AS rows,
 SUM(CASE WHEN document_number IS NULL OR document_number='' THEN 1 ELSE 0 END) AS missing_documents,
 COUNT(DISTINCT customer_id) AS distinct_customer_ids
FROM mapped_customers;

SELECT a.account_id,a.customer_id FROM mapped_accounts a
LEFT ANTI JOIN mapped_customers c ON a.customer_id=c.customer_id;

SELECT transaction_id,COUNT(*) AS occurrences FROM mapped_transactions
GROUP BY transaction_id HAVING COUNT(*)>1;

SELECT
 (SELECT ROUND(SUM(CAST(balance_amt AS DECIMAL(18,2))),2) FROM legacy_accounts) AS legacy_total,
 (SELECT ROUND(SUM(ledger_balance),2) FROM mapped_accounts) AS target_total;
