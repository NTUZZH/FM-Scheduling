"""Statistics-engine tests -- plain python script (no pytest).

Run:  PYTHONPATH=src python tests/test_stats.py

Covers ``fmwos.stats`` (spec S3 / protocol §R4.5).  Every case is synthetic and
self-contained, so the test never reads a results file and never depends on a
run having happened:

(a) BASE INSTANCE IDS: every documented transform suffix round-trips, a v1.0
    id without a suffix passes through unchanged, stacked suffixes all strip,
    and the generator id forms (which end in digits and contain ``_p``/``_c``
    groups) are left alone.

(b) CLUSTER BOOTSTRAP:
      * singleton clusters reproduce the classic row bootstrap -- the CI covers
        the known mean difference, excludes an implausible value, and its width
        matches the analytic normal-approximation width;
      * 10 clusters of 20 identical rows give a MUCH wider CI than treating the
        200 rows as independent (asserted ratio > 2; the theoretical factor is
        sqrt(20) = 4.5);
      * the multiplicity-weight shortcut equals an explicit resample that
        concatenates the drawn clusters' rows, on unequal cluster sizes;
      * the same seed reproduces the interval exactly, and the one-cluster edge
        case degenerates to the point estimate.

(c) HOLM: a hand-computed 4-p-value example.

(d) EQUIVALENCE VERDICT: all four branches, plus the relative-margin case.

(e) WILCOXON: the all-zero / empty convention of scripts/p4_analysis.py.

(f) PAIRED TABLE / EQUIVALENCE SET / COMPARE_ALL on a tiny 3-method frame whose
    answer is known by construction, including the infeasible-row filter, the
    duplicate-row guard, the subsample coverage flag, and the utilization bins.

Prints a report and finally 'ALL STATS TESTS PASSED'.
"""

import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))

from fmwos import stats                                          # noqa: E402

# Small enough to keep the test fast, large enough for stable percentiles.
N_BOOT = 2000


def _close(a, b, tol=1e-6):
    return abs(float(a) - float(b)) <= tol


# --------------------------------------------------------------------------- #
# (a) base instance ids
# --------------------------------------------------------------------------- #
def test_base_instance_id(failures):
    base = "c05_replay_150_0100"
    suffixes = ["_m0.6", "_m1.25", "_m1.0", "_sla0.5", "_sla1.5", "_q75",
                "_q90", "_bd", "_emg", "_rtn", "_pmp3", "_psum", "_pmax",
                "_pone"]
    for suf in suffixes:
        got = stats.base_instance_id(base + suf)
        if got != base:
            failures.append("base_instance_id(%r) = %r, want %r"
                            % (base + suf, got, base))
    print("suffix round-trip: %d documented suffixes -> %s"
          % (len(suffixes), base))

    # v1.0 ids (all five released id forms) pass through unchanged.
    untouched = [
        "c05_replay_150_0100",
        "c01_gen_400_0007",
        "c05_pmmix_150_p20_c60_0000",
        "c09_storm_400_a2.0_c0.6_0011",
        "c12_storm2_w80_u1.1_0003",
    ]
    for i in untouched:
        got = stats.base_instance_id(i)
        if got != i:
            failures.append("base_instance_id(%r) = %r, want it unchanged"
                            % (i, got))
    print("v1.0 id forms unchanged: %s" % ", ".join(untouched))

    # Stacked suffixes strip all the way back to the base instance.
    stacked = base + "_m0.6_sla1.5"
    got = stats.base_instance_id(stacked)
    if got != base:
        failures.append("base_instance_id(%r) = %r, want %r"
                        % (stacked, got, base))
    deep = base + "_m0.8_sla0.5_bd_pmax"
    got_deep = stats.base_instance_id(deep)
    if got_deep != base:
        failures.append("base_instance_id(%r) = %r, want %r"
                        % (deep, got_deep, base))
    print("stacked suffixes: %r -> %r ; %r -> %r"
          % (stacked, got, deep, got_deep))

    # A string that is nothing BUT a suffix must not be stripped to "".
    if stats.base_instance_id("_bd") != "_bd":
        failures.append("base_instance_id('_bd') consumed the whole string")


