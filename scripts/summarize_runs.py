"""Export comparable held-out metrics from completed runs as a CSV table."""

import argparse
import csv
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("reports", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    columns = [
        "run",
        "features",
        "dataset_sha256",
        "threshold",
        "n",
        "positives",
        "tn",
        "fp",
        "fn",
        "tp",
        "precision",
        "recall",
        "f1",
        "false_positive_rate",
        "average_precision",
        "roc_auc",
        "near_duplicate_flags",
    ]
    rows = []
    for path in args.reports:
        report = json.loads(path.read_text(encoding="utf-8"))
        result = report.get("test", report)
        metadata = report.get("metadata", {})
        row = {key: result.get(key, "") for key in columns}
        row.update(result["confusion_matrix"])
        row.update(
            {
                "run": path.parent.name,
                "features": metadata.get("features", "external"),
                "dataset_sha256": metadata.get("dataset_sha256", result.get("dataset_sha256", "")),
                "near_duplicate_flags": result["similarity_audit"]["flagged_count"],
            }
        )
        rows.append(row)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
