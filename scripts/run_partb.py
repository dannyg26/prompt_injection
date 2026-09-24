"""Study 2 Part B runner (Colab GPU). Gated, locked, resumable.

Usage (see notebooks/study2_partb_colab.ipynb):
    python scripts/run_partb.py --out /content/drive/MyDrive/injection_lab_partb
Environment: HF_TOKEN (optional; needed only for the gated Prompt Guard 2 model).
"""

import argparse
import json
import os
import platform
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from injection_lab.data import file_sha256, read_json_rows, write_json, write_jsonl
from injection_lab.partb import analyze, run_all
from injection_lab.pools import INJECGUARD_REVISION, rows_from_manifest
from injection_lab.transformer import (
    FINETUNE_MODEL,
    RECIPE,
    RELEASED_DETECTORS,
    finetune,
    load_released,
    resolve_revision,
    score,
)

LOCK = Path("results/leakage/PARTB_LOCK.json")
LEDGER = Path("results/study/pool_ledger.json")
POOLS = Path("data/processed/study/pools.jsonl")
CLONE = Path("data/raw/injecguard")
MANIFEST = Path("results/study/pool_manifest.csv.gz")
APPROVAL = "Part B in docs/PREREGISTRATION_LEAKAGE.md may be fit and scored"


def git(*args, cwd="."):
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    ).stdout.strip()


def verify():
    if APPROVAL not in Path("AGENTS.md").read_text(encoding="utf-8"):
        raise PermissionError("Owner approval amendment for Part B is not recorded in AGENTS.md")
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    for path, digest in lock["sha256"].items():
        if file_sha256(path) != digest:
            raise AssertionError(f"{path} differs from the Part B lock")
    head = git("rev-parse", "HEAD")
    if not git("branch", "-r", "--contains", head):
        raise AssertionError("Run from a commit that exists on the remote")
    if git("status", "--porcelain", "--", *lock["sha256"]):
        raise AssertionError("Locked files have local modifications")
    return head


def ensure_pools():
    expected = json.loads(LEDGER.read_text(encoding="utf-8"))["pools_sha256"]
    if not POOLS.exists():
        if not CLONE.exists():
            subprocess.run(
                ["git", "clone", "-q", "https://github.com/InjecGuard/InjecGuard", str(CLONE)],
                check=True,
            )
        git("checkout", "-q", INJECGUARD_REVISION, cwd=CLONE)
        write_jsonl(POOLS, rows_from_manifest(CLONE, MANIFEST))
    if file_sha256(POOLS) != expected:
        raise AssertionError("Rebuilt pools differ from the frozen Study 1 pools")
    return read_json_rows(POOLS)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help="Persistent directory (e.g. Google Drive)")
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    head = verify()
    rows = ensure_pools()
    token = os.environ.get("HF_TOKEN") or None
    revisions_path = out / "revisions.json"
    if revisions_path.exists():
        revisions = json.loads(revisions_path.read_text(encoding="utf-8"))
    else:
        # Pinned once, before any fitting or scoring; reused on every resume.
        revisions = {FINETUNE_MODEL: resolve_revision(FINETUNE_MODEL, token)}
        for repo, _, gated in RELEASED_DETECTORS:
            try:
                revisions[repo] = resolve_revision(repo, token)
            except Exception as exc:  # gated without access: recorded, not silently dropped
                revisions[repo] = None
                print(f"{repo}: unavailable ({type(exc).__name__}); gated={gated}")
        write_json(revisions_path, revisions)
    released = {
        repo.split("/")[1]: (repo, label)
        for repo, label, _ in RELEASED_DETECTORS
        if revisions[repo]
    }

    def deberta(train_rows, seed):
        return finetune(train_rows, seed, FINETUNE_MODEL, revisions[FINETUNE_MODEL])

    def released_scorer(name, texts):
        repo, label = released[name]
        model, tokenizer, index = load_released(repo, label, revisions[repo], token)
        return score(model, tokenizer, texts, positive_index=index, max_length=512)

    results = run_all(rows, out, deberta, released_scorer, list(released))
    report = analyze(rows, results, list(released))
    import torch

    report["run"] = {
        "commit": head,
        "finished_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "revisions": revisions,
        "recipe": RECIPE,
        "python": platform.python_version(),
        "torch": torch.__version__,
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    }
    write_json(out / "partb_results.json", report)
    print(json.dumps(report["inflation"], indent=1))


if __name__ == "__main__":
    main()
