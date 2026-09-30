"""Study 4 runner (Colab GPU): detector-mined and combined benign augmentation.

Stages (each resumable, all state on Drive):
  pools   verify lock -> PIDS-Bench with restored LMSYS test rows -> mine same-corpus rows
          that a released detector (ProtectAI v2, pinned) flags, generic hygiene filter, no
          PIDS-Bench selection rules or test composition -> disjointness and label-conflict
          filters -> B1/B3 pools; A2/A3 pools copied from Study 3; framed attack and framed
          benign sets; composition report; blind audit export. No detector is trained.
  fits    per seed, per arm: PIDS-Bench's own training function in a subprocess (reused
          from run_study3), our scoring, delete the model. Scores stay in the private folder
          until the analysis stage; only fit times are displayed.
  analyze confirmatory and secondary analyses -> public/study4_results.json.
Fixed by docs/PREREGISTRATION_STUDY4.md. LMSYS text never enters this git repository.

    python scripts/run_study4.py --out /content/drive/MyDrive/study4 \
        --study3-out /content/drive/MyDrive/study3 --stage pools|pilot|all
"""

import argparse
import csv
import json
import os
import shutil
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

import run_study3 as s3  # noqa: E402  (locked Study 3 helpers, imported unmodified)

from injection_lab.data import file_sha256, write_json  # noqa: E402
from injection_lab.study3 import (  # noqa: E402
    THRESHOLD,
    assert_outside_repo,
    cross_containment_hits,
    decide,
    f1_at,
    fingerprint,
    joint_bootstrap_diff,
    named_rng,
    percentile_interval,
    seed_t_interval,
    semantic_keep_mask,
    to_hardneg_frame_rows,
)
from injection_lab.study4 import (  # noqa: E402
    ARMS,
    CONFIRMATORY,
    CONFIRMATORY_LEVEL,
    CONFIRMATORY_REPS,
    FRAMING_PREFIXES,
    LMSYS_MAX_INDEX,
    LMSYS_START,
    LMSYS_STEP,
    MINING_DETECTOR,
    MINING_THRESHOLD,
    N_TRAIN,
    N_VAL,
    NONINFERIORITY_MARGIN,
    POOL_SEED,
    SEEDS,
    framed,
    generic_filter,
    index_blocks,
    mix_pools,
    moderation_flagged,
    noninferior,
    recipe_success,
    split_train_val,
    uniform_draw,
)

LOCK = REPO / "results/study4/PREREG_LOCK.json"
APPROVAL = "PREREGISTRATION_STUDY4.md may be fit and scored"
AUDIT_N = 200
SECONDARY_REPS = 2000
DATA = s3.DATA
STUDY3_POOLS = ("A2_matched", "A3_source_only")


def verify():
    if APPROVAL not in (REPO / "AGENTS.md").read_text(encoding="utf-8"):
        raise PermissionError("Owner approval for Study 4 is not recorded in AGENTS.md")
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    for rel, digest in lock["sha256"].items():
        if file_sha256(REPO / rel) != digest:
            raise AssertionError(f"{rel} differs from the Study 4 lock")
    if s3.git("status", "--porcelain", "--untracked-files=no"):
        raise AssertionError("Tracked files are modified; run from a clean pushed commit")
    head = s3.git("rev-parse", "HEAD")
    s3.git("fetch", "-q", "origin")
    if not s3.git("branch", "-r", "--contains", head):
        raise AssertionError("HEAD is not on the remote; run from a pushed commit")
    import datasets
    import transformers

    found = {"transformers": transformers.__version__, "datasets": datasets.__version__}
    if found != s3.VERSIONS:
        raise AssertionError(f"Versions {found} differ from preregistered {s3.VERSIONS}")
    return head


def write_frame(path, rows, arm, split):
    frame = to_hardneg_frame_rows(rows, arm, split)
    path = assert_outside_repo(path, REPO)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(frame[0]))
        writer.writeheader()
        writer.writerows(frame)


def load_frame(path, cell):
    return [
        {"text": r["text"], "source": r.get("source", ""), "cell": cell} for r in s3.read_rows(path)
    ]


