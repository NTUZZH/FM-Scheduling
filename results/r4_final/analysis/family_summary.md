# Family-level Eval-B analysis, EDD reference fixed in advance

Source: `results/r4_final/results.csv` (seed-level) collapsed to ten methods: the seven transparent rules and three policy pools (`mlp_pool` = 10 MLP seeds, `attn_pool` = 10 attention seeds, `v1_pool` = 3 curriculum-v1 seeds). A pool's value on an instance-configuration is the mean over its seeds there. Rolling CP-SAT ran on a subsample and is reported through its paired rows against EDD only, never ranked.

Statistics: `fmwos.stats`, paired on the configuration id, 95% percentile bootstrap over base-instance clusters, 10000 resamples, master seed 12345, equivalence margin max(1.0, 1% of the reference mean), Holm within a comparison family. A negative difference means the family is better than EDD.

Two comparisons per scope. The PRIMARY one is against EDD, chosen before any result was read, so no scope's reference depends on the outcome. The SECONDARY one is against the family with the lowest sample mean in that scope, reported for continuity with the released seed-level analysis and descriptive only.


## Seed coverage of the pools

| pool | n_seeds | n_configs | n_configs_dropped | status |
|---|---|---|---|---|
| mlp_pool | 10 | 887 | 0 | complete |
| attn_pool | 10 | 887 | 0 | complete |
| v1_pool | 3 | 887 | 0 | complete |

A pool has a value only where every one of its seeds has a feasible row; `n_configs_dropped` counts the configurations that rule removes.


## Reconciliation against the released pool comparisons

Every pool-vs-EDD row of `results/r4_final/analysis/pools.csv` recomputed from the family collapse, field by field (64 rows, all matching to 1e-9).

| scope_type | scope | family | released_mean_diff | family_mean_diff | released_ci_lo | family_ci_lo | released_ci_hi | family_ci_hi | max_abs_diff | ok |
|---|---|---|---|---|---|---|---|---|---|---|
| emp_m | m=0.6 | attn_pool | 3.839 | 3.839 | 1.304 | 1.304 | 7.040 | 7.040 | 0.000 | 1 |
| emp_m | m=0.6 | mlp_pool | -0.395 | -0.395 | -1.746 | -1.746 | 1.022 | 1.022 | 0.000 | 1 |
| emp_m | m=0.8 | attn_pool | 1.052 | 1.052 | 0.344 | 0.344 | 1.952 | 1.952 | 0.000 | 1 |
| emp_m | m=0.8 | mlp_pool | -0.146 | -0.146 | -0.508 | -0.508 | 0.274 | 0.274 | 0.000 | 1 |
| emp_m | m=1.0 | attn_pool | 0.399 | 0.399 | 0.067 | 0.067 | 0.835 | 0.835 | 0.000 | 1 |
| emp_m | m=1.0 | mlp_pool | -0.100 | -0.100 | -0.260 | -0.260 | 0.024 | 0.024 | 0.000 | 1 |
| emp_m_ubin | m=0.6|u_bin=0.5-0.8 | attn_pool | 3.536 | 3.536 | 0.209 | 0.209 | 9.421 | 9.421 | 0.000 | 1 |
| emp_m_ubin | m=0.6|u_bin=0.5-0.8 | mlp_pool | -1.169 | -1.169 | -3.024 | -3.024 | -0.059 | -0.059 | 0.000 | 1 |
| emp_m_ubin | m=0.6|u_bin=0.8-1.0 | attn_pool | 4.349 | 4.349 | -3.372 | -3.372 | 12.889 | 12.889 | 0.000 | 1 |
| emp_m_ubin | m=0.6|u_bin=0.8-1.0 | mlp_pool | -2.035 | -2.035 | -4.964 | -4.964 | 0.534 | 0.534 | 0.000 | 1 |
| emp_m_ubin | m=0.6|u_bin=1.0-1.2 | attn_pool | 15.046 | 15.046 | 1.263 | 1.263 | 38.244 | 38.244 | 0.000 | 1 |
| emp_m_ubin | m=0.6|u_bin=1.0-1.2 | mlp_pool | 6.737 | 6.737 | -0.794 | -0.794 | 17.579 | 17.579 | 0.000 | 1 |
| emp_m_ubin | m=0.6|u_bin=<0.5 | attn_pool | 0.641 | 0.641 | 0.059 | 0.059 | 1.311 | 1.311 | 0.000 | 1 |
| emp_m_ubin | m=0.6|u_bin=<0.5 | mlp_pool | -0.081 | -0.081 | -0.619 | -0.619 | 0.318 | 0.318 | 0.000 | 1 |
| emp_m_ubin | m=0.6|u_bin=>=1.2 | attn_pool | 2.099 | 2.099 | -0.481 | -0.481 | 5.195 | 5.195 | 0.000 | 1 |
| emp_m_ubin | m=0.6|u_bin=>=1.2 | mlp_pool | -1.484 | -1.484 | -4.237 | -4.237 | 0.528 | 0.528 | 0.000 | 1 |
| emp_m_ubin | m=0.8|u_bin=0.5-0.8 | attn_pool | 2.585 | 2.585 | 0.369 | 0.369 | 5.556 | 5.556 | 0.000 | 1 |
| emp_m_ubin | m=0.8|u_bin=0.5-0.8 | mlp_pool | -0.110 | -0.110 | -1.182 | -1.182 | 1.288 | 1.288 | 0.000 | 1 |
| emp_m_ubin | m=0.8|u_bin=0.8-1.0 | attn_pool | 0.842 | 0.842 | 0.053 | 0.053 | 2.187 | 2.187 | 0.000 | 1 |
| emp_m_ubin | m=0.8|u_bin=0.8-1.0 | mlp_pool | -0.271 | -0.271 | -0.825 | -0.825 | 0.013 | 0.013 | 0.000 | 1 |
| emp_m_ubin | m=0.8|u_bin=1.0-1.2 | attn_pool | 0.434 | 0.434 | -2.008 | -2.008 | 3.339 | 3.339 | 0.000 | 1 |
| emp_m_ubin | m=0.8|u_bin=1.0-1.2 | mlp_pool | -1.145 | -1.145 | -3.323 | -3.323 | 0.000 | 0.000 | 0.000 | 1 |
| emp_m_ubin | m=0.8|u_bin=<0.5 | attn_pool | 0.383 | 0.383 | 0.020 | 0.020 | 0.992 | 0.992 | 0.000 | 1 |
| emp_m_ubin | m=0.8|u_bin=<0.5 | mlp_pool | 0.007 | 0.007 | 0.000 | 0.000 | 0.022 | 0.022 | 0.000 | 1 |
| emp_m_ubin | m=0.8|u_bin=>=1.2 | attn_pool | 0.194 | 0.194 | 0.008 | 0.008 | 0.427 | 0.427 | 0.000 | 1 |
| emp_m_ubin | m=0.8|u_bin=>=1.2 | mlp_pool | 0.011 | 0.011 | -0.016 | -0.016 | 0.047 | 0.047 | 0.000 | 1 |
| emp_m_ubin | m=1.0|u_bin=0.5-0.8 | attn_pool | 0.460 | 0.460 | -0.109 | -0.109 | 1.460 | 1.460 | 0.000 | 1 |
| emp_m_ubin | m=1.0|u_bin=0.5-0.8 | mlp_pool | -0.275 | -0.275 | -0.707 | -0.707 | 0.057 | 0.057 | 0.000 | 1 |
| emp_m_ubin | m=1.0|u_bin=0.8-1.0 | attn_pool | 0.970 | 0.970 | -0.178 | -0.178 | 3.072 | 3.072 | 0.000 | 1 |
| emp_m_ubin | m=1.0|u_bin=0.8-1.0 | mlp_pool | -0.542 | -0.542 | -1.626 | -1.626 | 0.000 | 0.000 | 0.000 | 1 |
| emp_m_ubin | m=1.0|u_bin=1.0-1.2 | attn_pool | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1 |
| emp_m_ubin | m=1.0|u_bin=1.0-1.2 | mlp_pool | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1 |
| emp_m_ubin | m=1.0|u_bin=<0.5 | attn_pool | 0.368 | 0.368 | 0.000 | 0.000 | 0.984 | 0.984 | 0.000 | 1 |
| emp_m_ubin | m=1.0|u_bin=<0.5 | mlp_pool | 0.032 | 0.032 | -0.005 | -0.005 | 0.088 | 0.088 | 0.000 | 1 |
| emp_m_ubin | m=1.0|u_bin=>=1.2 | attn_pool | 0.165 | 0.165 | 0.005 | 0.005 | 0.355 | 0.355 | 0.000 | 1 |
| emp_m_ubin | m=1.0|u_bin=>=1.2 | mlp_pool | 0.030 | 0.030 | 0.000 | 0.000 | 0.076 | 0.076 | 0.000 | 1 |
| emp_pooled | ALL | attn_pool | 5.207 | 5.207 | 2.136 | 2.136 | 9.256 | 9.256 | 0.000 | 1 |
| emp_pooled | ALL | mlp_pool | 9.608 | 9.608 | 2.712 | 2.712 | 19.163 | 19.163 | 0.000 | 1 |
| emp_ubin | u_bin=0.5-0.8 | attn_pool | 2.158 | 2.158 | 0.394 | 0.394 | 4.837 | 4.837 | 0.000 | 1 |
| emp_ubin | u_bin=0.5-0.8 | mlp_pool | -0.501 | -0.501 | -1.231 | -1.231 | 0.145 | 0.145 | 0.000 | 1 |
| emp_ubin | u_bin=0.8-1.0 | attn_pool | 2.347 | 2.347 | -0.827 | -0.827 | 5.981 | 5.981 | 0.000 | 1 |
| emp_ubin | u_bin=0.8-1.0 | mlp_pool | -1.070 | -1.070 | -2.371 | -2.371 | 0.056 | 0.056 | 0.000 | 1 |
| emp_ubin | u_bin=1.0-1.2 | attn_pool | 7.472 | 7.472 | 0.594 | 0.594 | 19.037 | 19.037 | 0.000 | 1 |
| emp_ubin | u_bin=1.0-1.2 | mlp_pool | 2.875 | 2.875 | -0.997 | -0.997 | 8.422 | 8.422 | 0.000 | 1 |
| emp_ubin | u_bin=<0.5 | attn_pool | 0.425 | 0.425 | 0.097 | 0.097 | 0.873 | 0.873 | 0.000 | 1 |
| emp_ubin | u_bin=<0.5 | mlp_pool | 0.002 | 0.002 | -0.103 | -0.103 | 0.085 | 0.085 | 0.000 | 1 |
| emp_ubin | u_bin=>=1.2 | attn_pool | 1.131 | 1.131 | -0.172 | -0.172 | 2.770 | 2.770 | 0.000 | 1 |
| emp_ubin | u_bin=>=1.2 | mlp_pool | -0.725 | -0.725 | -2.186 | -2.186 | 0.270 | 0.270 | 0.000 | 1 |
| gen_all | ALL | attn_pool | 597.539 | 597.539 | 512.087 | 512.087 | 688.841 | 688.841 | 0.000 | 1 |
| gen_all | ALL | mlp_pool | 143.663 | 143.663 | 103.958 | 103.958 | 188.351 | 188.351 | 0.000 | 1 |
| gen_utarget | u_target=0.7 | attn_pool | 9.906 | 9.906 | 5.365 | 5.365 | 15.999 | 15.999 | 0.000 | 1 |
| gen_utarget | u_target=0.7 | mlp_pool | -0.227 | -0.227 | -0.983 | -0.983 | 0.523 | 0.523 | 0.000 | 1 |
| gen_utarget | u_target=0.9 | attn_pool | 218.397 | 218.397 | 180.706 | 180.706 | 256.359 | 256.359 | 0.000 | 1 |
| gen_utarget | u_target=0.9 | mlp_pool | 5.879 | 5.879 | -0.300 | -0.300 | 11.802 | 11.802 | 0.000 | 1 |
| gen_utarget | u_target=1.0 | attn_pool | 409.672 | 409.672 | 343.923 | 343.923 | 480.273 | 480.273 | 0.000 | 1 |
| gen_utarget | u_target=1.0 | mlp_pool | 22.797 | 22.797 | 14.668 | 14.668 | 32.256 | 32.256 | 0.000 | 1 |
| gen_utarget | u_target=1.1 | attn_pool | 731.042 | 731.042 | 614.576 | 614.576 | 856.475 | 856.475 | 0.000 | 1 |
| gen_utarget | u_target=1.1 | mlp_pool | 106.828 | 106.828 | 65.780 | 65.780 | 155.512 | 155.512 | 0.000 | 1 |
| gen_utarget | u_target=1.3 | attn_pool | 1618.677 | 1618.677 | 1350.099 | 1350.099 | 1916.765 | 1916.765 | 0.000 | 1 |
| gen_utarget | u_target=1.3 | mlp_pool | 583.035 | 583.035 | 432.655 | 432.655 | 748.902 | 748.902 | 0.000 | 1 |
| stress | campus=2|m=1.0 | attn_pool | 123.781 | 123.781 | 32.428 | 32.428 | 234.138 | 234.138 | 0.000 | 1 |
| stress | campus=2|m=1.0 | mlp_pool | 338.541 | 338.541 | 134.840 | 134.840 | 591.305 | 591.305 | 0.000 | 1 |
| transfer | campus=1|m=1.0 | attn_pool | 0.000 | 0.000 | 0.000 | 0.000 | 0.001 | 0.001 | 0.000 | 1 |
| transfer | campus=1|m=1.0 | mlp_pool | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1 |


## Empirical verdict campuses, per crew multiplier


**m=1.0** (180 configurations, 180 clusters). Against EDD, of 9 families compared: 9 equivalent (pfifo, wspt, atc, wmdd, lpt, random, mlp_pool, attn_pool, v1_pool). Sample-best family: mlp_pool.

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 180 | 180 | 444.869 | 444.869 | 0.000 | 0.000 | 0.000 | 4.449 | 1.000 | equivalent | mlp_pool | 0.022 | equivalent | 1.000 |
| wspt | 180 | 180 | 444.869 | 446.646 | 1.777 | 0.806 | 2.967 | 4.449 | 0.000 | equivalent | mlp_pool | 0.422 | equivalent | 1.000 |
| atc | 180 | 180 | 444.869 | 445.555 | 0.686 | 0.175 | 1.341 | 4.449 | 0.104 | equivalent | mlp_pool | 0.177 | equivalent | 1.000 |
| wmdd | 180 | 180 | 444.869 | 445.332 | 0.463 | 0.105 | 0.938 | 4.449 | 0.216 | equivalent | mlp_pool | 0.127 | equivalent | 1.000 |
| lpt | 180 | 180 | 444.869 | 445.579 | 0.710 | -0.076 | 2.108 | 4.449 | 0.729 | equivalent | mlp_pool | 0.182 | equivalent | 1.000 |
| random | 180 | 180 | 444.869 | 446.316 | 1.447 | 0.472 | 2.814 | 4.449 | 0.002 | equivalent | mlp_pool | 0.348 | equivalent | 1.000 |
| mlp_pool | 180 | 180 | 444.869 | 444.769 | -0.100 | -0.260 | 0.024 | 4.449 | 1.000 | equivalent | mlp_pool | 0.000 | equivalent | 1.000 |
| attn_pool | 180 | 180 | 444.869 | 445.268 | 0.399 | 0.067 | 0.835 | 4.449 | 0.038 | equivalent | mlp_pool | 0.112 | equivalent | 1.000 |
| v1_pool | 180 | 180 | 444.869 | 444.810 | -0.059 | -0.202 | 0.073 | 4.449 | 0.729 | equivalent | mlp_pool | 0.009 | equivalent | 1.000 |
| rollcp2 | 48 | 48 | 505.828 | 505.808 | -0.020 | -0.145 | 0.053 | 5.058 | 0.001 | equivalent | - | - | - | - |
| edd | 180 | 180 | 444.869 | 444.869 | 0.000 | 0.000 | 0.000 | 4.449 | 1.000 | reference | mlp_pool | 0.022 | equivalent | 1.000 |


