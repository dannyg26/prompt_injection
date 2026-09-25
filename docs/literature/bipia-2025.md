# Benchmarking and Defending Against Indirect Prompt Injection Attacks on Large Language Models

- Authors / venue / year / version read: Jingwei Yi, Yueqi Xie, Bin Zhu, Emre Kiciman, Guangzhong Sun, Xing Xie, Fangzhao Wu. KDD '25 (31st ACM SIGKDD, Toronto, Aug 3–7, 2025), publisher version, DOI 10.1145/3690624.3709179, proceedings pp. 1809–1820 (p. 1).
- File read: /home/user/prompt_injection/literature/pdfs/bipia_kdd25.pdf, pages read: 1–12 (all), unreadable parts: none in the text. **Method caveat:** the Read tool could not render this PDF (poppler/pdftoppm is not installed), so all 12 pages were read as text extracted with pypdf. Table layouts were garbled in extraction but still recoverable. The Table 1 counts below were cross-checked arithmetically (contexts × attacks × 3 positions = prompts). Figures 2–5 and 10–13 are plots, and only their captions and axis labels were readable, so no numeric values are taken from them.
- Note on page numbers: "p. N" means PDF page N of 12. Proceedings page = 1808 + N.

## What it does
- Introduces BIPIA, which the authors call "the first benchmark for indirect prompt injection attacks". It covers 5 application tasks (email QA, web QA, table QA, summarization, code QA) (p. 1, Abstract; p. 3, §4).
- Evaluates attack success rate (ASR) for 25 LLMs. The authors report that all 25 are vulnerable and that ASR on text tasks correlates positively with Chatbot Arena Elo (p. 2, §1; p. 4, Table 2, Fig. 2).
- Proposes black-box LLM defenses (an explicit reminder, multi-turn dialogue, and in-context learning) (p. 6, §6.1).
- Proposes a white-box defense: `<data>`/`</data>` special tokens plus adversarial supervised fine-tuning of Vicuna-7B/13B on BIPIA training prompts (p. 7, §6.2).
- Measures utility with ROUGE-1 on a clean version of BIPIA ("BIPIA-Clean") and with MT-Bench (p. 7, §7.1). Includes ablations of the two defense components (pp. 8–9, §7.3, Figs. 10–11).

## Data
- **Contexts (external content)** (p. 3, §4):
  - Email QA: "100 real-world emails with questions and answers from the OpenAI Evals repository".
  - Web QA: 1,000 NewsQA examples.
  - Table QA: 1,000 WikiTableQuestions examples.
  - Summarization: 1,000 XSum examples.
  - Code QA: "100 Python code samples with bugs and solutions from Stack Overflow" (self-collected).
- **Context split:** "For web QA, table QA, and summarization, we use a 900/100 train/test split, while for email QA and code QA, we employ a 50/50 split" (p. 3, §4). That gives 2,800 train and 400 test contexts overall (p. 3, Table 1). The paper does not say how the context split was drawn (random or otherwise). It also does not say whether the contexts were checked for duplicates or near-duplicates. Not found after reading §1–§8 and App. A–C.
- **Attacks:** "We design 30 types of text attacks and 20 types of code attacks, each containing five specific malicious instructions" (p. 3, §4). That is 150 text and 100 code malicious instructions, which matches the "250 attacker goals" (p. 2, §1).
  - Text attack types fall into three categories: task-irrelevant, task-relevant and targeted.
  - Code attack types fall into two categories: passive and active (p. 3, §4; p. 12, Tables 5–6).
- **Attack split (by type, i.e. by attack family):** "We randomly split 15 types of text attacks and 10 types of code attacks for training, with the remainder used for testing" (p. 3, §4).
  - Tables 5 (test) and 6 (train) list different type names. Each category contributes 5 types per split. Examples: test task-relevant types are "Substitution Ciphers, Base Encoding, Reverse Text, Emoji Substitution, Rare Language Translation"; train task-relevant types are "Alphanumeric Substitution, Homophonic Substitution, Misspelling Intentionally, Anagramming, Space Removal & Grouping" (p. 12, Tables 5–6).
  - Per split: 15 × 5 = 75 text attack strings and 10 × 5 = 50 code attack strings, 125 in total (p. 3, Table 1).
  - Attack types are therefore disjoint across train and test at the named-type level.
  - INFERENCE: the types can still be semantically close across splits (e.g. "Substitution Ciphers" in test vs "Alphanumeric Substitution" in train). The paper reports no semantic near-duplicate check between train and test attack instructions. Not found after reading §1–§8 and App. A–C.
