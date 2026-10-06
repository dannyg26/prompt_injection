# Study 5 results: paraphrase provenance, attack safety, transfer and framing

## Provenance

- **Lock and code:** run once under `results/study5/PREREG_LOCK.json`, which was locked at commit df17cb8. The fits ran on the locked tree. The analysis ran at commit de3056a, which differs from df17cb8 only in `AGENTS.md` (the owner's sixth amendment) and `docs/AUDIT_RUBRIC.md`. The runner verified all 12 locked file hashes. PIDS-Bench was at 87dc835, InjecGuard at cb1531f, and WildChat-1M at 7d6490e. The design is in `docs/PREREGISTRATION_STUDY5.md`.
- **Outputs:** `results/study5/study5_results.json` and `results/study5/pool_manifest.json`. The manifest holds hashes and counts only, no text. The analysis finished 2026-10-06T19:04Z with status `complete`.
- **Fits:** 27 fits in total, none retried, all on an NVIDIA A100-SXM4-40GB. Each took 48–50 minutes.
  - A0 (no augmentation), O_raw (raw OASST1/Dolly) and O_para (the same rows paraphrased by GPT-4o-mini) used seeds 13, 42, 123, 2024, 7777, 31, 271 and 9001.
  - W_raw (raw WildChat) used seeds 13, 42 and 123.
- **External set:** all 872 external hard-benign rows were present.
- **Seeds:** every number is a mean over the listed seeds. The seeds share all data, so they are not independent test examples. Seeds are not bitwise reproducible (Study 4), so arms are treated as unpaired.

## Pools

| | External test | O_raw | O_para | W_raw |
| --- | ---: | ---: | ---: | ---: |
| Rows | 872 | 535 | 535 | 535 |
| Median length (characters) | 298 | 66 | 85 | 106 |
| Rows with a PIDS-Bench context term | 100% | 0.9% | 2.1% | 6.9% |
| Rows with an injection keyword | 41% | 0.7% | 1.3% | 4.1% |

**Filter counts**
- O pool: 4,000 candidates → 3,892 available (96 removed by containment against evaluation rows, 12 as within-pool near-duplicates).
- W pool: 4,867 candidates → 4,134 available (12 removed by containment, 721 as within-pool near-duplicates).
- Paraphrasing: 740 attempts. 11 drops: 5 for term changes, 2 that added a term, and 4 for disjointness.

**Raw test seeds:** 696 benign seeds (97 human, 367 LLM-written, 232 unverified) and 380 attack seeds. Of the attacks, 284 are SPML seeds that are English, at most 512 tokens, and have an unseen system prompt.

None of these pools resembles the external test rows. That matters for reading T3 below.

## Blind audits (owner-labelled; rubric in `docs/AUDIT_RUBRIC.md`)

| Audit | Benign / valid | Share | Wilson 95% (assumes independent rows) | Preregistered consequence |
| --- | ---: | ---: | --- | --- |
| W_raw (Study 5) | 96/100 | 0.96 | [0.902, 0.984] | Passes (≥ 90). X1 is read normally. |
| O_para: same meaning **and** benign | **82/100** | 0.82 | [0.733, 0.883] | **Fails (< 90): T1 is not interpreted.** |
| Study 3 A2 (matched pool) | 197/200 | 0.985 | [0.957, 0.995] | Study 3's pool labels are supported. |
| Study 4 B1 (detector-mined pool) | **156/200** | 0.78 | [0.718, 0.832] | **The Wilson lower bound is below 0.90, so Study 4's C1 and C2 are *qualified by label noise*.** |

- These are single-annotator counts. The preregistered second annotator (50 rows per audit, for IAA) has **not** been done, so that is a limitation.
- For O_para, 18% of GPT-4o-mini paraphrases failed "same meaning and benign" at temperature 0.7. Every PIDS-Bench row was produced by the same model and prompt, but at an UNVERIFIED snapshot. **Our inference, not tested:** some PIDS-Bench rows may have drifted in meaning in the same way.
- For Study 4 B1, about one in five detector-mined "benign" rows was judged an injection or unclear. This supports the preregistration's warning that flagged rows are where real attacks hide.

## Confirmatory results (8 tests; Holm, family-wise α = 0.05)

Estimates are seed means at τ = 0.5. The bootstrap resamples content units and models. The companion interval is at the Holm-adjusted level: a t interval over models for within-model tests, and a Welch interval over seeds between arms. The 95% intervals shown are bootstrap percentile intervals.

| # | Contrast | Estimate | Bootstrap 95% | p | Holm α | Companion | Decision |
| --- | --- | ---: | --- | ---: | ---: | --- | --- |
| P1 | A0: FPR on raw benign seeds − on their paraphrases (n = 694 seeds) | −0.002 | [−0.007, +0.000] | 0.058 | 0.0167 | t [−0.005, +0.000] | Not established: **inconclusive** |
| P2 | A0: recall on raw SPML seeds − on their paraphrases (n = 284) | −0.001 | [−0.010, +0.009] | 0.891 | 0.05 | t [−0.003, +0.002] | Not established: **inconclusive** |
| T1 | O_para − O_raw: external FPR (n = 872) | +0.042 | [−0.006, +0.097] | 0.032 | 0.0125 | Welch [−0.019, +0.104] | **Not interpreted** (gate failed: T3 not established, and the O_para audit is 82 < 90) |
| T2 | O_raw − A0: recall on raw SPML seeds (non-inferiority, margin 0.02) | +0.000 | [−0.007, +0.008] | < 0.0001 | 0.00625 | Welch [−0.005, +0.006] | **Established non-inferior** |
| T3 | O_raw − A0: external FPR | −0.079 | [−0.153, −0.013] | 0.0012 | 0.0083 | Welch [−0.173, +0.016] | **Fragile** (Holm rejects; Welch includes 0) |
| X1 | (W_raw − O_raw) on LMSYS rows − the same on OASST1/Dolly rows | −0.086 | [−0.151, −0.016] | 0.002 | 0.01 | Welch [−0.196, +0.023] | **Fragile** |
| X2 | O_raw − A0: NotInject FPR (n = 339) | −0.028 | [−0.083, +0.023] | 0.235 | 0.025 | Welch [−0.087, +0.031] | Not established: **inconclusive** (A0 is 0.412, above the 0.05 floor) |
| F1 | A0: security-prefix − academic-prefix flag rate on benign rows (n = 1,364 per cell) | **+0.477** | [+0.268, +0.687] | < 0.0001 | 0.0071 | t [+0.304, +0.650] | **Established** |

- **T1 share (reported, not interpreted):** T1/(−T3) = 0.54, with a 95% interval of [0.05, 1.60] and a 90% interval of [0.13, 1.29].
- The 90% share interval is not inside ±0.25, so "no style dependence" cannot be claimed.
- Because the gate failed, nothing more is claimed from T1.

## Descriptive rates (seed mean; 95% joint group-and-seed bootstrap)

| Metric (τ = 0.5) | A0 none (8 seeds) | O_raw (8) | O_para (8) | W_raw (3) |
| --- | ---: | ---: | ---: | ---: |
| External FPR (n = 872) | 0.347 [0.291, 0.406] | 0.268 [0.228, 0.312] | 0.311 [0.261, 0.361] | **0.182** [0.136, 0.238] |
| Curated FPR (n = 600) | 0.581 [0.324, 0.798] | 0.467 [0.222, 0.690] | 0.503 [0.270, 0.718] | 0.466 [0.203, 0.716] |
| Test recall (n = 2,070) | 0.988 | 0.988 | 0.988 | 0.988 |
| Test FPR (n = 1,848) | 0.013 | 0.012 | 0.013 | 0.014 |
| NotInject FPR (n = 339) | 0.412 [0.357, 0.468] | 0.384 [0.329, 0.438] | 0.377 [0.319, 0.434] | 0.326 [0.280, 0.374] |
| HackAPrompt recall (n = 5,000; about 6 clusters, so the interval is unreliable) | 0.627 [0.272, 0.830] | 0.588 [0.257, 0.788] | 0.642 [0.271, 0.856] | **0.352** [0.111, 0.659] |
| Raw benign seed FPR (n = 694) | 0.004 [0.000, 0.009] | 0.003 [0.000, 0.006] | 0.004 [0.000, 0.009] | 0.003 [0.000, 0.007] |
| Paraphrased benign seed FPR | 0.007 [0.002, 0.013] | 0.006 [0.002, 0.012] | 0.007 [0.002, 0.012] | 0.008 [0.002, 0.015] |
| Raw SPML recall (n = 284) | 0.988 [0.974, 0.998] | 0.988 [0.974, 0.997] | 0.987 [0.973, 0.997] | 0.987 [0.972, 0.998] |

Test-set intervals are in the JSON; all lie within about ±0.008 of the estimates.

**Framing cells: share of benign test rows flagged with a prefix (n = 1,364 per cell)**

| Cell | A0 | O_raw | O_para | W_raw |
| --- | ---: | ---: | ---: | ---: |
| neutral | 0.019 [0.009, 0.029] | 0.014 | 0.019 | 0.018 |
| academic (control) | 0.027 [0.015, 0.043] | 0.020 | 0.023 | 0.015 |
| security | 0.504 [0.416, 0.595] | 0.398 | 0.425 | 0.399 |
| authority | 0.474 [0.415, 0.533] | 0.407 | 0.497 | 0.413 |
| study4 (Study 4's 5 prefixes) | 0.827 [0.772, 0.875] | 0.699 | 0.750 | 0.771 |
| instruction (injection-like; never called FPR) | 0.571 | 0.548 | 0.545 | 0.661 |

All intervals are in the JSON.

**Threshold-free metrics (t intervals over seeds)**

| | A0 | O_raw | O_para | W_raw |
| --- | ---: | ---: | ---: | ---: |
| External FPR at 95% recall on paraphrased test attacks | 0.227 [0.175, 0.280] | 0.161 [0.128, 0.195] | 0.182 [0.144, 0.220] | 0.084 [0.061, 0.106] |
| AUROC, external benign vs raw SPML | 0.984 | 0.987 | 0.988 | 0.993 |

**Exploratory contrasts (95%, uncorrected)**

| Contrast | Estimate | 95% |
| --- | ---: | --- |
| W_raw − A0, external FPR ("W_raw effective") | −0.165 | [−0.231, −0.101] |
| W_raw − A0, LMSYS external rows | −0.197 | [−0.275, −0.121] |
| W_raw − A0, OASST1/Dolly external rows | −0.062 | [−0.114, −0.020] |
| O_raw − A0, LMSYS external rows | −0.090 | [−0.152, −0.032] |
| O_raw − A0, OASST1/Dolly external rows | −0.041 | [−0.085, −0.005] |
| O_para − O_raw, LMSYS external rows | +0.049 | [+0.002, +0.102] |
| O_para − O_raw, OASST1/Dolly external rows | +0.021 | [−0.005, +0.050] |
| A0: security − neutral prefix | +0.486 | [+0.332, +0.638] |
| A0: security − authority prefix | +0.030 | [−0.174, +0.217] |
| A0: security − study4 prefix | −0.323 | [−0.551, −0.056] |
| HackAPrompt recall, O_raw − A0 (secondary; unreliable clusters) | −0.039 | [−0.101, +0.013] |
| P1, human seeds (n = 95) | −0.009 | [−0.030, +0.003] |
| P1, LLM seeds (n = 367) | −0.000 | [−0.002, 0.000] |
| P1, length-matched (n = 348) | −0.003 | [−0.008, 0.000] |

## What the results show

1. **Security-flavoured framing triggers this detector; a prefix by itself does not (F1, established).**
   - The baseline flags 50% of benign test messages that carry a security-education prefix. With an academic prefix of matched length and no security vocabulary, it flags 2.7%; with a neutral prefix, 1.9%. The difference is +0.48, 95% [+0.27, +0.69].
   - This answers Study 4's open question: the 0.83 framed-benign FPR was **not** caused by prepending any human sentence.
   - Caveats:
     - Authority prefixes ("as the system administrator…") trigger about as much (security − authority: +0.03, [−0.17, +0.22]). So the trigger is security or authority vocabulary, not "security" specifically.
     - Every augmented arm still flags 40–50% of these rows.
     - Only the A0 contrast is confirmatory.
     - The 24 prefixes per cell were written by us.
2. **No input-side provenance shortcut was detected (P1 and P2 inconclusive).**
   - A0 flags raw benign seeds at 0.4% and their paraphrases at 0.7%. On raw and paraphrased attacks, its recall is 0.988 for both.
   - The point estimates are tiny and the intervals lie within about ±1 point. Still, P1/P2 had no equivalence margin, so this is "not detected", not "absent".
   - Descriptively, raw text is clearly **not** what A0 flags: unparaphrased benign seeds get 0.4% FPR, against 35% on the external hard-benign rows. **Our inference:** the external over-defense is about content (context terms, injection-like vocabulary), not about text being unparaphrased.
3. **Raw-text augmentation did not open a raw-attack hole (T2, established non-inferior).** Adding 535 raw OASST1/Dolly rows left recall on raw SPML attacks within 2 points of A0.
   - Exploratory caution: W_raw's mean HackAPrompt recall is 0.35, against A0's 0.63. That contrast was not computed, and the HackAPrompt intervals are unreliable (about 6 template clusters, with very wide intervals). It is flagged as a possible safety cost of off-corpus chat augmentation that needs a proper test, not as a finding.
4. **The style-confound question is not resolved (T1 not interpreted).**
   - The design depended on (a) raw OASST1/Dolly augmentation clearly reducing external FPR (T3) and (b) faithful paraphrases. Neither held:
     - T3 is fragile: −0.079, and the Welch interval includes 0. The O pool is short, generic text (median 66 characters, 0.9% context terms), unlike Study 3's matched pool.
     - Only 82/100 paraphrases passed the audit.
   - Descriptively, paraphrasing the pool gave back about half of O_raw's small gain (share 0.54, 90% [0.13, 1.29]). That fits with **some** style dependence, but it is not a result.
   - Together with point 2, the evidence leans towards content over style. It does not settle the question.
5. **An off-corpus pool helps, especially on chat-like rows (exploratory; X1 fragile).**
   - 535 raw WildChat rows, which are not from any PIDS-Bench source corpus, cut external FPR from 0.347 to 0.182 (W_raw − A0: −0.165, [−0.231, −0.101]; 3 seeds).
   - At 95% recall on paraphrased test attacks, external FPR is 0.084 against A0's 0.227.
   - The gain is larger on LMSYS rows (−0.197) than on OASST1/Dolly rows (−0.062). The confirmatory interaction X1 is −0.086 and fragile.
   - Per the preregistration, WildChat is chat-like and from the same era as LMSYS, so this does not separate "same corpus" from "chat-like".
   - This is weaker than Study 3's oracle matched pool (0.058) and Study 4's mined pool (0.083, now label-noise-qualified). But it is the first pool here built with no access to PIDS-Bench's corpora.
6. **NotInject: inconclusive (X2).** A0 flags 41% of NotInject's benign trigger-word sentences. O_raw's change was −0.028 and not established. W_raw's 0.326 is descriptive only.

## Deviations and operational notes (logged)

1. **Audit rubric:** "benign" was undefined in the preregistrations. `docs/AUDIT_RUBRIC.md` defines it as *not a prompt-injection or jailbreak attempt*. It was committed (a620e19) after all fits finished, but before any audit row was labelled and before any result was seen.
2. **W audit file format:** the labelled W file was saved by Excel as a workbook with a `.csv` name. It was converted in Colab to a UTF-8 CSV, with a backup kept. The label column was checked unchanged: 100 rows, 96 ones, 4 zeros.
3. **Hidden errors in the notebook:** the notebook's output filter (`grep '\[study|Error|Traceback'`) hides the runner's `SystemExit` messages. The first analyze attempt failed on a missing file before computing anything. The successful run used `| tail -n 25` instead. The notebook is locked, so it was not edited.
4. **Stray file:** a stray copy of `audit_Opara_blind.csv` was uploaded into the private `logs` folder. The analysis reads only the main-folder copy.
5. **Study 3/4 counts:** the Study 3 and Study 4 audit counts were typed by the owner, as preregistered, and are not recounted by the runner.
6. **IAA:** the second-annotator IAA on 50 rows per audit was not done.

## Limitations

As preregistered:
- The project's launch gates remain unmet: component permissions and provenance, an independent sample-size design, and human annotation/IAA.
- One training benchmark and one model family. NotInject and HackAPrompt are scored zero-shot only.
- Unparaphrased ≠ human: Alpaca and SPML seeds are LLM-written (UNVERIFIED), chatbot_instructions' origin is unverified, and only 97 benign seeds are human.
- O_para uses one paraphrase per row, possibly at a different snapshot from PIDS-Bench's paraphraser.
- HackAPrompt clusters into about 6 template families.
- No adaptive attacker.
- Seeds share data, and arms are unpaired.

New from this run:
- W_raw has only 3 seeds.
- The O pool is far from the test rows in length and content, which limits T1/T3.
- The paraphrase audit failed, which blocks T1.
- The framing prefixes were written by the authors.
- The audits have a single annotator each.
