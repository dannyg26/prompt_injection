# Study 2 Part A: row-random vs template-group splits (results)

Locked run after Amendment 1 (commit `a93623d`). Raw output: `results/leakage/split_comparison.json` and `RESULTS.md`. Linear TF-IDF detector; 20 repeats per split type (split seeds 31000-31019); 70/30 splits. Repeats overlap, so intervals are Nadeau–Bengio corrected; they are not independent replications. Upstream labels only, no IAA (see AGENTS.md gates).

## Prespecified results, with a validity check added after the run

| Recall at 1% FPR (unless noted) | Row split | Group split | Inflation (points) | 95% CI | Validity |
| --- | ---: | ---: | ---: | --- | --- |
| TaskTracker (document-embedded) | 84.5 | 80.3 | +4.2 | [+0.8, +7.6] | valid |
| BIPIA (email/table/code) | 91.2 | 83.2 | +8.0 | [+3.8, +12.2] | valid |
| jailbreak-classification | 88.4 | 87.0 | +1.4 | [−2.3, +5.1] | valid; no inflation detected |
| AUROC, all rows | 0.996 | 0.971 | +0.025 | [+0.022, +0.028] | valid, but includes the HackAPrompt issue below |
| Pooled recall (primary) | 93.4 | 74.6 | +18.8 | [+17.0, +20.7] | **confounded**, see below |
| HackAPrompt | 100.0 | 5.2 | +94.8 | [+92.9, +96.7] | **invalid as an interval** |

**Post-hoc validity finding (not preregistered).** The group splitter assigns groups largest-first, with randomness only in tie order, to keep partitions balanced. In every one of the 20 group splits, the test set therefore received the **same single HackAPrompt template** (195 rows). BIPIA test groups did vary (20 distinct sets; mean pairwise Jaccard 0.34).

Two consequences:

1. The HackAPrompt interval reflects only training-set variation around one template and is not a valid sampling interval.
2. The pooled primary estimate mixes true inflation with a composition change. Row-split tests hold about 1,450 easy HackAPrompt positives; group-split tests hold 195 hard ones.

Under the preregistered rule the primary interval lies above 0. We nonetheless do not interpret the +18.8 as the size of the inflation, and we treat the per-source rows as the evidence. This was a design error in the preregistration and is reported, not corrected after the fact.

## Leave-one-HackAPrompt-template-out (descriptive; valid)

| Held-out template (rows) | 678 | 769 | 305 | 195 | 597 | 2,219 | 96 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Recall at 1% FPR | 0.0 | 58.9 | 100.0 | 3.1 | 33.0 | 82.6 | 0.0 |

Median 33.0% over the seven templates, range 0–100, against 100% when HackAPrompt rows are split at random. There are only seven templates, so no sampling interval is claimed. This is the cleanest evidence in the project that row-level splits of template-heavy attack corpora measure template memorization.

## Design effects (group splits; median and range over 20 repeats)

| Attack source | Design effect | What it means for example-level 95% intervals |
| --- | --- | --- |
| TaskTracker | 1.5 [1.4, 1.6] | about 1.2× too narrow |
| jailbreak-classification | 1.5 [1.1, 1.7] | about 1.2× too narrow |
| BIPIA | 2.3 [1.6, 2.5] | about 1.5× too narrow |
| HackAPrompt | undefined | only one template per test set; no interval can be estimated at all |

## Conclusions this supports

1. Row-random splitting inflated recall at 1% FPR on indirect-injection sources: by 4.2 points (TaskTracker) and 8.0 points (BIPIA), with intervals excluding 0, for this detector.
2. On a template-concentrated attack corpus (HackAPrompt), per-template recall ranges from 0% to 100% (median 33%), while a row split reports 100%.
3. Example-level intervals for attack recall understate variance by a factor of about 1.5 to 2.3, meaning they are about 1.2 to 1.5 times too narrow. Where one template dominates, no interval is meaningful.

## Limits

- One linear detector only.
- Lexical groups approximate templates.
- The group splitter's near-deterministic placement of large groups (above) should be fixed before Part B, for example by randomizing assignment among groups of similar size, and preregistered as an amendment.
- Relation to prior work: see LEAKAGE_NOVELTY.md. Dataset-level leakage is already published; these are within-dataset results. The novelty of this framing is still UNVERIFIED.
