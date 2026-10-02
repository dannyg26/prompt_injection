# Study 4 results: detector-mined and combined benign augmentation, plus a framing attack

**PROVISIONAL.** The preregistration requires the 200-row blind audit of B1 before the results are reported. The owner has not yet labelled it. Until then, C1 and C2 cannot be finally qualified for label noise, and this document must not be cited as final.

## Provenance

- **Lock and code:** run once under `results/study4/PREREG_LOCK.json` at commit 7422529, with PIDS-Bench at commit 87dc835. The design is in `docs/PREREGISTRATION_STUDY4.md`.
- **Outputs:** `results/study4/study4_results.json` and `results/study4/pool_manifest.json` (fingerprints and counts only; no text). The analysis finished 2026-10-02T00:40Z.
- **Completeness:** all 30 fits completed on the first attempt (6 arms × seeds 13, 42, 123, 2024, 7777), all on an NVIDIA A100-SXM4-40GB, each taking 48–50 minutes. Status: `complete`.
- **External set:** all 872 external hard-benign rows were present.
- **Seeds:** every number is a mean over the 5 seeds. The seeds share all data, so they are not independent test examples.

## The mined pool (B1)

- **Mining:** ProtectAI v2 (pinned) flagged 433 of 14,887 OASST1 rows, 9 of 14,295 Dolly rows, and 8,320 of 81,277 LMSYS rows (stream indices 200,000–400,000; no extension was needed).
- **Filters:**
  - 8,762 mined rows;
  - −78 removed by containment against evaluation rows;
  - −0 removed against training attacks;
  - −0 removed by char TF-IDF;
  - −3,502 removed as within-pool near-duplicates;
  - leaving **5,182 available**.
- **B1 (535 rows):** 492 LMSYS, 41 OASST1 and 2 Dolly rows.
- **Composition against the external test rows:**

| | External test | B1 |
| --- | --- | --- |
| Rows on LMSYS's "you are the text completion model" template | 0% | **52%** |
| Rows with an injection keyword | 41% | 68% |
| Rows with a context term | 100% | 70% |
| Median length (characters) | 298 | 404 |

  The detector mined a pool quite unlike the test set: the mining detector flags this LMSYS template heavily.

## Confirmatory results (Bonferroni: 5 contrasts at 99%; both intervals must agree)

| # | Contrast [metric, τ = 0.5] | Estimate | Bootstrap 99% | Seed-t 99% | Decision |
| --- | --- | ---: | ---: | ---: | --- |
| C1 | B1 mined − A3 random same-corpus [external FPR] | −0.058 | [−0.096, −0.017] | [−0.125, +0.009] | **Fragile: not established** (bootstrap excludes 0, seed-t does not) |
| C2 | B3 curated+mined − A1 curated [external FPR] | **−0.189** | [−0.252, −0.137] | [−0.282, −0.096] | **Established reduction** |
| C3 | B3 − B1 [curated FPR] | **−0.334** | [−0.654, −0.049] | [−0.443, −0.226] | **Established reduction** |
| C4 | B3 − A0 none [framed-attack recall] | −0.003 | [−0.007, −0.000] | [−0.006, +0.000] | **Non-inferior** (margin 0.02) |
| C5 | A2 matched − A0 [framed-attack recall] | −0.003 | [−0.007, −0.000] | [−0.004, −0.001] | **Non-inferior** (margin 0.02) |

**Recipe success (B3 fixes both kinds of over-defense): FALSE.**
- C2, C3 and C4 all hold, and B3's curated FPR is 0.002 (95% upper bounds 0.007 and 0.005, below 0.10).
- But B3's external FPR is 0.119, with 95% upper bounds 0.151 (bootstrap) and 0.143 (seed-t), above the preregistered 0.10 ceiling.
- Under the preregistered rule, B3 **reduces both** kinds of over-defense but does not **fix** external over-defense.

## Descriptive rates (seed mean; 95% joint group-and-seed bootstrap)

| Metric (τ = 0.5) | A0 none | A1 curated | A2 matched (oracle) | A3 random same-corpus | B1 mined | B3 curated+mined |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| External FPR (n = 872) | 0.343 [0.264, 0.426] | 0.308 [0.264, 0.356] | 0.057 [0.037, 0.081] | 0.142 [0.106, 0.176] | **0.083** [0.057, 0.115] | 0.119 [0.091, 0.151] |
| Curated FPR (n = 600) | 0.618 [0.359, 0.833] | 0.000 [0.000, 0.002] | 0.316 [0.095, 0.568] | 0.514 [0.250, 0.752] | 0.336 [0.104, 0.580] | **0.002** [0.000, 0.007] |
| Test recall (n = 2,070) | 0.988 | 0.989 | 0.988 | 0.989 | 0.988 | 0.988 |
| Test FPR (n = 1,848) | 0.013 | 0.013 | 0.012 | 0.015 | 0.011 | 0.013 |
| Framed-attack recall (n = 2,070) | 0.999 [0.997, 1.000] | 0.997 [0.994, 0.999] | 0.996 [0.992, 0.999] | 0.997 [0.994, 1.000] | 0.997 [0.992, 0.999] | 0.996 [0.992, 0.999] |
| **Framed-benign FPR (n = 1,848)** | **0.831** [0.714, 0.929] | 0.436 [0.317, 0.559] | 0.419 [0.365, 0.497] | 0.703 [0.576, 0.831] | 0.614 [0.502, 0.724] | 0.419 [0.311, 0.528] |

