"""Equal-label-budget adaptation study: threshold-only vs generic vs matched retraining.

Everything here is fixed by docs/PREREGISTRATION.md. Models see only S-train, the
generic bank, and revealed target-bank benign rows; thresholds see only S-cal benign rows
or the same revealed target rows. Evaluation rows are scored once and never tuned on.
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline

SEEDS = (17, 29, 42, 71, 101)
BUDGETS = (0, 25, 50, 100, 200)
CONFIRMATORY_BUDGET = 200
ALPHA_FPR = 0.01
ADDED_WEIGHTS = (1.0, 20.0)  # 1.0 primary; 20.0 prespecified dilution sensitivity
EVAL_PARTITIONS = ("S-test", "T-eval", "U-eval")


def build_detector():
    """Unchanged legacy 'combined' recipe; no hyperparameter search."""
    return Pipeline(
        [
            (
                "features",
                FeatureUnion(
                    [
                        (
                            "word",
                            TfidfVectorizer(
                                ngram_range=(1, 2), sublinear_tf=True, max_features=30000
                            ),
                        ),
                        (
                            "char",
                            TfidfVectorizer(
                                analyzer="char_wb",
                                ngram_range=(3, 5),
                                sublinear_tf=True,
                                max_features=50000,
                            ),
                        ),
                    ]
                ),
            ),
            (
                "classifier",
                LogisticRegression(class_weight="balanced", max_iter=1000, random_state=0),
            ),
        ]
    )


def fit_detector(train_rows, added_rows=(), added_weight=1.0):
    texts = [r["text"] for r in train_rows] + [r["text"] for r in added_rows]
    labels = [r["label"] for r in train_rows] + [r["label"] for r in added_rows]
    weights = np.r_[np.ones(len(train_rows)), np.full(len(added_rows), added_weight)]
    model = build_detector()
    model.fit(texts, labels, classifier__sample_weight=weights)
    return model


def benign_threshold(benign_scores, alpha=ALPHA_FPR):
    """Lowest threshold t with mean(benign >= t) <= alpha, over observed benign scores.

    With n benign scores at most floor(alpha*n) may reach t; for n < 1/alpha this is just
    above the maximum score.
    """
    scores = np.sort(np.asarray(benign_scores, dtype=float))[::-1]
    if not len(scores):
        raise ValueError("Threshold needs at least one benign score")
    allowed = int(np.floor(alpha * len(scores) + 1e-12))
    return float(np.nextafter(scores[allowed], np.inf)) if allowed < len(scores) else 0.0


def nested_subsets(rows, seed, budgets=BUDGETS):
    """Seed-specific random order; each budget is a prefix, so subsets are nested."""
    order = np.random.default_rng(seed).permutation(len(rows))
    ranked = [rows[i] for i in order]
    return {b: ranked[:b] for b in budgets}


def arm_specs():
    """(arm, budget, seed, model key, threshold rule). B=0 cells alias the frozen model."""
    specs = [("frozen", 0, None, "source", "S-cal")]
    for seed in SEEDS:
        for budget in BUDGETS:
            if budget == 0:
                continue
            specs.append(("threshold_only", budget, seed, "source", "T-bank"))
            for weight in ADDED_WEIGHTS:
                suffix = "" if weight == 1.0 else f"_w{int(weight)}"
                generic = f"generic{suffix}:{seed}:{budget}"
                matched = f"matched{suffix}:{seed}:{budget}"
                specs.append((f"generic{suffix}", budget, seed, generic, "S-cal"))
                specs.append((f"matched{suffix}", budget, seed, matched, "S-cal"))
                specs.append((f"matched{suffix}+threshold", budget, seed, matched, "T-bank"))
    return specs


# ---------- weighted metrics used identically for point estimates and bootstrap ----------


class RankedScores:
    """Rows sorted by descending score with tie blocks, for weighted ROC queries."""

    def __init__(self, scores, labels):
        scores = np.asarray(scores, dtype=float)
        self.labels = np.asarray(labels, dtype=int)
        self.order = np.argsort(-scores, kind="stable")
        ordered = scores[self.order]
        # Index of the last row of each tie block in sorted order.
        self.block_end = np.r_[np.nonzero(np.diff(ordered))[0], len(ordered) - 1]
        self.pos = self.labels[self.order] == 1
        self.scores = scores

    def recall_at_fpr(self, weights, alpha=ALPHA_FPR):
        """Largest empirical recall with FPR <= alpha. weights: (reps, n) or (n,)."""
        w = np.atleast_2d(weights)[:, self.order]
        cum_pos = np.cumsum(w * self.pos, axis=1)[:, self.block_end]
        cum_neg = np.cumsum(w * ~self.pos, axis=1)[:, self.block_end]
        total_pos, total_neg = cum_pos[:, -1:], cum_neg[:, -1:]
        with np.errstate(invalid="ignore", divide="ignore"):
            fpr = cum_neg / total_neg
            recall = cum_pos / total_pos
        recall = np.where(fpr <= alpha + 1e-12, recall, 0.0)
        result = recall.max(axis=1)
        result[(total_pos[:, 0] == 0) | (total_neg[:, 0] == 0)] = np.nan
        return result if np.ndim(weights) == 2 else float(result[0])


def operating_point(scores, labels, threshold, weights):
    """Weighted recall and FPR at a fixed threshold. weights: (reps, n) or (n,)."""
    flagged = np.asarray(scores) >= threshold
    labels = np.asarray(labels)
    w = np.atleast_2d(weights)
    pos, neg = labels == 1, labels == 0
    with np.errstate(invalid="ignore", divide="ignore"):
        recall = (w[:, pos & flagged].sum(1)) / w[:, pos].sum(1)
        fpr = (w[:, neg & flagged].sum(1)) / w[:, neg].sum(1)
    if np.ndim(weights) == 1:
        return float(recall[0]), float(fpr[0])
    return recall, fpr


def group_weights(groups, reps, rng):
    """Cluster bootstrap: each group drawn with replacement; rows inherit the group count."""
    unique, index = np.unique(groups, return_inverse=True)
    draws = rng.multinomial(len(unique), np.full(len(unique), 1 / len(unique)), size=reps)
    return draws[:, index].astype(float)


def seed_draws(reps, rng, seeds=SEEDS):
    return rng.integers(0, len(seeds), size=(reps, len(seeds)))


def percentile_interval(values, level):
    values = np.asarray(values, dtype=float)
    values = values[~np.isnan(values)]
    tail = (1 - level) / 2 * 100
    return [float(np.percentile(values, tail)), float(np.percentile(values, 100 - tail))]
