# Injection Lab: why prompt-injection detectors over-block, and how they can be evaded

A capstone research project on **over-defense** in prompt-injection detectors: classifiers that block harmless messages because they look like attacks. Six preregistered studies build on the open question left by PIDS-Bench (Shire & Kim, IEEE Access 2026): *does adding distribution-matched benign data fix external over-defense?* We answer that, then test **why** the problem occurs and whether **released detectors** share it.

**How the studies were run**
- **Preregistered.** Every study's design, tests and decision rules were frozen with SHA-256 hashes (`results/*/PREREG_LOCK.json`) before any result existed. The runners refuse to run on a modified tree.
- **Seeds and intervals.** Studies 3–5 report seed means with confidence intervals.
  - The seeds share all data, so they are not independent test examples.
  - Released detectors are single deterministic models; their intervals reflect content sampling only.
- **Blind label audits.** Augmentation pools and substitution sets were audited by hand. Failed checks are reported, and one non-replicating result is withdrawn.

## Main findings

| # | Finding | Evidence |
| --- | --- | --- |
| 1 | **Matched benign data cuts PIDS-Bench's external over-defense from 32% to 6%**, with no measurable loss in attack recall. This is an oracle setting: the pool uses the benchmark's own selection rules. | Study 3: A2 matched − A1 curated FPR = **−0.264**, 97.5% CI [−0.320, −0.210]; seeds 13, 42, 123, 2024, 7777 |
| 2 | **Detectors key on security vocabulary, not intent.** A security-education prefix makes the PIDS-Bench detector flag **50%** of benign messages, against **2.7%** for a length-matched academic prefix. | Study 5 F1: **+0.48**, 95% [+0.27, +0.69]; 8 seeds; Holm-corrected |
| 3 | **Every available released detector shares this over-flagging.** It holds for ProtectAI v2, Llama Prompt Guard 2 (86M and 22M) and deepset. | Study 6 F: **+0.083, +0.076, +0.180, +0.120**; all established (Holm), 4/4 |
| 4 | **Replacing injection vocabulary with plain wording evades 3 of 4 released detectors.** It is audited to keep attack intent (49/50). | Study 6 A: recall drops **3.9, 11.8 and 14.7 points** (ProtectAI v2, PG2-86M, PG2-22M). It does not evade deepset or the PIDS-Bench-trained models, so the preregistered "shared" rule is not met. |
| 5 | **A cheap black-box attacker evades often.** Substitution plus the best of 24 benign prefixes gets past released detectors on many attacks they otherwise catch. | Study 6, descriptive: ProtectAI v2 **23%** [20, 26], PG2-86M **39%** [33, 44], PG2-22M **39%** [34, 43] |
| 6 | **Common ways to build benign data are unreliable.** | Detector-mined "benign" rows: 156/200 benign (**22% not**). GPT-4o-mini paraphrases: 82/100 faithful (**18% not**). |

**What is *not* established:**
- whether a GPT-4o-mini writing-style shortcut contributes: the Study 5 test was blocked by its preregistered gates;
- that substitution evades *all* detectors;
- attack success against an LLM (we measure detector evasion only);
- behaviour of other model families;
- inter-annotator agreement for the audits (second annotator pending).

## Studies