- **Combination into samples:** each prompt combines one context, one attack instruction and one of 3 insertion positions ("beginning, middle, and end of external content") (p. 3, §4). The combination is a full cross product. Table 1 is consistent with this:
  - Email QA: 50 × 75 × 3 = 11,250 train and 11,250 test prompts.
  - Web QA, Table QA, Summarization: 900 × 75 × 3 = 202,500 train and 100 × 75 × 3 = 22,500 test prompts each.
  - Code QA: 50 × 50 × 3 = 7,500 per split.
  - Overall: 626,250 train and 86,250 test prompts (p. 3, Table 1, §4).
- INFERENCE (from the counts in Table 1):
  - Each test context appears in 225 test prompts (75 attacks × 3 positions); code contexts appear in 150.
  - Each test text-attack string appears in 300 prompts per text task (100 contexts × 3 positions), or 150 for email.
  - The 86,250 test prompts therefore come from only 400 contexts and 125 attack strings.
  - The paper counts prompts, not these groups, as the dataset size.
- The paper describes no deduplication, near-duplicate handling or template grouping beyond the type-level attack split. Not found after reading §1–§8 and App. A–C.
- **BIPIA-Clean** is "constructed following the same steps as BIPIA, but the external content does not contain any malicious instructions". It is used only for ROUGE-1 utility, not as a benign class for detection (p. 7, §7.1).
- The ethics statement says harmful attacks were removed by manual review: the benchmark "excludes attacks that could harm personal property and health" (p. 9, Ethical Consideration).

## Detectors / models evaluated
- **No detectors or classifiers are evaluated.** The paper does not evaluate PromptGuard, ProtectAI, PIGuard or any other injection classifier, and it reports no detection metrics such as AUROC, recall or FPR. Not found after reading §1–§8 and App. A–C. Everything evaluated is either an LLM defended by prompting or an LLM that was fine-tuned.
- **LLMs evaluated for vulnerability:** 25 released LLMs, including GPT-4, GPT-3.5-turbo, the Llama-2-Chat family, Vicuna 7B/13B/33B and Mistral-7B (p. 4, Table 2).
- **Black-box defenses:** tested on GPT-4, GPT-3.5-Turbo, Vicuna-7B and Vicuna-13B. In-context examples are taken "from the training set of BIPIA" (p. 7, §7.1).
- **White-box defense (trained here):** Vicuna-7B/13B, fine-tuned on training-split prompts. Settings: AdamW, 1 epoch, learning rate 2e-5, batch size 128, maximum length 2,048 (p. 7, §7.1).
  - Three sources were used for benign target responses: BIPIA labels, the original LLM, and GPT-4 (p. 7, §6.2).
  - Test attacks come from types that were held out of training, so this is the paper's cross-attack-type generalization setting.
  - INFERENCE: the paper does not present this as a generalization test. It reports no comparison with training and testing on the same attack types.

## Evaluation and statistics
- **Metrics** (pp. 3, 7, §5, §7.1):
  - ASR, computed by "rule-based evaluation, LLM-as-judge evaluation, and language detection based on langdetect".
  - ROUGE-1 recall on BIPIA-Clean.
  - MT-Bench score.
  - Overall ASR "is determined by weighting each task's ASR according to its example count" (p. 4, Table 2 caption).
- **Decoding:** temperature 0 and at most 2,000 new tokens for the benchmark evaluation and black-box defenses (pp. 3, 7). At most 512 tokens at test time for the white-box defense (p. 7, §7.1).
- **Seeds:** none reported. The paper reports no repeated runs and no seed for the fine-tuning. Not found after reading §1–§8 and App. A–C.
- **Uncertainty:** the paper reports **no confidence intervals, standard errors or significance tests for ASR, ROUGE or MT-Bench** in Tables 2–4. Every value is a point estimate (4 decimal places). Not found after reading §1–§8 and App. A–C.
  - The only inferential statistics are the Pearson correlations between Elo and ASR: "0.6423 (p < 0.001), 0.6635 (p < 0.001) and -0.0254 for all tasks, text tasks and code tasks" (p. 4, Fig. 2 caption). The paper does not state the test behind these p-values. INFERENCE: they are presumably computed over the n = 25 models.
  - INFERENCE: because prompts are crossed contexts × attacks × positions, any interval computed over individual prompts would be too narrow. The paper does not raise clustering or design effects.
