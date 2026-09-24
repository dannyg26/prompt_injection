> The full draft now lives in [PAPER.md](PAPER.md); this outline is kept for history.

# Capstone report outline

Working title: **Allocating Scarce Labels for Prompt-Injection Detection Under Domain Shift**

Provisional controlled replication/extension; novelty unresolved. See [related work](../docs/RELATED_WORK.md) and [experiment specification](../docs/EXPERIMENT_SPEC.md).

1. Abstract: write after results; include actual scope, seeds, uncertainty and limitations.
2. Introduction: trust-boundary construct; explicit narrow question and delivered contributions.
3. Related work: adaptation already studied; distinguish author-stated limitations from scope inference; resolve EvoShield.
4. Data: source revisions, permissions, contextual labeling, ambiguity, independent groups and sample-size justification.
5. Methods: fixed review budgets, source/target/third domain, paired arms, model/threshold freezing and annotation-cost accounting.
6. Results: every prespecified seed and interval; recall@empirical 1%FPR separate from frozen operational thresholds; hard benign, calibration, third-domain and negative/inconclusive outcomes.
7. Audit and error analysis: repaired exploratory checks clearly separate from confirmatory data; original claims withdrawn; no causal leakage estimate from changed test sets.
8. Limitations: semantic correlation, provenance, low-FPR precision, pretrained contamination, missing agent outcomes.
9. Reproducibility appendix: hashes, environment, annotation ledger, exclusions, protocol amendments and required AI-assistance disclosure.

The report must not present the proposal's future model or analysis as already implemented.
