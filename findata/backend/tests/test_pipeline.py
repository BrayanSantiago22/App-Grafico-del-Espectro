"""Integration tests that execute the actual Spark SQL engine."""
import json, os
from pathlib import Path
import pytest
from app.pipeline import run_pipeline

@pytest.fixture(scope="module")
def report(tmp_path_factory):
    data_dir=Path(os.getenv("FINDATA_DATA_DIR",Path(__file__).resolve().parents[2]/"data"))
    output=tmp_path_factory.mktemp("findata")/"report.json"
    result=run_pipeline(data_dir=data_dir,output_path=output,master="local[2]")
    assert output.exists()
    assert json.loads(output.read_text(encoding="utf-8"))["project"]=="FinData"
    return result

def test_pipeline_uses_real_spark_sql(report):
    assert report["engine"]["name"]=="Apache Spark SQL"
    assert report["engine"]["version"]
    assert report["engine"]["master"]=="local[2]"

def test_sources_are_profiled(report):
    assert len(report["source_summary"])==3
    assert all(source["rows"]>0 for source in report["source_summary"])
    assert report["source_summary"][0]["fields"]

def test_schema_mapping_covers_three_entities(report):
    assert {x["entity"] for x in report["schema_mapping"]}=={"customers","accounts","transactions"}
    assert len(report["schema_mapping"])>=10

def test_quality_engine_detects_intentional_anomalies(report):
    assert report["quality"]["total_rules"]==12
    assert report["quality"]["failed_rules"]>0
    assert report["quality"]["failed_checks"]>0
    assert 0<=report["quality"]["score"]<=100

def test_account_reconciliation_compares_source_and_target(report):
    r=report["reconciliation"]
    assert r["source_account_count"]==r["target_account_count"]
    assert r["balance_difference"]==0
    assert r["status"]=="MATCH"

def test_certification_blocks_critical_issues(report):
    assert report["certification"]["status"]=="REVIEW_REQUIRED"
    assert report["certification"]["critical_failures"]>0
