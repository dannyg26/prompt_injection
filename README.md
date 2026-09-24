# Injection Lab

Capstone research on scarce-label adaptation of prompt-injection detectors. **Broad domain adaptation is already studied; novelty of the narrower comparison is not established.** No new detector features are being developed during this audit.

Read these in order:

1. [Verified references and exact PIDS-Bench quotation](docs/VERIFIED_REFERENCES.md).
2. [Ten-paper related-work table and novelty decision](docs/RELATED_WORK.md).
3. [Data repair](docs/DATA_REPAIR.md), [before/after with every seed and CI](results/repair/COMPARISON.md), and [public dataset sizes/licenses/collection](docs/DATASETS.md).
4. [Two-page experiment specification](docs/EXPERIMENT_SPEC.md) ([PDF](docs/EXPERIMENT_SPEC.pdf)).

Original result claims are withdrawn. Repair retained 627 of 662 records, removed 33 redundant near-duplicate members and quarantined 2 mixed-label records. The three unchanged TF-IDF/logistic baselines were rerun for seeds 17, 29, 42, 71, 101. This small corrected corpus supports exploratory checks, not a 1% FPR claim.

## Environment and verification

Python 3.12.10 was used on Windows. Scientific dependencies are pinned in requirements-lock.txt.

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

No adaptation experiment, neural baseline, active agent evaluation or deployment has been implemented. The experiment specification is provisional: EvoShield does not report the exact proposed comparison; dataset provenance/permissions, annotation staffing and adequate independent evaluation size remain unresolved. See [status](docs/STATUS.md) and [standing research rules](AGENTS.md).

## Current audit and planning

- [EvoShield resolution and email status](docs/EVOSHIELD_RESOLUTION.md)
- [Explicit power analysis](docs/POWER_ANALYSIS.md)
- [Component provenance and license audit](docs/COMPONENT_PROVENANCE_AUDIT.md)
- [Annotation staffing, guidelines and IAA plan](docs/ANNOTATION_PLAN.md)
- [Embedding sensitivity](docs/SEMANTIC_SENSITIVITY.md)
- [Eight-week workload and recommended cuts](docs/EIGHT_WEEK_SCOPE.md)

The primary candidates are PromptShield and InjecGuard; deepset is legacy only. No new detector experiments ran.
