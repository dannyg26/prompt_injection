# Study 3 results: distribution-matched benign augmentation vs PIDS-Bench external over-defense

Run once under the lock `results/study3/PREREG_LOCK.json`, at commit 1e31220, with PIDS-Bench at commit 87dc835. The design is in `docs/PREREGISTRATION_STUDY3.md`. Raw outputs are in `results/study3/study3_results.json` and `results/study3/pool_manifest.json` (fingerprints and counts only; no LMSYS text). Analysis finished 2026-09-30T13:08Z.

- **Completeness:** all 25 fits completed on the first attempt (5 arms × seeds 13, 42, 123, 2024, 7777), each taking 48–50 A100 minutes. Status: `complete`.
- **External rows:** all 664 LMSYS test rows were restored, so the external set has the full 872 rows, in 763 near-duplicate groups.
- **Seeds are not extra test data.** Every number below is a mean over the 5 seeds. The seeds share the same training and test data, so they are not independent test examples.

## Confirmatory result (primary endpoint: external hard-benign FPR at τ = 0.5)

| Contrast | Estimate | Bootstrap 97.5% CI | Seed-t 97.5% CI | Decision |
| --- | ---: | ---: | ---: | --- |
| A2 matched − A1 curated | **−0.264** | [−0.320, −0.210] | [−0.320, −0.208] | Established reduction; beyond 5 points; not fragile |
| A2 matched − A0 none | **−0.268** | [−0.336, −0.199] | [−0.361, −0.175] | Established reduction; beyond 5 points; not fragile |

Per-seed differences (seeds 13, 42, 123, 2024, 7777):

- A2 − A1: −0.211, −0.297, −0.287, −0.281, −0.243.
- A2 − A0: −0.279, −0.182, −0.261, −0.267, −0.350.

Every seed shows a reduction of at least 18 points.

The effect is larger than the preregistered sensitivity limit (a minimum detectable reduction of about 0.17–0.20). Both of the required intervals exclude 0, and both upper bounds are below −0.05.

**Answer to PIDS-Bench's open question** (p. 19, §VIII-D), within the scope below: **yes, in an oracle setting.** Benign augmentation selected with the benchmark's own rules and test composition, from the same corpora, cut external over-defense from about 32% to about 6% at their operating point, which meets their 10% target. Unselected same-corpus rows (A3) achieve most of that reduction (to 0.14). There was no measurable loss of attack recall on in-distribution PIDS-Bench attacks, where recall is at ceiling. **Mechanism caveat (found in review, 2026-10-02):** every PIDS-Bench benign training row is a GPT-4o-mini paraphrase (pidsbench-2026.md:20; all 12,846 benign rows in train.csv have `generator_model = gpt-4o-mini`), while the external test rows and every pool row are raw human text. We cannot separate corpus content from a raw-versus-paraphrased style effect; see Study 4's results and the planned follow-up.

## Descriptive results by arm (seed mean; 95% CI)

The CIs are joint bootstraps over near-duplicate groups and seeds (2,000 replicates). For F1, the CI is a seed-t interval.