**m=0.8** (180 configurations, 180 clusters). Against EDD, of 9 families compared: 6 equivalent (pfifo, atc, wmdd, mlp_pool, attn_pool, v1_pool); 3 inconclusive (wspt, lpt, random). Sample-best family: v1_pool.

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 180 | 180 | 446.636 | 446.636 | 0.000 | 0.000 | 0.000 | 4.466 | 1.000 | equivalent | v1_pool | 0.058 | equivalent | 1.000 |
| wspt | 180 | 180 | 446.636 | 450.362 | 3.726 | 2.183 | 5.567 | 4.466 | 0.000 | inconclusive | v1_pool | 0.893 | inconclusive | 0.000 |
| atc | 180 | 180 | 446.636 | 448.166 | 1.530 | 0.527 | 2.756 | 4.466 | 0.014 | equivalent | v1_pool | 0.401 | equivalent | 1.000 |
| wmdd | 180 | 180 | 446.636 | 447.547 | 0.911 | 0.322 | 1.663 | 4.466 | 0.025 | equivalent | v1_pool | 0.262 | equivalent | 1.000 |
| lpt | 180 | 180 | 446.636 | 455.331 | 8.695 | 1.145 | 20.200 | 4.466 | 0.058 | inconclusive | v1_pool | 2.006 | inconclusive | 0.000 |
| random | 180 | 180 | 446.636 | 450.586 | 3.950 | 1.580 | 7.260 | 4.466 | 0.000 | inconclusive | v1_pool | 0.943 | inconclusive | 0.000 |
| mlp_pool | 180 | 180 | 446.636 | 446.490 | -0.146 | -0.508 | 0.274 | 4.466 | 0.534 | equivalent | v1_pool | 0.026 | equivalent | 1.000 |
| attn_pool | 180 | 180 | 446.636 | 447.688 | 1.052 | 0.344 | 1.952 | 4.466 | 0.001 | equivalent | v1_pool | 0.294 | equivalent | 1.000 |
| v1_pool | 180 | 180 | 446.636 | 446.376 | -0.260 | -0.555 | -0.004 | 4.466 | 0.058 | equivalent | v1_pool | 0.000 | equivalent | 1.000 |
| rollcp2 | 48 | 48 | 506.547 | 506.036 | -0.511 | -1.330 | 0.061 | 5.065 | 0.029 | equivalent | - | - | - | - |
| edd | 180 | 180 | 446.636 | 446.636 | 0.000 | 0.000 | 0.000 | 4.466 | 1.000 | reference | v1_pool | 0.058 | equivalent | 1.000 |


**m=0.6** (180 configurations, 180 clusters). Against EDD, of 9 families compared: 3 equivalent (pfifo, mlp_pool, v1_pool); 3 inconclusive (atc, wmdd, attn_pool); 3 worse (wspt, lpt, random). Sample-best family: v1_pool.

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 180 | 180 | 451.714 | 451.714 | 0.000 | 0.000 | 0.000 | 4.517 | 1.000 | equivalent | v1_pool | 0.187 | equivalent | 1.000 |
| wspt | 180 | 180 | 451.714 | 463.777 | 12.063 | 6.457 | 18.991 | 4.517 | 0.000 | worse | v1_pool | 2.862 | worse | 0.000 |
| atc | 180 | 180 | 451.714 | 456.441 | 4.727 | 1.841 | 8.071 | 4.517 | 0.000 | inconclusive | v1_pool | 1.235 | inconclusive | 0.000 |
| wmdd | 180 | 180 | 451.714 | 455.084 | 3.370 | 1.696 | 5.342 | 4.517 | 0.000 | inconclusive | v1_pool | 0.934 | inconclusive | 0.000 |
| lpt | 180 | 180 | 451.714 | 536.749 | 85.036 | 19.514 | 190.060 | 4.517 | 0.000 | worse | v1_pool | 19.047 | worse | 0.000 |
| random | 180 | 180 | 451.714 | 479.315 | 27.602 | 7.746 | 64.161 | 4.517 | 0.000 | worse | v1_pool | 6.308 | worse | 0.000 |
| mlp_pool | 180 | 180 | 451.714 | 451.318 | -0.395 | -1.746 | 1.022 | 4.517 | 0.423 | equivalent | v1_pool | 0.099 | equivalent | 1.000 |
| attn_pool | 180 | 180 | 451.714 | 455.552 | 3.839 | 1.304 | 7.040 | 4.517 | 0.000 | inconclusive | v1_pool | 1.038 | inconclusive | 0.000 |
| v1_pool | 180 | 180 | 451.714 | 450.872 | -0.842 | -2.270 | 0.496 | 4.517 | 0.201 | equivalent | v1_pool | 0.000 | equivalent | 1.000 |
| rollcp2 | 48 | 48 | 510.698 | 510.046 | -0.651 | -1.996 | 0.393 | 5.107 | 0.170 | equivalent | - | - | - | - |
| edd | 180 | 180 | 451.714 | 451.714 | 0.000 | 0.000 | 0.000 | 4.517 | 1.000 | reference | v1_pool | 0.187 | equivalent | 1.000 |


## Empirical verdict campuses, per realised-utilisation bin


**u_bin=<0.5** (180 configurations, 85 clusters). Against EDD, of 9 families compared: 8 equivalent (pfifo, atc, wmdd, lpt, random, mlp_pool, attn_pool, v1_pool); 1 inconclusive (wspt). Sample-best family: edd.

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 180 | 85 | 249.051 | 249.051 | 0.000 | 0.000 | 0.000 | 2.491 | 1.000 | equivalent | edd | 0.000 | equivalent | 1.000 |
| wspt | 180 | 85 | 249.051 | 250.412 | 1.361 | 0.445 | 2.513 | 2.491 | 0.002 | inconclusive | edd | 0.546 | inconclusive | 0.000 |
| atc | 180 | 85 | 249.051 | 249.579 | 0.528 | 0.039 | 1.236 | 2.491 | 0.166 | equivalent | edd | 0.212 | equivalent | 1.000 |
| wmdd | 180 | 85 | 249.051 | 249.561 | 0.510 | 0.045 | 1.224 | 2.491 | 0.166 | equivalent | edd | 0.205 | equivalent | 1.000 |
| lpt | 180 | 85 | 249.051 | 249.302 | 0.250 | 0.010 | 0.693 | 2.491 | 0.463 | equivalent | edd | 0.100 | equivalent | 1.000 |
| random | 180 | 85 | 249.051 | 249.850 | 0.799 | 0.237 | 1.527 | 2.491 | 0.015 | equivalent | edd | 0.321 | equivalent | 1.000 |
| mlp_pool | 180 | 85 | 249.051 | 249.054 | 0.002 | -0.103 | 0.085 | 2.491 | 0.639 | equivalent | edd | 0.001 | equivalent | 1.000 |
| attn_pool | 180 | 85 | 249.051 | 249.476 | 0.425 | 0.097 | 0.873 | 2.491 | 0.005 | equivalent | edd | 0.171 | equivalent | 1.000 |
| v1_pool | 180 | 85 | 249.051 | 249.062 | 0.010 | -0.080 | 0.124 | 2.491 | 1.000 | equivalent | edd | 0.004 | equivalent | 1.000 |
| rollcp2 | 54 | 27 | 321.151 | 321.201 | 0.051 | -0.124 | 0.235 | 3.212 | 0.000 | equivalent | - | - | - | - |
| edd | 180 | 85 | 249.051 | 249.051 | 0.000 | 0.000 | 0.000 | 2.491 | 1.000 | reference | edd | 0.000 | equivalent | 1.000 |


**u_bin=0.5-0.8** (152 configurations, 103 clusters). Against EDD, of 9 families compared: 6 equivalent (pfifo, atc, wmdd, mlp_pool, attn_pool, v1_pool); 3 inconclusive (wspt, lpt, random). Sample-best family: mlp_pool.

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 152 | 103 | 687.457 | 687.457 | 0.000 | 0.000 | 0.000 | 6.875 | 1.000 | equivalent | mlp_pool | 0.073 | equivalent | 1.000 |
| wspt | 152 | 103 | 687.457 | 692.771 | 5.315 | 1.958 | 10.067 | 6.875 | 0.000 | inconclusive | mlp_pool | 0.847 | inconclusive | 0.000 |
| atc | 152 | 103 | 687.457 | 689.987 | 2.530 | 0.536 | 5.338 | 6.875 | 0.005 | equivalent | mlp_pool | 0.441 | equivalent | 1.000 |
| wmdd | 152 | 103 | 687.457 | 689.239 | 1.783 | 0.349 | 3.725 | 6.875 | 0.017 | equivalent | mlp_pool | 0.332 | equivalent | 1.000 |
| lpt | 152 | 103 | 687.457 | 707.290 | 19.833 | 2.315 | 44.931 | 6.875 | 0.086 | inconclusive | mlp_pool | 2.960 | inconclusive | 0.000 |
| random | 152 | 103 | 687.457 | 693.841 | 6.384 | 1.687 | 13.262 | 6.875 | 0.000 | inconclusive | mlp_pool | 1.002 | inconclusive | 0.000 |
| mlp_pool | 152 | 103 | 687.457 | 686.956 | -0.501 | -1.231 | 0.145 | 6.875 | 0.238 | equivalent | mlp_pool | 0.000 | equivalent | 1.000 |
| attn_pool | 152 | 103 | 687.457 | 689.615 | 2.158 | 0.394 | 4.837 | 6.875 | 0.001 | equivalent | mlp_pool | 0.387 | equivalent | 1.000 |
| v1_pool | 152 | 103 | 687.457 | 687.034 | -0.422 | -1.059 | 0.179 | 6.875 | 0.123 | equivalent | mlp_pool | 0.011 | equivalent | 1.000 |
| rollcp2 | 47 | 29 | 797.293 | 796.818 | -0.474 | -1.136 | 0.037 | 7.973 | 0.024 | equivalent | - | - | - | - |
| edd | 152 | 103 | 687.457 | 687.457 | 0.000 | 0.000 | 0.000 | 6.875 | 1.000 | reference | mlp_pool | 0.073 | equivalent | 1.000 |


**u_bin=0.8-1.0** (64 configurations, 64 clusters). Against EDD, of 9 families compared: 5 equivalent (pfifo, wmdd, mlp_pool, attn_pool, v1_pool); 3 inconclusive (wspt, atc, random); 1 worse (lpt). Sample-best family: v1_pool.

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 64 | 64 | 625.242 | 625.242 | 0.000 | 0.000 | 0.000 | 6.252 | 1.000 | equivalent | v1_pool | 0.311 | equivalent | 1.000 |
| wspt | 64 | 64 | 625.242 | 634.473 | 9.232 | 2.256 | 17.329 | 6.252 | 0.005 | inconclusive | v1_pool | 1.792 | inconclusive | 0.000 |
| atc | 64 | 64 | 625.242 | 628.286 | 3.044 | -1.487 | 7.704 | 6.252 | 0.179 | inconclusive | v1_pool | 0.799 | inconclusive | 0.000 |
| wmdd | 64 | 64 | 625.242 | 628.198 | 2.957 | 0.864 | 5.540 | 6.252 | 0.046 | equivalent | v1_pool | 0.785 | inconclusive | 0.000 |
| lpt | 64 | 64 | 625.242 | 661.603 | 36.361 | 10.880 | 70.609 | 6.252 | 0.017 | worse | v1_pool | 6.144 | worse | 0.000 |
| random | 64 | 64 | 625.242 | 637.047 | 11.806 | 3.682 | 21.970 | 6.252 | 0.010 | inconclusive | v1_pool | 2.205 | inconclusive | 0.000 |
| mlp_pool | 64 | 64 | 625.242 | 624.171 | -1.070 | -2.371 | 0.056 | 6.252 | 0.192 | equivalent | v1_pool | 0.139 | equivalent | 1.000 |
| attn_pool | 64 | 64 | 625.242 | 627.589 | 2.347 | -0.827 | 5.981 | 6.252 | 0.049 | equivalent | v1_pool | 0.687 | inconclusive | 0.000 |
| v1_pool | 64 | 64 | 625.242 | 623.306 | -1.936 | -4.340 | -0.300 | 6.252 | 0.095 | equivalent | v1_pool | 0.000 | equivalent | 1.000 |
| rollcp2 | 13 | 13 | 853.590 | 851.349 | -2.241 | -6.656 | 0.426 | 8.536 | 0.938 | equivalent | - | - | - | - |
| edd | 64 | 64 | 625.242 | 625.242 | 0.000 | 0.000 | 0.000 | 6.252 | 1.000 | reference | v1_pool | 0.311 | equivalent | 1.000 |


**u_bin=1.0-1.2** (37 configurations, 37 clusters). Against EDD, of 9 families compared: 2 equivalent (pfifo, v1_pool); 5 inconclusive (wspt, atc, wmdd, mlp_pool, attn_pool); 2 worse (lpt, random). Sample-best family: edd.

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 37 | 37 | 608.195 | 608.195 | 0.000 | 0.000 | 0.000 | 6.082 | 1.000 | equivalent | edd | 0.000 | equivalent | 1.000 |
| wspt | 37 | 37 | 608.195 | 627.080 | 18.885 | 5.073 | 41.257 | 6.082 | 0.013 | inconclusive | edd | 3.105 | inconclusive | 0.000 |
| atc | 37 | 37 | 608.195 | 615.280 | 7.085 | 1.419 | 15.792 | 6.082 | 0.082 | inconclusive | edd | 1.165 | inconclusive | 0.000 |
| wmdd | 37 | 37 | 608.195 | 612.699 | 4.503 | 0.814 | 10.339 | 6.082 | 0.082 | inconclusive | edd | 0.740 | inconclusive | 0.000 |
| lpt | 37 | 37 | 608.195 | 837.919 | 229.724 | 7.651 | 660.177 | 6.082 | 0.082 | worse | edd | 37.771 | worse | 0.000 |
| random | 37 | 37 | 608.195 | 695.380 | 87.184 | 6.659 | 241.280 | 6.082 | 0.023 | worse | edd | 14.335 | worse | 0.000 |
| mlp_pool | 37 | 37 | 608.195 | 611.071 | 2.875 | -0.997 | 8.422 | 6.082 | 1.000 | inconclusive | edd | 0.473 | inconclusive | 0.000 |
| attn_pool | 37 | 37 | 608.195 | 615.667 | 7.472 | 0.594 | 19.037 | 6.082 | 0.467 | inconclusive | edd | 1.229 | inconclusive | 0.000 |
| v1_pool | 37 | 37 | 608.195 | 610.082 | 1.886 | -1.029 | 6.034 | 6.082 | 1.000 | equivalent | edd | 0.310 | equivalent | 1.000 |
| rollcp2 | 7 | 7 | 585.357 | 584.193 | -1.164 | -3.456 | 0.019 | 5.854 | 0.500 | equivalent | - | - | - | - |
| edd | 37 | 37 | 608.195 | 608.195 | 0.000 | 0.000 | 0.000 | 6.082 | 1.000 | reference | edd | 0.000 | equivalent | 1.000 |


**u_bin=>=1.2** (107 configurations, 53 clusters). Against EDD, of 9 families compared: 4 equivalent (pfifo, mlp_pool, attn_pool, v1_pool); 4 inconclusive (atc, wmdd, lpt, random); 1 worse (wspt). Sample-best family: v1_pool.

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 107 | 53 | 279.795 | 279.795 | 0.000 | 0.000 | 0.000 | 2.798 | 1.000 | equivalent | v1_pool | 0.310 | equivalent | 1.000 |
| wspt | 107 | 53 | 279.795 | 287.454 | 7.660 | 2.812 | 14.521 | 2.798 | 0.000 | worse | v1_pool | 3.056 | worse | 0.000 |
| atc | 107 | 53 | 279.795 | 282.722 | 2.928 | 0.100 | 6.703 | 2.798 | 0.166 | inconclusive | v1_pool | 1.360 | inconclusive | 0.000 |
| wmdd | 107 | 53 | 279.795 | 281.058 | 1.264 | 0.073 | 2.886 | 2.798 | 0.216 | inconclusive | v1_pool | 0.763 | inconclusive | 0.000 |
| lpt | 107 | 53 | 279.795 | 308.885 | 29.090 | 0.000 | 86.031 | 2.798 | 0.513 | inconclusive | v1_pool | 10.739 | inconclusive | 0.000 |
| random | 107 | 53 | 279.795 | 287.684 | 7.890 | 2.056 | 15.938 | 2.798 | 0.000 | inconclusive | v1_pool | 3.139 | inconclusive | 0.000 |
| mlp_pool | 107 | 53 | 279.795 | 279.069 | -0.725 | -2.186 | 0.270 | 2.798 | 1.000 | equivalent | v1_pool | 0.050 | equivalent | 1.000 |
| attn_pool | 107 | 53 | 279.795 | 280.925 | 1.131 | -0.172 | 2.770 | 2.798 | 0.002 | equivalent | v1_pool | 0.715 | inconclusive | 0.000 |
| v1_pool | 107 | 53 | 279.795 | 278.930 | -0.865 | -2.517 | 0.299 | 2.798 | 1.000 | equivalent | v1_pool | 0.000 | equivalent | 1.000 |
| rollcp2 | 23 | 10 | 134.715 | 134.719 | 0.005 | 0.000 | 0.014 | 1.347 | 0.102 | equivalent | - | - | - | - |
| edd | 107 | 53 | 279.795 | 279.795 | 0.000 | 0.000 | 0.000 | 2.798 | 1.000 | reference | v1_pool | 0.310 | equivalent | 1.000 |


