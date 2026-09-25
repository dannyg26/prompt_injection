# Get my drift? Catching LLM Task Drift with Activation Deltas

- Authors / venue / year / version read: Sahar Abdelnabi, Aideen Fay (joint first), Giovanni Cherubin, Ahmed Salem, Mario Fritz, Andrew Paverd (Microsoft; CISPA). 2025 IEEE Conference on Secure and Trustworthy Machine Learning (SaTML), DOI 10.1109/SaTML64287.2025.00011. Publisher (IEEE Xplore) version, printed pages 43–67 (p. 1). Code/data link given: https://github.com/microsoft/TaskTracker (p. 1).
- File read: literature/pdfs/tasktracker_get_my_drift.pdf, pages read: 1–25 (all). Unreadable parts: the Read tool could not render the PDF (pdftoppm missing in the container), so the full text of all 25 pages was extracted with pypdf into a scratch file and read in full. Figures (t-SNE plots, histograms, ROC curves, Fig. 6/7/12 box plots) were not viewed as images; only their captions and text-extractable axis labels/legend values were read. Table text was read from extraction; column alignment of Table I was reconstructed from extracted text and may be imperfect.
- Page convention: `p. N` = PDF page N; printed page = N + 42.

## What it does (3–6 bullets, each page-cited)

- Defines "task drift": deviation from the user's primary task caused by instructions in external data, and treats any injected instruction (benign or malicious) as a violation (p. 1, §I; p. 3, §III-A).
- Detects drift from white-box LLM activations: last-token hidden states after the primary task alone vs. after primary task + data block; the difference ("activation delta") is the feature (p. 4, §IV-A; p. 5, §IV-B).
- Two probes: logistic regression on activation deltas, and a triplet-loss metric-learning embedding with online hard/semi-hard mining (p. 5, §IV-C; pp. 15–16, App. C–E).
- Evaluated on six instruction-tuned LLMs (Phi-3 3.8B, Mistral 7B, Llama-3 8B, Phi-3 14B, Mixtral 8x7B, Llama-3 70B) with ROC AUC on a balanced test set (p. 6, §V).
- Builds and releases the TaskTracker dataset (>500K instances, per abstract) and activations for six models (p. 1, abstract; p. 2, contributions; p. 15, App. preamble).
- Compares against two released/proprietary text classifiers, Prompt Guard and Prompt Shields (p. 9, §V-A-4; p. 10, Tables X–XI).

## Data

**Components.** Each instance = primary task + data block, optionally with an injected task = trigger + payload (p. 3, §III-A). "Our dataset construction approach, as described below, is based on sampling each of these components individually and combining them." (p. 3, §III-A)

**Training split (p. 4, §III-B; p. 5, Table I; p. 15, App. A).**
- Data blocks: SQuAD training split, 18,882 instances (p. 15, App. A).
- Primary tasks: one SQuAD question sampled per instance (random if several), plus 60 generic NLP task prompts from SEP (summarization, translation, keyword extraction, ...) (p. 4, §III-B; p. 15, App. A).
- Injected tasks: payloads from Alpaca (31,323 instructions without input), 325 handwritten trivia Q/A pairs and the generic NLP prompts from SEP; triggers are 542 GPT-4-generated sentences (p. 15, App. A). Training triggers are "less tailored for attacks" than the val/test triggers (p. 4, §III-C).
- Position: each primary/injected combination repeated at beginning, middle, end of the block (p. 15, App. A; p. 4, §III-B).
- Size: "In total, the training dataset contains 418,110 clean and their corresponding 418,110 poisoned samples. We made sure that the poisoned samples are unique (i.e., no duplicate hashes)." (p. 15, App. A)
- Clean/poisoned relation: paired. "each clean point x_cln in the training data with a primary task x_pri and a text block has a corresponding poisoned point x_pois with the same primary task x_pri and text block but with an additional injected task." (p. 15, App. C)
- No jailbreaks or malicious instructions in training: "We deliberately do not train on any jailbreaks or malicious instructions." (p. 4, §III-C)