| Metric | A0 none | A1 curated | A2 matched | A3 source-only | A2L LMSYS-only |
| --- | ---: | ---: | ---: | ---: | ---: |
| External FPR, τ = 0.5 (n = 872) | 0.325 [0.265, 0.384] | 0.321 [0.275, 0.370] | **0.058** [0.036, 0.081] | 0.138 [0.104, 0.178] | 0.050 [0.033, 0.069] |
| External FPR, τ_val | 0.320 [0.267, 0.373] | 0.315 [0.267, 0.360] | 0.058 [0.037, 0.082] | 0.143 [0.114, 0.176] | 0.051 [0.033, 0.070] |
| External FPR, LMSYS rows (n = 664) | 0.385 [0.317, 0.455] | 0.381 [0.327, 0.438] | 0.064 [0.038, 0.094] | 0.156 [0.111, 0.202] | 0.049 [0.030, 0.073] |
| External FPR, OASST1/Dolly rows (n = 208) | 0.137 [0.092, 0.183] | 0.132 [0.088, 0.180] | 0.038 [0.017, 0.062] | 0.081 [0.049, 0.116] | 0.054 [0.029, 0.084] |
| Curated hard-benign FPR (n = 600) | 0.528 [0.248, 0.778] | **0.000** [0.000, 0.000] | 0.360 [0.146, 0.606] | 0.384 [0.166, 0.634] | 0.312 [0.086, 0.553] |
| Test recall (n = 2,070 attacks) | 0.987 [0.979, 0.993] | 0.988 [0.981, 0.994] | 0.989 [0.982, 0.995] | 0.987 [0.980, 0.994] | 0.988 [0.980, 0.994] |
| Test FPR (n = 1,848 benign) | 0.013 [0.007, 0.021] | 0.013 [0.006, 0.020] | 0.014 [0.007, 0.022] | 0.013 [0.006, 0.021] | 0.013 [0.006, 0.021] |
| Test F1 | 0.987 [0.986, 0.989] | 0.988 [0.988, 0.989] | 0.988 [0.987, 0.990] | 0.988 [0.987, 0.989] | 0.988 [0.987, 0.989] |
| Obfuscated recall (n = 405) | 0.984 [0.970, 0.995] | 0.984 [0.972, 0.994] | 0.988 [0.976, 0.996] | 0.985 [0.971, 0.995] | 0.988 [0.977, 0.996] |
| Oracle frontier met (seeds of 5)* | 0 | 0 | 5 | 5 | 5 |

\* The frontier column counts the seeds for which any τ gives test F1 ≥ 0.95 together with external FPR ≤ 0.10. It chooses τ with knowledge of the external rows, so it is an oracle, descriptive only. PIDS-Bench reports that no internal detector met it (p. 13); our A0 and A1 agree.

**Replication check.** PIDS-Bench published 0.3144 [0.288, 0.342] for A0 and 0.310 for A1. Our A0 gives 0.325 [0.265, 0.384] and our A1 gives 0.321, so both reproduce the published values within our intervals.

## Secondary contrasts (95%; bootstrap and seed-t)

| Contrast [metric] | Estimate | Bootstrap 95% | Seed-t 95% |
| --- | ---: | ---: | ---: |
| A2 − A3 [external FPR] | −0.081 | [−0.111, −0.054] | [−0.113, −0.048] |
| A2L − A2 [external FPR] | −0.008 | [−0.022, +0.005] | [−0.017, +0.002] |
| A2L − A1 [OASST1/Dolly external rows, n = 208] | −0.078 | [−0.122, −0.040] | [−0.107, −0.049] |
| A2L − A1 [LMSYS external rows, n = 664] | −0.332 | [−0.391, −0.276] | [−0.382, −0.282] |
| A2 − A1 [external FPR at τ_val] | −0.257 | [−0.307, −0.210] | [−0.298, −0.216] |
| A2 − A1 [curated FPR] | **+0.360** | [+0.145, +0.594] | [+0.301, +0.419] |
| A2 − A1 [test recall] | +0.001 | [−0.004, +0.006] | [−0.005, +0.006] |
| A2 − A1 [recall, test attacks with a context term, n = 1,025] | −0.002 | [−0.007, +0.001] | [−0.005, +0.001] |
| A2 − A1 [obfuscated recall] | +0.004 | [−0.004, +0.013] | [−0.004, +0.012] |
| A2 − A1 [obfuscated recall with a context term, n = 153] | 0.000 | [0, 0] | [0, 0] |

## What the results show, and what they do not

1. **Matched augmentation closes the external gap (oracle setting).** A2 cuts external over-defense by about 26 points against both the baseline and the curated pool, with every seed agreeing. The A0 and A1 means are 0.325 and 0.321; we computed no interval for A1 − A0, which matches PIDS-Bench's reported null (−0.004, [−0.014, +0.005]).

