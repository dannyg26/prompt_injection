# InjecGuard release: benchmark overlap and template concentration

Data-only audit, 2026-09-24. No model was fitted or scored. Script: `scripts/audit_benchmark_overlap.py`. Output with input hashes: `results/audit/benchmark_overlap.json`. InjecGuard revision `cb1531f`. These are exhaustive counts on fixed files, not sampled estimates, so no confidence intervals apply.

## 1. Do evaluation items appear in training or validation data?

Containment is the share of an evaluation item's word 5-gram shingles found inside a single training (or validation) row.

| Evaluation file (as used by InjecGuard's `eval.py`) | Items | In train.json (containment ≥ 0.8) | Exact copies in valid.json |
| --- | ---: | ---: | ---: |
| WildGuard benign | 971 | 1 | 24 |
| BIPIA text attacks | 75 | 0 | 12 |
| BIPIA code attacks | 50 | 0 | 12 |
| NotInject one / two / three | 113 each | 0 / 0 / 0 | 16 / 16 / 16 |
| PINT | private | not audited | 48 PINT items in valid.json |

**Finding.** The public training file is effectively clean against the public evaluation files. The 144-item validation set used for checkpoint selection (`train.py`) consists of exact evaluation items. The InjecGuard/PIGuard paper says validation samples were selected from these datasets. That makes this a disclosed, bounded selection bias (about 14% of each NotInject subset, 16% of BIPIA text attacks, 24% of BIPIA code attacks and 2.5% of WildGuard were seen during selection), not undisclosed contamination. We do not infer misconduct.

## 2. Template concentration inside the training pool

Groups are transitive components of shingle containment ≥ 0.5 (the same rule as the adaptation study), computed over all 76,735 rows.

| Source and class | Rows | Groups | Rows per group | Largest group share |
| --- | ---: | ---: | ---: | ---: |
| HackAPrompt, attack | 5,000 | 6 | 833 | 56.9% |
| TaskTracker, attack | 3,316 | 893 | 3.7 | 1.4% |
| BIPIA, attack / benign | 558 / 558 | 186 / 186 | 3.0 | 30.5% |
| Question Set, attack | 1,643 | 553 | 3.0 | 30.4% |
| Vigil jailbreak, attack | 104 | 46 | 2.3 | 51.9% |
| safe-guard, attack | 2,496 | 1,445 | 1.7 | 12.9% |
| jailbreak-classification, attack | 527 | 313 | 1.7 | 29.4% |
| chatbot_instruction_prompts, benign | 16,000 | 15,497 | 1.0 | 0.4% |
| TaskTracker, benign | 11,386 | 7,557 | 1.5 | 0.3% |

All 28 source/class cells are in the JSON.

**Finding.** Attack classes are far more template-concentrated than benign classes. Benign sources are close to one row per group, while several attack sources have 2-800 rows per group, with up to 57% of a source in a single group. Row counts overstate the independent evidence about attack recall, and example-level intervals for recall are correspondingly too narrow. Study 2 (`docs/PREREGISTRATION_LEAKAGE.md`) measures how much.

**Limits.** Grouping is lexical, so paraphrased templates can escape it and short formulaic prompts can be over-grouped. Groups approximate templates; they are not verified template identities. PINT could not be audited.
