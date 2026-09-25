# PIDS-Bench: Evaluating Prompt-Injection Detectors Under Over-Defense, Obfuscation, and Distribution Shift

- Authors / venue / year / version read: Yusuf Khalid Shire and Sang-Chul Kim (Kookmin University). IEEE Access, vol. 14, 2026, pp. 134184–134205, DOI 10.1109/ACCESS.2026.3728186. Received 22 July 2026, accepted 23 August 2026, published 28 August 2026, current version 3 September 2026. Open access, CC BY 4.0. (p. 1, header and footer; the page range comes from the printed folios 134184 on p. 1 and 134205 on p. 22.) Version read: the publisher PDF.
- File read: literature/pdfs/pids_bench.pdf. All 22 PDF pages were read, pp. 1–22.
- How it was read: the Read tool's PDF mode failed in this environment because `pdftoppm` was not installed. I extracted the full text layer of all 22 pages with PyMuPDF into a scratchpad file and read all of it. Table bodies are missing from the text layer, so I rendered pp. 8, 10, 12, 13, 14 and 17 as images and read them visually. That covers Tables 1–18 and Figures 1–3.
- Unreadable parts: none of substance. I did not inspect the figures at pixel level beyond what their captions and the text state. In this note, "p. N" means the PDF page. The printed page number is 134183 + N.

## What it does (3–6 bullets, each page-cited)

- It builds a frozen, SHA-256-checksummed detector benchmark: a main corpus of 35,000 rows (27,093 train / 3,989 validation / 3,918 test) and five stress sets (hard-benign, domain shift, structural shift, obfuscated, balanced-subtype). That makes 43,172 evaluation instances and 40,479 unique prompts. (p. 8, §V-C, Tables 2–3)
- It evaluates three internal learned detectors: TF-IDF+LR, DistilBERT and DeBERTa-v3-FT, each with 5 seeds. It also evaluates two released PI classifiers (ProtectAI v2 and deepset DeBERTa-PI), two broad-safety models (PromptGuard 2 86M and Llama Guard 3-1B) and a rule-based reference. (p. 5, §IV-A; p. 6, §IV-B1)
- Headline result: DeBERTa-v3-FT reaches IID F1 0.9882. At τ=0.5 it still flags 0.3144 ± 0.0525 of externally-sourced security-adjacent benign prompts. Across a full τ sweep, no internal detector reaches F1 ≥ 0.95 and externally-sourced hard-benign FPR ≤ 0.10 together. (p. 11, §VI-A1; p. 13, §VI-B, Table 9)
- Hard-negative augmentation (419 curated benign examples) nearly eliminates over-defense on curated prompts but leaves over-defense on externally-sourced prompts largely unchanged. The authors call this "provenance-sensitive over-defense". Varying the pool size (100/200/300/419) does not change it. (p. 13–14, §VI-C, Table 10, Fig. 3)
- Temperature scaling roughly halves ECE but leaves hard-benign FPR identical. The authors argue that over-defense is a decision-surface property, not a calibration artifact. (p. 15–16, §VI-F, Table 11)
- An observational decomposition of the externally-sourced FPR finds that instruction-like structure is the larger driver and that source corpus adds a smaller independent effect. (p. 14–15, §VI-D)

## Data

