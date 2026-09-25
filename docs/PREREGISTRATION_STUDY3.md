# Preregistration - Study 3: does distribution-matched benign augmentation fix external over-defense?

**Status: frozen 2026-09-25; NOT YET AUTHORIZED TO RUN.** `scripts/run_study3.py` refuses to run until two conditions hold. First, the project owner adds an AGENTS.md amendment containing the phrase "PREREGISTRATION_STUDY3.md may be fit and scored". Second, the hashes in `results/study3/PREREG_LOCK.json` match a pushed commit. No Study 3 pool has been drawn and no Study 3 model has been fitted. The design was revised before the lock after an internal hostile review (14 findings, all addressed here).

## Question

PIDS-Bench (Shire and Kim, IEEE Access 14, 2026; notes in `docs/literature/pidsbench-2026.md`) reports that DeBERTa-v3-base fine-tuned on its training set flags 0.3144 ± 0.0525 (5 seeds) of 872 externally sourced, security-adjacent benign prompts at τ = 0.5. Adding their 419 curated hard negatives leaves that rate unchanged: 0.314 → 0.310, Δ −0.004, bootstrap [−0.014, +0.005] (pp. 13–14, 17). The authors write: "What we have not tested is augmentation drawn to match the externally-sourced distribution rather than the curated pool; whether that would close the gap is open" (p. 19, §VIII-D).

Study 3 tests that question on their released benchmark with their own training code. Scope: the matched pool is built with the same keyword/context-term rules that define the external test set, so A2 is **oracle-distribution augmentation**: an upper bound on what matched data can do, not a deployable recipe. In the 16 papers read (`docs/STUDY3_PLAN.md`), no paper answers it. That wording is as strong as the evidence allows; later work citing PIDS-Bench is UNVERIFIED and will be checked before submission.

## Materials

- **Benchmark:** github.com/ShirePyDev/Prompt-Injection-Detection-System, commit 87dc835566b930ee921240874a4939b2c266c2fe (tag v1.0-pids-bench). Code is MIT. The benchmark is research/non-commercial use (their DATA_LICENSES.md).
- **Restoring the 664 LMSYS test rows:** their 664 LMSYS hard-benign test rows ship without text. Their `data_builder/rebuild_restricted.py` restores them from the owner's own licensed LMSYS-Chat-1M access. If more than 33 rows (5%) stay unrestored, the run stops. Up to 33 missing rows are excluded from every analysis, including the replication comparison, and the count is reported. Curated rows ship with text and are unaffected.
- **Pool sources:**
  - LMSYS-Chat-1M: gated licence, **no redistribution**.
  - OpenAssistant/oasst1: Apache-2.0 (UNVERIFIED here; per their DATA_LICENSES.md).
  - databricks-dolly-15k: CC BY-SA 3.0 (same caveat).
