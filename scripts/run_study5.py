"""Study 5 runner (Colab GPU): paraphrase provenance, attack safety, transfer, framing.

Stages (each resumable; all state on Drive):
  pools   verify lock -> PIDS-Bench with restored LMSYS test rows -> O pool (OASST1+Dolly,
          raw) and its GPT-4o-mini paraphrases (O_para) -> W pool (WildChat, raw) ->
          raw-seed table for the test set, NotInject, HackAPrompt, framing sets, audits.
          No detector is trained.
  fits    seed-major over arms: PIDS-Bench's own training (subprocess, via run_study3),
          our scoring of every frozen set, delete the model (A0 kept in fp16, privately).
  analyze confirmatory (Holm over 9 tests) and secondary analyses ->
          public/study5_results.json.
Fixed by docs/PREREGISTRATION_STUDY5.md. Licence-restricted text (LMSYS, WildChat) never
enters this git repository; only fingerprints, counts and scores are written publicly.

    python scripts/run_study5.py --out /content/drive/MyDrive/study5 --stage pools|pilot|all
"""

import argparse
import csv
import json
import math
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
sys.path.insert(0, str(REPO / "scripts"))

import run_study3 as s3  # noqa: E402  (locked Study 3 helpers, imported unmodified)
import run_study4 as s4  # noqa: E402  (locked Study 4 helpers, imported unmodified)

from injection_lab.data import file_sha256, write_json  # noqa: E402
from injection_lab.pools import INJECGUARD_REVISION  # noqa: E402
from injection_lab.study3 import (  # noqa: E402
    assert_outside_repo,
    cross_containment_hits,
    f1_at,
    fingerprint,
    named_rng,
    semantic_keep_mask,
)
from injection_lab.study4 import framed as study4_framed  # noqa: E402
from injection_lab.study4 import generic_filter, moderation_flagged, uniform_draw  # noqa: E402
from injection_lab.study5 import (  # noqa: E402
    ARM_SEEDS,
    BOOT_REPS,
    FRAMING_CELLS,
    N_RESERVE,
    N_TRAIN,
    N_VAL,
    NI_MARGIN,
    PARAPHRASE_MODEL,
    PARAPHRASE_TEMPERATURE,
    PARAPHRASE_TEMPLATE,
    POOL_SEED,
    SEED_CLASS,
    SEED_ORIGIN,
    SEEDS_MAIN,
    SEEDS_W,
    THRESHOLD,
    TOST_FRACTION,
    auroc,
    boot_p_noninferior,
    boot_p_two_sided,
    fpr_at_recall,
    framed,
    holm,
    is_english,
    length_ok,
    paired_within_model_diff,
    paraphrase_valid,
    parse_seed_id,
    percentile,
    system_prompt_key,
    t_interval,
    twoway_cell_diff,
    unpaired_bootstrap_diff,
    unpaired_bootstrap_interaction,
    welch_interval,
)

LOCK = REPO / "results/study5/PREREG_LOCK.json"
APPROVAL = "PREREGISTRATION_STUDY5.md may be fit and scored"
DATA = s3.DATA
REAL = Path("data/real_prompts")
WILDCHAT = "allenai/WildChat-1M"
INJECGUARD_URL = "https://github.com/InjecGuard/InjecGuard"
O_CANDIDATES = 4000
W_CANDIDATES = 5000
W_TEMPLATE_CAP = math.ceil(0.05 * (N_TRAIN + N_VAL))
AUDIT_N = 100
SECONDARY_REPS = 2000
MAX_TOKENS = 512


def log(msg):
    print(f"[study5 {datetime.now(UTC):%H:%M:%S}] {msg}", flush=True)


def verify():
    if APPROVAL not in (REPO / "AGENTS.md").read_text(encoding="utf-8"):
        raise PermissionError("Owner approval for Study 5 is not recorded in AGENTS.md")
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    for rel, digest in lock["sha256"].items():
        if file_sha256(REPO / rel) != digest:
            raise AssertionError(f"{rel} differs from the Study 5 lock")
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


def write_csv(path, fieldnames, rows):
    path = assert_outside_repo(path, REPO)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_rows(path):
    csv.field_size_limit(10**9)
    return s3.read_rows(path)


def ensure_injecguard(work):
    root = assert_outside_repo(work / "injecguard", REPO)
    if not root.exists():
        subprocess.run(["git", "clone", "-q", INJECGUARD_URL, str(root)], check=True)
    s3.git("checkout", "-q", INJECGUARD_REVISION, cwd=root)
    return root / "datasets"


# ------------------------------------- paraphrasing -------------------------------------


