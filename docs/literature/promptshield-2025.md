# PromptShield: Deployable Detection for Prompt Injection Attacks
- Authors / venue / year / version read: Dennis Jacob, Hend Alzahrani, Zhanhao Hu, Basel Alomair, David Wagner. ACM CODASPY '25, June 4–6 2025, Pittsburgh. Publisher (ACM) version, DOI 10.1145/3714393.3726501, proceedings pp. 341–352 (p. 1).
- File read: `literature/pdfs/promptshield_codaspy25.pdf`, pages read: 1–12 (all). The PDF page numbers used below map to proceedings pages as PDF p. N = proc. p. 340+N.
- Reading method / unreadable parts: The Read tool could not render the PDF because `pdftoppm` is not installed. The full text of all 12 pages was extracted with `pypdf` (per-page text) and read in full. Figures 1–3 are images, so only their captions were read. Ligatures such as "fi" and "ff" were lost in extraction. All numbers in the tables came through as text.
- **Not in this file:** Appendices A.1 (LMSYS toxicity filtering), A.2 (full list of injection link phrases), A.3 (validation split), B.2 (PromptGuard scoring) and C (attack effectiveness). The paper says they are in an extended technical report, arXiv 2501.15145 (p. 2, footnote 1). They were **not read**. Everything that depends on them is UNVERIFIED.

## What it does
- It introduces the PromptShield benchmark for training and evaluating prompt-injection detectors. The benchmark uses a taxonomy of "conversational data" (treated as always benign) and "application-structured data" (prompt || data, at risk of injection) (p. 4, §2.4; p. 5, Table 1).
- It fine-tunes the PromptShield detector (Llama-3.1-8B-Instruct with LoRA as the primary model, plus FLAN-T5, Llama-3.2-1B and DeBERTa-v3-base variants) on the benchmark's training split (p. 6, §3.2.1; p. 7, §4).
- It evaluates AUC and TPR at 1%, 0.5%, 0.1% and 0.05% FPR. Thresholds are calibrated on the evaluation split by interpolating the ROC curve, for its own detector and for released detectors (p. 7, §3.2.2, §4).
- It compares against released detectors: PromptGuard, ProtectAI v1, ProtectAI v2, InjecGuard and Fmops (p. 9, Table 4).
- It ablates model size (p. 8, §5.3; p. 9, Table 5), training-set size (1K/5K/10K/20K) (pp. 8–9, §5.4, Table 6) and training-data composition, with and without conversational data (pp. 9–11, §5.5, Tables 7–9).
- Focus is on indirect prompt injection. GCG-style optimization attacks, multi-turn conversations and function calling are out of scope (p. 3, §2.2; p. 4, §2.4).

## Data
- **Sources (p. 4, §3.1.1; p. 5, Table 1, §3.1.2):**
  - Benign conversational: Ultrachat; LMSYS (first turn only, toxicity-filtered with OpenAI moderation); prompt-only Alpaca and databricks-dolly; IFEval.
  - Benign application-structured: Alpaca, databricks-dolly, natural-instructions, Synthetic Python Problems (SPP).
  - Injections: "FourAttacks" (naive, ignore, completion and combined attacks from the StruQ implementation, applied to Alpaca, dolly and SPP samples, "a total of 12 combinations"); OpenPromptInjection attacks, "seeded by a separate set of benign datasets"; HackAPrompt (p. 6, §3.1.2).
- **How train and evaluation were formed: by dataset or source, not by random rows (p. 6, §3.1.3, Table 2).**
  - Train: benign Ultrachat, Alpaca and IFEval; injections FourAttacks (Alpaca) and HackAPrompt.
  - Evaluation: benign LMSYS, databricks-dolly, natural-instructions and SPP; injections FourAttacks (databricks-dolly), FourAttacks (SPP) and OpenPromptInject.
  - Quote: "The training and evaluation splits contain mutually exclusive subsets of the curated data discussed in Table 1." (p. 6, §3.1.3)
  - Quote: "Overall, we include the more filtered/simpler data (i.e., Ultrachat, Alpaca) in the training split and the more sophisticated data (i.e., natural-instructions, SPP) in the evaluation split. This is done so that the evaluation split can measure the out-of-distribution (OOD) performance of detectors fine-tuned on our training split." (p. 6, §3.1.3)
  - The assignment is a single, deliberate (non-random) allocation. No repeated or randomized source splits were found (p. 6, §3.1.3).
