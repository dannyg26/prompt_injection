# Claims register

Every finding the paper may state lives here first. The paper may not state a claim more strongly than its row allows.

- **Status** comes from our own results.
- **Novelty** comes from the novelty-auditor, using page-cited literature notes only.

Status values: SUPPORTED, SUPPORTED-DESCRIPTIVE (no inferential test), NULL (no effect detected; the interval is given), WITHDRAWN, KNOWN (standard result, used as a practical note).
Novelty values: UNVERIFIED, ALREADY SHOWN, PARTIALLY SHOWN, NOT FOUND IN N PAPERS READ.

| ID | Claim (the exact scope the paper may use) | Evidence | Status | Novelty |
| --- | --- | --- | --- | --- |
| C1 | In the InjecGuard release, attack sources are far more template-concentrated than benign sources under our lexical grouping. 5,000 HackAPrompt rows form 6 groups; benign sources are about 1 row per group. | docs/BENCHMARK_AUDIT.md; results/audit/benchmark_overlap.json | SUPPORTED (exhaustive counts) | UNVERIFIED |
| C2 | On HackAPrompt, recall at 1% FPR on held-out templates ranged from 0% to 100% (TF-IDF, median 34%) and from 11% to 100% (DeBERTa-v3-small, median 92%), against about 100% under row splits. There are 7 templates and no interval. | results/leakage/partb/partb_results.json (loto) | SUPPORTED-DESCRIPTIVE | UNVERIFIED |
| C3 | Design effects for attack recall exceed 1 on all sources: 1.1–2.6 on indirect and jailbreak sources, and 10–400 on HackAPrompt. Example-level intervals are therefore too narrow. | partb_results.json (design_effect); docs/STUDY2_PARTB_RESULTS.md §3 | SUPPORTED | UNVERIFIED |
| C4 | With randomized group splits, row splits did not measurably inflate recall on TaskTracker, BIPIA or jailbreak-classification, for TF-IDF or DeBERTa. All 95% intervals include 0. TF-IDF intervals are about ±10 points; DeBERTa on TaskTracker is [−1.2, +1.5]. | partb_results.json (inflation) | NULL | UNVERIFIED (relation to dataset-level leakage findings) |
| C5 | Part A: row splits inflate TaskTracker (+4.2) and BIPIA (+8.0). | docs/STUDY2_RESULTS.md | **WITHDRAWN** (did not replicate) | n/a |
| C6 | ProtectAI v2 recall at 1% FPR: 27.1% [23.4, 30.1] on TaskTracker and 29.8% [19.5, 40.0] on BIPIA, against 85–99% on direct attacks. Ranges are over 5 group splits; no interval; training overlap unknown. | partb_results.json (released) | SUPPORTED-DESCRIPTIVE | UNVERIFIED |
| C7 | With 200 benign target labels, matched retraining did not beat threshold-only (+0.10, 97.5% CI [−0.18, +0.49]) or generic retraining (+0.15, [−0.16, +0.47]). The linear detector had target AUROC 0.648. | results/study/results.json; exploratory_diagnostics.json | NULL (confirmatory) | UNVERIFIED (overlaps PIDS-Bench, CAPTURE) |
| C8 | A 1% threshold set from B < 100 benign labels has expected FPR 1/(B+1). Observed: 2.9% at B = 25. | results/study/RESULTS.md | KNOWN (order statistics; practical note) | not claimed as new |
| C9 | The InjecGuard training file is clean against its public evaluation files. Its validation set consists of evaluation items; the paper discloses this at a high level. | docs/BENCHMARK_AUDIT.md | SUPPORTED (exhaustive) | minor note, not a contribution |
| C10 | Deterministic group allocation (largest-first) fixed which templates were tested and produced a spurious inflation result (C5); randomizing the allocation removed it. | STUDY2_RESULTS.md vs STUDY2_PARTB_RESULTS.md | SUPPORTED (one case) | UNVERIFIED |

## Rules

- A claim moves to the paper's abstract only if Status is SUPPORTED or NULL, and Novelty is not ALREADY SHOWN (unless it is framed as a replication).
- WITHDRAWN claims may appear only in the replication-failure paragraph.
- Changing a Status requires a result file; changing a Novelty requires a page-cited literature note.