def paraphrase_all(texts, cache_path, key):
    """GPT-4o-mini paraphrases with PIDS-Bench's prompt; cached per text fingerprint."""
    from openai import OpenAI

    client = OpenAI(api_key=key)
    cache = {}
    if cache_path.exists():
        for line in cache_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                item = json.loads(line)
                cache[(item["fp"], item["attempt"])] = item["text"]

    def call(text, attempt):
        k = (fingerprint(text), attempt)
        if k in cache:
            return cache[k]
        for tries in range(6):
            try:
                resp = client.chat.completions.create(
                    model=PARAPHRASE_MODEL,
                    messages=[{"role": "user", "content": PARAPHRASE_TEMPLATE.format(text=text)}],
                    temperature=PARAPHRASE_TEMPERATURE,
                    max_tokens=512,
                    seed=POOL_SEED + attempt,
                )
                out = (resp.choices[0].message.content or "").strip()
                break
            except Exception as exc:  # rate limits, transient errors
                if tries == 5:
                    raise
                log(f"paraphrase retry after {type(exc).__name__}")
                time.sleep(2 ** (tries + 1))
        cache[k] = out
        with open(cache_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps({"fp": k[0], "attempt": attempt, "text": out}) + "\n")
        return out

    return call


# ------------------------------------- pools stage --------------------------------------


def disjoint(rows, eval_texts, extra_refs, hb):
    """Containment vs evaluation rows and extra references, char TF-IDF vs evaluation rows,
    then PIDS-Bench's within-pool semantic dedup. Returns (rows, counts)."""
    texts = [r["text"] for r in rows]
    hits = cross_containment_hits(texts, list(eval_texts) + list(extra_refs))
    kept = [r for i, r in enumerate(rows) if i not in hits]
    keep = semantic_keep_mask([r["text"] for r in kept], eval_texts)
    after = [r for r, k in zip(kept, keep) if k]
    final = hb.semantic_dedup(after)
    return final, {
        "candidates": len(rows),
        "removed_containment": len(hits),
        "removed_char_tfidf": len(kept) - len(after),
        "removed_within_pool": len(after) - len(final),
        "available": len(final),
    }


def template_cap(rows, cap):
    """Keep at most `cap` rows per word-5-gram containment group (stream order)."""
    groups = s3.near_duplicate_groups([r["text"] for r in rows], "w")
    counts, out = {}, []
    for r, g in zip(rows, groups):
        if counts.get(g, 0) < cap:
            counts[g] = counts.get(g, 0) + 1
            out.append(r)
    return out, max(counts.values()) if counts else 0


def build_raw_seeds(pids_root, tok):
    """Unique recoverable seeds of test.csv rows (obfuscated rows excluded)."""
    real = {s: read_rows(pids_root / REAL / f"{s}.csv") for s in SEED_CLASS}
    test = read_rows(pids_root / DATA / "test.csv")
    train = read_rows(pids_root / DATA / "train.csv")
    seen_keys = set()
    for r in train:
        parsed = parse_seed_id(r["parent_seed_id"])
        if parsed and parsed[0] == "spml_injection" and parsed[1] < len(real[parsed[0]]):
            seen_keys.add(system_prompt_key(real[parsed[0]][parsed[1]]["text"]))
    seeds = {}
    for i, r in enumerate(test):
        parsed = parse_seed_id(r["parent_seed_id"])
        if not parsed or r.get("obfuscation", "none") != "none":
            continue
        source, idx = parsed
        if idx >= len(real[source]) or int(r["label"]) != SEED_CLASS[source]:
            continue
        sid = r["parent_seed_id"]
        if sid not in seeds:
            text = real[source][idx]["text"]
            seeds[sid] = {
                "seed_id": sid,
                "text": text,
                "source": source,
                "label": SEED_CLASS[source],
                "origin": SEED_ORIGIN[source],
                "english": int(is_english(text)),
                "n_tokens": len(tok(text, truncation=False)["input_ids"]),
                "spml_seen": int(
                    source == "spml_injection" and system_prompt_key(text) in seen_keys
                ),
                "test_rows": [],
            }
        seeds[sid]["test_rows"].append(i)
    rows = []
    for s in seeds.values():
        s = dict(s, test_rows=";".join(map(str, s["test_rows"])))
        rows.append(s)
    return rows