# --------------------------------------------------------------------------- #
# (b) cluster bootstrap
# --------------------------------------------------------------------------- #
def test_bootstrap_singleton_clusters(failures):
    """All-singleton clusters == the classic bootstrap over rows."""
    rng = np.random.default_rng(7)
    n, true_mean, sd = 400, 5.0, 2.0
    # Centred on the known mean, so the estimand is exactly 5.0 and coverage is
    # a statement about the interval rather than about this particular draw.
    d = rng.normal(0.0, sd, size=n)
    d = d - d.mean() + true_mean
    clusters = np.array(["k%04d" % i for i in range(n)])

    lo, hi = stats.cluster_bootstrap_ci(d, clusters, n_boot=N_BOOT, seed=101)
    if not (lo <= true_mean <= hi):
        failures.append("singleton-cluster CI [%.4f, %.4f] misses the true "
                        "mean %.1f" % (lo, hi, true_mean))
    if lo <= 0.0 <= hi:
        failures.append("singleton-cluster CI [%.4f, %.4f] fails to exclude "
                        "the implausible value 0" % (lo, hi))

    # Classic bootstrap of a mean is the normal approximation at this n.
    analytic = 2 * 1.96 * float(np.std(d, ddof=1)) / np.sqrt(n)
    width = hi - lo
    if not (0.85 * analytic <= width <= 1.15 * analytic):
        failures.append("singleton-cluster CI width %.4f is not within 15%% of "
                        "the analytic width %.4f" % (width, analytic))
    print("singleton clusters (n=%d, mean %.3f): CI [%.3f, %.3f], width %.3f "
          "vs analytic %.3f" % (n, float(d.mean()), lo, hi, width, analytic))


def test_bootstrap_clustered(failures):
    """Correlated rows: the cluster CI must be much wider than the naive one."""
    rng = np.random.default_rng(11)
    n_clusters, per_cluster = 10, 20
    values = rng.normal(5.0, 2.0, size=n_clusters)
    d = np.repeat(values, per_cluster)                 # 20 identical rows each
    clustered = np.repeat(["k%02d" % i for i in range(n_clusters)],
                          per_cluster)
    naive = np.array(["r%04d" % i for i in range(d.size)])

    lo_c, hi_c = stats.cluster_bootstrap_ci(d, clustered, n_boot=N_BOOT,
                                            seed=202)
    lo_n, hi_n = stats.cluster_bootstrap_ci(d, naive, n_boot=N_BOOT, seed=202)
    w_c, w_n = hi_c - lo_c, hi_n - lo_n
    ratio = w_c / w_n if w_n > 0 else float("inf")
    if not ratio > 2.0:
        failures.append("clustered CI width %.4f is only %.2fx the naive width "
                        "%.4f; expected > 2x" % (w_c, ratio, w_n))
    print("clustered (10 clusters x 20 identical rows): cluster CI "
          "[%.3f, %.3f] width %.3f; naive CI [%.3f, %.3f] width %.3f; "
          "ratio %.2fx (theoretical sqrt(20)=%.2f)"
          % (lo_c, hi_c, w_c, lo_n, hi_n, w_n, ratio, np.sqrt(per_cluster)))


