# Study 2 Part A results (locked run)

Commit `a93623d08bd2866dde5170eb74c91687b622fa27`.

| Metric | Row split | Group split | Inflation | 95% CI (Nadeau-Bengio) |
| --- | ---: | ---: | ---: | --- |
| auroc | 0.996 | 0.971 | +0.025 | [+0.022, +0.028] |
| recall_at_1pct_fpr|pooled | 0.934 | 0.746 | +0.188 | [+0.170, +0.207] |
| recall_at_1pct_fpr|hackaprompt-dataset | 1.000 | 0.052 | +0.948 | [+0.929, +0.967] |
| recall_at_1pct_fpr|jailbreak-classification | 0.884 | 0.870 | +0.014 | [-0.023, +0.051] |
| recall_at_1pct_fpr|TaskTracker | 0.845 | 0.803 | +0.042 | [+0.008, +0.076] |
| recall_at_1pct_fpr|BIPIA | 0.912 | 0.832 | +0.080 | [+0.038, +0.122] |

| Attack source | Design effect median | Range | Defined repeats |
| --- | ---: | --- | ---: |
| hackaprompt-dataset | n/a | n/a | 0 |
| jailbreak-classification | 1.5 | [1.1, 1.7] | 20 |
| TaskTracker | 1.5 | [1.4, 1.6] | 20 |
| BIPIA | 2.3 | [1.6, 2.5] | 20 |

| Held-out HackAPrompt template | Rows | Recall at 1% FPR |
| --- | ---: | ---: |
| g:2553c4aa575363250f66 | 678 | 0.000 |
| g:2df28917cef47215d71d | 769 | 0.589 |
| g:39d9ced4ea7d351bd1b2 | 305 | 1.000 |
| g:4dd9ff1709c9f2dbe669 | 195 | 0.031 |
| g:5193198376a2b96b65c2 | 597 | 0.330 |
| g:d36c64c4ff13e462676b | 2219 | 0.826 |
| g:ee4efb8674a6f2cd1f00 | 96 | 0.000 |
