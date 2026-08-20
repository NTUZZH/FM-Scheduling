# R4 statistics — results.csv

Source: `results/r4_final/results.csv` (26770 rows, 0 infeasible excluded). Value column: `wwt`. Methods: atc, edd, lpt, pfifo, random, wmdd, wspt, rollcp2, v2rl301, v2rl302, v2rl303, v2rl304, v2rl305, v2rl306, v2rl307, v2rl308, v2rl309, v2rl310. References: edd, atc, wmdd.

Paired on instance-configuration id; clusters = base instances (527 clusters over 887 configurations). 95% percentile cluster bootstrap, 10000 resamples, seed 12345. Equivalence margin = max(1.0, 1% of the reference mean). Holm correction within each comparison family (rule-vs-rule, policy-vs-rule, ...). A negative difference means the method is BETTER than its reference.

## Mean wwt per method (pooled)

| method | n | mean | in equivalence set |
|---|---|---|---|
| rollcp2 | 160 | 510.409 | best |
| v2rl310 | 887 | 1425.733 | no |
| pfifo | 887 | 1428.030 | no |
| edd | 887 | 1428.096 | no |
| v2rl304 | 887 | 1428.317 | no |
| v2rl308 | 887 | 1429.436 | no |
| wmdd | 887 | 1434.314 | yes |
| atc | 887 | 1436.440 | no |
| v2rl305 | 887 | 1440.477 | no |
| v2rl302 | 887 | 1443.636 | no |
| v2rl307 | 887 | 1451.105 | no |
| v2rl306 | 887 | 1457.730 | no |
| v2rl301 | 887 | 1462.622 | no |
| v2rl309 | 887 | 1629.252 | no |
| v2rl303 | 887 | 1662.129 | no |
| wspt | 887 | 1678.371 | no |
| random | 887 | 4790.174 | no |
| lpt | 887 | 14898.354 | no |

## Equivalence sets

### scope_type = overall

| scope | best | mean(best) | equivalent to best | n_clusters |
|---|---|---|---|---|
| ALL | rollcp2 | 510.409 | wmdd | 64 |

Partial coverage (mean ranks over fewer configurations than the fullest method; read the paired comparison, not the rank): rollcp2 18%.

### scope_type = scope

| scope | best | mean(best) | equivalent to best | n_clusters |
|---|---|---|---|---|
| regime=final-empirical|crew_multiplier=0.6 | v2rl302 | 450.246 | edd, pfifo, rollcp2, v2rl301, v2rl303, v2rl304, v2rl305, v2rl307, v2rl308, v2rl310 | 180 |
| regime=final-empirical|crew_multiplier=0.8 | v2rl301 | 446.287 | atc, edd, pfifo, rollcp2, v2rl302, v2rl303, v2rl304, v2rl305, v2rl306, v2rl307, v2rl308, v2rl309, v2rl310, wmdd | 180 |
| regime=final-empirical|crew_multiplier=1.0 | wmdd | 454.988 | (none) | 227 |
| regime=final-gen|crew_multiplier=1.0 | v2rl310 | 3327.425 | edd, pfifo, v2rl304, v2rl308 | 300 |

Partial coverage (mean ranks over fewer configurations than the fullest method; read the paired comparison, not the rank): rollcp2 27%.

### scope_type = u_bin

| scope | best | mean(best) | equivalent to best | n_clusters |
|---|---|---|---|---|
| u_bin=0.5-0.8 | rollcp2 | 789.317 | edd, pfifo, v2rl301, v2rl302, v2rl303, v2rl304, v2rl305, v2rl306, v2rl307, v2rl308, v2rl309, v2rl310, wmdd | 31 |
| u_bin=0.8-1.0 | rollcp2 | 836.575 | edd, pfifo, v2rl301, v2rl302, v2rl303, v2rl304, v2rl305, v2rl306, v2rl307, v2rl308, v2rl310 | 15 |
| u_bin=1.0-1.2 | rollcp2 | 631.892 | v2rl308 | 8 |
| u_bin=<0.5 | v2rl302 | 234.571 | atc, edd, lpt, pfifo, random, rollcp2, v2rl301, v2rl303, v2rl304, v2rl305, v2rl306, v2rl307, v2rl308, v2rl309, v2rl310, wmdd | 100 |
| u_bin=>=1.2 | rollcp2 | 264.219 | (none) | 16 |

Partial coverage (mean ranks over fewer configurations than the fullest method; read the paired comparison, not the rank): rollcp2 6%.

## Paired comparisons vs each reference

### scope_type = overall

| scope | reference | method | n | clusters | mean diff | 95% CI | margin | Wilcoxon p | Holm p | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| ALL | atc | v2rl310 | 887 | 527 | -10.707 | [-16.405, -5.311] | 14.364 | 8.3e-14 | 2.0e-12 | inconclusive |
| ALL | atc | pfifo | 887 | 527 | -8.411 | [-14.400, -2.031] | 14.364 | 6.1e-20 | 5.5e-19 | inconclusive |
| ALL | atc | edd | 887 | 527 | -8.344 | [-14.179, -1.882] | 14.364 | 7.4e-20 | 5.9e-19 | equivalent |
| ALL | atc | v2rl304 | 887 | 527 | -8.123 | [-14.735, -0.529] | 14.364 | 2.3e-12 | 5.4e-11 | inconclusive |
| ALL | atc | v2rl308 | 887 | 527 | -7.004 | [-15.061, 2.440] | 14.364 | 9.7e-11 | 2.0e-09 | inconclusive |
| ALL | atc | rollcp2 | 160 | 64 | -3.454 | [-8.231, 0.421] | 5.139 | 0.0316 | 0.0316 | inconclusive |
| ALL | atc | wmdd | 887 | 527 | -2.126 | [-3.905, -0.449] | 14.364 | 3.2e-05 | 9.5e-05 | equivalent |
| ALL | atc | v2rl305 | 887 | 527 | +4.037 | [-6.548, 16.395] | 14.364 | 2.6e-09 | 4.9e-08 | inconclusive |
| ALL | atc | v2rl302 | 887 | 527 | +7.196 | [-2.578, 18.810] | 14.364 | 4.0e-06 | 6.0e-05 | inconclusive |
| ALL | atc | v2rl307 | 887 | 527 | +14.665 | [1.576, 30.821] | 14.364 | 1.1e-06 | 1.8e-05 | inconclusive |
| ALL | atc | v2rl306 | 887 | 527 | +21.289 | [5.826, 40.101] | 14.364 | 0.0019 | 0.0188 | inconclusive |
| ALL | atc | v2rl301 | 887 | 527 | +26.182 | [9.773, 45.484] | 14.364 | 0.0009 | 0.0100 | inconclusive |
| ALL | atc | v2rl309 | 887 | 527 | +192.812 | [140.567, 254.163] | 14.364 | 4.0e-23 | 1.1e-21 | worse |
| ALL | atc | v2rl303 | 887 | 527 | +225.689 | [167.018, 294.740] | 14.364 | 8.4e-17 | 2.1e-15 | worse |
| ALL | atc | wspt | 887 | 527 | +241.931 | [196.590, 291.123] | 14.364 | 2.2e-66 | 4.0e-65 | worse |
| ALL | atc | random | 887 | 527 | +3353.734 | [2676.448, 4090.010] | 14.364 | 7.4e-62 | 1.0e-60 | worse |
| ALL | atc | lpt | 887 | 527 | +13461.913 | [11087.575, 16220.260] | 14.364 | 8.5e-60 | 9.4e-59 | worse |
| ALL | edd | rollcp2 | 160 | 64 | -5.536 | [-16.359, 1.363] | 5.159 | 0.0005 | 0.0015 | inconclusive |
| ALL | edd | v2rl310 | 887 | 527 | -2.363 | [-6.887, 2.118] | 14.281 | 5.0e-05 | 0.0007 | equivalent |
| ALL | edd | pfifo | 887 | 527 | -0.066 | [-0.211, 0.008] | 14.281 | 0.6858 | 0.6858 | equivalent |
| ALL | edd | v2rl304 | 887 | 527 | +0.221 | [-3.431, 5.033] | 14.281 | 0.0621 | 0.3107 | equivalent |
| ALL | edd | v2rl308 | 887 | 527 | +1.340 | [-4.215, 8.769] | 14.281 | 0.0102 | 0.0920 | equivalent |
| ALL | edd | wmdd | 887 | 527 | +6.218 | [-0.155, 11.966] | 14.281 | 1.2e-18 | 6.2e-18 | equivalent |
| ALL | edd | atc | 887 | 527 | +8.344 | [1.987, 14.207] | 14.281 | 7.4e-20 | 5.9e-19 | equivalent |
| ALL | edd | v2rl305 | 887 | 527 | +12.381 | [3.821, 22.716] | 14.281 | 0.0288 | 0.2017 | inconclusive |
| ALL | edd | v2rl302 | 887 | 527 | +15.540 | [4.496, 28.719] | 14.281 | 0.2778 | 0.8333 | inconclusive |
| ALL | edd | v2rl307 | 887 | 527 | +23.009 | [12.145, 35.816] | 14.281 | 0.7338 | 0.8333 | inconclusive |
| ALL | edd | v2rl306 | 887 | 527 | +29.633 | [15.598, 46.401] | 14.281 | 0.2885 | 0.8333 | worse |
| ALL | edd | v2rl301 | 887 | 527 | +34.526 | [17.041, 55.687] | 14.281 | 0.1697 | 0.6788 | worse |
| ALL | edd | v2rl309 | 887 | 527 | +201.156 | [146.807, 264.036] | 14.281 | 1.8e-36 | 5.3e-35 | worse |
| ALL | edd | v2rl303 | 887 | 527 | +234.033 | [173.002, 307.901] | 14.281 | 1.3e-28 | 3.9e-27 | worse |
| ALL | edd | wspt | 887 | 527 | +250.275 | [202.126, 302.221] | 14.281 | 8.9e-65 | 1.4e-63 | worse |
| ALL | edd | random | 887 | 527 | +3362.078 | [2694.946, 4086.583] | 14.281 | 6.1e-63 | 9.2e-62 | worse |
| ALL | edd | lpt | 887 | 527 | +13470.258 | [11058.491, 16156.794] | 14.281 | 2.6e-60 | 3.1e-59 | worse |
| ALL | wmdd | v2rl310 | 887 | 527 | -8.581 | [-14.217, -2.979] | 14.343 | 6.8e-11 | 1.5e-09 | equivalent |
| ALL | wmdd | pfifo | 887 | 527 | -6.285 | [-12.004, 0.202] | 14.343 | 6.7e-19 | 4.0e-18 | equivalent |
| ALL | wmdd | edd | 887 | 527 | -6.218 | [-11.900, 0.266] | 14.343 | 1.2e-18 | 6.2e-18 | equivalent |
| ALL | wmdd | v2rl304 | 887 | 527 | -5.998 | [-12.518, 1.638] | 14.343 | 1.1e-09 | 2.3e-08 | equivalent |
| ALL | wmdd | v2rl308 | 887 | 527 | -4.878 | [-12.773, 5.097] | 14.343 | 5.6e-08 | 1.0e-06 | equivalent |
| ALL | wmdd | rollcp2 | 160 | 64 | -1.526 | [-4.298, 1.133] | 5.119 | 0.0054 | 0.0108 | equivalent |
| ALL | wmdd | atc | 887 | 527 | +2.126 | [0.444, 3.965] | 14.343 | 3.2e-05 | 9.5e-05 | equivalent |
| ALL | wmdd | v2rl305 | 887 | 527 | +6.163 | [-4.423, 18.876] | 14.343 | 6.4e-07 | 1.1e-05 | inconclusive |
| ALL | wmdd | v2rl302 | 887 | 527 | +9.322 | [-0.756, 21.403] | 14.343 | 0.0005 | 0.0066 | inconclusive |
| ALL | wmdd | v2rl307 | 887 | 527 | +16.791 | [3.321, 32.972] | 14.343 | 9.8e-05 | 0.0013 | inconclusive |
| ALL | wmdd | v2rl306 | 887 | 527 | +23.415 | [7.501, 42.996] | 14.343 | 0.0300 | 0.2017 | inconclusive |
| ALL | wmdd | v2rl301 | 887 | 527 | +28.308 | [10.940, 48.958] | 14.343 | 0.0218 | 0.1747 | inconclusive |
| ALL | wmdd | v2rl309 | 887 | 527 | +194.938 | [141.962, 256.339] | 14.343 | 1.8e-25 | 5.0e-24 | worse |
| ALL | wmdd | v2rl303 | 887 | 527 | +227.815 | [166.431, 296.995] | 14.343 | 9.7e-19 | 2.5e-17 | worse |
| ALL | wmdd | wspt | 887 | 527 | +244.057 | [198.179, 295.286] | 14.343 | 5.2e-66 | 8.9e-65 | worse |
| ALL | wmdd | random | 887 | 527 | +3355.860 | [2673.183, 4114.914] | 14.343 | 1.3e-61 | 1.6e-60 | worse |
| ALL | wmdd | lpt | 887 | 527 | +13464.039 | [11033.051, 16101.665] | 14.343 | 1.2e-59 | 1.2e-58 | worse |

