# Pre-specified evaluation protocol (public artifact)

This document states the evaluation gates and protocols that were fixed
before the corresponding results existed, with dated amendments. It is the
artifact referenced by the manuscript's "Pre-specified evaluation gates"
paragraph (Experimental setup) and the data-availability statement. The
dated entries of the released decision log (docs/decision_log.md) carry the
amendment record for this file and the result files it governs.

## Gate A — static track (fixed at project start)

**Criterion.** Solve the static instances exactly with CP-SAT under a 60 s
budget at data-calibrated capacity. If the solver reaches optimal or
near-optimal schedules at all realistic instance sizes (i.e., the static
problem is trivially easy at calibrated capacity), then shift the study's
weight to the dynamic track, and say so in the paper.

**Outcome.** Branch taken: CP-SAT certified optimality on 100% of generator
instances and 93-100% of replay instances within 60 s; the best dispatching
rules land within single-digit weighted-tardiness units of the certified
optima. The paper reports the static track as a reference and moves the
discriminative analysis to the dynamic track.

## Gate B — learned dispatcher (fixed before policy training)

**Criterion.** The learned policy passes if it beats at least 3 of the 5
ranked dispatching rules (EDD, WSPT, ATC, pFIFO, MOR) by paired Wilcoxon
signed-rank tests at alpha = 0.05, consistently across all training seeds,
on dynamic instances.

**Pre-committed branch on failure.** Re-scope the paper to "benchmark +
rigorous classical study + negative learning result"; report the failure as
a finding; do not redefine success.

**Amendment (dated).** After the v1 policy's results on the original
capacity-adequate arm (replay-default) existed, and before any contended-arm
numbers existed, a contended arm (replay-tight crew multipliers {0.6, 0.8}
plus storm cells) was added to the protocol, with the same pass criterion,
and designated the primary verdict because it is the regime where
dispatching matters. The amendment, its timing, and the reason are recorded
in the dated decision log entries of the development history and disclosed
in the manuscript (threats-to-validity section).

**Outcome.** Capacity-adequate arm: pass (beats 3/5). Contended arm: fail
(beats 1/5, MOR only). The pre-committed branch was followed: the negative
result is reported in full, for the original three seeds and for the
enlarged seed set and the stronger policy class added during revision.

## Locked defaults

Objective weights w = (8, 4, 2, 1); SLA windows P1/P2/P3/P4 = 8/24/80/171.4
business hours; business calendar 8 h x 5 d; crew sizing p95 weekly trade
hours / 40 h; CP-SAT budgets 60/300 s static, 2 s rolling; GA population 100,
60 s budget; PPO hyperparameters as listed in the manuscript appendix. Any
deviation is logged with its reason in the released decision log.

## Revision protocol R4 (fixed 2026-08-19, before any R4 results existed)

**State of evidence when this amendment was written.** Every result of the
original study exists: the Gate A and Gate B verdicts (both arms), the E1
static reference, the E2 dynamic evaluation across all regimes, the E5
sensitivity sweeps, the ten-seed MLP and attention pools, and the rolling
diagnostics, all on benchmark corpus v1.0. No R4 experiment listed below has
been run. The trigger is a venue change (the study is being revised for a
new submission after an editorial rejection without scientific review) and
an internal methodological review; the review's corrections are adopted
here before any new number exists. Existing v1.0 results remain reported as
development evidence; nothing in this amendment retroactively alters them.

**R4.1 Label and definition corrections (no schedules change).** The rule
released as "MOR" selects the longest-processing-time job within a single
trade queue and is renamed LPT everywhere; the formal problem statement is
corrected to a disjoint union of per-trade identical-parallel-machine
problems P | r_j | sum w_j T_j (one work order needs one trade, technicians
hold one trade, processing times are technician-independent, the objective
is additive), and the corrected decomposition is used to interpret the
results; "calibrated capacity" is renamed "workload-implied reference
capacity"; the replay track is renamed the "timestamp-ordered empirical
track" because the source field WOStartDate ("starting date of work order")
does not distinguish request, record-opening, scheduled-start, and
work-start events, and no claim may require a stronger reading.

**R4.2 Corpus v1.1.** Two construction corrections are adopted as the
benchmark definition: the priority mapping is refit on training years only
(<= 2017-12-31) and applied unchanged to all later data, and the R7
dominant-line selection uses a stable sort. The instance-level differences
against v1.0 are measured and disclosed before adoption. All reference
results shipped with the benchmark are regenerated on v1.1.

