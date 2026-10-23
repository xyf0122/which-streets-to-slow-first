# Data dictionary

CSV files use UTF-8 headers; `.csv.gz` files are gzip-compressed CSVs. Empty cells mean not applicable or unavailable, never zero. Numeric strings retain full precision. `True`/`False` are Boolean flags. The reference results are compressed JSON containing the same keyed output fields used by the checks.

## Kentucky

- `windows.csv.gz`: one deployment/interval/duration/window. `window_id` is unique; `interval_id` identifies its containing recording interval and `reference_id` adds duration. `radar_id` is a deployment label, not a unique independent street. `scope` is primary or illustrative. `duration_minutes`, `actual_duration_seconds`, `full_window`, passage counts and `status` describe eligibility. Only eligible rows have window/reference quantiles and signed/absolute deviations, all in working km/h. Shared-passage fractions describe dependence on the containing reference. Local times are unzoned.
- `references.csv.gz`: one interval/duration. `span_seconds`, `passages` and `reference_eligible` implement the duration/count criteria. The stored p85 uses equal passage weights. Coverage status refers to export continuity, not certified sensor uptime.
- `passage_summary.csv`: one admitted interval. Counts, signed recorded-speed quantiles and counts of negative/zero passage medians describe the underlying retained passage summaries.

The nine primary labels are r1, r11, r13, r15, r16, r17, r18, r19 and r20. r12 is separate. Full windows comprise eligible, low-count and reference-ineligible windows; trailing partial windows are accounted for separately. Median and empirical quartiles summarize each deployment. Duration summaries give each deployment with support at all four durations equal weight.

## Austin

`candidates.csv.gz` contains published-entry key, published rank, street label, council district, crash/context/measured-speed/egregious-volume component scores, authoritative total, original highlight flag and PDF page. Keys such as `AUS202407:P01:R001` locate published rows. Units are program-score points throughout.

`config.json` fixes K=10 as primary, K=5/20 as context, and revision radii 0, 0.5, 1, 2 and 5 points. A candidate with total T and measured-speed component s has allowed total interval `[T − min(r,s), T + r]`. Higher totals precede lower totals; equal totals follow ascending published rank. `strict_infimum` means that equality does not change inclusion, whereas `attained` means it does. Individual best/worst ranks are separate attainable endpoints, not one simultaneous ranking. `max_simultaneous_exchanged_slots` and loss use one joint score vector. `exact_point` and `open_interval_after` preserve equality behavior on the transition path.

## Portland

- `scores.csv.gz`: `(scenario, method_id, candidate_id)` and the fixed score/tie hash. Rules are `latest`, `history`, `predictive_mean` (calibrated mean) and `empirical_uncertainty` (empirical expected severity). `primary` and `availability_30d` identify score inputs; the other two sensitivity cohorts reuse primary scores.
- `observed_outcomes.csv.gz`: `(scenario, candidate_id)`, matching support/directions and source study keys. `Y` is maximum later p85 in mph across required directions. `S=max(0,Y−20)` is the nonnegative reference excess. Study dates and limit/exception comparison fields describe the fixed cohort.
- `features.csv.gz`: initial features for benchmark candidates. L is largest latest directional p85; H is largest directional age-weighted historical median (three-year half-life). `log1p_A=log(1+A)`, with A the largest latest age in years; N is log(1+minimum directional study count); V is largest directional weighted IQR; G is largest directional latest–history absolute difference; B indicates one required direction. Speed features use mph. Study/source keys are provenance identifiers, not predictors.
- `model.json`: saved standardized ridge coefficients, intercept, training means/SDs, penalty 10 and empirical residual laws for each input scenario. Feature order is explicit. Intercept is unpenalized. No refitting is performed by the reproduction command.
- `calibration.csv.gz`: location, historical episode, 1 km grouping cell, age band, historical outcome, prediction and residual. Residual is observed minus predicted mph. Residual laws weight cells equally, then locations within each cell; the age boundary is three years.
- `uncertainty.csv.gz`: f_i is the saved predicted later maximum p85; mu_i is prediction plus weighted mean residual. P_i clips mu_i−20 at zero. U_i averages individually clipped residual-shifted predictions. delta_i=U_i−P_i; threshold-crossing and residual-set fields explain differences. Tiny signed cancellation values are retained.
- `query_candidates.csv.gz`: 138 primary locations, mean severity `m_i`, variance, evidence age A, residual set, support, study keys and exact tie hash. Variance uses translation invariance when all predictive atoms are at/above the reference; `severity_variance_direct` retains the direct calculation.
- `query_atoms.csv.gz`: 1,458 candidate/residual combinations. `atom_id` links the residual set and calibration location. `f_i`, `residual` and positive `weight` generate `hypothetical_Y=f_i+residual` and `hypothetical_S=max(0,hypothetical_Y−20)`. Atoms are model-generated future outcomes, not newly observed terminal measurements.

`PT:LEG…` keys retain the municipal measurement-location identity and deterministic tie order. They are essential computational keys. `support_key` is a matching identifier, not a surveyed street boundary. Selection order is descending exact score, then SHA-256 of `TRA_METHOD_V01|candidate_id`, then candidate ID; no tolerance groups scores into ties.

Observed capture is selected S divided by the common observed cohort sum. Hindsight uses the largest observed S values; regret is the difference in sums (or divided by K for per-review regret). The model-based query denominator is the sum of expected candidate severities, not the observed 811 primary-cohort total. Query gains, probability of a selection change and expected slot exchanges are distinct outputs. The 22-way maximum-variance tie, six positive alternatives and the fixed tied choice are retained.
