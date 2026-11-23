-- PostgreSQL analytical examples for the normalized FinData model.
SET search_path TO findata;
-- CTE + JOIN + conditional aggregation.
WITH account_portfolio AS (
 SELECT customer_id,COUNT(*) AS account_count,SUM(ledger_balance) AS total_balance,
        COUNT(*) FILTER(WHERE product_type='SAVINGS') AS savings_accounts,
        COUNT(*) FILTER(WHERE product_type='CHECKING') AS checking_accounts
 FROM accounts GROUP BY customer_id
)
SELECT c.customer_id,c.customer_name,c.status,COALESCE(p.account_count,0) AS account_count,
       COALESCE(p.total_balance,0) AS total_balance,
       COALESCE(p.savings_accounts,0) AS savings_accounts,
       COALESCE(p.checking_accounts,0) AS checking_accounts
FROM customers c LEFT JOIN account_portfolio p USING(customer_id)
ORDER BY total_balance DESC;

-- Window function: running net movement by account.
SELECT account_id,transaction_id,transaction_at,transaction_type,amount,
 SUM(CASE WHEN transaction_type='CREDIT' THEN amount ELSE -amount END)
 OVER(PARTITION BY account_id ORDER BY transaction_at,transaction_id
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_net_movement
FROM transactions ORDER BY account_id,transaction_at;

-- Referential-integrity exceptions.
SELECT a.account_id,a.customer_id FROM accounts a
LEFT JOIN customers c ON c.customer_id=a.customer_id WHERE c.customer_id IS NULL;

-- Daily reconciliation by currency.
SELECT transaction_at::date AS transaction_date,currency_code,COUNT(*) AS transaction_count,
 SUM(CASE WHEN transaction_type='CREDIT' THEN amount ELSE 0 END) AS credits,
 SUM(CASE WHEN transaction_type='DEBIT' THEN amount ELSE 0 END) AS debits
FROM transactions GROUP BY transaction_at::date,currency_code ORDER BY transaction_date,currency_code;
