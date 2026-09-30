"""Study 4 runner (Colab GPU): realistic (detector-mined) and combined benign augmentation.

Stages (each resumable, all state on Drive):
  pools   verify lock -> PIDS-Bench with restored LMSYS test rows -> mine benign rows that a
          released detector (ProtectAI v2) flags, with a generic hygiene filter and no
          PIDS-Bench selection rules -> disjointness filters -> B1/B2/B3 pools, framed
          attack set, composition report, blind audit export. No detector is trained.
  fits    per seed, per arm: PIDS-Bench's own training function in a subprocess (reused
          from run_study3), our scoring (adds the framed attacks), delete the model.
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
    LMSYS_BLOCK,
    LMSYS_MAX_INDEX,
    LMSYS_MIN_MINED,
    MINING_DETECTOR,
    MINING_THRESHOLD,
    NONINFERIORITY_MARGIN,
    POOL_SEED,
    SEEDS,
    framed_attacks,
    generic_filter,
    mix_pools,
    moderation_flagged,
    noninferior,
    split_train_val,
    uniform_draw,
)

LOCK = REPO / "results/study4/PREREG_LOCK.json"
APPROVAL = "PREREGISTRATION_STUDY4.md may be fit and scored"
LMSYS_START = 200_000  # PIDS-Bench scanned only [0, 200000)
AUDIT_N = 200
SECONDARY_REPS = 2000
DATA = s3.DATA


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


def mine(token, revisions, bench_keys, hb):
    """Score generic-filtered rows with the released detector; keep those it flags."""
    from datasets import load_dataset

    from injection_lab.transformer import load_released, score

    repo, label = MINING_DETECTOR
    model, tok, idx = load_released(repo, label, revisions["mining_detector"]["sha"], token)
    stats = {}
    mined = []

    def run(source, texts):
        keep = []
        for t in texts:
            if t.lower() in bench_keys or hb._normalize_text(t).lower() in bench_keys:
                continue
            keep.append(t)
        probs = score(model, tok, keep, positive_index=idx, max_length=512) if keep else []
        hits = [t for t, p in zip(keep, probs) if p >= MINING_THRESHOLD]
        st = stats.setdefault(source, {"passed_filter": 0, "scored": 0, "flagged": 0})
        st["passed_filter"] += len(texts)
        st["scored"] += len(keep)
        st["flagged"] += len(hits)
        mined.extend({"text": t, "source": source} for t in hits)

    stream = load_dataset(
        s3.HF_REPOS["lmsys"][0],
        split="train",
        streaming=True,
        token=token,
        revision=revisions["lmsys"]["sha"],
    )
    block, end, lmsys_scanned = [], LMSYS_START + LMSYS_BLOCK, 0
    for i, row in enumerate(stream):
        if i < LMSYS_START:
            continue
        if i >= end:
            run("lmsys", block)
            block = []
            s3.log(f"mining: LMSYS rows [{LMSYS_START}, {end}) done, {len(mined)} flagged so far")
            n_lmsys = sum(1 for r in mined if r["source"] == "lmsys")
            if n_lmsys >= LMSYS_MIN_MINED or end >= LMSYS_MAX_INDEX:
                break
            end += LMSYS_BLOCK
        lmsys_scanned = i + 1
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
        text = generic_filter(first, moderation_flagged(row.get("openai_moderation")))
        if text:
            block.append(text)
    else:
        run("lmsys", block)
    stats["lmsys"]["stream_index_end"] = lmsys_scanned
    texts = []
    for split in ("train", "validation"):
        ds = load_dataset(
            s3.HF_REPOS["oasst1"][0], split=split, revision=revisions["oasst1"]["sha"]
        )
        for row in ds:
            role, lang = str(row.get("role", "")).lower(), str(row.get("lang", "")).lower()
            if role == "prompter" and lang == "en":
                t = generic_filter(row.get("text", ""))
                if t:
                    texts.append(t)
    run("oasst1", texts)
    ds = load_dataset(s3.HF_REPOS["dolly"][0], split="train", revision=revisions["dolly"]["sha"])
    run("dolly", [t for t in (generic_filter(r.get("instruction", "")) for r in ds) if t])
    model.to("cpu")
    return mined, stats


def build_pools(pids_root, private, public, study3_private, token):
    done = private / "pools_done.json"
    if done.exists():
        return json.loads(done.read_text(encoding="utf-8"))
    from injection_lab.transformer import resolve_revision

    hb = s3.load_pids_module(pids_root, "data_builder/build_hard_benign.py", "pids_hb4")
    revisions = s3.hf_revisions(token)
    repo = MINING_DETECTOR[0]
    revisions["mining_detector"] = {"repo": repo, "sha": resolve_revision(repo, token)}
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
    mined, mining_stats = mine(token, revisions, bench_keys, hb)
    texts = [r["text"] for r in mined]
    hits = cross_containment_hits(texts, eval_texts)
    rows = [r for i, r in enumerate(mined) if i not in hits]
    keep = semantic_keep_mask([r["text"] for r in rows], eval_texts)
    after_semantic = [r for r, k in zip(rows, keep) if k]
    universe = hb.semantic_dedup(after_semantic)
    filters = {
        "mined": len(mined),
        "removed_containment_vs_eval": len(hits),
        "removed_char_tfidf_vs_eval": len(rows) - len(after_semantic),
        "removed_within_pool": len(after_semantic) - len(universe),
        "available": len(universe),
    }
    for r in universe:
        r["cell"] = f"mined|{r['source']}"

    b1_train, b1_val = split_train_val(universe, POOL_SEED)
    curated = {
        "train": load_frame(data / "hard_negative_train.csv", "curated"),
        "val": load_frame(data / "hard_negative_val.csv", "curated"),
    }
    matched = {
        split: load_frame(study3_private / f"A2_matched_hard_negative_{split}.csv", "matched")
        for split in ("train", "val")
    }
    mined_split = {"train": b1_train, "val": b1_val}
    pools = {
        "B1_mined": (b1_train, b1_val),
        "B2_curated_matched": mix_pools(curated, matched, POOL_SEED + 10),
        "B3_curated_mined": mix_pools(curated, mined_split, POOL_SEED + 20),
        "A2_matched": (matched["train"], matched["val"]),
    }
    manifest, composition = [], {"external_test": None}
    hb_rows = s3.read_rows(data / s3.EVAL_FILES["hard_benign"])
    ext_texts = [r["text"] for r in hb_rows if r["source_type"] == "real" and r["text"].strip()]
    composition["external_test"] = s3.profile(ext_texts, hb)
    source_mix = {}
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

    attacks = [r for r in s3.read_rows(data / s3.EVAL_FILES["test"]) if r["label"] == "1"]
    framed, prefix_idx = framed_attacks([r["text"] for r in attacks], POOL_SEED + 30)
    framed_path = assert_outside_repo(private / "framed_attacks.csv", REPO)
    with open(framed_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["text", "label", "parent_seed_id", "prefix_index"])
        for r, t, p in zip(attacks, framed, prefix_idx):
            writer.writerow([t, 1, r["parent_seed_id"], p])

    audit = uniform_draw(b1_train + b1_val, AUDIT_N, POOL_SEED + 40)
    audit_path = assert_outside_repo(private / "audit_B1_blind.csv", REPO)
    with open(audit_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["audit_id", "text", "is_benign (1/0)", "notes"])
        for i, r in enumerate(audit):
            writer.writerow([f"b{i:03d}", r["text"], "", ""])

    result = {
        "hf_revisions": revisions,
        "mining": mining_stats,
        "filters": filters,
        "source_mix": source_mix,
        "composition": composition,
        "framed_attacks": {"n": len(framed), "prefix_counts": np.bincount(prefix_idx).tolist()},
        "audit_ids": [
            {"audit_id": f"b{i:03d}", "text_sha256": fingerprint(r["text"])}
            for i, r in enumerate(audit)
        ],
        "manifest": manifest,
    }
    done.write_text(json.dumps(result), encoding="utf-8")
    write_json(public / "pool_manifest.json", result)
    return result


def score(model_dir, root, arm, best_threshold, framed_texts):
    """Study 3's scorer (same settings), plus the framed attack set."""
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
    scores["framed"] = probs(framed_texts)
    val = s3.read_rows(data / "val.csv") + s3.read_rows(data / "hard_negative_val.csv")
    val_probs = probs([str(r["text"]) for r in val])
    tau, _ = best_threshold(val_probs, np.array([int(r["label"]) for r in val]))
    model.to("cpu")
    if device.type == "cuda":
        torch.cuda.empty_cache()
    return scores, float(tau)


