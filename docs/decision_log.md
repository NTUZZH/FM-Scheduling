# Dated decision log (public)

Curated technical log of every protocol deviation and non-obvious design
decision, in chronological order. Format: date — decision — reason/evidence.
The evaluation gates and their pass/fail criteria are stated in
`docs/protocol.md`; entries here timestamp the amendments and corrections the
manuscript discloses.

- 2026-07-04 — **Business-hour time axis** (8 bh/day, 5 d/wk concatenated;
  SLA windows converted accordingly). Jobs longer than one shift would
  otherwise require preemption at shift boundaries, and calendar modelling
  would roughly triple solver/environment state; standard practice in the
  parallel-machine tardiness literature. The E5 SLA sweep (±50%) covers the
  conversion's slack.
- 2026-07-04 — **Campus set**: replay restricted to the 6 timestamp-complete
  campuses (1, 2, 5, 9, 10, 12); transfer study trains on {5, 9, 10, 12} and
  holds out {1, 2}. Data reality: the remaining campuses lack usable start
  timestamps.
- 2026-07-04 — **Travel excluded from the v1 main protocol** (travel = 0);
  the 0.25 bh per-building-switch cost moves to an E5 sensitivity
  re-simulation. Sequence-dependent setups would force routing structure
  into the exact solver and blur comparability, and building identifiers are
  missing on several campuses.
- 2026-07-04 — **Priority mapping v2** (supersedes the naive numeric-
  ascending rule). Evidence: several nominal "priority" values are ~100%
  preventive (planned-work categories mixed into the field); realised
  completion durations invert the numeric order on campus 12 and contradict
  "1 = emergency" on campus 10; text-labelled campuses validate duration as
  an urgency proxy. New rule: preventive→P4; corrective keyword→class;
  corrective numeric scales keep their order with direction set by the
  Spearman sign against median corrective completion duration, then
  rank-quartiles to classes; rare/missing→P3.
- 2026-07-04 — **Replay sampling v2 (first-N releases)**. A generator realism
  check exposed selection bias in fixed-window sampling (only atypical
  low-volume days passed the acceptance filter on high-variance campuses;
  e.g. campus-5 replay PM share 0.02 against a true 0.45). v2 takes the
  first N releases from each anchor with non-overlapping windows; exact
  sizes, bias removed. Static gate re-run on rebuilt instances.
- 2026-07-04 — **R7 duplicate labour-line aggregation** changes the dataset
  scale: 1,454,039 unique work orders from 1,906,865 post-filter rows;
  labour cap p99.5 = 90.86 h computed post-aggregation.