def test_bootstrap_matches_explicit_resampling(failures):
    """The multiplicity-weight shortcut must equal the literal resample.

    ``cluster_bootstrap_ci`` never materialises a resampled dataset; it weights
    each cluster by how often it was drawn.  This rebuilds the resamples the
    slow, obvious way -- concatenating the rows of every drawn cluster -- from
    the same generator sequence, and requires the two percentile intervals to
    agree to machine precision.
    """
    rng = np.random.default_rng(19)
    sizes = [3, 7, 2, 5, 4, 6]                 # unequal clusters: the hard case
    labels, values = [], []
    for k, n_k in enumerate(sizes):
        labels += ["k%d" % k] * n_k
        values += list(rng.normal(2.0 * k, 1.0, size=n_k))
    d = np.asarray(values, dtype=float)
    clusters = np.asarray(labels)

    n_boot, seed = 500, 4242
    lo, hi = stats.cluster_bootstrap_ci(d, clusters, n_boot=n_boot, seed=seed)

    rows_by_cluster = [d[clusters == "k%d" % k] for k in range(len(sizes))]
    draw_rng = np.random.default_rng(seed)
    draws = draw_rng.integers(0, len(sizes), size=(n_boot, len(sizes)))
    means = np.array([np.concatenate([rows_by_cluster[j] for j in row]).mean()
                      for row in draws])
    want_lo, want_hi = np.percentile(means, [2.5, 97.5])
    if not (_close(lo, want_lo, 1e-12) and _close(hi, want_hi, 1e-12)):
        failures.append("weighted bootstrap [%.12f, %.12f] != explicit "
                        "resample [%.12f, %.12f]" % (lo, hi, want_lo, want_hi))
    print("weighted vs explicit resample (%d clusters of sizes %s): "
          "[%.6f, %.6f] vs [%.6f, %.6f]"
          % (len(sizes), sizes, lo, hi, want_lo, want_hi))


def test_bootstrap_determinism_and_edges(failures):
    rng = np.random.default_rng(3)
    d = rng.normal(1.0, 1.0, size=60)
    clusters = np.repeat(["k%d" % i for i in range(6)], 10)

    a = stats.cluster_bootstrap_ci(d, clusters, n_boot=N_BOOT, seed=12345)
    b = stats.cluster_bootstrap_ci(d, clusters, n_boot=N_BOOT, seed=12345)
    if a != b:
        failures.append("bootstrap is not deterministic: %r vs %r" % (a, b))
    c = stats.cluster_bootstrap_ci(d, clusters, n_boot=N_BOOT, seed=999)
    if a == c:
        failures.append("different seeds gave an identical CI %r" % (a,))
    print("determinism: seed 12345 -> [%.6f, %.6f] twice; seed 999 -> "
          "[%.6f, %.6f]" % (a[0], a[1], c[0], c[1]))

    # One cluster: no between-cluster variation to resample.
    one = stats.cluster_bootstrap_ci([1.0, 3.0, 5.0], ["k", "k", "k"],
                                     n_boot=N_BOOT, seed=1)
    if not (_close(one[0], 3.0) and _close(one[1], 3.0)):
        failures.append("one-cluster CI %r, want the point estimate (3.0, 3.0)"
                        % (one,))
    empty = stats.cluster_bootstrap_ci([], [], n_boot=N_BOOT, seed=1)
    if not (np.isnan(empty[0]) and np.isnan(empty[1])):
        failures.append("empty CI %r, want (nan, nan)" % (empty,))
    print("edge cases: one cluster -> (%.1f, %.1f); empty -> (nan, nan)"
          % one)


# --------------------------------------------------------------------------- #
# (c) Holm
# --------------------------------------------------------------------------- #
def test_holm(failures):
    """Hand-computed example, m = 4.

    sorted p: d .005, a .01, c .03, b .04
      d: 4*.005 = .020
      a: 3*.010 = .030 -> running max .030
      c: 2*.030 = .060 -> running max .060
      b: 1*.040 = .040 -> running max .060  (monotonicity)
    """
    pv = {"a": 0.01, "b": 0.04, "c": 0.03, "d": 0.005}
    want = {"a": 0.03, "b": 0.06, "c": 0.06, "d": 0.02}
    got = stats.holm(pv)
    for k in want:
        if not _close(got[k], want[k], 1e-12):
            failures.append("holm[%s] = %.6f, want %.6f" % (k, got[k], want[k]))
    if list(got.keys()) != list(pv.keys()):
        failures.append("holm changed the key order: %r" % list(got.keys()))
    print("holm: %s -> %s" % (pv, {k: round(v, 6) for k, v in got.items()}))

    # Capped at 1.0 and stable on an empty input.
    capped = stats.holm({"x": 0.9, "y": 0.95})
    if not (_close(capped["x"], 1.0) and _close(capped["y"], 1.0)):
        failures.append("holm did not cap at 1.0: %r" % capped)
    if stats.holm({}) != {}:
        failures.append("holm({}) is not {}")


