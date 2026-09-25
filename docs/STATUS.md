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

## Study 2 (benchmark leakage) - Part A run and reported

- Novelty check: [LEAKAGE_NOVELTY.md](LEAKAGE_NOVELTY.md). Dataset-level leakage is already published (*When Benchmarks Lie*; PIDS-Bench), so we do not claim it. Within-dataset template concentration on the attack side is a candidate gap, UNVERIFIED until both papers are read in full.
- Data audit: [BENCHMARK_AUDIT.md](BENCHMARK_AUDIT.md). The InjecGuard training file is clean against its public test files, but its validation set consists of test items (disclosed). Attack sources are highly template-concentrated: 5,000 HackAPrompt rows form 6 groups.
- Preregistration: [PREREGISTRATION_LEAKAGE.md](PREREGISTRATION_LEAKAGE.md), locked in `results/leakage/PREREG_LOCK.json`. **Running requires the owner's AGENTS.md amendment.** Part B (DeBERTa and released detectors) needs a GPU and Hugging Face access.
- **Part A results:** [STUDY2_RESULTS.md](STUDY2_RESULTS.md). Row splits inflate recall at 1% FPR by 4.2 points on TaskTracker and 8.0 on BIPIA (intervals exclude 0). Held-out HackAPrompt templates get a median of 33% recall (range 0-100) against 100% on row splits. Example-level intervals are about 1.2-1.5 times too narrow. The pooled primary estimate is confounded and the HackAPrompt interval is invalid, because the group splitter placed the same template in the test set every time (disclosed; fix before Part B).

## Paper integration (2026-09-24)

- `paper/PAPER.md` now reports the audit, Study 1 and Study 2 together, with figures, the Study 2 design defect and all limitations.
- Amendment 2 fixes the group splitter for any future run (`random_group_split`, tested); Part A was not refitted.
- Still required for a submission: Part B (transformer and released detectors; needs a GPU and Hugging Face), a human-labeled agreement sample, and a full-text read of the two closest papers.

## Study 2 Part B - run and reported (2026-09-25)

- Ran on Colab A100 at commit `93e5ec9` under Amendments 3-4. Results: [STUDY2_PARTB_RESULTS.md](STUDY2_PARTB_RESULTS.md).
- No row-split inflation was established on TaskTracker, BIPIA or jailbreak-classification for TF-IDF or DeBERTa. **The Part A per-source inflation result is withdrawn**; it did not replicate with the corrected splitter.
- HackAPrompt held-out templates: TF-IDF 0-100% (median 34%), DeBERTa 11-100% (median 92%). Design effects are above 1 throughout.
- ProtectAI v2, descriptive: 27% TaskTracker and 30% BIPIA recall at 1% FPR. Prompt Guard 2 was gated and not accessed.
- Remaining before submission: human-labeled agreement sample, full-text read of the two closest papers, and advisor review.
