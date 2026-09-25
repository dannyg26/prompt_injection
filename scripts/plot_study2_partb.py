"""Presentation-only Study 2 Part B figure from results/leakage/partb/partb_results.json."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RESULTS = Path("results/leakage/partb/partb_results.json")
OUT = Path("paper/figures/study2_partb.png")
INK, MUTED = "#0b0b0b", "#52514e"
# Reference categorical slots 1-3 (validated for all-pairs use), fixed per detector.
DETECTORS = (
    ("tfidf", "TF-IDF (trained here)", "#2a78d6"),
    ("deberta", "DeBERTa-v3-small (trained here)", "#eb6834"),
    ("protectai", "ProtectAI v2 (released; not retrained)", "#1baf7a"),
)
SOURCES = (
    ("TaskTracker", "TaskTracker"),
    ("BIPIA", "BIPIA"),
    ("jailbreak-classification", "jailbreak-\nclassification"),
)


def main():
    r = json.loads(RESULTS.read_text(encoding="utf-8"))
    fig, (left, right) = plt.subplots(
        1, 2, figsize=(13, 4.8), constrained_layout=True, gridspec_kw={"width_ratios": [1, 1.5]}
    )
    for y, (source, _) in enumerate(SOURCES):
        for k, (det, _, color) in enumerate(DETECTORS[:2]):
            v = r["inflation"][f"{det}|{source}"]
            lo, hi = (100 * x for x in v["ci95_nadeau_bengio"])
            yy = y + (k - 0.5) * 0.3
            left.plot([lo, hi], [yy, yy], color=color, linewidth=2)
            left.plot(100 * v["inflation_mean"], yy, "o", color=color, markersize=7)
    left.axvline(0, color=MUTED, linewidth=1, linestyle="--")
    left.set_yticks(range(len(SOURCES)), [label for _, label in SOURCES])
    left.invert_yaxis()
    left.set_xlabel("Row-split minus group-split recall at 1% FPR (points)")
    left.set_title(
        "Inflation from row splits: none established\n(5 repeats, 95% Nadeau-Bengio CI)",
        fontsize=10,
        loc="left",
    )
    series = {
        "tfidf": r["loto"]["tfidf"],
        "deberta": r["loto"]["deberta"],
        "protectai": r["released"]["deberta-v3-base-prompt-injection-v2"][
            "hackaprompt_per_template"
        ],
    }
    order = [x["group"] for x in sorted(series["tfidf"], key=lambda x: -x["rows"])]
    rows = {x["group"]: x["rows"] for x in series["tfidf"]}
    width = 0.26
    for k, (det, name, color) in enumerate(DETECTORS):
        values = {x["group"]: 100 * x["recall_at_1pct_fpr"] for x in series[det]}
        xs = [i + (k - 1) * width for i in range(len(order))]
        heights = [values[g] for g in order]
        right.bar(xs, heights, width=width - 0.03, color=color, label=name)
        for x, h in zip(xs, heights):
            if h < 1:  # a 0% bar is invisible; mark it so it is not read as missing
                right.annotate(
                    "0",
                    (x, 0),
                    xytext=(0, 2),
                    textcoords="offset points",
                    ha="center",
                    fontsize=7,
                    color=MUTED,
                )
    right.set_xticks(
        range(len(order)), [f"T{i + 1}\n({rows[g]} rows)" for i, g in enumerate(order)], fontsize=8
    )
    right.set_ylim(0, 105)
    right.set_ylabel("Recall at 1% FPR (%)")
    right.set_title(
        "HackAPrompt: each template held out in turn (7 templates; no interval)\n"
        "ProtectAI was not retrained here and may have seen HackAPrompt in training",
        fontsize=10,
        loc="left",
    )
    right.grid(axis="y", color="#e4e3df", linewidth=0.8)
    left.grid(axis="x", color="#e4e3df", linewidth=0.8)
    for ax in (left, right):
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle(
        "Study 2 Part B (randomized group splits)", fontsize=11, x=0.01, ha="left", color=INK
    )
    handles, labels = right.get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper right",
        ncol=3,
        frameon=False,
        fontsize=8,
        bbox_to_anchor=(0.99, 1.0),
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=160)
    print(OUT)


if __name__ == "__main__":
    main()