class Miner:
    """Scores generic-filtered texts with the pinned released detector; keeps flagged ones."""

    def __init__(self, token, bench_keys, hb):
        from injection_lab.transformer import load_released

        repo, label, sha = MINING_DETECTOR
        self.model, self.tok, self.idx = load_released(repo, label, sha, token)
        self.bench_keys, self.hb = bench_keys, hb
        self.stats, self.mined = {}, []

    def run(self, source, texts):
        from injection_lab.transformer import score

        keep = [
            t
            for t in texts
            if t.lower() not in self.bench_keys
            and self.hb._normalize_text(t).lower() not in self.bench_keys
        ]
        probs = score(self.model, self.tok, keep, positive_index=self.idx, max_length=512)
        hits = [t for t, p in zip(keep, probs) if p >= MINING_THRESHOLD] if keep else []
        st = self.stats.setdefault(
            source, {"passed_filter": 0, "not_in_benchmark": 0, "flagged": 0}
        )
        st["passed_filter"] += len(texts)
        st["not_in_benchmark"] += len(keep)
        st["flagged"] += len(hits)
        self.mined.extend({"text": t, "source": source} for t in hits)


def disjoint_universe(mined, eval_texts, train_attack_texts, hb):
    """Disjointness from evaluation rows, label-conflict removal against training attacks,
    then within-pool near-duplicate removal. Returns (universe, filter counts)."""
    texts = [r["text"] for r in mined]
    hits_eval = cross_containment_hits(texts, eval_texts)
    hits_attack = cross_containment_hits(texts, train_attack_texts)
    rows = [r for i, r in enumerate(mined) if i not in hits_eval and i not in hits_attack]
    keep = semantic_keep_mask([r["text"] for r in rows], eval_texts)
    after_semantic = [r for r, k in zip(rows, keep) if k]
    universe = hb.semantic_dedup(after_semantic)
    counts = {
        "mined": len(mined),
        "removed_containment_vs_eval": len(hits_eval),
        "removed_containment_vs_train_attacks": len(hits_attack - hits_eval),
        "removed_char_tfidf_vs_eval": len(rows) - len(after_semantic),
        "removed_within_pool": len(after_semantic) - len(universe),
        "available": len(universe),
    }
    return universe, counts