- 2026-07-05 — **Gate A verdict: "trivially easy" branch fires** (see
  protocol.md). CP-SAT proves optimality within 60 s on 100% of a 90-instance
  pilot at every size; due-date rules within 0.2% of best-known there. Study
  weight shifts to the dynamic track; the static track is kept as a
  reference/certificate layer. Win/tie/loss tallies adopt a tie tolerance of
  1.0 weighted unit (the solver's centi-hour grid perturbs ties by ~0.04).
- 2026-07-05 — **Gate B protocol amendment (dated before any contended-arm
  numbers existed)**. Trigger: PPO development curves are flat at default
  capacity (~409–411 across seeds), consistent with Gate A's finding that
  capacity-adequate episodes barely discriminate policies. Amendment: Gate B
  is judged on both the original capacity-adequate arm and a contended arm
  (crew multipliers {0.6, 0.8} on replay tests plus generator storm cells);
  "beats a rule" = lower mean TWT with paired Wilcoxon p < 0.05, ties are
  not wins; both arms are reported regardless of outcome.
- 2026-07-05 — Held-out campuses {1, 2} excluded from all Gate-B verdicts and
  from policy checkpoint selection; they appear only in the transfer study.
- 2026-07-05 — **Curriculum v2 + checkpoint selection change**: the
  default-capacity development metric plateaus for every trained variant and
  cannot discriminate checkpoints; v2 rebalances training toward contended
  regimes and selects checkpoints on a tight-capacity development set
  (crew multiplier 0.6). Disclosure: v2 was trained after aggregate results
  on test regimes existed (a leakage risk); mitigations: held-out campuses
  untouched, fresh evaluation seeds, and both v1 and v2 reported. In the
  event v2 was no better than v1.
- 2026-07-05 — **Rolling CP-SAT correction (two stages)**. (a) An apparent
  2× blow-up on default-capacity cells was an analysis artifact (an n=8
  subsample mean juxtaposed against full-cell means); the analysis was
  changed to same-instance comparisons. (b) The real tight-cell failures
  trace to burst releases under an arrival-only replan trigger: 12–15
  budget-capped replans, after which one stale plan executes uncorrected.
  A larger budget does not help (too few replans, not slow solves). Fix: a
  periodic trigger (arrival OR every 4 bh with non-empty queue) plus a
  lexicographic flow-time tiebreak. Both the pathology and the fix are
  reported.
- 2026-07-05 — **Rolling diagnostic re-run for the released figure**: fresh
  instrumented runs of the pathological cell show the burst-instance
  magnitudes vary across runs (budget-capped solves are not deterministic;
  e.g. 15,471 historical vs 10,324 re-run on one instance) while the
  collapse-and-recovery pattern is stable; the manuscript cites the released
  diagnostic's values and says so. An earlier "rolling beats EDD on a
  spread-arrival instance (420 vs 460)" observation did not reproduce
  against the final scored results and was removed; the supported statement
  is that failure severity scales inversely with replan count.
- 2026-07-06 — **Terminology**: objective renamed TWT (total weighted
  tardiness) throughout; "pre-registered" replaced by "pre-specified"
  (protocol lives in this repository's dated log, not an external registry).
- 2026-07-06 — **Campus-2 overload diagnosed as a calibration artifact**:
  its 69 training weeks sit inside the database's population ramp (median
  weekly volume 49 → 177 → 1,708 bh across 2016/2017/test), so p95 crew
  sizing under-provisions it; held-out campus 1 (221 stationary training
  weeks) calibrates correctly. Campus-2 cells are kept as an
  extreme-overload stress test and flagged as such in the manuscript.
- 2026-07-06 — **Revision experiments added**: travel-overhead re-simulation
  (0.25/0.50 bh per switch; ranking unchanged, τ=1.00 in every
  discriminative cell), priority-weight-vector sweep ((4,3,2,1) and
  (27,9,3,1); pooled τ=1.00), candidate-cap ablation (64→256), MLP seed set
  enlarged from 3 to 10, and an attention policy class trained as a second
  learner. Outcomes: the ten-seed pool reproduces both Gate-B arms exactly;
  the attention class is no stronger (it fails even the default arm's
  consistency requirement) and costs 0.94 ms per decision; the candidate-cap
  ablation shows ~89% exact ties and no verdict flips that survive
  netting; and the tight-capacity development floors of the two
  architectures coincide (426.73 vs 426.89), supporting the problem-set
  ceiling reading. The decision map's primary colouring moved to the
  full-cell four-way comparison (22 of 27 ties; ATC outright on the
  calibration-artifact campus 2 and the two tightest training cells).
- 2026-08-19 — **Revision protocol R4 fixed before any R4 result existed**
  (full text in `docs/protocol.md`). Trigger: venue change after an
  editorial rejection without scientific review, plus an internal
  methodological review whose corrections are adopted before any new number
  exists. Contents: label/definition corrections (MOR renamed LPT; the
  formal model corrected to disjoint per-trade P | r_j | sum w_j T_j;
  "workload-implied reference capacity"; "timestamp-ordered empirical
  track" because WOStartDate's operational meaning is not documented by the
  source); corpus v1.1 (priority mapping refit on training years only,
  stable dominant-line sort, diffs measured and disclosed); WMDD added and
  ATC's k tuned on development data only (grid {0.5,1,2,3,5,10}, frozen
  before the final evaluation); a fresh untouched final evaluation
  (anchor-shuffle seed 401, generator seed block 80000+, methods and
  checkpoints frozen first, run once); cluster-bootstrap practical-
  equivalence statistics with Holm correction, replacing the "beats 3 of 5"
  gate as the primary comparison (the historical gate outcome stands as a
  v1.0 result); a preventive-visibility experiment with pre-stated
  hypotheses H1-H4 (L in {0, 8, 40, inf} bh, policy seeds 501+, generator
  seeds 90000+); labor-line processing-time robustness (sum/max/single-line
  models); capacity-estimator sensitivity (p75/p90/p95); a synthetic
  release-backdating robustness scenario; and two additional service-window
  scenario families plus a preventive-priority convention variant. All
  v1.0 results remain reported as development evidence.
