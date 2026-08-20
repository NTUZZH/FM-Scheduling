# R4.6 preventive-visibility definitive analysis

Input: `results/r4_visibility/results.csv`. Statistics: `fmwos.stats`, protocol §R4.5, 10000 bootstrap resamples over base-instance clusters, master seed 12345, equivalence margin max(1.0, 1% of the comparator mean), Holm within the three levels of one arm inside one scope. A NEGATIVE effect means the level is better than the same arm at L = 0.


What is paired with what. Every configuration is scored at all four levels, so the control is the SAME arm on the SAME configuration at L = 0. The pairing key is the configuration id without its `_L<tag>` suffix; the cluster key is `base_id`, the base instance. For the visibility policies the arm at level X is the checkpoint trained at level X, and it pairs against the checkpoint trained at level 0 with the identical widened architecture and the same seed number, seed by seed; the pool row is the five-seed mean per configuration on each side. The policy contrast therefore carries the retraining as well as the information, while the forecast-aware ATC and the rolling planner are single artifacts run at four levels and carry the information alone.


The three non-delay rules (edd, atc, wmdd) are constant in L by construction and were scored once and copied; the copies are excluded from every paired effect and are used only to check that the spread across levels is exactly zero.


## 0. Run size and coverage

| scope | n_rows | n_ids | n_configs | n_clusters | n_levels | n_methods | n_infeasible | n_constant_rows |
|---|---|---|---|---|---|---|---|---|
| all | 50256 | 4320 | 1080 | 720 | 4 | 35 | 0 | 12960 |
| vis-gen | 24840 | 2160 | 540 | 540 | 4 | 34 | 0 | 6480 |
| vis-empirical | 25416 | 2160 | 540 | 180 | 4 | 35 | 0 | 6480 |


Every (method, level) cell against the coverage the design requires:

| method | level | n_rows | n_configs | expected_configs | n_gen | n_emp | constant_by_construction | mean_wwt |
|---|---|---|---|---|---|---|---|---|
| atc | 0 | 1080 | 1080 | 1080 | 540 | 540 | 1 | 1506.2 |
| atc | 8 | 1080 | 1080 | 1080 | 540 | 540 | 1 | 1506.2 |
| atc | 40 | 1080 | 1080 | 1080 | 540 | 540 | 1 | 1506.2 |
| atc | full | 1080 | 1080 | 1080 | 540 | 540 | 1 | 1506.2 |
| atc_la | 0 | 1080 | 1080 | 1080 | 540 | 540 | 0 | 1506.2 |
| atc_la | 8 | 1080 | 1080 | 1080 | 540 | 540 | 0 | 1504.9 |
| atc_la | 40 | 1080 | 1080 | 1080 | 540 | 540 | 0 | 1503.3 |
| atc_la | full | 1080 | 1080 | 1080 | 540 | 540 | 0 | 1503.3 |
| edd | 0 | 1080 | 1080 | 1080 | 540 | 540 | 1 | 1491.5 |
| edd | 8 | 1080 | 1080 | 1080 | 540 | 540 | 1 | 1491.5 |
| edd | 40 | 1080 | 1080 | 1080 | 540 | 540 | 1 | 1491.5 |
| edd | full | 1080 | 1080 | 1080 | 540 | 540 | 1 | 1491.5 |
| rollcp2 | 0 | 144 | 144 | 144 | 0 | 144 | 0 | 507.5 |
| rollcp2 | 8 | 144 | 144 | 144 | 0 | 144 | 0 | 507.7 |
| rollcp2 | 40 | 144 | 144 | 144 | 0 | 144 | 0 | 509.3 |
| rollcp2 | full | 144 | 144 | 144 | 0 | 144 | 0 | 510.5 |
| v2rl301 | 0 | 1080 | 1080 | 1080 | 540 | 540 | 0 | 1499.9 |
| v2rl302 | 0 | 1080 | 1080 | 1080 | 540 | 540 | 0 | 1719.8 |
| v2rl303 | 0 | 1080 | 1080 | 1080 | 540 | 540 | 0 | 1759.7 |
| v2rl304 | 0 | 1080 | 1080 | 1080 | 540 | 540 | 0 | 1490.8 |
| v2rl305 | 0 | 1080 | 1080 | 1080 | 540 | 540 | 0 | 1494.6 |
| v2rl306 | 0 | 1080 | 1080 | 1080 | 540 | 540 | 0 | 1509.1 |
| v2rl307 | 0 | 1080 | 1080 | 1080 | 540 | 540 | 0 | 1524.7 |
| v2rl308 | 0 | 1080 | 1080 | 1080 | 540 | 540 | 0 | 1499.0 |
| v2rl309 | 0 | 1080 | 1080 | 1080 | 540 | 540 | 0 | 1615.7 |
| v2rl310 | 0 | 1080 | 1080 | 1080 | 540 | 540 | 0 | 1488.0 |
| vis0rl501 | 0 | 1080 | 1080 | 1080 | 540 | 540 | 0 | 1521.2 |
| vis0rl502 | 0 | 1080 | 1080 | 1080 | 540 | 540 | 0 | 1498.8 |
| vis0rl503 | 0 | 1080 | 1080 | 1080 | 540 | 540 | 0 | 1815.5 |
| vis0rl504 | 0 | 1080 | 1080 | 1080 | 540 | 540 | 0 | 2141.0 |
| vis0rl505 | 0 | 1080 | 1080 | 1080 | 540 | 540 | 0 | 2674.0 |
| vis40rl501 | 40 | 1080 | 1080 | 1080 | 540 | 540 | 0 | 1495.5 |
| vis40rl502 | 40 | 1080 | 1080 | 1080 | 540 | 540 | 0 | 1490.3 |
| vis40rl503 | 40 | 1080 | 1080 | 1080 | 540 | 540 | 0 | 1491.5 |
| vis40rl504 | 40 | 1080 | 1080 | 1080 | 540 | 540 | 0 | 2132.5 |
| vis40rl505 | 40 | 1080 | 1080 | 1080 | 540 | 540 | 0 | 2879.0 |
| vis8rl501 | 8 | 1080 | 1080 | 1080 | 540 | 540 | 0 | 1781.1 |
| vis8rl502 | 8 | 1080 | 1080 | 1080 | 540 | 540 | 0 | 1491.1 |
| vis8rl503 | 8 | 1080 | 1080 | 1080 | 540 | 540 | 0 | 1491.1 |
| vis8rl504 | 8 | 1080 | 1080 | 1080 | 540 | 540 | 0 | 2120.9 |
| vis8rl505 | 8 | 1080 | 1080 | 1080 | 540 | 540 | 0 | 2877.1 |
| visfullrl501 | full | 1080 | 1080 | 1080 | 540 | 540 | 0 | 1501.2 |
| visfullrl502 | full | 1080 | 1080 | 1080 | 540 | 540 | 0 | 1493.5 |
| visfullrl503 | full | 1080 | 1080 | 1080 | 540 | 540 | 0 | 1494.5 |
| visfullrl504 | full | 1080 | 1080 | 1080 | 540 | 540 | 0 | 2132.5 |
| visfullrl505 | full | 1080 | 1080 | 1080 | 540 | 540 | 0 | 2879.0 |
| wmdd | 0 | 1080 | 1080 | 1080 | 540 | 540 | 1 | 1510.2 |
| wmdd | 8 | 1080 | 1080 | 1080 | 540 | 540 | 1 | 1510.2 |
| wmdd | 40 | 1080 | 1080 | 1080 | 540 | 540 | 1 | 1510.2 |
| wmdd | full | 1080 | 1080 | 1080 | 540 | 540 | 1 | 1510.2 |


## 1. The paired visibility effect, per scope, arm and level

`pct_of_control` is the mean paired difference as a percentage of the arm's own mean at L = 0 on the same configurations.


### generator cells (pm share x target utilization)

