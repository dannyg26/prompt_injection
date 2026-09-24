# PIDS-Bench direct-reading confirmation

The audit used the full [arXiv HTML manuscript v1](https://arxiv.org/html/2609.15017v1), not only the abstract landing page. The body was reread, including sections 6.3, 7.6 (Future Directions) and 8(d) (partial mitigation). The quoted 21-word sentence occurs in the abstract embedded in that full manuscript:

> Whether augmentation matched to the externally-sourced distribution would close this gap is untested; threshold calibration and curated-style augmentation alone do not.

The longer surrounding paragraph is not reproduced here (copyright). Summary of its context: the paper distinguishes strong ordinary benchmark results from false blocking of difficult legitimate text; its curated benign augmentation transfers poorly to externally sourced content, and calibration alone does not repair the separation. In the body, section 7.6 explicitly distinguishes distribution-matched augmentation from merely enlarging the curated pool, and identifies controlled source-holdout retraining as another untested design. The source analysis already presented is observational. Section 8(d) likewise frames augmentation as a diagnostic intervention, not a solved defense.

This is an author-stated gap within PIDS-Bench, not evidence that no other paper studied adaptation. Follow the full-text link to view the exact surrounding paragraph.
