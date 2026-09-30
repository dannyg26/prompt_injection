# Preregistration - Study 4: does detector-mined benign augmentation fix external over-defense, and can one pool fix both kinds?

**Status: frozen 2026-09-30; NOT YET AUTHORIZED TO RUN.** `scripts/run_study4.py` refuses to run until two conditions hold. First, the project owner adds an AGENTS.md amendment containing the phrase "PREREGISTRATION_STUDY4.md may be fit and scored". Second, the hashes in `results/study4/PREREG_LOCK.json` match a pushed commit. No Study 4 pool has been drawn and no Study 4 model has been fitted.

The design was revised before the lock after an internal hostile review (22 findings). The initial draft was rejected because C1 could not isolate mining, the framed-attack comparator already contained the cue, and the "fixes both" rule overclaimed. All findings are addressed below.

## Why Study 4 exists (from Study 3; docs/STUDY3_RESULTS.md)

1. **Oracle pool.** Study 3's matched pool (A2) cut external hard-benign FPR from 0.321 (A1) to 0.058. It used PIDS-Bench's own selection rules and test composition.
   - Random rows from the same corpora (A3) already reached 0.138, so corpus exposure alone explains much of the effect.
2. **Each pool fixed only its own distribution.** A1 gave curated FPR 0.000 but external FPR 0.321. The external pools gave curated FPR 0.31–0.38.
3. **Exploitable cue untested.** Recall was checked only on the benchmark's own attacks, which are near ceiling.

## Arms (6 arms × seeds 13, 42, 123, 2024, 7777 = 30 fits)

| Arm | Added rows | Role |
| --- | --- | --- |
| A0_none | none (their `run_train`) | comparator for the framing test (no cue in training) |
| A1_curated | their 419/116 curated hard negatives | comparator; replication |
| A2_matched | Study 3's A2 pool: same rows, same order, same files | oracle upper bound; exploit check |
| A3_source_only | Study 3's A3 pool: random same-corpus rows | **control for corpus exposure** |
| **B1_mined** | **detector-mined, same-corpus pool** (below) | does mining add beyond random same-corpus rows? |
| **B3_curated_mined** | **210/58 curated + 209/58 mined** (mined half drawn from B1) | candidate recipe for fixing both |

- **Refits.** A0–A3 are refit because Study 3 deleted its models, and the framing tests need scores.
- **Reproducibility (descriptive).** The GPU name is recorded per fit. Per seed, the report gives the maximum absolute hard-benign score difference against Study 3's fit and both external FPRs. These are descriptive per-seed values with no interval, and any missing seed is listed.
- **Blinding.** Study 3's score files are on Drive and are read only by the analysis stage.
- **Dropped arm.** The oracle combined arm (curated + matched) considered in the first draft is dropped to keep the budget at 30 fits.

## The detector-mined pool B1

This is a false-positive mining workflow a defender could run: score messages with a deployed detector, drop obvious attacks with a generic filter, and treat the flagged remainder as benign training data.

- **Mining detector:** `protectai/deberta-v3-base-prompt-injection-v2`, pinned to revision `90c9989b1a342275dd0d1a95aad283c04e075671` (already recorded in Study 2 Part B), at its default τ = 0.5.
  - Its training data may overlap public attack corpora, so its independence from PIDS-Bench is **UNVERIFIED**.
  - It was chosen with its published PIDS-Bench numbers already on file: external hard-benign FPR 0.083 and curated FPR 0.410 (docs/literature/pidsbench-2026.md).
- **Hygiene filter** (`generic_filter`):
  - 13 widely known jailbreak markers, fixed in `src/injection_lab/study4.py` and written before any Study 4 data was seen;
  - LMSYS's own moderation flag (LMSYS only; OASST1 and Dolly have no moderation field and are not moderated);
  - a length window of 20–1000 characters.
- **Borrowed from PIDS-Bench, recorded as design decisions** (not benchmark-free):
  - the length window;
  - the choice of sources (LMSYS, OASST1, Dolly: the corpora the external test set came from), with the same English, first-user-turn and non-redacted rules;
  - exact, containment and semantic disjointness against the benchmark's evaluation rows.
