# When Benchmarks Lie: Evaluating Malicious Prompt Classifiers under True Distribution Shift
- Authors / venue / year / version read: Max Fomin (Zenity). First Workshop on Agents in the Wild: Safety, Security, and Beyond (AIWILD) at ICLR 2026. arXiv:2602.14161v2 [cs.LG], dated 19 Jul 2026 (p. 1).
- File read: literature/pdfs/when_benchmarks_lie_2602.14161v2.pdf. Pages read: 1–27, all of them.
- How it was read: the Read tool could not render the PDF because `pdftoppm` is not installed. I extracted the text layer of all 27 pages with pypdf, installed in the session scratchpad, and read all of it. Unreadable parts: the images in Figures 1–6 (pp. 2, 4, 23, 24, 25, 26). Only their captions and the surrounding text were available. Some table cells run together in the extraction; for example, "BIPIA 15000 9563.1" in Table 4 on p. 8 reads as %Mal 95 and Raw 63.1, which agrees with Appendix M on p. 21 ("bipia 63.0%"). Garbled Table 4 cells are not quoted anywhere below except that one.

## What it does
- The paper trains activation probes (L2 logistic regression, plus a 2-layer MLP) on LLM hidden states and on SAE features. The training benchmark has 18 datasets and 105K samples, 47% malicious (p. 1, abstract; p. 4, §3.1).
- It proposes Leave-One-Dataset-Out (LODO) evaluation, which trains on K−1 datasets and tests on the held-out one, and compares it with 5-fold CV and with official held-out test splits. The author says the protocol is not new: "our contribution is not the protocol itself but applying it at the dataset level to prompt-attack classification (where it has not been adopted) and quantifying the resulting CV-LODO gap" (p. 5, §3.3).
- It reports a pooled-AUC gap between CV and LODO of 8.0–16.5 pp across four LLMs, and per-dataset gaps between held-out test and LODO of 1.2–25.4 pp (p. 1; p. 7, Table 2; p. 8, Table 3).
- It defines a "LODO coefficient retention" metric, r_j = min_i w_j^(−i)/w_j, to flag SAE features that act as dataset shortcuts. It finds 28% (Llama-3.1-8B) and 44% (Gemma-3-27B) of the top-50 SAE features are shortcuts at a 0.5 threshold (p. 5, Eq. 4; p. 9, §5.4).
- A dataset-identity classifier reaches 96.6% accuracy on SAE features and 89.1% on raw activations. Seven domain-generalization mitigations do not close the gap (p. 9, §5.4–5.5; p. 19–20, App. G).
- It compares the probe with PromptGuard 2, LlamaGuard 3, Llama-as-Judge, ProtectAI v2 and Deepset v2 (p. 10, §5.6; p. 20, App. I; p. 26, App. P.2).

## Data
- **Datasets.** 18 public datasets (p. 16, Table 7):
  - Harmful requests: AdvBench 520, HarmBench 400.
  - Jailbreak: WildJailbreak 2,210; yanismiraoui 1,034.
  - Indirect injection: BIPIA 15,000 (95.3% malicious); InjecAgent 1,054; LLMail 9,998.
  - Extraction: Mosscap 10,114, which includes 114 Gandalf samples.
  - Mixed: jayavibhav 10,000; qualifire 5,000; SafeGuard 8,236; deepset 546.
  - Benign: Enron 10,000; OpenOrca 9,997; Dolly 10,000; 10k-prompts 9,924; SoftAge 1,000.
  - Gandalf is merged into Mosscap, which gives 17 LODO datasets (p. 6, §4.1).
- **Not used.** HackAPrompt, TaskTracker's dataset and the InjecGuard/PIGuard release are not among the datasets. Not found after reading pp. 1–27; TaskTracker is cited only as related work and for its method (p. 3, p. 4).
- **Size caps.** "Most are capped at 10K samples for tractable activation extraction; BIPIA uses 15K to cover its three context types" (p. 4, §3.1). How the 10K subsamples were drawn (random or otherwise) was not found after reading pp. 1–27. Mosscap alone "contains 224k extraction attempts across 8 difficulty levels" (p. 17, App. B).
- **How splits are formed.**
  - Three protocols: (a) 5-fold CV, "StratifiedKFold(n splits=5, shuffle=True, random state=42)", i.e. random rows pooled across datasets; (b) official held-out test splits, available for 6 datasets; (c) LODO, where "folds are deterministic by dataset identity" (p. 5, §3.2; p. 7).
  - There is also leave-one-category-out (LOCO), which holds out harmful / jailbreak / indirect injection / benign (p. 5, §3.3; p. 20, App. H).
  - **Holdout by attack template or family within a dataset: not found after reading §1–§10 and App. A–R (pp. 1–27).** The finest holdout unit is the whole dataset.
  - The paper says TaskTracker "holds out attack types from training but trains and evaluates within the same constituent datasets, leaving dataset-level generalization unexamined" (p. 3, §2). Here "template" refers only to chat templates (p. 4, p. 17) and to Llama-as-Judge prompt templates (p. 3, §2), not to attack templates.
  - The official test splits are not capped: "the two accuracy columns for a given dataset are computed on different sample pools" (p. 7, Table 2 caption).
