"""Study 2 Part A: row-random vs template-group splits with the linear detector.

Refuses to run unless the leakage preregistration lock matches, is committed and pushed, and
AGENTS.md records the owner's approval amendment for this study.
"""

import json
import os
import subprocess
from pathlib import Path

import numpy as np
from joblib import Parallel, delayed

from injection_lab.adaptation import fit_detector
from injection_lab.data import file_sha256, read_json_rows, write_json
from injection_lab.splitcompare import (
    ATTACK_SOURCES,
    REPEATS,
    SPLIT_SEED_BASE,
    TEST_FRACTION,
    evaluate_split,
    group_split,
    nadeau_bengio_interval,
    recall_at_fpr,
    row_split,
)

LOCK = Path("results/leakage/PREREG_LOCK.json")
POOLS = Path("data/processed/study/pools.jsonl")
OUT = Path("results/leakage/split_comparison.json")
SUMMARY = Path("results/leakage/RESULTS.md")
APPROVAL = "PREREGISTRATION_LEAKAGE.md may be fit and scored"


def json_safe(value):
    """NaN (undefined metric, e.g. one group or p in {0, 1}) is written as null."""
    if isinstance(value, dict):
        return {k: json_safe(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [json_safe(v) for v in value]
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def verify():
    if APPROVAL not in Path("AGENTS.md").read_text(encoding="utf-8"):
        raise PermissionError("Owner approval amendment for study 2 is not recorded in AGENTS.md")
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    for path, digest in lock["sha256"].items():
        if file_sha256(path) != digest:
            raise AssertionError(f"{path} differs from the preregistered lock")
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    pushed = subprocess.run(
        ["git", "branch", "-r", "--contains", head], capture_output=True, text=True, check=True
    ).stdout.strip()
    if not pushed:
        raise AssertionError("Commit must be pushed before fitting")
    return head


def one_split(rows, kind, repeat):
    seed = SPLIT_SEED_BASE + repeat
    test = row_split(rows, seed) if kind == "row" else group_split(rows, seed)
    model = fit_detector([r for r, t in zip(rows, test) if not t])
    scores = np.full(len(rows), np.nan)
    scores[test] = model.predict_proba([r["text"] for r, t in zip(rows, test) if t])[:, 1]
    result = evaluate_split(scores, rows, test)
    result.update({"kind": kind, "repeat": repeat, "seed": seed, "n_test": int(test.sum())})
    return result


def leave_one_template_out(rows, group_id, benign_test):
    """Hold out one HackAPrompt template group plus a fixed benign test set."""
    test = benign_test | np.array([r["group"] == group_id for r in rows])
    model = fit_detector([r for r, t in zip(rows, test) if not t])
    s = model.predict_proba([r["text"] for r, t in zip(rows, test) if t])[:, 1]
    labels = np.array([r["label"] for r, t in zip(rows, test) if t])
    recall, _ = recall_at_fpr(s, labels, labels == 1)
    return {"group": group_id, "rows": int((labels == 1).sum()), "recall_at_1pct_fpr": recall}


def main():
    if OUT.exists():
        raise ValueError("Refusing to overwrite locked study-2 results")
    head = verify()
    rows = read_json_rows(POOLS)
    jobs = int(os.environ.get("STUDY_JOBS", "4"))
    splits = Parallel(n_jobs=jobs, verbose=5)(
        delayed(one_split)(rows, kind, r) for r in range(REPEATS) for kind in ("row", "group")
    )
    benign_test = group_split(rows, SPLIT_SEED_BASE) & np.array([r["label"] == 0 for r in rows])
    hp_groups = sorted(
        {r["group"] for r in rows if r["source"] == "hackaprompt-dataset" and r["label"] == 1}
    )
    loto = Parallel(n_jobs=jobs)(
        delayed(leave_one_template_out)(rows, g, benign_test) for g in hp_groups
    )
    n_test = int(np.mean([s["n_test"] for s in splits]))
    n_train = len(rows) - n_test
    metrics = ["auroc", "recall_at_1pct_fpr|pooled"]
    metrics += [f"recall_at_1pct_fpr|{s}" for s in ATTACK_SOURCES]
    inflation = {}
    for metric in metrics:
        row = {s["repeat"]: s[metric] for s in splits if s["kind"] == "row"}
        group = {s["repeat"]: s[metric] for s in splits if s["kind"] == "group"}
        diffs = [row[r] - group[r] for r in range(REPEATS)]
        inflation[metric] = {
            "row_mean": float(np.nanmean(list(row.values()))),
            "group_mean": float(np.nanmean(list(group.values()))),
            "inflation_mean": float(np.nanmean(diffs)),
            "inflation_ci95_nadeau_bengio": nadeau_bengio_interval(diffs, n_train, n_test),
            "per_repeat": diffs,
        }
    design = {}
    for source in ATTACK_SOURCES:
        values = [s[f"design_effect|{source}"] for s in splits if s["kind"] == "group"]
        values = np.array(values, dtype=float)
        design[source] = {
            "median": float(np.nanmedian(values)) if np.isfinite(values).any() else None,
            "range": [float(np.nanmin(values)), float(np.nanmax(values))]
            if np.isfinite(values).any()
            else None,
            "defined_repeats": int(np.isfinite(values).sum()),
        }
    report = {
        "preregistration_commit": head,
        "repeats": REPEATS,
        "split_seeds": [SPLIT_SEED_BASE + r for r in range(REPEATS)],
        "test_fraction": TEST_FRACTION,
        "splits": splits,
        "inflation": inflation,
        "design_effect_group_splits": design,
        "leave_one_hackaprompt_template_out": loto,
    }
    write_json(OUT, json_safe(report))
    lines = ["# Study 2 Part A results (locked run)", "", f"Commit `{head}`.", ""]
    lines += ["| Metric | Row split | Group split | Inflation | 95% CI (Nadeau-Bengio) |"]
    lines += ["| --- | ---: | ---: | ---: | --- |"]
    for metric, v in inflation.items():
        lo, hi = v["inflation_ci95_nadeau_bengio"]
        lines.append(
            f"| {metric} | {v['row_mean']:.3f} | {v['group_mean']:.3f} | "
            f"{v['inflation_mean']:+.3f} | [{lo:+.3f}, {hi:+.3f}] |"
        )
    lines += ["", "| Attack source | Design effect median | Range | Defined repeats |"]
    lines += ["| --- | ---: | --- | ---: |"]
    for source, v in design.items():
        rng = "n/a" if v["range"] is None else f"[{v['range'][0]:.1f}, {v['range'][1]:.1f}]"
        med = "n/a" if v["median"] is None else f"{v['median']:.1f}"
        lines.append(f"| {source} | {med} | {rng} | {v['defined_repeats']} |")
    lines += [
        "",
        "| Held-out HackAPrompt template | Rows | Recall at 1% FPR |",
        "| --- | ---: | ---: |",
    ]
    lines += [f"| {x['group']} | {x['rows']} | {x['recall_at_1pct_fpr']:.3f} |" for x in loto]
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(SUMMARY.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