| scope | arm | level | n_configs | n_clusters | mean_control | mean_diff | pct_of_control | pct_ci_lo | pct_ci_hi | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| gen|ALL | atc_la | 8 | 540 | 540 | 2562.3 | -2.57 | -0.100 | -0.194 | -0.024 | equivalent |
| gen|ALL | atc_la | 40 | 540 | 540 | 2562.3 | -5.68 | -0.222 | -0.413 | -0.066 | equivalent |
| gen|ALL | atc_la | full | 540 | 540 | 2562.3 | -5.68 | -0.222 | -0.408 | -0.067 | equivalent |
| gen|ALL | vispool | 8 | 540 | 540 | 3411.4 | 44.17 | 1.295 | 0.792 | 1.786 | inconclusive |
| gen|ALL | vispool | 40 | 540 | 540 | 3411.4 | -64.56 | -1.892 | -3.778 | -0.236 | inconclusive |
| gen|ALL | vispool | full | 540 | 540 | 3411.4 | -60.05 | -1.760 | -3.565 | -0.132 | inconclusive |
| gen|ALL | visseed501 | 8 | 540 | 540 | 2595.3 | 518.36 | 19.973 | 10.847 | 30.624 | worse |
| gen|ALL | visseed501 | 40 | 540 | 540 | 2595.3 | -51.26 | -1.975 | -2.980 | -1.092 | better |
| gen|ALL | visseed501 | full | 540 | 540 | 2595.3 | -40.05 | -1.543 | -2.414 | -0.794 | inconclusive |
| gen|ALL | visseed502 | 8 | 540 | 540 | 2549.6 | -14.31 | -0.561 | -0.932 | -0.247 | equivalent |
| gen|ALL | visseed502 | 40 | 540 | 540 | 2549.6 | -16.20 | -0.636 | -0.977 | -0.352 | equivalent |
| gen|ALL | visseed502 | full | 540 | 540 | 2549.6 | -10.63 | -0.417 | -0.690 | -0.185 | equivalent |
| gen|ALL | visseed503 | 8 | 540 | 540 | 3183.6 | -648.64 | -20.374 | -30.634 | -11.679 | better |
| gen|ALL | visseed503 | 40 | 540 | 540 | 3183.6 | -647.80 | -20.348 | -30.311 | -11.659 | better |
| gen|ALL | visseed503 | full | 540 | 540 | 3183.6 | -642.06 | -20.168 | -29.857 | -11.578 | better |
| gen|ALL | visseed504 | 8 | 540 | 540 | 3831.4 | -40.59 | -1.059 | -2.404 | 0.140 | inconclusive |
| gen|ALL | visseed504 | 40 | 540 | 540 | 3831.4 | -17.27 | -0.451 | -1.958 | 0.902 | inconclusive |
| gen|ALL | visseed504 | full | 540 | 540 | 3831.4 | -17.27 | -0.451 | -1.959 | 0.952 | inconclusive |
| gen|ALL | visseed505 | 8 | 540 | 540 | 4897.2 | 406.01 | 8.291 | 7.000 | 9.607 | worse |
| gen|ALL | visseed505 | 40 | 540 | 540 | 4897.2 | 409.74 | 8.367 | 7.084 | 9.700 | worse |
| gen|ALL | visseed505 | full | 540 | 540 | 4897.2 | 409.74 | 8.367 | 7.059 | 9.679 | worse |
| gen|u=0.7 | atc_la | 8 | 180 | 180 | 1996.4 | -0.09 | -0.005 | -0.010 | 0.001 | equivalent |
| gen|u=0.7 | atc_la | 40 | 180 | 180 | 1996.4 | -0.04 | -0.002 | -0.016 | 0.017 | equivalent |
| gen|u=0.7 | atc_la | full | 180 | 180 | 1996.4 | -0.04 | -0.002 | -0.016 | 0.017 | equivalent |
| gen|u=0.7 | vispool | 8 | 180 | 180 | 2007.0 | 0.81 | 0.041 | -0.048 | 0.124 | equivalent |
| gen|u=0.7 | vispool | 40 | 180 | 180 | 2007.0 | 0.23 | 0.011 | -0.076 | 0.090 | equivalent |
| gen|u=0.7 | vispool | full | 180 | 180 | 2007.0 | 0.40 | 0.020 | -0.070 | 0.099 | equivalent |
| gen|u=0.7 | visseed501 | 8 | 180 | 180 | 1995.2 | 2.48 | 0.124 | 0.041 | 0.237 | equivalent |
| gen|u=0.7 | visseed501 | 40 | 180 | 180 | 1995.2 | 0.97 | 0.048 | 0.001 | 0.107 | equivalent |
| gen|u=0.7 | visseed501 | full | 180 | 180 | 1995.2 | 1.11 | 0.056 | 0.002 | 0.133 | equivalent |
| gen|u=0.7 | visseed502 | 8 | 180 | 180 | 1996.8 | -0.54 | -0.027 | -0.074 | 0.017 | equivalent |
| gen|u=0.7 | visseed502 | 40 | 180 | 180 | 1996.8 | -1.91 | -0.096 | -0.151 | -0.046 | equivalent |
| gen|u=0.7 | visseed502 | full | 180 | 180 | 1996.8 | -1.39 | -0.070 | -0.115 | -0.028 | equivalent |
| gen|u=0.7 | visseed503 | 8 | 180 | 180 | 1995.8 | -0.88 | -0.044 | -0.126 | 0.007 | equivalent |
| gen|u=0.7 | visseed503 | 40 | 180 | 180 | 1995.8 | -1.17 | -0.058 | -0.149 | 0.004 | equivalent |
| gen|u=0.7 | visseed503 | full | 180 | 180 | 1995.8 | -0.95 | -0.048 | -0.135 | 0.009 | equivalent |
| gen|u=0.7 | visseed504 | 8 | 180 | 180 | 2003.9 | -0.84 | -0.042 | -0.311 | 0.203 | equivalent |
| gen|u=0.7 | visseed504 | 40 | 180 | 180 | 2003.9 | -0.04 | -0.002 | -0.273 | 0.253 | equivalent |
| gen|u=0.7 | visseed504 | full | 180 | 180 | 2003.9 | -0.04 | -0.002 | -0.277 | 0.252 | equivalent |
| gen|u=0.7 | visseed505 | 8 | 180 | 180 | 2043.3 | 3.85 | 0.189 | -0.051 | 0.459 | equivalent |
| gen|u=0.7 | visseed505 | 40 | 180 | 180 | 2043.3 | 3.28 | 0.160 | -0.049 | 0.412 | equivalent |
| gen|u=0.7 | visseed505 | full | 180 | 180 | 2043.3 | 3.28 | 0.160 | -0.052 | 0.410 | equivalent |
| gen|u=0.9 | atc_la | 8 | 180 | 180 | 2471.2 | -0.85 | -0.034 | -0.085 | 0.008 | equivalent |
| gen|u=0.9 | atc_la | 40 | 180 | 180 | 2471.2 | -1.49 | -0.060 | -0.146 | 0.015 | equivalent |
| gen|u=0.9 | atc_la | full | 180 | 180 | 2471.2 | -1.49 | -0.060 | -0.147 | 0.015 | equivalent |
| gen|u=0.9 | vispool | 8 | 180 | 180 | 2878.7 | 23.51 | 0.817 | -0.114 | 1.620 | inconclusive |
| gen|u=0.9 | vispool | 40 | 180 | 180 | 2878.7 | 14.16 | 0.492 | -0.573 | 1.365 | inconclusive |
| gen|u=0.9 | vispool | full | 180 | 180 | 2878.7 | 15.81 | 0.549 | -0.503 | 1.413 | inconclusive |
| gen|u=0.9 | visseed501 | 8 | 180 | 180 | 2468.4 | 82.64 | 3.348 | 0.766 | 7.385 | inconclusive |
| gen|u=0.9 | visseed501 | 40 | 180 | 180 | 2468.4 | -5.60 | -0.227 | -0.588 | 0.068 | equivalent |
| gen|u=0.9 | visseed501 | full | 180 | 180 | 2468.4 | -0.96 | -0.039 | -0.361 | 0.235 | equivalent |
| gen|u=0.9 | visseed502 | 8 | 180 | 180 | 2468.1 | -8.17 | -0.331 | -0.550 | -0.142 | equivalent |
| gen|u=0.9 | visseed502 | 40 | 180 | 180 | 2468.1 | -8.18 | -0.331 | -0.581 | -0.136 | equivalent |
| gen|u=0.9 | visseed502 | full | 180 | 180 | 2468.1 | -7.93 | -0.321 | -0.499 | -0.182 | equivalent |
| gen|u=0.9 | visseed503 | 8 | 180 | 180 | 2591.4 | -132.50 | -5.113 | -9.914 | -1.480 | better |
| gen|u=0.9 | visseed503 | 40 | 180 | 180 | 2591.4 | -132.08 | -5.097 | -9.793 | -1.443 | better |
| gen|u=0.9 | visseed503 | full | 180 | 180 | 2591.4 | -128.75 | -4.968 | -9.729 | -1.275 | better |
| gen|u=0.9 | visseed504 | 8 | 180 | 180 | 2952.3 | -54.39 | -1.842 | -3.559 | -0.384 | inconclusive |
| gen|u=0.9 | visseed504 | 40 | 180 | 180 | 2952.3 | -35.06 | -1.187 | -2.945 | 0.366 | inconclusive |
| gen|u=0.9 | visseed504 | full | 180 | 180 | 2952.3 | -35.06 | -1.187 | -2.932 | 0.368 | inconclusive |
| gen|u=0.9 | visseed505 | 8 | 180 | 180 | 3913.4 | 229.98 | 5.877 | 4.235 | 7.607 | worse |
| gen|u=0.9 | visseed505 | 40 | 180 | 180 | 3913.4 | 251.72 | 6.432 | 4.734 | 8.225 | worse |
| gen|u=0.9 | visseed505 | full | 180 | 180 | 3913.4 | 251.72 | 6.432 | 4.725 | 8.226 | worse |
| gen|u=1.1 | atc_la | 8 | 180 | 180 | 3219.5 | -6.77 | -0.210 | -0.427 | -0.034 | equivalent |
| gen|u=1.1 | atc_la | 40 | 180 | 180 | 3219.5 | -15.51 | -0.482 | -0.923 | -0.120 | equivalent |
| gen|u=1.1 | atc_la | full | 180 | 180 | 3219.5 | -15.51 | -0.482 | -0.914 | -0.120 | equivalent |
| gen|u=1.1 | vispool | 8 | 180 | 180 | 5348.5 | 108.18 | 2.023 | 1.192 | 2.827 | worse |
| gen|u=1.1 | vispool | 40 | 180 | 180 | 5348.5 | -208.06 | -3.890 | -7.318 | -0.797 | inconclusive |
| gen|u=1.1 | vispool | full | 180 | 180 | 5348.5 | -196.37 | -3.672 | -7.073 | -0.681 | inconclusive |
| gen|u=1.1 | visseed501 | 8 | 180 | 180 | 3322.3 | 1469.97 | 44.246 | 23.304 | 68.730 | worse |
| gen|u=1.1 | visseed501 | 40 | 180 | 180 | 3322.3 | -149.15 | -4.489 | -6.714 | -2.489 | better |
| gen|u=1.1 | visseed501 | full | 180 | 180 | 3322.3 | -120.29 | -3.621 | -5.591 | -1.884 | better |
| gen|u=1.1 | visseed502 | 8 | 180 | 180 | 3183.8 | -34.21 | -1.075 | -1.927 | -0.333 | inconclusive |
| gen|u=1.1 | visseed502 | 40 | 180 | 180 | 3183.8 | -38.52 | -1.210 | -2.009 | -0.551 | inconclusive |
| gen|u=1.1 | visseed502 | full | 180 | 180 | 3183.8 | -22.57 | -0.709 | -1.350 | -0.177 | inconclusive |
| gen|u=1.1 | visseed503 | 8 | 180 | 180 | 4963.7 | -1812.53 | -36.516 | -54.694 | -20.253 | better |
| gen|u=1.1 | visseed503 | 40 | 180 | 180 | 4963.7 | -1810.15 | -36.468 | -55.078 | -20.313 | better |
| gen|u=1.1 | visseed503 | full | 180 | 180 | 4963.7 | -1796.49 | -36.193 | -54.396 | -20.318 | better |
| gen|u=1.1 | visseed504 | 8 | 180 | 180 | 6537.8 | -66.53 | -1.018 | -3.139 | 0.941 | inconclusive |
| gen|u=1.1 | visseed504 | 40 | 180 | 180 | 6537.8 | -16.72 | -0.256 | -2.775 | 2.073 | inconclusive |
| gen|u=1.1 | visseed504 | full | 180 | 180 | 6537.8 | -16.72 | -0.256 | -2.796 | 2.043 | inconclusive |
| gen|u=1.1 | visseed505 | 8 | 180 | 180 | 8734.7 | 984.19 | 11.267 | 9.618 | 12.998 | worse |
| gen|u=1.1 | visseed505 | 40 | 180 | 180 | 8734.7 | 974.22 | 11.153 | 9.519 | 12.871 | worse |
| gen|u=1.1 | visseed505 | full | 180 | 180 | 8734.7 | 974.22 | 11.153 | 9.487 | 12.880 | worse |
| gen|pm=0.2 | atc_la | 8 | 180 | 180 | 4188.1 | -7.86 | -0.188 | -0.354 | -0.053 | equivalent |
| gen|pm=0.2 | atc_la | 40 | 180 | 180 | 4188.1 | -17.94 | -0.428 | -0.771 | -0.151 | equivalent |
| gen|pm=0.2 | atc_la | full | 180 | 180 | 4188.1 | -17.94 | -0.428 | -0.769 | -0.152 | equivalent |
| gen|pm=0.2 | vispool | 8 | 180 | 180 | 6003.7 | -18.55 | -0.309 | -1.017 | 0.346 | inconclusive |
| gen|pm=0.2 | vispool | 40 | 180 | 180 | 6003.7 | -361.19 | -6.016 | -9.123 | -3.421 | better |
| gen|pm=0.2 | vispool | full | 180 | 180 | 6003.7 | -347.79 | -5.793 | -8.682 | -3.285 | better |
| gen|pm=0.2 | visseed501 | 8 | 180 | 180 | 4284.4 | 1541.21 | 35.973 | 19.547 | 54.717 | worse |
| gen|pm=0.2 | visseed501 | 40 | 180 | 180 | 4284.4 | -158.98 | -3.711 | -5.481 | -2.182 | better |
| gen|pm=0.2 | visseed501 | full | 180 | 180 | 4284.4 | -124.67 | -2.910 | -4.419 | -1.557 | better |
| gen|pm=0.2 | visseed502 | 8 | 180 | 180 | 4142.2 | -38.87 | -0.938 | -1.595 | -0.355 | inconclusive |
| gen|pm=0.2 | visseed502 | 40 | 180 | 180 | 4142.2 | -45.34 | -1.095 | -1.709 | -0.574 | inconclusive |
| gen|pm=0.2 | visseed502 | full | 180 | 180 | 4142.2 | -30.19 | -0.729 | -1.230 | -0.311 | inconclusive |
| gen|pm=0.2 | visseed503 | 8 | 180 | 180 | 6045.0 | -1938.09 | -32.061 | -47.539 | -18.786 | better |
| gen|pm=0.2 | visseed503 | 40 | 180 | 180 | 6045.0 | -1939.48 | -32.084 | -47.220 | -18.940 | better |
| gen|pm=0.2 | visseed503 | full | 180 | 180 | 6045.0 | -1921.94 | -31.794 | -47.092 | -18.474 | better |
| gen|pm=0.2 | visseed504 | 8 | 180 | 180 | 7930.7 | -195.74 | -2.468 | -4.252 | -0.884 | inconclusive |
| gen|pm=0.2 | visseed504 | 40 | 180 | 180 | 7930.7 | -197.03 | -2.484 | -4.373 | -0.761 | inconclusive |
| gen|pm=0.2 | visseed504 | full | 180 | 180 | 7930.7 | -197.03 | -2.484 | -4.393 | -0.755 | inconclusive |
| gen|pm=0.2 | visseed505 | 8 | 180 | 180 | 7616.1 | 538.72 | 7.073 | 5.298 | 8.976 | worse |
| gen|pm=0.2 | visseed505 | 40 | 180 | 180 | 7616.1 | 534.87 | 7.023 | 5.360 | 8.801 | worse |
| gen|pm=0.2 | visseed505 | full | 180 | 180 | 7616.1 | 534.87 | 7.023 | 5.343 | 8.821 | worse |
| gen|pm=0.5 | atc_la | 8 | 180 | 180 | 2505.5 | -0.22 | -0.009 | -0.043 | 0.027 | equivalent |
| gen|pm=0.5 | atc_la | 40 | 180 | 180 | 2505.5 | 0.79 | 0.032 | -0.030 | 0.102 | equivalent |
| gen|pm=0.5 | atc_la | full | 180 | 180 | 2505.5 | 0.79 | 0.032 | -0.031 | 0.099 | equivalent |
| gen|pm=0.5 | vispool | 8 | 180 | 180 | 2948.9 | 91.39 | 3.099 | 2.352 | 3.917 | worse |
| gen|pm=0.5 | vispool | 40 | 180 | 180 | 2948.9 | 100.71 | 3.415 | 2.599 | 4.311 | worse |
| gen|pm=0.5 | vispool | full | 180 | 180 | 2948.9 | 100.95 | 3.423 | 2.615 | 4.332 | worse |
| gen|pm=0.5 | visseed501 | 8 | 180 | 180 | 2505.1 | 10.75 | 0.429 | 0.220 | 0.741 | equivalent |
| gen|pm=0.5 | visseed501 | 40 | 180 | 180 | 2505.1 | 3.53 | 0.141 | 0.061 | 0.236 | equivalent |
| gen|pm=0.5 | visseed501 | full | 180 | 180 | 2505.1 | 2.93 | 0.117 | 0.051 | 0.190 | equivalent |
| gen|pm=0.5 | visseed502 | 8 | 180 | 180 | 2509.4 | -2.56 | -0.102 | -0.223 | 0.025 | equivalent |
| gen|pm=0.5 | visseed502 | 40 | 180 | 180 | 2509.4 | -3.30 | -0.131 | -0.228 | -0.047 | equivalent |
| gen|pm=0.5 | visseed502 | full | 180 | 180 | 2509.4 | -1.73 | -0.069 | -0.142 | 0.003 | equivalent |
| gen|pm=0.5 | visseed503 | 8 | 180 | 180 | 2509.1 | -6.37 | -0.254 | -0.536 | -0.068 | equivalent |
| gen|pm=0.5 | visseed503 | 40 | 180 | 180 | 2509.1 | -4.03 | -0.161 | -0.446 | 0.025 | equivalent |
| gen|pm=0.5 | visseed503 | full | 180 | 180 | 2509.1 | -3.83 | -0.152 | -0.430 | 0.029 | equivalent |
| gen|pm=0.5 | visseed504 | 8 | 180 | 180 | 2559.9 | 43.39 | 1.695 | 0.351 | 3.889 | inconclusive |
| gen|pm=0.5 | visseed504 | 40 | 180 | 180 | 2559.9 | 86.90 | 3.395 | 1.382 | 6.427 | worse |
| gen|pm=0.5 | visseed504 | full | 180 | 180 | 2559.9 | 86.90 | 3.395 | 1.372 | 6.358 | worse |
| gen|pm=0.5 | visseed505 | 8 | 180 | 180 | 4661.2 | 411.77 | 8.834 | 6.684 | 11.119 | worse |
| gen|pm=0.5 | visseed505 | 40 | 180 | 180 | 4661.2 | 420.47 | 9.021 | 6.862 | 11.356 | worse |
| gen|pm=0.5 | visseed505 | full | 180 | 180 | 4661.2 | 420.47 | 9.021 | 6.815 | 11.380 | worse |
| gen|pm=0.8 | atc_la | 8 | 180 | 180 | 993.4 | 0.37 | 0.037 | -0.011 | 0.097 | equivalent |
| gen|pm=0.8 | atc_la | 40 | 180 | 180 | 993.4 | 0.12 | 0.012 | -0.056 | 0.078 | equivalent |
| gen|pm=0.8 | atc_la | full | 180 | 180 | 993.4 | 0.12 | 0.012 | -0.056 | 0.079 | equivalent |
| gen|pm=0.8 | vispool | 8 | 180 | 180 | 1281.6 | 59.66 | 4.655 | 3.381 | 6.016 | worse |
| gen|pm=0.8 | vispool | 40 | 180 | 180 | 1281.6 | 66.80 | 5.213 | 3.847 | 6.708 | worse |
| gen|pm=0.8 | vispool | full | 180 | 180 | 1281.6 | 66.68 | 5.203 | 3.860 | 6.671 | worse |
| gen|pm=0.8 | visseed501 | 8 | 180 | 180 | 996.4 | 3.12 | 0.313 | 0.131 | 0.532 | equivalent |
| gen|pm=0.8 | visseed501 | 40 | 180 | 180 | 996.4 | 1.67 | 0.168 | -0.003 | 0.388 | equivalent |
| gen|pm=0.8 | visseed501 | full | 180 | 180 | 996.4 | 1.60 | 0.160 | 0.047 | 0.287 | equivalent |
| gen|pm=0.8 | visseed502 | 8 | 180 | 180 | 997.1 | -1.49 | -0.150 | -0.308 | -0.012 | equivalent |
| gen|pm=0.8 | visseed502 | 40 | 180 | 180 | 997.1 | 0.03 | 0.003 | -0.125 | 0.144 | equivalent |
| gen|pm=0.8 | visseed502 | full | 180 | 180 | 997.1 | 0.02 | 0.002 | -0.119 | 0.119 | equivalent |
| gen|pm=0.8 | visseed503 | 8 | 180 | 180 | 996.8 | -1.45 | -0.146 | -0.329 | 0.012 | equivalent |
| gen|pm=0.8 | visseed503 | 40 | 180 | 180 | 996.8 | 0.12 | 0.012 | -0.087 | 0.115 | equivalent |
| gen|pm=0.8 | visseed503 | full | 180 | 180 | 996.8 | -0.41 | -0.042 | -0.143 | 0.059 | equivalent |
| gen|pm=0.8 | visseed504 | 8 | 180 | 180 | 1003.5 | 30.59 | 3.048 | 1.774 | 4.464 | worse |
| gen|pm=0.8 | visseed504 | 40 | 180 | 180 | 1003.5 | 58.32 | 5.812 | 3.416 | 8.564 | worse |
| gen|pm=0.8 | visseed504 | full | 180 | 180 | 1003.5 | 58.32 | 5.812 | 3.442 | 8.617 | worse |
| gen|pm=0.8 | visseed505 | 8 | 180 | 180 | 2414.1 | 267.53 | 11.082 | 7.794 | 14.676 | worse |
| gen|pm=0.8 | visseed505 | 40 | 180 | 180 | 2414.1 | 273.87 | 11.345 | 7.886 | 15.181 | worse |
| gen|pm=0.8 | visseed505 | full | 180 | 180 | 2414.1 | 273.87 | 11.345 | 8.000 | 15.217 | worse |
| gen|pm=0.2|u=0.7 | atc_la | 8 | 60 | 60 | 3219.6 | -0.20 | -0.006 | -0.015 | 0.002 | equivalent |
| gen|pm=0.2|u=0.7 | atc_la | 40 | 60 | 60 | 3219.6 | -0.02 | -0.001 | -0.024 | 0.034 | equivalent |
| gen|pm=0.2|u=0.7 | atc_la | full | 60 | 60 | 3219.6 | -0.02 | -0.001 | -0.024 | 0.034 | equivalent |
| gen|pm=0.2|u=0.7 | vispool | 8 | 60 | 60 | 3241.4 | -0.78 | -0.024 | -0.166 | 0.096 | equivalent |
| gen|pm=0.2|u=0.7 | vispool | 40 | 60 | 60 | 3241.4 | -1.98 | -0.061 | -0.205 | 0.043 | equivalent |
| gen|pm=0.2|u=0.7 | vispool | full | 60 | 60 | 3241.4 | -1.61 | -0.050 | -0.190 | 0.056 | equivalent |
| gen|pm=0.2|u=0.7 | visseed501 | 8 | 60 | 60 | 3216.7 | 5.53 | 0.172 | 0.038 | 0.357 | equivalent |
| gen|pm=0.2|u=0.7 | visseed501 | 40 | 60 | 60 | 3216.7 | 2.14 | 0.066 | -0.001 | 0.154 | equivalent |
| gen|pm=0.2|u=0.7 | visseed501 | full | 60 | 60 | 3216.7 | 2.42 | 0.075 | -0.001 | 0.204 | equivalent |
| gen|pm=0.2|u=0.7 | visseed502 | 8 | 60 | 60 | 3220.0 | -1.45 | -0.045 | -0.114 | 0.020 | equivalent |
| gen|pm=0.2|u=0.7 | visseed502 | 40 | 60 | 60 | 3220.0 | -3.94 | -0.122 | -0.211 | -0.036 | equivalent |
| gen|pm=0.2|u=0.7 | visseed502 | full | 60 | 60 | 3220.0 | -2.89 | -0.090 | -0.151 | -0.032 | equivalent |
| gen|pm=0.2|u=0.7 | visseed503 | 8 | 60 | 60 | 3218.5 | -2.30 | -0.071 | -0.213 | 0.010 | equivalent |
| gen|pm=0.2|u=0.7 | visseed503 | 40 | 60 | 60 | 3218.5 | -3.26 | -0.101 | -0.259 | 0.007 | equivalent |
| gen|pm=0.2|u=0.7 | visseed503 | full | 60 | 60 | 3218.5 | -2.73 | -0.085 | -0.240 | 0.016 | equivalent |
| gen|pm=0.2|u=0.7 | visseed504 | 8 | 60 | 60 | 3240.9 | -7.72 | -0.238 | -0.690 | 0.100 | equivalent |
| gen|pm=0.2|u=0.7 | visseed504 | 40 | 60 | 60 | 3240.9 | -6.38 | -0.197 | -0.650 | 0.152 | equivalent |
| gen|pm=0.2|u=0.7 | visseed504 | full | 60 | 60 | 3240.9 | -6.38 | -0.197 | -0.642 | 0.145 | equivalent |
| gen|pm=0.2|u=0.7 | visseed505 | 8 | 60 | 60 | 3311.2 | 2.04 | 0.061 | -0.247 | 0.415 | equivalent |
| gen|pm=0.2|u=0.7 | visseed505 | 40 | 60 | 60 | 3311.2 | 1.52 | 0.046 | -0.204 | 0.320 | equivalent |
| gen|pm=0.2|u=0.7 | visseed505 | full | 60 | 60 | 3311.2 | 1.52 | 0.046 | -0.204 | 0.324 | equivalent |
| gen|pm=0.2|u=0.9 | atc_la | 8 | 60 | 60 | 3951.7 | -3.18 | -0.080 | -0.169 | -0.009 | equivalent |
| gen|pm=0.2|u=0.9 | atc_la | 40 | 60 | 60 | 3951.7 | -4.23 | -0.107 | -0.252 | 0.014 | equivalent |
| gen|pm=0.2|u=0.9 | atc_la | full | 60 | 60 | 3951.7 | -4.23 | -0.107 | -0.254 | 0.015 | equivalent |
| gen|pm=0.2|u=0.9 | vispool | 8 | 60 | 60 | 4732.5 | -20.29 | -0.429 | -1.964 | 0.901 | inconclusive |
| gen|pm=0.2|u=0.9 | vispool | 40 | 60 | 60 | 4732.5 | -63.31 | -1.338 | -3.094 | 0.054 | inconclusive |
| gen|pm=0.2|u=0.9 | vispool | full | 60 | 60 | 4732.5 | -58.74 | -1.241 | -3.002 | 0.119 | inconclusive |
| gen|pm=0.2|u=0.9 | visseed501 | 8 | 60 | 60 | 3943.8 | 240.41 | 6.096 | 1.263 | 13.533 | worse |
| gen|pm=0.2|u=0.9 | visseed501 | 40 | 60 | 60 | 3943.8 | -19.45 | -0.493 | -1.197 | 0.049 | inconclusive |
| gen|pm=0.2|u=0.9 | visseed501 | full | 60 | 60 | 3943.8 | -6.83 | -0.173 | -0.772 | 0.346 | equivalent |
| gen|pm=0.2|u=0.9 | visseed502 | 8 | 60 | 60 | 3935.8 | -19.34 | -0.491 | -0.893 | -0.167 | equivalent |
| gen|pm=0.2|u=0.9 | visseed502 | 40 | 60 | 60 | 3935.8 | -21.17 | -0.538 | -0.972 | -0.201 | equivalent |
| gen|pm=0.2|u=0.9 | visseed502 | full | 60 | 60 | 3935.8 | -20.81 | -0.529 | -0.824 | -0.293 | equivalent |
| gen|pm=0.2|u=0.9 | visseed503 | 8 | 60 | 60 | 4314.7 | -397.56 | -9.214 | -17.518 | -2.847 | better |
| gen|pm=0.2|u=0.9 | visseed503 | 40 | 60 | 60 | 4314.7 | -399.75 | -9.265 | -17.664 | -2.816 | better |
| gen|pm=0.2|u=0.9 | visseed503 | full | 60 | 60 | 4314.7 | -389.89 | -9.036 | -17.452 | -2.697 | better |
| gen|pm=0.2|u=0.9 | visseed504 | 8 | 60 | 60 | 5353.8 | -208.82 | -3.900 | -6.503 | -1.696 | better |
| gen|pm=0.2|u=0.9 | visseed504 | 40 | 60 | 60 | 5353.8 | -188.42 | -3.519 | -6.186 | -1.205 | better |
| gen|pm=0.2|u=0.9 | visseed504 | full | 60 | 60 | 5353.8 | -188.42 | -3.519 | -6.124 | -1.211 | better |
| gen|pm=0.2|u=0.9 | visseed505 | 8 | 60 | 60 | 6114.4 | 283.86 | 4.642 | 2.196 | 7.112 | worse |
| gen|pm=0.2|u=0.9 | visseed505 | 40 | 60 | 60 | 6114.4 | 312.25 | 5.107 | 2.720 | 7.665 | worse |
| gen|pm=0.2|u=0.9 | visseed505 | full | 60 | 60 | 6114.4 | 312.25 | 5.107 | 2.750 | 7.628 | worse |
| gen|pm=0.2|u=1.1 | atc_la | 8 | 60 | 60 | 5393.1 | -20.19 | -0.374 | -0.743 | -0.064 | equivalent |
| gen|pm=0.2|u=1.1 | atc_la | 40 | 60 | 60 | 5393.1 | -49.57 | -0.919 | -1.667 | -0.296 | inconclusive |
| gen|pm=0.2|u=1.1 | atc_la | full | 60 | 60 | 5393.1 | -49.57 | -0.919 | -1.692 | -0.295 | inconclusive |
| gen|pm=0.2|u=1.1 | vispool | 8 | 60 | 60 | 10037.2 | -34.59 | -0.345 | -1.392 | 0.648 | inconclusive |
| gen|pm=0.2|u=1.1 | vispool | 40 | 60 | 60 | 10037.2 | -1018.29 | -10.145 | -15.010 | -5.835 | better |
| gen|pm=0.2|u=1.1 | vispool | full | 60 | 60 | 10037.2 | -983.02 | -9.794 | -14.555 | -5.551 | better |
| gen|pm=0.2|u=1.1 | visseed501 | 8 | 60 | 60 | 5692.8 | 4377.70 | 76.900 | 42.198 | 114.399 | worse |
| gen|pm=0.2|u=1.1 | visseed501 | 40 | 60 | 60 | 5692.8 | -459.63 | -8.074 | -11.642 | -4.953 | better |
| gen|pm=0.2|u=1.1 | visseed501 | full | 60 | 60 | 5692.8 | -369.59 | -6.492 | -9.576 | -3.719 | better |
| gen|pm=0.2|u=1.1 | visseed502 | 8 | 60 | 60 | 5271.0 | -95.82 | -1.818 | -3.294 | -0.492 | inconclusive |
| gen|pm=0.2|u=1.1 | visseed502 | 40 | 60 | 60 | 5271.0 | -110.92 | -2.104 | -3.498 | -0.967 | inconclusive |
| gen|pm=0.2|u=1.1 | visseed502 | full | 60 | 60 | 5271.0 | -66.86 | -1.269 | -2.388 | -0.313 | inconclusive |
| gen|pm=0.2|u=1.1 | visseed503 | 8 | 60 | 60 | 10602.0 | -5414.42 | -51.070 | -74.430 | -30.423 | better |
| gen|pm=0.2|u=1.1 | visseed503 | 40 | 60 | 60 | 10602.0 | -5415.43 | -51.080 | -74.102 | -30.172 | better |
| gen|pm=0.2|u=1.1 | visseed503 | full | 60 | 60 | 10602.0 | -5373.21 | -50.681 | -73.309 | -29.846 | better |
| gen|pm=0.2|u=1.1 | visseed504 | 8 | 60 | 60 | 15197.4 | -370.69 | -2.439 | -4.909 | -0.178 | inconclusive |
| gen|pm=0.2|u=1.1 | visseed504 | 40 | 60 | 60 | 15197.4 | -396.30 | -2.608 | -5.489 | -0.084 | inconclusive |
| gen|pm=0.2|u=1.1 | visseed504 | full | 60 | 60 | 15197.4 | -396.30 | -2.608 | -5.455 | -0.122 | inconclusive |
| gen|pm=0.2|u=1.1 | visseed505 | 8 | 60 | 60 | 13422.8 | 1330.27 | 9.910 | 7.765 | 12.160 | worse |
| gen|pm=0.2|u=1.1 | visseed505 | 40 | 60 | 60 | 13422.8 | 1290.85 | 9.617 | 7.595 | 11.682 | worse |
| gen|pm=0.2|u=1.1 | visseed505 | full | 60 | 60 | 13422.8 | 1290.85 | 9.617 | 7.528 | 11.694 | worse |
| gen|pm=0.5|u=0.7 | atc_la | 8 | 60 | 60 | 2015.8 | -0.06 | -0.003 | -0.007 | 0.000 | equivalent |
| gen|pm=0.5|u=0.7 | atc_la | 40 | 60 | 60 | 2015.8 | -0.13 | -0.007 | -0.023 | 0.006 | equivalent |
| gen|pm=0.5|u=0.7 | atc_la | full | 60 | 60 | 2015.8 | -0.13 | -0.007 | -0.023 | 0.007 | equivalent |
| gen|pm=0.5|u=0.7 | vispool | 8 | 60 | 60 | 2022.4 | 1.09 | 0.054 | -0.024 | 0.152 | equivalent |
| gen|pm=0.5|u=0.7 | vispool | 40 | 60 | 60 | 2022.4 | 0.96 | 0.047 | -0.019 | 0.138 | equivalent |
| gen|pm=0.5|u=0.7 | vispool | full | 60 | 60 | 2022.4 | 1.16 | 0.057 | -0.007 | 0.146 | equivalent |
| gen|pm=0.5|u=0.7 | visseed501 | 8 | 60 | 60 | 2015.3 | 1.60 | 0.080 | 0.003 | 0.210 | equivalent |
| gen|pm=0.5|u=0.7 | visseed501 | 40 | 60 | 60 | 2015.3 | 0.81 | 0.040 | -0.024 | 0.151 | equivalent |
| gen|pm=0.5|u=0.7 | visseed501 | full | 60 | 60 | 2015.3 | 0.86 | 0.043 | -0.020 | 0.152 | equivalent |
| gen|pm=0.5|u=0.7 | visseed502 | 8 | 60 | 60 | 2016.2 | 0.33 | 0.017 | -0.052 | 0.099 | equivalent |
| gen|pm=0.5|u=0.7 | visseed502 | 40 | 60 | 60 | 2016.2 | -1.31 | -0.065 | -0.129 | -0.019 | equivalent |
| gen|pm=0.5|u=0.7 | visseed502 | full | 60 | 60 | 2016.2 | -0.79 | -0.039 | -0.124 | 0.033 | equivalent |
| gen|pm=0.5|u=0.7 | visseed503 | 8 | 60 | 60 | 2015.2 | -0.51 | -0.026 | -0.088 | 0.015 | equivalent |
| gen|pm=0.5|u=0.7 | visseed503 | 40 | 60 | 60 | 2015.2 | -0.51 | -0.025 | -0.089 | 0.013 | equivalent |
| gen|pm=0.5|u=0.7 | visseed503 | full | 60 | 60 | 2015.2 | -0.09 | -0.004 | -0.049 | 0.031 | equivalent |
| gen|pm=0.5|u=0.7 | visseed504 | 8 | 60 | 60 | 2016.5 | 0.37 | 0.018 | -0.074 | 0.093 | equivalent |
| gen|pm=0.5|u=0.7 | visseed504 | 40 | 60 | 60 | 2016.5 | 1.34 | 0.066 | -0.068 | 0.233 | equivalent |
| gen|pm=0.5|u=0.7 | visseed504 | full | 60 | 60 | 2016.5 | 1.34 | 0.066 | -0.067 | 0.235 | equivalent |
| gen|pm=0.5|u=0.7 | visseed505 | 8 | 60 | 60 | 2048.6 | 3.64 | 0.178 | -0.188 | 0.660 | equivalent |
| gen|pm=0.5|u=0.7 | visseed505 | 40 | 60 | 60 | 2048.6 | 4.45 | 0.217 | -0.070 | 0.621 | equivalent |
| gen|pm=0.5|u=0.7 | visseed505 | full | 60 | 60 | 2048.6 | 4.45 | 0.217 | -0.069 | 0.642 | equivalent |
| gen|pm=0.5|u=0.9 | atc_la | 8 | 60 | 60 | 2483.1 | 0.01 | 0.000 | -0.038 | 0.038 | equivalent |
| gen|pm=0.5|u=0.9 | atc_la | 40 | 60 | 60 | 2483.1 | -0.46 | -0.018 | -0.107 | 0.079 | equivalent |
| gen|pm=0.5|u=0.9 | atc_la | full | 60 | 60 | 2483.1 | -0.46 | -0.018 | -0.109 | 0.079 | equivalent |
| gen|pm=0.5|u=0.9 | vispool | 8 | 60 | 60 | 2755.1 | 49.58 | 1.800 | 1.120 | 2.511 | worse |
| gen|pm=0.5|u=0.9 | vispool | 40 | 60 | 60 | 2755.1 | 58.64 | 2.128 | 1.436 | 2.870 | worse |
| gen|pm=0.5|u=0.9 | vispool | full | 60 | 60 | 2755.1 | 58.96 | 2.140 | 1.453 | 2.861 | worse |
| gen|pm=0.5|u=0.9 | visseed501 | 8 | 60 | 60 | 2477.9 | 6.48 | 0.262 | 0.139 | 0.417 | equivalent |
| gen|pm=0.5|u=0.9 | visseed501 | 40 | 60 | 60 | 2477.9 | 2.23 | 0.090 | 0.017 | 0.170 | equivalent |
| gen|pm=0.5|u=0.9 | visseed501 | full | 60 | 60 | 2477.9 | 2.67 | 0.108 | 0.016 | 0.213 | equivalent |
| gen|pm=0.5|u=0.9 | visseed502 | 8 | 60 | 60 | 2485.1 | -4.53 | -0.182 | -0.317 | -0.048 | equivalent |
| gen|pm=0.5|u=0.9 | visseed502 | 40 | 60 | 60 | 2485.1 | -3.97 | -0.160 | -0.310 | -0.028 | equivalent |
| gen|pm=0.5|u=0.9 | visseed502 | full | 60 | 60 | 2485.1 | -3.37 | -0.136 | -0.217 | -0.060 | equivalent |
| gen|pm=0.5|u=0.9 | visseed503 | 8 | 60 | 60 | 2476.0 | 0.35 | 0.014 | -0.057 | 0.107 | equivalent |
| gen|pm=0.5|u=0.9 | visseed503 | 40 | 60 | 60 | 2476.0 | 2.76 | 0.112 | 0.014 | 0.233 | equivalent |
| gen|pm=0.5|u=0.9 | visseed503 | full | 60 | 60 | 2476.0 | 3.33 | 0.135 | 0.050 | 0.241 | equivalent |
| gen|pm=0.5|u=0.9 | visseed504 | 8 | 60 | 60 | 2517.4 | 31.50 | 1.251 | 0.436 | 2.229 | inconclusive |
| gen|pm=0.5|u=0.9 | visseed504 | 40 | 60 | 60 | 2517.4 | 55.55 | 2.207 | 0.931 | 3.738 | inconclusive |
| gen|pm=0.5|u=0.9 | visseed504 | full | 60 | 60 | 2517.4 | 55.55 | 2.207 | 0.937 | 3.773 | inconclusive |
| gen|pm=0.5|u=0.9 | visseed505 | 8 | 60 | 60 | 3819.3 | 214.10 | 5.606 | 3.165 | 8.273 | worse |
| gen|pm=0.5|u=0.9 | visseed505 | 40 | 60 | 60 | 3819.3 | 236.60 | 6.195 | 3.804 | 8.867 | worse |
| gen|pm=0.5|u=0.9 | visseed505 | full | 60 | 60 | 3819.3 | 236.60 | 6.195 | 3.806 | 8.796 | worse |
| gen|pm=0.5|u=1.1 | atc_la | 8 | 60 | 60 | 3017.6 | -0.60 | -0.020 | -0.096 | 0.067 | equivalent |
| gen|pm=0.5|u=1.1 | atc_la | 40 | 60 | 60 | 3017.6 | 2.96 | 0.098 | -0.031 | 0.247 | equivalent |
| gen|pm=0.5|u=1.1 | atc_la | full | 60 | 60 | 3017.6 | 2.96 | 0.098 | -0.031 | 0.251 | equivalent |
| gen|pm=0.5|u=1.1 | vispool | 8 | 60 | 60 | 4069.3 | 223.51 | 5.493 | 4.261 | 6.783 | worse |
| gen|pm=0.5|u=1.1 | vispool | 40 | 60 | 60 | 4069.3 | 242.55 | 5.960 | 4.604 | 7.485 | worse |
| gen|pm=0.5|u=1.1 | vispool | full | 60 | 60 | 4069.3 | 242.73 | 5.965 | 4.603 | 7.457 | worse |
| gen|pm=0.5|u=1.1 | visseed501 | 8 | 60 | 60 | 3021.9 | 24.16 | 0.799 | 0.325 | 1.548 | inconclusive |
| gen|pm=0.5|u=1.1 | visseed501 | 40 | 60 | 60 | 3021.9 | 7.54 | 0.250 | 0.073 | 0.463 | equivalent |
| gen|pm=0.5|u=1.1 | visseed501 | full | 60 | 60 | 3021.9 | 5.25 | 0.174 | 0.045 | 0.320 | equivalent |
| gen|pm=0.5|u=1.1 | visseed502 | 8 | 60 | 60 | 3026.9 | -3.47 | -0.115 | -0.397 | 0.169 | equivalent |
| gen|pm=0.5|u=1.1 | visseed502 | 40 | 60 | 60 | 3026.9 | -4.61 | -0.152 | -0.360 | 0.018 | equivalent |
| gen|pm=0.5|u=1.1 | visseed502 | full | 60 | 60 | 3026.9 | -1.02 | -0.034 | -0.202 | 0.123 | equivalent |
| gen|pm=0.5|u=1.1 | visseed503 | 8 | 60 | 60 | 3036.1 | -18.95 | -0.624 | -1.292 | -0.188 | inconclusive |
| gen|pm=0.5|u=1.1 | visseed503 | 40 | 60 | 60 | 3036.1 | -14.35 | -0.473 | -1.157 | -0.039 | inconclusive |
| gen|pm=0.5|u=1.1 | visseed503 | full | 60 | 60 | 3036.1 | -14.72 | -0.485 | -1.165 | -0.052 | inconclusive |
| gen|pm=0.5|u=1.1 | visseed504 | 8 | 60 | 60 | 3145.7 | 98.28 | 3.124 | 0.039 | 8.284 | inconclusive |
| gen|pm=0.5|u=1.1 | visseed504 | 40 | 60 | 60 | 3145.7 | 203.80 | 6.479 | 1.741 | 13.488 | worse |
| gen|pm=0.5|u=1.1 | visseed504 | full | 60 | 60 | 3145.7 | 203.80 | 6.479 | 1.742 | 13.521 | worse |
| gen|pm=0.5|u=1.1 | visseed505 | 8 | 60 | 60 | 8115.7 | 1017.56 | 12.538 | 9.914 | 15.280 | worse |
| gen|pm=0.5|u=1.1 | visseed505 | 40 | 60 | 60 | 8115.7 | 1020.35 | 12.573 | 9.809 | 15.540 | worse |
| gen|pm=0.5|u=1.1 | visseed505 | full | 60 | 60 | 8115.7 | 1020.35 | 12.573 | 9.826 | 15.426 | worse |
| gen|pm=0.8|u=0.7 | atc_la | 8 | 60 | 60 | 753.7 | -0.01 | -0.002 | -0.025 | 0.018 | equivalent |
| gen|pm=0.8|u=0.7 | atc_la | 40 | 60 | 60 | 753.7 | 0.04 | 0.005 | -0.014 | 0.026 | equivalent |
| gen|pm=0.8|u=0.7 | atc_la | full | 60 | 60 | 753.7 | 0.04 | 0.005 | -0.014 | 0.026 | equivalent |
| gen|pm=0.8|u=0.7 | vispool | 8 | 60 | 60 | 757.2 | 2.13 | 0.282 | 0.040 | 0.595 | equivalent |
| gen|pm=0.8|u=0.7 | vispool | 40 | 60 | 60 | 757.2 | 1.71 | 0.225 | -0.025 | 0.571 | equivalent |
| gen|pm=0.8|u=0.7 | vispool | full | 60 | 60 | 757.2 | 1.66 | 0.220 | -0.032 | 0.561 | equivalent |
| gen|pm=0.8|u=0.7 | visseed501 | 8 | 60 | 60 | 753.7 | 0.30 | 0.039 | -0.003 | 0.098 | equivalent |
| gen|pm=0.8|u=0.7 | visseed501 | 40 | 60 | 60 | 753.7 | -0.05 | -0.006 | -0.023 | 0.009 | equivalent |
| gen|pm=0.8|u=0.7 | visseed501 | full | 60 | 60 | 753.7 | 0.05 | 0.007 | -0.022 | 0.045 | equivalent |
| gen|pm=0.8|u=0.7 | visseed502 | 8 | 60 | 60 | 754.3 | -0.50 | -0.067 | -0.154 | -0.008 | equivalent |
| gen|pm=0.8|u=0.7 | visseed502 | 40 | 60 | 60 | 754.3 | -0.49 | -0.065 | -0.171 | 0.002 | equivalent |
| gen|pm=0.8|u=0.7 | visseed502 | full | 60 | 60 | 754.3 | -0.50 | -0.067 | -0.179 | 0.003 | equivalent |
| gen|pm=0.8|u=0.7 | visseed503 | 8 | 60 | 60 | 753.7 | 0.17 | 0.022 | -0.025 | 0.076 | equivalent |
| gen|pm=0.8|u=0.7 | visseed503 | 40 | 60 | 60 | 753.7 | 0.27 | 0.036 | -0.012 | 0.115 | equivalent |
| gen|pm=0.8|u=0.7 | visseed503 | full | 60 | 60 | 753.7 | -0.03 | -0.004 | -0.039 | 0.027 | equivalent |
| gen|pm=0.8|u=0.7 | visseed504 | 8 | 60 | 60 | 754.4 | 4.83 | 0.640 | 0.006 | 1.806 | inconclusive |
| gen|pm=0.8|u=0.7 | visseed504 | 40 | 60 | 60 | 754.4 | 4.93 | 0.653 | 0.005 | 1.834 | inconclusive |
| gen|pm=0.8|u=0.7 | visseed504 | full | 60 | 60 | 754.4 | 4.93 | 0.653 | 0.006 | 1.834 | inconclusive |
| gen|pm=0.8|u=0.7 | visseed505 | 8 | 60 | 60 | 770.1 | 5.88 | 0.764 | 0.007 | 1.785 | inconclusive |
| gen|pm=0.8|u=0.7 | visseed505 | 40 | 60 | 60 | 770.1 | 3.87 | 0.502 | -0.286 | 1.716 | inconclusive |
| gen|pm=0.8|u=0.7 | visseed505 | full | 60 | 60 | 770.1 | 3.87 | 0.502 | -0.282 | 1.724 | inconclusive |
| gen|pm=0.8|u=0.9 | atc_la | 8 | 60 | 60 | 978.7 | 0.63 | 0.064 | -0.001 | 0.136 | equivalent |
| gen|pm=0.8|u=0.9 | atc_la | 40 | 60 | 60 | 978.7 | 0.23 | 0.023 | -0.056 | 0.102 | equivalent |
| gen|pm=0.8|u=0.9 | atc_la | full | 60 | 60 | 978.7 | 0.23 | 0.023 | -0.055 | 0.105 | equivalent |
| gen|pm=0.8|u=0.9 | vispool | 8 | 60 | 60 | 1148.6 | 41.24 | 3.591 | 2.098 | 5.262 | worse |
| gen|pm=0.8|u=0.9 | vispool | 40 | 60 | 60 | 1148.6 | 47.16 | 4.106 | 2.463 | 5.928 | worse |
| gen|pm=0.8|u=0.9 | vispool | full | 60 | 60 | 1148.6 | 47.20 | 4.109 | 2.443 | 5.941 | worse |
| gen|pm=0.8|u=0.9 | visseed501 | 8 | 60 | 60 | 983.4 | 1.02 | 0.104 | -0.006 | 0.225 | equivalent |
| gen|pm=0.8|u=0.9 | visseed501 | 40 | 60 | 60 | 983.4 | 0.43 | 0.044 | -0.067 | 0.159 | equivalent |
| gen|pm=0.8|u=0.9 | visseed501 | full | 60 | 60 | 983.4 | 1.28 | 0.130 | 0.013 | 0.267 | equivalent |
| gen|pm=0.8|u=0.9 | visseed502 | 8 | 60 | 60 | 983.4 | -0.63 | -0.064 | -0.235 | 0.138 | equivalent |
| gen|pm=0.8|u=0.9 | visseed502 | 40 | 60 | 60 | 983.4 | 0.62 | 0.063 | -0.207 | 0.396 | equivalent |
| gen|pm=0.8|u=0.9 | visseed502 | full | 60 | 60 | 983.4 | 0.40 | 0.041 | -0.168 | 0.264 | equivalent |
| gen|pm=0.8|u=0.9 | visseed503 | 8 | 60 | 60 | 983.6 | -0.29 | -0.030 | -0.192 | 0.155 | equivalent |
| gen|pm=0.8|u=0.9 | visseed503 | 40 | 60 | 60 | 983.6 | 0.74 | 0.076 | -0.044 | 0.194 | equivalent |
| gen|pm=0.8|u=0.9 | visseed503 | full | 60 | 60 | 983.6 | 0.32 | 0.033 | -0.065 | 0.130 | equivalent |
| gen|pm=0.8|u=0.9 | visseed504 | 8 | 60 | 60 | 985.8 | 14.13 | 1.433 | 0.388 | 2.818 | inconclusive |
| gen|pm=0.8|u=0.9 | visseed504 | 40 | 60 | 60 | 985.8 | 27.70 | 2.809 | 0.821 | 5.504 | inconclusive |
| gen|pm=0.8|u=0.9 | visseed504 | full | 60 | 60 | 985.8 | 27.70 | 2.809 | 0.846 | 5.551 | inconclusive |
| gen|pm=0.8|u=0.9 | visseed505 | 8 | 60 | 60 | 1806.6 | 191.98 | 10.627 | 5.847 | 16.026 | worse |
| gen|pm=0.8|u=0.9 | visseed505 | 40 | 60 | 60 | 1806.6 | 206.30 | 11.419 | 6.257 | 17.277 | worse |
| gen|pm=0.8|u=0.9 | visseed505 | full | 60 | 60 | 1806.6 | 206.30 | 11.419 | 6.245 | 17.407 | worse |
| gen|pm=0.8|u=1.1 | atc_la | 8 | 60 | 60 | 1247.7 | 0.49 | 0.039 | -0.059 | 0.167 | equivalent |
| gen|pm=0.8|u=1.1 | atc_la | 40 | 60 | 60 | 1247.7 | 0.09 | 0.007 | -0.144 | 0.155 | equivalent |
| gen|pm=0.8|u=1.1 | atc_la | full | 60 | 60 | 1247.7 | 0.09 | 0.007 | -0.140 | 0.154 | equivalent |
| gen|pm=0.8|u=1.1 | vispool | 8 | 60 | 60 | 1938.9 | 135.60 | 6.994 | 5.026 | 9.203 | worse |
| gen|pm=0.8|u=1.1 | vispool | 40 | 60 | 60 | 1938.9 | 151.55 | 7.816 | 5.701 | 10.203 | worse |
| gen|pm=0.8|u=1.1 | vispool | full | 60 | 60 | 1938.9 | 151.18 | 7.797 | 5.704 | 10.111 | worse |
| gen|pm=0.8|u=1.1 | visseed501 | 8 | 60 | 60 | 1252.1 | 8.05 | 0.643 | 0.238 | 1.142 | inconclusive |
| gen|pm=0.8|u=1.1 | visseed501 | 40 | 60 | 60 | 1252.1 | 4.64 | 0.371 | -0.021 | 0.888 | equivalent |
| gen|pm=0.8|u=1.1 | visseed501 | full | 60 | 60 | 1252.1 | 3.46 | 0.276 | 0.020 | 0.542 | equivalent |
| gen|pm=0.8|u=1.1 | visseed502 | 8 | 60 | 60 | 1253.6 | -3.35 | -0.267 | -0.600 | 0.010 | equivalent |
| gen|pm=0.8|u=1.1 | visseed502 | 40 | 60 | 60 | 1253.6 | -0.04 | -0.003 | -0.219 | 0.215 | equivalent |
| gen|pm=0.8|u=1.1 | visseed502 | full | 60 | 60 | 1253.6 | 0.17 | 0.014 | -0.210 | 0.233 | equivalent |
| gen|pm=0.8|u=1.1 | visseed503 | 8 | 60 | 60 | 1253.0 | -4.23 | -0.338 | -0.741 | 0.008 | equivalent |
| gen|pm=0.8|u=1.1 | visseed503 | 40 | 60 | 60 | 1253.0 | -0.66 | -0.052 | -0.265 | 0.175 | equivalent |
| gen|pm=0.8|u=1.1 | visseed503 | full | 60 | 60 | 1253.0 | -1.53 | -0.122 | -0.351 | 0.109 | equivalent |
| gen|pm=0.8|u=1.1 | visseed504 | 8 | 60 | 60 | 1270.3 | 72.82 | 5.732 | 3.119 | 8.740 | worse |
| gen|pm=0.8|u=1.1 | visseed504 | 40 | 60 | 60 | 1270.3 | 142.34 | 11.205 | 6.210 | 16.805 | worse |
| gen|pm=0.8|u=1.1 | visseed504 | full | 60 | 60 | 1270.3 | 142.34 | 11.205 | 6.269 | 16.845 | worse |
| gen|pm=0.8|u=1.1 | visseed505 | 8 | 60 | 60 | 4665.7 | 604.73 | 12.961 | 8.958 | 17.642 | worse |
| gen|pm=0.8|u=1.1 | visseed505 | 40 | 60 | 60 | 4665.7 | 611.46 | 13.105 | 8.748 | 18.215 | worse |
| gen|pm=0.8|u=1.1 | visseed505 | full | 60 | 60 | 4665.7 | 611.46 | 13.105 | 8.688 | 18.007 | worse |


