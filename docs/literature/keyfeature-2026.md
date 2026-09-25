# Prompt Injection Detection via Key Feature Integration in Large Language Models
- Authors / venue / year / version read: Seyeon Won, Wooguil Pak (Yeungnam University); 2026 International Conference on Artificial Intelligence in Information and Communication (ICAIIC), 24–27 Feb. 2026; IEEE publisher version, pp. 679–682, DOI 10.1109/ICAIIC68212.2026.11454256 (p. 1 footer; PDF metadata).
- Note on key: the requested file name is `keyfeature-2026.md`; the agent convention `firstauthor-year-shortword` would give `won-2026-keyfeature`. The requested name was kept.
- File read: literature/pdfs/keyfeature_icaiic26.pdf, pages read: 1–4 (all; = printed pp. 679–682). Page references use PDF page numbers, with printed page in brackets.
- Unreadable parts: the Read tool's page renderer was unavailable (pdftoppm missing), so the text layer was extracted with pypdf. All body text, Tables I–II and references were extracted. **Fig. 1 (structure of TLD) is an image and was not read**; only its caption and the text describing it were.

## What it does
- Proposes Total-Layer Detection (TLD): concatenate hidden states from all layers of an LLM into one feature vector, select the top-K features by "feature importance analysis", and classify with a linear layer (p. 1 [679], Abstract; p. 2 [680], §III.A–D).
- The importance measure used to rank features is not named. Not found after reading §III–§IV. How K was chosen is also not found.
- Compares TLD against single-layer baselines: "Last Layer" and "Best Layer" (the latter described as corresponding to LEC), all with `torch.nn.Linear` classifiers (p. 2 [680], §IV.B; p. 3 [681], §IV.C).
- Headline claim: TLD beat single-layer approaches "in three out of four scenarios" (p. 3 [681], §IV.D).

## Data
- Two datasets: "SPML [6], LMSYS+SALAD [7, 8]" (p. 2 [680], §IV.A).
  - SPML: system prompt/user prompt pairs; "attempts by users to intentionally violate or circumvent safety rules specified in system prompts" are "attacks" (p. 2 [680], §IV.A.1).
  - LMSYS+SALAD: benign = LMSYS-Chat-1M logs filtered to "'harmless' by the OpenAI Moderation API criteria, in English, and single-turn"; attack = "only the base set subset" of SALAD-Bench (harmful questions); "combining both datasets at an equal ratio" (p. 2 [680], §IV.A.2).
- INFERENCE: LMSYS+SALAD uses harmful-content questions (SALAD-Bench) as the "attack" class, so it is a harmful-request / jailbreak-style task, not prompt injection in the instruction-override sense. In that dataset the two classes also come from different sources, so source identity may be learnable (not addressed by the authors).
- No deepset, HackAPrompt, safe-guard, TaskTracker or BIPIA data are used. Not found after reading §I–§V and Tables I–II.
- Split, exact quote: "Each dataset was equally split into training (3,300 samples), validation (1,700 samples), and test (1,700 samples) sets." (p. 2 [680], §IV.A). That is 6,700 samples per dataset (our arithmetic). How the samples were drawn, whether the split was random by row, and whether it was stratified are not stated ("equally split" is ambiguous given the unequal sizes).
- Deduplication, near-duplicate handling, and grouping by system prompt, template or source: Not found after reading §I–§V.
- INFERENCE: with no grouping or deduplication described, a row-level split could put near-copies of one template (e.g. SPML pairs sharing a system prompt, or templated SALAD-Bench items) in both training and test. The paper gives no information that rules this out. The SPML set-up (3,300/1,700/1,700) is identical to Lee & Pak 2026 (docs/literature/hierarchical-2026.md) from the same lab, but neither paper states that the splits are shared.

