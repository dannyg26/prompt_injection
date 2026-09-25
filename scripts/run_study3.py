"""Study 3 runner (Colab GPU): matched benign augmentation vs PIDS-Bench over-defense.

Stages (each resumable, all state on Drive):
  pools   verify lock -> clone PIDS-Bench, restore its LMSYS test rows -> build pools,
          disjointness filters, composition report, blind audit export. No model.
  fits    per seed, per arm: PIDS-Bench's own training function in a subprocess, our
          scoring, delete the model. Only fit times are displayed.
  analyze confirmatory and secondary analyses -> public/study3_results.json.
Fixed by docs/PREREGISTRATION_STUDY3.md.

LMSYS-Chat-1M text never enters this git repository: every text-bearing path is checked
with assert_outside_repo, and only fingerprints, counts and scores are written publicly.

    python scripts/run_study3.py --out /content/drive/MyDrive/study3 --stage pools|pilot|all
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
    CONFIRMATORY,
    CONFIRMATORY_REPS,
    N_TRAIN,
    N_VAL,
    POOL_SEED,
    PRIMARY_ARMS,
    SECONDARY_ARMS,
    SEEDS,
    THRESHOLD,
    assert_outside_repo,
    cross_containment_hits,
    decide,
    f1_at,
    feasible_counts,
    fingerprint,
    joint_bootstrap_diff,
    named_rng,
    percentile_interval,
    sample_pool,
    seed_t_interval,
    semantic_keep_mask,
    sweep_frontier,
    to_hardneg_frame_rows,
)

PIDS_URL = "https://github.com/ShirePyDev/Prompt-Injection-Detection-System"
PIDS_COMMIT = "87dc835566b930ee921240874a4939b2c266c2fe"  # tag v1.0-pids-bench
LOCK = REPO / "results/study3/PREREG_LOCK.json"
APPROVAL = "PREREGISTRATION_STUDY3.md may be fit and scored"
VERSIONS = {"transformers": "4.57.1", "datasets": "4.4.1"}  # PIDS-Bench requirements.txt
HF_REPOS = {
    "lmsys": ("lmsys/lmsys-chat-1m", "dataset"),
    "oasst1": ("OpenAssistant/oasst1", "dataset"),
    "dolly": ("databricks/databricks-dolly-15k", "dataset"),
    "deberta": ("microsoft/deberta-v3-base", "model"),
}
DATA = Path("data/pids_bench_v3")
LMSYS_SKIP = 200_000  # PIDS-Bench scanned only LMSYS rows [0, 200000)
LMSYS_MAX_SCAN = 1_000_000
CAND_CAP = 5000  # candidates kept per cell (first in stream order) before filtering
MAX_UNRESTORED = 33  # at most ~5% of the 664 LMSYS test rows may stay unrestored
AUDIT_N = 200
BATCH, ACCUM = 8, 2
SECONDARY_REPS = 2000
TC_PHRASE = "you are the text completion model"
EVAL_FILES = {
    "hard_benign": "eval_subsets/hard_benign_test.csv",
    "test": "test.csv",
    "obfuscated": "eval_subsets/obfuscated_attacks.csv",
    "domain_ood": "ood/domain_ood.csv",
    "structural_ood": "ood/structural_ood.csv",
}
# External hard-benign test composition: source|class row counts in their CSV
# (their source names: lmsys = keyword class, lmsys_ai_adjacent = random class, etc.)
MATCHED = {
    "lmsys|keyword": 298,
    "lmsys|random": 366,
    "oasst1|keyword": 40,
    "oasst1|random": 100,
    "dolly|keyword": 18,
    "dolly|random": 50,
}
SOURCE_ONLY = {"lmsys|any": 664, "oasst1|any": 140, "dolly|any": 68}
LMSYS_ONLY = {"lmsys|keyword": 298, "lmsys|random": 366}
FALLBACK = {  # only OASST1/Dolly cells may fall back; a short LMSYS cell stops the study
    "oasst1|keyword": "lmsys|keyword",
    "dolly|keyword": "lmsys|keyword",
    "oasst1|random": "lmsys|random",
    "dolly|random": "lmsys|random",
    "oasst1|any": "lmsys|any",
    "dolly|any": "lmsys|any",
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
    if git("status", "--porcelain", "--untracked-files=no"):
        raise AssertionError("Tracked files are modified; run from a clean pushed commit")
    head = git("rev-parse", "HEAD")
    git("fetch", "-q", "origin")
    if not git("branch", "-r", "--contains", head):
        raise AssertionError("HEAD is not on the remote; run from a pushed commit")
    import datasets
    import transformers

    found = {"transformers": transformers.__version__, "datasets": datasets.__version__}
    if found != VERSIONS:
        raise AssertionError(f"Versions {found} differ from preregistered {VERSIONS}")
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
            stdout=subprocess.DEVNULL,
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


def hf_revisions(token):
    from huggingface_hub import HfApi

    api = HfApi(token=token)
    out = {}
    for key, (repo, kind) in HF_REPOS.items():
        info = api.dataset_info(repo) if kind == "dataset" else api.model_info(repo)
        out[key] = {"repo": repo, "sha": info.sha}
    return out


def profile(texts, hb):
    """Composition summary (no text) used to compare pools with the external test rows."""
    lengths = np.array([len(t) for t in texts]) if texts else np.zeros(0)
    if not len(lengths):
        return {"n": 0}
    return {
        "n": len(texts),
        "median_chars": float(np.median(lengths)),
        "iqr_chars": [float(np.percentile(lengths, 25)), float(np.percentile(lengths, 75))],
        "share_text_completion_template": float(np.mean([TC_PHRASE in t.lower() for t in texts])),
        "share_injection_keyword": float(
            np.mean([hb._contains_injection_keyword(t) for t in texts])
        ),
        "share_context_term": float(np.mean([hb._contains_hard_benign_context(t) for t in texts])),
    }


def build_pools(pids_root, private, public, token):
    """Candidate pools with PIDS-Bench's own selection code, disjoint from the benchmark."""
    done = private / "pools_done.json"
    if done.exists():
        return json.loads(done.read_text(encoding="utf-8"))
    from datasets import load_dataset

    revisions = hf_revisions(token)
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
        row = {"text": text, "source": source}
        cls = hb._classify_real_text(text, moderation)
        for key in (f"{source}|{cls}", f"{source}|any"):  # 'any' = all filtered rows
            if key in cells and len(cells[key]) < CAND_CAP:
                cells[key].append(row)

    lmsys_cells = [k for k in cells if k.startswith("lmsys")]
    stream = load_dataset(
        HF_REPOS["lmsys"][0],
        split="train",
        streaming=True,
        token=token,
        revision=revisions["lmsys"]["sha"],
    )
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
        oasst = load_dataset(
            HF_REPOS["oasst1"][0], split=split, revision=revisions["oasst1"]["sha"]
        )
        for row in oasst:
            role, lang = str(row.get("role", "")).lower(), str(row.get("lang", "")).lower()
            if role == "prompter" and lang == "en":
                add("oasst1", row.get("text", ""), None)
    dolly = load_dataset(HF_REPOS["dolly"][0], split="train", revision=revisions["dolly"]["sha"])
    for row in dolly:
        add("dolly", row.get("instruction", ""), None)

    steps = {}
    for key, rows in cells.items():
        texts = [r["text"] for r in rows]
        hits = cross_containment_hits(texts, eval_texts)
        rows = [r for i, r in enumerate(rows) if i not in hits]
        keep = semantic_keep_mask([r["text"] for r in rows], eval_texts)
        after_semantic = [r for r, k in zip(rows, keep) if k]
        cells[key] = hb.semantic_dedup(after_semantic)
        steps[key] = {
            "candidates": len(texts),
            "removed_containment_vs_eval": len(hits),
            "removed_char_tfidf_vs_eval": len(rows) - len(after_semantic),
            "removed_within_cell": len(after_semantic) - len(cells[key]),
            "available": len(cells[key]),
        }
    available = {k: v["available"] for k, v in steps.items()}
    hb_rows = read_rows(data / EVAL_FILES["hard_benign"])
    ext_texts = [r["text"] for r in hb_rows if r["source_type"] == "real" and r["text"].strip()]
    manifest, allocation, composition = [], {}, {"external_test": profile(ext_texts, hb)}
    audit_pool = []
    for arm, weights in POOL_ARMS.items():
        counts, moved = feasible_counts(weights, available, N_TRAIN + N_VAL, FALLBACK)
        allocation[arm] = {"counts": counts, "moved_to_fallback": moved}
        train, val = sample_pool(cells, counts)
        composition[arm] = profile([r["text"] for r in train + val], hb)
        if arm == "A2_matched":
            audit_pool = train + val
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
    rng = np.random.default_rng(POOL_SEED + 1)
    audit = [audit_pool[i] for i in rng.permutation(len(audit_pool))[:AUDIT_N]]
    audit_path = assert_outside_repo(private / "audit_A2_blind.csv", REPO)
    with open(audit_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["audit_id", "text", "is_benign (1/0)", "notes"])
        for i, r in enumerate(audit):
            writer.writerow([f"a{i:03d}", r["text"], "", ""])
    result = {
        "scanned": scanned,
        "lmsys_rows_skipped": LMSYS_SKIP,
        "hf_revisions": revisions,
        "filter_steps": steps,
        "allocation": allocation,
        "composition": composition,
        "audit_ids": [
            {"audit_id": f"a{i:03d}", "text_sha256": fingerprint(r["text"])}
            for i, r in enumerate(audit)
        ],
        "manifest": manifest,
    }
    done.write_text(json.dumps(result), encoding="utf-8")
    write_json(public / "pool_manifest.json", result)  # fingerprints and counts only
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
    """PIDS-Bench's training in a subprocess. Its console output contains evaluation
    metrics (A0), so the log goes to the private folder and is never displayed."""
    template = FIT_BASE if arm == "A0_none" else FIT_HARDNEG
    code = template.format(b=BATCH, a=ACCUM, s=seed, o=fit_dir)
    with open(log_path, "a", encoding="utf-8") as handle:
        handle.write(f"\n=== attempt {datetime.now(UTC).isoformat()} ===\n")
        handle.flush()
        proc = subprocess.run(
            [sys.executable, "-c", code], cwd=root, stdout=handle, stderr=subprocess.STDOUT
        )
    return proc.returncode == 0


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
    """One fit + score. Preregistered failure rule: one identical retry, then the arm is
    marked failed (hence incomplete). Returns minutes, 'failed', or None if already done."""
    out = public / "scores" / f"{arm}_seed{seed}.npz"
    failed = public / "scores" / f"{arm}_seed{seed}.failed"
    if out.exists() or failed.exists():
        return None
    root = arm_root(pids_root, arm, private, work)
    fit_dir = work / "fits" / f"{arm}_seed{seed}"
    (private / "logs").mkdir(parents=True, exist_ok=True)
    log_path = private / "logs" / f"{arm}_seed{seed}.log"
    for attempt in (1, 2):
        shutil.rmtree(fit_dir, ignore_errors=True)
        start = time.time()
        if fit(arm, seed, root, fit_dir, log_path):
            seconds = time.time() - start
            scores, tau = score(fit_dir / "model", root, arm, best_threshold)
            out.parent.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(out, tau=tau, fit_seconds=seconds, attempts=attempt, **scores)
            shutil.rmtree(fit_dir)
            return seconds / 60
        log(f"{arm} seed {seed}: attempt {attempt} failed")
    failed.parent.mkdir(parents=True, exist_ok=True)
    failed.write_text("failed twice with identical settings\n", encoding="utf-8")
    shutil.rmtree(fit_dir, ignore_errors=True)
    return "failed"


