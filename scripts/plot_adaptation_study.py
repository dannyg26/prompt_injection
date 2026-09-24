"""Presentation-only figure from results/study/results.json (no new analysis)."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RESULTS = Path("results/study/results.json")
OUT = Path("paper/figures/target_learning_curves.png")
# Reference categorical slots 1-4 (validated adjacent-pair palette), fixed per arm.
ARMS = {
    "threshold_only": ("Threshold only", "#2a78d6", "o"),
    "generic": ("Generic retraining", "#eb6834", "s"),
    "matched": ("Matched retraining", "#1baf7a", "D"),
    "matched+threshold": ("Matched + threshold", "#eda100", "^"),
}
PANELS = (
    ("recall_at_1pct_fpr", "Recall at 1% FPR (evaluation ROC)"),
    ("operational_recall", "Recall at deployed threshold"),
    ("operational_fpr", "FPR at deployed threshold"),
)


def main():
    report = json.loads(RESULTS.read_text(encoding="utf-8"))
    rows = [d for d in report["descriptive"] if d["set"] == "T"]
    budgets = report["design"]["budgets"]
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), constrained_layout=True)
    for ax, (metric, title) in zip(axes, PANELS):
        frozen = next(d for d in rows if d["arm"] == "frozen" and d["metric"] == metric)
        for arm, (label, color, marker) in ARMS.items():
            points = [frozen] + [
                next(d for d in rows if (d["arm"], d["budget"], d["metric"]) == (arm, b, metric))
                for b in budgets[1:]
            ]
            y = [100 * d["estimate_seed_mean"] for d in points]
            low = [100 * d["ci95"][0] for d in points]
            high = [100 * d["ci95"][1] for d in points]
            ax.fill_between(budgets, low, high, color=color, alpha=0.08, linewidth=0)
            ax.plot(budgets, y, color=color, linewidth=2, marker=marker, markersize=6, label=label)
        if metric == "operational_fpr":
            ax.axhline(1.0, color="#52514e", linewidth=1, linestyle="--")
            ax.annotate(
                "1% target",
                (budgets[0], 1.0),
                textcoords="offset points",
                xytext=(2, -11),
                ha="left",
                fontsize=8,
                color="#52514e",
            )
        ax.set_title(title, fontsize=10, loc="left")
        ax.set_xlabel("Revealed target benign labels (B)")
        ax.set_ylabel("Percent")
        ax.set_xticks(budgets)
        ax.set_ylim(bottom=0)
        ax.grid(axis="y", color="#e4e3df", linewidth=0.8)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].legend(frameon=False, fontsize=8)
    fig.suptitle(
        "Target domain (TaskTracker): seed mean, 95% group/seed bootstrap band. "
        "Matched and matched + threshold share one model, so their ROC recall coincides.",
        fontsize=11,
        x=0.01,
        ha="left",
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=160)
    print(OUT)


if __name__ == "__main__":
    main()
