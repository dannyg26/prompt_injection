# A Systematic Review of Prompt Injection Attacks on Large Language Models: Trends, Taxonomy, Evaluation, Defenses, and Opportunities

- Authors / venue / year / version read: Jaqueline Damacena Duarte, Guilherme D. Cândido, José Ricardo A. de Britto Filho, João Souza Neto, Elena J. da Costa, João Paulo Javidi da Costa, Laerte Peotta de Melo (University of Brasília). IEEE Access, vol. 14, 2026, pp. 12875–12899. DOI 10.1109/ACCESS.2026.3656849. Published 21 Jan 2026, current version 27 Jan 2026. CC BY 4.0. Publisher version (p. 1).
- File read: `literature/pdfs/systematic_review_access26.pdf`, pages read: 1–25 (all).
- How it was read: the Read tool could not render this PDF because `pdftoppm`/poppler is not installed in this environment. The text layer of all 25 pages was extracted with `pypdf`, installed into the session scratchpad, and that text was read in full. Page numbers below are PDF pages 1–25. Journal page = PDF page + 12874.
- Unreadable parts: the bodies of **Tables 1–6** (pp. 5, 6, 8, 15, 16, 19) and **Figures 1–8** are images with no text layer, so they could not be read. Only their captions and the running text that refers to them were read. Table 5 is "Datasets used in PromptRobust, grouped by task with dataset names and citations" (p. 16). Table 6 is "Mitigation strategies discussed across articles" (p. 19). Any dataset or detector named only inside those tables is **not covered** by this note.

