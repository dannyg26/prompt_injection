# Detection of Prompt Injection Attacks Using a Hierarchical Approach
- Authors / venue / year / version read: Sujin Lee, Wooguil Pak (Yeungnam University); 2026 International Conference on Artificial Intelligence in Information and Communication (ICAIIC), 24–27 Feb. 2026; IEEE publisher version, pp. 541–543, DOI 10.1109/ICAIIC68212.2026.11454295 (p. 1 footer; PDF metadata).
- File read: literature/pdfs/hierarchical_icaiic26.pdf, pages read: 1–3 (all; = printed pp. 541–543). Page references below use PDF page numbers, with printed page in brackets.
- Unreadable parts: the Read tool's page renderer was unavailable (pdftoppm missing), so the text layer was extracted with pypdf. All body text, Table I and references were extracted. **Fig. 1 (LEC per-layer classification results) and Fig. 2 (MHD structure) are images and were not read**; only their captions and the text describing them were. Some table cells show extraction artifacts (e.g. MHD Qwen2.5-0.5B accuracy extracted as "99"; see Evaluation).

## What it does
- Proposes Multi-layer Hierarchical Detection (MHD): classifiers on hidden states of each Transformer layer of the service LLM, with early exit; inputs classified as Safe/Harmful at a lower layer stop, "Uncertain" ones go to the next layer (p. 1 [541], Abstract; p. 2 [542], §III.B–C).
- Ternary training data per layer are built by training a binary classifier per layer and relabelling its misclassified samples as "Uncertain"; a final binary classifier at the "MHD last layer" decides remaining inputs (p. 2 [542], §III.C).
- Motivation: in LEC, "Layer 1 achieves 96.38% F1-score", so passing all data to a fixed deeper layer is unnecessary (p. 2 [542], §III.A, referring to Fig. 1).
- Compares against ProtectAI deberta-v3-base-prompt-injection-v2, Meta Prompt Guard (2), Attention Tracker and LEC on the SPML dataset, with Qwen2.5-0.5B-Instruct and Qwen2.5-14B-Instruct as feature extractors (p. 2 [542], §IV, §IV.A.1).
- Headline claim: average number of classification layers reduced by 75.3%–88.5% versus LEC with F1 within about ±0.5% (p. 1 [541], Abstract; p. 3 [543], §IV.B).

