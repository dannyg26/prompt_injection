# Study 6 results: security vocabulary in released detectors, and a trigger-word substitution attack

## Provenance

- **Lock and approval:** run once under `results/study6/PREREG_LOCK.json`, locked at commit a70edc3. The run used commit 3214e93, which differs only in `AGENTS.md`: the owner's seventh amendment. The design is in `docs/PREREGISTRATION_STUDY6.md`.
- **No training:** no detector was trained in this study.
- **Outputs:**
  - `results/study6/study6_results.json` (analysis finished 2026-10-22T22:28Z, status `complete_with_unavailable`);
  - `results/study6/prep_manifest.json`;
  - `results/study6/detector_revisions.json`.

  These hold scores, counts and hashes only; no text.
- **Scoring:** on Colab, 2026-10-06 22:41 to 2026-10-07 00:04 UTC.

**Detectors:**

| Key | Revision | Benign label |
| --- | --- | --- |
| ProtectAI v2 (`protectai/deberta-v3-base-prompt-injection-v2`) | 90c9989 (pinned) | SAFE |
| Prompt Guard 2 86M (`meta-llama/Llama-Prompt-Guard-2-86M`) | a8ded8e (pinned) | LABEL_0 |
| Prompt Guard 2 22M (`meta-llama/Llama-Prompt-Guard-2-22M`) | 11614a1 (resolved at run time) | LABEL_0 |
| deepset (`deepset/deberta-v3-base-injection`) | 80dda00 (resolved at run time) | LEGIT |
| A0 family: Study 5's A0 models, seeds 13, 42, 123, 2024, 7777, 31, 271, 9001 | fp16 checkpoints, scored in fp32 | LABEL_0 |
| InjecGuard (`leolee99/InjecGuard`) | **unavailable** | needs `trust_remote_code`, which the preregistration excludes; reported, not replaced |

**Other run details:**
- **Decision rule:** flag if 1 − P(benign) ≥ 0.5.
- **Eligible rows per detector:** 1,359–1,362 of 1,364 benign framing rows, and 1,649–1,660 of 1,665 attack rows. Rows were excluded only where a prefix would push the text past 512 tokens.
- **Substitution audit (owner, single annotator):** **49/50** substituted attacks kept their attack intent, a share of 0.98 (Wilson 95% [0.895, 0.996], assuming independent rows). It passes the preregistered 45/50, so the A tests are interpreted.
- **Seeds and intervals:**
  - A0-family rates are means over its 8 seeds. Those seeds share data and are not independent test examples.
  - Released detectors are single deterministic models, so their intervals reflect content sampling only.

## Confirmatory results (9 informative tests; Holm, family-wise α = 0.05)

| Test | Estimate | Bootstrap 95% | Holm α | Bootstrap at Holm level | Decision |
| --- | ---: | --- | ---: | --- | --- |
| F ProtectAI v2 (security − academic prefix, benign flag rate) | **+0.083** | [+0.031, +0.148] | 0.0056 | [+0.016, +0.185] | **Established** |
| F Prompt Guard 2 86M | **+0.076** | [+0.021, +0.147] | 0.0125 | [+0.012, +0.170] | **Established** |
| F Prompt Guard 2 22M | **+0.180** | [+0.077, +0.302] | 0.0083 | [+0.049, +0.349] | **Established** |
| F deepset | **+0.120** | [+0.040, +0.197] | 0.0167 | [+0.023, +0.214] | **Established** |
| A ProtectAI v2 (recall on changed attacks, plain − substituted) | **+0.039** | [+0.020, +0.060] | 0.0063 | [+0.013, +0.069] | **Established** (substitution evades) |
| A Prompt Guard 2 86M | **+0.118** | [+0.088, +0.149] | 0.0071 | [+0.078, +0.161] | **Established** |
| A Prompt Guard 2 22M | **+0.147** | [+0.114, +0.182] | 0.0100 | [+0.104, +0.193] | **Established** |
| A deepset | **−0.009** | [−0.018, −0.002] | 0.025 | [−0.020, −0.001] | **Established, opposite direction**: substitution slightly *raises* detection |
| A A0 family (8 seeds) | +0.001 | [−0.005, +0.007] | 0.05 | t over models [−0.001, +0.003] | Not established: **inconclusive** |

**Preregistered summary rules:**
- **F, shared across released detectors: TRUE.** The gap is established and positive in all 4 available released detectors, and negative in none.
- **A, shared across released detectors: FALSE.** It is established and positive in 3 (ProtectAI v2 and both Prompt Guard 2 models), but deepset's result is established in the opposite direction, and the rule requires none opposite.

## Descriptive rates (τ = 0.5; 95% bootstrap)

