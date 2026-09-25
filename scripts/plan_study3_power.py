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


def mde(n_seeds, rho_design_effect=2.0):
    # Per-arm variance of the seed-mean FPR: seed component + row component. Arms are
    # trained on different data, so seed pairing is assumed to remove no variance.
    row_var = P0 * (1 - P0) / N_ROWS * rho_design_effect / n_seeds  # conservative
    se_diff = np.sqrt(2 * (SEED_SD**2 / n_seeds + row_var))
    z = stats.norm.ppf(1 - ALPHA / 2) + stats.norm.ppf(POWER)
    t = stats.t.ppf(1 - ALPHA / 2, n_seeds - 1) + stats.t.ppf(POWER, n_seeds - 1)
    return {"se_difference": se_diff, "mde_normal": z * se_diff, "mde_seed_t": t * se_diff}


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
    "by_seeds": {n: mde(n) for n in (3, 4, 5)},
}
write_json(Path("results/study3/power_planning.json"), plan)
print(json.dumps(plan["by_seeds"], indent=1))
