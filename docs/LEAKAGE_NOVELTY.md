# Novelty check: benchmark leakage in prompt-injection detection

Checked 2026-09-24. **Method limit:** arxiv.org, Semantic Scholar, LessWrong and the arXiv mirrors are blocked from the compute environment. Claims below come from search-engine extracts of each paper's own text and are marked **UNVERIFIED (full text not read)**. They must be confirmed by reading the PDFs before any novelty claim appears in the report.

## Closest prior work

| Work | What it already establishes | Status |
| --- | --- | --- |
| [When Benchmarks Lie (arXiv 2602.14161)](https://arxiv.org/abs/2602.14161) | 18 datasets (about 105K samples); activation-probe classifiers; **leave-one-dataset-out** evaluation; same-source splits inflate AUC by about 8.4 points on aggregate, with per-dataset gaps of 1-25%. Embedding-based cross-dataset audit finds 10.5% exact cross-dataset duplicates, all benign, and no malicious duplicates across datasets. 28% of top SAE features are dataset-specific shortcuts. | UNVERIFIED (full text not read) |
| [PIDS-Bench (arXiv 2609.15017)](https://arxiv.org/abs/2609.15017) | Enforces **seed-family separation**: paraphrases and obfuscated descendants share a partition. Reports five-seed means and **example-level** bootstrap intervals (10,000 resamples). Template-derived paraphrases are 38.7% of its test injections. | Full text read in the earlier audit (docs/PIDS_CONTEXT.md); bootstrap detail from extract, UNVERIFIED |
| [PIGuard / InjecGuard (ACL 2025)](https://aclanthology.org/2025.acl-long.1468/) | States that its evaluation split does not overlap competitor training sets; 144 validation samples are selected from the evaluation datasets. | Extract only, UNVERIFIED |
| [Defenses Against Prompt Attacks Learn Surface Heuristics (ACL 2026)](https://aclanthology.org/2026.acl-long.502/) | Shortcut learning (position, trigger tokens, topic) in tuned defenses. | Read in the earlier audit |
| [Confidently Wrong (arXiv 2606.22659)](https://arxiv.org/abs/2606.22659) | Pooled calibration hides severe miscalibration on attacks; detectors confidently pass indirect hijacks. | UNVERIFIED |

## Decision

- **Not novel:** "same-source splits overstate generalization". Dataset-level leakage is shown by *When Benchmarks Lie*, and family-aware splitting is already practised by PIDS-Bench. Our report must cite both and must not claim this.
- **Candidate gap 1 (not found in the extracts):** *within-dataset* template concentration on the **attack** side, and its consequence that example-level intervals for attack recall are anticonservative. The overlap audit (`results/audit/benchmark_overlap.json`) supports this: 5,000 HackAPrompt attacks form 6 groups, while benign sources are almost all singleton groups. The adaptation study shows the practical effect: 91.8% recall on three HackAPrompt templates has a group-bootstrap interval of [0, 100], and one held-out obfuscation template gets 0% recall.
- **Candidate gap 2 (weak):** contamination of released guardrails' own benchmarks. For InjecGuard the public training file is clean against its public evaluation files. Its validation set consists of exact test items (BIPIA 24, NotInject 48, WildGuard 24, plus 48 private PINT items not audited), and this is disclosed at a high level. It is a minor methodological note, not a headline.
- **Required before claiming either gap:** read *When Benchmarks Lie* and PIDS-Bench in full, and search for "effective sample size" and "cluster bootstrap" in guardrail and jailbreak benchmarks; the September 2026 extracts showed cluster bootstrap in an agent-probe paper (arXiv 2606.22864, UNVERIFIED) but not for detector benchmarks.

Global novelty is **not established**. The realistic target is a focused workshop paper on evaluation methodology, not a top-venue novelty claim.