**R4.3 Baseline set.** Weighted Modified Due Date (WMDD, Kanet and Li 2004)
is added as a strong transparent baseline; LPT and random are retained as
diagnostic floors and reported as such. The ATC look-ahead k is tuned on
development data only: grid k in {0.5, 1, 2, 3, 5, 10}, evaluated on the
training-period empirical-track instances of the training campuses at crew
multipliers {0.6, 0.8} (the contended development scope); the single global
k with the lowest pooled mean TWT is frozen before the final evaluation,
with ties broken toward the literature default k = 2, which is retained as
a sensitivity comparator. EDD and pFIFO are reported as one rule family
where their schedules coincide.

**R4.4 Final evaluation (Eval-B).** A fresh, untouched final test set is
created before any method sees it: new empirical-track anchors drawn with
shuffle seed 401 whose windows do not overlap any released v1.0 instance
window (amended before any Eval-B evaluation existed to the same-size-class
rule; see "R4 adjustments" below, and R4.11 for what the amended rule leaves
overlapping and how it is handled in the analysis)
(target 30 per campus-size cell at sizes 150 and 400, test period;
cells that cannot supply 10 non-overlapping windows are dropped and
disclosed), plus fixed-window generator cells at target utilization
{0.7, 0.9, 1.0, 1.1, 1.3} from the training campuses with fresh seeds
(80000+ block). Crew multipliers {1.0, 0.8, 0.6} apply to the verdict
campuses; held-out campuses run at 1.0 (campus 2 is reported only as the
nonstationary-calibration stress case). Every method parameter and policy
checkpoint is frozen before the run (the existing v1/v2/attention
checkpoints; no retraining for Eval-B); the evaluation runs once and every
seed is retained. The primary explanatory variable is realized utilization,
binned at u < 0.5, 0.5-0.8, 0.8-1.0, 1.0-1.2, >= 1.2.

