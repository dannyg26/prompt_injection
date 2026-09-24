# Research rules

- Do not add product or detector features without a new request. Current work is a literature audit, data repair, and an experiment specification.
- Every reported experimental metric must identify all seeds and carry a confidence interval with its method and assumptions. Counts, configuration values, and planned budgets are not estimated performance metrics.
- Never describe repeated seeds on overlapping data as independent additional test examples.
- Keep dataset/template groups disjoint across partitions; document the operational near-duplicate definition and remaining semantic uncertainty.
- Preserve immutable original data and superseded outputs for audit, but withdraw contaminated results from current research claims.
- Label unresolved references, metadata, licenses, and novelty claims UNVERIFIED. Distinguish an author's stated limitation from our inference.
- Never select cleaning rules, thresholds, models, or hyperparameters from held-out performance. Record exploratory amendments.

- Current launch gate: no detector training, adaptation or scoring until primary component permissions/provenance, independent sample-size design, and human annotation/IAA gates are satisfied. Analytical planning and frozen embedding data audits are authorized.
- Amendment 2026-09-24 (project owner's decision): the single study in docs/PREREGISTRATION.md may be fit and scored once, only after its lock (results/study/PREREG_LOCK.json) is committed and pushed. The unmet gates above stay unmet and must be reported as limitations of that study, not as satisfied. All other detector training remains gated.
- Amendment 2026-09-24 (project owner's decision, second): Study 2 Part A in docs/PREREGISTRATION_LEAKAGE.md may be fit and scored once, only after its lock (results/leakage/PREREG_LOCK.json) matches a pushed commit. Part B remains gated. The unmet gates above must be reported as limitations.
- Adaptation labels revealed to algorithms and evaluation-set size are separate pools; never shrink evaluation to the adaptation budget.