# --------------------------------------------------------------------------- #
# (d) equivalence verdict
# --------------------------------------------------------------------------- #
def test_equivalence_verdict(failures):
    cases = [
        # (ci_lo, ci_hi, ref_mean, expected)
        (-0.5, 0.5, 10.0, "equivalent"),      # inside +/- max(1, 0.1) = 1
        (-5.0, -2.0, 100.0, "better"),        # entirely below -1
        (2.0, 5.0, 100.0, "worse"),           # entirely above +1
        (-3.0, 4.0, 100.0, "inconclusive"),   # straddles 0
        (0.5, 3.0, 100.0, "inconclusive"),    # excludes 0 but crosses +margin
        (-8.0, 8.0, 1000.0, "equivalent"),    # relative margin 10 dominates
        (float("nan"), 1.0, 10.0, "inconclusive"),
    ]
    for lo, hi, ref, want in cases:
        got = stats.equivalence_verdict(lo, hi, ref)
        if got != want:
            failures.append("equivalence_verdict(%r, %r, ref=%r) = %r, want %r"
                            % (lo, hi, ref, got, want))
        print("  CI [%6.2f, %6.2f] ref %7.1f (margin %5.2f) -> %s"
              % (lo, hi, ref, stats.equivalence_margin(ref), got))


# --------------------------------------------------------------------------- #
# (e) Wilcoxon convention (matches scripts/p4_analysis.py)
# --------------------------------------------------------------------------- #
def test_wilcoxon_p(failures):
    if stats.wilcoxon_p([]) != 1.0:
        failures.append("wilcoxon_p([]) != 1.0")
    if stats.wilcoxon_p(np.zeros(20)) != 1.0:
        failures.append("wilcoxon_p(all zeros) != 1.0")
    rng = np.random.default_rng(5)
    d = rng.normal(2.0, 1.0, size=30)
    want = float(wilcoxon(d).pvalue)
    got = stats.wilcoxon_p(d)
    if not _close(got, want, 1e-12):
        failures.append("wilcoxon_p = %.3e, scipy = %.3e" % (got, want))
    print("wilcoxon: empty -> 1.0; all-zero -> 1.0; shifted sample -> %.3e"
          % got)


# --------------------------------------------------------------------------- #
# (f) frame-level drivers on a tiny synthetic results frame
# --------------------------------------------------------------------------- #
def _tiny_frame():
    """3 methods x 5 base instances x 4 configurations, known by construction.

    ``a`` is best; ``b`` is 0.2 weighted units worse on every configuration
    (well inside the margin, which is max(1.0, 1% of ~110) = 1.1); ``c`` is 50
    units worse (far outside).  Every row is feasible.
    """
    rows = []
    i = 0
    for k in range(5):
        base = "c05_replay_150_010%d" % k
        for suffix in ("", "_m0.6", "_sla0.5", "_bd"):
            va = 100.0 + i
            rows.append({"id": base + suffix, "method": "a", "feasible": 1,
                         "wwt": va, "u_realized": 0.4 + 0.25 * k})
            rows.append({"id": base + suffix, "method": "b", "feasible": 1,
                         "wwt": va + 0.2, "u_realized": 0.4 + 0.25 * k})
            rows.append({"id": base + suffix, "method": "c", "feasible": 1,
                         "wwt": va + 50.0, "u_realized": 0.4 + 0.25 * k})
            i += 1
    return pd.DataFrame(rows)


