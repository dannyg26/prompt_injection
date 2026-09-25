# Preregistration - Study 3: does distribution-matched benign augmentation fix external over-defense?

**Status: frozen 2026-09-25; NOT YET AUTHORIZED TO RUN.** `scripts/run_study3.py` refuses to run until two conditions hold. First, the project owner adds an AGENTS.md amendment containing the phrase "PREREGISTRATION_STUDY3.md may be fit and scored". Second, the hashes in `results/study3/PREREG_LOCK.json` match a pushed commit. No Study 3 pool has been drawn and no Study 3 model has been fitted.

## Question

PIDS-Bench (Shire and Kim, IEEE Access 14, 2026; notes in `docs/literature/pidsbench-2026.md`) reports that DeBERTa-v3-base fine-tuned on its training set flags 0.3144 ± 0.0525 (5 seeds) of 872 externally sourced, security-adjacent benign prompts at τ = 0.5. Adding their 419 curated hard negatives leaves that rate unchanged: 0.314 → 0.310, Δ −0.004, bootstrap [−0.014, +0.005] (pp. 13–14, 17). The authors write: "What we have not tested is augmentation drawn to match the externally-sourced distribution rather than the curated pool; whether that would close the gap is open" (p. 19, §VIII-D).

Study 3 tests that question on their released benchmark with their own training code. In the 16 papers read (`docs/STUDY3_PLAN.md`), no paper answers it. That wording is as strong as the evidence allows; later work citing PIDS-Bench is UNVERIFIED and will be checked before submission.

## Materials

- **Benchmark:** github.com/ShirePyDev/Prompt-Injection-Detection-System, commit 87dc835 (tag v1.0-pids-bench). Code is MIT. The benchmark is research/non-commercial use (their DATA_LICENSES.md).
- **Restoring the 664 LMSYS test rows:** their 664 LMSYS hard-benign test rows ship without text. Their `data_builder/rebuild_restricted.py` restores them from the owner's own licensed LMSYS-Chat-1M access. If more than 33 rows (5%) stay unrestored, the run stops. Up to 33 missing rows are excluded from all arms and the count is reported.
- **Pool sources:**
  - LMSYS-Chat-1M: gated licence, **no redistribution**.
  - OpenAssistant/oasst1: Apache-2.0 (UNVERIFIED here; per their DATA_LICENSES.md).
  - databricks-dolly-15k: CC BY-SA 3.0 (same caveat).
- **LMSYS licence handling:** LMSYS text is written only outside this git repository, in the owner's Colab or Drive, and every path is checked by `assert_outside_repo`. The repository receives only SHA-256 fingerprints, counts and scores.

## Pools (built once; `build_pools` in scripts/run_study3.py)

**Candidates.** Candidates are selected with PIDS-Bench's own code in `data_builder/build_hard_benign.py`, imported unmodified:

- **Text handling:** `_normalize_text`; length 20–1000 characters; `_passes_moderation`.
- **Exclusions:** `EXCLUDE_PATTERNS`, `LOW_SIGNAL_PATTERNS` and `FINAL_EXCLUDE_PATTERNS` are all applied.
- **Classes:** `_classify_real_text` assigns class `keyword` (an injection keyword with a hard-benign context term) or `random` (an AI term with a context term). Rows with neither form class `none`.
- **LMSYS:** English, non-redacted conversations, first user turn, as in their `collect_lmsys`. Only stream rows with index ≥ 200,000 are used. They scanned only rows [0, 200,000), so pool rows cannot be their test rows by construction. Scanning stops at index 1,000,000 or when every LMSYS cell holds 3,000 candidates.
- **OASST1:** English prompter turns, train and validation splits. **Dolly:** `instruction`.
- **Cap:** each (source, class) cell keeps its first 3,000 candidates in stream order.

**Disjointness.** Disjointness is enforced in three steps, before sampling:

