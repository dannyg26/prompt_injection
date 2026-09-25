# Study 2 Part B: transformer and released detectors (results)

Locked run under Amendments 3–4 (commit `93e5ec9`). Run on Google Colab with an NVIDIA A100-SXM4-40GB, Python 3.13.15, torch 2.11.0+cu128; finished 2026-09-25T14:37Z.

Model revisions were pinned at first run: `microsoft/deberta-v3-small` `a36c739`; `protectai/deberta-v3-base-prompt-injection-v2` `90c9989`. `meta-llama/Llama-Prompt-Guard-2-86M` was unavailable (gated; no access), so it was excluded as specified and not replaced.

Raw output: `results/leakage/partb/partb_results.json` and `revisions.json`.

**Design.** 5 repeats (split seeds 31000–31004) of 70/30 row splits and randomized group splits. The 5 repeats share data and are not independent replications; intervals are 95% Nadeau–Bengio corrected, with J = 5. Labels are upstream; no IAA.

## 1. Primary endpoint: per-source recall inflation (row split − group split, recall at 1% FPR)

| Detector | Source | Row split | Group split | Inflation (points) [95% CI] |
| --- | --- | ---: | ---: | --- |
| TF-IDF | TaskTracker | 84.2 | 85.1 | −0.9 [−11.8, +10.1] |
| TF-IDF | BIPIA | 90.7 | 89.9 | +0.8 [−9.3, +10.8] |
| TF-IDF | jailbreak-classification | 88.2 | 89.7 | −1.5 [−4.1, +1.1] |
| DeBERTa-v3-small | TaskTracker | 98.0 | 97.9 | +0.2 [−1.2, +1.5] |
| DeBERTa-v3-small | BIPIA | 96.9 | 98.6 | −1.6 [−6.2, +2.9] |
| DeBERTa-v3-small | jailbreak-classification | 94.5 | 92.4 | +2.1 [−3.4, +7.6] |

**No inflation was established for any primary source with either detector:** every interval includes 0. For DeBERTa on TaskTracker the interval excludes inflation larger than 1.5 points. The TF-IDF intervals are wide, about ±10 points, because only 5 repeats were run.

**Consequence for Part A.** Part A reported TF-IDF inflation of +4.2 [+0.8, +7.6] on TaskTracker and +8.0 [+3.8, +12.2] on BIPIA. Part A used the largest-first splitter, which put the same large groups on the test side in every repeat. With the randomized splitter, the same detector shows −0.9 and +0.8, with intervals covering 0. The Part A per-source results did not replicate. The likeliest explanation is that they depended on which fixed groups sat in the test set. They are **withdrawn from current claims**; they remain in `docs/STUDY2_RESULTS.md` for the audit record.

Pooled and HackAPrompt rows (reported, not interpreted as inflation, per Amendment 2):

- TF-IDF pooled: +19.7 [−9.0, +48.4].
- DeBERTa pooled: +3.8 [−3.5, +11.2].
- HackAPrompt: TF-IDF +36.4 [−47.8, +120.6]; DeBERTa +6.7 [−10.3, +23.8]. These are not interpretable, because the group-split test sides contain 0–2 HackAPrompt templates.

## 2. HackAPrompt: each template held out in turn (7 templates; recall at 1% FPR; no interval)

| Template (rows) | 2,219 | 769 | 678 | 597 | 305 | 195 | 96 | Median |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| TF-IDF | 83.0 | 44.0 | 0.0 | 33.5 | 100.0 | 4.1 | 0.0 | 33.5 |
| DeBERTa-v3-small | 98.3 | 92.2 | 73.0 | 100.0 | 100.0 | 29.2 | 11.5 | 92.2 |
| ProtectAI v2 (not retrained)† | 97.7 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 43.8 | 100.0 |

Under row splits, both trained detectors reached about 100% recall on HackAPrompt: TF-IDF 100.0, DeBERTa 99.99.

- **Template-level held-out recall varies widely for both trained detectors.** The transformer generalizes across templates much better than TF-IDF (median 92% vs 34%). It still falls to 11–29% on two templates.
- With 7 templates, no sampling interval is claimed. These are per-template observations.

†ProtectAI v2 was not trained here, and its training data may include HackAPrompt. Its near-perfect HackAPrompt recall therefore cannot be read as generalization to unseen templates.

## 3. Design effects (group splits; median [range] over repeats with a defined value)

| Source | TF-IDF | DeBERTa | ProtectAI v2 |
| --- | --- | --- | --- |
| TaskTracker | 1.6 [1.3, 1.7] | 1.2 [1.0, 1.6] | 1.1 |
| BIPIA | 1.4 [1.1, 14.9] | 2.6 [1.5, 3.7] (2 repeats) | 2.6 |
| jailbreak-classification | 1.2 [1.1, 1.5] | 1.2 [1.1, 1.5] | 1.4 |
| HackAPrompt | 402 [17, 871] (3 repeats) | 147 [9, 356] (3 repeats) | 10.6 |

ProtectAI values are medians only. Design effects are above 1 wherever they are defined. That means example-level intervals for attack recall are too narrow: by a factor of about 1.1–1.6 on the indirect and jailbreak sources, and by one to two orders of magnitude on HackAPrompt.

## 4. A released detector on indirect injections (descriptive)

Recall at 1% FPR for ProtectAI v2, measured on the test side of the 5 randomized group splits. The FPR cutoff is set on all benign test rows. Values are the mean [min, max] over splits. No interval was prespecified for released detectors; the per-row scores are held on Drive, so a group-bootstrap interval can be added later if needed.

| Source | ProtectAI v2 recall at 1% FPR (%) |
| --- | --- |
| TaskTracker (instructions inside documents) | 27.1 [23.4, 30.1] |
| BIPIA (email/table/code contexts) | 29.8 [19.5, 40.0] |
| jailbreak-classification | 85.2 [81.7, 89.0] |
| HackAPrompt | 99.0 [97.7, 100.0] |

This released detector found about 27–30% of document-embedded injections at 1% FPR on these data, against 85–99% on direct attacks. Two caveats: overlap between its training data and these rows cannot be ruled out, and the benign mix defining the 1% FPR point is this study's, not the vendor's.

## What this changes

- **Withdrawn:** "row-random splits inflate recall on TaskTracker and BIPIA" (Part A). It was not supported once the splitter was fixed.
- **Supported, for both a linear and a transformer detector:**
  - Held-out template recall on a template-concentrated corpus (HackAPrompt) varies widely, while row splits report about 100%.
  - Attack-recall variance exceeds the example-level assumption.
- **Supported, descriptive:** a widely used released detector detected under a third of document-embedded injections at 1% FPR on these data.
- **Not claimed:**
  - that row splits never inflate results: small effects cannot be ruled out for TF-IDF, whose intervals were wide;
  - anything about Prompt Guard 2;
  - novelty relative to prior dataset-level work (still UNVERIFIED).
