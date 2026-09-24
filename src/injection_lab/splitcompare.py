"""Row-random vs template-group splits: inflation and design effects (study 2).

Fixed by docs/PREREGISTRATION_LEAKAGE.md. Pure functions here; the runner lives in
scripts/run_split_comparison.py and is gated on owner approval.
"""

import numpy as np
from scipy import stats
from sklearn.metrics import roc_auc_score

from .adaptation import ALPHA_FPR, RankedScores
from .pools import allocate

REPEATS = 20
TEST_FRACTION = 0.3
SPLIT_SEED_BASE = 31000
ATTACK_SOURCES = ("hackaprompt-dataset", "jailbreak-classification", "TaskTracker", "BIPIA")


def row_split(rows, seed, test_fraction=TEST_FRACTION):
    """Random rows to test, stratified by label; ignores groups (the common practice)."""
    rng = np.random.default_rng(seed)
    test = np.zeros(len(rows), dtype=bool)
    labels = np.array([r["label"] for r in rows])
    for label in (0, 1):
        index = np.nonzero(labels == label)[0]
        chosen = rng.choice(index, size=int(round(test_fraction * len(index))), replace=False)
        test[chosen] = True
    return test


def group_split(rows, seed, test_fraction=TEST_FRACTION):
    """Whole groups to test, stratified by whether a group contains a positive."""
    info = {}
    for row in rows:
        has_pos, size = info.get(row["group"], (False, 0))
        info[row["group"]] = (has_pos or row["label"] == 1, size + 1)
    fractions = {"train": 1 - test_fraction, "test": test_fraction}
    assignment = allocate(info, fractions, np.random.default_rng(seed))
    return np.array([assignment[r["group"]] == "test" for r in rows])


def recall_at_fpr(scores, labels, mask_positive, alpha=ALPHA_FPR):
    """Recall on the positives selected by mask_positive, at the evaluation-ROC cutoff set
    by all benign test rows (FPR <= alpha). Returns (recall, cutoff)."""
    keep = (labels == 0) | mask_positive
    ranked = RankedScores(scores[keep], labels[keep])
    recall = ranked.recall_at_fpr(np.ones(keep.sum()), alpha)
    benign = np.sort(scores[labels == 0])[::-1]
    allowed = int(np.floor(alpha * len(benign) + 1e-12))
    cutoff = float(np.nextafter(benign[allowed], np.inf)) if allowed < len(benign) else 0.0
    return recall, cutoff


def evaluate_split(scores, rows, test_mask, sources=ATTACK_SOURCES):
    labels = np.array([r["label"] for r in rows])[test_mask]
    source = np.array([r["source"] for r in rows])[test_mask]
    groups = np.array([r["group"] for r in rows])[test_mask]
    s = scores[test_mask]
    result = {"auroc": float(roc_auc_score(labels, s))}
    pooled, cutoff = recall_at_fpr(s, labels, labels == 1)
    result["recall_at_1pct_fpr|pooled"] = pooled
    for name in sources:
        positives = (labels == 1) & (source == name)
        if positives.sum() == 0:
            result[f"recall_at_1pct_fpr|{name}"] = float("nan")
            result[f"design_effect|{name}"] = float("nan")
            continue
        flagged = (s >= cutoff) & positives
        result[f"recall_at_1pct_fpr|{name}"] = float(flagged.sum() / positives.sum())
        result[f"design_effect|{name}"] = design_effect(flagged[positives], groups[positives])
        result[f"groups|{name}"] = int(len(set(groups[positives])))
        result[f"positives|{name}"] = int(positives.sum())
    return result


def design_effect(successes, groups):
    """Cluster (ratio-estimator) variance of a proportion over its binomial variance.

    1 means groups behave like independent rows; large values mean example-level intervals
    are too narrow. NaN when undefined (one group, or p in {0, 1}).
    """
    successes = np.asarray(successes, dtype=float)
    n = len(successes)
    p = successes.mean()
    unique, index = np.unique(groups, return_inverse=True)
    g = len(unique)
    if g < 2 or p in (0.0, 1.0):
        return float("nan")
    y = np.bincount(index, weights=successes)
    m = np.bincount(index)
    cluster_var = g / (g - 1) * np.sum((y - p * m) ** 2) / n**2
    return float(cluster_var / (p * (1 - p) / n))


def nadeau_bengio_interval(differences, n_train, n_test, level=0.95):
    """Corrected resampled-t interval for a mean over overlapping repeated splits."""
    d = np.asarray(differences, dtype=float)
    d = d[~np.isnan(d)]
    j = len(d)
    if j < 2:
        return [float("nan"), float("nan")]
    variance = (1 / j + n_test / n_train) * d.var(ddof=1)
    half = stats.t.ppf(0.5 + level / 2, j - 1) * np.sqrt(variance)
    return [float(d.mean() - half), float(d.mean() + half)]


def random_group_split(rows, seed, test_fraction=TEST_FRACTION):
    """Amendment 2 splitter for Part B: groups in uniformly random order, each placed in test
    while the stratum's test share is below target. Unlike largest-first allocation, which
    puts large template groups on the same side in every repeat, every group's side varies
    across seeds."""
    rng = np.random.default_rng(seed)
    info = {}
    for row in rows:
        has_pos, size = info.get(row["group"], (False, 0))
        info[row["group"]] = (has_pos or row["label"] == 1, size + 1)
    in_test = set()
    for has_positive in (True, False):
        subset = sorted(g for g, (pos, _) in info.items() if pos == has_positive)
        total = sum(info[g][1] for g in subset)
        filled = 0
        for index in rng.permutation(len(subset)):
            gid = subset[index]
            if filled < test_fraction * total:
                in_test.add(gid)
                filled += info[gid][1]
    return np.array([r["group"] in in_test for r in rows])