### scope_type = scope

| scope | reference | method | n | clusters | mean diff | 95% CI | margin | Wilcoxon p | Holm p | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| regime=final-empirical|crew_multiplier=0.6 | atc | v2rl302 | 180 | 180 | -6.195 | [-10.342, -2.470] | 4.564 | 6.9e-05 | 0.0018 | inconclusive |
| regime=final-empirical|crew_multiplier=0.6 | atc | v2rl303 | 180 | 180 | -6.092 | [-10.408, -2.340] | 4.564 | 8.2e-05 | 0.0020 | inconclusive |
| regime=final-empirical|crew_multiplier=0.6 | atc | v2rl310 | 180 | 180 | -6.067 | [-10.065, -2.635] | 4.564 | 0.0001 | 0.0028 | inconclusive |
| regime=final-empirical|crew_multiplier=0.6 | atc | v2rl305 | 180 | 180 | -5.906 | [-10.097, -2.138] | 4.564 | 0.0002 | 0.0045 | inconclusive |
| regime=final-empirical|crew_multiplier=0.6 | atc | v2rl304 | 180 | 180 | -5.873 | [-10.064, -2.393] | 4.564 | 0.0001 | 0.0029 | inconclusive |
| regime=final-empirical|crew_multiplier=0.6 | atc | v2rl308 | 180 | 180 | -5.465 | [-9.305, -2.115] | 4.564 | 0.0001 | 0.0024 | inconclusive |
| regime=final-empirical|crew_multiplier=0.6 | atc | v2rl307 | 180 | 180 | -5.307 | [-9.574, -1.450] | 4.564 | 0.0004 | 0.0061 | inconclusive |
| regime=final-empirical|crew_multiplier=0.6 | atc | rollcp2 | 48 | 48 | -5.110 | [-11.643, -0.516] | 5.152 | 0.9317 | 1.0000 | inconclusive |
| regime=final-empirical|crew_multiplier=0.6 | atc | v2rl301 | 180 | 180 | -4.791 | [-8.884, -1.082] | 4.564 | 0.0021 | 0.0314 | inconclusive |
| regime=final-empirical|crew_multiplier=0.6 | atc | edd | 180 | 180 | -4.727 | [-8.025, -1.847] | 4.564 | 0.0001 | 0.0010 | inconclusive |
| regime=final-empirical|crew_multiplier=0.6 | atc | pfifo | 180 | 180 | -4.727 | [-8.087, -1.791] | 4.564 | 0.0001 | 0.0010 | inconclusive |
| regime=final-empirical|crew_multiplier=0.6 | atc | v2rl309 | 180 | 180 | -2.996 | [-5.593, -0.727] | 4.564 | 0.0023 | 0.0321 | inconclusive |
| regime=final-empirical|crew_multiplier=0.6 | atc | v2rl306 | 180 | 180 | -2.530 | [-6.443, 1.013] | 4.564 | 0.0159 | 0.1586 | inconclusive |
| regime=final-empirical|crew_multiplier=0.6 | atc | wmdd | 180 | 180 | -1.357 | [-3.154, 0.535] | 4.564 | 0.0063 | 0.0189 | equivalent |
| regime=final-empirical|crew_multiplier=0.6 | atc | wspt | 180 | 180 | +7.336 | [4.301, 11.158] | 4.564 | 3.7e-10 | 6.7e-09 | inconclusive |
| regime=final-empirical|crew_multiplier=0.6 | atc | random | 180 | 180 | +22.875 | [5.374, 54.375] | 4.564 | 2.3e-08 | 3.2e-07 | worse |
| regime=final-empirical|crew_multiplier=0.6 | atc | lpt | 180 | 180 | +80.309 | [16.484, 185.832] | 4.564 | 0.0006 | 0.0024 | worse |
| regime=final-empirical|crew_multiplier=0.6 | edd | v2rl302 | 180 | 180 | -1.468 | [-3.047, 0.017] | 4.517 | 0.0012 | 0.0199 | equivalent |
| regime=final-empirical|crew_multiplier=0.6 | edd | v2rl303 | 180 | 180 | -1.365 | [-3.064, 0.323] | 4.517 | 0.0072 | 0.0796 | equivalent |
| regime=final-empirical|crew_multiplier=0.6 | edd | v2rl310 | 180 | 180 | -1.341 | [-2.593, -0.281] | 4.517 | 0.0039 | 0.0473 | equivalent |
| regime=final-empirical|crew_multiplier=0.6 | edd | v2rl305 | 180 | 180 | -1.179 | [-3.281, 1.127] | 4.517 | 0.0191 | 0.1586 | equivalent |
| regime=final-empirical|crew_multiplier=0.6 | edd | v2rl304 | 180 | 180 | -1.146 | [-2.511, 0.011] | 4.517 | 0.0324 | 0.2157 | equivalent |
| regime=final-empirical|crew_multiplier=0.6 | edd | v2rl308 | 180 | 180 | -0.739 | [-1.727, 0.138] | 4.517 | 0.1124 | 0.2248 | equivalent |
| regime=final-empirical|crew_multiplier=0.6 | edd | rollcp2 | 48 | 48 | -0.651 | [-2.026, 0.387] | 5.107 | 0.1702 | 0.5107 | equivalent |
| regime=final-empirical|crew_multiplier=0.6 | edd | v2rl307 | 180 | 180 | -0.580 | [-2.789, 1.978] | 4.517 | 0.0308 | 0.2157 | equivalent |
| regime=final-empirical|crew_multiplier=0.6 | edd | v2rl301 | 180 | 180 | -0.064 | [-2.480, 2.810] | 4.517 | 0.0487 | 0.2157 | equivalent |
| regime=final-empirical|crew_multiplier=0.6 | edd | pfifo | 180 | 180 | +0.000 | [0.000, 0.000] | 4.517 | 1.0000 | 1.0000 | equivalent |
| regime=final-empirical|crew_multiplier=0.6 | edd | v2rl309 | 180 | 180 | +1.731 | [0.185, 3.762] | 4.517 | 0.0716 | 0.2157 | equivalent |
| regime=final-empirical|crew_multiplier=0.6 | edd | v2rl306 | 180 | 180 | +2.197 | [-0.970, 6.216] | 4.517 | 0.2528 | 0.2528 | inconclusive |
| regime=final-empirical|crew_multiplier=0.6 | edd | wmdd | 180 | 180 | +3.370 | [1.706, 5.394] | 4.517 | 1.8e-05 | 0.0002 | inconclusive |
| regime=final-empirical|crew_multiplier=0.6 | edd | atc | 180 | 180 | +4.727 | [1.785, 8.038] | 4.517 | 0.0001 | 0.0010 | inconclusive |
| regime=final-empirical|crew_multiplier=0.6 | edd | wspt | 180 | 180 | +12.063 | [6.360, 18.930] | 4.517 | 1.4e-09 | 2.3e-08 | worse |
| regime=final-empirical|crew_multiplier=0.6 | edd | random | 180 | 180 | +27.602 | [7.573, 61.797] | 4.517 | 1.2e-08 | 1.8e-07 | worse |
| regime=final-empirical|crew_multiplier=0.6 | edd | lpt | 180 | 180 | +85.036 | [18.657, 190.250] | 4.517 | 1.2e-05 | 0.0001 | worse |
| regime=final-empirical|crew_multiplier=0.6 | wmdd | v2rl302 | 180 | 180 | -4.838 | [-7.869, -2.161] | 4.551 | 3.5e-05 | 0.0010 | inconclusive |
| regime=final-empirical|crew_multiplier=0.6 | wmdd | v2rl303 | 180 | 180 | -4.735 | [-7.857, -1.948] | 4.551 | 0.0001 | 0.0030 | inconclusive |
| regime=final-empirical|crew_multiplier=0.6 | wmdd | v2rl310 | 180 | 180 | -4.711 | [-7.347, -2.410] | 4.551 | 5.9e-05 | 0.0016 | inconclusive |
| regime=final-empirical|crew_multiplier=0.6 | wmdd | v2rl305 | 180 | 180 | -4.549 | [-7.930, -1.366] | 4.551 | 0.0003 | 0.0055 | inconclusive |
| regime=final-empirical|crew_multiplier=0.6 | wmdd | v2rl304 | 180 | 180 | -4.516 | [-7.487, -2.161] | 4.551 | 5.6e-05 | 0.0016 | inconclusive |
| regime=final-empirical|crew_multiplier=0.6 | wmdd | v2rl308 | 180 | 180 | -4.109 | [-6.714, -1.960] | 4.551 | 6.3e-05 | 0.0017 | inconclusive |
| regime=final-empirical|crew_multiplier=0.6 | wmdd | v2rl307 | 180 | 180 | -3.950 | [-7.091, -1.007] | 4.551 | 0.0001 | 0.0030 | inconclusive |
| regime=final-empirical|crew_multiplier=0.6 | wmdd | rollcp2 | 48 | 48 | -3.578 | [-7.911, -0.355] | 5.136 | 0.8864 | 1.0000 | inconclusive |
| regime=final-empirical|crew_multiplier=0.6 | wmdd | v2rl301 | 180 | 180 | -3.434 | [-6.633, -0.285] | 4.551 | 0.0029 | 0.0383 | inconclusive |
| regime=final-empirical|crew_multiplier=0.6 | wmdd | edd | 180 | 180 | -3.370 | [-5.324, -1.700] | 4.551 | 1.8e-05 | 0.0002 | inconclusive |
| regime=final-empirical|crew_multiplier=0.6 | wmdd | pfifo | 180 | 180 | -3.370 | [-5.324, -1.683] | 4.551 | 1.8e-05 | 0.0002 | inconclusive |
| regime=final-empirical|crew_multiplier=0.6 | wmdd | v2rl309 | 180 | 180 | -1.639 | [-3.276, -0.266] | 4.551 | 0.0175 | 0.1586 | equivalent |
| regime=final-empirical|crew_multiplier=0.6 | wmdd | v2rl306 | 180 | 180 | -1.173 | [-4.409, 2.260] | 4.551 | 0.0428 | 0.2157 | equivalent |
| regime=final-empirical|crew_multiplier=0.6 | wmdd | atc | 180 | 180 | +1.357 | [-0.523, 3.186] | 4.551 | 0.0063 | 0.0189 | equivalent |
| regime=final-empirical|crew_multiplier=0.6 | wmdd | wspt | 180 | 180 | +8.693 | [4.345, 13.839] | 4.551 | 3.4e-09 | 5.4e-08 | inconclusive |
| regime=final-empirical|crew_multiplier=0.6 | wmdd | random | 180 | 180 | +24.231 | [5.676, 57.359] | 4.551 | 2.2e-07 | 2.9e-06 | worse |
| regime=final-empirical|crew_multiplier=0.6 | wmdd | lpt | 180 | 180 | +81.666 | [16.655, 186.018] | 4.551 | 0.0004 | 0.0019 | worse |
| regime=final-empirical|crew_multiplier=0.8 | atc | v2rl301 | 180 | 180 | -1.879 | [-3.411, -0.604] | 4.482 | 0.0045 | 0.1071 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | atc | v2rl307 | 180 | 180 | -1.867 | [-3.384, -0.615] | 4.482 | 0.0031 | 0.0849 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | atc | v2rl305 | 180 | 180 | -1.850 | [-3.324, -0.624] | 4.482 | 0.0023 | 0.0662 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | atc | v2rl303 | 180 | 180 | -1.848 | [-3.264, -0.681] | 4.482 | 0.0011 | 0.0337 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | atc | v2rl302 | 180 | 180 | -1.842 | [-3.334, -0.625] | 4.482 | 0.0023 | 0.0662 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | atc | v2rl310 | 180 | 180 | -1.795 | [-3.266, -0.560] | 4.482 | 0.0099 | 0.1777 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | atc | rollcp2 | 48 | 48 | -1.793 | [-4.880, -0.017] | 5.078 | 0.1137 | 0.1137 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | atc | v2rl308 | 180 | 180 | -1.701 | [-3.131, -0.518] | 4.482 | 0.0043 | 0.1071 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | atc | v2rl304 | 180 | 180 | -1.531 | [-2.787, -0.499] | 4.482 | 0.0038 | 0.0979 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | atc | edd | 180 | 180 | -1.530 | [-2.722, -0.552] | 4.482 | 0.0024 | 0.0284 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | atc | pfifo | 180 | 180 | -1.530 | [-2.737, -0.534] | 4.482 | 0.0024 | 0.0284 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | atc | v2rl306 | 180 | 180 | -1.429 | [-2.968, -0.122] | 4.482 | 0.0151 | 0.2414 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | atc | v2rl309 | 180 | 180 | -1.023 | [-1.955, -0.262] | 4.482 | 0.0072 | 0.1577 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | atc | wmdd | 180 | 180 | -0.620 | [-1.351, -0.062] | 4.482 | 0.0505 | 0.2523 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | atc | wspt | 180 | 180 | +2.196 | [1.347, 3.161] | 4.482 | 3.6e-07 | 6.2e-06 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | atc | random | 180 | 180 | +2.420 | [0.657, 4.942] | 4.482 | 0.0017 | 0.0222 | inconclusive |
| regime=final-empirical|crew_multiplier=0.8 | atc | lpt | 180 | 180 | +7.165 | [-0.058, 18.706] | 4.482 | 0.2046 | 0.4091 | inconclusive |
| regime=final-empirical|crew_multiplier=0.8 | edd | rollcp2 | 48 | 48 | -0.511 | [-1.341, 0.063] | 5.065 | 0.0285 | 0.0856 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | edd | v2rl301 | 180 | 180 | -0.349 | [-0.932, 0.197] | 4.466 | 0.1240 | 0.5152 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | edd | v2rl307 | 180 | 180 | -0.336 | [-0.882, 0.184] | 4.466 | 0.0747 | 0.5152 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | edd | v2rl305 | 180 | 180 | -0.320 | [-0.823, 0.196] | 4.466 | 0.0736 | 0.5152 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | edd | v2rl303 | 180 | 180 | -0.318 | [-0.775, 0.075] | 4.466 | 0.0355 | 0.4256 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | edd | v2rl302 | 180 | 180 | -0.311 | [-0.843, 0.190] | 4.466 | 0.0413 | 0.4256 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | edd | v2rl310 | 180 | 180 | -0.265 | [-0.782, 0.254] | 4.466 | 0.1787 | 0.5362 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | edd | v2rl308 | 180 | 180 | -0.171 | [-0.567, 0.294] | 4.466 | 0.0995 | 0.5152 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | edd | v2rl304 | 180 | 180 | -0.001 | [-0.413, 0.442] | 4.466 | 0.9721 | 0.9721 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | edd | pfifo | 180 | 180 | +0.000 | [0.000, 0.000] | 4.466 | 1.0000 | 1.0000 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | edd | v2rl306 | 180 | 180 | +0.101 | [-0.542, 0.935] | 4.466 | 0.3305 | 0.6611 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | edd | v2rl309 | 180 | 180 | +0.508 | [0.112, 0.999] | 4.466 | 0.0303 | 0.3937 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | edd | wmdd | 180 | 180 | +0.911 | [0.296, 1.652] | 4.466 | 0.0050 | 0.0453 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | edd | atc | 180 | 180 | +1.530 | [0.537, 2.736] | 4.466 | 0.0024 | 0.0284 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | edd | wspt | 180 | 180 | +3.726 | [2.139, 5.543] | 4.466 | 2.5e-07 | 4.5e-06 | inconclusive |
| regime=final-empirical|crew_multiplier=0.8 | edd | random | 180 | 180 | +3.950 | [1.582, 7.158] | 4.466 | 6.9e-06 | 0.0001 | inconclusive |
| regime=final-empirical|crew_multiplier=0.8 | edd | lpt | 180 | 180 | +8.695 | [1.139, 20.419] | 4.466 | 0.0176 | 0.1057 | inconclusive |
| regime=final-empirical|crew_multiplier=0.8 | wmdd | v2rl301 | 180 | 180 | -1.259 | [-2.382, -0.341] | 4.475 | 0.0131 | 0.2221 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | wmdd | v2rl307 | 180 | 180 | -1.247 | [-2.341, -0.347] | 4.475 | 0.0076 | 0.1596 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | wmdd | v2rl305 | 180 | 180 | -1.230 | [-2.306, -0.354] | 4.475 | 0.0084 | 0.1672 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | wmdd | v2rl303 | 180 | 180 | -1.228 | [-2.255, -0.406] | 4.475 | 0.0052 | 0.1204 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | wmdd | v2rl302 | 180 | 180 | -1.222 | [-2.289, -0.324] | 4.475 | 0.0084 | 0.1672 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | wmdd | rollcp2 | 48 | 48 | -1.183 | [-3.377, 0.061] | 5.072 | 0.0285 | 0.0856 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | wmdd | v2rl310 | 180 | 180 | -1.176 | [-2.256, -0.282] | 4.475 | 0.0428 | 0.4256 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | wmdd | v2rl308 | 180 | 180 | -1.081 | [-2.088, -0.248] | 4.475 | 0.0186 | 0.2599 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | wmdd | v2rl304 | 180 | 180 | -0.912 | [-1.765, -0.213] | 4.475 | 0.0171 | 0.2559 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | wmdd | edd | 180 | 180 | -0.911 | [-1.654, -0.321] | 4.475 | 0.0050 | 0.0453 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | wmdd | pfifo | 180 | 180 | -0.911 | [-1.661, -0.320] | 4.475 | 0.0050 | 0.0453 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | wmdd | v2rl306 | 180 | 180 | -0.810 | [-1.868, 0.138] | 4.475 | 0.0557 | 0.4458 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | wmdd | v2rl309 | 180 | 180 | -0.403 | [-0.917, 0.015] | 4.475 | 0.0386 | 0.4256 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | wmdd | atc | 180 | 180 | +0.620 | [0.077, 1.383] | 4.475 | 0.0505 | 0.2523 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | wmdd | wspt | 180 | 180 | +2.816 | [1.672, 4.176] | 4.475 | 3.6e-07 | 6.2e-06 | equivalent |
| regime=final-empirical|crew_multiplier=0.8 | wmdd | random | 180 | 180 | +3.039 | [1.032, 5.810] | 4.475 | 0.0003 | 0.0037 | inconclusive |
| regime=final-empirical|crew_multiplier=0.8 | wmdd | lpt | 180 | 180 | +7.784 | [0.561, 19.027] | 4.475 | 0.1259 | 0.3776 | inconclusive |
| regime=final-empirical|crew_multiplier=1.0 | atc | rollcp2 | 64 | 64 | -3.458 | [-13.674, 4.019] | 5.174 | 0.0360 | 0.0360 | inconclusive |
| regime=final-empirical|crew_multiplier=1.0 | atc | wmdd | 227 | 227 | -2.715 | [-5.134, -0.878] | 4.577 | 0.0012 | 0.0129 | inconclusive |
| regime=final-empirical|crew_multiplier=1.0 | atc | edd | 227 | 227 | +3.890 | [-3.498, 14.542] | 4.577 | 0.0674 | 0.4715 | inconclusive |
| regime=final-empirical|crew_multiplier=1.0 | atc | pfifo | 227 | 227 | +3.890 | [-3.428, 13.945] | 4.577 | 0.0674 | 0.4715 | inconclusive |
| regime=final-empirical|crew_multiplier=1.0 | atc | wspt | 227 | 227 | +3.911 | [1.923, 6.287] | 4.577 | 4.2e-07 | 7.1e-06 | inconclusive |
| regime=final-empirical|crew_multiplier=1.0 | atc | v2rl310 | 227 | 227 | +4.781 | [-1.764, 13.314] | 4.577 | 0.8078 | 1.0000 | inconclusive |
| regime=final-empirical|crew_multiplier=1.0 | atc | v2rl302 | 227 | 227 | +11.913 | [2.105, 24.710] | 4.577 | 0.3304 | 1.0000 | inconclusive |
| regime=final-empirical|crew_multiplier=1.0 | atc | v2rl304 | 227 | 227 | +14.021 | [-0.200, 37.358] | 4.577 | 0.8329 | 1.0000 | inconclusive |
| regime=final-empirical|crew_multiplier=1.0 | atc | v2rl309 | 227 | 227 | +14.567 | [1.375, 36.475] | 4.577 | 0.2172 | 1.0000 | inconclusive |
| regime=final-empirical|crew_multiplier=1.0 | atc | v2rl308 | 227 | 227 | +17.459 | [-1.389, 49.160] | 4.577 | 0.8192 | 1.0000 | inconclusive |
| regime=final-empirical|crew_multiplier=1.0 | atc | random | 227 | 227 | +29.448 | [11.688, 50.924] | 4.577 | 2.5e-05 | 0.0004 | worse |
| regime=final-empirical|crew_multiplier=1.0 | atc | v2rl305 | 227 | 227 | +34.458 | [8.600, 70.813] | 4.577 | 0.0875 | 1.0000 | worse |
| regime=final-empirical|crew_multiplier=1.0 | atc | v2rl307 | 227 | 227 | +36.757 | [8.441, 74.779] | 4.577 | 0.3720 | 1.0000 | worse |
| regime=final-empirical|crew_multiplier=1.0 | atc | v2rl301 | 227 | 227 | +44.236 | [10.533, 87.969] | 4.577 | 0.2414 | 1.0000 | worse |
| regime=final-empirical|crew_multiplier=1.0 | atc | v2rl306 | 227 | 227 | +45.235 | [12.805, 85.933] | 4.577 | 0.1361 | 1.0000 | worse |
| regime=final-empirical|crew_multiplier=1.0 | atc | v2rl303 | 227 | 227 | +68.214 | [24.165, 122.157] | 4.577 | 0.0480 | 1.0000 | worse |
| regime=final-empirical|crew_multiplier=1.0 | atc | lpt | 227 | 227 | +102.093 | [37.437, 183.629] | 4.577 | 0.0049 | 0.0395 | worse |
| regime=final-empirical|crew_multiplier=1.0 | edd | rollcp2 | 64 | 64 | -12.969 | [-38.514, 4.216] | 5.269 | 0.0097 | 0.0259 | inconclusive |
| regime=final-empirical|crew_multiplier=1.0 | edd | wmdd | 227 | 227 | -6.605 | [-18.328, 1.581] | 4.616 | 0.4080 | 1.0000 | inconclusive |
| regime=final-empirical|crew_multiplier=1.0 | edd | atc | 227 | 227 | -3.890 | [-13.903, 3.444] | 4.616 | 0.0674 | 0.4715 | inconclusive |
| regime=final-empirical|crew_multiplier=1.0 | edd | pfifo | 227 | 227 | +0.000 | [0.000, 0.000] | 4.616 | 1.0000 | 1.0000 | equivalent |
| regime=final-empirical|crew_multiplier=1.0 | edd | wspt | 227 | 227 | +0.021 | [-10.626, 8.199] | 4.616 | 1.9e-05 | 0.0003 | inconclusive |
| regime=final-empirical|crew_multiplier=1.0 | edd | v2rl310 | 227 | 227 | +0.892 | [-2.900, 4.603] | 4.616 | 0.7089 | 1.0000 | equivalent |
| regime=final-empirical|crew_multiplier=1.0 | edd | v2rl302 | 227 | 227 | +8.024 | [-1.188, 18.263] | 4.616 | 0.2627 | 1.0000 | inconclusive |
| regime=final-empirical|crew_multiplier=1.0 | edd | v2rl304 | 227 | 227 | +10.131 | [-0.339, 26.876] | 4.616 | 0.4688 | 1.0000 | inconclusive |
| regime=final-empirical|crew_multiplier=1.0 | edd | v2rl309 | 227 | 227 | +10.677 | [-2.811, 29.509] | 4.616 | 0.0078 | 0.2273 | inconclusive |
| regime=final-empirical|crew_multiplier=1.0 | edd | v2rl308 | 227 | 227 | +13.569 | [0.434, 36.934] | 4.616 | 0.2891 | 1.0000 | inconclusive |
| regime=final-empirical|crew_multiplier=1.0 | edd | random | 227 | 227 | +25.558 | [8.176, 47.672] | 4.616 | 5.2e-06 | 8.3e-05 | worse |
| regime=final-empirical|crew_multiplier=1.0 | edd | v2rl305 | 227 | 227 | +30.568 | [8.816, 60.180] | 4.616 | 0.0047 | 0.1402 | worse |
| regime=final-empirical|crew_multiplier=1.0 | edd | v2rl307 | 227 | 227 | +32.867 | [8.687, 65.171] | 4.616 | 0.0206 | 0.5365 | worse |
| regime=final-empirical|crew_multiplier=1.0 | edd | v2rl301 | 227 | 227 | +40.346 | [9.604, 79.830] | 4.616 | 0.0333 | 0.7980 | worse |
| regime=final-empirical|crew_multiplier=1.0 | edd | v2rl306 | 227 | 227 | +41.345 | [13.029, 77.724] | 4.616 | 0.0078 | 0.2273 | worse |
| regime=final-empirical|crew_multiplier=1.0 | edd | v2rl303 | 227 | 227 | +64.324 | [22.877, 115.857] | 4.616 | 0.0100 | 0.2699 | worse |
| regime=final-empirical|crew_multiplier=1.0 | edd | lpt | 227 | 227 | +98.203 | [34.364, 179.015] | 4.616 | 0.0002 | 0.0026 | worse |
| regime=final-empirical|crew_multiplier=1.0 | wmdd | rollcp2 | 64 | 64 | -0.243 | [-4.818, 5.002] | 5.142 | 0.0086 | 0.0259 | equivalent |
| regime=final-empirical|crew_multiplier=1.0 | wmdd | atc | 227 | 227 | +2.715 | [0.863, 5.099] | 4.550 | 0.0012 | 0.0129 | inconclusive |
| regime=final-empirical|crew_multiplier=1.0 | wmdd | edd | 227 | 227 | +6.605 | [-1.631, 18.323] | 4.550 | 0.4080 | 1.0000 | inconclusive |
| regime=final-empirical|crew_multiplier=1.0 | wmdd | pfifo | 227 | 227 | +6.605 | [-1.526, 18.612] | 4.550 | 0.4080 | 1.0000 | inconclusive |
| regime=final-empirical|crew_multiplier=1.0 | wmdd | wspt | 227 | 227 | +6.626 | [3.113, 10.968] | 4.550 | 1.2e-07 | 2.2e-06 | inconclusive |
| regime=final-empirical|crew_multiplier=1.0 | wmdd | v2rl310 | 227 | 227 | +7.496 | [-0.304, 17.719] | 4.550 | 0.7677 | 1.0000 | inconclusive |
| regime=final-empirical|crew_multiplier=1.0 | wmdd | v2rl302 | 227 | 227 | +14.628 | [3.222, 29.418] | 4.550 | 0.1698 | 1.0000 | inconclusive |
| regime=final-empirical|crew_multiplier=1.0 | wmdd | v2rl304 | 227 | 227 | +16.735 | [1.316, 40.321] | 4.550 | 0.5503 | 1.0000 | inconclusive |
| regime=final-empirical|crew_multiplier=1.0 | wmdd | v2rl309 | 227 | 227 | +17.282 | [2.822, 40.766] | 4.550 | 0.0930 | 1.0000 | inconclusive |
| regime=final-empirical|crew_multiplier=1.0 | wmdd | v2rl308 | 227 | 227 | +20.174 | [0.274, 52.464] | 4.550 | 0.8076 | 1.0000 | inconclusive |
| regime=final-empirical|crew_multiplier=1.0 | wmdd | random | 227 | 227 | +32.162 | [12.834, 57.011] | 4.550 | 5.3e-05 | 0.0007 | worse |
| regime=final-empirical|crew_multiplier=1.0 | wmdd | v2rl305 | 227 | 227 | +37.173 | [10.305, 74.771] | 4.550 | 0.0636 | 1.0000 | worse |
| regime=final-empirical|crew_multiplier=1.0 | wmdd | v2rl307 | 227 | 227 | +39.472 | [9.568, 78.734] | 4.550 | 0.1790 | 1.0000 | worse |
| regime=final-empirical|crew_multiplier=1.0 | wmdd | v2rl301 | 227 | 227 | +46.950 | [11.923, 91.669] | 4.550 | 0.1808 | 1.0000 | worse |
| regime=final-empirical|crew_multiplier=1.0 | wmdd | v2rl306 | 227 | 227 | +47.949 | [13.828, 91.129] | 4.550 | 0.0680 | 1.0000 | worse |
| regime=final-empirical|crew_multiplier=1.0 | wmdd | v2rl303 | 227 | 227 | +70.929 | [26.572, 128.314] | 4.550 | 0.0273 | 0.6827 | worse |
| regime=final-empirical|crew_multiplier=1.0 | wmdd | lpt | 227 | 227 | +104.808 | [38.369, 187.647] | 4.550 | 0.0042 | 0.0375 | worse |
| regime=final-gen|crew_multiplier=1.0 | atc | v2rl310 | 300 | 300 | -30.558 | [-45.548, -16.042] | 33.580 | 1.9e-10 | 4.5e-09 | inconclusive |
| regime=final-gen|crew_multiplier=1.0 | atc | v2rl304 | 300 | 300 | -30.185 | [-44.461, -16.451] | 33.580 | 1.3e-08 | 2.9e-07 | inconclusive |
| regime=final-gen|crew_multiplier=1.0 | atc | v2rl308 | 300 | 300 | -29.619 | [-45.463, -14.420] | 33.580 | 2.7e-07 | 5.3e-06 | inconclusive |
| regime=final-gen|crew_multiplier=1.0 | atc | pfifo | 300 | 300 | -24.056 | [-39.693, -6.741] | 33.580 | 5.4e-14 | 3.2e-13 | inconclusive |
| regime=final-gen|crew_multiplier=1.0 | atc | edd | 300 | 300 | -23.860 | [-39.182, -6.468] | 33.580 | 6.3e-14 | 3.2e-13 | inconclusive |
| regime=final-gen|crew_multiplier=1.0 | atc | v2rl305 | 300 | 300 | -9.485 | [-31.724, 15.096] | 33.580 | 5.5e-08 | 1.2e-06 | equivalent |
| regime=final-gen|crew_multiplier=1.0 | atc | wmdd | 300 | 300 | -3.046 | [-7.915, 1.365] | 33.580 | 0.0235 | 0.0706 | equivalent |
| regime=final-gen|crew_multiplier=1.0 | atc | v2rl302 | 300 | 300 | +17.083 | [-10.050, 50.509] | 33.580 | 0.0008 | 0.0115 | inconclusive |
| regime=final-gen|crew_multiplier=1.0 | atc | v2rl307 | 300 | 300 | +19.850 | [-10.284, 58.013] | 33.580 | 0.0001 | 0.0024 | inconclusive |
| regime=final-gen|crew_multiplier=1.0 | atc | v2rl306 | 300 | 300 | +31.094 | [-5.834, 77.529] | 33.580 | 0.0076 | 0.0918 | inconclusive |
| regime=final-gen|crew_multiplier=1.0 | atc | v2rl301 | 300 | 300 | +47.942 | [7.416, 95.900] | 33.580 | 0.0132 | 0.1443 | inconclusive |
| regime=final-gen|crew_multiplier=1.0 | atc | v2rl309 | 300 | 300 | +561.469 | [418.195, 720.503] | 33.580 | 1.1e-27 | 3.0e-26 | worse |
| regime=final-gen|crew_multiplier=1.0 | atc | v2rl303 | 300 | 300 | +620.435 | [457.448, 799.974] | 33.580 | 2.0e-22 | 5.1e-21 | worse |
| regime=final-gen|crew_multiplier=1.0 | atc | wspt | 300 | 300 | +706.630 | [595.425, 824.639] | 33.580 | 1.2e-46 | 1.8e-45 | worse |
| regime=final-gen|crew_multiplier=1.0 | atc | random | 300 | 300 | +9878.415 | [8197.730, 11619.502] | 33.580 | 1.5e-45 | 1.8e-44 | worse |
| regime=final-gen|crew_multiplier=1.0 | atc | lpt | 300 | 300 | +39672.656 | [33957.478, 45713.663] | 33.580 | 5.6e-49 | 1.0e-47 | worse |
| regime=final-gen|crew_multiplier=1.0 | edd | v2rl310 | 300 | 300 | -6.698 | [-19.569, 6.330] | 33.341 | 0.0006 | 0.0092 | equivalent |
| regime=final-gen|crew_multiplier=1.0 | edd | v2rl304 | 300 | 300 | -6.325 | [-13.157, -0.754] | 33.341 | 0.1023 | 0.5599 | equivalent |
| regime=final-gen|crew_multiplier=1.0 | edd | v2rl308 | 300 | 300 | -5.759 | [-16.765, 5.835] | 33.341 | 0.0131 | 0.1443 | equivalent |
| regime=final-gen|crew_multiplier=1.0 | edd | pfifo | 300 | 300 | -0.197 | [-0.614, 0.025] | 33.341 | 0.6858 | 0.6858 | equivalent |
| regime=final-gen|crew_multiplier=1.0 | edd | v2rl305 | 300 | 300 | +14.375 | [-3.067, 36.692] | 33.341 | 0.0142 | 0.1443 | inconclusive |
| regime=final-gen|crew_multiplier=1.0 | edd | wmdd | 300 | 300 | +20.814 | [3.746, 35.693] | 33.341 | 2.9e-14 | 2.3e-13 | inconclusive |
| regime=final-gen|crew_multiplier=1.0 | edd | atc | 300 | 300 | +23.860 | [6.560, 39.265] | 33.341 | 6.3e-14 | 3.2e-13 | inconclusive |
| regime=final-gen|crew_multiplier=1.0 | edd | v2rl302 | 300 | 300 | +40.943 | [9.781, 79.381] | 33.341 | 0.8173 | 1.0000 | inconclusive |
| regime=final-gen|crew_multiplier=1.0 | edd | v2rl307 | 300 | 300 | +43.710 | [17.681, 73.817] | 33.341 | 0.9020 | 1.0000 | inconclusive |
| regime=final-gen|crew_multiplier=1.0 | edd | v2rl306 | 300 | 300 | +54.953 | [21.401, 96.961] | 33.341 | 0.4649 | 1.0000 | inconclusive |
| regime=final-gen|crew_multiplier=1.0 | edd | v2rl301 | 300 | 300 | +71.802 | [28.189, 123.020] | 33.341 | 0.0933 | 0.5599 | inconclusive |
| regime=final-gen|crew_multiplier=1.0 | edd | v2rl309 | 300 | 300 | +585.329 | [437.007, 750.393] | 33.341 | 4.7e-33 | 1.4e-31 | worse |
| regime=final-gen|crew_multiplier=1.0 | edd | v2rl303 | 300 | 300 | +644.295 | [471.677, 829.008] | 33.341 | 2.5e-31 | 7.2e-30 | worse |
| regime=final-gen|crew_multiplier=1.0 | edd | wspt | 300 | 300 | +730.490 | [611.739, 858.219] | 33.341 | 1.4e-46 | 1.9e-45 | worse |
| regime=final-gen|crew_multiplier=1.0 | edd | random | 300 | 300 | +9902.275 | [8185.108, 11732.660] | 33.341 | 1.5e-45 | 1.8e-44 | worse |
| regime=final-gen|crew_multiplier=1.0 | edd | lpt | 300 | 300 | +39696.516 | [33988.642, 45896.011] | 33.341 | 5.6e-49 | 1.0e-47 | worse |
| regime=final-gen|crew_multiplier=1.0 | wmdd | v2rl310 | 300 | 300 | -27.512 | [-41.949, -13.198] | 33.549 | 7.1e-08 | 1.5e-06 | inconclusive |
| regime=final-gen|crew_multiplier=1.0 | wmdd | v2rl304 | 300 | 300 | -27.139 | [-40.509, -13.741] | 33.549 | 6.8e-07 | 1.3e-05 | inconclusive |
| regime=final-gen|crew_multiplier=1.0 | wmdd | v2rl308 | 300 | 300 | -26.574 | [-42.292, -11.143] | 33.549 | 4.4e-05 | 0.0008 | inconclusive |
| regime=final-gen|crew_multiplier=1.0 | wmdd | pfifo | 300 | 300 | -21.011 | [-35.457, -4.019] | 33.549 | 1.7e-14 | 1.6e-13 | inconclusive |
| regime=final-gen|crew_multiplier=1.0 | wmdd | edd | 300 | 300 | -20.814 | [-35.075, -3.527] | 33.549 | 2.9e-14 | 2.3e-13 | inconclusive |
| regime=final-gen|crew_multiplier=1.0 | wmdd | v2rl305 | 300 | 300 | -6.439 | [-27.655, 19.057] | 33.549 | 1.0e-05 | 0.0002 | equivalent |
| regime=final-gen|crew_multiplier=1.0 | wmdd | atc | 300 | 300 | +3.046 | [-1.399, 8.016] | 33.549 | 0.0235 | 0.0706 | equivalent |
| regime=final-gen|crew_multiplier=1.0 | wmdd | v2rl302 | 300 | 300 | +20.129 | [-7.778, 54.215] | 33.549 | 0.0353 | 0.2824 | inconclusive |
| regime=final-gen|crew_multiplier=1.0 | wmdd | v2rl307 | 300 | 300 | +22.896 | [-7.551, 61.925] | 33.549 | 0.0033 | 0.0430 | inconclusive |
| regime=final-gen|crew_multiplier=1.0 | wmdd | v2rl306 | 300 | 300 | +34.139 | [-3.965, 81.342] | 33.549 | 0.0671 | 0.4694 | inconclusive |
| regime=final-gen|crew_multiplier=1.0 | wmdd | v2rl301 | 300 | 300 | +50.988 | [10.150, 100.365] | 33.549 | 0.1661 | 0.6643 | inconclusive |
| regime=final-gen|crew_multiplier=1.0 | wmdd | v2rl309 | 300 | 300 | +564.515 | [422.827, 723.043] | 33.549 | 5.1e-28 | 1.4e-26 | worse |
| regime=final-gen|crew_multiplier=1.0 | wmdd | v2rl303 | 300 | 300 | +623.481 | [463.788, 801.710] | 33.549 | 6.3e-24 | 1.6e-22 | worse |
| regime=final-gen|crew_multiplier=1.0 | wmdd | wspt | 300 | 300 | +709.675 | [596.654, 826.409] | 33.549 | 1.5e-46 | 2.0e-45 | worse |
| regime=final-gen|crew_multiplier=1.0 | wmdd | random | 300 | 300 | +9881.460 | [8185.651, 11615.200] | 33.549 | 1.5e-45 | 1.8e-44 | worse |
| regime=final-gen|crew_multiplier=1.0 | wmdd | lpt | 300 | 300 | +39675.702 | [33955.151, 45705.757] | 33.549 | 5.6e-49 | 1.0e-47 | worse |

