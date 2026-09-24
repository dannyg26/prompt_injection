# Explicit sample-size analysis
Draft v0.3, 2026-09-23. These are hypothetical analytical design calculations, **not detector performance measurements**. No experimental seeds or sampling confidence intervals apply to deterministic calculated power. All assumptions below must be checked before a confirmatory claim.

## Three separate questions

1. Precision of an FPR estimate near 1%.
2. Power to compare paired, fixed-threshold predictions.
3. Power to compare recall at a 1% ROC cutoff estimated from data.

They have different sample requirements. A 95% confidence level specifies type-I error, not an 80% or 90% probability of detecting a real effect. ?Separate? means a paired difference interval excludes zero; marginal intervals need not be nonoverlapping.

## FPR precision

For a first approximation, n_negative = z_(.975)^2 p(1-p)/h^2, where p=.01 and h is desired absolute half-width.

| Desired approximate half-width | Required negatives, normal planning approximation |
| --- | ---: |
| 0.5 percentage points | 1,522 |
| 0.3 percentage points | 4,226 |
| 0.2 percentage points | 9,508 |

For hypothetical observed FPR exactly 1%, two-sided Wilson 95% intervals are:

| Independent negatives | Hypothetical false positives | Wilson interval |
| --- | ---: | --- |
| 1,500 | 15 | 0.607%-1.643% |
| 2,000 | 20 | 0.648%-1.540% |
| 5,000 | 50 | 0.759%-1.316% |
| 10,000 | 100 | 0.823%-1.215% |

Thus 1,500 is a reasonable approximate starting point for a coarse 1% estimate, not certification below 1% or universal comparative power. With 68 negatives, the empirical grid is 1/68 = 1.47 percentage points: zero observed errors is the only attainable value at or below 1%. It does not imply true FPR zero. No extra seeds change that grid for a fixed evaluation pool.

## Paired fixed-threshold comparisons

For one class, let b=P(A wrong, B right), c=P(A right, B wrong), delta=b-c and q=b+c. Each independent item is evaluated by both systems. Then Var(difference)=(q-delta^2)/n. A normal planning approximation is:

n ~= [z_(1-alpha/2)*sqrt(q) + z_power*sqrt(q-delta^2)]^2 / delta^2.

For recall, n means **positives**; for FPR, n means **negatives**. The effect size alone cannot determine n: disagreement q is required.

The implemented calculation checks sufficient N against exact conditional two-sided McNemar rejection probabilities, averaged over D~Binomial(n,q). Given D, the directional count is Binomial(D,(q+delta)/(2q)). N is rounded upward in 25-item steps; these are sufficient designs under the assumptions, not claimed exact minima. [NCSS technical procedure](https://www.ncss.com/wp-content/themes/ncss/pdf/Procedures/PASS/Tests_for_Two_Correlated_Proportions-McNemar_Test.pdf), [statsmodels test definition](https://www.statsmodels.org/stable/generated/statsmodels.stats.contingency_tables.mcnemar.html).

| Recall difference | Discordance q | Positives: 80% power, alpha=.05 | Positives: 90% power, alpha=.05 | Positives: 90% power, alpha=.025 |
| --- | --- | ---: | ---: | ---: |
| 2 points | .10 | 2,050 | 2,700 | 3,175 |
| 2 points | .20 | 4,025 | 5,350 | 6,300 |
| 3 points | .10 | 925 | 1,225 | 1,425 |
| 3 points | .20 | 1,800 | 2,400 | 2,825 |
| 5 points | .10 | 350 | 450 | 525 |
| 5 points | .20 | 675 | 875 | 1,025 |

Alpha=.025 allows two prespecified contrasts to share a familywise .05 error budget using Bonferroni; corresponding individual confidence intervals are 97.5%. This supersedes the old four-contrast confirmatory plan: third-domain analyses are descriptive unless separately powered.

| Hypothetical FPR change | Conservative possible q for these marginals | Negatives: 80% power, alpha=.05 | Negatives: 90% power, alpha=.05 | Negatives: 90% power, alpha=.025 |
| --- | --- | ---: | ---: | ---: |
| 3% to 1% (2 points) | .04 | 850 | 1,100 | 1,275 |
| 6% to 1% (5 points) | .07 | 250 | 300 | 350 |
| 1% to 0.5% (0.5 points) | .015 | 5,000 | 6,550 | 7,650 |

A 2-5-point FPR reduction cannot start from 1%; distinguish reducing elevated FPR to 1% from resolving small differences near 1%.

## Recall at an estimated 1% ROC cutoff costs more negatives

The previous table conditions on fixed thresholds. For empirical recall@1%FPR the cutoff itself is uncertain. Under a smooth-score model, a paired delta-method variance is:

V = (q_positive-delta^2)/n_positive + C_negative/n_negative,

where C_negative = (lambda_A^2+lambda_B^2)*f*(1-f) - 2*lambda_A*lambda_B*Cov(I_A_negative,I_B_negative), f=.01 and lambda_j = positive score density / negative score density at its cutoff. Steep ROC slopes magnify negative-tail uncertainty. This also explains why positive counts alone cannot power this endpoint.

Illustration only: both models have unit-variance Gaussian scores; baseline recall .80 at population FPR .01; paired score correlation .90 within both classes; n_positive=6,500; alpha=.025. Positive means are set to yield the stated recall difference. Numerical quadrature calculates joint tail probabilities without Monte Carlo.

| Recall difference | Required negatives: approximate 80% power | Required negatives: approximate 90% power |
| --- | ---: | ---: |
| 2 points | 35,212 | 55,416 |
| 3 points | 11,589 | 16,055 |
| 5 points | 3,518 | 4,680 |

These are **model-dependent sensitivity calculations**, not empirically established power. At a 2-point effect, changing score correlation to .99 gives about 8,536 negatives for 80% power; correlation .50 requires about 211,787 with the same 6,500 positives. No universal claim follows from a single correlation assumption. The JSON contains all scenarios.

## Decision and limitations

Keep adaptation B small and evaluation separate. Reserve all permitted, independent public evaluation groups; aim for roughly 10,000 negatives and 5,000 positives in the target if available after exclusions. That is a planning target, not proof of 2-point ROC-effect power. A 5-point effect is more plausible to resolve within current public-pool scale; a 2-point recall@1%FPR claim needs stronger justified correlation/ROC-slope assumptions or more data. Do not merge unrelated domains simply to meet counts.

For a frozen-threshold conditional 2-point recall comparison, q<=.20 and 90% power with two contrasts require about 6,300 independent positives. Test-informed ROC thresholds require the additional analysis above. Public PromptShield's raw 6,486 positives are not 6,486 verified independent target-domain positives.

All counts assume independent paired units. Shared documents/templates require grouping; average cluster size m and intra-cluster correlation r give the rough design-effect warning 1+(m-1)r, not a license to treat correlated rows as independent. Uncertain labels and source mixture further limit inference. The calculations also omit between-training-seed variation: a training-procedure claim needs that variance estimated on a source-only pilot and a joint seed/group analysis. Do not pool seeds as additional test cases.

The previous hypothesis demanded a lower bound above a five-point margin while contemplating a true effect as small as five points. That cannot be powered like a test against zero. Revised statistical superiority tests zero; a two-point practical-relevance margin is assessed separately. An upper interval below two points rules out that meaningful effect; an interval crossing the margin is inconclusive.

Reproducibility: [script](../scripts/power_analysis.py), [all analytical outputs](../results/planning/power.json). Tests compare the power calculation against independent finite binomial-test enumeration and an exact boundary case. No detector was fitted.
