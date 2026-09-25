# Novelty verdict (novelty-auditor, 2026-09-25)

**Scope.** This verdict uses only the page-cited notes in `docs/literature/`. It does not use memory of any paper. The 10 papers read in full are:

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

"Not found" always means not found in these 10 papers. It does not mean the result is new. Page numbers are the PDF pages as used in each note.

## Verdict table

| Claim | Verdict | Closest paper + page | What remains ours |
| --- | --- | --- | --- |
| C1: attack sources template-concentrated (HackAPrompt 5,000 rows = 6 groups) | NOT FOUND IN 10 PAPERS READ. UNVERIFIED against HackAPrompt and InjecGuard (not read). | PIDS-Bench pp. 7, 11, 17 (its own template-derived rows are "lexically more uniform"). BIPIA p. 3, Table 1: a crossed design with 125 attack strings (our inference). WBL p. 9: dataset-level distinguishability only. | An exhaustive count of groups per source in the InjecGuard release. Risk: if the HackAPrompt paper documents a level/template structure, this is a descriptive audit of a known construction, not a finding. |
| C2: leave-one-template-out recall on HackAPrompt 0–100% vs ~100% under row splits | PARTIALLY SHOWN | WBL p. 5 §3.3, p. 7 Table 2, p. 8 Table 3: random-row CV AUC ≥0.996 vs LODO 0.829–0.920 at the dataset level. PIDS-Bench p. 19 §VIII-C: template-derived recall is "best read as an upper bound", asserted but not measured. PromptShield p. 6 and BIPIA p. 3: phrase- and type-disjoint split designs. | The same phenomenon at a finer unit (templates within one dataset), at recall@1% FPR, with per-template dispersion shown for two detector families. A WBL reader would predict the direction but not the dispersion. 7 templates, descriptive only. |
| C3: design effects >1; example-level intervals too narrow | NOT FOUND IN 10 PAPERS READ | WBL p. 8: DeLong CIs over 105,034 pooled predictions. PIDS-Bench p. 7 §IV-D5 and p. 16 §VI-H: an "example-level bootstrap", called "narrow". The other 8 papers report no intervals. | A measurement, in this domain, of the clustering that the two closest papers' intervals ignore. The method is standard survey statistics and not ours. The HackAPrompt magnitudes (10–400) rest on 3 repeats with 0–2 templates per test side, so claim only "well above 1". |
| C4: no measurable row-vs-group inflation on TaskTracker, BIPIA, jailbreak | NOT FOUND IN 10 PAPERS READ | PIDS-Bench p. 7 §V-A asserts that family separation eliminates inflation but does not measure it (it cites CheckList). WBL pp. 7–8 finds gaps at the dataset level. BIPIA p. 3 and TaskTracker p. 4: the official splits are already type- or source-disjoint. | A bounded null at the within-dataset group level. It contrasts with WBL (a different unit) and does not contradict it. Caveat: with about 1.5–3.7 rows per group, the two split types differ little by construction. Only DeBERTa on TaskTracker ([−1.2, +1.5]) is tight. |
| C5 (withdrawn) | n/a | none | Only in the replication-failure paragraph. |
| C6: ProtectAI v2 27–30% recall@1% FPR on TaskTracker/BIPIA vs 85–99% direct | ALREADY SHOWN (qualitative) | WBL p. 20 Table 13: ProtectAI v2 detects 8.0% of indirect injections (at 4.2% FPR) vs 73.6% of jailbreaks, at its native threshold. The indirect set is BIPIA, InjecAgent and LLMail (Table 12). PromptShield p. 9 Table 4: ProtectAI v2 TPR 1.97% at 1% FPR (AUC 0.705) on data-embedded injections, with thresholds fit on the evaluation data (p. 7). | A replication on different data: TaskTracker, which neither paper used, and BIPIA at a fixed 1% FPR, with a direct-attack contrast from the same benign pool. The magnitude differs (27–30% vs 2–8%); report it and do not explain it. |
| C7: matched benign retraining ≈ threshold-only ≈ generic at B = 200 | PARTIALLY SHOWN (UNVERIFIED vs CAPTURE, WAInjectBench App. B and EvoShield, which have no notes) | PIDS-Bench pp. 13–14 §VI-C, Table 10: curated benign augmentation leaves externally-sourced FPR unchanged. pp. 15–16 §VI-F: calibration does not fix it. p. 14 and p. 19 §VIII-D: distribution-matched augmentation is "not tested". | A preregistered, equal-budget comparison that includes target-matched benign labels. It does **not** test PIDS-Bench's open question, because the targets differ. Theirs is benign FPR on external text. Ours is attack recall at 1% FPR, and our source threshold already met target FPR (1.0% [0.8, 1.3]), so there was no over-defense for matched benign labels to fix. The null follows largely from a recall floor (AUROC 0.648) that benign labels cannot address. |
| C8: 1/(B+1) expected FPR | not claimed as new (standard order statistics) | Adjacent only: PromptShield p. 7 recommends validation-set calibration. PromptShield p. 11, Tables 7 and 9: transferred 1% thresholds realise 1.27–1.61% FPR. | A practical note; cite a statistics text. |
| C9: InjecGuard train file clean vs eval; validation = eval items | NOT FOUND IN 10 PAPERS READ; minor note | None of the 10 notes audits InjecGuard. PromptShield p. 6 checks only overlap with its own evaluation split. | An audit fact. The clause "the paper discloses this at a high level" is UNVERIFIED: InjecGuard/PIGuard has not been read. |
| C10: deterministic allocation produced a spurious result | NOT FOUND IN 10 PAPERS READ | WBL p. 5 (folds "deterministic by dataset identity"). PromptShield p. 6 (one deliberate allocation). PIDS-Bench p. 8 (allocation not stated). BIPIA p. 3 ("randomly split", no seed). | A cautionary case from one of our own bugs. The general point, that allocation can fix which groups get tested, is inferable. This is not a contribution. |

