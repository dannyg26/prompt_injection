# Novelty verdict (novelty-auditor, 2026-09-25, update 2: 14 papers)

**Scope.** This verdict uses only the page-cited notes in `docs/literature/`. It does not use memory of any paper. The 14 papers read in full are:

1. When Benchmarks Lie (WBL; Fomin, AIWILD@ICLR 2026)
2. PIDS-Bench (IEEE Access 2026)
3. PromptShield (CODASPY 2025)
4. BIPIA (KDD 2025)
5. TaskTracker (SaTML 2025)
6. Systematic Review (IEEE Access 2026)
7. DataSentinel (S&P 2025)
8. MalPID (ComNet 2024)
9. Hierarchical/MHD (ICAIIC 2026)
10. Key-Feature/TLD (ICAIIC 2026)
11. HackAPrompt (Schulhoff et al.; arXiv 2311.16119v3; EMNLP 2023 per task brief, venue UNVERIFIED from the PDF) — new
12. InjecGuard (Li and Liu; arXiv 2410.22770v3; the ACL 2025 "PIGuard" version was NOT read) — new
13. A Critical Evaluation of Defenses against Prompt Injection Attacks (CriticalEval; SACMAT 2026, 6-page version; arXiv 2505.18333 NOT read) — new
14. CAPTURE (Kholkar and Ahuja; LLMSEC@ACL 2025) — new

"Not found" always means not found in these 14 papers. It does not mean the result is new. Page numbers are PDF pages as used in each note.

**Claim-text changes made in this update (scope narrowing only).** C1 and C2 were narrowed in `docs/CLAIMS.md`; no Status was changed.
- C1 now separates (a) the HackAPrompt concentration, stated as descriptive and by design, from (b) the release-wide attack-vs-benign contrast, which is stated as "more", not "far more", with the numbers from `results/audit/benchmark_overlap.json`: summed per-source rows per group are 3.1 for attack and 1.2 for benign classes, 2.1 vs 1.2 without HackAPrompt, and BIPIA benign is 3.0. These are exhaustive counts on a fixed file, not estimates, so no interval applies.
- C2 now says "7 lexical groups held out in turn", says that the groups correspond to competition level templates (one merging about 5 levels), and says what the held-out unit measures (transfer to unseen level wrappers and level-specific input constraints, not unseen attack strategies).

## Verdict table