**Validation split (p. 4, §III-C; p. 5, Table I; p. 15, App. B).**
- Clean: SQuAD dev (1,204) and HotPotQA dev (7,395), each with one question or question + generic NLP task; 17,198 clean instances (p. 15, App. B).
- Poisoned: SQuAD dev blocks; payloads from BIPA (150), AdvBench (520), forbidden questions (391), TrustLLM jailbreaks (1,400); new set of 195 GPT-4 triggers; 14,766 poisoned instances (p. 15, App. B).
- Used for model selection: metric-learning probe trained 5 epochs "while keeping track of the ROC AUC of the validation data to save the best model" (p. 16, App. D).

**Test split (p. 4, §III-C; p. 5, Table I; p. 15, App. B).**
- Payloads: 2,000 each randomly sampled from Code Alpaca, BeaverTails, Do-Not-Answer (6,000 total) inserted into SQuAD dev blocks; 250 JailbreakBench prompts (PAIR and adaptive attacks) inserted into HotPotQA blocks (p. 15, App. B; p. 4, §III-C).
- Clean: "For the clean examples, we used the 'train' subset from HotPotQA (note that HotPotQA was not used in training our probes)." (p. 15, App. B)
- Size: 31,134 clean and 31,134 poisoned (p. 15, App. B).
- Triggers: GPT-4 generated, "inspired by previous hand-written prompt injections [17] (e.g., 'ignore previous prompts')"; also a no-trigger variant using "Please answer the following: " (p. 4, §III-C).

**How the splits are separated.** Separation is by *source dataset* per component, not by paragraph ID, template cluster or near-duplicate grouping:
- Data blocks: SQuAD train (train) vs SQuAD dev / HotPotQA (val/test) (p. 4, §III-B–C).
- Payloads: Alpaca/SEP (train) vs disjoint attack datasets in val (BIPA, AdvBench, forbidden questions, TrustLLM) and test (BeaverTails, Do-Not-Answer, Code Alpaca, JailbreakBench) (p. 5, Table I). "We use non-overlapping splits of these datasets in the validation and test data." (p. 4, §III-C)
- Triggers: separate GPT-4-generated trigger sets for train (542) and val (195) (p. 15, App. A–B); the test trigger set's size is not stated (not found after reading §III, App. A–B).
- Primary tasks: val/test add two-task "mix" primaries not seen in training (p. 4, §III-C; p. 6, §V-A-1).
- Deduplication: only "no duplicate hashes" among training poisoned samples (p. 15, App. A). No near-duplicate or cross-split deduplication, and no grouping of triggers/payloads into templates, found after reading §III, §V, App. A–B.
- INFERENCE: SQuAD dev blocks appear in both validation and test poisoned examples (p. 15, App. B), so validation and test share data-block paragraphs; the paper does not state whether the same dev paragraphs are reused.
- INFERENCE: In the test set as described in App. B, clean examples come from HotPotQA *train* while most poisoned examples use SQuAD dev blocks (p. 15, App. B). This conflicts with §III-C/Table I, which list SQuAD (dev) as a test data-block source for both classes (p. 4, §III-C; p. 5, Table I). If App. B is literal, the test clean/poisoned classes differ in paragraph source, a possible confound. The paper does not address this.
- INFERENCE: SQuAD train/dev are disjoint by Wikipedia article in the original SQuAD release; this paper does not state it. UNVERIFIED from this paper.

**Additional evaluation sets (all small, constructed for analyses).**
- In-distribution translation sample: 1,204 per class, SQuAD dev, 25 languages, prompt wording unseen but translation task seen in training (p. 8, §V-A-1; p. 9, Table VII).
- In-context injection: 1,204 per class, injected task = a different SQuAD question on the same paragraph (p. 9, Table VIII).
- Naturally-phrased questions in clean data (GPT-4 paraphrases) (p. 9, Table IX).
- 500 translated injections (p. 10, §VI-A; p. 11, Table XII); 1,000 WildChat conversations with three meta-prompt levels (p. 11, Table XIII; p. 24, App. J); 500 spotlighting-evasion examples (p. 11, Table XIV); adaptive "lie"/"not new instructions" triggers (p. 12, Table XV; p. 24, App. K).
- Internal non-public prompt-injection dataset, ~13K instances: "We note that this dataset cannot be released via the TaskTracker toolkit." (p. 9, footnote 3)

**Licensing.** No license statement for the TaskTracker dataset, the released activations, or the component datasets (SQuAD, HotPotQA, Alpaca, SEP, BeaverTails, etc.) was found after reading pp. 1–25. Only the GitHub URL is given (p. 1). License: UNVERIFIED.

