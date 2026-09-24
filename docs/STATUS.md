# Research status - v0.4 (2026-09-24)

**The preregistered adaptation study ran once and has been analyzed.** Report: [paper/PAPER.md](../paper/PAPER.md).

Completed:
- Grouped S/T/U pools from the pinned InjecGuard GitHub release (61,819 rows; license-declared components only; word-shingle containment grouping). Deterministic rebuild verified byte-identical.
- Preregistration, code and pool hashes locked and pushed (commit `0f120e6`) before any study model was scored. 81 models were fitted and scored once (16.4 minutes on 4 CPU cores).
- Confirmatory result: no benefit of matched benign retraining over threshold-only or generic retraining at B = 200; a 2-point benefit is excluded. Descriptive and post-hoc exploratory diagnostics are reported separately.
- 35 tests pass, including brute-force checks of the weighted ROC and threshold rules. Ruff lint and format are clean.

Unmet gates, reported as limitations:
- No human annotation or IAA; upstream labels only.
- Nested component licenses partly UNVERIFIED; research use only, no redistribution.
- Evaluation not sized to a target effect; all permitted rows were used.

Not done:
- No transformer detector: no GPU, and Hugging Face is blocked in the compute environment.
- The EvoShield author email has still not been sent.
- Any further detector training (for example, benign-vs-attack label allocation) needs a new preregistration and owner approval under AGENTS.md.
