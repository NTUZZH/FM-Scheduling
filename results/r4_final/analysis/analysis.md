# Eval-B definitive analysis

Source: `results/r4_final/results.csv` (26770 rows, 887 configurations, 527 base-instance clusters, 31 methods, 0 infeasible, 0 errors). Statistics: `fmwos.stats`, protocol §R4.5, 10000 bootstrap resamples, master seed 12345, equivalence margin max(1.0, 1% of the comparator mean), Holm within each comparison family. A negative difference means the method is better than its comparator.

Coverage discipline: equivalence sets are ranked among the 30 full-coverage methods only. Rolling CP-SAT ran on 160 of 887 configurations (8 per empirical cell, 2 s budget) and appears only in its own paired rows, with that subsample size on every row.


## 1. Empirical verdict (campuses 5, 9, 10, 12)

Verdict scope: 540 configurations over 180 base instances.


### Per crew multiplier


**m=0.6** — best rl301 (mean 449.767), 180 configurations, 180 clusters. Equivalence set (15 methods): EDD and PFIFO, eight of the ten policy seeds, two of the ten attention seeds, and all three first-curriculum seeds.

| method | mean | pct_from_best | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|
| rl301 | 449.767 | 0.000 | 0.000 | 0.000 | 0.000 | 4.498 | 1.000 | equivalent | 1 |
| v2rl302 | 450.246 | 0.106 | 0.479 | -0.331 | 1.560 | 4.498 | 1.000 | equivalent | 1 |
| v2rl303 | 450.348 | 0.129 | 0.581 | -0.459 | 1.955 | 4.498 | 1.000 | equivalent | 1 |
| v2rl310 | 450.373 | 0.135 | 0.606 | 0.146 | 1.192 | 4.498 | 0.496 | equivalent | 1 |
| v2rl305 | 450.535 | 0.171 | 0.768 | -0.761 | 2.773 | 4.498 | 1.000 | equivalent | 1 |
| v2rl304 | 450.567 | 0.178 | 0.800 | -0.681 | 2.242 | 4.498 | 0.137 | equivalent | 1 |
| v2at302 | 450.733 | 0.215 | 0.966 | -0.175 | 2.792 | 4.498 | 1.000 | equivalent | 1 |
| v2rl308 | 450.975 | 0.269 | 1.208 | 0.277 | 2.370 | 4.498 | 0.060 | equivalent | 1 |
| v2rl307 | 451.134 | 0.304 | 1.367 | -0.159 | 3.504 | 4.498 | 1.000 | equivalent | 1 |
| rl302 | 451.188 | 0.316 | 1.421 | 0.049 | 3.176 | 4.498 | 1.000 | equivalent | 1 |
| v2at310 | 451.227 | 0.325 | 1.460 | 0.555 | 2.557 | 4.498 | 0.011 | equivalent | 1 |
| v2rl301 | 451.649 | 0.418 | 1.882 | 0.015 | 4.453 | 4.498 | 1.000 | equivalent | 1 |
| edd | 451.714 | 0.433 | 1.946 | 0.758 | 3.423 | 4.498 | 0.001 | equivalent | 1 |
| pfifo | 451.714 | 0.433 | 1.946 | 0.758 | 3.401 | 4.498 | 0.001 | equivalent | 1 |
| wmdd | 455.084 | 1.182 | 5.317 | 2.715 | 8.283 | 4.498 | 0.000 | inconclusive | 0 |
| atc | 456.441 | 1.484 | 6.673 | 2.934 | 10.971 | 4.498 | 0.000 | inconclusive | 0 |
| wspt | 463.777 | 3.115 | 14.010 | 7.661 | 21.522 | 4.498 | 0.000 | worse | 0 |
| random | 479.315 | 6.570 | 29.548 | 9.070 | 64.806 | 4.498 | 0.000 | worse | 0 |
| lpt | 536.749 | 19.339 | 86.982 | 20.209 | 195.522 | 4.498 | 0.000 | worse | 0 |


Seed-averaged pools (aggregates, excluded from the set):

| method | reference | mean_method | mean_ref | mean_diff | ci_lo | ci_hi | verdict |
|---|---|---|---|---|---|---|---|
| v2attnpool | atc | 455.552 | 456.441 | -0.888 | -2.581 | 0.652 | equivalent |
| v2attnpool | edd | 455.552 | 451.714 | 3.839 | 1.304 | 7.040 | inconclusive |
| v2attnpool | rl301 | 455.552 | 449.767 | 5.785 | 2.554 | 9.536 | inconclusive |
| v2attnpool | wmdd | 455.552 | 455.084 | 0.469 | -1.239 | 2.285 | equivalent |
| v2pool | atc | 451.318 | 456.441 | -5.122 | -8.733 | -1.837 | inconclusive |
| v2pool | edd | 451.318 | 451.714 | -0.395 | -1.746 | 1.022 | equivalent |
| v2pool | rl301 | 451.318 | 449.767 | 1.551 | 0.562 | 2.805 | equivalent |
| v2pool | wmdd | 451.318 | 455.084 | -3.765 | -6.280 | -1.521 | inconclusive |


Seed dispersion:

| pool | pooled_mean | min_mean | median_mean | max_mean | spread_ratio | n_seeds_in_set | seeds_outside_set |
|---|---|---|---|---|---|---|---|
| v2_mlp | 451.318 | 450.246 | 450.771 | 453.910 | 1.008 | 8 | v2rl306 v2rl309 |
| v2_attn | 455.552 | 450.733 | 455.485 | 460.801 | 1.022 | 2 | v2at301 v2at303 v2at304 v2at305 v2at306 v2at307 v2at308 v2at309 |
| v1_mlp | 450.872 | 449.767 | 451.188 | 451.660 | 1.004 | 3 |  |


Rolling CP-SAT, paired on its own 48-configuration subsample:

| reference | n_configs | n_clusters | mean_method | mean_ref | mean_diff | ci_lo | ci_hi | holm_p | verdict |
|---|---|---|---|---|---|---|---|---|---|
| atc | 48 | 48 | 510.046 | 515.157 | -5.110 | -11.759 | -0.493 | 1.000 | inconclusive |
| edd | 48 | 48 | 510.046 | 510.698 | -0.651 | -1.996 | 0.393 | 0.511 | equivalent |
| wmdd | 48 | 48 | 510.046 | 513.624 | -3.578 | -7.915 | -0.367 | 1.000 | inconclusive |


**m=0.8** — best rl301 (mean 446.214), 180 configurations, 180 clusters. Equivalence set (26 methods): EDD, PFIFO, ATC and WMDD, all ten policy seeds, nine of the ten attention seeds, and all three first-curriculum seeds.

| method | mean | pct_from_best | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|
| rl301 | 446.214 | 0.000 | 0.000 | 0.000 | 0.000 | 4.462 | 1.000 | equivalent | 1 |
| v2at302 | 446.268 | 0.012 | 0.054 | -0.470 | 0.732 | 4.462 | 1.000 | equivalent | 1 |
| v2rl301 | 446.287 | 0.017 | 0.074 | -0.436 | 0.739 | 4.462 | 1.000 | equivalent | 1 |
| v2rl307 | 446.300 | 0.019 | 0.086 | -0.429 | 0.752 | 4.462 | 1.000 | equivalent | 1 |
| v2rl305 | 446.316 | 0.023 | 0.103 | -0.435 | 0.784 | 4.462 | 1.000 | equivalent | 1 |
| rl302 | 446.318 | 0.023 | 0.104 | -0.386 | 0.671 | 4.462 | 1.000 | equivalent | 1 |
| v2rl303 | 446.318 | 0.023 | 0.105 | -0.229 | 0.601 | 4.462 | 1.000 | equivalent | 1 |
| v2rl302 | 446.325 | 0.025 | 0.111 | -0.271 | 0.717 | 4.462 | 1.000 | equivalent | 1 |
| v2rl310 | 446.371 | 0.035 | 0.157 | -0.335 | 0.803 | 4.462 | 1.000 | equivalent | 1 |
| v2rl308 | 446.465 | 0.056 | 0.252 | -0.236 | 0.911 | 4.462 | 1.000 | equivalent | 1 |
| rl303 | 446.595 | 0.086 | 0.382 | -0.311 | 1.345 | 4.462 | 1.000 | equivalent | 1 |
| v2rl304 | 446.635 | 0.094 | 0.421 | 0.031 | 1.046 | 4.462 | 0.534 | equivalent | 1 |
| edd | 446.636 | 0.095 | 0.422 | 0.063 | 0.887 | 4.462 | 0.046 | equivalent | 1 |
| pfifo | 446.636 | 0.095 | 0.422 | 0.061 | 0.894 | 4.462 | 0.046 | equivalent | 1 |
| wmdd | 447.547 | 0.299 | 1.333 | 0.468 | 2.347 | 4.462 | 0.010 | equivalent | 1 |
| atc | 448.166 | 0.438 | 1.953 | 0.770 | 3.354 | 4.462 | 0.003 | equivalent | 1 |
| wspt | 450.362 | 0.930 | 4.149 | 2.408 | 6.234 | 4.462 | 0.000 | inconclusive | 0 |
| random | 450.586 | 0.980 | 4.372 | 1.767 | 7.824 | 4.462 | 0.000 | inconclusive | 0 |
| lpt | 455.331 | 2.043 | 9.117 | 1.313 | 20.971 | 4.462 | 0.010 | inconclusive | 0 |


Seed-averaged pools (aggregates, excluded from the set):

