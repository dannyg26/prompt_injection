# Study 5 design draft: style vs content, off-corpus transfer, second model, framing

**Status: design draft for pre-mortem review, 2026-10-02. Not a preregistration. Nothing has been run.**

## Purpose

Study 5 should resolve, in one run, every **major** objection raised by the independent review of Studies 3–4 (2026-10-02). The minor ones are documentation fixes, already applied.

| Review objection | How Study 5 answers it |
| --- | --- |
| D1. Style confound: all PIDS-Bench benign training rows are GPT-4o-mini paraphrases, while every added row is raw human text | S1 (test-side style) and S2 (train-side style) |
| D10. External validity: same corpora, one model | S3 and S4 (WildChat, a corpus never used by PIDS-Bench); second model family (DistilBERT) |
| D2 and D9. Framing test lacks sensitivity, neutral control and prefix variety | S5: factorial prefixes with neutral controls, released detectors, raw and paraphrased rows |
| D6. One pool draw | A second independent draw of the A3 pool |
| D8. Nondeterminism; models deleted | Deterministic kernels requested; every evaluation set built **before** fitting and scored at fit time; A0 checkpoints kept privately |
| D4. Unaudited labels | Blind audits of the paraphrased pool and of the new WildChat test set (200 rows each), plus a second annotator for IAA |
| D5. Mining detector chosen with known FPR | Not re-run here; disclosed as a limitation of Study 4 (B1 is exploratory) |

## Paraphrasing (owner's decision: both paraphrasers)

- **Prompt.** We use PIDS-Bench's exact prompt (`data_builder/config_v3.yaml`): "Rewrite the following prompt preserving its intent while using diverse wording: {text}". Temperature 0.7, one paraphrase per row.
- **OASST1/Dolly rows → GPT-4o-mini via the OpenAI API.** This is PIDS-Bench's own paraphraser. Both corpora's licences permit it, and the cost is a few dollars.
- **LMSYS rows → an open model run in the owner's Colab (Qwen2.5-7B-Instruct, pinned revision).** LMSYS-Chat-1M text may not be sent to a third-party API under its licence. The two-paraphraser setup is analysed per paraphraser as well as pooled.
- **Validity check.** A paraphrase is valid if it is non-empty, 20–1000 characters, not a refusal, and has char TF-IDF cosine ≥ 0.3 to its source. Invalid outputs are regenerated once, then dropped and counted.

## Arms

Each arm uses DeBERTa-v3-base with PIDS-Bench's recipe, seeds 13, 42, 123, 2024 and 7777, and adds 419 training / 116 validation rows.

| Arm | Added rows | Role |
| --- | --- | --- |
| A0 | none | baseline; test-side style test |
| A3r | Study 3 A3 pool (raw, random same-corpus) | content reference |
| A3p | **the same A3 rows, paraphrased** | **train-side style test** |
| A3r2 | second independent draw of random same-corpus rows | pool-draw variance |
| A2p | Study 3 A2 matched pool, paraphrased | does matched selection survive paraphrasing? |
| W | 535 random English WildChat first user turns (generic filter, disjoint) | **off-corpus raw text** |

That is 6 arms × 5 seeds = 30 DeBERTa fits, about 25 A100 hours.

**Second model family:** PIDS-Bench's own DistilBERT code (unmodified) for A0, A3r, A3p and W × 5 seeds. That is 20 fits, about 3 A100 hours (to be timed in the pilot).

## Evaluation sets (all built and frozen before any fit)

| Set | Rows | Purpose |
| --- | --- | --- |
| External hard-benign test, raw | 872 | primary over-defense endpoint (as Studies 3–4) |
| External hard-benign test, paraphrased | 872 | test-side style |
| Curated hard-benign | 600 | as before |
| test.csv attacks / benign | 2,070 / 1,848 | recall and FPR |
| **WildChat security-adjacent benign** | about 870 | new-corpus over-defense test. Built with PIDS-Bench's selection rules from WildChat rows disjoint from W's pool. Labels audited (200) |
| Framing sets | see S5 | — |