### empirical cells (Eval-B anchors x crew multiplier)

| scope | arm | level | n_configs | n_clusters | mean_control | mean_diff | pct_of_control | pct_ci_lo | pct_ci_hi | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| emp|ALL | atc_la | 8 | 540 | 180 | 450.1 | -0.02 | -0.004 | -0.015 | 0.002 | equivalent |
| emp|ALL | atc_la | 40 | 540 | 180 | 450.1 | -0.02 | -0.004 | -0.015 | 0.002 | equivalent |
| emp|ALL | atc_la | full | 540 | 180 | 450.1 | -0.02 | -0.004 | -0.015 | 0.002 | equivalent |
| emp|ALL | rollcp2 | 8 | 144 | 48 | 507.5 | 0.19 | 0.037 | -0.001 | 0.082 | equivalent |
| emp|ALL | rollcp2 | 40 | 144 | 48 | 507.5 | 1.80 | 0.354 | -0.118 | 1.182 | inconclusive |
| emp|ALL | rollcp2 | full | 144 | 48 | 507.5 | 2.95 | 0.581 | -0.016 | 1.761 | inconclusive |
| emp|ALL | vispool | 8 | 540 | 180 | 448.8 | 0.15 | 0.033 | -0.029 | 0.109 | equivalent |
| emp|ALL | vispool | 40 | 540 | 180 | 448.8 | -0.08 | -0.017 | -0.061 | 0.026 | equivalent |
| emp|ALL | vispool | full | 540 | 180 | 448.8 | 0.14 | 0.031 | 0.001 | 0.069 | equivalent |
| emp|ALL | visseed501 | 8 | 540 | 180 | 447.1 | 1.38 | 0.308 | -0.006 | 0.750 | equivalent |
| emp|ALL | visseed501 | 40 | 540 | 180 | 447.1 | -0.14 | -0.032 | -0.190 | 0.088 | equivalent |
| emp|ALL | visseed501 | full | 540 | 180 | 447.1 | 0.11 | 0.024 | -0.039 | 0.115 | equivalent |
| emp|ALL | visseed502 | 8 | 540 | 180 | 448.0 | -1.00 | -0.224 | -0.399 | -0.081 | equivalent |
| emp|ALL | visseed502 | 40 | 540 | 180 | 448.0 | -0.74 | -0.164 | -0.368 | 0.031 | equivalent |
| emp|ALL | visseed502 | full | 540 | 180 | 448.0 | -0.03 | -0.006 | -0.087 | 0.072 | equivalent |
| emp|ALL | visseed503 | 8 | 540 | 180 | 447.3 | -0.13 | -0.029 | -0.083 | 0.015 | equivalent |
| emp|ALL | visseed503 | 40 | 540 | 180 | 447.3 | -0.10 | -0.023 | -0.097 | 0.026 | equivalent |
| emp|ALL | visseed503 | full | 540 | 180 | 447.3 | 0.02 | 0.006 | -0.041 | 0.047 | equivalent |
| emp|ALL | visseed504 | 8 | 540 | 180 | 450.7 | 0.28 | 0.062 | -0.082 | 0.234 | equivalent |
| emp|ALL | visseed504 | 40 | 540 | 180 | 450.7 | 0.28 | 0.061 | -0.082 | 0.233 | equivalent |
| emp|ALL | visseed504 | full | 540 | 180 | 450.7 | 0.28 | 0.061 | -0.085 | 0.236 | equivalent |
| emp|ALL | visseed505 | 8 | 540 | 180 | 450.8 | 0.23 | 0.050 | -0.007 | 0.138 | equivalent |
| emp|ALL | visseed505 | 40 | 540 | 180 | 450.8 | 0.32 | 0.070 | -0.001 | 0.166 | equivalent |
| emp|ALL | visseed505 | full | 540 | 180 | 450.8 | 0.32 | 0.070 | -0.001 | 0.167 | equivalent |
| emp|m=1.0 | atc_la | 8 | 180 | 180 | 445.6 | 0.00 | 0.000 | 0.000 | 0.000 | equivalent |
| emp|m=1.0 | atc_la | 40 | 180 | 180 | 445.6 | 0.00 | 0.000 | 0.000 | 0.000 | equivalent |
| emp|m=1.0 | atc_la | full | 180 | 180 | 445.6 | 0.00 | 0.000 | 0.000 | 0.000 | equivalent |
| emp|m=1.0 | rollcp2 | 8 | 48 | 48 | 505.9 | 0.00 | 0.001 | -0.014 | 0.015 | equivalent |
| emp|m=1.0 | rollcp2 | 40 | 48 | 48 | 505.9 | -0.01 | -0.003 | -0.017 | 0.007 | equivalent |
| emp|m=1.0 | rollcp2 | full | 48 | 48 | 505.9 | 6.12 | 1.211 | -0.015 | 3.639 | inconclusive |
| emp|m=1.0 | vispool | 8 | 180 | 180 | 445.0 | -0.03 | -0.007 | -0.022 | 0.007 | equivalent |
| emp|m=1.0 | vispool | 40 | 180 | 180 | 445.0 | -0.05 | -0.010 | -0.034 | 0.007 | equivalent |
| emp|m=1.0 | vispool | full | 180 | 180 | 445.0 | -0.00 | -0.000 | -0.020 | 0.019 | equivalent |
| emp|m=1.0 | visseed501 | 8 | 180 | 180 | 444.7 | 0.17 | 0.038 | -0.001 | 0.104 | equivalent |
| emp|m=1.0 | visseed501 | 40 | 180 | 180 | 444.7 | 0.05 | 0.011 | 0.000 | 0.027 | equivalent |
| emp|m=1.0 | visseed501 | full | 180 | 180 | 444.7 | 0.05 | 0.012 | 0.000 | 0.027 | equivalent |
| emp|m=1.0 | visseed502 | 8 | 180 | 180 | 445.0 | -0.30 | -0.068 | -0.158 | -0.004 | equivalent |
| emp|m=1.0 | visseed502 | 40 | 180 | 180 | 445.0 | -0.31 | -0.069 | -0.159 | -0.005 | equivalent |
| emp|m=1.0 | visseed502 | full | 180 | 180 | 445.0 | -0.09 | -0.019 | -0.103 | 0.070 | equivalent |
| emp|m=1.0 | visseed503 | 8 | 180 | 180 | 444.8 | -0.05 | -0.011 | -0.024 | 0.000 | equivalent |
| emp|m=1.0 | visseed503 | 40 | 180 | 180 | 444.8 | -0.00 | -0.001 | -0.005 | 0.002 | equivalent |
| emp|m=1.0 | visseed503 | full | 180 | 180 | 444.8 | -0.01 | -0.002 | -0.006 | 0.000 | equivalent |
| emp|m=1.0 | visseed504 | 8 | 180 | 180 | 444.9 | 0.05 | 0.012 | -0.035 | 0.061 | equivalent |
| emp|m=1.0 | visseed504 | 40 | 180 | 180 | 444.9 | 0.05 | 0.012 | -0.031 | 0.062 | equivalent |
| emp|m=1.0 | visseed504 | full | 180 | 180 | 444.9 | 0.05 | 0.012 | -0.034 | 0.062 | equivalent |
| emp|m=1.0 | visseed505 | 8 | 180 | 180 | 445.7 | -0.02 | -0.005 | -0.020 | 0.006 | equivalent |
| emp|m=1.0 | visseed505 | 40 | 180 | 180 | 445.7 | -0.02 | -0.005 | -0.020 | 0.006 | equivalent |
| emp|m=1.0 | visseed505 | full | 180 | 180 | 445.7 | -0.02 | -0.005 | -0.020 | 0.006 | equivalent |
| emp|m=0.8 | atc_la | 8 | 180 | 180 | 448.2 | -0.03 | -0.007 | -0.020 | 0.000 | equivalent |
| emp|m=0.8 | atc_la | 40 | 180 | 180 | 448.2 | -0.03 | -0.007 | -0.020 | 0.000 | equivalent |
| emp|m=0.8 | atc_la | full | 180 | 180 | 448.2 | -0.03 | -0.007 | -0.020 | 0.000 | equivalent |
| emp|m=0.8 | rollcp2 | 8 | 48 | 48 | 506.0 | 0.16 | 0.032 | -0.002 | 0.089 | equivalent |
| emp|m=0.8 | rollcp2 | 40 | 48 | 48 | 506.0 | 3.72 | 0.736 | 0.008 | 2.139 | inconclusive |
| emp|m=0.8 | rollcp2 | full | 48 | 48 | 506.0 | 1.41 | 0.279 | -0.001 | 0.826 | equivalent |
| emp|m=0.8 | vispool | 8 | 180 | 180 | 447.0 | 0.10 | 0.022 | -0.034 | 0.084 | equivalent |
| emp|m=0.8 | vispool | 40 | 180 | 180 | 447.0 | 0.04 | 0.009 | -0.038 | 0.060 | equivalent |
| emp|m=0.8 | vispool | full | 180 | 180 | 447.0 | 0.16 | 0.035 | -0.002 | 0.084 | equivalent |
| emp|m=0.8 | visseed501 | 8 | 180 | 180 | 446.3 | 0.49 | 0.109 | -0.019 | 0.353 | equivalent |
| emp|m=0.8 | visseed501 | 40 | 180 | 180 | 446.3 | -0.02 | -0.006 | -0.016 | 0.002 | equivalent |
| emp|m=0.8 | visseed501 | full | 180 | 180 | 446.3 | -0.04 | -0.008 | -0.020 | 0.001 | equivalent |
| emp|m=0.8 | visseed502 | 8 | 180 | 180 | 447.0 | -0.71 | -0.159 | -0.347 | -0.012 | equivalent |
| emp|m=0.8 | visseed502 | 40 | 180 | 180 | 447.0 | -0.65 | -0.145 | -0.336 | -0.014 | equivalent |
| emp|m=0.8 | visseed502 | full | 180 | 180 | 447.0 | 0.06 | 0.014 | -0.073 | 0.101 | equivalent |
| emp|m=0.8 | visseed503 | 8 | 180 | 180 | 446.3 | -0.03 | -0.006 | -0.015 | 0.001 | equivalent |
| emp|m=0.8 | visseed503 | 40 | 180 | 180 | 446.3 | 0.14 | 0.031 | 0.000 | 0.084 | equivalent |
| emp|m=0.8 | visseed503 | full | 180 | 180 | 446.3 | 0.02 | 0.005 | -0.010 | 0.026 | equivalent |
| emp|m=0.8 | visseed504 | 8 | 180 | 180 | 447.0 | 0.45 | 0.101 | 0.006 | 0.282 | equivalent |
| emp|m=0.8 | visseed504 | 40 | 180 | 180 | 447.0 | 0.45 | 0.101 | 0.006 | 0.279 | equivalent |
| emp|m=0.8 | visseed504 | full | 180 | 180 | 447.0 | 0.45 | 0.101 | 0.003 | 0.279 | equivalent |
| emp|m=0.8 | visseed505 | 8 | 180 | 180 | 448.6 | 0.29 | 0.065 | 0.003 | 0.177 | equivalent |
| emp|m=0.8 | visseed505 | 40 | 180 | 180 | 448.6 | 0.29 | 0.065 | 0.003 | 0.177 | equivalent |
| emp|m=0.8 | visseed505 | full | 180 | 180 | 448.6 | 0.29 | 0.065 | 0.003 | 0.177 | equivalent |
| emp|m=0.6 | atc_la | 8 | 180 | 180 | 456.4 | -0.02 | -0.005 | -0.026 | 0.010 | equivalent |
| emp|m=0.6 | atc_la | 40 | 180 | 180 | 456.4 | -0.03 | -0.006 | -0.026 | 0.009 | equivalent |
| emp|m=0.6 | atc_la | full | 180 | 180 | 456.4 | -0.03 | -0.006 | -0.026 | 0.009 | equivalent |
| emp|m=0.6 | rollcp2 | 8 | 48 | 48 | 510.7 | 0.40 | 0.077 | -0.021 | 0.195 | equivalent |
| emp|m=0.6 | rollcp2 | 40 | 48 | 48 | 510.7 | 1.68 | 0.329 | -0.448 | 1.459 | inconclusive |
| emp|m=0.6 | rollcp2 | full | 48 | 48 | 510.7 | 1.30 | 0.255 | -0.066 | 0.859 | equivalent |
| emp|m=0.6 | vispool | 8 | 180 | 180 | 454.3 | 0.38 | 0.084 | -0.071 | 0.275 | equivalent |
| emp|m=0.6 | vispool | 40 | 180 | 180 | 454.3 | -0.23 | -0.050 | -0.142 | 0.031 | equivalent |
| emp|m=0.6 | vispool | full | 180 | 180 | 454.3 | 0.26 | 0.058 | -0.016 | 0.141 | equivalent |
| emp|m=0.6 | visseed501 | 8 | 180 | 180 | 450.3 | 3.48 | 0.773 | -0.015 | 1.972 | inconclusive |
| emp|m=0.6 | visseed501 | 40 | 180 | 180 | 450.3 | -0.45 | -0.099 | -0.561 | 0.260 | equivalent |
| emp|m=0.6 | visseed501 | full | 180 | 180 | 450.3 | 0.31 | 0.068 | -0.114 | 0.343 | equivalent |
| emp|m=0.6 | visseed502 | 8 | 180 | 180 | 452.0 | -2.00 | -0.442 | -0.773 | -0.167 | equivalent |
| emp|m=0.6 | visseed502 | 40 | 180 | 180 | 452.0 | -1.25 | -0.277 | -0.719 | 0.231 | equivalent |
| emp|m=0.6 | visseed502 | full | 180 | 180 | 452.0 | -0.06 | -0.012 | -0.246 | 0.204 | equivalent |
| emp|m=0.6 | visseed503 | 8 | 180 | 180 | 450.9 | -0.32 | -0.070 | -0.221 | 0.061 | equivalent |
| emp|m=0.6 | visseed503 | 40 | 180 | 180 | 450.9 | -0.44 | -0.097 | -0.316 | 0.046 | equivalent |
| emp|m=0.6 | visseed503 | full | 180 | 180 | 450.9 | 0.06 | 0.013 | -0.124 | 0.136 | equivalent |
| emp|m=0.6 | visseed504 | 8 | 180 | 180 | 460.3 | 0.34 | 0.074 | -0.273 | 0.413 | equivalent |
| emp|m=0.6 | visseed504 | 40 | 180 | 180 | 460.3 | 0.33 | 0.071 | -0.287 | 0.404 | equivalent |
| emp|m=0.6 | visseed504 | full | 180 | 180 | 460.3 | 0.33 | 0.071 | -0.277 | 0.413 | equivalent |
| emp|m=0.6 | visseed505 | 8 | 180 | 180 | 458.0 | 0.40 | 0.088 | -0.020 | 0.240 | equivalent |
| emp|m=0.6 | visseed505 | 40 | 180 | 180 | 458.0 | 0.68 | 0.148 | -0.003 | 0.349 | equivalent |
| emp|m=0.6 | visseed505 | full | 180 | 180 | 458.0 | 0.68 | 0.148 | -0.002 | 0.343 | equivalent |