1. **Exact:** remove any candidate whose normalized, lower-cased text equals any text in any benchmark CSV (train, val, test, curated hard negatives, all eval and OOD files).
2. **Cross-set semantic:** remove any candidate whose char_wb 3–4-gram TF-IDF cosine to any evaluation-file row (hard-benign, test, obfuscated, domain-OOD, structural-OOD) is ≥ 0.92. This is PIDS-Bench's own near-duplicate representation and cutoff.
3. **Within-cell:** their `semantic_dedup` at 0.92.

Their training script's `dedup_safety_check` re-verifies exact disjointness from the evaluation files before every fit.

**Near-duplicate definition and remaining uncertainty.** The operational near-duplicate definition is character TF-IDF cosine ≥ 0.92. Paraphrases below that cutoff can remain, so semantic overlap with the test distribution is intended (that is the intervention) but paraphrase-level duplicates of individual test rows are not ruled out. The count removed at each step is reported.

**Arms.** Each augmented arm adds exactly 419 training and 116 validation benign rows, the sizes their script asserts. Rows are drawn with seed 20260925 from the deduplicated cells, and each cell is split train/validation proportionally.

| Arm | Added rows | Composition |
| --- | --- | --- |
| A0_none | none (their `deberta_v3.run_train`) | — |
| A1_curated | their 419/116 curated hard negatives | their file, unchanged |
| A2_matched | matched pool | proportional to the external test cells: lmsys keyword 298, lmsys random 366, oasst1 keyword 40, oasst1 random 100, dolly keyword 18, dolly random 50 |
| A3_source_only | same corpora, class `none` | lmsys 664, oasst1 140, dolly 68 |
| A2L_matched_lmsys_only (secondary) | matched, LMSYS only | lmsys keyword 298, lmsys random 366 |

**Fallback rule (fixed now).** If an OASST1 or Dolly cell has fewer deduplicated candidates than its allocation, its deficit moves to the LMSYS cell of the same class, via `feasible_counts`. This is expected for the small keyword cells. The final counts and every reassignment are reported in `pool_manifest.json`.

**What A3 isolates.** A3 separates "same corpora" from "same selection". The contrasts A2 − A3 and A2L on OASST1/Dolly rows are secondary.

## Training (their code, unmodified)

- **Recipe:** their DeBERTa-v3-base recipe, run as `run_train` (A0) or `train_and_tune` after `verify_hard_negatives` and `dedup_safety_check` (other arms). Each fit runs in a fresh subprocess inside that arm's copy of their repository; only `hard_negative_{train,val}.csv` differs between copies.
- **Hyperparameters:** 3 epochs; lr 2e-5; maximum length 512; batch 8 × gradient accumulation 2; warmup 0.06; weight decay 0.01; fp32 with TF32 disabled; best epoch by validation F1.
- **Seeds:** 13, 42, 123, 2024 and 7777.
- **Versions:** pinned to their requirements where Colab allows: transformers 4.57.1, datasets 4.4.1. The torch version is Colab's and is recorded in the logs.
- **Numerics:** bitwise equality with their runs is not expected.

**Order and budget.** Fits run seed by seed, with all primary arms for a seed before the next seed, then A2L. If the compute budget ends early, the completed seeds stay balanced across arms. The confirmatory analysis requires all 5 seeds of every primary arm. With fewer, the study is reported as incomplete and descriptive only, and no contrast is called established. The runner prints only fit times until the analysis stage, so stopping cannot depend on results. The first fit (A1, seed 13) doubles as the timing pilot; its scores are kept as part of the study.

## Scoring (ours; `score` in scripts/run_study3.py)

- **Procedure:** each saved model scores every row of hard_benign_test, test, obfuscated_attacks, domain_ood and structural_ood. Settings: max length 512, dynamic padding, fp32. The model is then deleted.
- **Thresholds:** τ = 0.5 is their operating point for the main tables. τ_val is their `best_threshold` (grid step 0.002, maximum F1, ties to the highest τ) on that arm's validation set: val.csv plus the arm's 116 validation hard negatives, or val.csv alone for A0.
- **Held-out data:** no threshold, pool rule or hyperparameter is chosen from test or hard-benign data.