- **Deduplication and near-duplicates.** Only cross-dataset duplicates are audited.
  - Exact quote: "Embedding-based cross-dataset audit (text + raw activations) finds 10.5% exact cross-dataset duplicates, all benign prompts shared between benign-only datasets (common instructional phrases, email headers); no malicious duplicates exist across datasets." (p. 21, App. K)
  - Exact quote: "The overlap means CV permits a degree of data-leakage that LODO eliminates; if anything, deduplicating the benchmark would widen the CV-LODO gap." (p. 21, App. K)
  - The duplicates were not removed; the text says deduplicating "would" widen the gap (p. 21).
  - No similarity threshold or operational near-duplicate definition is given. Within-dataset deduplication or near-duplicate grouping was not found after reading pp. 1–27.
  - Similarity comparison: within-dataset text-embedding similarity is 0.635 and cross-dataset is 0.545, p = 0.005. In activation space the figures are 0.751 vs 0.662, p < 0.001 (p. 9, §5.4). The test used for these p-values was not found.
- **Template concentration and effective sample size.** Not found after reading pp. 1–27. The closest analyses are dataset-level: dataset-identity classifiers (p. 9; p. 22, App. O.1) and the similarity comparison above.

## Detectors / models evaluated
- **Trained in this paper.** Probes on Llama-3.1-8B-Instruct (layer 31 raw; layer-27 SAE from Arditi 2024), Gemma-3-27B (Gemma Scope 2 SAE, layer 42), Qwen-3.5-2B/4B, and a partial Llama-3.3-70B run (p. 4, §3.2; p. 18–19, App. F).
  - Hyperparameters: LogReg C=1.0, lbfgs, class_weight='balanced'. MLP: hidden 512, dropout 0.1, Adam 1e-3, 20 epochs (p. 5, §3.2).
  - Author-stated inconsistency: footnote 1 says "the main-table probe uses C=0.1" (p. 17), while §3.2 gives C=1.0 (p. 5).
  - Layer and position were "selected by aggregate LODO accuracy per model" (p. 8, Table 3 caption; p. 17, App. C.2).
  - INFERENCE: this means configuration was selected on the LODO evaluation itself.
  - A training-free Mahalanobis baseline (LPM) was also run (p. 21–22, App. N).
- **Released detectors, used off the shelf.**
  - PromptGuard 2 (Llama-Prompt-Guard-2-86M): "512-token chunking with max-pooling. Cannot process tool schemas; this prevents evaluation on InjecAgent." (p. 26, Q.1)
  - LlamaGuard 3 8B (p. 26, Q.2).
  - Llama-3.1-8B as judge, with 4 prompt variants (p. 21, App. J; p. 27, Q.3).
  - ProtectAI Guard v2 and Deepset prompt-injection v2 (both DeBERTa-v3-base), run "by serializing multi-turn conversations into plain text with explicit role markers" (p. 20, App. I). They are benchmarked "at their native operating points" (p. 2).
  - PIGuard/InjecGuard: not evaluated. Not found after reading pp. 1–27.
- **Indirect-injection data for the released detectors.** The "Indirect inj." category is BIPIA, InjecAgent and LLMail (p. 20, Table 12, LOCO definition).
  - Table 13 reports ProtectAI v2 indirect-injection detection of 8.0% with 4.2% benign FPR, and Deepset v2 >99.9% with 82.4% FPR (p. 20).
  - INFERENCE: Table 13's category probably uses the same three datasets as Table 12, but the paper does not say so explicitly for Table 13.
  - The LJ variants were tested on "10,054 prompts (3 indirect-injection datasets + 3 benign)" (p. 21, App. J); the datasets are not named there.
  - TaskTracker data was not used with any released detector (not found, pp. 1–27).