## 2. The four pre-stated hypotheses


**H1. visibility has negligible value under slack capacity**


Verdict: supported.


Carried by: under slack capacity the largest visibility effect over every arm that can read advance knowledge is +0.189% of the same arm's own L=0 mean, and 44 of the 45 arm-level contrasts are practically equivalent.


Numbers: gen|u=0.7 visseed505 at L=8: +0.189% [-0.051, +0.459], equivalent | the only slack contrast outside equivalence is the rolling planner, emp|m=1.0 rollcp2 at L=full: +1.211% [-0.015, +3.639], inconclusive, which is the solver budget and not the information


**H2. visibility becomes valuable near capacity when preventive work is a substantial share of workload**


Verdict: not supported as stated; the gain region is the opposite preventive share.


Carried by: the policy pool gains only where preventive work is a SMALL share and capacity is exceeded, and loses where the preventive share is high (pm 0.5: +6.0%, pm 0.8: +7.8%, both at u=1.1, L=40).


Numbers: gen|pm=0.2|u=1.1 vispool at L=40: -10.145% [-15.010, -5.835], better | H2's own region: gen|pm=0.8|u=1.1 vispool at L=40: +7.816% [+5.701, +10.203], worse


**H3. rolling optimization benefits more from visibility than myopic rules, provided replanning remains feasible**