## Endpoints

- **Primary:** external hard-benign FPR at τ = 0.5 over the restored external rows (source_type = real, n ≤ 872).
  - Contrasts: **A2 − A1** and **A2 − A0**.
- **Secondary** (descriptive; 95% intervals where stated):
  - External FPR at τ_val.
  - Curated hard-benign FPR.
  - Test F1, recall and FPR at τ = 0.5.
  - Obfuscated-attack recall.
  - External FPR on LMSYS rows vs OASST1/Dolly rows.
  - Contrasts A2 − A3 and A2L − A2.
  - Their frontier criterion (any τ on the 0.002 grid with test F1 ≥ 0.95 and external FPR ≤ 0.10). This picks τ with oracle knowledge of the external rows, is labelled an oracle, and is never used for decisions.
  - Domain- and structural-OOD scores are stored for later descriptive use.
- **Replication check** (descriptive): A0 and A1 are compared with the published 0.314 [0.288, 0.342] and 0.310. A mismatch is reported, not corrected.

## Inference

- **Primary interval:** paired percentile bootstrap, 10,000 replicates, seed 20260925 (`joint_bootstrap_diff`).
  - **Row groups:** each replicate resamples near-duplicate groups of external rows (word 5-gram containment ≥ 0.5, transitive; our Study 1–2 definition).
  - **Seeds:** each replicate independently resamples the 5 seeds with replacement. The per-seed arm difference is computed on the same rows.
  - **Reporting:** the seed-mean difference is reported with its 97.5% interval (Bonferroni over the two confirmatory contrasts) and its 95% interval.
- **Assumptions:** groups are exchangeable. Seeds are draws of training randomness. All seeds share the same training and test data, so seeds are **not** independent test examples, and a bootstrap over only 5 seeds understates seed variance.
- **Sensitivity interval:** a Student-t interval (df = 4) over the 5 per-seed differences, at 97.5%. It ignores row variance.
- **Decision rule:** a reduction is **established** when the primary 97.5% interval lies entirely below 0. If the sensitivity interval disagrees, the reduction is reported as fragile.
- **Closing the gap:** a reduction counts as a practically meaningful closing of the gap only if the upper bound is below −0.05. Separately, the report states whether A2's mean external FPR reaches ≤ 0.10, their target.
- **Other outcomes:** an interval entirely above 0 is reported as an increase. Anything else is inconclusive at this sample size. Null and negative results are reported as found.

**Sensitivity (planning; `results/study3/power_planning.json`).** The inputs are their published seed SD of 0.0525, 872 rows, a row design effect of 2, α = 0.025 per contrast and 80% power. With them, the minimum detectable reduction with 5 seeds is ≈ 0.11 under the normal approximation and ≈ 0.16 under the seed-t. The study can therefore detect the ≈ 0.21 reduction needed to reach their 0.10 target, but not reductions of a few points. These are planning values, not measured results.

## Limitations stated in advance

1. **Unmet launch gates (AGENTS.md).** The project's launch gates remain unmet, and running under the owner's scoped approval does not satisfy them:
   - primary component permissions and provenance review;
   - an independent sample-size design (the calculation above is ours);
   - human annotation and IAA.
2. **Pool labels.** Pool rows are labelled benign by PIDS-Bench's heuristic selection plus moderation. No human reviewed them, so some could be injection attempts. PIDS-Bench's own benign/non-benign audit of hard-benign test rows found 1/200 errors (p. 9). That audit does not cover our pools.
3. **Five seeds share one dataset,** and one pool draw is used (pool seed 20260925). Variation across pool draws is not estimated.
4. **Single model family and benchmark.** The results address DeBERTa-v3-base on PIDS-Bench only.
5. **Fallback rows.** Fallback reassignment can make A2's source mix deviate from the test mix; the deviation is reported.

## Amendments

None yet. Any change after the lock is appended here with a date and a statement of what results, if any, had been seen.
