# Preregistration: equal-label-budget adaptation of a prompt-injection detector

**Frozen 2026-09-24, before any study model was scored.** The lock file `results/study/PREREG_LOCK.json` records SHA-256 hashes of this document, the frozen pools and all study code. `scripts/run_adaptation_study.py` refuses to run unless those hashes match, the files are committed and the commit is pushed. The git history therefore shows this plan was fixed before results existed. The study runs once. Any later bug fix and rerun will be reported as a dated amendment, and both outputs will be kept.

## Authorization and what changed from the v0.3 specification

The project owner lifted the AGENTS.md launch gate on 2026-09-24 for this preregistered study only (see AGENTS.md). Three gates remain **unmet**, and they are reported as limitations, not waived:

- **Human annotation and IAA.** Only upstream labels are used. No inter-annotator agreement was measured.
- **Component-level license clearance.** Only components whose own card or repository declares a license are admitted, and only for research use. Nested upstream terms stay partly UNVERIFIED. No raw text is redistributed.
- **Independent sample-size design.** Every permitted evaluation row is used. The evaluation set was not sized to a target effect.

| v0.3 spec | This study | Reason |
| --- | --- | --- |
| PromptShield + InjecGuard pools | InjecGuard GitHub release only, revision `cb1531f` | Hugging Face is blocked from the compute environment; the InjecGuard release is on GitHub |
| DeBERTa-v3-small fine-tuning | Word+char TF-IDF logistic regression (unchanged legacy "combined" recipe) | CPU only (4 cores, no GPU). The conclusions apply to this detector class only |
| Domains S/T/U from Dolly/NI/SPP components | S = direct user prompts and chat; T = TaskTracker (instructions embedded in retrieved documents); U = BIPIA (email/table/code contexts), NotInject and WildGuard benign | These are the source strings available in the release, and they fit the direct-vs-indirect distinction |
| Budgets 0/50/200 (compact) | Full catalog 0/25/50/100/200 | Linear models are cheap; B=200 is the only confirmatory budget |
| Brier/NLL/ECE endpoints | Dropped | Out of scope for the confirmatory question; logistic scores are not claimed to be calibrated |

## Data and pools (frozen; no model used)

`scripts/build_study_pools.py` builds everything. Counts and hashes are in `results/study/pool_ledger.json`, and the row-to-group-to-partition map is in `results/study/pool_manifest.csv.gz` (IDs and text hashes only).

1. **Admission.** 13 components are admitted, each listed with its license evidence in `pools.py`. 14,203 rows from 11 other source strings are excluded: no verified component license declaration, legacy deepset, or a construct mismatch.
2. **Deduplication.** Text is normalized with NFKC, casefolding and whitespace collapse. Same-label exact duplicates are collapsed (1,952 removed). Every row of a text with conflicting labels is removed (5).
3. **Grouping.** Texts are represented as word 5-gram shingles. Two texts are linked when they share at least min(3, size of the smaller set) shingles and those shingles cover at least 50% of the smaller set. The search is exhaustive and links are transitive. This catches near-duplicates, a clean paragraph inside its poisoned copy, and templates or payloads reused inside longer texts. It over-groups some short, formulaic prompts; that is the conservative direction.
4. **Cross-domain overlap.** In a group that spans domains, the T/U rows are removed (66) and the S rows are kept, so no evaluation text shares a group with source data.
5. **Partitions.** Whole groups are assigned with seed 20260924. S groups are split 55/25/5/15 into S-train, S-cal, S-generic-bank and S-test, stratified by whether a group contains a positive and placed largest-first. Random T groups fill a T-bank until it holds 1,000 benign rows; the bank's 258 positive rows are discarded. Every other T group is T-eval. All U rows are evaluation-only.

| Partition | Benign rows | Positive rows | Groups | Use |
| --- | ---: | ---: | ---: | --- |
| S-train | 22,069 | 2,929 | 18,878 | All detector fitting |
| S-cal | 10,031 | 1,331 | 10,124 | Benign rows set source thresholds |
| S-generic-bank | 2,005 | (268 unused) | 2,079 | Benign rows for generic arm |
| S-test | 6,018 | 799 | 6,110 | Source retention (descriptive) |
| T-bank | 1,000 | 0 | 693 | Revealed benign target labels |
| T-eval | 10,139 | 2,877 | 7,432 | **Confirmatory evaluation** |
| U-eval BIPIA | 235 | 557 | 185 | Untouched domain (descriptive) |
| U-eval NotInject / WildGuard | 339 / 964 | 0 | 339 / 938 | Hard-benign FPR (descriptive) |