| Claim | Verdict | Closest paper + page | What remains ours |
| --- | --- | --- | --- |
| C1a: HackAPrompt's 5,000 rows in the InjecGuard release form 6 groups | ALREADY SHOWN by construction (descriptive audit) | HackAPrompt p. 3 §3.1, p. 4: one fixed template per challenge, user input inserted at a placeholder, the "full prompt" fed to the LLM. p. 21 App. E.2: the release stores `prompt` and `user_input` separately; redundancy and spam stated but not quantified. pp. 22–25 App. F: the level templates. | Only the observation that InjecGuard used the full templated prompt (from our data check; InjecGuard pp. 6, 14 do not say which field was used), and the consequence: every row split of this source shares level templates between train and test. This is a data-release caveat that cites HackAPrompt, not a finding. |
| C1b: across the release, attack classes are more template-concentrated than benign classes | PARTIALLY SHOWN | Templated attack construction is documented source by source: HackAPrompt p. 3, BIPIA p. 3 Table 1 (crossed design, our inference), MalPID pp. 2–3, PIDS-Bench p. 7. InjecGuard pp. 6, 14 (Tables 4–5) give per-source counts but no template, dedup or group analysis. | A cross-source measurement of the attack-vs-benign asymmetry in one merged release. Not found in the 14 papers. Skeptic: that attack data are templated is inferable from the per-source papers, and outside HackAPrompt the asymmetry is modest (2.1 vs 1.2 rows per group). |
| C1, grouping validity | our data check, not a literature claim | HackAPrompt pp. 22–25 give the ground-truth templates. | On the one source where templates are known, no known template was split across lexical groups (3 stray rows), but 5 of 11 templates were chained into one group. This can be stated as a partial validity check (no under-grouping; over-grouping observed) once it is saved as a result file. It does not validate grouping on sources without known templates, and the marker-based level assignment is itself heuristic (10 multi-match rows). |
| C2: held-out-level-group recall on HackAPrompt 0–100% vs ~100% under row splits | PARTIALLY SHOWN | WBL p. 5 §3.3, p. 7 Table 2, p. 8 Table 3: dataset-level LODO gap. PIDS-Bench p. 19 §VIII-C: template-derived recall is an "upper bound", asserted but not measured. HackAPrompt pp. 3–4, 22–25: the unit is a competition level. No held-out-level evaluation appears in HackAPrompt (p. 21: no recommended splits), InjecGuard (pp. 6–8), CAPTURE (p. 2) or CriticalEval (p. 4). | The per-level dispersion for two detector families at recall@1% FPR. The direction (row splits ~100%, held-out levels lower) is predictable from HackAPrompt's fixed wrappers plus WBL. The dispersion is partly driven by level-specific input transformations (the 0% TF-IDF group is the slash/Unicode level; HackAPrompt p. 7, pp. 24–25), not by template leakage alone. 7 groups, no interval. |
| C3: design effects >1; example-level intervals too narrow | NOT FOUND IN 14 PAPERS READ | WBL p. 8: DeLong CIs over pooled predictions. PIDS-Bench p. 7 §IV-D5 and p. 16 §VI-H: an example-level bootstrap. InjecGuard (all pages), CAPTURE (§1–§5, App. A) and CriticalEval (pp. 4–6) report only single point estimates; CriticalEval's contaminated sets are crossed designs (p. 4, our inference). | The measurement in this domain; the method is standard and not ours. The HackAPrompt magnitude (10–400) is expected by construction (HackAPrompt p. 3) and rests on 3 repeats, so state only "well above 1". The informative result is the modest 1.1–2.6 on small-group sources. |
| C4: no measurable row-vs-group inflation on TaskTracker, BIPIA, jailbreak | NOT FOUND IN 14 PAPERS READ | PIDS-Bench p. 7 §V-A asserts that family separation eliminates inflation but does not measure it. WBL pp. 7–8: dataset-level gaps. BIPIA p. 3 and TaskTracker p. 4: the official splits are already disjoint. CAPTURE p. 2 splits only seed questions. | A bounded null at the within-dataset group level. The null is partly expected with 1.5–3.7 rows per group, and only DeBERTa on TaskTracker ([−1.2, +1.5]) is tight. |
| C5 (withdrawn) | n/a | none | Only in the replication-failure paragraph. |
| C6: ProtectAI v2 27–30% recall@1% FPR on TaskTracker/BIPIA vs 85–99% direct | ALREADY SHOWN (qualitative), by three primary sources | WBL p. 20 Table 13 (8.0% indirect at 4.2% FPR vs 73.6% jailbreak). PromptShield p. 9 Table 4 (TPR 1.97% at 1% FPR). **InjecGuard p. 16 Table 7** (accuracy 8.67% on BIPIA injections vs 88.53% on PINT injections; single run, native decision rule, BIPIA subset unstated). CAPTURE p. 12 Table 6 repeats 8.67%, but copies it from InjecGuard (p. 4), so it is not independent. | A replication: TaskTracker (used by none of the four), and BIPIA at a fixed 1% FPR with a direct-attack contrast from the same benign pool. Report the magnitude gap (27–30% here vs 2–9% in the three primary sources) without explaining it. |
| C7: matched benign retraining ≈ threshold-only ≈ generic at B = 200 | PARTIALLY SHOWN (PIDS-Bench). Resolved against CAPTURE: not pre-empted. Still UNVERIFIED against WAInjectBench App. B and EvoShield. | PIDS-Bench pp. 13–16, p. 19. CAPTURE p. 3 §2.4, p. 4 Table 2, p. 12 Table 5: adds in-domain attacks and benign prompts to the generic InjecGuard data, threshold fixed at 0.5, tested on the same generator; it has no threshold-only, generic-only, equal-budget or benign-only arm. InjecGuard p. 6 §4.2, p. 8 Table 2, p. 16 Table 9: MOF generic benign augmentation, a trade-off with malicious accuracy, and no threshold-only arm. | A preregistered equal-budget comparison with a target-matched benign arm. It does not answer PIDS-Bench's open question, because the targets differ (benign FPR there, attack recall at 1% FPR here). The null is explained by a recall floor (AUROC 0.648). |
| C8: 1/(B+1) expected FPR | not claimed as new | Adjacent: PromptShield p. 7, p. 11. CriticalEval p. 3 §4.2.1 argues for thresholded FPR/FNR but does not discuss how thresholds are set. | A practical note; cite a statistics text. CriticalEval p. 3 can motivate fixed-operating-point reporting. |
| C9: InjecGuard train file clean vs eval; validation = eval items | NOT FOUND IN 14 PAPERS READ; a minor note | InjecGuard arXiv v3 never mentions a validation or checkpoint-selection set (no hits for "valid" on any of the 17 pages; p. 7 §5.1). p. 14 Tables 4–5 sum to the 76,735-row release. p. 14 §B.2: the authors state that they chose the MOF scale by the headline evaluation average. | The code-derived fact that the 144-item validation set consists of evaluation items, which v3 does not disclose. The former "discloses at a high level" clause is unsupported by v3 and has been removed from our docs; the ACL 2025 PIGuard version and the repository README are UNVERIFIED. Keep the authors' stated MOF selection (theirs) separate from our finding. No misconduct inference. |
| C10: deterministic allocation produced a spurious result | NOT FOUND IN 14 PAPERS READ | Allocation is unstated or single in WBL p. 5, PromptShield p. 6, PIDS-Bench p. 8, BIPIA p. 3, CAPTURE p. 2 and InjecGuard p. 14. | A cautionary case, not a contribution. |

