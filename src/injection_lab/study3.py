"""Study 3: distribution-matched benign augmentation vs PIDS-Bench external over-defense.

Pure, testable logic only (no LMSYS access, no GPU). Colab orchestration lives in
scripts/run_study3.py. Fixed by docs/PREREGISTRATION_STUDY3.md.

LMSYS-Chat-1M text may not be redistributed: text-bearing files are only ever written
outside the git working tree (see assert_outside_repo).
"""

import hashlib
import subprocess
from pathlib import Path

import numpy as np

SEEDS = (13, 42, 123, 2024, 7777)  # PIDS-Bench's five seeds
POOL_SEED = 20260925
N_TRAIN, N_VAL = 419, 116  # PIDS-Bench curated pool sizes; their script asserts these
THRESHOLD = 0.5  # PIDS-Bench default operating point
SEMANTIC_THRESHOLD = 0.92  # PIDS-Bench's own near-duplicate cutoff (char_wb 3-4 TF-IDF)
PRIMARY_ARMS = ("A0_none", "A1_curated", "A2_matched", "A3_source_only")
SECONDARY_ARMS = ("A2L_matched_lmsys_only",)
CONFIRMATORY = (("A2_matched", "A1_curated"), ("A2_matched", "A0_none"))
BOOTSTRAP_SEED = 20260925
CONFIRMATORY_REPS = 10000


def assert_outside_repo(path, repo_root):
    """Refuse to write text-bearing output inside the git working tree (LMSYS licence)."""
    path, repo_root = Path(path).resolve(), Path(repo_root).resolve()
    if path == repo_root or repo_root in path.parents:
        raise PermissionError(f"Refusing to write text-bearing data inside the repo: {path}")
    return path


