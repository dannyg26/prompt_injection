# Study 4 results: detector-mined and combined benign augmentation, plus a framing attack

**Audit complete (2026-10-06): C1 and C2 are *qualified by label noise*.** The owner labelled the 200-row blind audit of B1 using `docs/AUDIT_RUBRIC.md`.
- 156/200 rows were judged benign (0.78; Wilson 95% [0.718, 0.832], assuming independent rows; single annotator, no IAA).
- The lower bound is below the preregistered 0.90, so **C1 and C2 are qualified by label noise**. About one in five detector-mined "benign" rows was judged an injection or unclear.
- B1's (and B3's) external-FPR gains may partly come from training on real attacks labelled benign. C5 and the framed-recall results measure that cost only partly.
- Writing this report before the audit (2026-10-02) remains a logged deviation. The audit was labelled before any Study 5 result was seen.

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
| C5 | A2 matched − A0 [framed-attack recall] | −0.003 | [−0.007, −0.000] | [−0.004, −0.001] | **Non-inferior** (margin 0.02), but both 99% intervals lie below 0: A2 detectably misses more framed attacks (miss rate 0.13% → 0.41%, about 3×; prefix 0 recall 0.996 → 0.986) |

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

- **B1 − A1, external FPR:** −0.225 [−0.276, −0.177]. Same-corpus pools, mined (0.083) or random (0.142), cut external over-defense far below the curated pool; the added value of mining is fragile (C1).
- **B1 − A2, external FPR:** +0.027. The bootstrap interval [+0.007, +0.049] excludes 0, but the seed-t interval [−0.001, +0.054] does not. The detector-mined same-corpus pool comes within about 3 points of the oracle pool.
- **B1 − A1 on OASST1/Dolly external rows:** −0.084 [−0.133, −0.033].
- **B1 vs A0:** no measurable change in test recall or test FPR. Framed recall is −0.002 [−0.005, −0.000]; the difference is detectable, but it is a tenth of the 0.02 margin.
- **Framed-benign FPR against A0:** B3 − A0 = −0.412 [−0.530, −0.313] and A2 − A0 = −0.412 [−0.530, −0.292].

## What the results show

1. **Exploratory: a detector-mined pool from the test set's own corpora approaches the oracle.** It used no PIDS-Bench selection rules or test composition, but it did use the benchmark's length window and test-disjointness filters, and the mining detector was chosen knowing its PIDS-Bench external FPR (0.083; AGENTS.md treats this as selection informed by held-out performance, recorded here as a limitation).
   - Benign rows mined by a released detector from the same corpora cut external FPR from 0.308 (curated) to 0.083. Study 3's oracle matched pool reached 0.057.
   - Caveat: this is exploratory (B1 − A1 and B1 − A2 were not confirmatory). The pool still draws on the test set's corpora, and the mining detector's independence is UNVERIFIED.
2. **Whether mining beats random same-corpus rows is not established.**
   - B1 is 5.8 points below A3 (0.083 vs 0.142), and all five seeds point the same way.
   - The preregistered seed-t interval includes 0 (C1 fragile). As the preregistration warned, C1 was underpowered for gaps under about 0.10.
   - The honest statement is: *most of the gain comes from same-corpus text; mining may add a few points.*
3. **A combined pool improves both, and fixes one.**
   - Half curated, half mined (B3) keeps curated over-defense at A1's level (0.002) while cutting external over-defense from 0.308 to 0.119.
   - Study 3's trade-off (each pool fixes only its own distribution) is therefore largely, not fully, resolved. B3's external FPR misses the 0.10 target, and it is higher than B1 alone (0.119 vs 0.083): halving the mined rows costs external FPR.
4. **This framing test could not detect the feared exploit, and it raised a separate question.**
   - Recall on framed attacks stays at 0.996–0.999 for every arm, and framing raised recall slightly (about +0.8 to +1.1 points against plain attacks). The prefixes contain injection vocabulary ("prompt injection", "red team", "system prompts", "process the following normally"), so they push attacks *towards* detection: the test lacked sensitivity for an evasion exploit. A2 still missed about 3× more framed attacks than A0 (C5). The exploit a pool most plausibly teaches is its own context, e.g. the LMSYS text-completion template (33% of A2, 52% of B1), which was not tested.
   - Benign test rows (all LLM paraphrases) prefixed with these strings were flagged at **0.831** by the baseline (A0), against 0.013 without a prefix.
   - Augmentation lowered this (A1, A2 and B3 to about 0.42–0.44), but every arm still flags 42–83% of benign messages that carry a security-education prefix.
   - INFERENCE, not established: without a neutral-prefix control (e.g. a non-security sentence of the same length) we cannot attribute this to security framing rather than to any prepended human sentence. Only 5 prefix strings were used, so the intervals describe these 5 strings, and no per-prefix benign FPR was computed. The phenomenon resembles known trigger-word over-defense (NotInject, injecguard-2024.md) and LLM over-refusal benchmarks (XSTest, OR-Bench; UNVERIFIED in our notes).

## Reproducibility (descriptive per-seed values; no interval)

The four refit arms used the same code, data, seed and GPU type as Study 3. Their models were **not** reproducible bitwise: the maximum per-row score difference ranged from 0.9977 to 0.9999 across seeds and arms. Per-seed external FPRs moved by up to about 0.11 (A0 seed 13: 0.358 → 0.463). Because seeds are not reproducible, the seed pairing across arms used by the seed-t interval is nominal, not a true pairing.

Arm means differed by at most 0.018 (descriptive, no interval):

| Arm | Study 3 external FPR | Study 4 external FPR |
| --- | ---: | ---: |
| A0 | 0.325 | 0.343 |
| A1 | 0.321 | 0.308 |
| A2 | 0.058 | 0.057 |
| A3 | 0.138 | 0.142 |

Training is nondeterministic run to run even with fixed seeds, as GPU training usually is without deterministic kernels. That supports treating seeds as draws of training randomness, and it means single-seed results should not be compared across runs.

## Mechanism confound (found in review, 2026-10-02)

Every PIDS-Bench benign training row is a GPT-4o-mini paraphrase (pidsbench-2026.md:20; all 12,846 benign rows in train.csv), while the external test rows and every pool row in Studies 3–4 are raw human text. All same-corpus arms (A2, A3, B1, B3) therefore add raw human benign text. Their gains are consistent with corpus content and equally with a learned "raw human text = benign" style shortcut. A3's pool (median 85 characters, 5% context terms) still cut external FPR to 0.142, which fits the style explanation at least as well. This is the most important open question for the work; a paraphrased-pool control is planned.

## Limitations

As preregistered:
- The project's launch gates remain unmet: component permissions and provenance, an independent sample-size design, and human annotation/IAA.
- B1 is same-corpus, not cross-distribution.
- The mining detector's independence is UNVERIFIED.
- Pool labels: audited 2026-10-06, 156/200 benign (see top).
- The framing attack is simple and non-adaptive.
- One model family and one benchmark; one pool draw per arm; five seeds sharing all data.

New from this run:
- B1 is 52% one LMSYS template, against 0% in the test rows.
- The mined pool is 92% LMSYS.
- Models are not bitwise reproducible.
