# Preregistration - Study 5: paraphrase provenance, attack safety, transfer and framing

**Status: frozen on lock; NOT YET AUTHORIZED TO RUN.** `scripts/run_study5.py` refuses to run until two conditions hold:

1. The owner adds an AGENTS.md amendment containing "PREREGISTRATION_STUDY5.md may be fit and scored".
2. `results/study5/PREREG_LOCK.json` matches a pushed commit.

No Study 5 pool has been drawn and no Study 5 model has been fitted. The rationale and the two pre-mortem reviews are recorded in `docs/STUDY5_DESIGN.md` (v1–v3). Where the two documents differ, this document governs; in particular, design item R9 (a NotInject floor check "after the lock and before any fit") is replaced by the floor rule under X2 below.

**Pre-lock code review (2026-10-05).** It found 4 blocking, 11 should-fix and 7 minor issues, all addressed in this document and the code:
- PIDS-Bench's executed paraphrase temperature is 0.7;
- evaluation text is frozen by fingerprint;
- analysis is gated on the audits;
- a failed non-inferiority test is read as inconclusive;
- T1 is gated on T3, with a share interval;
- HackAPrompt is moved to secondary;
- the framing rows are restricted and an academic control cell is added;
- seen system prompts include validation rows;
- equivalence rules are set for nulls;
- terms are matched at word boundaries, and paraphrases are checked for disjointness;
- audit consequences are fixed in advance.

## Questions

Studies 3–4 found that adding raw same-corpus benign text cut PIDS-Bench's external over-defense from about 0.31–0.34 to 0.06–0.14. But every PIDS-Bench train and test row, in both classes, is a GPT-4o-mini paraphrase. Study 5 asks four questions:

1. **Provenance shortcut (P1, P2).** Does the baseline treat unparaphrased text differently from its GPT-4o-mini paraphrase of the same content, for benign and for attack text?
2. **Train side (T1, T3).** Does the benefit of adding benign rows depend on their being unparaphrased?
3. **Attack safety (T2; HackAPrompt secondary).** Does adding unparaphrased benign text lower recall on unparaphrased attacks? The confirmatory attacks are SPML seeds. HackAPrompt competition rows are secondary.
4. **Transfer (X1, X2) and framing (F1).**
   - Is any user text enough, or must it come from the same corpora?
   - Does the fix transfer to an independent over-defense benchmark?
   - Does security vocabulary itself trigger flags, against academic-register prefixes without security vocabulary?

"Unparaphrased" is not "human": Alpaca and probably SPML are LLM-written. Origins are listed below and analysed separately.

## Materials

**Code and data versions**
- PIDS-Bench is used at commit 87dc835566b930ee921240874a4939b2c266c2fe, with its LMSYS test rows restored as in Study 3 (the stop rule if more than 33 rows stay missing also applies).
- InjecGuard is used at revision cb1531f36bffb38b6493438217b36cda8875da8a. From it we take NotInject (339 benign rows; MIT per its card) and the `hackaprompt-dataset` attack rows (5,000; MIT declared, gated upstream). Both licences are UNVERIFIED beyond those declarations.
- WildChat-1M is ODC-BY and openly accessible, as checked by the owner on 2026-10-02. Its revision SHA is recorded at run time.
- The Hugging Face SHAs of OASST1, Dolly, LMSYS-Chat-1M and deberta-v3-base are recorded, as in Studies 3–4.

**Recovering raw test seeds** (verified before the lock)
- A test row's `parent_seed_id` `{source}_seed_{i}` indexes row *i* of PIDS-Bench's `data/real_prompts/{source}.csv`.
- Rows are used only when the obfuscation is `none` and the label matches the source class.
- Each seed is linked to its 1–3 paraphrased test rows.

| Source | Class | Origin |
| --- | --- | --- |
| `alpaca_benign` | 0 | LLM, self-instruct (UNVERIFIED) |
| `chatbot_instructions_benign` | 0 | unverified |
| `sharegpt` (file content is OASST1) | 0 | human |
| `stackexchange` (file content is Dolly) | 0 | human |
| `spml_injection` | 1 | LLM (UNVERIFIED) |
| `deepset_injection` | 1 | human |

- Expected counts: about 696 benign seeds (97 human, 367 LLM, 232 unverified) and about 380 attack seeds. Of the attack seeds, about 284 are SPML, English, ≤ 512 tokens, and have a system prompt not seen in train or val.
- **"Seen system prompt"** means the first 80 normalised characters match a **train or validation** SPML seed (validation informs checkpoint selection). That stratum (about 87 seeds) is reported but is not confirmatory.
- **SPML file caveat.** PIDS-Bench's config names `spml_injection_classified.csv`, which is not in the repository. The mapping is verified only through `spml_injection.csv`.
- **Non-English seeds** are excluded from primary analyses. The English check is an ASCII-share heuristic plus a German function-word heuristic.
- **Seeds over 512 tokens** (DeBERTa tokenizer) are also excluded from primary analyses.