## Empirical verdict campuses, crew multiplier by utilisation bin


**m=1.0|u_bin=<0.5** (85 configurations, 85 clusters). Against EDD, of 9 families compared: 9 equivalent (pfifo, wspt, atc, wmdd, lpt, random, mlp_pool, attn_pool, v1_pool). Sample-best family: edd.

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 85 | 85 | 307.361 | 307.361 | 0.000 | 0.000 | 0.000 | 3.074 | 1.000 | equivalent | edd | 0.000 | equivalent | 1.000 |
| wspt | 85 | 85 | 307.361 | 308.362 | 1.001 | 0.131 | 2.377 | 3.074 | 0.246 | equivalent | edd | 0.326 | equivalent | 1.000 |
| atc | 85 | 85 | 307.361 | 307.855 | 0.494 | 0.000 | 1.247 | 3.074 | 1.000 | equivalent | edd | 0.161 | equivalent | 1.000 |
| wmdd | 85 | 85 | 307.361 | 307.819 | 0.458 | 0.000 | 1.151 | 3.074 | 1.000 | equivalent | edd | 0.149 | equivalent | 1.000 |
| lpt | 85 | 85 | 307.361 | 307.427 | 0.066 | -0.005 | 0.175 | 3.074 | 1.000 | equivalent | edd | 0.021 | equivalent | 1.000 |
| random | 85 | 85 | 307.361 | 307.977 | 0.616 | 0.071 | 1.414 | 3.074 | 0.302 | equivalent | edd | 0.200 | equivalent | 1.000 |
| mlp_pool | 85 | 85 | 307.361 | 307.393 | 0.032 | -0.005 | 0.088 | 3.074 | 1.000 | equivalent | edd | 0.010 | equivalent | 1.000 |
| attn_pool | 85 | 85 | 307.361 | 307.730 | 0.368 | 0.000 | 0.984 | 3.074 | 0.246 | equivalent | edd | 0.120 | equivalent | 1.000 |
| v1_pool | 85 | 85 | 307.361 | 307.446 | 0.085 | -0.007 | 0.261 | 3.074 | 1.000 | equivalent | edd | 0.028 | equivalent | 1.000 |
| rollcp2 | 27 | 27 | 392.172 | 392.103 | -0.070 | -0.282 | 0.049 | 3.922 | 0.016 | equivalent | - | - | - | - |
| edd | 85 | 85 | 307.361 | 307.361 | 0.000 | 0.000 | 0.000 | 3.074 | 1.000 | reference | edd | 0.000 | equivalent | 1.000 |


**m=1.0|u_bin=0.5-0.8** (52 configurations, 52 clusters). Against EDD, of 9 families compared: 9 equivalent (pfifo, wspt, atc, wmdd, lpt, random, mlp_pool, attn_pool, v1_pool). Sample-best family: v1_pool.

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 52 | 52 | 859.959 | 859.959 | 0.000 | 0.000 | 0.000 | 8.600 | 1.000 | equivalent | v1_pool | 0.033 | equivalent | 1.000 |
| wspt | 52 | 52 | 859.959 | 861.878 | 1.918 | 0.260 | 4.253 | 8.600 | 0.252 | equivalent | v1_pool | 0.257 | equivalent | 1.000 |
| atc | 52 | 52 | 859.959 | 860.749 | 0.790 | -0.010 | 2.226 | 8.600 | 0.865 | equivalent | v1_pool | 0.125 | equivalent | 1.000 |
| wmdd | 52 | 52 | 859.959 | 860.574 | 0.615 | 0.000 | 1.692 | 8.600 | 0.899 | equivalent | v1_pool | 0.105 | equivalent | 1.000 |
| lpt | 52 | 52 | 859.959 | 860.088 | 0.129 | -0.492 | 0.803 | 8.600 | 1.000 | equivalent | v1_pool | 0.049 | equivalent | 1.000 |
| random | 52 | 52 | 859.959 | 860.930 | 0.971 | 0.161 | 1.998 | 8.600 | 0.252 | equivalent | v1_pool | 0.146 | equivalent | 1.000 |
| mlp_pool | 52 | 52 | 859.959 | 859.684 | -0.275 | -0.707 | 0.057 | 8.600 | 1.000 | equivalent | v1_pool | 0.001 | equivalent | 1.000 |
| attn_pool | 52 | 52 | 859.959 | 860.420 | 0.460 | -0.109 | 1.460 | 8.600 | 1.000 | equivalent | v1_pool | 0.087 | equivalent | 1.000 |
| v1_pool | 52 | 52 | 859.959 | 859.671 | -0.288 | -0.692 | -0.005 | 8.600 | 0.527 | equivalent | v1_pool | 0.000 | equivalent | 1.000 |
| rollcp2 | 11 | 11 | 1128.279 | 1128.359 | 0.079 | 0.027 | 0.140 | 11.283 | 0.016 | equivalent | - | - | - | - |
| edd | 52 | 52 | 859.959 | 859.959 | 0.000 | 0.000 | 0.000 | 8.600 | 1.000 | reference | v1_pool | 0.033 | equivalent | 1.000 |


**m=1.0|u_bin=0.8-1.0** (13 configurations, 13 clusters). Against EDD, of 9 families compared: 3 equivalent (pfifo, mlp_pool, v1_pool); 6 inconclusive (wspt, atc, wmdd, lpt, random, attn_pool). Sample-best family: mlp_pool.

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 13 | 13 | 279.746 | 279.746 | 0.000 | 0.000 | 0.000 | 2.797 | 1.000 | equivalent | mlp_pool | 0.194 | equivalent | 1.000 |
| wspt | 13 | 13 | 279.746 | 287.144 | 7.398 | 0.154 | 17.798 | 2.797 | 1.000 | inconclusive | mlp_pool | 2.844 | inconclusive | 0.000 |
| atc | 13 | 13 | 279.746 | 282.855 | 3.109 | 0.000 | 8.372 | 2.797 | 1.000 | inconclusive | mlp_pool | 1.308 | inconclusive | 0.000 |
| wmdd | 13 | 13 | 279.746 | 280.701 | 0.955 | 0.000 | 2.866 | 2.797 | 1.000 | inconclusive | mlp_pool | 0.536 | inconclusive | 0.000 |
| lpt | 13 | 13 | 279.746 | 288.592 | 8.846 | 0.000 | 26.538 | 2.797 | 1.000 | inconclusive | mlp_pool | 3.362 | inconclusive | 0.000 |
| random | 13 | 13 | 279.746 | 291.149 | 11.403 | 0.049 | 28.179 | 2.797 | 1.000 | inconclusive | mlp_pool | 4.278 | inconclusive | 0.000 |
| mlp_pool | 13 | 13 | 279.746 | 279.204 | -0.542 | -1.626 | 0.000 | 2.797 | 1.000 | equivalent | mlp_pool | 0.000 | equivalent | 1.000 |
| attn_pool | 13 | 13 | 279.746 | 280.715 | 0.970 | -0.178 | 3.072 | 2.797 | 1.000 | inconclusive | mlp_pool | 0.541 | inconclusive | 0.000 |
| v1_pool | 13 | 13 | 279.746 | 279.473 | -0.273 | -0.818 | 0.000 | 2.797 | 1.000 | equivalent | mlp_pool | 0.096 | equivalent | 1.000 |
| rollcp2 | 3 | 3 | 118.000 | 118.022 | 0.022 | 0.000 | 0.065 | 1.180 | 1.000 | equivalent | - | - | - | - |
| edd | 13 | 13 | 279.746 | 279.746 | 0.000 | 0.000 | 0.000 | 2.797 | 1.000 | reference | mlp_pool | 0.194 | equivalent | 1.000 |


**m=1.0|u_bin=1.0-1.2** (6 configurations, 6 clusters). Against EDD, of 9 families compared: 9 equivalent (pfifo, wspt, atc, wmdd, lpt, random, mlp_pool, attn_pool, v1_pool). Sample-best family: atc.

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 6 | 6 | 5.667 | 5.667 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | atc | 0.000 | equivalent | 1.000 |
| wspt | 6 | 6 | 5.667 | 5.667 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | atc | 0.000 | equivalent | 1.000 |
| atc | 6 | 6 | 5.667 | 5.667 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | atc | 0.000 | equivalent | 1.000 |
| wmdd | 6 | 6 | 5.667 | 5.667 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | atc | 0.000 | equivalent | 1.000 |
| lpt | 6 | 6 | 5.667 | 5.667 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | atc | 0.000 | equivalent | 1.000 |
| random | 6 | 6 | 5.667 | 5.667 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | atc | 0.000 | equivalent | 1.000 |
| mlp_pool | 6 | 6 | 5.667 | 5.667 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | atc | 0.000 | equivalent | 1.000 |
| attn_pool | 6 | 6 | 5.667 | 5.667 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | atc | 0.000 | equivalent | 1.000 |
| v1_pool | 6 | 6 | 5.667 | 5.667 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | atc | 0.000 | equivalent | 1.000 |
| rollcp2 | 1 | 1 | 34.000 | 34.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | - | - | - | - |
| edd | 6 | 6 | 5.667 | 5.667 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | reference | atc | 0.000 | equivalent | 1.000 |


**m=1.0|u_bin=>=1.2** (24 configurations, 24 clusters). Against EDD, of 9 families compared: 8 equivalent (pfifo, atc, wmdd, lpt, random, mlp_pool, attn_pool, v1_pool); 1 inconclusive (wspt). Sample-best family: atc.

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 24 | 24 | 231.756 | 231.756 | 0.000 | 0.000 | 0.000 | 2.318 | 1.000 | equivalent | atc | 0.000 | equivalent | 1.000 |
| wspt | 24 | 24 | 231.756 | 233.374 | 1.618 | 0.537 | 2.848 | 2.318 | 0.246 | inconclusive | atc | 0.698 | inconclusive | 0.000 |
| atc | 24 | 24 | 231.756 | 231.756 | 0.000 | 0.000 | 0.000 | 2.318 | 1.000 | equivalent | atc | 0.000 | equivalent | 1.000 |
| wmdd | 24 | 24 | 231.756 | 231.756 | 0.000 | 0.000 | 0.000 | 2.318 | 1.000 | equivalent | atc | 0.000 | equivalent | 1.000 |
| lpt | 24 | 24 | 231.756 | 231.774 | 0.018 | 0.000 | 0.054 | 2.318 | 1.000 | equivalent | atc | 0.008 | equivalent | 1.000 |
| random | 24 | 24 | 231.756 | 232.148 | 0.392 | 0.000 | 0.926 | 2.318 | 0.762 | equivalent | atc | 0.169 | equivalent | 1.000 |
| mlp_pool | 24 | 24 | 231.756 | 231.785 | 0.030 | 0.000 | 0.076 | 2.318 | 1.000 | equivalent | atc | 0.013 | equivalent | 1.000 |
| attn_pool | 24 | 24 | 231.756 | 231.921 | 0.165 | 0.005 | 0.355 | 2.318 | 0.543 | equivalent | atc | 0.071 | equivalent | 1.000 |
| v1_pool | 24 | 24 | 231.756 | 231.784 | 0.028 | 0.000 | 0.084 | 2.318 | 1.000 | equivalent | atc | 0.012 | equivalent | 1.000 |
| rollcp2 | 6 | 6 | 148.667 | 148.667 | 0.000 | 0.000 | 0.000 | 1.487 | 1.000 | equivalent | - | - | - | - |
| edd | 24 | 24 | 231.756 | 231.756 | 0.000 | 0.000 | 0.000 | 2.318 | 1.000 | reference | atc | 0.000 | equivalent | 1.000 |


**m=0.8|u_bin=<0.5** (61 configurations, 61 clusters). Against EDD, of 9 families compared: 8 equivalent (pfifo, atc, wmdd, lpt, random, mlp_pool, attn_pool, v1_pool); 1 inconclusive (wspt). Sample-best family: lpt.

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 61 | 61 | 223.973 | 223.973 | 0.000 | 0.000 | 0.000 | 2.240 | 1.000 | equivalent | lpt | 0.004 | equivalent | 1.000 |
| wspt | 61 | 61 | 223.973 | 225.317 | 1.345 | 0.262 | 2.887 | 2.240 | 0.162 | inconclusive | lpt | 0.604 | inconclusive | 0.000 |
| atc | 61 | 61 | 223.973 | 224.513 | 0.540 | 0.000 | 1.540 | 2.240 | 1.000 | equivalent | lpt | 0.245 | equivalent | 1.000 |
| wmdd | 61 | 61 | 223.973 | 224.560 | 0.587 | 0.000 | 1.681 | 2.240 | 1.000 | equivalent | lpt | 0.266 | equivalent | 1.000 |
| lpt | 61 | 61 | 223.973 | 223.964 | -0.009 | -0.026 | 0.000 | 2.240 | 1.000 | equivalent | lpt | 0.000 | equivalent | 1.000 |
| random | 61 | 61 | 223.973 | 224.596 | 0.623 | 0.066 | 1.411 | 2.240 | 0.459 | equivalent | lpt | 0.282 | equivalent | 1.000 |
| mlp_pool | 61 | 61 | 223.973 | 223.980 | 0.007 | 0.000 | 0.022 | 2.240 | 1.000 | equivalent | lpt | 0.007 | equivalent | 1.000 |
| attn_pool | 61 | 61 | 223.973 | 224.356 | 0.383 | 0.020 | 0.992 | 2.240 | 0.345 | equivalent | lpt | 0.175 | equivalent | 1.000 |
| v1_pool | 61 | 61 | 223.973 | 223.968 | -0.004 | -0.013 | 0.000 | 2.240 | 1.000 | equivalent | lpt | 0.002 | equivalent | 1.000 |
| rollcp2 | 18 | 18 | 234.254 | 234.272 | 0.018 | 0.005 | 0.036 | 2.343 | 0.012 | equivalent | - | - | - | - |
| edd | 61 | 61 | 223.973 | 223.973 | 0.000 | 0.000 | 0.000 | 2.240 | 1.000 | reference | lpt | 0.004 | equivalent | 1.000 |


**m=0.8|u_bin=0.5-0.8** (52 configurations, 52 clusters). Against EDD, of 9 families compared: 6 equivalent (pfifo, atc, wmdd, mlp_pool, attn_pool, v1_pool); 3 inconclusive (wspt, lpt, random). Sample-best family: v1_pool.

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 52 | 52 | 757.461 | 757.461 | 0.000 | 0.000 | 0.000 | 7.575 | 1.000 | equivalent | v1_pool | 0.066 | equivalent | 1.000 |
| wspt | 52 | 52 | 757.461 | 762.771 | 5.310 | 1.674 | 10.025 | 7.575 | 0.020 | inconclusive | v1_pool | 0.767 | inconclusive | 0.000 |
| atc | 52 | 52 | 757.461 | 760.594 | 3.133 | 0.435 | 6.477 | 7.575 | 0.166 | equivalent | v1_pool | 0.480 | equivalent | 1.000 |
| wmdd | 52 | 52 | 757.461 | 759.321 | 1.860 | 0.227 | 3.893 | 7.575 | 0.272 | equivalent | v1_pool | 0.312 | equivalent | 1.000 |
| lpt | 52 | 52 | 757.461 | 783.024 | 25.563 | 1.645 | 66.027 | 7.575 | 0.166 | inconclusive | v1_pool | 3.443 | inconclusive | 0.000 |
| random | 52 | 52 | 757.461 | 766.357 | 8.897 | 1.701 | 19.715 | 7.575 | 0.024 | inconclusive | v1_pool | 1.241 | inconclusive | 0.000 |
| mlp_pool | 52 | 52 | 757.461 | 757.351 | -0.110 | -1.182 | 1.288 | 7.575 | 0.615 | equivalent | v1_pool | 0.051 | equivalent | 1.000 |
| attn_pool | 52 | 52 | 757.461 | 760.045 | 2.585 | 0.369 | 5.556 | 7.575 | 0.140 | equivalent | v1_pool | 0.407 | equivalent | 1.000 |
| v1_pool | 52 | 52 | 757.461 | 756.962 | -0.499 | -1.338 | 0.256 | 7.575 | 0.408 | equivalent | v1_pool | 0.000 | equivalent | 1.000 |
| rollcp2 | 18 | 18 | 936.824 | 935.422 | -1.402 | -3.561 | 0.126 | 9.368 | 0.638 | equivalent | - | - | - | - |
| edd | 52 | 52 | 757.461 | 757.461 | 0.000 | 0.000 | 0.000 | 7.575 | 1.000 | reference | v1_pool | 0.066 | equivalent | 1.000 |