def test_paired_table(failures):
    df = _tiny_frame()
    pt = stats.paired_table(df, "b", "a")
    if len(pt) != 20:
        failures.append("paired_table has %d rows, want 20" % len(pt))
    if pt["cluster"].nunique() != 5:
        failures.append("paired_table has %d clusters, want 5"
                        % pt["cluster"].nunique())
    if not np.allclose(pt["diff"].to_numpy(), 0.2):
        failures.append("paired_table diffs are not all 0.2")
    print("paired_table(b, a): %d configs, %d clusters, mean diff %+.3f"
          % (len(pt), pt["cluster"].nunique(), pt["diff"].mean()))

    # Infeasible rows drop out of the pairing.
    df2 = df.copy()
    df2.loc[(df2["method"] == "b") & (df2["id"].str.endswith("_bd")),
            "feasible"] = 0
    pt2 = stats.paired_table(df2, "b", "a")
    if len(pt2) != 15:
        failures.append("infeasible filter left %d rows, want 15" % len(pt2))

    # A duplicated (id, method) pair means the frame still mixes regimes.
    df3 = pd.concat([df, df[df["method"] == "a"].head(1)], ignore_index=True)
    try:
        stats.paired_table(df3, "b", "a")
        failures.append("paired_table accepted a duplicated (id, method) row")
    except ValueError as exc:
        print("duplicate guard: %s" % exc)
    pt3 = stats.paired_table(df3, "b", "a", on_duplicate="mean")
    if len(pt3) != 20:
        failures.append("on_duplicate='mean' left %d rows, want 20" % len(pt3))


def test_equivalence_set(failures):
    df = _tiny_frame()
    eq = stats.equivalence_set(df, n_boot=N_BOOT).set_index("method")
    print("equivalence_set (pooled):")
    for meth in ("a", "b", "c"):
        r = eq.loc[meth]
        print("  %s: mean %8.3f  diff %+7.3f  CI [%+.3f, %+.3f]  margin %.3f "
              " %-12s in_set=%d"
              % (meth, r["mean"], r["mean_diff"], r["ci_lo"], r["ci_hi"],
                 r["margin"], r["verdict"], int(r["in_equivalence_set"])))
    want_best = "a"
    if set(eq["best_method"]) != {want_best}:
        failures.append("best method is %r, want %r"
                        % (sorted(set(eq["best_method"])), want_best))
    want_set = {"a": 1, "b": 1, "c": 0}
    for meth, want in want_set.items():
        got = int(eq.loc[meth, "in_equivalence_set"])
        if got != want:
            failures.append("in_equivalence_set[%s] = %d, want %d"
                            % (meth, got, want))
    if eq.loc["c", "verdict"] != "worse":
        failures.append("verdict for c is %r, want 'worse'"
                        % eq.loc["c", "verdict"])
    if int(eq.loc["b", "n_clusters"]) != 5:
        failures.append("n_clusters for b is %d, want 5"
                        % int(eq.loc["b", "n_clusters"]))

    if not np.allclose(eq["coverage"].to_numpy(), 1.0):
        failures.append("coverage is not 1.0 for a fully-crossed frame: %r"
                        % eq["coverage"].to_dict())
    # A subsampled method (rolling CP-SAT is run on 8 instances per cell) must
    # be flagged by coverage, not silently ranked against full-coverage means.
    sub_df = pd.concat([df[df["method"] != "c"],
                        df[df["method"] == "c"].head(5)], ignore_index=True)
    eq_sub = stats.equivalence_set(sub_df, n_boot=N_BOOT).set_index("method")
    if not _close(eq_sub.loc["c", "coverage"], 0.25):
        failures.append("coverage for the subsampled method is %.3f, want 0.25"
                        % eq_sub.loc["c", "coverage"])
    print("coverage: full frame 1.00 for all methods; 5-of-20 subsample -> "
          "%.2f" % eq_sub.loc["c", "coverage"])

    # Scoped by utilization bin: the same answer inside every bin.
    df = stats.add_utilization_bin(df)
    eq_u = stats.equivalence_set(df, scope_cols=["u_bin"], n_boot=N_BOOT)
    bins = sorted(eq_u["u_bin"].unique())
    if set(eq_u[eq_u["method"] == "c"]["in_equivalence_set"]) != {0}:
        failures.append("method c entered an equivalence set in some u bin")
    print("per-u_bin equivalence sets: bins %s; c excluded from all" % bins)


