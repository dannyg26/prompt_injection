# A Critical Evaluation of Defenses against Prompt Injection Attacks [Dataset/Tool Paper]
- Authors / venue / year / version read: Yuqi Jia, Zedian Shao, Yupei Liu, Jinyuan Jia, Dawn Song, Neil Gong. Proceedings of the 31st ACM Symposium on Access Control Models and Technologies (SACMAT '26), July 8–10, 2026, Waterloo, ON, Canada. 6 pages, proceedings pp. 265–270, DOI 10.1145/3750555.3811884, ISBN 979-8-4007-2107-6/2026/07. Licensed CC BY 4.0 (p. 1).
- **Version read: the 6-page SACMAT 2026 publisher version only.** An extended arXiv version (2505.18333) may exist. It was NOT read, and whether it is the same work in longer form is UNVERIFIED. Nothing in this note applies to it.
- File read: literature/pdfs/critical_eval_sacmat26.pdf. Pages read: 1–6, all of them (body pp. 1–5, references and appendix Table 3 on p. 6).
- How it was read: the Read tool could not render the PDF because `pdftoppm` is missing. I extracted the text layer of all 6 pages with pypdf and read all of it. Unreadable parts: none. The paper has no figures. Some equations came out garbled (subscripts and summation signs split across lines, pp. 2–3, 5). Their meaning is clear from the surrounding text, and no garbled equation is quoted here.
- Page numbers are PDF pages 1–6. The printed proceedings page numbers are 265–270.

## What it does
- It argues that defenses are evaluated without rigor: "We argue that these claims rely on unrigorous evaluation, particularly in the choice of attacks, evaluation metrics, and benchmarks." (p. 1, §1)
- It proposes evaluating defenses on two dimensions: "(1) effectiveness, measured against both existing and adaptive prompt injection attacks involving diverse target and injected prompts, and (2) general-purpose utility" (p. 1, abstract). For detectors, utility is FPR and effectiveness is FNR (p. 3, §4.1.1, §4.2.1).
- It re-evaluates three prevention defenses: StruQ, SecAlign (released Llama-3-8B-Instruct fine-tunes) and Instruction Hierarchy (GPT-4o-mini) (p. 4, §5.1; pp. 4–5, §5.2–5.3; p. 4 Table 1; p. 5 Table 2).
- It re-evaluates two detection defenses, PromptGuard and Attention Tracker, reporting FPR, FNR and AUC under the Combined Attack (p. 5, §5.4; p. 6, Table 3a).
- It proposes a general adaptive-attack loss for detectors (evasion loss plus α × task cross-entropy, Eq. 3) and applies it to Attention Tracker with GCG (p. 5, §5.4; p. 6, Table 3b).
- It introduces a new benchmark, MMLU-PI, built from the MMLU test split (p. 4, §5.1).

## Data
- **OpenPromptInjection** (Liu et al., USENIX Security 2024, ref. [19]): "𝑃𝑅 in OpenPromptInjection consists of 700 prompt-response pairs sampled from seven NLP tasks, with 100 pairs per task." T (ASV tuples) has 4,900 tuples. X (clean) has 700 samples, 100 per task. X_c (contaminated) has 4,900 pairs (p. 4, §5.1).
- **MMLU-PI** (new): "𝑃𝑅 includes 200 prompt-response pairs sampled from the test split of MMLU". T has 1,000 tuples. X "comprises the 200 clean data samples from 𝑃𝑅". X_c has 1,000 pairs (p. 4, §5.1).
- **How contaminated examples are built:** "the data portion of one prompt serves as 𝑥, while another prompt provides 𝑝𝑒" (p. 4, §4.2.3). Contaminated data is x_t ‖ z ‖ p_e, where z is the separator produced by an attack (p. 2, §2).
- **GCG optimisation subset:** "we optimize the separator 𝑧 over 50 tuples from OpenPromptInjection and 25 from MMLU-PI" (p. 4, §5.2). For the adaptive attack on Attention Tracker, the authors "evaluate the adaptive attacks using the same tuples (𝑝𝑡,𝑟𝑡,𝑝𝑒,𝑟𝑒) as in Section 5.2" (p. 5, §5.4).
  - Whether the optimisation tuples are disjoint from the evaluation tuples: not stated, not found after reading pp. 1–6.
  - INFERENCE: the wording allows optimisation and evaluation on the same small tuple set. The paper does not say either way.
- **Train/test split, deduplication, near-duplicate or template handling:** Not found after reading §1–§6 and the Appendix (pp. 1–6).
  - No detector is trained here, so no train/test split is formed (p. 4, §5.1: released models only).
  - The word "template" does not appear in the extracted text. "Duplicate" appears only as the task name "duplicate sentence detection" (p. 3, p. 4).
- **Sampling procedure:** how the 700 and 200 pairs were sampled (random, seed) is not stated. Not found after reading pp. 1–6.
- **Our datasets:** HackAPrompt, TaskTracker, BIPIA, jailbreak-classification and the InjecGuard release are not used. Not found after reading pp. 1–6. BIPIA is cited only as ref. [42] among prevention methods (p. 1).

## Detectors / models evaluated
- **Trained here:** none. All defenses are released models or deployed APIs (p. 4, §5.1; p. 5, §5.4).
- **Released detectors evaluated:** two.
  - **PromptGuard** (Meta 2024, ref. [22]), described as fine-tuning "mDeBERTa-v3-base [11] on large attack corpora" (p. 2, §3). INFERENCE: this describes Prompt Guard v1, not Prompt Guard 2. The model version or HF identifier is not given (not found, pp. 1–6).
  - **Attention Tracker** (ref. [15]), run with Qwen2-1.5B-Instruct as the LLM (p. 5, §5.4).
- **Detectors not evaluated:**
  - **DataSentinel** (ref. [20], an S&P 2025 paper by several of the same authors) is only mentioned: "fine-tune LLMs in game-theoretic settings to detect injected prompts [20]" (p. 1, §1). It is not evaluated. Not found in §5 or Table 3, pp. 4–6.
  - **ProtectAI, PIGuard/InjecGuard and Deepset** are not mentioned anywhere. Not found after reading pp. 1–6.
  - **Embedding-based classifiers** (ref. [3], Ayub & Majumdar) are cited as detectors evaluated "only on existing attacks" (p. 1) but are not re-evaluated.
- **Detector results** (p. 6, Appendix Table 3a; Combined Attack; described on p. 5, §5.4):

| Detector | OPI FPR | OPI FNR | OPI AUC | MMLU-PI FPR | MMLU-PI FNR | MMLU-PI AUC |
| --- | --- | --- | --- | --- | --- | --- |
| PromptGuard | 0.89 | 0.00 | 0.92 | 0.84 | 0.00 | 0.75 |
| Attention Tracker | 0.00 | 0.00 | 1.00 | 0.00 | 0.69 | 1.00 |

- **Adaptive attack on Attention Tracker** (p. 6, Table 3b), FNR:
  - Separator only: 0.66 (OPI) and 1.00 (MMLU-PI).
  - Separator+Instruction: 0.96 and 1.00.
  - Separator+Instruction+Data: 0.96 and 1.00.
  - "All successfully evading samples also trigger the target LLM to produce the attacker-desired response" (p. 5, §5.4).
- **Prevention results:**
  - Table 1 (p. 4): win rate against Llama-3-8B-Instruct is 21.60% for StruQ and 36.42% for SecAlign. Absolute utility (OPI / MMLU-PI) is 0.54/0.35 for StruQ, 0.48/0.34 for SecAlign and 0.65/0.45 undefended.
  - Table 2 (p. 5): GCG ASV reaches 0.80–1.00 against StruQ.
  - For Instruction Hierarchy on GPT-4o-mini, Combined Attack ASVs are 0.68 and 0.75 (p. 5, §5.3).

## Evaluation and statistics
- **Metrics:**
  - Prevention: absolute utility, win rate and ASV (p. 3, Eq. 1).
  - Detection: FPR on clean data (p. 3, §4.1.1), FNR (p. 3, Eq. 2) and AUC.
- **Operating point / threshold:** The paper argues for thresholded metrics: "In practice, a detector must choose a decision threshold to separate clean from contaminated inputs, and a high AUC does not guarantee reliable thresholding or detection performance." (p. 3, §4.2.1)
  - Which threshold was used for PromptGuard and Attention Tracker (a native or default threshold, or one fit to data) is not stated. PromptGuard's label mapping (its INJECTION/JAILBREAK/BENIGN outputs) is also not stated. Not found after reading pp. 1–6.
  - No fixed-FPR operating point (e.g. recall at 1% FPR) is used. Not found, pp. 1–6.
- **Seeds, repeats, confidence intervals, standard errors, significance tests:** Not found after reading §1–§6 and the Appendix (pp. 1–6).
  - Every number in Tables 1–3 is a single point estimate with no interval (pp. 4–6).
  - The words "confidence", "interval", "seed", "variance", "bootstrap" and "standard error" do not occur in the extracted text.
- **Effective sample size / clustering:** Not found after reading pp. 1–6.
  - INFERENCE: the contaminated sets are crossed designs. X_c has 4,900 pairs built from 700 clean samples, and 1,000 pairs from 200 (p. 4, §5.1), so each clean sample and each injected prompt appears in several pairs.
  - INFERENCE: all detector FNRs in Table 3a use one attack template, the Combined Attack separator (p. 5, §5.4). Under our framing, the attack side of the detector evaluation is a single template.
  - The paper does not discuss either point.
- **Evaluation flaws it identifies:**
  1. **A single injected prompt:** "they often use a single example such as “Print exactly Hacked!”, which fails to capture the diversity of real-world attacks and leads to overly optimistic results." (p. 3, §4.2.1; also p. 1, §1; p. 4, §5.2)
  2. **Relative-only utility (win rate):** "comparable win rates, even when both are high, do not necessarily reflect true performance, as both defended and undefended LLMs may exhibit low-quality outputs" (p. 3, §4.1.1). Also: AlpacaFarm "provides prompts but lacks ground-truth responses" (p. 3, §4.1.2).
  3. **AUC-only detector evaluation:** "Some defenses rely solely on the Area Under the Curve (AUC) as an effectiveness metric, which is insufficient in deployment since AUC reflects a detector’s ability to rank clean and contaminated samples, not to classify them accurately." (p. 3, §4.2.1)
  4. **Narrow attack sets:** "several defenses [15, 37] claim effectiveness based only on a narrow subset of existing attacks" (p. 3, §4.2.2).
  5. **No adaptive attacks:** "Many defenses [1, 7, 15, 37] omit adaptive evaluations, weakening the credibility of their claims." (p. 3, §4.2.2)
  6. **Narrow utility benchmarks:** FPR "should also be measured on diverse benchmarks" (p. 3, §4.1.2).
- **Flaws it does NOT identify:** train/test template overlap, near-duplicates, data leakage between training and evaluation data, split procedure, effective sample size, and statistical uncertainty or confidence intervals. Not found after reading §1–§6 and the Appendix (pp. 1–6).
- **Proposed principles:** "the effectiveness and utility of a defense should be tested against diverse attacks–including both existing and adaptive ones–alongside a broad range of target and injected prompts, meaningful metrics, and large-scale benchmarks." (pp. 1–2, §1) Also: "Detection methods should be assessed using metrics such as false positive rate (FPR) and false negative rate (FNR), rather than solely relying on AUC." (p. 2, §1)

## Findings relevant to our claims
The paper studies different evaluation flaws from ours: attack diversity and adaptivity, and metric choice. It does not study data partitioning or statistical uncertainty. It does not pre-empt any claim in docs/CLAIMS.md.

- **C1 (template concentration in the InjecGuard release):** does not audit any training release or measure template concentration.
  - INFERENCE, adjacent only: its critique that a single injected prompt "leads to overly optimistic results" (p. 3) is a concern about low attack diversity. It concerns evaluation prompts for prevention defenses, not the composition of training data. OVERLAP = none.
- **C2 (held-out-template recall 0–100% vs ~100% under row splits):** no detector is trained and no split is formed (p. 4, §5.1). Not found, pp. 1–6.
  - The closest point is that results on narrow prompt or attack sets overstate defense success (p. 3, §4.2.1–4.2.2; p. 4, §5.2; p. 5, §5.3). That is a coverage argument about evaluation sets, not a train/test leakage measurement. OVERLAP = none (conceptually adjacent: a "diversity" principle).
- **C3 (design effects >1; example-level intervals too narrow):** reports no intervals, seeds or effective sample sizes at all (pp. 4–6, Tables 1–3). Not found, pp. 1–6.
  - INFERENCE: its X_c sets are crossed (700 clean × 7 = 4,900; p. 4), and detector FNRs use one attack template (p. 5). It could serve as an example of clustered evaluation reported without intervals, but it makes no claim about this. OVERLAP = none.
- **C4 (no measurable row-vs-group inflation on small-group sources):** Not found, pp. 1–6. OVERLAP = none.
- **C5 (withdrawn):** n/a.
- **C6 (ProtectAI v2 27–30% recall@1% FPR on indirect sources vs 85–99% direct):** does not evaluate ProtectAI (not mentioned, pp. 1–6).
  - It evaluates PromptGuard, apparently v1 (INFERENCE from "mDeBERTa-v3-base", p. 2), on OPI and MMLU-PI with the Combined Attack. PromptGuard has FNR 0.00 but FPR 0.89/0.84, with AUC 0.92/0.75 (p. 6, Table 3a). That is over-flagging of benign data, the opposite failure mode from C6's missed indirect injections.
  - This adds no support for C6's "already shown" status. It may be cited as a separate released-detector failure (FPR) at an unstated threshold. OVERLAP = none.
- **C7 (matched benign retraining vs threshold-only):** no adaptation or retraining experiments. Not found, pp. 1–6. OVERLAP = none.
- **C8 (1/(B+1) expected FPR from B benign labels):** it argues that thresholded FPR/FNR, not AUC, should be reported (p. 3, §4.2.1; p. 5, §5.4), and shows high AUC alongside unusable FPR (PromptGuard) or FNR (Attention Tracker) (p. 6, Table 3a).
  - It does not discuss how thresholds are set or how many labels calibration needs, and does not state which thresholds it used. Not found, pp. 1–6.
  - It can be cited to motivate fixed-operating-point reporting. OVERLAP = none (adjacent motivation only).
- **C9 (InjecGuard train file clean vs eval):** Not found, pp. 1–6. OVERLAP = none.
- **C10 (deterministic allocation produced a spurious result):** no splits. Not found, pp. 1–6. OVERLAP = none.

INFERENCE for the novelty auditor:
- This paper removes the SACMAT 2026 risk named in NOVELTY_VERDICT.md, for the SACMAT version only. None of C1–C3 is pre-empted by it.
- The arXiv 2505.18333 version was not read. The absence of these topics in that version is UNVERIFIED.
- Related Work can cite it as the attack-diversity/adaptive-attack/metric critique that complements our partition/uncertainty critique. Neither critique covers the other.

## Author-stated limitations (quoted, page-cited)
- No limitations section. Not found after reading pp. 1–6.
- The only scope-limiting statements are about computation: "For computational efficiency, we optimize the separator 𝑧 over 50 tuples from OpenPromptInjection and 25 from MMLU-PI" (p. 4, §5.2).
- The authors give a hedged explanation for one of their results: the adaptive Combined Attack "does not yield higher ASVs, likely because it introduces nearly twice as many tokens" (p. 5, §5.2).
- The code/data link on p. 1 is anonymised ("https://github.com/PIEval123/PIEval"). Whether it is still live is UNVERIFIED.

## Bibliographic entry (BibTeX)
```bibtex
@inproceedings{jia2026critical,
  author    = {Jia, Yuqi and Shao, Zedian and Liu, Yupei and Jia, Jinyuan and Song, Dawn and Gong, Neil},
  title     = {A Critical Evaluation of Defenses against Prompt Injection Attacks},
  booktitle = {Proceedings of the 31st ACM Symposium on Access Control Models and Technologies (SACMAT '26)},
  year      = {2026},
  pages     = {265--270},
  address   = {Waterloo, ON, Canada},
  publisher = {ACM},
  doi       = {10.1145/3750555.3811884},
  note      = {Dataset/Tool Paper. 6-page SACMAT version read; extended arXiv 2505.18333 not read (UNVERIFIED)}
}
```