def build_pools(pids_root, private, public, study3_private, token):
    done = private / "pools_done.json"
    if done.exists():
        return json.loads(done.read_text(encoding="utf-8"))
    from datasets import load_dataset
    from transformers import AutoTokenizer

    hb = s3.load_pids_module(pids_root, "data_builder/build_hard_benign.py", "pids_hb4")
    revisions = s3.hf_revisions(token)
    revisions["mining_detector"] = {"repo": MINING_DETECTOR[0], "sha": MINING_DETECTOR[2]}
    data = pids_root / DATA
    bench = [r["text"] for f in data.rglob("*.csv") for r in s3.read_rows(f) if r.get("text")]
    bench_keys = {hb._normalize_text(t).lower() for t in bench} | {
        " ".join(t.split()).lower() for t in bench
    }
    eval_texts = [
        r["text"]
        for f in s3.EVAL_FILES.values()
        for r in s3.read_rows(data / f)
        if r["text"].strip()
    ]
    train_attack_texts = [r["text"] for r in s3.read_rows(data / "train.csv") if r["label"] == "1"]
    miner = Miner(token, bench_keys, hb)

    oasst = []
    for split in ("train", "validation"):
        ds = load_dataset(
            s3.HF_REPOS["oasst1"][0], split=split, revision=revisions["oasst1"]["sha"]
        )
        for row in ds:
            role, lang = str(row.get("role", "")).lower(), str(row.get("lang", "")).lower()
            if role == "prompter" and lang == "en":
                t = generic_filter(row.get("text", ""))
                if t:
                    oasst.append(t)
    miner.run("oasst1", oasst)
    ds = load_dataset(s3.HF_REPOS["dolly"][0], split="train", revision=revisions["dolly"]["sha"])
    miner.run("dolly", [t for t in (generic_filter(r.get("instruction", "")) for r in ds) if t])

    stream = load_dataset(
        s3.HF_REPOS["lmsys"][0],
        split="train",
        streaming=True,
        token=token,
        revision=revisions["lmsys"]["sha"],
    )
    universe, counts, lmsys_range = [], {}, None
    for _lo, hi, rows in index_blocks(stream, LMSYS_START, LMSYS_STEP, LMSYS_MAX_INDEX):
        texts = []
        for row in rows:
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
            t = generic_filter(first, moderation_flagged(row.get("openai_moderation")))
            if t:
                texts.append(t)
        miner.run("lmsys", texts)
        lmsys_range = [LMSYS_START, hi]
        universe, counts = disjoint_universe(miner.mined, eval_texts, train_attack_texts, hb)
        s3.log(f"mining: LMSYS [{LMSYS_START}, {hi}) done; {counts['available']} rows available")
        if counts["available"] >= N_TRAIN + N_VAL:
            break  # preregistered: extend the scan range only while short
    miner.model.to("cpu")
    if counts.get("available", 0) < N_TRAIN + N_VAL:
        raise SystemExit(
            f"Only {counts.get('available', 0)} mined rows after filters up to index "
            f"{LMSYS_MAX_INDEX}; preregistered stop before any fit"
        )
    for r in universe:
        r["cell"] = f"mined|{r['source']}"

    b1_train, b1_val = split_train_val(universe, POOL_SEED)
    curated = {
        "train": load_frame(data / "hard_negative_train.csv", "curated"),
        "val": load_frame(data / "hard_negative_val.csv", "curated"),
    }
    b3_train, b3_val = mix_pools(curated, {"train": b1_train, "val": b1_val}, POOL_SEED + 20)
    pools = {"B1_mined": (b1_train, b1_val), "B3_curated_mined": (b3_train, b3_val)}
    for arm in STUDY3_POOLS:  # same rows, same order, same file as Study 3
        for split in ("train", "val"):
            name = f"{arm}_hard_negative_{split}.csv"
            shutil.copy(study3_private / name, assert_outside_repo(private / name, REPO))
    manifest, source_mix = [], {}
    hb_rows = s3.read_rows(data / s3.EVAL_FILES["hard_benign"])
    ext_texts = [r["text"] for r in hb_rows if r["source_type"] == "real" and r["text"].strip()]
    composition = {"external_test": s3.profile(ext_texts, hb)}
    for arm, (train, val) in pools.items():
        for split, rows_ in (("train", train), ("val", val)):
            write_frame(private / f"{arm}_hard_negative_{split}.csv", rows_, arm, split)
            manifest += [
                {
                    "arm": arm,
                    "split": split,
                    "cell": r["cell"],
                    "text_sha256": fingerprint(r["text"]),
                }
                for r in rows_
            ]
        composition[arm] = s3.profile([r["text"] for r in train + val], hb)
        mix = {}
        for r in train + val:
            mix[r["cell"]] = mix.get(r["cell"], 0) + 1
        source_mix[arm] = mix

    tok = AutoTokenizer.from_pretrained(
        s3.HF_REPOS["deberta"][0], revision=revisions["deberta"]["sha"]
    )
    test = s3.read_rows(data / s3.EVAL_FILES["test"])
    framed_summary = {}
    for kind, label, seed in (("attack", "1", POOL_SEED + 30), ("benign", "0", POOL_SEED + 31)):
        base = [r for r in test if r["label"] == label]
        texts, prefix_idx = framed([r["text"] for r in base], seed)
        lengths = [len(tok(t, truncation=False)["input_ids"]) for t in texts]
        path = assert_outside_repo(private / f"framed_{kind}.csv", REPO)
        with open(path, "w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["text", "label", "parent_seed_id", "prefix_index", "truncated"])
            for r, t, p, n in zip(base, texts, prefix_idx, lengths):
                writer.writerow([t, label, r["parent_seed_id"], p, int(n > 512)])
        framed_summary[kind] = {
            "n": len(texts),
            "prefix_counts": np.bincount(prefix_idx, minlength=len(FRAMING_PREFIXES)).tolist(),
            "share_truncated_past_512_tokens": float(np.mean([n > 512 for n in lengths])),
        }

    audit = uniform_draw(b1_train + b1_val, AUDIT_N, POOL_SEED + 40)
    audit_path = assert_outside_repo(private / "audit_B1_blind.csv", REPO)
    with open(audit_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["audit_id", "text", "is_benign (1/0)", "notes"])
        for i, r in enumerate(audit):
            writer.writerow([f"b{i:03d}", r["text"], "", ""])

    result = {
        "hf_revisions": revisions,
        "mining": miner.stats,
        "lmsys_range_scanned": lmsys_range,
        "filters": counts,
        "source_mix": source_mix,
        "composition": composition,
        "framed": framed_summary,
        "audit_ids": [
            {"audit_id": f"b{i:03d}", "text_sha256": fingerprint(r["text"])}
            for i, r in enumerate(audit)
        ],
        "manifest": manifest,
    }
    done.write_text(json.dumps(result), encoding="utf-8")
    write_json(public / "pool_manifest.json", result)
    return result


def score(model_dir, root, arm, best_threshold, extra):
    """Study 3's scorer (same settings), plus the framed attack and framed benign sets."""
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
        name: probs([str(r["text"]) for r in s3.read_rows(data / f)])
        for name, f in s3.EVAL_FILES.items()
    }
    for name, texts in extra.items():
        scores[name] = probs(texts)
    val = s3.read_rows(data / "val.csv")
    if arm != "A0_none":
        val += s3.read_rows(data / "hard_negative_val.csv")
    val_probs = probs([str(r["text"]) for r in val])
    tau, _ = best_threshold(val_probs, np.array([int(r["label"]) for r in val]))
    gpu = torch.cuda.get_device_name(0) if device.type == "cuda" else "cpu"
    model.to("cpu")
    if device.type == "cuda":
        torch.cuda.empty_cache()
    return scores, float(tau), gpu


