# R4 robustness definitive analysis (R4.7-R4.10)

Inputs: `results/r4_robustness/{pmodel,capacity,backdate,sla}/results.csv` and the Eval-B empirical anchors at crew multiplier 1.0 from `results/r4_final/results.csv`. Statistics: `fmwos.stats`, protocol §R4.5, 10000 bootstrap resamples over base-instance clusters, master seed 12345, equivalence margin max(1.0, 1% of the comparator mean). Rank correlations are Kendall tau-b (`scipy.stats.kendalltau`). A negative paired difference means the method is better than its comparator.

Scoring: 17 methods, all of them run on every configuration of every arm (7 transparent rules and the 10 policy seeds, each seed ranked individually). Strata: verdict = verdict campuses (5, 9, 10, 12); campus1 = campus 1 (transfer); campus2 = campus 2 (nonstationary overload). Campus 2 never enters a verdict scope.


How to read a low `tau_method`: on these anchors the 17 methods sit within a fraction of a per cent of each other, and the equivalence margin is wider than that whole spread, so the pairwise ORDER of the methods is not identified. Every stability row therefore carries `spread_pct` (the worst mean over the best mean) and `margin_pct_of_best` (the margin as a share of the best mean) next to the rank correlation.


## 0. Run sizes

| check | protocol | n_rows | n_configs | n_anchors | n_methods | n_arms | n_infeasible | n_errors | n_verdict | n_campus1 | n_campus2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| evalb_anchors | R4.4 | 3859 | 227 | 227 | 17 | 1 | 0 | 0 | 180 | 30 | 17 |
| pmodel | R4.7 | 11560 | 680 | 227 | 17 | 3 | 0 | 0 | 539 | 90 | 51 |
| capacity | R4.8 | 7718 | 454 | 227 | 17 | 2 | 0 | 0 | 360 | 60 | 34 |
| backdate | R4.9 | 3859 | 227 | 227 | 17 | 1 | 0 | 0 | 180 | 30 | 17 |
| sla | R4.10 | 11577 | 681 | 227 | 17 | 3 | 0 | 0 | 540 | 90 | 51 |


## Processing-time model (R4.7)

Endpoint: does the method-family ranking survive the line-aggregation choice?


Calibration cascade (portfolio rows of `calib_summary.csv`); capacity is recalibrated per model, which is what keeps realized utilization comparable across the three arms.

| p_model | work_orders | r4_labor_cap_hours | n_trades | total_technicians | mean_p_bh | median_p_bh | pm_share |
|---|---|---|---|---|---|---|---|
| sum | 1454039 | 90.865 | 68 | 687 | 3.219 | 1.000 | 0.616 |
| max | 1454039 | 43.881 | 68 | 491 | 2.361 | 1.000 | 0.616 |
| single | 1316010 | 40.000 | 65 | 396 | 2.135 | 1.000 | 0.623 |


Per campus:

| p_model | campus | work_orders | n_trades | total_technicians | mean_p_bh |
|---|---|---|---|---|---|
| sum | 1 | 125637 | 11 | 94 | 3.590 |
| sum | 2 | 40567 | 7 | 38 | 6.279 |
| sum | 5 | 393669 | 11 | 116 | 3.312 |
| sum | 9 | 144114 | 13 | 99 | 3.704 |
| sum | 10 | 608217 | 13 | 154 | 2.085 |
| sum | 12 | 137058 | 13 | 186 | 6.073 |
| max | 1 | 125637 | 11 | 80 | 3.275 |
| max | 2 | 40567 | 7 | 24 | 3.967 |
| max | 5 | 393669 | 11 | 106 | 3.102 |
| max | 9 | 144114 | 13 | 87 | 3.417 |
| max | 10 | 608217 | 13 | 111 | 1.203 |
| max | 12 | 137058 | 13 | 83 | 2.846 |
| single | 1 | 124139 | 11 | 75 | 3.137 |
| single | 2 | 29959 | 7 | 14 | 1.803 |
| single | 5 | 393669 | 11 | 106 | 3.070 |
| single | 9 | 136347 | 13 | 82 | 3.162 |
| single | 10 | 548087 | 12 | 91 | 1.069 |
| single | 12 | 79325 | 11 | 28 | 1.531 |


What the recalibration holds fixed. The three models change how much work an order carries, so without the table below a reader cannot tell whether a change in weighted tardiness is the aggregation choice or a change of contention regime (`pmodel_utilization.csv`):

| arm | stratum | n_configs | mean_technicians | u_mean | u_median | u_max | share_u_over_one |
|---|---|---|---|---|---|---|---|
| sum | verdict | 180 | 149.167 | 0.777 | 0.521 | 5.990 | 0.167 |
| sum | campus1 | 30 | 94.000 | 0.687 | 0.499 | 3.011 | 0.133 |
| sum | campus2 | 17 | 38.000 | 1.356 | 1.233 | 2.903 | 0.765 |
| max | verdict | 180 | 96.833 | 0.793 | 0.553 | 6.795 | 0.172 |
| max | campus1 | 30 | 80.000 | 0.754 | 0.562 | 3.538 | 0.167 |
| max | campus2 | 17 | 24.000 | 1.315 | 1.146 | 2.839 | 0.765 |
| single | verdict | 179 | 71.240 | 0.751 | 0.507 | 7.305 | 0.145 |
| single | campus1 | 30 | 75.000 | 0.782 | 0.555 | 3.773 | 0.167 |
| single | campus2 | 17 | 14.000 | 0.660 | 0.451 | 2.236 | 0.235 |


### Stability against the summed line hours (v1 default) arm

| arm | stratum | n_configs | n_anchors | best_method | best_mean | spread_pct | margin_pct_of_best | tau_method | tau_family | set_size | baseline_set_size | set_jaccard | left_set | entered_set | n_policy_seeds_in_set | top3_families | top3_is_leading_trio |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sum | verdict | 180 | 180 | v2rl302 | 444.681 | 0.442 | 1.000 | 1.000 | 1.000 | 17 | 17 | 1.000 | - | - | 10 | duedate policy weighted | 1 |
| sum | campus1 | 30 | 30 | atc | 80.417 | 1.094 | 1.244 | 1.000 | 1.000 | 15 | 15 | 1.000 | - | - | 10 | duedate policy weighted | 1 |
| sum | campus2 | 17 | 17 | wmdd | 1218.229 | 114.665 | 1.000 | 1.000 | 1.000 | 1 | 1 | 1.000 | - | - | 0 | duedate random weighted | 0 |
| max | verdict | 180 | 180 | v2rl310 | 64.927 | 58.405 | 1.540 | 0.644 | 0.800 | 1 | 17 | 0.059 | atc edd lpt pfifo random v2rl301 v2rl302 v2rl303 v2rl304 v2rl305 v2rl306 v2rl307 v2rl308 v2rl309 wmdd wspt | - | 1 | duedate policy weighted | 1 |
| max | campus1 | 30 | 30 | atc | 40.504 | 2.172 | 2.469 | 1.000 | 0.778 | 16 | 15 | 0.938 | - | random | 10 | duedate policy weighted | 1 |
| max | campus2 | 17 | 17 | wmdd | 444.208 | 385.936 | 1.000 | 0.733 | 0.800 | 1 | 1 | 1.000 | - | - | 0 | duedate policy weighted | 1 |
| single | verdict | 179 | 179 | wmdd | 17.193 | 355.630 | 5.816 | -0.037 | 0.200 | 2 | 17 | 0.118 | edd lpt pfifo random v2rl301 v2rl302 v2rl303 v2rl304 v2rl305 v2rl306 v2rl307 v2rl308 v2rl309 v2rl310 wspt | - | 0 | duedate policy weighted | 1 |
| single | campus1 | 30 | 30 | atc | 31.180 | 3.746 | 3.207 | 1.000 | 0.778 | 16 | 15 | 0.938 | - | random | 10 | duedate policy weighted | 1 |
| single | campus2 | 17 | 17 | atc | 0.000 | - | - | 0.325 | 0.598 | 15 | 1 | 0.067 | - | atc edd pfifo v2rl301 v2rl302 v2rl303 v2rl304 v2rl305 v2rl306 v2rl307 v2rl308 v2rl309 v2rl310 wspt | 10 | duedate policy weighted | 1 |