Verdict: not supported: no visibility gain for the rolling planner at any level or crew multiplier.


Carried by: across the 12 rolling contrasts (the pooled empirical scope and the three crew multipliers, each at three levels) the effect runs from -0.003% to +1.211% and no interval clears the margin on the better side; the replan diagnostic is consistent with budget dilution, mean seconds per replan 0.45 s at L=0 against 0.90 s at L=40 on a fixed 2 s budget, and the share of configurations whose mean replan sits at 95% of the budget rises from 6% to 27%.


Numbers: best emp|m=1.0 rollcp2 at L=40: -0.003% [-0.017, +0.007], equivalent | worst emp|m=1.0 rollcp2 at L=full: +1.211% [-0.015, +3.639], inconclusive


**H4. the learned policy gains only if the lookahead features carry information a fixed rule cannot summarize**


Verdict: supported where the policy gains, with a boundary the hypothesis did not anticipate.


Carried by: in the one region where advance knowledge pays, the policy pool gains 10.1% while the forecast-aware rule reading the same future work gains 0.92%; where the preventive share is high the same policies are 7.8% WORSE than their own L=0 control, so the lookahead input is not free.


Numbers: gen|pm=0.2|u=1.1 vispool at L=40: -10.145% [-15.010, -5.835], better | rule: gen|pm=0.2|u=1.1 atc_la at L=40: -0.919% [-1.667, -0.296], inconclusive | negative transfer: gen|pm=0.8|u=1.1 vispool at L=40: +7.816% [+5.701, +10.203], worse