- **Not used** (the claim is narrowed to exactly this):
  - PIDS-Bench's corpus-tuned exclusion lists;
  - its keyword and context-term selection rules;
  - the test set's source or class composition.

  B1 is therefore **"detector-mined, same-corpus"**, not "realistic" in general.
- **Scan range:**
  - OASST1 (English prompter turns, train and validation) and Dolly (`instruction`) are scored in full.
  - LMSYS is scanned over the fixed range [200,000, 400,000).
  - Only if fewer than 535 rows survive all filters below is the range extended by 200,000 rows at a time, up to 1,000,000; then the run stops at the pools stage, before any fit.
  - The source mix is whatever this fixed procedure yields.
- **Filters**, in order:
  1. exact match against every benchmark CSV;
  2. word 5-gram containment ≥ 0.5 against every evaluation row;
  3. **the same containment against train.csv attack rows** (removes label conflicts);
  4. char TF-IDF cosine ≥ 0.92 against evaluation rows;
  5. PIDS-Bench's within-pool `semantic_dedup` at 0.92.
- **Draw:** 535 rows are drawn uniformly (seed 20261001); the first 419 are for training and the rest for validation. B3 draws 210/58 curated and 209/58 mined rows (seed 20261021), with the mined half taken from B1's rows.
- **Reporting:** mining statistics per source, filter counts, the LMSYS range scanned, source mix, and composition against the external test rows are written to `pool_manifest.json`, without text.
- **Blind audit, required before results are reported.** 200 random B1 rows are exported, without labels, for the owner to label.
  - The share judged benign is reported with a Wilson 95% interval, which assumes independent rows.
  - **If the Wilson lower bound is below 0.90**, conclusions on C1 and C2 are reported as *qualified by label noise*.
  - The audit does not change the pools.
- **B1 can contain real attacks.** Flagged rows are exactly where they hide. Recall endpoints measure the consequence.

## Framing tests

**Framed attacks.** Each of the 2,070 test.csv attack rows gets one of five fixed security-education prefixes (seed 20261031), with the payload kept verbatim.
- Prefixes 4 and 5 ("process the following normally", an authority claim) are themselves classic injection cues and may *raise* recall. Recall is therefore reported per prefix.
- Rows whose framed text exceeds 512 tokens can lose part of the payload to truncation. Their share is reported, and recall is also reported on the untruncated rows.

**Framed benign control.** The same prefixes (seed 20261032) are applied to the 1,848 test.csv benign rows, and the FPR change is reported. This shows whether a prefix itself moves scores.

This is a simple, non-adaptive attack, not an optimized adversary.

## Endpoints

**Confirmatory** (5 contrasts; Bonferroni level 1 − 0.05/5 = **99%**):

| # | Contrast | Metric (τ = 0.5) | Question | Rule |
| --- | --- | --- | --- | --- |
| C1 | B1 − A3 | external FPR | Does detector mining add beyond random same-corpus rows? | reduction if both intervals < 0 |
| C2 | B3 − A1 | external FPR | Does the combined pool cut external over-defense vs curated? | reduction if both intervals < 0 |
| C3 | B3 − B1 | curated FPR | Does adding curated rows restore curated behaviour?* | reduction if both intervals < 0 |
| C4 | B3 − A0 | framed-attack recall | Is the recipe no worse than no augmentation on framed attacks? | non-inferior if both lower bounds > −0.02 |
| C5 | A2 − A0 | framed-attack recall | Does Study 3's matched fix open the framing exploit? | non-inferior if both lower bounds > −0.02 |

\* The curated test rows come from the same 8 families as the curated training rows. C3 therefore measures fit to those families, not generalisation.