def test_compare_all(failures):
    df = _tiny_frame()
    comp = stats.compare_all(df, reference_methods=["a"], n_boot=N_BOOT)
    print("compare_all vs reference a:")
    for _, r in comp.iterrows():
        print("  %s vs %s: n=%d clusters=%d diff %+7.3f CI [%+.3f, %+.3f] "
              "p=%.3g holm=%.3g %s (%s)"
              % (r["method"], r["reference"], r["n_configs"], r["n_clusters"],
                 r["mean_diff"], r["ci_lo"], r["ci_hi"], r["wilcoxon_p"],
                 r["holm_p"], r["verdict"], r["family"]))
    for col in stats.COMPARE_COLUMNS:
        if col not in comp.columns:
            failures.append("compare_all output is missing column %r" % col)
    if len(comp) != 2:
        failures.append("compare_all produced %d rows, want 2" % len(comp))
    v = dict(zip(comp["method"], comp["verdict"]))
    if v.get("b") != "equivalent" or v.get("c") != "worse":
        failures.append("compare_all verdicts %r, want b=equivalent, c=worse"
                        % v)
    # Holm within the family: 2 comparisons, so the smaller p doubles.
    fam = set(comp["family"])
    if fam != {"rule-vs-rule"}:
        # 'a','b','c' are not known rule names, so they classify as policies.
        if fam != {"policy-vs-policy"}:
            failures.append("unexpected family labels %r" % fam)
    for _, r in comp.iterrows():
        if r["holm_p"] < r["wilcoxon_p"] - 1e-12:
            failures.append("holm_p %.6g < raw p %.6g for %s"
                            % (r["holm_p"], r["wilcoxon_p"], r["method"]))


def test_utilization_bin(failures):
    cases = [(0.0, "<0.5"), (0.49999, "<0.5"), (0.5, "0.5-0.8"),
             (0.79, "0.5-0.8"), (0.8, "0.8-1.0"), (0.999, "0.8-1.0"),
             (1.0, "1.0-1.2"), (1.19, "1.0-1.2"), (1.2, ">=1.2"),
             (3.0, ">=1.2"), (None, "unknown"), (float("nan"), "unknown")]
    for u, want in cases:
        got = stats.utilization_bin(u)
        if got != want:
            failures.append("utilization_bin(%r) = %r, want %r" % (u, got, want))
    print("utilization_bin: %d boundary cases OK (labels %s)"
          % (len(cases), ", ".join(stats.U_BIN_ORDER)))


def main():
    failures = []
    print("== (a) base instance ids ==")
    test_base_instance_id(failures)
    print("\n== (b) cluster bootstrap ==")
    test_bootstrap_singleton_clusters(failures)
    test_bootstrap_clustered(failures)
    test_bootstrap_matches_explicit_resampling(failures)
    test_bootstrap_determinism_and_edges(failures)
    print("\n== (c) Holm ==")
    test_holm(failures)
    print("\n== (d) equivalence verdict ==")
    test_equivalence_verdict(failures)
    print("\n== (e) Wilcoxon ==")
    test_wilcoxon_p(failures)
    print("\n== (f) frame drivers ==")
    test_paired_table(failures)
    test_equivalence_set(failures)
    test_compare_all(failures)
    test_utilization_bin(failures)

    if failures:
        print("\nFAILURES:")
        for f in failures:
            print("  - " + f)
        sys.exit(1)
    print("\nALL STATS TESTS PASSED")


if __name__ == "__main__":
    main()
