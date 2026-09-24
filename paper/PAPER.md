# Spending a Small Benign-Label Budget on a Prompt-Injection Detector Under Domain Shift: Threshold, Generic Data, or Matched Data?

*Capstone report draft. Preregistered study; locked single run. Author: Danny G. AI assistance: study code, analysis and drafting were produced with an AI coding assistant under the author's direction (disclosed per course policy).*

## Abstract

Prompt-injection detectors are typically trained on direct user prompts, but they are deployed where attacks arrive inside documents. We ask how a small budget of labeled *benign* examples from the new domain should be spent: on moving the decision threshold, on retraining with generic extra data, or on retraining with the target examples. We built grouped source, target and untouched pools from 61,819 licensed rows of the public InjecGuard release. Grouping treats reused templates and clean/poisoned document twins as single units. We then ran a preregistered, single-run comparison with a word+character TF-IDF logistic-regression detector, five label-draw seeds and joint group/seed bootstrap intervals.

At B = 200 benign labels, matched retraining did not improve target recall at 1% FPR over threshold-only adjustment (+0.10 points, 97.5% CI −0.18 to +0.49) or over generic retraining (+0.15, −0.16 to +0.47). Both intervals exclude a 2-point benefit. The reason is a floor. On document-embedded injections (TaskTracker) the source detector's AUROC is 0.648 (95% CI 0.635–0.661) and its recall is 3.1% (2.4–3.9) at a threshold whose target FPR is already on target, 1.0% (0.8–1.3). The failure is missed attacks, not false alarms, and benign-only labels cannot supply the missing signal.

Three secondary findings matter for practitioners and benchmark authors:
1. With fewer than about 100 benign labels, a threshold chosen to allow at most 1% of them overshoots the 1% target (2.9% FPR at B = 25), as order statistics predict.
2. Reusing the same labels for retraining and thresholding inflates FPR.
3. After grouping, 5,000 HackAPrompt attacks collapse to 7 templates. The detector catches 92% of attacks from calibration templates but 0% of one held-out obfuscation template, so per-row test metrics on such corpora can greatly overstate generalization.

## 1. Introduction

Prompt-injection detectors are classifiers placed in front of an LLM application to flag text that tries to override the application's instructions. They are usually trained on direct, user-typed attacks and chat prompts, then deployed where the dangerous text is *indirect*: instructions hidden inside retrieved documents, emails or tool outputs. Under that shift, two failures matter operationally. Clean documents are falsely blocked (over-defense), and hidden instructions are missed.

A team that deploys such a detector in a new setting can usually afford a small number of labeled *benign* examples from that setting, because clean documents are cheap to collect and verify. Labeled attacks from the new setting are much harder to obtain. The practical question is how to spend those few benign labels:

- **Threshold only.** Keep the model and move its decision threshold so that about 1% of the new benign examples are flagged.
- **Generic retraining.** Retrain with the same number of extra benign examples from the original distribution. This controls for "more data" without any domain match.
- **Matched retraining.** Retrain with the new-domain benign examples.

Broad domain adaptation for injection detection is already studied (CAPTURE; WAInjectBench, Appendix B; PromptShield's data-composition experiments; EvoShield's online test-time adaptation). PIDS-Bench states that distribution-matched augmentation was untested in its own experiments. We did not find this exact equal-budget, three-arm comparison with an untouched third domain in the ten works we audited. We do **not** claim global novelty (see `docs/RELATED_WORK.md`). The contribution is a controlled, preregistered measurement with group-aware uncertainty, plus a reproducible data-hygiene pipeline for public injection corpora.

## 2. Data

All data come from the public InjecGuard training release (GitHub revision `cb1531f`), which merges about 20 public sources and keeps a per-row `source` string. We admit only the 13 components whose own card or repository declares a license, for research use (`src/injection_lab/pools.py`, `docs/COMPONENT_PROVENANCE_AUDIT.md`). No raw text is redistributed.