## Data
- Single dataset: SPML [11] (Sharma et al., arXiv:2402.11755), "system prompt-user prompt pairs"; label 1 (harmful) "if a user prompt attempts to elicit an output that violates the system prompt's instructions, regardless of the user's actual malicious intent" (p. 3 [543], §IV.A.2).
- No deepset, HackAPrompt, safe-guard, TaskTracker, BIPIA or other public prompt-injection sets are used. Not found after reading §I–§V and Table I.
- Split, exact quote: "The dataset was split into 3,300 training, 1,700 validation, and 1,700 test samples, with the class labels uniformly distributed." (p. 3 [543], §IV.A.2). Total used = 6,700 samples (our arithmetic). Whether this is a subsample of SPML, how the 6,700 were drawn, and whether the split was random by row is not stated.
- "Class labels uniformly distributed" reads as class balance (stratified or balanced sampling); the mechanism is not stated.
- Deduplication, near-duplicate handling, and grouping by system prompt or template: Not found after reading §I–§V.
- INFERENCE: SPML pairs share system prompts across many rows (UNVERIFIED about SPML's construction; not stated in this paper). Because the paper describes no grouping or deduplication, a row-level split could put pairs with the same system prompt, or near-copies of one attack template, in both training and test. The paper gives no information that rules this out.

## Detectors / models evaluated
- Trained here: MHD (per-layer binary and ternary classifiers on hidden states; hyperparameters "learning rate of 0.05 and an early stopping patience of 20 epochs") and LEC re-implemented as a baseline (p. 3 [543], §IV.A.2; p. 2 [542], §IV). The classifier family for MHD is not named; LEC is described as "a penalized logistic regression classifier" (p. 2 [542], §II.B).
- Only the service model's hidden states are used (no detection-fine-tuned extractor) (p. 2 [542], §IV.A.1).
- Released detectors: ProtectAI deberta-v3-base-prompt-injection-v2 [6] and Meta Llama-Prompt-Guard-2-86M [7] ("Prompt Guard2" in Table I) (p. 3 [543], Table I; refs p. 3). Training-free: Attention Tracker [8].
- Decision threshold used for released detectors: Not found after reading §IV.
- How the "MHD last layer" and LEC's layer were chosen (validation vs test): Not found after reading §III–§IV. INFERENCE: the 1,700-sample validation split presumably served for early stopping and layer choice, but this is not stated.

## Evaluation and statistics
- Metrics: Accuracy (%), F1 (%), maximum and average classification layer (p. 3 [543], Table I). No AUROC, no recall at fixed FPR, no operating-point reporting.
- Seeds: Not found after reading §IV. Confidence intervals, standard deviations or significance tests: Not found after reading §IV–§V. Results appear to be a single run on one 1,700-sample test split.
- Headline numbers, Table I (p. 3 [543]):
  - Qwen2.5-0.5B: MHD acc 99 (extracted as "99"; exact decimals unreadable) / F1 98.99, max layer 5, avg layer 3.70; LEC 98.53 / 98.52, layer 15; Attention Tracker 80.76 / 76.53.
  - Qwen2.5-14B: MHD 98.59 / 98.57, max layer 3, avg 2.53; LEC 98.88 / 98.88, layer 22; Attention Tracker 86.29 / 84.22 (layer 48).
  - ProtectAI deberta-v3-base-prompt-injection-v2: 94.47 / 94.7. Prompt Guard2: 77.12 / 70.33.
- Quote: "Overall, the F1-score difference between the two methods remained within a narrow range of ±0.5%." (p. 3 [543], §IV.B). The ±0.5% is an observed difference, not an interval.
- The 75.3% and 88.5% reductions match 1 − 3.70/15 and 1 − 2.53/22 (our arithmetic from Table I).

## Findings relevant to our claims
- C1 (template concentration of InjecGuard/HackAPrompt): does not audit dataset composition or template concentration. OVERLAP = none.
- C2 (held-out-template recall on HackAPrompt): no held-out-template or group split; SPML only (p. 3 [543], §IV.A.2). OVERLAP = none.
- C3 (design effects; example-level intervals too narrow): reports no intervals at all (p. 3 [543], Table I). It is an example of the practice C3 critiques, not prior evidence for it. OVERLAP = none.
- C4 (row vs group split inflation, null): no comparison of split types. OVERLAP = none.
- C5 (withdrawn): n/a.
- C6 (ProtectAI v2 low recall on indirect injection): reports ProtectAI v2 at 94.47% accuracy / 94.7 F1 on SPML (direct system/user prompt pairs), not on indirect sources and not at 1% FPR (p. 3 [543], Table I). Different dataset and metric. OVERLAP = none.
- C7 (matched retraining vs threshold-only under small benign budgets): not addressed. OVERLAP = none.
- C8 (threshold from few benign labels): not addressed. OVERLAP = none.
- C9 (InjecGuard train/eval cleanliness): not addressed. OVERLAP = none.
- C10 (deterministic group allocation artefact): not addressed. OVERLAP = none.

## Author-stated limitations (quoted, page-cited)
- "First, MHD requires a dedicated classifier for each layer, resulting in a larger total number of trainable parameters compared to single-classifier methods like LEC." (p. 3 [543], §V)
- "Second, inputs that are not classified at early layers must undergo sequential classification up to the MHD last layer. In such worst-case scenarios, computational overhead may slightly increase compared to a single-pass method." (p. 3 [543], §V)
- No stated limitation about the single dataset, the split, leakage, seeds or intervals. Not found after reading §IV–§V. (Our observation, not an author statement.)
- Of Attention Tracker, the authors say "its performance varies considerably across different domains, indicating high domain-dependence" (p. 1 [541], §II.B). MHD itself is evaluated on one domain/dataset only (p. 2 [542], §IV).

## Bibliographic entry (BibTeX)
```bibtex
@inproceedings{lee2026hierarchical,
  author    = {Lee, Sujin and Pak, Wooguil},
  title     = {Detection of Prompt Injection Attacks Using a Hierarchical Approach},
  booktitle = {2026 International Conference on Artificial Intelligence in Information and Communication (ICAIIC)},
  year      = {2026},
  pages     = {541--543},
  publisher = {IEEE},
  doi       = {10.1109/ICAIIC68212.2026.11454295}
}
```