| method | reference | mean_method | mean_ref | mean_diff | ci_lo | ci_hi | verdict |
|---|---|---|---|---|---|---|---|
| v2attnpool | atc | 447.688 | 448.166 | -0.478 | -1.068 | -0.026 | equivalent |
| v2attnpool | edd | 447.688 | 446.636 | 1.052 | 0.344 | 1.952 | equivalent |
| v2attnpool | rl301 | 447.688 | 446.214 | 1.475 | 0.606 | 2.550 | equivalent |
| v2attnpool | wmdd | 447.688 | 447.547 | 0.142 | -0.299 | 0.562 | equivalent |
| v2pool | atc | 446.490 | 448.166 | -1.677 | -3.075 | -0.559 | equivalent |
| v2pool | edd | 446.490 | 446.636 | -0.146 | -0.508 | 0.274 | equivalent |
| v2pool | rl301 | 446.490 | 446.214 | 0.276 | -0.166 | 0.903 | equivalent |
| v2pool | wmdd | 446.490 | 447.547 | -1.057 | -1.975 | -0.303 | equivalent |


Seed dispersion:

| pool | pooled_mean | min_mean | median_mean | max_mean | spread_ratio | n_seeds_in_set | seeds_outside_set |
|---|---|---|---|---|---|---|---|
| v2_mlp | 446.490 | 446.287 | 446.348 | 447.144 | 1.002 | 10 |  |
| v2_attn | 447.688 | 446.268 | 447.769 | 449.828 | 1.008 | 9 | v2at301 |
| v1_mlp | 446.376 | 446.214 | 446.318 | 446.595 | 1.001 | 3 |  |


Rolling CP-SAT, paired on its own 48-configuration subsample:

| reference | n_configs | n_clusters | mean_method | mean_ref | mean_diff | ci_lo | ci_hi | holm_p | verdict |
|---|---|---|---|---|---|---|---|---|---|
| atc | 48 | 48 | 506.036 | 507.830 | -1.793 | -4.896 | -0.014 | 0.114 | equivalent |
| edd | 48 | 48 | 506.036 | 506.547 | -0.511 | -1.330 | 0.061 | 0.086 | equivalent |
| wmdd | 48 | 48 | 506.036 | 507.219 | -1.183 | -3.375 | 0.061 | 0.086 | equivalent |


**m=1.0** — best v2rl302 (mean 444.681), 180 configurations, 180 clusters. Equivalence set (30 methods): every transparent rule, all ten policy seeds, all ten attention seeds, and all three first-curriculum seeds.

| method | mean | pct_from_best | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|
| v2rl302 | 444.681 | 0.000 | 0.000 | 0.000 | 0.000 | 4.447 | 1.000 | equivalent | 1 |
| v2rl308 | 444.708 | 0.006 | 0.027 | 0.000 | 0.065 | 4.447 | 0.979 | equivalent | 1 |
| v2rl310 | 444.712 | 0.007 | 0.031 | -0.003 | 0.083 | 4.447 | 0.979 | equivalent | 1 |
| v2at302 | 444.716 | 0.008 | 0.035 | -0.001 | 0.082 | 4.447 | 0.979 | equivalent | 1 |
| v2rl303 | 444.731 | 0.011 | 0.050 | 0.000 | 0.130 | 4.447 | 0.979 | equivalent | 1 |
| v2rl301 | 444.756 | 0.017 | 0.075 | 0.014 | 0.159 | 4.447 | 0.690 | equivalent | 1 |
| v2rl305 | 444.760 | 0.018 | 0.079 | 0.011 | 0.180 | 4.447 | 0.690 | equivalent | 1 |
| v2rl304 | 444.763 | 0.018 | 0.082 | -0.002 | 0.195 | 4.447 | 0.979 | equivalent | 1 |
| rl301 | 444.763 | 0.018 | 0.082 | -0.002 | 0.213 | 4.447 | 0.979 | equivalent | 1 |
| rl302 | 444.764 | 0.019 | 0.083 | 0.000 | 0.240 | 4.447 | 0.979 | equivalent | 1 |
| v2at310 | 444.765 | 0.019 | 0.084 | -0.006 | 0.259 | 4.447 | 0.979 | equivalent | 1 |
| v2rl307 | 444.770 | 0.020 | 0.089 | 0.012 | 0.183 | 4.447 | 0.690 | equivalent | 1 |
| edd | 444.869 | 0.042 | 0.188 | 0.023 | 0.406 | 4.447 | 0.071 | equivalent | 1 |
| pfifo | 444.869 | 0.042 | 0.188 | 0.027 | 0.404 | 4.447 | 0.071 | equivalent | 1 |
| wmdd | 445.332 | 0.146 | 0.651 | 0.165 | 1.274 | 4.447 | 0.063 | equivalent | 1 |
| atc | 445.555 | 0.197 | 0.874 | 0.263 | 1.641 | 4.447 | 0.051 | equivalent | 1 |
| lpt | 445.579 | 0.202 | 0.898 | 0.074 | 2.438 | 4.447 | 0.038 | equivalent | 1 |
| random | 446.316 | 0.368 | 1.635 | 0.572 | 3.181 | 4.447 | 0.001 | equivalent | 1 |
| wspt | 446.646 | 0.442 | 1.965 | 0.891 | 3.312 | 4.447 | 0.000 | equivalent | 1 |


Seed-averaged pools (aggregates, excluded from the set):

| method | reference | mean_method | mean_ref | mean_diff | ci_lo | ci_hi | verdict |
|---|---|---|---|---|---|---|---|
| v2attnpool | atc | 445.268 | 445.555 | -0.287 | -0.599 | -0.037 | equivalent |
| v2attnpool | edd | 445.268 | 444.869 | 0.399 | 0.067 | 0.835 | equivalent |
| v2attnpool | v2rl302 | 445.268 | 444.681 | 0.587 | 0.173 | 1.136 | equivalent |
| v2attnpool | wmdd | 445.268 | 445.332 | -0.064 | -0.337 | 0.183 | equivalent |
| v2pool | atc | 444.769 | 445.555 | -0.786 | -1.488 | -0.210 | equivalent |
| v2pool | edd | 444.769 | 444.869 | -0.100 | -0.260 | 0.024 | equivalent |
| v2pool | v2rl302 | 444.769 | 444.681 | 0.088 | 0.021 | 0.184 | equivalent |
| v2pool | wmdd | 444.769 | 445.332 | -0.563 | -1.109 | -0.126 | equivalent |


Seed dispersion:

| pool | pooled_mean | min_mean | median_mean | max_mean | spread_ratio | n_seeds_in_set | seeds_outside_set |
|---|---|---|---|---|---|---|---|
| v2_mlp | 444.769 | 444.681 | 444.758 | 444.953 | 1.001 | 10 |  |
| v2_attn | 445.268 | 444.716 | 445.252 | 445.884 | 1.003 | 10 |  |
| v1_mlp | 444.810 | 444.763 | 444.764 | 444.902 | 1.000 | 3 |  |


Rolling CP-SAT, paired on its own 48-configuration subsample:

| reference | n_configs | n_clusters | mean_method | mean_ref | mean_diff | ci_lo | ci_hi | holm_p | verdict |
|---|---|---|---|---|---|---|---|---|---|
| atc | 48 | 48 | 505.808 | 506.296 | -0.488 | -1.553 | 0.064 | 0.007 | equivalent |
| edd | 48 | 48 | 505.808 | 505.828 | -0.020 | -0.145 | 0.053 | 0.002 | equivalent |
| wmdd | 48 | 48 | 505.808 | 506.222 | -0.414 | -1.325 | 0.053 | 0.002 | equivalent |


### Per realized-utilization bin (empirical regime only)


**u_bin=0.5-0.8** — best v2rl303 (mean 686.471), 152 configurations, 103 clusters. Equivalence set (21 methods): EDD, PFIFO and WMDD, all ten policy seeds, five of the ten attention seeds, and all three first-curriculum seeds.

| method | mean | pct_from_best | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|
| v2rl303 | 686.471 | 0.000 | 0.000 | 0.000 | 0.000 | 6.865 | 1.000 | equivalent | 1 |
| rl301 | 686.539 | 0.010 | 0.069 | -0.551 | 0.551 | 6.865 | 1.000 | equivalent | 1 |
| v2at302 | 686.646 | 0.026 | 0.176 | -0.204 | 0.637 | 6.865 | 1.000 | equivalent | 1 |
| v2rl305 | 686.713 | 0.035 | 0.243 | -0.170 | 0.710 | 6.865 | 1.000 | equivalent | 1 |
| v2rl306 | 686.718 | 0.036 | 0.247 | -0.197 | 0.851 | 6.865 | 1.000 | equivalent | 1 |
| v2rl310 | 686.723 | 0.037 | 0.252 | -0.123 | 0.711 | 6.865 | 1.000 | equivalent | 1 |
| v2rl301 | 686.767 | 0.043 | 0.296 | -0.160 | 0.914 | 6.865 | 1.000 | equivalent | 1 |
| v2rl302 | 686.848 | 0.055 | 0.378 | -0.006 | 1.032 | 6.865 | 1.000 | equivalent | 1 |
| v2rl308 | 686.853 | 0.056 | 0.383 | -0.041 | 0.967 | 6.865 | 1.000 | equivalent | 1 |
| v2rl307 | 686.937 | 0.068 | 0.466 | -0.137 | 1.373 | 6.865 | 1.000 | equivalent | 1 |
| rl302 | 687.047 | 0.084 | 0.576 | -0.210 | 1.906 | 6.865 | 1.000 | equivalent | 1 |
| v2at310 | 687.418 | 0.138 | 0.948 | 0.039 | 2.487 | 6.865 | 0.531 | equivalent | 1 |
| edd | 687.457 | 0.144 | 0.986 | 0.126 | 2.145 | 6.865 | 0.017 | equivalent | 1 |
| pfifo | 687.457 | 0.144 | 0.986 | 0.108 | 2.162 | 6.865 | 0.017 | equivalent | 1 |
| wmdd | 689.239 | 0.403 | 2.769 | 0.547 | 5.827 | 6.865 | 0.004 | equivalent | 1 |
| atc | 689.987 | 0.512 | 3.516 | 0.735 | 7.335 | 6.865 | 0.002 | inconclusive | 0 |
| wspt | 692.771 | 0.918 | 6.301 | 2.094 | 12.215 | 6.865 | 0.000 | inconclusive | 0 |
| random | 693.841 | 1.074 | 7.370 | 1.929 | 15.148 | 6.865 | 0.000 | inconclusive | 0 |
| lpt | 707.290 | 3.033 | 20.819 | 2.635 | 46.698 | 6.865 | 0.003 | inconclusive | 0 |


