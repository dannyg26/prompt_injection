# Preregistration - Study 5: paraphrase provenance, attack safety, transfer and framing

**Status: frozen on lock; NOT YET AUTHORIZED TO RUN.** `scripts/run_study5.py` refuses to run until two conditions hold:

1. The owner adds an AGENTS.md amendment containing "PREREGISTRATION_STUDY5.md may be fit and scored".
2. `results/study5/PREREG_LOCK.json` matches a pushed commit.

No Study 5 pool has been drawn and no Study 5 model has been fitted. The rationale and the two pre-mortem reviews are recorded in `docs/STUDY5_DESIGN.md` (v1–v3). Where the two documents differ, this document governs.

## Questions

Studies 3–4 found that adding raw same-corpus benign text cut PIDS-Bench's external over-defense from about 0.31–0.34 to 0.06–0.14. But every PIDS-Bench train and test row, in both classes, is a GPT-4o-mini paraphrase. Study 5 asks four questions:

1. **Provenance shortcut (P1, P2).** Does the baseline treat unparaphrased text differently from its GPT-4o-mini paraphrase of the same content, for benign and for attack text?
2. **Train side (T1, T3).** Does the benefit of adding benign rows depend on their being unparaphrased?
3. **Attack safety (T2, T2h).** Does adding unparaphrased benign text lower recall on unparaphrased attacks? The attacks are SPML seeds and HackAPrompt's human-written submissions.
4. **Transfer (X1, X2) and framing (F1).**
   - Is any user text enough, or must it come from the same corpora?
   - Does the fix transfer to an independent over-defense benchmark?
   - Does security vocabulary itself trigger flags, against neutral prefixes?

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

- Expected counts: about 696 benign seeds (97 human, 367 LLM, 232 unverified) and about 380 attack seeds. Of the attack seeds, about 291 are SPML, English, ≤ 512 tokens, and have a system prompt not seen in train.
- **"Seen system prompt"** means the first 80 normalised characters match a train SPML seed. That stratum is reported but is not confirmatory.
- **Non-English seeds** are excluded from primary analyses. The English check is an ASCII-share heuristic plus a German function-word heuristic.
- **Seeds over 512 tokens** (DeBERTa tokenizer) are also excluded from primary analyses.

**Licence handling.** LMSYS and WildChat text is written only to the owner's private Drive folder. The public outputs contain fingerprints, counts and scores only.

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
- Each row gets one direct paraphrase from `gpt-4o-mini-2024-07-18`. This matches PIDS-Bench's prompt ("Rewrite the following prompt preserving its intent while using diverse wording: {text}") and temperature 0.9. PIDS-Bench's own snapshot is UNVERIFIED.
- A paraphrase is valid if:
  - it is non-empty and 20–1000 characters;
  - it is not a refusal;
  - it keeps every PIDS-Bench context term and injection keyword that its source contains.
- An invalid paraphrase is regenerated once. A row that still fails is dropped from **both** arms.
- The first 535 valid pairs, in draw order, form O_raw and O_para (419 training, 116 validation). Drop counts are reported by whether the source contained a term.
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
- Results are reported only after the audits **and** the pending Study 3/4 audits are labelled.

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
- Seeds were not bitwise reproducible in Study 4, so **arms are treated as unpaired**. A0 checkpoints are kept privately in fp16.
- Budget: 27 fits × about 49 minutes ≈ 22 A100 hours.
- **Blinding.** Scores and logs are private. Only fit times are displayed. The owner commits not to open them before the analysis stage.

## Evaluation sets (frozen in the pools stage; every arm scores every set)

| Set | Rows |
| --- | --- |
| PIDS-Bench: external hard-benign, curated hard-benign, test, obfuscated, domain-OOD, structural-OOD | as in Studies 3–4 |
| Raw test seeds | unparaphrased text of each recovered seed |
| NotInject | 339 |
| HackAPrompt submissions | 5,000 |
| Framing | 1,848 test benign rows × 5 cells |