## Evaluation and statistics
- **Metrics.** ROC AUC, pooled over all held-out predictions (p. 5, §3.3). Accuracy at threshold 0.5; for single-class datasets this equals recall or 1−FPR (p. 8, Table 4). Weighted and macro averages. Detection rate by category at thresholds 0.5 and 0.9 (p. 10, Table 6).
- **Matched-FPR comparison.** The probe threshold is "calibrated to match baseline FPR=x on pure-benign datasets under LODO" at 0.4%, 3.0% and 4.4% (p. 26, Table 17). No 1%-FPR operating point was found.
- **Intervals.**
  - The only intervals on main results are "DeLong 95% CIs for pooled AUC: Raw 0.912 (0.911-0.915), SAE 0.838 (0.836-0.841), MLP 0.841 (0.839-0.843)" (p. 8, Table 4 caption), over N=105,034 pooled predictions.
  - INFERENCE: DeLong's method treats predictions as independent examples. No cluster-, dataset- or template-level correction was found after reading pp. 1–27.
  - One bootstrap CI is reported: "bootstrap 95% CI on the gap [+1.63,+1.78] pp" for targeted vs random subspace projection (p. 9, §5.4). The resampling unit is not stated.
  - The CV-LODO gaps (Tables 1–3, pp. 7–8), the per-dataset LODO accuracies (Table 4, p. 8), and the released-detector rates (Tables 6, 13, 17) have no intervals. Not found after reading pp. 1–27.
- **Seeds.** CV uses one split seed (random_state=42), and "logistic regression with the lbfgs solver is deterministic" (p. 5). Seeds are mentioned only for DANN: "BIPIA +13pp across seeds" (p. 19, App. G) and "remained stable across seeds" (p. 10). The number of seeds is not stated.
- **Other tests.** Sign test over 16 per-dataset deltas for LOCO vs LODO, p < 0.001 (p. 20, App. H). Random projections: −0.02 ± 0.13 pp over 10 draws (p. 9).
- **Same-source vs LODO numbers.**
  - Table 1, Llama-3.1-8B: 5-fold CV AUC 0.996; held-out test 0.997; LODO pooled 0.912; gap 8.4 pp (p. 7).
  - Table 3, CV vs LODO AUC: Llama-3.1-8B 0.996 vs 0.912 (8.4 pp); Gemma-3-27B 0.999 vs 0.920 (8.0 pp); Qwen-3.5-4B 0.998 vs 0.845 (15.4 pp); Qwen-3.5-2B 0.998 vs 0.829 (16.5 pp) (p. 8). Llama-3.3-70B LODO AUC is 0.910, with no paired CV.
  - Table 2, test vs LODO accuracy (p. 7):

    | Dataset | Test acc | LODO acc | Gap (pp) |
    | --- | --- | --- | --- |
    | mosscap | 99.5% | 79.4% | +20.1 |
    | jayavibhav | 94.5% | 69.1% | +25.4 |
    | qualifire | 95.8% | 77.8% | +18.0 |
    | enron | 99.2% | 82.6% | +16.6 |
    | safeguard | 97.9% | 96.7% | +1.2 |
    | deepset | 80.2% | 77.7% | +2.5 |

  - Mixed-class datasets excluding BIPIA: weighted CV-LODO gap 12.5 pp (range 3.4–22.2). Including BIPIA it is 41.1 pp (p. 21, App. L).
  - Per-dataset LODO on indirect sets (Llama-8B raw): BIPIA 63.1%, InjecAgent 98.9%, LLMail 71.4% (p. 8, Table 4). BIPIA AUC is 0.655 (p. 26, Fig. 6 caption).
  - LOCO is lower than LODO by 2.6 pp accuracy and 2.8 pp AUC (p. 20, App. H).

## Findings relevant to our claims
- **C1 (template concentration in the InjecGuard release). OVERLAP = none.**
  - The paper does not analyze the InjecGuard release or HackAPrompt, or within-source template concentration (not found, pp. 1–27).
  - It does measure dataset-level distinguishability (96.6% SAE dataset classifier) and within- vs cross-dataset similarity (p. 9, §5.4; p. 22, App. O.1).
  - Justifying pages: 16 (Table 7), 21 (App. K).
- **C2 (held-out templates within HackAPrompt). OVERLAP = partial.**
  - The paper shows the same general phenomenon at a coarser unit. Random-row CV reports AUC ≥ 0.996, while holding out whole datasets drops it to 0.829–0.920 (p. 8, Table 3).
  - Per-dataset gaps reach 25.4 pp (p. 7, Table 2).
  - It does not hold out templates or families within a dataset, and does not use HackAPrompt (p. 5, §3.3; not found, pp. 1–27).
  - Justifying page: 5 (§3.3), with Table 3 on p. 8.
- **C3 (design effects > 1; example-level intervals too narrow). OVERLAP = none.**
  - The paper's own intervals are example-level DeLong CIs over 105,034 pooled predictions (p. 8, Table 4 caption).
  - No design effect, cluster-robust interval or effective-sample-size analysis was found (pp. 1–27).
  - Justifying page: 8.