- **Injection sources** (p. 7, §V-B1): SPML Chatbot Prompt Injection (8,423), Qualifire (676) and deepset (126), plus template-derived attacks. "The counts reported here are the final per-source totals in the released corpus, after deduplication and class-balanced sampling". The main injection pool has n = 18,363 (p. 8, Table 1). HackAPrompt, TaskTracker and BIPIA are **not** data sources. BIPIA appears only in related work, as an end-to-end benchmark (p. 2, p. 4 §II-C, p. 17 §VII-A). TaskTracker: not found after reading §I–§IX and the Appendix.
- **Benign sources** (p. 7, §V-B2): Alpaca (7,952), ChatBot Instructions (4,961), OASST1 (1,317), Dolly-15K (576) and 1,831 template-generated prompts, for 16,637 in total. Quote: "No corpus text is carried over verbatim: each seed is rewritten by GPT-4o-mini [44] over one to three paraphrase rounds under a meaning-preserving prompt, and every released benign row is a paraphrase variant that inherits its seed's label." (p. 7)
- **Template construction** (p. 7, §V-B3): template-derived attacks cover only `encoded_attack` and `tool_injection`. Quote: "GPT-4o-mini [44] generates three surface-level paraphrases per real seed at sampling temperature 0.9, under a prompt that varies phrasing while preserving adversarial intent." Template-derived rows are "934 of the 3,918 held-out test examples (23.84%) and 801 of the 2,070 test injections (38.70%)." (p. 7) The per-partition template share is 33.6% train, 23.2% validation and 23.8% test (p. 8, Table 3).
- **Seed-family separation: how families are defined and assigned.** Quote: "First, split assignment is enforced at the seed-family level. Every paraphrase and obfuscated descendant of a source example is assigned to the same partition before the train/validation/test split is applied, eliminating the evaluation inflation that arises when structurally similar examples straddle training and evaluation data [3]." (p. 7, §V-A)
  - A family is therefore one source seed together with its GPT-4o-mini paraphrases and obfuscated variants. This is a lineage-based (provenance) grouping, not a similarity-based clustering. (p. 7)
  - **How families are assigned to splits** (random, stratified or otherwise), the number of families and the family-size distribution: not found after reading §IV–§VI and the Appendix. The paper says only "Template-derived examples are concentrated in the training split so that evaluation preserves external provenance" (p. 8, §V-C). Test still contains 23.8% template-derived rows (p. 8, Table 3).
  - **Effect of NOT separating families** (a row-level versus family-level split comparison, with numbers): not found after reading §I–§IX and Appendices A–H. The inflation is asserted with a citation to Ribeiro et al. [3] (CheckList), not measured. (p. 7)
  - Author-stated limit of family separation. Quote: "seed-family separation prevents variant leakage across partitions but does not remove this shared style. Recall on these two subtypes is therefore best read as an upper bound, and attacks written by other generators or by hand could lower it." (p. 19, §VIII-C)
  - Related descriptive result: template-derived test F1 is higher than real-source F1 for every internal detector. The values are DeBERTa-v3-FT 0.9974 vs 0.9825, DistilBERT 0.9980 vs 0.9738, and TF-IDF 0.9962 vs 0.9467 (p. 17, Table 13; p. 11, §VI-A5). Quote: "Because template-derived text is lexically more uniform, aggregate IID F1 overstates real-source performance" (p. 11).
- **Deduplication and near-duplicate handling**:
  - Main corpus: "Exact-match and near-duplicate filtering reduces leakage, but residual label noise or incidental injection-adjacent phrasing may remain" (p. 7, §V-B2). The operational near-duplicate definition for the main corpus is not found after reading §V.
  - Domain-shift set: "Both sides are near-duplicate filtered against training (character n-gram TF-IDF, cosine threshold 0.90)" (p. 10, §V-F1). Structural-shift injection seeds are "near-duplicate filtered against training" (p. 10, §V-F3).
  - Table 2 overlap counts "are computed by exact text matching across all partitions of the released artifact" (p. 8, Table 2 caption).
  - The hard-benign evaluation prompts are "disjoint from the training rows, with verified zero text overlap" (p. 9, §V-E3).
  - The hard-negative augmentation pool "is built from training-side seeds only and deduplicated against all frozen evaluation sets" (p. 13, §VI-C).
- **Stress sets**:
  - Hard-benign: 1,472 rows, split into 872 externally-sourced and 600 curated. The externally-sourced rows come from LMSYS-Chat-1M (298 plain + 366 AI-adjacent), OASST1 (40 + 100) and Dolly (18 + 50). The curated rows form "eight equally sized authored families" of 75 each. (p. 9 §V-E3; p. 10 Table 4)
  - Domain shift: 2,000 rows, 250 benign and 250 injection for each of four domains. (p. 10, §V-F1)
  - Structural shift: 1,998 rows, from 333 benign and 333 injection seeds × 3 transforms. (p. 10, §V-F3)
  - Obfuscated: 405 held-out test injections. The authors say "These transform families already appear in training". (p. 11, §V-F4)
  - Balanced-subtype: 2,297 rows, of which 2,288 come from the test split. (p. 8–9, §V-D)
- **Annotation**: subtype κ = 0.758 on 150 rows (p. 8). Hard-benign benign/non-benign: 199/200 agreement, κ = 0.85. Security-adjacent designation: κ = 0.53. Label-error rate 1/200, 95% Wilson interval [0.001, 0.028]. (p. 9, §V-E2)
- **Licensing**: two corpora are non-commercial. LMSYS rows are released text-stripped with SHA-256 fingerprints, and 664 rows are restored by `rebuild_restricted.py`. The artifact is tagged v1.0-pids-bench, commit 87dc835. (p. 21, App. G)

## Detectors / models evaluated