**Licence handling.** LMSYS and WildChat text is written only to the owner's private Drive folder. The public outputs contain fingerprints, counts and scores only.

**Frozen evaluation text.**
- At the pools stage, the exact-text SHA-256 of every row of every PIDS-Bench evaluation file is saved (`eval_fingerprints.json`; an empty row is recorded as empty).
- Before every fit and at analysis, the evaluation files actually used are checked against it; any difference stops the run.
- The external-row mask is built from the frozen fingerprints. This guards against restoring LMSYS rows differently after a Colab reconnect.
- This relies on PIDS-Bench's `rebuild_restricted.py` restoring the same text every time (it matches by fingerprint, so it should). Any difference, including a row that was empty at the pools stage and is restored later, stops the run rather than silently changing the test set.
- Text is read with Python's `csv` module without `newline=''`, so a carriage return inside a field reads as a newline. This affects scored and stored text identically.

## Pools

Each pool adds 419 training / 116 validation rows through PIDS-Bench's `train_and_tune`. A0 uses their `run_train`.

**O_raw: OASST1 and Dolly**
- Rows are English OASST1 prompter turns (train and validation) and Dolly instructions.
- Filters: Study 4's `generic_filter` (13 jailbreak markers and length 20–1000), and no exact match to any benchmark CSV or to PIDS-Bench's own OASST1/Dolly seed files.
- From a random 4,000 candidates (seed 20261005), we remove:
  - word 5-gram containment ≥ 0.5 against every evaluation row, every raw test seed, NotInject and PIDS-Bench's OASST1/Dolly seed files;
  - char TF-IDF cosine ≥ 0.92 against the same evaluation texts;
  - within-pool duplicates (`semantic_dedup` at 0.92).
- 735 rows are drawn uniformly (seed 20261006), the extra 200 as reserve.

**O_para: the same rows, paraphrased**
- Each row gets one direct paraphrase from `gpt-4o-mini-2024-07-18`, matching PIDS-Bench's paraphrasing **as executed**:
  - their prompt template ("Rewrite the following prompt preserving its intent while using diverse wording: {text}");
  - **temperature 0.7**, which `generators/realize.py:61` hard-codes; the config's 0.9 is unused;
  - their input sanitisation (`_sanitize_text`, copied as `sanitize_like_pids`).
- PIDS-Bench's own snapshot is UNVERIFIED. PIDS-Bench applied no validity filter; ours (below) is an addition that applies to both arms.
- A paraphrase is valid if:
  - it is non-empty and 20–1000 characters;
  - it is not a refusal;
  - it keeps every PIDS-Bench context term and injection keyword its source contains (word-boundary, case-insensitive match).
- An invalid paraphrase is regenerated once. A row that still fails is dropped from **both** arms.
- A valid paraphrase is also checked for disjointness (the same containment and TF-IDF filters as the raw pool). A pair whose paraphrase is hit is dropped from both arms.
- The first 535 surviving pairs, in draw order, form O_raw and O_para (419 training, 116 validation). If the universe is smaller than 735, all of it is drawn.
- The report gives drop counts by whether the source contained a term, plus the number of paraphrases that **add** a term their source lacked.
- If fewer than 535 pairs remain, the run stops before any fit.

**W_raw: WildChat**
- English, non-toxic, non-redacted first user turns.
- Same generic filter as O_raw, plus LMSYS-style moderation flags.
- Exact and near-duplicate disjointness against all evaluation texts.
- At most 27 rows (5% of 535) per word 5-gram containment group, applied before and after filtering.
- The first 5,000 candidates in stream order are used; 535 are drawn uniformly (seed 20261007).

**Audits** (blind; each 100 rows; owner-labelled; a second annotator on 50 rows each for IAA):
- W_raw: whether each row is benign.
- O_para: whether each paraphrase is "same meaning and benign" as its source.
- **The analysis stage refuses to run** until all four audit counts (W, O_para, Study 3 A2, Study 4 B1) are supplied. The `all` stage trains and scores but does not analyse, so labels are given before any result is seen.
- **Consequences fixed now:**
  - If fewer than 90/100 O_para pairs pass, T1 is not interpreted.
  - If fewer than 90/100 W rows are benign, X1 is still tested, but any X1 conclusion is stated as possibly driven by mislabelled (non-benign) W rows.
  - The analysis stage recounts the 1s in the two Study 5 audit files and refuses to run if any row is unlabelled or the typed counts differ. The Study 3/4 counts are typed by the owner.
  - Study 3/4 audits follow those studies' rules.

