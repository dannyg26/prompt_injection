"""Analytical planning only: no detector fitting, predictions, or outcome selection."""

import json
import math
from pathlib import Path

import numpy as np
from scipy.integrate import quad
from scipy.stats import binom, norm


def approximate_n(delta, discordance, power=0.8, alpha=0.05):
    if not 0 < delta <= discordance <= 1:
        raise ValueError("Require 0 < delta <= discordance <= 1")
    return math.ceil(
        (
            norm.ppf(1 - alpha / 2) * math.sqrt(discordance)
            + norm.ppf(power) * math.sqrt(discordance - delta**2)
        )
        ** 2
        / delta**2
    )


def exact_power(n, delta, discordance, alpha=0.05):
    """Unconditional power of the exact conditional, two-sided McNemar test.

    Sum over D~Binomial(n,q), then B|D~Binomial(D,(q+delta)/(2q)).
    Omitting binomial D tails below 1e-13 each bounds numerical omission.
    """
    lo, hi = binom.ppf([1e-13, 1 - 1e-13], n, discordance).astype(int)
    d = np.arange(lo, hi + 1)
    critical = binom.ppf(alpha / 2, d, 0.5).astype(int)
    critical -= binom.cdf(critical, d, 0.5) > alpha / 2
    conditional = (discordance + delta) / (2 * discordance)
    rejection = binom.cdf(critical, d, conditional) + binom.sf(d - critical - 1, d, conditional)
    return float(np.dot(binom.pmf(d, n, discordance), rejection))


def planned_n(delta, discordance, power, alpha):
    """A verified sufficient rounded N, not a claimed exact minimum."""
    start = approximate_n(delta, discordance, power, alpha)
    n = int(math.ceil(start / 25) * 25)
    while exact_power(n, delta, discordance, alpha) < power:
        n += 25
    return n


def wilson_at_rate(n, p=0.01):
    z = norm.ppf(0.975)
    den = 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [center - half, center + half]


def joint_survival(a, b, rho):
    return quad(
        lambda x: norm.pdf(x) * norm.cdf((rho * x - b) / math.sqrt(1 - rho**2)),
        a,
        12,
        epsabs=1e-12,
    )[0]


def roc_planning(delta, rho, n_positive=6500, alpha=0.025):
    """Illustrative binormal delta-method calculation including ROC cutoff error."""
    fpr = 0.01
    cutoff = norm.ppf(1 - fpr)
    a, b = -norm.ppf(0.8), -norm.ppf(0.8 + delta)
    discordance = 1.6 + delta - 2 * joint_survival(a, b, rho)
    la, lb = norm.pdf(a) / norm.pdf(cutoff), norm.pdf(b) / norm.pdf(cutoff)
    negative_coefficient = (la**2 + lb**2) * fpr * (1 - fpr) - 2 * la * lb * (
        joint_survival(cutoff, cutoff, rho) - fpr**2
    )
    result = {
        "delta": delta,
        "score_correlation_in_each_class": rho,
        "baseline_recall": 0.8,
        "n_positive": n_positive,
        "alpha": alpha,
        "q_positive": discordance,
        "negative_variance_coefficient": negative_coefficient,
    }
    for power in (0.8, 0.9):
        variance_budget = (delta / (norm.ppf(1 - alpha / 2) + norm.ppf(power))) ** 2
        remaining = variance_budget - (discordance - delta**2) / n_positive
        result[f"n_negative_{int(power * 100)}"] = (
            math.ceil(negative_coefficient / remaining) if remaining > 0 else None
        )
    return result


def main():
    scenarios = [
        ("recall", delta, q) for delta in (0.02, 0.03, 0.05) for q in (0.05, 0.10, 0.20)
    ] + [
        ("FPR 3% to 1%", 0.02, 0.04),
        ("FPR 6% to 1%", 0.05, 0.07),
        ("FPR 1% to 0.5%", 0.005, 0.015),
    ]
    rows = []
    for name, delta, q in scenarios:
        for alpha in (0.05, 0.025):
            entry = {"endpoint": name, "delta": delta, "discordance": q, "alpha": alpha}
            for power in (0.8, 0.9):
                n = planned_n(delta, q, power, alpha)
                entry[f"n_{int(power * 100)}"] = n
                entry[f"analytical_power_{int(power * 100)}"] = exact_power(n, delta, q, alpha)
            rows.append(entry)
    out = Path("results/planning")
    out.mkdir(parents=True, exist_ok=True)
    report = {
        "status": "HYPOTHETICAL DESIGN CALCULATIONS, not experimental metrics",
        "seed": None,
        "seed_reason": "Deterministic analytical enumeration; no Monte Carlo used",
        "ci_reason": "Power is a calculated probability under assumptions, not an estimate",
        "sample_size_unit": "independent paired positive OR negative evaluation items",
        "rounding": "sufficient N rounded upward in 25-item steps; not exact minimum",
        "rows": rows,
        "fpr_precision": [
            {"n_negative": n, "hypothetical_fpr": 0.01, "wilson95": wilson_at_rate(n)}
            for n in (1500, 2000, 5000, 10000)
        ],
        "normal_n_for_halfwidth": {
            str(h): math.ceil(norm.ppf(0.975) ** 2 * 0.01 * 0.99 / h**2)
            for h in (0.005, 0.003, 0.002)
        },
        "illustrative_roc_cutoff_uncertainty": [
            roc_planning(delta, rho) for delta in (0.02, 0.03, 0.05) for rho in (0.5, 0.9, 0.99)
        ],
        "limitations": [
            "Paired fixed-threshold outcomes, conditional on trained models and calibration",
            "Not power for test-set-selected ROC thresholds or the multi-seed treatment effect",
            "Unknown discordance, clustering and label error require sensitivity analysis",
            "A 2pp decrease from a 1% baseline is impossible; 3%->1% is a different question",
        ],
    }
    (out / "power.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