- **Template handling (injection link phrases) (p. 6, §3.1.3):**
  - Quote: "we leverage a set of 10 phrases (i.e., “Ignore all instructions...”, “Please disregard all previous...”, etc.) for the train split and a distinct set of 11 phrases (i.e., “Oh, never mind...”, “Now, erase everything...”, etc.) for the evaluation split. Attacks are randomly assigned phrases from the set corresponding to their benchmark split."
  - Stated rationale: "This is done to ensure that detectors fine-tuned on our training split do not simply memorize common terms to detect possible injections."
  - The full phrase list is in Appendix A.2 (not in this file; UNVERIFIED).
  - INFERENCE: the four attack *strategies* (naive, ignore, completion, combined) are the same in both splits. Only the carrier dataset and the link phrase change. The naive attack has no link phrase (p. 5, §3.1.2), so it is not phrase-disjoint. The paper does not say whether the injected tasks or payloads (e.g., "Please output 'Injected.'") differ between splits. Not found after reading §3.1–§4.
  - HackAPrompt is used only in training (p. 6, Table 2). No analysis of its internal template or level structure was found after reading §3–§5.
- **Overlap checks with other datasets (p. 6, §3.1.3):**
  - Quote: "We are able to confirm (to a best effort) that the training sets of PromptGuard [30], ProtectAI [21, 22], and InjecGuard [13] do not overlap with our evaluation split."
  - The method of this check (exact match, near-duplicate, or by dataset name) is not described in the main text. Not found after reading §3–§5.
  - Fmops is not listed in the overlap check (p. 6, §3.1.3).
- **Deduplication or near-duplicate handling:** no row-level deduplication, near-duplicate threshold or cross-split similarity check within the benchmark was found after reading §1–§8 and Tables 1–9. Disjointness is argued at the level of dataset source and link phrase only (p. 6, §3.1.3).
- **Sizes:**
  - Detector training: 20,000 points sampled from the training split, "roughly 10,000" benign and 10,000 malicious; all English (p. 6, §3.2.1).
  - Validation: "~1000 random datapoints from the training dataset" (p. 6, §3.2.1). INFERENCE: this is a random-row validation split from the same sources as training.
  - Evaluation: "~24,000 datapoints" sampled from the evaluation split (p. 7, §4). Per-source and per-class counts are not given in the main text. Not found after reading §3–§5.
- **Training augmentation:** 1–3 random newlines inserted before the prompt, before the data and after the data (p. 7, §4).
- **Licenses:** the paper itself is CC BY-ND 4.0 (p. 1). The benchmark's license and the licenses of its component datasets are not stated in the pages read: UNVERIFIED. The benchmark is released at huggingface.co/datasets/hendzh/PromptShield and the code at github.com/wagner-group/PromptShield (p. 2).

## Detectors / models evaluated
- **Trained here (PromptShield):** DeBERTa-v3-base (184M), FLAN-T5-small, base and large (61M, 223M, 751M), Llama-3.2-1B-Instruct, and Llama-3.1-8B-Instruct (8B, primary) (p. 8, §5.3; p. 9, Table 5).
  - Llama models: LoRA, 3 epochs, learning rate 2e-4.
  - FLAN models: full fine-tuning, 3 epochs, learning rate 5e-5.
  - DeBERTa: learning rate 5e-6.
  - All use early stopping on validation (p. 7, §4).
- **Released detectors evaluated (p. 9, Table 4; p. 10, §6):**
  - PromptGuard (mDeBERTa-v3-base, 279M), scored on the injection class only (p. 8, §5.1; details in Appendix B.2, not read).
  - ProtectAI v1 (DeBERTa-v3-base), ref [22]: `protectai/deberta-v3-base-prompt-injection`.
  - ProtectAI v2 (DeBERTa-v3-base), ref [21]: `protectai/deberta-v3-base-prompt-injection-v2` (p. 11, refs).
  - InjecGuard (DeBERTa-v3-base).
  - Fmops (DistilBERT, 67M).
- Attention Tracker is discussed but not evaluated (p. 10, §6).

## Evaluation and statistics
- **Metrics:** ROC AUC, and TPR at 1%, 0.5%, 0.1% and 0.05% FPR (p. 7, §4).
- **Threshold selection is done on the evaluation data itself (p. 7, §3.2.2):**
  - Quote: "we cache model output scores on the evaluation split and compute both true positive rates (TPR) and false positive rates (FPR) across a range of decision thresholds... We then use linear interpolation on the curve to find a threshold that results in a FPR close to our target (i.e., within 25%)." A bisection fallback is used.
  - This calibration is applied "retroactively" to the competing detectors (p. 7, §3.2.2).
  - The authors acknowledge the problem. Quote: "In retrospect, we should have used the validation split for this calibration step. We recommend that future work compute the decision threshold using the validation set." (p. 7, §3.2.2)
  - Table footnote †: a value is "set to 0% as there does not exist a threshold that achieves the desired FPR aside from 1.0" (p. 9, Tables 4–5).
