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

## Amendment 1 (2026-09-24): output serialization fix

The first authorized run fitted all 40 splits and then crashed while writing its output, because undefined design effects (NaN) are rejected by the strict JSON writer. No result file or summary was written or seen. The only change is that NaN values are now written as `null` (`json_safe` in the run script). The analysis, splits, seeds and decision rules are unchanged. The lock was re-hashed and pushed before the rerun.

## Amendment 2 (2026-09-24, after Part A): splitter for Part B

A post-hoc check of Part A found that the group splitter (largest-first allocation) placed the same HackAPrompt template in the test side of all 20 group splits. The Part A HackAPrompt interval is therefore invalid, and the pooled primary estimate is confounded by test composition (docs/STUDY2_RESULTS.md). Part A results stay as run; they are not re-fitted, because the owner approved a single run.

For Part B:

1. Group splits use `random_group_split`: uniformly random group order, filled to the test fraction per stratum. A test verifies that a large group lands on both sides across seeds.
2. The primary endpoint changes from pooled recall to **per-source recall inflation**, reported separately for each attack source with at least 20 groups (TaskTracker, BIPIA, jailbreak-classification in these pools). This avoids the composition confound.
3. HackAPrompt (7 groups) is analyzed only by leave-one-template-out; no inflation interval is computed for it.

This amendment was written after Part A results were seen. It is a design correction for the next experiment, not a reanalysis of Part A. `splitcompare.py` changed after the Part A run; the Part A lock in git history (commit `a93623d`) records the code that produced those results.

## Amendment 3 (2026-09-24): Part B design, locked before any Part B run

This supersedes the Part B sketch above wherever they differ. Everything here was fixed before any Part B model was trained or scored, and no Part B output exists. The runner is `scripts/run_partb.py` (with `src/injection_lab/partb.py` and `transformer.py`); hashes are in `results/leakage/PARTB_LOCK.json`. It runs on Google Colab (GPU) because the project environment has no GPU or Hugging Face access.

- **Data.** The frozen Study 1 pools, rebuilt on Colab from the committed manifest plus the pinned InjecGuard clone. The runner refuses to continue unless the rebuilt file's sha256 equals `pools_sha256` in `results/study/pool_ledger.json`.
- **Splits.** 5 repeats (split seeds 31000–31004) of a row split and a **randomized** group split (`random_group_split`, Amendment 2); 70/30.
- **Trained detectors.**
  - The Study 1 TF-IDF recipe, run on the same new splits.
  - `microsoft/deberta-v3-small`, fine-tuned once per split with a fixed recipe: AdamW, learning rate 2e-5, weight decay 0.01, **1 epoch**, batch size 32, maximum length 256, 6% linear warmup, balanced class weights, fp16 autocast, gradient clipping at 1.0.
  - The original sketch said 2 epochs. We changed it to 1 to fit a free Colab session. The choice is based on compute alone; no Part B performance had been seen.
- **Released detectors, scored only, never trained.**
  - `protectai/deberta-v3-base-prompt-injection-v2`.
  - `meta-llama/Llama-Prompt-Guard-2-86M`, if the runner's Hugging Face token has access. If it is not available, the runner records it as unavailable; it is not replaced.
  - Maximum length 512 for both.
  - **PIGuard is excluded**, because it was trained on this exact InjecGuard release, so scores on these rows would measure memorization.
- **Revisions.** Every Hub model is pinned to its commit sha at the first run (`revisions.json`), and that sha is reused on resume.
- **Primary endpoints.** For each trained detector, the per-source inflation of recall at 1% FPR (row minus group) for TaskTracker, BIPIA and jailbreak-classification, with 95% Nadeau–Bengio intervals (J = 5; test/train = 0.3/0.7). The pooled and HackAPrompt rows are reported but not interpreted as inflation.
- **Secondary endpoints.**
  - Design effects: median and range over the group splits.
  - HackAPrompt leave-one-template-out recall for both trained detectors, with no interval.
  - For released detectors: per-source recall at 1% FPR over the 5 group-split test sets (mean and range), design effects, and per-HackAPrompt-template recall. Their training data are partly unknown, so no inflation is estimated for them and overlap with these rows cannot be ruled out.
- **Decision rules.** As before: inflation is established for a source if its interval lies above 0. All results are reported.
- **Execution.** Resumable: each finished fit is written to Google Drive and skipped on restart. A crash or disconnect is not a new run. Any change to locked files requires a new amendment.
- **Code changes after Part A.** `pools.py` gained `rows_from_manifest` after Study 1 and Part A ran. Their locks in git history (commits `0f120e6` and `a93623d`) record the code that produced those results.

## Amendment 4 (2026-09-25): gated-model access check

The first Colab execution completed every trained-detector fit and the ProtectAI scoring, which were saved to Drive, then crashed on `meta-llama/Llama-Prompt-Guard-2-86M`. A gated repository exposes its metadata publicly, so pinning a revision succeeded even though the model files were not accessible. No results had been analyzed or seen. The fix checks that the model files can actually be downloaded (`can_download`) on every run. An inaccessible detector is recorded in `unavailable_detectors.json` and excluded, as Amendment 3 already specified; it is not replaced. Nothing about the design or analysis changes. Finished fits are reused from Drive, not re-run.
