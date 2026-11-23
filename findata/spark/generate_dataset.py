"""Generate deterministic synthetic banking CSV files with optional known quality issues."""
import argparse, csv, random
from datetime import datetime, timedelta
from pathlib import Path

def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w",newline="",encoding="utf-8") as handle:
        writer=csv.DictWriter(handle,fieldnames=fields); writer.writeheader(); writer.writerows(rows)

def date_for(index: int) -> datetime:
    return datetime(1965,1,1)+timedelta(days=index*417)

def generate(output: Path, customers: int=30, accounts: int=45, transactions: int=120,
             seed: int=42, inject_anomalies: bool=True) -> dict[str,int]:
    if customers<10 or accounts<10 or transactions<20:
        raise ValueError("Use at least 10 customers, 10 accounts and 20 transactions.")
    rng=random.Random(seed); output.mkdir(parents=True,exist_ok=True)
    customer_rows=[]
    for i in range(1,customers+1):
        document=str(1000000000+i); email=f"cliente{i:03d}@example.test"
        if inject_anomalies and i==5: document=str(1000000004)
        if inject_anomalies and i==7: document=""
        if inject_anomalies and i==8: email="correo-no-valido"
        if inject_anomalies and i==9: email=""
        customer_rows.append({"customer_code":f"C{i:05d}","full_name":f"Cliente Demostracion {i:03d}",
          "id_number":document,"email_address":email,"birth_date":date_for(i).strftime("%Y-%m-%d"),
          "customer_status":"I" if i%9==0 else "A","branch_code":f"SUC-{(i%5)+1:02d}"})
    write_csv(output/"customers_legacy.csv",["customer_code","full_name","id_number","email_address","birth_date","customer_status","branch_code"],customer_rows)
    account_rows=[]; account_ids=[]
    for i in range(1,accounts+1):
        account_id=f"ACC{i:07d}"; account_ids.append(account_id)
        customer_code="C99999" if inject_anomalies and i==13 else f"C{((i-1)%customers)+1:05d}"
        account_type="OTR" if inject_anomalies and i==17 else ("AHO","CTE","CHQ")[(i-1)%3]
        account_rows.append({"acct_no":account_id,"cust_code":customer_code,"acct_type":account_type,
          "currency":"COP","opening_dt":(datetime(2020,1,1)+timedelta(days=i*13)).strftime("%Y-%m-%d"),
          "balance_amt":f"{rng.randint(150000,25000000)}.{rng.randint(0,99):02d}",
          "branch_code":f"SUC-{(i%5)+1:02d}","account_status":"C" if i%14==0 else "A"})
    write_csv(output/"accounts_legacy.csv",["acct_no","cust_code","acct_type","currency","opening_dt","balance_amt","branch_code","account_status"],account_rows)
    transaction_rows=[]; base=datetime(2025,1,1)
    for i in range(1,transactions+1):
        txn_id="TXN000000025" if inject_anomalies and i==26 else f"TXN{i:09d}"
        account_id="ACC9999999" if inject_anomalies and i==31 else rng.choice(account_ids)
        amount=0 if inject_anomalies and i==44 else round(rng.uniform(1000,900000),2)
        currency="XXX" if inject_anomalies and i==45 else "COP"
        when=base+timedelta(days=rng.randint(0,650),minutes=rng.randint(0,1439))
        transaction_rows.append({"txn_id":txn_id,"acct_no":account_id,"txn_datetime":when.strftime("%Y-%m-%d %H:%M:%S"),
          "txn_type":"DEBIT" if i%2 else "CREDIT","amount":f"{amount:.2f}","currency":currency,
          "channel":("BRANCH","ATM","WEB","MOBILE")[i%4],"reference":f"REF-{i:010d}"})
    write_csv(output/"transactions_legacy.csv",["txn_id","acct_no","txn_datetime","txn_type","amount","currency","channel","reference"],transaction_rows)
    return {"customers":len(customer_rows),"accounts":len(account_rows),"transactions":len(transaction_rows)}

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--output",default="findata/data")
    p.add_argument("--customers",type=int,default=30); p.add_argument("--accounts",type=int,default=45)
    p.add_argument("--transactions",type=int,default=120); p.add_argument("--seed",type=int,default=42)
    p.add_argument("--clean",action="store_true",help="Generate data without intentional anomalies.")
    a=p.parse_args()
    print("Synthetic banking data generated:",generate(Path(a.output),a.customers,a.accounts,a.transactions,a.seed,not a.clean))
if __name__=="__main__": main()
