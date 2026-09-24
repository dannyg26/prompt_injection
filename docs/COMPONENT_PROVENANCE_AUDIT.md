# Primary-pool provenance and license audit
Date: 2026-09-23. **Adoption decision: HOLD both merged releases pending component-level clearance and row mapping.** Downloads were inspected for metadata/counts/overlap only; none were used for model fitting or scoring. Repository/card labels are evidence of declarations, not proof that all upstream material is relicensed.

## Pinned public artifacts and actual counts

| Artifact | Revision | Actual inspected counts / fields |
| --- | --- | --- |
| [PromptShield](https://huggingface.co/datasets/hendzh/PromptShield) | `a5234cb1f5cdb256600cab64b8c961195b5e8404` | train 18,909 (9,457 benign/9,452 positive); validation 1,000 (497/503); test 23,516 (17,030/6,486). All rows expose only prompt/label. |
| [InjecGuard train.json](https://github.com/InjecGuard/InjecGuard/blob/main/datasets/train.json) | `cb1531f36bffb38b6493438217b36cda8875da8a` | 76,735 (61,069 benign/15,666 positive), prompt/label/source; 22 distinct source strings |
| InjecGuard valid.json, same revision | same | 144 rows; includes BIPIA, NotInject, WildGuard and PINT subsets. It is not an independent clean development set for tests on those same sources. |

The InjecGuard paper's base-pool total is 76,755. The downloaded file differs by 20 benign records; reason **UNVERIFIED**. File hashes and counts are archived. Do not substitute paper totals for the actual release.

## Cross-pool exact overlap

NFKC/case/whitespace-normalized text hashing found these PromptShield rows also in InjecGuard training:

| PromptShield split | Overlapping rows | Distinct overlapping texts | Rows with any cross-pool label conflict |
| --- | ---: | ---: | ---: |
| Train | 472 | 472 | 0 |
| Validation | 20 | 20 | 0 |
| Test | 479 | 455 | 1 |

Source-hit counts may exceed rows because one text appears under multiple InjecGuard sources. These are exhaustive counts for the pinned snapshots, not sampled performance metrics. The paper's best-effort non-overlap statement does not establish non-overlap for these files. Versions/compositions may differ; no misconduct is inferred. [Count ledger](../results/planning/provenance_counts.json).

## PromptShield components

[Paper Table 1 and §3.1](https://arxiv.org/html/2501.15145v2) identify the families below. Actual row-to-component assignment is absent from the public files; request or reconstruct a provenance map with exact upstream IDs, then audit transformed parents.

| Component | Primary evidence / terms | Decision |
| --- | --- | --- |
| Alpaca, including transformed descendants | [Stanford DATA_LICENSE/README](https://github.com/tatsu-lab/stanford_alpaca): data CC-BY-NC-4.0; code differs | Conditional research-only candidate; preserve attribution and derivative lineage |
| Ultrachat | Exact version UNVERIFIED; [H4 ultrachat_200k](https://huggingface.co/datasets/HuggingFaceH4/ultrachat_200k) declares MIT, but do not silently equate versions | Recover version and row origins |
| LMSYS-Chat-1M | [Primary agreement](https://huggingface.co/datasets/lmsys/lmsys-chat-1m) includes no-third-party-transfer provision and access terms | Exclude/unavailable pending a compliant provenance/permission path; outer Apache label is insufficient |
| Databricks Dolly | [Official card](https://huggingface.co/datasets/databricks/databricks-dolly-15k): CC-BY-SA-3.0 | Conditional candidate; preserve share-alike/attribution obligations and source IDs |
| Natural Instructions | [Official repository](https://github.com/allenai/natural-instructions); many underlying tasks; inspected HF derivative has no license field | Audit task-specific data terms and version; aggregate coverage UNVERIFIED |
| Synthetic Python Problems (SPP) | Exact upstream release/rights not resolved | UNVERIFIED, not adopted |
| IFEval | Exact selected source artifact/data terms not resolved | UNVERIFIED, not adopted |
| HackAPrompt | [Official HF card](https://huggingface.co/datasets/hackaprompt/hackaprompt-dataset): MIT declaration, current gated access | Verify selected release and access terms; no gated terms accepted |
| FourAttacks/StruQ and OpenPromptInject descendants | Transformed source data retain parent provenance/terms | Method/code license does not clear parent texts; recover source/template lineage |

## Every InjecGuard source string

Counts are benign/positive in the pinned file. The source field gives a first-level provenance label, not original-row IDs or complete template ancestry.

| Source | Counts 0/1 | Terms / provenance finding | Adoption gate |
| --- | --- | --- | --- |
| Alpaca | 4000/0 | CC-BY-NC-4.0 data, not Apache code | Research-only, attribution, source IDs |
| chatbot_instruction_prompts | 16000/0 | [Card](https://huggingface.co/datasets/alespalla/chatbot_instruction_prompts) declares Apache-2.0 but lists Alpaca, Dahoas and Prosocial-Dialog parents | Nested-license mismatch unresolved; recover parent IDs |
| open-instruct | 12000/0 | [VMware card](https://huggingface.co/datasets/VMware/open-instruct) declares CC-BY-3.0 and lists CC-BY-SA-3.0, CDLA-Sharing and other components | Preserve component source/task metadata; includes Dolly, so exclude target overlap |
| xtest-v2-copy | 450/0 | Source naming differs from paper xstest; exact derivative retrieval failed | UNVERIFIED |
| grok-conversation-harmless | 4000/0 | [H4 card](https://huggingface.co/datasets/HuggingFaceH4/grok-conversation-harmless): Apache-2.0 | Recover row IDs and validate benign construct |
| prompt-injections | 343/203 | [deepset card](https://huggingface.co/datasets/deepset/prompt-injections): Apache-2.0 | Legacy only; exclude all these rows from the primary study |
| safe-guard-prompt-injection | 5740/2496 | [Card](https://huggingface.co/datasets/xTRam1/safe-guard-prompt-injection) has no license declaration; names multiple nested sources | UNVERIFIED aggregate terms; hold |
| awesome-chatgpt-prompts | 170/0 | [Official card](https://huggingface.co/datasets/fka/awesome-chatgpt-prompts): CC0-1.0 | Candidate after context/provenance audit |
| no_robots | 1500/0 | [H4 card](https://huggingface.co/datasets/HuggingFaceH4/no_robots): CC-BY-NC-4.0 | Conditional non-commercial research candidate |
| ultrachat_200k | 3000/0 | [H4 card](https://huggingface.co/datasets/HuggingFaceH4/ultrachat_200k): MIT | Shared with PromptShield; group/exclude across partitions |
| TaskTracker | 11386/3316 | Source is named in paper; exact data release/terms/parent IDs unresolved | UNVERIFIED; do not substitute repository license |
| BIPIA | 558/558 | [Primary license](https://github.com/microsoft/BIPIA/blob/main/LICENSE) has explicit component exceptions | Recover originating task/doc/table; not blanket MIT |
| jailbreak-classification | 517/527 | [Card](https://huggingface.co/datasets/jackhhao/jailbreak-classification): Apache-2.0, with jailbreak_llms/OpenOrca/GPTeacher parents | Nested terms plus jailbreak-vs-injection construct need audit |
| Question Set | 643/1643 | Ambiguous source name, paper references Shen et al. | Exact artifact/terms UNVERIFIED |
| over-defense | 762/0 | Author-generated augmentation | Generation/version manifest and explicit data terms needed |
| InjecAgent | 0/111 | Task-derived contexts with injection labels | Exact component terms and parent context IDs UNVERIFIED |
| StruQ | 0/20 | Task-data transformation | Parent data rights/IDs UNVERIFIED |
| LLM Augmented set | 0/435 | Author-generated formats | Data terms/generation lineage UNVERIFIED |
| Prompt-Injection-Mixed-Techniques | 0/1174 | Referenced HF endpoint returned 401 | UNVERIFIED; no mirror substituted |
| ChatGPT-Jailbreak-Prompts | 0/79 | [Card](https://huggingface.co/datasets/rubend18/ChatGPT-Jailbreak-Prompts) has no license field | UNVERIFIED plus construct mismatch |
| vigil-jailbreak-ada-002 | 0/104 | [Card](https://huggingface.co/datasets/deadbits/vigil-jailbreak-ada-002) has no license field | UNVERIFIED plus construct mismatch |
| hackaprompt-dataset | 0/5000 | MIT declared, access currently gated | Verify exact selected version/lineage and access terms |

## Rebuilt study pools

Deepset's 627 records are legacy diagnostics only. PromptShield and InjecGuard are the two primary **candidate collections**, not two automatically independent domains. Build one joint manifest with collection, component, original ID, task, delivery boundary, parent document/template, license and derivative chain. Remove exact/semantic/template overlap across the whole graph before selecting S/T/U and adaptation/evaluation pools.

Candidate domain mapping: S generic instruction/conversation tasks; T natural-language document/application tasks (Dolly/Natural-Instructions components); U code tasks (SPP). Train/source calibration and generic-label additions use only approved S components; target B labels come from a separate T bank; U supplies no adaptation labels. Confirmatory target evaluation is fixed and as large as permitted independent data allow. This map remains provisional because missing provenance must not be invented from text style alone.

By the end of week 2, every admitted component needs auditable terms and origin; otherwise exclude it and recalculate usable class/group counts. Do not train a conveniently available merged dataset and postpone the audit until publication. Current permission/provenance gaps are a real blocker, not a completed clearance.
