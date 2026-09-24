import numpy as np
import pytest

from injection_lab.adaptation import RankedScores
from injection_lab.splitcompare import (
    design_effect,
    evaluate_split,
    group_split,
    nadeau_bengio_interval,
    recall_at_fpr,
    row_split,
)


def rows_fixture(n=3000, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n):
        label = int(rng.random() < 0.3)
        source = "hackaprompt-dataset" if label and i % 2 else ("BIPIA" if label else "chat")
        rows.append({"label": label, "source": source, "group": f"g{i // 3}", "text": str(i)})
    return rows


def test_row_split_ignores_groups_and_group_split_respects_them():
    rows = rows_fixture()
    row_mask, group_mask = row_split(rows, 1), group_split(rows, 1)
    assert abs(row_mask.mean() - 0.3) < 0.01 and abs(group_mask.mean() - 0.3) < 0.03
    groups = np.array([r["group"] for r in rows])
    straddle = lambda mask: sum(  # noqa: E731
        len(set(mask[groups == g])) > 1 for g in set(groups)
    )
    assert straddle(group_mask) == 0 and straddle(row_mask) > 0


def test_design_effect_near_one_for_independent_rows_and_large_for_clusters():
    rng = np.random.default_rng(2)
    independent = rng.random(5000) < 0.4
    assert design_effect(independent, np.arange(5000)) == pytest.approx(1, abs=0.1)
    clustered = np.repeat(rng.random(50) < 0.4, 100)  # 50 groups of identical outcomes
    assert design_effect(clustered, np.repeat(np.arange(50), 100)) > 50
    assert np.isnan(design_effect(np.ones(10), np.arange(10)))


def test_nadeau_bengio_is_wider_than_naive_t():
    d = np.random.default_rng(3).normal(0.05, 0.02, 20)
    lo, hi = nadeau_bengio_interval(d, n_train=7000, n_test=3000)
    naive = 2.093 * d.std(ddof=1) / np.sqrt(20)
    assert lo < d.mean() < hi and (hi - lo) / 2 > naive


def test_per_source_recall_matches_ranked_roc():
    rng = np.random.default_rng(4)
    labels = rng.integers(0, 2, 2000)
    scores = rng.normal(labels, 1)
    pooled, _ = recall_at_fpr(scores, labels, labels == 1)
    assert pooled == pytest.approx(RankedScores(scores, labels).recall_at_fpr(np.ones(2000)))


def test_evaluate_split_reports_each_attack_source():
    rows = rows_fixture(600)
    rng = np.random.default_rng(5)
    scores = np.array([r["label"] + rng.normal(0, 0.5) for r in rows])
    result = evaluate_split(scores, rows, np.ones(len(rows), dtype=bool))
    assert 0 <= result["recall_at_1pct_fpr|BIPIA"] <= 1
    assert result["groups|hackaprompt-dataset"] > 1