**m=0.8|u_bin=0.8-1.0** (24 configurations, 24 clusters). Against EDD, of 9 families compared: 7 equivalent (pfifo, atc, wmdd, lpt, mlp_pool, attn_pool, v1_pool); 2 inconclusive (wspt, random). Sample-best family: v1_pool.

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 24 | 24 | 746.947 | 746.947 | 0.000 | 0.000 | 0.000 | 7.469 | 1.000 | equivalent | v1_pool | 0.045 | equivalent | 1.000 |
| wspt | 24 | 24 | 746.947 | 751.884 | 4.937 | 0.770 | 10.607 | 7.469 | 0.249 | inconclusive | v1_pool | 0.706 | inconclusive | 0.000 |
| atc | 24 | 24 | 746.947 | 747.803 | 0.856 | 0.000 | 2.538 | 7.469 | 1.000 | equivalent | v1_pool | 0.159 | equivalent | 1.000 |
| wmdd | 24 | 24 | 746.947 | 747.311 | 0.364 | 0.000 | 1.061 | 7.469 | 1.000 | equivalent | v1_pool | 0.093 | equivalent | 1.000 |
| lpt | 24 | 24 | 746.947 | 748.734 | 1.787 | -0.889 | 6.250 | 7.469 | 1.000 | equivalent | v1_pool | 0.284 | equivalent | 1.000 |
| random | 24 | 24 | 746.947 | 751.489 | 4.542 | 0.292 | 10.833 | 7.469 | 0.475 | inconclusive | v1_pool | 0.653 | inconclusive | 0.000 |
| mlp_pool | 24 | 24 | 746.947 | 746.677 | -0.271 | -0.825 | 0.013 | 7.469 | 1.000 | equivalent | v1_pool | 0.008 | equivalent | 1.000 |
| attn_pool | 24 | 24 | 746.947 | 747.789 | 0.842 | 0.053 | 2.187 | 7.469 | 0.371 | equivalent | v1_pool | 0.157 | equivalent | 1.000 |
| v1_pool | 24 | 24 | 746.947 | 746.614 | -0.333 | -1.000 | 0.000 | 7.469 | 1.000 | equivalent | v1_pool | 0.000 | equivalent | 1.000 |
| rollcp2 | 2 | 2 | 977.334 | 977.482 | 0.148 | 0.000 | 0.296 | 9.773 | 1.000 | equivalent | - | - | - | - |
| edd | 24 | 24 | 746.947 | 746.947 | 0.000 | 0.000 | 0.000 | 7.469 | 1.000 | reference | v1_pool | 0.045 | equivalent | 1.000 |


**m=0.8|u_bin=1.0-1.2** (13 configurations, 13 clusters). Against EDD, of 9 families compared: 2 equivalent (pfifo, v1_pool); 7 inconclusive (wspt, atc, wmdd, lpt, random, mlp_pool, attn_pool). Sample-best family: mlp_pool.

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 13 | 13 | 282.415 | 282.415 | 0.000 | 0.000 | 0.000 | 2.824 | 1.000 | equivalent | mlp_pool | 0.407 | inconclusive | 0.000 |
| wspt | 13 | 13 | 282.415 | 292.698 | 10.284 | 0.265 | 22.248 | 2.824 | 1.000 | inconclusive | mlp_pool | 4.063 | inconclusive | 0.000 |
| atc | 13 | 13 | 282.415 | 286.957 | 4.542 | -0.224 | 12.040 | 2.824 | 1.000 | inconclusive | mlp_pool | 2.022 | inconclusive | 0.000 |
| wmdd | 13 | 13 | 282.415 | 284.155 | 1.741 | 0.000 | 4.501 | 2.824 | 1.000 | inconclusive | mlp_pool | 1.026 | inconclusive | 0.000 |
| lpt | 13 | 13 | 282.415 | 297.328 | 14.913 | 0.000 | 44.633 | 2.824 | 1.000 | inconclusive | mlp_pool | 5.709 | inconclusive | 0.000 |
| random | 13 | 13 | 282.415 | 289.156 | 6.741 | -0.202 | 16.433 | 2.824 | 1.000 | inconclusive | mlp_pool | 2.804 | inconclusive | 0.000 |
| mlp_pool | 13 | 13 | 282.415 | 281.270 | -1.145 | -3.323 | 0.000 | 2.824 | 1.000 | inconclusive | mlp_pool | 0.000 | equivalent | 1.000 |
| attn_pool | 13 | 13 | 282.415 | 282.848 | 0.434 | -2.008 | 3.339 | 2.824 | 1.000 | inconclusive | mlp_pool | 0.561 | inconclusive | 0.000 |
| v1_pool | 13 | 13 | 282.415 | 281.474 | -0.941 | -2.598 | 0.000 | 2.824 | 1.000 | equivalent | mlp_pool | 0.073 | equivalent | 1.000 |
| rollcp2 | 3 | 3 | 118.000 | 118.022 | 0.022 | 0.000 | 0.065 | 1.180 | 1.000 | equivalent | - | - | - | - |
| edd | 13 | 13 | 282.415 | 282.415 | 0.000 | 0.000 | 0.000 | 2.824 | 1.000 | reference | mlp_pool | 0.407 | inconclusive | 0.000 |


**m=0.8|u_bin=>=1.2** (30 configurations, 30 clusters). Against EDD, of 9 families compared: 8 equivalent (pfifo, atc, wmdd, lpt, random, mlp_pool, attn_pool, v1_pool); 1 inconclusive (wspt). Sample-best family: lpt.

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 30 | 30 | 191.535 | 191.535 | 0.000 | 0.000 | 0.000 | 1.915 | 1.000 | equivalent | lpt | 0.007 | equivalent | 1.000 |
| wspt | 30 | 30 | 191.535 | 193.549 | 2.015 | 0.651 | 3.680 | 1.915 | 0.249 | inconclusive | lpt | 1.059 | inconclusive | 0.000 |
| atc | 30 | 30 | 191.535 | 191.535 | 0.000 | 0.000 | 0.000 | 1.915 | 1.000 | equivalent | lpt | 0.007 | equivalent | 1.000 |
| wmdd | 30 | 30 | 191.535 | 191.535 | 0.000 | 0.000 | 0.000 | 1.915 | 1.000 | equivalent | lpt | 0.007 | equivalent | 1.000 |
| lpt | 30 | 30 | 191.535 | 191.521 | -0.014 | -0.043 | 0.000 | 1.915 | 1.000 | equivalent | lpt | 0.000 | equivalent | 1.000 |
| random | 30 | 30 | 191.535 | 191.992 | 0.457 | 0.017 | 1.016 | 1.915 | 0.557 | equivalent | lpt | 0.246 | equivalent | 1.000 |
| mlp_pool | 30 | 30 | 191.535 | 191.546 | 0.011 | -0.016 | 0.047 | 1.915 | 1.000 | equivalent | lpt | 0.013 | equivalent | 1.000 |
| attn_pool | 30 | 30 | 191.535 | 191.728 | 0.194 | 0.008 | 0.427 | 1.915 | 0.345 | equivalent | lpt | 0.109 | equivalent | 1.000 |
| v1_pool | 30 | 30 | 191.535 | 191.522 | -0.013 | -0.039 | 0.000 | 1.915 | 1.000 | equivalent | lpt | 0.001 | equivalent | 1.000 |
| rollcp2 | 7 | 7 | 132.317 | 132.320 | 0.003 | 0.000 | 0.010 | 1.323 | 1.000 | equivalent | - | - | - | - |
| edd | 30 | 30 | 191.535 | 191.535 | 0.000 | 0.000 | 0.000 | 1.915 | 1.000 | reference | lpt | 0.007 | equivalent | 1.000 |


**m=0.6|u_bin=<0.5** (34 configurations, 34 clusters). Against EDD, of 9 families compared: 5 equivalent (pfifo, wmdd, mlp_pool, attn_pool, v1_pool); 4 inconclusive (wspt, atc, lpt, random). Sample-best family: v1_pool.

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 34 | 34 | 148.270 | 148.270 | 0.000 | 0.000 | 0.000 | 1.483 | 1.000 | equivalent | v1_pool | 0.101 | equivalent | 1.000 |
| wspt | 34 | 34 | 148.270 | 150.560 | 2.290 | 0.353 | 4.929 | 1.483 | 0.388 | inconclusive | v1_pool | 1.647 | inconclusive | 0.000 |
| atc | 34 | 34 | 148.270 | 148.860 | 0.590 | 0.000 | 1.537 | 1.483 | 1.000 | inconclusive | v1_pool | 0.499 | inconclusive | 0.000 |
| wmdd | 34 | 34 | 148.270 | 148.772 | 0.502 | 0.000 | 1.271 | 1.483 | 1.000 | equivalent | v1_pool | 0.439 | inconclusive | 0.000 |
| lpt | 34 | 34 | 148.270 | 149.446 | 1.176 | 0.000 | 3.412 | 1.483 | 1.000 | inconclusive | v1_pool | 0.895 | inconclusive | 0.000 |
| random | 34 | 34 | 148.270 | 149.841 | 1.571 | 0.000 | 3.537 | 1.483 | 0.762 | inconclusive | v1_pool | 1.161 | inconclusive | 0.000 |
| mlp_pool | 34 | 34 | 148.270 | 148.189 | -0.081 | -0.619 | 0.318 | 1.483 | 1.000 | equivalent | v1_pool | 0.046 | equivalent | 1.000 |
| attn_pool | 34 | 34 | 148.270 | 148.911 | 0.641 | 0.059 | 1.311 | 1.483 | 0.543 | equivalent | v1_pool | 0.533 | inconclusive | 0.000 |
| v1_pool | 34 | 34 | 148.270 | 148.121 | -0.149 | -0.447 | 0.000 | 1.483 | 1.000 | equivalent | v1_pool | 0.000 | equivalent | 1.000 |
| rollcp2 | 9 | 9 | 281.880 | 282.356 | 0.477 | 0.016 | 1.365 | 2.819 | 0.031 | equivalent | - | - | - | - |
| edd | 34 | 34 | 148.270 | 148.270 | 0.000 | 0.000 | 0.000 | 1.483 | 1.000 | reference | v1_pool | 0.101 | equivalent | 1.000 |


**m=0.6|u_bin=0.5-0.8** (48 configurations, 48 clusters). Against EDD, of 9 families compared: 3 equivalent (pfifo, mlp_pool, v1_pool); 6 inconclusive (wspt, atc, wmdd, lpt, random, attn_pool). Sample-best family: mlp_pool.

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 48 | 48 | 424.741 | 424.741 | 0.000 | 0.000 | 0.000 | 4.247 | 1.000 | equivalent | mlp_pool | 0.276 | equivalent | 1.000 |
| wspt | 48 | 48 | 424.741 | 433.740 | 9.000 | 1.639 | 19.844 | 4.247 | 0.020 | inconclusive | mlp_pool | 2.401 | inconclusive | 0.000 |
| atc | 48 | 48 | 424.741 | 428.503 | 3.762 | 0.053 | 9.439 | 4.247 | 0.259 | inconclusive | mlp_pool | 1.164 | inconclusive | 0.000 |
| wmdd | 48 | 48 | 424.741 | 427.705 | 2.964 | 0.050 | 7.307 | 4.247 | 0.259 | inconclusive | mlp_pool | 0.976 | inconclusive | 0.000 |
| lpt | 48 | 48 | 424.741 | 459.713 | 34.972 | -0.332 | 97.706 | 4.247 | 1.000 | inconclusive | mlp_pool | 8.532 | inconclusive | 0.000 |
| random | 48 | 48 | 424.741 | 434.268 | 9.527 | 1.148 | 23.565 | 4.247 | 0.027 | inconclusive | mlp_pool | 2.525 | inconclusive | 0.000 |
| mlp_pool | 48 | 48 | 424.741 | 423.572 | -1.169 | -3.024 | -0.059 | 4.247 | 0.705 | equivalent | mlp_pool | 0.000 | equivalent | 1.000 |
| attn_pool | 48 | 48 | 424.741 | 428.276 | 3.536 | 0.209 | 9.421 | 4.247 | 0.036 | inconclusive | mlp_pool | 1.111 | inconclusive | 0.000 |
| v1_pool | 48 | 48 | 424.741 | 424.256 | -0.485 | -2.085 | 0.785 | 4.247 | 1.000 | equivalent | mlp_pool | 0.161 | equivalent | 1.000 |
| rollcp2 | 18 | 18 | 455.492 | 455.607 | 0.115 | -1.251 | 1.549 | 4.555 | 0.086 | equivalent | - | - | - | - |
| edd | 48 | 48 | 424.741 | 424.741 | 0.000 | 0.000 | 0.000 | 4.247 | 1.000 | reference | mlp_pool | 0.276 | equivalent | 1.000 |


**m=0.6|u_bin=0.8-1.0** (27 configurations, 27 clusters). Against EDD, of 9 families compared: 2 equivalent (pfifo, mlp_pool); 6 inconclusive (wspt, atc, wmdd, random, attn_pool, v1_pool); 1 worse (lpt). Sample-best family: v1_pool.

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 27 | 27 | 683.409 | 683.409 | 0.000 | 0.000 | 0.000 | 6.834 | 1.000 | equivalent | v1_pool | 0.613 | inconclusive | 0.000 |
| wspt | 27 | 27 | 683.409 | 697.341 | 13.932 | -1.097 | 31.868 | 6.834 | 0.183 | inconclusive | v1_pool | 2.664 | inconclusive | 0.000 |
| atc | 27 | 27 | 683.409 | 688.367 | 4.958 | -5.254 | 15.763 | 6.834 | 0.525 | inconclusive | v1_pool | 1.343 | inconclusive | 0.000 |
| wmdd | 27 | 27 | 683.409 | 689.634 | 6.225 | 1.559 | 11.914 | 6.834 | 0.184 | inconclusive | v1_pool | 1.529 | inconclusive | 0.000 |
| lpt | 27 | 27 | 683.409 | 763.750 | 80.341 | 22.476 | 159.171 | 6.834 | 0.046 | worse | v1_pool | 12.441 | worse | 0.000 |
| random | 27 | 27 | 683.409 | 701.865 | 18.456 | 0.835 | 39.639 | 6.834 | 0.184 | inconclusive | v1_pool | 3.330 | inconclusive | 0.000 |
| mlp_pool | 27 | 27 | 683.409 | 681.374 | -2.035 | -4.964 | 0.534 | 6.834 | 0.484 | equivalent | v1_pool | 0.313 | equivalent | 1.000 |
| attn_pool | 27 | 27 | 683.409 | 687.758 | 4.349 | -3.372 | 12.889 | 6.834 | 0.398 | inconclusive | v1_pool | 1.253 | inconclusive | 0.000 |
| v1_pool | 27 | 27 | 683.409 | 679.248 | -4.161 | -9.712 | -0.338 | 6.834 | 0.253 | inconclusive | v1_pool | 0.000 | equivalent | 1.000 |
| rollcp2 | 8 | 8 | 1098.499 | 1094.813 | -3.686 | -10.266 | 0.656 | 10.985 | 0.812 | equivalent | - | - | - | - |
| edd | 27 | 27 | 683.409 | 683.409 | 0.000 | 0.000 | 0.000 | 6.834 | 1.000 | reference | v1_pool | 0.613 | inconclusive | 0.000 |


