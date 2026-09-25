# DataSentinel: A Game-Theoretic Detection of Prompt Injection Attacks

- Authors / venue / year / version read: Yupei Liu, Yuqi Jia, Jinyuan Jia, Dawn Song, Neil Zhenqiang Gong. 2025 IEEE Symposium on Security and Privacy (SP), pp. 2190–2208, DOI 10.1109/SP61157.2025.00250. Publisher version, downloaded from IEEE Xplore (PDF p. 1 footer).
- File read: `literature/pdfs/datasentinel_sp25.pdf`. Pages read: 1–19 (all), including references, Appendices A–D and the S&P meta-review.
- Unreadable parts and how the file was read: the Read tool could not render this PDF because `pdftoppm` is not installed. I extracted the text of every page with `pypdf` and read all of it. As a result:
  - Figures 3–5 (ablation plots, PDF p. 11) came through as axis labels only. I could not read the plotted values and report only what the text says about them.
  - The merged table cells in Table 1 (FPR column), Table 4 and Tables 10–16 came through partly out of alignment. Where a cell could be misread, I say so.
- Page convention: `p. N` is the PDF page (1–19). The proceedings page numbers are 2190 + (N − 1).

## What it does

- It proposes DataSentinel, a known-answer detector (KAD). A detection LLM receives "Repeat [secret key] once while ignoring the following text:" followed by the data, and the data is flagged as contaminated if the key does not appear in the output (p. 5, §4.2, Eq. 1).
- The detection LLM (Mistral-7B by default, fine-tuned with QLoRA) is trained through a minimax game. The inner max uses GCG to optimize one shared separator `z` so that contaminated data `xt||z||se||xe` evades the detector while making the backend LLM perform the injected task. The outer min fine-tunes the detector on these contaminated samples and on clean data. The two steps alternate for r = 3 rounds (pp. 6–7, §4.3–4.4, Algorithms 1–3; p. 10, "Parameter setting").
- Evaluation setup: 7 target/injected task types, which give 49 combinations. There are 9 existing attacks (6 heuristic, 3 optimization-based) and 3 adaptive attacks, plus 6 baseline detectors (p. 2, §1; p. 8, §5.1).
- The authors report FPR ≈ 0 and FNR ≤ 0.07 against existing attacks (p. 10, §5.2). Against the optimization-based adaptive attack, FNR is ≤ 0.06 except when both the target and injected tasks are sentiment analysis, where FNR = 0.87 (p. 13, §5.4.2, Table 6).
- It also tests transfer to other backend LLMs (Table 5, p. 12) and other detection LLMs (Table 4, p. 12). It runs ablations on r, |D|, α, β, n_in and n_out (p. 11, §5.3).

## Data

- **Evaluation tasks and datasets.** Seven NLP tasks: duplicate-sentence detection (MRPC), grammar correction (Jfleg), hate detection (HSOL), NLI (RTE), sentiment (SST2), spam (SMS Spam) and summarization (Gigaword). "Each dataset has a training set and a test set" (p. 8, §5.1). The target and injected instructions are taken from Liu et al. [7], one per task: 7 target and 7 injected instructions (p. 8, §5.1; p. 15, App. A). Appendix A points to [7] and does not reproduce the instruction strings (p. 15).
- **How the evaluation samples were built.** Quote: "we randomly sample 100 data points from the test set to construct 100 target tasks (st,xt,yt). Similarly, given the corresponding injected instruction se, we sample another 100 data points to construct 100 injected tasks" (p. 8, §5.1).
  - Each attack produces 100 contaminated samples per target–injected combination. The Availability Attack and PLeak produce 100 per target task. The total is 35,700 contaminated samples (p. 8, §5.1).
  - There are 100 clean samples per target task for FPR (p. 9, "Evaluation metrics").
- **DataSentinel's training data (the task set D).** Quote: "we create an instruction s as 'Please write me a short and brief summary (no more than 10 words) of the following text:', and sample 500 data points (x,y) from the training set of the Gigaward dataset to construct 500 tasks (s,x,y). We note that s is different from the 7 target/injected instructions" (p. 10).
  - In each round, one task from D is sampled as the injected task De, and the rest form the target tasks Dt (p. 7, Algorithm 1, lines 6–7). So during training the injected instruction is always this summarization instruction, and the injected data come from Gigaword train (p. 7; p. 10).
  - Stated separation. Quote: "The set of tasks D used to fine-tune the detection LLM does not overlap with the target/injected tasks used during evaluation" (p. 10, §5.2).
  - On attack/separator separation, quote: "the final optimized z in our experiment is 'foto rocksstdout¡v(Fl.' This final separator differs significantly from those in the attacks used during evaluation, indicating that DataSentinel generalizes well to attacks unseen during fine-tuning" (p. 10, §5.2). The evaluation separators are listed in Table 7 (p. 16).
