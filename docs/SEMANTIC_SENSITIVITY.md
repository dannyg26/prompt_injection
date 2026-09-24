# Embedding-based split sensitivity
Completed 2026-09-23 on **627 legacy deepset records only**. No detector was fitted or scored. No primary split was replaced.

Model: [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2), Apache-2.0 model card, revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. Frozen ONNX CPU inference; attention-masked mean pooling, 256-wordpiece chunks with 32-token overlap, weighted chunk averaging and L2 normalization. Long-record tails are included. Exact all-pairs cosine search, not approximate nearest neighbors. Prespecified sensitivity thresholds .85/.90/.95 were not chosen from classifier outcomes.

| Cosine cutoff | Candidate pairs | Additional redundant records removed in sensitivity | Additional mixed-label records quarantined | Retained | New train/val/test counts | Cross-split candidate pairs, old seed 42 |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| .85 | 39 | 28 | 21 | 578 | 380 / 96 / 102 | 19 |
| .90 | 15 | 11 | 8 | 608 | 400 / 101 / 107 | 8 |
| .95 | 0 | 0 | 0 | 627 | 412 / 105 / 110 | 0 |

Connected components and representative/quarantine rules follow the lexical audit. At .90, seed 42 loses three old test records through collapsing/quarantine; re-stratification changes the partition of 286 retained IDs and retains 38 old test IDs in the new test. That large membership change is mostly the effect of **reshuffling after curation**, not evidence of 286 semantic duplicates. At .85 the corresponding counts are 10 removed old test IDs, 283 retained IDs changing partition and 25 shared test IDs.

All split seeds **17,29,42,71,101** are recorded in [machine-readable results](../results/semantic/sensitivity.json), with candidate IDs, component ledgers, model/data/embedding hashes and the exact script archive. The .95 condition reproduces original membership for all seeds. Counts enumerate this fixed corpus, so no sampling confidence interval is claimed for them.

These are **candidate merges**, not human-confirmed paraphrase equivalence. Embeddings can confuse similar subject matter with the same instruction, and can miss short matching spans within long documents. Mixed-label cases may be legitimate contextual distinctions rather than label errors. Human review is required before adopting semantic groups. No duplicate-detection precision/recall or IAA was measured.

The audit demonstrates that the earlier lexical checks do not exhaust plausible overlap. The larger PromptShield/InjecGuard corpora still require a separate semantic/provenance audit after permissions and row origins are resolved. For those corpora, preserve document, attack-instance and template IDs, use batched similarity candidate retrieval, validate candidates independently, and freeze grouping before modeling. Do not describe today's 627-row sensitivity as full-corpus decontamination.