**m=0.6|u_bin=1.0-1.2** (18 configurations, 18 clusters). Against EDD, of 9 families compared: 1 equivalent (pfifo); 6 inconclusive (wspt, atc, wmdd, mlp_pool, attn_pool, v1_pool); 2 worse (lpt, random). Sample-best family: edd.

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 18 | 18 | 1044.324 | 1044.324 | 0.000 | 0.000 | 0.000 | 10.443 | 1.000 | equivalent | edd | 0.000 | equivalent | 1.000 |
| wspt | 18 | 18 | 1044.324 | 1075.716 | 31.391 | 5.799 | 75.139 | 10.443 | 0.062 | inconclusive | edd | 3.006 | inconclusive | 0.000 |
| atc | 18 | 18 | 1044.324 | 1055.607 | 11.282 | 1.560 | 27.309 | 10.443 | 0.166 | inconclusive | edd | 1.080 | inconclusive | 0.000 |
| wmdd | 18 | 18 | 1044.324 | 1052.324 | 8.000 | 0.824 | 19.355 | 10.443 | 0.166 | inconclusive | edd | 0.766 | inconclusive | 0.000 |
| lpt | 18 | 18 | 1044.324 | 1505.763 | 461.439 | 11.024 | 1340.627 | 10.443 | 0.153 | worse | edd | 44.185 | worse | 0.000 |
| random | 18 | 18 | 1044.324 | 1218.668 | 174.343 | 11.052 | 488.241 | 10.443 | 0.062 | worse | edd | 16.694 | worse | 0.000 |
| mlp_pool | 18 | 18 | 1044.324 | 1051.061 | 6.737 | -0.794 | 17.579 | 10.443 | 1.000 | inconclusive | edd | 0.645 | inconclusive | 0.000 |
| attn_pool | 18 | 18 | 1044.324 | 1059.370 | 15.046 | 1.263 | 38.244 | 10.443 | 0.275 | inconclusive | edd | 1.441 | inconclusive | 0.000 |
| v1_pool | 18 | 18 | 1044.324 | 1048.881 | 4.557 | -1.136 | 12.705 | 10.443 | 1.000 | inconclusive | edd | 0.436 | inconclusive | 0.000 |
| rollcp2 | 3 | 3 | 1236.500 | 1233.763 | -2.737 | -7.990 | 0.000 | 12.365 | 0.500 | equivalent | - | - | - | - |
| edd | 18 | 18 | 1044.324 | 1044.324 | 0.000 | 0.000 | 0.000 | 10.443 | 1.000 | reference | edd | 0.000 | equivalent | 1.000 |


**m=0.6|u_bin=>=1.2** (53 configurations, 53 clusters). Against EDD, of 9 families compared: 1 equivalent (pfifo); 6 inconclusive (atc, wmdd, lpt, mlp_pool, attn_pool, v1_pool); 2 worse (wspt, random). Sample-best family: v1_pool.

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 53 | 53 | 351.506 | 351.506 | 0.000 | 0.000 | 0.000 | 3.515 | 1.000 | equivalent | v1_pool | 0.501 | inconclusive | 0.000 |
| wspt | 53 | 53 | 351.506 | 365.097 | 13.591 | 4.179 | 25.741 | 3.515 | 0.003 | worse | v1_pool | 4.387 | worse | 0.000 |
| atc | 53 | 53 | 351.506 | 357.417 | 5.910 | 0.212 | 13.017 | 3.515 | 0.166 | inconclusive | v1_pool | 2.191 | inconclusive | 0.000 |
| wmdd | 53 | 53 | 351.506 | 354.057 | 2.551 | 0.139 | 5.602 | 3.515 | 0.216 | inconclusive | v1_pool | 1.230 | inconclusive | 0.000 |
| lpt | 53 | 53 | 351.506 | 410.235 | 58.729 | 0.000 | 164.403 | 3.515 | 0.552 | inconclusive | v1_pool | 17.292 | inconclusive | 0.000 |
| random | 53 | 53 | 351.506 | 366.999 | 15.492 | 3.629 | 30.552 | 3.515 | 0.005 | worse | v1_pool | 4.930 | worse | 0.000 |
| mlp_pool | 53 | 53 | 351.506 | 350.022 | -1.484 | -4.237 | 0.528 | 3.515 | 1.000 | inconclusive | v1_pool | 0.076 | equivalent | 1.000 |
| attn_pool | 53 | 53 | 351.506 | 353.605 | 2.099 | -0.481 | 5.195 | 3.515 | 0.063 | inconclusive | v1_pool | 1.101 | inconclusive | 0.000 |
| v1_pool | 53 | 53 | 351.506 | 349.755 | -1.751 | -4.863 | 0.560 | 3.515 | 0.929 | inconclusive | v1_pool | 0.000 | equivalent | 1.000 |
| rollcp2 | 10 | 10 | 128.022 | 128.030 | 0.009 | 0.000 | 0.022 | 1.280 | 0.500 | equivalent | - | - | - | - |
| edd | 53 | 53 | 351.506 | 351.506 | 0.000 | 0.000 | 0.000 | 3.515 | 1.000 | reference | v1_pool | 0.501 | inconclusive | 0.000 |


## Generator cells, pooled


**ALL** (300 configurations, 300 clusters). Against EDD, of 9 families compared: 1 equivalent (pfifo); 2 inconclusive (atc, wmdd); 6 worse (wspt, lpt, random, mlp_pool, attn_pool, v1_pool). Sample-best family: pfifo.

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 300 | 300 | 3334.123 | 3333.926 | -0.197 | -0.615 | 0.026 | 33.341 | 0.686 | equivalent | pfifo | 0.000 | equivalent | 1.000 |
| wspt | 300 | 300 | 3334.123 | 4064.613 | 730.490 | 616.011 | 856.535 | 33.341 | 0.000 | worse | pfifo | 21.917 | worse | 0.000 |
| atc | 300 | 300 | 3334.123 | 3357.983 | 23.860 | 6.632 | 39.046 | 33.341 | 0.000 | inconclusive | pfifo | 0.722 | inconclusive | 0.000 |
| wmdd | 300 | 300 | 3334.123 | 3354.937 | 20.814 | 3.917 | 35.343 | 33.341 | 0.000 | inconclusive | pfifo | 0.630 | inconclusive | 0.000 |
| lpt | 300 | 300 | 3334.123 | 43030.639 | 39696.516 | 33896.156 | 45704.663 | 33.341 | 0.000 | worse | pfifo | 1190.690 | worse | 0.000 |
| random | 300 | 300 | 3334.123 | 13236.398 | 9902.275 | 8231.783 | 11693.674 | 33.341 | 0.000 | worse | pfifo | 297.021 | worse | 0.000 |
| mlp_pool | 300 | 300 | 3334.123 | 3477.785 | 143.663 | 103.958 | 188.351 | 33.341 | 0.000 | worse | pfifo | 4.315 | worse | 0.000 |
| attn_pool | 300 | 300 | 3334.123 | 3931.662 | 597.539 | 512.087 | 688.841 | 33.341 | 0.000 | worse | pfifo | 17.929 | worse | 0.000 |
| v1_pool | 300 | 300 | 3334.123 | 4026.608 | 692.485 | 558.506 | 835.280 | 33.341 | 0.000 | worse | pfifo | 20.777 | worse | 0.000 |
| edd | 300 | 300 | 3334.123 | 3334.123 | 0.000 | 0.000 | 0.000 | 33.341 | 1.000 | reference | pfifo | 0.006 | equivalent | 1.000 |


## Generator cells, per target utilisation


**u_target=0.7** (60 configurations, 60 clusters). Against EDD, of 9 families compared: 7 equivalent (pfifo, wspt, atc, wmdd, mlp_pool, attn_pool, v1_pool); 2 worse (lpt, random). Sample-best family: mlp_pool.

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 60 | 60 | 2258.266 | 2258.266 | 0.000 | 0.000 | 0.000 | 22.583 | 1.000 | equivalent | mlp_pool | 0.010 | equivalent | 1.000 |
| wspt | 60 | 60 | 2258.266 | 2269.049 | 10.783 | 5.726 | 17.384 | 22.583 | 0.000 | equivalent | mlp_pool | 0.488 | equivalent | 1.000 |
| atc | 60 | 60 | 2258.266 | 2258.746 | 0.480 | -0.707 | 1.745 | 22.583 | 1.000 | equivalent | mlp_pool | 0.031 | equivalent | 1.000 |
| wmdd | 60 | 60 | 2258.266 | 2259.155 | 0.889 | 0.316 | 1.620 | 22.583 | 0.007 | equivalent | mlp_pool | 0.049 | equivalent | 1.000 |
| lpt | 60 | 60 | 2258.266 | 2574.504 | 316.238 | 200.923 | 454.914 | 22.583 | 0.000 | worse | mlp_pool | 14.015 | worse | 0.000 |
| random | 60 | 60 | 2258.266 | 2304.053 | 45.787 | 23.993 | 73.647 | 22.583 | 0.000 | worse | mlp_pool | 2.038 | worse | 0.000 |
| mlp_pool | 60 | 60 | 2258.266 | 2258.039 | -0.227 | -0.983 | 0.523 | 22.583 | 1.000 | equivalent | mlp_pool | 0.000 | equivalent | 1.000 |
| attn_pool | 60 | 60 | 2258.266 | 2268.172 | 9.906 | 5.365 | 15.999 | 22.583 | 0.000 | equivalent | mlp_pool | 0.449 | equivalent | 1.000 |
| v1_pool | 60 | 60 | 2258.266 | 2260.318 | 2.052 | -0.280 | 5.073 | 22.583 | 1.000 | equivalent | mlp_pool | 0.101 | equivalent | 1.000 |
| edd | 60 | 60 | 2258.266 | 2258.266 | 0.000 | 0.000 | 0.000 | 22.583 | 1.000 | reference | mlp_pool | 0.010 | equivalent | 1.000 |


**u_target=0.9** (60 configurations, 60 clusters). Against EDD, of 9 families compared: 4 equivalent (pfifo, atc, wmdd, mlp_pool); 5 worse (wspt, lpt, random, attn_pool, v1_pool). Sample-best family: edd.

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 60 | 60 | 3000.471 | 3000.471 | 0.000 | 0.000 | 0.000 | 30.005 | 1.000 | equivalent | edd | 0.000 | equivalent | 1.000 |
| wspt | 60 | 60 | 3000.471 | 3214.838 | 214.367 | 153.918 | 278.752 | 30.005 | 0.000 | worse | edd | 7.144 | worse | 0.000 |
| atc | 60 | 60 | 3000.471 | 3011.755 | 11.284 | 5.493 | 17.625 | 30.005 | 0.000 | equivalent | edd | 0.376 | equivalent | 1.000 |
| wmdd | 60 | 60 | 3000.471 | 3008.921 | 8.450 | 4.741 | 12.661 | 30.005 | 0.000 | equivalent | edd | 0.282 | equivalent | 1.000 |
| lpt | 60 | 60 | 3000.471 | 16524.005 | 13523.534 | 10714.114 | 16358.838 | 30.005 | 0.000 | worse | edd | 450.714 | worse | 0.000 |
| random | 60 | 60 | 3000.471 | 4924.665 | 1924.194 | 1496.218 | 2371.890 | 30.005 | 0.000 | worse | edd | 64.130 | worse | 0.000 |
| mlp_pool | 60 | 60 | 3000.471 | 3006.350 | 5.879 | -0.300 | 11.802 | 30.005 | 0.031 | equivalent | edd | 0.196 | equivalent | 1.000 |
| attn_pool | 60 | 60 | 3000.471 | 3218.868 | 218.397 | 180.706 | 256.359 | 30.005 | 0.000 | worse | edd | 7.279 | worse | 0.000 |
| v1_pool | 60 | 60 | 3000.471 | 3072.348 | 71.877 | 44.088 | 104.697 | 30.005 | 0.000 | worse | edd | 2.396 | worse | 0.000 |
| edd | 60 | 60 | 3000.471 | 3000.471 | 0.000 | 0.000 | 0.000 | 30.005 | 1.000 | reference | edd | 0.000 | equivalent | 1.000 |


**u_target=1.0** (60 configurations, 60 clusters). Against EDD, of 9 families compared: 2 equivalent (pfifo, wmdd); 2 inconclusive (atc, mlp_pool); 5 worse (wspt, lpt, random, attn_pool, v1_pool). Sample-best family: edd.

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 60 | 60 | 3120.226 | 3120.226 | 0.000 | 0.000 | 0.000 | 31.202 | 1.000 | equivalent | edd | 0.000 | equivalent | 1.000 |
| wspt | 60 | 60 | 3120.226 | 3527.016 | 406.790 | 313.646 | 507.605 | 31.202 | 0.000 | worse | edd | 13.037 | worse | 0.000 |
| atc | 60 | 60 | 3120.226 | 3141.091 | 20.865 | 11.318 | 31.606 | 31.202 | 0.000 | inconclusive | edd | 0.669 | inconclusive | 0.000 |
| wmdd | 60 | 60 | 3120.226 | 3139.498 | 19.273 | 10.675 | 28.894 | 31.202 | 0.000 | equivalent | edd | 0.618 | equivalent | 1.000 |
| lpt | 60 | 60 | 3120.226 | 29770.910 | 26650.684 | 21757.284 | 31574.756 | 31.202 | 0.000 | worse | edd | 854.127 | worse | 0.000 |
| random | 60 | 60 | 3120.226 | 8149.989 | 5029.763 | 3979.733 | 6192.263 | 31.202 | 0.000 | worse | edd | 161.199 | worse | 0.000 |
| mlp_pool | 60 | 60 | 3120.226 | 3143.023 | 22.797 | 14.668 | 32.256 | 31.202 | 0.000 | inconclusive | edd | 0.731 | inconclusive | 0.000 |
| attn_pool | 60 | 60 | 3120.226 | 3529.898 | 409.672 | 343.923 | 480.273 | 31.202 | 0.000 | worse | edd | 13.130 | worse | 0.000 |
| v1_pool | 60 | 60 | 3120.226 | 3345.697 | 225.471 | 159.037 | 306.462 | 31.202 | 0.000 | worse | edd | 7.226 | worse | 0.000 |
| edd | 60 | 60 | 3120.226 | 3120.226 | 0.000 | 0.000 | 0.000 | 31.202 | 1.000 | reference | edd | 0.000 | equivalent | 1.000 |


**u_target=1.1** (60 configurations, 60 clusters). Against EDD, of 9 families compared: 1 equivalent (pfifo); 2 inconclusive (atc, wmdd); 6 worse (wspt, lpt, random, mlp_pool, attn_pool, v1_pool). Sample-best family: pfifo.

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 60 | 60 | 3699.835 | 3698.828 | -1.007 | -3.020 | 0.000 | 36.998 | 0.317 | equivalent | pfifo | 0.000 | equivalent | 1.000 |
| wspt | 60 | 60 | 3699.835 | 4509.238 | 809.403 | 641.602 | 997.648 | 36.998 | 0.000 | worse | pfifo | 21.910 | worse | 0.000 |
| atc | 60 | 60 | 3699.835 | 3736.408 | 36.573 | 16.428 | 60.019 | 36.998 | 0.000 | inconclusive | pfifo | 1.016 | inconclusive | 0.000 |
| wmdd | 60 | 60 | 3699.835 | 3737.153 | 37.318 | 18.446 | 58.881 | 36.998 | 0.000 | inconclusive | pfifo | 1.036 | inconclusive | 0.000 |
| lpt | 60 | 60 | 3699.835 | 52750.153 | 49050.318 | 40745.394 | 57310.055 | 36.998 | 0.000 | worse | pfifo | 1326.131 | worse | 0.000 |
| random | 60 | 60 | 3699.835 | 14661.981 | 10962.146 | 8899.010 | 13009.502 | 36.998 | 0.000 | worse | pfifo | 296.395 | worse | 0.000 |
| mlp_pool | 60 | 60 | 3699.835 | 3806.663 | 106.828 | 65.780 | 155.512 | 36.998 | 0.000 | worse | pfifo | 2.915 | worse | 0.000 |
| attn_pool | 60 | 60 | 3699.835 | 4430.877 | 731.042 | 614.576 | 856.475 | 36.998 | 0.000 | worse | pfifo | 19.791 | worse | 0.000 |
| v1_pool | 60 | 60 | 3699.835 | 4410.234 | 710.399 | 566.297 | 858.092 | 36.998 | 0.000 | worse | pfifo | 19.233 | worse | 0.000 |
| edd | 60 | 60 | 3699.835 | 3699.835 | 0.000 | 0.000 | 0.000 | 36.998 | 1.000 | reference | pfifo | 0.027 | equivalent | 1.000 |


**u_target=1.3** (60 configurations, 60 clusters). Against EDD, of 9 families compared: 1 equivalent (pfifo); 2 inconclusive (atc, wmdd); 6 worse (wspt, lpt, random, mlp_pool, attn_pool, v1_pool). Sample-best family: edd.

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 60 | 60 | 4591.817 | 4591.841 | 0.024 | -0.098 | 0.158 | 45.918 | 0.715 | equivalent | edd | 0.001 | equivalent | 1.000 |
| wspt | 60 | 60 | 4591.817 | 6802.923 | 2211.106 | 1853.689 | 2566.335 | 45.918 | 0.000 | worse | edd | 48.153 | worse | 0.000 |
| atc | 60 | 60 | 4591.817 | 4641.915 | 50.098 | -33.565 | 120.432 | 45.918 | 0.003 | inconclusive | edd | 1.091 | inconclusive | 0.000 |
| wmdd | 60 | 60 | 4591.817 | 4629.958 | 38.141 | -44.458 | 104.994 | 45.918 | 0.003 | inconclusive | edd | 0.831 | inconclusive | 0.000 |
| lpt | 60 | 60 | 4591.817 | 113533.625 | 108941.808 | 91405.306 | 126471.117 | 45.918 | 0.000 | worse | edd | 2372.521 | worse | 0.000 |
| random | 60 | 60 | 4591.817 | 36141.300 | 31549.483 | 26268.661 | 36780.942 | 45.918 | 0.000 | worse | edd | 687.081 | worse | 0.000 |
| mlp_pool | 60 | 60 | 4591.817 | 5174.852 | 583.035 | 432.655 | 748.902 | 45.918 | 0.000 | worse | edd | 12.697 | worse | 0.000 |
| attn_pool | 60 | 60 | 4591.817 | 6210.494 | 1618.677 | 1350.099 | 1916.765 | 45.918 | 0.000 | worse | edd | 35.251 | worse | 0.000 |
| v1_pool | 60 | 60 | 4591.817 | 7044.440 | 2452.623 | 2018.340 | 2872.378 | 45.918 | 0.000 | worse | edd | 53.413 | worse | 0.000 |
| edd | 60 | 60 | 4591.817 | 4591.817 | 0.000 | 0.000 | 0.000 | 45.918 | 1.000 | reference | edd | 0.000 | equivalent | 1.000 |