- 2026-08-19 — **ATC look-ahead frozen at k = 2 by the R4.3 development
  tuning** (`scripts/r4_atc_tune.py`, `results/r4_revision/atc_tuning*`).
  Grid {0.5, 1, 2, 3, 5, 10} on the 760 training-period empirical-track
  instances of the training campuses at crew multipliers {0.6, 0.8}, 9,120
  schedules scored by the independent validator: pooled mean TWT is
  minimized at k = 2 outright (290.50 vs 290.98 at k = 3 and 297.80 at
  k = 1), so the selected value coincides with the literature default the
  study had used throughout. No existing result changes; ATC may now be
  described as development-tuned.
- 2026-08-19 — **Corpus v1.1 diffs measured before adoption**
  (`scripts/r4_corpus_diff.py`, `results/r4_revision/corpus_diff*`): the
  train-only priority refit changes one mapping key (campus 10, raw value
  4.0: class 3 under the all-years fit, class 4 under the training-window
  fit, 513 work orders, 0.04%); the stable dominant-line sort changes 72
  work orders (0.005%, mostly trade, campuses 2 and 9); combined, 585 of
  1,449,262 work orders (0.04%) and 135 of 3,186 released replay instances
  differ, with p_bh unchanged everywhere (asserted). A field-by-field
  provenance check reproduced the released corpus exactly under the v1.0
  pipeline before measuring. The labor-line audit is scripted
  (`scripts/r4_labor_audit.py`): 9.5% of work orders are multi-line
  (31% of rows); 96.1% of multi-line orders share a single start and end
  timestamp and only 1.6% start more than one business day apart, the
  signature of parallel labor lines rather than repeat visits.
- 2026-08-19 — **Two R4 adjustments fixed before any Eval-B or visibility
  result existed** (full text in `docs/protocol.md`): the Eval-B anchor
  exclusion is relaxed to same-size-class released windows (the
  whole-window rule is physically unsatisfiable for 400-order windows on
  four campuses; measured gap distributions in the protocol text), and
  rolling CP-SAT is excluded from the fixed-window generator cells of
  Eval-B and the visibility experiment (one 2 s-budget run on the smallest
  such instance exceeded 900 s; the v1.0 overload sweep had the same
  boundary), remaining at 8 configurations per empirical cell. H3 is
  evaluated on the empirical cells.
- 2026-08-19 — **Eval-B corpus built (v1.1) and cell outcome recorded**
  before any evaluation on it: under the same-size-class rule the four
  400-order cells on campuses 1, 2, 5 and 9 REMAIN empty, because the
  released 400-order windows themselves tile those campuses' test spans
  (507/576/538/581 of ~526-601 candidate anchors still collide with
  same-size released windows); they are dropped per R4.4's disclosure
  branch. Final corpus: 227 empirical instances (150-order cells on all six
  campuses, campus 2 restored with 17; 400-order cells on campuses 10 and
  12 only) plus 300 fixed-window generator instances, 527 in total. Fresh
  400-order empirical evidence therefore exists only on the two high-volume
  campuses; the generator cells carry the larger-scale coverage, and the
  v1.0 corpus remains the development evidence at size 400 elsewhere.
