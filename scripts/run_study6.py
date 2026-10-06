"""Study 6 runner (Colab GPU): released detectors' security-vocabulary sensitivity, a
trigger-word substitution attack, and audit inter-annotator agreement.

Stages (each resumable; no detector is trained):
  prepare  verify lock -> PIDS-Bench with restored LMSYS test rows (frozen against Study 5)
           -> attack rows (test, label 1, no obfuscation) with substituted versions ->
           substitution audit export (owner labels) -> public/prep_manifest.json.
  score    every detector in DETECTORS and Study 5's eight A0 checkpoints scores the frozen
           sets; scores are written privately, one file per detector.
  analyze  needs --audit SUB=<count of 1s of 50>; writes public/study6_results.json.
  iaa      needs the four iaa_*_blind.csv files labelled by the second annotator; writes
           public/iaa_results.json.
Fixed by docs/PREREGISTRATION_STUDY6.md.
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

import export_iaa  # noqa: E402  (IAA draw, imported unmodified)
import run_study3 as s3  # noqa: E402  (locked Study 3 helpers, imported unmodified)
import run_study5 as s5  # noqa: E402  (locked Study 5 helpers, imported unmodified)

from injection_lab.data import file_sha256, write_json  # noqa: E402
from injection_lab.study3 import assert_outside_repo, named_rng  # noqa: E402
from injection_lab.study4 import FRAMING_PREFIXES, uniform_draw  # noqa: E402
from injection_lab.study5 import (  # noqa: E402
    FRAMING_CELLS,
    SEEDS_MAIN,
    boot_p_two_sided,
    holm,
    paired_within_model_diff,
    percentile,
    t_interval,
    twoway_cell_diff,
)
from injection_lab.study6 import (  # noqa: E402
    A0_FAMILY,
    ALPHA,
    ATTACK_CELLS,
    BOOT_REPS,
    CHANGED_RECALL_FLOOR,
    DETECTORS,
    MAX_TOKENS,
    PLAIN_FPR_CEILING,
    PREP_SEED,
    SECONDARY_REPS,
    SUB_AUDIT_N,
    SUB_AUDIT_PASS,
    THRESHOLD,
    agreement,
    attack_variants,
    benign_index,
    best_of_k_evades,
    conditional_rate_reps,
    shared,
    single_prefix_index,
    substitute,
    variant_slices,
)

LOCK = REPO / "results/study6/PREREG_LOCK.json"
APPROVAL = "PREREGISTRATION_STUDY6.md may be scored"
DATA = s3.DATA
S5_PRIVATE = "private_restricted_text_do_not_share"
TOKEN_MARGIN = 4


def log(msg):
    print(f"[study6 {datetime.now(UTC):%H:%M:%S}] {msg}", flush=True)


def verify():
    if APPROVAL not in (REPO / "AGENTS.md").read_text(encoding="utf-8"):
        raise PermissionError("Owner approval for Study 6 is not recorded in AGENTS.md")
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    for rel, digest in lock["sha256"].items():
        if file_sha256(REPO / rel) != digest:
            raise AssertionError(f"{rel} differs from the Study 6 lock")
    if s3.git("status", "--porcelain", "--untracked-files=no"):
        raise AssertionError("Tracked files are modified; run from a clean pushed commit")
    head = s3.git("rev-parse", "HEAD")
    s3.git("fetch", "-q", "origin")
    if not s3.git("branch", "-r", "--contains", head):
        raise AssertionError("HEAD is not on the remote; run from a pushed commit")
    import transformers

    if transformers.__version__ != s3.VERSIONS["transformers"]:
        raise AssertionError(f"transformers {transformers.__version__} is not preregistered")
    return head


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ------------------------------------- prepare -------------------------------------


def prepare(pids_root, s5_private, private, public):
    done = private / "prep_done.json"
    if done.exists():
        return json.loads(done.read_text(encoding="utf-8"))
    s5.check_frozen(pids_root, s5_private)
    test = s5.read_rows(pids_root / DATA / "test.csv")
    attacks = []
    for i, r in enumerate(test):
        if r["label"] != "1" or r.get("obfuscation", "none") != "none":
            continue
        sub, n = substitute(r["text"])
        attacks.append(
            {
                "test_row": i,
                "parent_seed_id": r["parent_seed_id"] or f"t{i}",
                "source": r["source"],
                "text": r["text"],
                "sub_text": sub,
                "n_changes": n,
            }
        )
    s5.write_csv(private / "attacks.csv", list(attacks[0]), attacks)
    changed = [a for a in attacks if a["n_changes"] > 0]
    audit = uniform_draw(changed, SUB_AUDIT_N, PREP_SEED + 1)
    s5.write_csv(
        private / "audit_SUB_blind.csv",
        ["audit_id", "original", "substituted", "same_attack_intent (1/0)", "notes"],
        [
            {
                "audit_id": f"s{i:03d}",
                "original": a["text"],
                "substituted": a["sub_text"],
                "same_attack_intent (1/0)": "",
                "notes": "",
            }
            for i, a in enumerate(audit)
        ],
    )
    inputs = {name: sha(s5_private / name) for name in ("framing.csv", "notinject.csv")} | {
        "attacks.csv": sha(private / "attacks.csv")
    }
    result = {
        "attack_rows": len(attacks),
        "attack_groups": len({a["parent_seed_id"] for a in attacks}),
        "changed_rows": len(changed),
        "changed_groups": len({a["parent_seed_id"] for a in changed}),
        "attack_sources": dict(
            sorted(
                {
                    s: sum(a["source"] == s for a in attacks)
                    for s in {a["source"] for a in attacks}
                }.items()
            )
        ),
        "substitutions_per_changed_row_median": float(np.median([a["n_changes"] for a in changed])),
        "input_sha256": inputs,
    }
    done.write_text(json.dumps(result), encoding="utf-8")
    write_json(public / "prep_manifest.json", result)
    return result


def check_inputs(s5_private, private, prep):
    for name, digest in prep["input_sha256"].items():
        folder = private if name == "attacks.csv" else s5_private
        if sha(folder / name) != digest:
            raise AssertionError(f"{name} changed since the prepare stage")


# -------------------------------------- scoring --------------------------------------


def frozen_sets(pids_root, s5_private, private):
    test = s5.read_rows(pids_root / DATA / "test.csv")
    frames = s5.read_rows(s5_private / "framing.csv")
    cells = [*sorted(FRAMING_CELLS), "study4"]
    rows0 = [int(r["test_row"]) for r in frames if r["cell"] == cells[0]]
    sets = {"benign_plain": [test[i]["text"] for i in rows0]}
    for cell in cells:
        sub = [r for r in frames if r["cell"] == cell]
        if [int(r["test_row"]) for r in sub] != rows0:
            raise AssertionError(f"framing cell {cell} rows are not aligned")
        sets[f"frame_{cell}"] = [r["text"] for r in sub]
    sets["external"] = [
        r["text"] for r in s5.read_rows(pids_root / DATA / s3.EVAL_FILES["hard_benign"])
    ]
    sets["notinject"] = [r["text"] for r in s5.read_rows(s5_private / "notinject.csv")]
    attacks = s5.read_rows(private / "attacks.csv")
    sets["attack_variants"] = [
        v for a in attacks for v in attack_variants(a["text"], a["sub_text"])
    ]
    return sets, len(attacks)


def load_detector(key, repo, revision, token):
    from huggingface_hub import HfApi
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    resolved = HfApi(token=token).model_info(repo, revision=revision).sha
    if revision is not None and resolved != revision:
        raise AssertionError(f"{repo}: resolved {resolved} != pinned {revision}")
    tok = AutoTokenizer.from_pretrained(repo, revision=resolved, token=token)
    model = AutoModelForSequenceClassification.from_pretrained(
        repo, revision=resolved, token=token, trust_remote_code=False
    )
    return model, tok, {"repo": repo, "sha": resolved}


def score_texts(model, tok, texts, benign):
    import torch

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    model = model.to(device).float().eval()
    order = np.argsort([len(t) for t in texts], kind="stable")
    out = np.empty(len(texts))
    with torch.no_grad():
        for s in range(0, len(texts), 128):
            idx = order[s : s + 128]
            enc = tok(
                [texts[i] for i in idx],
                truncation=True,
                max_length=MAX_TOKENS,
                padding=True,
                return_tensors="pt",
            ).to(device)
            p = torch.softmax(model(**enc).logits.double(), -1)
            out[idx] = 1 - p[:, benign].cpu().numpy()
    model.to("cpu")
    if device.type == "cuda":
        torch.cuda.empty_cache()
    return out


def eligible_mask(tok, plain_texts, prefixes, alt_texts=None):
    """True where the longest prefix plus the (longer of plain/alt) text fits in MAX_TOKENS."""
    longest = max(len(tok(p, add_special_tokens=False)["input_ids"]) for p in prefixes)
    n_plain = [len(ids) for ids in tok(list(plain_texts), add_special_tokens=False)["input_ids"]]
    if alt_texts is not None:
        n_alt = [len(ids) for ids in tok(list(alt_texts), add_special_tokens=False)["input_ids"]]
        n_plain = [max(a, b) for a, b in zip(n_plain, n_alt)]
    return np.array([n + longest + TOKEN_MARGIN <= MAX_TOKENS for n in n_plain])


def score_one(key, model, tok, benign, sets, n_attacks, attacks, out_path, meta):
    prefixes = [p for cell in FRAMING_CELLS.values() for p in cell] + list(FRAMING_PREFIXES)
    scores = {name: score_texts(model, tok, texts, benign) for name, texts in sets.items()}
    scores["attack_variants"] = scores["attack_variants"].reshape(n_attacks, -1)
    elig_benign = eligible_mask(tok, sets["benign_plain"], prefixes)
    elig_attack = eligible_mask(
        tok, [a["text"] for a in attacks], prefixes, [a["sub_text"] for a in attacks]
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out_path, elig_benign=elig_benign, elig_attack=elig_attack, **scores)
    meta_path = out_path.with_suffix(".json")
    meta_path.write_text(json.dumps(meta), encoding="utf-8")
    log(f"{key}: scored")


def score_all(pids_root, s5_private, private, public, token):
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    sets, n_attacks = frozen_sets(pids_root, s5_private, private)
    attacks = s5.read_rows(private / "attacks.csv")
    revisions = {}
    for key, repo, revision in DETECTORS:
        out = private / "scores" / f"{key}.npz"
        bad = private / "scores" / f"{key}.unavailable.json"
        if out.exists() or bad.exists():
            continue
        try:
            model, tok, meta = load_detector(key, repo, revision, token)
            benign = benign_index(model.config.id2label)
            meta["id2label"] = {str(k): v for k, v in model.config.id2label.items()}
            if benign is None:
                raise ValueError(f"no unique benign label in {meta['id2label']}")
            meta["benign_index"] = benign
        except Exception as exc:  # unavailable detectors are reported, never replaced
            bad.parent.mkdir(parents=True, exist_ok=True)
            bad.write_text(json.dumps({"repo": repo, "reason": repr(exc)[:500]}), encoding="utf-8")
            log(f"{key}: UNAVAILABLE ({type(exc).__name__})")
            continue
        score_one(key, model, tok, benign, sets, n_attacks, attacks, out, meta)
        del model
    for seed in SEEDS_MAIN:
        key = f"{A0_FAMILY}_seed{seed}"
        out = private / "scores" / f"{key}.npz"
        if out.exists():
            continue
        ckpt = s5_private / "checkpoints" / f"A0_seed{seed}"
        tok = AutoTokenizer.from_pretrained(ckpt)
        model = AutoModelForSequenceClassification.from_pretrained(ckpt)
        meta = {"checkpoint": f"study5 A0 seed {seed} (fp16, scored in fp32)", "benign_index": 0}
        score_one(key, model, tok, 0, sets, n_attacks, attacks, out, meta)
        del model
    for path in sorted((private / "scores").glob("*.json")):
        revisions[path.stem] = json.loads(path.read_text(encoding="utf-8"))
    write_json(public / "detector_revisions.json", revisions)


# -------------------------------------- analysis --------------------------------------


def analyze(pids_root, s5_private, private, public, head, sub_audit):
    test = s5.read_rows(pids_root / DATA / "test.csv")
    frames = s5.read_rows(s5_private / "framing.csv")
    attacks = s5.read_rows(private / "attacks.csv")
    hb = s5.read_rows(pids_root / DATA / s3.EVAL_FILES["hard_benign"])
    frozen = json.loads((s5_private / "eval_fingerprints.json").read_text(encoding="utf-8"))
    ext = np.array([r["source_type"] == "real" for r in hb]) & np.array(
        [fp != "" for fp in frozen["hard_benign"]]
    )
    g_ext = s3.near_duplicate_groups([r["text"] for r, e in zip(hb, ext) if e], "e")
    cells = [*sorted(FRAMING_CELLS), "study4"]
    rows0 = np.array([int(r["test_row"]) for r in frames if r["cell"] == cells[0]])
    g_benign = np.array([test[i]["parent_seed_id"] or f"t{i}" for i in rows0])
    pidx = {c: np.array([int(r["prefix"]) for r in frames if r["cell"] == c]) for c in cells}
    g_att = np.array([a["parent_seed_id"] for a in attacks])
    changed = np.array([int(a["n_changes"]) > 0 for a in attacks])
    sl = variant_slices()
    sub_ok = sub_audit >= SUB_AUDIT_PASS

    families = {}
    unavailable = {}
    for key, repo, _ in DETECTORS:
        path = private / "scores" / f"{key}.npz"
        if path.exists():
            families[key] = [np.load(path)]
        else:
            bad = private / "scores" / f"{key}.unavailable.json"
            unavailable[key] = json.loads(bad.read_text()) if bad.exists() else "not scored"
    a0 = [private / "scores" / f"{A0_FAMILY}_seed{s}.npz" for s in SEEDS_MAIN]
    if all(p.exists() for p in a0):
        families[A0_FAMILY] = [np.load(p) for p in a0]
    else:
        unavailable[A0_FAMILY] = "incomplete"

    def fl(runs, name, mask=None):
        return np.array(
            [(r[name] if mask is None else r[name][mask]) >= THRESHOLD for r in runs], float
        )

    tests, descriptive, secondary = {}, {}, {}
    for fam, runs in families.items():
        eb = runs[0]["elig_benign"]
        ea = runs[0]["elig_attack"]
        av = [r["attack_variants"] for r in runs]
        caught = np.array([v[:, sl["plain"]][:, 0] >= THRESHOLD for v in av], float)
        d = {"n_benign_eligible": int(eb.sum()), "n_attack_eligible": int(ea.sum())}
        d["benign_plain_fpr"] = s3.rate_interval(
            fl(runs, "benign_plain", eb), g_benign[eb], f"s6:{fam}:plain"
        )
        for cell in cells:
            d[f"frame_{cell}_flag_rate"] = s3.rate_interval(
                fl(runs, f"frame_{cell}", eb), g_benign[eb], f"s6:{fam}:{cell}"
            )
        d["external_fpr"] = s3.rate_interval(
            np.array([r["external"][ext] >= THRESHOLD for r in runs], float), g_ext, f"s6:{fam}:ext"
        )
        d["notinject_fpr"] = s3.rate_interval(
            fl(runs, "notinject"),
            np.array([f"n{i}" for i in range(len(runs[0]["notinject"]))]),
            f"s6:{fam}:ni",
        )
        d["attack_recall_plain"] = s3.rate_interval(caught[:, ea], g_att[ea], f"s6:{fam}:rec")
        for cell in ATTACK_CELLS:
            one = single_prefix_index(len(attacks), cell)
            f1 = np.array(
                [v[:, sl[cell]][np.arange(len(attacks)), one] >= THRESHOLD for v in av], float
            )
            d[f"attack_recall_single_{cell}"] = s3.rate_interval(
                f1[:, ea], g_att[ea], f"s6:{fam}:single:{cell}"
            )

        def evasion(cols, name):
            ev = np.array([best_of_k_evades(v[:, cols]) for v in av], float)
            reps = conditional_rate_reps(
                ev[:, ea], caught[:, ea], g_att[ea], SECONDARY_REPS, named_rng(name)
            )
            est = np.mean(
                [(e * c).sum() / max(c.sum(), 1) for e, c in zip(ev[:, ea], caught[:, ea])]
            )
            return {"estimate": float(est), "ci95": percentile(reps, 0.95)}

        idx = np.arange(sl["academic"].start, sl["neutral"].stop)
        for cell in ATTACK_CELLS:
            d[f"evasion_best_of_24_{cell}"] = evasion(sl[cell], f"s6:{fam}:ev:{cell}")
        d["evasion_best_of_48_benign_register"] = evasion(idx, f"s6:{fam}:ev:benign48")
        sub_cols = np.r_[1, np.arange(sl["sub_academic"].start, sl["sub_academic"].stop)]
        d["evasion_sub_plus_academic"] = evasion(sub_cols, f"s6:{fam}:ev:subacad")
        d["evasion_any_variant"] = evasion(np.arange(1, av[0].shape[1]), f"s6:{fam}:ev:any")
        m = changed & ea
        d["n_changed_eligible"] = int(m.sum())
        d["recall_changed_plain"] = s3.rate_interval(caught[:, m], g_att[m], f"s6:{fam}:chp")
        subf = np.array([v[:, 1] >= THRESHOLD for v in av], float)
        d["recall_changed_sub"] = s3.rate_interval(subf[:, m], g_att[m], f"s6:{fam}:chs")
        descriptive[fam] = d

        # Confirmatory F_d (released detectors only; A0's F1 is Study 5's).
        if fam != A0_FAMILY:
            sec, aca = fl(runs, "frame_security", eb), fl(runs, "frame_academic", eb)
            reps = twoway_cell_diff(
                sec,
                aca,
                pidx["security"][eb],
                pidx["academic"][eb],
                g_benign[eb],
                BOOT_REPS,
                named_rng(f"s6:F:{fam}"),
            )
            plain = d["benign_plain_fpr"]["estimate"]
            tests[f"F_{fam}"] = {
                "estimate": float(sec.mean() - aca.mean()),
                "reps": reps,
                "informative": plain < PLAIN_FPR_CEILING,
                "per_model": None,
            }
        # Confirmatory A_d: recall on changed rows, plain - substituted (positive = evasion).
        plain_m, sub_m = caught[:, m], subf[:, m]
        reps = paired_within_model_diff(
            plain_m, sub_m, g_att[m], BOOT_REPS, named_rng(f"s6:A:{fam}")
        )
        per_model = (plain_m.mean(1) - sub_m.mean(1)).tolist()
        tests[f"A_{fam}"] = {
            "estimate": float(np.mean(per_model)),
            "reps": reps,
            "informative": float(plain_m.mean()) >= CHANGED_RECALL_FLOOR,
            "per_model": per_model if fam == A0_FAMILY else None,
        }
        # Secondary: best-of-24 academic minus security evasion; neutral minus academic.
        for a, b in (("academic", "security"), ("neutral", "academic")):
            ea_, eb_ = d[f"evasion_best_of_24_{a}"], d[f"evasion_best_of_24_{b}"]
            secondary[f"{fam}:evasion_{a}-{b}"] = ea_["estimate"] - eb_["estimate"]

    names = [k for k, v in tests.items() if v["informative"]]
    rejected, used = holm([boot_p_two_sided(tests[k]["reps"]) for k in names], ALPHA)
    out_tests = {}
    for k, v in tests.items():
        rec = {
            "estimate": v["estimate"],
            "informative": v["informative"],
            "p": boot_p_two_sided(v["reps"]),
            "bootstrap_ci95": percentile(v["reps"], 0.95),
        }
        if v["informative"]:
            i = names.index(k)
            level = 1 - used[i]
            rec.update(
                holm_alpha=used[i],
                holm_rejected=rejected[i],
                bootstrap_ci_holm=percentile(v["reps"], level),
            )
            agree = True
            if v["per_model"] is not None:
                ci = t_interval(v["per_model"], level)
                rec.update(per_model=v["per_model"], companion_ci=ci, companion="t over models")
                agree = (ci[0] > 0) if v["estimate"] > 0 else (ci[1] < 0)
            est = rejected[i] and agree
            rec["established"] = est
            rec["fragile"] = rejected[i] and not agree
            if k.startswith("A_"):
                rec["sub_audit_pass"] = sub_ok
                if not sub_ok:
                    rec["established"] = None
        else:
            rec["established"] = None
        out_tests[k] = rec

    def decision(k):
        r = out_tests.get(k)
        if r is None or not r["informative"] or r["established"] is None:
            return None
        if r["established"]:
            return 1 if r["estimate"] > 0 else -1
        return 0

    released = [k for k, _, _ in DETECTORS]
    summary = {
        "F_shared_across_released": shared({k: decision(f"F_{k}") for k in released}),
        "A_shared_across_released": shared({k: decision(f"A_{k}") for k in released})
        if sub_ok
        else None,
    }
    report = {
        "status": "complete" if not unavailable else "complete_with_unavailable",
        "commit": head,
        "detectors_scored": sorted(families),
        "unavailable": unavailable,
        "a0_seeds": list(SEEDS_MAIN),
        "sub_audit_of_50": sub_audit,
        "n_tests_in_holm": len(names),
        "tests": out_tests,
        "summary": summary,
        "secondary_exploratory": secondary,
        "descriptive": descriptive,
        "interval_method": (
            "Confirmatory: Holm over the informative tests at family-wise alpha 0.05; p-values "
            "from bootstrap percentile inversion (10,000 replicates, named streams). F_d "
            "resamples parent_seed_id groups and prefixes within cell; A_d resamples "
            "parent_seed_id groups (and, for the A0 family, models, with a t companion over "
            "models at the Holm level). Released detectors are deterministic single models, "
            "so their intervals reflect content sampling only. A tests are interpreted only "
            "if the substitution audit passes (>= 45/50). Descriptive rates: 95% joint "
            "group(+model) bootstrap, 2,000 replicates. Seeds share data and are not "
            "independent test examples."
        ),
        "finished_utc": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    write_json(public / "study6_results.json", report)
    return report


def iaa(drive_root, public):
    out = {}
    for key, folder, name, label, _ in export_iaa.AUDITS:
        owner = {r["audit_id"]: r for r in export_iaa.read_rows(drive_root / folder / name)}
        second = export_iaa.read_rows(drive_root / folder / f"iaa_{name.removeprefix('audit_')}")
        a = [str(owner[r["audit_id"]][label]).strip() for r in second]
        b = [str(r[label]).strip() for r in second]
        if any(v not in ("0", "1") for v in a + b):
            raise SystemExit(f"{key}: every IAA row needs a 1 or 0 from both annotators")
        out[key] = agreement(
            np.array(a, int), np.array(b, int), SECONDARY_REPS, named_rng(f"s6:iaa:{key}")
        )
    write_json(public / "iaa_results.json", out)
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help="Drive folder for Study 6 state")
    parser.add_argument("--study5", required=True, help="Study 5 Drive folder")
    parser.add_argument("--stage", choices=("prepare", "score", "analyze", "iaa"), required=True)
    parser.add_argument("--audit", default="", help="analyze only: SUB=<count of 1s of 50>")
    parser.add_argument("--pids-root", default="/content/pidsbench")
    args = parser.parse_args()
    out = assert_outside_repo(args.out, REPO)
    private, public = out / "private_restricted_text_do_not_share", out / "public"
    for d in (private, public):
        d.mkdir(parents=True, exist_ok=True)
    if args.stage == "iaa":
        result = iaa(Path(args.study5).parent, public)
        log("iaa written: " + json.dumps({k: round(v["kappa"], 3) for k, v in result.items()}))
        return
    token = os.environ.get("HF_TOKEN", "")
    if not token:
        raise SystemExit("Set HF_TOKEN from Colab Secrets (never paste it into a cell)")
    head = verify()
    s5_private = Path(args.study5) / S5_PRIVATE
    pids_root, unrestored = s3.ensure_pids(Path(args.pids_root), token)
    log(f"PIDS-Bench ready; {unrestored} LMSYS test rows unrestored")
    prep = prepare(pids_root, s5_private, private, public)
    log("prepared " + json.dumps({k: v for k, v in prep.items() if k != "input_sha256"}))
    check_inputs(s5_private, private, prep)
    s5.check_frozen(pids_root, s5_private)
    if args.stage == "prepare":
        log("prepare complete; label audit_SUB_blind.csv before the analyze stage")
        return
    if args.stage == "score":
        score_all(pids_root, s5_private, private, public, token)
        log("scoring complete; label the substitution audit, then run --stage analyze")
        return
    parts = dict(x.split("=") for x in args.audit.split(",") if "=" in x)
    if "SUB" not in {k.strip() for k in parts}:
        raise SystemExit("Analysis needs --audit SUB=<count of 1s of 50>")
    sub_audit = int({k.strip(): v for k, v in parts.items()}["SUB"])
    labels = [
        str(r["same_attack_intent (1/0)"]).strip()
        for r in export_iaa.read_rows(private / "audit_SUB_blind.csv")
    ]
    if any(v not in ("0", "1") for v in labels):
        raise SystemExit("audit_SUB_blind.csv has unlabelled or invalid rows")
    if labels.count("1") != sub_audit:
        raise SystemExit(f"audit has {labels.count('1')} ones but --audit says {sub_audit}")
    report = analyze(pids_root, s5_private, private, public, head, sub_audit)
    log(f"analysis written: status {report['status']}")


if __name__ == "__main__":
    main()
