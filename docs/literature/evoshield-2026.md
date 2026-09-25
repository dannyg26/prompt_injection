# EvoShield: Selective Test-Time Adaptation for Prompt Injection Detection via Active LLM Querying

- Authors / venue / year / version read: Zanhong Zheng, Jieming Liang, Mengqin Hu, Yijuan Pei, Guobao Xu, Zhenlu Wu (corresponding, zlwu@gdou.edu.cn), Guangdong Ocean University. *Mathematics* (MDPI) 14(10):1719, 2026, DOI 10.3390/math14101719 (p. 1). Dates printed on the PDF: received 15 April 2026, revised 7 May 2026, accepted 14 May 2026, published 16 May 2026 (p. 1). The PDF has no version label. The caller calls this "v2", and docs/EVOSHIELD_RESOLUTION.md records a publisher update on 21 May 2026. Whether this PDF is that updated version: UNVERIFIED.
- File read: /home/user/prompt_injection/literature/pdfs/evoshield_math26.pdf. Pages read: 1–19 (all pages), rendered through the Read tool's native PDF input, with text and page images. Unreadable parts: none. The curves in Figures 2 and 3 (pp. 15–16) are small. I relied on the authors' descriptions of them, not on values read off the plots.

## What it does
- It frames prompt-injection detection as "a selective test-time adaptation problem" over an input stream (p. 1 Abstract; p. 4 §3.1).
- A local detector (bert-base-uncased used as a masked LM, with a learnable soft verbalizer following PTE) outputs a class distribution. Its Shannon entropy H(x) decides the route: if H(x) ≤ τ the local prediction is used, and if H(x) > τ the input goes to an external LLM (pp. 4–6, §3.2–3.3, Eqs. 1–4).
- Queried samples whose LLM label can be parsed are used for an immediate update. They are also stored in a bounded review window (default 128) that is replayed for further updates. Samples whose labels cannot be parsed are skipped (p. 6 §3.4, Eq. 5; p. 8 §4.2).
- It evaluates four external LLMs (Claude Sonnet 4.6, Gemini 3.1 Pro Preview, GPT-5.2, Grok-4.1 Fast Reasoning) against "Vanilla" pure-LLM baselines on four binary datasets. It reports retention ratios and API-call counts (p. 9 §5.1; p. 10 Table 2).
- It includes sensitivity sweeps over the entropy threshold τ and the review-window size (p. 11 Table 4; p. 12 Table 5), an ablation (Vanilla local detector / without review / full; p. 13 Table 6), security metrics (Attack Recall, FNR, FRR; p. 14 Table 7), and an ordered JC(Balanced)→PI distribution-shift stream (p. 14 §5.4, Table 8).

## Data
- Four datasets (pp. 6–7 §4.1):
  - PI = deepset/prompt-injections (ref. 28, p. 19).
  - JC-balanced and JC-imbalanced = jackhhao/jailbreak-classification (ref. 29, p. 19).
  - SG = "Safe-Guard prompt injection detection". Its citation, ref. 30 (p. 19), is "Synthetic data (almost) from scratch: Generalized instruction tuning" (arXiv:2402.13064). INFERENCE: this citation may not identify the Safe-Guard dataset itself. The exact dataset source is UNVERIFIED.
  - How the balanced and imbalanced JC variants were built from the source: Not found after reading §4.1–§4.2 (pp. 6–9).
- Split procedure, quoted: "We merged the original data splits and randomly sampled a 16-shot subset to serve as the training set, reserving the remainder as the test set." (p. 7 §4.1). Table 1 gives 16 rows per class for training (32 in total) in every dataset. Test sets: JC-balance 1,274 (624 benign / 650 attack); JC-imbalance 1,966 (1,316 / 650); PI 630 (383 / 247); SG 2,052 (1,440 / 612). SG also has a validation set of 205 (143 / 62) (p. 7 Table 1).
- The train/test split is a random row-level split of the merged original splits (p. 7 §4.1). Deduplication, near-duplicate handling, and template, paraphrase or group handling: Not found after reading §3–§6 (pp. 4–17).
- Use of training/validation data, quoted: the training and validation splits "are used for the vanilla local-detector baseline and the related local-detector ablation analysis … They are not used to initialize or tune EvoShield in the main evaluation." (p. 7 §4.1). EvoShield is "cold-started from bert-base-uncased and the prompt/verbalizer configuration, without using target-task training or validation labels before deployment" (p. 8 §4.2).
- Label use in the stream, quoted: "During online testing, ground-truth labels in the stream are kept hidden from the model and are used only after prediction for metric computation." (p. 7 §4.1)
- Data availability: github.com/Lh-Liang/EvoShield (p. 18).

