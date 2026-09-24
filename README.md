# Injection Lab

Capstone research on spending scarce labels to adapt prompt-injection detectors under domain shift. **Broad domain adaptation is already studied; global novelty of the narrower comparison is not claimed.**

## Main result (preregistered, locked single run)

**Report: [paper/PAPER.md](paper/PAPER.md).** Plan, fixed before any model was scored: [docs/PREREGISTRATION.md](docs/PREREGISTRATION.md). All tables: [results/study/RESULTS.md](results/study/RESULTS.md).

- **Setup.** A TF-IDF logistic-regression detector trained on direct prompts is moved to injections embedded in documents (TaskTracker): 13,016 evaluation rows in 7,432 independent groups, from 61,819 grouped, licensed rows of the InjecGuard release.
- **Confirmatory result.** With 200 benign target labels, matched retraining did not beat threshold-only adjustment (+0.10 recall points at 1% FPR, 97.5% CI −0.18 to +0.49) or generic retraining (+0.15, −0.16 to +0.47). A 2-point benefit is excluded.
- **Why.** The shift is a recall failure, not over-defense. Target AUROC is 0.648 and recall is 3.1% while target FPR is already at 1.0%. Benign-only labels cannot supply attack signal.
- **Also found.**
  - Fewer than about 100 benign labels cannot set a 1% threshold (2.9% FPR at B = 25).
  - Reusing labels for fitting and thresholding inflates FPR.
  - 5,000 HackAPrompt attacks are only 7 templates. The detector catches 92% of calibration templates but 0% of one held-out obfuscation template.
  - It flags 26.7% of benign safety-sensitive WildGuard prompts.

Limitations, stated in advance: upstream labels only with no human IAA, one detector class, a single merged data release, CPU only. The earlier deepset starter results remain [withdrawn](results/INITIAL_FINDINGS.md) and the repaired runs are exploratory ([data repair](docs/DATA_REPAIR.md)).

Study 2 (template leakage): [results](docs/STUDY2_RESULTS.md), [preregistration](docs/PREREGISTRATION_LEAKAGE.md), [data audit](docs/BENCHMARK_AUDIT.md), [novelty check](docs/LEAKAGE_NOVELTY.md).

Background audit, in reading order: [verified references](docs/VERIFIED_REFERENCES.md), [related work and novelty decision](docs/RELATED_WORK.md), [component provenance and licenses](docs/COMPONENT_PROVENANCE_AUDIT.md), [power analysis](docs/POWER_ANALYSIS.md), and the [v0.3 spec](docs/EXPERIMENT_SPEC.md), which the preregistration supersedes where they differ.

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