### H3 mechanism: what visibility does to the rolling planner

A known-but-unreleased order enlarges every snapshot the planner solves while the budget stays at 2 s, so `share_saturated` (configurations whose mean replan reaches 95% of the budget) is the diagnostic that decides whether replanning stayed feasible. `d_*` columns are paired against L = 0 on the same configurations.

| scope | level | n_configs | mean_replans | mean_replan_s | median_replan_s | share_saturated | d_replans | d_replan_s | d_replan_s_lo | d_replan_s_hi | mean_wall_s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| emp|ALL | 0 | 144 | 62.7 | 0.447 | 0.107 | 0.056 | 0.000 | 0.000 | 0.000 | 0.000 | 18.8 |
| emp|ALL | 8 | 144 | 75.8 | 0.862 | 0.433 | 0.250 | 13.181 | 0.415 | 0.248 | 0.597 | 49.9 |
| emp|ALL | 40 | 144 | 71.5 | 0.905 | 0.532 | 0.271 | 8.868 | 0.458 | 0.278 | 0.648 | 50.9 |
| emp|ALL | full | 144 | 71.6 | 0.925 | 0.537 | 0.285 | 8.951 | 0.478 | 0.306 | 0.668 | 51.0 |
| emp|m=1.0 | 0 | 48 | 62.2 | 0.371 | 0.049 | 0.042 | 0.000 | 0.000 | 0.000 | 0.000 | 12.3 |
| emp|m=1.0 | 8 | 48 | 75.3 | 0.763 | 0.126 | 0.229 | 13.146 | 0.391 | 0.222 | 0.578 | 40.2 |
| emp|m=1.0 | 40 | 48 | 71.4 | 0.786 | 0.155 | 0.250 | 9.167 | 0.415 | 0.226 | 0.625 | 41.2 |
| emp|m=1.0 | full | 48 | 71.4 | 0.822 | 0.153 | 0.292 | 9.167 | 0.451 | 0.270 | 0.655 | 41.3 |
| emp|m=0.8 | 0 | 48 | 62.6 | 0.424 | 0.094 | 0.062 | 0.000 | 0.000 | 0.000 | 0.000 | 16.6 |
| emp|m=0.8 | 8 | 48 | 75.8 | 0.823 | 0.400 | 0.229 | 13.229 | 0.398 | 0.219 | 0.593 | 46.9 |
| emp|m=0.8 | 40 | 48 | 71.5 | 0.851 | 0.437 | 0.271 | 8.875 | 0.427 | 0.237 | 0.628 | 46.5 |
| emp|m=0.8 | full | 48 | 71.7 | 0.881 | 0.444 | 0.292 | 9.083 | 0.457 | 0.280 | 0.645 | 46.9 |
| emp|m=0.6 | 0 | 48 | 63.2 | 0.545 | 0.262 | 0.062 | 0.000 | 0.000 | 0.000 | 0.000 | 27.4 |
| emp|m=0.6 | 8 | 48 | 76.3 | 1.002 | 0.901 | 0.292 | 13.167 | 0.457 | 0.294 | 0.629 | 62.6 |
| emp|m=0.6 | 40 | 48 | 71.7 | 1.077 | 1.201 | 0.292 | 8.562 | 0.532 | 0.355 | 0.725 | 65.0 |
| emp|m=0.6 | full | 48 | 71.8 | 1.071 | 1.183 | 0.271 | 8.604 | 0.526 | 0.350 | 0.714 | 64.8 |


