"""Prespecified analysis of scored adaptation-study models (see docs/PREREGISTRATION.md)."""

import numpy as np

from .adaptation import (
    ALPHA_FPR,
    BUDGETS,
    CONFIRMATORY_BUDGET,
    SEEDS,
    RankedScores,
    arm_specs,
    benign_threshold,
    group_weights,
    nested_subsets,
    operating_point,
    percentile_interval,
    seed_draws,
)

BOOTSTRAP_SEED = 20260923
CONFIRMATORY_REPS = 10000
DESCRIPTIVE_REPS = 2000
BATCH = 250
CONFIRMATORY = (
    ("matched", "threshold_only"),  # threshold-only keeps the frozen ranking
    ("matched", "generic"),
)


def eval_sets(rows):
    """Named evaluation sets: (row indices, has positives)."""
    sets = {
        "T": [i for i, r in enumerate(rows) if r["partition"] == "T-eval"],
        "S": [i for i, r in enumerate(rows) if r["partition"] == "S-test"],
    }
    for source in ("BIPIA", "NotInject", "WildGuard"):
        sets[f"U-{source}"] = [
            i for i, r in enumerate(rows) if r["partition"] == "U-eval" and r["source"] == source
        ]
    return {k: np.array(v) for k, v in sets.items() if v}


def thresholds(scores, rows, bank_order):
    """Deployed threshold for every arm/budget/seed cell, using only its allowed labels."""
    cal = np.array([i for i, r in enumerate(rows) if r["partition"] == "S-cal" and not r["label"]])
    result = {}
    for arm, budget, seed, key, rule in arm_specs():
        if rule == "S-cal":
            tau = benign_threshold(scores[key][cal])
        else:
            revealed = bank_order[seed][budget]
            tau = benign_threshold(scores[key][revealed])
        result[(arm, budget, seed)] = (key, tau)
    return result


def bank_orders(rows):
    """Revealed target-bank benign row indices for each seed and budget (nested)."""
    bank = [i for i, r in enumerate(rows) if r["partition"] == "T-bank" and r["label"] == 0]
    return {
        seed: {b: np.array(v, dtype=int) for b, v in nested_subsets(bank, seed).items()}
        for seed in SEEDS
    }


def cells(threshold_map):
    """Group seed-level cells into (arm, budget) -> list of (seed, model key, threshold)."""
    grouped = {}
    for (arm, budget, seed), (key, tau) in threshold_map.items():
        grouped.setdefault((arm, budget), []).append((seed, key, tau))
    # B=0 aliases: every arm at B=0 is the frozen source model with the source threshold.
    return grouped


_RANKED = {}


def ranked(scores, key, index, labels):
    cache_key = (key, index.tobytes())
    if cache_key not in _RANKED:
        if len(_RANKED) > 512:
            _RANKED.clear()
        _RANKED[cache_key] = RankedScores(scores[key][index], labels)
    return _RANKED[cache_key]


def metric_matrix(metric, members, scores, rows, index, weights):
    """(len(members), reps) metric values; weights is (reps, len(index))."""
    labels = np.array([rows[i]["label"] for i in index])
    out = []
    for _, key, tau in members:
        s = scores[key][index]
        if metric == "recall_at_1pct_fpr":
            out.append(ranked(scores, key, index, labels).recall_at_fpr(weights, ALPHA_FPR))
        else:
            recall, fpr = operating_point(s, labels, tau, weights)
            out.append(recall if metric == "operational_recall" else fpr)
    return np.array(out)


def summarize(values_by_seed, seed_index):
    """Seed-mean per replicate from resampled seed positions (single-member cells ignore)."""
    if values_by_seed.shape[0] == 1:
        return values_by_seed[0]
    return np.take_along_axis(values_by_seed, seed_index.T, axis=0).mean(axis=0)


def metrics_for(set_name, rows, index):
    labels = {rows[i]["label"] for i in index}
    if labels == {0}:
        return ("operational_fpr",)
    return ("recall_at_1pct_fpr", "operational_recall", "operational_fpr")