Seed-averaged pools (aggregates, excluded from the set):

| method | reference | mean_method | mean_ref | mean_diff | ci_lo | ci_hi | verdict |
|---|---|---|---|---|---|---|---|
| v2attnpool | atc | 689.615 | 689.987 | -0.372 | -1.085 | 0.189 | equivalent |
| v2attnpool | edd | 689.615 | 687.457 | 2.158 | 0.394 | 4.837 | equivalent |
| v2attnpool | v2rl303 | 689.615 | 686.471 | 3.144 | 0.627 | 6.922 | inconclusive |
| v2attnpool | wmdd | 689.615 | 689.239 | 0.375 | -0.448 | 1.480 | equivalent |
| v2pool | atc | 686.956 | 689.987 | -3.031 | -6.245 | -0.589 | equivalent |
| v2pool | edd | 686.956 | 687.457 | -0.501 | -1.231 | 0.145 | equivalent |
| v2pool | v2rl303 | 686.956 | 686.471 | 0.485 | 0.020 | 1.255 | equivalent |
| v2pool | wmdd | 686.956 | 689.239 | -2.284 | -4.699 | -0.397 | equivalent |


Rolling CP-SAT, paired on its own 47-configuration subsample:

| reference | n_configs | n_clusters | mean_method | mean_ref | mean_diff | ci_lo | ci_hi | holm_p | verdict |
|---|---|---|---|---|---|---|---|---|---|
| atc | 47 | 29 | 796.818 | 800.961 | -4.143 | -11.456 | -0.150 | 0.509 | inconclusive |
| edd | 47 | 29 | 796.818 | 797.293 | -0.474 | -1.136 | 0.037 | 0.072 | equivalent |
| wmdd | 47 | 29 | 796.818 | 799.580 | -2.762 | -7.713 | 0.039 | 0.193 | equivalent |


**u_bin=0.8-1.0** — best v2rl305 (mean 622.246), 64 configurations, 64 clusters. Equivalence set (13 methods): eight of the ten policy seeds, two of the ten attention seeds, and all three first-curriculum seeds.

| method | mean | pct_from_best | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|
| v2rl305 | 622.246 | 0.000 | 0.000 | 0.000 | 0.000 | 6.222 | 1.000 | equivalent | 1 |
| v2rl302 | 622.780 | 0.086 | 0.534 | -1.280 | 3.077 | 6.222 | 1.000 | equivalent | 1 |
| v2rl301 | 622.945 | 0.112 | 0.699 | -0.035 | 2.111 | 6.222 | 1.000 | equivalent | 1 |
| v2rl307 | 623.008 | 0.122 | 0.762 | -0.954 | 3.274 | 6.222 | 1.000 | equivalent | 1 |
| v2at302 | 623.064 | 0.131 | 0.818 | -0.747 | 3.264 | 6.222 | 1.000 | equivalent | 1 |
| v2rl303 | 623.181 | 0.150 | 0.935 | -0.654 | 3.396 | 6.222 | 1.000 | equivalent | 1 |
| rl302 | 623.216 | 0.156 | 0.970 | -0.826 | 3.550 | 6.222 | 1.000 | equivalent | 1 |
| rl303 | 623.260 | 0.163 | 1.014 | 0.025 | 2.295 | 6.222 | 0.747 | equivalent | 1 |
| rl301 | 623.442 | 0.192 | 1.195 | -0.630 | 3.848 | 6.222 | 1.000 | equivalent | 1 |
| v2rl310 | 623.965 | 0.276 | 1.718 | 0.060 | 4.276 | 6.222 | 0.510 | equivalent | 1 |
| v2at310 | 624.749 | 0.402 | 2.503 | 0.347 | 5.336 | 6.222 | 0.393 | equivalent | 1 |
| v2rl308 | 624.782 | 0.408 | 2.536 | 0.402 | 5.460 | 6.222 | 0.305 | equivalent | 1 |
| edd | 625.242 | 0.481 | 2.995 | 0.118 | 6.664 | 6.222 | 0.094 | inconclusive | 0 |
| pfifo | 625.242 | 0.481 | 2.995 | 0.153 | 6.793 | 6.222 | 0.094 | inconclusive | 0 |
| wmdd | 628.198 | 0.957 | 5.952 | 1.181 | 11.748 | 6.222 | 0.083 | inconclusive | 0 |
| atc | 628.286 | 0.971 | 6.040 | 1.149 | 12.718 | 6.222 | 0.083 | inconclusive | 0 |
| wspt | 634.473 | 1.965 | 12.227 | 4.635 | 22.433 | 6.222 | 0.002 | inconclusive | 0 |
| random | 637.047 | 2.379 | 14.801 | 5.768 | 26.451 | 6.222 | 0.001 | inconclusive | 0 |
| lpt | 661.603 | 6.325 | 39.356 | 11.944 | 77.368 | 6.222 | 0.007 | worse | 0 |


Seed-averaged pools (aggregates, excluded from the set):

| method | reference | mean_method | mean_ref | mean_diff | ci_lo | ci_hi | verdict |
|---|---|---|---|---|---|---|---|
| v2attnpool | atc | 627.589 | 628.286 | -0.697 | -2.348 | 0.771 | equivalent |
| v2attnpool | edd | 627.589 | 625.242 | 2.347 | -0.827 | 5.981 | equivalent |
| v2attnpool | v2rl305 | 627.589 | 622.246 | 5.343 | 1.293 | 11.425 | inconclusive |
| v2attnpool | wmdd | 627.589 | 628.198 | -0.609 | -4.050 | 1.924 | equivalent |
| v2pool | atc | 624.171 | 628.286 | -4.114 | -9.564 | 0.467 | inconclusive |
| v2pool | edd | 624.171 | 625.242 | -1.070 | -2.371 | 0.056 | equivalent |
| v2pool | v2rl305 | 624.171 | 622.246 | 1.925 | 0.055 | 4.543 | equivalent |
| v2pool | wmdd | 624.171 | 628.198 | -4.027 | -7.697 | -1.061 | inconclusive |


Rolling CP-SAT, paired on its own 13-configuration subsample:

| reference | n_configs | n_clusters | mean_method | mean_ref | mean_diff | ci_lo | ci_hi | holm_p | verdict |
|---|---|---|---|---|---|---|---|---|---|
| atc | 13 | 13 | 851.349 | 859.727 | -8.378 | -25.059 | 0.426 | 1.000 | inconclusive |
| edd | 13 | 13 | 851.349 | 853.590 | -2.241 | -6.656 | 0.426 | 1.000 | equivalent |
| wmdd | 13 | 13 | 851.349 | 857.886 | -6.537 | -17.811 | 0.420 | 1.000 | inconclusive |


**u_bin=1.0-1.2** — best v2rl304 (mean 605.007), 37 configurations, 37 clusters. Equivalence set (1 methods): one of the ten policy seeds.

| method | mean | pct_from_best | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|
| v2rl304 | 605.007 | 0.000 | 0.000 | 0.000 | 0.000 | 6.050 | 1.000 | equivalent | 1 |
| rl301 | 607.113 | 0.348 | 2.105 | -0.829 | 7.419 | 6.050 | 1.000 | inconclusive | 0 |
| v2rl310 | 607.830 | 0.466 | 2.822 | -0.329 | 8.911 | 6.050 | 1.000 | inconclusive | 0 |
| v2rl308 | 607.917 | 0.481 | 2.910 | 0.046 | 7.192 | 6.050 | 1.000 | inconclusive | 0 |
| edd | 608.195 | 0.527 | 3.188 | 0.275 | 8.055 | 6.050 | 0.076 | inconclusive | 0 |
| pfifo | 608.195 | 0.527 | 3.188 | 0.242 | 8.075 | 6.050 | 0.076 | inconclusive | 0 |
| v2rl303 | 608.325 | 0.548 | 3.318 | -0.642 | 9.033 | 6.050 | 1.000 | inconclusive | 0 |
| v2rl302 | 608.889 | 0.642 | 3.882 | -0.356 | 10.266 | 6.050 | 1.000 | inconclusive | 0 |
| v2at310 | 609.052 | 0.668 | 4.044 | -0.250 | 11.514 | 6.050 | 1.000 | inconclusive | 0 |
| rl302 | 610.582 | 0.921 | 5.575 | 0.010 | 16.249 | 6.050 | 1.000 | inconclusive | 0 |
| v2at302 | 611.361 | 1.050 | 6.353 | -0.473 | 16.716 | 6.050 | 1.000 | inconclusive | 0 |
| v2at309 | 611.566 | 1.084 | 6.559 | 0.776 | 16.155 | 6.050 | 0.649 | inconclusive | 0 |
| wmdd | 612.699 | 1.271 | 7.691 | 1.271 | 18.399 | 6.050 | 0.033 | inconclusive | 0 |
| atc | 615.280 | 1.698 | 10.273 | 2.099 | 23.755 | 6.050 | 0.031 | inconclusive | 0 |
| wspt | 627.080 | 3.648 | 22.072 | 5.652 | 49.196 | 6.050 | 0.010 | inconclusive | 0 |
| random | 695.380 | 14.937 | 90.372 | 7.176 | 249.142 | 6.050 | 0.014 | worse | 0 |
| lpt | 837.919 | 38.497 | 232.911 | 8.456 | 668.078 | 6.050 | 0.025 | worse | 0 |


