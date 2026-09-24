# Data repair and withdrawal record

Completed 2026-09-23 after the reference audit and related-work table, before repaired models were fitted. No detector features or architectures were added. This is exploratory because original test examples had already been inspected.

## Changes

Of 662 original records, **627 retained**, **33 redundant members removed**, **2 mixed-label records quarantined**. There were **0 normalized exact duplicates**; removals arose from near-duplicate grouping. Quarantine is not relabeling.

For seeds **17, 29, 42, 71, 101**, each new split has 412 training records (159 positive, 253 benign), 105 validation (41 positive, 64 benign), 110 test (42 positive, 68 benign). Previous proportions are approximately preserved; previous test membership is not.

1. Normalize NFKC, case and whitespace for deduplication only.
2. Build a graph from exact matches, raw/normalized character-TF-IDF cosine >=0.90, and symmetric sequence-match similarity >=0.90.
3. Form connected components. Quarantine mixed-label components; retain one content-hash/ID-selected representative per homogeneous component, independent of old split/model output.
4. Stratify retained components with five prespecified seeds. Add high-cosine edges exposed by split-specific vocabularies; repeat before fitting. Closure took three iterations.
5. Assert group disjointness and no qualifying raw/normalized cross-split cosine pairs for every seed, then fit unchanged baselines.

This establishes lexical disjointness under declared rules, not semantic independence. Transitivity can over-group distinct examples. Unknown shared generation templates and contextual label errors remain possible; quarantined labels await human adjudication.

## Results and limits

[Before/after and all 15 repaired runs](../results/repair/COMPARISON.md) report seeds, confusion counts, recall/FPR and two-sided 95% Wilson intervals. [Results JSON](../results/repair/baselines.json) records thresholds, hashes and versions; [curation ledger](../results/repair/deduplication-audit.json) records components and exclusion reasons.

Reruns retain the old **5% empirical validation FPR budget** to isolate the repair recipe. These are not the future 1% study. Changed test membership/class balance prevent a causal estimate of leakage inflation. Historical intervals are nominal and cannot rehabilitate contaminated results.

Wilson intervals assume independent retained units and condition on fitting/threshold selection. They omit training/selection uncertainty. Seed-specific test sets overlap: never pool denominators. Cleaning resolves the known lexical overlap, **not** insufficient precision.

## Withdrawal and reproduction

Original result exports and prior documentation were hashed and archived under `artifacts/superseded_pre_cleanup/`; see [withdrawal ledger](../results/repair/withdrawal-ledger.json). Original `artifacts/deepset-*` reports are also withdrawn and retained for audit. The active initial-findings page no longer repeats their claims.

On a fresh reconstruction use the pinned source/dependencies, run `scripts/repair_data.py`, then `scripts/rerun_repaired_baselines.py`. Both refuse to overwrite completed outputs. The latter also requires original historical prediction files for its comparison; recorded hashes prevent silent substitution. Do not run legacy fetch into the repaired default path.

Validation: **19 tests passed**, including transitive grouping, quarantine, representative selection, similarity, disjoint/reproducible splits and original evaluation arithmetic. Ruff lint/format checks passed. No adaptation study has been run.