- **Source domain S (direct prompts).** Instruction and chat prompts (Alpaca, chatbot_instruction_prompts, open-instruct, no_robots, UltraChat, Grok-harmless, awesome-chatgpt-prompts) plus HackAPrompt and jailbreak-classification attacks.
- **Target domain T (indirect, document-embedded).** TaskTracker: Wikipedia/SQuAD-style paragraphs, some carrying inserted instructions.
- **Untouched domain U.** BIPIA email, table and code contexts with and without injections; NotInject trigger-word benign prompts; WildGuard benign prompts. U is never used for training or thresholds.

**Grouping.** Public injection corpora are full of reuse. A poisoned document is often its clean twin plus one sentence, and attack templates recur with small edits. We link any two texts whose word 5-gram shingles overlap on at least half of the smaller text, take transitive components, and treat each component as one independent unit for partitioning and for the bootstrap. Evaluation-domain rows in a component shared with S are removed. The pipeline removed 1,952 exact duplicates and 5 label-conflicting texts. It also found that 5,000 HackAPrompt attacks reduce to 7 template groups. Section 5 returns to what that means for published per-row metrics.

| Partition | Benign | Injected | Independent groups | Role |
| --- | ---: | ---: | ---: | --- |
| S-train | 22,069 | 2,929 | 18,878 | detector fitting |
| S-cal | 10,031 | 1,331 | 10,124 | source thresholds (benign only) |
| S-generic-bank | 2,005 | - | 2,079 | generic arm |
| S-test | 6,018 | 799 | 6,110 | source retention |
| T-bank | 1,000 | - | 693 | revealed target labels |
| **T-eval** | **10,139** | **2,877** | **7,432** | **confirmatory evaluation** |
| U: BIPIA / NotInject / WildGuard | 235 / 339 / 964 | 557 / 0 / 0 | 185 / 339 / 938 | untouched domain |

## 3. Method

**Detector.** Word 1-2-gram TF-IDF (30k features) plus character 3-5-gram TF-IDF (50k), feeding class-balanced logistic regression. This is the unchanged legacy recipe with no tuning, CPU only.

**Arms at budget B ∈ {25, 50, 100, 200}** (B = 0 is the frozen source model for every arm):

| Arm | Model | Deployed threshold set on |
| --- | --- | --- |
| Frozen | source | 10,031 held-out source benign rows (1% FPR) |
| Threshold only | source | the B revealed target benign rows |
| Generic retraining | refit on source + B generic benign rows | source benign rows |
| Matched retraining | refit on source + the B target benign rows | source benign rows |
| Matched + threshold (secondary) | matched model | the same B target rows |

Five seeds (17, 29, 42, 71, 101) change which bank rows are revealed; budgets are nested. Evaluation rows are fixed. Seeds therefore measure sensitivity to the label draw and are not extra test data.

**Endpoints.**

- *Confirmatory:* target recall at the empirical 1% FPR point of the evaluation ROC, at B = 200. Two contrasts: matched vs threshold-only, and matched vs generic, with Bonferroni-adjusted 97.5% intervals.
- *Descriptive:* recall and FPR at each arm's deployed threshold, on the target, source and untouched domains.

**Inference.** A percentile bootstrap resamples evaluation groups and seeds jointly (10,000 replicates for the confirmatory contrasts, 2,000 for descriptive results). ROC cutoffs are recomputed in every replicate. Everything above was committed and pushed before scoring (`docs/PREREGISTRATION.md`, lock hashes in `results/study/PREREG_LOCK.json`).

## 4. Results

All numbers come from the locked run (models scored after preregistration commit `0f120e6`; `results/study/run_log.json`). Full tables for every arm, budget, domain and seed are in `results/study/RESULTS.md`, and the machine-readable version is `results.json`. Percentages are seed means over seeds 17, 29, 42, 71 and 101. Brackets are percentile bootstrap intervals that resample evaluation groups and seeds jointly, conditional on the fitted models and deployed thresholds. The seeds share one evaluation set, so they are not independent test examples.

### 4.1 Confirmatory contrasts (T-eval, recall at 1% FPR, B = 200)