- **FPR pooling:** the benign pool for the Table 4 FPR mixes conversational (LMSYS) and application-structured (dolly, natural-instructions, SPP) benign data (p. 6, Table 2; p. 7, §4). INFERENCE: TPR is pooled over all evaluation injection sources. No per-source TPR for released detectors was found after reading §5 and Tables 3–9.
- **Seeds:** no number of training seeds, repeated runs or run-to-run variance is reported. Not found after reading §3–§8 and Tables 3–9.
- **Confidence intervals:** no confidence intervals, standard errors or significance tests are reported for any metric. Every number is a single point estimate. Not found after reading §3–§8 and Tables 3–9.
- **Uncertainty unit:** there is no discussion of example-level vs group- or cluster-level uncertainty. Not found after reading §1–§8.
- **Composition-ablation thresholds (p. 10, §5.5.1):** thresholds are chosen at target FPRs on the *application-structured* evaluation subset and then applied to the full and conversational-only subsets.
  - Table 9, conversational benign FPR at thresholds tuned for 1% / 0.5% / 0.1% / 0.05%: 1.61% / 1.03% / 0.18% / 0.06% with conversational training data, and 2.15% / 1.25% / 0.38% / 0.32% without (p. 11).

## Key reported numbers (single runs, no intervals, thresholds fit on the evaluation data)
- **Table 4 (p. 9)**, AUC / TPR at 1% / 0.5% / 0.1% / 0.05% FPR:

  | Detector | AUC | TPR@1% | TPR@0.5% | TPR@0.1% | TPR@0.05% |
  | --- | --- | --- | --- | --- | --- |
  | PromptGuard | 0.874 | 12.78% | 12.43% | 9.39% | 1.54% |
  | ProtectAI v1 | 0.646 | 7.05% | 3.36% | 0.00%† | 0.00%† |
  | **ProtectAI v2** | **0.705** | **1.97%** | 1.34% | 0.00% | 0.00%† |
  | InjecGuard | 0.765 | 20.37% | 16.30% | 6.61% | 4.32% |
  | Fmops | 0.754 | 13.00% | 8.39% | 2.10% | 1.48% |
  | PromptShield DeBERTa-v3-base | 0.976 | 43.22% | 40.50% | 31.45% | 0.00%† |
  | PromptShield Llama-3.1-8B | 0.998 | 94.80% | 87.80% | 65.33% | 47.53% |

- **PromptGuard at fixed thresholds (p. 8, Table 3):**
  - Threshold 0.5: TPR 22.82%, FPR 2.91%.
  - Threshold 0.99988: TPR 12.81%, FPR 1.03%.
  - The authors contrast this with PromptGuard's self-reported 71% TPR at 1% FPR, cited to [7] (p. 8, §5.1).
- **Training-set size (Llama-8B, p. 9, Table 6):** TPR@1% FPR is 62.04% (1K), 89.62% (5K), 88.84% (10K) and 94.80% (20K). The subsets share the same 1,000-point validation split (p. 8, §5.4).
- **Composition ablation (p. 11, Tables 7–8):** on application-structured test data, TPR at the 0.05%-FPR threshold is 53.68% with conversational training data and 70.90% without. At 1%, TPR is 95.40% vs 96.19%.

## Findings relevant to our claims
- **C1** (template concentration of the InjecGuard release; HackAPrompt forms 6 groups). The paper includes HackAPrompt in training (p. 6, Table 2) but does no template or group concentration analysis of HackAPrompt or of the InjecGuard release. Not found after reading §3–§5. **OVERLAP = none** (p. 6).
- **C2** (recall on held-out HackAPrompt templates vs row splits). The paper holds out link phrases (10 train vs 11 evaluation) and dataset sources to measure OOD performance (p. 6, §3.1.3). It does not compare against a row-split baseline, does not do leave-one-template-out, and uses HackAPrompt only for training. **OVERLAP = none** (p. 6). Related design only: phrase-disjoint splits motivated by memorization (p. 6 quote above).
- **C3** (design effects above 1; example-level intervals too narrow). No intervals of any kind; no cluster or design-effect analysis. Not found after reading §3–§8. **OVERLAP = none** (pp. 7–9).
- **C4** (row vs randomized group splits: no measurable inflation on TaskTracker, BIPIA or jailbreak-classification). TaskTracker, BIPIA and jailbreak-classification are not used (p. 5, Table 1). There is no row-vs-group split comparison. **OVERLAP = none** (pp. 5–6).
- **C5** (withdrawn). **OVERLAP = none**.
- **C6** (ProtectAI v2 recall at 1% FPR about 27–30% on document-embedded injections in TaskTracker and BIPIA, vs 85–99% on direct attacks).
  - The paper reports ProtectAI v2 **TPR 1.97% at 1% FPR** (AUC 0.705) on its own evaluation split (p. 9, Table 4). That split's injections are StruQ-style naive, ignore, completion and combined attacks embedded in the *data* field of dolly and SPP samples, plus OpenPromptInjection attacks (p. 6, Table 2; p. 5, §3.1.2).
  - It independently shows that ProtectAI v2 has low recall at 1% FPR on application- or data-embedded injections.
  - It does **not** use TaskTracker or BIPIA, gives no per-source breakdown, and has no direct-attack contrast for ProtectAI v2.
  - Its thresholds are fit on the evaluation data, and its FPR pool includes LMSYS conversational benign data.
  - Its magnitude (about 2%) is far below ours (27–30%). INFERENCE: this is likely driven by the different benign pool and attack mix; the paper gives no breakdown to confirm.
  - The paper confirms "to a best effort" that ProtectAI's training sets do not overlap its evaluation split (p. 6).
  - **OVERLAP = partial** (p. 9, Table 4; p. 6, Table 2 and §3.1.3).