def analyze(rows, scores, reps=DESCRIPTIVE_REPS, confirmatory_reps=CONFIRMATORY_REPS):
    orders = bank_orders(rows)
    grouped = cells(thresholds(scores, rows, orders))
    sets = eval_sets(rows)
    groups = np.array([r["group"] for r in rows])
    report = {"descriptive": [], "confirmatory": [], "thresholds": []}
    for (arm, budget), members in sorted(grouped.items(), key=lambda x: (x[0][1], x[0][0])):
        for seed, key, tau in members:
            report["thresholds"].append(
                {"arm": arm, "budget": budget, "seed": seed, "model": key, "threshold": tau}
            )
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    for set_name, index in sets.items():
        unit = np.ones((1, len(index)))
        boot = {}
        seed_index = seed_draws(reps, rng)
        weights_batches = [
            group_weights(groups[index], min(BATCH, reps - start), rng)
            for start in range(0, reps, BATCH)
        ]
        for (arm, budget), members in grouped.items():
            for metric in metrics_for(set_name, rows, index):
                point_by_seed = metric_matrix(metric, members, scores, rows, index, unit)[:, 0]
                reps_by_seed = np.concatenate(
                    [
                        metric_matrix(metric, members, scores, rows, index, w)
                        for w in weights_batches
                    ],
                    axis=1,
                )
                boot[(arm, budget, metric)] = reps_by_seed
                report["descriptive"].append(
                    {
                        "set": set_name,
                        "arm": arm,
                        "budget": budget,
                        "metric": metric,
                        "estimate_seed_mean": float(np.nanmean(point_by_seed)),
                        "per_seed": {
                            str(seed if seed is not None else "none"): float(v)
                            for (seed, _, _), v in zip(members, point_by_seed)
                        },
                        "ci95": percentile_interval(summarize(reps_by_seed, seed_index), 0.95),
                        "n_rows": int(len(index)),
                        "n_positive": int(sum(rows[i]["label"] for i in index)),
                        "n_groups": int(len(set(groups[index]))),
                    }
                )
    # Confirmatory: target recall@1%FPR at B=200, 10,000 joint group/seed replicates.
    index = sets["T"]
    labels = np.array([rows[i]["label"] for i in index])
    crng = np.random.default_rng(BOOTSTRAP_SEED + 1)
    seed_index = seed_draws(confirmatory_reps, crng)
    diffs = {c: [] for c in CONFIRMATORY}
    points = {}
    for start in range(0, confirmatory_reps, BATCH):
        w = group_weights(groups[index], min(BATCH, confirmatory_reps - start), crng)
        for treat, control in CONFIRMATORY:
            a = _by_seed(grouped[(treat, CONFIRMATORY_BUDGET)], scores, index, labels, w)
            b = _by_seed(grouped[(control, CONFIRMATORY_BUDGET)], scores, index, labels, w)
            diffs[(treat, control)].append(a - b)
    unit = np.ones((1, len(index)))
    for treat, control in CONFIRMATORY:
        a = _by_seed(grouped[(treat, CONFIRMATORY_BUDGET)], scores, index, labels, unit)[:, 0]
        b = _by_seed(grouped[(control, CONFIRMATORY_BUDGET)], scores, index, labels, unit)[:, 0]
        points[(treat, control)] = a - b
    for (treat, control), chunks in diffs.items():
        by_seed = np.concatenate(chunks, axis=1)
        replicate = summarize(by_seed, seed_index)
        point = points[(treat, control)]
        report["confirmatory"].append(
            {
                "contrast": f"{treat} - {control}",
                "set": "T",
                "budget": CONFIRMATORY_BUDGET,
                "metric": "recall_at_1pct_fpr (difference, proportion)",
                "estimate_seed_mean": float(point.mean()),
                "per_seed": {str(s): float(v) for s, v in zip(SEEDS, point)},
                "ci97_5": percentile_interval(replicate, 0.975),
                "ci95": percentile_interval(replicate, 0.95),
                "undefined_replicates": int(np.isnan(replicate).sum()),
                "replicates": confirmatory_reps,
            }
        )
    report["design"] = {
        "seeds": list(SEEDS),
        "budgets": list(BUDGETS),
        "alpha_fpr": ALPHA_FPR,
        "bootstrap": (
            "percentile; joint resampling of evaluation groups (with replacement) and of the "
            "five adaptation seeds; operational thresholds held fixed; ROC cutoffs recomputed"
        ),
        "bootstrap_seed": BOOTSTRAP_SEED,
        "descriptive_reps": reps,
        "confirmatory_reps": confirmatory_reps,
    }
    return report


def _by_seed(members, scores, index, labels, weights):
    members = sorted(members, key=lambda m: SEEDS.index(m[0]))
    return np.array(
        [ranked(scores, key, index, labels).recall_at_fpr(weights) for _, key, _ in members]
    )