## How the paper should cite and frame the overlaps

- **C2 and C4 against WBL.** Present Study 2 as extending WBL's dataset-level LODO (pp. 5, 7–8) down to the template level within a dataset. Credit WBL for the phenomenon. Say explicitly that at the within-dataset level the effect appears only where templates are extreme (HackAPrompt), and that no measurable effect appears on sources with small groups. WBL says itself that LODO is not new, only its application to this area (p. 5 §3.3). Our template-level variant is a further application, not a new protocol.
- **C2, C3 and C4 against PIDS-Bench.** Cite p. 7 (family separation asserted, not measured), p. 19 (upper bound) and pp. 7/16 (example-level bootstrap). The honest framing is that PIDS-Bench asserts that family separation prevents inflation and reports example-level intervals; we measure both issues on other data. Do not state or imply that PIDS-Bench's results are wrong. We did not evaluate PIDS-Bench data.
- **C6.** Downgrade it to a replication. A suggested sentence: "Consistent with WBL (p. 20, Table 13) and PromptShield (p. 9, Table 4), which found that ProtectAI v2 missed most indirect or data-embedded injections, we observe 27–30% recall at 1% FPR on TaskTracker and BIPIA. Absolute rates differ across the three studies, whose data, benign pools and operating points all differ." Under CLAIMS.md rules, C6 (SUPPORTED-DESCRIPTIVE) does not qualify for the abstract. The current abstract states it; move it out, or reduce it to one "consistent with prior work" clause.
- **C7.** Remove any wording suggesting that Study 1 tests the intervention PIDS-Bench left open. Cite PIDS-Bench for the shared conclusion that generic augmentation and calibration do not repair a target-distribution failure. Report our null as specific to a recall-limited source model.

## Consistency issues noticed (for the hostile-reviewer and related-work-writer; not fixed here)

1. The CLAIMS.md rules allow only SUPPORTED or NULL claims in the abstract. The abstract of `paper/PAPER.md` states C2 and C6, which are both SUPPORTED-DESCRIPTIVE.
2. C3 gives the non-HackAPrompt design-effect range as "1.1–2.6". The PAPER abstract gives "1.2–2.6". The per-repeat minimum for DeBERTa on TaskTracker is 1.0 (STUDY2_PARTB_RESULTS.md §3), so "exceed 1 on all sources" holds for medians only.
3. PAPER.md §2 and §7 say neither WBL nor PIDS-Bench was read in full, and cite PIDS-Bench as arXiv:2609.15017 and WBL with authors UNVERIFIED. The notes now record full reads: PIDS-Bench is IEEE Access 14:134184–134205, DOI 10.1109/ACCESS.2026.3728186, and WBL is by Fomin, AIWILD@ICLR 2026, arXiv v2. The Related Work, Limitations and References sections are stale.
4. PAPER.md §5.3 attributes ProtectAI's near-perfect HackAPrompt recall possibly to training overlap. That is appropriate. The same caveat applies to C6 on BIPIA: WBL used BIPIA (p. 16), but ProtectAI's training data are not documented in any note.

## Strongest honest contribution

Here is a claim the project can make without overclaiming.

> *In a widely used merged training release, the attack side is concentrated in a handful of templates. On such sources the effective sample size is the number of templates, not the number of rows. Held-out-template recall ranged from 0% to 100% where row splits reported about 100%, and design effects were far above 1. On sources with small groups, row splits did not measurably inflate recall. So template leakage matters where concentration is extreme. Wherever design effects could be estimated, the example-level intervals used by the closest prior work (WBL p. 8; PIDS-Bench pp. 7, 16) understate uncertainty.*

