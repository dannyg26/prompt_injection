"""Study 3 sensitivity planning (no data, no model): minimum detectable FPR reduction.

Inputs are PIDS-Bench's published values (docs/literature/pidsbench-2026.md): baseline
external hard-benign FPR 0.3144 with seed SD 0.0525 over 5 seeds, on 872 rows. These are
planning assumptions, not results of this project.
"""

import json
import sys
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from injection_lab.data import write_json  # noqa: E402

P0, SEED_SD, N_ROWS, ALPHA, POWER = 0.3144, 0.0525, 872, 0.025, 0.80


def mde(n_seeds, seed_corr, row_design_effect=2.0):
    """Normal and seed-t minimum detectable reduction for the paired seed-mean difference.

    Seed component: 2 (1 - seed_corr) SD^2 / n_seeds (seed_corr = correlation of the two
    arms' per-seed rates; arms train on different data, so 0 is the cautious case).
    Row component: rows are shared by all seeds and both arms, so it is NOT divided by
    n_seeds; 2 p (1 - p) deff / N treats the two arms' row errors as independent, which
    is conservative because paired rows are positively correlated.
    """
    seed_var = 2 * (1 - seed_corr) * SEED_SD**2 / n_seeds
    row_var = 2 * P0 * (1 - P0) * row_design_effect / N_ROWS
    se = float(np.sqrt(seed_var + row_var))
    z = stats.norm.ppf(1 - ALPHA / 2) + stats.norm.ppf(POWER)
    t = stats.t.ppf(1 - ALPHA / 2, n_seeds - 1) + stats.t.ppf(POWER, n_seeds - 1)
    return {
        "se_difference": se,
        "mde_normal": z * se,
        "mde_seed_t": t * se,
        "true_reduction_needed_for_upper_bound_below_minus_0.05_seed_t": t * se + 0.05,
    }


plan = {
    "assumptions": {
        "baseline_ext_fpr": P0,
        "seed_sd": SEED_SD,
        "n_external_rows": N_ROWS,
        "row_design_effect": 2.0,
        "two_sided_alpha_per_contrast": ALPHA,
        "power": POWER,
        "source": "PIDS-Bench published values; planning inputs, not measured here",
    },
    "note": "Decisions require both intervals, so the seed-t column is the binding one.",
    "by_seed_correlation": {str(r): {str(n): mde(n, r) for n in (3, 5)} for r in (0.0, 0.5)},
}
write_json(Path("results/study3/power_planning.json"), plan)
print(json.dumps(plan["by_seed_correlation"], indent=1))