## What changed from the 10-paper verdict

- **C1: from NOT FOUND (with an UNVERIFIED flag) to a split verdict.** The HackAPrompt part (C1a) is now ALREADY SHOWN by construction (HackAPrompt pp. 3–4, 21, 22–25). The 6 groups are the competition's level templates, partly merged, and InjecGuard's rows contain the full templated prompt. The release-wide contrast (C1b) is PARTIALLY SHOWN and has been narrowed to "more", because without HackAPrompt it is 2.1 vs 1.2 rows per group. The risk flagged in the 10-paper verdict has materialised.
- **C1 grouping validity: new.** The lexical grouping recovered HackAPrompt's known level structure without splitting any template but merged 5 of 11. This can be stated as a partial, one-source validity check (no under-grouping; over-grouping observed) after the check is saved as a result file.
- **C2: verdict unchanged (PARTIALLY SHOWN), but scope and value reduced.** The unit is now "held-out competition levels/level groups". The direction of the effect is predictable from HackAPrompt plus WBL, and the extreme 0% case coincides with a level whose input is transformed (slashes, Unicode letters). Only the dispersion remains ours, and it is descriptive.
- **C3: now NOT FOUND in 14 papers.** InjecGuard, CAPTURE and CriticalEval also report no intervals. The HackAPrompt design effect is downgraded to "expected by construction".
- **C6: ALREADY SHOWN is strengthened.** InjecGuard p. 16 Table 7 is a third primary source. CAPTURE's matching 8.67% is secondhand and must not be counted as independent.
- **C7: the CAPTURE part is resolved as not pre-empting.** InjecGuard MOF is adjacent. WAInjectBench and EvoShield remain UNVERIFIED.
- **C9: the disclosure question is resolved against arXiv v3.** v3 never mentions a validation set. Other versions are UNVERIFIED.
- **The SACMAT 2026 risk is removed (SACMAT version only).** CriticalEval critiques attack diversity, adaptivity and AUC-only metrics. It does not study partitioning or uncertainty (p. 3), so it pre-empts none of C1–C10. Its arXiv extended version is unread.