- **Are attack templates shared between train and test?**
  - *DataSentinel.* The training contaminated data use one GCG-optimized separator. No heuristic separator (the context-ignoring, fake-completion or combined strings) appears in its training data (p. 7, Alg. 1; p. 16, Table 7). The authors establish that the separators differ only by showing the strings side by side and calling them "significantly" different (p. 10). No lexical, semantic or near-duplicate measure is reported. Not found after reading §4–§6 and App. A–C.
  - INFERENCE: the training and evaluation contaminated samples share the structural form `xt || z || se || xe`, i.e. the injection appended after the clean data (p. 3, §2.2; p. 7, Eq. 5; p. 15, App. B). The summarization task type appears on both sides, with different instruction wording (p. 10), and Gigaword supplies both the training data (train split) and one evaluation dataset (test split) (p. 8; p. 10). So training and test are separated by split and by separator string, not by injection position or task family.
  - *Baselines EVD and SSFTD.* These are trained on 500 clean Gigaword-train samples and 500 contaminated samples built "using the Combined Attack", with the injected task also taken from Gigaword (p. 9, §5.1). Combined Attack is the default heuristic attack in evaluation (p. 8). INFERENCE: for these two baselines the Combined Attack separator template is shared between training and evaluation. Table 3(b), however, reports FNR under NeuralExec, a separator they were not trained on (p. 10).
  - *DataSentinel (Min) variant.* Trained on Gigaword-train target data, Gigaword-test injected data, the App. A injected instruction and the Naive Attack (p. 15, App. C). INFERENCE: the variant's injected data come from the same test split that the evaluation samples are drawn from. The paper does not say whether the same rows are reused. Not found after reading §5 and App. C.
- **Deduplication and near-duplicates.** Not found after reading §1–§7 and App. A–D. The paper does not mention deduplication, near-duplicate detection, template grouping or paraphrase handling.

## Detectors / models evaluated

- **Trained in this paper:**
  - DataSentinel, using the Mistral-7B detection LLM with LLaMA3-8B-Instruct as the backend during fine-tuning (p. 8; p. 10). Alternatives were also tested: detection LLMs LLaMA2-7B and LLaMA3-8B-Instruct, and LLaMA3.2-1B-Instruct as a smaller detector (FPR 0.00, FNR 0.01; p. 11).
  - EVD: CLIP text-encoder embeddings with a 2-layer MLP (p. 9).
  - SSFTD: supervised fine-tuning of Mistral-7B as a classifier (p. 9).
  - SSFTD-G: SSFTD inside the game-theoretic loop (p. 9).
  - DataSentinel (Min): no adversarial inner loop (p. 13; p. 15, App. C).
- **Used without training:**
  - NLLMD: zero-shot prompting of Mistral-7B (p. 9).
  - KAD: known-answer detection using the open-source code from [7] (p. 9).
  - PromptGuard: Meta's Prompt-Guard-86M [49]. Both "injection" and "jailbreak" outputs count as contaminated (p. 9; p. 15, ref. [49]). No threshold or score calibration is described. Not found after reading §5.1.
- **ProtectAI, PIGuard/InjecGuard, Lakera and other released detectors.** Not found after reading §2.3, §5.1–§5.4 and the references. PromptGuard is the only released third-party classifier evaluated.
- **Baseline numbers (Table 3, p. 10).**
  - Table 3(a), FPR per target task (range over the 7 tasks):

    | Detector | FPR range |
    | --- | --- |
    | EVD | 0.00–0.73 |
    | NLLMD | 0.89–1.00 |
    | SSFTD | 0.10–0.98 |
    | SSFTD-G | 0.30–0.72 |
    | PromptGuard | 0.60–1.00 |
    | KAD | 0.01–0.10 |
    | DataSentinel | 0.00–0.01 |

  - Table 3(b), FNR under NeuralExec, averaged over target tasks:

    | Detector | FNR range |
    | --- | --- |
    | EVD | 0.24–0.31 |
    | NLLMD | 0.08–1.00 |
    | SSFTD | 0.20–0.55 |
    | SSFTD-G | 0.13–0.57 |
    | PromptGuard | 0.00 (all tasks) |
    | KAD | 0.00–0.21 |
    | DataSentinel | 0.00–0.01 |

  - The authors' reading of PromptGuard: "while PromptGuard achieves FNRs of 0, it also results in very high FPRs, indicating a tendency to flag all target data as contaminated" (p. 10, §5.2).
