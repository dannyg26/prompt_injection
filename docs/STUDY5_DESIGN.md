# Study 5 design draft v2: provenance shortcut, attack safety, transfer, framing

**Status: design draft v2 for a second pre-mortem, 2026-10-02. Not a preregistration. Nothing has been run.** v1 was reviewed by a pre-mortem (6 blocking findings). This version replaces it; v1 remains in the git history.

## Key facts that reshape the study (verified)

1. **Every row of PIDS-Bench's train and test, in both classes, is a GPT-4o-mini paraphrase** (`generator_model`: train has 12,846 benign + 14,247 attack rows; test has 1,848 + 2,070). The detector has never seen raw human text of either class. Every row added in Studies 3–4 was raw human benign text, so those arms may have learned "raw text = benign". That shortcut would be exploitable by raw-style attacks, which no Study 3–4 recall metric measured.
2. **The raw source text of 2,864 of the 3,918 test rows is recoverable from PIDS-Bench's own repo.** `parent_seed_id` `{source}_seed_{i}` indexes row *i* of `data/real_prompts/{source}.csv`.
   - Verified by char TF-IDF cosine between test rows and their mapped source rows: median 0.36–0.66 per source, against 0.05 for random pairs.
   - Raw seeds by class:
     - attacks: SPML 1,125 and deepset 24 test rows;
     - benign: Alpaca 852, ChatBot-Instructions 607, ShareGPT 182 and StackExchange 74 test rows.
   - Unmapped: templates and Qualifire.
   - So raw and paraphrased versions of the **same content** exist for both classes, and **no paraphrasing is needed on the test side**. This removes v1's paraphraser×corpus confound (B3) and its content-drift problem (B4) for every test-side contrast.
3. **NotInject** (InjecGuard; 339 benign LLM-generated sentences with 1–3 trigger words) is already in `data/raw/injecguard/datasets/`. It is an independent over-defense benchmark that can be scored zero-shot.
4. **PIDS-Bench's paraphrasing** (`config_v3.yaml`): GPT-4o-mini, prompt "Rewrite the following prompt preserving its intent while using diverse wording: {text}", **temperature 0.9**, 1–3 rounds per row.

## Arms

All arms use DeBERTa-v3-base with PIDS-Bench's recipe and their `train_and_tune`/`run_train`, unmodified. Each augmented arm adds 419 training / 116 validation rows. Deterministic kernels are requested only if the pilot shows a slowdown of at most 1.3×; otherwise per-row scores are kept and seeds are treated as unpaired.

| Arm | Added rows | Seeds | Role |
| --- | --- | --- | --- |
| A0 | none | 8 | baseline; test-side provenance tests |
| O-raw | 535 random OASST1+Dolly benign rows (raw), disjoint from the benchmark and from Study 3–4 pools | 8 | raw-text augmentation |
| O-para | **the same 535 rows paraphrased by GPT-4o-mini with PIDS-Bench's exact prompt, temperature 0.9, rounds drawn 1–3 as in PIDS-Bench** | 8 | train-side style test |
| W | 535 random English WildChat first user turns (raw); template share capped; disjoint from the test set | 5 | off-corpus raw text |

That is 29 fits × about 49 minutes ≈ 24 A100 hours, plus about 3 hours of headroom and scoring.

- **Why OASST1/Dolly and not A3 (LMSYS).** The pool must be paraphrased with PIDS-Bench's own paraphraser (GPT-4o-mini). LMSYS text may not be sent to a third-party API, but OASST1 (Apache-2.0) and Dolly (CC BY-SA 3.0) may; their licence terms are UNVERIFIED here. The OASST1/Dolly external rows (n = 208) also showed the effect in Studies 3–4.
- **Same rows in both arms.** O-raw and O-para are the same rows. Rows whose paraphrase fails validation (empty, refusal, length outside 20–1000 characters, or lost any PIDS context term or injection keyword the source had) are dropped from **both** arms and topped up from a common reserve.
- **Cut from v1, on the pre-mortem's advice:** DistilBERT, A2p and the second A3 draw. The hours go to more seeds instead.

## Evaluation sets (all frozen before any fit; all scored for every arm)

| Set | Content | Purpose |
| --- | --- | --- |
| External hard-benign | 872 raw rows | primary over-defense (Studies 3–5 comparable) |
| Paired provenance set, benign | unique raw benign seeds + their paraphrased test rows | test-side style |
| Paired provenance set, attacks | unique raw SPML/deepset attack seeds + their paraphrased test rows | **raw-attack recall** |
| Curated hard-benign, test.csv, obfuscated, domain/structural OOD | as before | continuity; domain-OOD benign is raw, non-security text |
| NotInject | 339 benign | independent over-defense benchmark |
| Framing sets | below | S6 |