## How the paper should cite and frame the overlaps

- **C1a.** Suggested wording: "HackAPrompt consists of ten challenges plus a demonstration, each with a fixed prompt template into which the user's text is inserted (Schulhoff et al., pp. 3–4, App. F). The InjecGuard release includes the full templated prompt, so its 5,000 HackAPrompt rows fall into a handful of level templates by design, and any row split shares templates across train and test." Remove the abstract sentence "5,000 HackAPrompt attacks form 6 lexical groups" as a headline finding. If it is kept, attribute it to the competition's design.
- **C1b.** Say "more concentrated" and give the numbers, including the BIPIA-benign exception (a crossed design, BIPIA p. 3). Do not say "benign sources are close to one row per group" without that exception.
- **C2.** Say "held-out competition levels (lexical groups)". Credit WBL for the phenomenon and HackAPrompt for the unit. State that the 0% group is the level whose input is transformed, so the dispersion mixes wrapper transfer with input transformation.
- **C6.** Suggested sentence: "Consistent with WBL (p. 20, Table 13), PromptShield (p. 9, Table 4) and InjecGuard (p. 16, Table 7), which found that ProtectAI v2 missed most indirect or data-embedded injections, we observe 27–30% recall at 1% FPR on TaskTracker and BIPIA; the absolute rates differ across studies whose data and operating points differ." Do not cite CAPTURE for the 8.67% figure.
- **C7.** Cite CAPTURE as adjacent: in-domain labelled retraining helps on data from the same generator, without a threshold-only or equal-budget control (pp. 3–4, 12). PAPER.md §2 currently groups CAPTURE under "domain adaptation"; describe it more exactly.
- **C9.** Keep the current v3 wording in BENCHMARK_AUDIT.md and PAPER.md §3.

## Consistency issues noticed (not fixed here)

1. The PAPER.md abstract (line 9) still presents "5,000 HackAPrompt attacks form 6 lexical groups, while benign sources are close to one row per group" as a finding. After the C1 narrowing, this overstates both parts.
2. PAPER.md §5.3 calls the held-out units "templates" and says the pools contain 7 groups. It should say that these are lexical groups corresponding to competition levels, one of which merges about 5 levels.
3. The issues carried over from the 10-paper verdict remain:
   - the abstract states SUPPORTED-DESCRIPTIVE claims (C2, C6);
   - the design-effect range reads 1.1–2.6 in CLAIMS.md and 1.2–2.6 in the abstract;
   - PAPER.md §2 still says WBL and PIDS-Bench were not read in full and cites stale identifiers.
4. The HackAPrompt level mapping exists only in a literature note's "Our data check" section. Save it as a result file (for example, under results/audit/) before the paper cites it as a validity check.

## Strongest honest contribution (re-assessed skeptically)

With C1a explained by HackAPrompt's design, the HackAPrompt results (C1a, C2, and the C3 magnitude) are largely predictable, and they are illustrations rather than findings. What survives:

> *In a widely used merged training release, the attack side is more template-concentrated than the benign side, and one component (HackAPrompt) enters as full templated prompts, so row splits share competition templates by construction. Under a corrected, randomized group splitter, row splits did not measurably inflate recall at 1% FPR on sources with small groups; the null is tight for one detector and source (DeBERTa on TaskTracker, [−1.2, +1.5]). Design effects of 1.1–2.6 on those sources show that the example-level intervals used by the closest prior work (WBL p. 8; PIDS-Bench pp. 7, 16) are too narrow, modestly. Held-out HackAPrompt levels illustrate the extreme case.*

