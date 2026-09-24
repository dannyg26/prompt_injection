# Annotation protocol and staffing
Draft v0.3. No human annotations, elapsed-time measurements or agreement results have been collected. **IAA is NOT MEASURED**, not assumed.

## Where target labels come from

Primary candidate data are the pinned PromptShield and InjecGuard releases. Target labels are independently reviewed existing records with recoverable task/context and origin, not labels invented by an LLM. Proposed target: natural-language document/application tasks mapped to Dolly/Natural-Instructions components. Source: generic instruction/conversation components. Code/SPP is the untouched third-domain candidate. These assignments cannot be activated until the component-to-row mapping and permissions are verified. Missing context is not filled by guessing.

Existing public evaluation labels form a large separate evaluation pool; newly reviewed adaptation labels form a small disjoint bank. No evaluation label enters retraining, threshold selection, early stopping or hyperparameter choice. An evaluation audit does not count against B, but its labor cost is explicit.

B means **final labels revealed to an algorithm**: 0/25/50/100/200 in the full design. It does not mean the entire available evaluation set or the total human review effort. The compact design retains 0/50/200. Review counts, unusable examples and adjudication time are reported separately; equal revealed labels do not imply equal annotation cost. Threshold-only uses its B labels for calibration, not training.

## People and timing

- Annotator A: the student investigator (proposed; availability not confirmed).
- Annotator B: an independent classmate/research assistant with ML/security literacy, nominated by the supervisor. **Not yet assigned. An AI assistant is not a second human annotator.**
- Adjudicator: supervisor or designated senior researcher, also not yet confirmed.
- Planning time: 1-2 minutes per short record; 3-5 minutes when task context is long. Use **2 minutes/judgment** for the base schedule and a 4-minute sensitivity case. These are assumptions; time the first 20 records and replace them with measured medians and upper quartiles.
- Do 20 calibration examples together outside all study pools; revise the rubric, then blind the subsequent annotation.

## Labeling rules

For each record, identify (a) authorized task, (b) trusted instruction boundary, (c) untrusted text, and (d) whether an instruction attempts to cross that boundary. Reviewers see task context, not upstream labels, model scores, arm or budget.

1. **Injection:** the lower-trust span attempts to redirect task behavior or override governing instructions. Label the attempt, not whether a model follows it.
2. **Benign:** legitimate task data, procedural prose, quotation or security discussion without that attempted redirection.
3. **Ambiguous / insufficient context:** the boundary, task or intended role cannot be recovered reliably. Do not force a binary label.
4. Harmful subject matter, direct jailbreak requests, imperative language and ordinary requests are not by themselves evidence of indirect injection. Preserve a separate direct-jailbreak category for exclusion/scope analysis.
5. Record the decisive span, reason code, domain, provenance ID and uncertainty. Preserve original labels separately. Disagreements receive written adjudication after independent judgments are saved.

## Agreement: at least 100, explicitly scheduled

Double-annotate **100 target evaluation items** (50 upstream-positive, 50 upstream-benign) without revealing those strata; add 100 source and 100 third-domain items for 300 audited evaluation records in total. Sampling seed **20260923**; sample independent groups, not siblings. The target 100 satisfy the minimum; report each domain separately.

Before adjudication, report the complete three-label confusion table, raw agreement, Cohen's kappa and class-specific agreement with 95% group-bootstrap intervals (10,000 draws, seed **20260924**). State undefined kappa if a class is absent. Do not inflate agreement by deleting ambiguous items or report post-adjudication agreement as IAA. Review disagreement reasons and context availability before deciding that labels are usable. A 100-item audit cannot establish a sub-1% gold-label error rate.

For adaptation, budget a bank of **300 usable benign target and 300 usable benign generic records**, drawn from at most 800 reviewed candidate records total. Both annotators label all candidates. If fewer than 200 usable records remain in either bank, the B=200 comparison is not feasible; do not silently replace records without reporting added costs. Seed-specific nested samples reuse this bank; seeds are not independent new annotations.

## Work estimate and gate

At the 800-candidate cap plus 300 evaluation-audit items: 1,100 records x 2 reviewers x 2 minutes = **73.3 person-hours**. Assuming 10% require four minutes of additional adjudication: **7.3 hours**. Add two hours calibration and four hours ledger/quality checks: **86.7 person-hours**. At four minutes per judgment, total rises to **160 hours**. These are workload scenarios, not measured timing statistics.

Each main reviewer needs roughly 37-40 hours in the base case, concentrated in weeks 2-4; adjudication/administration is extra. Fully relabeling an 11,000-row evaluation set with two reviewers at two minutes would require **733.3 person-hours**, before adjudication. That is incompatible with the eight-week plan. Therefore reuse provenance-verified public labels with an explicit audit and scope claims to their validity.

Launch requires named reviewers, measured pilot time, completed independent target IAA on >=100, documented ambiguity and an auditable separation of adaptation and evaluation pools. No agreement score or confidence interval is fabricated to fill the current gap.
