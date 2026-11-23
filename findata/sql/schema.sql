-- FinData target model (PostgreSQL compatible)
CREATE SCHEMA IF NOT EXISTS findata;
SET search_path TO findata;
CREATE TABLE IF NOT EXISTS customers (
 customer_id VARCHAR(32) PRIMARY KEY, customer_name VARCHAR(160) NOT NULL,
 document_number VARCHAR(32) NOT NULL UNIQUE, email VARCHAR(180), birth_date DATE,
 status VARCHAR(16) NOT NULL CHECK(status IN ('ACTIVE','INACTIVE')), branch_id VARCHAR(16)
);
CREATE TABLE IF NOT EXISTS accounts (
 account_id VARCHAR(32) PRIMARY KEY, customer_id VARCHAR(32) NOT NULL REFERENCES customers(customer_id),
 product_type VARCHAR(16) NOT NULL CHECK(product_type IN ('SAVINGS','CHECKING','CHECKS')),
 currency_code CHAR(3) NOT NULL, opened_at DATE, ledger_balance NUMERIC(18,2) NOT NULL,
 branch_id VARCHAR(16), status VARCHAR(16) NOT NULL CHECK(status IN ('ACTIVE','CLOSED'))
);
CREATE TABLE IF NOT EXISTS transactions (
 transaction_id VARCHAR(40) PRIMARY KEY, account_id VARCHAR(32) NOT NULL REFERENCES accounts(account_id),
 transaction_at TIMESTAMP NOT NULL, transaction_type VARCHAR(12) NOT NULL CHECK(transaction_type IN ('DEBIT','CREDIT')),
 amount NUMERIC(18,2) NOT NULL CHECK(amount>0), currency_code CHAR(3) NOT NULL,
 channel VARCHAR(16), reference VARCHAR(40)
);
CREATE INDEX IF NOT EXISTS ix_accounts_customer ON accounts(customer_id);
CREATE INDEX IF NOT EXISTS ix_transactions_account_date ON transactions(account_id,transaction_at);