## Confirmatory contrasts (Holm within each family, α = 0.05; "established" also needs bootstrap and seed-t to agree)

**Family P: provenance shortcut (test side, A0 only).** Paired at seed level; the bootstrap resamples seeds (content units) and models.
- **P1.** A0's FPR on raw benign seeds − FPR on their paraphrases.
- **P2.** A0's recall on raw attack seeds − recall on their paraphrases. *Negative means raw attacks evade the baseline.*

**Family T: train side.**
- **T1.** O-para − O-raw on external FPR. Positive means the gain from adding raw rows depends on their raw style.
- **T2.** O-raw − A0 on **raw-attack recall**, non-inferiority, margin 0.02. *Failure means raw-text augmentation opens a raw-attack hole.*
- **T3.** O-raw − A0 on external FPR, as a replication of the Studies 3–4 effect with a new pool.

**Family X: transfer.**
- **X1.** W − O-raw on external FPR. About 0 means any raw user text works; positive means same-corpus content matters.
- **X2.** O-raw − A0 on NotInject FPR, testing transfer to an independent over-defense benchmark.

**Equivalence.** "No difference" is claimed only via TOST with margin ±0.05 at 90%, using Welch intervals over seeds (seeds are not reproducible, so they are unpaired). Otherwise a null is reported as inconclusive.

**Threshold-free secondary metrics:** AUROC and FPR at 95% recall for external benign versus raw attacks and versus paraphrased attacks, per arm.

## S6 framing (secondary; one confirmatory test)

- **Cells:** four, each with 24 prefixes written before any score:
  - neutral;
  - security vocabulary;
  - authority claim;
  - processing instruction (injection-like by construction; stated as such).
- **Length matching:** prefixes are matched in length across cells (±15%).
- **Rows:** 1,000 paraphrased test.csv benign rows, and the same rows' raw seeds where they can be recovered.
- **Confirmatory (F1):** A0's FPR on paraphrased benign rows with the security-vocabulary cell − the neutral cell. The bootstrap is two-way clustered by prefix and by row. This replicates Study 4's setting with a neutral control.
- **Secondary:** ProtectAI v2 (pinned) and every arm on every cell; mixed-effects logistic regression with a prefix random effect.

## Power (from Studies 3–4 per-seed SDs; planning only)

- **External FPR.** Per-seed SDs are about 0.05–0.06 for A0-like arms and about 0.02–0.03 for augmented arms.
- **Unpaired Welch, 8 vs 8 seeds.** For T1 (both arms augmented, SD about 0.03), the 95% half-width is about 0.032. The detectable difference is about 0.045, which is 24% of the about 0.19 gain to be explained.
- **P1/P2** are paired within A0 over hundreds of seeds, so they have high power.
- **Equivalence at ±0.05** is reachable for T1, but not for contrasts that involve A0.

## Pre-mortem: every outcome pattern

| Pattern | Headline |
| --- | --- |
| P1 > 0, T1 > 0 | A provenance shortcut: detectors trained on LLM-paraphrased data treat raw text as suspicious, or once augmented as benign. A benchmark-validity finding with a practical warning. |
| P2 < 0 or T2 fails | **Security finding:** raw human-written attacks evade (or augmentation opens a raw-attack hole). |
| P1 ≈ 0, T1 equivalent to 0, X1 ≈ 0 | Content, not style: real user text fixes over-defense, transfers off-corpus, and is attack-safe if T2 holds. |
| X2 < 0 | The fix transfers to an independent over-defense benchmark. |
| F1 > 0 vs neutral | Security vocabulary itself triggers over-defense. F1 ≈ 0 means Study 4's 0.83 was not security-specific. |

## Requirements from the owner

- An OpenAI key as the Colab Secret `OPENAI_API_KEY`; cost about $1–3.
- The WildChat-1M terms accepted on Hugging Face (UNVERIFIED terms).
- The Study 3/4 audits, plus a 100-row audit of the O-para paraphrases (label preserved?) and a second annotator on 50 rows of each audit for IAA.

## Not addressed (stated limitations)

- A second benchmark is used for **training** only via NotInject transfer, which is zero-shot scoring.
- No optimised adaptive attacker.
- One model family.
- Project launch gates remain unmet.