def build_pools(pids_root, private, public, token, openai_key, work):
    done = private / "pools_done.json"
    if done.exists():
        return json.loads(done.read_text(encoding="utf-8"))
    from datasets import load_dataset
    from huggingface_hub import HfApi
    from transformers import AutoTokenizer

    hb = s3.load_pids_module(pids_root, "data_builder/build_hard_benign.py", "pids_hb5")
    revisions = s3.hf_revisions(token)
    revisions["wildchat"] = {
        "repo": WILDCHAT,
        "sha": HfApi(token=token).dataset_info(WILDCHAT).sha,
    }
    revisions["paraphraser"] = {"model": PARAPHRASE_MODEL, "temperature": PARAPHRASE_TEMPERATURE}
    data = pids_root / DATA
    bench = [r["text"] for f in data.rglob("*.csv") for r in read_rows(f) if r.get("text")]
    pids_seed_od = [
        r["text"]
        for s in ("sharegpt", "stackexchange")
        for r in read_rows(pids_root / REAL / f"{s}.csv")
    ]
    bench_keys = {" ".join(t.split()).lower() for t in bench + pids_seed_od}
    eval_texts = [
        r["text"] for f in s3.EVAL_FILES.values() for r in read_rows(data / f) if r["text"].strip()
    ]
    tok = AutoTokenizer.from_pretrained(
        s3.HF_REPOS["deberta"][0], revision=revisions["deberta"]["sha"]
    )
    raw_seeds = build_raw_seeds(pids_root, tok)
    seed_texts = [r["text"] for r in raw_seeds]
    ig = ensure_injecguard(work)
    notinject = [
        {"text": item["prompt"], "subset": part}
        for part in ("one", "two", "three")
        for item in json.loads((ig / f"NotInject_{part}.json").read_text(encoding="utf-8"))
    ]
    hackaprompt = [
        {"text": item["prompt"]}
        for item in json.loads((ig / "train.json").read_text(encoding="utf-8"))
        if item["source"] == "hackaprompt-dataset" and int(item["label"]) == 1
    ]
    all_eval = eval_texts + seed_texts + [r["text"] for r in notinject]

    # O pool: OASST1 + Dolly, raw, generic hygiene only.
    cands = []
    for split in ("train", "validation"):
        ds = load_dataset(
            s3.HF_REPOS["oasst1"][0], split=split, revision=revisions["oasst1"]["sha"]
        )
        for row in ds:
            if (
                str(row.get("role", "")).lower() == "prompter"
                and str(row.get("lang", "")).lower() == "en"
            ):
                t = generic_filter(row.get("text", ""))
                if t and t.lower() not in bench_keys:
                    cands.append({"text": t, "source": "oasst1"})
    ds = load_dataset(s3.HF_REPOS["dolly"][0], split="train", revision=revisions["dolly"]["sha"])
    for row in ds:
        t = generic_filter(row.get("instruction", ""))
        if t and t.lower() not in bench_keys:
            cands.append({"text": t, "source": "dolly"})
    rng = np.random.default_rng(POOL_SEED)
    cands = [cands[i] for i in rng.permutation(len(cands))[:O_CANDIDATES]]
    o_universe, o_filters = disjoint(cands, all_eval, pids_seed_od, hb)
    o_draw = uniform_draw(o_universe, N_TRAIN + N_VAL + N_RESERVE, POOL_SEED + 1)

    terms = sorted(set(hb.HARD_BENIGN_CONTEXT_TERMS + hb.INJECTION_KEYWORDS))
    call = paraphrase_all([r["text"] for r in o_draw], private / "paraphrases.jsonl", openai_key)
    pairs, drops = [], {"with_term": 0, "without_term": 0, "attempts": 0}
    for r in o_draw:
        if len(pairs) == N_TRAIN + N_VAL:
            break
        has_term = any(t in r["text"].lower() for t in terms)
        para = None
        for attempt in (0, 1):
            drops["attempts"] += 1
            candidate = call(r["text"], attempt)
            if length_ok(r["text"]) and paraphrase_valid(r["text"], candidate, terms):
                para = " ".join(candidate.split())
                break
        if para is None:
            drops["with_term" if has_term else "without_term"] += 1
            continue
        pairs.append({"raw": r["text"], "para": para, "source": r["source"]})
    if len(pairs) < N_TRAIN + N_VAL:
        raise SystemExit(f"Only {len(pairs)} valid paraphrase pairs; preregistered stop")
    o_raw = [{"text": p["raw"], "source": p["source"], "cell": f"o|{p['source']}"} for p in pairs]
    o_para = [{"text": p["para"], "source": p["source"], "cell": f"o|{p['source']}"} for p in pairs]

    # W pool: WildChat, raw first user turns.
    w_cands = []
    stream = load_dataset(
        WILDCHAT, split="train", streaming=True, token=token, revision=revisions["wildchat"]["sha"]
    )
    for row in stream:
        if len(w_cands) >= W_CANDIDATES:
            break
        if (
            str(row.get("language", "")).lower() != "english"
            or row.get("toxic")
            or row.get("redacted")
        ):
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
        if t and t.lower() not in bench_keys:
            w_cands.append({"text": t, "source": "wildchat"})
    w_cands, w_max_group = template_cap(w_cands, W_TEMPLATE_CAP)
    w_universe, w_filters = disjoint(w_cands, all_eval, [], hb)
    w_universe, _ = template_cap(w_universe, W_TEMPLATE_CAP)
    w_draw = uniform_draw(w_universe, N_TRAIN + N_VAL, POOL_SEED + 2)
    for r in w_draw:
        r["cell"] = "w|wildchat"

    pools = {
        "O_raw": (o_raw[:N_TRAIN], o_raw[N_TRAIN:]),
        "O_para": (o_para[:N_TRAIN], o_para[N_TRAIN:]),
        "W_raw": (w_draw[:N_TRAIN], w_draw[N_TRAIN:]),
    }
    manifest, composition = [], {}
    hb_rows = read_rows(data / s3.EVAL_FILES["hard_benign"])
    ext_texts = [r["text"] for r in hb_rows if r["source_type"] == "real" and r["text"].strip()]
    composition["external_test"] = s3.profile(ext_texts, hb)
    for arm, (train, val) in pools.items():
        for split, rows_ in (("train", train), ("val", val)):
            s4.write_frame(private / f"{arm}_hard_negative_{split}.csv", rows_, arm, split)
            manifest += [
                {"arm": arm, "split": split, "text_sha256": fingerprint(r["text"])} for r in rows_
            ]
        composition[arm] = s3.profile([r["text"] for r in train + val], hb)

    # Frozen evaluation sets (private; licence-restricted or derived text).
    write_csv(
        private / "raw_seeds.csv",
        [
            "seed_id",
            "text",
            "source",
            "label",
            "origin",
            "english",
            "n_tokens",
            "spml_seen",
            "test_rows",
        ],
        raw_seeds,
    )
    write_csv(private / "notinject.csv", ["text", "subset"], notinject)
    write_csv(private / "hackaprompt.csv", ["text"], hackaprompt)
    test = read_rows(data / "test.csv")
    benign_idx = [i for i, r in enumerate(test) if r["label"] == "0"]
    benign_texts = [test[i]["text"] for i in benign_idx]
    frame_rows = []
    for cell, (texts, pidx) in framed(benign_texts, POOL_SEED + 50).items():
        frame_rows += [
            {"cell": cell, "test_row": i, "prefix": p, "text": t}
            for i, p, t in zip(benign_idx, pidx, texts)
        ]
    s4_texts, s4_idx = study4_framed(benign_texts, POOL_SEED + 51)
    frame_rows += [
        {"cell": "study4", "test_row": i, "prefix": p, "text": t}
        for i, p, t in zip(benign_idx, s4_idx, s4_texts)
    ]
    write_csv(private / "framing.csv", ["cell", "test_row", "prefix", "text"], frame_rows)

    # Blind audits (owner labels; never committed).
    w_audit = uniform_draw(w_draw, AUDIT_N, POOL_SEED + 60)
    write_csv(
        private / "audit_W_blind.csv",
        ["audit_id", "text", "is_benign (1/0)", "notes"],
        [
            {"audit_id": f"w{i:03d}", "text": r["text"], "is_benign (1/0)": "", "notes": ""}
            for i, r in enumerate(w_audit)
        ],
    )
    p_audit = uniform_draw([{"text": p["raw"], **p} for p in pairs], AUDIT_N, POOL_SEED + 61)
    write_csv(
        private / "audit_Opara_blind.csv",
        ["audit_id", "original", "paraphrase", "same_meaning_and_benign (1/0)", "notes"],
        [
            {
                "audit_id": f"p{i:03d}",
                "original": r["raw"],
                "paraphrase": r["para"],
                "same_meaning_and_benign (1/0)": "",
                "notes": "",
            }
            for i, r in enumerate(p_audit)
        ],
    )

    def seed_counts(pred):
        return sum(1 for r in raw_seeds if pred(r))

    result = {
        "hf_revisions": revisions,
        "injecguard_revision": INJECGUARD_REVISION,
        "o_filters": o_filters,
        "o_paraphrase_drops": drops,
        "w_filters": w_filters,
        "w_max_group_before_cap": w_max_group,
        "composition": composition,
        "raw_seeds": {
            "benign": seed_counts(lambda r: r["label"] == 0),
            "attack": seed_counts(lambda r: r["label"] == 1),
            "benign_by_origin": {
                o: seed_counts(lambda r, o=o: r["label"] == 0 and r["origin"] == o)
                for o in ("human", "llm", "unverified")
            },
            "spml_unseen_english_le512": seed_counts(
                lambda r: (
                    r["source"] == "spml_injection"
                    and not r["spml_seen"]
                    and r["english"]
                    and r["n_tokens"] <= MAX_TOKENS
                )
            ),
            "spml_seen": seed_counts(lambda r: r["spml_seen"] == 1),
            "non_english": seed_counts(lambda r: not r["english"]),
            "over_512_tokens": seed_counts(lambda r: r["n_tokens"] > MAX_TOKENS),
        },
        "notinject": len(notinject),
        "hackaprompt": len(hackaprompt),
        "framing_rows_per_cell": len(benign_idx),
        "manifest": manifest,
    }
    done.write_text(json.dumps(result), encoding="utf-8")
    write_json(public / "pool_manifest.json", result)
    return result


