"""Local API for executing the FinData Spark pipeline."""
import csv
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .pipeline import run_pipeline

DATA_DIR = Path(os.getenv("FINDATA_DATA_DIR", "/app/data"))
REPORT_PATH = Path(os.getenv("FINDATA_REPORT_PATH", "/app/site/spark-results.json"))

app = FastAPI(
    title="FinData API",
    description="API local de demostración para profiling, procesamiento y certificación financiera con PySpark.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "findata-api"}


@app.get("/api/sources")
def sources() -> dict[str, Any]:
    result = []
    for name in ("customers_legacy.csv", "accounts_legacy.csv", "transactions_legacy.csv"):
        path = DATA_DIR / name
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
            result.append({
                "name": name,
                "rows": len(rows),
                "columns": len(reader.fieldnames or []),
                "fields": reader.fieldnames or [],
            })
    return {"sources": result}


@app.get("/api/report")
def get_report() -> dict[str, Any]:
    if not REPORT_PATH.exists():
        raise HTTPException(status_code=404, detail="No existe un reporte. Ejecuta POST /api/run.")
    import json
    return json.loads(REPORT_PATH.read_text(encoding="utf-8"))


@app.post("/api/run")
def run() -> dict[str, Any]:
    try:
        return run_pipeline(DATA_DIR, REPORT_PATH)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