- **Trained here** (p. 5, §IV-A1; p. 5–6, §IV-B): TF-IDF (1–2-gram) + LR, DistilBERT (distilbert-base-uncased, 2 epochs) and DeBERTa-v3-FT (microsoft/deberta-v3-base, 3 epochs). A keyword/regex rule-based reference is reported separately.
- **Released PI detectors, inference-only at default τ=0.5** (p. 5, §IV-A2; p. 3 §II-B):
  - ProtectAI `deberta-v3-base-prompt-injection-v2` [22]
  - deepset `DeBERTa-v3-base-injection` ("DeBERTa-PI") [23]
- **Broad-safety comparators** (p. 5, §IV-A3): Llama Prompt Guard 2 (86M) [24] and Llama Guard 3-1B [19].
- **Not evaluated:** PIGuard/InjecGuard (cited only as [14], "NotInject"; p. 3, p. 21) and PromptShield (cited as [16], p. 3). Not found as evaluated detectors after reading §IV–§VI.
- **Released-detector results, at default τ=0.5 on PIDS-Bench data only** (p. 12, Table 7):

  | Detector | IID F1 | IID recall | hb-FPR | Obf. recall | Struct.-shift FPR | ROC-AUC |
  | --- | --- | --- | --- | --- | --- | --- |
  | ProtectAI | 0.9036 | 0.858 | 0.216 | 0.906 | 0.4525 | 0.9741 |
  | DeBERTa-PI | 0.8044 | 0.944 | 0.804 | — | 1.000 | 0.8712 |

  - The extracted row for DeBERTa-PI obfuscated recall reads 0.970. The table has four ProtectAI/DeBERTa-PI rows, including swept thresholds: ProtectAI τ=0.002 and DeBERTa-PI τ=0.986.
  - Per-origin hb-FPR with example-level 95% bootstrap intervals (p. 17, Table 18): ProtectAI ext-sourced 0.083 [0.065, 0.101] and curated 0.410 [0.372, 0.448]; DeBERTa-PI ext-sourced 0.825 [0.799, 0.849] and curated 0.773 [0.740, 0.807].
  - **Recall on externally sourced indirect-injection data (TaskTracker, BIPIA)** and **recall at a fixed low FPR for released detectors**: not found after reading §IV–§VII and Appendices A–F. The released detectors are reported only at τ=0.5 and at a validation-F1-swept τ.
  - The only fixed-FPR recall figures are for the internal detectors on the IID split. Quote: "at an IID benign FPR of 0.01, DeBERTa-v3-FT recalls 0.984 of injections and DistilBERT 0.963" (p. 15, §VI-E1).
  - The structural-shift set's `json_wrap` and `prompt_dilute` transforms are described as "mimicking tool-call output" and "mimicking injection buried in a retrieved passage" (p. 10). For released detectors, only the benign-side FPR on this set is tabulated, not attack recall (p. 12, Table 7).

## Evaluation and statistics

- **Metrics** (p. 6, §IV-D):
  - IID: F1, with real-source F1 as primary; precision, recall and ROC-AUC.
  - Hard-benign: FPR, reported in aggregate and by provenance.
  - Obfuscated: recall.
  - Domain and structural shift: F1 and benign FPR.
- **Thresholds** (p. 6, §IV-C):
  - Internal detectors: per-seed grid search over [0, 1], step 0.002, maximising validation F1. The selected DeBERTa-v3-FT thresholds are {0.01, 0.108, 0.152, 0.444, 0.904}; DistilBERT {0.112, …, 0.664}; TF-IDF 0.518 every run.
  - Main multi-axis tables use fixed τ=0.5 (p. 12, Tables 6, 8).
  - The oracle frontier selects τ on the hard-benign set itself, labelled as an upper bound (p. 15, §VI-E3).
- **Seeds**: "Each internal architecture is trained five times under identical hyperparameters with distinct random seeds {13, 42, 123, 2024, 7777} on the same cluster environment. All reported quantitative results are five-seed mean ± standard deviation" (p. 6, §IV-B1). TF-IDF is identical across seeds, so its std is 0 "by construction" (p. 6). The same test and stress sets are used for every seed (p. 6, §IV-C). INFERENCE: the seeds are repeated runs on overlapping data, not additional test examples.
- **Confidence intervals: example-level bootstrap.** Quote: "Because seed variance does not capture the sampling uncertainty of a finite stress set, we additionally report example-level bootstrap confidence intervals [35] (10,000 resamples) for the headline metrics" (p. 7, §IV-D5). Repeated at p. 16, §VI-H: "We therefore report example-level bootstrap confidence intervals (10,000 resamples) alongside the seed standard deviations".
  - The 95% intervals are described as "narrow and agree with the seed standard deviations" (p. 16, §VI-H1). Example: DeBERTa-v3-FT ext-sourced hb-FPR 0.3144 [0.2881, 0.3424] (p. 17, Table 17).
  - ROC-AUC intervals are omitted near the ceiling (p. 16, Table 17 caption).
  - Whether the bootstrap for a five-seed mean resamples examples within each seed, or pools them: not stated after reading §IV-D5, §VI-H and Appendix E.
