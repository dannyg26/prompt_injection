# Spending a Small Benign-Label Budget on a Prompt-Injection Detector Under Domain Shift: Threshold, Generic Data, or Matched Data?

*Capstone report draft. Preregistered study; locked single run. Author: Danny G. AI assistance: study code, analysis and drafting were produced with an AI coding assistant under the author's direction (disclosed per course policy).*

## Abstract

<!-- RESULTS:ABSTRACT -->

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

<!-- RESULTS:POOLTABLE -->

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

<!-- RESULTS:BODY -->