**Internal inconsistencies noted (author text).**
- BIPA is cited as [4] in §III-C (p. 4) but as [5] (Spotlighting) in Table I and App. B (p. 5; p. 15).
- Tables VII and VIII report identical numbers (0.98, 0.999, 0.999, 0.999, 0.991) for two different experiments (p. 9).
- Mistral "Clean (Baseline)" is 0.18±0.07 in Table VI (p. 7) but 0.18±0.18 in Tables XIV–XV (p. 11; p. 12).

## Detectors / models evaluated

- Trained here: linear (logistic regression) probe and triplet metric-learning probe on activation deltas of six open LLMs (p. 5, §IV-C; p. 6, §V). Hyperparameters: margin 0.3, mining batch 2,500, train batch 1,024, semi-hard then hard mining after 3,000 steps, 5 epochs, Adam lr 0.0005 (p. 16, App. D).
- Released/proprietary text classifiers compared: Meta Prompt Guard [15] and Microsoft Prompt Shields [16] (p. 9, §V-A-4). ProtectAI, PIGuard/InjecGuard and other detectors: not found after reading §V–§VI and appendices.
- Results on TaskTracker test (probe on Phi-3 14B): TaskTracker 0.996, Prompt Guard 0.974, Prompt Shields 0.988 ROC AUC (p. 10, Table X). Prompt Guard / Prompt Shields were run off-the-shelf; the threshold/score used for them and whether Prompt Guard's injection or jailbreak label was used are not stated (not found after reading §V-A-4, Table X).
- Non-public ~13K set: TaskTracker 0.934, TaskTracker (re-trained) 0.989, proprietary classifier 0.959, Prompt Guard 0.728 ROC AUC (p. 10, Table XI).
- Linear-probe ROC AUC per layer across models: up to 0.999 (p. 6, Tables II–III). Metric-learning probes: 0.93–0.99 by layer range (p. 7, Tables IV–V).
- Training-size ablation: "even with just 5% of the original training data, we achieve excellent performance (AUC 0.9986)" (p. 9, §V-A-3).

## Evaluation and statistics

- Metric: ROC AUC on a balanced test set (p. 6, §V). ROC curves plotted (pp. 16–18, Figs. 8–10). No TPR/recall at a fixed low FPR (e.g., 1%) is reported in any table (not found after reading §V, §VI, App. F–G).
- Distances reported as mean ± a spread (e.g., "0.20±0.11") (p. 7, Table VI; pp. 11–12, Tables XII–XV). What "±" denotes (SD, SE, CI) is not stated (not found after reading §V–§VI, App. J–K).
- Seeds / repeated runs: none reported (not found after reading §V, App. B–G). All AUCs are single point estimates.
- Confidence intervals: none for any AUC, for either probes or baseline classifiers (not found after reading pp. 1–25). No significance testing for the Table X/XI comparisons (0.996 vs 0.988 vs 0.974).
- No example-level vs group/cluster-level uncertainty discussion. INFERENCE: test instances share components (same payload across positions/primaries, same data block paired clean/poisoned, triggers resampled from a finite set; p. 15, App. A–B), so they are not independent examples, but the paper does not discuss this.
- Model selection on validation ROC AUC (p. 16, App. D); layer choice is reported per layer on test rather than pre-selected (p. 6, Tables II–III). How the layer for the Table X probe (Phi-3 14B) was chosen is not stated.

## Findings relevant to our claims