Family means (mean of the member methods' means) and the family order they imply:

| arm | stratum | mean_duedate | mean_weighted | mean_processing | mean_random | mean_policy | family_order |
|---|---|---|---|---|---|---|---|
| sum | verdict | 444.869 | 445.444 | 446.112 | 446.316 | 444.769 | policy>duedate>weighted>processing>random |
| sum | campus1 | 80.417 | 80.417 | 80.857 | 81.121 | 80.417 | policy>duedate>weighted>processing>random |
| sum | campus2 | 1311.322 | 1235.172 | 1953.175 | 1636.031 | 1649.863 | weighted>duedate>random>policy>processing |
| max | verdict | 66.352 | 66.874 | 86.829 | 82.211 | 66.308 | policy>duedate>weighted>random>processing |
| max | campus1 | 40.504 | 40.504 | 40.944 | 40.785 | 40.504 | policy>duedate>weighted>random>processing |
| max | campus2 | 530.673 | 461.616 | 1367.269 | 1004.701 | 813.486 | weighted>duedate>policy>random>processing |
| single | verdict | 20.088 | 17.360 | 49.057 | 42.751 | 21.791 | weighted>duedate>policy>random>processing |
| single | campus1 | 31.180 | 31.180 | 31.765 | 31.189 | 31.180 | policy>duedate>weighted>random>processing |
| single | campus2 | 0.000 | 0.000 | 18.172 | 6.412 | 0.000 | duedate>weighted>policy>random>processing |


Per-arm method table (rules in bold positions, policy seeds ranked individually):


**sum / verdict** (summed line hours (v1 default)) - best v2rl302 (mean 444.681), 180 configurations. Equivalence set: 17 of 17 methods.

| rank | method | family | mean | pct_from_best | abs_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | v2rl302 | policy | 444.681 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 4.447 | equivalent | 1 |
| 2 | v2rl308 | policy | 444.708 | 0.006 | 0.027 | 0.027 | 0.000 | 0.065 | 4.447 | equivalent | 1 |
| 3 | v2rl310 | policy | 444.712 | 0.007 | 0.031 | 0.031 | -0.003 | 0.083 | 4.447 | equivalent | 1 |
| 4 | v2rl303 | policy | 444.731 | 0.011 | 0.050 | 0.050 | 0.000 | 0.130 | 4.447 | equivalent | 1 |
| 5 | v2rl301 | policy | 444.756 | 0.017 | 0.075 | 0.075 | 0.014 | 0.159 | 4.447 | equivalent | 1 |
| 6 | v2rl305 | policy | 444.760 | 0.018 | 0.079 | 0.079 | 0.011 | 0.180 | 4.447 | equivalent | 1 |
| 7 | v2rl304 | policy | 444.763 | 0.018 | 0.082 | 0.082 | -0.002 | 0.195 | 4.447 | equivalent | 1 |
| 8 | v2rl307 | policy | 444.770 | 0.020 | 0.089 | 0.089 | 0.012 | 0.183 | 4.447 | equivalent | 1 |
| 9 | v2rl306 | policy | 444.859 | 0.040 | 0.178 | 0.178 | 0.007 | 0.484 | 4.447 | equivalent | 1 |
| 10 | edd | duedate | 444.869 | 0.042 | 0.188 | 0.188 | 0.023 | 0.406 | 4.447 | equivalent | 1 |
| 10 | pfifo | duedate | 444.869 | 0.042 | 0.188 | 0.188 | 0.027 | 0.404 | 4.447 | equivalent | 1 |
| 12 | v2rl309 | policy | 444.953 | 0.061 | 0.272 | 0.272 | 0.030 | 0.635 | 4.447 | equivalent | 1 |
| 13 | wmdd | weighted | 445.332 | 0.146 | 0.651 | 0.651 | 0.165 | 1.274 | 4.447 | equivalent | 1 |
| 14 | atc | weighted | 445.555 | 0.197 | 0.874 | 0.874 | 0.263 | 1.641 | 4.447 | equivalent | 1 |
| 15 | lpt | processing | 445.579 | 0.202 | 0.898 | 0.898 | 0.074 | 2.438 | 4.447 | equivalent | 1 |
| 16 | random | random | 446.316 | 0.368 | 1.635 | 1.635 | 0.572 | 3.181 | 4.447 | equivalent | 1 |
| 17 | wspt | processing | 446.646 | 0.442 | 1.965 | 1.965 | 0.891 | 3.312 | 4.447 | equivalent | 1 |


**sum / campus1** (summed line hours (v1 default)) - best atc (mean 80.417), 30 configurations. Equivalence set: 15 of 17 methods.

| rank | method | family | mean | pct_from_best | abs_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | atc | weighted | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | edd | duedate | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | lpt | processing | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | pfifo | duedate | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl301 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl302 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl303 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl304 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl305 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl306 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl307 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl308 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl309 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl310 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | wmdd | weighted | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 16 | random | random | 81.121 | 0.875 | 0.704 | 0.704 | 0.000 | 1.775 | 1.000 | inconclusive | 0 |
| 17 | wspt | processing | 81.297 | 1.094 | 0.880 | 0.880 | 0.000 | 2.293 | 1.000 | inconclusive | 0 |


**sum / campus2** (summed line hours (v1 default)) - best wmdd (mean 1218.229), 17 configurations. Equivalence set: 1 of 17 methods.

| rank | method | family | mean | pct_from_best | abs_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | wmdd | weighted | 1218.229 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 12.182 | equivalent | 1 |
| 2 | atc | weighted | 1252.116 | 2.782 | 33.887 | 33.887 | 12.321 | 59.462 | 12.182 | worse | 0 |
| 3 | wspt | processing | 1291.239 | 5.993 | 73.010 | 73.010 | 35.217 | 113.926 | 12.182 | worse | 0 |
| 4 | edd | duedate | 1311.322 | 7.642 | 93.093 | 93.093 | -17.248 | 242.406 | 12.182 | inconclusive | 0 |
| 4 | pfifo | duedate | 1311.322 | 7.642 | 93.093 | 93.093 | -16.389 | 241.693 | 12.182 | inconclusive | 0 |
| 6 | v2rl310 | policy | 1324.889 | 8.755 | 106.660 | 106.660 | 9.846 | 226.410 | 12.182 | inconclusive | 0 |
| 7 | v2rl302 | policy | 1420.451 | 16.600 | 202.223 | 202.223 | 67.394 | 367.774 | 12.182 | worse | 0 |
| 8 | v2rl304 | policy | 1447.724 | 18.838 | 229.495 | 229.495 | 33.037 | 520.343 | 12.182 | worse | 0 |
| 9 | v2rl309 | policy | 1453.006 | 19.272 | 234.777 | 234.777 | 57.100 | 525.791 | 12.182 | worse | 0 |
| 10 | v2rl308 | policy | 1494.215 | 22.655 | 275.986 | 275.986 | 15.248 | 683.838 | 12.182 | worse | 0 |
| 11 | random | random | 1636.031 | 34.296 | 417.802 | 417.802 | 215.398 | 661.251 | 12.182 | worse | 0 |
| 12 | v2rl305 | policy | 1720.644 | 41.241 | 502.415 | 502.415 | 188.441 | 917.362 | 12.182 | worse | 0 |
| 13 | v2rl307 | policy | 1751.246 | 43.753 | 533.018 | 533.018 | 193.128 | 968.132 | 12.182 | worse | 0 |
| 14 | v2rl301 | policy | 1851.252 | 51.963 | 633.023 | 633.023 | 225.055 | 1116.052 | 12.182 | worse | 0 |
| 15 | v2rl306 | policy | 1863.508 | 52.969 | 645.279 | 645.279 | 260.127 | 1105.504 | 12.182 | worse | 0 |
| 16 | v2rl303 | policy | 2171.693 | 78.266 | 953.464 | 953.464 | 451.924 | 1507.926 | 12.182 | worse | 0 |
| 17 | lpt | processing | 2615.112 | 114.665 | 1396.883 | 1396.883 | 683.108 | 2224.134 | 12.182 | worse | 0 |


**max / verdict** (dominant line's own hours) - best v2rl310 (mean 64.927), 180 configurations. Equivalence set: 1 of 17 methods.

| rank | method | family | mean | pct_from_best | abs_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | v2rl310 | policy | 64.927 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 2 | v2rl301 | policy | 65.873 | 1.457 | 0.946 | 0.946 | -0.073 | 2.579 | 1.000 | inconclusive | 0 |
| 3 | v2rl308 | policy | 65.875 | 1.460 | 0.948 | 0.948 | -0.122 | 2.597 | 1.000 | inconclusive | 0 |
| 4 | v2rl304 | policy | 66.028 | 1.695 | 1.100 | 1.100 | 0.469 | 1.897 | 1.000 | inconclusive | 0 |
| 5 | v2rl303 | policy | 66.125 | 1.844 | 1.197 | 1.197 | -0.184 | 3.569 | 1.000 | inconclusive | 0 |
| 6 | v2rl305 | policy | 66.153 | 1.887 | 1.225 | 1.225 | -0.159 | 3.616 | 1.000 | inconclusive | 0 |
| 7 | v2rl307 | policy | 66.233 | 2.011 | 1.306 | 1.306 | -0.144 | 3.837 | 1.000 | inconclusive | 0 |
| 8 | edd | duedate | 66.352 | 2.194 | 1.425 | 1.425 | 0.235 | 3.011 | 1.000 | inconclusive | 0 |
| 8 | pfifo | duedate | 66.352 | 2.194 | 1.425 | 1.425 | 0.244 | 3.051 | 1.000 | inconclusive | 0 |
| 10 | v2rl302 | policy | 66.440 | 2.330 | 1.513 | 1.513 | -0.010 | 4.107 | 1.000 | inconclusive | 0 |
| 11 | atc | weighted | 66.845 | 2.954 | 1.918 | 1.918 | 0.621 | 3.952 | 1.000 | inconclusive | 0 |
| 12 | wmdd | weighted | 66.903 | 3.043 | 1.976 | 1.976 | 0.676 | 3.905 | 1.000 | inconclusive | 0 |
| 13 | v2rl306 | policy | 67.505 | 3.970 | 2.578 | 2.578 | 0.425 | 5.581 | 1.000 | inconclusive | 0 |
| 14 | v2rl309 | policy | 67.918 | 4.607 | 2.991 | 2.991 | 0.823 | 6.052 | 1.000 | inconclusive | 0 |
| 15 | wspt | processing | 70.811 | 9.061 | 5.883 | 5.883 | 2.525 | 10.417 | 1.000 | worse | 0 |
| 16 | random | random | 82.211 | 26.620 | 17.284 | 17.284 | 7.589 | 29.152 | 1.000 | worse | 0 |
| 17 | lpt | processing | 102.848 | 58.405 | 37.921 | 37.921 | 15.207 | 69.507 | 1.000 | worse | 0 |


**max / campus1** (dominant line's own hours) - best atc (mean 40.504), 30 configurations. Equivalence set: 16 of 17 methods.

| rank | method | family | mean | pct_from_best | abs_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | atc | weighted | 40.504 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | edd | duedate | 40.504 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | lpt | processing | 40.504 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | pfifo | duedate | 40.504 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl301 | policy | 40.504 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl302 | policy | 40.504 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl303 | policy | 40.504 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl304 | policy | 40.504 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl305 | policy | 40.504 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl306 | policy | 40.504 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl307 | policy | 40.504 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl308 | policy | 40.504 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl309 | policy | 40.504 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl310 | policy | 40.504 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | wmdd | weighted | 40.504 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 16 | random | random | 40.785 | 0.694 | 0.281 | 0.281 | 0.000 | 0.707 | 1.000 | equivalent | 1 |
| 17 | wspt | processing | 41.384 | 2.172 | 0.880 | 0.880 | 0.000 | 2.293 | 1.000 | inconclusive | 0 |


**max / campus2** (dominant line's own hours) - best wmdd (mean 444.208), 17 configurations. Equivalence set: 1 of 17 methods.

| rank | method | family | mean | pct_from_best | abs_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | wmdd | weighted | 444.208 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 4.442 | equivalent | 1 |
| 2 | atc | weighted | 479.024 | 7.838 | 34.816 | 34.816 | 5.409 | 68.556 | 4.442 | worse | 0 |
| 3 | v2rl308 | policy | 511.780 | 15.212 | 67.572 | 67.572 | 1.480 | 151.600 | 4.442 | inconclusive | 0 |
| 4 | v2rl310 | policy | 523.635 | 17.881 | 79.427 | 79.427 | 6.948 | 173.653 | 4.442 | worse | 0 |
| 5 | edd | duedate | 530.673 | 19.465 | 86.466 | 86.466 | -4.164 | 232.809 | 4.442 | inconclusive | 0 |
| 5 | pfifo | duedate | 530.673 | 19.465 | 86.466 | 86.466 | -3.945 | 233.649 | 4.442 | inconclusive | 0 |
| 7 | v2rl304 | policy | 573.661 | 29.143 | 129.454 | 129.454 | 19.082 | 273.052 | 4.442 | worse | 0 |
| 8 | wspt | processing | 575.975 | 29.663 | 131.767 | 131.767 | 59.095 | 210.080 | 4.442 | worse | 0 |
| 9 | v2rl302 | policy | 632.397 | 42.365 | 188.190 | 188.190 | 55.005 | 345.313 | 4.442 | worse | 0 |
| 10 | v2rl309 | policy | 643.229 | 44.804 | 199.021 | 199.021 | 84.922 | 331.073 | 4.442 | worse | 0 |
| 11 | v2rl305 | policy | 905.096 | 103.755 | 460.889 | 460.889 | 140.576 | 866.131 | 4.442 | worse | 0 |
| 12 | v2rl301 | policy | 942.267 | 112.123 | 498.059 | 498.059 | 155.496 | 930.176 | 4.442 | worse | 0 |
| 13 | v2rl307 | policy | 960.469 | 116.221 | 516.262 | 516.262 | 182.665 | 913.275 | 4.442 | worse | 0 |
| 14 | random | random | 1004.701 | 126.178 | 560.494 | 560.494 | 310.850 | 842.690 | 4.442 | worse | 0 |
| 15 | v2rl306 | policy | 1031.470 | 132.204 | 587.262 | 587.262 | 173.361 | 1093.218 | 4.442 | worse | 0 |
| 16 | v2rl303 | policy | 1410.861 | 217.613 | 966.653 | 966.653 | 397.427 | 1622.415 | 4.442 | worse | 0 |
| 17 | lpt | processing | 2158.563 | 385.936 | 1714.356 | 1714.356 | 844.353 | 2743.384 | 4.442 | worse | 0 |


**single / verdict** (single-line orders only) - best wmdd (mean 17.193), 179 configurations. Equivalence set: 2 of 17 methods.

| rank | method | family | mean | pct_from_best | abs_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | wmdd | weighted | 17.193 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 2 | atc | weighted | 17.526 | 1.933 | 0.332 | 0.332 | -0.126 | 0.969 | 1.000 | equivalent | 1 |
| 3 | v2rl304 | policy | 17.929 | 4.278 | 0.736 | 0.736 | 0.092 | 1.625 | 1.000 | inconclusive | 0 |
| 4 | v2rl308 | policy | 19.196 | 11.646 | 2.002 | 2.002 | 0.130 | 4.739 | 1.000 | inconclusive | 0 |
| 5 | wspt | processing | 19.775 | 15.017 | 2.582 | 2.582 | 1.207 | 4.529 | 1.000 | worse | 0 |
| 6 | edd | duedate | 20.088 | 16.837 | 2.895 | 2.895 | 0.031 | 7.177 | 1.000 | inconclusive | 0 |
| 6 | pfifo | duedate | 20.088 | 16.837 | 2.895 | 2.895 | 0.037 | 7.343 | 1.000 | inconclusive | 0 |
| 8 | v2rl310 | policy | 20.092 | 16.859 | 2.899 | 2.899 | -0.019 | 8.321 | 1.000 | inconclusive | 0 |
| 9 | v2rl309 | policy | 20.287 | 17.991 | 3.093 | 3.093 | 0.067 | 8.581 | 1.000 | inconclusive | 0 |
| 10 | v2rl302 | policy | 21.548 | 25.328 | 4.355 | 4.355 | -0.108 | 12.235 | 1.000 | inconclusive | 0 |
| 11 | v2rl305 | policy | 23.095 | 34.325 | 5.902 | 5.902 | 0.005 | 14.415 | 1.000 | inconclusive | 0 |
| 12 | v2rl307 | policy | 23.356 | 35.841 | 6.162 | 6.162 | 0.092 | 15.167 | 1.000 | inconclusive | 0 |
| 13 | v2rl301 | policy | 23.785 | 38.336 | 6.591 | 6.591 | 0.002 | 16.077 | 1.000 | inconclusive | 0 |
| 14 | v2rl303 | policy | 24.107 | 40.213 | 6.914 | 6.914 | 0.049 | 17.187 | 1.000 | inconclusive | 0 |
| 15 | v2rl306 | policy | 24.516 | 42.591 | 7.323 | 7.323 | 0.251 | 17.696 | 1.000 | inconclusive | 0 |
| 16 | random | random | 42.751 | 148.648 | 25.558 | 25.558 | 8.811 | 52.106 | 1.000 | worse | 0 |
| 17 | lpt | processing | 78.338 | 355.630 | 61.145 | 61.145 | 15.337 | 140.266 | 1.000 | worse | 0 |


**single / campus1** (single-line orders only) - best atc (mean 31.180), 30 configurations. Equivalence set: 16 of 17 methods.

| rank | method | family | mean | pct_from_best | abs_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | atc | weighted | 31.180 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | edd | duedate | 31.180 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | lpt | processing | 31.180 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | pfifo | duedate | 31.180 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl301 | policy | 31.180 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl302 | policy | 31.180 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl303 | policy | 31.180 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl304 | policy | 31.180 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl305 | policy | 31.180 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl306 | policy | 31.180 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl307 | policy | 31.180 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl308 | policy | 31.180 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl309 | policy | 31.180 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl310 | policy | 31.180 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | wmdd | weighted | 31.180 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 16 | random | random | 31.189 | 0.028 | 0.009 | 0.009 | 0.000 | 0.027 | 1.000 | equivalent | 1 |
| 17 | wspt | processing | 32.349 | 3.746 | 1.168 | 1.168 | 0.000 | 2.937 | 1.000 | inconclusive | 0 |


**single / campus2** (single-line orders only) - best atc (mean 0.000), 17 configurations. Equivalence set: 15 of 17 methods.

| rank | method | family | mean | pct_from_best | abs_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | atc | weighted | 0.000 | - | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | edd | duedate | 0.000 | - | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | pfifo | duedate | 0.000 | - | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl301 | policy | 0.000 | - | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl302 | policy | 0.000 | - | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl303 | policy | 0.000 | - | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl304 | policy | 0.000 | - | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl305 | policy | 0.000 | - | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl306 | policy | 0.000 | - | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl307 | policy | 0.000 | - | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl308 | policy | 0.000 | - | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl309 | policy | 0.000 | - | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl310 | policy | 0.000 | - | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | wmdd | weighted | 0.000 | - | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | wspt | processing | 0.000 | - | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 16 | random | random | 6.412 | - | 6.412 | 6.412 | 0.000 | 18.818 | 1.000 | inconclusive | 0 |
| 17 | lpt | processing | 36.344 | - | 36.344 | 36.344 | 4.523 | 76.341 | 1.000 | worse | 0 |


## Capacity estimator (R4.8)

Endpoint: do the conclusions depend on the crew-sizing quantile, or on the realized utilization it produces?


Realized utilization per estimator quantile and stratum (`capacity_utilization.csv`):

| arm | stratum | n_configs | u_mean | u_median | u_p25 | u_p75 | u_max | share_u_over_one | u_shift_mean | u_shift_median |
|---|---|---|---|---|---|---|---|---|---|---|
| q0.95 | verdict | 180 | 0.777 | 0.521 | 0.341 | 0.786 | 5.990 | 0.167 | 0.000 | 0.000 |
| q0.95 | campus1 | 30 | 0.687 | 0.499 | 0.353 | 0.717 | 3.011 | 0.133 | 0.000 | 0.000 |
| q0.95 | campus2 | 17 | 1.356 | 1.233 | 1.025 | 1.410 | 2.903 | 0.765 | 0.000 | 0.000 |
| q0.90 | verdict | 180 | 0.950 | 0.610 | 0.436 | 0.939 | 7.232 | 0.228 | 0.173 | 0.087 |
| q0.90 | campus1 | 30 | 0.808 | 0.586 | 0.414 | 0.843 | 3.538 | 0.167 | 0.120 | 0.087 |
| q0.90 | campus2 | 17 | 1.717 | 1.562 | 1.299 | 1.786 | 3.677 | 0.941 | 0.362 | 0.329 |
| q0.75 | verdict | 180 | 1.312 | 0.820 | 0.617 | 1.233 | 10.981 | 0.361 | 0.535 | 0.306 |
| q0.75 | campus1 | 30 | 1.077 | 0.781 | 0.553 | 1.123 | 4.717 | 0.333 | 0.390 | 0.283 |
| q0.75 | campus2 | 17 | 2.711 | 2.466 | 2.051 | 2.820 | 5.805 | 1.000 | 1.356 | 1.233 |


Realized vs nominal crew multipliers, portfolio (`capacity_multipliers.csv`); rounding a per-trade crew to a whole technician is what separates the two.

| m | crew_nominal | crew_realized | realized_multiplier |
|---|---|---|---|
| 0.500 | 687 | 344 | 0.501 |
| 0.600 | 687 | 413 | 0.601 |
| 0.800 | 687 | 546 | 0.795 |
| 1.000 | 687 | 687 | 1.000 |
| 1.250 | 687 | 855 | 1.244 |


### Stability against the p95 of weekly trade hours (Eval-B default) arm

| arm | stratum | n_configs | n_anchors | best_method | best_mean | spread_pct | margin_pct_of_best | tau_method | tau_family | set_size | baseline_set_size | set_jaccard | left_set | entered_set | n_policy_seeds_in_set | top3_families | top3_is_leading_trio |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| q0.95 | verdict | 180 | 180 | v2rl302 | 444.681 | 0.442 | 1.000 | 1.000 | 1.000 | 17 | 17 | 1.000 | - | - | 10 | duedate policy weighted | 1 |
| q0.95 | campus1 | 30 | 30 | atc | 80.417 | 1.094 | 1.244 | 1.000 | 1.000 | 15 | 15 | 1.000 | - | - | 10 | duedate policy weighted | 1 |
| q0.95 | campus2 | 17 | 17 | wmdd | 1218.229 | 114.665 | 1.000 | 1.000 | 1.000 | 1 | 1 | 1.000 | - | - | 0 | duedate random weighted | 0 |
| q0.90 | verdict | 180 | 180 | v2rl301 | 446.138 | 0.778 | 1.000 | 0.644 | 0.800 | 15 | 17 | 0.882 | lpt random | - | 10 | duedate policy weighted | 1 |
| q0.90 | campus1 | 30 | 30 | atc | 80.417 | 1.453 | 1.244 | 1.000 | 0.778 | 15 | 15 | 1.000 | - | - | 10 | duedate policy weighted | 1 |
| q0.90 | campus2 | 17 | 17 | wmdd | 1417.144 | 192.765 | 1.000 | 0.911 | 1.000 | 1 | 1 | 1.000 | - | - | 0 | duedate random weighted | 0 |
| q0.75 | verdict | 180 | 180 | v2rl310 | 456.303 | 7.271 | 1.000 | 0.363 | 0.400 | 6 | 17 | 0.353 | edd lpt pfifo random v2rl301 v2rl305 v2rl306 v2rl307 v2rl308 v2rl309 wspt | - | 4 | duedate policy weighted | 1 |
| q0.75 | campus1 | 30 | 30 | v2rl304 | 80.477 | 2.677 | 1.243 | 0.531 | 0.333 | 14 | 15 | 0.933 | lpt | - | 10 | duedate policy weighted | 1 |
| q0.75 | campus2 | 17 | 17 | atc | 2830.055 | 454.150 | 1.000 | 0.731 | 1.000 | 1 | 1 | 0.000 | wmdd | atc | 0 | duedate random weighted | 0 |


Family means (mean of the member methods' means) and the family order they imply:

| arm | stratum | mean_duedate | mean_weighted | mean_processing | mean_random | mean_policy | family_order |
|---|---|---|---|---|---|---|---|
| q0.95 | verdict | 444.869 | 445.444 | 446.112 | 446.316 | 444.769 | policy>duedate>weighted>processing>random |
| q0.95 | campus1 | 80.417 | 80.417 | 80.857 | 81.121 | 80.417 | policy>duedate>weighted>processing>random |
| q0.95 | campus2 | 1311.322 | 1235.172 | 1953.175 | 1636.031 | 1649.863 | weighted>duedate>random>policy>processing |
| q0.90 | verdict | 446.523 | 447.192 | 449.259 | 448.965 | 446.270 | policy>duedate>weighted>random>processing |
| q0.90 | campus1 | 80.417 | 80.417 | 81.001 | 80.888 | 80.417 | policy>duedate>weighted>random>processing |
| q0.90 | campus2 | 1770.180 | 1448.726 | 2834.222 | 2333.274 | 2470.876 | weighted>duedate>random>policy>processing |
| q0.75 | verdict | 462.173 | 457.848 | 475.768 | 473.205 | 461.328 | weighted>policy>duedate>random>processing |
| q0.75 | campus1 | 80.478 | 80.478 | 81.873 | 81.393 | 80.527 | duedate>weighted>policy>random>processing |
| q0.75 | campus2 | 5625.282 | 2892.521 | 9324.480 | 7278.249 | 8115.341 | weighted>duedate>random>policy>processing |


Per-arm method table (rules in bold positions, policy seeds ranked individually):


**q0.95 / verdict** (p95 of weekly trade hours (Eval-B default)) - best v2rl302 (mean 444.681), 180 configurations. Equivalence set: 17 of 17 methods.

| rank | method | family | mean | pct_from_best | abs_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | v2rl302 | policy | 444.681 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 4.447 | equivalent | 1 |
| 2 | v2rl308 | policy | 444.708 | 0.006 | 0.027 | 0.027 | 0.000 | 0.065 | 4.447 | equivalent | 1 |
| 3 | v2rl310 | policy | 444.712 | 0.007 | 0.031 | 0.031 | -0.003 | 0.083 | 4.447 | equivalent | 1 |
| 4 | v2rl303 | policy | 444.731 | 0.011 | 0.050 | 0.050 | 0.000 | 0.130 | 4.447 | equivalent | 1 |
| 5 | v2rl301 | policy | 444.756 | 0.017 | 0.075 | 0.075 | 0.014 | 0.159 | 4.447 | equivalent | 1 |
| 6 | v2rl305 | policy | 444.760 | 0.018 | 0.079 | 0.079 | 0.011 | 0.180 | 4.447 | equivalent | 1 |
| 7 | v2rl304 | policy | 444.763 | 0.018 | 0.082 | 0.082 | -0.002 | 0.195 | 4.447 | equivalent | 1 |
| 8 | v2rl307 | policy | 444.770 | 0.020 | 0.089 | 0.089 | 0.012 | 0.183 | 4.447 | equivalent | 1 |
| 9 | v2rl306 | policy | 444.859 | 0.040 | 0.178 | 0.178 | 0.007 | 0.484 | 4.447 | equivalent | 1 |
| 10 | edd | duedate | 444.869 | 0.042 | 0.188 | 0.188 | 0.023 | 0.406 | 4.447 | equivalent | 1 |
| 10 | pfifo | duedate | 444.869 | 0.042 | 0.188 | 0.188 | 0.027 | 0.404 | 4.447 | equivalent | 1 |
| 12 | v2rl309 | policy | 444.953 | 0.061 | 0.272 | 0.272 | 0.030 | 0.635 | 4.447 | equivalent | 1 |
| 13 | wmdd | weighted | 445.332 | 0.146 | 0.651 | 0.651 | 0.165 | 1.274 | 4.447 | equivalent | 1 |
| 14 | atc | weighted | 445.555 | 0.197 | 0.874 | 0.874 | 0.263 | 1.641 | 4.447 | equivalent | 1 |
| 15 | lpt | processing | 445.579 | 0.202 | 0.898 | 0.898 | 0.074 | 2.438 | 4.447 | equivalent | 1 |
| 16 | random | random | 446.316 | 0.368 | 1.635 | 1.635 | 0.572 | 3.181 | 4.447 | equivalent | 1 |
| 17 | wspt | processing | 446.646 | 0.442 | 1.965 | 1.965 | 0.891 | 3.312 | 4.447 | equivalent | 1 |


**q0.95 / campus1** (p95 of weekly trade hours (Eval-B default)) - best atc (mean 80.417), 30 configurations. Equivalence set: 15 of 17 methods.

| rank | method | family | mean | pct_from_best | abs_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | atc | weighted | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | edd | duedate | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | lpt | processing | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | pfifo | duedate | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl301 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl302 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl303 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl304 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl305 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl306 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl307 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl308 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl309 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl310 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | wmdd | weighted | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 16 | random | random | 81.121 | 0.875 | 0.704 | 0.704 | 0.000 | 1.775 | 1.000 | inconclusive | 0 |
| 17 | wspt | processing | 81.297 | 1.094 | 0.880 | 0.880 | 0.000 | 2.293 | 1.000 | inconclusive | 0 |


**q0.95 / campus2** (p95 of weekly trade hours (Eval-B default)) - best wmdd (mean 1218.229), 17 configurations. Equivalence set: 1 of 17 methods.

| rank | method | family | mean | pct_from_best | abs_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | wmdd | weighted | 1218.229 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 12.182 | equivalent | 1 |
| 2 | atc | weighted | 1252.116 | 2.782 | 33.887 | 33.887 | 12.321 | 59.462 | 12.182 | worse | 0 |
| 3 | wspt | processing | 1291.239 | 5.993 | 73.010 | 73.010 | 35.217 | 113.926 | 12.182 | worse | 0 |
| 4 | edd | duedate | 1311.322 | 7.642 | 93.093 | 93.093 | -17.248 | 242.406 | 12.182 | inconclusive | 0 |
| 4 | pfifo | duedate | 1311.322 | 7.642 | 93.093 | 93.093 | -16.389 | 241.693 | 12.182 | inconclusive | 0 |
| 6 | v2rl310 | policy | 1324.889 | 8.755 | 106.660 | 106.660 | 9.846 | 226.410 | 12.182 | inconclusive | 0 |
| 7 | v2rl302 | policy | 1420.451 | 16.600 | 202.223 | 202.223 | 67.394 | 367.774 | 12.182 | worse | 0 |
| 8 | v2rl304 | policy | 1447.724 | 18.838 | 229.495 | 229.495 | 33.037 | 520.343 | 12.182 | worse | 0 |
| 9 | v2rl309 | policy | 1453.006 | 19.272 | 234.777 | 234.777 | 57.100 | 525.791 | 12.182 | worse | 0 |
| 10 | v2rl308 | policy | 1494.215 | 22.655 | 275.986 | 275.986 | 15.248 | 683.838 | 12.182 | worse | 0 |
| 11 | random | random | 1636.031 | 34.296 | 417.802 | 417.802 | 215.398 | 661.251 | 12.182 | worse | 0 |
| 12 | v2rl305 | policy | 1720.644 | 41.241 | 502.415 | 502.415 | 188.441 | 917.362 | 12.182 | worse | 0 |
| 13 | v2rl307 | policy | 1751.246 | 43.753 | 533.018 | 533.018 | 193.128 | 968.132 | 12.182 | worse | 0 |
| 14 | v2rl301 | policy | 1851.252 | 51.963 | 633.023 | 633.023 | 225.055 | 1116.052 | 12.182 | worse | 0 |
| 15 | v2rl306 | policy | 1863.508 | 52.969 | 645.279 | 645.279 | 260.127 | 1105.504 | 12.182 | worse | 0 |
| 16 | v2rl303 | policy | 2171.693 | 78.266 | 953.464 | 953.464 | 451.924 | 1507.926 | 12.182 | worse | 0 |
| 17 | lpt | processing | 2615.112 | 114.665 | 1396.883 | 1396.883 | 683.108 | 2224.134 | 12.182 | worse | 0 |


**q0.90 / verdict** (p90 of weekly trade hours) - best v2rl301 (mean 446.138), 180 configurations. Equivalence set: 15 of 17 methods.

| rank | method | family | mean | pct_from_best | abs_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | v2rl301 | policy | 446.138 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 4.461 | equivalent | 1 |
| 2 | v2rl305 | policy | 446.176 | 0.009 | 0.038 | 0.038 | -0.052 | 0.174 | 4.461 | equivalent | 1 |
| 3 | v2rl310 | policy | 446.184 | 0.010 | 0.046 | 0.046 | -0.075 | 0.183 | 4.461 | equivalent | 1 |
| 4 | v2rl307 | policy | 446.201 | 0.014 | 0.062 | 0.062 | -0.024 | 0.177 | 4.461 | equivalent | 1 |
| 5 | v2rl302 | policy | 446.203 | 0.014 | 0.065 | 0.065 | -0.052 | 0.256 | 4.461 | equivalent | 1 |
| 6 | v2rl303 | policy | 446.212 | 0.016 | 0.073 | 0.073 | -0.059 | 0.282 | 4.461 | equivalent | 1 |
| 7 | v2rl304 | policy | 446.252 | 0.025 | 0.114 | 0.114 | -0.028 | 0.305 | 4.461 | equivalent | 1 |
| 8 | v2rl308 | policy | 446.280 | 0.032 | 0.141 | 0.141 | -0.057 | 0.436 | 4.461 | equivalent | 1 |
| 9 | v2rl309 | policy | 446.457 | 0.071 | 0.319 | 0.319 | 0.005 | 0.802 | 4.461 | equivalent | 1 |
| 10 | edd | duedate | 446.523 | 0.086 | 0.385 | 0.385 | 0.048 | 0.852 | 4.461 | equivalent | 1 |
| 10 | pfifo | duedate | 446.523 | 0.086 | 0.385 | 0.385 | 0.051 | 0.836 | 4.461 | equivalent | 1 |
| 12 | v2rl306 | policy | 446.596 | 0.103 | 0.458 | 0.458 | -0.052 | 1.425 | 4.461 | equivalent | 1 |
| 13 | wmdd | weighted | 446.979 | 0.188 | 0.840 | 0.840 | 0.203 | 1.675 | 4.461 | equivalent | 1 |
| 14 | atc | weighted | 447.404 | 0.284 | 1.266 | 1.266 | 0.363 | 2.443 | 4.461 | equivalent | 1 |
| 15 | wspt | processing | 448.909 | 0.621 | 2.771 | 2.771 | 1.424 | 4.405 | 4.461 | equivalent | 1 |
| 16 | random | random | 448.965 | 0.634 | 2.827 | 2.827 | 1.103 | 5.204 | 4.461 | inconclusive | 0 |
| 17 | lpt | processing | 449.608 | 0.778 | 3.470 | 3.470 | 0.290 | 8.157 | 4.461 | inconclusive | 0 |


**q0.90 / campus1** (p90 of weekly trade hours) - best atc (mean 80.417), 30 configurations. Equivalence set: 15 of 17 methods.

| rank | method | family | mean | pct_from_best | abs_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | atc | weighted | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | edd | duedate | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | lpt | processing | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | pfifo | duedate | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl301 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl302 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl303 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl304 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl305 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl306 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl307 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl308 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl309 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl310 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | wmdd | weighted | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 16 | random | random | 80.888 | 0.585 | 0.470 | 0.470 | 0.000 | 1.407 | 1.000 | inconclusive | 0 |
| 17 | wspt | processing | 81.586 | 1.453 | 1.168 | 1.168 | 0.000 | 2.937 | 1.000 | inconclusive | 0 |


**q0.90 / campus2** (p90 of weekly trade hours) - best wmdd (mean 1417.144), 17 configurations. Equivalence set: 1 of 17 methods.

| rank | method | family | mean | pct_from_best | abs_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | wmdd | weighted | 1417.144 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 14.171 | equivalent | 1 |
| 2 | atc | weighted | 1480.309 | 4.457 | 63.165 | 63.165 | 25.939 | 106.332 | 14.171 | worse | 0 |
| 3 | wspt | processing | 1519.547 | 7.226 | 102.404 | 102.404 | 50.652 | 162.553 | 14.171 | worse | 0 |
| 4 | v2rl310 | policy | 1752.254 | 23.647 | 335.110 | 335.110 | 75.852 | 676.728 | 14.171 | worse | 0 |
| 5 | edd | duedate | 1770.180 | 24.912 | 353.036 | 353.036 | 59.682 | 749.418 | 14.171 | worse | 0 |
| 5 | pfifo | duedate | 1770.180 | 24.912 | 353.036 | 353.036 | 61.904 | 745.345 | 14.171 | worse | 0 |
| 7 | v2rl309 | policy | 1874.735 | 32.290 | 457.591 | 457.591 | 162.357 | 825.724 | 14.171 | worse | 0 |
| 8 | v2rl304 | policy | 1894.378 | 33.676 | 477.234 | 477.234 | 164.639 | 855.190 | 14.171 | worse | 0 |
| 9 | v2rl308 | policy | 2005.107 | 41.489 | 587.963 | 587.963 | 168.178 | 1089.477 | 14.171 | worse | 0 |
| 10 | v2rl302 | policy | 2029.856 | 43.236 | 612.713 | 612.713 | 161.836 | 1172.738 | 14.171 | worse | 0 |
| 11 | random | random | 2333.274 | 64.646 | 916.130 | 916.130 | 391.296 | 1541.471 | 14.171 | worse | 0 |
| 12 | v2rl305 | policy | 2760.573 | 94.798 | 1343.429 | 1343.429 | 536.026 | 2243.223 | 14.171 | worse | 0 |
| 13 | v2rl307 | policy | 2886.493 | 103.684 | 1469.349 | 1469.349 | 630.414 | 2404.560 | 14.171 | worse | 0 |
| 14 | v2rl301 | policy | 2976.173 | 110.012 | 1559.029 | 1559.029 | 676.035 | 2530.967 | 14.171 | worse | 0 |
| 15 | v2rl306 | policy | 3187.308 | 124.911 | 1770.164 | 1770.164 | 713.987 | 3022.790 | 14.171 | worse | 0 |
| 16 | v2rl303 | policy | 3341.883 | 135.818 | 1924.740 | 1924.740 | 908.007 | 3107.644 | 14.171 | worse | 0 |
| 17 | lpt | processing | 4148.896 | 192.765 | 2731.752 | 2731.752 | 1308.884 | 4366.366 | 14.171 | worse | 0 |


**q0.75 / verdict** (p75 of weekly trade hours) - best v2rl310 (mean 456.303), 180 configurations. Equivalence set: 6 of 17 methods.

| rank | method | family | mean | pct_from_best | abs_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | v2rl310 | policy | 456.303 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 4.563 | equivalent | 1 |
| 2 | v2rl302 | policy | 456.445 | 0.031 | 0.142 | 0.142 | -0.486 | 1.088 | 4.563 | equivalent | 1 |
| 3 | v2rl304 | policy | 456.675 | 0.081 | 0.372 | 0.372 | -0.022 | 0.819 | 4.563 | equivalent | 1 |
| 4 | v2rl303 | policy | 456.918 | 0.135 | 0.615 | 0.615 | -0.203 | 1.727 | 4.563 | equivalent | 1 |
| 5 | atc | weighted | 457.559 | 0.275 | 1.256 | 1.256 | -2.161 | 4.064 | 4.563 | equivalent | 1 |
| 6 | wmdd | weighted | 458.136 | 0.402 | 1.833 | 1.833 | 0.471 | 3.359 | 4.563 | equivalent | 1 |
| 7 | v2rl308 | policy | 458.376 | 0.454 | 2.073 | 2.073 | -0.149 | 6.233 | 4.563 | inconclusive | 0 |
| 8 | wspt | processing | 462.056 | 1.261 | 5.753 | 5.753 | 3.182 | 8.736 | 4.563 | inconclusive | 0 |
| 9 | edd | duedate | 462.173 | 1.286 | 5.870 | 5.870 | 0.243 | 14.636 | 4.563 | inconclusive | 0 |
| 9 | pfifo | duedate | 462.173 | 1.286 | 5.870 | 5.870 | 0.224 | 14.572 | 4.563 | inconclusive | 0 |
| 11 | v2rl301 | policy | 464.563 | 1.810 | 8.260 | 8.260 | -1.517 | 24.608 | 4.563 | inconclusive | 0 |
| 12 | v2rl307 | policy | 465.486 | 2.012 | 9.182 | 9.182 | -0.141 | 25.329 | 4.563 | inconclusive | 0 |
| 13 | v2rl305 | policy | 465.536 | 2.023 | 9.233 | 9.233 | -0.113 | 24.821 | 4.563 | inconclusive | 0 |
| 14 | v2rl306 | policy | 466.345 | 2.201 | 10.041 | 10.041 | 0.587 | 26.049 | 4.563 | inconclusive | 0 |
| 15 | v2rl309 | policy | 466.629 | 2.263 | 10.326 | 10.326 | 0.801 | 26.848 | 4.563 | inconclusive | 0 |
| 16 | random | random | 473.205 | 3.704 | 16.902 | 16.902 | 6.262 | 33.752 | 4.563 | worse | 0 |
| 17 | lpt | processing | 489.481 | 7.271 | 33.178 | 33.178 | 13.518 | 57.919 | 4.563 | worse | 0 |


**q0.75 / campus1** (p75 of weekly trade hours) - best v2rl304 (mean 80.477), 30 configurations. Equivalence set: 14 of 17 methods.

| rank | method | family | mean | pct_from_best | abs_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | v2rl304 | policy | 80.477 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl310 | policy | 80.477 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 3 | atc | weighted | 80.478 | 0.001 | 0.001 | 0.001 | 0.000 | 0.002 | 1.000 | equivalent | 1 |
| 3 | edd | duedate | 80.478 | 0.001 | 0.001 | 0.001 | 0.000 | 0.002 | 1.000 | equivalent | 1 |
| 3 | pfifo | duedate | 80.478 | 0.001 | 0.001 | 0.001 | 0.000 | 0.002 | 1.000 | equivalent | 1 |
| 3 | v2rl307 | policy | 80.478 | 0.001 | 0.001 | 0.001 | 0.000 | 0.002 | 1.000 | equivalent | 1 |
| 3 | v2rl308 | policy | 80.478 | 0.001 | 0.001 | 0.001 | 0.000 | 0.002 | 1.000 | equivalent | 1 |
| 3 | wmdd | weighted | 80.478 | 0.001 | 0.001 | 0.001 | 0.000 | 0.002 | 1.000 | equivalent | 1 |
| 9 | v2rl301 | policy | 80.545 | 0.084 | 0.067 | 0.067 | 0.000 | 0.202 | 1.000 | equivalent | 1 |
| 9 | v2rl302 | policy | 80.545 | 0.084 | 0.067 | 0.067 | 0.000 | 0.202 | 1.000 | equivalent | 1 |
| 9 | v2rl303 | policy | 80.545 | 0.084 | 0.067 | 0.067 | 0.000 | 0.202 | 1.000 | equivalent | 1 |
| 9 | v2rl305 | policy | 80.545 | 0.084 | 0.067 | 0.067 | 0.000 | 0.202 | 1.000 | equivalent | 1 |
| 9 | v2rl306 | policy | 80.545 | 0.084 | 0.067 | 0.067 | 0.000 | 0.202 | 1.000 | equivalent | 1 |
| 14 | v2rl309 | policy | 80.640 | 0.202 | 0.162 | 0.162 | 0.000 | 0.445 | 1.000 | equivalent | 1 |
| 15 | lpt | processing | 81.114 | 0.791 | 0.636 | 0.636 | 0.000 | 1.908 | 1.000 | inconclusive | 0 |
| 16 | random | random | 81.393 | 1.138 | 0.916 | 0.916 | 0.000 | 2.415 | 1.000 | inconclusive | 0 |
| 17 | wspt | processing | 82.632 | 2.677 | 2.155 | 2.155 | 0.000 | 5.157 | 1.000 | inconclusive | 0 |


**q0.75 / campus2** (p75 of weekly trade hours) - best atc (mean 2830.055), 17 configurations. Equivalence set: 1 of 17 methods.

| rank | method | family | mean | pct_from_best | abs_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | atc | weighted | 2830.055 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 28.301 | equivalent | 1 |
| 2 | wmdd | weighted | 2954.988 | 4.415 | 124.933 | 124.933 | -154.883 | 588.185 | 28.301 | inconclusive | 0 |
| 3 | wspt | processing | 2966.211 | 4.811 | 136.156 | 136.156 | 64.847 | 222.132 | 28.301 | worse | 0 |
| 4 | v2rl310 | policy | 4427.083 | 56.431 | 1597.028 | 1597.028 | 711.863 | 2635.106 | 28.301 | worse | 0 |
| 5 | v2rl308 | policy | 4722.222 | 66.860 | 1892.168 | 1892.168 | 909.601 | 2986.822 | 28.301 | worse | 0 |
| 6 | v2rl309 | policy | 5068.351 | 79.090 | 2238.297 | 2238.297 | 1237.959 | 3369.552 | 28.301 | worse | 0 |
| 7 | v2rl304 | policy | 5326.375 | 88.207 | 2496.320 | 2496.320 | 1140.380 | 3985.643 | 28.301 | worse | 0 |
| 8 | pfifo | duedate | 5620.576 | 98.603 | 2790.521 | 2790.521 | 1353.093 | 4368.123 | 28.301 | worse | 0 |
| 9 | edd | duedate | 5629.989 | 98.936 | 2799.934 | 2799.934 | 1376.219 | 4380.928 | 28.301 | worse | 0 |
| 10 | random | random | 7278.249 | 157.177 | 4448.194 | 4448.194 | 2681.510 | 6305.003 | 28.301 | worse | 0 |
| 11 | v2rl302 | policy | 7316.840 | 158.541 | 4486.786 | 4486.786 | 2001.480 | 7318.190 | 28.301 | worse | 0 |
| 12 | v2rl307 | policy | 10134.585 | 258.106 | 7304.530 | 7304.530 | 3837.636 | 11021.898 | 28.301 | worse | 0 |
| 13 | v2rl305 | policy | 10241.061 | 261.868 | 7411.006 | 7411.006 | 3826.584 | 11330.270 | 28.301 | worse | 0 |
| 14 | v2rl301 | policy | 10863.265 | 283.854 | 8033.210 | 8033.210 | 4172.917 | 12300.569 | 28.301 | worse | 0 |
| 15 | v2rl303 | policy | 11499.530 | 306.336 | 8669.476 | 8669.476 | 4634.718 | 13106.391 | 28.301 | worse | 0 |
| 16 | v2rl306 | policy | 11554.097 | 308.264 | 8724.042 | 8724.042 | 4502.694 | 13330.949 | 28.301 | worse | 0 |
| 17 | lpt | processing | 15682.750 | 454.150 | 12852.695 | 12852.695 | 7658.280 | 18449.292 | 28.301 | worse | 0 |


## Backdated releases (R4.9, synthetic)

Endpoint: does an earlier release proxy move the ranking or the equivalence set?


How much of the synthetic shift the instances absorb (`backdate_clamp.csv`): a shifted release is clamped at the start of the scheduling window, so a clamped order keeps its original release.

| stratum | n_configs | n_corrective | clamped_total | clamped_mean | clamped_median | clamped_min | clamped_max | clamp_share_corrective_pooled | delta_bh_mean | delta_bh_max |
|---|---|---|---|---|---|---|---|---|---|---|
| verdict | 180 | 22371 | 15040 | 83.556 | 81.500 | 0 | 267 | 0.672 | 15.467 | 85.694 |
| campus1 | 30 | 2542 | 1449 | 48.300 | 48.000 | 5 | 85 | 0.570 | 9.216 | 82.993 |
| campus2 | 17 | 1930 | 879 | 51.706 | 50.000 | 29 | 86 | 0.455 | 12.142 | 39.992 |


### Stability against the released timestamps (Eval-B) arm

| arm | stratum | n_configs | n_anchors | best_method | best_mean | spread_pct | margin_pct_of_best | tau_method | tau_family | set_size | baseline_set_size | set_jaccard | left_set | entered_set | n_policy_seeds_in_set | top3_families | top3_is_leading_trio |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | verdict | 180 | 180 | v2rl302 | 444.681 | 0.442 | 1.000 | 1.000 | 1.000 | 17 | 17 | 1.000 | - | - | 10 | duedate policy weighted | 1 |
| baseline | campus1 | 30 | 30 | atc | 80.417 | 1.094 | 1.244 | 1.000 | 1.000 | 15 | 15 | 1.000 | - | - | 10 | duedate policy weighted | 1 |
| baseline | campus2 | 17 | 17 | wmdd | 1218.229 | 114.665 | 1.000 | 1.000 | 1.000 | 1 | 1 | 1.000 | - | - | 0 | duedate random weighted | 0 |
| backdate | verdict | 180 | 180 | edd | 444.932 | 0.909 | 1.000 | 0.506 | 0.600 | 14 | 17 | 0.824 | lpt random wspt | - | 10 | duedate policy weighted | 1 |
| backdate | campus1 | 30 | 30 | v2rl304 | 80.425 | 0.746 | 1.243 | 0.539 | 0.527 | 16 | 15 | 0.938 | - | random | 10 | duedate policy random | 0 |
| backdate | campus2 | 17 | 17 | wmdd | 1265.913 | 161.643 | 1.000 | 0.837 | 1.000 | 1 | 1 | 1.000 | - | - | 0 | duedate random weighted | 0 |


Family means (mean of the member methods' means) and the family order they imply:

| arm | stratum | mean_duedate | mean_weighted | mean_processing | mean_random | mean_policy | family_order |
|---|---|---|---|---|---|---|---|
| baseline | verdict | 444.869 | 445.444 | 446.112 | 446.316 | 444.769 | policy>duedate>weighted>processing>random |
| baseline | campus1 | 80.417 | 80.417 | 80.857 | 81.121 | 80.417 | policy>duedate>weighted>processing>random |
| baseline | campus2 | 1311.322 | 1235.172 | 1953.175 | 1636.031 | 1649.863 | weighted>duedate>random>policy>processing |
| backdate | verdict | 444.932 | 445.578 | 448.578 | 447.881 | 445.017 | duedate>policy>weighted>random>processing |
| backdate | campus1 | 80.471 | 80.648 | 80.748 | 80.605 | 80.458 | policy>duedate>random>weighted>processing |
| backdate | campus2 | 1292.865 | 1287.966 | 2334.932 | 1857.464 | 1880.515 | weighted>duedate>random>policy>processing |


Per-arm method table (rules in bold positions, policy seeds ranked individually):


**baseline / verdict** (released timestamps (Eval-B)) - best v2rl302 (mean 444.681), 180 configurations. Equivalence set: 17 of 17 methods.

| rank | method | family | mean | pct_from_best | abs_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | v2rl302 | policy | 444.681 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 4.447 | equivalent | 1 |
| 2 | v2rl308 | policy | 444.708 | 0.006 | 0.027 | 0.027 | 0.000 | 0.065 | 4.447 | equivalent | 1 |
| 3 | v2rl310 | policy | 444.712 | 0.007 | 0.031 | 0.031 | -0.003 | 0.083 | 4.447 | equivalent | 1 |
| 4 | v2rl303 | policy | 444.731 | 0.011 | 0.050 | 0.050 | 0.000 | 0.130 | 4.447 | equivalent | 1 |
| 5 | v2rl301 | policy | 444.756 | 0.017 | 0.075 | 0.075 | 0.014 | 0.159 | 4.447 | equivalent | 1 |
| 6 | v2rl305 | policy | 444.760 | 0.018 | 0.079 | 0.079 | 0.011 | 0.180 | 4.447 | equivalent | 1 |
| 7 | v2rl304 | policy | 444.763 | 0.018 | 0.082 | 0.082 | -0.002 | 0.195 | 4.447 | equivalent | 1 |
| 8 | v2rl307 | policy | 444.770 | 0.020 | 0.089 | 0.089 | 0.012 | 0.183 | 4.447 | equivalent | 1 |
| 9 | v2rl306 | policy | 444.859 | 0.040 | 0.178 | 0.178 | 0.007 | 0.484 | 4.447 | equivalent | 1 |
| 10 | edd | duedate | 444.869 | 0.042 | 0.188 | 0.188 | 0.023 | 0.406 | 4.447 | equivalent | 1 |
| 10 | pfifo | duedate | 444.869 | 0.042 | 0.188 | 0.188 | 0.027 | 0.404 | 4.447 | equivalent | 1 |
| 12 | v2rl309 | policy | 444.953 | 0.061 | 0.272 | 0.272 | 0.030 | 0.635 | 4.447 | equivalent | 1 |
| 13 | wmdd | weighted | 445.332 | 0.146 | 0.651 | 0.651 | 0.165 | 1.274 | 4.447 | equivalent | 1 |
| 14 | atc | weighted | 445.555 | 0.197 | 0.874 | 0.874 | 0.263 | 1.641 | 4.447 | equivalent | 1 |
| 15 | lpt | processing | 445.579 | 0.202 | 0.898 | 0.898 | 0.074 | 2.438 | 4.447 | equivalent | 1 |
| 16 | random | random | 446.316 | 0.368 | 1.635 | 1.635 | 0.572 | 3.181 | 4.447 | equivalent | 1 |
| 17 | wspt | processing | 446.646 | 0.442 | 1.965 | 1.965 | 0.891 | 3.312 | 4.447 | equivalent | 1 |


**baseline / campus1** (released timestamps (Eval-B)) - best atc (mean 80.417), 30 configurations. Equivalence set: 15 of 17 methods.

| rank | method | family | mean | pct_from_best | abs_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | atc | weighted | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | edd | duedate | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | lpt | processing | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | pfifo | duedate | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl301 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl302 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl303 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl304 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl305 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl306 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl307 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl308 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl309 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl310 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | wmdd | weighted | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 16 | random | random | 81.121 | 0.875 | 0.704 | 0.704 | 0.000 | 1.775 | 1.000 | inconclusive | 0 |
| 17 | wspt | processing | 81.297 | 1.094 | 0.880 | 0.880 | 0.000 | 2.293 | 1.000 | inconclusive | 0 |


**baseline / campus2** (released timestamps (Eval-B)) - best wmdd (mean 1218.229), 17 configurations. Equivalence set: 1 of 17 methods.

| rank | method | family | mean | pct_from_best | abs_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | wmdd | weighted | 1218.229 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 12.182 | equivalent | 1 |
| 2 | atc | weighted | 1252.116 | 2.782 | 33.887 | 33.887 | 12.321 | 59.462 | 12.182 | worse | 0 |
| 3 | wspt | processing | 1291.239 | 5.993 | 73.010 | 73.010 | 35.217 | 113.926 | 12.182 | worse | 0 |
| 4 | edd | duedate | 1311.322 | 7.642 | 93.093 | 93.093 | -17.248 | 242.406 | 12.182 | inconclusive | 0 |
| 4 | pfifo | duedate | 1311.322 | 7.642 | 93.093 | 93.093 | -16.389 | 241.693 | 12.182 | inconclusive | 0 |
| 6 | v2rl310 | policy | 1324.889 | 8.755 | 106.660 | 106.660 | 9.846 | 226.410 | 12.182 | inconclusive | 0 |
| 7 | v2rl302 | policy | 1420.451 | 16.600 | 202.223 | 202.223 | 67.394 | 367.774 | 12.182 | worse | 0 |
| 8 | v2rl304 | policy | 1447.724 | 18.838 | 229.495 | 229.495 | 33.037 | 520.343 | 12.182 | worse | 0 |
| 9 | v2rl309 | policy | 1453.006 | 19.272 | 234.777 | 234.777 | 57.100 | 525.791 | 12.182 | worse | 0 |
| 10 | v2rl308 | policy | 1494.215 | 22.655 | 275.986 | 275.986 | 15.248 | 683.838 | 12.182 | worse | 0 |
| 11 | random | random | 1636.031 | 34.296 | 417.802 | 417.802 | 215.398 | 661.251 | 12.182 | worse | 0 |
| 12 | v2rl305 | policy | 1720.644 | 41.241 | 502.415 | 502.415 | 188.441 | 917.362 | 12.182 | worse | 0 |
| 13 | v2rl307 | policy | 1751.246 | 43.753 | 533.018 | 533.018 | 193.128 | 968.132 | 12.182 | worse | 0 |
| 14 | v2rl301 | policy | 1851.252 | 51.963 | 633.023 | 633.023 | 225.055 | 1116.052 | 12.182 | worse | 0 |
| 15 | v2rl306 | policy | 1863.508 | 52.969 | 645.279 | 645.279 | 260.127 | 1105.504 | 12.182 | worse | 0 |
| 16 | v2rl303 | policy | 2171.693 | 78.266 | 953.464 | 953.464 | 451.924 | 1507.926 | 12.182 | worse | 0 |
| 17 | lpt | processing | 2615.112 | 114.665 | 1396.883 | 1396.883 | 683.108 | 2224.134 | 12.182 | worse | 0 |


**backdate / verdict** (corrective releases shifted earlier) - best edd (mean 444.932), 180 configurations. Equivalence set: 14 of 17 methods.

| rank | method | family | mean | pct_from_best | abs_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | edd | duedate | 444.932 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 4.449 | equivalent | 1 |
| 1 | pfifo | duedate | 444.932 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 4.449 | equivalent | 1 |
| 3 | v2rl302 | policy | 444.940 | 0.002 | 0.008 | 0.008 | -0.167 | 0.145 | 4.449 | equivalent | 1 |
| 3 | v2rl310 | policy | 444.940 | 0.002 | 0.008 | 0.008 | -0.171 | 0.166 | 4.449 | equivalent | 1 |
| 5 | v2rl308 | policy | 444.944 | 0.003 | 0.012 | 0.012 | -0.193 | 0.196 | 4.449 | equivalent | 1 |
| 6 | v2rl307 | policy | 444.960 | 0.006 | 0.027 | 0.027 | -0.162 | 0.198 | 4.449 | equivalent | 1 |
| 7 | v2rl304 | policy | 444.985 | 0.012 | 0.052 | 0.052 | -0.156 | 0.275 | 4.449 | equivalent | 1 |
| 8 | v2rl305 | policy | 444.996 | 0.014 | 0.064 | 0.064 | -0.142 | 0.290 | 4.449 | equivalent | 1 |
| 9 | v2rl301 | policy | 445.001 | 0.016 | 0.069 | 0.069 | -0.183 | 0.408 | 4.449 | equivalent | 1 |
| 10 | v2rl306 | policy | 445.057 | 0.028 | 0.125 | 0.125 | -0.148 | 0.490 | 4.449 | equivalent | 1 |
| 11 | v2rl309 | policy | 445.142 | 0.047 | 0.210 | 0.210 | -0.141 | 0.751 | 4.449 | equivalent | 1 |
| 12 | v2rl303 | policy | 445.202 | 0.061 | 0.270 | 0.270 | -0.106 | 0.829 | 4.449 | equivalent | 1 |
| 13 | wmdd | weighted | 445.388 | 0.102 | 0.456 | 0.456 | 0.083 | 1.000 | 4.449 | equivalent | 1 |
| 14 | atc | weighted | 445.768 | 0.188 | 0.835 | 0.835 | 0.155 | 1.725 | 4.449 | equivalent | 1 |
| 15 | random | random | 447.881 | 0.663 | 2.949 | 2.949 | 0.555 | 6.431 | 4.449 | inconclusive | 0 |
| 16 | wspt | processing | 448.177 | 0.729 | 3.245 | 3.245 | 1.104 | 6.384 | 4.449 | inconclusive | 0 |
| 17 | lpt | processing | 448.978 | 0.909 | 4.045 | 4.045 | 0.497 | 9.733 | 4.449 | inconclusive | 0 |


**backdate / campus1** (corrective releases shifted earlier) - best v2rl304 (mean 80.425), 30 configurations. Equivalence set: 16 of 17 methods.

| rank | method | family | mean | pct_from_best | abs_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | v2rl304 | policy | 80.425 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl307 | policy | 80.425 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl310 | policy | 80.425 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 4 | edd | duedate | 80.471 | 0.058 | 0.047 | 0.047 | 0.000 | 0.140 | 1.000 | equivalent | 1 |
| 4 | lpt | processing | 80.471 | 0.058 | 0.047 | 0.047 | 0.000 | 0.140 | 1.000 | equivalent | 1 |
| 4 | pfifo | duedate | 80.471 | 0.058 | 0.047 | 0.047 | 0.000 | 0.140 | 1.000 | equivalent | 1 |
| 4 | v2rl301 | policy | 80.471 | 0.058 | 0.047 | 0.047 | 0.000 | 0.140 | 1.000 | equivalent | 1 |
| 4 | v2rl302 | policy | 80.471 | 0.058 | 0.047 | 0.047 | 0.000 | 0.140 | 1.000 | equivalent | 1 |
| 4 | v2rl303 | policy | 80.471 | 0.058 | 0.047 | 0.047 | 0.000 | 0.140 | 1.000 | equivalent | 1 |
| 4 | v2rl305 | policy | 80.471 | 0.058 | 0.047 | 0.047 | 0.000 | 0.140 | 1.000 | equivalent | 1 |
| 4 | v2rl306 | policy | 80.471 | 0.058 | 0.047 | 0.047 | 0.000 | 0.140 | 1.000 | equivalent | 1 |
| 4 | v2rl308 | policy | 80.471 | 0.058 | 0.047 | 0.047 | 0.000 | 0.140 | 1.000 | equivalent | 1 |
| 4 | v2rl309 | policy | 80.471 | 0.058 | 0.047 | 0.047 | 0.000 | 0.140 | 1.000 | equivalent | 1 |
| 14 | random | random | 80.605 | 0.224 | 0.180 | 0.180 | 0.000 | 0.493 | 1.000 | equivalent | 1 |
| 14 | wmdd | weighted | 80.605 | 0.224 | 0.180 | 0.180 | 0.000 | 0.493 | 1.000 | equivalent | 1 |
| 16 | atc | weighted | 80.692 | 0.332 | 0.267 | 0.267 | 0.000 | 0.800 | 1.000 | equivalent | 1 |
| 17 | wspt | processing | 81.025 | 0.746 | 0.600 | 0.600 | 0.000 | 1.333 | 1.000 | inconclusive | 0 |


**backdate / campus2** (corrective releases shifted earlier) - best wmdd (mean 1265.913), 17 configurations. Equivalence set: 1 of 17 methods.

| rank | method | family | mean | pct_from_best | abs_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | wmdd | weighted | 1265.913 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 12.659 | equivalent | 1 |
| 2 | edd | duedate | 1292.865 | 2.129 | 26.951 | 26.951 | -34.699 | 117.925 | 12.659 | inconclusive | 0 |
| 2 | pfifo | duedate | 1292.865 | 2.129 | 26.951 | 26.951 | -35.061 | 117.848 | 12.659 | inconclusive | 0 |
| 4 | atc | weighted | 1310.019 | 3.484 | 44.106 | 44.106 | -0.217 | 94.248 | 12.659 | inconclusive | 0 |
| 5 | wspt | processing | 1357.696 | 7.250 | 91.783 | 91.783 | 23.904 | 165.911 | 12.659 | worse | 0 |
| 6 | v2rl302 | policy | 1512.922 | 19.512 | 247.009 | 247.009 | 49.577 | 513.113 | 12.659 | worse | 0 |
| 7 | v2rl309 | policy | 1516.996 | 19.834 | 251.083 | 251.083 | 45.143 | 535.821 | 12.659 | worse | 0 |
| 8 | v2rl308 | policy | 1518.755 | 19.973 | 252.842 | 252.842 | 39.814 | 547.148 | 12.659 | worse | 0 |
| 9 | v2rl310 | policy | 1531.633 | 20.990 | 265.720 | 265.720 | 25.949 | 568.381 | 12.659 | worse | 0 |
| 10 | v2rl304 | policy | 1557.446 | 23.029 | 291.533 | 291.533 | 35.139 | 618.937 | 12.659 | worse | 0 |
| 11 | random | random | 1857.464 | 46.729 | 591.550 | 591.550 | 281.167 | 967.039 | 12.659 | worse | 0 |
| 12 | v2rl307 | policy | 2038.865 | 61.059 | 772.951 | 772.951 | 212.062 | 1446.882 | 12.659 | worse | 0 |
| 13 | v2rl305 | policy | 2066.274 | 63.224 | 800.360 | 800.360 | 314.129 | 1354.416 | 12.659 | worse | 0 |
| 14 | v2rl306 | policy | 2133.753 | 68.554 | 867.839 | 867.839 | 287.991 | 1539.961 | 12.659 | worse | 0 |
| 15 | v2rl301 | policy | 2309.000 | 82.398 | 1043.087 | 1043.087 | 393.419 | 1766.956 | 12.659 | worse | 0 |
| 16 | v2rl303 | policy | 2619.502 | 106.926 | 1353.589 | 1353.589 | 577.328 | 2231.940 | 12.659 | worse | 0 |
| 17 | lpt | processing | 3312.168 | 161.643 | 2046.255 | 2046.255 | 977.526 | 3301.999 | 12.659 | worse | 0 |


## Service-window and priority scenarios (R4.10)

Endpoint: does a different service-window or priority convention move the ranking or the equivalence set?


### Stability against the contract windows as recorded (Eval-B) arm

| arm | stratum | n_configs | n_anchors | best_method | best_mean | spread_pct | margin_pct_of_best | tau_method | tau_family | set_size | baseline_set_size | set_jaccard | left_set | entered_set | n_policy_seeds_in_set | top3_families | top3_is_leading_trio |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | verdict | 180 | 180 | v2rl302 | 444.681 | 0.442 | 1.000 | 1.000 | 1.000 | 17 | 17 | 1.000 | - | - | 10 | duedate policy weighted | 1 |
| baseline | campus1 | 30 | 30 | atc | 80.417 | 1.094 | 1.244 | 1.000 | 1.000 | 15 | 15 | 1.000 | - | - | 10 | duedate policy weighted | 1 |
| baseline | campus2 | 17 | 17 | wmdd | 1218.229 | 114.665 | 1.000 | 1.000 | 1.000 | 1 | 1 | 1.000 | - | - | 0 | duedate random weighted | 0 |
| emg | verdict | 180 | 180 | v2rl303 | 633.200 | 0.549 | 1.000 | 0.704 | 1.000 | 17 | 17 | 1.000 | - | - | 10 | duedate policy weighted | 1 |
| emg | campus1 | 30 | 30 | atc | 137.550 | 0.831 | 1.000 | 0.500 | 0.316 | 14 | 15 | 0.933 | lpt | - | 10 | duedate policy weighted | 1 |
| emg | campus2 | 17 | 17 | wmdd | 1658.550 | 108.030 | 1.000 | 0.967 | 0.800 | 1 | 1 | 1.000 | - | - | 0 | duedate policy weighted | 1 |
| rtn | verdict | 180 | 180 | v2rl310 | 471.141 | 0.684 | 1.000 | 0.881 | 0.800 | 15 | 17 | 0.882 | lpt wspt | - | 10 | duedate policy weighted | 1 |
| rtn | campus1 | 30 | 30 | atc | 97.900 | 0.899 | 1.021 | 0.776 | 0.556 | 14 | 15 | 0.933 | v2rl309 | - | 9 | duedate policy weighted | 1 |
| rtn | campus2 | 17 | 17 | wmdd | 1454.189 | 115.823 | 1.000 | 0.937 | 1.000 | 1 | 1 | 1.000 | - | - | 0 | duedate random weighted | 0 |
| pmp3 | verdict | 180 | 180 | v2rl302 | 459.647 | 0.470 | 1.000 | 0.837 | 1.000 | 17 | 17 | 1.000 | - | - | 10 | duedate policy weighted | 1 |
| pmp3 | campus1 | 30 | 30 | atc | 90.558 | 1.034 | 1.104 | 0.830 | 0.556 | 15 | 15 | 1.000 | - | - | 10 | duedate policy weighted | 1 |
| pmp3 | campus2 | 17 | 17 | wmdd | 1231.344 | 112.965 | 1.000 | 1.000 | 1.000 | 1 | 1 | 1.000 | - | - | 0 | duedate random weighted | 0 |


Family means (mean of the member methods' means) and the family order they imply:

| arm | stratum | mean_duedate | mean_weighted | mean_processing | mean_random | mean_policy | family_order |
|---|---|---|---|---|---|---|---|
| baseline | verdict | 444.869 | 445.444 | 446.112 | 446.316 | 444.769 | policy>duedate>weighted>processing>random |
| baseline | campus1 | 80.417 | 80.417 | 80.857 | 81.121 | 80.417 | policy>duedate>weighted>processing>random |
| baseline | campus2 | 1311.322 | 1235.172 | 1953.175 | 1636.031 | 1649.863 | weighted>duedate>random>policy>processing |
| emg | verdict | 633.402 | 633.962 | 635.563 | 636.674 | 633.376 | policy>duedate>weighted>processing>random |
| emg | campus1 | 137.643 | 137.610 | 138.561 | 138.373 | 137.664 | weighted>duedate>policy>random>processing |
| emg | campus2 | 1875.625 | 1674.699 | 2600.213 | 2299.784 | 2296.616 | weighted>duedate>policy>random>processing |
| rtn | verdict | 472.032 | 472.904 | 473.859 | 473.716 | 471.335 | policy>duedate>weighted>random>processing |
| rtn | campus1 | 97.900 | 97.900 | 98.340 | 98.603 | 97.984 | duedate>weighted>policy>processing>random |
| rtn | campus2 | 1627.485 | 1469.616 | 2317.894 | 1934.059 | 2258.077 | weighted>duedate>random>policy>processing |
| pmp3 | verdict | 459.836 | 460.449 | 461.197 | 461.326 | 459.750 | policy>duedate>weighted>processing>random |
| pmp3 | campus1 | 90.558 | 90.558 | 91.026 | 91.262 | 90.585 | duedate>weighted>policy>processing>random |
| pmp3 | campus2 | 1321.473 | 1249.751 | 1964.148 | 1643.508 | 1667.195 | weighted>duedate>random>policy>processing |


Per-arm method table (rules in bold positions, policy seeds ranked individually):


**baseline / verdict** (contract windows as recorded (Eval-B)) - best v2rl302 (mean 444.681), 180 configurations. Equivalence set: 17 of 17 methods.

| rank | method | family | mean | pct_from_best | abs_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | v2rl302 | policy | 444.681 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 4.447 | equivalent | 1 |
| 2 | v2rl308 | policy | 444.708 | 0.006 | 0.027 | 0.027 | 0.000 | 0.065 | 4.447 | equivalent | 1 |
| 3 | v2rl310 | policy | 444.712 | 0.007 | 0.031 | 0.031 | -0.003 | 0.083 | 4.447 | equivalent | 1 |
| 4 | v2rl303 | policy | 444.731 | 0.011 | 0.050 | 0.050 | 0.000 | 0.130 | 4.447 | equivalent | 1 |
| 5 | v2rl301 | policy | 444.756 | 0.017 | 0.075 | 0.075 | 0.014 | 0.159 | 4.447 | equivalent | 1 |
| 6 | v2rl305 | policy | 444.760 | 0.018 | 0.079 | 0.079 | 0.011 | 0.180 | 4.447 | equivalent | 1 |
| 7 | v2rl304 | policy | 444.763 | 0.018 | 0.082 | 0.082 | -0.002 | 0.195 | 4.447 | equivalent | 1 |
| 8 | v2rl307 | policy | 444.770 | 0.020 | 0.089 | 0.089 | 0.012 | 0.183 | 4.447 | equivalent | 1 |
| 9 | v2rl306 | policy | 444.859 | 0.040 | 0.178 | 0.178 | 0.007 | 0.484 | 4.447 | equivalent | 1 |
| 10 | edd | duedate | 444.869 | 0.042 | 0.188 | 0.188 | 0.023 | 0.406 | 4.447 | equivalent | 1 |
| 10 | pfifo | duedate | 444.869 | 0.042 | 0.188 | 0.188 | 0.027 | 0.404 | 4.447 | equivalent | 1 |
| 12 | v2rl309 | policy | 444.953 | 0.061 | 0.272 | 0.272 | 0.030 | 0.635 | 4.447 | equivalent | 1 |
| 13 | wmdd | weighted | 445.332 | 0.146 | 0.651 | 0.651 | 0.165 | 1.274 | 4.447 | equivalent | 1 |
| 14 | atc | weighted | 445.555 | 0.197 | 0.874 | 0.874 | 0.263 | 1.641 | 4.447 | equivalent | 1 |
| 15 | lpt | processing | 445.579 | 0.202 | 0.898 | 0.898 | 0.074 | 2.438 | 4.447 | equivalent | 1 |
| 16 | random | random | 446.316 | 0.368 | 1.635 | 1.635 | 0.572 | 3.181 | 4.447 | equivalent | 1 |
| 17 | wspt | processing | 446.646 | 0.442 | 1.965 | 1.965 | 0.891 | 3.312 | 4.447 | equivalent | 1 |


**baseline / campus1** (contract windows as recorded (Eval-B)) - best atc (mean 80.417), 30 configurations. Equivalence set: 15 of 17 methods.

| rank | method | family | mean | pct_from_best | abs_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | atc | weighted | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | edd | duedate | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | lpt | processing | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | pfifo | duedate | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl301 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl302 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl303 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl304 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl305 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl306 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl307 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl308 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl309 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl310 | policy | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | wmdd | weighted | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 16 | random | random | 81.121 | 0.875 | 0.704 | 0.704 | 0.000 | 1.775 | 1.000 | inconclusive | 0 |
| 17 | wspt | processing | 81.297 | 1.094 | 0.880 | 0.880 | 0.000 | 2.293 | 1.000 | inconclusive | 0 |


**baseline / campus2** (contract windows as recorded (Eval-B)) - best wmdd (mean 1218.229), 17 configurations. Equivalence set: 1 of 17 methods.

| rank | method | family | mean | pct_from_best | abs_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | wmdd | weighted | 1218.229 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 12.182 | equivalent | 1 |
| 2 | atc | weighted | 1252.116 | 2.782 | 33.887 | 33.887 | 12.321 | 59.462 | 12.182 | worse | 0 |
| 3 | wspt | processing | 1291.239 | 5.993 | 73.010 | 73.010 | 35.217 | 113.926 | 12.182 | worse | 0 |
| 4 | edd | duedate | 1311.322 | 7.642 | 93.093 | 93.093 | -17.248 | 242.406 | 12.182 | inconclusive | 0 |
| 4 | pfifo | duedate | 1311.322 | 7.642 | 93.093 | 93.093 | -16.389 | 241.693 | 12.182 | inconclusive | 0 |
| 6 | v2rl310 | policy | 1324.889 | 8.755 | 106.660 | 106.660 | 9.846 | 226.410 | 12.182 | inconclusive | 0 |
| 7 | v2rl302 | policy | 1420.451 | 16.600 | 202.223 | 202.223 | 67.394 | 367.774 | 12.182 | worse | 0 |
| 8 | v2rl304 | policy | 1447.724 | 18.838 | 229.495 | 229.495 | 33.037 | 520.343 | 12.182 | worse | 0 |
| 9 | v2rl309 | policy | 1453.006 | 19.272 | 234.777 | 234.777 | 57.100 | 525.791 | 12.182 | worse | 0 |
| 10 | v2rl308 | policy | 1494.215 | 22.655 | 275.986 | 275.986 | 15.248 | 683.838 | 12.182 | worse | 0 |
| 11 | random | random | 1636.031 | 34.296 | 417.802 | 417.802 | 215.398 | 661.251 | 12.182 | worse | 0 |
| 12 | v2rl305 | policy | 1720.644 | 41.241 | 502.415 | 502.415 | 188.441 | 917.362 | 12.182 | worse | 0 |
| 13 | v2rl307 | policy | 1751.246 | 43.753 | 533.018 | 533.018 | 193.128 | 968.132 | 12.182 | worse | 0 |
| 14 | v2rl301 | policy | 1851.252 | 51.963 | 633.023 | 633.023 | 225.055 | 1116.052 | 12.182 | worse | 0 |
| 15 | v2rl306 | policy | 1863.508 | 52.969 | 645.279 | 645.279 | 260.127 | 1105.504 | 12.182 | worse | 0 |
| 16 | v2rl303 | policy | 2171.693 | 78.266 | 953.464 | 953.464 | 451.924 | 1507.926 | 12.182 | worse | 0 |
| 17 | lpt | processing | 2615.112 | 114.665 | 1396.883 | 1396.883 | 683.108 | 2224.134 | 12.182 | worse | 0 |


**emg / verdict** (compressed emergency focus (P1/P2 halved)) - best v2rl303 (mean 633.200), 180 configurations. Equivalence set: 17 of 17 methods.

| rank | method | family | mean | pct_from_best | abs_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | v2rl303 | policy | 633.200 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 6.332 | equivalent | 1 |
| 2 | v2rl310 | policy | 633.264 | 0.010 | 0.064 | 0.064 | -0.017 | 0.181 | 6.332 | equivalent | 1 |
| 3 | v2rl305 | policy | 633.307 | 0.017 | 0.107 | 0.107 | -0.056 | 0.381 | 6.332 | equivalent | 1 |
| 4 | v2rl302 | policy | 633.333 | 0.021 | 0.134 | 0.134 | -0.050 | 0.424 | 6.332 | equivalent | 1 |
| 5 | v2rl307 | policy | 633.351 | 0.024 | 0.151 | 0.151 | -0.004 | 0.425 | 6.332 | equivalent | 1 |
| 6 | v2rl301 | policy | 633.353 | 0.024 | 0.153 | 0.153 | 0.008 | 0.416 | 6.332 | equivalent | 1 |
| 7 | v2rl304 | policy | 633.394 | 0.031 | 0.194 | 0.194 | 0.017 | 0.435 | 6.332 | equivalent | 1 |
| 8 | edd | duedate | 633.402 | 0.032 | 0.202 | 0.202 | 0.033 | 0.423 | 6.332 | equivalent | 1 |
| 8 | pfifo | duedate | 633.402 | 0.032 | 0.202 | 0.202 | 0.038 | 0.422 | 6.332 | equivalent | 1 |
| 10 | v2rl306 | policy | 633.466 | 0.042 | 0.267 | 0.267 | 0.000 | 0.800 | 6.332 | equivalent | 1 |
| 11 | v2rl308 | policy | 633.486 | 0.045 | 0.286 | 0.286 | -0.009 | 0.749 | 6.332 | equivalent | 1 |
| 12 | v2rl309 | policy | 633.605 | 0.064 | 0.405 | 0.405 | 0.057 | 0.895 | 6.332 | equivalent | 1 |
| 13 | wmdd | weighted | 633.928 | 0.115 | 0.728 | 0.728 | 0.195 | 1.434 | 6.332 | equivalent | 1 |
| 14 | atc | weighted | 633.997 | 0.126 | 0.797 | 0.797 | 0.191 | 1.610 | 6.332 | equivalent | 1 |
| 15 | wspt | processing | 635.562 | 0.373 | 2.362 | 2.362 | 1.207 | 3.774 | 6.332 | equivalent | 1 |
| 16 | lpt | processing | 635.564 | 0.373 | 2.364 | 2.364 | 0.625 | 4.900 | 6.332 | equivalent | 1 |
| 17 | random | random | 636.674 | 0.549 | 3.475 | 3.475 | 1.658 | 5.998 | 6.332 | equivalent | 1 |


**emg / campus1** (compressed emergency focus (P1/P2 halved)) - best atc (mean 137.550), 30 configurations. Equivalence set: 14 of 17 methods.

| rank | method | family | mean | pct_from_best | abs_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | atc | weighted | 137.550 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.376 | equivalent | 1 |
| 2 | edd | duedate | 137.643 | 0.068 | 0.093 | 0.093 | 0.000 | 0.280 | 1.376 | equivalent | 1 |
| 2 | pfifo | duedate | 137.643 | 0.068 | 0.093 | 0.093 | 0.000 | 0.280 | 1.376 | equivalent | 1 |
| 2 | v2rl304 | policy | 137.643 | 0.068 | 0.093 | 0.093 | 0.000 | 0.280 | 1.376 | equivalent | 1 |
| 2 | v2rl307 | policy | 137.643 | 0.068 | 0.093 | 0.093 | 0.000 | 0.280 | 1.376 | equivalent | 1 |
| 6 | v2rl301 | policy | 137.670 | 0.087 | 0.120 | 0.120 | 0.000 | 0.359 | 1.376 | equivalent | 1 |
| 6 | v2rl302 | policy | 137.670 | 0.087 | 0.120 | 0.120 | 0.000 | 0.359 | 1.376 | equivalent | 1 |
| 6 | v2rl303 | policy | 137.670 | 0.087 | 0.120 | 0.120 | 0.000 | 0.359 | 1.376 | equivalent | 1 |
| 6 | v2rl305 | policy | 137.670 | 0.087 | 0.120 | 0.120 | 0.000 | 0.359 | 1.376 | equivalent | 1 |
| 6 | v2rl306 | policy | 137.670 | 0.087 | 0.120 | 0.120 | 0.000 | 0.359 | 1.376 | equivalent | 1 |
| 6 | v2rl308 | policy | 137.670 | 0.087 | 0.120 | 0.120 | 0.000 | 0.359 | 1.376 | equivalent | 1 |
| 6 | v2rl309 | policy | 137.670 | 0.087 | 0.120 | 0.120 | 0.000 | 0.359 | 1.376 | equivalent | 1 |
| 6 | v2rl310 | policy | 137.670 | 0.087 | 0.120 | 0.120 | 0.000 | 0.359 | 1.376 | equivalent | 1 |
| 6 | wmdd | weighted | 137.670 | 0.087 | 0.120 | 0.120 | 0.000 | 0.359 | 1.376 | equivalent | 1 |
| 15 | random | random | 138.373 | 0.599 | 0.823 | 0.823 | 0.000 | 1.895 | 1.376 | inconclusive | 0 |
| 16 | wspt | processing | 138.430 | 0.640 | 0.880 | 0.880 | 0.000 | 2.293 | 1.376 | inconclusive | 0 |
| 17 | lpt | processing | 138.692 | 0.831 | 1.142 | 1.142 | 0.000 | 3.068 | 1.376 | inconclusive | 0 |


**emg / campus2** (compressed emergency focus (P1/P2 halved)) - best wmdd (mean 1658.550), 17 configurations. Equivalence set: 1 of 17 methods.

| rank | method | family | mean | pct_from_best | abs_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | wmdd | weighted | 1658.550 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 16.586 | equivalent | 1 |
| 2 | atc | weighted | 1690.848 | 1.947 | 32.298 | 32.298 | 8.761 | 58.687 | 16.586 | inconclusive | 0 |
| 3 | wspt | processing | 1750.153 | 5.523 | 91.602 | 91.602 | 46.073 | 141.234 | 16.586 | worse | 0 |
| 4 | pfifo | duedate | 1874.826 | 13.040 | 216.275 | 216.275 | 32.581 | 441.891 | 16.586 | worse | 0 |
| 5 | edd | duedate | 1876.423 | 13.136 | 217.873 | 217.873 | 31.423 | 446.273 | 16.586 | worse | 0 |
| 6 | v2rl310 | policy | 1883.885 | 13.586 | 225.335 | 225.335 | 59.574 | 429.410 | 16.586 | worse | 0 |
| 7 | v2rl302 | policy | 1981.273 | 19.458 | 322.723 | 322.723 | 92.974 | 618.764 | 16.586 | worse | 0 |
| 8 | v2rl309 | policy | 2049.384 | 23.565 | 390.833 | 390.833 | 80.602 | 862.384 | 16.586 | worse | 0 |
| 9 | v2rl308 | policy | 2094.958 | 26.313 | 436.407 | 436.407 | 108.306 | 916.307 | 16.586 | worse | 0 |
| 10 | v2rl304 | policy | 2138.962 | 28.966 | 480.412 | 480.412 | 138.937 | 938.398 | 16.586 | worse | 0 |
| 11 | random | random | 2299.784 | 38.662 | 641.234 | 641.234 | 332.406 | 1033.237 | 16.586 | worse | 0 |
| 12 | v2rl305 | policy | 2395.857 | 44.455 | 737.307 | 737.307 | 271.471 | 1307.688 | 16.586 | worse | 0 |
| 13 | v2rl307 | policy | 2429.788 | 46.501 | 771.238 | 771.238 | 315.671 | 1338.036 | 16.586 | worse | 0 |
| 14 | v2rl301 | policy | 2509.337 | 51.297 | 850.787 | 850.787 | 336.531 | 1461.400 | 16.586 | worse | 0 |
| 15 | v2rl306 | policy | 2527.763 | 52.408 | 869.213 | 869.213 | 324.338 | 1512.373 | 16.586 | worse | 0 |
| 16 | v2rl303 | policy | 2954.956 | 78.165 | 1296.406 | 1296.406 | 593.561 | 2120.010 | 16.586 | worse | 0 |
| 17 | lpt | processing | 3450.274 | 108.030 | 1791.724 | 1791.724 | 883.131 | 2852.910 | 16.586 | worse | 0 |


**rtn / verdict** (routine tightening (P3/P4 halved)) - best v2rl310 (mean 471.141), 180 configurations. Equivalence set: 15 of 17 methods.

| rank | method | family | mean | pct_from_best | abs_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | v2rl310 | policy | 471.141 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 4.711 | equivalent | 1 |
| 2 | v2rl302 | policy | 471.154 | 0.003 | 0.013 | 0.013 | -0.017 | 0.054 | 4.711 | equivalent | 1 |
| 3 | v2rl308 | policy | 471.168 | 0.006 | 0.027 | 0.027 | -0.001 | 0.069 | 4.711 | equivalent | 1 |
| 4 | v2rl305 | policy | 471.249 | 0.023 | 0.109 | 0.109 | 0.021 | 0.226 | 4.711 | equivalent | 1 |
| 5 | v2rl304 | policy | 471.261 | 0.026 | 0.121 | 0.121 | 0.014 | 0.258 | 4.711 | equivalent | 1 |
| 6 | v2rl307 | policy | 471.264 | 0.026 | 0.123 | 0.123 | 0.021 | 0.256 | 4.711 | equivalent | 1 |
| 7 | v2rl303 | policy | 471.272 | 0.028 | 0.131 | 0.131 | 0.028 | 0.266 | 4.711 | equivalent | 1 |
| 8 | v2rl301 | policy | 471.345 | 0.043 | 0.204 | 0.204 | 0.057 | 0.397 | 4.711 | equivalent | 1 |
| 9 | v2rl306 | policy | 471.365 | 0.048 | 0.225 | 0.225 | 0.038 | 0.511 | 4.711 | equivalent | 1 |
| 10 | edd | duedate | 472.032 | 0.189 | 0.892 | 0.892 | 0.125 | 2.140 | 4.711 | equivalent | 1 |
| 10 | pfifo | duedate | 472.032 | 0.189 | 0.892 | 0.892 | 0.132 | 2.082 | 4.711 | equivalent | 1 |
| 12 | v2rl309 | policy | 472.134 | 0.211 | 0.993 | 0.993 | 0.148 | 2.293 | 4.711 | equivalent | 1 |
| 13 | wmdd | weighted | 472.750 | 0.342 | 1.610 | 1.610 | 0.415 | 3.389 | 4.711 | equivalent | 1 |
| 14 | atc | weighted | 473.058 | 0.407 | 1.917 | 1.917 | 0.646 | 3.612 | 4.711 | equivalent | 1 |
| 15 | lpt | processing | 473.354 | 0.470 | 2.213 | 2.213 | 0.118 | 5.548 | 4.711 | inconclusive | 0 |
| 16 | random | random | 473.716 | 0.547 | 2.576 | 2.576 | 0.978 | 4.710 | 4.711 | equivalent | 1 |
| 17 | wspt | processing | 474.365 | 0.684 | 3.224 | 3.224 | 1.500 | 5.427 | 4.711 | inconclusive | 0 |


**rtn / campus1** (routine tightening (P3/P4 halved)) - best atc (mean 97.900), 30 configurations. Equivalence set: 14 of 17 methods.

| rank | method | family | mean | pct_from_best | abs_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | atc | weighted | 97.900 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | edd | duedate | 97.900 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | lpt | processing | 97.900 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | pfifo | duedate | 97.900 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl301 | policy | 97.900 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl302 | policy | 97.900 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl303 | policy | 97.900 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl304 | policy | 97.900 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl305 | policy | 97.900 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl306 | policy | 97.900 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl307 | policy | 97.900 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl308 | policy | 97.900 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl310 | policy | 97.900 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | wmdd | weighted | 97.900 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 15 | random | random | 98.603 | 0.719 | 0.704 | 0.704 | 0.000 | 1.775 | 1.000 | inconclusive | 0 |
| 16 | v2rl309 | policy | 98.738 | 0.856 | 0.838 | 0.838 | 0.000 | 2.243 | 1.000 | inconclusive | 0 |
| 17 | wspt | processing | 98.780 | 0.899 | 0.880 | 0.880 | 0.000 | 2.293 | 1.000 | inconclusive | 0 |


**rtn / campus2** (routine tightening (P3/P4 halved)) - best wmdd (mean 1454.189), 17 configurations. Equivalence set: 1 of 17 methods.

| rank | method | family | mean | pct_from_best | abs_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | wmdd | weighted | 1454.189 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 14.542 | equivalent | 1 |
| 2 | atc | weighted | 1485.043 | 2.122 | 30.854 | 30.854 | 10.767 | 54.351 | 14.542 | inconclusive | 0 |
| 3 | wspt | processing | 1497.308 | 2.965 | 43.119 | 43.119 | 18.054 | 71.739 | 14.542 | worse | 0 |
| 4 | edd | duedate | 1624.937 | 11.742 | 170.748 | 170.748 | 24.327 | 354.607 | 14.542 | worse | 0 |
| 5 | pfifo | duedate | 1630.032 | 12.092 | 175.843 | 175.843 | 33.960 | 357.272 | 14.542 | worse | 0 |
| 6 | v2rl310 | policy | 1783.322 | 22.633 | 329.133 | 329.133 | 149.084 | 533.499 | 14.542 | worse | 0 |
| 7 | v2rl309 | policy | 1820.647 | 25.200 | 366.458 | 366.458 | 119.185 | 710.169 | 14.542 | worse | 0 |
| 8 | v2rl302 | policy | 1845.419 | 26.904 | 391.231 | 391.231 | 160.303 | 663.307 | 14.542 | worse | 0 |
| 9 | v2rl304 | policy | 1897.238 | 30.467 | 443.049 | 443.049 | 181.273 | 768.904 | 14.542 | worse | 0 |
| 10 | random | random | 1934.059 | 32.999 | 479.870 | 479.870 | 255.881 | 734.382 | 14.542 | worse | 0 |
| 11 | v2rl308 | policy | 2004.557 | 37.847 | 550.368 | 550.368 | 219.201 | 987.655 | 14.542 | worse | 0 |
| 12 | v2rl307 | policy | 2487.115 | 71.031 | 1032.926 | 1032.926 | 506.925 | 1626.516 | 14.542 | worse | 0 |
| 13 | v2rl305 | policy | 2503.703 | 72.172 | 1049.515 | 1049.515 | 544.166 | 1604.435 | 14.542 | worse | 0 |
| 14 | v2rl301 | policy | 2689.958 | 84.980 | 1235.770 | 1235.770 | 653.307 | 1876.618 | 14.542 | worse | 0 |
| 15 | v2rl306 | policy | 2752.688 | 89.294 | 1298.499 | 1298.499 | 694.865 | 1951.519 | 14.542 | worse | 0 |
| 16 | v2rl303 | policy | 2796.124 | 92.281 | 1341.935 | 1341.935 | 673.686 | 2061.176 | 14.542 | worse | 0 |
| 17 | lpt | processing | 3138.480 | 115.823 | 1684.291 | 1684.291 | 890.089 | 2573.782 | 14.542 | worse | 0 |


**pmp3 / verdict** (preventive work mapped to P3) - best v2rl302 (mean 459.647), 180 configurations. Equivalence set: 17 of 17 methods.

| rank | method | family | mean | pct_from_best | abs_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | v2rl302 | policy | 459.647 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 4.596 | equivalent | 1 |
| 2 | v2rl310 | policy | 459.671 | 0.005 | 0.024 | 0.024 | -0.008 | 0.065 | 4.596 | equivalent | 1 |
| 3 | v2rl308 | policy | 459.697 | 0.011 | 0.050 | 0.050 | 0.004 | 0.114 | 4.596 | equivalent | 1 |
| 4 | v2rl304 | policy | 459.713 | 0.014 | 0.065 | 0.065 | -0.002 | 0.171 | 4.596 | equivalent | 1 |
| 5 | v2rl307 | policy | 459.715 | 0.015 | 0.068 | 0.068 | 0.011 | 0.145 | 4.596 | equivalent | 1 |
| 6 | v2rl301 | policy | 459.737 | 0.020 | 0.090 | 0.090 | 0.023 | 0.183 | 4.596 | equivalent | 1 |
| 7 | v2rl305 | policy | 459.749 | 0.022 | 0.102 | 0.102 | 0.020 | 0.214 | 4.596 | equivalent | 1 |
| 8 | v2rl303 | policy | 459.750 | 0.022 | 0.102 | 0.102 | 0.011 | 0.231 | 4.596 | equivalent | 1 |
| 9 | edd | duedate | 459.836 | 0.041 | 0.189 | 0.189 | 0.023 | 0.406 | 4.596 | equivalent | 1 |
| 9 | pfifo | duedate | 459.836 | 0.041 | 0.189 | 0.189 | 0.027 | 0.406 | 4.596 | equivalent | 1 |
| 11 | v2rl306 | policy | 459.848 | 0.044 | 0.201 | 0.201 | 0.023 | 0.517 | 4.596 | equivalent | 1 |
| 12 | v2rl309 | policy | 459.974 | 0.071 | 0.327 | 0.327 | 0.054 | 0.741 | 4.596 | equivalent | 1 |
| 13 | wmdd | weighted | 460.335 | 0.150 | 0.688 | 0.688 | 0.202 | 1.320 | 4.596 | equivalent | 1 |
| 14 | atc | weighted | 460.562 | 0.199 | 0.915 | 0.915 | 0.305 | 1.689 | 4.596 | equivalent | 1 |
| 15 | lpt | processing | 460.587 | 0.204 | 0.940 | 0.940 | 0.102 | 2.491 | 4.596 | equivalent | 1 |
| 16 | random | random | 461.326 | 0.365 | 1.679 | 1.679 | 0.610 | 3.235 | 4.596 | equivalent | 1 |
| 17 | wspt | processing | 461.807 | 0.470 | 2.160 | 2.160 | 1.064 | 3.522 | 4.596 | equivalent | 1 |


**pmp3 / campus1** (preventive work mapped to P3) - best atc (mean 90.558), 30 configurations. Equivalence set: 15 of 17 methods.

| rank | method | family | mean | pct_from_best | abs_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | atc | weighted | 90.558 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | edd | duedate | 90.558 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | lpt | processing | 90.558 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | pfifo | duedate | 90.558 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl301 | policy | 90.558 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl302 | policy | 90.558 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl303 | policy | 90.558 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl304 | policy | 90.558 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl305 | policy | 90.558 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl306 | policy | 90.558 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl307 | policy | 90.558 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl308 | policy | 90.558 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | v2rl310 | policy | 90.558 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 1 | wmdd | weighted | 90.558 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | equivalent | 1 |
| 15 | v2rl309 | policy | 90.828 | 0.298 | 0.270 | 0.270 | 0.000 | 0.809 | 1.000 | equivalent | 1 |
| 16 | random | random | 91.262 | 0.777 | 0.704 | 0.704 | 0.000 | 1.775 | 1.000 | inconclusive | 0 |
| 17 | wspt | processing | 91.494 | 1.034 | 0.936 | 0.936 | 0.000 | 2.406 | 1.000 | inconclusive | 0 |


**pmp3 / campus2** (preventive work mapped to P3) - best wmdd (mean 1231.344), 17 configurations. Equivalence set: 1 of 17 methods.

| rank | method | family | mean | pct_from_best | abs_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | wmdd | weighted | 1231.344 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 12.313 | equivalent | 1 |
| 2 | atc | weighted | 1268.159 | 2.990 | 36.814 | 36.814 | 10.390 | 67.681 | 12.313 | inconclusive | 0 |
| 3 | wspt | processing | 1305.967 | 6.060 | 74.623 | 74.623 | 35.805 | 117.729 | 12.313 | worse | 0 |
| 4 | edd | duedate | 1321.473 | 7.320 | 90.129 | 90.129 | -20.612 | 239.888 | 12.313 | inconclusive | 0 |
| 4 | pfifo | duedate | 1321.473 | 7.320 | 90.129 | 90.129 | -19.482 | 239.118 | 12.313 | inconclusive | 0 |
| 6 | v2rl310 | policy | 1331.526 | 8.136 | 100.181 | 100.181 | 2.779 | 220.291 | 12.313 | inconclusive | 0 |
| 7 | v2rl302 | policy | 1432.731 | 16.355 | 201.387 | 201.387 | 65.613 | 366.361 | 12.313 | worse | 0 |
| 8 | v2rl304 | policy | 1455.983 | 18.243 | 224.639 | 224.639 | 28.509 | 515.368 | 12.313 | worse | 0 |
| 9 | v2rl309 | policy | 1485.120 | 20.610 | 253.776 | 253.776 | 60.545 | 555.091 | 12.313 | worse | 0 |
| 10 | v2rl308 | policy | 1501.857 | 21.969 | 270.513 | 270.513 | 9.459 | 679.268 | 12.313 | inconclusive | 0 |
| 11 | random | random | 1643.508 | 33.473 | 412.164 | 412.164 | 212.878 | 651.389 | 12.313 | worse | 0 |
| 12 | v2rl305 | policy | 1727.387 | 40.285 | 496.043 | 496.043 | 184.041 | 911.566 | 12.313 | worse | 0 |
| 13 | v2rl307 | policy | 1759.603 | 42.901 | 528.259 | 528.259 | 190.447 | 963.381 | 12.313 | worse | 0 |
| 14 | v2rl301 | policy | 1859.614 | 51.023 | 628.269 | 628.269 | 221.086 | 1109.056 | 12.313 | worse | 0 |
| 15 | v2rl306 | policy | 1873.288 | 52.134 | 641.944 | 641.944 | 257.799 | 1101.677 | 12.313 | worse | 0 |
| 16 | v2rl303 | policy | 2244.843 | 82.308 | 1013.499 | 1013.499 | 471.916 | 1622.442 | 12.313 | worse | 0 |
| 17 | lpt | processing | 2622.329 | 112.965 | 1390.985 | 1390.985 | 679.096 | 2213.184 | 12.313 | worse | 0 |


## R4.8 addendum: equivalence sets read against realized utilization

The three crew sizings are the same weeks under three estimators, so pooling their configurations and binning them on REALIZED utilization is the reading R4.8 prescribes. Verdict campuses only; the cluster bootstrap resamples base instances, so the three configurations of one week count as one observation.


**u_bin <0.5** (realized u in [0.12, 0.50], 175 configurations over 85 base instances) - best v2rl310, set of 17.

| rank | method | mean | pct_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|
| 8 | edd | 286.975 | 0.020 | 0.056 | 0.000 | 0.152 | 2.869 | equivalent | 1 |
| 8 | pfifo | 286.975 | 0.020 | 0.056 | 0.000 | 0.152 | 2.869 | equivalent | 1 |
| 13 | lpt | 287.378 | 0.160 | 0.460 | 0.014 | 1.084 | 2.869 | equivalent | 1 |
| 14 | wmdd | 287.406 | 0.170 | 0.488 | 0.046 | 1.091 | 2.869 | equivalent | 1 |
| 15 | atc | 287.486 | 0.198 | 0.568 | 0.041 | 1.235 | 2.869 | equivalent | 1 |
| 16 | random | 287.712 | 0.277 | 0.794 | 0.188 | 1.603 | 2.869 | equivalent | 1 |
| 17 | wspt | 288.078 | 0.404 | 1.160 | 0.361 | 2.213 | 2.869 | equivalent | 1 |


**u_bin 0.5-0.8** (realized u in [0.50, 0.80], 171 configurations over 107 base instances) - best v2rl302, set of 8.

| rank | method | mean | pct_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|
| 6 | wmdd | 670.731 | 0.207 | 1.387 | 0.430 | 2.598 | 6.693 | equivalent | 1 |
| 7 | atc | 671.380 | 0.304 | 2.035 | 0.633 | 3.776 | 6.693 | equivalent | 1 |
| 8 | edd | 673.201 | 0.576 | 3.857 | 0.028 | 11.486 | 6.693 | inconclusive | 0 |
| 8 | pfifo | 673.201 | 0.576 | 3.857 | 0.021 | 11.504 | 6.693 | inconclusive | 0 |
| 10 | wspt | 673.234 | 0.581 | 3.889 | 1.811 | 6.470 | 6.693 | equivalent | 1 |
| 16 | random | 680.579 | 1.678 | 11.235 | 2.280 | 27.131 | 6.693 | inconclusive | 0 |
| 17 | lpt | 681.556 | 1.824 | 12.212 | 1.550 | 29.896 | 6.693 | inconclusive | 0 |


**u_bin 0.8-1.0** (realized u in [0.80, 0.98], 58 configurations over 52 base instances) - best v2rl308, set of 11.

| rank | method | mean | pct_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|
| 4 | edd | 770.643 | 0.050 | 0.385 | -0.005 | 1.007 | 7.703 | equivalent | 1 |
| 4 | pfifo | 770.643 | 0.050 | 0.385 | -0.005 | 0.986 | 7.703 | equivalent | 1 |
| 8 | wmdd | 771.567 | 0.170 | 1.309 | 0.064 | 3.308 | 7.703 | equivalent | 1 |
| 11 | atc | 772.381 | 0.276 | 2.123 | -1.042 | 5.642 | 7.703 | equivalent | 1 |
| 15 | wspt | 775.806 | 0.720 | 5.548 | 1.026 | 10.796 | 7.703 | inconclusive | 0 |
| 16 | random | 791.175 | 2.716 | 20.917 | 8.157 | 37.499 | 7.703 | worse | 0 |
| 17 | lpt | 808.706 | 4.992 | 38.448 | 5.705 | 86.832 | 7.703 | inconclusive | 0 |


**u_bin 1.0-1.2** (realized u in [1.00, 1.19], 29 configurations over 29 base instances) - best v2rl301, set of 1.

| rank | method | mean | pct_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|
| 2 | atc | 430.975 | 0.869 | 3.714 | -0.828 | 10.505 | 4.273 | inconclusive | 0 |
| 11 | edd | 436.692 | 2.207 | 9.431 | -0.199 | 27.454 | 4.273 | inconclusive | 0 |
| 11 | pfifo | 436.692 | 2.207 | 9.431 | -0.199 | 27.554 | 4.273 | inconclusive | 0 |
| 13 | wmdd | 437.541 | 2.406 | 10.280 | 0.000 | 27.153 | 4.273 | inconclusive | 0 |
| 15 | random | 442.119 | 3.478 | 14.859 | 2.540 | 30.455 | 4.273 | inconclusive | 0 |
| 16 | wspt | 443.878 | 3.889 | 16.618 | 1.579 | 39.502 | 4.273 | inconclusive | 0 |
| 17 | lpt | 477.888 | 11.849 | 50.627 | 4.130 | 127.610 | 4.273 | inconclusive | 0 |


**u_bin >=1.2** (realized u in [1.20, 10.98], 107 configurations over 51 base instances) - best v2rl302, set of 4.

| rank | method | mean | pct_from_best | mean_diff | ci_lo | ci_hi | margin | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|
| 5 | wmdd | 192.989 | 0.542 | 1.041 | -0.078 | 2.726 | 1.919 | inconclusive | 0 |
| 6 | atc | 193.280 | 0.694 | 1.333 | -0.150 | 3.861 | 1.919 | inconclusive | 0 |
| 7 | random | 195.226 | 1.708 | 3.278 | 0.611 | 7.289 | 1.919 | inconclusive | 0 |
| 13 | edd | 195.723 | 1.967 | 3.776 | 0.015 | 11.094 | 1.919 | inconclusive | 0 |
| 13 | pfifo | 195.723 | 1.967 | 3.776 | 0.018 | 11.173 | 1.919 | inconclusive | 0 |
| 15 | wspt | 195.926 | 2.073 | 3.979 | 1.258 | 7.935 | 1.919 | inconclusive | 0 |
| 17 | lpt | 202.235 | 5.360 | 10.287 | 0.705 | 23.680 | 1.919 | inconclusive | 0 |


## Every method against the baseline arm's best method

The reference of each row is the method with the lowest mean on the BASELINE arm of that stratum, held fixed while the arm changes; this is the comparison that says whether the baseline's choice survives.

| check | arm | stratum | method | reference | n_configs | mean_method | mean_ref | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pmodel | sum | verdict | edd | v2rl302 | 180 | 444.869 | 444.681 | 0.188 | 0.025 | 0.408 | 4.447 | 0.071 | equivalent |
| pmodel | sum | verdict | pfifo | v2rl302 | 180 | 444.869 | 444.681 | 0.188 | 0.026 | 0.403 | 4.447 | 0.071 | equivalent |
| pmodel | sum | verdict | wspt | v2rl302 | 180 | 446.646 | 444.681 | 1.965 | 0.883 | 3.236 | 4.447 | 0.000 | equivalent |
| pmodel | sum | verdict | atc | v2rl302 | 180 | 445.555 | 444.681 | 0.874 | 0.271 | 1.642 | 4.447 | 0.051 | equivalent |
| pmodel | sum | verdict | wmdd | v2rl302 | 180 | 445.332 | 444.681 | 0.651 | 0.165 | 1.265 | 4.447 | 0.063 | equivalent |
| pmodel | sum | verdict | lpt | v2rl302 | 180 | 445.579 | 444.681 | 0.898 | 0.073 | 2.420 | 4.447 | 0.038 | equivalent |
| pmodel | sum | verdict | random | v2rl302 | 180 | 446.316 | 444.681 | 1.635 | 0.575 | 3.136 | 4.447 | 0.001 | equivalent |
| pmodel | sum | campus1 | edd | atc | 30 | 80.417 | 80.417 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| pmodel | sum | campus1 | pfifo | atc | 30 | 80.417 | 80.417 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| pmodel | sum | campus1 | wspt | atc | 30 | 81.297 | 80.417 | 0.880 | 0.000 | 2.293 | 1.000 | 1.000 | inconclusive |
| pmodel | sum | campus1 | wmdd | atc | 30 | 80.417 | 80.417 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| pmodel | sum | campus1 | lpt | atc | 30 | 80.417 | 80.417 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| pmodel | sum | campus1 | random | atc | 30 | 81.121 | 80.417 | 0.704 | 0.000 | 1.775 | 1.000 | 1.000 | inconclusive |
| pmodel | sum | campus2 | edd | wmdd | 17 | 1311.322 | 1218.229 | 93.093 | -15.486 | 237.024 | 12.182 | 1.000 | inconclusive |
| pmodel | sum | campus2 | pfifo | wmdd | 17 | 1311.322 | 1218.229 | 93.093 | -15.460 | 237.433 | 12.182 | 1.000 | inconclusive |
| pmodel | sum | campus2 | wspt | wmdd | 17 | 1291.239 | 1218.229 | 73.010 | 35.147 | 115.046 | 12.182 | 0.009 | worse |
| pmodel | sum | campus2 | atc | wmdd | 17 | 1252.116 | 1218.229 | 33.887 | 11.738 | 59.799 | 12.182 | 0.014 | inconclusive |
| pmodel | sum | campus2 | lpt | wmdd | 17 | 2615.112 | 1218.229 | 1396.883 | 681.947 | 2231.971 | 12.182 | 0.009 | worse |
| pmodel | sum | campus2 | random | wmdd | 17 | 1636.031 | 1218.229 | 417.802 | 213.525 | 658.847 | 12.182 | 0.009 | worse |
| pmodel | max | verdict | edd | v2rl302 | 180 | 66.352 | 66.440 | -0.088 | -1.758 | 1.328 | 1.000 | 0.815 | inconclusive |
| pmodel | max | verdict | pfifo | v2rl302 | 180 | 66.352 | 66.440 | -0.088 | -1.699 | 1.311 | 1.000 | 0.815 | inconclusive |
| pmodel | max | verdict | wspt | v2rl302 | 180 | 70.811 | 66.440 | 4.371 | 0.352 | 9.035 | 1.000 | 0.000 | inconclusive |
| pmodel | max | verdict | atc | v2rl302 | 180 | 66.845 | 66.440 | 0.405 | -2.461 | 2.811 | 1.000 | 0.206 | inconclusive |
| pmodel | max | verdict | wmdd | v2rl302 | 180 | 66.903 | 66.440 | 0.463 | -2.112 | 2.769 | 1.000 | 0.206 | inconclusive |
| pmodel | max | verdict | lpt | v2rl302 | 180 | 102.848 | 66.440 | 36.408 | 13.620 | 68.263 | 1.000 | 0.000 | worse |
| pmodel | max | verdict | random | v2rl302 | 180 | 82.211 | 66.440 | 15.771 | 6.329 | 27.843 | 1.000 | 0.000 | worse |
| pmodel | max | campus1 | edd | atc | 30 | 40.504 | 40.504 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| pmodel | max | campus1 | pfifo | atc | 30 | 40.504 | 40.504 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| pmodel | max | campus1 | wspt | atc | 30 | 41.384 | 40.504 | 0.880 | 0.000 | 2.293 | 1.000 | 1.000 | inconclusive |
| pmodel | max | campus1 | wmdd | atc | 30 | 40.504 | 40.504 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| pmodel | max | campus1 | lpt | atc | 30 | 40.504 | 40.504 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| pmodel | max | campus1 | random | atc | 30 | 40.785 | 40.504 | 0.281 | 0.000 | 0.707 | 1.000 | 1.000 | equivalent |
| pmodel | max | campus2 | edd | wmdd | 17 | 530.673 | 444.208 | 86.466 | -3.794 | 231.380 | 4.442 | 0.656 | inconclusive |
| pmodel | max | campus2 | pfifo | wmdd | 17 | 530.673 | 444.208 | 86.466 | -3.544 | 234.371 | 4.442 | 0.656 | inconclusive |
| pmodel | max | campus2 | wspt | wmdd | 17 | 575.975 | 444.208 | 131.767 | 60.906 | 210.799 | 4.442 | 0.025 | worse |
| pmodel | max | campus2 | atc | wmdd | 17 | 479.024 | 444.208 | 34.816 | 5.807 | 68.772 | 4.442 | 0.253 | worse |
| pmodel | max | campus2 | lpt | wmdd | 17 | 2158.563 | 444.208 | 1714.356 | 828.816 | 2759.115 | 4.442 | 0.005 | worse |
| pmodel | max | campus2 | random | wmdd | 17 | 1004.701 | 444.208 | 560.494 | 310.422 | 842.671 | 4.442 | 0.004 | worse |
| pmodel | single | verdict | edd | v2rl302 | 179 | 20.088 | 21.548 | -1.460 | -6.125 | 1.864 | 1.000 | 1.000 | inconclusive |
| pmodel | single | verdict | pfifo | v2rl302 | 179 | 20.088 | 21.548 | -1.460 | -6.135 | 1.882 | 1.000 | 1.000 | inconclusive |
| pmodel | single | verdict | wspt | v2rl302 | 179 | 19.775 | 21.548 | -1.773 | -8.186 | 1.967 | 1.000 | 0.019 | inconclusive |
| pmodel | single | verdict | atc | v2rl302 | 179 | 17.526 | 21.548 | -4.022 | -11.213 | 0.054 | 1.000 | 0.710 | inconclusive |
| pmodel | single | verdict | wmdd | v2rl302 | 179 | 17.193 | 21.548 | -4.355 | -12.488 | 0.116 | 1.000 | 0.705 | inconclusive |
| pmodel | single | verdict | lpt | v2rl302 | 179 | 78.338 | 21.548 | 56.790 | 14.379 | 132.752 | 1.000 | 0.000 | worse |
| pmodel | single | verdict | random | v2rl302 | 179 | 42.751 | 21.548 | 21.203 | 6.263 | 47.269 | 1.000 | 0.000 | worse |
| pmodel | single | campus1 | edd | atc | 30 | 31.180 | 31.180 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| pmodel | single | campus1 | pfifo | atc | 30 | 31.180 | 31.180 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| pmodel | single | campus1 | wspt | atc | 30 | 32.349 | 31.180 | 1.168 | 0.000 | 2.937 | 1.000 | 1.000 | inconclusive |
| pmodel | single | campus1 | wmdd | atc | 30 | 31.180 | 31.180 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| pmodel | single | campus1 | lpt | atc | 30 | 31.180 | 31.180 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| pmodel | single | campus1 | random | atc | 30 | 31.189 | 31.180 | 0.009 | 0.000 | 0.027 | 1.000 | 1.000 | equivalent |
| pmodel | single | campus2 | edd | wmdd | 17 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| pmodel | single | campus2 | pfifo | wmdd | 17 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| pmodel | single | campus2 | wspt | wmdd | 17 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| pmodel | single | campus2 | atc | wmdd | 17 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| pmodel | single | campus2 | lpt | wmdd | 17 | 36.344 | 0.000 | 36.344 | 4.523 | 76.449 | 1.000 | 0.259 | worse |
| pmodel | single | campus2 | random | wmdd | 17 | 6.412 | 0.000 | 6.412 | 0.000 | 18.818 | 1.000 | 0.899 | inconclusive |
| capacity | q0.95 | verdict | edd | v2rl302 | 180 | 444.869 | 444.681 | 0.188 | 0.025 | 0.400 | 4.447 | 0.071 | equivalent |
| capacity | q0.95 | verdict | pfifo | v2rl302 | 180 | 444.869 | 444.681 | 0.188 | 0.027 | 0.404 | 4.447 | 0.071 | equivalent |
| capacity | q0.95 | verdict | wspt | v2rl302 | 180 | 446.646 | 444.681 | 1.965 | 0.888 | 3.278 | 4.447 | 0.000 | equivalent |
| capacity | q0.95 | verdict | atc | v2rl302 | 180 | 445.555 | 444.681 | 0.874 | 0.252 | 1.629 | 4.447 | 0.051 | equivalent |
| capacity | q0.95 | verdict | wmdd | v2rl302 | 180 | 445.332 | 444.681 | 0.651 | 0.156 | 1.273 | 4.447 | 0.063 | equivalent |
| capacity | q0.95 | verdict | lpt | v2rl302 | 180 | 445.579 | 444.681 | 0.898 | 0.079 | 2.421 | 4.447 | 0.038 | equivalent |
| capacity | q0.95 | verdict | random | v2rl302 | 180 | 446.316 | 444.681 | 1.635 | 0.572 | 3.164 | 4.447 | 0.001 | equivalent |
| capacity | q0.95 | campus1 | edd | atc | 30 | 80.417 | 80.417 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| capacity | q0.95 | campus1 | pfifo | atc | 30 | 80.417 | 80.417 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| capacity | q0.95 | campus1 | wspt | atc | 30 | 81.297 | 80.417 | 0.880 | 0.000 | 2.293 | 1.000 | 1.000 | inconclusive |
| capacity | q0.95 | campus1 | wmdd | atc | 30 | 80.417 | 80.417 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| capacity | q0.95 | campus1 | lpt | atc | 30 | 80.417 | 80.417 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| capacity | q0.95 | campus1 | random | atc | 30 | 81.121 | 80.417 | 0.704 | 0.000 | 1.775 | 1.000 | 1.000 | inconclusive |
| capacity | q0.95 | campus2 | edd | wmdd | 17 | 1311.322 | 1218.229 | 93.093 | -16.414 | 245.193 | 12.182 | 1.000 | inconclusive |
| capacity | q0.95 | campus2 | pfifo | wmdd | 17 | 1311.322 | 1218.229 | 93.093 | -17.262 | 238.294 | 12.182 | 1.000 | inconclusive |
| capacity | q0.95 | campus2 | wspt | wmdd | 17 | 1291.239 | 1218.229 | 73.010 | 34.704 | 114.839 | 12.182 | 0.009 | worse |
| capacity | q0.95 | campus2 | atc | wmdd | 17 | 1252.116 | 1218.229 | 33.887 | 12.518 | 59.667 | 12.182 | 0.014 | worse |
| capacity | q0.95 | campus2 | lpt | wmdd | 17 | 2615.112 | 1218.229 | 1396.883 | 692.065 | 2227.514 | 12.182 | 0.009 | worse |
| capacity | q0.95 | campus2 | random | wmdd | 17 | 1636.031 | 1218.229 | 417.802 | 214.676 | 666.899 | 12.182 | 0.009 | worse |
| capacity | q0.90 | verdict | edd | v2rl302 | 180 | 446.523 | 446.203 | 0.321 | 0.036 | 0.741 | 4.462 | 0.076 | equivalent |
| capacity | q0.90 | verdict | pfifo | v2rl302 | 180 | 446.523 | 446.203 | 0.321 | 0.035 | 0.749 | 4.462 | 0.076 | equivalent |
| capacity | q0.90 | verdict | wspt | v2rl302 | 180 | 448.909 | 446.203 | 2.706 | 1.419 | 4.262 | 4.462 | 0.000 | equivalent |
| capacity | q0.90 | verdict | atc | v2rl302 | 180 | 447.404 | 446.203 | 1.202 | 0.376 | 2.239 | 4.462 | 0.009 | equivalent |
| capacity | q0.90 | verdict | wmdd | v2rl302 | 180 | 446.979 | 446.203 | 0.776 | 0.215 | 1.485 | 4.462 | 0.015 | equivalent |
| capacity | q0.90 | verdict | lpt | v2rl302 | 180 | 449.608 | 446.203 | 3.405 | 0.208 | 8.005 | 4.462 | 0.076 | inconclusive |
| capacity | q0.90 | verdict | random | v2rl302 | 180 | 448.965 | 446.203 | 2.762 | 1.004 | 5.070 | 4.462 | 0.000 | inconclusive |
| capacity | q0.90 | campus1 | edd | atc | 30 | 80.417 | 80.417 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| capacity | q0.90 | campus1 | pfifo | atc | 30 | 80.417 | 80.417 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| capacity | q0.90 | campus1 | wspt | atc | 30 | 81.586 | 80.417 | 1.168 | 0.000 | 2.937 | 1.000 | 1.000 | inconclusive |
| capacity | q0.90 | campus1 | wmdd | atc | 30 | 80.417 | 80.417 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| capacity | q0.90 | campus1 | lpt | atc | 30 | 80.417 | 80.417 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| capacity | q0.90 | campus1 | random | atc | 30 | 80.888 | 80.417 | 0.470 | 0.000 | 1.407 | 1.000 | 1.000 | inconclusive |
| capacity | q0.90 | campus2 | edd | wmdd | 17 | 1770.180 | 1417.144 | 353.036 | 58.716 | 744.266 | 14.171 | 0.601 | worse |
| capacity | q0.90 | campus2 | pfifo | wmdd | 17 | 1770.180 | 1417.144 | 353.036 | 63.081 | 751.662 | 14.171 | 0.601 | worse |
| capacity | q0.90 | campus2 | wspt | wmdd | 17 | 1519.547 | 1417.144 | 102.404 | 50.692 | 164.519 | 14.171 | 0.008 | worse |
| capacity | q0.90 | campus2 | atc | wmdd | 17 | 1480.309 | 1417.144 | 63.165 | 26.083 | 106.189 | 14.171 | 0.008 | worse |
| capacity | q0.90 | campus2 | lpt | wmdd | 17 | 4148.896 | 1417.144 | 2731.752 | 1324.641 | 4392.231 | 14.171 | 0.005 | worse |
| capacity | q0.90 | campus2 | random | wmdd | 17 | 2333.274 | 1417.144 | 916.130 | 396.314 | 1538.671 | 14.171 | 0.006 | worse |
| capacity | q0.75 | verdict | edd | v2rl302 | 180 | 462.173 | 456.445 | 5.728 | -0.076 | 14.359 | 4.564 | 0.137 | inconclusive |
| capacity | q0.75 | verdict | pfifo | v2rl302 | 180 | 462.173 | 456.445 | 5.728 | -0.095 | 14.545 | 4.564 | 0.137 | inconclusive |
| capacity | q0.75 | verdict | wspt | v2rl302 | 180 | 462.056 | 456.445 | 5.610 | 2.860 | 8.730 | 4.564 | 0.000 | inconclusive |
| capacity | q0.75 | verdict | atc | v2rl302 | 180 | 457.559 | 456.445 | 1.114 | -2.144 | 3.896 | 4.564 | 0.137 | equivalent |
| capacity | q0.75 | verdict | wmdd | v2rl302 | 180 | 458.136 | 456.445 | 1.691 | 0.049 | 3.405 | 4.564 | 0.083 | equivalent |
| capacity | q0.75 | verdict | lpt | v2rl302 | 180 | 489.481 | 456.445 | 33.036 | 13.202 | 58.249 | 4.564 | 0.000 | worse |
| capacity | q0.75 | verdict | random | v2rl302 | 180 | 473.205 | 456.445 | 16.760 | 6.269 | 34.111 | 4.564 | 0.000 | worse |
| capacity | q0.75 | campus1 | edd | atc | 30 | 80.478 | 80.478 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| capacity | q0.75 | campus1 | pfifo | atc | 30 | 80.478 | 80.478 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| capacity | q0.75 | campus1 | wspt | atc | 30 | 82.632 | 80.478 | 2.154 | -0.001 | 5.140 | 1.000 | 0.865 | inconclusive |
| capacity | q0.75 | campus1 | wmdd | atc | 30 | 80.478 | 80.478 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| capacity | q0.75 | campus1 | lpt | atc | 30 | 81.114 | 80.478 | 0.636 | 0.000 | 1.907 | 1.000 | 1.000 | inconclusive |
| capacity | q0.75 | campus1 | random | atc | 30 | 81.393 | 80.478 | 0.915 | -0.001 | 2.414 | 1.000 | 1.000 | inconclusive |
| capacity | q0.75 | campus2 | edd | wmdd | 17 | 5629.989 | 2954.988 | 2675.001 | 1178.180 | 4284.019 | 29.550 | 0.022 | worse |
| capacity | q0.75 | campus2 | pfifo | wmdd | 17 | 5620.576 | 2954.988 | 2665.588 | 1206.602 | 4246.987 | 29.550 | 0.022 | worse |
| capacity | q0.75 | campus2 | wspt | wmdd | 17 | 2966.211 | 2954.988 | 11.223 | -476.206 | 323.051 | 29.550 | 0.068 | inconclusive |
| capacity | q0.75 | campus2 | atc | wmdd | 17 | 2830.055 | 2954.988 | -124.933 | -590.021 | 156.816 | 29.550 | 0.148 | inconclusive |
| capacity | q0.75 | campus2 | lpt | wmdd | 17 | 15682.750 | 2954.988 | 12727.762 | 7543.360 | 18429.331 | 29.550 | 0.000 | worse |
| capacity | q0.75 | campus2 | random | wmdd | 17 | 7278.249 | 2954.988 | 4323.261 | 2555.869 | 6193.521 | 29.550 | 0.000 | worse |
| backdate | baseline | verdict | edd | v2rl302 | 180 | 444.869 | 444.681 | 0.188 | 0.026 | 0.407 | 4.447 | 0.071 | equivalent |
| backdate | baseline | verdict | pfifo | v2rl302 | 180 | 444.869 | 444.681 | 0.188 | 0.026 | 0.407 | 4.447 | 0.071 | equivalent |
| backdate | baseline | verdict | wspt | v2rl302 | 180 | 446.646 | 444.681 | 1.965 | 0.888 | 3.289 | 4.447 | 0.000 | equivalent |
| backdate | baseline | verdict | atc | v2rl302 | 180 | 445.555 | 444.681 | 0.874 | 0.251 | 1.655 | 4.447 | 0.051 | equivalent |
| backdate | baseline | verdict | wmdd | v2rl302 | 180 | 445.332 | 444.681 | 0.651 | 0.164 | 1.249 | 4.447 | 0.063 | equivalent |
| backdate | baseline | verdict | lpt | v2rl302 | 180 | 445.579 | 444.681 | 0.898 | 0.075 | 2.409 | 4.447 | 0.038 | equivalent |
| backdate | baseline | verdict | random | v2rl302 | 180 | 446.316 | 444.681 | 1.635 | 0.572 | 3.091 | 4.447 | 0.001 | equivalent |
| backdate | baseline | campus1 | edd | atc | 30 | 80.417 | 80.417 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| backdate | baseline | campus1 | pfifo | atc | 30 | 80.417 | 80.417 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| backdate | baseline | campus1 | wspt | atc | 30 | 81.297 | 80.417 | 0.880 | 0.000 | 2.293 | 1.000 | 1.000 | inconclusive |
| backdate | baseline | campus1 | wmdd | atc | 30 | 80.417 | 80.417 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| backdate | baseline | campus1 | lpt | atc | 30 | 80.417 | 80.417 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| backdate | baseline | campus1 | random | atc | 30 | 81.121 | 80.417 | 0.704 | 0.000 | 1.775 | 1.000 | 1.000 | inconclusive |
| backdate | baseline | campus2 | edd | wmdd | 17 | 1311.322 | 1218.229 | 93.093 | -16.081 | 241.625 | 12.182 | 1.000 | inconclusive |
| backdate | baseline | campus2 | pfifo | wmdd | 17 | 1311.322 | 1218.229 | 93.093 | -17.152 | 243.837 | 12.182 | 1.000 | inconclusive |
| backdate | baseline | campus2 | wspt | wmdd | 17 | 1291.239 | 1218.229 | 73.010 | 35.826 | 116.207 | 12.182 | 0.009 | worse |
| backdate | baseline | campus2 | atc | wmdd | 17 | 1252.116 | 1218.229 | 33.887 | 12.382 | 59.916 | 12.182 | 0.014 | worse |
| backdate | baseline | campus2 | lpt | wmdd | 17 | 2615.112 | 1218.229 | 1396.883 | 669.994 | 2234.612 | 12.182 | 0.009 | worse |
| backdate | baseline | campus2 | random | wmdd | 17 | 1636.031 | 1218.229 | 417.802 | 211.745 | 665.894 | 12.182 | 0.009 | worse |
| backdate | backdate | verdict | edd | v2rl302 | 180 | 444.932 | 444.940 | -0.008 | -0.145 | 0.170 | 4.449 | 0.628 | equivalent |
| backdate | backdate | verdict | pfifo | v2rl302 | 180 | 444.932 | 444.940 | -0.008 | -0.145 | 0.168 | 4.449 | 0.628 | equivalent |
| backdate | backdate | verdict | wspt | v2rl302 | 180 | 448.177 | 444.940 | 3.237 | 1.119 | 6.355 | 4.449 | 0.000 | inconclusive |
| backdate | backdate | verdict | atc | v2rl302 | 180 | 445.768 | 444.940 | 0.827 | 0.111 | 1.786 | 4.449 | 0.260 | equivalent |
| backdate | backdate | verdict | wmdd | v2rl302 | 180 | 445.388 | 444.940 | 0.448 | 0.061 | 0.955 | 4.449 | 0.260 | equivalent |
| backdate | backdate | verdict | lpt | v2rl302 | 180 | 448.978 | 444.940 | 4.037 | 0.484 | 9.636 | 4.449 | 0.125 | inconclusive |
| backdate | backdate | verdict | random | v2rl302 | 180 | 447.881 | 444.940 | 2.941 | 0.589 | 6.271 | 4.449 | 0.001 | inconclusive |
| backdate | backdate | campus1 | edd | atc | 30 | 80.471 | 80.692 | -0.220 | -0.800 | 0.140 | 1.000 | 1.000 | equivalent |
| backdate | backdate | campus1 | pfifo | atc | 30 | 80.471 | 80.692 | -0.220 | -0.800 | 0.140 | 1.000 | 1.000 | equivalent |
| backdate | backdate | campus1 | wspt | atc | 30 | 81.025 | 80.692 | 0.333 | -0.267 | 1.067 | 1.000 | 1.000 | inconclusive |
| backdate | backdate | campus1 | wmdd | atc | 30 | 80.605 | 80.692 | -0.087 | -0.400 | 0.140 | 1.000 | 1.000 | equivalent |
| backdate | backdate | campus1 | lpt | atc | 30 | 80.471 | 80.692 | -0.220 | -0.800 | 0.140 | 1.000 | 1.000 | equivalent |
| backdate | backdate | campus1 | random | atc | 30 | 80.605 | 80.692 | -0.087 | -0.400 | 0.140 | 1.000 | 1.000 | equivalent |
| backdate | backdate | campus2 | edd | wmdd | 17 | 1292.865 | 1265.913 | 26.951 | -34.498 | 121.039 | 12.659 | 0.941 | inconclusive |
| backdate | backdate | campus2 | pfifo | wmdd | 17 | 1292.865 | 1265.913 | 26.951 | -34.430 | 119.302 | 12.659 | 0.941 | inconclusive |
| backdate | backdate | campus2 | wspt | wmdd | 17 | 1357.696 | 1265.913 | 91.783 | 26.095 | 165.072 | 12.659 | 0.033 | worse |
| backdate | backdate | campus2 | atc | wmdd | 17 | 1310.019 | 1265.913 | 44.106 | -1.158 | 92.311 | 12.659 | 0.124 | inconclusive |
| backdate | backdate | campus2 | lpt | wmdd | 17 | 3312.168 | 1265.913 | 2046.255 | 955.925 | 3301.373 | 12.659 | 0.011 | worse |
| backdate | backdate | campus2 | random | wmdd | 17 | 1857.464 | 1265.913 | 591.550 | 285.794 | 961.302 | 12.659 | 0.002 | worse |
| sla | baseline | verdict | edd | v2rl302 | 180 | 444.869 | 444.681 | 0.188 | 0.025 | 0.405 | 4.447 | 0.071 | equivalent |
| sla | baseline | verdict | pfifo | v2rl302 | 180 | 444.869 | 444.681 | 0.188 | 0.025 | 0.410 | 4.447 | 0.071 | equivalent |
| sla | baseline | verdict | wspt | v2rl302 | 180 | 446.646 | 444.681 | 1.965 | 0.885 | 3.267 | 4.447 | 0.000 | equivalent |
| sla | baseline | verdict | atc | v2rl302 | 180 | 445.555 | 444.681 | 0.874 | 0.249 | 1.655 | 4.447 | 0.051 | equivalent |
| sla | baseline | verdict | wmdd | v2rl302 | 180 | 445.332 | 444.681 | 0.651 | 0.161 | 1.265 | 4.447 | 0.063 | equivalent |
| sla | baseline | verdict | lpt | v2rl302 | 180 | 445.579 | 444.681 | 0.898 | 0.076 | 2.424 | 4.447 | 0.038 | equivalent |
| sla | baseline | verdict | random | v2rl302 | 180 | 446.316 | 444.681 | 1.635 | 0.575 | 3.138 | 4.447 | 0.001 | equivalent |
| sla | baseline | campus1 | edd | atc | 30 | 80.417 | 80.417 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| sla | baseline | campus1 | pfifo | atc | 30 | 80.417 | 80.417 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| sla | baseline | campus1 | wspt | atc | 30 | 81.297 | 80.417 | 0.880 | 0.000 | 2.293 | 1.000 | 1.000 | inconclusive |
| sla | baseline | campus1 | wmdd | atc | 30 | 80.417 | 80.417 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| sla | baseline | campus1 | lpt | atc | 30 | 80.417 | 80.417 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| sla | baseline | campus1 | random | atc | 30 | 81.121 | 80.417 | 0.704 | 0.000 | 1.775 | 1.000 | 1.000 | inconclusive |
| sla | baseline | campus2 | edd | wmdd | 17 | 1311.322 | 1218.229 | 93.093 | -17.008 | 239.312 | 12.182 | 1.000 | inconclusive |
| sla | baseline | campus2 | pfifo | wmdd | 17 | 1311.322 | 1218.229 | 93.093 | -15.295 | 237.707 | 12.182 | 1.000 | inconclusive |
| sla | baseline | campus2 | wspt | wmdd | 17 | 1291.239 | 1218.229 | 73.010 | 35.720 | 115.400 | 12.182 | 0.009 | worse |
| sla | baseline | campus2 | atc | wmdd | 17 | 1252.116 | 1218.229 | 33.887 | 12.625 | 60.054 | 12.182 | 0.014 | worse |
| sla | baseline | campus2 | lpt | wmdd | 17 | 2615.112 | 1218.229 | 1396.883 | 675.045 | 2236.533 | 12.182 | 0.009 | worse |
| sla | baseline | campus2 | random | wmdd | 17 | 1636.031 | 1218.229 | 417.802 | 218.473 | 656.455 | 12.182 | 0.009 | worse |
| sla | emg | verdict | edd | v2rl302 | 180 | 633.402 | 633.333 | 0.068 | -0.195 | 0.308 | 6.333 | 0.764 | equivalent |
| sla | emg | verdict | pfifo | v2rl302 | 180 | 633.402 | 633.333 | 0.068 | -0.187 | 0.303 | 6.333 | 0.764 | equivalent |
| sla | emg | verdict | wspt | v2rl302 | 180 | 635.562 | 633.333 | 2.229 | 1.171 | 3.491 | 6.333 | 0.000 | equivalent |
| sla | emg | verdict | atc | v2rl302 | 180 | 633.997 | 633.333 | 0.663 | 0.045 | 1.449 | 6.333 | 0.315 | equivalent |
| sla | emg | verdict | wmdd | v2rl302 | 180 | 633.928 | 633.333 | 0.594 | 0.021 | 1.276 | 6.333 | 0.335 | equivalent |
| sla | emg | verdict | lpt | v2rl302 | 180 | 635.564 | 633.333 | 2.230 | 0.581 | 4.489 | 6.333 | 0.026 | equivalent |
| sla | emg | verdict | random | v2rl302 | 180 | 636.674 | 633.333 | 3.341 | 1.617 | 5.664 | 6.333 | 0.000 | equivalent |
| sla | emg | campus1 | edd | atc | 30 | 137.643 | 137.550 | 0.093 | 0.000 | 0.280 | 1.376 | 0.952 | equivalent |
| sla | emg | campus1 | pfifo | atc | 30 | 137.643 | 137.550 | 0.093 | 0.000 | 0.280 | 1.376 | 0.952 | equivalent |
| sla | emg | campus1 | wspt | atc | 30 | 138.430 | 137.550 | 0.880 | 0.000 | 2.293 | 1.376 | 0.719 | inconclusive |
| sla | emg | campus1 | wmdd | atc | 30 | 137.670 | 137.550 | 0.120 | 0.000 | 0.359 | 1.376 | 0.952 | equivalent |
| sla | emg | campus1 | lpt | atc | 30 | 138.692 | 137.550 | 1.142 | 0.000 | 3.068 | 1.376 | 0.653 | inconclusive |
| sla | emg | campus1 | random | atc | 30 | 138.373 | 137.550 | 0.823 | 0.000 | 1.895 | 1.376 | 0.653 | inconclusive |
| sla | emg | campus2 | edd | wmdd | 17 | 1876.423 | 1658.550 | 217.873 | 30.380 | 445.245 | 16.586 | 0.174 | worse |
| sla | emg | campus2 | pfifo | wmdd | 17 | 1874.826 | 1658.550 | 216.275 | 33.028 | 442.749 | 16.586 | 0.174 | worse |
| sla | emg | campus2 | wspt | wmdd | 17 | 1750.153 | 1658.550 | 91.602 | 46.870 | 141.995 | 16.586 | 0.006 | worse |
| sla | emg | campus2 | atc | wmdd | 17 | 1690.848 | 1658.550 | 32.298 | 9.164 | 58.792 | 16.586 | 0.058 | inconclusive |
| sla | emg | campus2 | lpt | wmdd | 17 | 3450.274 | 1658.550 | 1791.724 | 868.980 | 2875.270 | 16.586 | 0.009 | worse |
| sla | emg | campus2 | random | wmdd | 17 | 2299.784 | 1658.550 | 641.234 | 326.896 | 1033.553 | 16.586 | 0.006 | worse |
| sla | rtn | verdict | edd | v2rl302 | 180 | 472.032 | 471.154 | 0.879 | 0.129 | 2.065 | 4.712 | 0.016 | equivalent |
| sla | rtn | verdict | pfifo | v2rl302 | 180 | 472.032 | 471.154 | 0.879 | 0.127 | 2.067 | 4.712 | 0.016 | equivalent |
| sla | rtn | verdict | wspt | v2rl302 | 180 | 474.365 | 471.154 | 3.211 | 1.544 | 5.357 | 4.712 | 0.000 | inconclusive |
| sla | rtn | verdict | atc | v2rl302 | 180 | 473.058 | 471.154 | 1.904 | 0.649 | 3.529 | 4.712 | 0.003 | equivalent |
| sla | rtn | verdict | wmdd | v2rl302 | 180 | 472.750 | 471.154 | 1.596 | 0.429 | 3.263 | 4.712 | 0.005 | equivalent |
| sla | rtn | verdict | lpt | v2rl302 | 180 | 473.354 | 471.154 | 2.200 | 0.109 | 5.545 | 4.712 | 0.016 | inconclusive |
| sla | rtn | verdict | random | v2rl302 | 180 | 473.716 | 471.154 | 2.562 | 0.973 | 4.641 | 4.712 | 0.000 | equivalent |
| sla | rtn | campus1 | edd | atc | 30 | 97.900 | 97.900 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| sla | rtn | campus1 | pfifo | atc | 30 | 97.900 | 97.900 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| sla | rtn | campus1 | wspt | atc | 30 | 98.780 | 97.900 | 0.880 | 0.000 | 2.293 | 1.000 | 1.000 | inconclusive |
| sla | rtn | campus1 | wmdd | atc | 30 | 97.900 | 97.900 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| sla | rtn | campus1 | lpt | atc | 30 | 97.900 | 97.900 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| sla | rtn | campus1 | random | atc | 30 | 98.603 | 97.900 | 0.704 | 0.000 | 1.775 | 1.000 | 1.000 | inconclusive |
| sla | rtn | campus2 | edd | wmdd | 17 | 1624.937 | 1454.189 | 170.748 | 23.844 | 346.110 | 14.542 | 0.142 | worse |
| sla | rtn | campus2 | pfifo | wmdd | 17 | 1630.032 | 1454.189 | 175.843 | 34.755 | 356.319 | 14.542 | 0.142 | worse |
| sla | rtn | campus2 | wspt | wmdd | 17 | 1497.308 | 1454.189 | 43.119 | 17.390 | 72.237 | 14.542 | 0.011 | worse |
| sla | rtn | campus2 | atc | wmdd | 17 | 1485.043 | 1454.189 | 30.854 | 10.956 | 54.524 | 14.542 | 0.038 | inconclusive |
| sla | rtn | campus2 | lpt | wmdd | 17 | 3138.480 | 1454.189 | 1684.291 | 884.808 | 2579.190 | 14.542 | 0.011 | worse |
| sla | rtn | campus2 | random | wmdd | 17 | 1934.059 | 1454.189 | 479.870 | 255.092 | 726.775 | 14.542 | 0.011 | worse |
| sla | pmp3 | verdict | edd | v2rl302 | 180 | 459.836 | 459.647 | 0.189 | 0.024 | 0.405 | 4.596 | 0.056 | equivalent |
| sla | pmp3 | verdict | pfifo | v2rl302 | 180 | 459.836 | 459.647 | 0.189 | 0.027 | 0.401 | 4.596 | 0.056 | equivalent |
| sla | pmp3 | verdict | wspt | v2rl302 | 180 | 461.807 | 459.647 | 2.160 | 1.091 | 3.474 | 4.596 | 0.000 | equivalent |
| sla | pmp3 | verdict | atc | v2rl302 | 180 | 460.562 | 459.647 | 0.915 | 0.294 | 1.683 | 4.596 | 0.016 | equivalent |
| sla | pmp3 | verdict | wmdd | v2rl302 | 180 | 460.335 | 459.647 | 0.688 | 0.199 | 1.321 | 4.596 | 0.020 | equivalent |
| sla | pmp3 | verdict | lpt | v2rl302 | 180 | 460.587 | 459.647 | 0.940 | 0.103 | 2.495 | 4.596 | 0.020 | equivalent |
| sla | pmp3 | verdict | random | v2rl302 | 180 | 461.326 | 459.647 | 1.679 | 0.619 | 3.215 | 4.596 | 0.000 | equivalent |
| sla | pmp3 | campus1 | edd | atc | 30 | 90.558 | 90.558 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| sla | pmp3 | campus1 | pfifo | atc | 30 | 90.558 | 90.558 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| sla | pmp3 | campus1 | wspt | atc | 30 | 91.494 | 90.558 | 0.936 | 0.000 | 2.406 | 1.000 | 1.000 | inconclusive |
| sla | pmp3 | campus1 | wmdd | atc | 30 | 90.558 | 90.558 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| sla | pmp3 | campus1 | lpt | atc | 30 | 90.558 | 90.558 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent |
| sla | pmp3 | campus1 | random | atc | 30 | 91.262 | 90.558 | 0.704 | 0.000 | 1.775 | 1.000 | 1.000 | inconclusive |
| sla | pmp3 | campus2 | edd | wmdd | 17 | 1321.473 | 1231.344 | 90.129 | -18.901 | 236.293 | 12.313 | 1.000 | inconclusive |
| sla | pmp3 | campus2 | pfifo | wmdd | 17 | 1321.473 | 1231.344 | 90.129 | -19.405 | 237.414 | 12.313 | 1.000 | inconclusive |
| sla | pmp3 | campus2 | wspt | wmdd | 17 | 1305.967 | 1231.344 | 74.623 | 35.723 | 117.559 | 12.313 | 0.009 | worse |
| sla | pmp3 | campus2 | atc | wmdd | 17 | 1268.159 | 1231.344 | 36.814 | 10.368 | 68.098 | 12.313 | 0.056 | inconclusive |
| sla | pmp3 | campus2 | lpt | wmdd | 17 | 2622.329 | 1231.344 | 1390.985 | 664.696 | 2216.854 | 12.313 | 0.009 | worse |
| sla | pmp3 | campus2 | random | wmdd | 17 | 1643.508 | 1231.344 | 412.164 | 211.331 | 646.428 | 12.313 | 0.009 | worse |


## Sanity checks

| check | got | want | ok |
|---|---|---|---|
| Eval-B anchors at m=1.0 | 227 | 227 | True |
| Eval-B anchors, verdict stratum | 180 | 180 | True |
| Eval-B scored methods | 17 | 17 | True |
| pmodel: configs vs meta.json | 680 | 680 | True |
| pmodel: rows vs meta.json | 11560 | 11560 | True |
| pmodel: infeasible vs meta.json | 0 | 0 | True |
| pmodel: errors vs meta.json | 0 | 0 | True |
| pmodel: base instances vs meta.json | 227 | 227 | True |
| pmodel: methods scored | 17 | 17 | True |
| pmodel: every anchor is an Eval-B anchor | 1 | 1 | True |
| pmodel: id suffix strips back to the anchor | 1 | 1 | True |
| pmodel: every method covers every configuration of its arm | 1 | 1 | True |
| pmodel: value column has no missing entry | 0 | 0 | True |
| capacity: configs vs meta.json | 454 | 454 | True |
| capacity: rows vs meta.json | 7718 | 7718 | True |
| capacity: infeasible vs meta.json | 0 | 0 | True |
| capacity: errors vs meta.json | 0 | 0 | True |
| capacity: base instances vs meta.json | 227 | 227 | True |
| capacity: methods scored | 17 | 17 | True |
| capacity: every anchor is an Eval-B anchor | 1 | 1 | True |
| capacity: id suffix strips back to the anchor | 1 | 1 | True |
| capacity: every method covers every configuration of its arm | 1 | 1 | True |
| capacity: value column has no missing entry | 0 | 0 | True |
| backdate: configs vs meta.json | 227 | 227 | True |
| backdate: rows vs meta.json | 3859 | 3859 | True |
| backdate: infeasible vs meta.json | 0 | 0 | True |
| backdate: errors vs meta.json | 0 | 0 | True |
| backdate: base instances vs meta.json | 227 | 227 | True |
| backdate: methods scored | 17 | 17 | True |
| backdate: every anchor is an Eval-B anchor | 1 | 1 | True |
| backdate: id suffix strips back to the anchor | 1 | 1 | True |
| backdate: every method covers every configuration of its arm | 1 | 1 | True |
| backdate: value column has no missing entry | 0 | 0 | True |
| sla: configs vs meta.json | 681 | 681 | True |
| sla: rows vs meta.json | 11577 | 11577 | True |
| sla: infeasible vs meta.json | 0 | 0 | True |
| sla: errors vs meta.json | 0 | 0 | True |
| sla: base instances vs meta.json | 227 | 227 | True |
| sla: methods scored | 17 | 17 | True |
| sla: every anchor is an Eval-B anchor | 1 | 1 | True |
| sla: id suffix strips back to the anchor | 1 | 1 | True |
| sla: every method covers every configuration of its arm | 1 | 1 | True |
| sla: value column has no missing entry | 0 | 0 | True |
| R4.7 sum arm pairs with every Eval-B row | 3859 | 3859 | True |
| R4.7 sum arm reproduces Eval-B exactly | 0.000 | 0.000 | True |
| R4.8 baseline utilization matches Eval-B (max abs diff < 1e-6) | True | True | True |
