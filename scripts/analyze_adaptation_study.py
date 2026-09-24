"""Prespecified analysis of the locked run; writes results JSON and a Markdown summary."""

import json
from pathlib import Path

import numpy as np

from injection_lab.data import file_sha256, read_json_rows, write_json
from injection_lab.study_analysis import analyze

POOLS = Path("data/processed/study/pools.jsonl")
SCORES = Path("artifacts/study/scores.npz")
RUN_LOG = Path("results/study/run_log.json")
RESULTS = Path("results/study/results.json")
SUMMARY = Path("results/study/RESULTS.md")
ARMS = ("frozen", "threshold_only", "generic", "matched", "matched+threshold")


def pct(value):
    return "n/a" if value is None or np.isnan(value) else f"{100 * value:.1f}"


def cell(entry):
    low, high = entry["ci95"]
    return f"{pct(entry['estimate_seed_mean'])} [{pct(low)}, {pct(high)}]"


def main():
    if RESULTS.exists():
        raise ValueError("Refusing to overwrite locked results")
    log = json.loads(RUN_LOG.read_text(encoding="utf-8"))
    if file_sha256(SCORES) != log["scores_sha256"]:
        raise AssertionError("Scores differ from the locked run")
    rows = read_json_rows(POOLS)
    with np.load(SCORES) as data:
        scores = {k.replace("__", ":"): data[k] for k in data.files}
    report = analyze(rows, scores)
    report["run"] = {
        "preregistration_commit": log["preregistration_commit"],
        "scores_sha256": log["scores_sha256"],
    }
    write_json(RESULTS, report)
    SUMMARY.write_text(render(report), encoding="utf-8")
    print(SUMMARY.read_text(encoding="utf-8"))


def lookup(report, set_name, arm, budget, metric):
    for d in report["descriptive"]:
        if (d["set"], d["arm"], d["budget"], d["metric"]) == (set_name, arm, budget, metric):
            return d
    return None


def render(report):
    lines = [
        "# Adaptation study results (locked run)",
        "",
        f"Preregistration commit `{report['run']['preregistration_commit']}`. Seeds "
        f"{', '.join(map(str, report['design']['seeds']))}. Percentages. Intervals are "
        "percentile bootstrap intervals that jointly resample evaluation groups and the "
        "five adaptation seeds; operational thresholds are held fixed. Seeds share the "
        "same evaluation rows and are not independent test examples.",
        "",
        "## Confirmatory contrasts (target recall at 1% FPR, B=200)",
        "",
        "| Contrast | Estimate (points) | 97.5% CI | 95% CI | Per seed |",
        "| --- | ---: | --- | --- | --- |",
    ]
    for c in report["confirmatory"]:
        per_seed = ", ".join(f"{s}: {100 * v:+.2f}" for s, v in c["per_seed"].items())
        lo, hi = c["ci97_5"]
        lo95, hi95 = c["ci95"]
        lines.append(
            f"| {c['contrast']} | {100 * c['estimate_seed_mean']:+.2f} | "
            f"[{100 * lo:+.2f}, {100 * hi:+.2f}] | [{100 * lo95:+.2f}, {100 * hi95:+.2f}]"
            f" | {per_seed} |"
        )
    for set_name in ("T", "S", "U-BIPIA", "U-NotInject", "U-WildGuard"):
        metrics = ("recall_at_1pct_fpr", "operational_recall", "operational_fpr")
        present = [m for m in metrics if lookup(report, set_name, "frozen", 0, m)]
        if not present:
            continue
        first = lookup(report, set_name, "frozen", 0, present[0])
        lines += [
            "",
            f"## {set_name} (n={first['n_rows']}, positives={first['n_positive']}, "
            f"groups={first['n_groups']})",
            "",
            "| Arm | B | " + " | ".join(present) + " |",
            "| --- | ---: |" + " --- |" * len(present),
        ]
        for budget in report["design"]["budgets"]:
            for arm in ARMS + ("generic_w20", "matched_w20", "matched_w20+threshold"):
                entries = [lookup(report, set_name, arm, budget, m) for m in present]
                if all(entries):
                    lines.append(
                        f"| {arm} | {budget} | " + " | ".join(cell(e) for e in entries) + " |"
                    )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