| Contrast | Estimate (points) | 97.5% CI | Per seed (17/29/42/71/101) |
| --- | ---: | --- | --- |
| Matched − threshold-only | +0.10 | [−0.18, +0.49] | +0.14 / +0.14 / +0.10 / +0.14 / +0.00 |
| Matched − generic | +0.15 | [−0.16, +0.47] | +0.07 / +0.24 / +0.28 / +0.10 / +0.07 |

Neither contrast meets the preregistered superiority rule (interval above 0). Both upper bounds are below the 2-point practical margin, so a benefit of that size is ruled out for this detector and data. No bootstrap replicate was undefined.

![Target learning curves](figures/target_learning_curves.png)

### 4.2 Why nothing moved: a recall floor, not an over-defense problem

| Target (T-eval), B = 200 | Recall at 1% FPR | Recall at deployed threshold | FPR at deployed threshold |
| --- | --- | --- | --- |
| Frozen (B = 0) | 3.1 [2.4, 3.9] | 3.1 [2.4, 3.8] | 1.0 [0.8, 1.3] |
| Threshold only | 3.1 [2.4, 3.9] | 3.5 [1.3, 6.0] | 1.2 [0.3, 2.0] |
| Generic retraining | 3.0 [2.3, 3.9] | 3.1 [2.4, 3.7] | 1.0 [0.8, 1.2] |
| Matched retraining | 3.2 [2.5, 4.1] | 2.3 [1.8, 2.9] | 0.7 [0.5, 0.8] |
| Matched + threshold | 3.2 [2.5, 4.1] | 4.8 [1.9, 7.8] | 1.5 [0.5, 2.5] |

The threshold calibrated on source benign text already gives about 1% FPR on target documents. The detector does not over-block clean documents. It simply cannot rank injected documents above clean ones. A post-hoc, exploratory AUROC on the locked frozen scores is 0.648 [0.635, 0.661] on T, 0.717 [0.697, 0.738] on BIPIA and 0.951 [0.943, 0.998] on S-test (`results/study/exploratory_diagnostics.json`; group bootstrap, deterministic model, no seeds). Benign target examples can teach the model what clean documents look like. Matched retraining did lower target FPR (0.7%). But benign examples carry no information about what an injected instruction inside a document looks like, so recall cannot rise.

Descriptively, the prespecified sensitivity arm that weights the added rows ×20 raised recall at 1% FPR from 3.1 to 4.3 [3.2, 5.8] at B = 200. That is the only visible ranking gain, and it is small in absolute terms.

### 4.3 Small benign budgets cannot set a 1% threshold

With B benign labels, the "at most 1% flagged" rule places the threshold just above the maximum score whenever B < 100. The expected false-positive rate of that rule is 1/(B+1): 3.8% at B = 25, 2.0% at B = 50. The observed target FPR of threshold-only follows this: 2.9% [1.0, 4.9] at B = 25, 1.4% [0.3, 2.6] at B = 50, 1.2% [0.3, 2.0] at B = 200. Reusing the retraining labels to set the threshold (matched + threshold) was worse at every budget, because the model has already fit those rows. With ×20 weighting the FPR reached 13.2% [7.5, 19.3] at B = 25. The practical rule: a 1% operating point needs a few hundred held-back benign labels that were not used for fitting.

### 4.4 Untouched domain and hard benign text

Retraining arms with source-calibrated thresholds left BIPIA and NotInject behavior essentially unchanged. Arms that set the threshold from target labels did transfer their higher false-alarm rates: for example, BIPIA benign FPR was 7.1% [2.7, 13.4] for matched + threshold at B = 200, against 3.4% [1.5, 6.1] frozen (tables in `RESULTS.md`). The frozen detector flags 26.7% [24.0, 29.5] of WildGuard's benign but safety-sensitive prompts, against 1.8% [0.6, 3.2] of NotInject's trigger-word prompts. It confuses *harmful topics* with *injection*, which is a construct error that none of the adaptation arms addresses.

### 4.5 Template grouping changes what a held-out test means (exploratory)