**R4.5 Statistics.** Primary reporting is the paired per-instance TWT
difference in absolute weighted units with a 95% cluster-bootstrap
confidence interval (clusters = base instances, so an instance evaluated
under several configurations is resampled as one unit). Two methods are
practically equivalent on a scope when that interval lies within +/- max(1.0
weighted unit, 1% of the comparator's mean TWT). Holm correction is applied
within each family of policy-versus-rule and rule-versus-rule comparisons.
The historical Gate-B "beats 3 of 5 rules" outcome is preserved as a v1.0
result; the revision's primary comparison is practical equivalence or
non-inferiority against the strongest transparent rules (tuned ATC, WMDD,
and the EDD family), reported per utilization bin.

**R4.6 Preventive-visibility experiment.** Preventive orders become known L
business hours before their release, L in {0, 8, 40, infinity} (corrective
orders are never known in advance); known orders are plannable but not
startable before release, enforced by the unchanged validator release
check. Methods: the myopic rules unchanged (stated as unable to exploit
visibility by construction); a forecast-aware ATC that conditions its
look-ahead on the trade's known future work (transparent baseline); rolling
CP-SAT with known orders included in its snapshots (it may deliberately
idle for them); and the learned policy retrained with appended lookahead
features, 5 seeds per level (seeds 501+), including an L = 0 control with
the identical widened architecture. Design: PM share {0.2, 0.5, 0.8} x
target utilization {0.7, 0.9, 1.1} fixed-window generator cells (seeds
90000+ block) plus empirical-track cells from the Eval-B anchors at crew
multipliers {1.0, 0.8, 0.6}. Pre-stated hypotheses: H1, visibility has
negligible value under slack capacity; H2, visibility becomes valuable near
capacity when preventive work is a substantial share of workload; H3,
rolling optimization benefits more from visibility than myopic rules,
provided replanning remains feasible; H4, the learned policy gains only if
the lookahead features carry information a fixed rule cannot summarize.
Positive and negative outcomes are reported alike.

**R4.7 Labor-line robustness.** The manuscript reports the measured
multi-line audit (line-count distribution, within-order field agreement,
timestamp patterns) and compares three processing-time models: summed line
hours (v1 default), the dominant line's own hours (max model), and the
single-line-only subset. The endpoint is stability of the method-family
ranking and of the equivalence sets; capacity is recalibrated per model and
the cascade is disclosed.

**R4.8 Capacity-estimator sensitivity.** Crew sizing is recomputed at the
p75, p90, and p95 of weekly trade hours; results are reported against
realized utilization so conclusions do not depend on the estimator; the
realized (post-rounding) effect of every crew multiplier is disclosed
alongside the nominal value.

**R4.9 Release-time robustness (synthetic, stated as such).** Because the
release proxy may postdate the true request time, a clearly-synthetic
backdating scenario shifts each corrective release earlier by
delta ~ Uniform[0, 0.5 x SLA(class)] under a fixed seed, with due windows
recomputed from the shifted release; the endpoint is ranking and
equivalence-set stability.

**R4 adjustments (dated 2026-08-19, after the corpus builders were wired
but before any Eval-B or visibility evaluation existed).** Two elements of
R4.4/R4.6 were adjusted for measured physical constraints, not for any
result. (1) Anchor exclusion: the whole-window rule of R4.4 is
unsatisfiable for 400-order windows on four campuses (the released corpus
already covers 68--79% of their test spans and fragments the remainder into
gaps of median 9--14 business hours, against the 34--72 business hours a
400-order window needs; consequently 5 of 12 cells returned fewer than 10
windows and every 400-order verdict cell was empty). The rule becomes: an
Eval-B window must not overlap any released window OF THE SAME SIZE CLASS,
nor any other Eval-B window in its cell. A wiring smoke had printed
objective values for seven strict-rule instances before this adjustment;
the adjustment is driven by the anchor-supply measurements above, which
contain no method results. (2) Rolling CP-SAT is excluded from the
fixed-window generator cells of both Eval-B and the visibility experiment,
extending the scale boundary already stated for the v1.0 overload sweep:
these cells draw 1,500--12,400 orders per instance, and one 2-second-budget
rolling run on the smallest such instance had not finished after 900
seconds. Rolling runs on the empirical cells (8 configurations per cell as
before), and hypothesis H3 is evaluated there.

**R4.10 Service-window and priority-convention scenarios.** Beyond the
existing uniform +/-50% SLA sweep and weight-vector sweep, two interpretable
scenario families run on the Eval-B empirical base: compressed
emergency-focus (P1/P2 windows halved, P3/P4 unchanged) and routine
tightening (P3/P4 halved, P1/P2 unchanged); and one preventive-priority
convention variant (all preventive orders mapped to P3 instead of P4).
These are scenario robustness checks, not claims about true contracts.

**R4.11 Post-hoc sensitivity analyses (added 2026-08-23, AFTER the final
results existed).** Three checks were added during revision. They are
sensitivity analyses, not pre-specified reporting: R4.5 remains the primary
analysis, and no verdict in the manuscript is taken from R4.11. Each is
reported in full in the Supplementary Material and reproduced by
`scripts/r4_overlap.py` and `scripts/r4_seedboot.py`.

(1) *Window overlap and the resampling cluster.* The same-size-class
acceptance rule of the R4 adjustment leaves windows of different size
classes on one campus free to cover the same stretch of time. Measured on
the instance files: 41 instance pairs of the final empirical set share at
least one work order, all cross-size, all on campuses 10 and 12; 81 of 227
instances touch another; 49,050 work-order slots cover 43,023 distinct work
orders. The primary comparison is re-run with the connected components of
the sharing relation as the resampling cluster (186 components over 227
instances; 139 over the 180 verdict-campus instances). No verdict changes in
any of the 60 scope-by-family cells, and the widest confidence interval
grows by 2.9 per cent.

(2) *Size-stratified re-analysis.* Within one size class no two windows
share a work order, so the primary comparison is also re-run separately for
the 150-order and 400-order instances. At the reference crew multiplier all
ten families are equivalent to EDD in both strata. The strata do not cover
the same campuses (400-order cells exist only on campuses 10 and 12), so a
difference between them confounds instance size with campus.

(3) *Training-seed uncertainty.* The primary intervals for the three policy
pools are conditional on the fixed set of trained seeds, because each pool
is collapsed to a per-configuration seed mean before the bootstrap. A
two-level bootstrap resamples training seeds and instance clusters jointly,
10,000 replicates. The empirical crew-multiplier verdicts are unchanged;
on the generator track the intervals widen by a median factor of 2.7 and
nine of the 33 cells move off a definite verdict, eight of them from worse
to inconclusive. With ten seeds (three for the curriculum-v1 pool) the seed
level is resampled from a small set, so the widened interval should be
interpreted cautiously and may not capture the full training-seed
uncertainty.

Also disclosed with (1): no work order of the final evaluation appears in
any window a policy trained on (0 of 227 instances share with a train-split
v1.0 window), so there is no training leakage; but 101 of 227 share work
orders with a test-split v1.0 window of a different size class, which the
development evaluation scored. The final evaluation is therefore fresh in
its windows and in its construction, not in the underlying work-order
population.
