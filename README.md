# Injection Lab

Capstone research on template concentration in public prompt-injection data and its consequences for evaluation and for benign-label adaptation. **Broad domain adaptation is already studied; global novelty of the narrower comparison is not claimed.**

## Findings (two preregistered studies; one linear detector; details and limits in the paper)

**Report: [paper/PAPER.md](paper/PAPER.md).**

- **Audit.** Attack data in the InjecGuard release are highly template-concentrated: 5,000 HackAPrompt attacks form 6 lexical groups, while benign sources are close to one row per group ([audit](docs/BENCHMARK_AUDIT.md)).
- **Study 2 (template leakage).** Row-random splits raised recall at 1% FPR relative to group splits on TaskTracker (+4.2 points, 95% CI +0.8 to +7.6) and BIPIA (+8.0, +3.8 to +12.2); jailbreak-classification showed no detected inflation. Held-out HackAPrompt templates got 0-100% recall (median 33%) against 100% under row splits. Example-level intervals were about 1.2 to 1.5 times too narrow. A splitter defect invalidates the HackAPrompt interval and the pooled primary estimate ([results](docs/STUDY2_RESULTS.md), [preregistration](docs/PREREGISTRATION_LEAKAGE.md)).
- **Study 1 (benign-label adaptation).** With 200 benign target labels, matched retraining did not beat threshold adjustment (+0.10 points, 97.5% CI −0.18 to +0.49) or generic retraining. The detector barely separated document-embedded attacks from clean text (AUROC 0.648) ([preregistration](docs/PREREGISTRATION.md), [tables](results/study/RESULTS.md)).

Not established: behavior of transformer detectors (Part B not run), human-verified labels, and novelty relative to prior dataset-level work (UNVERIFIED; see [novelty check](docs/LEAKAGE_NOVELTY.md)). The earlier deepset starter results remain [withdrawn](results/INITIAL_FINDINGS.md).

Background audit: [verified references](docs/VERIFIED_REFERENCES.md), [related work](docs/RELATED_WORK.md), [component licenses](docs/COMPONENT_PROVENANCE_AUDIT.md), [power analysis](docs/POWER_ANALYSIS.md), [status](docs/STATUS.md).

## Reproduce the study

```bash
git clone https://github.com/InjecGuard/InjecGuard data/raw/injecguard   # then: git -C data/raw/injecguard checkout cb1531f36bffb38b6493438217b36cda8875da8a
python scripts/build_study_pools.py        # deterministic; must match results/study/PREREG_LOCK.json
python scripts/run_adaptation_study.py     # 81 fits, ~16 min on 4 CPU cores; refuses to run unlocked
python scripts/analyze_adaptation_study.py
python scripts/exploratory_diagnostics.py  # post-hoc, labelled exploratory
python scripts/plot_adaptation_study.py
```

Every script refuses to overwrite its outputs. To rerun, move them aside; do not edit locked results.

## Environment and verification

The legacy repair ran on Python 3.12.10 (Windows); the adaptation study ran on Python 3.11.15 (Linux) with the same pinned scientific versions from requirements-lock.txt.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check src tests scripts
.\.venv\Scripts\python.exe -m ruff format --check src tests scripts
```

See [repair reproduction requirements](docs/DATA_REPAIR.md) before rerunning scripts. Existing repair outputs are immutable and scripts refuse overwrite. The default processed deepset file now contains the cleaned seed-42 split. Raw/archive/processed data and model artifacts remain outside Git.

The legacy CLI and CSV exporter remain for backward compatibility but are superseded as research reporting paths: not every legacy metric has a confidence interval. Only results carrying seeds and valid uncertainty intervals may appear in research claims. Do not reuse withdrawn original model reports or overwrite repaired inputs with legacy fetch output.

One preregistered adaptation study (linear detector) has run; see above. No neural baseline, agent evaluation or deployment exists. Annotation staffing/IAA and full component clearance remain unresolved. See [status](docs/STATUS.md) and [standing research rules](AGENTS.md).

## Supporting audit and planning

- [EvoShield resolution and email status](docs/EVOSHIELD_RESOLUTION.md)
- [Explicit power analysis](docs/POWER_ANALYSIS.md)
- [Component provenance and license audit](docs/COMPONENT_PROVENANCE_AUDIT.md)
- [Annotation staffing, guidelines and IAA plan](docs/ANNOTATION_PLAN.md)
- [Embedding sensitivity](docs/SEMANTIC_SENSITIVITY.md)
- [Eight-week workload and recommended cuts](docs/EIGHT_WEEK_SCOPE.md)

Deepset is legacy only. PromptShield remains a candidate for a future transformer replication.
