"""CLI entry point for the FinData Spark SQL pipeline."""
import argparse, json, sys
from pathlib import Path
PROJECT_ROOT=Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path: sys.path.insert(0,str(PROJECT_ROOT))
from backend.app.pipeline import run_pipeline  # noqa: E402

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-dir",default=str(PROJECT_ROOT/"data"))
    p.add_argument("--output",default=str(PROJECT_ROOT/"site"/"spark-results.json"))
    p.add_argument("--master",default="local[2]")
    a=p.parse_args()
    report=run_pipeline(a.data_dir,a.output,a.master)
    print(json.dumps({"spark_version":report["engine"]["version"],
      "source_rows":{x["entity"]:x["rows"] for x in report["source_summary"]},
      "quality_score":report["quality"]["score"],"failed_checks":report["quality"]["failed_checks"],
      "reconciliation":report["reconciliation"]["status"],"certification":report["certification"]["status"],
      "output":str(Path(a.output))},indent=2))
if __name__=="__main__": main()