## Campus 1 (transfer)


**campus=1|m=1.0** (30 configurations, 30 clusters). Against EDD, of 9 families compared: 7 equivalent (pfifo, atc, wmdd, lpt, mlp_pool, attn_pool, v1_pool); 2 inconclusive (wspt, random). Sample-best family: atc.

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 30 | 30 | 80.417 | 80.417 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | atc | 0.000 | equivalent | 1.000 |
| wspt | 30 | 30 | 80.417 | 81.297 | 0.880 | 0.000 | 2.293 | 1.000 | 1.000 | inconclusive | atc | 1.094 | inconclusive | 0.000 |
| atc | 30 | 30 | 80.417 | 80.417 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | atc | 0.000 | equivalent | 1.000 |
| wmdd | 30 | 30 | 80.417 | 80.417 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | atc | 0.000 | equivalent | 1.000 |
| lpt | 30 | 30 | 80.417 | 80.417 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | atc | 0.000 | equivalent | 1.000 |
| random | 30 | 30 | 80.417 | 81.121 | 0.704 | 0.000 | 1.775 | 1.000 | 1.000 | inconclusive | atc | 0.875 | inconclusive | 0.000 |
| mlp_pool | 30 | 30 | 80.417 | 80.417 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | atc | 0.000 | equivalent | 1.000 |
| attn_pool | 30 | 30 | 80.417 | 80.418 | 0.000 | 0.000 | 0.001 | 1.000 | 1.000 | equivalent | atc | 0.000 | equivalent | 1.000 |
| v1_pool | 30 | 30 | 80.417 | 80.417 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | atc | 0.000 | equivalent | 1.000 |
| rollcp2 | 8 | 8 | 100.045 | 100.056 | 0.011 | 0.003 | 0.021 | 1.000 | 0.250 | equivalent | - | - | - | - |
| edd | 30 | 30 | 80.417 | 80.417 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | reference | atc | 0.000 | equivalent | 1.000 |


## Campus 2 (nonstationary overload)


**campus=2|m=1.0** (17 configurations, 17 clusters). Against EDD, of 9 families compared: 1 equivalent (pfifo); 3 inconclusive (wspt, atc, wmdd); 5 worse (lpt, random, mlp_pool, attn_pool, v1_pool). Sample-best family: wmdd.

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 17 | 17 | 1311.322 | 1311.322 | 0.000 | 0.000 | 0.000 | 13.113 | 1.000 | equivalent | wmdd | 7.642 | inconclusive | 0.000 |
| wspt | 17 | 17 | 1311.322 | 1291.239 | -20.083 | -154.959 | 88.999 | 13.113 | 0.608 | inconclusive | wmdd | 5.993 | worse | 0.000 |
| atc | 17 | 17 | 1311.322 | 1252.116 | -59.206 | -196.258 | 40.425 | 13.113 | 1.000 | inconclusive | wmdd | 2.782 | worse | 0.000 |
| wmdd | 17 | 17 | 1311.322 | 1218.229 | -93.093 | -239.074 | 16.540 | 13.113 | 1.000 | inconclusive | wmdd | 0.000 | equivalent | 1.000 |
| lpt | 17 | 17 | 1311.322 | 2615.112 | 1303.790 | 628.027 | 2114.112 | 13.113 | 0.013 | worse | wmdd | 114.665 | worse | 0.000 |
| random | 17 | 17 | 1311.322 | 1636.031 | 324.708 | 120.318 | 566.172 | 13.113 | 0.035 | worse | wmdd | 34.296 | worse | 0.000 |
| mlp_pool | 17 | 17 | 1311.322 | 1649.863 | 338.541 | 134.840 | 591.305 | 13.113 | 0.023 | worse | wmdd | 35.431 | worse | 0.000 |
| attn_pool | 17 | 17 | 1311.322 | 1435.103 | 123.781 | 32.428 | 234.138 | 13.113 | 0.080 | worse | wmdd | 17.802 | worse | 0.000 |
| v1_pool | 17 | 17 | 1311.322 | 1593.992 | 282.670 | 109.332 | 500.836 | 13.113 | 0.023 | worse | wmdd | 30.845 | worse | 0.000 |
| rollcp2 | 8 | 8 | 1080.425 | 976.783 | -103.642 | -280.492 | 33.903 | 10.804 | 0.562 | inconclusive | - | - | - | - |
| edd | 17 | 17 | 1311.322 | 1311.322 | 0.000 | 0.000 | 0.000 | 13.113 | 1.000 | reference | wmdd | 7.642 | inconclusive | 0.000 |


## Every empirical configuration pooled (heterogeneous: verdict, transfer and stress campuses together)


**ALL** (587 configurations, 227 clusters, no family ranking: heterogeneous scope). Against EDD, of 9 families compared: 2 equivalent (pfifo, atc); 5 inconclusive (wspt, wmdd, mlp_pool, attn_pool, v1_pool); 2 worse (lpt, random).

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 587 | 227 | 453.977 | 453.977 | 0.000 | 0.000 | 0.000 | 4.540 | 1.000 | equivalent |  | - | - | - |
| wspt | 587 | 227 | 453.977 | 458.827 | 4.850 | 0.201 | 9.026 | 4.540 | 0.000 | inconclusive |  | - | - | - |
| atc | 587 | 227 | 453.977 | 454.391 | 0.415 | -3.862 | 3.632 | 4.540 | 0.000 | equivalent |  | - | - | - |
| wmdd | 587 | 227 | 453.977 | 452.735 | -1.241 | -5.954 | 2.104 | 4.540 | 0.000 | inconclusive |  | - | - | - |
| lpt | 587 | 227 | 453.977 | 520.695 | 66.718 | 30.453 | 112.719 | 4.540 | 0.000 | worse |  | - | - | - |
| random | 587 | 227 | 453.977 | 473.535 | 19.559 | 8.676 | 34.386 | 4.540 | 0.000 | worse |  | - | - | - |
| mlp_pool | 587 | 227 | 453.977 | 463.585 | 9.608 | 2.712 | 19.163 | 4.540 | 1.000 | inconclusive |  | - | - | - |
| attn_pool | 587 | 227 | 453.977 | 459.184 | 5.207 | 2.136 | 9.256 | 4.540 | 0.000 | inconclusive |  | - | - | - |
| v1_pool | 587 | 227 | 453.977 | 461.807 | 7.830 | 1.988 | 15.674 | 4.540 | 1.000 | inconclusive |  | - | - | - |
| rollcp2 | 160 | 64 | 515.945 | 510.409 | -5.536 | -16.159 | 1.337 | 5.159 | 0.000 | inconclusive |  | - | - | - |
| edd | 587 | 227 | 453.977 | 453.977 | 0.000 | 0.000 | 0.000 | 4.540 | 1.000 | reference |  | - | - | - |


## Every configuration pooled (heterogeneous: both regimes)


**ALL** (887 configurations, 527 clusters, no family ranking: heterogeneous scope). Against EDD, of 9 families compared: 3 equivalent (pfifo, atc, wmdd); 6 worse (wspt, lpt, random, mlp_pool, attn_pool, v1_pool).

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 887 | 527 | 1428.096 | 1428.030 | -0.066 | -0.213 | 0.008 | 14.281 | 0.686 | equivalent |  | - | - | - |
| wspt | 887 | 527 | 1428.096 | 1678.371 | 250.275 | 202.135 | 304.519 | 14.281 | 0.000 | worse |  | - | - | - |
| atc | 887 | 527 | 1428.096 | 1436.440 | 8.344 | 1.975 | 14.143 | 14.281 | 0.000 | equivalent |  | - | - | - |
| wmdd | 887 | 527 | 1428.096 | 1434.314 | 6.218 | -0.300 | 11.930 | 14.281 | 0.000 | equivalent |  | - | - | - |
| lpt | 887 | 527 | 1428.096 | 14898.354 | 13470.258 | 11052.645 | 16122.366 | 14.281 | 0.000 | worse |  | - | - | - |
| random | 887 | 527 | 1428.096 | 4790.174 | 3362.078 | 2693.335 | 4108.478 | 14.281 | 0.000 | worse |  | - | - | - |
| mlp_pool | 887 | 527 | 1428.096 | 1483.044 | 54.948 | 39.683 | 72.717 | 14.281 | 0.000 | worse |  | - | - | - |
| attn_pool | 887 | 527 | 1428.096 | 1633.641 | 205.545 | 168.648 | 246.504 | 14.281 | 0.000 | worse |  | - | - | - |
| v1_pool | 887 | 527 | 1428.096 | 1667.489 | 239.393 | 188.138 | 297.130 | 14.281 | 0.000 | worse |  | - | - | - |
| rollcp2 | 160 | 64 | 515.945 | 510.409 | -5.536 | -16.159 | 1.337 | 5.159 | 0.000 | inconclusive |  | - | - | - |
| edd | 887 | 527 | 1428.096 | 1428.096 | 0.000 | 0.000 | 0.000 | 14.281 | 1.000 | reference |  | - | - | - |


## Capacity estimator arms and the stress campus

The capacity check scored the seven transparent rules and the ten MLP seeds, so its family vocabulary is the seven rules plus `mlp_pool`; the attention and curriculum-v1 pools were not run there. The p95 arm is the untransformed Eval-B anchor set at crew multiplier 1.0.


Seed coverage on the capacity arms:

| arm | pool | n_seeds | n_configs | n_configs_dropped | status |
|---|---|---|---|---|---|
| q0.95 | mlp_pool | 10 | 227 | 0 | complete |
| q0.95 | attn_pool | 0 | 0 | 0 | absent |
| q0.95 | v1_pool | 0 | 0 | 0 | absent |
| q0.90 | mlp_pool | 10 | 227 | 0 | complete |
| q0.90 | attn_pool | 0 | 0 | 0 | absent |
| q0.90 | v1_pool | 0 | 0 | 0 | absent |
| q0.75 | mlp_pool | 10 | 227 | 0 | complete |
| q0.75 | attn_pool | 0 | 0 | 0 | absent |
| q0.75 | v1_pool | 0 | 0 | 0 | absent |


**capacity / q0.95 / verdict** (p95 of weekly trade hours (Eval-B default); 180 configurations, 180 clusters). Against EDD, of 7 families compared: 7 equivalent (pfifo, wspt, atc, wmdd, lpt, random, mlp_pool).

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 180 | 180 | 444.869 | 444.869 | 0.000 | 0.000 | 0.000 | 4.449 | 1.000 | equivalent | mlp_pool | 0.022 | equivalent | 1.000 |
| wspt | 180 | 180 | 444.869 | 446.646 | 1.777 | 0.813 | 2.982 | 4.449 | 0.000 | equivalent | mlp_pool | 0.422 | equivalent | 1.000 |
| atc | 180 | 180 | 444.869 | 445.555 | 0.686 | 0.176 | 1.324 | 4.449 | 0.086 | equivalent | mlp_pool | 0.177 | equivalent | 1.000 |
| wmdd | 180 | 180 | 444.869 | 445.332 | 0.463 | 0.105 | 0.936 | 4.449 | 0.172 | equivalent | mlp_pool | 0.127 | equivalent | 1.000 |
| lpt | 180 | 180 | 444.869 | 445.579 | 0.710 | -0.074 | 2.118 | 4.449 | 0.547 | equivalent | mlp_pool | 0.182 | equivalent | 1.000 |
| random | 180 | 180 | 444.869 | 446.316 | 1.447 | 0.460 | 2.791 | 4.449 | 0.002 | equivalent | mlp_pool | 0.348 | equivalent | 1.000 |
| mlp_pool | 180 | 180 | 444.869 | 444.769 | -0.100 | -0.256 | 0.021 | 4.449 | 1.000 | equivalent | mlp_pool | 0.000 | equivalent | 1.000 |
| edd | 180 | 180 | 444.869 | 444.869 | 0.000 | 0.000 | 0.000 | 4.449 | 1.000 | reference | mlp_pool | 0.022 | equivalent | 1.000 |


**capacity / q0.95 / campus1** (p95 of weekly trade hours (Eval-B default); 30 configurations, 30 clusters). Against EDD, of 7 families compared: 5 equivalent (pfifo, atc, wmdd, lpt, mlp_pool); 2 inconclusive (wspt, random).

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 30 | 30 | 80.417 | 80.417 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | atc | 0.000 | equivalent | 1.000 |
| wspt | 30 | 30 | 80.417 | 81.297 | 0.880 | 0.000 | 2.293 | 1.000 | 1.000 | inconclusive | atc | 1.094 | inconclusive | 0.000 |
| atc | 30 | 30 | 80.417 | 80.417 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | atc | 0.000 | equivalent | 1.000 |
| wmdd | 30 | 30 | 80.417 | 80.417 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | atc | 0.000 | equivalent | 1.000 |
| lpt | 30 | 30 | 80.417 | 80.417 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | atc | 0.000 | equivalent | 1.000 |
| random | 30 | 30 | 80.417 | 81.121 | 0.704 | 0.000 | 1.775 | 1.000 | 1.000 | inconclusive | atc | 0.875 | inconclusive | 0.000 |
| mlp_pool | 30 | 30 | 80.417 | 80.417 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | atc | 0.000 | equivalent | 1.000 |
| edd | 30 | 30 | 80.417 | 80.417 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | reference | atc | 0.000 | equivalent | 1.000 |


**capacity / q0.95 / campus2** (p95 of weekly trade hours (Eval-B default); 17 configurations, 17 clusters). Against EDD, of 7 families compared: 1 equivalent (pfifo); 3 inconclusive (wspt, atc, wmdd); 3 worse (lpt, random, mlp_pool).

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 17 | 17 | 1311.322 | 1311.322 | 0.000 | 0.000 | 0.000 | 13.113 | 1.000 | equivalent | wmdd | 7.642 | inconclusive | 0.000 |
| wspt | 17 | 17 | 1311.322 | 1291.239 | -20.083 | -154.808 | 90.782 | 13.113 | 0.608 | inconclusive | wmdd | 5.993 | worse | 0.000 |
| atc | 17 | 17 | 1311.322 | 1252.116 | -59.206 | -189.721 | 39.876 | 13.113 | 1.000 | inconclusive | wmdd | 2.782 | worse | 0.000 |
| wmdd | 17 | 17 | 1311.322 | 1218.229 | -93.093 | -236.237 | 15.536 | 13.113 | 1.000 | inconclusive | wmdd | 0.000 | equivalent | 1.000 |
| lpt | 17 | 17 | 1311.322 | 2615.112 | 1303.790 | 627.164 | 2123.705 | 13.113 | 0.010 | worse | wmdd | 114.665 | worse | 0.000 |
| random | 17 | 17 | 1311.322 | 1636.031 | 324.708 | 122.586 | 557.877 | 13.113 | 0.029 | worse | wmdd | 34.296 | worse | 0.000 |
| mlp_pool | 17 | 17 | 1311.322 | 1649.863 | 338.541 | 137.656 | 583.042 | 13.113 | 0.017 | worse | wmdd | 35.431 | worse | 0.000 |
| edd | 17 | 17 | 1311.322 | 1311.322 | 0.000 | 0.000 | 0.000 | 13.113 | 1.000 | reference | wmdd | 7.642 | inconclusive | 0.000 |


