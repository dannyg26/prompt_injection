"""Check planning mathematics against independent finite enumeration."""

import numpy as np
import pytest
from scipy.stats import binom, binomtest

from scripts.power_analysis import exact_power, roc_planning, wilson_at_rate


def test_exact_power_agrees_with_enumerated_binomial_tests():
    n, delta, q, alpha = 12, 0.15, 0.4, 0.05
    expected = 0.0
    for d in range(1, n + 1):
        for k in range(d + 1):
            if binomtest(k, d, 0.5).pvalue <= alpha:
                expected += binom.pmf(d, n, q) * binom.pmf(k, d, (q + delta) / (2 * q))
    assert exact_power(n, delta, q, alpha) == pytest.approx(expected, abs=1e-12)


def test_one_direction_discordance_needs_six_discordant_pairs():
    assert exact_power(100, 0.1, 0.1) == pytest.approx(binom.sf(5, 100, 0.1), abs=1e-12)


def test_low_fpr_precision_is_not_certification():
    low, high = wilson_at_rate(1500)
    assert low < 0.01 < high
    assert high > 0.015


def test_roc_uncertainty_requires_more_negatives_for_small_effect():
    small = roc_planning(0.02, 0.9)
    large = roc_planning(0.05, 0.9)
    assert small["n_negative_80"] > 30000
    assert large["n_negative_80"] < 5000
    assert np.isfinite(small["negative_variance_coefficient"])