- **C1** (InjecGuard release; HackAPrompt template concentration). Paper does not analyze InjecGuard or HackAPrompt. Its own triggers are drawn from a finite GPT-4-generated set (542 train, 195 val) (p. 15, App. A–B), but no template-concentration analysis is done. OVERLAP = none (p. 15).
- **C2** (HackAPrompt held-out-template recall range). No HackAPrompt, no leave-one-template-out. The paper does evaluate on held-out payload *sources* and held-out trigger sets (p. 4, §III-C; p. 5, Table I), which is source-level OOD testing of its probe, not a template-level analysis of text detectors. OVERLAP = none (p. 4–5).
- **C3** (design effects > 1; example-level intervals too narrow). No intervals, no design effect or clustering discussion (pp. 6–10; p. 15). OVERLAP = none (pp. 6, 10).
- **C4** (row vs group split inflation on TaskTracker etc.). The paper never compares a row-level random split against a group split; its main split is source-disjoint by construction (p. 4, §III-C). Its in-distribution translation sample also scores high (p. 9, Table VII), but that is not a row-vs-group comparison. Relevant to our grouping design: clean and poisoned items are pairs sharing primary task and data block (p. 15, App. C), and each primary/injected combination is repeated at three positions (p. 15, App. A), so pairs/position-triplets must be kept in the same group. OVERLAP = none (pp. 4, 15).
- **C5** (withdrawn). OVERLAP = none.
- **C6** (ProtectAI v2 recall at 1% FPR on TaskTracker/BIPIA). ProtectAI not evaluated. Related but different: Prompt Guard ROC AUC 0.974 and Prompt Shields 0.988 on the TaskTracker test set (p. 10, Table X). Different detectors, a different metric (AUC, not recall at 1% FPR), no interval. INFERENCE: high AUC for Prompt Guard on this test set does not bear directly on recall at 1% FPR; the paper's test set also includes jailbreak/malicious payloads (BeaverTails, Do-Not-Answer, JailbreakBench) that text classifiers may be trained on (p. 15, App. B). OVERLAP = none (p. 10).
- **C7** (200 benign target labels; matched retraining vs threshold-only). Not tested. Related: training-size ablation down to 5% (~40K) (p. 9, §V-A-3) and re-training on the non-public set (0.934 → 0.989) (p. 10, Table XI), neither with a small label budget or a threshold-only baseline. OVERLAP = none (pp. 9–10).
- **C8** (threshold from B < 100 benign labels). No fixed-FPR threshold setting reported. OVERLAP = none (pp. 6, 10).
- **C9** (InjecGuard train vs eval files). Not addressed. OVERLAP = none.
- **C10** (deterministic group allocation producing spurious inflation). Not addressed; no group allocation procedure (p. 4, §III-C; p. 15, App. A–B). OVERLAP = none.

## Author-stated limitations (quoted, page-cited)

- On what activations capture: "While our method shows surprisingly good performance and helps solve a major security and safety problem, it is still unclear what these activations really capture." (p. 12, §VI-B)
- On adaptive attacks: "While future attacks may be devised to evade activation deltas, we suspect that this may not be as straightforward" (p. 12, §VI-B). "It is thus still an open question if truly having deceptive answers (if possible) would indeed lead to smaller deltas (and successfully avoid detection)." (p. 12, §VI-B)
- On long injections: "an adaptive attacker may use a completely different strategy of using very long spans of instructions to 'squash' the contrast and context-shift signals" (p. 12, §VI-B). Jailbreaks had lower distances for some models (p. 6, §V-A-1).
- On model transfer: "We did not evaluate how probes can transfer between different fine-tuned versions of models." (p. 13, §VI-B)
- On no-trigger injections: "It is, however, unclear whether the distance drop is due to lack of generalization or due to models not following/detecting weakly phrased instructions" (p. 8, §V-A-1).
- On the prompt template: activation collection without the template was tested only on Mistral 7B; "It also remains to be studied which activation collection strategy results in better performance across models and better adversarial robustness." (p. 18, App. G)
- On attack-success verification: "generating outputs was only done once; therefore, the 'not detected' examples may have been successful in other attempts" (p. 20, Fig. 12 caption).
- Threat-model assumption: input is "a primary task, followed by data blocks" (p. 3, §III-A).
- Non-public test set cannot be released (p. 9, footnote 3).
- Not stated as limitations by the authors (our observations, INFERENCE): absence of CIs/seeds; source-level rather than template-level grouping; possible clean/poisoned source mismatch in the test set (p. 15, App. B vs p. 5, Table I).

## Bibliographic entry (BibTeX)

```bibtex
@inproceedings{abdelnabi2025getmydrift,
  author    = {Abdelnabi, Sahar and Fay, Aideen and Cherubin, Giovanni and Salem, Ahmed and Fritz, Mario and Paverd, Andrew},
  title     = {Get my drift? Catching {LLM} Task Drift with Activation Deltas},
  booktitle = {2025 IEEE Conference on Secure and Trustworthy Machine Learning (SaTML)},
  pages     = {43--67},
  year      = {2025},
  publisher = {IEEE},
  doi       = {10.1109/SaTML64287.2025.00011}
}
```