The piece not found in the 14 papers is the within-release measurement: where template leakage does not measurably matter (small-group sources) and how much clustering widens intervals. The positive leakage effect is confined to a source whose templating is documented by design.

**Publishability (skeptical).** This is weaker than the 10-paper assessment. At best it is a short workshop measurement note (for example, LLMSEC or AISec), or a negative-results or dataset-audit note. It is not a main-venue paper. A reviewer will say:

- the only large effect is on HackAPrompt and is obvious from the competition design (HackAPrompt pp. 3–4);
- the closest prior work (WBL) is a workshop paper making the coarser point;
- the main surviving result is a null, tight for only one detector and source;
- the non-HackAPrompt design effects are modest;
- grouping is lexical, with only a one-source partial validity check and no human IAA;
- there are 5 repeats, one untuned recipe per family, and no Prompt Guard 2;
- C6 is already shown three times, and C7 is a mechanism-explained null.

## Papers still needed (cited in the notes or the paper, not yet read)

Priority 1 (could change a verdict):
- **WAInjectBench (App. B)** and **EvoShield** (Mathematics 2026): cited in PAPER.md §2, with no notes. C7 remains UNVERIFIED against them.
- **InjecGuard/PIGuard, ACL 2025 published version**, and the InjecGuard repository README: needed for C9 (whether any version discloses the validation set) and for C1a (which HackAPrompt field and which rows were sampled; InjecGuard p. 14 gives counts only).
- **Defenses Against Prompt Attacks Learn Surface Heuristics** (ACL 2026): cited in PAPER.md §2, with no note. It is now more relevant to C2, whose held-out-level drop may be wrapper or surface-cue learning.

Priority 2:
- **CriticalEval extended version** (arXiv 2505.18333): the SACMAT note does not cover it.
- **PINT benchmark** documentation: the non-BIPIA side of InjecGuard's C6 contrast (p. 16) and our unaudited PINT items (C9).
- **PromptShield extended technical report** (arXiv 2501.15145), Apps. A.2, A.3 and B.2 (C2, C6).
- **InjecAgent** (Findings of ACL 2024): part of WBL's indirect set (C6).
- **Liu et al. (2023)**, the F/S/D framework used by CAPTURE (p. 2), and **Safe-Guard prompt-injection dataset** (Erdogan et al. 2024; CAPTURE p. 2): bear on C1b (construction of other attack sources in the release).
- **Greshake et al.** (AISec 2023), **"Do Anything Now"** (CCS 2024) and **CheckList** (PIDS-Bench [3]).
- **How Not to Detect Prompt Injections with an LLM** (AISec 2025).

Priority 3 (low): OpenPromptInjection (Liu et al., USENIX Security 2024; CriticalEval [19]), LLMail, SPML, PAP, ReNeLLM, Muliarevych, Hidden-in-Plain-Text, and Wang et al. 2021 (the InjecGuard Table 3 baseline). For C3 and C8, cite standard statistics sources for design effects and order statistics.

## Bottom line

1. The project still has a contribution found in none of the 14 papers read, but a smaller one: a within-release measurement showing that row splits did not measurably inflate recall on small-group sources (tight for one detector and source only), and that design effects of 1.1–2.6 make example-level intervals, as used by the closest prior work, too narrow.
2. The headline HackAPrompt results are not findings. The concentration is by design (HackAPrompt pp. 3–4, 21, 22–25), and the held-out-level drop is predictable from that design plus WBL's dataset-level result. Present them as a descriptive caveat and an illustration. C6 is a replication of three primary sources (WBL, PromptShield, InjecGuard), and C7–C10 are notes or nulls.
3. This is at most a modest workshop measurement or negative-results note. Before submission, save the level-mapping check as a result file, rewrite the abstract to match the narrowed C1 and C2, and read WAInjectBench, EvoShield, the PIGuard ACL version and the surface-heuristics paper.