- **Cluster / family-level resampling, design effect, effective sample size, ICC**: not found after reading §IV–§VIII and Appendices A–F. The resampling unit is stated only as "example-level" (p. 7, p. 16, p. 17 captions).
  - INFERENCE: the curated hard-benign subset has 8 authored families of 75 rows (p. 10, Table 4). The structural-shift set has 3 transforms per seed (p. 10). Test rows include up to three paraphrases per seed (p. 7). An example-level bootstrap treats these related rows as independent. The paper does not discuss this.
- **Augmentation test** (p. 16, §VI-H2; p. 17, Table 12): a paired t-test and a Wilcoxon signed-rank test over 5 seeds, plus an example-level bootstrap interval on the difference. Quote: "With five paired observations, the Wilcoxon p-value cannot fall below 0.0625; for the large curated and aggregate effects, that floor, not a weak signal, is why the test reports 0.0625, so we treat the bootstrap as primary." (p. 16) For DistilBERT's externally-sourced effect, they instead say: "Because augmentation is applied per seed, the seed-level tests are the appropriate measure of the effect, so we read the reduction as suggestive rather than established." (p. 16)
  - DeBERTa-v3-FT ext-sourced: Δ −0.004, t-p 0.90, bootstrap [−0.014, +0.005].
  - DistilBERT ext-sourced: Δ −0.071, t-p 0.13, Wilcoxon p 0.125, bootstrap [−0.084, −0.058].
- **Other inference**: partial correlations with p-values for structure versus source (p. 14, §VI-D). The authors state "we therefore do not conduct cross-group significance testing" (p. 7).

## Findings relevant to our claims

- **C1** (template concentration of InjecGuard/HackAPrompt sources)
  - The paper does not use the InjecGuard release or HackAPrompt data. It does not count rows per template or group for any source: not found after reading §V and Appendix A.
  - It does report that its own GPT-4o-mini template-derived rows are "lexically more uniform" and inflate IID F1 (p. 7, p. 11, p. 17 Table 13).
  - OVERLAP = **none** for C1 as scoped. The general observation that template-derived rows are easier is related; see p. 11 and p. 19, §VIII-C.
- **C2** (held-out-template recall range vs row splits on HackAPrompt)
  - No leave-template-out or leave-family-out evaluation and no row-split comparison: not found after reading §IV–§VIII.
  - The author-stated qualitative caveat is closest: shared generator style survives family separation, so template-subtype recall is "best read as an upper bound" (p. 19, §VIII-C).
  - "Controlled leave-one-source-out retraining" is listed as untested future work (p. 18, §VII-F).
  - OVERLAP = **none** (p. 18–19).
- **C3** (design effects > 1; example-level intervals too narrow)
  - The paper uses only example-level bootstrap intervals and describes them as "narrow" and in agreement with seed std (p. 16). No design effect, ICC or cluster bootstrap: not found after reading §IV-D, §VI-H and Appendices E–F.
  - OVERLAP = **none** (p. 7, p. 16).
  - INFERENCE: the paper's intervals are an instance of the practice C3 critiques.
- **C4** (row vs randomized group split inflation on TaskTracker/BIPIA/jailbreak)
  - The paper asserts that family separation eliminates inflation (p. 7, §V-A) but does not measure the row-vs-family difference. It does not use TaskTracker, BIPIA or jailbreak-classification.
  - OVERLAP = **none** (p. 7).
- **C5** (withdrawn): OVERLAP = **none**.
- **C6** (ProtectAI v2 recall at 1% FPR on TaskTracker/BIPIA)
  - ProtectAI v2 is evaluated, but only on PIDS-Bench sets at τ=0.5 or a swept τ. Reported values: IID recall 0.858, obfuscated recall 0.906, ext-sourced hb-FPR 0.083 (p. 12, Table 7; p. 17, Table 18). No indirect-injection external data and no fixed-FPR operating point for released detectors.
  - OVERLAP = **none** for the claim. It shares the detector (p. 12).