## 3. The visibility policy family against the frozen v2 pool

At L = 0 both pools run with nothing known early, so a difference is a property of the retrained control and not of visibility; it bounds how far the visibility arms' ABSOLUTE levels may be read against the frozen pool the rest of the paper reports. At the other three levels the same contrast asks whether advance knowledge closes whatever gap the retraining opened.

| scope | level | n_configs | n_clusters | mean_v2 | mean_vis | mean_diff | pct_of_v2 | pct_ci_lo | pct_ci_hi | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| gen|ALL | 0 | 540 | 540 | 2672.7 | 3411.4 | 738.68 | 27.638 | 21.844 | 33.872 | worse |
| gen|u=0.7 | 0 | 180 | 180 | 1996.1 | 2007.0 | 10.87 | 0.545 | 0.346 | 0.782 | equivalent |
| gen|u=0.9 | 0 | 180 | 180 | 2493.3 | 2878.7 | 385.48 | 15.461 | 11.822 | 19.484 | worse |
| gen|u=1.1 | 0 | 180 | 180 | 3528.8 | 5348.5 | 1819.68 | 51.567 | 39.952 | 64.022 | worse |
| gen|pm=0.2|u=0.7 | 0 | 60 | 60 | 3217.0 | 3241.4 | 24.47 | 0.761 | 0.446 | 1.155 | inconclusive |
| gen|pm=0.2|u=0.9 | 0 | 60 | 60 | 3999.9 | 4732.5 | 732.59 | 18.315 | 12.808 | 24.280 | worse |
| gen|pm=0.2|u=1.1 | 0 | 60 | 60 | 6206.1 | 10037.2 | 3831.08 | 61.731 | 46.241 | 78.047 | worse |
| gen|pm=0.5|u=0.7 | 0 | 60 | 60 | 2015.8 | 2022.4 | 6.53 | 0.324 | 0.139 | 0.562 | equivalent |
| gen|pm=0.5|u=0.9 | 0 | 60 | 60 | 2487.5 | 2755.1 | 267.61 | 10.758 | 6.728 | 15.247 | worse |
| gen|pm=0.5|u=1.1 | 0 | 60 | 60 | 3099.5 | 4069.3 | 969.75 | 31.287 | 18.426 | 44.749 | worse |
| gen|pm=0.8|u=0.7 | 0 | 60 | 60 | 755.6 | 757.2 | 1.62 | 0.215 | -0.066 | 0.499 | equivalent |
| gen|pm=0.8|u=0.9 | 0 | 60 | 60 | 992.3 | 1148.6 | 156.24 | 15.745 | 8.816 | 23.546 | worse |
| gen|pm=0.8|u=1.1 | 0 | 60 | 60 | 1280.7 | 1938.9 | 658.21 | 51.393 | 29.671 | 74.752 | worse |
| emp|ALL | 0 | 540 | 180 | 447.5 | 448.8 | 1.26 | 0.281 | 0.106 | 0.506 | equivalent |
| emp|m=1.0 | 0 | 180 | 180 | 444.8 | 445.0 | 0.25 | 0.055 | 0.012 | 0.110 | equivalent |
| emp|m=0.8 | 0 | 180 | 180 | 446.5 | 447.0 | 0.54 | 0.122 | 0.046 | 0.218 | equivalent |
| emp|m=0.6 | 0 | 180 | 180 | 451.3 | 454.3 | 2.98 | 0.660 | 0.248 | 1.221 | inconclusive |
| gen|ALL | 8 | 540 | 540 | 2672.7 | 3455.6 | 782.84 | 29.290 | 23.477 | 35.517 | worse |
| gen|u=0.7 | 8 | 180 | 180 | 1996.1 | 2007.8 | 11.69 | 0.586 | 0.387 | 0.805 | equivalent |
| gen|u=0.9 | 8 | 180 | 180 | 2493.3 | 2902.3 | 408.99 | 16.404 | 12.679 | 20.536 | worse |
| gen|u=1.1 | 8 | 180 | 180 | 3528.8 | 5456.6 | 1927.85 | 54.632 | 42.837 | 66.911 | worse |
| gen|pm=0.2|u=0.7 | 8 | 60 | 60 | 3217.0 | 3240.7 | 23.69 | 0.736 | 0.451 | 1.063 | inconclusive |
| gen|pm=0.2|u=0.9 | 8 | 60 | 60 | 3999.9 | 4712.2 | 712.30 | 17.808 | 12.317 | 24.005 | worse |
| gen|pm=0.2|u=1.1 | 8 | 60 | 60 | 6206.1 | 10002.6 | 3796.49 | 61.173 | 45.555 | 77.616 | worse |
| gen|pm=0.5|u=0.7 | 8 | 60 | 60 | 2015.8 | 2023.5 | 7.62 | 0.378 | 0.146 | 0.694 | equivalent |
| gen|pm=0.5|u=0.9 | 8 | 60 | 60 | 2487.5 | 2804.7 | 317.19 | 12.751 | 8.138 | 17.748 | worse |
| gen|pm=0.5|u=1.1 | 8 | 60 | 60 | 3099.5 | 4292.8 | 1193.26 | 38.498 | 25.153 | 53.174 | worse |
| gen|pm=0.8|u=0.7 | 8 | 60 | 60 | 755.6 | 759.4 | 3.76 | 0.497 | 0.123 | 0.935 | equivalent |
| gen|pm=0.8|u=0.9 | 8 | 60 | 60 | 992.3 | 1189.8 | 197.48 | 19.901 | 11.516 | 29.298 | worse |
| gen|pm=0.8|u=1.1 | 8 | 60 | 60 | 1280.7 | 2074.5 | 793.81 | 61.981 | 38.161 | 87.297 | worse |
| emp|ALL | 8 | 540 | 180 | 447.5 | 448.9 | 1.41 | 0.314 | 0.115 | 0.571 | equivalent |
| emp|m=1.0 | 8 | 180 | 180 | 444.8 | 445.0 | 0.22 | 0.048 | 0.013 | 0.095 | equivalent |
| emp|m=0.8 | 8 | 180 | 180 | 446.5 | 447.1 | 0.64 | 0.144 | 0.068 | 0.236 | equivalent |
| emp|m=0.6 | 8 | 180 | 180 | 451.3 | 454.7 | 3.36 | 0.745 | 0.242 | 1.435 | inconclusive |
| gen|ALL | 40 | 540 | 540 | 2672.7 | 3346.8 | 674.12 | 25.222 | 20.850 | 29.768 | worse |
| gen|u=0.7 | 40 | 180 | 180 | 1996.1 | 2007.2 | 11.10 | 0.556 | 0.364 | 0.764 | equivalent |
| gen|u=0.9 | 40 | 180 | 180 | 2493.3 | 2892.9 | 399.64 | 16.029 | 12.667 | 19.747 | worse |
| gen|u=1.1 | 40 | 180 | 180 | 3528.8 | 5140.4 | 1611.61 | 45.670 | 37.124 | 54.393 | worse |
| gen|pm=0.2|u=0.7 | 40 | 60 | 60 | 3217.0 | 3239.5 | 22.49 | 0.699 | 0.429 | 0.999 | equivalent |
| gen|pm=0.2|u=0.9 | 40 | 60 | 60 | 3999.9 | 4669.2 | 669.28 | 16.732 | 11.950 | 21.939 | worse |
| gen|pm=0.2|u=1.1 | 40 | 60 | 60 | 6206.1 | 9018.9 | 2812.79 | 45.323 | 35.223 | 55.853 | worse |
| gen|pm=0.5|u=0.7 | 40 | 60 | 60 | 2015.8 | 2023.3 | 7.48 | 0.371 | 0.144 | 0.676 | equivalent |
| gen|pm=0.5|u=0.9 | 40 | 60 | 60 | 2487.5 | 2813.8 | 326.24 | 13.115 | 8.441 | 18.211 | worse |
| gen|pm=0.5|u=1.1 | 40 | 60 | 60 | 3099.5 | 4311.8 | 1212.29 | 39.112 | 25.932 | 53.733 | worse |
| gen|pm=0.8|u=0.7 | 40 | 60 | 60 | 755.6 | 758.9 | 3.33 | 0.441 | 0.050 | 0.910 | equivalent |
| gen|pm=0.8|u=0.9 | 40 | 60 | 60 | 992.3 | 1195.7 | 203.40 | 20.497 | 11.969 | 30.103 | worse |
| gen|pm=0.8|u=1.1 | 40 | 60 | 60 | 1280.7 | 2090.5 | 809.75 | 63.226 | 38.989 | 89.393 | worse |
| emp|ALL | 40 | 540 | 180 | 447.5 | 448.7 | 1.18 | 0.264 | 0.110 | 0.458 | equivalent |
| emp|m=1.0 | 40 | 180 | 180 | 444.8 | 445.0 | 0.20 | 0.045 | 0.010 | 0.092 | equivalent |
| emp|m=0.8 | 40 | 180 | 180 | 446.5 | 447.1 | 0.59 | 0.131 | 0.060 | 0.215 | equivalent |
| emp|m=0.6 | 40 | 180 | 180 | 451.3 | 454.1 | 2.75 | 0.610 | 0.246 | 1.099 | inconclusive |
| gen|ALL | full | 540 | 540 | 2672.7 | 3351.4 | 678.62 | 25.391 | 20.954 | 30.085 | worse |
| gen|u=0.7 | full | 180 | 180 | 1996.1 | 2007.4 | 11.28 | 0.565 | 0.376 | 0.778 | equivalent |
| gen|u=0.9 | full | 180 | 180 | 2493.3 | 2894.5 | 401.29 | 16.095 | 12.692 | 19.762 | worse |
| gen|u=1.1 | full | 180 | 180 | 3528.8 | 5152.1 | 1623.31 | 46.002 | 37.418 | 54.625 | worse |
| gen|pm=0.2|u=0.7 | full | 60 | 60 | 3217.0 | 3239.8 | 22.86 | 0.711 | 0.434 | 1.015 | inconclusive |
| gen|pm=0.2|u=0.9 | full | 60 | 60 | 3999.9 | 4673.8 | 673.85 | 16.847 | 11.986 | 21.989 | worse |
| gen|pm=0.2|u=1.1 | full | 60 | 60 | 6206.1 | 9054.2 | 2848.06 | 45.891 | 35.538 | 56.416 | worse |
| gen|pm=0.5|u=0.7 | full | 60 | 60 | 2015.8 | 2023.5 | 7.68 | 0.381 | 0.152 | 0.696 | equivalent |
| gen|pm=0.5|u=0.9 | full | 60 | 60 | 2487.5 | 2814.1 | 326.56 | 13.128 | 8.432 | 18.180 | worse |
| gen|pm=0.5|u=1.1 | full | 60 | 60 | 3099.5 | 4312.0 | 1212.48 | 39.118 | 25.526 | 53.726 | worse |
| gen|pm=0.8|u=0.7 | full | 60 | 60 | 755.6 | 758.9 | 3.29 | 0.435 | 0.040 | 0.912 | equivalent |
| gen|pm=0.8|u=0.9 | full | 60 | 60 | 992.3 | 1195.8 | 203.44 | 20.501 | 11.895 | 30.185 | worse |
| gen|pm=0.8|u=1.1 | full | 60 | 60 | 1280.7 | 2090.1 | 809.39 | 63.197 | 38.927 | 89.306 | worse |
| emp|ALL | full | 540 | 180 | 447.5 | 448.9 | 1.40 | 0.312 | 0.135 | 0.536 | equivalent |
| emp|m=1.0 | full | 180 | 180 | 444.8 | 445.0 | 0.24 | 0.055 | 0.012 | 0.113 | equivalent |
| emp|m=0.8 | full | 180 | 180 | 446.5 | 447.2 | 0.70 | 0.157 | 0.067 | 0.269 | equivalent |
| emp|m=0.6 | full | 180 | 180 | 451.3 | 454.6 | 3.24 | 0.719 | 0.303 | 1.277 | inconclusive |


## 4. The win region and the negative-transfer region

Read the win region against section 3 before quoting it. The gain is measured inside the visibility family, and in this cell that family starts 62% above the frozen v2 pool at L = 0 and is still 45% above it at L = 40 (9019 against 6206 weighted units). Advance knowledge is therefore worth a measured amount to a policy trained to use it, and it does not make that policy the best available option on these giant generator cells.


`n_seeds_improved` counts the five seed-level contrasts with a negative mean difference and `n_seeds_better` the ones whose whole interval clears the margin on the better side. A pool effect one seed carries and a pool effect five seeds agree on are different findings, so both counts are reported with the pool number.