Seed-averaged pools (aggregates, excluded from the set):

| method | reference | mean_method | mean_ref | mean_diff | ci_lo | ci_hi | verdict |
|---|---|---|---|---|---|---|---|
| v2attnpool | atc | 615.667 | 615.280 | 0.387 | -3.249 | 4.768 | equivalent |
| v2attnpool | edd | 615.667 | 608.195 | 7.472 | 0.594 | 19.037 | inconclusive |
| v2attnpool | v2rl304 | 615.667 | 605.007 | 10.660 | 1.628 | 26.861 | inconclusive |
| v2attnpool | wmdd | 615.667 | 612.699 | 2.969 | -1.576 | 9.783 | inconclusive |
| v2pool | atc | 611.071 | 615.280 | -4.210 | -10.359 | 1.430 | inconclusive |
| v2pool | edd | 611.071 | 608.195 | 2.875 | -0.997 | 8.422 | inconclusive |
| v2pool | v2rl304 | 611.071 | 605.007 | 6.063 | 0.291 | 15.066 | inconclusive |
| v2pool | wmdd | 611.071 | 612.699 | -1.628 | -5.788 | 3.431 | equivalent |


Rolling CP-SAT, paired on its own 7-configuration subsample:

| reference | n_configs | n_clusters | mean_method | mean_ref | mean_diff | ci_lo | ci_hi | holm_p | verdict |
|---|---|---|---|---|---|---|---|---|---|
| atc | 7 | 7 | 584.193 | 587.762 | -3.569 | -8.256 | 0.019 | 1.000 | inconclusive |
| edd | 7 | 7 | 584.193 | 585.357 | -1.164 | -3.456 | 0.019 | 1.000 | equivalent |
| wmdd | 7 | 7 | 584.193 | 585.551 | -1.357 | -3.804 | 0.019 | 1.000 | equivalent |


**u_bin=<0.5** — best rl302 (mean 248.965), 180 configurations, 85 clusters. Equivalence set (29 methods): EDD, PFIFO, ATC, WMDD, LPT and random, all ten policy seeds, all ten attention seeds, and all three first-curriculum seeds.

| method | mean | pct_from_best | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|
| rl302 | 248.965 | 0.000 | 0.000 | 0.000 | 0.000 | 2.490 | 1.000 | equivalent | 1 |
| v2rl302 | 248.965 | 0.000 | 0.000 | 0.000 | 0.000 | 2.490 | 1.000 | equivalent | 1 |
| v2rl310 | 248.970 | 0.002 | 0.005 | -0.008 | 0.025 | 2.490 | 1.000 | equivalent | 1 |
| v2at302 | 248.982 | 0.007 | 0.016 | -0.008 | 0.059 | 2.490 | 1.000 | equivalent | 1 |
| v2rl303 | 249.002 | 0.015 | 0.037 | 0.000 | 0.104 | 2.490 | 1.000 | equivalent | 1 |
| v2rl305 | 249.003 | 0.015 | 0.038 | 0.000 | 0.105 | 2.490 | 1.000 | equivalent | 1 |
| v2at305 | 249.007 | 0.017 | 0.041 | 0.000 | 0.116 | 2.490 | 1.000 | equivalent | 1 |
| v2rl307 | 249.019 | 0.022 | 0.054 | 0.000 | 0.141 | 2.490 | 1.000 | equivalent | 1 |
| rl301 | 249.023 | 0.023 | 0.058 | 0.000 | 0.151 | 2.490 | 1.000 | equivalent | 1 |
| v2rl301 | 249.027 | 0.025 | 0.062 | 0.000 | 0.162 | 2.490 | 1.000 | equivalent | 1 |
| v2rl308 | 249.049 | 0.034 | 0.084 | 0.000 | 0.247 | 2.490 | 1.000 | equivalent | 1 |
| edd | 249.051 | 0.035 | 0.086 | 0.001 | 0.232 | 2.490 | 0.136 | equivalent | 1 |
| pfifo | 249.051 | 0.035 | 0.086 | 0.001 | 0.231 | 2.490 | 0.136 | equivalent | 1 |
| lpt | 249.302 | 0.135 | 0.336 | 0.022 | 0.839 | 2.490 | 0.129 | equivalent | 1 |
| wmdd | 249.561 | 0.240 | 0.596 | 0.046 | 1.369 | 2.490 | 0.090 | equivalent | 1 |
| atc | 249.579 | 0.247 | 0.614 | 0.040 | 1.397 | 2.490 | 0.090 | equivalent | 1 |
| random | 249.850 | 0.355 | 0.885 | 0.241 | 1.726 | 2.490 | 0.013 | equivalent | 1 |
| wspt | 250.412 | 0.581 | 1.447 | 0.459 | 2.669 | 2.490 | 0.001 | inconclusive | 0 |


Seed-averaged pools (aggregates, excluded from the set):

| method | reference | mean_method | mean_ref | mean_diff | ci_lo | ci_hi | verdict |
|---|---|---|---|---|---|---|---|
| v2attnpool | atc | 249.476 | 249.579 | -0.103 | -0.437 | 0.144 | equivalent |
| v2attnpool | edd | 249.476 | 249.051 | 0.425 | 0.097 | 0.873 | equivalent |
| v2attnpool | rl302 | 249.476 | 248.965 | 0.511 | 0.108 | 1.031 | equivalent |
| v2attnpool | wmdd | 249.476 | 249.561 | -0.085 | -0.452 | 0.178 | equivalent |
| v2pool | atc | 249.054 | 249.579 | -0.526 | -1.208 | -0.015 | equivalent |
| v2pool | edd | 249.054 | 249.051 | 0.002 | -0.103 | 0.085 | equivalent |
| v2pool | rl302 | 249.054 | 248.965 | 0.088 | 0.021 | 0.174 | equivalent |
| v2pool | wmdd | 249.054 | 249.561 | -0.508 | -1.208 | -0.021 | equivalent |


Rolling CP-SAT, paired on its own 54-configuration subsample:

| reference | n_configs | n_clusters | mean_method | mean_ref | mean_diff | ci_lo | ci_hi | holm_p | verdict |
|---|---|---|---|---|---|---|---|---|---|
| atc | 54 | 27 | 321.201 | 321.688 | -0.486 | -1.671 | 0.173 | 0.001 | equivalent |
| edd | 54 | 27 | 321.201 | 321.151 | 0.051 | -0.124 | 0.235 | 0.000 | equivalent |
| wmdd | 54 | 27 | 321.201 | 321.649 | -0.448 | -1.499 | 0.171 | 0.001 | equivalent |


**u_bin=>=1.2** — best rl301 (mean 278.434), 107 configurations, 53 clusters. Equivalence set (12 methods): seven of the ten policy seeds, two of the ten attention seeds, and all three first-curriculum seeds.

| method | mean | pct_from_best | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|
| rl301 | 278.434 | 0.000 | 0.000 | 0.000 | 0.000 | 2.784 | 1.000 | equivalent | 1 |
| v2rl307 | 278.522 | 0.032 | 0.089 | -0.245 | 0.538 | 2.784 | 1.000 | equivalent | 1 |
| v2rl302 | 278.727 | 0.105 | 0.293 | -0.005 | 0.800 | 2.784 | 1.000 | equivalent | 1 |
| v2at302 | 278.746 | 0.112 | 0.312 | 0.000 | 0.817 | 2.784 | 1.000 | equivalent | 1 |
| v2rl305 | 278.783 | 0.126 | 0.350 | -0.005 | 0.946 | 2.784 | 1.000 | equivalent | 1 |
| v2rl301 | 278.834 | 0.144 | 0.400 | -0.003 | 0.937 | 2.784 | 1.000 | equivalent | 1 |
| v2rl304 | 278.859 | 0.153 | 0.425 | 0.000 | 1.187 | 2.784 | 1.000 | equivalent | 1 |
| v2at310 | 278.896 | 0.166 | 0.463 | 0.019 | 1.328 | 2.784 | 1.000 | equivalent | 1 |
| v2rl310 | 278.899 | 0.167 | 0.465 | 0.031 | 1.245 | 2.784 | 0.473 | equivalent | 1 |
| rl303 | 279.042 | 0.219 | 0.609 | -0.002 | 1.632 | 2.784 | 1.000 | equivalent | 1 |
| v2rl308 | 279.226 | 0.284 | 0.792 | -0.005 | 2.360 | 2.784 | 1.000 | equivalent | 1 |
| rl302 | 279.313 | 0.316 | 0.879 | -0.013 | 2.459 | 2.784 | 1.000 | equivalent | 1 |
| edd | 279.795 | 0.489 | 1.361 | 0.098 | 3.307 | 2.784 | 0.252 | inconclusive | 0 |
| pfifo | 279.795 | 0.489 | 1.361 | 0.097 | 3.361 | 2.784 | 0.252 | inconclusive | 0 |
| wmdd | 281.058 | 0.943 | 2.624 | 0.425 | 5.908 | 2.784 | 0.252 | inconclusive | 0 |
| atc | 282.722 | 1.540 | 4.288 | 0.492 | 9.932 | 2.784 | 0.250 | inconclusive | 0 |
| wspt | 287.454 | 3.240 | 9.021 | 3.045 | 17.610 | 2.784 | 0.000 | worse | 0 |
| random | 287.684 | 3.322 | 9.251 | 2.298 | 18.971 | 2.784 | 0.000 | inconclusive | 0 |
| lpt | 308.885 | 10.937 | 30.451 | 0.385 | 91.488 | 2.784 | 0.252 | inconclusive | 0 |


Seed-averaged pools (aggregates, excluded from the set):

