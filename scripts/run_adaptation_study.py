"""Fit every prespecified model once and score allowed rows. Refuses to run unlocked."""

import json
import os
import platform
import subprocess
import time
from pathlib import Path

import numpy as np
from joblib import Parallel, delayed

from injection_lab.adaptation import ADDED_WEIGHTS, BUDGETS, SEEDS, fit_detector, nested_subsets
from injection_lab.data import file_sha256, read_json_rows, write_json

LOCK = Path("results/study/PREREG_LOCK.json")
POOLS = Path("data/processed/study/pools.jsonl")
SCORES = Path("artifacts/study/scores.npz")
RUN_LOG = Path("results/study/run_log.json")
SCORED = ("S-cal", "S-test", "T-bank", "T-eval", "U-eval")


def verify_lock():
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    for path, digest in lock["sha256"].items():
        if file_sha256(path) != digest:
            raise AssertionError(f"{path} differs from the preregistered lock")
    status = subprocess.run(
        ["git", "status", "--porcelain", "--", *lock["sha256"]],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    if status.strip():
        raise AssertionError("Locked files have uncommitted changes")
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    pushed = subprocess.run(
        ["git", "branch", "-r", "--contains", head], capture_output=True, text=True, check=True
    ).stdout.strip()
    if not pushed:
        raise AssertionError("Preregistration commit must be pushed before scoring")
    return lock, head


def model_plan(rows):
    train = [r for r in rows if r["partition"] == "S-train"]
    generic_bank = [r for r in rows if r["partition"] == "S-generic-bank" and r["label"] == 0]
    target_bank = [r for r in rows if r["partition"] == "T-bank" and r["label"] == 0]
    plan = [("source", train, [], 1.0)]
    for seed in SEEDS:
        generic = nested_subsets(generic_bank, seed)
        target = nested_subsets(target_bank, seed)
        for budget in BUDGETS[1:]:
            for weight in ADDED_WEIGHTS:
                suffix = "" if weight == 1.0 else f"_w{int(weight)}"
                plan.append((f"generic{suffix}:{seed}:{budget}", train, generic[budget], weight))
                plan.append((f"matched{suffix}:{seed}:{budget}", train, target[budget], weight))
    return plan


def fit_and_score(key, train, added, weight, texts):
    start = time.perf_counter()
    model = fit_detector(train, added, weight)
    fitted = time.perf_counter() - start
    scores = model.predict_proba(texts)[:, 1]
    return (
        key,
        scores,
        {
            "fit_seconds": fitted,
            "total_seconds": time.perf_counter() - start,
            "added_rows": len(added),
            "added_weight": weight,
        },
    )


def main():
    if SCORES.exists() or RUN_LOG.exists():
        raise ValueError("Refusing to overwrite the single locked run")
    lock, head = verify_lock()
    rows = read_json_rows(POOLS)
    scored = [i for i, r in enumerate(rows) if r["partition"] in SCORED]
    texts = [rows[i]["text"] for i in scored]
    plan = model_plan(rows)
    started = time.time()
    results = Parallel(n_jobs=int(os.environ.get("STUDY_JOBS", "4")), verbose=5)(
        delayed(fit_and_score)(key, train, added, weight, texts)
        for key, train, added, weight in plan
    )
    arrays, timing = {}, {}
    for key, scores, info in results:
        full = np.full(len(rows), np.nan)
        full[scored] = scores
        arrays[key] = full
        timing[key] = info
    SCORES.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(SCORES, **{k.replace(":", "__"): v for k, v in arrays.items()})
    write_json(
        RUN_LOG,
        {
            "preregistration_commit": head,
            "lock": lock["sha256"],
            "models": len(arrays),
            "wall_seconds": time.time() - started,
            "scores_sha256": file_sha256(SCORES),
            "python": platform.python_version(),
            "machine": {"cpus": os.cpu_count(), "platform": platform.platform(), "gpu": None},
            "timing": timing,
        },
    )
    print(f"Scored {len(arrays)} models in {time.time() - started:.0f}s")


if __name__ == "__main__":
    main()