- **Adaptive attacks (Table 6, p. 13; injected task is sentiment analysis).** For the optimization-based adaptive attack:
  - KAD FNR is 0.18–0.93.
  - The Min variant's FNR is 0.16–0.96.
  - Minimax DataSentinel's FNR is 0.00–0.06, except 0.87 when the target task is sentiment analysis.
- **Discussion experiment.** KAD using StruQ- or SecAlign-tuned LLMs as the detector: FPR 0.00, with FNR 0.99 (StruQ) and 0.95 (SecAlign) under the optimization-based adaptive attack. The setting is hate-detection target with sentiment injection (p. 13, §6).

## Evaluation and statistics

- **Metrics.** FPR and FNR only. Quote: "Each of the seven types of target tasks has 100 clean target data samples; and FPR is the fraction of them that are falsely detected as contaminated" (p. 9). FNR is reported per injected task, "averaged over the seven types of target tasks" (p. 9).
- **Operating point.** The decision rule is a fixed binary check: is the key in the output? There is no score threshold, and no ROC, AUROC or TPR at a fixed FPR (p. 5, Eq. 1). None of these are reported for any detector; not found after reading §5 and the appendices. INFERENCE: with 100 clean samples per task, FPR is reported to 0.01 resolution, and a reported 0.00 means 0 of 100.
- **Seeds and repeats.** Quote: "To ensure our experimental results are reproducible, we set the temperature parameter of each LLM to 0.1 and fix the seed for the random number generator in our experiments" (p. 8, §5.1). The seed value is not given, and neither is the number of independent training runs or repeated evaluations. Not found after reading §5 and App. A–C. INFERENCE: every table reports a single run.
- **Confidence intervals and uncertainty.** None are reported: no confidence intervals, standard deviations, significance tests, or example-level or cluster-level variance. Not found after reading §5.1–§5.4, §6 and App. A–D.
- **Inconsistency between text and tables (our observation).** The text says "the FNRs are consistently no larger than 0.07 for all prompt injection attacks" (p. 10, §5.2). The introduction likewise says "at most 0.07" (p. 2). In the extracted Tables 1, 2 and 10–16, the largest DataSentinel FNR I could read against existing attacks is 0.02 (Table 10, p. 17). This could be an extraction misalignment of the merged cells, so the 0.07 figure is UNVERIFIED against a table.
- **Selecting hyperparameters and checkpoints.**
  - The ablations (Figs. 3–5, p. 11) report FPR/FNR as r, |D|, α, β, n_in and n_out vary. The paper does not say which data these curves were computed on, or whether it was separate from the Table 1–3 evaluation samples. Not found after reading §5.1 and §5.3.
  - Quote: "As a rule of thump, we can set α and β to be 1 in practice" (p. 11, §5.3). The defaults α = 1 and β = 1 match that recommendation (p. 10).
  - INFERENCE: the paper gives no evidence that the defaults were chosen on a validation set disjoint from the evaluation data.
- **Generalization and unseen-attack evaluation:**
  - Training uses one GCG separator on Gigaword with a summarization instruction. Evaluation covers 9 existing attacks (the separators in Table 7) on 7 tasks, with 7 injected instructions that differ from the training instruction (p. 10; p. 16).
  - Transfer across backend LLMs: the detector is fine-tuned against LLaMA3-8B-Instruct and tested on NeuralExec samples optimized against OpenChat, Mistral-7B, Mixtral-8x7B and LLaMA-3.1-8B-Instruct. FNR is 0.00–0.01, averaged over the 7×7 pairs (p. 12, Table 5).
  - Adaptive attacks that know the key space but not the key (p. 12, Eq. 6; p. 13, Table 6).
  - No group-disjoint or leave-one-attack-family-out protocol is described, and no row-split vs template-split comparison is made. Not found after reading §5.1–§5.4.