| method | reference | mean_method | mean_ref | mean_diff | ci_lo | ci_hi | verdict |
|---|---|---|---|---|---|---|---|
| v2attnpool | atc | 280.925 | 282.722 | -1.797 | -4.341 | 0.067 | inconclusive |
| v2attnpool | edd | 280.925 | 279.795 | 1.131 | -0.172 | 2.770 | equivalent |
| v2attnpool | rl301 | 280.925 | 278.434 | 2.492 | 0.440 | 5.465 | inconclusive |
| v2attnpool | wmdd | 280.925 | 281.058 | -0.133 | -1.049 | 0.597 | equivalent |
| v2pool | atc | 279.069 | 282.722 | -3.653 | -8.119 | -0.437 | inconclusive |
| v2pool | edd | 279.069 | 279.795 | -0.725 | -2.186 | 0.270 | equivalent |
| v2pool | rl301 | 279.069 | 278.434 | 0.636 | 0.026 | 1.588 | equivalent |
| v2pool | wmdd | 279.069 | 281.058 | -1.989 | -4.487 | -0.319 | inconclusive |


Rolling CP-SAT, paired on its own 23-configuration subsample:

| reference | n_configs | n_clusters | mean_method | mean_ref | mean_diff | ci_lo | ci_hi | holm_p | verdict |
|---|---|---|---|---|---|---|---|---|---|
| atc | 23 | 10 | 134.719 | 134.715 | 0.005 | 0.000 | 0.014 | 0.307 | equivalent |
| edd | 23 | 10 | 134.719 | 134.715 | 0.005 | 0.000 | 0.014 | 0.307 | equivalent |
| wmdd | 23 | 10 | 134.719 | 134.715 | 0.005 | 0.000 | 0.014 | 0.307 | equivalent |


### Per crew multiplier and utilization bin (cross)

| scope | best | mean_best | n_clusters | set_size |
|---|---|---|---|---|
| m=0.6|u_bin=0.5-0.8 | v2rl303 | 422.380 | 48 | 9 |
| m=0.6|u_bin=0.8-1.0 | v2rl305 | 677.095 | 27 | 3 |
| m=0.6|u_bin=1.0-1.2 | v2rl304 | 1039.157 | 18 | 1 |
| m=0.6|u_bin=<0.5 | rl302 | 147.944 | 34 | 16 |
| m=0.6|u_bin=>=1.2 | rl301 | 348.744 | 53 | 10 |
| m=0.8|u_bin=0.5-0.8 | rl301 | 756.785 | 52 | 23 |
| m=0.8|u_bin=0.8-1.0 | v2at305 | 746.531 | 24 | 28 |
| m=0.8|u_bin=1.0-1.2 | rl301 | 279.988 | 13 | 11 |
| m=0.8|u_bin=<0.5 | rl302 | 223.940 | 61 | 29 |
| m=0.8|u_bin=>=1.2 | rl301 | 191.510 | 30 | 28 |
| m=1.0|u_bin=0.5-0.8 | rl303 | 859.602 | 52 | 30 |
| m=1.0|u_bin=0.8-1.0 | v2at302 | 278.728 | 13 | 13 |
| m=1.0|u_bin=1.0-1.2 | atc | 5.667 | 6 | 30 |
| m=1.0|u_bin=<0.5 | v2at302 | 307.327 | 85 | 30 |
| m=1.0|u_bin=>=1.2 | atc | 231.756 | 24 | 28 |


## 2. Generator verdict (fixed-window cells, rolling CP-SAT absent)


**u_target=0.7** — best rl301 (mean 2257.500), 60 configurations, 60 clusters. Equivalence set (27 methods): EDD, PFIFO, WSPT, ATC and WMDD, all ten policy seeds, nine of the ten attention seeds, and all three first-curriculum seeds.

| method | mean | pct_from_best | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|
| rl301 | 2257.500 | 0.000 | 0.000 | 0.000 | 0.000 | 22.575 | 1.000 | equivalent | 1 |
| v2rl307 | 2257.543 | 0.002 | 0.043 | -0.600 | 0.648 | 22.575 | 1.000 | equivalent | 1 |
| v2at302 | 2257.573 | 0.003 | 0.074 | -0.562 | 0.699 | 22.575 | 1.000 | equivalent | 1 |
| v2rl301 | 2257.635 | 0.006 | 0.135 | -0.554 | 0.820 | 22.575 | 1.000 | equivalent | 1 |
| v2rl302 | 2257.737 | 0.011 | 0.237 | -0.435 | 0.968 | 22.575 | 1.000 | equivalent | 1 |
| v2rl304 | 2257.766 | 0.012 | 0.266 | -0.405 | 0.986 | 22.575 | 1.000 | equivalent | 1 |
| v2rl310 | 2257.799 | 0.013 | 0.299 | -0.392 | 1.065 | 22.575 | 1.000 | equivalent | 1 |
| v2rl306 | 2257.846 | 0.015 | 0.346 | -0.354 | 1.065 | 22.575 | 1.000 | equivalent | 1 |
| v2rl305 | 2257.848 | 0.015 | 0.349 | -0.378 | 1.098 | 22.575 | 1.000 | equivalent | 1 |
| v2rl308 | 2257.857 | 0.016 | 0.357 | -0.277 | 1.000 | 22.575 | 1.000 | equivalent | 1 |
| edd | 2258.266 | 0.034 | 0.766 | 0.050 | 1.487 | 22.575 | 0.136 | equivalent | 1 |
| pfifo | 2258.266 | 0.034 | 0.766 | 0.064 | 1.501 | 22.575 | 0.136 | equivalent | 1 |
| atc | 2258.746 | 0.055 | 1.246 | 0.165 | 2.539 | 22.575 | 0.136 | equivalent | 1 |
| wmdd | 2259.155 | 0.073 | 1.655 | 0.783 | 2.707 | 22.575 | 0.003 | equivalent | 1 |
| wspt | 2269.049 | 0.512 | 11.549 | 6.448 | 18.132 | 22.575 | 0.000 | equivalent | 1 |
| random | 2304.053 | 2.062 | 46.553 | 24.585 | 73.891 | 22.575 | 0.000 | worse | 0 |
| lpt | 2574.504 | 14.042 | 317.004 | 201.646 | 457.447 | 22.575 | 0.000 | worse | 0 |


**u_target=0.9** — best v2at302 (mean 2990.305), 60 configurations, 60 clusters. Equivalence set (15 methods): EDD, PFIFO and WMDD, eight of the ten policy seeds, three of the ten attention seeds, and one of the three first-curriculum seeds.

| method | mean | pct_from_best | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|
| v2at302 | 2990.305 | 0.000 | 0.000 | 0.000 | 0.000 | 29.903 | 1.000 | equivalent | 1 |
| v2rl301 | 2990.815 | 0.017 | 0.510 | -1.680 | 2.517 | 29.903 | 0.577 | equivalent | 1 |
| v2rl310 | 2990.941 | 0.021 | 0.635 | -1.759 | 3.152 | 29.903 | 0.582 | equivalent | 1 |
| rl301 | 2991.641 | 0.045 | 1.335 | -0.975 | 3.512 | 29.903 | 0.577 | equivalent | 1 |
| v2rl305 | 2991.994 | 0.056 | 1.689 | -0.185 | 3.825 | 29.903 | 0.557 | equivalent | 1 |
| v2rl302 | 2993.477 | 0.106 | 3.172 | 0.917 | 5.664 | 29.903 | 0.010 | equivalent | 1 |
| v2rl306 | 2993.642 | 0.112 | 3.336 | 0.273 | 6.956 | 29.903 | 0.121 | equivalent | 1 |
| v2rl307 | 2993.989 | 0.123 | 3.684 | 1.416 | 6.125 | 29.903 | 0.053 | equivalent | 1 |
| v2rl308 | 2995.290 | 0.167 | 4.985 | 2.266 | 8.038 | 29.903 | 0.022 | equivalent | 1 |
| v2rl304 | 2997.740 | 0.249 | 7.434 | 3.746 | 11.593 | 29.903 | 0.005 | equivalent | 1 |
| edd | 3000.471 | 0.340 | 10.166 | 4.776 | 16.335 | 29.903 | 0.005 | equivalent | 1 |
| pfifo | 3000.471 | 0.340 | 10.166 | 4.948 | 16.369 | 29.903 | 0.005 | equivalent | 1 |
| wmdd | 3008.921 | 0.623 | 18.616 | 9.999 | 28.570 | 29.903 | 0.000 | equivalent | 1 |
| atc | 3011.755 | 0.717 | 21.450 | 12.379 | 32.108 | 29.903 | 0.000 | inconclusive | 0 |
| wspt | 3214.838 | 7.509 | 224.532 | 161.631 | 294.077 | 29.903 | 0.000 | worse | 0 |
| random | 4924.665 | 64.688 | 1934.359 | 1496.573 | 2383.435 | 29.903 | 0.000 | worse | 0 |
| lpt | 16524.005 | 452.586 | 13533.699 | 10837.200 | 16378.540 | 29.903 | 0.000 | worse | 0 |


**u_target=1.0** — best rl301 (mean 3104.700), 60 configurations, 60 clusters. Equivalence set (12 methods): EDD and PFIFO, eight of the ten policy seeds, one of the ten attention seeds, and one of the three first-curriculum seeds.