| Study | Question | Status and result | Write-up |
| --- | --- | --- | --- |
| 1 | Do 200 benign target labels help domain adaptation? (linear detector) | Null: matched − threshold-only **+0.10 points**, 97.5% CI [−0.18, +0.49]; 5 seeds | [results](results/study/RESULTS.md) |
| 2 | Do row splits inflate detector recall (template leakage)? | Part A inflation **withdrawn** (did not replicate). Held-out HackAPrompt templates: recall 0–100% (median 34% TF-IDF, 92% DeBERTa) | [Part B](docs/STUDY2_PARTB_RESULTS.md) |
| 3 | Does distribution-matched benign augmentation fix external over-defense? | **Yes, in an oracle setting:** 0.32 → 0.06; curated over-defense rises to 0.36 | [results](docs/STUDY3_RESULTS.md) |
| 4 | Can a defender build the pool without oracle knowledge (detector mining, mixing)? | Mined pool 0.083, mixed 0.119 (misses the 10% target); **qualified by label noise** (78% audit) | [results](docs/STUDY4_RESULTS.md) |
| 5 | Why: writing-style shortcut, attack safety, transfer, framing? | Security framing established (+0.48); no attack-recall cost (non-inferior); style test not interpretable; WildChat pool 0.35 → 0.18 (exploratory) | [results](docs/STUDY5_RESULTS.md) |
| 6 | Do released detectors share the flaw, and can it be exploited? | Shared over-flagging (4/4); substitution evades 3/4; black-box evasion 23–39% | [results](docs/STUDY6_RESULTS.md) |

Each study has a preregistration in `docs/PREREGISTRATION*.md` and a lock in `results/*/PREREG_LOCK.json`. The audit labelling rubric is [docs/AUDIT_RUBRIC.md](docs/AUDIT_RUBRIC.md).

## Setup and models

- **Benchmark:** PIDS-Bench at commit `87dc835`. Its detector recipe is reproduced: DeBERTa-v3-base, 3 epochs, lr 2e-5, max length 512. Our baseline external FPR is 0.325, against 0.314 published.
- **Released detectors (Study 6):**
  - `protectai/deberta-v3-base-prompt-injection-v2` @ 90c9989;
  - `meta-llama/Llama-Prompt-Guard-2-86M` @ a8ded8e;
  - `meta-llama/Llama-Prompt-Guard-2-22M` @ 11614a1;
  - `deepset/deberta-v3-base-injection` @ 80dda00;
  - InjecGuard was unavailable (it requires remote code).
- **Compute:** 82 DeBERTa-v3-base fits of about 49 minutes each on Colab A100 (Studies 3–5: 25 + 30 + 27), plus Study 2 Part B (DeBERTa-v3-small) and Study 6 scoring (13 models, about 1.4 hours).

## Repository layout

```
src/injection_lab/      pure, tested logic per study (study3.py ... study6.py)
scripts/run_study*.py   Colab runners: verify lock -> build pools -> fit/score -> analyze
notebooks/              one Colab notebook per GPU study
docs/                   preregistrations, results write-ups, audits, literature notes
results/                locks and result JSON (scores, counts and hashes only; no text)
tests/                  unit tests (pytest)
paper/                  draft paper (currently covers Studies 1-2; being revised for 3-6)
```

## Reproducing

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-lock.txt && pip install --no-deps -e .
pytest -q && ruff check src scripts tests
```

GPU studies (3–6) run in Colab through `notebooks/study*_colab.ipynb`, with Hugging Face access as a Colab secret (Prompt Guard 2 is gated under Meta's licence). Each runner refuses to run unless:
- its lock matches;
- the tree is clean and pushed;
- the owner's approval line is present in `AGENTS.md`.

Locked results must not be overwritten.

## Data and licences

- **No dataset text is committed.** LMSYS-Chat-1M (no redistribution) and WildChat-1M text stay in the owner's private storage; the repository holds only hashes, counts and scores.
- Component licences beyond their declarations are **UNVERIFIED**. This is research use only.

## Limitations

- One main benchmark (PIDS-Bench), and one trained model family (DeBERTa-v3).
- Benign evaluation rows are GPT-4o-mini paraphrases.
- The prefixes and the substitution table were written by the author.
- Audits have a single annotator so far.
- No optimised or adaptive attacker.
- Released detectors are scored at τ = 0.5.
- The project's own launch gates (independent sample-size design, full annotation/IAA, component clearance) remain unmet and are reported as limitations in every study.

Research rules for this repository are in [AGENTS.md](AGENTS.md). Project status is in [docs/STATUS.md](docs/STATUS.md).