**Benign framing rows (PIDS-Bench paraphrased benign test rows, about 1,360 per cell): share flagged**

| Cell | ProtectAI v2 | PG2 86M | PG2 22M | deepset | A0 (8 seeds) |
| --- | ---: | ---: | ---: | ---: | ---: |
| no prefix | 0.007 [0.001, 0.015] | 0.000 | 0.000 | 0.414 [0.378, 0.453] | 0.010 [0.003, 0.019] |
| neutral | 0.007 [0.002, 0.012] | 0.001 | 0.003 | 0.652 [0.616, 0.686] | 0.019 [0.009, 0.029] |
| academic (control) | 0.004 [0.000, 0.009] | 0.000 | 0.002 | 0.742 [0.711, 0.773] | 0.028 [0.015, 0.044] |
| **security** | **0.087** [0.070, 0.103] | **0.076** [0.060, 0.092] | **0.182** [0.161, 0.204] | 0.862 [0.837, 0.885] | **0.504** [0.416, 0.593] |
| authority | **0.291** [0.264, 0.318] | 0.001 | 0.001 | 0.891 [0.870, 0.912] | 0.474 [0.418, 0.535] |
| study4 (Study 4's 5 prefixes) | 0.172 [0.149, 0.196] | 0.017 [0.010, 0.025] | 0.154 [0.135, 0.175] | 0.818 [0.792, 0.844] | 0.827 [0.772, 0.874] |
| instruction (injection-like; a flag rate, not an FPR) | 0.079 | 0.012 | 0.032 | 1.000 | 0.570 |

**Other benchmarks (false-positive rate)**

| Set | ProtectAI v2 | PG2 86M | PG2 22M | deepset | A0 (8 seeds) |
| --- | ---: | ---: | ---: | ---: | ---: |
| PIDS-Bench external hard-benign FPR (n = 872) | 0.083 [0.064, 0.104] | 0.107 [0.082, 0.132] | 0.130 [0.103, 0.158] | 0.825 [0.798, 0.852] | 0.347 [0.288, 0.408] |
| NotInject FPR (n = 339) | 0.428 [0.375, 0.478] | 0.065 [0.038, 0.091] | 0.077 [0.047, 0.106] | 0.705 [0.658, 0.758] | 0.412 [0.357, 0.470] |

**Attacks (PIDS-Bench test attacks without obfuscation, about 1,650 eligible)**

| Measure | ProtectAI v2 | PG2 86M | PG2 22M | deepset | A0 (8 seeds) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Plain recall | 0.848 [0.820, 0.873] | 0.386 [0.354, 0.420] | 0.432 [0.395, 0.467] | 0.938 [0.919, 0.955] | 0.989 [0.980, 0.995] |
| Recall with one security prefix | 0.868 | 0.560 | 0.585 | 0.989 | 0.999 |
| Recall on changed rows: plain → substituted | 0.905 → 0.865 | 0.535 → 0.417 | 0.604 → 0.457 | 0.970 → 0.979 | 0.993 → 0.992 |

**Evasion among attacks each detector catches in plain form** (black-box attacker; descriptive)

| Attacker | ProtectAI v2 | PG2 86M | PG2 22M | deepset | A0 (8 seeds) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Best of 24 academic prefixes | 0.173 [0.146, 0.202] | 0.248 [0.205, 0.292] | 0.203 [0.170, 0.240] | 0.039 [0.026, 0.053] | 0.005 [0.001, 0.009] |
| Best of 24 neutral prefixes | 0.077 [0.058, 0.097] | 0.199 [0.164, 0.236] | 0.156 [0.126, 0.186] | 0.010 [0.004, 0.016] | 0.005 [0.002, 0.009] |
| Best of 24 security prefixes | 0.140 [0.114, 0.165] | 0.193 [0.151, 0.234] | 0.210 [0.174, 0.249] | 0.002 [0.000, 0.004] | 0.000 [0.000, 0.001] |
| Substitution + best of 24 academic prefixes | 0.227 [0.195, 0.258] | 0.388 [0.334, 0.440] | 0.387 [0.342, 0.435] | 0.028 [0.019, 0.039] | 0.008 [0.003, 0.015] |
| Any of the 97 variants | 0.237 [0.205, 0.269] | 0.413 [0.361, 0.462] | 0.452 [0.404, 0.499] | 0.042 [0.029, 0.056] | 0.010 [0.004, 0.017] |

## What the results show

1. **Security-vocabulary over-flagging is shared by every available released detector (F, established for 4/4).**
   - On the same benign requests, a security-education prefix raised flags over a length-matched academic prefix by:
     - **+8.3 points** for ProtectAI v2;
     - **+7.6** for Prompt Guard 2 86M;
     - **+18.0** for Prompt Guard 2 22M;
     - **+12.0** for deepset.
   - Both Prompt Guard 2 models flag **0%** of these rows without a prefix and 0–0.2% with the academic prefix.
   - The gaps are much smaller in absolute terms than in our PIDS-Bench-trained models (A0: +48 points, Study 5). Released detectors are less sensitive, but not immune.
   - Prior work: InjecGuard showed trigger-word over-defense on NotInject (injecguard-2024.md). These results add a matched, register-controlled contrast.
2. **The trigger differs by detector.**
   - ProtectAI v2 is triggered most by **authority** prefixes (29% flagged, against 8.7% for security). Prompt Guard 2 is not (≤ 0.1%).
   - deepset flags 41% of benign rows with no prefix, and 65–74% with *any* prefix, so it barely separates benign from attack text here. Its F result is real but sits on a very high baseline.
   - INFERENCE: each detector has learned its own surface cues. "Security vocabulary" is a common one, not a universal mechanism.
3. **Swapping injection vocabulary for plain wording evades 3 of 4 released detectors (A, established; audit 49/50).**
   - Recall on the 882–891 changed attacks falls:
     - ProtectAI v2: 0.905 → 0.865 (−3.9 points);
     - Prompt Guard 2 86M: 0.535 → 0.417 (−11.8);
     - Prompt Guard 2 22M: 0.604 → 0.457 (−14.7).
   - It does **not** evade deepset (a slight increase, established) or our A0 models (inconclusive; recall stays at 0.99).
   - So the preregistered "shared" rule fails. The honest statement: "substitution evades ProtectAI v2 and both Prompt Guard 2 models; it does not evade a detector that flags nearly everything, or detectors trained on this benchmark's distribution."
   - There is no placebo-edit control, so this shows the substitution evades, not that the security words specifically are the cause. That is supported only jointly with F.
4. **A cheap black-box attacker gets past released detectors often (descriptive).**
   - Among attacks a detector catches in plain form, trying the substitution plus 24 academic prefixes evades:
     - ProtectAI v2 on **23%** of attacks;
     - Prompt Guard 2 86M on **39%**;
     - Prompt Guard 2 22M on **39%**;
     - deepset on 3%;
     - A0 on 0.8%.
   - Using all 97 variants: 24%, 41%, 45%, 4% and 1%.
   - Single prefixes barely change recall. The evasion comes from querying many variants (best of 24).
   - Academic prefixes evade more than neutral ones for every released detector. For ProtectAI v2, academic 17% vs neutral 8%.
5. **Prompt Guard 2 has low recall on these attacks at τ = 0.5: 0.39 and 0.43.**
   - Its documentation may recommend a different operating point (UNVERIFIED). The attacks are GPT-4o-mini paraphrases from PIDS-Bench, which may differ from its training distribution.
   - Prompt Guard 2 has low over-defense on NotInject (6.5–7.7%) and on unprefixed rows (0%). INFERENCE: it trades recall for low over-defense on these data.
   - Adding a security prefix to *attacks* raises its recall to 0.56–0.58, more evidence that its scores track vocabulary.
6. **PIDS-Bench external over-defense is far lower for ProtectAI v2 and Prompt Guard 2 (0.08–0.13) than for the benchmark's own detector (0.35).** These detectors were not trained on PIDS-Bench, so this is a level comparison only.

## Deviations and notes

- InjecGuard was unavailable (custom code), as the availability rule allows; 4 of 5 released detectors were scored.
- Scoring finished 2026-10-07. The analysis ran 2026-10-22, after the owner labelled the audit; the audit was labelled without opening the scores.
- The IAA stage has not run: the second annotator's labels are pending (`iaa_*` files exported, 50 rows per audit).

## Limitations

As preregistered:
- The project's launch gates remain unmet: component permissions and provenance, an independent sample-size design, and human annotation/IAA (IAA pending).
- Benign rows are PIDS-Bench paraphrases.
- The prefixes were written by the authors (24 per cell).
- There is one substitution table, and its audit has a single annotator.
- There is no placebo-edit control.
- Detector evasion is measured, not attack success against an LLM.
- The attacker is weak (no optimisation).
- Released detectors are scored at τ = 0.5, which may not be their deployed thresholds.
- The A0 models are fp16 copies.

New from this run:
- deepset's very high baseline flag rate makes its F and A results hard to compare with the others.
- Prompt Guard 2's low recall at τ = 0.5 means its evasion rates are computed on a smaller caught set: about 640–710 attacks, against about 1,400 for ProtectAI v2.
