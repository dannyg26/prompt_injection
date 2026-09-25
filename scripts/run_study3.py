"""Study 3 runner (Colab GPU): matched benign augmentation vs PIDS-Bench over-defense.

Stages: verify lock -> clone PIDS-Bench and restore its LMSYS test rows -> build pools
-> per arm and seed: PIDS-Bench's own training function (subprocess), our scoring,
delete model (resumable) -> analysis. Fixed by docs/PREREGISTRATION_STUDY3.md.

LMSYS-Chat-1M text never enters this git repository: every text-bearing path is checked
with assert_outside_repo, and only fingerprints, counts and scores are written publicly.

    python scripts/run_study3.py --out /content/drive/MyDrive/study3 [--pilot]
"""

import argparse
import csv
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from injection_lab.curation import components  # noqa: E402
from injection_lab.data import file_sha256, write_json  # noqa: E402
from injection_lab.pools import containment_edges  # noqa: E402
from injection_lab.study3 import (  # noqa: E402
    BOOTSTRAP_SEED,
    CONFIRMATORY,
    CONFIRMATORY_REPS,
    N_TRAIN,
    N_VAL,
    PRIMARY_ARMS,
    SECONDARY_ARMS,
    SEEDS,
    THRESHOLD,
    assert_outside_repo,
    f1_at,
    feasible_counts,
    fingerprint,
    joint_bootstrap_diff,
    percentile_interval,
    sample_pool,
    seed_t_interval,
    semantic_keep_mask,
    sweep_frontier,
    to_hardneg_frame_rows,
)

PIDS_URL = "https://github.com/ShirePyDev/Prompt-Injection-Detection-System"
PIDS_COMMIT = "87dc835"  # tag v1.0-pids-bench
LOCK = REPO / "results/study3/PREREG_LOCK.json"
APPROVAL = "PREREGISTRATION_STUDY3.md may be fit and scored"
DATA = Path("data/pids_bench_v3")
LMSYS_SKIP = 200_000  # PIDS-Bench scanned only LMSYS rows [0, 200000)
LMSYS_MAX_SCAN = 1_000_000
CAND_CAP = 3000  # candidates kept per cell before deduplication
MAX_UNRESTORED = 33  # at most ~5% of the 664 LMSYS test rows may stay unrestored
BATCH, ACCUM = 8, 2
EVAL_FILES = {
    "hard_benign": "eval_subsets/hard_benign_test.csv",
    "test": "test.csv",
    "obfuscated": "eval_subsets/obfuscated_attacks.csv",
    "domain_ood": "ood/domain_ood.csv",
    "structural_ood": "ood/structural_ood.csv",
}
# External hard-benign test composition (source|class row counts in their CSV)
MATCHED = {
    "lmsys|keyword": 298,
    "lmsys|random": 366,
    "oasst1|keyword": 40,
    "oasst1|random": 100,
    "dolly|keyword": 18,
    "dolly|random": 50,
}
SOURCE_ONLY = {"lmsys|none": 664, "oasst1|none": 140, "dolly|none": 68}
LMSYS_ONLY = {"lmsys|keyword": 298, "lmsys|random": 366}
FALLBACK = {
    "oasst1|keyword": "lmsys|keyword",
    "dolly|keyword": "lmsys|keyword",
    "oasst1|random": "lmsys|random",
    "dolly|random": "lmsys|random",
    "oasst1|none": "lmsys|none",
    "dolly|none": "lmsys|none",
}
POOL_ARMS = {
    "A2_matched": MATCHED,
    "A3_source_only": SOURCE_ONLY,
    "A2L_matched_lmsys_only": LMSYS_ONLY,
}

FIT_BASE = """
import sys; sys.path.insert(0, ".")
from src.baselines.deberta_v3 import run_train
run_train(num_epochs=3, batch_size={b}, lr=2e-5, seed={s},
          gradient_accumulation_steps={a}, out_dir="{o}")
"""
FIT_HARDNEG = """
import sys; sys.path.insert(0, ".")
from pathlib import Path
import src.baselines.deberta_v3_hardneg as m
paths = m._make_paths(Path(".").resolve(), out_dir=Path("{o}"))
m.confirm_hyperparams({b}, {a}, {s})
hn_tr, hn_va = m.verify_hard_negatives(paths)
m.dedup_safety_check(hn_tr, paths)
m.train_and_tune(paths, hn_tr=hn_tr, hn_va=hn_va, batch_size={b}, grad_accum={a}, seed={s})
"""