This combines C1, C2, C3 and C4. The piece not found in the 10 papers is the pairing of where template leakage does and does not matter within datasets with the measured design effects. The dispersion finding itself is a finer-grained extension of WBL. The preregistration and the documented self-retraction (C5 and C10) add credibility, but they are not contributions.

**Workshop publishability (skeptical).** This could be a short workshop paper at a venue such as ACL LLMSEC or AISec, framed as a measurement and methodology note. It is not a main-venue paper. Weaknesses a reviewer will press:

- the closest prior work (WBL) is itself a workshop paper making the coarser version of the same point;
- the headline dispersion rests on 7 templates from one dataset, with no intervals;
- design-effect magnitudes on HackAPrompt come from 3 repeats with 0–2 clusters;
- grouping is lexical, and there is no human IAA;
- 5 repeats leave the TF-IDF nulls at about ±10 points;
- one detector architecture per family, one untuned DeBERTa recipe, and Prompt Guard 2 unavailable;
- C6 is already shown, and C7 is a mechanism-explained null.

Acceptance also depends on reading HackAPrompt, InjecGuard/PIGuard and the SACMAT 2026 critical evaluation first. Any one of them could pre-empt C1–C3.

## Papers still needed (cited in the notes or the paper, not yet read)

Priority 1 (could change a verdict):

- **A Critical Evaluation of Defenses against Prompt Injection Attacks** (SACMAT 2026). Listed as "needed" in docs/literature/README.md, item 4. Bears on C6 and possibly on C2–C4.
- **HackAPrompt** (Schulhoff et al., EMNLP 2023). Systematic Review ref. [33], p. 22. Bears on C1 and C2: does the competition's level and template structure explain the 6–7 groups?
- **InjecGuard / PIGuard** (arXiv 2410.22770; ACL 2025). Cited as [14] "NotInject" in PIDS-Bench (p. 3, p. 21). Bears on C1 and on C9's disclosure clause.
- **CAPTURE** (LLMSEC@ACL 2025), **WAInjectBench** (App. B) and **EvoShield** (Mathematics 2026). Cited in PAPER.md §2 and in C7's prior Novelty field, with no notes. Bear on C7.

Priority 2:

- **PromptShield extended technical report** (arXiv 2501.15145), Appendices A.2 (link phrases), A.3 (validation split) and B.2 (PromptGuard scoring) (promptshield-2025 p. 2, footnote 1). Bears on C2 (phrase disjointness) and C6.
- **InjecAgent** (Zhan et al., Findings of ACL 2024). Systematic Review [58], p. 23; part of WBL's indirect category (p. 20, Table 12). Bears on C6: what WBL's 8.0% contains.
- **Greshake et al., "Not what you've signed up for"** (AISec 2023). Systematic Review [7], p. 21. C6 framing of indirect injection.
- **"Do Anything Now"** (Shen et al., CCS 2024). Systematic Review [34], p. 22. Bears on C1 and C3: jailbreak prompt families.
- **CheckList** (Ribeiro et al.). PIDS-Bench [3], p. 7, the stated basis for its inflation assertion. Bears on C4.
- **How Not to Detect Prompt Injections with an LLM** (AISec 2025). README item 6.
- **Defenses Against Prompt Attacks Learn Surface Heuristics** (ACL 2026). Cited in PAPER.md §2, with no note. Bears on C2.

Priority 3 (low): OpenPromptInjection (Liu et al.; DataSentinel [7], PromptShield p. 6), LLMail (WBL p. 16), SPML (Sharma et al.; hierarchical-2026 p. 3), PAP [41] and ReNeLLM [47] (Systematic Review p. 22), Muliarevych [111] (p. 24), Hidden-in-Plain-Text (WWW 2026; README item 12). For C8 and C3, also cite a standard statistics source for order statistics and for design effects. No note covers either.

## Bottom line

1. The project has a publishable contribution at the workshop level only: a within-dataset, template-level measurement showing where template leakage matters (extreme concentration: 0–100% held-out-template recall, design effects far above 1) and where it does not (no measurable row-split inflation on small-group sources). The measured design effects show that the example-level intervals used by the closest prior work understate uncertainty. None of this was found in the 10 papers read.
2. The contribution is incremental. It extends WBL's dataset-level LODO finding to a finer unit and measures what PIDS-Bench asserts without measuring. C6 is already shown, by WBL p. 20 and PromptShield p. 9, and must be reframed as a replication. C7 only partly overlaps PIDS-Bench, is explained by a recall floor, and does not answer PIDS-Bench's open question. C8–C10 are notes, not contributions.
3. Before submission, read HackAPrompt, InjecGuard/PIGuard and the SACMAT 2026 critical evaluation, any of which could pre-empt C1–C3. Also fix the stale Related Work section and the abstract-eligibility violations in PAPER.md.