S positives are dominated by HackAPrompt templates, which collapse into 7 groups. S-test recall therefore rests on few independent templates and is descriptive only.

## Question, arms and thresholds

**Question.** With B labeled **benign** target-domain examples (B = 0/25/50/100/200), which works best:

- only moving the decision threshold,
- retraining with B extra generic source examples, or
- retraining with the B target examples?

Performance is measured on the target domain, and retention on the source and an untouched domain.

The detector is the legacy combined recipe: word 1-2-gram TF-IDF (30k features) plus char_wb 3-5-gram TF-IDF (50k features, sublinear), feeding `LogisticRegression(class_weight="balanced", C=1, max_iter=1000)`. There is no hyperparameter search. "Retraining" refits the full pipeline, vocabulary included, on S-train plus the added rows. The operating target is 1% FPR. A threshold set from n benign scores is the lowest threshold that at most floor(0.01n) of those scores reach, which for n<100 is just above the maximum.

| Arm | Model | Threshold from |
| --- | --- | --- |
| frozen (= every arm at B=0) | source | S-cal benign |
| threshold_only | source | the B revealed T-bank benign rows |
| generic | refit with B S-generic-bank benign rows | S-cal benign |
| matched | refit with the B revealed T-bank benign rows | S-cal benign |
| matched+threshold (secondary) | matched model | the same B revealed rows (in-sample reuse; no extra labels exist) |
| `_w20` variants (sensitivity) | as above, added rows weighted 20 | as above |

Seeds **17, 29, 42, 71, 101** each draw a random order of the T-bank and the generic bank. Budgets are nested prefixes of that order. The seeds vary which labels are revealed; the evaluation rows stay fixed and shared, so seeds are never counted as additional test examples. The sensitivity weight of 20 was fixed a priori to probe dilution of 200 rows among about 25,000; it was not tuned.

## Endpoints and decision rules

**Confirmatory (two contrasts; Bonferroni, familywise 5%).** The endpoint is T-eval recall at the largest empirical ROC point with FPR ≤ 1% (an evaluation-only cutoff, never deployed), averaged over the five seeds, at B=200:

1. matched − threshold_only (threshold_only keeps the frozen ranking, so this is matched − frozen)
2. matched − generic

**Inference.** 10,000-replicate percentile bootstrap (seed 20260924 = 20260923+1 stream) that jointly resamples T-eval groups with replacement and the five seeds with replacement. ROC cutoffs are recomputed in every replicate. Report 97.5% and 95% intervals, all per-seed values and any undefined replicates.

- **Superiority:** the 97.5% interval lies above 0.
- **Harm:** the interval lies below 0.
- **Practical margin:** 2 recall points. An interval entirely below +2 rules out a benefit of that size; an interval that crosses 2 is inconclusive about practical size.

**Descriptive (95% intervals, 2,000 replicates, same joint resampling, bootstrap seed 20260923).** Every arm and budget, reporting:

- on T-eval, S-test and U-BIPIA: recall at 1% FPR, and recall and FPR at the deployed threshold;
- on NotInject and WildGuard benign: FPR at the deployed threshold.

The operational question, whether a deployed threshold actually achieves about 1% FPR on T, is answered descriptively. Intervals condition on the fitted models and thresholds. No descriptive result is promoted to confirmatory.

## Pre-run disclosure

Before freezing, one source-only fit was timed on S-train (16.1 s; no rows were scored). Pool construction inspected counts, group sizes and a handful of example texts to verify parsing and overlap; it used no model. The grouping rules changed twice before any model existed:

- cross-domain removal was changed to drop only the evaluation-domain members;
- allocation was changed to place the largest groups first, after the first draft left S-test with 136 positives.

Both are recorded here.

## Limitations stated in advance

- Upstream labels only, with no IAA. TaskTracker labels come from construction (whether an instruction was inserted), not from human judgment.
- One detector class. TF-IDF behavior may not transfer to transformers.
- A single public release as the source of every domain. Domains are defined by source string and may still share hidden generators; lexical grouping is not semantic independence.
- TaskTracker positives are synthetic insertions. Recall here is text-classification recall, not agent attack success.
- The results answer this dataset and this detector. They do not establish the field-wide ranking of adaptation strategies.