**Framing cells.** The four cells below have 24 prefixes each, fixed in `src/injection_lab/study5.py`, with every length within ±15% of the overall mean. Each row gets one seeded random prefix per cell.
- **neutral** and **authority:** no PIDS-Bench context terms or AI terms (checked).
- **security:** every prefix contains a context term and no imperatives.
- **instruction:** injection-like by construction. Its flags are reported but never called benign FPR.
- **study4:** Study 4's 5 prefixes, as a replication cell.

## Confirmatory tests (9; Holm, family-wise α = 0.05)

| # | Test | Units resampled | Kind |
| --- | --- | --- | --- |
| P1 | A0: FPR on raw benign seeds − mean FPR over each seed's paraphrased test rows | content seeds × models | two-sided |
| P2 | A0: recall on raw SPML unseen-prompt seeds − recall on their paraphrases | content seeds × models | two-sided |
| T1 | O_para − O_raw: external FPR (τ = 0.5) | near-duplicate groups; seeds per arm | two-sided; gated on T3 |
| T2 | O_raw − A0: recall on raw SPML unseen-prompt seeds | seeds; seeds per arm | non-inferiority, margin 0.02 |
| T2h | O_raw − A0: HackAPrompt recall | containment groups; seeds per arm | non-inferiority, margin 0.02 |
| T3 | O_raw − A0: external FPR | groups; seeds per arm | two-sided (gate) |
| X1 | (W_raw − O_raw) on LMSYS external rows − (W_raw − O_raw) on OASST1/Dolly external rows | groups; seeds per arm | two-sided; prediction: negative if same-corpus content matters, 0 if any user text works |
| X2 | O_raw − A0: NotInject FPR | rows; seeds per arm | two-sided |
| F1 | A0: security-cell flag rate − neutral-cell flag rate on paraphrased test benign rows | parent_seed_id groups, prefixes within cell, models | two-sided |

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

If Holm and the companion disagree, the result is "fragile". If any arm is incomplete, nothing is established.

**T1 interpretation**
- T1 is interpreted only if T3 is established, and it is reported as a fraction of T3.
- "No style dependence" is claimed only by TOST: both the 90% bootstrap and the 90% Welch interval must lie inside ±0.25·|T3|.
- Any other null is "inconclusive".

## Secondary (exploratory; 95%; uncorrected; labelled as such)

- P1 by origin (human / LLM / unverified), and P1 on length-matched seeds (raw length within ±20% of the mean paraphrase length).
- P2 on the seen-system-prompt stratum and on deepset seeds.
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

## Interpretation fixed in advance

| Result | Statement allowed |
| --- | --- |
| P1 > 0 established | A0 flags unparaphrased benign text more than its GPT-4o-mini paraphrase. By origin: if it holds for LLM-written seeds, the cue is "not GPT-4o-mini style", not "human". |
| P2 < 0 established | Unparaphrased attacks evade A0 more than their paraphrases: a provenance-based evasion. |
| T1 > 0 established | The over-defense fix depends on the added rows being unparaphrased. |
| T2 or T2h not non-inferior | Adding unparaphrased benign text lowers recall on unparaphrased or human attacks: the fix opens a hole. |
| X1 < 0 | Same-corpus content matters beyond "any user text". X1 ≈ 0 with W_raw effective: any recent chatbot user text works. |
| X2 < 0 | The fix transfers to NotInject (LLM-written), which is evidence against a pure "unparaphrased = benign" shortcut. |
| F1 > 0 | Security vocabulary raises flags against length-matched neutral prefixes. F1 ≈ 0 means Study 4's 0.83 is not security-specific. |

## Limitations stated in advance

1. **Launch gates.** The project's launch gates remain unmet: component permissions and provenance, an independent sample-size design, and human annotation/IAA.
2. **Sources and origins.**
   - One training benchmark and one model family; NotInject and HackAPrompt are scored zero-shot only.
   - Unparaphrased ≠ human for Alpaca and SPML.
   - chatbot_instructions' origin is unverified.
   - Only 97 benign seeds are human.
3. **Paraphrases.** O_para uses one paraphrase per row, with possible snapshot differences from PIDS-Bench's paraphraser.
4. **HackAPrompt.** It forms very few lexical groups (6 in Study 2), so T2h's interval is wide.
5. **Weak attacker.** No adaptive or optimised attacker.
6. **Seeds.** Seeds share data, and arms are unpaired.

## Amendments

None yet.
