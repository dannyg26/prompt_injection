"""POST-HOC exploratory diagnostics on the locked source-model scores.

Not preregistered. No model is fitted; only the frozen source model's locked scores are
read. The source model is deterministic, so no adaptation seed applies. Intervals are 95%
percentile group bootstraps (2,000 replicates, seed 20260925) conditioned on the model and
the deployed source threshold.
"""

import json
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

from injection_lab.adaptation import benign_threshold, group_weights, percentile_interval
from injection_lab.data import file_sha256, read_json_rows, write_json

POOLS = Path("data/processed/study/pools.jsonl")
SCORES = Path("artifacts/study/scores.npz")
RUN_LOG = Path("results/study/run_log.json")
OUT = Path("results/study/exploratory_diagnostics.json")
REPS = 2000


def main():
    if OUT.exists():
        raise ValueError("Refusing to overwrite exploratory diagnostics")
    log = json.loads(RUN_LOG.read_text(encoding="utf-8"))
    if file_sha256(SCORES) != log["scores_sha256"]:
        raise AssertionError("Scores differ from the locked run")
    rows = read_json_rows(POOLS)
    with np.load(SCORES) as data:
        score = data["source"]
    part = np.array([r["partition"] for r in rows])
    label = np.array([r["label"] for r in rows])
    source = np.array([r["source"] for r in rows])
    group = np.array([r["group"] for r in rows])
    tau = benign_threshold(score[(part == "S-cal") & (label == 0)])
    rng = np.random.default_rng(20260925)
    report = {
        "status": "POST-HOC EXPLORATORY; not preregistered",
        "threshold": tau,
        "auroc": [],
        "recall_by_source": [],
    }
    sets = {
        "T-eval": part == "T-eval",
        "S-test": part == "S-test",
        "U-BIPIA": (part == "U-eval") & (source == "BIPIA"),
    }
    for name, mask in sets.items():
        idx = np.nonzero(mask)[0]
        weights = group_weights(group[idx], REPS, rng)
        values = [roc_auc_score(label[idx], score[idx], sample_weight=w) for w in weights]
        report["auroc"].append(
            {
                "set": name,
                "estimate": roc_auc_score(label[idx], score[idx]),
                "ci95": percentile_interval(values, 0.95),
                "n": int(len(idx)),
                "groups": int(len(set(group[idx]))),
            }
        )
    for name in ("S-cal", "S-test"):
        for src in ("hackaprompt-dataset", "jailbreak-classification"):
            idx = np.nonzero((part == name) & (source == src) & (label == 1))[0]
            flagged = (score[idx] >= tau).astype(float)
            groups = len(set(group[idx]))
            entry = {
                "partition": name,
                "source": src,
                "positives": int(len(idx)),
                "groups": groups,
                "recall": float(flagged.mean()),
            }
            if groups > 1:
                w = group_weights(group[idx], REPS, rng)
                entry["ci95"] = percentile_interval((w * flagged).sum(1) / w.sum(1), 0.95)
            else:
                entry["ci95"] = None
                entry["note"] = "single template group: no sampling interval is possible"
            report["recall_by_source"].append(entry)
    write_json(OUT, report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