- **C7** (matched retraining vs threshold-only vs generic retraining with 200 benign target labels)
  - The paper shows that curated hard-negative augmentation (419 examples, pool sizes 100–419, 5 seeds) does not reduce externally-sourced over-defense. DeBERTa-v3-FT goes 0.314 → 0.310, Δ −0.004, bootstrap [−0.014, +0.005] (p. 13–14 Table 10, Fig. 3; p. 17 Table 12).
  - Threshold sweeps and temperature scaling do not reach the target (p. 13, Table 9; p. 15–16, §VI-F).
  - Author-stated gap: "Augmentation drawn to match the externally-sourced distribution is a distinct intervention we do not evaluate; we identify it as future work (Section VII-F)" (p. 14, §VI-C). Also: "What we have not tested is augmentation drawn to match the externally-sourced distribution rather than the curated pool; whether that would close the gap is open" (p. 19, §VIII-D). Also in the abstract (p. 1) and the conclusion (p. 20).
  - The paper tests generic/curated augmentation and threshold/calibration adjustments, which correspond to C7's comparators. It explicitly does not test distribution-matched augmentation, which is C7's intervention.
  - OVERLAP = **partial** (p. 14, p. 19).
  - INFERENCE: C7 tests an intervention that this paper names as untested. C7's null result therefore does not duplicate this paper, but the two papers share the conclusion that threshold-only and generic augmentation are insufficient on the target distribution.
- **C8** (order-statistic threshold from B benign labels)
  - Not found after reading §IV-C and §VI-B/E. Thresholds are selected on a validation set of 3,989 rows (p. 6), with no small-B analysis.
  - OVERLAP = **none**.
- **C9** (InjecGuard train/eval contamination)
  - Not found. InjecGuard/PIGuard data is not used (p. 3, p. 21 ref [14]).
  - OVERLAP = **none**.
- **C10** (deterministic vs randomized group allocation)
  - How families are allocated to splits is not stated; see the Data section.
  - OVERLAP = **none** (p. 7–8).

## Author-stated limitations (quoted, page-cited)

- "Because these two subtypes are lexically more uniform than externally-sourced attacks, they may under-represent real-world surface diversity, a caveat that applies to every model evaluated on the test split." (p. 7–8, §V-B3)
- "seed-family separation prevents variant leakage across partitions but does not remove this shared style. Recall on these two subtypes is therefore best read as an upper bound, and attacks written by other generators or by hand could lower it." (p. 19, §VIII-C)
- "What we have not tested is augmentation drawn to match the externally-sourced distribution rather than the curated pool; whether that would close the gap is open (Section VII-F). We therefore treat augmentation as a diagnostic probe of the over-defense mechanism, not a solved mitigation." (p. 19, §VIII-D)
- "Benign labels are accepted as originally curated and, unlike the hard-benign stress set (Section V-E), were not subject to independent inter-annotator audit at the same depth." (p. 7, §V-B2)
- "The remaining caveat is that both annotators are project-internal; an external audit is left to future work." (p. 19, §VIII-B)
- "The evaluation does not impose a shared calibration protocol across all model groups … This creates two distinct operating conditions and limits the interpretability of cross-group threshold-dependent comparisons." (p. 6, §IV-C)
- "These transform families already appear in training, so the set measures sensitivity to known perturbations rather than robustness to novel evasion" (p. 11, §V-F4)
- "the source-controlled analysis of Section VI-D is observational, and a source-holdout design remains the direct test of the residual source component." (p. 18, §VII-F)
- "any single-threshold result for the neural detectors should be read as one point on an unstable surface rather than a fixed property" (p. 19, §VIII-E)
- "aggregate hard-benign figures should be read as worst-case characterizations, not as predictions of operational false-positive rates." (p. 20, §VIII-H)
- The benchmark covers English, single-turn prompts only (p. 19, §VIII-A). The mechanism claim is a hypothesis; feature evidence covers only the linear model (p. 19, §VIII-F).

## Bibliographic entry (BibTeX)

```bibtex
@article{shire2026pidsbench,
  author  = {Shire, Yusuf Khalid and Kim, Sang-Chul},
  title   = {{PIDS-Bench}: Evaluating Prompt-Injection Detectors Under Over-Defense, Obfuscation, and Distribution Shift},
  journal = {IEEE Access},
  volume  = {14},
  pages   = {134184--134205},
  year    = {2026},
  doi     = {10.1109/ACCESS.2026.3728186},
  note    = {Published 28 Aug. 2026; current version 3 Sep. 2026. Metadata as printed on the PDF (p. 1 header, page folios); not cross-checked against IEEE Xplore}
}
```
