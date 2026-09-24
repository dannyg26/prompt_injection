# Preregistration - Study 2: how much do row-random splits overstate prompt-injection detection?

**Status: frozen 2026-09-24; NOT YET AUTHORIZED TO RUN.** AGENTS.md gates all detector training beyond Study 1. `scripts/run_split_comparison.py` refuses to run until the project owner adds an AGENTS.md amendment containing the phrase "PREREGISTRATION_LEAKAGE.md may be fit and scored", and until the hashes in `results/leakage/PREREG_LOCK.json` match a pushed commit. No Study 2 model has been fitted.

## Motivation and prior work

Dataset-level leakage is already documented: *When Benchmarks Lie* (leave-one-dataset-out), and PIDS-Bench's family-separated splits. This study targets the within-dataset, template-level question and its statistical consequence (docs/LEAKAGE_NOVELTY.md, docs/BENCHMARK_AUDIT.md). All novelty claims remain UNVERIFIED until those papers are read in full.

## Data

The frozen Study 1 pools (`data/processed/study/pools.jsonl`, sha256 in `results/study/pool_ledger.json`): 61,819 license-declared rows with template groups. Study 1 partitions are ignored and all rows are pooled. Attack sources analyzed: HackAPrompt, jailbreak-classification, TaskTracker and BIPIA. All benign rows serve as negatives.

## Part A (CPU; runs on approval)

**Splits.** For repeats r = 0..19 (split seed 31000 + r), two 70/30 splits of the same pool:

- **Row split:** random rows, stratified by label. This is the common practice.
- **Group split:** whole groups, stratified by whether a group contains an attack, placed largest-first.

**Detector.** The unchanged Study 1 recipe (word+char TF-IDF, class-balanced logistic regression, no tuning), fit on the train side and scored once on the test side.

**Metrics per split.**

- AUROC.
- Recall at the evaluation-ROC cutoff where FPR ≤ 1% over all benign test rows, pooled and per attack source.
- Per attack source on group splits, the design effect of recall at that cutoff: cluster ratio-estimator variance divided by binomial variance.

**Estimands and inference.**

1. **Inflation** (primary): the mean over repeats of (row-split metric − group-split metric), for pooled recall at 1% FPR (primary) and for AUROC and per-source recall (secondary). The 95% interval is the Nadeau–Bengio corrected resampled t with J = 20, n_test/n_train = 0.3/0.7. Repeated splits overlap, so repeats are not independent samples, and the naive t-interval is not used.
2. **Design effect:** the median and range over the 20 group splits, per attack source. This is descriptive and needs no interval.
3. **Leave-one-HackAPrompt-template-out:** hold out each HackAPrompt group in turn, together with the benign test rows of group split seed 31000. Report recall at 1% FPR for each group. There are only about 7 groups, so results are descriptive and no interval is claimed.

**Decision rules.**

- Inflation is established if the primary interval lies above 0.
- A design effect above 2 for a source means example-level recall intervals for that source understate variance by more than a factor of 2.
- Null or negative results are reported as found.

## Part B (conditional; specified now, run later under an amendment lock)

This part runs only if a GPU and Hugging Face access are both available.

1. **DeBERTa-v3-small:** repeat Part A with the checkpoint pinned by revision hash before fitting, fixed hyperparameters (learning rate 2e-5, 2 epochs, max length 256, batch size 32), no tuning, and 5 repeats.
2. **Released detectors:** score ProtectAI deberta-v3-base-prompt-injection-v2, Meta Prompt Guard 2 (86M) and PIGuard, pinned by revision, on the group-split test sets. Their training data are partly unknown, so only the design effect and the per-template recall spread are estimated, not inflation.

The exact code will be locked in an amendment before any Part B run.

## Known limitations (stated in advance)

- Lexical groups approximate templates.
- Upstream labels only, with no IAA.
- One linear detector in Part A.
- Repeated-split inference is approximate even with the Nadeau–Bengio correction.
- Pooling all domains mixes direct and indirect attacks.
