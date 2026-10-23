# Which Streets Should We Slow Down First?

Data and code for the study of decision robustness and evidence priorities for traffic-calming review.

## Reproduce the results

Python 3.10 or later is sufficient; all calculations use the standard library. From this directory:

```sh
python src/reproduce.py --out output
python tests/check_results.py --out output
python -m unittest discover -s tests -p 'test_*.py'
```

Choose a new output directory for each run. The result check compares every reproduced field with the full-precision reference values. Input and code checksums are in `checksums.json`.

## Contents and scope

| Evidence | Inputs | Reproduced results |
|---|---|---|
| Kentucky | Recorded window/reference quantiles, counts and passage-distribution summaries | Deployment and equal-deployment summaries for 15, 30, 60 and 120 minutes |
| Austin | 703 published entries and their July 2024 scores | Score-revision tipping points, membership bounds, exact transition paths, possible slot exchanges and conditional worst-case loss |
| Portland, observed | Fixed four-rule scores, common-cohort outcomes, model parameters and calibration residuals | K=5/10/20 comparisons for the primary cohort and three fixed sensitivities; selected sets and pairwise differences |
| Portland, model-based | 138 candidate distributions and 1,458 weighted predictive atoms | The exact one-query diagnostic and four equal-query-count policies, with a no-query baseline |

This is reproduction from finalized analytical summaries. Kentucky starts at the recorded-window level rather than individual radar trajectories. Portland uses the saved fitted model and scores; it does not retrain the model or rebuild the cohort. The files include the inputs needed to check those predictions and residual distributions. The repository contains neither manuscript production files nor imagery.

## Interpretation

Kentucky quantifies within-deployment differences between short recording windows and their containing reference periods, in **working km/h**. The windows overlap their references. Cross-site Kentucky allocation was **not evaluated**; r12 is an illustrative case and is separate from the nine primary deployments. r2/r10 and incomplete r21/r22 are excluded.

Austin's objective is a sum of **published program-score points**. Its guarantees and losses are conditional on independently bounded changes to the measured-speed component, a zero floor for that component, and the declared published-rank tie rule. The changes are scenarios, not estimated speed-measurement errors.

Portland's observed objective sums positive excess above an analytical **20 mph reference**, using the largest later p85 across each location's required directions. All four rules use the same whole-location cohort within each comparison. The query experiment instead uses an independent-location working predictive model and perfect revelation of one modeled future outcome. Its expected benefit is distinct from a measured benefit of a new survey. Exact ties, numerical cancellation, unchanged selections, null results and adverse comparisons are retained.

See [data definitions](docs/DATA.md) for keys, units and exclusions, and [sources](docs/SOURCES.md) for the municipal datasets and measurement context. The same tie seed and candidate keys are retained because changing either would change scientific tie outcomes.
