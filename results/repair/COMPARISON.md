# Data repair: before/after audit

The original scores are WITHDRAWN. They appear below only for the requested audit comparison.
All intervals are two-sided 95% Wilson. Historical intervals are nominal and do not remedy leakage.
The before/after test sets differ, so changes cannot be attributed solely to leakage removal.

## Seed 42 comparison (split seed = model seed)

| Features | Before recall (withdrawn) | After recall | Before FPR (withdrawn) | After FPR |
| --- | --- | --- | --- | --- |
| word | 73.3% [61.0, 82.9] | 76.2% [61.5, 86.5] | 1.8% [0.3, 9.4] | 4.4% [1.5, 12.2] |
| char | 78.3% [66.4, 86.9] | 83.3% [69.4, 91.7] | 1.8% [0.3, 9.4] | 2.9% [0.8, 10.1] |
| combined | 80.0% [68.2, 88.2] | 81.0% [66.7, 90.0] | 1.8% [0.3, 9.4] | 2.9% [0.8, 10.1] |

## All prescribed seeds

Seeds were set to 17, 29, 42, 71, 101 before fitting; none selected on performance.
| Seed | Features | Test N | TP/FN/FP/TN | Recall [95% CI] | FPR [95% CI] |
| --- | --- | ---: | --- | --- | --- |
| 17 | word | 110 | 33/9/10/58 | 78.6% [64.1, 88.3] | 14.7% [8.2, 25.0] |
| 17 | char | 110 | 34/8/3/65 | 81.0% [66.7, 90.0] | 4.4% [1.5, 12.2] |
| 17 | combined | 110 | 35/7/5/63 | 83.3% [69.4, 91.7] | 7.4% [3.2, 16.1] |
| 29 | word | 110 | 34/8/3/65 | 81.0% [66.7, 90.0] | 4.4% [1.5, 12.2] |
| 29 | char | 110 | 37/5/4/64 | 88.1% [75.0, 94.8] | 5.9% [2.3, 14.2] |
| 29 | combined | 110 | 38/4/6/62 | 90.5% [77.9, 96.2] | 8.8% [4.1, 17.9] |
| 42 | word | 110 | 32/10/3/65 | 76.2% [61.5, 86.5] | 4.4% [1.5, 12.2] |
| 42 | char | 110 | 35/7/2/66 | 83.3% [69.4, 91.7] | 2.9% [0.8, 10.1] |
| 42 | combined | 110 | 34/8/2/66 | 81.0% [66.7, 90.0] | 2.9% [0.8, 10.1] |
| 71 | word | 110 | 25/17/3/65 | 59.5% [44.5, 73.0] | 4.4% [1.5, 12.2] |
| 71 | char | 110 | 29/13/1/67 | 69.0% [54.0, 80.9] | 1.5% [0.3, 7.9] |
| 71 | combined | 110 | 29/13/1/67 | 69.0% [54.0, 80.9] | 1.5% [0.3, 7.9] |
| 101 | word | 110 | 36/6/6/62 | 85.7% [72.2, 93.3] | 8.8% [4.1, 17.9] |
| 101 | char | 110 | 39/3/10/58 | 92.9% [81.0, 97.5] | 14.7% [8.2, 25.0] |
| 101 | combined | 110 | 39/3/11/57 | 92.9% [81.0, 97.5] | 16.2% [9.3, 26.7] |

The operating point remains the original 5% empirical validation FPR budget to keep the
baseline recipe fixed during repair. These are not results at 1% FPR. The proposed larger
study uses a different, prespecified operating point and has not been run.

See baselines.json for counts, seeds, thresholds, hashes and limitations; see
deduplication-audit.json for every component and removal decision.