## Detectors / models evaluated
- Trained in this paper: the bert-base-uncased prompt-based detector with a soft verbalizer (p. 5 §3.2; p. 8 §4.2). There are two regimes:
  - (a) A "trained local-detector baseline" fit on the 16-shot training sets. Epochs (200) were chosen by grid search on the SG validation split (p. 8 §4.2).
  - (b) EvoShield, cold-started and adapted online (p. 8 §4.2).
  - INFERENCE: the Table 6 "Vanilla" row (0 API calls) is regime (a). Table 2 "Vanilla" is the pure-LLM baseline (p. 10 Table 2 caption, p. 12 §5.3.1).
- External LLMs used as the supervision source and as baselines: Claude Sonnet 4.6, Gemini 3.1 Pro Preview, GPT-5.2, Grok-4.1 Fast Reasoning, at temperature 0, with the same prompt template and label parser (p. 9 §4.2).
- Released detectors (PromptGuard, ProtectAI, PIGuard/InjecGuard, PromptShield, and others) appear only in Related Work (p. 3 §2, refs. 10–12). Evaluation of any released detector: Not found after reading §4–§5 (pp. 6–14).

## Evaluation and statistics
- Primary metric is accuracy, with Macro-Precision, Macro-Recall and Macro-F1. "Overall" is the mean of the four (p. 7 §4.2; p. 10 Table 2 caption). For EvoShield, "these metrics are computed cumulatively on the online test stream after each prediction has been made." (p. 7 §4.2)
- Security metrics (p. 8 Eqs. 9–10): Attack Recall, FNR, and "the false rejection rate (FRR), which measures how often benign samples are incorrectly rejected as attacks". FRR = FP/(FP+TN) is the benign false-positive rate. FRR is reported only for EvoShield (p. 14 Table 7). FRR for the pure-LLM baselines, the vanilla local detector, the w/o-review ablation or the shift stream: Not found after reading §5.1–§5.4 (pp. 9–14). Table 8 reports Acc, Attack Recall, FNR, QR and entropy, but no FRR (p. 14).
- Operating point: the classification decision is the local argmax or the LLM label (p. 6 Eq. 4). τ is an entropy routing threshold (default 0.2), not a decision threshold on the attack score (p. 5 §3.3; p. 8 §4.2). Reporting at fixed-FPR operating points (e.g. recall at 1% FPR): Not found after reading §4–§5.
- Seeds, quoted: "We use random seed 42 for all experiments." (p. 8 §4.2). One stream order per dataset. Repeated seeds, shuffled stream orders or repeated 16-shot draws: Not found after reading §4–§6.
- Confidence intervals, standard errors or significance tests: Not found after reading §4–§6 (pp. 6–17). All tables give point estimates (Tables 2–8, pp. 10–14).
- The sensitivity sweeps use GPT-5.2 only, averaged over the four tasks, varying one parameter at a time (p. 11 §5.2). INFERENCE: τ and the window size were swept on the same test streams that are reported. The authors call the defaults "default operating settings rather than globally optimal constants" (p. 8).
- Internal inconsistency (our observation, not author-stated): with GPT-5.2 at τ = 0.20 and window 128, Table 4 reports an average Macro-F1 of 0.8746 (p. 11), while Table 5 reports 0.8598 (p. 12) for what appears to be the same setting.

## Adaptation labels (what is adapted on)
- The adapted samples are the high-entropy stream inputs routed to the LLM, which then return a parsable label. Quoted: "Whenever a high-entropy sample receives a parsable LLM label, the pair (xt, yLLM t) is added to a bounded review window." (p. 6 §3.4)
- Selection is by uncertainty only, not by class. Both benign and malicious samples can therefore be adapted on, whichever label the LLM returns (p. 5 §3.3; p. 6 §3.4). The paper does not report a breakdown of queried or adapted samples by class (benign vs attack): Not found after reading §5–§6 (pp. 9–16).
- How many: per-stream API calls range from 123 to 316 in the main runs (p. 10 Table 2; e.g. 133/1,274 for JC-balanced with Claude, 316/2,052 for SG with Grok). The number actually added to the window is the parsable subset of these. Counts of unparsable outputs: Not found.
- Labels come from an LLM, not from humans or ground truth. The authors treat the LLM "as a fallible auxiliary supervision source rather than as a perfectly reliable oracle" (p. 5 §3.3).
- Effect on benign false positives: no before/after-adaptation FRR is reported. The only FRR values are the end-of-stream EvoShield figures in Table 7, which range from 0.005 (PI, GPT-5.2) to 0.196 (SG, Grok) (p. 14 Table 7). The authors state: "some SG settings achieve high Attack Recall but have larger false rejection rates" (p. 13).