def run_one(arm, seed, pids_root, private, work, best_threshold, extra):
    """One fit + score; one identical retry, then the arm is marked failed. Scores are kept
    in the private folder until the analysis stage (blinding)."""
    out = private / "scores" / f"{arm}_seed{seed}.npz"
    failed = private / "scores" / f"{arm}_seed{seed}.failed"
    if out.exists() or failed.exists():
        return None
    root = s3.arm_root(pids_root, arm, private, work)
    fit_dir = work / "fits" / f"{arm}_seed{seed}"
    (private / "logs").mkdir(parents=True, exist_ok=True)
    log_path = private / "logs" / f"{arm}_seed{seed}.log"
    for attempt in (1, 2):
        shutil.rmtree(fit_dir, ignore_errors=True)
        start = time.time()
        if s3.fit(arm, seed, root, fit_dir, log_path):
            seconds = time.time() - start
            scores, tau, gpu = score(fit_dir / "model", root, arm, best_threshold, extra)
            out.parent.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(
                out, tau=tau, fit_seconds=seconds, attempts=attempt, gpu=gpu, **scores
            )
            shutil.rmtree(fit_dir)
            return seconds / 60
        s3.log(f"{arm} seed {seed}: attempt {attempt} failed")
    failed.parent.mkdir(parents=True, exist_ok=True)
    failed.write_text("failed twice with identical settings\n", encoding="utf-8")
    shutil.rmtree(fit_dir, ignore_errors=True)
    return "failed"