| region | arm | level | n_configs | mean_control | mean_diff | pct_of_control | pct_ci_lo | pct_ci_hi | verdict | n_seeds_improved | n_seeds_better | n_seeds_worse | seed_pct_min | seed_pct_max |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| win | vispool | 8 | 120 | 7384.8 | -27.44 | -0.37 | -1.228 | 0.431 | inconclusive | 3 | 2 | 2 | -38.96 | 47.92 |
| win | atc_la | 8 | 120 | 4672.4 | -11.68 | -0.25 | -0.471 | -0.067 | equivalent | 3 | 2 | 2 | -38.96 | 47.92 |
| win | vispool | 40 | 120 | 7384.8 | -540.80 | -7.32 | -10.818 | -4.115 | better | 4 | 2 | 1 | -38.98 | 8.21 |
| win | atc_la | 40 | 120 | 4672.4 | -26.90 | -0.58 | -1.027 | -0.195 | inconclusive | 4 | 2 | 1 | -38.98 | 8.21 |
| win | vispool | full | 120 | 7384.8 | -520.88 | -7.05 | -10.386 | -3.936 | better | 4 | 2 | 1 | -38.64 | 8.21 |
| win | atc_la | full | 120 | 4672.4 | -26.90 | -0.58 | -1.022 | -0.205 | inconclusive | 4 | 2 | 1 | -38.64 | 8.21 |
| winpeak | vispool | 8 | 60 | 10037.2 | -34.59 | -0.34 | -1.413 | 0.626 | inconclusive | 3 | 1 | 2 | -51.07 | 76.90 |
| winpeak | atc_la | 8 | 60 | 5393.1 | -20.19 | -0.37 | -0.743 | -0.068 | equivalent | 3 | 1 | 2 | -51.07 | 76.90 |
| winpeak | vispool | 40 | 60 | 10037.2 | -1018.29 | -10.15 | -14.929 | -5.666 | better | 4 | 2 | 1 | -51.08 | 9.62 |
| winpeak | atc_la | 40 | 60 | 5393.1 | -49.57 | -0.92 | -1.678 | -0.293 | inconclusive | 4 | 2 | 1 | -51.08 | 9.62 |
| winpeak | vispool | full | 60 | 10037.2 | -983.02 | -9.79 | -14.392 | -5.576 | better | 4 | 2 | 1 | -50.68 | 9.62 |
| winpeak | atc_la | full | 60 | 5393.1 | -49.57 | -0.92 | -1.661 | -0.284 | inconclusive | 4 | 2 | 1 | -50.68 | 9.62 |
| negative | vispool | 8 | 360 | 2115.3 | 75.53 | 3.57 | 2.925 | 4.270 | worse | 2 | 0 | 2 | -0.22 | 9.60 |
| negative | atc_la | 8 | 360 | 1749.5 | 0.07 | 0.00 | -0.025 | 0.035 | equivalent | 2 | 0 | 2 | -0.22 | 9.60 |
| negative | vispool | 40 | 360 | 2115.3 | 83.76 | 3.96 | 3.238 | 4.723 | worse | 2 | 0 | 2 | -0.11 | 9.81 |
| negative | atc_la | 40 | 360 | 1749.5 | 0.45 | 0.03 | -0.021 | 0.079 | equivalent | 2 | 0 | 2 | -0.11 | 9.81 |
| negative | vispool | full | 360 | 2115.3 | 83.81 | 3.96 | 3.266 | 4.721 | worse | 2 | 0 | 2 | -0.12 | 9.81 |
| negative | atc_la | full | 360 | 1749.5 | 0.45 | 0.03 | -0.023 | 0.078 | equivalent | 2 | 0 | 2 | -0.12 | 9.81 |
| negativepeak | vispool | 8 | 60 | 1938.9 | 135.60 | 6.99 | 4.993 | 9.176 | worse | 2 | 0 | 2 | -0.34 | 12.96 |
| negativepeak | atc_la | 8 | 60 | 1247.7 | 0.49 | 0.04 | -0.061 | 0.167 | equivalent | 2 | 0 | 2 | -0.34 | 12.96 |
| negativepeak | vispool | 40 | 60 | 1938.9 | 151.55 | 7.82 | 5.687 | 10.182 | worse | 2 | 0 | 2 | -0.05 | 13.11 |
| negativepeak | atc_la | 40 | 60 | 1247.7 | 0.09 | 0.01 | -0.142 | 0.150 | equivalent | 2 | 0 | 2 | -0.05 | 13.11 |
| negativepeak | vispool | full | 60 | 1938.9 | 151.18 | 7.80 | 5.696 | 10.104 | worse | 1 | 0 | 2 | -0.12 | 13.11 |
| negativepeak | atc_la | full | 60 | 1247.7 | 0.09 | 0.01 | -0.143 | 0.153 | equivalent | 1 | 0 | 2 | -0.12 | 13.11 |


Per seed, in the same regions:

| region | arm | level | n_configs | mean_control | mean_diff | pct_of_control | pct_ci_lo | pct_ci_hi | verdict |
|---|---|---|---|---|---|---|---|---|---|
| win | visseed501 | 8 | 120 | 4818.3 | 2309.05 | 47.92 | 26.298 | 71.973 | worse |
| win | visseed502 | 8 | 120 | 4603.4 | -57.58 | -1.25 | -2.124 | -0.479 | inconclusive |
| win | visseed503 | 8 | 120 | 7458.3 | -2905.99 | -38.96 | -57.232 | -23.035 | better |
| win | visseed504 | 8 | 120 | 10275.6 | -289.75 | -2.82 | -4.748 | -1.040 | better |
| win | visseed505 | 8 | 120 | 9768.6 | 807.06 | 8.26 | 6.365 | 10.290 | worse |
| win | visseed501 | 40 | 120 | 4818.3 | -239.54 | -4.97 | -7.254 | -2.999 | better |
| win | visseed502 | 40 | 120 | 4603.4 | -66.04 | -1.43 | -2.264 | -0.754 | inconclusive |
| win | visseed503 | 40 | 120 | 7458.3 | -2907.59 | -38.98 | -56.580 | -23.107 | better |
| win | visseed504 | 40 | 120 | 10275.6 | -292.36 | -2.85 | -5.072 | -0.874 | inconclusive |
| win | visseed505 | 40 | 120 | 9768.6 | 801.55 | 8.21 | 6.390 | 10.049 | worse |
| win | visseed501 | full | 120 | 4818.3 | -188.21 | -3.91 | -5.911 | -2.150 | better |
| win | visseed502 | full | 120 | 4603.4 | -43.84 | -0.95 | -1.603 | -0.397 | inconclusive |
| win | visseed503 | full | 120 | 7458.3 | -2881.55 | -38.64 | -56.413 | -23.115 | better |
| win | visseed504 | full | 120 | 10275.6 | -292.36 | -2.85 | -5.091 | -0.857 | inconclusive |
| win | visseed505 | full | 120 | 9768.6 | 801.55 | 8.21 | 6.412 | 10.163 | worse |
| winpeak | visseed501 | 8 | 60 | 5692.8 | 4377.70 | 76.90 | 42.149 | 115.521 | worse |
| winpeak | visseed502 | 8 | 60 | 5271.0 | -95.82 | -1.82 | -3.278 | -0.520 | inconclusive |
| winpeak | visseed503 | 8 | 60 | 10602.0 | -5414.42 | -51.07 | -74.357 | -30.237 | better |
| winpeak | visseed504 | 8 | 60 | 15197.4 | -370.69 | -2.44 | -4.934 | -0.108 | inconclusive |
| winpeak | visseed505 | 8 | 60 | 13422.8 | 1330.27 | 9.91 | 7.696 | 12.147 | worse |
| winpeak | visseed501 | 40 | 60 | 5692.8 | -459.63 | -8.07 | -11.661 | -4.909 | better |
| winpeak | visseed502 | 40 | 60 | 5271.0 | -110.92 | -2.10 | -3.448 | -0.983 | inconclusive |
| winpeak | visseed503 | 40 | 60 | 10602.0 | -5415.43 | -51.08 | -74.291 | -30.162 | better |
| winpeak | visseed504 | 40 | 60 | 15197.4 | -396.30 | -2.61 | -5.452 | -0.091 | inconclusive |
| winpeak | visseed505 | 40 | 60 | 13422.8 | 1290.85 | 9.62 | 7.544 | 11.694 | worse |
| winpeak | visseed501 | full | 60 | 5692.8 | -369.59 | -6.49 | -9.513 | -3.729 | better |
| winpeak | visseed502 | full | 60 | 5271.0 | -66.86 | -1.27 | -2.355 | -0.360 | inconclusive |
| winpeak | visseed503 | full | 60 | 10602.0 | -5373.21 | -50.68 | -74.156 | -30.568 | better |
| winpeak | visseed504 | full | 60 | 15197.4 | -396.30 | -2.61 | -5.451 | -0.049 | inconclusive |
| winpeak | visseed505 | full | 60 | 13422.8 | 1290.85 | 9.62 | 7.598 | 11.726 | worse |
| negative | visseed501 | 8 | 360 | 1750.7 | 6.93 | 0.40 | 0.232 | 0.632 | equivalent |
| negative | visseed502 | 8 | 360 | 1753.2 | -2.03 | -0.12 | -0.214 | -0.017 | equivalent |
| negative | visseed503 | 8 | 360 | 1752.9 | -3.91 | -0.22 | -0.435 | -0.081 | equivalent |
| negative | visseed504 | 8 | 360 | 1781.7 | 36.99 | 2.08 | 1.002 | 3.732 | worse |
| negative | visseed505 | 8 | 360 | 3537.7 | 339.65 | 9.60 | 7.816 | 11.518 | worse |
| negative | visseed501 | 40 | 360 | 1750.7 | 2.60 | 0.15 | 0.069 | 0.238 | equivalent |
| negative | visseed502 | 40 | 360 | 1753.2 | -1.63 | -0.09 | -0.171 | -0.019 | equivalent |
| negative | visseed503 | 40 | 360 | 1752.9 | -1.96 | -0.11 | -0.312 | 0.025 | equivalent |
| negative | visseed504 | 40 | 360 | 1781.7 | 72.61 | 4.08 | 2.398 | 6.368 | worse |
| negative | visseed505 | 40 | 360 | 3537.7 | 347.17 | 9.81 | 7.921 | 11.807 | worse |
| negative | visseed501 | full | 360 | 1750.7 | 2.26 | 0.13 | 0.069 | 0.192 | equivalent |
| negative | visseed502 | full | 360 | 1753.2 | -0.85 | -0.05 | -0.110 | 0.014 | equivalent |
| negative | visseed503 | full | 360 | 1752.9 | -2.12 | -0.12 | -0.324 | 0.016 | equivalent |
| negative | visseed504 | full | 360 | 1781.7 | 72.61 | 4.08 | 2.449 | 6.273 | worse |
| negative | visseed505 | full | 360 | 3537.7 | 347.17 | 9.81 | 7.912 | 11.842 | worse |
| negativepeak | visseed501 | 8 | 60 | 1252.1 | 8.05 | 0.64 | 0.240 | 1.157 | inconclusive |
| negativepeak | visseed502 | 8 | 60 | 1253.6 | -3.35 | -0.27 | -0.605 | 0.018 | equivalent |
| negativepeak | visseed503 | 8 | 60 | 1253.0 | -4.23 | -0.34 | -0.733 | -0.000 | equivalent |
| negativepeak | visseed504 | 8 | 60 | 1270.3 | 72.82 | 5.73 | 3.132 | 8.585 | worse |
| negativepeak | visseed505 | 8 | 60 | 4665.7 | 604.73 | 12.96 | 8.826 | 17.540 | worse |
| negativepeak | visseed501 | 40 | 60 | 1252.1 | 4.64 | 0.37 | -0.026 | 0.896 | equivalent |
| negativepeak | visseed502 | 40 | 60 | 1253.6 | -0.04 | -0.00 | -0.222 | 0.214 | equivalent |
| negativepeak | visseed503 | 40 | 60 | 1253.0 | -0.66 | -0.05 | -0.271 | 0.169 | equivalent |
| negativepeak | visseed504 | 40 | 60 | 1270.3 | 142.34 | 11.20 | 6.236 | 16.826 | worse |
| negativepeak | visseed505 | 40 | 60 | 4665.7 | 611.46 | 13.11 | 8.648 | 18.131 | worse |
| negativepeak | visseed501 | full | 60 | 1252.1 | 3.46 | 0.28 | 0.031 | 0.542 | equivalent |
| negativepeak | visseed502 | full | 60 | 1253.6 | 0.17 | 0.01 | -0.216 | 0.234 | equivalent |
| negativepeak | visseed503 | full | 60 | 1253.0 | -1.53 | -0.12 | -0.347 | 0.106 | equivalent |
| negativepeak | visseed504 | full | 60 | 1270.3 | 142.34 | 11.20 | 6.238 | 16.918 | worse |
| negativepeak | visseed505 | full | 60 | 4665.7 | 611.46 | 13.11 | 8.675 | 18.009 | worse |


## 5. Sanity checks

| check | got | want | ok |
|---|---|---|---|
| rows vs meta.json | 50256 | 50256 | True |
| configurations vs meta.json | 1080 | 1080 | True |
| infeasible vs meta.json | 0 | 0 | True |
| errors vs meta.json | 0 | 0 | True |
| levels | 4 | 4 | True |
| evaluated ids = configurations x levels | 4320 | 4320 | True |
| vis-gen configurations vs meta.json | 540 | 540 | True |
| vis-empirical configurations vs meta.json | 540 | 540 | True |
| visibility arms missing (meta.json) | 0 | 0 | True |
| every (method, level) covers its designed configurations | 0 | 0 | True |
| methods scored | 35 | 35 | True |
| rolling configurations vs meta.json | 144 | 144 | True |
| rolling runs on the empirical cells only | ['vis-empirical'] | ['vis-empirical'] | True |
| base_id equals the library's cluster derivation from id | True | True | True |
| cluster derived from the pairing key equals base_id | True | True | True |
| every configuration carries every level | 4 | 4 | True |
| clusters | 720 | 720 | True |
| constant-by-construction methods | ['atc', 'edd', 'wmdd'] | ['atc', 'edd', 'wmdd'] | True |
| constant rules are identical at every level (max spread) | 0.000 | 0.000 | True |
| no constant-by-construction row enters a paired L-effect | 0 | 0 | True |
| generator cells | 9 | 9 | True |
| generator configurations per cell | [60] | [60] | True |
| generator campuses | [5, 9, 10, 12] | [5, 9, 10, 12] | True |
| empirical crew multipliers | [0.6, 0.8, 1.0] | [0.6, 0.8, 1.0] | True |
| empirical base instances per crew multiplier | [180] | [180] | True |
| empirical campuses | [5, 9, 10, 12] | [5, 9, 10, 12] | True |
| no missing objective value | 0 | 0 | True |
| visibility seeds at L=0 | [501, 502, 503, 504, 505] | [501, 502, 503, 504, 505] | True |
| visibility seeds at L=8 | [501, 502, 503, 504, 505] | [501, 502, 503, 504, 505] | True |
| visibility seeds at L=40 | [501, 502, 503, 504, 505] | [501, 502, 503, 504, 505] | True |
| visibility seeds at L=full | [501, 502, 503, 504, 505] | [501, 502, 503, 504, 505] | True |