## Confirmatory contrasts (Bonferroni over 5, 99%; both bootstrap and seed-t intervals must agree, as before)

- **S1, test-side style.** A0's external FPR on the paraphrased external rows minus the same rows raw (paired by row).
  - Reading: strongly negative means raw human style drives over-defense; about 0 means style is not the driver.
- **S2, train-side style.** A3p − A3r on raw external FPR.
  - Reading: about 0 means content (corpus) drives the gain. Positive and approaching A0 means style drives it.
- **S3, off-corpus raw text.** W − A0 on raw external FPR.
  - Reading: negative means any raw user text helps, whatever the corpus.
- **S4, transfer to a new corpus.** A3r − A0 on WildChat security-adjacent FPR.
  - Reading: negative means the same-corpus pool's benefit generalises beyond its own corpora.
- **S5, framing.** ProtectAI v2 (pinned, released) on raw benign rows: FPR with security-vocabulary-only prefixes minus FPR with neutral prefixes.
  - The bootstrap is two-way, clustered by prefix and by row.

## S5 framing design

- **Prefixes.** Three binary factors: security vocabulary, authority claim, and processing instruction. That gives 8 cells, the all-zero cell being neutral. Each cell gets 8 hand-written prefixes, 64 in total, length-matched within ±15%. All prefixes are fixed in code before any score.
- **Rows.** 1,000 raw benign rows (OASST1/Dolly, disjoint from the benchmark and from all pools); the 1,848 paraphrased test.csv benign rows; and the 2,070 test.csv attacks. Each row appears once per cell, with a seeded random prefix from that cell.
- **Detectors.**
  - Released: ProtectAI v2 (pinned) and Prompt Guard 2 if accessible (recorded as unavailable otherwise).
  - Trained: every Study 5 arm, scored at fit time.
- **Analysis.** Per-cell FPR and recall with two-way cluster bootstrap intervals, plus main effects of each factor. A mixed-effects logistic model is a secondary analysis.

## Pre-mortem: every outcome yields a reportable result

| Outcome | Paper's headline |
| --- | --- |
| S1 strongly negative, S2 positive | PIDS-Bench's over-defense is largely a paraphrase-style artifact: detectors trained on LLM-paraphrased benign data flag raw human text. A benchmark-validity finding with a recommendation for benchmark builders. |
| S1 about 0, S2 about 0, S3 negative | Content, not style: raw user text from any corpus fixes over-defense. The practical recipe is validated off-corpus. |
| S1 about 0, S2 about 0, S3 about 0, S4 negative | Corpus-specific content matters. Matched data transfers to a new corpus, but random off-corpus text does not. |
| Mixed (e.g. S1 negative but S2 about 0) | Style explains test-side behaviour but not the training fix; both mechanisms are quantified. |
| S5 positive | Security vocabulary alone triggers over-defense in released detectors (with neutral controls). |
| S5 about 0 | The 0.83 effect in Study 4 was a "prepended human sentence" artifact, not security framing. |

## Budget

| Item | Estimate |
| --- | --- |
| DeBERTa fits | about 25 A100 h |
| DistilBERT fits | about 3 h |
| Paraphrasing and WildChat building | about 1–2 h |
| Framing scoring | about 1 h |
| **Total** | **about 30 A100 hours** |
| OpenAI API cost | a few US dollars |

**Requires from the owner:**
- an OpenAI API key (Colab Secret `OPENAI_API_KEY`);
- the WildChat-1M licence accepted on Hugging Face (licence terms UNVERIFIED here);
- the audits.

## What Study 5 does not fix

- One benchmark (PIDS-Bench).
- No optimised or adaptive attacker.
- Detector-mined pool (Study 4 B1) remains exploratory.
- Project launch gates (permissions/provenance, independent sample-size design, human IAA) remain unmet.