| method | mean | pct_from_best | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|
| rl301 | 3104.700 | 0.000 | 0.000 | 0.000 | 0.000 | 31.047 | 1.000 | equivalent | 1 |
| v2at302 | 3107.801 | 0.100 | 3.101 | -2.670 | 8.878 | 31.047 | 0.540 | equivalent | 1 |
| v2rl310 | 3108.184 | 0.112 | 3.484 | -0.237 | 7.652 | 31.047 | 0.244 | equivalent | 1 |
| v2rl305 | 3108.860 | 0.134 | 4.159 | -0.456 | 9.193 | 31.047 | 0.405 | equivalent | 1 |
| v2rl308 | 3113.170 | 0.273 | 8.470 | 3.259 | 14.248 | 31.047 | 0.017 | equivalent | 1 |
| v2rl307 | 3113.954 | 0.298 | 9.254 | 3.078 | 16.820 | 31.047 | 0.044 | equivalent | 1 |
| v2rl302 | 3115.302 | 0.341 | 10.601 | 3.356 | 19.131 | 31.047 | 0.020 | equivalent | 1 |
| v2rl306 | 3115.719 | 0.355 | 11.019 | 4.891 | 18.140 | 31.047 | 0.009 | equivalent | 1 |
| v2rl304 | 3117.911 | 0.426 | 13.211 | 6.282 | 21.005 | 31.047 | 0.009 | equivalent | 1 |
| v2rl301 | 3118.047 | 0.430 | 13.347 | 5.442 | 23.040 | 31.047 | 0.025 | equivalent | 1 |
| edd | 3120.226 | 0.500 | 15.526 | 7.456 | 24.946 | 31.047 | 0.003 | equivalent | 1 |
| pfifo | 3120.226 | 0.500 | 15.526 | 7.322 | 24.758 | 31.047 | 0.003 | equivalent | 1 |
| wmdd | 3139.498 | 1.121 | 34.798 | 19.169 | 52.348 | 31.047 | 0.001 | inconclusive | 0 |
| atc | 3141.091 | 1.172 | 36.390 | 20.338 | 54.214 | 31.047 | 0.000 | inconclusive | 0 |
| wspt | 3527.016 | 13.602 | 422.315 | 325.147 | 529.124 | 31.047 | 0.000 | worse | 0 |
| random | 8149.989 | 162.505 | 5045.289 | 3982.568 | 6205.235 | 31.047 | 0.000 | worse | 0 |
| lpt | 29770.910 | 858.898 | 26666.210 | 21842.835 | 31589.159 | 31.047 | 0.000 | worse | 0 |


**u_target=1.1** — best rl301 (mean 3688.496), 60 configurations, 60 clusters. Equivalence set (8 methods): EDD and PFIFO, four of the ten policy seeds, one of the ten attention seeds, and one of the three first-curriculum seeds.

| method | mean | pct_from_best | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|
| rl301 | 3688.496 | 0.000 | 0.000 | 0.000 | 0.000 | 36.885 | 1.000 | equivalent | 1 |
| v2rl305 | 3691.867 | 0.091 | 3.370 | -11.249 | 22.654 | 36.885 | 1.000 | equivalent | 1 |
| v2at302 | 3692.268 | 0.102 | 3.772 | -9.829 | 21.845 | 36.885 | 1.000 | equivalent | 1 |
| v2rl310 | 3692.381 | 0.105 | 3.885 | -14.169 | 30.623 | 36.885 | 0.821 | equivalent | 1 |
| v2rl304 | 3695.764 | 0.197 | 7.267 | -11.285 | 23.885 | 36.885 | 0.098 | equivalent | 1 |
| pfifo | 3698.828 | 0.280 | 10.332 | -10.959 | 30.050 | 36.885 | 0.683 | equivalent | 1 |
| edd | 3699.835 | 0.307 | 11.339 | -10.275 | 31.439 | 36.885 | 0.683 | equivalent | 1 |
| v2rl308 | 3700.348 | 0.321 | 11.852 | 3.716 | 21.800 | 36.885 | 0.098 | equivalent | 1 |
| v2at310 | 3718.350 | 0.809 | 29.854 | 8.896 | 52.578 | 36.885 | 0.490 | inconclusive | 0 |
| v2rl307 | 3722.230 | 0.915 | 33.733 | 6.411 | 68.704 | 36.885 | 0.252 | inconclusive | 0 |
| v2rl302 | 3726.147 | 1.021 | 37.651 | 9.902 | 73.134 | 36.885 | 0.045 | inconclusive | 0 |
| v2at307 | 3734.891 | 1.258 | 46.394 | 15.767 | 77.907 | 36.885 | 0.069 | inconclusive | 0 |
| atc | 3736.408 | 1.299 | 47.912 | 18.473 | 83.205 | 36.885 | 0.020 | inconclusive | 0 |
| wmdd | 3737.153 | 1.319 | 48.657 | 19.008 | 82.047 | 36.885 | 0.683 | inconclusive | 0 |
| wspt | 4509.238 | 22.251 | 820.742 | 645.293 | 1011.534 | 36.885 | 0.000 | worse | 0 |
| random | 14661.981 | 297.506 | 10973.485 | 8886.502 | 13069.533 | 36.885 | 0.000 | worse | 0 |
| lpt | 52750.153 | 1330.126 | 49061.656 | 40661.976 | 57259.274 | 36.885 | 0.000 | worse | 0 |


**u_target=1.3** — best v2rl304 (mean 4569.811), 60 configurations, 60 clusters. Equivalence set (1 methods): one of the ten policy seeds.

| method | mean | pct_from_best | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|
| v2rl304 | 4569.811 | 0.000 | 0.000 | 0.000 | 0.000 | 45.698 | 1.000 | equivalent | 1 |
| v2rl308 | 4575.153 | 0.117 | 5.341 | -22.290 | 47.020 | 45.698 | 1.000 | inconclusive | 0 |
| v2rl310 | 4587.819 | 0.394 | 18.008 | -18.570 | 60.217 | 45.698 | 1.000 | inconclusive | 0 |
| edd | 4591.817 | 0.482 | 22.006 | -3.159 | 53.147 | 45.698 | 0.298 | inconclusive | 0 |
| pfifo | 4591.841 | 0.482 | 22.030 | -2.327 | 53.403 | 45.698 | 0.298 | inconclusive | 0 |
| v2at310 | 4604.906 | 0.768 | 35.095 | 6.080 | 70.805 | 45.698 | 0.616 | inconclusive | 0 |
| rl301 | 4611.499 | 0.912 | 41.688 | -8.782 | 100.026 | 45.698 | 1.000 | inconclusive | 0 |
| wmdd | 4629.958 | 1.316 | 60.147 | -0.289 | 120.326 | 45.698 | 0.172 | inconclusive | 0 |
| atc | 4641.915 | 1.578 | 72.104 | 11.120 | 134.141 | 45.698 | 0.037 | inconclusive | 0 |
| v2at307 | 4671.940 | 2.235 | 102.129 | 51.821 | 157.072 | 45.698 | 0.000 | worse | 0 |
| v2rl305 | 4691.921 | 2.672 | 122.109 | 41.643 | 225.571 | 45.698 | 0.616 | inconclusive | 0 |
| v2at302 | 4746.296 | 3.862 | 176.485 | 59.914 | 322.490 | 45.698 | 0.399 | worse | 0 |
| wspt | 6802.923 | 48.867 | 2233.112 | 1883.764 | 2589.079 | 45.698 | 0.000 | worse | 0 |
| random | 36141.300 | 690.871 | 31571.489 | 26216.568 | 36896.477 | 45.698 | 0.000 | worse | 0 |
| lpt | 113533.625 | 2384.427 | 108963.814 | 91347.331 | 126031.386 | 45.698 | 0.000 | worse | 0 |


Diagnostic-floor deterioration ratios (mean / best mean):

| scope | method | mean | mean_best | ratio_to_best | pct_from_best |
|---|---|---|---|---|---|
| u_target=0.7 | lpt | 2574.504 | 2257.500 | 1.140 | 14.042 |
| u_target=0.7 | random | 2304.053 | 2257.500 | 1.021 | 2.062 |
| u_target=0.7 | wspt | 2269.049 | 2257.500 | 1.005 | 0.512 |
| u_target=0.7 | edd | 2258.266 | 2257.500 | 1.000 | 0.034 |
| u_target=0.7 | atc | 2258.746 | 2257.500 | 1.001 | 0.055 |
| u_target=0.7 | wmdd | 2259.155 | 2257.500 | 1.001 | 0.073 |
| u_target=0.7 | pfifo | 2258.266 | 2257.500 | 1.000 | 0.034 |
| u_target=0.9 | lpt | 16524.005 | 2990.305 | 5.526 | 452.586 |
| u_target=0.9 | random | 4924.665 | 2990.305 | 1.647 | 64.688 |
| u_target=0.9 | wspt | 3214.838 | 2990.305 | 1.075 | 7.509 |
| u_target=0.9 | edd | 3000.471 | 2990.305 | 1.003 | 0.340 |
| u_target=0.9 | atc | 3011.755 | 2990.305 | 1.007 | 0.717 |
| u_target=0.9 | wmdd | 3008.921 | 2990.305 | 1.006 | 0.623 |
| u_target=0.9 | pfifo | 3000.471 | 2990.305 | 1.003 | 0.340 |
| u_target=1.0 | lpt | 29770.910 | 3104.700 | 9.589 | 858.898 |
| u_target=1.0 | random | 8149.989 | 3104.700 | 2.625 | 162.505 |
| u_target=1.0 | wspt | 3527.016 | 3104.700 | 1.136 | 13.602 |
| u_target=1.0 | edd | 3120.226 | 3104.700 | 1.005 | 0.500 |
| u_target=1.0 | atc | 3141.091 | 3104.700 | 1.012 | 1.172 |
| u_target=1.0 | wmdd | 3139.498 | 3104.700 | 1.011 | 1.121 |
| u_target=1.0 | pfifo | 3120.226 | 3104.700 | 1.005 | 0.500 |
| u_target=1.1 | lpt | 52750.153 | 3688.496 | 14.301 | 1330.126 |
| u_target=1.1 | random | 14661.981 | 3688.496 | 3.975 | 297.506 |
| u_target=1.1 | wspt | 4509.238 | 3688.496 | 1.223 | 22.251 |
| u_target=1.1 | edd | 3699.835 | 3688.496 | 1.003 | 0.307 |
| u_target=1.1 | atc | 3736.408 | 3688.496 | 1.013 | 1.299 |
| u_target=1.1 | wmdd | 3737.153 | 3688.496 | 1.013 | 1.319 |
| u_target=1.1 | pfifo | 3698.828 | 3688.496 | 1.003 | 0.280 |
| u_target=1.3 | lpt | 113533.625 | 4569.811 | 24.844 | 2384.427 |
| u_target=1.3 | random | 36141.300 | 4569.811 | 7.909 | 690.871 |
| u_target=1.3 | wspt | 6802.923 | 4569.811 | 1.489 | 48.867 |
| u_target=1.3 | edd | 4591.817 | 4569.811 | 1.005 | 0.482 |
| u_target=1.3 | atc | 4641.915 | 4569.811 | 1.016 | 1.578 |
| u_target=1.3 | wmdd | 4629.958 | 4569.811 | 1.013 | 1.316 |
| u_target=1.3 | pfifo | 4591.841 | 4569.811 | 1.005 | 0.482 |