- **Attack effectiveness without a defense.** Reported as ASV and PNA-I (p. 17, Table 9). Some injected tasks have low ASV even without a defense, e.g. grammar correction, ASV 0.02–0.15 (p. 17). INFERENCE: FNR is counted over every constructed contaminated sample, whether or not the injection succeeds against the backend LLM.

## Findings relevant to our claims

| Claim | What the paper shows | Page | OVERLAP |
| --- | --- | --- | --- |
| C1 | Nothing on InjecGuard, HackAPrompt or template concentration in any release. INFERENCE: its own heuristic evaluation attacks consist of 5 fixed separator strings (p. 16, Table 7), but the paper does not analyse concentration. | p. 16 | none |
| C2 | Evaluates DataSentinel on attack separators not used in its training and calls this generalization to "attacks unseen during fine-tuning". There is no row-split vs held-out-template comparison, no per-template spread, and no HackAPrompt. | p. 10, §5.2 | none |
| C3 | No confidence intervals or variance of any kind, so no design-effect or cluster analysis. | §5 (pp. 8–13) | none |
| C4 | No comparison of row splits with group splits; TaskTracker and BIPIA are not used. | §5 | none |
| C5 | WITHDRAWN claim; not applicable. | — | n/a |
| C6 | ProtectAI is not evaluated. A related result for a different released detector: PromptGuard (86M) on data-embedded clean/contaminated samples has FPR 0.60–1.00 and FNR 0.00. It flags almost everything, at its default decision with no threshold calibration. This partly supports the broader point that released detectors fail on indirect/data-embedded inputs. It does not cover ProtectAI, recall at 1% FPR, TaskTracker or BIPIA. | p. 10, Table 3 | partial |
| C7 | No study of target-benign labels, threshold-only adaptation or matched vs generic retraining. The detector is trained on generic Gigaword data and applied to all targets (Table 4/5 show transfer across backend and detection LLMs, not label budgets). | pp. 10–12 | none |
| C8 | No score threshold: the rule is a binary key-match with no calibration from benign labels. | p. 5, Eq. 1 | none |
| C9 | Nothing on InjecGuard. | — | none |
| C10 | No group-allocation procedure. The evaluation samples are drawn at random from test sets. | p. 8 | none |

## Author-stated limitations (quoted, page-cited)

- On same-type tasks: "DataSentinel is less effective when the injected task and the target task are of the same type. This is because an attacker can leverage adaptive adversarial examples to implement an adaptive prompt injection attack whose contaminated target data only includes injected data but not injected instruction" (p. 14, §6).
- On benign instructions inside data: "in certain scenarios, a data sample may contain benign instructions. [...] In such cases, DataSentinel may falsely classify these benign instructions as prompt injection attacks." (p. 14, §6).
- On the training-time adaptive attack: "Note that our constraint on xc may make the adaptive attack weaker." (p. 7, §4.4).
- On the adaptive-attack objective: "our adaptive attack optimizes for an exact match to the secret key, while detection only requires the secret key to be included in the detection LLM's output. This aims to make the adaptive attack more evasive, with potentially reduced attack effectiveness." (pp. 12–13, §5.4.1).
- Future work: "exploring stronger adaptive attacks, e.g., when more advanced optimization methods are developed" (p. 14, §7).
- Meta-review concern (written by the S&P PC, not the authors): "It is possible that the defense would work less well as LLMs get better at following instructions, as this might make it easier to build adaptive attacks that make the LLM return the known answer and follow the prompt injection." (p. 19, App. D.4).
- INFERENCE (not stated by the authors):
  - The benign evaluation data are standard NLP dataset rows (100 per task). This makes the ~0 FPR a statement about those 7 datasets, not about benign inputs that contain instructions. The authors raise that case only as a limitation, without measuring it (p. 9; p. 14).
  - No interval accompanies any FPR or FNR.

## Bibliographic entry (BibTeX)

```bibtex
@inproceedings{liu2025datasentinel,
  author    = {Liu, Yupei and Jia, Yuqi and Jia, Jinyuan and Song, Dawn and Gong, Neil Zhenqiang},
  title     = {{DataSentinel}: A Game-Theoretic Detection of Prompt Injection Attacks},
  booktitle = {2025 IEEE Symposium on Security and Privacy (SP)},
  pages     = {2190--2208},
  year      = {2025},
  publisher = {IEEE},
  doi       = {10.1109/SP61157.2025.00250}
}
```