## Detectors / models evaluated
- Trained here: TLD, Best Layer and Last Layer linear classifiers on hidden states of Qwen2.5-0.5B-Instruct (24 layers, 896-d) and Qwen2.5-14B-Instruct (48 layers, 5,120-d) (p. 2 [680], §IV.B; p. 3 [681], §IV.C). (The paper cites Qwen as "[2]" in §IV.B, but [2] in its reference list is Perez & Ribeiro; Qwen is [1] (p. 4 [682]).)
- Released detectors (PromptGuard, ProtectAI, PIGuard, etc.): none evaluated. Not found after reading §IV.
- Training hyperparameters (optimizer, epochs, learning rate): Not found after reading §IV.
- Whether "Best Layer", the feature ranking and K were selected on validation or test data: Not found after reading §III–§IV. INFERENCE: if Best Layer and K were chosen by test performance, the reported gains would be optimistic. The paper does not let us check this.

## Evaluation and statistics
- Metrics: Accuracy (%) and F1 (%) only (p. 3 [681], Tables I–II). No AUROC, recall at fixed FPR or operating-point reporting.
- Seeds: Not found after reading §IV. Confidence intervals, standard deviations or significance tests: Not found after reading §IV–§V. Results appear to be a single run per configuration on one 1,700-sample test split.
- Headline numbers (Accuracy / F1):
  - LMSYS+SALAD, Table I (p. 3 [681]): Qwen2.5-0.5B: Feature Select (K=16,000) 93.12/93.12; Best Layer (layer 7) 95.00/95.00; Last Layer 87.00/86.99. Qwen2.5-14B: Feature Select (K=700) 97.59/97.59; Best Layer (layer 9) 97.12/97.12; Last Layer 94.47/94.47.
  - SPML, Table II (p. 3 [681]): Qwen2.5-0.5B: Feature Select (K=17,000) 96.65/96.65; Best Layer (layer 13) 95.82/95.82; Last Layer 89.82/89.82. Qwen2.5-14B: Feature Select (K=15,000) 99.18/99.18; Best Layer (layer 27) 99.06/99.06; Last Layer 97.53/97.53.
- Feature use: "Qwen2.5-0.5B utilized an average of approximately 76.7% of the total features, whereas Qwen2.5-14B used an average of only 3.19% of the total dimensions." (p. 3 [681], §IV.D).
- INFERENCE: the TLD vs Best Layer gaps on the 14B model (+0.47 and +0.12 points, i.e. about 8 and 2 of 1,700 test items) are within single-split binomial noise. The paper reports no interval or test, so the "outperformed" statements are not supported by any stated inferential evidence.

## Findings relevant to our claims
- C1 (template concentration of InjecGuard/HackAPrompt): not addressed. OVERLAP = none.
- C2 (held-out-template recall on HackAPrompt): no held-out-template or group split (p. 2 [680], §IV.A). OVERLAP = none.
- C3 (design effects; example-level intervals too narrow): reports no intervals at all (p. 3 [681], Tables I–II). It is an example of the practice C3 critiques, not prior evidence for it. OVERLAP = none.
- C4 (row vs group split inflation, null): no comparison of split types. OVERLAP = none.
- C5 (withdrawn): n/a.
- C6 (released ProtectAI v2 recall on indirect sources): no released detectors evaluated. OVERLAP = none.
- C7 (matched retraining vs threshold-only under small benign budgets): not addressed. OVERLAP = none.
- C8 (threshold from few benign labels): not addressed. OVERLAP = none.
- C9 (InjecGuard train/eval cleanliness): not addressed. OVERLAP = none.
- C10 (deterministic group allocation artefact): not addressed. OVERLAP = none.

## Author-stated limitations (quoted, page-cited)
- "However, the proposed method still has the limitation of requiring a relatively large number of features compared to single-layer approaches." (p. 3 [681], §V)
- No stated limitation about the split, leakage, dataset construction, seeds or intervals. Not found after reading §IV–§V. (Our observation, not an author statement.)

## Bibliographic entry (BibTeX)
```bibtex
@inproceedings{won2026keyfeature,
  author    = {Won, Seyeon and Pak, Wooguil},
  title     = {Prompt Injection Detection via Key Feature Integration in Large Language Models},
  booktitle = {2026 International Conference on Artificial Intelligence in Information and Communication (ICAIIC)},
  year      = {2026},
  pages     = {679--682},
  publisher = {IEEE},
  doi       = {10.1109/ICAIIC68212.2026.11454256}
}
```