## 3. Transfer and stress


### Campus 1 (transfer, m=1.0)

Best atc (mean 80.417), 30 configurations, 30 clusters. Equivalence set (28 methods): EDD, PFIFO, ATC, WMDD and LPT, all ten policy seeds, all ten attention seeds, and all three first-curriculum seeds.

| method | mean | pct_from_best | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|
| atc | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | 1 |
| edd | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | 1 |
| lpt | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | 1 |
| pfifo | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | 1 |
| rl301 | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | 1 |
| rl302 | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | 1 |
| rl303 | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | 1 |
| v2at301 | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | 1 |
| v2at302 | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | 1 |
| v2at304 | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | 1 |
| v2at305 | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | 1 |
| v2at306 | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | 1 |
| wmdd | 80.417 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | equivalent | 1 |
| random | 81.121 | 0.875 | 0.704 | 0.000 | 1.775 | 1.000 | 1.000 | inconclusive | 0 |
| wspt | 81.297 | 1.094 | 0.880 | 0.000 | 2.293 | 1.000 | 1.000 | inconclusive | 0 |


### Campus 2 (nonstationary stress, never pooled with a verdict)

Best wmdd (mean 1218.229), 17 configurations, 17 clusters. Equivalence set (1 methods): WMDD.

| method | mean | pct_from_best | mean_diff | ci_lo | ci_hi | margin | holm_p | verdict | in_equivalence_set |
|---|---|---|---|---|---|---|---|---|---|
| wmdd | 1218.229 | 0.000 | 0.000 | 0.000 | 0.000 | 12.182 | 1.000 | equivalent | 1 |
| v2at309 | 1220.106 | 0.154 | 1.877 | -32.534 | 37.458 | 12.182 | 0.960 | inconclusive | 0 |
| v2at301 | 1226.390 | 0.670 | 8.161 | -12.492 | 31.492 | 12.182 | 0.960 | inconclusive | 0 |
| atc | 1252.116 | 2.782 | 33.887 | 12.321 | 59.462 | 12.182 | 0.014 | worse | 0 |
| wspt | 1291.239 | 5.993 | 73.010 | 35.217 | 113.926 | 12.182 | 0.009 | worse | 0 |
| edd | 1311.322 | 7.642 | 93.093 | -17.248 | 242.406 | 12.182 | 1.000 | inconclusive | 0 |
| pfifo | 1311.322 | 7.642 | 93.093 | -16.389 | 241.693 | 12.182 | 1.000 | inconclusive | 0 |
| v2at308 | 1319.604 | 8.322 | 101.376 | 19.905 | 206.225 | 12.182 | 0.308 | worse | 0 |
| v2rl310 | 1324.889 | 8.755 | 106.660 | 9.846 | 226.410 | 12.182 | 0.544 | inconclusive | 0 |
| v2at304 | 1341.317 | 10.104 | 123.088 | 33.495 | 233.411 | 12.182 | 0.305 | worse | 0 |
| v2at307 | 1361.673 | 11.775 | 143.445 | 36.713 | 291.764 | 12.182 | 0.205 | worse | 0 |
| rl302 | 1365.712 | 12.106 | 147.483 | 14.645 | 324.307 | 12.182 | 0.506 | worse | 0 |
| random | 1636.031 | 34.296 | 417.802 | 215.398 | 661.251 | 12.182 | 0.009 | worse | 0 |
| lpt | 2615.112 | 114.665 | 1396.883 | 683.108 | 2224.134 | 12.182 | 0.009 | worse | 0 |


Campus 2 realized utilization:

| statistic | value |
|---|---|
| n_configs | 17.000 |
| u_min | 0.785 |
| u_p25 | 1.025 |
| u_median | 1.233 |
| u_mean | 1.356 |
| u_p75 | 1.410 |
| u_max | 2.903 |
| share_over_one | 0.765 |
| n_in_bin_0.5-0.8 | 1.000 |
| n_in_bin_0.8-1.0 | 3.000 |
| n_in_bin_1.0-1.2 | 3.000 |
| n_in_bin_>=1.2 | 10.000 |


## 3b. Rolling CP-SAT, every paired row

Rolling CP-SAT is excluded from every equivalence-set ranking because it was run on 160 of 887 configurations (8 per empirical cell, none on the generator cells). Its evidence is the paired table below; `n_configs` is the subsample each row is computed on.

| scope_type | scope | reference | n_configs | n_clusters | mean_method | mean_ref | mean_diff | ci_lo | ci_hi | holm_p | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| emp_m | m=0.6 | atc | 48 | 48 | 510.046 | 515.157 | -5.110 | -11.759 | -0.493 | 1.000 | inconclusive |
| emp_m | m=0.6 | edd | 48 | 48 | 510.046 | 510.698 | -0.651 | -1.996 | 0.393 | 0.511 | equivalent |
| emp_m | m=0.6 | wmdd | 48 | 48 | 510.046 | 513.624 | -3.578 | -7.915 | -0.367 | 1.000 | inconclusive |
| emp_m | m=0.8 | atc | 48 | 48 | 506.036 | 507.830 | -1.793 | -4.896 | -0.014 | 0.114 | equivalent |
| emp_m | m=0.8 | edd | 48 | 48 | 506.036 | 506.547 | -0.511 | -1.330 | 0.061 | 0.086 | equivalent |
| emp_m | m=0.8 | wmdd | 48 | 48 | 506.036 | 507.219 | -1.183 | -3.375 | 0.061 | 0.086 | equivalent |
| emp_m | m=1.0 | atc | 48 | 48 | 505.808 | 506.296 | -0.488 | -1.553 | 0.064 | 0.007 | equivalent |
| emp_m | m=1.0 | edd | 48 | 48 | 505.808 | 505.828 | -0.020 | -0.145 | 0.053 | 0.002 | equivalent |
| emp_m | m=1.0 | wmdd | 48 | 48 | 505.808 | 506.222 | -0.414 | -1.325 | 0.053 | 0.002 | equivalent |
| emp_pooled | ALL | atc | 160 | 64 | 510.409 | 513.863 | -3.454 | -8.376 | 0.447 | 0.032 | inconclusive |
| emp_pooled | ALL | edd | 160 | 64 | 510.409 | 515.945 | -5.536 | -16.159 | 1.337 | 0.001 | inconclusive |
| emp_pooled | ALL | wmdd | 160 | 64 | 510.409 | 511.935 | -1.526 | -4.327 | 1.135 | 0.011 | equivalent |
| emp_ubin | u_bin=0.5-0.8 | atc | 47 | 29 | 796.818 | 800.961 | -4.143 | -11.456 | -0.150 | 0.509 | inconclusive |
| emp_ubin | u_bin=0.5-0.8 | edd | 47 | 29 | 796.818 | 797.293 | -0.474 | -1.136 | 0.037 | 0.072 | equivalent |
| emp_ubin | u_bin=0.5-0.8 | wmdd | 47 | 29 | 796.818 | 799.580 | -2.762 | -7.713 | 0.039 | 0.193 | equivalent |
| emp_ubin | u_bin=0.8-1.0 | atc | 13 | 13 | 851.349 | 859.727 | -8.378 | -25.059 | 0.426 | 1.000 | inconclusive |
| emp_ubin | u_bin=0.8-1.0 | edd | 13 | 13 | 851.349 | 853.590 | -2.241 | -6.656 | 0.426 | 1.000 | equivalent |
| emp_ubin | u_bin=0.8-1.0 | wmdd | 13 | 13 | 851.349 | 857.886 | -6.537 | -17.811 | 0.420 | 1.000 | inconclusive |
| emp_ubin | u_bin=1.0-1.2 | atc | 7 | 7 | 584.193 | 587.762 | -3.569 | -8.256 | 0.019 | 1.000 | inconclusive |
| emp_ubin | u_bin=1.0-1.2 | edd | 7 | 7 | 584.193 | 585.357 | -1.164 | -3.456 | 0.019 | 1.000 | equivalent |
| emp_ubin | u_bin=1.0-1.2 | wmdd | 7 | 7 | 584.193 | 585.551 | -1.357 | -3.804 | 0.019 | 1.000 | equivalent |
| emp_ubin | u_bin=<0.5 | atc | 54 | 27 | 321.201 | 321.688 | -0.486 | -1.671 | 0.173 | 0.001 | equivalent |
| emp_ubin | u_bin=<0.5 | edd | 54 | 27 | 321.201 | 321.151 | 0.051 | -0.124 | 0.235 | 0.000 | equivalent |
| emp_ubin | u_bin=<0.5 | wmdd | 54 | 27 | 321.201 | 321.649 | -0.448 | -1.499 | 0.171 | 0.001 | equivalent |
| emp_ubin | u_bin=>=1.2 | atc | 23 | 10 | 134.719 | 134.715 | 0.005 | 0.000 | 0.014 | 0.307 | equivalent |
| emp_ubin | u_bin=>=1.2 | edd | 23 | 10 | 134.719 | 134.715 | 0.005 | 0.000 | 0.014 | 0.307 | equivalent |
| emp_ubin | u_bin=>=1.2 | wmdd | 23 | 10 | 134.719 | 134.715 | 0.005 | 0.000 | 0.014 | 0.307 | equivalent |
| stress | campus=2|m=1.0 | atc | 8 | 8 | 976.783 | 1001.529 | -24.746 | -102.665 | 36.451 | 1.000 | inconclusive |
| stress | campus=2|m=1.0 | edd | 8 | 8 | 976.783 | 1080.425 | -103.642 | -280.492 | 33.903 | 1.000 | inconclusive |
| stress | campus=2|m=1.0 | wmdd | 8 | 8 | 976.783 | 976.256 | 0.527 | -37.081 | 42.941 | 1.000 | inconclusive |
| transfer | campus=1|m=1.0 | atc | 8 | 8 | 100.056 | 100.045 | 0.011 | 0.003 | 0.021 | 0.750 | equivalent |
| transfer | campus=1|m=1.0 | edd | 8 | 8 | 100.056 | 100.045 | 0.011 | 0.003 | 0.021 | 0.750 | equivalent |
| transfer | campus=1|m=1.0 | wmdd | 8 | 8 | 100.056 | 100.045 | 0.011 | 0.003 | 0.021 | 0.750 | equivalent |


