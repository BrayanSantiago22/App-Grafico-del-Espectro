"""Generate deterministic synthetic banking source files with known data-quality issues."""
import argparse
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def generate(output: Path, customers: int = 30, accounts: int = 45,
             transactions: int = 120, seed: int = 42) -> dict[str, int]:
    if customers < 10 or accounts < 10 or transactions < 20:
        raise ValueError("Use at least 10 customers, 10 accounts and 20 transactions.")
    rng = random.Random(seed)
    output.mkdir(parents=True, exist_ok=True)

    customer_rows = []
    for i in range(1, customers + 1):
        document = str(1000000000 + i)
        email = f"cliente{i:03d}@example.test"
        if i == 5:
            document = str(1000000004)  # Duplicate document: intentional anomaly.
        if i == 7:
            document = ""  # Missing document: intentional anomaly.
        if i == 8:
            email = "correo-no-valido"  # Invalid email: intentional anomaly.
        if i == 9:
            email = ""
        customer_rows.append({
            "customer_code": f"C{i:05d}",
            "full_name": f"Cliente Demostracion {i:03d}",
            "id_number": document,
            "email_address": email,
            "birth_date": (date_for(i)).strftime("%Y-%m-%d"),
            "customer_status": "I" if i % 9 == 0 else "A",
            "branch_code": f"SUC-{(i % 5) + 1:02d}",
        })
    write_csv(output / "customers_legacy.csv",
              ["customer_code", "full_name", "id_number", "email_address", "birth_date", "customer_status", "branch_code"],
              customer_rows)

    account_rows = []
    account_ids = []
    for i in range(1, accounts + 1):
        account_id = f"ACC{i:07d}"
        account_ids.append(account_id)
        customer_code = f"C{((i - 1) % customers) + 1:05d}"
        if i == 13:
            customer_code = "C99999"  # Orphan account: intentional anomaly.
        account_type = ("AHO", "CTE", "CHQ")[(i - 1) % 3]
        if i == 17:
            account_type = "OTR"  # Unmapped legacy product code.
        account_rows.append({
            "acct_no": account_id,
            "cust_code": customer_code,
            "acct_type": account_type,
            "currency": "COP",
            "opening_dt": (datetime(2020, 1, 1) + timedelta(days=i * 13)).strftime("%Y-%m-%d"),
            "balance_amt": f"{rng.randint(150000, 25000000)}.{rng.randint(0, 99):02d}",
            "branch_code": f"SUC-{(i % 5) + 1:02d}",
            "account_status": "C" if i % 14 == 0 else "A",
        })
    write_csv(output / "accounts_legacy.csv",
              ["acct_no", "cust_code", "acct_type", "currency", "opening_dt", "balance_amt", "branch_code", "account_status"],
              account_rows)

    transaction_rows = []
    base_date = datetime(2025, 1, 1)
    for i in range(1, transactions + 1):
        transaction_id = f"TXN{i:09d}"
        if i == 26:
            transaction_id = "TXN000000025"  # Duplicate key: intentional anomaly.
        account_id = rng.choice(account_ids)
        if i == 31:
            account_id = "ACC9999999"  # Orphan transaction: intentional anomaly.
        amount = round(rng.uniform(1000, 900000), 2)
        if i == 44:
            amount = 0  # Invalid amount: intentional anomaly.
        currency = "COP"
        if i == 45:
            currency = "XXX"  # Unsupported currency: intentional anomaly.
        when = base_date + timedelta(days=rng.randint(0, 650), minutes=rng.randint(0, 1439))
        transaction_rows.append({
            "txn_id": transaction_id,
            "acct_no": account_id,
            "txn_datetime": when.strftime("%Y-%m-%d %H:%M:%S"),
            "txn_type": "DEBIT" if i % 2 else "CREDIT",
            "amount": f"{amount:.2f}",
            "currency": currency,
            "channel": ("BRANCH", "ATM", "WEB", "MOBILE")[i % 4],
            "reference": f"REF-{i:010d}",
        })
    write_csv(output / "transactions_legacy.csv",
              ["txn_id", "acct_no", "txn_datetime", "txn_type", "amount", "currency", "channel", "reference"],
              transaction_rows)

    return {
        "customers": len(customer_rows),
        "accounts": len(account_rows),
        "transactions": len(transaction_rows),
    }


def date_for(index: int) -> datetime:
    return datetime(1965, 1, 1) + timedelta(days=index * 417)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="findata/data")
    parser.add_argument("--customers", type=int, default=30)
    parser.add_argument("--accounts", type=int, default=45)
    parser.add_argument("--transactions", type=int, default=120)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    counts = generate(Path(args.output), args.customers, args.accounts, args.transactions, args.seed)
    print("Synthetic banking data generated:", counts)


if __name__ == "__main__":
    main()