### scope_type = u_bin

| scope | reference | method | n | clusters | mean diff | 95% CI | margin | Wilcoxon p | Holm p | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| u_bin=0.5-0.8 | atc | rollcp2 | 49 | 31 | -3.973 | [-11.043, -0.135] | 7.933 | 0.3600 | 0.3600 | inconclusive |
| u_bin=0.5-0.8 | atc | v2rl301 | 223 | 174 | -2.494 | [-4.849, -0.697] | 10.869 | 0.0037 | 0.0587 | equivalent |
| u_bin=0.5-0.8 | atc | v2rl310 | 223 | 174 | -2.480 | [-4.896, -0.611] | 10.869 | 0.0009 | 0.0197 | equivalent |
| u_bin=0.5-0.8 | atc | v2rl305 | 223 | 174 | -2.473 | [-4.874, -0.626] | 10.869 | 0.0053 | 0.0638 | equivalent |
| u_bin=0.5-0.8 | atc | v2rl306 | 223 | 174 | -2.471 | [-4.867, -0.667] | 10.869 | 0.0016 | 0.0285 | equivalent |
| u_bin=0.5-0.8 | atc | v2rl302 | 223 | 174 | -2.411 | [-4.619, -0.686] | 10.869 | 0.0008 | 0.0180 | equivalent |
| u_bin=0.5-0.8 | atc | v2rl307 | 223 | 174 | -2.403 | [-4.588, -0.733] | 10.869 | 0.0003 | 0.0078 | equivalent |
| u_bin=0.5-0.8 | atc | v2rl308 | 223 | 174 | -2.375 | [-4.680, -0.585] | 10.869 | 0.0076 | 0.0638 | equivalent |
| u_bin=0.5-0.8 | atc | v2rl303 | 223 | 174 | -2.139 | [-4.849, -0.009] | 10.869 | 0.0043 | 0.0638 | equivalent |
| u_bin=0.5-0.8 | atc | v2rl304 | 223 | 174 | -1.946 | [-3.718, -0.558] | 10.869 | 0.0056 | 0.0638 | equivalent |
| u_bin=0.5-0.8 | atc | edd | 223 | 174 | -1.854 | [-3.796, -0.422] | 10.869 | 0.0063 | 0.0380 | equivalent |
| u_bin=0.5-0.8 | atc | pfifo | 223 | 174 | -1.854 | [-3.810, -0.414] | 10.869 | 0.0063 | 0.0380 | equivalent |
| u_bin=0.5-0.8 | atc | v2rl309 | 223 | 174 | -1.371 | [-2.839, -0.110] | 10.869 | 0.0101 | 0.0638 | equivalent |
| u_bin=0.5-0.8 | atc | wmdd | 223 | 174 | -0.399 | [-1.098, 0.180] | 10.869 | 0.3019 | 0.9056 | equivalent |
| u_bin=0.5-0.8 | atc | wspt | 223 | 174 | +4.820 | [3.044, 6.996] | 10.869 | 1.0e-12 | 1.8e-11 | equivalent |
| u_bin=0.5-0.8 | atc | random | 223 | 174 | +14.862 | [8.096, 23.359] | 10.869 | 1.1e-10 | 1.1e-09 | inconclusive |
| u_bin=0.5-0.8 | atc | lpt | 223 | 174 | +96.751 | [59.152, 141.356] | 10.869 | 2.0e-11 | 2.4e-10 | worse |
| u_bin=0.5-0.8 | edd | v2rl301 | 223 | 174 | -0.640 | [-1.295, -0.048] | 10.851 | 0.0182 | 0.0909 | equivalent |
| u_bin=0.5-0.8 | edd | v2rl310 | 223 | 174 | -0.626 | [-1.317, -0.030] | 10.851 | 0.0087 | 0.0638 | equivalent |
| u_bin=0.5-0.8 | edd | v2rl305 | 223 | 174 | -0.619 | [-1.276, -0.043] | 10.851 | 0.0070 | 0.0638 | equivalent |
| u_bin=0.5-0.8 | edd | v2rl306 | 223 | 174 | -0.617 | [-1.254, -0.041] | 10.851 | 0.0044 | 0.0638 | equivalent |
| u_bin=0.5-0.8 | edd | v2rl302 | 223 | 174 | -0.557 | [-1.149, -0.046] | 10.851 | 0.0049 | 0.0638 | equivalent |
| u_bin=0.5-0.8 | edd | v2rl307 | 223 | 174 | -0.549 | [-1.142, -0.020] | 10.851 | 0.0027 | 0.0451 | equivalent |
| u_bin=0.5-0.8 | edd | v2rl308 | 223 | 174 | -0.521 | [-1.156, 0.044] | 10.851 | 0.0267 | 0.1069 | equivalent |
| u_bin=0.5-0.8 | edd | rollcp2 | 49 | 31 | -0.454 | [-1.105, 0.045] | 7.898 | 0.0132 | 0.0395 | equivalent |
| u_bin=0.5-0.8 | edd | v2rl303 | 223 | 174 | -0.286 | [-1.328, 0.818] | 10.851 | 0.0754 | 0.2263 | equivalent |
| u_bin=0.5-0.8 | edd | v2rl304 | 223 | 174 | -0.093 | [-0.607, 0.456] | 10.851 | 0.1977 | 0.3953 | equivalent |
| u_bin=0.5-0.8 | edd | pfifo | 223 | 174 | +0.000 | [0.000, 0.000] | 10.851 | 1.0000 | 1.0000 | equivalent |
| u_bin=0.5-0.8 | edd | v2rl309 | 223 | 174 | +0.483 | [-0.304, 1.465] | 10.851 | 0.7589 | 0.7589 | equivalent |
| u_bin=0.5-0.8 | edd | wmdd | 223 | 174 | +1.455 | [0.457, 2.763] | 10.851 | 1.8e-05 | 0.0002 | equivalent |
| u_bin=0.5-0.8 | edd | atc | 223 | 174 | +1.854 | [0.438, 3.716] | 10.851 | 0.0063 | 0.0380 | equivalent |
| u_bin=0.5-0.8 | edd | wspt | 223 | 174 | +6.674 | [3.835, 10.342] | 10.851 | 4.0e-12 | 6.3e-11 | equivalent |
| u_bin=0.5-0.8 | edd | random | 223 | 174 | +16.716 | [9.291, 25.717] | 10.851 | 6.5e-13 | 1.2e-11 | inconclusive |
| u_bin=0.5-0.8 | edd | lpt | 223 | 174 | +98.605 | [60.622, 144.216] | 10.851 | 5.3e-12 | 7.9e-11 | worse |
| u_bin=0.5-0.8 | wmdd | rollcp2 | 49 | 31 | -2.648 | [-7.277, 0.035] | 7.920 | 0.0571 | 0.1141 | equivalent |
| u_bin=0.5-0.8 | wmdd | v2rl301 | 223 | 174 | -2.094 | [-3.928, -0.681] | 10.865 | 0.0011 | 0.0228 | equivalent |
| u_bin=0.5-0.8 | wmdd | v2rl310 | 223 | 174 | -2.080 | [-4.004, -0.605] | 10.865 | 0.0001 | 0.0040 | equivalent |
| u_bin=0.5-0.8 | wmdd | v2rl305 | 223 | 174 | -2.074 | [-3.944, -0.622] | 10.865 | 0.0003 | 0.0065 | equivalent |
| u_bin=0.5-0.8 | wmdd | v2rl306 | 223 | 174 | -2.071 | [-3.918, -0.643] | 10.865 | 0.0001 | 0.0036 | equivalent |
| u_bin=0.5-0.8 | wmdd | v2rl302 | 223 | 174 | -2.011 | [-3.737, -0.672] | 10.865 | 9.1e-05 | 0.0026 | equivalent |
| u_bin=0.5-0.8 | wmdd | v2rl307 | 223 | 174 | -2.003 | [-3.676, -0.722] | 10.865 | 7.7e-06 | 0.0002 | equivalent |
| u_bin=0.5-0.8 | wmdd | v2rl308 | 223 | 174 | -1.976 | [-3.755, -0.588] | 10.865 | 0.0005 | 0.0121 | equivalent |
| u_bin=0.5-0.8 | wmdd | v2rl303 | 223 | 174 | -1.740 | [-3.903, -0.006] | 10.865 | 0.0014 | 0.0272 | equivalent |
| u_bin=0.5-0.8 | wmdd | v2rl304 | 223 | 174 | -1.547 | [-2.871, -0.530] | 10.865 | 0.0003 | 0.0078 | equivalent |
| u_bin=0.5-0.8 | wmdd | edd | 223 | 174 | -1.455 | [-2.775, -0.461] | 10.865 | 1.8e-05 | 0.0002 | equivalent |
| u_bin=0.5-0.8 | wmdd | pfifo | 223 | 174 | -1.455 | [-2.777, -0.450] | 10.865 | 1.8e-05 | 0.0002 | equivalent |
| u_bin=0.5-0.8 | wmdd | v2rl309 | 223 | 174 | -0.972 | [-2.142, -0.017] | 10.865 | 0.0046 | 0.0638 | equivalent |
| u_bin=0.5-0.8 | wmdd | atc | 223 | 174 | +0.399 | [-0.180, 1.085] | 10.865 | 0.3019 | 0.9056 | equivalent |
| u_bin=0.5-0.8 | wmdd | wspt | 223 | 174 | +5.219 | [3.158, 7.860] | 10.865 | 8.7e-12 | 1.2e-10 | equivalent |
| u_bin=0.5-0.8 | wmdd | random | 223 | 174 | +15.262 | [8.358, 23.633] | 10.865 | 2.4e-11 | 2.6e-10 | inconclusive |
| u_bin=0.5-0.8 | wmdd | lpt | 223 | 174 | +97.151 | [59.075, 142.745] | 10.865 | 1.5e-11 | 1.9e-10 | worse |
| u_bin=0.8-1.0 | atc | v2rl305 | 166 | 166 | -16.894 | [-23.656, -10.679] | 20.241 | 4.1e-08 | 1.1e-06 | inconclusive |
| u_bin=0.8-1.0 | atc | v2rl310 | 166 | 166 | -16.800 | [-23.829, -10.309] | 20.241 | 3.6e-08 | 1.0e-06 | inconclusive |
| u_bin=0.8-1.0 | atc | v2rl307 | 166 | 166 | -14.532 | [-20.997, -8.864] | 20.241 | 5.4e-08 | 1.5e-06 | inconclusive |
| u_bin=0.8-1.0 | atc | v2rl301 | 166 | 166 | -14.343 | [-20.625, -8.628] | 20.241 | 8.9e-07 | 2.1e-05 | inconclusive |
| u_bin=0.8-1.0 | atc | v2rl302 | 166 | 166 | -14.246 | [-20.669, -8.291] | 20.241 | 1.6e-06 | 3.6e-05 | inconclusive |
| u_bin=0.8-1.0 | atc | v2rl308 | 166 | 166 | -13.790 | [-19.987, -8.217] | 20.241 | 3.6e-06 | 7.2e-05 | equivalent |
| u_bin=0.8-1.0 | atc | v2rl306 | 166 | 166 | -12.674 | [-19.209, -6.832] | 20.241 | 0.0001 | 0.0018 | equivalent |
| u_bin=0.8-1.0 | atc | v2rl304 | 166 | 166 | -11.874 | [-17.572, -6.632] | 20.241 | 5.5e-06 | 0.0001 | equivalent |
| u_bin=0.8-1.0 | atc | edd | 166 | 166 | -9.839 | [-14.177, -5.784] | 20.241 | 3.8e-08 | 2.3e-07 | equivalent |
| u_bin=0.8-1.0 | atc | pfifo | 166 | 166 | -9.839 | [-14.181, -5.738] | 20.241 | 3.8e-08 | 2.3e-07 | equivalent |
| u_bin=0.8-1.0 | atc | rollcp2 | 15 | 15 | -7.679 | [-22.376, 0.205] | 8.443 | 0.6744 | 1.0000 | inconclusive |
| u_bin=0.8-1.0 | atc | wmdd | 166 | 166 | -0.671 | [-3.317, 2.068] | 20.241 | 0.1903 | 0.5710 | equivalent |
| u_bin=0.8-1.0 | atc | v2rl309 | 166 | 166 | +36.782 | [16.065, 61.824] | 20.241 | 0.0106 | 0.0552 | inconclusive |
| u_bin=0.8-1.0 | atc | v2rl303 | 166 | 166 | +54.641 | [32.863, 79.721] | 20.241 | 0.0016 | 0.0125 | worse |
| u_bin=0.8-1.0 | atc | wspt | 166 | 166 | +161.766 | [124.166, 202.501] | 20.241 | 7.2e-21 | 1.3e-19 | worse |
| u_bin=0.8-1.0 | atc | random | 166 | 166 | +1692.056 | [1301.761, 2111.641] | 20.241 | 1.1e-19 | 1.4e-18 | worse |
| u_bin=0.8-1.0 | atc | lpt | 166 | 166 | +10396.750 | [8259.630, 12695.539] | 20.241 | 1.9e-20 | 3.0e-19 | worse |
| u_bin=0.8-1.0 | edd | v2rl305 | 166 | 166 | -7.055 | [-10.506, -3.870] | 20.143 | 0.0001 | 0.0018 | equivalent |
| u_bin=0.8-1.0 | edd | v2rl310 | 166 | 166 | -6.961 | [-10.756, -3.596] | 20.143 | 3.9e-05 | 0.0005 | equivalent |
| u_bin=0.8-1.0 | edd | v2rl307 | 166 | 166 | -4.693 | [-7.624, -1.976] | 20.143 | 0.0013 | 0.0116 | equivalent |
| u_bin=0.8-1.0 | edd | v2rl301 | 166 | 166 | -4.504 | [-7.634, -1.700] | 20.143 | 0.0118 | 0.0552 | equivalent |
| u_bin=0.8-1.0 | edd | v2rl302 | 166 | 166 | -4.407 | [-7.632, -1.595] | 20.143 | 0.0092 | 0.0552 | equivalent |
| u_bin=0.8-1.0 | edd | v2rl308 | 166 | 166 | -3.951 | [-6.858, -1.212] | 20.143 | 0.0137 | 0.0552 | equivalent |
| u_bin=0.8-1.0 | edd | v2rl306 | 166 | 166 | -2.835 | [-6.364, 0.669] | 20.143 | 0.0533 | 0.1066 | equivalent |
| u_bin=0.8-1.0 | edd | rollcp2 | 15 | 15 | -2.262 | [-6.096, 0.202] | 8.388 | 0.6744 | 1.0000 | equivalent |
| u_bin=0.8-1.0 | edd | v2rl304 | 166 | 166 | -2.035 | [-4.409, 0.178] | 20.143 | 0.1591 | 0.1591 | equivalent |
| u_bin=0.8-1.0 | edd | pfifo | 166 | 166 | +0.000 | [0.000, 0.000] | 20.143 | 1.0000 | 1.0000 | equivalent |
| u_bin=0.8-1.0 | edd | wmdd | 166 | 166 | +9.168 | [5.897, 12.994] | 20.143 | 4.9e-09 | 4.4e-08 | equivalent |
| u_bin=0.8-1.0 | edd | atc | 166 | 166 | +9.839 | [5.815, 14.211] | 20.143 | 3.8e-08 | 2.3e-07 | equivalent |
| u_bin=0.8-1.0 | edd | v2rl309 | 166 | 166 | +46.621 | [26.495, 70.047] | 20.143 | 8.0e-07 | 1.9e-05 | worse |
| u_bin=0.8-1.0 | edd | v2rl303 | 166 | 166 | +64.480 | [41.886, 89.536] | 20.143 | 4.9e-09 | 1.5e-07 | worse |
| u_bin=0.8-1.0 | edd | wspt | 166 | 166 | +171.605 | [131.924, 214.246] | 20.143 | 1.2e-20 | 2.1e-19 | worse |
| u_bin=0.8-1.0 | edd | random | 166 | 166 | +1701.895 | [1310.765, 2119.015] | 20.143 | 2.5e-19 | 2.7e-18 | worse |
| u_bin=0.8-1.0 | edd | lpt | 166 | 166 | +10406.589 | [8244.182, 12687.428] | 20.143 | 4.4e-20 | 5.8e-19 | worse |
| u_bin=0.8-1.0 | wmdd | v2rl305 | 166 | 166 | -16.223 | [-22.983, -10.210] | 20.235 | 4.4e-07 | 1.2e-05 | inconclusive |
| u_bin=0.8-1.0 | wmdd | v2rl310 | 166 | 166 | -16.129 | [-22.900, -10.060] | 20.235 | 4.6e-07 | 1.2e-05 | inconclusive |
| u_bin=0.8-1.0 | wmdd | v2rl307 | 166 | 166 | -13.861 | [-19.705, -8.582] | 20.235 | 2.2e-06 | 4.7e-05 | equivalent |
| u_bin=0.8-1.0 | wmdd | v2rl301 | 166 | 166 | -13.672 | [-19.516, -8.273] | 20.235 | 1.1e-05 | 0.0002 | equivalent |
| u_bin=0.8-1.0 | wmdd | v2rl302 | 166 | 166 | -13.575 | [-19.504, -8.166] | 20.235 | 7.2e-06 | 0.0001 | equivalent |
| u_bin=0.8-1.0 | wmdd | v2rl308 | 166 | 166 | -13.119 | [-18.923, -7.784] | 20.235 | 1.2e-05 | 0.0002 | equivalent |
| u_bin=0.8-1.0 | wmdd | v2rl306 | 166 | 166 | -12.003 | [-18.208, -6.279] | 20.235 | 0.0003 | 0.0030 | equivalent |
| u_bin=0.8-1.0 | wmdd | v2rl304 | 166 | 166 | -11.203 | [-16.448, -6.592] | 20.235 | 2.2e-05 | 0.0003 | equivalent |
| u_bin=0.8-1.0 | wmdd | edd | 166 | 166 | -9.168 | [-12.910, -5.878] | 20.235 | 4.9e-09 | 4.4e-08 | equivalent |
| u_bin=0.8-1.0 | wmdd | pfifo | 166 | 166 | -9.168 | [-12.909, -5.844] | 20.235 | 4.9e-09 | 4.4e-08 | equivalent |
| u_bin=0.8-1.0 | wmdd | rollcp2 | 15 | 15 | -6.771 | [-17.468, 0.103] | 8.433 | 0.6744 | 1.0000 | inconclusive |
| u_bin=0.8-1.0 | wmdd | atc | 166 | 166 | +0.671 | [-2.108, 3.293] | 20.235 | 0.1903 | 0.5710 | equivalent |
| u_bin=0.8-1.0 | wmdd | v2rl309 | 166 | 166 | +37.453 | [16.430, 62.227] | 20.235 | 0.0058 | 0.0409 | inconclusive |
| u_bin=0.8-1.0 | wmdd | v2rl303 | 166 | 166 | +55.312 | [32.674, 80.610] | 20.235 | 0.0005 | 0.0054 | worse |
| u_bin=0.8-1.0 | wmdd | wspt | 166 | 166 | +162.437 | [125.008, 203.036] | 20.235 | 2.2e-20 | 3.4e-19 | worse |
| u_bin=0.8-1.0 | wmdd | random | 166 | 166 | +1692.727 | [1296.156, 2101.269] | 20.235 | 4.0e-19 | 4.0e-18 | worse |
| u_bin=0.8-1.0 | wmdd | lpt | 166 | 166 | +10397.421 | [8233.628, 12664.536] | 20.235 | 3.9e-20 | 5.4e-19 | worse |
| u_bin=1.0-1.2 | atc | v2rl310 | 124 | 124 | -31.124 | [-53.350, -7.755] | 27.446 | 1.0e-05 | 0.0002 | inconclusive |
| u_bin=1.0-1.2 | atc | v2rl304 | 124 | 124 | -28.094 | [-43.170, -14.886] | 27.446 | 3.9e-05 | 0.0009 | inconclusive |
| u_bin=1.0-1.2 | atc | pfifo | 124 | 124 | -26.737 | [-39.212, -15.970] | 27.446 | 3.7e-09 | 3.4e-08 | inconclusive |
| u_bin=1.0-1.2 | atc | edd | 124 | 124 | -26.250 | [-39.079, -15.328] | 27.446 | 4.7e-09 | 3.8e-08 | inconclusive |
| u_bin=1.0-1.2 | atc | v2rl308 | 124 | 124 | -26.149 | [-44.508, -8.850] | 27.446 | 0.0009 | 0.0175 | inconclusive |
| u_bin=1.0-1.2 | atc | v2rl305 | 124 | 124 | -21.311 | [-44.892, 2.601] | 27.446 | 0.0007 | 0.0143 | inconclusive |
| u_bin=1.0-1.2 | atc | v2rl302 | 124 | 124 | -12.299 | [-31.963, 9.283] | 27.446 | 0.0061 | 0.1091 | inconclusive |
| u_bin=1.0-1.2 | atc | v2rl307 | 124 | 124 | -9.325 | [-35.319, 18.215] | 27.446 | 0.0062 | 0.1091 | inconclusive |
| u_bin=1.0-1.2 | atc | wmdd | 124 | 124 | -2.579 | [-7.464, 2.490] | 27.446 | 0.1165 | 0.3496 | equivalent |
| u_bin=1.0-1.2 | atc | v2rl301 | 124 | 124 | +0.555 | [-23.221, 27.414] | 27.446 | 0.0464 | 0.6026 | equivalent |
| u_bin=1.0-1.2 | atc | v2rl306 | 124 | 124 | +3.346 | [-24.600, 35.698] | 27.446 | 0.1348 | 1.0000 | inconclusive |
| u_bin=1.0-1.2 | atc | rollcp2 | 8 | 8 | +11.966 | [-6.743, 43.952] | 6.199 | 1.0000 | 1.0000 | inconclusive |
| u_bin=1.0-1.2 | atc | v2rl309 | 124 | 124 | +250.635 | [168.235, 341.877] | 27.446 | 1.2e-13 | 3.3e-12 | worse |
| u_bin=1.0-1.2 | atc | v2rl303 | 124 | 124 | +256.358 | [159.229, 372.552] | 27.446 | 1.5e-07 | 3.9e-06 | worse |
| u_bin=1.0-1.2 | atc | wspt | 124 | 124 | +475.007 | [369.603, 589.244] | 27.446 | 8.3e-18 | 1.2e-16 | worse |
| u_bin=1.0-1.2 | atc | random | 124 | 124 | +6668.745 | [5279.102, 8090.562] | 27.446 | 1.1e-17 | 1.2e-16 | worse |
| u_bin=1.0-1.2 | atc | lpt | 124 | 124 | +30366.828 | [24485.135, 36454.719] | 27.446 | 9.6e-18 | 1.2e-16 | worse |
| u_bin=1.0-1.2 | edd | v2rl310 | 124 | 124 | -4.874 | [-19.478, 16.539] | 27.183 | 0.0078 | 0.1246 | equivalent |
| u_bin=1.0-1.2 | edd | v2rl304 | 124 | 124 | -1.844 | [-7.194, 3.905] | 27.183 | 0.3464 | 1.0000 | equivalent |
| u_bin=1.0-1.2 | edd | pfifo | 124 | 124 | -0.487 | [-1.461, 0.000] | 27.183 | 0.3173 | 0.3496 | equivalent |
| u_bin=1.0-1.2 | edd | v2rl308 | 124 | 124 | +0.101 | [-11.496, 14.781] | 27.183 | 0.2400 | 1.0000 | equivalent |
| u_bin=1.0-1.2 | edd | v2rl305 | 124 | 124 | +4.939 | [-12.403, 26.467] | 27.183 | 0.2328 | 1.0000 | equivalent |
| u_bin=1.0-1.2 | edd | v2rl302 | 124 | 124 | +13.951 | [-4.392, 38.334] | 27.183 | 0.7218 | 1.0000 | inconclusive |
| u_bin=1.0-1.2 | edd | rollcp2 | 8 | 8 | +16.221 | [-2.996, 51.697] | 6.157 | 1.0000 | 1.0000 | inconclusive |
| u_bin=1.0-1.2 | edd | v2rl307 | 124 | 124 | +16.925 | [-5.202, 44.400] | 27.183 | 0.7355 | 1.0000 | inconclusive |
| u_bin=1.0-1.2 | edd | wmdd | 124 | 124 | +23.671 | [13.501, 35.107] | 27.183 | 3.5e-07 | 1.7e-06 | inconclusive |
| u_bin=1.0-1.2 | edd | atc | 124 | 124 | +26.250 | [15.427, 38.582] | 27.183 | 4.7e-09 | 3.8e-08 | inconclusive |
| u_bin=1.0-1.2 | edd | v2rl301 | 124 | 124 | +26.805 | [2.253, 57.407] | 27.183 | 0.4597 | 1.0000 | inconclusive |
| u_bin=1.0-1.2 | edd | v2rl306 | 124 | 124 | +29.596 | [0.045, 67.445] | 27.183 | 0.5655 | 1.0000 | inconclusive |
| u_bin=1.0-1.2 | edd | v2rl309 | 124 | 124 | +276.885 | [191.968, 372.305] | 27.183 | 8.5e-17 | 2.5e-15 | worse |
| u_bin=1.0-1.2 | edd | v2rl303 | 124 | 124 | +282.608 | [177.425, 405.489] | 27.183 | 6.0e-11 | 1.6e-09 | worse |
| u_bin=1.0-1.2 | edd | wspt | 124 | 124 | +501.257 | [388.129, 625.019] | 27.183 | 5.7e-18 | 1.0e-16 | worse |
| u_bin=1.0-1.2 | edd | random | 124 | 124 | +6694.995 | [5306.586, 8146.008] | 27.183 | 6.6e-18 | 1.1e-16 | worse |
| u_bin=1.0-1.2 | edd | lpt | 124 | 124 | +30393.078 | [24589.674, 36462.100] | 27.183 | 1.0e-17 | 1.2e-16 | worse |
| u_bin=1.0-1.2 | wmdd | v2rl310 | 124 | 124 | -28.546 | [-49.849, -6.357] | 27.420 | 0.0003 | 0.0070 | inconclusive |
| u_bin=1.0-1.2 | wmdd | v2rl304 | 124 | 124 | -25.515 | [-38.925, -13.026] | 27.420 | 0.0009 | 0.0175 | inconclusive |
| u_bin=1.0-1.2 | wmdd | pfifo | 124 | 124 | -24.159 | [-35.497, -14.137] | 27.420 | 2.1e-07 | 1.3e-06 | inconclusive |
| u_bin=1.0-1.2 | wmdd | edd | 124 | 124 | -23.671 | [-35.141, -13.743] | 27.420 | 3.5e-07 | 1.7e-06 | inconclusive |
| u_bin=1.0-1.2 | wmdd | v2rl308 | 124 | 124 | -23.571 | [-41.562, -6.512] | 27.420 | 0.0283 | 0.3957 | inconclusive |
| u_bin=1.0-1.2 | wmdd | v2rl305 | 124 | 124 | -18.733 | [-42.038, 6.108] | 27.420 | 0.0216 | 0.3239 | inconclusive |
| u_bin=1.0-1.2 | wmdd | v2rl302 | 124 | 124 | -9.720 | [-29.455, 13.416] | 27.420 | 0.0805 | 0.9665 | inconclusive |
| u_bin=1.0-1.2 | wmdd | v2rl307 | 124 | 124 | -6.746 | [-33.052, 20.802] | 27.420 | 0.1289 | 1.0000 | inconclusive |
| u_bin=1.0-1.2 | wmdd | atc | 124 | 124 | +2.579 | [-2.238, 7.503] | 27.420 | 0.1165 | 0.3496 | equivalent |
| u_bin=1.0-1.2 | wmdd | v2rl301 | 124 | 124 | +3.133 | [-21.773, 31.839] | 27.420 | 0.3403 | 1.0000 | inconclusive |
| u_bin=1.0-1.2 | wmdd | v2rl306 | 124 | 124 | +5.924 | [-22.763, 41.131] | 27.420 | 0.5412 | 1.0000 | inconclusive |
| u_bin=1.0-1.2 | wmdd | rollcp2 | 8 | 8 | +14.184 | [-3.199, 45.993] | 6.177 | 1.0000 | 1.0000 | inconclusive |
| u_bin=1.0-1.2 | wmdd | v2rl309 | 124 | 124 | +253.213 | [171.344, 346.904] | 27.420 | 7.3e-15 | 2.1e-13 | worse |
| u_bin=1.0-1.2 | wmdd | v2rl303 | 124 | 124 | +258.937 | [160.050, 374.582] | 27.420 | 4.3e-08 | 1.1e-06 | worse |
| u_bin=1.0-1.2 | wmdd | wspt | 124 | 124 | +477.586 | [372.839, 589.217] | 27.420 | 5.7e-18 | 1.0e-16 | worse |
| u_bin=1.0-1.2 | wmdd | random | 124 | 124 | +6671.323 | [5289.971, 8105.730] | 27.420 | 6.8e-18 | 1.1e-16 | worse |
| u_bin=1.0-1.2 | wmdd | lpt | 124 | 124 | +30369.407 | [24556.046, 36405.304] | 27.420 | 1.2e-17 | 1.2e-16 | worse |
| u_bin=<0.5 | atc | v2rl302 | 195 | 100 | -0.567 | [-1.281, -0.038] | 2.351 | 0.0180 | 0.5388 | equivalent |
| u_bin=<0.5 | atc | v2rl310 | 195 | 100 | -0.562 | [-1.271, -0.037] | 2.351 | 0.0180 | 0.5388 | equivalent |
| u_bin=<0.5 | atc | v2rl303 | 195 | 100 | -0.533 | [-1.214, -0.037] | 2.351 | 0.0180 | 0.5388 | equivalent |
| u_bin=<0.5 | atc | v2rl305 | 195 | 100 | -0.532 | [-1.198, -0.038] | 2.351 | 0.0180 | 0.5388 | equivalent |
| u_bin=<0.5 | atc | v2rl307 | 195 | 100 | -0.517 | [-1.165, -0.037] | 2.351 | 0.0180 | 0.5388 | equivalent |
| u_bin=<0.5 | atc | v2rl301 | 195 | 100 | -0.510 | [-1.132, -0.036] | 2.351 | 0.0180 | 0.5388 | equivalent |
| u_bin=<0.5 | atc | v2rl308 | 195 | 100 | -0.489 | [-1.151, -0.037] | 2.351 | 0.0180 | 0.5388 | equivalent |
| u_bin=<0.5 | atc | edd | 195 | 100 | -0.487 | [-1.112, -0.035] | 2.351 | 0.0277 | 0.3879 | equivalent |
| u_bin=<0.5 | atc | pfifo | 195 | 100 | -0.487 | [-1.120, -0.036] | 2.351 | 0.0277 | 0.3879 | equivalent |
| u_bin=<0.5 | atc | v2rl304 | 195 | 100 | -0.454 | [-1.078, -0.037] | 2.351 | 0.0180 | 0.5388 | equivalent |
| u_bin=<0.5 | atc | rollcp2 | 59 | 32 | -0.444 | [-1.528, 0.160] | 3.008 | 0.0004 | 0.0007 | equivalent |
| u_bin=<0.5 | atc | v2rl309 | 195 | 100 | -0.356 | [-0.905, 0.014] | 2.351 | 0.0425 | 0.5953 | equivalent |
| u_bin=<0.5 | atc | v2rl306 | 195 | 100 | -0.332 | [-1.049, 0.330] | 2.351 | 0.1614 | 1.0000 | equivalent |
| u_bin=<0.5 | atc | lpt | 195 | 100 | -0.256 | [-0.913, 0.366] | 2.351 | 0.1614 | 0.8071 | equivalent |
| u_bin=<0.5 | atc | wmdd | 195 | 100 | -0.016 | [-0.082, 0.038] | 2.351 | 0.4652 | 1.0000 | equivalent |
| u_bin=<0.5 | atc | random | 195 | 100 | +0.306 | [-0.116, 0.755] | 2.351 | 0.0747 | 0.5979 | equivalent |
| u_bin=<0.5 | atc | wspt | 195 | 100 | +0.851 | [0.341, 1.506] | 2.351 | 0.0002 | 0.0033 | equivalent |
| u_bin=<0.5 | edd | v2rl302 | 195 | 100 | -0.080 | [-0.215, -0.001] | 2.347 | 0.0679 | 0.7468 | equivalent |
| u_bin=<0.5 | edd | v2rl310 | 195 | 100 | -0.075 | [-0.206, -0.001] | 2.347 | 0.0679 | 0.7468 | equivalent |
| u_bin=<0.5 | edd | v2rl303 | 195 | 100 | -0.045 | [-0.175, 0.039] | 2.347 | 0.4652 | 1.0000 | equivalent |
| u_bin=<0.5 | edd | v2rl305 | 195 | 100 | -0.045 | [-0.174, 0.039] | 2.347 | 0.8927 | 1.0000 | equivalent |
| u_bin=<0.5 | edd | v2rl307 | 195 | 100 | -0.030 | [-0.163, 0.059] | 2.347 | 0.6858 | 1.0000 | equivalent |
| u_bin=<0.5 | edd | v2rl301 | 195 | 100 | -0.022 | [-0.164, 0.078] | 2.347 | 0.6858 | 1.0000 | equivalent |
| u_bin=<0.5 | edd | v2rl308 | 195 | 100 | -0.002 | [-0.028, 0.026] | 2.347 | 0.7150 | 1.0000 | equivalent |
| u_bin=<0.5 | edd | pfifo | 195 | 100 | +0.000 | [0.000, 0.000] | 2.347 | 1.0000 | 1.0000 | equivalent |
| u_bin=<0.5 | edd | v2rl304 | 195 | 100 | +0.033 | [-0.002, 0.100] | 2.347 | 0.2850 | 1.0000 | equivalent |
| u_bin=<0.5 | edd | rollcp2 | 59 | 32 | +0.047 | [-0.114, 0.216] | 3.003 | 2.8e-05 | 8.3e-05 | equivalent |
| u_bin=<0.5 | edd | v2rl309 | 195 | 100 | +0.131 | [0.009, 0.289] | 2.347 | 0.0458 | 0.5953 | equivalent |
| u_bin=<0.5 | edd | v2rl306 | 195 | 100 | +0.155 | [-0.127, 0.588] | 2.347 | 0.3454 | 1.0000 | equivalent |
| u_bin=<0.5 | edd | lpt | 195 | 100 | +0.231 | [0.009, 0.646] | 2.347 | 0.1159 | 0.6951 | equivalent |
| u_bin=<0.5 | edd | wmdd | 195 | 100 | +0.471 | [0.041, 1.131] | 2.347 | 0.0277 | 0.3879 | equivalent |
| u_bin=<0.5 | edd | atc | 195 | 100 | +0.487 | [0.036, 1.145] | 2.347 | 0.0277 | 0.3879 | equivalent |
| u_bin=<0.5 | edd | random | 195 | 100 | +0.794 | [0.263, 1.488] | 2.347 | 0.0015 | 0.0220 | equivalent |
| u_bin=<0.5 | edd | wspt | 195 | 100 | +1.338 | [0.493, 2.384] | 2.347 | 0.0001 | 0.0024 | inconclusive |
| u_bin=<0.5 | wmdd | v2rl302 | 195 | 100 | -0.550 | [-1.283, -0.041] | 2.351 | 0.0180 | 0.5388 | equivalent |
| u_bin=<0.5 | wmdd | v2rl310 | 195 | 100 | -0.546 | [-1.244, -0.042] | 2.351 | 0.0180 | 0.5388 | equivalent |
| u_bin=<0.5 | wmdd | v2rl303 | 195 | 100 | -0.516 | [-1.213, -0.041] | 2.351 | 0.0180 | 0.5388 | equivalent |
| u_bin=<0.5 | wmdd | v2rl305 | 195 | 100 | -0.516 | [-1.188, -0.042] | 2.351 | 0.0180 | 0.5388 | equivalent |
| u_bin=<0.5 | wmdd | v2rl307 | 195 | 100 | -0.501 | [-1.146, -0.042] | 2.351 | 0.0180 | 0.5388 | equivalent |
| u_bin=<0.5 | wmdd | v2rl301 | 195 | 100 | -0.493 | [-1.136, -0.042] | 2.351 | 0.0180 | 0.5388 | equivalent |
| u_bin=<0.5 | wmdd | v2rl308 | 195 | 100 | -0.473 | [-1.146, -0.042] | 2.351 | 0.0180 | 0.5388 | equivalent |
| u_bin=<0.5 | wmdd | edd | 195 | 100 | -0.471 | [-1.149, -0.041] | 2.351 | 0.0277 | 0.3879 | equivalent |
| u_bin=<0.5 | wmdd | pfifo | 195 | 100 | -0.471 | [-1.145, -0.042] | 2.351 | 0.0277 | 0.3879 | equivalent |
| u_bin=<0.5 | wmdd | v2rl304 | 195 | 100 | -0.437 | [-1.080, -0.042] | 2.351 | 0.0180 | 0.5388 | equivalent |
| u_bin=<0.5 | wmdd | rollcp2 | 59 | 32 | -0.409 | [-1.337, 0.156] | 3.008 | 0.0004 | 0.0007 | equivalent |
| u_bin=<0.5 | wmdd | v2rl309 | 195 | 100 | -0.340 | [-0.900, 0.009] | 2.351 | 0.0425 | 0.5953 | equivalent |
| u_bin=<0.5 | wmdd | v2rl306 | 195 | 100 | -0.316 | [-1.060, 0.334] | 2.351 | 0.1614 | 1.0000 | equivalent |
| u_bin=<0.5 | wmdd | lpt | 195 | 100 | -0.240 | [-0.934, 0.354] | 2.351 | 0.1614 | 0.8071 | equivalent |
| u_bin=<0.5 | wmdd | atc | 195 | 100 | +0.016 | [-0.037, 0.078] | 2.351 | 0.4652 | 1.0000 | equivalent |
| u_bin=<0.5 | wmdd | random | 195 | 100 | +0.323 | [-0.132, 0.799] | 2.351 | 0.0869 | 0.6080 | equivalent |
| u_bin=<0.5 | wmdd | wspt | 195 | 100 | +0.867 | [0.330, 1.555] | 2.351 | 0.0002 | 0.0033 | equivalent |
| u_bin=>=1.2 | atc | v2rl310 | 179 | 125 | -12.215 | [-33.530, 8.147] | 17.293 | 0.1234 | 1.0000 | inconclusive |
| u_bin=>=1.2 | atc | edd | 179 | 125 | -11.199 | [-38.277, 19.498] | 17.293 | 0.0010 | 0.0070 | inconclusive |
| u_bin=>=1.2 | atc | pfifo | 179 | 125 | -11.191 | [-39.188, 19.579] | 17.293 | 0.0010 | 0.0070 | inconclusive |
| u_bin=>=1.2 | atc | rollcp2 | 29 | 16 | -10.770 | [-34.731, 0.010] | 2.750 | 0.9163 | 1.0000 | inconclusive |
| u_bin=>=1.2 | atc | wmdd | 179 | 125 | -7.611 | [-15.584, -0.629] | 17.293 | 0.0002 | 0.0017 | equivalent |
| u_bin=>=1.2 | atc | v2rl304 | 179 | 125 | -6.862 | [-36.871, 28.744] | 17.293 | 0.0200 | 0.3801 | inconclusive |
| u_bin=>=1.2 | atc | v2rl308 | 179 | 125 | -0.312 | [-37.145, 46.557] | 17.293 | 0.0455 | 0.6830 | inconclusive |
| u_bin=>=1.2 | atc | v2rl305 | 179 | 125 | +54.093 | [7.048, 111.868] | 17.293 | 0.9863 | 1.0000 | inconclusive |
| u_bin=>=1.2 | atc | v2rl302 | 179 | 125 | +61.010 | [16.265, 116.851] | 17.293 | 0.2518 | 1.0000 | inconclusive |
| u_bin=>=1.2 | atc | v2rl307 | 179 | 125 | +96.161 | [35.429, 175.647] | 17.293 | 0.1673 | 1.0000 | worse |
| u_bin=>=1.2 | atc | v2rl306 | 179 | 125 | +118.371 | [45.356, 209.403] | 17.293 | 0.1275 | 1.0000 | worse |
| u_bin=>=1.2 | atc | v2rl301 | 179 | 125 | +146.319 | [68.747, 243.420] | 17.293 | 0.0159 | 0.3171 | worse |
| u_bin=>=1.2 | atc | wspt | 179 | 125 | +712.837 | [517.754, 932.660] | 17.293 | 4.2e-17 | 7.1e-16 | worse |
| u_bin=>=1.2 | atc | v2rl309 | 179 | 125 | +749.804 | [510.033, 1041.490] | 17.293 | 5.3e-13 | 1.4e-11 | worse |
| u_bin=>=1.2 | atc | v2rl303 | 179 | 125 | +893.341 | [621.181, 1225.318] | 17.293 | 8.6e-13 | 2.1e-11 | worse |
| u_bin=>=1.2 | atc | random | 179 | 125 | +10411.074 | [7501.998, 13851.815] | 17.293 | 2.7e-16 | 4.1e-15 | worse |
| u_bin=>=1.2 | atc | lpt | 179 | 125 | +35909.746 | [25968.909, 47471.104] | 17.293 | 8.6e-14 | 9.5e-13 | worse |
| u_bin=>=1.2 | edd | rollcp2 | 29 | 16 | -33.179 | [-98.395, 0.010] | 2.974 | 0.9163 | 1.0000 | inconclusive |
| u_bin=>=1.2 | edd | v2rl310 | 179 | 125 | -1.017 | [-19.779, 16.253] | 17.181 | 0.7028 | 1.0000 | inconclusive |
| u_bin=>=1.2 | edd | pfifo | 179 | 125 | +0.008 | [-0.035, 0.054] | 17.181 | 0.7150 | 0.7150 | equivalent |
| u_bin=>=1.2 | edd | wmdd | 179 | 125 | +3.588 | [-27.449, 30.200] | 17.181 | 0.0045 | 0.0180 | inconclusive |
| u_bin=>=1.2 | edd | v2rl304 | 179 | 125 | +4.337 | [-12.991, 27.304] | 17.181 | 0.4094 | 1.0000 | inconclusive |
| u_bin=>=1.2 | edd | v2rl308 | 179 | 125 | +10.887 | [-14.846, 45.980] | 17.181 | 0.7600 | 1.0000 | inconclusive |
| u_bin=>=1.2 | edd | atc | 179 | 125 | +11.199 | [-18.653, 38.151] | 17.181 | 0.0010 | 0.0070 | inconclusive |
| u_bin=>=1.2 | edd | v2rl305 | 179 | 125 | +65.292 | [26.565, 116.343] | 17.181 | 0.0292 | 0.4956 | worse |
| u_bin=>=1.2 | edd | v2rl302 | 179 | 125 | +72.209 | [23.198, 135.846] | 17.181 | 0.0316 | 0.5056 | worse |
| u_bin=>=1.2 | edd | v2rl307 | 179 | 125 | +107.360 | [55.501, 170.515] | 17.181 | 0.0002 | 0.0051 | worse |
| u_bin=>=1.2 | edd | v2rl306 | 179 | 125 | +129.569 | [63.665, 211.447] | 17.181 | 6.6e-05 | 0.0015 | worse |
| u_bin=>=1.2 | edd | v2rl301 | 179 | 125 | +157.518 | [76.059, 262.021] | 17.181 | 4.7e-06 | 0.0001 | worse |
| u_bin=>=1.2 | edd | wspt | 179 | 125 | +724.036 | [525.407, 955.419] | 17.181 | 4.9e-16 | 6.4e-15 | worse |
| u_bin=>=1.2 | edd | v2rl309 | 179 | 125 | +761.003 | [510.050, 1059.757] | 17.181 | 2.0e-13 | 6.0e-12 | worse |
| u_bin=>=1.2 | edd | v2rl303 | 179 | 125 | +904.540 | [623.718, 1252.821] | 17.181 | 3.3e-13 | 9.2e-12 | worse |
| u_bin=>=1.2 | edd | random | 179 | 125 | +10422.273 | [7500.953, 13849.106] | 17.181 | 4.2e-16 | 5.8e-15 | worse |
| u_bin=>=1.2 | edd | lpt | 179 | 125 | +35920.945 | [25958.071, 47583.231] | 17.181 | 9.5e-14 | 9.5e-13 | worse |
| u_bin=>=1.2 | wmdd | v2rl310 | 179 | 125 | -4.604 | [-26.865, 17.313] | 17.217 | 0.3658 | 1.0000 | inconclusive |
| u_bin=>=1.2 | wmdd | edd | 179 | 125 | -3.588 | [-30.368, 27.278] | 17.217 | 0.0045 | 0.0180 | inconclusive |
| u_bin=>=1.2 | wmdd | pfifo | 179 | 125 | -3.580 | [-30.587, 27.972] | 17.217 | 0.0045 | 0.0180 | inconclusive |
| u_bin=>=1.2 | wmdd | rollcp2 | 29 | 16 | -3.521 | [-11.912, 0.010] | 2.677 | 0.9163 | 1.0000 | inconclusive |
| u_bin=>=1.2 | wmdd | v2rl304 | 179 | 125 | +0.749 | [-29.676, 37.338] | 17.217 | 0.1488 | 1.0000 | inconclusive |
| u_bin=>=1.2 | wmdd | v2rl308 | 179 | 125 | +7.299 | [-29.366, 54.727] | 17.217 | 0.2237 | 1.0000 | inconclusive |
| u_bin=>=1.2 | wmdd | atc | 179 | 125 | +7.611 | [0.747, 15.601] | 17.217 | 0.0002 | 0.0017 | equivalent |
| u_bin=>=1.2 | wmdd | v2rl305 | 179 | 125 | +61.704 | [12.154, 122.882] | 17.217 | 0.5479 | 1.0000 | inconclusive |
| u_bin=>=1.2 | wmdd | v2rl302 | 179 | 125 | +68.621 | [22.813, 126.805] | 17.217 | 0.0463 | 0.6830 | worse |
| u_bin=>=1.2 | wmdd | v2rl307 | 179 | 125 | +103.772 | [40.523, 183.595] | 17.217 | 0.0792 | 1.0000 | worse |
| u_bin=>=1.2 | wmdd | v2rl306 | 179 | 125 | +125.982 | [50.004, 220.931] | 17.217 | 0.0244 | 0.4389 | worse |
| u_bin=>=1.2 | wmdd | v2rl301 | 179 | 125 | +153.930 | [71.763, 252.738] | 17.217 | 0.0043 | 0.0910 | worse |
| u_bin=>=1.2 | wmdd | wspt | 179 | 125 | +720.448 | [525.255, 944.437] | 17.217 | 3.8e-17 | 6.9e-16 | worse |
| u_bin=>=1.2 | wmdd | v2rl309 | 179 | 125 | +757.415 | [514.248, 1041.716] | 17.217 | 2.0e-13 | 6.0e-12 | worse |
| u_bin=>=1.2 | wmdd | v2rl303 | 179 | 125 | +900.952 | [631.030, 1231.869] | 17.217 | 4.2e-13 | 1.1e-11 | worse |
| u_bin=>=1.2 | wmdd | random | 179 | 125 | +10418.685 | [7508.392, 13892.521] | 17.217 | 2.0e-16 | 3.2e-15 | worse |
| u_bin=>=1.2 | wmdd | lpt | 179 | 125 | +35917.357 | [25950.864, 47307.677] | 17.217 | 7.9e-14 | 9.5e-13 | worse |