## What it does
- This is a PRISMA-guided systematic literature review of prompt injection (PI). The search used Scopus only, with no time filter, and was limited to peer-reviewed journal and conference papers in English (p. 4, §III-B; p. 5). The final corpus is "32 peer-reviewed articles selected ... until May 31, 2025" (p. 21, §VIII).
- It is organised around five research questions: taxonomies (RQ1), evolution over time (RQ2), evaluation methods and benchmarks (RQ3), mitigations (RQ4), and gaps (RQ5) (p. 4, §III-A).
- It consolidates attack taxonomies by goal or intent, by level or trust boundary (direct vs indirect; Kumar et al.'s injection "space"), and by technique (p. 6–12, §V-A; Table 3, p. 8, image only).
- It reviews the datasets and metrics used to evaluate **attacks**: Q&A benchmarks, JailbreakHub, HackAPrompt, ASR, AIM/ASP/WRS, PDR/APDR and others (pp. 14–17, §V-C).
- It reviews defenses: automated red-teaming frameworks, input and output filtering, an LLM-based attack validator, RA-LLM, and CoT defenses (pp. 17–20, §V-D). It also lists eight gaps (p. 20, §VI).

## Data
- **The survey's own data.** Retrieved literature records were "tabulated, de-duplicated, and screened by at least two researchers" (p. 5, §III-B). This de-duplication applies to **bibliographic records**, not to prompt datasets. Two co-authors assessed eligibility independently, and a third resolved disagreements. The authors report "inter-rater agreement fully matched" (p. 5). No agreement statistic is given.
- **Datasets it reports from the reviewed literature:**
  - Q&A and NLU benchmarks used to measure degradation under attack: TruthfulQA, Q16, QNLI/GLUE, Yelp, IMDB, MNLI (p. 14, §V-C1).
  - Annotated datasets used for output judging: ETHOS, NudeNet, ToxiGen (p. 14).
  - Jailbreak Chat, 78 prompts (Liu et al. [39]) (p. 14).
  - JailbreakHub (Shen et al. [34]): "15,140 prompts collected from December 2022 to December 2023 ... of which 1,405 were identified as jailbreak prompts". It comes with a forbidden-question set of 107,250 samples (p. 14).
  - HackAPrompt (Schulhoff et al. [33]): "over 2,800 participants who submitted more than 600,000 human-authored adversarial prompts" (p. 15).
  - The Adversarial Nibbler T2I red-teaming dataset (p. 15).
  - PAP: harmful base prompts paraphrased by a fine-tuned "Persuasive Paraphraser" (p. 14).
  - For InjecAgent [58], the survey reports "1,054 test cases in 30 different LLM agents" using 17 ToolEmu tools (p. 11).
- **Train/test formation.** Not found after reading §I–§IX (pp. 1–21). The survey does not describe how any reviewed study split train and test data, whether splits were by row, source, template or family, or any deduplication or near-duplicate handling of prompt datasets.
- **Dataset critique.** Author-stated (p. 15, §V-C1): "However, a key limitation is the lack of a unified, standardized approach. While valuable, many datasets (including those collected from uncontrolled online environments for ground truth) may introduce noise or bias." The authors add that malicious-prompt datasets are mostly monolingual (English). They call for "standardized, comprehensive, multilingual, and multicultural benchmarks ... to ensure reliable and generalizable PI evaluation" (p. 15).
- **Paraphrase and template material, described as attack techniques rather than as a leakage concern.** PAP paraphrasing (pp. 10, 13, 14). ReNeLLM "prompt rewriting and scenario nesting" (p. 10). Community-shared jailbreak prompts that persist and are refined: "one example remained for over 240 days and achieved a 95% attack success rate", citing [34] (p. 13).
  - INFERENCE: these passages describe the same mechanisms that would produce template or paraphrase near-duplicates in PI datasets. The survey never draws that connection.

## Detectors / models evaluated
- The survey trains and evaluates nothing itself (whole paper; p. 21, §IX "relied exclusively on published secondary data").
- **Released PI detectors.** None of PromptGuard, ProtectAI, InjecGuard/PIGuard or any DeBERTa-based PI classifier is named in the extracted text, pp. 1–25. Tables 5 and 6 could not be read (see above).
- **Detection-type defenses it describes:**
  - Muliarevych [111] (p. 19): a Prompt Analyzer plus an "Attack Validator module that uses LLMs to classify prompts as benign or adversarial", and a Fuzzy Search method that compares inputs "to a database of known attack patterns using approximate matching". The LLM validator "provided stronger defense against sophisticated prompts, outperforming fuzzy matching" (p. 19). No numbers, splits or intervals are reported.
    - INFERENCE: fuzzy matching against known attack patterns would benefit directly from template overlap between the pattern database and the test prompts. The survey does not raise this.
  - Greshake et al. [7]: input and output filtering, outlier detection, and a second LLM as moderator (p. 19).
  - Zhu et al. [38]: perplexity-based filtering, spelling verification, and trust-based access control (p. 19).
  - Sharma et al. [52]: the SPML image-input validation pipeline (p. 19).
  - RA-LLM [112]: random token dropping with a refusal-consistency check (p. 19).
  - FDI, reported via Sun et al. [45]: "Defensive techniques such as ... ONION and anomaly classifiers proved largely ineffective, either by failing to filter malicious feedback or by excessively removing benign content" (p. 12).
  - Frozen safety classifiers (Q16, NudeNet, ToxiGen, LaMDA-based psafe) appear only as **scoring engines** inside red-teaming frameworks (pp. 13, 17–18). They are not evaluated as detectors.

## Evaluation and statistics
- **Metrics catalogued (all oriented to attacks):**
  - ASR, the most prevalent (p. 16, §V-C2).
  - AIM, ASP and WRS (Yip et al. [32]) (p. 16).
  - A-Rate, P-Rate, G-Error, S-Sim and S-Cons (Prompt-Attack [43]) (p. 16).
  - QMA, BLEU and chrF ([42], [35]) (p. 16).
  - ACC and SSS (LinkPrompt [50]) (p. 17).
  - PDR and APDR (PromptRobust [38]) (p. 17).
  - Pass@1 (VPI [46]) (p. 17).
  - Clean and robust accuracy (APT [40]) (p. 17).
- **Its critique of ASR, quoted.** "However this approach does not differentiate the severity of a successful attack and can't correctly measures accurate and semantic degradation of model responses." (p. 16). Synthesis: "a clear trend from binary success rates toward multidimensional evaluation frameworks" (p. 17).
- **Detector operating points.** Nothing on FPR thresholds, recall at fixed FPR, AUROC, or false-positive cost on benign traffic. Not found after reading §V-C–§VI (pp. 14–20). F1 appears only as one task metric inside PDR (p. 17).
- **Seeds, variance and uncertainty.** Nothing on confidence intervals (example-level or group/cluster-level), seeds, variance, bootstrap, significance testing, or design effects. Not found after reading §I–§IX (pp. 1–21). A keyword search of the full extracted text for "confidence", "interval", "seed" (used only for red-team seed prompts, p. 18), "variance" and "statistic" found nothing relevant.
- **Generalization.** It appears only as: a call for "reliable and generalizable PI evaluation" benchmarks (p. 15); transferability of attacks across models (LinkPrompt, p. 9; reproducibility enabling "analysis of transferability of attack and defense strategies", p. 20); and cross-lingual generalization (p. 10, p. 20). There is no discussion of detector generalization to unseen templates, sources or datasets. Not found after reading pp. 1–21.
- **Reproducibility.** Author-stated gap (p. 20, §VI): "Fourth, reproducibility remains a challenge, particularly in integrated-tools (e.g. AI agents) and glass-box attack scenarios". They note that many reviewed studies shared code and data.
- **Classifier-based scoring noise.** Author-stated gap (p. 20, §VI): "Seventh, various studies rely on automatic feedback coming from classifiers that may introduce noise, highlighting the need for more studies on the impact of noise and its mitigation [66]."

## Does the survey identify template/near-duplicate leakage or group-level uncertainty as an open problem?
**No.** The survey lists these eight gaps (p. 20, §VI; numbered in the text "First" ... "Seventh", "Eighteenth" [sic]):
1. agent and integrated-tool evaluation;
2. no standardized metric framework;
3. monolingual focus;
4. reproducibility;
5. multimodal channels;
6. lack of defense evaluation;
7. classifier-feedback noise;
8. cryptographic safeguards.

None concerns train/test leakage, template or near-duplicate concentration, group-aware splitting, or group- or cluster-level uncertainty. The closest statements are:
- dataset "noise or bias" from uncontrolled online collection (p. 15);
- the lack of "a standardized metric framework" (p. 20);
- the call for "the design of PI-specific adversarial evaluation metrics" (p. 21, §VII).

INFERENCE: this survey does not anticipate C1–C4 or C10 as recognised open problems. It does not show that such problems are unrecognised elsewhere: its corpus is 32 Scopus-indexed papers up to May 2025 and excludes arXiv-only work (pp. 4–5, 21).

## Findings relevant to our claims
- **C1** (template concentration in the InjecGuard release; HackAPrompt 5,000 rows = 6 groups). The survey describes HackAPrompt only as a large competition dataset (>600,000 prompts from >2,800 participants). It does not analyse template concentration or any benign/attack asymmetry (p. 15). It does not mention InjecGuard. **OVERLAP = none** (p. 15).
- **C2** (leave-one-template-out recall on HackAPrompt). No detector evaluation under held-out templates, and no row-split vs template-split comparison. Not found after reading pp. 1–21. **OVERLAP = none** (pp. 14–17).
- **C3** (design effects above 1; example-level intervals too narrow). There is no discussion of intervals, clustering or design effects. Not found after reading pp. 1–21. **OVERLAP = none** (pp. 16–17, 20).
- **C4** (null inflation on TaskTracker/BIPIA/jailbreak under randomized group splits). TaskTracker and BIPIA are not mentioned, and neither is split-induced inflation. Not found after reading pp. 1–21. **OVERLAP = none** (pp. 14–15).
- **C5** (withdrawn). Not applicable; nothing related (pp. 14–17). **OVERLAP = none**.
- **C6** (ProtectAI v2 low recall on indirect injection). The survey discusses indirect PI as an attack class (Greshake [7], InjecAgent [58]; pp. 7, 11–12, 14) and LLM or fuzzy detectors (p. 19). It does not name or evaluate any released PI classifier on indirect-injection data. **OVERLAP = none** (pp. 11–12, 19).
- **C7** (benign-only target adaptation with 200 labels). The survey covers no benign-only adaptation, threshold recalibration, or retraining of detectors on target-domain benign data. Not found after reading pp. 1–21. **OVERLAP = none** (pp. 17–20).
- **C8** (FPR from a threshold set on B benign labels). The survey does not discuss FPR operating points or threshold calibration. **OVERLAP = none** (pp. 16–17).
- **C9** (InjecGuard train/eval cleanliness; validation = evaluation items). InjecGuard is not mentioned. **OVERLAP = none** (pp. 1–21).
- **C10** (deterministic largest-first group allocation produced a spurious result). The survey does not discuss split allocation procedures. **OVERLAP = none** (pp. 1–21).

## Cited works to consider reading
Each entry gives the reference number and the title as printed (pp. 21–24), with the claim it may bear on.

INFERENCE: none of the cited works is about benchmark leakage, template or paraphrase duplication as an evaluation artifact, group-aware splitting, or benign-only adaptation, so relevance below is indirect. Also, the reference list has no entries for PromptGuard, ProtectAI, InjecGuard/PIGuard, BIPIA, TaskTracker, PIDS-Bench or "When Benchmarks Lie" (pp. 21–24).

- **[33]** S. Schulhoff et al., "Ignore this title and HackAPrompt: Exposing systemic vulnerabilities of LLMs through a global prompt hacking competition," EMNLP 2023 (p. 22).
  - Bears on C1, C2, C3: the origin of the HackAPrompt data whose template concentration we measure. Already item 9 on our reading list.
- **[34]** X. Shen, Z. Chen, M. Backes, Y. Shen, and Y. Zhang, "'Do anything now': Characterizing and evaluating in-the-wild jailbreak prompts on large language models," ACM CCS 2024 (p. 22).
  - Bears on C1, C3: it characterises community-shared, iteratively refined jailbreak prompts ("131 jailbreak communities", p. 13). It may contain its own analysis of near-duplicate or prompt-family structure. UNVERIFIED until read.
- **[7]** K. Greshake, S. Abdelnabi, S. Mishra, C. Endres, T. Holz, and M. Fritz, "Not what you've signed up for: Compromising real-world LLM-integrated applications with indirect prompt injection," AISec 2023 (p. 21).
  - Bears on C6: the foundational framing of indirect PI. The survey also credits it with recommending filtering and LLM-moderator detection (p. 19).
- **[58]** Q. Zhan, Z. Liang, Z. Ying, and D. Kang, "InjecAgent: Benchmarking indirect prompt injections in tool-integrated large language model agents," Findings of ACL 2024 (p. 23).
  - Bears on C6: an indirect-injection benchmark built from templated test cases (1,054 cases, 17 tools; p. 11). Its construction may bear on template concentration in indirect data. UNVERIFIED.
- **[111]** O. Muliarevych, "Enhancing system security: LLM-driven defense against prompt injection vulnerabilities," IEEE TCSET 2024 (p. 24).
  - Bears on C2, C6: the only reviewed work that evaluates a classifier-style PI detector (an LLM validator vs fuzzy matching against known attack patterns; p. 19). It is worth checking how its test prompts relate to its pattern database.
- **[38]** K. Zhu et al., "PromptRobust: Towards evaluating the robustness of large language models on adversarial prompts," ACM LAMPS Workshop 2023 (p. 22).
  - Bears on C2: a robustness benchmark across prompt types and manipulation levels, with aggregated PDR/APDR (p. 17). Possible relevance to how aggregation across prompt groups is handled.
- **[41]** Y. Zeng, H. Lin, J. Zhang, D. Yang, R. Jia, and W. Shi, "How Johnny can persuade LLMs to jailbreak them: Rethinking persuasion to challenge AI safety by humanizing LLMs," ACL 2024 (p. 22).
  - Bears on C1, C2: systematically paraphrased attack prompts (PAP) form natural paraphrase families derived from shared base prompts (p. 14).
- **[47]** P. Ding et al., "A wolf in sheep's clothing: Generalized nested jailbreak prompts can fool large language models easily," NAACL 2024 (p. 22).
  - Bears on C1, C2: rewriting plus nesting into a small set of scenario templates (p. 10), which is template-structured attack generation.
- **[32]** D. W. Yip, A. Esmradi, and C. F. Chan, "A novel evaluation framework for assessing resilience against prompt injection attacks in large language models," IEEE CSDE 2023 (p. 22).
  - Bears on C3: a PI evaluation-methodology paper (AIM/ASP/WRS; p. 16). Check whether it reports any uncertainty.
- **[66]** N. Mehrabi et al., "FLIRT: FeedBack loop in-context red teaming," EMNLP 2024 (p. 23).
  - Bears on C3, weakly: the survey cites it for noise from classifier-based scoring (p. 20).
- **[11]** S. S. Kumar, M. Cummings, and A. Stimpson, "Strengthening LLM trust boundaries: A survey of prompt injection attacks," IEEE ICHMS 2024 (p. 21).
  - Background survey. Its "explored space" of community-validated prompts (p. 7) is conceptually related to template reuse.
- **[42]** A. V. Miceli Barone and Z. Sun, "A test suite of prompt injection attacks for LLM-based machine translation," WMT 2024 (p. 22).
  - A templated PI test suite; low priority.

## Author-stated limitations (quoted, page-cited)
- "We emphasize that the scope of our analysis was limited to the corpus of 32 peer-reviewed articles selected through the most relevant venues and publications until May 31, 2025, based on a predefined SLR protocol. While the selected material provides substantive insights, it does not exhaustively cover the full spectrum of adversarial prompting techniques, especially in emerging or under-reported domains." (p. 21, §VIII)
- Search restricted to Scopus, and to "peer-reviewed journal articles and conference papers ... written in English" (pp. 4–5, §III-B).
  - INFERENCE: arXiv-only detector and benchmark papers, such as InjecGuard (arXiv version), "When Benchmarks Lie" and PIDS-Bench (2026), fall outside its window or scope.
- On datasets: "many datasets (including those collected from uncontrolled online environments for ground truth) may introduce noise or bias." (p. 15, §V-C1)
- On metrics: "the lack of a standardized metric framework reduces the suitability of assessments for practical purposes, limiting the accurate evaluation of vulnerability severity for risk assessment and negatively impacting the benchmarking of solutions." (p. 20, §VI)
- Minor internal inconsistencies observed:
  - Footnote 4, attached to "PRISMA", points to a Google LaMDA blog URL (p. 4).
  - The gap list jumps from "Seventh" to "Eighteenth" (p. 20).
  - Footnote markers and URLs are offset: marker 7 after "StackOverflow" resolves to the HackAPrompt HuggingFace URL, and the HackAPrompt marker 8 has no printed footnote (pp. 14–15).
  - Reference [2] attributes "The Illusion of Thinking" to Khashabi et al. (p. 21).
  - INFERENCE: these editing errors suggest checking the survey's secondary descriptions against the primary sources before relying on them.

## Bibliographic entry (BibTeX)
```bibtex
@article{duarte2026systematic,
  author  = {Duarte, Jaqueline Damacena and C{\^a}ndido, Guilherme D. and de Britto Filho, Jos{\'e} Ricardo A. and Souza Neto, Jo{\~a}o and da Costa, Elena J. and da Costa, Jo{\~a}o Paulo Javidi and de Melo, Laerte Peotta},
  title   = {A Systematic Review of Prompt Injection Attacks on Large Language Models: Trends, Taxonomy, Evaluation, Defenses, and Opportunities},
  journal = {IEEE Access},
  volume  = {14},
  pages   = {12875--12899},
  year    = {2026},
  doi     = {10.1109/ACCESS.2026.3656849}
}
```