# --------------------------------------- fits ---------------------------------------


def extra_sets(private):
    sets = {
        "raw_seeds": [r["text"] for r in read_rows(private / "raw_seeds.csv")],
        "notinject": [r["text"] for r in read_rows(private / "notinject.csv")],
        "hackaprompt": [r["text"] for r in read_rows(private / "hackaprompt.csv")],
    }
    frames = read_rows(private / "framing.csv")
    for cell in [*sorted(FRAMING_CELLS), "study4"]:
        sets[f"frame_{cell}"] = [r["text"] for r in frames if r["cell"] == cell]
    return sets


def run_one(arm, seed, pids_root, private, work, best_threshold, extra):
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
            scores, tau, gpu = s4.score(fit_dir / "model", root, arm, best_threshold, extra)
            out.parent.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(
                out, tau=tau, fit_seconds=seconds, attempts=attempt, gpu=gpu, **scores
            )
            if arm == "A0_none":
                keep_checkpoint(fit_dir / "model", private / "checkpoints" / f"A0_seed{seed}")
            shutil.rmtree(fit_dir)
            return seconds / 60
        log(f"{arm} seed {seed}: attempt {attempt} failed")
    failed.parent.mkdir(parents=True, exist_ok=True)
    failed.write_text("failed twice with identical settings\n", encoding="utf-8")
    shutil.rmtree(fit_dir, ignore_errors=True)
    return "failed"