def log(msg):
    print(f"[study3 {datetime.now(UTC):%H:%M:%S}] {msg}", flush=True)


def git(*args, cwd=REPO):
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


def read_rows(path):
    with open(path, encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def verify():
    if APPROVAL not in (REPO / "AGENTS.md").read_text(encoding="utf-8"):
        raise PermissionError("Owner approval for Study 3 is not recorded in AGENTS.md")
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    for rel, digest in lock["sha256"].items():
        if file_sha256(REPO / rel) != digest:
            raise AssertionError(f"{rel} differs from the Study 3 lock")
    head = git("rev-parse", "HEAD")
    git("fetch", "-q", "origin")
    if not git("branch", "-r", "--contains", head):
        raise AssertionError("HEAD is not on the remote; run from a pushed commit")
    return head


def ensure_pids(pids_root, token):
    pids_root = assert_outside_repo(pids_root, REPO)
    if not pids_root.exists():
        subprocess.run(["git", "clone", "-q", PIDS_URL, str(pids_root)], check=True)
    git("checkout", "-q", PIDS_COMMIT, cwd=pids_root)
    hb = pids_root / DATA / EVAL_FILES["hard_benign"]
    if any(not r["text"].strip() for r in read_rows(hb)):
        log("restoring LMSYS test rows with PIDS-Bench's rebuild_restricted.py")
        subprocess.run(
            [sys.executable, "data_builder/rebuild_restricted.py", "--data-root", str(DATA)],
            cwd=pids_root,
            check=True,
            env=dict(os.environ, HF_TOKEN=token),
        )
    empty = sum(1 for r in read_rows(hb) if not r["text"].strip())
    if empty > MAX_UNRESTORED:
        raise RuntimeError(f"{empty} LMSYS test rows unrestored (> {MAX_UNRESTORED}); stop")
    return pids_root, empty


def load_pids_module(pids_root, rel, name):
    spec = importlib.util.spec_from_file_location(name, pids_root / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # required by their @dataclass
    sys.path.insert(0, str(pids_root))
    spec.loader.exec_module(module)
    return module


def build_pools(pids_root, private, token):
    """Candidate pools with PIDS-Bench's own selection code, disjoint from the benchmark."""
    done = private / "pools_done.json"
    if done.exists():
        return json.loads(done.read_text(encoding="utf-8"))
    from datasets import load_dataset

    hb = load_pids_module(pids_root, "data_builder/build_hard_benign.py", "pids_hard_benign")
    data = pids_root / DATA
    bench = [r["text"] for f in data.rglob("*.csv") for r in read_rows(f) if r.get("text")]
    bench_keys = {hb._normalize_text(t).lower() for t in bench}
    eval_texts = [
        r["text"] for f in EVAL_FILES.values() for r in read_rows(data / f) if r["text"].strip()
    ]
    cells = {k: [] for arm in POOL_ARMS.values() for k in arm}
    scanned = {"lmsys": 0, "oasst1": 0, "dolly": 0}
    excluded = hb.EXCLUDE_PATTERNS + hb.LOW_SIGNAL_PATTERNS + hb.FINAL_EXCLUDE_PATTERNS

    def add(source, raw, moderation):
        scanned[source] += 1
        text = hb._normalize_text(raw)
        if not (hb.MIN_LEN <= len(text) <= hb.MAX_LEN) or not hb._passes_moderation(moderation):
            return
        if hb._matches_any_pattern(text, excluded) or text.lower() in bench_keys:
            return
        key = f"{source}|{hb._classify_real_text(text, moderation) or 'none'}"
        if key in cells and len(cells[key]) < CAND_CAP:
            cells[key].append({"text": text, "source": source})

    lmsys_cells = [k for k in cells if k.startswith("lmsys")]
    stream = load_dataset("lmsys/lmsys-chat-1m", split="train", streaming=True, token=token)
    for i, row in enumerate(stream):
        if i < LMSYS_SKIP:
            continue
        if i >= LMSYS_MAX_SCAN or all(len(cells[k]) >= CAND_CAP for k in lmsys_cells):
            break
        if str(row.get("language", "")).strip().lower() != "english" or row.get("redacted"):
            continue
        first = next(
            (
                m.get("content", "")
                for m in row.get("conversation") or []
                if m.get("role") == "user"
            ),
            "",
        )
        add("lmsys", first, row.get("openai_moderation"))
    for split in ("train", "validation"):
        for row in load_dataset("OpenAssistant/oasst1", split=split):
            role, lang = str(row.get("role", "")).lower(), str(row.get("lang", "")).lower()
            if role == "prompter" and lang == "en":
                add("oasst1", row.get("text", ""), None)
    for row in load_dataset("databricks/databricks-dolly-15k", split="train"):
        add("dolly", row.get("instruction", ""), None)

    raw_counts, clean_counts = {}, {}
    for key, rows in cells.items():
        raw_counts[key] = len(rows)
        keep = semantic_keep_mask([r["text"] for r in rows], eval_texts)
        cells[key] = hb.semantic_dedup([r for r, k in zip(rows, keep) if k])
        clean_counts[key] = len(cells[key])
    manifest, allocation = [], {}
    for arm, weights in POOL_ARMS.items():
        counts, moved = feasible_counts(weights, clean_counts, N_TRAIN + N_VAL, FALLBACK)
        allocation[arm] = {"counts": counts, "moved_to_fallback": moved}
        train, val = sample_pool(cells, counts)
        for split, rows in (("train", train), ("val", val)):
            frame = to_hardneg_frame_rows(rows, arm, split)
            path = assert_outside_repo(private / f"{arm}_hard_negative_{split}.csv", REPO)
            with open(path, "w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(frame[0]))
                writer.writeheader()
                writer.writerows(frame)
            manifest += [
                {
                    "arm": arm,
                    "split": split,
                    "cell": r["cell"],
                    "text_sha256": fingerprint(r["text"]),
                }
                for r in rows
            ]
    result = {
        "scanned": scanned,
        "lmsys_rows_skipped": LMSYS_SKIP,
        "candidates_before_dedup": raw_counts,
        "candidates_after_dedup": clean_counts,
        "allocation": allocation,
        "manifest": manifest,
    }
    done.write_text(json.dumps(result), encoding="utf-8")
    return result


def arm_root(pids_root, arm, private, work):
    if arm in ("A0_none", "A1_curated"):
        return pids_root
    root = work / "arms" / arm
    if not root.exists():
        ignore = shutil.ignore_patterns(".git", "outputs", "models")
        shutil.copytree(pids_root, root, ignore=ignore)
        for split in ("train", "val"):
            shutil.copy(
                private / f"{arm}_hard_negative_{split}.csv",
                root / DATA / f"hard_negative_{split}.csv",
            )
    return root


def fit(arm, seed, root, fit_dir, log_path):
    template = FIT_BASE if arm == "A0_none" else FIT_HARDNEG
    code = template.format(b=BATCH, a=ACCUM, s=seed, o=fit_dir)
    with open(log_path, "w", encoding="utf-8") as handle:
        proc = subprocess.run(
            [sys.executable, "-c", code], cwd=root, stdout=handle, stderr=subprocess.STDOUT
        )
    if proc.returncode:
        raise RuntimeError(f"{arm} seed {seed} failed; see {log_path}")


def score(model_dir, root, arm, best_threshold):
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    tok = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForSequenceClassification.from_pretrained(model_dir)
    model = model.to(device).float().eval()

    def probs(texts):
        order = np.argsort([len(t) for t in texts], kind="stable")
        out = np.empty(len(texts))
        with torch.no_grad():
            for s in range(0, len(texts), 64):
                idx = order[s : s + 64]
                enc = tok(
                    [texts[i] for i in idx],
                    truncation=True,
                    max_length=512,
                    padding=True,
                    return_tensors="pt",
                ).to(device)
                logits = model(**enc).logits.double()
                out[idx] = torch.softmax(logits, -1)[:, 1].cpu().numpy()
        return out

    data = root / DATA
    scores = {
        name: probs([str(r["text"]) for r in read_rows(data / f)]) for name, f in EVAL_FILES.items()
    }
    val = read_rows(data / "val.csv")
    if arm != "A0_none":
        val += read_rows(data / "hard_negative_val.csv")
    val_probs = probs([str(r["text"]) for r in val])
    tau, _ = best_threshold(val_probs, np.array([int(r["label"]) for r in val]))
    model.to("cpu")
    if device.type == "cuda":
        torch.cuda.empty_cache()
    return scores, float(tau)


def run_one(arm, seed, pids_root, private, work, public, best_threshold):
    out = public / "scores" / f"{arm}_seed{seed}.npz"
    if out.exists():
        return None
    root = arm_root(pids_root, arm, private, work)
    fit_dir = work / "fits" / f"{arm}_seed{seed}"
    shutil.rmtree(fit_dir, ignore_errors=True)
    (public / "logs").mkdir(parents=True, exist_ok=True)
    start = time.time()
    fit(arm, seed, root, fit_dir, public / "logs" / f"{arm}_seed{seed}.log")
    seconds = time.time() - start
    scores, tau = score(fit_dir / "model", root, arm, best_threshold)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out, tau=tau, fit_seconds=seconds, **scores)
    shutil.rmtree(fit_dir)
    return seconds


def near_duplicate_groups(texts):
    groups = np.empty(len(texts), dtype=object)
    for g, members in enumerate(components(len(texts), containment_edges(texts))):
        for i in members:
            groups[i] = f"g{g}"
    return groups


def share(flags):
    """Mean of 0/1 flags; None (not NaN) for an empty subset so JSON stays valid."""
    flags = np.asarray(flags)
    return float(flags.mean()) if flags.size else None


def seed_row(seed, run, y, ext, lm, cur):
    hbs, tau = run["hard_benign"], float(run["tau"])
    return {
        "seed": seed,
        "tau_val": tau,
        "fit_seconds": float(run["fit_seconds"]),
        "ext_fpr_0.5": share(hbs[ext] >= THRESHOLD),
        "ext_fpr_tau_val": share(hbs[ext] >= tau),
        "ext_fpr_lmsys_0.5": share(hbs[ext & lm] >= THRESHOLD),
        "ext_fpr_oasst1_dolly_0.5": share(hbs[ext & ~lm] >= THRESHOLD),
        "curated_fpr_0.5": share(hbs[cur] >= THRESHOLD),
        "test_f1_0.5": f1_at(run["test"], y, THRESHOLD),
        "test_recall_0.5": share(run["test"][y == 1] >= THRESHOLD),
        "test_fpr_0.5": share(run["test"][y == 0] >= THRESHOLD),
        "obfuscated_recall_0.5": share(run["obfuscated"] >= THRESHOLD),
        "frontier_any_tau_f1_0.95_extfpr_0.10": sweep_frontier(run["test"], y, hbs[ext]),
    }


def analyze(pids_root, public, head, unrestored):
    data = pids_root / DATA
    hb = read_rows(data / EVAL_FILES["hard_benign"])
    y = np.array([int(r["label"]) for r in read_rows(data / EVAL_FILES["test"])])
    present = np.array([bool(r["text"].strip()) for r in hb])
    ext = np.array([r["source_type"] == "real" for r in hb]) & present
    cur = np.array([r["source_type"] == "curated" for r in hb])
    lm = np.array([r["source"].startswith("lmsys") for r in hb])
    groups = near_duplicate_groups([r["text"] for r in hb])[ext]
    arms = [
        a
        for a in PRIMARY_ARMS + SECONDARY_ARMS
        if all((public / "scores" / f"{a}_seed{s}.npz").exists() for s in SEEDS)
    ]
    runs = {a: [np.load(public / "scores" / f"{a}_seed{s}.npz") for s in SEEDS] for a in arms}
    flags = {
        a: np.array([r["hard_benign"][ext] >= THRESHOLD for r in runs[a]], float) for a in arms
    }
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    zero = np.zeros((len(SEEDS), int(ext.sum())))
    descriptive = {}
    for arm in arms:
        reps = joint_bootstrap_diff(flags[arm], zero, groups, 2000, rng)
        descriptive[arm] = {
            "ext_fpr_0.5_mean_over_seeds": float(flags[arm].mean()),
            "ext_fpr_0.5_ci95": percentile_interval(reps, 0.95),
            "per_seed": [seed_row(s, r, y, ext, lm, cur) for s, r in zip(SEEDS, runs[arm])],
        }
    confirmatory = []
    for a, b in CONFIRMATORY:
        if a in flags and b in flags:
            reps = joint_bootstrap_diff(flags[a], flags[b], groups, CONFIRMATORY_REPS, rng)
            ci = percentile_interval(reps, 0.975)
            confirmatory.append(
                {
                    "contrast": f"{a} - {b}",
                    "metric": "external hard-benign FPR at tau=0.5",
                    "estimate": float(flags[a].mean() - flags[b].mean()),
                    "ci97_5": ci,
                    "ci95": percentile_interval(reps, 0.95),
                    "per_seed_difference": (flags[a].mean(1) - flags[b].mean(1)).tolist(),
                    "sensitivity_seed_t_ci97_5": seed_t_interval(
                        flags[a].mean(1) - flags[b].mean(1), 0.975
                    ),
                    "established_reduction": bool(ci[1] < 0),
                    "established_increase": bool(ci[0] > 0),
                    "reduction_beyond_5_points": bool(ci[1] < -0.05),
                }
            )
    report = {
        "commit": head,
        "pids_commit": PIDS_COMMIT,
        "seeds": list(SEEDS),
        "arms": arms,
        "n_external": int(ext.sum()),
        "n_external_unrestored_excluded": int(unrestored),
        "n_external_groups": len(set(groups)),
        "confirmatory": confirmatory,
        "descriptive": descriptive,
        "interval_method": (
            "Percentile bootstrap. Each replicate resamples near-duplicate groups of external "
            "rows (word 5-gram containment >= 0.5, transitive) and, independently, the 5 "
            "seeds with replacement; paired contrasts use the same rows and seeds in both "
            f"arms. {CONFIRMATORY_REPS} replicates for contrasts, 2000 for single arms, "
            f"seed {BOOTSTRAP_SEED}. Assumes exchangeable groups and seeds as draws of "
            "training randomness; all seeds share the same data, so seeds are not "
            "independent test examples."
        ),
        "finished_utc": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    write_json(public / "study3_results.json", report)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help="Drive folder for resumable state")
    parser.add_argument("--pids-root", default="/content/pidsbench")
    parser.add_argument("--work", default="/content/study3_work")
    parser.add_argument("--pilot", action="store_true", help="one fit (A1, seed 13), then stop")
    args = parser.parse_args()
    token = os.environ.get("HF_TOKEN", "")
    if not token:
        raise SystemExit("Set HF_TOKEN from Colab Secrets (never paste it into a cell)")
    head = verify()
    out = assert_outside_repo(args.out, REPO)
    work = assert_outside_repo(args.work, REPO)
    private = out / "private_lmsys_text_do_not_share"
    public = out / "public"
    for d in (private, public, work):
        d.mkdir(parents=True, exist_ok=True)
    pids_root, unrestored = ensure_pids(Path(args.pids_root), token)
    log(f"PIDS-Bench ready; {unrestored} LMSYS test rows unrestored")
    pools = build_pools(pids_root, private, token)
    write_json(public / "pool_manifest.json", pools)  # fingerprints and counts only
    log(f"pool allocation: {json.dumps(pools['allocation'])}")
    best_threshold = load_pids_module(
        pids_root, "src/baselines/deberta_v3_hardneg.py", "pids_hardneg"
    ).best_threshold
    plan = [(a, s) for s in SEEDS for a in PRIMARY_ARMS]
    plan += [(a, s) for s in SEEDS for a in SECONDARY_ARMS]
    if args.pilot:
        plan = [("A1_curated", SEEDS[0])]
    for arm, seed in plan:
        seconds = run_one(arm, seed, pids_root, private, work, public, best_threshold)
        if seconds is not None:
            log(f"{arm} seed {seed}: {seconds / 60:.1f} min")
    if args.pilot:
        log("pilot complete")
        return
    report = analyze(pids_root, public, head, unrestored)
    print(json.dumps(report["confirmatory"], indent=1))


if __name__ == "__main__":
    main()