**capacity / q0.90 / verdict** (p90 of weekly trade hours; 180 configurations, 180 clusters). Against EDD, of 7 families compared: 6 equivalent (pfifo, wspt, atc, wmdd, random, mlp_pool); 1 inconclusive (lpt).

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 180 | 180 | 446.523 | 446.523 | 0.000 | 0.000 | 0.000 | 4.465 | 1.000 | equivalent | mlp_pool | 0.057 | equivalent | 1.000 |
| wspt | 180 | 180 | 446.523 | 448.909 | 2.386 | 1.270 | 3.714 | 4.465 | 0.000 | equivalent | mlp_pool | 0.591 | equivalent | 1.000 |
| atc | 180 | 180 | 446.523 | 447.404 | 0.881 | 0.201 | 1.787 | 4.465 | 0.038 | equivalent | mlp_pool | 0.254 | equivalent | 1.000 |
| wmdd | 180 | 180 | 446.523 | 446.979 | 0.455 | 0.102 | 0.903 | 4.465 | 0.072 | equivalent | mlp_pool | 0.159 | equivalent | 1.000 |
| lpt | 180 | 180 | 446.523 | 449.608 | 3.085 | 0.117 | 7.444 | 4.465 | 0.214 | inconclusive | mlp_pool | 0.748 | inconclusive | 0.000 |
| random | 180 | 180 | 446.523 | 448.965 | 2.442 | 0.906 | 4.404 | 4.465 | 0.000 | equivalent | mlp_pool | 0.604 | inconclusive | 0.000 |
| mlp_pool | 180 | 180 | 446.523 | 446.270 | -0.254 | -0.532 | -0.042 | 4.465 | 0.450 | equivalent | mlp_pool | 0.000 | equivalent | 1.000 |
| edd | 180 | 180 | 446.523 | 446.523 | 0.000 | 0.000 | 0.000 | 4.465 | 1.000 | reference | mlp_pool | 0.057 | equivalent | 1.000 |


**capacity / q0.90 / campus1** (p90 of weekly trade hours; 30 configurations, 30 clusters). Against EDD, of 7 families compared: 5 equivalent (pfifo, atc, wmdd, lpt, mlp_pool); 2 inconclusive (wspt, random).

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 30 | 30 | 80.417 | 80.417 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | atc | 0.000 | equivalent | 1.000 |
| wspt | 30 | 30 | 80.417 | 81.586 | 1.168 | 0.000 | 2.937 | 1.000 | 1.000 | inconclusive | atc | 1.453 | inconclusive | 0.000 |
| atc | 30 | 30 | 80.417 | 80.417 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | atc | 0.000 | equivalent | 1.000 |
| wmdd | 30 | 30 | 80.417 | 80.417 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | atc | 0.000 | equivalent | 1.000 |
| lpt | 30 | 30 | 80.417 | 80.417 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | atc | 0.000 | equivalent | 1.000 |
| random | 30 | 30 | 80.417 | 80.888 | 0.470 | 0.000 | 1.407 | 1.000 | 1.000 | inconclusive | atc | 0.585 | inconclusive | 0.000 |
| mlp_pool | 30 | 30 | 80.417 | 80.417 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | atc | 0.000 | equivalent | 1.000 |
| edd | 30 | 30 | 80.417 | 80.417 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | reference | atc | 0.000 | equivalent | 1.000 |


**capacity / q0.90 / campus2** (p90 of weekly trade hours; 17 configurations, 17 clusters). Against EDD, of 7 families compared: 1 better (wmdd); 1 equivalent (pfifo); 2 inconclusive (wspt, atc); 3 worse (lpt, random, mlp_pool).

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 17 | 17 | 1770.180 | 1770.180 | 0.000 | 0.000 | 0.000 | 17.702 | 1.000 | equivalent | wmdd | 24.912 | worse | 0.000 |
| wspt | 17 | 17 | 1770.180 | 1519.547 | -250.633 | -627.452 | 28.578 | 17.702 | 1.000 | inconclusive | wmdd | 7.226 | worse | 0.000 |
| atc | 17 | 17 | 1770.180 | 1480.309 | -289.871 | -689.260 | -9.213 | 17.702 | 1.000 | inconclusive | wmdd | 4.457 | worse | 0.000 |
| wmdd | 17 | 17 | 1770.180 | 1417.144 | -353.036 | -740.653 | -59.858 | 17.702 | 1.000 | better | wmdd | 0.000 | equivalent | 1.000 |
| lpt | 17 | 17 | 1770.180 | 4148.896 | 2378.716 | 1136.861 | 3869.216 | 17.702 | 0.007 | worse | wmdd | 192.765 | worse | 0.000 |
| random | 17 | 17 | 1770.180 | 2333.274 | 563.094 | 127.008 | 1125.949 | 17.702 | 0.073 | worse | wmdd | 64.646 | worse | 0.000 |
| mlp_pool | 17 | 17 | 1770.180 | 2470.876 | 700.696 | 306.663 | 1184.899 | 17.702 | 0.009 | worse | wmdd | 74.356 | worse | 0.000 |
| edd | 17 | 17 | 1770.180 | 1770.180 | 0.000 | 0.000 | 0.000 | 17.702 | 1.000 | reference | wmdd | 24.912 | worse | 0.000 |


**capacity / q0.75 / verdict** (p75 of weekly trade hours; 180 configurations, 180 clusters). Against EDD, of 7 families compared: 2 equivalent (pfifo, mlp_pool); 4 inconclusive (wspt, atc, wmdd, random); 1 worse (lpt).

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 180 | 180 | 462.173 | 462.173 | 0.000 | 0.000 | 0.000 | 4.622 | 1.000 | equivalent | atc | 1.008 | inconclusive | 0.000 |
| wspt | 180 | 180 | 462.173 | 462.056 | -0.117 | -9.414 | 6.387 | 4.622 | 0.000 | inconclusive | atc | 0.983 | inconclusive | 0.000 |
| atc | 180 | 180 | 462.173 | 457.559 | -4.614 | -14.213 | 2.271 | 4.622 | 0.423 | inconclusive | atc | 0.000 | equivalent | 1.000 |
| wmdd | 180 | 180 | 462.173 | 458.136 | -4.037 | -13.415 | 2.006 | 4.622 | 0.281 | inconclusive | atc | 0.126 | equivalent | 1.000 |
| lpt | 180 | 180 | 462.173 | 489.481 | 27.308 | 11.044 | 47.590 | 4.622 | 0.000 | worse | atc | 6.977 | worse | 0.000 |
| random | 180 | 180 | 462.173 | 473.205 | 11.032 | 2.303 | 21.289 | 4.622 | 0.000 | inconclusive | atc | 3.419 | worse | 0.000 |
| mlp_pool | 180 | 180 | 462.173 | 461.328 | -0.845 | -2.931 | 0.816 | 4.622 | 1.000 | equivalent | atc | 0.824 | inconclusive | 0.000 |
| edd | 180 | 180 | 462.173 | 462.173 | 0.000 | 0.000 | 0.000 | 4.622 | 1.000 | reference | atc | 1.008 | inconclusive | 0.000 |


**capacity / q0.75 / campus1** (p75 of weekly trade hours; 30 configurations, 30 clusters). Against EDD, of 7 families compared: 4 equivalent (pfifo, atc, wmdd, mlp_pool); 3 inconclusive (wspt, lpt, random).

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 30 | 30 | 80.478 | 80.478 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | atc | 0.000 | equivalent | 1.000 |
| wspt | 30 | 30 | 80.478 | 82.632 | 2.154 | -0.001 | 5.157 | 1.000 | 1.000 | inconclusive | atc | 2.677 | inconclusive | 0.000 |
| atc | 30 | 30 | 80.478 | 80.478 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | atc | 0.000 | equivalent | 1.000 |
| wmdd | 30 | 30 | 80.478 | 80.478 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | atc | 0.000 | equivalent | 1.000 |
| lpt | 30 | 30 | 80.478 | 81.114 | 0.636 | 0.000 | 1.907 | 1.000 | 1.000 | inconclusive | atc | 0.790 | inconclusive | 0.000 |
| random | 30 | 30 | 80.478 | 81.393 | 0.915 | -0.001 | 2.414 | 1.000 | 1.000 | inconclusive | atc | 1.138 | inconclusive | 0.000 |
| mlp_pool | 30 | 30 | 80.478 | 80.527 | 0.049 | 0.000 | 0.136 | 1.000 | 1.000 | equivalent | atc | 0.061 | equivalent | 1.000 |
| edd | 30 | 30 | 80.478 | 80.478 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | reference | atc | 0.000 | equivalent | 1.000 |


**capacity / q0.75 / campus2** (p75 of weekly trade hours; 17 configurations, 17 clusters). Against EDD, of 7 families compared: 3 better (wspt, atc, wmdd); 1 equivalent (pfifo); 3 worse (lpt, random, mlp_pool).

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 17 | 17 | 5629.989 | 5620.576 | -9.413 | -29.907 | 1.669 | 56.300 | 0.655 | equivalent | atc | 98.603 | worse | 0.000 |
| wspt | 17 | 17 | 5629.989 | 2966.211 | -2663.778 | -4241.120 | -1225.488 | 56.300 | 0.022 | better | atc | 4.811 | worse | 0.000 |
| atc | 17 | 17 | 5629.989 | 2830.055 | -2799.934 | -4362.563 | -1345.963 | 56.300 | 0.022 | better | atc | 0.000 | equivalent | 1.000 |
| wmdd | 17 | 17 | 5629.989 | 2954.988 | -2675.001 | -4251.407 | -1226.621 | 56.300 | 0.022 | better | atc | 4.415 | inconclusive | 0.000 |
| lpt | 17 | 17 | 5629.989 | 15682.750 | 10052.761 | 6137.994 | 14260.541 | 56.300 | 0.000 | worse | atc | 454.150 | worse | 0.000 |
| random | 17 | 17 | 5629.989 | 7278.249 | 1648.260 | 835.774 | 2453.347 | 56.300 | 0.003 | worse | atc | 157.177 | worse | 0.000 |
| mlp_pool | 17 | 17 | 5629.989 | 8115.341 | 2485.352 | 1310.183 | 3860.179 | 56.300 | 0.000 | worse | atc | 186.756 | worse | 0.000 |
| edd | 17 | 17 | 5629.989 | 5629.989 | 0.000 | 0.000 | 0.000 | 56.300 | 1.000 | reference | atc | 98.936 | worse | 0.000 |


**evalb / stress / campus2** (Eval-B empirical anchors, crew multiplier 1.0; 17 configurations, 17 clusters). Against EDD, of 9 families compared: 1 equivalent (pfifo); 3 inconclusive (wspt, atc, wmdd); 5 worse (lpt, random, mlp_pool, attn_pool, v1_pool).

| family | n_configs | n_clusters | mean_edd | mean_family | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | best_family | pct_from_best | verdict_vs_best | in_best_set |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pfifo | 17 | 17 | 1311.322 | 1311.322 | 0.000 | 0.000 | 0.000 | 13.113 | 1.000 | equivalent | wmdd | 7.642 | inconclusive | 0.000 |
| wspt | 17 | 17 | 1311.322 | 1291.239 | -20.083 | -154.959 | 88.999 | 13.113 | 0.608 | inconclusive | wmdd | 5.993 | worse | 0.000 |
| atc | 17 | 17 | 1311.322 | 1252.116 | -59.206 | -196.258 | 40.425 | 13.113 | 1.000 | inconclusive | wmdd | 2.782 | worse | 0.000 |
| wmdd | 17 | 17 | 1311.322 | 1218.229 | -93.093 | -239.074 | 16.540 | 13.113 | 1.000 | inconclusive | wmdd | 0.000 | equivalent | 1.000 |
| lpt | 17 | 17 | 1311.322 | 2615.112 | 1303.790 | 628.027 | 2114.112 | 13.113 | 0.013 | worse | wmdd | 114.665 | worse | 0.000 |
| random | 17 | 17 | 1311.322 | 1636.031 | 324.708 | 120.318 | 566.172 | 13.113 | 0.035 | worse | wmdd | 34.296 | worse | 0.000 |
| mlp_pool | 17 | 17 | 1311.322 | 1649.863 | 338.541 | 134.840 | 591.305 | 13.113 | 0.023 | worse | wmdd | 35.431 | worse | 0.000 |
| attn_pool | 17 | 17 | 1311.322 | 1435.103 | 123.781 | 32.428 | 234.138 | 13.113 | 0.080 | worse | wmdd | 17.802 | worse | 0.000 |
| v1_pool | 17 | 17 | 1311.322 | 1593.992 | 282.670 | 109.332 | 500.836 | 13.113 | 0.023 | worse | wmdd | 30.845 | worse | 0.000 |
| rollcp2 | 8 | 8 | 1080.425 | 976.783 | -103.642 | -280.492 | 33.903 | 10.804 | 0.562 | inconclusive | - | - | - | - |
| edd | 17 | 17 | 1311.322 | 1311.322 | 0.000 | 0.000 | 0.000 | 13.113 | 1.000 | reference | wmdd | 7.642 | inconclusive | 0.000 |


## Seed dispersion inside each pool