2. **Most of the gain comes from unselected same-corpus raw text; the matched selection adds the rest.**
   - A3 draws 535 random filtered rows from the same corpora. Only 5% of them contain a context term (`pool_manifest.json`, composition), yet A3 already lowers external FPR to 0.138.
   - Matched selection (A2) lowers it by a further 8.1 points [−11.1, −5.4].
   - INFERENCE: much of the external over-defense reflects the training set's lack of raw user text. Because PIDS-Bench's benign training rows are all LLM paraphrases, this could be corpus content or a learned "raw human text = benign" style shortcut; we did not test which.

3. **Each pool fixes the distribution it came from, and not the other.**
   - A1's curated pool removes curated over-defense entirely: 0.528 → 0.000.
   - Every externally drawn pool leaves curated FPR at 0.31–0.38. A2 − A1 is +0.360, with a wide bootstrap interval because curated rows form few groups.
   - None of the five arms solves both sets. INFERENCE: this fits PIDS-Bench's account that the over-defense boundary is distribution-specific. Deployments would likely need both kinds of benign data; we did not test a combined pool.

4. **The effect carries over to a source held out of the pool, but less strongly.**
   - A2L draws only from LMSYS, yet still lowers FPR on the OASST1/Dolly external rows by 7.8 points [−12.2, −4.0].
   - Its reduction on LMSYS rows is 33.2 points.
   - A2L and A2 do not differ measurably overall.

5. **No measurable recall cost, but the exploitable-cue check is limited.** At τ = 0.5, test recall, obfuscated recall and recall on attacks that contain a PIDS-Bench context term are unchanged: all differences lie within ±0.7 points. Two limits apply:
   - Recall is near its ceiling (0.995–1.000) in these subsets, so the check has little room to detect harm.
   - We did not test adaptive attacks that deliberately wrap an injection in security-education framing. An attacker who knows the augmentation could target exactly that.

## Scope and limitations (as preregistered, with what the run revealed)

- **Oracle-distribution augmentation.** The pool uses the benchmark's own selection rules and the test set's source/class counts. This result is an upper bound on what matched data can do. It is not evidence that a defender without that knowledge can build such a pool.
- **The pool differs from the test mix.**
  - No unused Dolly keyword rows survived filtering, so 11 rows moved to LMSYS keyword, as preregistered.
  - 33% of A2's rows (and 41% of A2L's) use LMSYS's "you are the text completion model" template, against 0% of the external test rows.
  - At the median the test rows are shorter (298 characters vs 397 in A2), but they have a longer upper tail (upper quartile 582.5 vs 423.5).
  - The reduction happened despite these differences; we did not try to correct them. Because filter 2 did not remove the template (the test set contains none of it), A2 is not fully distribution-matched.
- **Deviation (logged 2026-10-02):** the preregistration's LMSYS stopping rule says 3,000 candidates per cell, but its Cap rule and the runner (`CAND_CAP = 5000`) use 5,000. The run used 5,000. This internal inconsistency in the frozen document was not noticed before the run.
- **Pool labels are unaudited so far.** The 200-row blind audit export exists, but the owner's labels are pending. Until they are in, the share of pool rows that are truly benign is not known.
- **Same corpora, disjoint rows.** Pool rows are disjoint from every evaluation row: exact match, word 5-gram containment ≥ 0.5, and char TF-IDF cosine ≥ 0.92. LMSYS pool rows also come from stream indices ≥ 200,000, while all test rows came from the first 200,000. However, pool and test share their corpora, so this is in-distribution generalisation, not generalisation to new sources. The OASST1/Dolly transfer result (A2L) is the only cross-source evidence, and it is partial.
- **Other scope limits.**
  - One model family (DeBERTa-v3-base) and one benchmark.
  - One pool draw, so variation across pool draws is not estimated.
  - Five seeds sharing all data.
- **Project gates.** The project's launch gates (primary component permissions and provenance, an independent sample-size design, human annotation and IAA) remain unmet and are limitations of this study.
- **Novelty.** The novelty claim is limited to "not found in the 16 papers read". Papers citing PIDS-Bench after 28 Aug 2026 have not been checked (UNVERIFIED).