## Arms and fits

| Arm | Added rows | Seeds |
| --- | --- | --- |
| A0_none | none | 13, 42, 123, 2024, 7777, 31, 271, 9001 |
| O_raw | O pool, raw | same 8 |
| O_para | O pool, paraphrased | same 8 |
| W_raw | WildChat, raw | 13, 42, 123 |

- The recipe is PIDS-Bench's DeBERTa-v3-base recipe, unmodified, as in Studies 3–4.
- Fits run seed-major: A0, O_raw, O_para, then W_raw when the seed belongs to W. The pilot is O_para seed 13; its scores are kept.
- Failure rule: one identical retry, then the arm is marked incomplete.
- Seeds were not bitwise reproducible in Study 4, so **arms are treated as unpaired**. A0 checkpoints are kept privately in fp16. **Any later use of them is exploratory** and labelled as such.
- Budget: 27 fits × about 49 minutes ≈ 22 A100 hours.
- **Blinding.** Scores and logs are private. Only fit times are displayed. The owner commits not to open them before the analysis stage.

## Evaluation sets (frozen in the pools stage; every arm scores every set)

| Set | Rows |
| --- | --- |
| PIDS-Bench: external hard-benign, curated hard-benign, test, obfuscated, domain-OOD, structural-OOD | as in Studies 3–4 |
| Raw test seeds | unparaphrased text of each recovered seed |
| NotInject | 339 |
| HackAPrompt competition rows (level template plus participant submission; some over 512 tokens) | 5,000 |
| Framing | about 1,364 test benign rows (obfuscation none, source_type real) × 6 cells |

**Framing cells.** The five cells below have 24 prefixes each, fixed in `src/injection_lab/study5.py`, with every length within ±15% of the overall mean. Mean lengths are: academic 62.2, neutral 63.2, authority 63.5, security 66.4 and instruction 60.2 characters. Each row gets one seeded random prefix per cell.
- **academic:** academic register (seminars, theses, coursework) with no PIDS-Bench context terms, AI terms or injection keywords (checked). It is the control for F1.
- **neutral** and **authority:** no context terms, AI terms or injection keywords (checked).
- **security:** the same academic register, with security vocabulary and no imperatives. Every prefix contains a context term; 9 of 24 also contain a PIDS-Bench injection keyword (e.g. "jailbreak", "system prompt").
- **instruction:** injection-like by construction. Its flags are reported but never called benign FPR.
- **study4:** Study 4's 5 prefixes, as a replication cell.

## Confirmatory tests (8; Holm, family-wise α = 0.05)

| # | Test | Units resampled | Kind |
| --- | --- | --- | --- |
| P1 | A0: FPR on raw benign seeds − mean FPR over each seed's paraphrased test rows | content seeds × models | two-sided |
| P2 | A0: recall on raw SPML unseen-prompt seeds − recall on their paraphrases | content seeds × models | two-sided |
| T1 | O_para − O_raw: external FPR (τ = 0.5) | near-duplicate groups; seeds per arm | two-sided; gated on T3 |
| T2 | O_raw − A0: recall on raw SPML unseen-prompt seeds | seeds; seeds per arm | non-inferiority, margin 0.02 |
| T3 | O_raw − A0: external FPR | groups; seeds per arm | two-sided (gate) |
| X1 | (W_raw − O_raw) on LMSYS external rows − (W_raw − O_raw) on OASST1/Dolly external rows | groups; seeds per arm | two-sided |
| X2 | O_raw − A0: NotInject FPR | rows; seeds per arm | two-sided |
| F1 | A0: security-cell flag rate − academic-cell flag rate on the framing rows | parent_seed_id groups, prefixes within cell, models | two-sided |

**p-values and Holm**
- p-values come from bootstrap percentile inversion with 10,000 replicates and a named RNG stream per test.
- Non-inferiority p-values are one-sided: the share of replicates ≤ −0.02.
- Holm's step-down procedure assigns each test its α.

**"Established"** requires both of:
- Holm rejection;
- a companion interval at the Holm-adjusted level that agrees:
  - a t interval over per-model differences (P1, P2, F1, which are within-model);
  - a Welch interval over per-seed rates between arms;
  - for non-inferiority, the companion is the lower bound of the two-sided (1 − 2α) Welch interval, which must exceed −0.02.

- The companion interval must exclude 0 **on the same side as the estimate**.

If Holm and the companion disagree, the result is "fragile". If any arm is incomplete, nothing is established.