def near_duplicate_groups(texts, prefix):
    groups = np.empty(len(texts), dtype=object)
    for g, members in enumerate(components(len(texts), containment_edges(texts))):
        for i in members:
            groups[i] = f"{prefix}{g}"
    return groups


def rate_interval(flag_matrix, groups, name):
    """Seed-mean rate with a 95% joint group+seed percentile bootstrap interval."""
    if flag_matrix.shape[1] == 0:
        return {"n_rows": 0, "estimate": None, "ci95": None}
    zero = np.zeros_like(flag_matrix)
    reps = joint_bootstrap_diff(flag_matrix, zero, groups, SECONDARY_REPS, named_rng(name))
    return {
        "n_rows": int(flag_matrix.shape[1]),
        "estimate": float(flag_matrix.mean()),
        "ci95": percentile_interval(reps, 0.95),
    }


def contrast(fa, fb, groups, name, reps, level):
    if fa.shape[1] == 0:
        return {"n_rows": 0, "estimate": None}
    boot = joint_bootstrap_diff(fa, fb, groups, reps, named_rng(name))
    per_seed = fa.mean(1) - fb.mean(1)
    return {
        "n_rows": int(fa.shape[1]),
        "estimate": float(fa.mean() - fb.mean()),
        "per_seed_difference": per_seed.tolist(),
        f"bootstrap_ci{int(level * 1000) / 10:g}": percentile_interval(boot, level),
        f"seed_t_ci{int(level * 1000) / 10:g}": seed_t_interval(per_seed, level),
    }