- 2026-08-19 — **Generator-pack fit-window note (bounded, disclosed).** The
  Eval-B and visibility generator packs (results/r4_final/gen_params) were
  fitted before `generator.fit_params` gained the training-window mapping
  argument, so the priority mapping used inside that fit was the all-years
  one, which differs from the v1.1 mapping in exactly one rare key
  (campus 10 raw value 4.0, class 3 vs 4, under 0.5% of that campus's
  corrective rows; see the corpus-diff entry). The drawn instances are
  frozen artifacts identical for every method, so no method comparison is
  affected; the archived packs reproduce them exactly. Rebuilt development
  packs (scripts/p2_generator.py --corpus v11) use the corrected call.
- 2026-08-19 — **Reference-selection sensitivity run as a post-hoc analysis
  (revision item A3).** The released equivalence sets are built around each
  scope's lowest-mean method, which is a max-statistic selected on the same
  data the intervals come from, so the sets are exposed to the winner's
  curse and a reviewer may read them as an artifact of that choice.
  `scripts/r4_ref_sensitivity.py` therefore recomputes all 31 reported
  scopes with the reference FIXED A PRIORI at EDD, holding everything else
  constant: the same configurations, the same pairing on the
  instance-configuration id, the same 10,000-resample cluster bootstrap at
  seed 12345, the same margin rule max(1.0, 1% of the reference mean) now
  taken on EDD's paired mean, and the same Holm family structure. Outputs:
  `results/r4_final/analysis/ref_sensitivity.csv` (930 rows, both
  memberships side by side), `paper/supp_refsens.tex` and the \rfd block of
  `paper/macros_r4d.tex`. Every row that `analysis/comparisons.csv` already
  holds reproduces to the last digit (7 cross-checks). Result: the
  narrowing survives, EDD-reference sets running 30/26/17 over the crew
  multipliers, 29/26/17/8/18 over the empirical utilisation bins and
  27/16/15/9/3 over the generator targets, against 30/26/15, 29/21/13/1/12
  and 27/15/12/8/1 under the sample-best reference; the set is identical in
  13 of the 31 scopes; and no method anywhere is better than EDD beyond the
  margin (0 of 930 comparisons). This is a sensitivity analysis reported
  beside the primary one, not a replacement for it: the released sets stand
  as the paper's verdict.
- 2026-08-19 — **Two trade-derivation shares measured (revision item A9).**
  The trade taxonomy (UNIFORMAT top level) and the MISC merge threshold are
  definitional choices that the robustness suite does not sweep, so the
  manuscript now reports how much of the corpus each touches instead of
  claiming every derived quantity is varied.
  `scripts/r4_trade_shares.py` rebuilds the cleaned corpus exactly as the
  instance builder does (v1.1 stable dominant-line sort) and writes
  `results/p0_profile/trade_shares.json`: over the six benchmark campuses,
  0.21% of the 1,449,262 retained work orders carry no system code (trade
  UNK) and 0.90% are handled by a campus's merged MISC crew. The
  work-order count is cross-checked against
  `results/r4_revision/labor_audit.json` and the all-campus count against
  `results/p0_profile/overview.json`; a mismatch aborts the script.

## 2026-08-20 ~00:55 — E2 rebuild pin-thrash incident and remediation
At 22:25 on 08-19 the running v1.1 rebuild chain was pinned to cores 8-15
(shared-box core covenant with two sibling projects). The 12-worker E2 run,
sized for the whole box, then oversubscribed the 8-core block (~8x slowdown,
141 -> ~17 configs/min). VALIDITY: 616 shards written after the pin contain
rollcp2 rows, whose 2 s wall-clock solver budget makes their plan quality
compute-dependent; all 616 were DELETED (never merged into any results.csv)
and re-run under clean conditions. Rule and policy rows are deterministic in
quality and unaffected; no reported latency derives from this run (paper
latencies come from the frozen final evaluation). The chain was restarted at
workers 6 under taskset -c 8-15 (rebuild_resume2; marker line "resume2" in
results/r4_revision/rebuild.log). E1 and the solvability gate completed
before the pin and are untouched.