def keep_checkpoint(model_dir, dest):
    """fp16 copy of an A0 model for future evaluation sets (private, never committed)."""
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    dest = assert_outside_repo(dest, REPO)
    dest.mkdir(parents=True, exist_ok=True)
    AutoModelForSequenceClassification.from_pretrained(model_dir).half().save_pretrained(dest)
    AutoTokenizer.from_pretrained(model_dir).save_pretrained(dest)


def plan():
    order = []
    for s in SEEDS_MAIN:
        for arm in ("A0_none", "O_raw", "O_para"):
            order.append((arm, s))
        if s in SEEDS_W:
            order.append(("W_raw", s))
    return order


# -------------------------------------- analysis --------------------------------------


def analyze(pids_root, private, public, head, unrestored):
    data = pids_root / DATA
    hb = read_rows(data / s3.EVAL_FILES["hard_benign"])
    test = read_rows(data / "test.csv")
    y = np.array([int(r["label"]) for r in test])
    seeds_tab = read_rows(private / "raw_seeds.csv")
    frames = read_rows(private / "framing.csv")
    hack = read_rows(private / "hackaprompt.csv")
    ni = read_rows(private / "notinject.csv")
    present = np.array([bool(r["text"].strip()) for r in hb])
    ext = np.array([r["source_type"] == "real" for r in hb]) & present
    cur = np.array([r["source_type"] == "curated" for r in hb])
    lm = np.array([r["source"].startswith("lmsys") for r in hb])
    hb_arr = np.array(hb, dtype=object)
    g_ext = s3.near_duplicate_groups([r["text"] for r in hb_arr[ext]], "e")
    g_cur = s3.near_duplicate_groups([r["text"] for r in hb_arr[cur]], "c")
    g_test = np.array([r["parent_seed_id"] or f"t{i}" for i, r in enumerate(test)])
    g_hack = s3.near_duplicate_groups([r["text"] for r in hack], "h")
    g_ni = np.array([f"n{i}" for i in range(len(ni))])
    lm_e = lm[ext]

    complete_arms = [
        a
        for a, ss in ARM_SEEDS.items()
        if all((private / "scores" / f"{a}_seed{s}.npz").exists() for s in ss)
    ]
    complete = len(complete_arms) == len(ARM_SEEDS)
    runs = {
        a: [np.load(private / "scores" / f"{a}_seed{s}.npz") for s in ARM_SEEDS[a]]
        for a in complete_arms
    }

    def flags(arm, key, mask=None):
        return np.array(
            [(r[key] if mask is None else r[key][mask]) >= THRESHOLD for r in runs[arm]], float
        )

    # Raw-seed units: raw flag per seed vs mean flag over its paraphrased test rows.
    sid = np.array([r["seed_id"] for r in seeds_tab])
    s_label = np.array([int(r["label"]) for r in seeds_tab])
    s_origin = np.array([r["origin"] for r in seeds_tab])
    s_eng = np.array([r["english"] == "1" for r in seeds_tab])
    s_ok = np.array([int(r["n_tokens"]) <= MAX_TOKENS for r in seeds_tab])
    s_unseen = np.array([r["spml_seen"] == "0" for r in seeds_tab])
    s_source = np.array([r["source"] for r in seeds_tab])
    s_rows = [list(map(int, r["test_rows"].split(";"))) for r in seeds_tab]
    s_len_raw = np.array([len(r["text"]) for r in seeds_tab])
    s_len_para = np.array([np.mean([len(test[i]["text"]) for i in rows]) for rows in s_rows])

    def seed_values(arm):
        raw = np.array([r["raw_seeds"] >= THRESHOLD for r in runs[arm]], float)
        para = np.array(
            [[np.mean(r["test"][rows] >= THRESHOLD) for rows in s_rows] for r in runs[arm]]
        )
        return raw, para

    benign_core = (s_label == 0) & s_eng & s_ok
    spml_core = (s_source == "spml_injection") & s_unseen & s_eng & s_ok

    results = {"tests": {}, "secondary": {}, "descriptive": {}}
    tests = {}

    def paired_test(name, arm, mask, extra=None):
        raw, para = seed_values(arm)
        reps = paired_within_model_diff(
            raw[:, mask], para[:, mask], sid[mask], BOOT_REPS, named_rng("s5:" + name)
        )
        per_model = raw[:, mask].mean(1) - para[:, mask].mean(1)
        return {
            "kind": "difference",
            "n_units": int(mask.sum()),
            "estimate": float(per_model.mean()),
            "per_model": per_model.tolist(),
            "reps": reps,
            "p": boot_p_two_sided(reps),
            "t_rates": per_model,
            **(extra or {}),
        }

    def unpaired_test(name, a, b, key, mask, groups, kind="difference"):
        fa, fb = flags(a, key, mask), flags(b, key, mask)
        reps = unpaired_bootstrap_diff(fa, fb, groups, BOOT_REPS, named_rng("s5:" + name))
        p = boot_p_two_sided(reps) if kind == "difference" else boot_p_noninferior(reps, NI_MARGIN)
        return {
            "kind": kind,
            "n_rows": int(fa.shape[1]),
            "estimate": float(fa.mean() - fb.mean()),
            "rates_a": fa.mean(1).tolist(),
            "rates_b": fb.mean(1).tolist(),
            "reps": reps,
            "p": p,
        }

    have = set(complete_arms)
    if "A0_none" in have:
        tests["P1"] = paired_test("P1", "A0_none", benign_core)
        tests["P2"] = paired_test("P2", "A0_none", spml_core)
        rf = np.array([r["frame_security"] >= THRESHOLD for r in runs["A0_none"]], float)
        rn = np.array([r["frame_neutral"] >= THRESHOLD for r in runs["A0_none"]], float)
        pre = {
            c: np.array([int(r["prefix"]) for r in frames if r["cell"] == c])
            for c in ("security", "neutral")
        }
        rows_fr = np.array([int(r["test_row"]) for r in frames if r["cell"] == "security"])
        reps = twoway_cell_diff(
            rf, rn, pre["security"], pre["neutral"], g_test[rows_fr], BOOT_REPS, named_rng("s5:F1")
        )
        per_model = rf.mean(1) - rn.mean(1)
        tests["F1"] = {
            "kind": "difference",
            "n_rows": int(rf.shape[1]),
            "estimate": float(per_model.mean()),
            "per_model": per_model.tolist(),
            "reps": reps,
            "p": boot_p_two_sided(reps),
            "t_rates": per_model,
        }
    if {"O_raw", "O_para"} <= have:
        tests["T1"] = unpaired_test("T1", "O_para", "O_raw", "hard_benign", ext, g_ext)
    if {"O_raw", "A0_none"} <= have:
        raw_o = np.array([r["raw_seeds"][spml_core] >= THRESHOLD for r in runs["O_raw"]], float)
        raw_a = np.array([r["raw_seeds"][spml_core] >= THRESHOLD for r in runs["A0_none"]], float)
        reps = unpaired_bootstrap_diff(raw_o, raw_a, sid[spml_core], BOOT_REPS, named_rng("s5:T2"))
        tests["T2"] = {
            "kind": "noninferior",
            "n_rows": int(spml_core.sum()),
            "estimate": float(raw_o.mean() - raw_a.mean()),
            "rates_a": raw_o.mean(1).tolist(),
            "rates_b": raw_a.mean(1).tolist(),
            "reps": reps,
            "p": boot_p_noninferior(reps, NI_MARGIN),
        }
        tests["T2h"] = unpaired_test(
            "T2h", "O_raw", "A0_none", "hackaprompt", None, g_hack, "noninferior"
        )
        tests["T3"] = unpaired_test("T3", "O_raw", "A0_none", "hard_benign", ext, g_ext)
        tests["X2"] = unpaired_test("X2", "O_raw", "A0_none", "notinject", None, g_ni)
    if {"W_raw", "O_raw"} <= have and lm_e.any() and (~lm_e).any():
        fw, fo = flags("W_raw", "hard_benign", ext), flags("O_raw", "hard_benign", ext)
        reps = unpaired_bootstrap_interaction(
            fw, fo, g_ext, lm_e, ~lm_e, BOOT_REPS, named_rng("s5:X1")
        )
        dw = fw[:, lm_e].mean(1) - fw[:, ~lm_e].mean(1)
        do = fo[:, lm_e].mean(1) - fo[:, ~lm_e].mean(1)
        tests["X1"] = {
            "kind": "difference",
            "n_rows": int(fw.shape[1]),
            "estimate": float(dw.mean() - do.mean()),
            "rates_a": dw.tolist(),
            "rates_b": do.tolist(),
            "reps": reps,
            "p": boot_p_two_sided(reps),
            "prediction": "negative (W relatively better on LMSYS rows)",
        }

    order = ["P1", "P2", "T1", "T2", "T2h", "T3", "X1", "X2", "F1"]
    names = [k for k in order if k in tests]
    rejected, used = holm([tests[k]["p"] for k in names]) if names else ([], [])
    t3_est = None
    for k, rej, a in zip(names, rejected, used):
        t = tests[k]
        if t["kind"] == "difference":
            level = 1 - a
            boot_ci = percentile(t["reps"], level)
            comp = (
                t_interval(t["t_rates"], level)
                if "t_rates" in t
                else welch_interval(t["rates_a"], t["rates_b"], level)
            )
            agree = comp[1] < 0 or comp[0] > 0
        else:
            level = 1 - 2 * a
            boot_ci = percentile(t["reps"], level)
            comp = welch_interval(t["rates_a"], t["rates_b"], level)
            agree = comp[0] > -NI_MARGIN
        established = bool(rej and agree and complete)
        results["tests"][k] = {
            key: (v.tolist() if isinstance(v, np.ndarray) else v)
            for key, v in t.items()
            if key not in ("reps", "t_rates")
        }
        results["tests"][k].update(
            {
                "holm_alpha": a,
                "holm_rejected": bool(rej),
                "bootstrap_ci": boot_ci,
                "companion_ci": comp,
                "companion": "t over models" if "t_rates" in t else "Welch over seeds",
                "established": established if complete else None,
                "fragile": bool(rej != agree) if complete else None,
            }
        )
        if k == "T3":
            t3_est = t["estimate"]
    if "T1" in tests and t3_est is not None:
        margin = TOST_FRACTION * abs(t3_est)
        b90 = percentile(tests["T1"]["reps"], 0.90)
        w90 = welch_interval(tests["T1"]["rates_a"], tests["T1"]["rates_b"], 0.90)
        gate = bool(results["tests"].get("T3", {}).get("established"))
        results["tests"]["T1"].update(
            {
                "gate_T3_established": gate,
                "fraction_of_T3": float(tests["T1"]["estimate"] / t3_est) if t3_est else None,
                "tost_margin": margin,
                "tost_bootstrap_ci90": b90,
                "tost_welch_ci90": w90,
                "equivalent": bool(
                    gate and complete and all(-margin < x < margin for x in b90 + w90)
                ),
            }
        )

    # Secondary (exploratory, 95%): strata, origins, length-matched P1, seen stratum, deepset.
    sec = {}
    if "A0_none" in have:
        for o in ("human", "llm", "unverified"):
            m = benign_core & (s_origin == o)
            if m.sum():
                r = paired_test(f"P1_{o}", "A0_none", m)
                sec[f"P1_origin_{o}"] = {
                    "n_units": int(m.sum()),
                    "estimate": r["estimate"],
                    "ci95": percentile(r["reps"], 0.95),
                }
        lm_match = benign_core & (np.abs(s_len_raw - s_len_para) <= 0.2 * s_len_para)
        r = paired_test("P1_len", "A0_none", lm_match)
        sec["P1_length_matched"] = {
            "n_units": int(lm_match.sum()),
            "estimate": r["estimate"],
            "ci95": percentile(r["reps"], 0.95),
        }
        for nm, m in (
            ("P2_spml_seen", (s_source == "spml_injection") & ~s_unseen & s_eng & s_ok),
            ("P2_deepset", (s_source == "deepset_injection") & s_eng & s_ok),
        ):
            if m.sum():
                r = paired_test(nm, "A0_none", m)
                sec[nm] = {
                    "n_units": int(m.sum()),
                    "estimate": r["estimate"],
                    "ci95": percentile(r["reps"], 0.95),
                }
    for arm_a, arm_b in (
        ("O_raw", "A0_none"),
        ("O_para", "O_raw"),
        ("W_raw", "A0_none"),
        ("W_raw", "O_raw"),
    ):
        if {arm_a, arm_b} <= have:
            for stratum, m in (("lmsys", ext & lm), ("oasst1_dolly", ext & ~lm)):
                gm = g_ext[lm_e] if stratum == "lmsys" else g_ext[~lm_e]
                if not len(gm):
                    continue
                fa, fb = flags(arm_a, "hard_benign", m), flags(arm_b, "hard_benign", m)
                reps = unpaired_bootstrap_diff(
                    fa, fb, gm, SECONDARY_REPS, named_rng(f"s5:{arm_a}-{arm_b}:{stratum}")
                )
                sec[f"{arm_a}-{arm_b}:ext_fpr_{stratum}"] = {
                    "estimate": float(fa.mean() - fb.mean()),
                    "ci95": percentile(reps, 0.95),
                }
    results["secondary_exploratory"] = sec

    # Descriptive per-arm rates (95% joint group x seed bootstrap) and threshold-free metrics.
    for arm in complete_arms:
        d = {}
        for key, score_key, mask, groups in (
            ("ext_fpr", "hard_benign", ext, g_ext),
            ("curated_fpr", "hard_benign", cur, g_cur),
            ("test_recall", "test", y == 1, g_test[y == 1]),
            ("test_fpr", "test", y == 0, g_test[y == 0]),
            ("hackaprompt_recall", "hackaprompt", None, g_hack),
            ("notinject_fpr", "notinject", None, g_ni),
        ):
            d[key] = s3.rate_interval(flags(arm, score_key, mask), groups, f"s5:{arm}:{key}")
        raw, para = seed_values(arm)
        for nm, m in (
            ("raw_benign_seed_fpr", benign_core),
            ("para_benign_seed_fpr", benign_core),
            ("raw_spml_unseen_recall", spml_core),
            ("para_spml_unseen_recall", spml_core),
        ):
            v = raw if nm.startswith("raw") else para
            d[nm] = s3.rate_interval(v[:, m], sid[m], f"s5:{arm}:{nm}")
        for cell in [*sorted(FRAMING_CELLS), "study4"]:
            fr = np.array([r[f"frame_{cell}"] >= THRESHOLD for r in runs[arm]], float)
            rows_c = np.array([int(r["test_row"]) for r in frames if r["cell"] == cell])
            d[f"frame_{cell}_flag_rate"] = s3.rate_interval(
                fr, g_test[rows_c], f"s5:{arm}:frame_{cell}"
            )
        au_raw, au_para, f95 = [], [], []
        for r in runs[arm]:
            ben = r["hard_benign"][ext]
            au_raw.append(auroc(ben, r["raw_seeds"][spml_core]))
            au_para.append(auroc(ben, r["test"][y == 1]))
            f95.append(fpr_at_recall(ben, r["test"][y == 1]))
        d["auroc_ext_vs_raw_spml"] = {
            "estimate": float(np.mean(au_raw)),
            "ci95_t": t_interval(au_raw, 0.95),
        }
        d["auroc_ext_vs_para_attacks"] = {
            "estimate": float(np.mean(au_para)),
            "ci95_t": t_interval(au_para, 0.95),
        }
        d["ext_fpr_at_95_recall_para_attacks"] = {
            "estimate": float(np.mean(f95)),
            "ci95_t": t_interval(f95, 0.95),
        }
        f1s = [f1_at(r["test"], y, THRESHOLD) for r in runs[arm]]
        d["test_f1"] = {"estimate": float(np.mean(f1s)), "ci95_t": t_interval(f1s, 0.95)}
        d["per_seed"] = [
            {
                "seed": s,
                "tau_val": float(r["tau"]),
                "fit_minutes": float(r["fit_seconds"]) / 60,
                "attempts": int(r["attempts"]),
                "gpu": str(r["gpu"]),
            }
            for s, r in zip(ARM_SEEDS[arm], runs[arm])
        ]
        results["descriptive"][arm] = d

    report = {
        "status": "complete" if complete else "incomplete",
        "commit": head,
        "pids_commit": s3.PIDS_COMMIT,
        "arm_seeds": {k: list(v) for k, v in ARM_SEEDS.items()},
        "arms_complete": complete_arms,
        "n_external": int(ext.sum()),
        "n_external_unrestored_excluded": int(unrestored),
        **results,
        "interval_method": (
            "Confirmatory: Holm over the tests present (nominal 9) at family-wise alpha 0.05. "
            "p-values from bootstrap percentile inversion (two-sided; non-inferiority one-sided "
            f"against margin {NI_MARGIN}). Bootstraps resample content units (seed ids, "
            "near-duplicate groups, parent_seed_id, prefixes for framing) and models; arms "
            "with different models are resampled independently (seeds are not reproducible, "
            "so arms are unpaired). 'Established' requires Holm rejection and agreement of a "
            "companion interval at the Holm-adjusted level (t over models for within-model "
            "contrasts; Welch over seeds between arms). T1 is interpreted only if T3 is "
            f"established; equivalence (TOST, margin {TOST_FRACTION} x |T3|) needs both 90% "
            "intervals inside the margin. Secondary results are exploratory (95%, "
            "uncorrected). Seeds share data and are not independent test examples."
        ),
        "finished_utc": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    write_json(public / "study5_results.json", report)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help="Drive folder for Study 5 state")
    parser.add_argument("--stage", choices=("pools", "pilot", "all"), required=True)
    parser.add_argument("--pids-root", default="/content/pidsbench")
    parser.add_argument("--work", default="/content/study5_work")
    args = parser.parse_args()
    token = os.environ.get("HF_TOKEN", "")
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    if not token:
        raise SystemExit("Set HF_TOKEN from Colab Secrets (never paste it into a cell)")
    head = verify()
    out = assert_outside_repo(args.out, REPO)
    work = assert_outside_repo(args.work, REPO)
    private = out / "private_restricted_text_do_not_share"
    public = out / "public"
    for d in (private, public, work):
        d.mkdir(parents=True, exist_ok=True)
    pids_root, unrestored = s3.ensure_pids(Path(args.pids_root), token)
    log(f"PIDS-Bench ready; {unrestored} LMSYS test rows unrestored")
    if not (private / "pools_done.json").exists() and not openai_key:
        raise SystemExit("Set OPENAI_API_KEY from Colab Secrets for the pools stage")
    pools = build_pools(pids_root, private, public, token, openai_key, work)
    log(
        f"O filters {json.dumps(pools['o_filters'])}; paraphrase drops {json.dumps(pools['o_paraphrase_drops'])}"
    )
    log(f"W filters {json.dumps(pools['w_filters'])}; raw seeds {json.dumps(pools['raw_seeds'])}")
    if args.stage == "pools":
        log("pools stage complete; see public/pool_manifest.json (no detector trained)")
        return
    extra = extra_sets(private)
    best_threshold = s3.load_pids_module(
        pids_root, "src/baselines/deberta_v3_hardneg.py", "pids_hardneg5"
    ).best_threshold
    order = plan()
    if args.stage == "pilot":
        order = [("O_para", SEEDS_MAIN[0])]
    for arm, seed in order:
        result = run_one(arm, seed, pids_root, private, work, best_threshold, extra)
        if result == "failed":
            log(f"{arm} seed {seed}: FAILED twice; arm marked incomplete")
        elif result is not None:
            log(f"{arm} seed {seed}: fit took {result:.1f} min")
    if args.stage == "pilot":
        log("pilot complete")
        return
    report = analyze(pids_root, private, public, head, unrestored)
    log(f"analysis written: status {report['status']}")


if __name__ == "__main__":
    main()