- **C7** (with 200 benign target labels, matched retraining does not beat threshold-only or generic retraining).
  - There is no label-budget or target-adaptation experiment.
  - The closest design recalibrates released detectors' thresholds on the full evaluation split and compares them with detectors retrained on the PromptShield training sources (p. 7, §3.2.2; p. 9, Table 4). The retrained detectors win by a wide margin, but these are different models and data, not a matched-budget comparison.
  - The composition ablation (with vs without conversational training data) is a training-data-composition study, not target adaptation (pp. 9–11, §5.5).
  - **OVERLAP = none** (p. 7, p. 10). This is an adjacent design only.
- **C8** (a 1% threshold from B < 100 benign labels has expected FPR 1/(B+1)). No order-statistics analysis. The related observation is that thresholds tuned on one subset transfer with a higher realized FPR: a target of 1% gives 1.27% on all data and 1.61% on conversational data (p. 11, Tables 7 and 9). The paper also recommends validation-set calibration (p. 7). **OVERLAP = none** (pp. 7, 11).
- **C9** (the InjecGuard training file is clean against InjecGuard's public evaluation files; its validation set consists of evaluation items). The paper checks only that InjecGuard's training set does not overlap the *PromptShield* evaluation split ("to a best effort", method not described) (p. 6, §3.1.3). **OVERLAP = none** (p. 6).
- **C10** (deterministic largest-first group allocation produced a spurious inflation result; randomizing removed it). The paper's split is one deliberate, non-random allocation of sources (simpler data to train, sophisticated data to evaluation) (p. 6, §3.1.3). The sensitivity of results to the allocation is not studied. **OVERLAP = none** (p. 6).

## Author-stated limitations (quoted, page-cited)
- "First, the training setup does not account for concept drift or optimized adversarial attacks specifically crafted to bypass detection. As attacker strategies evolve, our detector's performance may degrade without ongoing adaptation." (p. 10, §7)
- "Second, our approach is limited to text-based inputs and does not extend to multi-modal settings." (p. 10, §7)
- "Note that in real-life deployment settings model maintainers will not necessarily have access to test data. In retrospect, we should have used the validation split for this calibration step." (p. 7, §3.2.2)
- Scope: "For simplicity, our taxonomy does not include multi-turn scenarios... Also, we do not include function calling." (p. 4, §2.4). "Because these methods are expensive, we consider them [optimization-based attacks such as GCG] out of scope for this work." (p. 3, §2.2)
- INFERENCE (our assessment, not stated by the authors):
  - There are no seeds or intervals.
  - The competitor overlap check is a "best effort" of unspecified method.
  - Attack strategies are shared across splits; only phrases and carriers differ.
  - The FPR pool mixes conversational and application benign data.

## Bibliographic entry (BibTeX)
```bibtex
@inproceedings{jacob2025promptshield,
  author    = {Jacob, Dennis and Alzahrani, Hend and Hu, Zhanhao and Alomair, Basel and Wagner, David},
  title     = {PromptShield: Deployable Detection for Prompt Injection Attacks},
  booktitle = {Proceedings of the Fifteenth ACM Conference on Data and Application Security and Privacy (CODASPY '25)},
  year      = {2025},
  pages     = {341--352},
  address   = {Pittsburgh, PA, USA},
  publisher = {ACM},
  doi       = {10.1145/3714393.3726501}
}
```
Extended version with appendices: arXiv 2501.15145 (p. 2, footnote 1). Not read; its contents are UNVERIFIED.