def git_toplevel(start="."):
    return Path(
        subprocess.run(
            ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    )


def fingerprint(text):
    """Commit-safe identifier for a text (no text is stored)."""
    return hashlib.sha256(" ".join(str(text).split()).lower().encode("utf-8")).hexdigest()


def largest_remainder(weights, total):
    """Integer allocation of `total` proportional to `weights` (dict), deterministic ties."""
    keys = sorted(weights)
    w = np.array([float(weights[k]) for k in keys])
    if w.sum() <= 0:
        raise ValueError("weights must be positive")
    raw = w / w.sum() * total
    base = np.floor(raw).astype(int)
    order = sorted(range(len(keys)), key=lambda i: (-(raw[i] - base[i]), keys[i]))
    for i in order[: total - base.sum()]:
        base[i] += 1
    return {k: int(v) for k, v in zip(keys, base)}


def feasible_counts(cell_weights, available, total, fallback):
    """Integer cell counts summing to `total`, proportional to cell_weights, capped at
    `available`; a capped cell's deficit moves to fallback[cell] (preregistered rule).

    Returns (counts, moved) where moved maps cell -> rows reassigned away from it.
    """
    counts = largest_remainder(cell_weights, total)
    moved = {}
    for _ in range(len(counts) + 1):
        short = {c: n - available.get(c, 0) for c, n in counts.items() if n > available.get(c, 0)}
        if not short:
            return counts, moved
        for cell, deficit in short.items():
            target = fallback.get(cell)
            if target is None or target == cell:
                raise ValueError(f"Cell {cell} short by {deficit} with no fallback")
            counts[cell] -= deficit
            counts[target] = counts.get(target, 0) + deficit
            moved[cell] = moved.get(cell, 0) + deficit
    raise ValueError("Fallback allocation did not converge")


def sample_pool(candidates_by_cell, cell_weights, seed=POOL_SEED, n_train=N_TRAIN, n_val=N_VAL):
    """Draw n_train + n_val rows with cell composition proportional to cell_weights.

    Returns (train_rows, val_rows). Each cell is split train/val proportionally, so both
    splits mirror the target composition. Raises if a cell has too few candidates.
    """
    total = largest_remainder(cell_weights, n_train + n_val)
    train_alloc = largest_remainder(total, n_train)
    rng = np.random.default_rng(seed)
    train, val = [], []
    for cell in sorted(total):
        pool = sorted(candidates_by_cell.get(cell, []), key=lambda r: fingerprint(r["text"]))
        need = total[cell]
        if len(pool) < need:
            raise ValueError(f"Cell {cell}: need {need} candidates, have {len(pool)}")
        chosen = [pool[i] for i in rng.permutation(len(pool))[:need]]
        k = train_alloc[cell]
        train += [dict(r, cell=cell) for r in chosen[:k]]
        val += [dict(r, cell=cell) for r in chosen[k:]]
    return train, val


def semantic_keep_mask(candidates, references, threshold=SEMANTIC_THRESHOLD, batch=500):
    """True where a candidate's max char_wb(3,4) TF-IDF cosine to every reference is below
    threshold. Mirrors PIDS-Bench's semantic dedup representation, applied across sets."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    if not candidates or not references:
        return np.ones(len(candidates), dtype=bool)
    vec = TfidfVectorizer(
        analyzer="char_wb", ngram_range=(3, 4), min_df=1, max_features=12000, sublinear_tf=True
    )
    vec.fit(list(references) + list(candidates))
    ref = vec.transform(references)
    keep = np.ones(len(candidates), dtype=bool)
    for start in range(0, len(candidates), batch):
        sims = cosine_similarity(vec.transform(candidates[start : start + batch]), ref)
        keep[start : start + batch] = sims.max(axis=1) < threshold
    return keep


def to_hardneg_frame_rows(rows, arm, split):
    """PIDS-Bench hard_negative_{train,val}.csv schema, all label 0."""
    return [
        {
            "text": r["text"],
            "label": 0,
            "source_type": f"study3_{arm}",
            "parent_seed_id": "s3_" + fingerprint(r["text"])[:16],
            "split": split,
            "hardneg_category": r["cell"],
            "source": r["source"],
            "attack_type": "none",
            "language": "en",
            "obfuscation": "none",
        }
        for r in rows
    ]


# ------------------------------- metrics and inference -------------------------------


def rate(flags, weights=None):
    flags = np.asarray(flags, dtype=float)
    if weights is None:
        return float(flags.mean()) if len(flags) else float("nan")
    w = np.atleast_2d(weights)
    return (w * flags).sum(axis=1) / w.sum(axis=1)


def joint_bootstrap_diff(flags_a, flags_b, groups, reps, rng):
    """Paired difference of seed-mean rates, jointly resampling row groups and seeds.

    flags_a, flags_b: arrays (n_seeds, n_rows) of 0/1 outcomes on the same rows, seeds
    aligned. Returns replicate differences (reps,).
    """
    flags_a, flags_b = np.asarray(flags_a, float), np.asarray(flags_b, float)
    n_seeds = flags_a.shape[0]
    unique, index = np.unique(groups, return_inverse=True)
    out = np.empty(reps)
    for start in range(0, reps, 500):
        m = min(500, reps - start)
        draws = rng.multinomial(len(unique), np.full(len(unique), 1 / len(unique)), size=m)
        w = draws[:, index].astype(float)
        s = rng.integers(0, n_seeds, size=(m, n_seeds))
        ra = (w @ flags_a.T) / w.sum(axis=1, keepdims=True)  # (m, n_seeds)
        rb = (w @ flags_b.T) / w.sum(axis=1, keepdims=True)
        d = ra - rb
        out[start : start + m] = np.take_along_axis(d, s, axis=1).mean(axis=1)
    return out


def percentile_interval(values, level):
    values = np.asarray(values, float)
    values = values[np.isfinite(values)]
    tail = (1 - level) / 2 * 100
    return [float(np.percentile(values, tail)), float(np.percentile(values, 100 - tail))]


def f1_at(scores, labels, tau):
    pred = np.asarray(scores) >= tau
    labels = np.asarray(labels).astype(bool)
    tp = int((pred & labels).sum())
    denom = int(pred.sum()) + int(labels.sum())
    return 2 * tp / denom if denom else 0.0


def sweep_frontier(test_scores, test_labels, benign_scores, f1_min=0.95, fpr_max=0.10):
    """PIDS-Bench's frontier criterion (p. 13): does ANY tau on the 0.002 grid give test
    F1 >= f1_min and benign FPR <= fpr_max together? Oracle over tau, descriptive only."""
    benign_scores = np.asarray(benign_scores)
    for tau in np.arange(0.0, 1.001, 0.002):
        if (benign_scores >= tau).mean() <= fpr_max and f1_at(
            test_scores, test_labels, tau
        ) >= f1_min:
            return True
    return False


def seed_t_interval(diffs, level):
    """Sensitivity interval: Student-t over per-seed differences (df = seeds - 1).

    Ignores row sampling variance; complements the joint bootstrap, which understates
    seed variance when only 5 seeds are resampled."""
    from scipy import stats

    diffs = np.asarray(diffs, float)
    half = stats.t.ppf(0.5 + level / 2, len(diffs) - 1) * diffs.std(ddof=1) / np.sqrt(len(diffs))
    return [float(diffs.mean() - half), float(diffs.mean() + half)]


def named_rng(name):
    """Independent, reproducible stream per analysis, so no interval depends on which
    other analyses ran first."""
    digest = int(hashlib.sha256(name.encode("utf-8")).hexdigest()[:8], 16)
    return np.random.default_rng([BOOTSTRAP_SEED, digest])


def decide(boot_ci, t_ci, complete):
    """Preregistered decision: established only if BOTH 97.5% intervals exclude 0 and all
    primary arms are complete; 'fragile' if exactly one interval excludes 0."""
    if not complete:
        return {
            "status": "incomplete",
            "established_reduction": None,
            "established_increase": None,
            "fragile": None,
            "reduction_beyond_5_points": None,
        }
    below = [boot_ci[1] < 0, t_ci[1] < 0]
    above = [boot_ci[0] > 0, t_ci[0] > 0]
    return {
        "status": "complete",
        "established_reduction": all(below),
        "established_increase": all(above),
        "fragile": any(below) != all(below) or any(above) != all(above),
        "reduction_beyond_5_points": boot_ci[1] < -0.05 and t_ci[1] < -0.05,
    }


def cross_containment_hits(candidates, references):
    """Indices of candidates with word 5-gram containment >= 0.5 (min 3 shared shingles)
    to any reference: the grouping definition used for inference, applied as a filter."""
    from injection_lab.pools import containment_edges

    n = len(candidates)
    edges = containment_edges(list(candidates) + list(references))
    return {i for pair in edges for i in pair if i < n and any(j >= n for j in pair)}