After grouping, S-test's 799 attacks are one HackAPrompt template group (678 rows) plus 121 jailbreak prompts in 94 groups. Recall at the deployed threshold is 92.6% [87.4, 97.0] on the jailbreak prompts and **0.0%** on the held-out HackAPrompt template, a character-obfuscation attack written in Unicode mathematical letters separated by slashes. The same detector catches 91.8% of S-cal's 1,169 HackAPrompt attacks, but those come from only three templates, and their group-bootstrap interval is [0, 100]. With so few independent templates the data cannot distinguish "generalizes" from "memorized the templates". A row-level split would have mixed templates across train and test and reported high recall with a misleadingly narrow interval.

## 5. Discussion

**What the study shows.** For a lexical detector trained on direct prompts, spending up to 200 benign target labels, whether on thresholding, generic data or matched data, does not produce detectable gains in target recall at 1% FPR. The confirmatory intervals are tight enough to exclude a 2-point gain. The mechanism is clear from the descriptive results. The direct-to-indirect shift here is a *recall* failure (AUROC 0.65), and benign labels can only move the benign side of the decision.

**What it does not show.** It does not show that matched adaptation is useless in general. With a detector that ranks target attacks reasonably well, or with target *attack* labels, the ranking of the arms could change. That is the natural next experiment (Section 7). The results also say nothing about transformer detectors, which were infeasible on this CPU-only budget.

**Relation to prior work.** PIDS-Bench reports that curated-style augmentation and calibration do not close its externally sourced gap, and states that distribution-matched augmentation was untested. For benign-only matched data under an equal budget, we find no gain either. Our evidence adds a reason: when the gap is on the positive class, benign matching cannot close it. WAInjectBench (Appendix B) reports that adaptation can specialize without transferring; we observe no transfer harm from retraining itself to BIPIA or NotInject, but also no gain; target-derived thresholds do raise untouched-domain false alarms.

**Benchmark hygiene.** The grouping audit suggests that per-row test sets from template-heavy public corpora deserve skepticism. The HackAPrompt split shows 0% versus 92% recall depending on which templates land in the test set.

## 6. Limitations

- **Labels.** Upstream labels only. No human annotation or inter-annotator agreement was measured, and TaskTracker labels are construction labels (was an instruction inserted?). This preregistered gate stays unmet.
- **Detector.** One detector class (TF-IDF + logistic regression) with no tuning. Conclusions are scoped to it.
- **Data provenance.** Every domain comes from one merged release, and domains are defined by source string. Nested component licenses remain partly UNVERIFIED. Data were used for research only and not redistributed.
- **Grouping.** Grouping is lexical (word 5-gram containment). Semantic paraphrases can escape it, and short formulaic prompts are over-grouped.
- **Construct.** Recall here is text-classification recall, not agent attack success.
- **Interval scope.** Intervals condition on the fitted models and deployed thresholds. Seeds vary only which labels are revealed.
- **Exploratory material.** Sections 4.2 (AUROC) and 4.5 are post hoc diagnostics on locked scores and were not preregistered.

## 7. Future work

The single next experiment most implied by these results is equal-budget allocation between **benign and attack** target labels. It has to be preregistered separately, because AGENTS.md authorizes only this study. A second is repeating the design with a transformer detector once GPU access and Hugging Face data (PromptShield) are available.

## Reproducibility

The pinned InjecGuard clone (`cb1531f`) feeds the scripts in this order:

1. `scripts/build_study_pools.py` (deterministic; rebuilds byte-identical pools)
2. `scripts/run_adaptation_study.py` (81 fits, 16.4 minutes on 4 CPU cores)
3. `scripts/analyze_adaptation_study.py`
4. `scripts/exploratory_diagnostics.py`
5. `scripts/plot_adaptation_study.py`

Hashes are recorded in `results/study/PREREG_LOCK.json` and `run_log.json`. The environment was Python 3.11.15 on Linux with scikit-learn 1.7.2, numpy 2.2.6 and scipy 1.15.3. The raw text and score arrays are not committed (licenses, size), and each script refuses to overwrite its outputs.