def run_one(arm, seed, pids_root, private, work, public, best_threshold, framed_texts):
    """One fit + score; one identical retry, then the arm is marked failed."""
    out = public / "scores" / f"{arm}_seed{seed}.npz"
    failed = public / "scores" / f"{arm}_seed{seed}.failed"
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
            scores, tau = score(fit_dir / "model", root, arm, best_threshold, framed_texts)
            out.parent.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(out, tau=tau, fit_seconds=seconds, attempts=attempt, **scores)
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
    framed_rows = s3.read_rows(private / "framed_attacks.csv")
    present = np.array([bool(r["text"].strip()) for r in hb])
    ext = np.array([r["source_type"] == "real" for r in hb]) & present
    cur = np.array([r["source_type"] == "curated" for r in hb])
    lm = np.array([r["source"].startswith("lmsys") for r in hb])
    hb_arr = np.array(hb, dtype=object)
    groups = {
        "ext": s3.near_duplicate_groups([r["text"] for r in hb_arr[ext]], "e"),
        "cur": s3.near_duplicate_groups([r["text"] for r in hb_arr[cur]], "c"),
        "test": np.array([r["parent_seed_id"] or f"t{i}" for i, r in enumerate(test)]),
        "framed": np.array([r["parent_seed_id"] or f"f{i}" for i, r in enumerate(framed_rows)]),
    }
    arms = [
        a for a in ARMS if all((public / "scores" / f"{a}_seed{s}.npz").exists() for s in SEEDS)
    ]
    complete = len(arms) == len(ARMS)
    runs = {a: [np.load(public / "scores" / f"{a}_seed{s}.npz") for s in SEEDS] for a in arms}
    lm_e = lm[ext]
    endpoints = {
        # name: (score key, row mask, group key, use tau_val, sub-mask within group key)
        "ext_fpr_0.5": ("hard_benign", ext, "ext", False, None),
        "ext_fpr_tau_val": ("hard_benign", ext, "ext", True, None),
        "ext_fpr_lmsys_0.5": ("hard_benign", ext & lm, "ext", False, lm_e),
        "ext_fpr_oasst1_dolly_0.5": ("hard_benign", ext & ~lm, "ext", False, ~lm_e),
        "curated_fpr_0.5": ("hard_benign", cur, "cur", False, None),
        "test_recall_0.5": ("test", y == 1, "test", False, None),
        "test_fpr_0.5": ("test", y == 0, "test", False, None),
        "framed_attack_recall_0.5": (
            "framed",
            np.ones(len(framed_rows), bool),
            "framed",
            False,
            None,
        ),
    }

    def flags(arm, key):
        split, mask, _, use_tau, _ = endpoints[key]
        return np.array(
            [r[split][mask] >= (float(r["tau"]) if use_tau else THRESHOLD) for r in runs[arm]],
            float,
        )

    def grp(key):
        split, mask, gkey, _, within = endpoints[key]
        if gkey in ("ext", "cur"):
            return groups[gkey] if within is None else groups[gkey][within]
        return groups[gkey][mask]

    descriptive = {}
    for arm in arms:
        f1s = np.array([f1_at(r["test"], y, THRESHOLD) for r in runs[arm]])
        descriptive[arm] = {
            k: s3.rate_interval(flags(arm, k), grp(k), f"s4:{arm}:{k}") for k in endpoints
        }
        descriptive[arm]["test_f1_0.5"] = {
            "estimate": float(f1s.mean()),
            "ci95_seed_t": seed_t_interval(f1s, 0.95),
        }
        plain = flags(arm, "test_recall_0.5")
        framed = flags(arm, "framed_attack_recall_0.5")
        descriptive[arm]["framing_recall_drop_0.5"] = s3.contrast(
            framed, plain, groups["framed"], f"s4:{arm}:framing_drop", SECONDARY_REPS, 0.95
        )
        descriptive[arm]["per_seed"] = [
            {
                "seed": s,
                "tau_val": float(r["tau"]),
                "fit_minutes": float(r["fit_seconds"]) / 60,
                "attempts": int(r["attempts"]),
            }
            for s, r in zip(SEEDS, runs[arm])
        ]

    level_tag = f"{int(CONFIRMATORY_LEVEL * 10000) / 100:g}"
    confirmatory = []
    for a, b, key, kind in CONFIRMATORY:
        name = f"{a} - {b} [{key}]"
        entry = {"contrast": name, "kind": kind}
        if a in arms and b in arms:
            fa, fb = flags(a, key), flags(b, key)
            boot = joint_bootstrap_diff(
                fa, fb, grp(key), CONFIRMATORY_REPS, named_rng("s4:" + name)
            )
            per_seed = fa.mean(1) - fb.mean(1)
            bci = percentile_interval(boot, CONFIRMATORY_LEVEL)
            tci = seed_t_interval(per_seed, CONFIRMATORY_LEVEL)
            entry.update(
                {
                    "estimate": float(fa.mean() - fb.mean()),
                    "per_seed_difference": per_seed.tolist(),
                    f"bootstrap_ci{level_tag}": bci,
                    f"seed_t_ci{level_tag}": tci,
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

    secondary_specs = [
        ("B1_mined", "A2_matched", "ext_fpr_0.5"),
        ("B2_curated_matched", "A2_matched", "ext_fpr_0.5"),
        ("B2_curated_matched", "A1_curated", "ext_fpr_0.5"),
        ("B2_curated_matched", "A2_matched", "curated_fpr_0.5"),
        ("B3_curated_mined", "A1_curated", "curated_fpr_0.5"),
        ("B1_mined", "A1_curated", "ext_fpr_oasst1_dolly_0.5"),
        ("B1_mined", "A1_curated", "test_recall_0.5"),
        ("B1_mined", "A1_curated", "framed_attack_recall_0.5"),
        ("A2_matched", "A1_curated", "framed_attack_recall_0.5"),
        ("B2_curated_matched", "A1_curated", "framed_attack_recall_0.5"),
        ("B1_mined", "A1_curated", "test_fpr_0.5"),
    ]
    secondary = []
    for a, b, key in secondary_specs:
        if a in arms and b in arms:
            name = f"{a} - {b} [{key}]"
            secondary.append(
                {
                    "contrast": name,
                    **s3.contrast(
                        flags(a, key), flags(b, key), grp(key), "s4:" + name, SECONDARY_REPS, 0.95
                    ),
                }
            )

    replication = {}
    for arm in ("A1_curated", "A2_matched"):
        if arm not in arms or study3_public is None:
            continue
        rows = []
        for s, r in zip(SEEDS, runs[arm]):
            path = study3_public / "scores" / f"{arm}_seed{s}.npz"
            if not path.exists():
                continue
            old = np.load(path)
            rows.append(
                {
                    "seed": s,
                    "max_abs_score_diff_hard_benign": float(
                        np.abs(old["hard_benign"] - r["hard_benign"]).max()
                    ),
                    "study3_ext_fpr_0.5": float((old["hard_benign"][ext] >= THRESHOLD).mean()),
                    "study4_ext_fpr_0.5": float((r["hard_benign"][ext] >= THRESHOLD).mean()),
                }
            )
        replication[arm] = rows

    report = {
        "status": "complete" if complete else "incomplete",
        "commit": head,
        "pids_commit": s3.PIDS_COMMIT,
        "seeds": list(SEEDS),
        "arms_complete": arms,
        "arms_failed_or_missing": [a for a in ARMS if a not in arms],
        "n_external": int(ext.sum()),
        "n_external_unrestored_excluded": int(unrestored),
        "n_framed_attacks": len(framed_rows),
        "confirmatory_level": CONFIRMATORY_LEVEL,
        "confirmatory": confirmatory,
        "secondary_contrasts": secondary,
        "descriptive": descriptive,
        "replication_vs_study3": replication,
        "interval_method": (
            "As Study 3: percentile bootstrap resampling near-duplicate groups (external and "
            "curated hard-benign rows: word 5-gram containment >= 0.5, transitive, within each "
            "set; test and framed attacks: parent_seed_id) and, independently, the 5 seeds; "
            "contrasts pair rows and seed indices. Confirmatory: 4 contrasts at "
            f"{CONFIRMATORY_LEVEL:.4f} (Bonferroni), {CONFIRMATORY_REPS} replicates, plus a "
            "Student-t (df 4) interval over per-seed differences; both must agree. "
            f"Non-inferiority margin {NONINFERIORITY_MARGIN} on recall. Secondary: "
            f"{SECONDARY_REPS} replicates, 95%. Seeds share one dataset and are not "
            "independent test examples."
        ),
        "finished_utc": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    write_json(public / "study4_results.json", report)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help="Drive folder for Study 4 state")
    parser.add_argument(
        "--study3-out", required=True, help="Drive folder of Study 3 (pools, scores)"
    )
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
    if not (study3_private / "A2_matched_hard_negative_train.csv").exists():
        raise SystemExit(f"Study 3 matched pool not found in {study3_private}")
    private = out / "private_lmsys_text_do_not_share"
    public = out / "public"
    for d in (private, public, work):
        d.mkdir(parents=True, exist_ok=True)
    pids_root, unrestored = s3.ensure_pids(Path(args.pids_root), token)
    s3.log(f"PIDS-Bench ready; {unrestored} LMSYS test rows unrestored")
    pools = build_pools(pids_root, private, public, study3_private, token)
    s3.log(f"mining: {json.dumps(pools['mining'])}")
    s3.log(
        f"filters: {json.dumps(pools['filters'])}; source mix: {json.dumps(pools['source_mix'])}"
    )
    if args.stage == "pools":
        s3.log("pools stage complete; see public/pool_manifest.json (no detector trained)")
        return
    framed_texts = [r["text"] for r in s3.read_rows(private / "framed_attacks.csv")]
    best_threshold = s3.load_pids_module(
        pids_root, "src/baselines/deberta_v3_hardneg.py", "pids_hardneg4"
    ).best_threshold
    plan = [(a, s) for s in SEEDS for a in ARMS]
    if args.stage == "pilot":
        plan = [("B1_mined", SEEDS[0])]
    for arm, seed in plan:
        result = run_one(arm, seed, pids_root, private, work, public, best_threshold, framed_texts)
        if result == "failed":
            s3.log(f"{arm} seed {seed}: FAILED twice; arm marked incomplete")
        elif result is not None:
            s3.log(f"{arm} seed {seed}: fit took {result:.1f} min")
    if args.stage == "pilot":
        s3.log("pilot complete")
        return
    study3_public = study3 / "public"
    report = analyze(pids_root, private, public, head, unrestored, study3_public)
    s3.log(f"analysis written: status {report['status']}")


if __name__ == "__main__":
    main()