def analyze(pids_root, public, head, unrestored):
    hbmod = load_pids_module(pids_root, "data_builder/build_hard_benign.py", "pids_hb_terms")
    data = pids_root / DATA
    hb = read_rows(data / EVAL_FILES["hard_benign"])
    test = read_rows(data / EVAL_FILES["test"])
    obf = read_rows(data / EVAL_FILES["obfuscated"])
    y = np.array([int(r["label"]) for r in test])
    present = np.array([bool(r["text"].strip()) for r in hb])
    ext = np.array([r["source_type"] == "real" for r in hb]) & present
    cur = np.array([r["source_type"] == "curated" for r in hb])
    lm = np.array([r["source"].startswith("lmsys") for r in hb])
    ctx_test = np.array([hbmod._contains_hard_benign_context(r["text"]) for r in test])
    ctx_obf = np.array([hbmod._contains_hard_benign_context(r["text"]) for r in obf])
    groups = {
        "ext": near_duplicate_groups([r["text"] for r in np.array(hb)[ext]], "e"),
        "cur": near_duplicate_groups([r["text"] for r in np.array(hb)[cur]], "c"),
        "test": np.array([r["parent_seed_id"] or f"t{i}" for i, r in enumerate(test)]),
        "obf": np.array([r["parent_seed_id"] or f"o{i}" for i, r in enumerate(obf)]),
    }
    all_arms = PRIMARY_ARMS + SECONDARY_ARMS
    arms = [
        a for a in all_arms if all((public / "scores" / f"{a}_seed{s}.npz").exists() for s in SEEDS)
    ]
    complete = all(a in arms for a in PRIMARY_ARMS)
    runs = {a: [np.load(public / "scores" / f"{a}_seed{s}.npz") for s in SEEDS] for a in arms}

    def flags(arm, split, mask, tau=None):
        return np.array(
            [(r[split][mask] >= (float(r["tau"]) if tau else THRESHOLD)) for r in runs[arm]],
            float,
        )

    def sub(mask_within_ext):
        return mask_within_ext[ext]

    lm_e = sub(lm)
    endpoints = {
        "ext_fpr_0.5": ("hard_benign", ext, "ext", False, None),
        "ext_fpr_tau_val": ("hard_benign", ext, "ext", True, None),
        "ext_fpr_lmsys_0.5": ("hard_benign", ext & lm, "ext", False, lm_e),
        "ext_fpr_oasst1_dolly_0.5": ("hard_benign", ext & ~lm, "ext", False, ~lm_e),
        "curated_fpr_0.5": ("hard_benign", cur, "cur", False, None),
        "test_recall_0.5": ("test", y == 1, "test", False, None),
        "test_fpr_0.5": ("test", y == 0, "test", False, None),
        "context_term_attack_recall_0.5": ("test", (y == 1) & ctx_test, "test", False, None),
        "obfuscated_recall_0.5": ("obfuscated", np.ones(len(obf), bool), "obf", False, None),
        "context_term_obfuscated_recall_0.5": ("obfuscated", ctx_obf, "obf", False, None),
    }

    def endpoint_flags(arm, key):
        split, mask, gkey, use_tau, _ = endpoints[key]
        return flags(arm, split, mask, use_tau)

    def endpoint_groups(key):
        split, mask, gkey, _, within_ext = endpoints[key]
        if gkey == "ext":
            return groups["ext"] if within_ext is None else groups["ext"][within_ext]
        if gkey == "test":
            return groups["test"][mask]
        if gkey == "obf":
            return groups["obf"][mask]
        return groups["cur"]

    descriptive = {}
    for arm in arms:
        f1s = np.array([f1_at(r["test"], y, THRESHOLD) for r in runs[arm]])
        descriptive[arm] = {
            key: rate_interval(endpoint_flags(arm, key), endpoint_groups(key), f"{arm}:{key}")
            for key in endpoints
        }
        descriptive[arm]["test_f1_0.5"] = {
            "estimate": float(f1s.mean()),
            "ci95_seed_t": seed_t_interval(f1s, 0.95),
        }
        descriptive[arm]["per_seed"] = [
            {
                "seed": s,
                "tau_val": float(r["tau"]),
                "fit_minutes": float(r["fit_seconds"]) / 60,
                "attempts": int(r["attempts"]),
                "oracle_frontier_any_tau_f1_0.95_extfpr_0.10": sweep_frontier(
                    r["test"], y, r["hard_benign"][ext]
                ),
            }
            for s, r in zip(SEEDS, runs[arm])
        ]

    confirmatory = []
    for a, b in CONFIRMATORY:
        name = f"{a} - {b}"
        if a in arms and b in arms:
            c = contrast(
                endpoint_flags(a, "ext_fpr_0.5"),
                endpoint_flags(b, "ext_fpr_0.5"),
                groups["ext"],
                name,
                CONFIRMATORY_REPS,
                0.975,
            )
            c.update(decide(c["bootstrap_ci97.5"], c["seed_t_ci97.5"], complete))
        else:
            c = decide(None, None, False)
        confirmatory.append({"contrast": name, "metric": "ext_fpr_0.5", **c})

    secondary_specs = [
        ("A2_matched", "A3_source_only", "ext_fpr_0.5"),
        ("A2L_matched_lmsys_only", "A2_matched", "ext_fpr_0.5"),
        ("A2L_matched_lmsys_only", "A1_curated", "ext_fpr_oasst1_dolly_0.5"),
        ("A2L_matched_lmsys_only", "A1_curated", "ext_fpr_lmsys_0.5"),
        ("A2_matched", "A1_curated", "ext_fpr_tau_val"),
        ("A2_matched", "A1_curated", "curated_fpr_0.5"),
        ("A2_matched", "A1_curated", "test_recall_0.5"),
        ("A2_matched", "A1_curated", "context_term_attack_recall_0.5"),
        ("A2_matched", "A1_curated", "obfuscated_recall_0.5"),
        ("A2_matched", "A1_curated", "context_term_obfuscated_recall_0.5"),
    ]
    secondary = []
    for a, b, key in secondary_specs:
        if a in arms and b in arms:
            name = f"{a} - {b} [{key}]"
            fa, fb = endpoint_flags(a, key), endpoint_flags(b, key)
            secondary.append(
                {
                    "contrast": name,
                    **contrast(fa, fb, endpoint_groups(key), name, SECONDARY_REPS, 0.95),
                }
            )
    report = {
        "status": "complete" if complete else "incomplete",
        "commit": head,
        "pids_commit": PIDS_COMMIT,
        "seeds": list(SEEDS),
        "arms_complete": arms,
        "arms_failed_or_missing": [a for a in all_arms if a not in arms],
        "n_external": int(ext.sum()),
        "n_external_unrestored_excluded": int(unrestored),
        "n_external_groups": len(set(groups["ext"])),
        "confirmatory": confirmatory,
        "secondary_contrasts": secondary,
        "descriptive": descriptive,
        "interval_method": (
            "Rates: percentile bootstrap resampling near-duplicate groups (external and curated "
            "hard-benign rows: word 5-gram containment >= 0.5, transitive, computed within each "
            "set; test and obfuscated rows: parent_seed_id) and, independently, the 5 seeds "
            "with replacement; contrasts pair the same rows and seed indices. Confirmatory: "
            f"{CONFIRMATORY_REPS} replicates at 97.5% (Bonferroni over 2) plus a Student-t "
            "(df 4) interval over the 5 per-seed differences; both must exclude 0. Secondary: "
            f"{SECONDARY_REPS} replicates, 95%. F1: Student-t over seeds. Each analysis uses "
            "its own RNG stream (named_rng). All seeds share one dataset, so seeds are not "
            "independent test examples; a 5-seed bootstrap understates seed variance, which "
            "is why the t-interval is also required."
        ),
        "finished_utc": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    write_json(public / "study3_results.json", report)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help="Drive folder for resumable state")
    parser.add_argument("--stage", choices=("pools", "pilot", "all"), required=True)
    parser.add_argument("--pids-root", default="/content/pidsbench")
    parser.add_argument("--work", default="/content/study3_work")
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
    pools = build_pools(pids_root, private, public, token)
    log(f"pool allocation: {json.dumps(pools['allocation'])}")
    if args.stage == "pools":
        log("pools stage complete; see public/pool_manifest.json (no model trained)")
        return
    best_threshold = load_pids_module(
        pids_root, "src/baselines/deberta_v3_hardneg.py", "pids_hardneg"
    ).best_threshold
    plan = [(a, s) for s in SEEDS for a in PRIMARY_ARMS]
    plan += [(a, s) for s in SEEDS for a in SECONDARY_ARMS]
    if args.stage == "pilot":
        plan = [("A1_curated", SEEDS[0])]
    for arm, seed in plan:
        result = run_one(arm, seed, pids_root, private, work, public, best_threshold)
        if result == "failed":
            log(f"{arm} seed {seed}: FAILED twice; arm marked incomplete")
        elif result is not None:
            log(f"{arm} seed {seed}: fit took {result:.1f} min")
    if args.stage == "pilot":
        log("pilot complete")
        return
    report = analyze(pids_root, public, head, unrestored)
    log(f"analysis written: status {report['status']}")


if __name__ == "__main__":
    main()