## Findings relevant to our claims
- **Study 3 (distribution-matched benign augmentation vs over-defense).**
  - EvoShield does not add benign examples selected to match a shifted or external benign distribution.
  - It does not add curated or generic hard negatives.
  - It does not adjust the binary decision threshold to control FPR.
  - It does not target over-defense as an endpoint. "Over-defense" appears only when describing PIGuard/InjecGuard (p. 3 §2).
  - Its adaptation data are LLM-labelled, uncertainty-selected target-stream samples of either class (p. 6 §3.4). It never reports class composition or an FRR change (Tables 2–8, pp. 10–14).
  - Its shift experiment is attack-side: jailbreak → prompt injection, measured by Attack Recall/FNR (p. 14 Table 8).
  - **Verdict: DOES NOT pre-empt Study 3.** Adjacent only, in that target-stream samples are used for adaptation.
- **C7** (equal-budget threshold-only vs generic vs matched benign retraining). None of the three arms, and no equal label budget, is found after reading §4–§5 (pp. 6–14). The τ sweep (Table 4, p. 11) changes routing and API usage, not the decision threshold. The window-size sweep (Table 5, p. 12) and the ablation (Table 6, p. 13) change the replay and adaptation mechanism, not the data provenance. **OVERLAP = none.** This confirms docs/EVOSHIELD_RESOLUTION.md. One point to add there: the full PDF reports FRR (benign FPR) for EvoShield only (Table 7), with no seeds beyond 42 and no intervals.
- **C1** (template concentration in the InjecGuard/HackAPrompt release): no template or group analysis; HackAPrompt and InjecGuard data are not used (pp. 6–7). **OVERLAP = none.**
- **C2** (leave-one-level-group-out on HackAPrompt): no held-out template or group evaluation. The only held-out-distribution test is the ordered JC→PI dataset shift (p. 14). **OVERLAP = none.**
- **C3** (design effects; example-level intervals too narrow): no intervals of any kind; single seed 42 (p. 8). **OVERLAP = none.**
- **C4** (row vs group split inflation): uses random row-level splits only, with no group comparison (p. 7). **OVERLAP = none.**
- **C5** (withdrawn): n/a.
- **C6** (ProtectAI v2 on indirect attacks): ProtectAI is not evaluated; PI is deepset/prompt-injections, a direct-prompt dataset (p. 19 ref. 28). **OVERLAP = none.**
- **C8** (threshold from B benign labels has expected FPR 1/(B+1)): no FPR-targeted threshold setting (p. 5 §3.3; p. 8). **OVERLAP = none.**
- **C9** (InjecGuard train/validation contamination): not used. Aside: EvoShield's own SG validation split is used only for epoch selection of the local baseline, not for EvoShield (p. 7). **OVERLAP = none.**
- **C10** (deterministic group allocation): no group allocation; random 16-shot sampling with seed 42 (pp. 7–8). **OVERLAP = none.**

## Author-stated limitations (quoted, page-cited)
- "The bounded review window lets the detector rapidly reuse recently queried hard cases, but it may also bias local updates toward newly observed difficult samples rather than representing the full deployment distribution." (p. 6 §3.4)
- "Because the review window is recent and difficulty-focused, local forgetting remains possible: if online updates make the detector less stable on standard benign inputs or previously familiar patterns, the affected samples may receive higher predictive entropy and therefore be escalated to the external LLM." (p. 6 §3.4)
- "This experiment is intended as an initial non-stationary stream evaluation rather than a complete adaptive-attack benchmark." (p. 14 §5.4)
- "…the results should not be interpreted as evidence of full robustness against perturbation, paraphrasing, or deliberately adaptive entropy-evasion attacks." (p. 14 §5.4)
- "EvoShield does not guarantee that the local detector will become uncertain before every error. In particular, a malicious input may be assigned a low-entropy, high-confidence benign prediction by the local model." (p. 17 §6.3)
- "EvoShield should be understood as a cost-aware adaptation framework rather than a complete standalone defense against all prompt-injection evasion strategies." (p. 17 §6.3)
- On the PI query ratio: "This difference should be interpreted with caution." It is attributed to the small PI test set (p. 16 §6.2.1).
- Other backbones are left to future work: "We regard a full architecture-efficiency comparison among these backbones as complementary future work." (p. 5 §3.2)

## Bibliographic entry (BibTeX)
```bibtex
@article{zheng2026evoshield,
  title   = {EvoShield: Selective Test-Time Adaptation for Prompt Injection Detection via Active LLM Querying},
  author  = {Zheng, Zanhong and Liang, Jieming and Hu, Mengqin and Pei, Yijuan and Xu, Guobao and Wu, Zhenlu},
  journal = {Mathematics},
  volume  = {14},
  number  = {10},
  pages   = {1719},
  year    = {2026},
  doi     = {10.3390/math14101719},
  publisher = {MDPI}
}
```