Test-set intervals (recall and FPR) are in the JSON; all lie within about ±0.008 of the estimates.

### Exploratory contrasts (95%, uncorrected)

- **B1 − A1, external FPR:** −0.225 [−0.276, −0.177]. Detector mining cuts external over-defense far below the curated pool.
- **B1 − A2, external FPR:** +0.027. The bootstrap interval [+0.007, +0.049] excludes 0, but the seed-t interval [−0.001, +0.054] does not. The realistic pool comes within about 3 points of the oracle pool.
- **B1 − A1 on OASST1/Dolly external rows:** −0.084 [−0.133, −0.033].
- **B1 vs A0:** no measurable change in test recall or test FPR. Framed recall is −0.002 [−0.005, −0.000]; the difference is detectable, but it is a tenth of the 0.02 margin.
- **Framed-benign FPR against A0:** B3 − A0 = −0.412 [−0.530, −0.313] and A2 − A0 = −0.412 [−0.530, −0.292].

## What the results show

1. **A defender can get most of the oracle's benefit without the benchmark's selection rules.**
   - Benign rows mined by a released detector from the same corpora cut external FPR from 0.308 (curated) to 0.083. Study 3's oracle matched pool reached 0.057.
   - Caveat: this is exploratory (B1 − A1 and B1 − A2 were not confirmatory). The pool still draws on the test set's corpora, and the mining detector's independence is UNVERIFIED.
2. **Whether mining beats random same-corpus rows is not established.**
   - B1 is 5.8 points below A3 (0.083 vs 0.142), and four of five seeds point the same way.
   - The preregistered seed-t interval includes 0 (C1 fragile). As the preregistration warned, C1 was underpowered for gaps under about 0.10.
   - The honest statement is: *most of the gain comes from same-corpus text; mining may add a few points.*
3. **A combined pool improves both, and fixes one.**
   - Half curated, half mined (B3) keeps curated over-defense at A1's level (0.002) while cutting external over-defense from 0.308 to 0.119.
   - Study 3's trade-off (each pool fixes only its own distribution) is therefore largely, not fully, resolved. B3's external FPR misses the 0.10 target, and it is higher than B1 alone (0.119 vs 0.083): halving the mined rows costs external FPR.
4. **The feared exploit did not appear in this test, but a different problem did.**
   - Recall on framed attacks stays at 0.996–0.999 for every arm. Framing raised recall slightly (about +0.8 to +1.1 points against plain attacks), so security-education framing did not help attacks evade detection here.
   - The benign control shows why: the framing **itself** is treated as an attack signal. Adding the same prefixes to ordinary benign test messages raised FPR from 0.013 to **0.831** for the baseline (A0).
   - Augmentation lowered this (A1, A2 and B3 to about 0.42–0.44), but every arm still flags 42–83% of benign messages that carry a security-education prefix.
   - INFERENCE: this is a severe over-defense failure mode in its own right. The framing test was simple and non-adaptive, so it says nothing about optimised attacks.

## Reproducibility (descriptive per-seed values; no interval)

The four refit arms used the same code, data, seed and GPU type as Study 3. Their models were **not** reproducible bitwise: the maximum per-row score difference was about 0.998–0.999 for every seed. Per-seed external FPRs moved by up to about 0.11 (A0 seed 13: 0.358 → 0.463).

Arm means did reproduce:

| Arm | Study 3 external FPR | Study 4 external FPR |
| --- | ---: | ---: |
| A0 | 0.325 | 0.343 |
| A1 | 0.321 | 0.308 |
| A2 | 0.058 | 0.057 |
| A3 | 0.138 | 0.142 |

Training is nondeterministic run to run even with fixed seeds, as GPU training usually is without deterministic kernels. That supports treating seeds as draws of training randomness, and it means single-seed results should not be compared across runs.

## Limitations

As preregistered:
- The project's launch gates remain unmet: component permissions and provenance, an independent sample-size design, and human annotation/IAA.
- B1 is same-corpus, not cross-distribution.
- The mining detector's independence is UNVERIFIED.
- Pool labels are unaudited (blind audit pending).
- The framing attack is simple and non-adaptive.
- One model family and one benchmark; one pool draw per arm; five seeds sharing all data.

New from this run:
- B1 is 52% one LMSYS template, against 0% in the test rows.
- The mined pool is 92% LMSYS.
- Models are not bitwise reproducible.