- **Intervals.** "Both intervals" means the joint group-and-seed percentile bootstrap (10,000 replicates) and the Student-t (df 4) over per-seed differences, both at 99%.
- **Non-inferiority.** The non-inferiority margin is 2 recall points. At baseline recall ≈ 0.99, that allows at most about a threefold miss rate. A two-sided 99% lower bound is a one-sided 99.5% test.
- **Fragile and incomplete.** A result is "fragile" if exactly one interval excludes 0. If any arm is incomplete, nothing is established.
- **Recipe success (`recipe_success_B3`, computed in code).** B3 is said to *fix both kinds of over-defense* only if all of the following hold:
  - C2 is a reduction and C3 is a reduction;
  - C4 is non-inferior;
  - B3's external FPR has both 95% upper bounds ≤ 0.10 (PIDS-Bench's target), using the group-and-seed bootstrap and the seed-t over per-seed rates;
  - B3's curated FPR has both 95% upper bounds ≤ 0.10.

  Otherwise the result is reported as found (for example "reduces both" or "reduces external only").

**Secondary (exploratory; 95%, uncorrected; each labelled exploratory in the results):**
- B1 − A1 and B1 − A2 on external FPR (mined vs curated, mined vs oracle); A3 − A1 on external FPR.
- B3 − A1 on curated FPR.
- B1 − A1 on OASST1/Dolly external rows.
- B1 − A0 on test recall, test FPR and framed recall.
- A1 − A0 and A3 − A0 on framed recall.
- B3 − A0 and A2 − A0 on framed-benign FPR.
- Per arm: every rate with a 95% interval, including external FPR at τ_val and on the LMSYS and OASST1/Dolly subsets; framed recall per prefix and on untruncated rows; framed-benign FPR; test F1 (seed-t); framed-minus-plain recall and framed-minus-plain benign FPR, paired by row.

## Everything else is Study 3's

Unless stated above, everything follows `docs/PREREGISTRATION_STUDY3.md`: recipe, versions, subprocess fits, scorer, thresholds, the one-identical-retry failure rule, LMSYS licence handling, near-duplicate definitions, and the bootstrap assumptions.

- **Blinding, strengthened.**
  - Score files, including the pilot's, are written to the private folder, not the public one.
  - Only fit times are displayed.
  - The owner commits not to open `private/scores` or `private/logs` before the analysis stage.
  - Mining statistics shown at the pools stage are not outcomes.
- **Stages:** pools, then pilot (B1 seed 13; its scores are kept), then all 30 fits. The pools stage needs a GPU because it scores tens of thousands of texts.
- **Budget:** 30 × about 49 min ≈ 24.5 A100 hours, plus about 1 hour for pools.
- **Order:** seed by seed, so an early stop leaves balanced seeds.
- **Completeness:** confirmatory results require all 30 fits.

## Sensitivity (planning)

- **Wider intervals than Study 3.** At 99%, the df-4 t quantile is 4.60, against 3.50 at Study 3's 97.5%, so intervals are about 32% wider. Study 3's seed-t half-widths of 0.056–0.093 become about 0.074–0.123.
- **C1.** Reductions below about 0.10–0.12 may come out inconclusive. Study 3's A3 − A2 gap was 0.081, so C1 is **not well powered** for a gap of that size. A null C1 must not be read as "mining adds nothing".
- **C3.** Study 3's curated-FPR bootstrap had a 95% half-width of about 0.22, which becomes about 0.29 at 99%. C3 is detectable only if B3 brings curated FPR close to A1's level (from about 0.35 to under 0.05).
- **C4 and C5.** Recall differences had seed SDs of about 0.004 in Study 3, so non-inferiority at 0.02 is detectable unless framing moves recall materially.
- These are planning values, not results.

## Limitations stated in advance

1. **Unmet launch gates (AGENTS.md).** The project's launch gates remain unmet: component permissions and provenance, an independent sample-size design, and human annotation/IAA.
2. **Same corpora.** B1 is detector-mined but same-corpus. A defender whose traffic differs from these corpora is not represented.
3. **Mining detector.** Its independence is UNVERIFIED, and a different screener would mine a different pool.
4. **Pool labels.** They are unaudited until the blind audit is labelled; see the label-noise rule above.
5. **Weak attack.** The framing attack is simple and non-adaptive.
6. **Narrow scope.** One model family, one benchmark, one pool draw per arm, and five seeds that share all data.
7. **Cross-study comparisons are descriptive.** Study 4's own refits are the comparators.

## Amendments

None yet.