- **C4 (null inflation from row splits under randomized group splits within TaskTracker, BIPIA and jailbreak). OVERLAP = none.**
  - There are no within-dataset group-vs-row split comparisons, and the TaskTracker data is not used.
  - The paper's leakage finding is at dataset level: CV/test vs LODO (p. 7, Tables 1–2). BIPIA has no official test split, so it has no test-vs-LODO row (p. 7).
  - INFERENCE: this is a contrast at a different unit of analysis, not a contradiction.
  - Justifying page: 7.
- **C5 (withdrawn). OVERLAP = none.**
  - No within-dataset row-vs-group comparison on TaskTracker or BIPIA (p. 7; not found, pp. 1–27).
- **C6 (ProtectAI v2 low recall on indirect injection). OVERLAP = partial.**
  - Table 13 reports ProtectAI v2 at 8.0% indirect-injection detection with 4.2% benign FPR, and Jailbreak at 73.6% (p. 20, App. I). The operating point is native, not 1% FPR, and there is no interval.
  - The indirect category is BIPIA, InjecAgent and LLMail (p. 20, Table 12); TaskTracker is not used.
  - Justifying page: 20 (Table 13).
- **C7 (matched retraining vs threshold-only with 200 benign target labels). OVERLAP = none.**
  - There is no target-label adaptation budget or comparison of retraining with thresholding.
  - Related observations only: "Per-dataset optimal thresholds vary from 0.01 (BIPIA, deepset) to 0.73 (jayavibhav)" and "Calibration is itself distribution-dependent" (p. 25, App. P.1).
  - Justifying page: 25.
- **C8 (expected FPR 1/(B+1) from small benign calibration sets). OVERLAP = none.**
  - Matched-FPR thresholds are calibrated on large pure-benign LODO pools (p. 26, Table 17). No small-B analysis was found.
  - Justifying page: 26.
- **C9 (InjecGuard training file clean against its evaluation files). OVERLAP = none.**
  - InjecGuard is not audited. The only overlap audit is cross-dataset within the paper's own benchmark (p. 21, App. K).
  - Justifying page: 21.
- **C10 (deterministic vs randomized group allocation). OVERLAP = none.**
  - LODO folds are "deterministic by dataset identity" (p. 5). There is no group allocation to randomize at that unit, and no such comparison was found (pp. 1–27).
  - Justifying page: 5.

## Author-stated limitations (quoted, page-cited)
- "LODO measures static distribution generalization, not robustness to adaptive attackers." (p. 11, §8)
- "LODO treats each constituent dataset as a domain. When component datasets share methodology, LODO understates the deployment gap; when they are unrepresentative of production traffic, LODO may be pessimistic or optimistic depending on direction." (p. 11, §8)
- "Our activation-based approach requires access to model internals, limiting direct deployment with closed-source APIs." (p. 11, §8)
- "We establish the gap and show it resists seven standard domain-generalization interventions, but do not present a method that closes it." (p. 11, §8)
- "Ablating the 14 identified SAE shortcuts moves pooled AUC by only −0.1pp because other features compensate via redundant decision boundaries — we therefore do not claim shortcuts cause the gap." (p. 11, §6)
- "For DANN specifically, we did not find a parameter set that both improved aggregate accuracy and remained stable across seeds; we make no claim that such a setting does not exist." (p. 10, §5.5)
- "We do not report full per-dataset calibration curves (ECE, Brier) under LODO in this work" (p. 25, App. P.1)
- Our inferences, not author-stated:
  - INFERENCE: per-example DeLong intervals, a single CV seed, and layer/position selection by aggregate LODO accuracy (p. 8; p. 5) are not listed as limitations by the author.
  - INFERENCE: the Table 2 comparison mixes uncapped test pools with capped LODO pools. The author discloses this in the caption (p. 7) but does not list it in §8.

## Bibliographic entry (BibTeX)
```bibtex
@inproceedings{fomin2026whenbenchmarkslie,
  title     = {When Benchmarks Lie: Evaluating Malicious Prompt Classifiers under True Distribution Shift},
  author    = {Fomin, Max},
  booktitle = {First Workshop on Agents in the Wild: Safety, Security, and Beyond (AIWILD) at ICLR 2026},
  year      = {2026},
  eprint    = {2602.14161},
  archivePrefix = {arXiv},
  primaryClass  = {cs.LG},
  note      = {arXiv v2, 19 Jul 2026. Code: https://github.com/maxf-zn/prompt-mining}
}
```