def analyze(pids_root, private, public, head, unrestored, study3_public):
    data = pids_root / DATA
    hb = s3.read_rows(data / s3.EVAL_FILES["hard_benign"])
    test = s3.read_rows(data / s3.EVAL_FILES["test"])
    y = np.array([int(r["label"]) for r in test])
    fa_rows = s3.read_rows(private / "framed_attack.csv")
    fb_rows = s3.read_rows(private / "framed_benign.csv")
    present = np.array([bool(r["text"].strip()) for r in hb])
    ext = np.array([r["source_type"] == "real" for r in hb]) & present
    cur = np.array([r["source_type"] == "curated" for r in hb])
    lm = np.array([r["source"].startswith("lmsys") for r in hb])
    hb_arr = np.array(hb, dtype=object)
    prefix = np.array([int(r["prefix_index"]) for r in fa_rows])
    untrunc = np.array([r["truncated"] == "0" for r in fa_rows])
    groups = {
        "ext": s3.near_duplicate_groups([r["text"] for r in hb_arr[ext]], "e"),
        "cur": s3.near_duplicate_groups([r["text"] for r in hb_arr[cur]], "c"),
        "test": np.array([r["parent_seed_id"] or f"t{i}" for i, r in enumerate(test)]),
        "fa": np.array([r["parent_seed_id"] or f"fa{i}" for i, r in enumerate(fa_rows)]),
        "fb": np.array([r["parent_seed_id"] or f"fb{i}" for i, r in enumerate(fb_rows)]),
    }
    arms = [
        a for a in ARMS if all((private / "scores" / f"{a}_seed{s}.npz").exists() for s in SEEDS)
    ]
    complete = len(arms) == len(ARMS)
    runs = {a: [np.load(private / "scores" / f"{a}_seed{s}.npz") for s in SEEDS] for a in arms}
    all_fa = np.ones(len(fa_rows), bool)
    all_fb = np.ones(len(fb_rows), bool)
    endpoints = {
        # name: (score key, row mask, group key, use tau_val, sub-mask of the group array)
        "ext_fpr_0.5": ("hard_benign", ext, "ext", False, None),
        "ext_fpr_tau_val": ("hard_benign", ext, "ext", True, None),
        "ext_fpr_lmsys_0.5": ("hard_benign", ext & lm, "ext", False, lm[ext]),
        "ext_fpr_oasst1_dolly_0.5": ("hard_benign", ext & ~lm, "ext", False, ~lm[ext]),
        "curated_fpr_0.5": ("hard_benign", cur, "cur", False, None),
        "test_recall_0.5": ("test", y == 1, "test", False, y == 1),
        "test_fpr_0.5": ("test", y == 0, "test", False, y == 0),
        "framed_attack_recall_0.5": ("framed_attack", all_fa, "fa", False, None),
        "framed_attack_recall_untruncated_0.5": ("framed_attack", untrunc, "fa", False, untrunc),
        "framed_benign_fpr_0.5": ("framed_benign", all_fb, "fb", False, None),
    }
    for k in range(len(FRAMING_PREFIXES)):
        endpoints[f"framed_attack_recall_prefix{k}_0.5"] = (
            "framed_attack",
            prefix == k,
            "fa",
            False,
            prefix == k,
        )

    def flags(arm, key):
        split, mask, _, use_tau, _ = endpoints[key]
        return np.array(
            [r[split][mask] >= (float(r["tau"]) if use_tau else THRESHOLD) for r in runs[arm]],
            float,
        )

    def grp(key):
        _, _, gkey, _, sub = endpoints[key]
        return groups[gkey] if sub is None else groups[gkey][sub]

    descriptive = {}
    for arm in arms:
        f1s = np.array([f1_at(r["test"], y, THRESHOLD) for r in runs[arm]])
        d = {k: s3.rate_interval(flags(arm, k), grp(k), f"s4:{arm}:{k}") for k in endpoints}
        for k in ("ext_fpr_0.5", "curated_fpr_0.5"):
            d[k]["ci95_seed_t_over_seed_rates"] = seed_t_interval(flags(arm, k).mean(1), 0.95)
        d["test_f1_0.5"] = {
            "estimate": float(f1s.mean()),
            "ci95_seed_t": seed_t_interval(f1s, 0.95),
        }
        d["framing_recall_change_0.5"] = s3.contrast(
            flags(arm, "framed_attack_recall_0.5"),
            flags(arm, "test_recall_0.5"),
            groups["fa"],
            f"s4:{arm}:framing_recall_change",
            SECONDARY_REPS,
            0.95,
        )
        d["framing_benign_fpr_change_0.5"] = s3.contrast(
            flags(arm, "framed_benign_fpr_0.5"),
            flags(arm, "test_fpr_0.5"),
            groups["fb"],
            f"s4:{arm}:framing_fpr_change",
            SECONDARY_REPS,
            0.95,
        )
        d["per_seed"] = [
            {
                "seed": s,
                "tau_val": float(r["tau"]),
                "fit_minutes": float(r["fit_seconds"]) / 60,
                "attempts": int(r["attempts"]),
                "gpu": str(r["gpu"]),
            }
            for s, r in zip(SEEDS, runs[arm])
        ]
        descriptive[arm] = d

    tag = f"{int(round(CONFIRMATORY_LEVEL * 10000)) / 100:g}"
    confirmatory = []
    for a, b, key, kind in CONFIRMATORY:
        name = f"{a} - {b} [{key}]"
        entry = {"contrast": name, "kind": kind}
        if a in arms and b in arms:
            fa_, fb_ = flags(a, key), flags(b, key)
            boot = joint_bootstrap_diff(
                fa_, fb_, grp(key), CONFIRMATORY_REPS, named_rng("s4:" + name)
            )
            per_seed = fa_.mean(1) - fb_.mean(1)
            bci = percentile_interval(boot, CONFIRMATORY_LEVEL)
            tci = seed_t_interval(per_seed, CONFIRMATORY_LEVEL)
            entry.update(
                {
                    "estimate": float(fa_.mean() - fb_.mean()),
                    "per_seed_difference": per_seed.tolist(),
                    f"bootstrap_ci{tag}": bci,
                    f"seed_t_ci{tag}": tci,
                }
            )
            if kind == "difference":
                entry.update(decide(bci, tci, complete))
            else:
                ok = noninferior(bci[0]) and noninferior(tci[0])
                entry.update(
                    {
                        "status": "complete" if complete else "incomplete",
                        "margin": NONINFERIORITY_MARGIN,
                        "noninferior": ok if complete else None,
                    }
                )
        else:
            entry.update(decide(None, None, False))
        confirmatory.append(entry)

    recipe = None
    if complete:
        b3 = descriptive["B3_curated_mined"]
        recipe = recipe_success(
            confirmatory[1].get("established_reduction"),
            confirmatory[2].get("established_reduction"),
            confirmatory[3].get("noninferior"),
            [b3["ext_fpr_0.5"]["ci95"][1], b3["ext_fpr_0.5"]["ci95_seed_t_over_seed_rates"][1]],
            [
                b3["curated_fpr_0.5"]["ci95"][1],
                b3["curated_fpr_0.5"]["ci95_seed_t_over_seed_rates"][1],
            ],
        )

    secondary_specs = [
        ("B1_mined", "A1_curated", "ext_fpr_0.5"),
        ("B1_mined", "A2_matched", "ext_fpr_0.5"),
        ("A3_source_only", "A1_curated", "ext_fpr_0.5"),
        ("B3_curated_mined", "A1_curated", "curated_fpr_0.5"),
        ("B1_mined", "A1_curated", "ext_fpr_oasst1_dolly_0.5"),
        ("B1_mined", "A0_none", "test_recall_0.5"),
        ("B1_mined", "A0_none", "test_fpr_0.5"),
        ("B1_mined", "A0_none", "framed_attack_recall_0.5"),
        ("A1_curated", "A0_none", "framed_attack_recall_0.5"),
        ("A3_source_only", "A0_none", "framed_attack_recall_0.5"),
        ("B3_curated_mined", "A0_none", "framed_benign_fpr_0.5"),
        ("A2_matched", "A0_none", "framed_benign_fpr_0.5"),
    ]
    secondary = []
    for a, b, key in secondary_specs:
        if a in arms and b in arms:
            name = f"{a} - {b} [{key}]"
            res = s3.contrast(
                flags(a, key), flags(b, key), grp(key), "s4:" + name, SECONDARY_REPS, 0.95
            )
            secondary.append({"contrast": name, "exploratory": True, **res})

    replication = {"note": "descriptive per-seed values; no interval", "arms": {}}
    for arm in ("A0_none", "A1_curated", "A2_matched", "A3_source_only"):
        if arm not in arms:
            continue
        rows, missing = [], []
        for s, r in zip(SEEDS, runs[arm]):
            path = study3_public / "scores" / f"{arm}_seed{s}.npz"
            if not path.exists():
                missing.append(s)
                continue
            old = np.load(path)
            if len(old["hard_benign"]) != len(r["hard_benign"]):
                missing.append(s)
                continue
            rows.append(
                {
                    "seed": s,
                    "gpu_study4": str(r["gpu"]),
                    "max_abs_score_diff_hard_benign": float(
                        np.abs(old["hard_benign"] - r["hard_benign"]).max()
                    ),
                    "study3_ext_fpr_0.5": float((old["hard_benign"][ext] >= THRESHOLD).mean()),
                    "study4_ext_fpr_0.5": float((r["hard_benign"][ext] >= THRESHOLD).mean()),
                }
            )
        replication["arms"][arm] = {"seeds": rows, "missing_seeds": missing}

    report = {
        "status": "complete" if complete else "incomplete",
        "commit": head,
        "pids_commit": s3.PIDS_COMMIT,
        "seeds": list(SEEDS),
        "arms_complete": arms,
        "arms_failed_or_missing": [a for a in ARMS if a not in arms],
        "n_external": int(ext.sum()),
        "n_external_unrestored_excluded": int(unrestored),
        "n_framed_attacks": len(fa_rows),
        "n_framed_benign": len(fb_rows),
        "confirmatory_level": CONFIRMATORY_LEVEL,
        "confirmatory": confirmatory,
        "recipe_success_B3": recipe,
        "secondary_contrasts_exploratory": secondary,
        "descriptive": descriptive,
        "replication_vs_study3": replication,
        "interval_method": (
            "As Study 3: percentile bootstrap resampling near-duplicate groups (external and "
            "curated hard-benign rows: word 5-gram containment >= 0.5, transitive, within each "
            "set; test and framed rows: parent_seed_id) and, independently, the 5 seeds; "
            f"contrasts pair rows and seed indices. Confirmatory: {len(CONFIRMATORY)} contrasts "
            f"at {CONFIRMATORY_LEVEL:.4f} (Bonferroni), {CONFIRMATORY_REPS} replicates, plus a "
            "Student-t (df 4) interval over per-seed differences; both must agree. "
            f"Non-inferiority margin {NONINFERIORITY_MARGIN} on recall (two-sided 99% lower "
            "bound = one-sided 99.5%). Secondary contrasts are exploratory: "
            f"{SECONDARY_REPS} replicates, 95%, uncorrected. Seeds share one dataset and are "
            "not independent test examples."
        ),
        "finished_utc": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    write_json(public / "study4_results.json", report)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help="Drive folder for Study 4 state")
    parser.add_argument("--study3-out", required=True, help="Drive folder of Study 3")
    parser.add_argument("--stage", choices=("pools", "pilot", "all"), required=True)
    parser.add_argument("--pids-root", default="/content/pidsbench")
    parser.add_argument("--work", default="/content/study4_work")
    args = parser.parse_args()
    token = os.environ.get("HF_TOKEN", "")
    if not token:
        raise SystemExit("Set HF_TOKEN from Colab Secrets (never paste it into a cell)")
    head = verify()
    out = assert_outside_repo(args.out, REPO)
    work = assert_outside_repo(args.work, REPO)
    study3 = assert_outside_repo(args.study3_out, REPO)
    study3_private = study3 / "private_lmsys_text_do_not_share"
    for arm in STUDY3_POOLS:
        if not (study3_private / f"{arm}_hard_negative_train.csv").exists():
            raise SystemExit(f"Study 3 pool {arm} not found in {study3_private}")
    private = out / "private_lmsys_text_do_not_share"
    public = out / "public"
    for d in (private, public, work):
        d.mkdir(parents=True, exist_ok=True)
    pids_root, unrestored = s3.ensure_pids(Path(args.pids_root), token)
    s3.log(f"PIDS-Bench ready; {unrestored} LMSYS test rows unrestored")
    pools = build_pools(pids_root, private, public, study3_private, token)
    s3.log(f"mining: {json.dumps(pools['mining'])}; LMSYS range {pools['lmsys_range_scanned']}")
    s3.log(f"filters: {json.dumps(pools['filters'])}; mix: {json.dumps(pools['source_mix'])}")
    if args.stage == "pools":
        s3.log("pools stage complete; see public/pool_manifest.json (no detector trained)")
        return
    extra = {
        "framed_attack": [r["text"] for r in s3.read_rows(private / "framed_attack.csv")],
        "framed_benign": [r["text"] for r in s3.read_rows(private / "framed_benign.csv")],
    }
    best_threshold = s3.load_pids_module(
        pids_root, "src/baselines/deberta_v3_hardneg.py", "pids_hardneg4"
    ).best_threshold
    plan = [(a, s) for s in SEEDS for a in ARMS]
    if args.stage == "pilot":
        plan = [("B1_mined", SEEDS[0])]
    for arm, seed in plan:
        result = run_one(arm, seed, pids_root, private, work, best_threshold, extra)
        if result == "failed":
            s3.log(f"{arm} seed {seed}: FAILED twice; arm marked incomplete")
        elif result is not None:
            s3.log(f"{arm} seed {seed}: fit took {result:.1f} min")
    if args.stage == "pilot":
        s3.log("pilot complete")
        return
    report = analyze(pids_root, private, public, head, unrestored, study3 / "public")
    s3.log(f"analysis written: status {report['status']}")


if __name__ == "__main__":
    main()
