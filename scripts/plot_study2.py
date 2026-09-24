"""Presentation-only Study 2 figure from results/leakage/split_comparison.json."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RESULTS = Path("results/leakage/split_comparison.json")
OUT = Path("paper/figures/study2_template_leakage.png")
BLUE, INK, MUTED = "#2a78d6", "#0b0b0b", "#52514e"
# Only sources whose interval is valid (varied test groups; see docs/STUDY2_RESULTS.md).
SOURCES = (
    ("TaskTracker", "TaskTracker"),
    ("BIPIA", "BIPIA"),
    ("jailbreak-classification", "jailbreak-\nclassification"),
)


def main():
    report = json.loads(RESULTS.read_text(encoding="utf-8"))
    fig, (left, right) = plt.subplots(
        1, 2, figsize=(12, 4.2), constrained_layout=True, gridspec_kw={"width_ratios": [1, 1.4]}
    )
    for y, (key, label) in enumerate(SOURCES):
        v = report["inflation"][f"recall_at_1pct_fpr|{key}"]
        lo, hi = (100 * x for x in v["inflation_ci95_nadeau_bengio"])
        mean = 100 * v["inflation_mean"]
        left.plot([lo, hi], [y, y], color=BLUE, linewidth=2)
        left.plot(mean, y, "o", color=BLUE, markersize=8)
        left.annotate(
            f"{mean:+.1f} [{lo:+.1f}, {hi:+.1f}]",
            (hi, y),
            xytext=(6, -3),
            textcoords="offset points",
            fontsize=8,
            color=INK,
        )
    left.axvline(0, color=MUTED, linewidth=1, linestyle="--")
    left.set_yticks(range(len(SOURCES)), [label for _, label in SOURCES])
    left.set_xlim(-5, 18)
    left.invert_yaxis()
    left.set_xlabel("Row-split minus group-split recall at 1% FPR (points)")
    left.set_title(
        "Inflation from row-random splits\n(mean of 20 repeats, 95% Nadeau-Bengio CI)",
        fontsize=10,
        loc="left",
    )
    loto = sorted(report["leave_one_hackaprompt_template_out"], key=lambda x: -x["rows"])
    x = range(len(loto))
    right.bar(x, [100 * t["recall_at_1pct_fpr"] for t in loto], color=BLUE, width=0.6)
    for i, t in enumerate(loto):
        right.annotate(
            f"{100 * t['recall_at_1pct_fpr']:.0f}%",
            (i, 100 * t["recall_at_1pct_fpr"]),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            fontsize=8,
            color=INK,
        )
    right.axhline(100, color=MUTED, linewidth=1, linestyle="--")
    right.annotate(
        "row split: 100%",
        (len(loto) - 0.5, 100),
        xytext=(0, -12),
        textcoords="offset points",
        ha="right",
        fontsize=8,
        color=MUTED,
    )
    right.set_xticks(
        list(x), [f"T{i + 1}\n({t['rows']} rows)" for i, t in enumerate(loto)], fontsize=8
    )
    right.set_ylim(0, 112)
    right.set_ylabel("Recall at 1% FPR (%)")
    right.set_title(
        "HackAPrompt: each template held out in turn\n(7 templates; no interval)",
        fontsize=10,
        loc="left",
    )
    for ax in (left, right):
        ax.spines[["top", "right"]].set_visible(False)
    right.grid(axis="y", color="#e4e3df", linewidth=0.8)
    left.grid(axis="x", color="#e4e3df", linewidth=0.8)
    fig.suptitle(
        "Study 2: TF-IDF detector, InjecGuard-derived pools", fontsize=11, x=0.01, ha="left"
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=160)
    print(OUT)


if __name__ == "__main__":
    main()