## 2026-08-20 — E2 v1.1 rollcp2 contention audit (post-rebuild, forensics columns)

Progress-stratified audit of the merged pool-1 results (81,366 rows), per
the rule adopted after the pin-thrash incident: only rollcp2 rows that
IMPROVED on the deterministic EDD fallback can carry contention bias; a
row equal to its fallback made no progress and is contention-immune.

- 1,536 rollcp2 rows total; 77 carry cpu/wall forensics (the resume-3
  tail, patch active). The remaining rows come from the two eras with no
  thrash exposure (the original pinned run and the workers-6-on-16-cores
  resume); every shard written during the thrash window itself had been
  deleted and re-run, so no surviving row predates that remediation.
- Of the 77 audited rows: 18 improved on EDD. Minimum cpu/wall ratio
  1.03 in the improved stratum (1.02 overall); ZERO rows below 1.0, the
  starvation line (the incident-era ratios were 0.1-0.3). Median 1.26
  improved / 1.14 not; the sub-2 medians are structural (the measurement
  window spans the whole rolling episode, whose single-threaded
  simulation phases dilute the 2-thread solve bursts).
- Improved share 6.1% of rollcp2 rows, consistent with the manuscript's
  limited-gain-at-2-s framing. VERDICT: no contamination signal; the 2 s
  wall-clock rows stand.

## 2026-08-23 — Post-hoc sensitivity analyses around the primary comparison (protocol R4.11)

Three checks added after the final results existed, reported as sensitivity
analyses; R4.5 remains the primary reporting and no manuscript verdict is
taken from these.

- **Window overlap** (`scripts/r4_overlap.py`). The same-size-class anchor
  rule adopted in the dated R4 adjustment leaves windows of different size
  classes on one campus free to cover the same period. Measured on the
  instance files: 41 sharing pairs, all cross-size, all on campuses 10 and
  12; 81 of 227 final empirical instances touch another; 49,050 slots over
  43,023 distinct work orders. Re-running the primary comparison with the
  connected components of the sharing relation as the cluster (186
  components over 227 instances; 139 over the 180 verdict-campus
  instances) changes 0 of 60 verdicts, widest interval +2.9%. The base arm
  of that script reproduces the released `family_comparisons.csv` on all
  360 field comparisons, which is what licenses reading the component arm
  as a like-for-like contrast.
- **Size stratification** (same script). Within one size class no two
  windows share a work order. At m=1.0 all ten families are equivalent to
  EDD in both strata; at m=0.6 the 150-order stratum is 6/4/0
  (equivalent/inconclusive/worse) and the 400-order stratum 4/3/3, the
  worse ones WSPT, LPT and random. Confounded with campus (400-order cells
  exist only on campuses 10 and 12) and with cluster count (60 against
  120); the 400-order margin is ~4.5x larger, so the faster narrowing is
  not a stricter-margin artefact.
- **Training-seed uncertainty** (`scripts/r4_seedboot.py`). The released
  pool intervals are conditional on the fixed trained-seed set, because
  each pool is collapsed to a per-configuration seed mean before the
  bootstrap. A two-level bootstrap resampling seeds and clusters jointly
  (10,000 replicates) leaves all 9 empirical crew-multiplier verdicts
  unchanged (median width ratio 1.21) and widens the generator intervals by
  a median factor of 3.93; 9 of 33 cells move off a definite verdict, 8 of
  them worse to inconclusive. Point estimates match the released
  `mean_diff` to 9e-13 and the instance-only arm reproduces the released
  bounds on the released stream, so the change is the seed level and not
  the estimator. With K=10 (K=3 for the curriculum-v1 pool) the widened
  interval should be interpreted cautiously and may not capture the full
  training-seed uncertainty.
- **Freshness of Eval-B against the released corpus** (same overlap
  script). 0 of 227 final empirical instances share a work order with a
  train-split v1.0 window, so no training leakage; 101 of 227 share with a
  test-split v1.0 window of a different size class, which the development
  evaluation scored. Fresh in its windows and its construction, not in the
  underlying work-order population.
