"""Rerun unchanged baselines; report only metrics with seeds and uncertainty."""

import json
import platform
from pathlib import Path

from injection_lab.curation import SEEDS, cross_split_edges
from injection_lab.data import assert_disjoint, file_sha256, read_rows, write_json, write_jsonl
from injection_lab.experiment import build_model, select_threshold, wilson

FEATURES = ("word", "char", "combined")


def rates(y, predicted):
    counts = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
    for label, prediction in zip(y, predicted):
        counts[
            "tp" if label and prediction else "fn" if label else "fp" if prediction else "tn"
        ] += 1
    tp, fp, tn, fn = (counts[key] for key in ("tp", "fp", "tn", "fn"))
    return {
        "counts": counts,
        "recall": {"estimate": tp / (tp + fn), "ci95": wilson(tp, tp + fn)},
        "false_positive_rate": {"estimate": fp / (fp + tn), "ci95": wilson(fp, fp + tn)},
    }


def cell(rate):
    value = rate["estimate"] * 100
    low, high = (v * 100 for v in rate["ci95"])
    return f"{value:.1f}% [{low:.1f}, {high:.1f}]"


def main():
    out = Path("results/repair/baselines.json")
    if out.exists():
        raise ValueError("Refusing to overwrite completed repair results")
    audit = json.loads(Path("results/repair/deduplication-audit.json").read_text())
    runs = []
    for seed in SEEDS:
        path = Path(f"data/processed/repaired/seed-{seed}.jsonl")
        if file_sha256(path) != audit["output_sha256"][str(seed)]:
            raise AssertionError("Input differs from the pre-fit repair audit")
        rows = read_rows(path)
        if list(cross_split_edges(rows)):
            raise AssertionError("Residual cross-split near duplicates")
        splits = {
            name: [r for r in rows if r["split"] == name]
            for name in ("train", "validation", "test")
        }
        for a, b in (("train", "validation"), ("train", "test"), ("validation", "test")):
            assert_disjoint(splits[a], splits[b], f"{a}/{b}")
        for features in FEATURES:
            model = build_model(seed, features)
            model.fit([r["text"] for r in splits["train"]], [r["label"] for r in splits["train"]])
            validation_scores = model.predict_proba([r["text"] for r in splits["validation"]])[:, 1]
            threshold = select_threshold(
                [r["label"] for r in splits["validation"]], validation_scores, 0.05
            )
            scores = model.predict_proba([r["text"] for r in splits["test"]])[:, 1]
            report = {
                "features": features,
                "split_seed": seed,
                "model_seed": seed,
                "threshold": threshold,
                "validation_fpr_budget": 0.05,
                "dataset_sha256": file_sha256(path),
                "test_n": len(splits["test"]),
                "ci_method": "two-sided 95% Wilson, conditional on fitted model/threshold",
                **rates([r["label"] for r in splits["test"]], scores >= threshold),
            }
            runs.append(report)
            write_jsonl(
                f"artifacts/repaired/seed-{seed}/{features}/predictions.jsonl",
                [
                    {
                        "id": row["id"],
                        "group_id": row["group_id"],
                        "label": row["label"],
                        "score": float(score),
                        "prediction": int(score >= threshold),
                    }
                    for row, score in zip(splits["test"], scores)
                ],
            )
            print(
                f"seed={seed}, {features}: recall {cell(report['recall'])}; "
                f"FPR {cell(report['false_positive_rate'])}; Wilson 95% CI"
            )
    # Historical values are read only after all corrected fits and audits have completed.
    previous = []
    for features in FEATURES:
        path = Path(f"artifacts/deepset-{features}/test_predictions.jsonl")
        predictions = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        previous.append(
            {
                "features": features,
                "split_seed": 42,
                "model_seed": 42,
                "status": "WITHDRAWN; descriptive historical audit only",
                "ci_caveat": "Nominal Wilson intervals do not correct leakage or template dependence",
                "predictions_sha256": file_sha256(path),
                **rates([r["label"] for r in predictions], [r["prediction"] for r in predictions]),
            }
        )
    import importlib.metadata

    versions = {
        name: importlib.metadata.version(name)
        for name in ("scikit-learn", "numpy", "scipy", "joblib")
    }
    report = {
        "status": "EXPLORATORY DATA-REPAIR CHECK, not confirmatory evidence",
        "python": platform.python_version(),
        "versions": versions,
        "seeds": list(SEEDS),
        "bootstrap_seed": None,
        "ci_method": "Wilson analytical intervals; no bootstrap used",
        "code_sha256": {
            str(path): file_sha256(path)
            for path in (Path(__file__), Path("src/injection_lab/experiment.py"))
        },
        "audit_sha256": file_sha256("results/repair/deduplication-audit.json"),
        "before": previous,
        "after": runs,
        "limitations": [
            "Before/after test membership differs; differences are not causal leakage estimates.",
            "Wilson intervals assume independence between retained lexical groups.",
            "Intervals condition on fitting and threshold selection; seed sensitivity is separate.",
            "Different seed test sets overlap; do not pool their denominators.",
            "This small corpus cannot establish recall at 1% population FPR.",
        ],
    }
    write_json(out, report)
    lines = [
        "# Data repair: before/after audit",
        "",
        "The original scores are WITHDRAWN. They appear below only for the requested audit comparison.",
        "All intervals are two-sided 95% Wilson. Historical intervals are nominal and do not remedy leakage.",
        "The before/after test sets differ, so changes cannot be attributed solely to leakage removal.",
        "",
        "## Seed 42 comparison (split seed = model seed)",
        "",
        "| Features | Before recall (withdrawn) | After recall | Before FPR (withdrawn) | After FPR |",
        "| --- | --- | --- | --- | --- |",
    ]
    for old in previous:
        new = next(r for r in runs if r["split_seed"] == 42 and r["features"] == old["features"])
        lines.append(
            f"| {old['features']} | {cell(old['recall'])} | {cell(new['recall'])} | "
            f"{cell(old['false_positive_rate'])} | {cell(new['false_positive_rate'])} |"
        )
    lines += [
        "",
        "## All prescribed seeds",
        "",
        "Seeds were set to 17, 29, 42, 71, 101 before fitting; none selected on performance.",
        "| Seed | Features | Test N | TP/FN/FP/TN | Recall [95% CI] | FPR [95% CI] |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]
    for run in runs:
        c = run["counts"]
        lines.append(
            f"| {run['split_seed']} | {run['features']} | {run['test_n']} | "
            f"{c['tp']}/{c['fn']}/{c['fp']}/{c['tn']} | {cell(run['recall'])} | "
            f"{cell(run['false_positive_rate'])} |"
        )
    lines += [
        "",
        "The operating point remains the original 5% empirical validation FPR budget to keep the",
        "baseline recipe fixed during repair. These are not results at 1% FPR. The proposed larger",
        "study uses a different, prespecified operating point and has not been run.",
        "",
        "See baselines.json for counts, seeds, thresholds, hashes and limitations; see",
        "deduplication-audit.json for every component and removal decision.",
        "",
    ]
    Path("results/repair/COMPARISON.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
