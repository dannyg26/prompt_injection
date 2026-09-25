# Study 3 plan: does distribution-matched benign augmentation fix external over-defense?

Draft, 2026-09-25. **Not preregistered yet, and no model has been run.**

## Question (the authors' own words)

PIDS-Bench (Shire and Kim, IEEE Access 14, 2026) found that DeBERTa-v3-FT flags 31.4% of externally sourced, security-adjacent benign prompts. Their 419 curated hard negatives removed over-defense on curated prompts but not on external ones (0.314 → 0.310; docs/literature/pidsbench-2026.md, pp. 13–14). They state:

> "What we have not tested is augmentation drawn to match the externally-sourced distribution rather than the curated pool; whether that would close the gap is open." (p. 19, §VIII-D; also p. 1, p. 14, p. 20)

Study 3 tests exactly this, on their released benchmark (github.com/ShirePyDev/Prompt-Injection-Detection-System, tag v1.0-pids-bench, commit 87dc835; code MIT; data research-only), using their own training recipe.

## Design (to be locked in a preregistration before any fit)

**Detector.** Their DeBERTa-v3-base recipe, unchanged: 3 epochs, learning rate 2e-5, maximum length 512, effective batch size 16, warmup 0.06. Their five seeds: 13, 42, 123, 2024, 7777.

**Arms.** Each arm adds the same number of benign rows, N = 419, to their training set:

| Arm | Added rows | Purpose |
| --- | --- | --- |
| A0 | none | Baseline; replicates their 0.314 |
| A1 | their 419 curated hard negatives | Replicates their null (0.314 → 0.310) |
| A2 | 419 **matched** rows: LMSYS/OASST1/Dolly drawn with *their* selection code (keyword + AI-adjacent classes, moderation filter), then exact- and semantic-deduplicated against every test, validation and hard-benign row, and grouped | The open question |
| A3 | 419 **source-only** rows: random benign rows from the same corpora, without their keyword/AI-adjacent selection | Separates "same corpus" from "same selection" (relates to their structure-vs-source decomposition, pp. 14–15) |

**Dose (secondary).** A2 at N = 50 and 150, to show how many matched rows are needed.

**Transfer check (secondary; no extra fits).** Draw the matched pool from LMSYS only. Then report external FPR separately on held-in LMSYS rows and on held-out-source OASST1 and Dolly rows. This separates learning the over-defense boundary from learning one corpus's style.

**Endpoints.**
- Primary: FPR on their 872 externally sourced hard-benign test rows at τ = 0.5 (their operating point). Contrasts: A2 − A1 and A2 − A0.
- Secondary: FPR at a validation-set threshold; FPR on their curated hard-benign rows; test F1 and recall; recall on obfuscated attacks (does matched augmentation cost recall?); per-source external FPR.

**Inference.** Paired over seeds (the same 5 seeds in every arm), with a group-aware bootstrap over test rows. Near-duplicate groups are used; their example-level bootstrap is reported alongside for comparability. Decision rule: a contrast is established if its 97.5% interval (two contrasts, Bonferroni) excludes 0. Practical margin: an FPR reduction of 5 points.

**Any outcome answers their question.**
- Matched augmentation closes the gap → the fix is data provenance, and its cost in recall is measured.
- It does not → over-defense is not fixed by in-distribution benign data either, which strengthens their "decision-surface" account.

## Requirements

- **LMSYS-Chat-1M access** (gated on Hugging Face; accept the licence). It is needed to restore their 664 LMSYS test rows, using their `rebuild_restricted.py`, and to draw the matched pool. Without it, the external set shrinks to about 208 rows.
- **GPU:** Colab A100. The primary arms are 4 × 5 = 20 DeBERTa-base fits and the dose arm adds 10. Estimated 15–25 minutes per fit, so roughly 8–12 A100 hours. A timing pilot on one fit comes first.
- **Remaining novelty check:** WAInjectBench (arXiv 2510.01354, App. B adaptation) and EvoShield (MDPI Mathematics, open access) must be read before the preregistration.
- **Owner approval** in AGENTS.md before any fit.

## Novelty check (2026-09-25; 16 papers read in full, page-cited notes in docs/literature/)

No paper read tests benign augmentation matched to an external distribution as a fix for detector over-defense:

- **PIDS-Bench** (pp. 1, 14, 19, 20) states the question is open.
- **EvoShield** adapts on LLM-labelled stream samples of either class. Over-defense is not an endpoint, and it has no before/after benign false-positive rate (evoshield-2026.md).
- **WAInjectBench v2** (§6, p. 8) adapts with malicious plus benign in-domain data for embedding detectors whose FPR was already 0. It has no benign-only, curated or threshold arm (wainjectbench-2025.md).
- **CAPTURE** and **InjecGuard** (MOF augmentation) are adjacent only.

The strongest wording allowed is "not found in the 16 papers we read". PIDS-Bench was published on 28 Aug 2026. Before submission, check papers citing it (Google Scholar "Cited by") for any later answer.