- **LMSYS licence handling:** LMSYS text is written only outside this git repository, in the owner's Colab or Drive, and every path is checked by `assert_outside_repo`. The repository receives only SHA-256 fingerprints, counts and scores. A fingerprint of lower-cased LMSYS text can be linked back to an LMSYS row by anyone holding the dataset; it does not disclose the text.
- **Versions and revisions:** the runner refuses to start unless transformers is 4.57.1 and datasets is 4.4.1 (PIDS-Bench's pins), tracked files are unmodified, and HEAD is pushed. The Hugging Face commit SHAs of LMSYS-Chat-1M, OASST1, Dolly and deberta-v3-base are resolved once and recorded; pool data are loaded at those revisions. Their training code loads deberta-v3-base without a revision, so for the model the SHA is recorded, not enforced.

## Stages

`--stage pools` (pools, filters, composition report, audit export; no model) → `--stage pilot` (one fit, A1 seed 13, timing only) → `--stage all` (remaining fits, then analysis). Each stage is resumable.

## Pools (built once; `build_pools` in scripts/run_study3.py)

**Candidates.** Candidates are selected with PIDS-Bench's own code in `data_builder/build_hard_benign.py`, imported unmodified:

- **Text handling:** `_normalize_text`; length 20–1000 characters; `_passes_moderation`.
- **Exclusions:** `EXCLUDE_PATTERNS`, `LOW_SIGNAL_PATTERNS` and `FINAL_EXCLUDE_PATTERNS` are all applied.
- **Classes:** `_classify_real_text` assigns class `keyword` (an injection keyword with a hard-benign context term) or `random` (an AI term with a context term). Rows with neither form class `none`.
- **LMSYS:** English, non-redacted conversations, first user turn, as in their `collect_lmsys`. Only stream rows with index ≥ 200,000 are used. They scanned only rows [0, 200,000), so pool rows cannot be their test rows by construction. Scanning stops at index 1,000,000 or when every LMSYS cell holds 3,000 candidates.
- **OASST1:** English prompter turns, train and validation splits. **Dolly:** `instruction`.
- **Cells:** keyword and random cells per source, plus an `any` cell per source holding every row that passes the filters, whatever its class.
- **Cap:** each cell keeps its first 5,000 candidates in stream (dataset) order; the arm's rows are then a seeded random draw from what survives the filters below. This is not PIDS-Bench's final sampling step (`sample_to_source_targets`), whose text-completion cap is moot here because template-sharing rows are removed by filter 2.

**Disjointness.** Disjointness is enforced in three steps, before sampling:

1. **Exact:** remove any candidate whose normalized, lower-cased text equals any text in any benchmark CSV (train, val, test, curated hard negatives, all eval and OOD files).
2. **Template containment:** remove any candidate with word 5-gram containment ≥ 0.5 (at least 3 shared shingles) to any evaluation-file row (hard-benign, test, obfuscated, domain-OOD, structural-OOD). This is the same definition used to group rows for inference, so no pool row falls in a test row's group. It also removes LMSYS prompts built on a shared template (for example "you are the text completion model…") when test rows use that template, per the AGENTS.md rule that template groups stay disjoint across partitions. The resulting difference in template share between pool and test is reported, not corrected.
3. **Cross-set semantic:** remove any candidate whose char_wb 3–4-gram TF-IDF cosine to any evaluation-file row is ≥ 0.92, PIDS-Bench's own near-duplicate representation and cutoff.
4. **Within-cell:** their `semantic_dedup` at 0.92.

Their training script's `dedup_safety_check` re-verifies exact disjointness of the training hard negatives from test, hard-benign, domain-OOD and structural-OOD before every fit. It does not check the validation hard negatives or the obfuscated file; filters 1–3 do.

**Near-duplicate definition and remaining uncertainty.** The operational definitions are word 5-gram containment ≥ 0.5 and character TF-IDF cosine ≥ 0.92. Paraphrases below both cutoffs can remain, so semantic overlap with the test distribution is intended (that is the intervention) but paraphrase-level duplicates of individual test rows are not ruled out. The count removed at each step, per cell, is reported in `pool_manifest.json`, together with a composition comparison (length, injection-keyword share, context-term share, template share) of each arm's pool against the external test rows.

**Arms.** Each augmented arm adds exactly 419 training and 116 validation benign rows, the sizes their script asserts. Rows are drawn with seed 20260925 from the deduplicated cells, and each cell is split train/validation proportionally.

| Arm | Added rows | Composition |
| --- | --- | --- |
| A0_none | none (their `deberta_v3.run_train`) | — |
| A1_curated | their 419/116 curated hard negatives | their file, unchanged |
| A2_matched | matched pool | proportional to the external test cells: lmsys keyword 298, lmsys random 366, oasst1 keyword 40, oasst1 random 100, dolly keyword 18, dolly random 50 |
| A3_source_only | same corpora, uniform over all filtered rows (`any` cell), no class selection | lmsys 664, oasst1 140, dolly 68 |
| A2L_matched_lmsys_only (secondary) | matched, LMSYS only | lmsys keyword 298, lmsys random 366 |

**Fallback rule (fixed now).** If an OASST1 or Dolly cell has fewer deduplicated candidates than its allocation, its deficit moves to the LMSYS cell of the same class, via `feasible_counts`. This is expected for the small keyword cells. The final counts and every reassignment are reported in `pool_manifest.json`. If an LMSYS cell itself is short after scanning to row 1,000,000, the run stops at the pools stage, before any fit, and an amendment is required.

**What A3 isolates.** A3 separates "same corpora" from "same selection". The contrasts A2 − A3 and A2L on OASST1/Dolly rows are secondary.

**Blind audit (pools stage, before any fit).** 200 rows drawn at random (seed 20260926) from A2's 535 rows are exported, without arm or class labels, to the private folder. The owner labels each row benign or not. The share judged benign is reported with a Wilson 95% interval. The audit is descriptive: it does not change the pools, and its result cannot influence any fit because the pools are frozen first.

## Training (their code, unmodified)

- **Recipe:** their DeBERTa-v3-base recipe, run as `run_train` (A0) or `train_and_tune` after `verify_hard_negatives` and `dedup_safety_check` (other arms). Each fit runs in a fresh subprocess inside that arm's copy of their repository; only `hard_negative_{train,val}.csv` differs between copies.
- **Hyperparameters:** 3 epochs; lr 2e-5; maximum length 512; batch 8 × gradient accumulation 2; warmup 0.06; weight decay 0.01; fp32 with TF32 disabled; best epoch by validation F1.
- **Seeds:** 13, 42, 123, 2024 and 7777.
- **Versions:** pinned to their requirements where Colab allows: transformers 4.57.1, datasets 4.4.1. The torch version is Colab's and is recorded in the logs.
- **Numerics:** bitwise equality with their runs is not expected.
- **Confounds between arms, stated in advance.** Every arm except A0 goes through the same `train_and_tune`. A0 uses their `run_train`, and its best epoch and τ_val are chosen on val.csv without hard negatives. A2 − A0 therefore mixes augmentation with a different model-selection set; **A2 − A1 is the clean contrast**. In A2, the 116 validation rows come from the matched distribution, so epoch selection (maximum validation F1) is itself tuned toward the endpoint; that is part of the intervention as PIDS-Bench's script defines it, and it is reported as such. No last-epoch variant is run, because that would require modifying their code.
- **Failed fits.** A fit that raises (including their NaN guard) is retried once with identical settings. A second failure marks that arm and seed failed, the arm becomes incomplete, and the batch-size change their error message suggests is not applied. Every attempt is logged.

**Order and budget.** Fits run seed by seed, with all primary arms for a seed before the next seed, then A2L. If the compute budget ends early, the completed seeds stay balanced across arms. The confirmatory analysis requires all 5 seeds of every primary arm. With fewer, the study is reported as incomplete and descriptive only, and no contrast is called established. The runner displays only fit times until the analysis stage. PIDS-Bench's training output, which for A0 includes evaluation metrics, goes to logs in the private folder and is never displayed. The per-fit score files exist on Drive; blinding relies on the fixed plan and on the owner not opening them before the analysis stage, which the owner commits to by approving this plan. The first fit (A1, seed 13) doubles as the timing pilot; its scores are kept as part of the study.

## Scoring (ours; `score` in scripts/run_study3.py)

- **Procedure:** each saved model scores every row of hard_benign_test, test, obfuscated_attacks, domain_ood and structural_ood. Settings: max length 512, dynamic padding, fp32. The model is then deleted.
- **Thresholds:** τ = 0.5 is their operating point for the main tables. τ_val is their `best_threshold` (grid step 0.002, maximum F1, ties to the highest τ) on that arm's validation set: val.csv plus the arm's 116 validation hard negatives, or val.csv alone for A0.
- **Held-out data:** no threshold, pool rule or hyperparameter is chosen from test or hard-benign data.

## Endpoints

- **Primary:** external hard-benign FPR at τ = 0.5 over the restored external rows (source_type = real, n ≤ 872).
  - Contrasts: **A2 − A1** (clean) and **A2 − A0** (see confounds).
- **Secondary** (descriptive; every rate and contrast carries a 95% interval, method below):
  - External FPR at τ_val.
  - Curated hard-benign FPR.
  - Test F1, recall and FPR at τ = 0.5.
  - Obfuscated-attack recall.
  - External FPR on LMSYS rows vs OASST1/Dolly rows.
  - Contrasts A2 − A3 and A2L − A2 on external FPR; A2L − A1 on OASST1/Dolly and on LMSYS external rows (transfer).
  - **Exploitable-cue check:** because the pool teaches "context term plus keyword = benign", recall on test attacks and obfuscated attacks that contain a PIDS-Bench context term (`_contains_hard_benign_context`), for A2 − A1.
  - A2 − A1 on external FPR at τ_val, curated FPR, test recall and obfuscated recall.
  - Their frontier criterion (any τ on the 0.002 grid with test F1 ≥ 0.95 and external FPR ≤ 0.10). This picks τ with oracle knowledge of the external rows, is labelled an oracle, and is never used for decisions.
  - Domain- and structural-OOD scores are stored for later descriptive use.
- **Replication check** (descriptive): A0 and A1 are compared with the published 0.314 [0.288, 0.342] and 0.310. A mismatch is reported, not corrected.

## Inference

- **Primary intervals:** two intervals, both at 97.5% (Bonferroni over the two confirmatory contrasts).
- **Bootstrap:** paired percentile bootstrap, 10,000 replicates (`joint_bootstrap_diff`), with its own RNG stream per analysis (`named_rng`, base seed 20260925).
  - **Row groups:** each replicate resamples near-duplicate groups of external rows (word 5-gram containment ≥ 0.5, transitive; our Study 1–2 definition), computed among external rows only. Curated rows are grouped separately; test and obfuscated rows are grouped by their `parent_seed_id`.
  - **Seeds:** each replicate independently resamples the 5 seeds with replacement. The per-seed arm difference is computed on the same rows.
  - **Reporting:** the seed-mean difference is reported with its 97.5% interval (Bonferroni over the two confirmatory contrasts) and its 95% interval.
- **Seed-t:** a Student-t interval (df = 4) over the 5 per-seed differences. It ignores row variance.
- **Assumptions:** groups are exchangeable. Seeds are draws of training randomness. All seeds share the same training and test data, so seeds are **not** independent test examples. A bootstrap over only 5 seeds understates seed variance (126 distinct seed resamples), which is why the seed-t interval is also required.
- **Decision rule:** a reduction is **established** only when **both** 97.5% intervals lie entirely below 0 and all four primary arms are complete for all 5 seeds. If exactly one interval excludes 0, the result is reported as **fragile**, not established. If any primary arm is incomplete, `status` is `incomplete` and no contrast is called established.
- **Closing the gap:** a reduction counts as practically meaningful only if both upper bounds are below −0.05. Separately, the report states whether A2's mean external FPR reaches ≤ 0.10, their target.
- **Other outcomes:** an interval entirely above 0 is reported as an increase. Anything else is inconclusive at this sample size. Null and negative results are reported as found.

**Sensitivity (planning; `results/study3/power_planning.json`).** The inputs are their published seed SD of 0.0525, 872 rows, a row design effect of 2, α = 0.025 per contrast and 80% power. Row variance is shared by all seeds and is not divided by the seed count. Because a decision needs both intervals, the seed-t is binding: with 5 seeds, the minimum detectable reduction is ≈ 0.17 (arms' per-seed rates correlated 0.5) to ≈ 0.20 (uncorrelated). Reaching both upper bounds below −0.05 needs a true reduction of ≈ 0.22–0.25. Reaching their 0.10 target from 0.314 is a reduction of ≈ 0.21. **The study is therefore powered only to detect near-complete closing of the gap; a partial reduction will most likely be inconclusive, and an inconclusive result is not evidence of no effect.** Five seeds match PIDS-Bench's design; more seeds are outside the compute budget. These are planning values, not measured results.

## Limitations stated in advance

1. **Unmet launch gates (AGENTS.md).** The project's launch gates remain unmet, and running under the owner's scoped approval does not satisfy them:
   - primary component permissions and provenance review;
   - an independent sample-size design (the calculation above is ours);
   - human annotation and IAA.
2. **Pool labels.** Pool rows are labelled benign by PIDS-Bench's heuristic selection plus moderation. No human reviewed them, so some could be injection attempts. PIDS-Bench's own benign/non-benign audit of hard-benign test rows found 1/200 errors (p. 9). That audit does not cover our pools.
3. **Five seeds share one dataset,** and one pool draw is used (pool seed 20260925). Variation across pool draws is not estimated.
4. **Single model family and benchmark.** The results address DeBERTa-v3-base on PIDS-Bench only.
5. **Fallback rows and template filtering.** Fallback reassignment and filter 2 can make A2's source and template mix deviate from the test mix; the deviation is reported.
6. **Oracle distribution.** A2 uses the benchmark's own selection rules and the test set's cell counts. A positive result shows what matched data can do in the best case; it does not show that a defender without that knowledge can build such a pool.
7. **Low power** for partial reductions (see Sensitivity).

## Amendments

None yet. Any change after the lock is appended here with a date and a statement of what results, if any, had been seen.