| scope_type | scope | family | seed_n | mean_family | seed_min_mean | seed_median_mean | seed_max_mean | seed_sd | seed_spread_pct | seed_best | seed_worst |
|---|---|---|---|---|---|---|---|---|---|---|---|
| overall | ALL | mlp_pool | 10.000 | 1483.044 | 1425.733 | 1447.371 | 1662.129 | 86.951 | 16.581 | v2rl310 | v2rl303 |
| overall | ALL | attn_pool | 10.000 | 1633.641 | 1436.464 | 1489.068 | 2634.422 | 370.839 | 83.396 | v2at310 | v2at301 |
| overall | ALL | v1_pool | 3.000 | 1667.489 | 1431.476 | 1673.891 | 1897.101 | 232.878 | 32.528 | rl301 | rl303 |
| emp_m | m=1.0 | mlp_pool | 10.000 | 444.769 | 444.681 | 444.758 | 444.953 | 0.081 | 0.061 | v2rl302 | v2rl309 |
| emp_m | m=1.0 | attn_pool | 10.000 | 445.268 | 444.716 | 445.252 | 445.884 | 0.395 | 0.263 | v2at302 | v2at301 |
| emp_m | m=1.0 | v1_pool | 3.000 | 444.810 | 444.763 | 444.764 | 444.902 | 0.080 | 0.031 | rl301 | rl303 |
| emp_m | m=0.8 | mlp_pool | 10.000 | 446.490 | 446.287 | 446.348 | 447.144 | 0.277 | 0.192 | v2rl301 | v2rl309 |
| emp_m | m=0.8 | attn_pool | 10.000 | 447.688 | 446.268 | 447.769 | 449.828 | 1.013 | 0.798 | v2at302 | v2at301 |
| emp_m | m=0.8 | v1_pool | 3.000 | 446.376 | 446.214 | 446.318 | 446.595 | 0.197 | 0.086 | rl301 | rl303 |
| emp_m | m=0.6 | mlp_pool | 10.000 | 451.318 | 450.246 | 450.771 | 453.910 | 1.319 | 0.814 | v2rl302 | v2rl306 |
| emp_m | m=0.6 | attn_pool | 10.000 | 455.552 | 450.733 | 455.485 | 460.801 | 3.101 | 2.234 | v2at302 | v2at301 |
| emp_m | m=0.6 | v1_pool | 3.000 | 450.872 | 449.767 | 451.188 | 451.660 | 0.985 | 0.421 | rl301 | rl303 |
| emp_ubin | u_bin=<0.5 | mlp_pool | 10.000 | 249.054 | 248.965 | 249.023 | 249.219 | 0.088 | 0.102 | v2rl302 | v2rl306 |
| emp_ubin | u_bin=<0.5 | attn_pool | 10.000 | 249.476 | 248.982 | 249.612 | 249.865 | 0.336 | 0.355 | v2at302 | v2at301 |
| emp_ubin | u_bin=<0.5 | v1_pool | 3.000 | 249.062 | 248.965 | 249.023 | 249.197 | 0.121 | 0.093 | rl302 | rl303 |
| emp_ubin | u_bin=0.5-0.8 | mlp_pool | 10.000 | 686.956 | 686.471 | 686.807 | 688.012 | 0.459 | 0.224 | v2rl303 | v2rl309 |
| emp_ubin | u_bin=0.5-0.8 | attn_pool | 10.000 | 689.615 | 686.646 | 689.683 | 694.240 | 2.080 | 1.106 | v2at302 | v2at301 |
| emp_ubin | u_bin=0.5-0.8 | v1_pool | 3.000 | 687.034 | 686.539 | 687.047 | 687.516 | 0.489 | 0.142 | rl301 | rl303 |
| emp_ubin | u_bin=0.8-1.0 | mlp_pool | 10.000 | 624.171 | 622.246 | 623.573 | 627.257 | 1.706 | 0.805 | v2rl305 | v2rl309 |
| emp_ubin | u_bin=0.8-1.0 | attn_pool | 10.000 | 627.589 | 623.064 | 627.664 | 630.214 | 2.247 | 1.148 | v2at302 | v2at304 |
| emp_ubin | u_bin=0.8-1.0 | v1_pool | 3.000 | 623.306 | 623.216 | 623.260 | 623.442 | 0.120 | 0.036 | rl302 | rl301 |
| emp_ubin | u_bin=1.0-1.2 | mlp_pool | 10.000 | 611.071 | 605.007 | 610.332 | 619.496 | 4.310 | 2.395 | v2rl304 | v2rl306 |
| emp_ubin | u_bin=1.0-1.2 | attn_pool | 10.000 | 615.667 | 609.052 | 614.037 | 628.803 | 5.956 | 3.243 | v2at310 | v2at305 |
| emp_ubin | u_bin=1.0-1.2 | v1_pool | 3.000 | 610.082 | 607.113 | 610.582 | 612.551 | 2.753 | 0.896 | rl301 | rl303 |
| emp_ubin | u_bin=>=1.2 | mlp_pool | 10.000 | 279.069 | 278.522 | 278.879 | 279.796 | 0.425 | 0.457 | v2rl307 | v2rl309 |
| emp_ubin | u_bin=>=1.2 | attn_pool | 10.000 | 280.925 | 278.746 | 280.698 | 284.597 | 1.693 | 2.099 | v2at302 | v2at301 |
| emp_ubin | u_bin=>=1.2 | v1_pool | 3.000 | 278.930 | 278.434 | 279.042 | 279.313 | 0.450 | 0.316 | rl301 | rl302 |
| emp_m_ubin | m=1.0|u_bin=<0.5 | mlp_pool | 10.000 | 307.393 | 307.327 | 307.407 | 307.473 | 0.048 | 0.048 | v2rl310 | v2rl309 |
| emp_m_ubin | m=1.0|u_bin=<0.5 | attn_pool | 10.000 | 307.730 | 307.327 | 307.732 | 308.316 | 0.281 | 0.322 | v2at302 | v2at301 |
| emp_m_ubin | m=1.0|u_bin=<0.5 | v1_pool | 3.000 | 307.446 | 307.332 | 307.356 | 307.650 | 0.177 | 0.103 | rl302 | rl303 |
| emp_m_ubin | m=1.0|u_bin=0.5-0.8 | mlp_pool | 10.000 | 859.684 | 859.602 | 859.680 | 859.790 | 0.063 | 0.022 | v2rl302 | v2rl305 |
| emp_m_ubin | m=1.0|u_bin=0.5-0.8 | attn_pool | 10.000 | 860.420 | 859.604 | 860.634 | 861.128 | 0.562 | 0.177 | v2at310 | v2at301 |
| emp_m_ubin | m=1.0|u_bin=0.5-0.8 | v1_pool | 3.000 | 859.671 | 859.602 | 859.636 | 859.776 | 0.092 | 0.020 | rl303 | rl301 |
| emp_m_ubin | m=1.0|u_bin=0.8-1.0 | mlp_pool | 10.000 | 279.204 | 278.728 | 278.928 | 280.701 | 0.747 | 0.708 | v2rl301 | v2rl309 |
| emp_m_ubin | m=1.0|u_bin=0.8-1.0 | attn_pool | 10.000 | 280.715 | 278.728 | 280.106 | 284.393 | 2.125 | 2.032 | v2at302 | v2at304 |
| emp_m_ubin | m=1.0|u_bin=0.8-1.0 | v1_pool | 3.000 | 279.473 | 278.928 | 279.746 | 279.746 | 0.472 | 0.293 | rl301 | rl303 |
| emp_m_ubin | m=1.0|u_bin=1.0-1.2 | mlp_pool | 10.000 | 5.667 | 5.667 | 5.667 | 5.667 | 0.000 | 0.000 | v2rl301 | v2rl310 |
| emp_m_ubin | m=1.0|u_bin=1.0-1.2 | attn_pool | 10.000 | 5.667 | 5.667 | 5.667 | 5.667 | 0.000 | 0.000 | v2at301 | v2at310 |
| emp_m_ubin | m=1.0|u_bin=1.0-1.2 | v1_pool | 3.000 | 5.667 | 5.667 | 5.667 | 5.667 | 0.000 | 0.000 | rl301 | rl303 |
| emp_m_ubin | m=1.0|u_bin=>=1.2 | mlp_pool | 10.000 | 231.785 | 231.756 | 231.774 | 231.912 | 0.046 | 0.067 | v2rl304 | v2rl309 |
| emp_m_ubin | m=1.0|u_bin=>=1.2 | attn_pool | 10.000 | 231.921 | 231.756 | 231.756 | 233.062 | 0.411 | 0.564 | v2at303 | v2at301 |
| emp_m_ubin | m=1.0|u_bin=>=1.2 | v1_pool | 3.000 | 231.784 | 231.758 | 231.774 | 231.819 | 0.032 | 0.026 | rl303 | rl301 |
| emp_m_ubin | m=0.8|u_bin=<0.5 | mlp_pool | 10.000 | 223.980 | 223.940 | 223.978 | 224.038 | 0.027 | 0.044 | v2rl302 | v2rl309 |
| emp_m_ubin | m=0.8|u_bin=<0.5 | attn_pool | 10.000 | 224.356 | 223.940 | 224.439 | 224.725 | 0.289 | 0.350 | v2at305 | v2at303 |
| emp_m_ubin | m=0.8|u_bin=<0.5 | v1_pool | 3.000 | 223.968 | 223.940 | 223.964 | 224.001 | 0.031 | 0.027 | rl302 | rl303 |
| emp_m_ubin | m=0.8|u_bin=0.5-0.8 | mlp_pool | 10.000 | 757.351 | 756.920 | 757.110 | 758.903 | 0.639 | 0.262 | v2rl305 | v2rl309 |
| emp_m_ubin | m=0.8|u_bin=0.5-0.8 | attn_pool | 10.000 | 760.045 | 756.920 | 760.100 | 765.905 | 2.520 | 1.187 | v2at302 | v2at301 |
| emp_m_ubin | m=0.8|u_bin=0.5-0.8 | v1_pool | 3.000 | 756.962 | 756.785 | 756.913 | 757.188 | 0.206 | 0.053 | rl301 | rl303 |
| emp_m_ubin | m=0.8|u_bin=0.8-1.0 | mlp_pool | 10.000 | 746.677 | 746.614 | 746.614 | 747.197 | 0.183 | 0.078 | v2rl301 | v2rl309 |
| emp_m_ubin | m=0.8|u_bin=0.8-1.0 | attn_pool | 10.000 | 747.789 | 746.531 | 747.671 | 749.470 | 0.990 | 0.394 | v2at305 | v2at307 |
| emp_m_ubin | m=0.8|u_bin=0.8-1.0 | v1_pool | 3.000 | 746.614 | 746.614 | 746.614 | 746.614 | 0.000 | 0.000 | rl301 | rl303 |
| emp_m_ubin | m=0.8|u_bin=1.0-1.2 | mlp_pool | 10.000 | 281.270 | 279.988 | 280.496 | 286.564 | 2.025 | 2.349 | v2rl301 | v2rl306 |
| emp_m_ubin | m=0.8|u_bin=1.0-1.2 | attn_pool | 10.000 | 282.848 | 279.988 | 282.817 | 285.837 | 2.302 | 2.089 | v2at302 | v2at306 |
| emp_m_ubin | m=0.8|u_bin=1.0-1.2 | v1_pool | 3.000 | 281.474 | 279.988 | 281.006 | 283.428 | 1.767 | 1.229 | rl301 | rl303 |
| emp_m_ubin | m=0.8|u_bin=>=1.2 | mlp_pool | 10.000 | 191.546 | 191.521 | 191.521 | 191.665 | 0.049 | 0.075 | v2rl301 | v2rl309 |
| emp_m_ubin | m=0.8|u_bin=>=1.2 | attn_pool | 10.000 | 191.728 | 191.521 | 191.535 | 193.185 | 0.521 | 0.869 | v2at305 | v2at301 |
| emp_m_ubin | m=0.8|u_bin=>=1.2 | v1_pool | 3.000 | 191.522 | 191.510 | 191.521 | 191.535 | 0.012 | 0.013 | rl301 | rl303 |
| emp_m_ubin | m=0.6|u_bin=<0.5 | mlp_pool | 10.000 | 148.189 | 147.944 | 147.944 | 149.003 | 0.371 | 0.716 | v2rl301 | v2rl306 |
| emp_m_ubin | m=0.6|u_bin=<0.5 | attn_pool | 10.000 | 148.911 | 147.944 | 149.057 | 149.917 | 0.720 | 1.333 | v2at302 | v2at308 |
| emp_m_ubin | m=0.6|u_bin=<0.5 | v1_pool | 3.000 | 148.121 | 147.944 | 148.148 | 148.270 | 0.164 | 0.220 | rl302 | rl303 |
| emp_m_ubin | m=0.6|u_bin=0.5-0.8 | mlp_pool | 10.000 | 423.572 | 422.380 | 423.349 | 425.157 | 0.786 | 0.657 | v2rl303 | v2rl309 |
| emp_m_ubin | m=0.6|u_bin=0.5-0.8 | attn_pool | 10.000 | 428.276 | 423.015 | 428.240 | 435.806 | 3.496 | 3.024 | v2at302 | v2at301 |
| emp_m_ubin | m=0.6|u_bin=0.5-0.8 | v1_pool | 3.000 | 424.256 | 422.767 | 424.387 | 425.613 | 1.427 | 0.673 | rl301 | rl303 |
| emp_m_ubin | m=0.6|u_bin=0.8-1.0 | mlp_pool | 10.000 | 681.374 | 677.095 | 680.125 | 687.504 | 3.622 | 1.537 | v2rl305 | v2rl309 |
| emp_m_ubin | m=0.6|u_bin=0.8-1.0 | attn_pool | 10.000 | 687.758 | 679.033 | 688.298 | 692.486 | 4.117 | 1.981 | v2at302 | v2at304 |
| emp_m_ubin | m=0.6|u_bin=0.8-1.0 | v1_pool | 3.000 | 679.248 | 678.903 | 679.008 | 679.832 | 0.509 | 0.137 | rl302 | rl301 |
| emp_m_ubin | m=0.6|u_bin=1.0-1.2 | mlp_pool | 10.000 | 1051.061 | 1039.157 | 1050.183 | 1064.557 | 7.970 | 2.444 | v2rl304 | v2rl306 |
| emp_m_ubin | m=0.6|u_bin=1.0-1.2 | attn_pool | 10.000 | 1059.370 | 1047.837 | 1055.450 | 1084.981 | 11.498 | 3.545 | v2at310 | v2at305 |
| emp_m_ubin | m=0.6|u_bin=1.0-1.2 | v1_pool | 3.000 | 1048.881 | 1043.851 | 1050.248 | 1052.545 | 4.505 | 0.833 | rl301 | rl303 |
| emp_m_ubin | m=0.6|u_bin=>=1.2 | mlp_pool | 10.000 | 350.022 | 348.938 | 349.631 | 351.365 | 0.833 | 0.696 | v2rl307 | v2rl309 |
| emp_m_ubin | m=0.6|u_bin=>=1.2 | attn_pool | 10.000 | 353.605 | 349.374 | 353.330 | 359.675 | 3.077 | 2.949 | v2at302 | v2at301 |
| emp_m_ubin | m=0.6|u_bin=>=1.2 | v1_pool | 3.000 | 349.755 | 348.744 | 349.987 | 350.534 | 0.917 | 0.513 | rl301 | rl302 |
| gen_all | ALL | mlp_pool | 10.000 | 3477.785 | 3327.425 | 3376.449 | 3978.418 | 250.205 | 19.564 | v2rl310 | v2rl303 |
| gen_all | ALL | attn_pool | 10.000 | 3931.662 | 3342.649 | 3504.944 | 6897.663 | 1097.061 | 106.353 | v2at310 | v2at301 |
| gen_all | ALL | v1_pool | 3.000 | 4026.608 | 3330.767 | 4058.342 | 4690.713 | 680.528 | 40.830 | rl301 | rl303 |
| gen_utarget | u_target=0.7 | mlp_pool | 10.000 | 2258.039 | 2257.543 | 2257.822 | 2259.702 | 0.657 | 0.096 | v2rl307 | v2rl303 |
| gen_utarget | u_target=0.7 | attn_pool | 10.000 | 2268.172 | 2257.573 | 2260.537 | 2334.254 | 23.371 | 3.397 | v2at302 | v2at301 |
| gen_utarget | u_target=0.7 | v1_pool | 3.000 | 2260.318 | 2257.500 | 2259.881 | 2263.573 | 3.060 | 0.269 | rl301 | rl302 |
| gen_utarget | u_target=0.9 | mlp_pool | 10.000 | 3006.350 | 2990.815 | 2993.815 | 3065.295 | 27.425 | 2.490 | v2rl301 | v2rl303 |
| gen_utarget | u_target=0.9 | attn_pool | 10.000 | 3218.868 | 2990.305 | 3043.213 | 4626.060 | 499.212 | 54.702 | v2at302 | v2at301 |
| gen_utarget | u_target=0.9 | v1_pool | 3.000 | 3072.348 | 2991.641 | 3071.202 | 3154.201 | 81.286 | 5.434 | rl301 | rl302 |
| gen_utarget | u_target=1.0 | mlp_pool | 10.000 | 3143.023 | 3108.184 | 3115.510 | 3276.383 | 62.008 | 5.411 | v2rl310 | v2rl303 |
| gen_utarget | u_target=1.0 | attn_pool | 10.000 | 3529.898 | 3107.801 | 3225.757 | 6040.129 | 895.431 | 94.354 | v2at302 | v2at301 |
| gen_utarget | u_target=1.0 | v1_pool | 3.000 | 3345.697 | 3104.700 | 3464.596 | 3467.795 | 208.716 | 11.695 | rl301 | rl302 |
| gen_utarget | u_target=1.1 | mlp_pool | 10.000 | 3806.663 | 3691.867 | 3724.189 | 4196.135 | 195.653 | 13.659 | v2rl305 | v2rl309 |
| gen_utarget | u_target=1.1 | attn_pool | 10.000 | 4430.877 | 3692.268 | 3861.848 | 8464.522 | 1466.881 | 129.250 | v2at302 | v2at301 |
| gen_utarget | u_target=1.1 | v1_pool | 3.000 | 4410.234 | 3688.496 | 4478.806 | 5063.400 | 690.012 | 37.275 | rl301 | rl303 |
| gen_utarget | u_target=1.3 | mlp_pool | 10.000 | 5174.852 | 4569.811 | 4792.058 | 7135.676 | 967.635 | 56.148 | v2rl304 | v2rl303 |
| gen_utarget | u_target=1.3 | attn_pool | 10.000 | 6210.494 | 4604.906 | 5093.602 | 13023.348 | 2641.990 | 182.815 | v2at310 | v2at301 |
| gen_utarget | u_target=1.3 | v1_pool | 3.000 | 7044.440 | 4611.499 | 6927.335 | 9594.486 | 2493.557 | 108.056 | rl301 | rl303 |
| transfer | campus=1|m=1.0 | mlp_pool | 10.000 | 80.417 | 80.417 | 80.417 | 80.417 | 0.000 | 0.000 | v2rl301 | v2rl310 |
| transfer | campus=1|m=1.0 | attn_pool | 10.000 | 80.418 | 80.417 | 80.417 | 80.420 | 0.001 | 0.004 | v2at301 | v2at303 |
| transfer | campus=1|m=1.0 | v1_pool | 3.000 | 80.417 | 80.417 | 80.417 | 80.417 | 0.000 | 0.000 | rl301 | rl303 |
| stress | campus=2|m=1.0 | mlp_pool | 10.000 | 1649.863 | 1324.889 | 1607.429 | 2171.693 | 265.806 | 63.915 | v2rl310 | v2rl303 |
| stress | campus=2|m=1.0 | attn_pool | 10.000 | 1435.103 | 1220.106 | 1367.112 | 1823.957 | 195.344 | 49.492 | v2at309 | v2at305 |
| stress | campus=2|m=1.0 | v1_pool | 3.000 | 1593.992 | 1365.712 | 1573.115 | 1843.148 | 239.402 | 34.959 | rl302 | rl303 |
| emp_pooled | ALL | mlp_pool | 10.000 | 463.585 | 453.829 | 462.142 | 478.336 | 7.740 | 5.400 | v2rl310 | v2rl303 |
| emp_pooled | ALL | attn_pool | 10.000 | 459.184 | 452.454 | 457.309 | 470.866 | 5.219 | 4.069 | v2at309 | v2at305 |
| emp_pooled | ALL | v1_pool | 3.000 | 461.807 | 455.261 | 460.800 | 469.360 | 7.103 | 3.097 | rl302 | rl303 |