**Conservatism.** The bootstrap resamples both rows and seeds, so per-row Bernoulli noise enters twice. In a null simulation by the reviewer, nominal 5% tests rejected about 1% of the time. This makes established results conservative, and non-inferiority harder to show.

**T1 interpretation**
- T1 is interpreted only if T3 is established **and** the O_para audit passes; otherwise T1 is reported with `established = null`.
- T1 is reported as the **share of T3's reduction lost when the pool is paraphrased**, T1/(−T3). Its 95% and 90% intervals come from a joint bootstrap that resamples A0, O_raw and O_para seeds independently with shared row weights.
- "No style dependence" is claimed only if the 90% share interval lies inside ±0.25.

**Non-inferiority (T2).** "Non-inferior" requires Holm rejection and agreement. Failing to show non-inferiority is **inconclusive**. "Lowers recall" may be stated only if the upper bound of the two-sided (1 − 2α) interval lies below 0.

**Other nulls.**
- X1, X2 and F1 have no equivalence margins, so a non-established result is reported as **inconclusive**, never as "≈ 0" or "no effect".
- X2 floor: if A0's mean NotInject FPR is below 0.05, X2 is reported as uninformative (not established).

## Secondary (exploratory; 95%; uncorrected; labelled as such)

- P1 by origin (human / LLM / unverified), and P1 on length-matched seeds (raw length within ±20% of the mean paraphrase length).
- P2 on the seen-system-prompt stratum and on deepset seeds.
- HackAPrompt recall, O_raw − A0. It is secondary because rows cluster into about 6 template families, for which a percentile bootstrap is unreliable.
- W_raw effectiveness: W_raw − A0 on external FPR. "W_raw effective" means this 95% interval lies below 0.
- A0: security-cell flag rate against the neutral, authority and study4 cells.
- Every pairwise external-FPR contrast between arms on the LMSYS and OASST1/Dolly strata.
- Per-arm descriptive rates with 95% joint bootstrap intervals:
  - external FPR, curated FPR, test recall and FPR, HackAPrompt recall, NotInject FPR;
  - raw and paraphrased seed FPR and recall;
  - every framing cell's flag rate.
- Threshold-free metrics:
  - AUROC for external benign rows vs raw SPML attacks, and vs paraphrased test attacks;
  - external FPR at 95% recall on paraphrased attacks;
  - test F1;
  - all with t intervals over seeds.
- ProtectAI v2 and other released detectors are not scored in this study (out of budget). Framing on released detectors is future work.
- The instruction cell is reported as a flag rate, never as benign FPR.

## Interpretation fixed in advance

| Result | Statement allowed |
| --- | --- |
| P1 > 0 established | A0 flags unparaphrased benign text more than its GPT-4o-mini paraphrase. By origin: if it holds for LLM-written seeds, the cue is "not GPT-4o-mini style", not "human". |
| P2 < 0 established | Unparaphrased attacks evade A0 more than their paraphrases: a provenance-based evasion. |
| T1 > 0 established (gate passed) | The over-defense fix depends partly on the added rows being unparaphrased; the share interval says how much. |
| T2 non-inferior | Raw-text augmentation does not open a raw-attack hole of more than 2 points. Not non-inferior: inconclusive, unless the interval excludes 0 from above ("lowers recall"). |
| X1 < 0 established | Pools closer to the LMSYS rows (WildChat: chat-like and from the same era) help those rows relatively more. This does not separate "same corpus" from "chat-like". |
| X2 < 0 established | The fix transfers to NotInject. NotInject's sentences are LLM-generated (generator UNVERIFIED); if so, this is evidence against a pure "unparaphrased = benign" shortcut. |
| F1 > 0 established | Security vocabulary raises flags beyond academic register at matched length. Not established: inconclusive. |

## Limitations stated in advance

1. **Launch gates.** The project's launch gates remain unmet: component permissions and provenance, an independent sample-size design, and human annotation/IAA.
2. **Sources and origins.**
   - One training benchmark and one model family; NotInject and HackAPrompt are scored zero-shot only.
   - Unparaphrased ≠ human for Alpaca and SPML.
   - chatbot_instructions' origin is unverified.
   - Only 97 benign seeds are human.
3. **Paraphrases.** O_para uses one paraphrase per row, with possible snapshot differences from PIDS-Bench's paraphraser.
4. **HackAPrompt.** Rows combine organiser templates with submissions and form about 6 lexical groups, so the secondary HackAPrompt interval is unreliable.
5. **Weak attacker.** No adaptive or optimised attacker.
6. **Seeds.** Seeds share data, and arms are unpaired.

## Amendments

None yet.
