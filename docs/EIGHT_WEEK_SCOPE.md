# Eight-week scope and workload
Draft v0.3. Planning assumptions, not observed runtime.

## Count training separately from evaluation

One source-to-target adaptation direction; evaluate each configuration on S, T and untouched U. U is not a second adaptation direction.

| Design | Nominal arm-budget-seed-domain cells | Unique decision configurations | Detector fits/checkpoints | Model-domain scoring passes |
| --- | ---: | ---: | ---: | ---: |
| Full: 4 arms x 5 budgets x 10 seeds x 3 domains | 600 | 130 | 90 | 270 |
| Compact: 4 arms x 3 budgets (0/50/200) x 5 seeds x 3 domains | 180 | 35 | 25 | 75 |

Full per seed: one shared B=0/frozen model + four threshold-only configurations + eight retrained models = 13 configurations, of which nine require model fitting. Repeated frozen/B=0 cells are aliases, not new experiments. Threshold sweeps reuse scores. The compact version has seven configurations and five fits per seed. NotInject adds 130/35 decision evaluations and 90/25 cached scoring passes, respectively.

Applying the full Cartesian grid to four architectures would create 2,400 nominal evaluation cells and 360 fits in total, though three architectures are cheap linear models. This breadth is unnecessary for the primary question. Keep one prespecified neural architecture. Retain one combined linear baseline at B=0 as a diagnostic; do not expand the full adaptation grid over all three legacy baselines.

## Recommended cuts

Keep the three competing intervention arms and frozen control: deleting generic-data or threshold-only would undermine the causal comparison. First cut extra architectures, then reduce budgets to 0/50/200 and seeds to **17,29,42,71,101**. Make B=200 the only confirmatory budget; B=50 describes the learning curve. Keep U as an untouched descriptive diagnostic unless its own power gate is met. Do not sacrifice independent evaluation size to preserve more runs. The full 25/100 budget points remain a documented extension, not silently executed.

Hypothetical GPU schedule: 2-6 GPU-hours per source fit and 0.25-1 GPU-hour per adaptation fit. Full: **40-140 GPU-hours** before scoring; compact: **15-50 GPU-hours**. Measure on the selected hardware only after gates clear; these timings are UNVERIFIED. CPU-only transformer training is not assumed feasible. Add a 30% contingency and reserve inference/bootstrap time. A source-only pilot must check between-seed variability; fewer seeds do not guarantee power for a training-procedure-level effect.

Annotation base estimate is **86.7 person-hours**, potentially **160** for longer records, from the separate annotation plan. Planning capacity is student 15-20 hours/week plus a second reviewer with about 40 hours total and an available adjudicator. These people/time commitments are not yet confirmed. Without the second reviewer, the proposed study does not fit as a defensible human-audited eight-week project.

## Calendar

| Week | Deliverable and gate |
| --- | --- |
| 1 | Resolve published EvoShield overlap; send author inquiry when account available; component permissions/provenance ledger; analytical power plan. No model runs. |
| 2 | Recover per-row source/task IDs; exclude unlicensed/untraceable material; 20-record annotation timing pilot; >=100 independent dual target annotations and IAA. |
| 3 | Finish adaptation label bank and evaluation audits; run full-corpus lexical/embedding/provenance grouping; inventory independent class counts. Freeze domain membership. |
| 4 | Only after gates: source-only runtime/discordance/seed-variance pilot; choose feasible detectable effect, freeze hashes, hyperparameters, analysis and exact compute cap. |
| 5 | Train five source models and twenty compact adaptation checkpoints; thresholds use only their allowed label pool. |
| 6 | One locked evaluation, paired intervals and uncertainty checks. Stop expansion; report failed precision gates rather than add post-hoc endpoints. |
| 7 | Error analysis and complete report, including negative/inconclusive outcomes. |
| 8 | Reproduce key tables, final audit, revisions and presentation. |

Fail-fast: if provenance/staffing is unresolved at the end of week 2, or cleaned independent class counts miss the chosen effect-size design at the end of week 3, narrow to an explicitly exploratory replication/data audit. More epochs or seeds cannot rescue deficient labels or evaluation units.
