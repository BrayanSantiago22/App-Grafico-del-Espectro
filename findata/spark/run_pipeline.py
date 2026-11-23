"""Command-line entry point for the FinData Spark SQL pipeline."""
import argparse
import json
from pathlib import Path

from backend.app.pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="findata/data")
    parser.add_argument("--output", default="findata/site/spark-results.json")
    parser.add_argument("--master", default="local[2]")
    args = parser.parse_args()
    report = run_pipeline(args.data_dir, args.output, args.master)
    print(json.dumps({
        "spark_version": report["engine"]["version"],
        "source_rows": {item["entity"]: item["rows"] for item in report["source_summary"]},
        "quality_score": report["quality"]["score"],
        "failed_checks": report["quality"]["failed_checks"],
        "reconciliation": report["reconciliation"]["status"],
        "certification": report["certification"]["status"],
        "output": str(Path(args.output)),
    }, indent=2))


if __name__ == "__main__":
    main()
