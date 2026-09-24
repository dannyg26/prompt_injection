# EvoShield overlap resolution
Date: 2026-09-23. Published-design question resolved; independent author reply pending.

**Verdict.** No: in the published design, EvoShield does not report an equal-label-budget comparison of decision-threshold adjustment, generic additional training data and domain-matched additional training data. Sections 4.1-4.2 describe online LLM supervision; Tables 4-5 vary routing/replay settings, Table 6 ablates routing/review, and Table 8 studies an ordered dataset shift. Its routing threshold controls escalation to an external LLM, not the binary decision threshold of a frozen classifier. It remains close prior work on adaptation, but does not establish duplication of this specific comparison. This finding is not a global novelty claim.

Primary source: [publisher article](https://www.mdpi.com/2227-7390/14/10/1719), DOI [10.3390/math14101719](https://doi.org/10.3390/math14101719).

## Evidence and access log

- Publisher-indexed article body retrieved through web search on 2026-09-23, including methods, experimental setup, results sections 5.1-5.4, table descriptions and references. This was substantially more text than the abstract-only access in the initial audit. It was not a successful local PDF download.
- Main comparisons and sweeps were checked against the three requested arms. No generic-vs-matched data allocation arm or equal human-label budget was reported there.
- Direct publisher HTML/PDF/XML and three public publisher-CDN PDF paths still returned access errors. Do not claim a locally verified PDF.
- Exact-title/arXiv-restricted searches found no verified alternative arXiv manuscript.
- Institutional-domain and corresponding-author searches found no verified institutional full-text copy.
- [Semantic Scholar DOI lookup](https://api.semanticscholar.org/graph/v1/paper/DOI:10.3390/math14101719?fields=title,authors,openAccessPdf,url) succeeded; its open-access pointer leads back to the publisher DOI, not an independent manuscript.
- Publisher correspondence field identifies **Zhenlu Wu, zlwu@gdou.edu.cn**. The institutional attribution is Guangdong Ocean University.
- Author inquiry is prepared in [EVOSHIELD_EMAIL.eml](EVOSHIELD_EMAIL.eml). **NOT SENT**: no sending account is connected. No reply is claimed.
- The publisher version history lists an update on 21 May 2026. The comparison above concerns the currently indexed article; an unindexed supplement or subsequent revision is not ruled out.

No model training, adaptation or detector scoring was performed during this resolution. Data audits and mathematical design calculations are separate. The remaining launch blockers are source permissions/provenance, annotation staffing and adequate independent evaluation counts. If the author identifies an overlooked matching experiment, reopen the novelty decision before any model run.