- INFERENCE (observation only): Vicuna-7B's baseline overall ASR is 0.1049 in Table 2 (p. 4) but 0.1237 as "Original" in Table 3 (p. 8). Vicuna-13B is 0.1294 in Table 2 vs 0.1531 in Table 3. The paper does not explain the difference.
- Headline defense results (p. 8, Tables 3–4; point estimates, no intervals):
  - Black-box, GPT-4 overall ASR: 0.3103 → 0.2408 (ICL) and 0.2056 (multi-turn).
  - White-box, Vicuna-7B overall ASR: 0.1237 → 0.0053 with GPT-4 responses.
  - White-box, Vicuna-13B overall ASR: 0.1531 → 0.0047 with original-LLM responses.

## Findings relevant to our claims
- **C1 (template concentration in the InjecGuard release):** not studied. The paper does not measure InjecGuard, HackAPrompt or how concentrated attack sources are.
  - INFERENCE: BIPIA is built as a design with few groups (125 attack strings per split × 400 test contexts × 3 positions; p. 3, Table 1). This fits the general idea that injection benchmarks are template-structured, but the paper does not measure or state this.
  - OVERLAP = none.
- **C2 (recall at 1% FPR varies across held-out templates vs row splits):** no detector recall, no FPR operating point, and no comparison of held-out-template and row splits.
  - Design precedent only: the attack split is disjoint by type ("We randomly split 15 types of text attacks and 10 types of code attacks for training, with the remainder used for testing", p. 3, §4). So held-out attack-type evaluation already exists in this benchmark's design.
  - The paper does not report variation across held-out types or a row-split contrast.
  - OVERLAP = none (design precedent at p. 3 only).
- **C3 (design effects > 1; example-level intervals too narrow):** no intervals of any kind for ASR, and the paper does not discuss clustering by context or attack.
  - INFERENCE: BIPIA's crossed structure (p. 3, Table 1) is a direct case where clustering would apply.
  - OVERLAP = none.
- **C4 (on BIPIA, row splits do not measurably inflate detector recall under randomized group splits):** the paper trains no detector and makes no row-split vs group-split comparison. Its official splits are already disjoint by context and by attack type (p. 3, §4).
  - INFERENCE: this matters for C4. The authors' own split is disjoint by group, so a row split of BIPIA is something our study constructs, not the paper's protocol.
  - OVERLAP = none.
- **C5 (withdrawn):** OVERLAP = none.
- **C6 (ProtectAI v2 recall on BIPIA):** the paper does not evaluate released detectors (§1–§8, App. A–C). OVERLAP = none.
- **C7 (matched retraining vs threshold-only with 200 benign labels):** not studied. OVERLAP = none.
- **C8 (1% threshold from B < 100 benign labels):** not studied. OVERLAP = none.
- **C9 (InjecGuard train/eval cleanliness):** not studied. OVERLAP = none.
- **C10 (deterministic vs randomized group allocation):** the paper states that its attack-type split was random ("We randomly split", p. 3, §4). It reports no comparison with deterministic allocation and does not state a split seed. OVERLAP = none.

## Author-stated limitations (quoted, page-cited)
- There is no dedicated limitations section. Not found after reading §1–§8 and App. A–C.
- "we do caution developers against overreliance on these defense mechanisms without careful testing and red teaming in the context of specific, end-to-end applications." (p. 9, Ethical Consideration)
- "the black-box defense methods can effectively reduce ASR but cannot make LLMs robust to indirect prompt injection attacks" (p. 9, §8)
- On the white-box defense: "white-box fine-tuning does not affect the performance of LLMs on the fine-tuning task without attack, but may affect the performance on general tasks." (p. 9, §7.3)
- On benign-response construction: BIPIA labels "may limit their diversity", and for the other two sources "the correctness cannot be guaranteed" (p. 7, §6.2).
- On Table 3 comparisons: a larger model's higher ASR "could be attributed to the inherently higher base ASR of the more powerful LLM" (p. 8, §7.2).

## Bibliographic entry (BibTeX)
```bibtex
@inproceedings{yi2025bipia,
  author    = {Yi, Jingwei and Xie, Yueqi and Zhu, Bin and Kiciman, Emre and Sun, Guangzhong and Xie, Xing and Wu, Fangzhao},
  title     = {Benchmarking and Defending Against Indirect Prompt Injection Attacks on Large Language Models},
  booktitle = {Proceedings of the 31st ACM SIGKDD Conference on Knowledge Discovery and Data Mining V.1 (KDD '25)},
  year      = {2025},
  pages     = {1809--1820},
  publisher = {ACM},
  address   = {Toronto, ON, Canada},
  doi       = {10.1145/3690624.3709179}
}
```