## 4. Latency

| scope | family | unit | n_rows | median | p90 | mean | max |
|---|---|---|---|---|---|---|---|
| empirical_all | rolling | ms_per_decision | 160 | 125.599 | 1492.081 | 430.381 | 2026.758 |
| empirical_all | rolling | s_per_replan | 160 | 0.125 | 1.491 | 0.430 | 2.025 |
| empirical_all | rules | ms_per_decision | 4109 | 0.003 | 0.008 | 0.004 | 0.108 |
| empirical_all | v1_mlp | ms_per_decision | 1761 | 0.218 | 0.429 | 0.283 | 2.663 |
| empirical_all | v2_attn | ms_per_decision | 5870 | 0.582 | 0.887 | 0.647 | 3.219 |
| empirical_all | v2_mlp | ms_per_decision | 5870 | 0.194 | 0.349 | 0.230 | 5.768 |
| empirical_verdict | rolling | ms_per_decision | 144 | 107.869 | 1535.046 | 427.407 | 2026.758 |
| empirical_verdict | rolling | s_per_replan | 144 | 0.108 | 1.532 | 0.427 | 2.025 |
| empirical_verdict | rules | ms_per_decision | 3780 | 0.003 | 0.008 | 0.005 | 0.108 |
| empirical_verdict | v1_mlp | ms_per_decision | 1620 | 0.219 | 0.430 | 0.284 | 2.663 |
| empirical_verdict | v2_attn | ms_per_decision | 5400 | 0.583 | 0.868 | 0.646 | 3.219 |
| empirical_verdict | v2_mlp | ms_per_decision | 5400 | 0.195 | 0.348 | 0.230 | 5.768 |
| generator | rules | ms_per_decision | 2100 | 0.006 | 0.034 | 0.016 | 0.239 |
| generator | v1_mlp | ms_per_decision | 900 | 0.451 | 1.422 | 0.686 | 3.961 |
| generator | v2_attn | ms_per_decision | 3000 | 0.807 | 1.643 | 1.008 | 5.133 |
| generator | v2_mlp | ms_per_decision | 3000 | 0.431 | 1.478 | 0.685 | 3.926 |


## 5. Seed dispersion (all reported scopes)

| scope_type | scope | pool | pooled_mean | min_mean | median_mean | max_mean | spread_ratio | n_seeds_in_set | seeds_outside_set |
|---|---|---|---|---|---|---|---|---|---|
| emp_m | m=1.0 | v2_mlp | 444.769 | 444.681 | 444.758 | 444.953 | 1.001 | 10 |  |
| emp_m | m=1.0 | v2_attn | 445.268 | 444.716 | 445.252 | 445.884 | 1.003 | 10 |  |
| emp_m | m=1.0 | v1_mlp | 444.810 | 444.763 | 444.764 | 444.902 | 1.000 | 3 |  |
| emp_m | m=0.8 | v2_mlp | 446.490 | 446.287 | 446.348 | 447.144 | 1.002 | 10 |  |
| emp_m | m=0.8 | v2_attn | 447.688 | 446.268 | 447.769 | 449.828 | 1.008 | 9 | v2at301 |
| emp_m | m=0.8 | v1_mlp | 446.376 | 446.214 | 446.318 | 446.595 | 1.001 | 3 |  |
| emp_m | m=0.6 | v2_mlp | 451.318 | 450.246 | 450.771 | 453.910 | 1.008 | 8 | v2rl306 v2rl309 |
| emp_m | m=0.6 | v2_attn | 455.552 | 450.733 | 455.485 | 460.801 | 1.022 | 2 | v2at301 v2at303 v2at304 v2at305 v2at306 v2at307 v2at308 v2at309 |
| emp_m | m=0.6 | v1_mlp | 450.872 | 449.767 | 451.188 | 451.660 | 1.004 | 3 |  |
| gen_all | ALL | v2_mlp | 3477.785 | 3327.425 | 3376.449 | 3978.418 | 1.196 | 3 | v2rl301 v2rl302 v2rl303 v2rl305 v2rl306 v2rl307 v2rl309 |
| gen_all | ALL | v2_attn | 3931.662 | 3342.649 | 3504.944 | 6897.663 | 2.064 | 1 | v2at301 v2at302 v2at303 v2at304 v2at305 v2at306 v2at307 v2at308 v2at309 |
| gen_all | ALL | v1_mlp | 4026.608 | 3330.767 | 4058.342 | 4690.713 | 1.408 | 1 | rl302 rl303 |
| gen_utarget | u_target=0.7 | v2_mlp | 2258.039 | 2257.543 | 2257.822 | 2259.702 | 1.001 | 10 |  |
| gen_utarget | u_target=0.7 | v2_attn | 2268.172 | 2257.573 | 2260.537 | 2334.254 | 1.034 | 9 | v2at301 |
| gen_utarget | u_target=0.7 | v1_mlp | 2260.318 | 2257.500 | 2259.881 | 2263.573 | 1.003 | 3 |  |
| gen_utarget | u_target=0.9 | v2_mlp | 3006.350 | 2990.815 | 2993.815 | 3065.295 | 1.025 | 8 | v2rl303 v2rl309 |
| gen_utarget | u_target=0.9 | v2_attn | 3218.868 | 2990.305 | 3043.213 | 4626.060 | 1.547 | 3 | v2at301 v2at303 v2at304 v2at305 v2at306 v2at308 v2at309 |
| gen_utarget | u_target=0.9 | v1_mlp | 3072.348 | 2991.641 | 3071.202 | 3154.201 | 1.054 | 1 | rl302 rl303 |
| gen_utarget | u_target=1.0 | v2_mlp | 3143.023 | 3108.184 | 3115.510 | 3276.383 | 1.054 | 8 | v2rl303 v2rl309 |
| gen_utarget | u_target=1.0 | v2_attn | 3529.898 | 3107.801 | 3225.757 | 6040.129 | 1.944 | 1 | v2at301 v2at303 v2at304 v2at305 v2at306 v2at307 v2at308 v2at309 v2at310 |
| gen_utarget | u_target=1.0 | v1_mlp | 3345.697 | 3104.700 | 3464.596 | 3467.795 | 1.117 | 1 | rl302 rl303 |
| gen_utarget | u_target=1.1 | v2_mlp | 3806.663 | 3691.867 | 3724.189 | 4196.135 | 1.137 | 4 | v2rl301 v2rl302 v2rl303 v2rl306 v2rl307 v2rl309 |
| gen_utarget | u_target=1.1 | v2_attn | 4430.877 | 3692.268 | 3861.848 | 8464.522 | 2.292 | 1 | v2at301 v2at303 v2at304 v2at305 v2at306 v2at307 v2at308 v2at309 v2at310 |
| gen_utarget | u_target=1.1 | v1_mlp | 4410.234 | 3688.496 | 4478.806 | 5063.400 | 1.373 | 1 | rl302 rl303 |
| gen_utarget | u_target=1.3 | v2_mlp | 5174.852 | 4569.811 | 4792.058 | 7135.676 | 1.561 | 1 | v2rl301 v2rl302 v2rl303 v2rl305 v2rl306 v2rl307 v2rl308 v2rl309 v2rl310 |
| gen_utarget | u_target=1.3 | v2_attn | 6210.494 | 4604.906 | 5093.602 | 13023.348 | 2.828 | 0 | v2at301 v2at302 v2at303 v2at304 v2at305 v2at306 v2at307 v2at308 v2at309 v2at310 |
| gen_utarget | u_target=1.3 | v1_mlp | 7044.440 | 4611.499 | 6927.335 | 9594.486 | 2.081 | 0 | rl301 rl302 rl303 |


## 6. Sanity checks

| check | got | want | ok |
|---|---|---|---|
| n_configs vs meta.json | 887 | 887 | True |
| n_rows vs meta.json | 26770 | 26770 | True |
| n_infeasible vs meta.json | 0 | 0 | True |
| n_errors vs meta.json | 0 | 0 | True |
| empirical configs vs meta.json | 587 | 587 | True |
| generator configs vs meta.json | 300 | 300 | True |
| rolling configs vs meta.json | 160 | 160 | True |
| methods present vs meta.json | 31 | 31 | True |
| every non-rolling method covers every configuration | 887 | 887 | True |
| no rolling row on generator cells | 0 | 0 | True |
| value column has no missing entry | 0 | 0 | True |
