#!/usr/bin/env python
"""Two-level uncertainty for the learned pools: instances AND training seeds.

Why this analysis exists
------------------------
``scripts/r4_family_analysis.py`` reduces each learned-policy pool to ONE value
per instance-configuration before any interval is computed: ``collapse_families``
averages the pool's training seeds on the configuration, and the paired
comparison against EDD is then bootstrapped over base-instance clusters alone.
That is the right way to stop ten training runs of one configuration counting as
ten methods, but it fixes the seed sample while resampling the instance sample,
so the released interval is CONDITIONAL on the particular seeds that were
trained.  It describes uncertainty from the instances only.

The seed sample is a sample too.  This script adds the second level and reports
all three intervals side by side on the same comparison:

* **instance-only**  clusters resampled, seeds held at the full set.  This is
  the released quantity, recomputed here as a control.
* **seed-only**      the pool's seed columns resampled with replacement (a seed
  drawn twice counts twice), instances held fixed.
* **two-level**      clusters and seed columns resampled independently inside
  the same replicate.

Nothing is re-run and no schedule is re-scored: every value comes from the
existing seed-level result rows.

What is computed
----------------
For each scope of ``scripts/r4_analysis.scope_frames`` whose type is one of
``emp_m``, ``gen_all``, ``gen_utarget``, ``transfer`` or ``stress``, and for
each of the three pools (``mlp_pool`` = 10 MLP seeds, ``attn_pool`` = 10
attention seeds, ``v1_pool`` = 3 curriculum-v1 seeds):

1. The configurations where EDD is feasible and EVERY one of the pool's seeds is
   feasible.  That is the released coverage rule, so a pool value is never
   averaged over a different seed set than its neighbours.
2. ``V``, the (configurations x seeds) matrix of per-seed values in a fixed
   sorted seed order; ``r``, the EDD value on each configuration; and the
   base-instance cluster of each configuration.
3. The point estimate ``mean_i( mean_k V[i,k] - r[i] )``, which is the released
   ``mean_diff`` for that (scope, family) by construction.  It is checked against
   ``results/r4_final/analysis/family_comparisons.csv`` field by field and any
   mismatch stops the run before an output is written: that check is what proves
   the three intervals below belong to the quantity the manuscript reports.
   The instance-only interval is checked the same way, on the released
   comparison's own bootstrap stream, so a difference between this run's
   instance-only bounds and the released ones can only be the draw sequence.
4. The three 95% percentile intervals, each from ``--n-boot`` resamples with a
   fixed seed derived from the cell's label, with the protocol equivalence
   verdict (margin ``max(1.0, 1% of the reference mean)``) and the interval
   width for each.

Arithmetic of the joint draw.  Writing ``s`` for the multiplicity of each seed
column in a replicate and ``w`` for the multiplicity of each cluster, the pool
value on configuration ``i`` is ``(V[i,:] . s) / K`` and the resampled mean is
``(w . cluster_sums) / (w . cluster_counts)``, exactly the weighted form
``fmwos.stats.cluster_bootstrap_ci`` uses.  With the seed multiplicities held at
one this reduces to that function, and the run asserts the reduction on every
cell rather than assuming it.

What the method cannot do
-------------------------
Ten training seeds (three for ``v1_pool``) are a small sample, and a bootstrap
resamples only the seeds that exist.  The seed level here is therefore coarse:
the two-level interval should be interpreted cautiously, may not capture the
full training-seed uncertainty, and says nothing about seed variation the
trained set never exhibited.  The report states this in the same words.

Inputs
------
  results/r4_final/results.csv                          (Eval-B, seed level)
  results/r4_final/analysis/family_comparisons.csv      (the released point
                                                         estimates and intervals)

Outputs
-------
  results/r4_final/analysis/seed_bootstrap.csv          one row per scope x pool
  results/r4_final/analysis/seed_bootstrap_summary.md   the readable report
  paper/macros_r4i.tex                                  the \\sbo... macros

Usage
-----
    PYTHONPATH=src python scripts/r4_seedboot.py [--out DIR] [--paper DIR]
                                                 [--n-boot N] [--seed S]
                                                 [--no-macros]

Re-running is idempotent: every stream is seeded from the protocol master seed
and the cell label, the iteration order is fixed, and every output is rewritten
from the same inputs, so a second run reproduces every digit.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

# Small dense linear algebra and bincounts only; keep the shared box's BLAS from
# oversubscribing it.
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "8")

import numpy as np                                          # noqa: E402
import pandas as pd                                         # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from fmwos import stats                                     # noqa: E402
# Scope construction, macro plumbing and number formatting are shared with the
# released analyses so the generated files read identically and no scope, seed
# set or margin is redefined here.
from r4_analysis import (U_TOKEN, VALUE_COL, MacroFile,     # noqa: E402
                         existing_macro_names, house_number,
                         f_diff, f_int, f_pct, f_text, f_twt,
                         load_results, scope_frames)
from r4_family_analysis import (FAMILY_NAME, POOL_SEEDS,    # noqa: E402
                                REFERENCE)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
EVALB_CSV = Path("results/r4_final/results.csv")
FAMILY_CSV = Path("results/r4_final/analysis/family_comparisons.csv")
OUT_DIR = Path("results/r4_final/analysis")
PAPER_DIR = Path("paper")
MACRO_FILE = "macros_r4i.tex"

# The pools, in report order, with the label every output carries.
POOL_KEYS = ("v2pool", "v2attnpool", "v1pool")
POOL_TOKEN = {"v2pool": "Mlp", "v2attnpool": "Attn", "v1pool": "Vone"}

# Scope types carried here: the empirical verdict campuses per crew multiplier,
# the generator track pooled and per target utilisation, and the two single
# campuses.  The heterogeneous scopes (overall, emp_pooled) and the finer
# empirical splits are left out: they are not the scopes the pool verdicts are
# quoted on.
SCOPE_TYPES = ("emp_m", "gen_all", "gen_utarget", "transfer", "stress")

# The scope the manuscript's headline pool verdicts are read from.
HEADLINE_SCOPE = ("emp_m", "m=1.0")

# The two halves the seed level separates: the empirical crew-multiplier scopes,
# where the pools sit inside the equivalence margin, and the generator scopes,
# where they do not.  Every verdict change falls in the second group.
EMP_SCOPE_TYPES = ("emp_m",)
GEN_SCOPE_TYPES = ("gen_all", "gen_utarget")
# The generator target utilisations the prose quotes, with the token r4_analysis
# already uses for them in the companion macro files.
GEN_QUOTED = (1.1, 1.3)

# The point estimate must reproduce the released one exactly; it is the same
# arithmetic on the same rows, so the tolerance is float round-off, not slack.
RECONCILE_TOL = 1e-9

# On the transfer campus the pools reproduce EDD exactly, so both intervals
# there are round-off around zero and their ratio measures floating-point noise
# rather than uncertainty.  The equivalence margin is at least 1.0 weighted
# unit, so an interval narrower than this carries no width worth comparing; such
# cells keep their raw ratio in the CSV and are counted separately in the report
# and excluded from the summary median and maximum.
NOISE_WIDTH = 1e-9

# The released interval of a pool comes from ``fmwos.stats.compare_all`` with the
# per-comparison stream "<scope label>|<method>|<reference>" and the protocol
# master seed, so feeding that stream to the instance-only arm must return the
# released bounds themselves rather than a nearby pair.  The check runs only at
# the protocol resample count, because a different count is a different stream.
RELEASED_STREAM = "analysis_scope=%s|%s|%s"
RELEASED_CI_TOL = 1e-6

CSV_COLUMNS = [
    "scope_type", "scope", "family", "n_seeds", "n_configs", "n_clusters",
    "mean_ref", "mean_diff", "released_mean_diff",
    "ci_lo_inst", "ci_hi_inst", "verdict_inst",
    "ci_lo_seed", "ci_hi_seed", "verdict_seed",
    "ci_lo_two", "ci_hi_two", "verdict_two",
    "width_inst", "width_seed", "width_two", "width_ratio_two_inst",
    "verdict_changed", "seed_sd", "seed_min_mean", "seed_max_mean",
]


# --------------------------------------------------------------------------- #
# Cell construction
# --------------------------------------------------------------------------- #
def build_cell(sub: pd.DataFrame, pool: str):
    """The per-seed matrix, the reference vector and the clusters of one cell.

    ``sub`` is one scope of the seed-level results file.  A configuration enters
    when EDD has a feasible row on it and every seed of the pool has one, which
    is the coverage rule ``r4_family_analysis.collapse_families`` applies.
    Returns ``None`` when the pool did not run on the scope.
    """
    seeds = sorted(POOL_SEEDS[pool])
    present = set(sub["method"].astype(str))
    missing = [s for s in seeds if s not in present]
    if len(missing) == len(seeds):
        return None
    if missing:
        raise SystemExit("pool %s is partially present on this scope (%d of %d "
                         "seeds); refusing to average over a different seed set"
                         % (FAMILY_NAME[pool], len(seeds) - len(missing),
                            len(seeds)))
    feas = sub[sub["feasible"] == 1] if "feasible" in sub.columns else sub

    ref = feas[feas["method"] == REFERENCE][["id", VALUE_COL]]
    if ref["id"].duplicated().any():
        raise SystemExit("the reference has several rows for one configuration; "
                         "the scope still mixes regimes")
    ref = ref.set_index("id")[VALUE_COL]

    pool_rows = feas[feas["method"].isin(seeds)]
    if pool_rows.duplicated(["id", "method"]).any():
        raise SystemExit("a seed has several rows for one configuration; the "
                         "scope still mixes regimes")
    wide = pool_rows.pivot_table(index="id", columns="method",
                                 values=VALUE_COL, aggfunc="mean")
    if wide.empty:
        return None
    wide = wide.reindex(columns=seeds)
    # Complete seed coverage, then the intersection with the reference.
    wide = wide.dropna(axis=0, how="any")
    ids = sorted(set(wide.index) & set(ref.index))
    if not ids:
        return None
    wide = wide.loc[ids]
    V = wide.to_numpy(dtype=float)
    r = ref.loc[ids].to_numpy(dtype=float)
    clusters = np.array([stats.base_instance_id(i) for i in ids], dtype=object)
    return {"ids": ids, "seeds": seeds, "V": V, "r": r, "clusters": clusters}


def _cluster_aggregates(V, r, clusters):
    """Per-cluster seed-wise sums, reference sums and row counts."""
    _uniq, idx = np.unique(np.asarray(clusters, dtype=object),
                           return_inverse=True)
    n_clusters = int(idx.max()) + 1
    K = V.shape[1]
    A = np.empty((n_clusters, K), dtype=float)
    for k in range(K):
        A[:, k] = np.bincount(idx, weights=V[:, k], minlength=n_clusters)
    b = np.bincount(idx, weights=r, minlength=n_clusters)
    counts = np.bincount(idx, minlength=n_clusters).astype(float)
    return A, b, counts, n_clusters


def _multiplicities(rng, n, rows):
    """Row-wise multiplicity counts of ``n`` draws with replacement, ``rows`` of
    them, through one flat bincount (the form ``cluster_bootstrap_ci`` uses)."""
    draw = rng.integers(0, n, size=(rows, n))
    flat = draw + (np.arange(rows)[:, None] * n)
    return np.bincount(flat.ravel(), minlength=rows * n
                       ).reshape(rows, n).astype(float)


def bootstrap_ci(V, r, clusters, n_boot: int, seed: int,
                 resample_clusters: bool, resample_seeds: bool,
                 alpha: float = stats.ALPHA):
    """Percentile interval of the mean paired difference under one draw scheme.

    With ``resample_seeds`` false and ``resample_clusters`` true this is exactly
    ``fmwos.stats.cluster_bootstrap_ci`` on the seed-averaged differences: the
    same weighted mean, the same chunking and the same draw sequence.  The seed
    level enters as a second multiplicity vector inside the replicate, so the
    pool value on a configuration is the mean of the drawn columns.
    """
    A, b, counts, n_clusters = _cluster_aggregates(V, r, clusters)
    K = V.shape[1]
    if n_clusters == 1 and resample_clusters and not resample_seeds:
        # One cluster carries no between-cluster variation to resample; the
        # released function reports the point estimate twice and so does this.
        mean = float((A.sum() / K - b.sum()) / counts.sum())
        return mean, mean
    rng = np.random.default_rng(seed)
    chunk = max(1, min(int(n_boot), stats._MAX_BOOT_CELLS // max(1, n_clusters)))
    means = np.empty(int(n_boot), dtype=float)
    done = 0
    while done < n_boot:
        rows = min(chunk, int(n_boot) - done)
        if resample_clusters:
            w = _multiplicities(rng, n_clusters, rows)
        else:
            w = np.ones((rows, n_clusters), dtype=float)
        if resample_seeds:
            s = _multiplicities(rng, K, rows)
        else:
            s = np.ones((rows, K), dtype=float)
        num = ((w @ A) * s).sum(axis=1) / K - (w @ b)
        means[done:done + rows] = num / (w @ counts)
        done += rows
    lo, hi = np.percentile(means, [100.0 * alpha / 2.0,
                                   100.0 * (1.0 - alpha / 2.0)])
    return float(lo), float(hi)


def cell_row(scope_type: str, scope: str, pool: str, cell: dict,
             released: pd.DataFrame, n_boot: int, seed: int) -> dict:
    """One (scope, pool) row: the point estimate and the three intervals."""
    V, r, clusters = cell["V"], cell["r"], cell["clusters"]
    family = FAMILY_NAME[pool]
    n_configs = int(V.shape[0])
    n_clusters = int(len(set(clusters)))
    mean_ref = float(r.mean())
    d = V.mean(axis=1) - r
    mean_diff = float(d.mean())

    # ---- the released row this cell must reproduce ----------------------- #
    want = released[(released["scope_type"] == scope_type)
                    & (released["scope"] == scope)
                    & (released["family"] == family)]
    if len(want) != 1:
        raise SystemExit("expected one released row for %s / %s / %s, found %d"
                         % (scope_type, scope, family, len(want)))
    w = want.iloc[0]
    for field, got in (("n_configs", n_configs), ("n_clusters", n_clusters)):
        if int(w[field]) != got:
            raise SystemExit(
                "coverage mismatch on %s / %s / %s: released %s = %d, "
                "recomputed %d" % (scope_type, scope, family, field,
                                   int(w[field]), got))
    released_diff = float(w["mean_diff"])
    if abs(mean_diff - released_diff) > RECONCILE_TOL:
        raise SystemExit(
            "point estimate mismatch on %s / %s / %s: released mean_diff "
            "%.12g, recomputed %.12g (difference %.3g exceeds %.0e); the two "
            "are not the same quantity, so no output was written"
            % (scope_type, scope, family, released_diff, mean_diff,
               abs(mean_diff - released_diff), RECONCILE_TOL))

    # ---- the three intervals --------------------------------------------- #
    label = "seedboot|%s|%s|%s" % (scope_type, scope, family)
    arms = {}
    for arm, (rc, rs) in (("inst", (True, False)), ("seed", (False, True)),
                          ("two", (True, True))):
        arms[arm] = bootstrap_ci(
            V, r, clusters, n_boot=n_boot,
            seed=stats._derived_seed(seed, "%s|%s" % (label, arm)),
            resample_clusters=rc, resample_seeds=rs)

    # The instance-only arm must be the released function's own output on the
    # seed-averaged differences; checking it here is what licenses the explicit
    # arithmetic used for the joint draw.
    check = stats.cluster_bootstrap_ci(
        d, clusters, n_boot=n_boot,
        seed=stats._derived_seed(seed, "%s|inst" % label))
    # Algebraically the same expression, evaluated in a different order, so the
    # agreement is exact up to floating-point round-off rather than bit for bit.
    if not np.allclose(arms["inst"], check, rtol=1e-9, atol=1e-9,
                       equal_nan=True):
        raise SystemExit(
            "the instance-only arm on %s / %s / %s does not reproduce "
            "fmwos.stats.cluster_bootstrap_ci (%r vs %r)"
            % (scope_type, scope, family, arms["inst"], check))

    row = {"scope_type": scope_type, "scope": scope, "family": family,
           "n_seeds": int(V.shape[1]), "n_configs": n_configs,
           "n_clusters": n_clusters, "mean_ref": mean_ref,
           "mean_diff": mean_diff, "released_mean_diff": released_diff}
    for arm in ("inst", "seed", "two"):
        lo, hi = arms[arm]
        row["ci_lo_%s" % arm] = lo
        row["ci_hi_%s" % arm] = hi
        row["verdict_%s" % arm] = stats.equivalence_verdict(lo, hi, mean_ref)
        row["width_%s" % arm] = float(hi - lo)
    # A width ratio needs a positive denominator; on the transfer campus every
    # pool matches EDD to floating-point noise and the instance-only interval
    # has no width, so the ratio is left undefined there rather than forced.
    row["width_ratio_two_inst"] = (row["width_two"] / row["width_inst"]
                                   if row["width_inst"] > 0.0 else float("nan"))
    row["verdict_changed"] = int(row["verdict_two"] != row["verdict_inst"])

    seed_means = V.mean(axis=0)
    row["seed_sd"] = (float(seed_means.std(ddof=1)) if seed_means.size > 1
                      else 0.0)
    row["seed_min_mean"] = float(seed_means.min())
    row["seed_max_mean"] = float(seed_means.max())

    # Kept out of the CSV (whose schema is fixed) and used by the report: how
    # far this run's instance-only arm lands from the released interval, which
    # is Monte-Carlo noise from a different stream and nothing else.
    row["_released_ci_lo"] = float(w["ci_lo"])
    row["_released_ci_hi"] = float(w["ci_hi"])
    row["_released_verdict"] = str(w["verdict"])
    row["_inst_vs_released"] = max(abs(row["ci_lo_inst"] - float(w["ci_lo"])),
                                   abs(row["ci_hi_inst"] - float(w["ci_hi"])))
    row["_released_width"] = float(w["ci_hi"]) - float(w["ci_lo"])

    # Same arm, run on the released comparison's own stream: this must return
    # the released bounds themselves, which separates a different draw sequence
    # from a different estimator.  A resample count other than the protocol one
    # is a different stream, so the check applies only at the protocol count.
    row["_released_stream_dev"] = float("nan")
    if n_boot == stats.N_BOOT:
        lo, hi = stats.cluster_bootstrap_ci(
            d, clusters, n_boot=n_boot,
            seed=stats._derived_seed(stats.SEED,
                                     RELEASED_STREAM % (scope, pool, REFERENCE)))
        dev = max(abs(lo - float(w["ci_lo"])), abs(hi - float(w["ci_hi"])))
        row["_released_stream_dev"] = float(dev)
        if dev > RELEASED_CI_TOL:
            raise SystemExit(
                "the instance-only arm on %s / %s / %s does not reproduce the "
                "released interval on the released stream: recomputed "
                "[%.9g, %.9g], released [%.9g, %.9g], deviation %.3g > %.0e"
                % (scope_type, scope, family, lo, hi, float(w["ci_lo"]),
                   float(w["ci_hi"]), dev, RELEASED_CI_TOL))
    return row


def build_table(df: pd.DataFrame, released: pd.DataFrame, n_boot: int,
                seed: int) -> pd.DataFrame:
    rows = []
    for scope_type, scope, sub in scope_frames(df):
        if scope_type not in SCOPE_TYPES:
            continue
        for pool in POOL_KEYS:
            cell = build_cell(sub, pool)
            if cell is None:
                continue
            rows.append(cell_row(scope_type, scope, pool, cell, released,
                                 n_boot, seed))
            print("  %-12s %-16s %-10s n=%d clusters=%d"
                  % (scope_type, scope, FAMILY_NAME[pool],
                     rows[-1]["n_configs"], rows[-1]["n_clusters"]), flush=True)
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #
def _fmt(x, nd=3):
    if x is None or (isinstance(x, float) and not np.isfinite(float(x))):
        return "-"
    return ("%%.%df" % nd) % float(x)


def _md_table(frame: pd.DataFrame, cols, nd=3) -> str:
    head = ("| " + " | ".join(cols) + " |\n|"
            + "|".join(["---"] * len(cols)) + "|\n")
    body = []
    for r in frame.itertuples():
        cells = []
        for c in cols:
            v = getattr(r, c)
            cells.append(_fmt(v, nd) if isinstance(v, float) else str(v))
        body.append("| " + " | ".join(cells) + " |")
    return head + "\n".join(body) + "\n"


def _cell_label(r) -> str:
    return "%s / %s / %s" % (r["scope_type"], r["scope"], r["family"])


def split_by_width(tab: pd.DataFrame):
    """Split the cells into those whose width ratio is informative and the rest.

    A cell whose instance-only interval is narrower than ``NOISE_WIDTH`` has no
    width to compare: both of its intervals are round-off around zero.  The
    width summaries run over the informative cells and count the others.
    """
    ok = (tab["width_inst"] > NOISE_WIDTH) & np.isfinite(
        tab["width_ratio_two_inst"])
    return tab[ok], tab[~ok]


REPORT_COLS = ["scope_type", "scope", "family", "n_seeds", "n_configs",
               "n_clusters", "mean_diff", "ci_lo_inst", "ci_hi_inst",
               "verdict_inst", "ci_lo_seed", "ci_hi_seed", "verdict_seed",
               "ci_lo_two", "ci_hi_two", "verdict_two", "width_ratio_two_inst"]


def write_report(path: Path, tab: pd.DataFrame, n_boot: int, seed: int) -> Path:
    L = []
    A = L.append
    informative, degenerate = split_by_width(tab)
    ratios = informative["width_ratio_two_inst"]
    changed = tab[tab["verdict_changed"] == 1]
    head = tab[(tab["scope_type"] == HEADLINE_SCOPE[0])
               & (tab["scope"] == HEADLINE_SCOPE[1])]

    A("# Seed-level uncertainty in the pool-vs-EDD comparisons")
    A("")
    A("Generated by scripts/r4_seedboot.py on %s."
      % datetime.now().isoformat(timespec="seconds"))
    A("")
    A("The released pool intervals (results/r4_final/analysis/"
      "family_comparisons.csv) collapse each pool to one value per "
      "instance-configuration, the mean over its training seeds, and then "
      "resample base-instance clusters. They are therefore conditional on the "
      "seeds that were trained and describe uncertainty from the instance "
      "sample alone. This report recomputes the same point estimates and adds "
      "the seed level.")
    A("")
    A("Three intervals per cell, each a 95%% percentile interval from %d "
      "resamples with a seed derived from the cell label and the protocol "
      "master seed %d:" % (n_boot, seed))
    A("")
    A("- instance-only: clusters resampled, seeds held at the full set (the "
      "released quantity);")
    A("- seed-only: the pool's seed columns resampled with replacement, a seed "
      "drawn twice counting twice, instances held fixed;")
    A("- two-level: clusters and seed columns resampled independently inside "
      "one replicate.")
    A("")
    A("Verdicts use the protocol margin max(%.1f, %.0f%% of the reference "
      "mean) (fmwos.stats.equivalence_verdict). A negative difference means the "
      "pool is better than EDD. `width` is ci_hi minus ci_lo, so it is twice "
      "the half-width."
      % (stats.MARGIN_ABS, 100 * stats.MARGIN_REL))
    A("")

    A("## 1. Cells computed, and the point estimates they rest on")
    A("")
    A("%d (scope, pool) cells: %d scopes of types %s, times the three pools "
      "(mlp_pool = %d MLP seeds, attn_pool = %d attention seeds, v1_pool = %d "
      "curriculum-v1 seeds)."
      % (len(tab), tab.groupby(["scope_type", "scope"]).ngroups,
         ", ".join(SCOPE_TYPES),
         int(tab.loc[tab["family"] == "mlp_pool", "n_seeds"].iloc[0]),
         int(tab.loc[tab["family"] == "attn_pool", "n_seeds"].iloc[0]),
         int(tab.loc[tab["family"] == "v1_pool", "n_seeds"].iloc[0])))
    A("")
    A("Every point estimate reproduces the released mean_diff for its (scope, "
      "family): largest absolute deviation %.3g over %d cells, against a "
      "tolerance of %.0e, and the configuration and cluster counts match "
      "exactly. A mismatch aborts the run, because it would mean the intervals "
      "below belong to a different quantity than the one the manuscript "
      "reports."
      % (float((tab["mean_diff"] - tab["released_mean_diff"]).abs().max()),
         len(tab), RECONCILE_TOL))
    A("")
    share = (tab["_inst_vs_released"]
             / tab["_released_width"].where(tab["_released_width"] > NOISE_WIDTH))
    A("The instance-only arm is the released computation rerun on a different "
      "stream, so it agrees with the released interval up to Monte-Carlo noise "
      "rather than digit for digit. Largest absolute deviation on an interval "
      "bound %.4g, median %.4g; as a share of the released interval width, "
      "median %.2f%% and largest %.2f%% over the %d cells whose released "
      "interval has width. %d of %d released verdicts are reproduced%s."
      % (float(tab["_inst_vs_released"].max()),
         float(tab["_inst_vs_released"].median()),
         100.0 * float(share.median()), 100.0 * float(share.max()),
         int(share.notna().sum()),
         int((tab["verdict_inst"] == tab["_released_verdict"]).sum()), len(tab),
         "" if bool((tab["verdict_inst"] == tab["_released_verdict"]).all())
         else " (the exceptions are cells whose released interval already sat "
              "on a margin edge)"))
    A("")
    dev = tab["_released_stream_dev"]
    if bool(dev.notna().all()):
        A("Given the released comparison's own bootstrap stream instead, the "
          "same arm returns the released bounds themselves: largest deviation "
          "%.3g over %d cells, against a tolerance of %.0e. The deviations in "
          "the previous paragraph are therefore the draw sequence and nothing "
          "else; the estimator is the released one."
          % (float(dev.max()), int(dev.notna().sum()), RELEASED_CI_TOL))
    else:
        A("The check that the same arm returns the released bounds on the "
          "released comparison's own stream was skipped: it holds only at the "
          "protocol resample count of %d, and this run used %d."
          % (stats.N_BOOT, n_boot))
    A("")

    A("## 2. Verdicts that change when seed uncertainty is added")
    A("")
    if changed.empty:
        A("None. All %d cells carry the same equivalence verdict under the "
          "two-level interval as under the instance-only one." % len(tab))
    else:
        A("%d of %d cells change verdict between the instance-only and the "
          "two-level interval:" % (len(changed), len(tab)))
        A("")
        for _, r in changed.iterrows():
            A("- %s: %s -> %s (instance-only [%.3f, %.3f], two-level "
              "[%.3f, %.3f], margin %.3f)"
              % (_cell_label(r), r["verdict_inst"], r["verdict_two"],
                 r["ci_lo_inst"], r["ci_hi_inst"], r["ci_lo_two"],
                 r["ci_hi_two"], stats.equivalence_margin(r["mean_ref"])))
    A("")

    A("## 3. How much wider the two-level interval is")
    A("")
    A("Ratio of the two-level interval width to the instance-only width, over "
      "the %d cells whose instance-only interval has width: median %.2f, "
      "maximum %.2f (%s), minimum %.2f (%s)."
      % (len(ratios), float(ratios.median()), float(ratios.max()),
         _cell_label(informative.loc[ratios.idxmax()]), float(ratios.min()),
         _cell_label(informative.loc[ratios.idxmin()])))
    A("")
    if not degenerate.empty:
        A("The %d remaining cell(s) (%s) are excluded from those two numbers. "
          "The pools reproduce EDD there, so both intervals are round-off "
          "around zero, at most %.1e weighted units wide against an "
          "equivalence margin of at least %.1f, and their ratio measures "
          "floating-point noise. Their raw ratios stay in the CSV."
          % (len(degenerate),
             "; ".join(_cell_label(r) for _, r in degenerate.iterrows()),
             float(degenerate["width_inst"].max()), stats.MARGIN_ABS))
        A("")
    emp = informative[informative["scope_type"].isin(EMP_SCOPE_TYPES)]
    gen = informative[informative["scope_type"].isin(GEN_SCOPE_TYPES)]
    other = changed[~changed["scope_type"].isin(GEN_SCOPE_TYPES)]
    A("The seed level does not widen every scope by a common factor. On the "
      "empirical crew-multiplier scopes the ratio has median %.2f and maximum "
      "%.2f over %d cells; on the generator scopes it has median %.2f and "
      "maximum %.2f over %d cells. %d of the %d verdict changes are on the "
      "generator scopes and %d %s; all %d empirical crew-multiplier cells keep "
      "their verdict."
      % (float(emp["width_ratio_two_inst"].median()),
         float(emp["width_ratio_two_inst"].max()), len(emp),
         float(gen["width_ratio_two_inst"].median()),
         float(gen["width_ratio_two_inst"].max()), len(gen),
         int(changed["scope_type"].isin(GEN_SCOPE_TYPES).sum()), len(changed),
         len(other),
         ("elsewhere (%s)" % "; ".join(_cell_label(r) for _, r in
                                       other.iterrows())) if len(other)
         else "elsewhere",
         int((tab["scope_type"].isin(EMP_SCOPE_TYPES)
              & (tab["verdict_changed"] == 0)).sum())))
    A("")
    A("The seed-only interval is the seed level on its own, with the instances "
      "held fixed. Its width is a median %.2f of the instance-only width over "
      "the same %d cells."
      % (float((informative["width_seed"]
                / informative["width_inst"]).median()), len(ratios)))
    A("")

    A("## 4. Per-seed mean spread on the headline scope (%s, %s)"
      % HEADLINE_SCOPE)
    A("")
    A("Each pool's per-seed mean weighted tardiness over the %d configurations "
      "of the scope, and the reference mean beside it."
      % int(head["n_configs"].max()))
    A("")
    A(_md_table(head[["family", "n_seeds", "mean_ref", "seed_min_mean",
                      "seed_max_mean", "seed_sd", "mean_diff"]],
                ["family", "n_seeds", "mean_ref", "seed_min_mean",
                 "seed_max_mean", "seed_sd", "mean_diff"]))
    A("The spread between the best and the worst seed of a pool is what the "
      "seed level resamples. On this scope it is %.3f weighted units for "
      "mlp_pool, %.3f for attn_pool and %.3f for v1_pool, against paired "
      "differences against EDD of %.3f, %.3f and %.3f."
      % tuple([float(head.loc[head["family"] == f, "seed_max_mean"].iloc[0]
                     - head.loc[head["family"] == f, "seed_min_mean"].iloc[0])
               for f in ("mlp_pool", "attn_pool", "v1_pool")]
              + [float(head.loc[head["family"] == f, "mean_diff"].iloc[0])
                 for f in ("mlp_pool", "attn_pool", "v1_pool")]))
    A("")

    A("## 5. What this method cannot do")
    A("")
    A("The seed level is resampled from a small set: 10 training seeds for "
      "mlp_pool and attn_pool, 3 for v1_pool. A bootstrap over 10 values is "
      "coarse, and over 3 it is barely more than a range; the percentile "
      "interval of such a small sample is unstable and its coverage is not the "
      "nominal 95%. A bootstrap also resamples only the seeds that exist, so "
      "it cannot represent training outcomes the trained set never produced.")
    A("")
    A("The two-level interval should therefore be interpreted cautiously and "
      "may not capture the full training-seed uncertainty. It shows that the "
      "released intervals understate total uncertainty and by roughly how "
      "much; it does not certify the size of the understatement. Removing "
      "that limit needs more training seeds, not a different estimator.")
    A("")

    A("## Every cell")
    A("")
    A(_md_table(tab, REPORT_COLS))

    path.write_text("\n".join(L))
    return path


# --------------------------------------------------------------------------- #
# Macros (paper/macros_r4i.tex, prefix \sbo)
# --------------------------------------------------------------------------- #
class SeedBootMacroFile(MacroFile):
    """A macro collection whose names carry the seed-bootstrap prefix.

    Values pass through :func:`house_number` on the way in, so the number style
    is a property of the file rather than of each call site.
    """

    PREFIX = "sbo"

    def add(self, name, value, source):
        if not name.startswith(self.PREFIX):
            raise SystemExit("macro %r does not use the \\%s prefix"
                             % (name, self.PREFIX))
        if not name.isalpha():
            raise SystemExit("macro %r must be letters only (LaTeX)" % name)
        if name in self.existing:
            raise SystemExit("macro %r already exists in a companion macro file"
                             % name)
        if name in self.names:
            raise SystemExit("macro %r defined twice in this run" % name)
        v = house_number(value)
        if v.strip() == "" or "nan" in v.lower() or "inf" in v.lower():
            raise SystemExit("macro %r has a non-finite value %r" % (name, v))
        self.names.add(name)
        self.items.append((name, v, source))


def f_ratio2(x) -> str:
    """A width ratio, two decimals: the interesting range here is near one."""
    return "%.2f" % float(x)


def _cell(tab: pd.DataFrame, scope_type: str, scope: str, family: str):
    """The single row of one (scope, pool) cell, or None when it was not run."""
    sub = tab[(tab["scope_type"] == scope_type) & (tab["scope"] == scope)
              & (tab["family"] == family)]
    return sub.iloc[0] if len(sub) else None


def build_macros(tab: pd.DataFrame, paper_dir: Path, n_boot: int) -> tuple:
    """Write paper/macros_r4i.tex from the table this run produced."""
    target = paper_dir / MACRO_FILE
    existing = set()
    for p in sorted(paper_dir.glob("macros*.tex")):
        if p != target:
            existing |= existing_macro_names(p)
    mf = SeedBootMacroFile(existing)

    src = "results/r4_final/analysis/seed_bootstrap.csv"
    informative, _degenerate = split_by_width(tab)
    ratios = informative["width_ratio_two_inst"]

    mf.section("Scope of the two-level bootstrap (%s)" % src)
    mf.add("sboCells", f_int(len(tab)),
           src + " rows (scope x pool cells with all three intervals)")
    mf.add("sboScopes", f_int(tab.groupby(["scope_type", "scope"]).ngroups),
           src + " fields=scope_type,scope (distinct scopes carried)")
    mf.add("sboBoot", f_int(n_boot),
           "scripts/r4_seedboot.py --n-boot (resamples per interval)")
    mf.add("sboVerdictChanges", f_int(int(tab["verdict_changed"].sum())),
           src + " field=verdict_changed (cells whose equivalence verdict "
                 "differs between the instance-only and two-level intervals)")
    mf.add("sboRatioCells", f_int(len(ratios)),
           src + " field=width_inst (cells whose instance-only interval has "
                 "width; the rest reproduce EDD exactly and both their "
                 "intervals are round-off around zero)")
    mf.add("sboRatioMedian", f_ratio2(ratios.median()),
           src + " field=width_ratio_two_inst (median over those cells)")
    mf.add("sboRatioMax", f_ratio2(ratios.max()),
           src + " field=width_ratio_two_inst (maximum over those cells)")

    head = tab[(tab["scope_type"] == HEADLINE_SCOPE[0])
               & (tab["scope"] == HEADLINE_SCOPE[1])]
    mf.section("Headline empirical scope (%s scope_type=%s scope=%s): the "
               "three intervals per pool" % ((src,) + HEADLINE_SCOPE))
    mf.add("sboHeadConfigs", f_int(head["n_configs"].max()),
           src + " field=n_configs (configurations behind every pool row on "
                 "this scope)")
    for pool in POOL_KEYS:
        name = FAMILY_NAME[pool]
        r = head[head["family"] == name]
        if r.empty:
            continue
        r = r.iloc[0]
        pref = "sbo" + POOL_TOKEN[pool]
        psrc = (src + " scope_type=%s scope=%s family=%s"
                % (HEADLINE_SCOPE + (name,)))
        mf.add(pref + "Seeds", f_int(r["n_seeds"]),
               psrc + " field=n_seeds (training seeds in the pool)")
        mf.add(pref + "Diff", f_diff(r["mean_diff"]),
               psrc + " field=mean_diff (paired difference against EDD)")
        mf.add(pref + "InstCiLo", f_diff(r["ci_lo_inst"]),
               psrc + " field=ci_lo_inst (instance-only interval)")
        mf.add(pref + "InstCiHi", f_diff(r["ci_hi_inst"]),
               psrc + " field=ci_hi_inst (instance-only interval)")
        mf.add(pref + "InstVerdict", f_text(r["verdict_inst"]),
               psrc + " field=verdict_inst")
        mf.add(pref + "SeedCiLo", f_diff(r["ci_lo_seed"]),
               psrc + " field=ci_lo_seed (seed-only interval)")
        mf.add(pref + "SeedCiHi", f_diff(r["ci_hi_seed"]),
               psrc + " field=ci_hi_seed (seed-only interval)")
        mf.add(pref + "SeedVerdict", f_text(r["verdict_seed"]),
               psrc + " field=verdict_seed")
        mf.add(pref + "TwoCiLo", f_diff(r["ci_lo_two"]),
               psrc + " field=ci_lo_two (two-level interval)")
        mf.add(pref + "TwoCiHi", f_diff(r["ci_hi_two"]),
               psrc + " field=ci_hi_two (two-level interval)")
        mf.add(pref + "TwoVerdict", f_text(r["verdict_two"]),
               psrc + " field=verdict_two")
        mf.add(pref + "WidthInst", f_diff(r["width_inst"]),
               psrc + " field=width_inst (ci_hi_inst minus ci_lo_inst)")
        mf.add(pref + "WidthTwo", f_diff(r["width_two"]),
               psrc + " field=width_two (ci_hi_two minus ci_lo_two)")
        mf.add(pref + "WidthRatio", f_ratio2(r["width_ratio_two_inst"]),
               psrc + " field=width_ratio_two_inst (two-level width over "
                      "instance-only width)")
        mf.add(pref + "SeedSd", f_diff(r["seed_sd"]),
               psrc + " field=seed_sd (standard deviation of the per-seed "
                      "means on this scope)")
        mf.add(pref + "SeedMinMean", f_twt(r["seed_min_mean"]),
               psrc + " field=seed_min_mean (best seed's mean weighted "
                      "tardiness on this scope)")
        mf.add(pref + "SeedMaxMean", f_twt(r["seed_max_mean"]),
               psrc + " field=seed_max_mean (worst seed's mean weighted "
                      "tardiness on this scope)")
        mf.add(pref + "SeedSpread", f_diff(float(r["seed_max_mean"])
                                           - float(r["seed_min_mean"])),
               psrc + " fields=seed_max_mean-seed_min_mean (worst seed's mean "
                      "minus best seed's mean, weighted units)")
        mf.add(pref + "SeedSpreadPct",
               f_pct(100.0 * (float(r["seed_max_mean"])
                              / float(r["seed_min_mean"]) - 1.0)),
               psrc + " fields=seed_max_mean/seed_min_mean (worst seed's mean "
                      "over best seed's mean, per cent)")

    # ---- the empirical scopes against the generator scopes --------------- #
    # The seed level separates the two regimes rather than widening everything
    # by a common factor, and every verdict change sits on the generator side.
    mf.section("Empirical crew-multiplier scopes against generator scopes: how "
               "much the seed level widens each (%s scope_type=emp_m against "
               "scope_type=gen_all and gen_utarget)" % src)
    emp_all = tab[tab["scope_type"].isin(EMP_SCOPE_TYPES)]
    gen_all_cells = tab[tab["scope_type"].isin(GEN_SCOPE_TYPES)]
    emp = informative[informative["scope_type"].isin(EMP_SCOPE_TYPES)]
    gen = informative[informative["scope_type"].isin(GEN_SCOPE_TYPES)]
    mf.add("sboEmpCells", f_int(len(emp_all)),
           src + " scope_type=emp_m (cells on the empirical crew-multiplier "
                 "scopes: three crew multipliers times three pools)")
    mf.add("sboEmpUnchanged", f_int(int((emp_all["verdict_changed"] == 0).sum())),
           src + " scope_type=emp_m field=verdict_changed (empirical cells "
                 "whose verdict is the same under both intervals)")
    mf.add("sboEmpRatioMedian", f_ratio2(emp["width_ratio_two_inst"].median()),
           src + " scope_type=emp_m field=width_ratio_two_inst (median)")
    mf.add("sboEmpRatioMax", f_ratio2(emp["width_ratio_two_inst"].max()),
           src + " scope_type=emp_m field=width_ratio_two_inst (maximum)")
    mf.add("sboGenCells", f_int(len(gen_all_cells)),
           src + " scope_type=gen_all,gen_utarget (cells on the generator "
                 "scopes: the pooled track and five target utilisations, times "
                 "three pools)")
    mf.add("sboGenRatioMedian", f_ratio2(gen["width_ratio_two_inst"].median()),
           src + " scope_type=gen_all,gen_utarget field=width_ratio_two_inst "
                 "(median)")
    mf.add("sboGenRatioMax", f_ratio2(gen["width_ratio_two_inst"].max()),
           src + " scope_type=gen_all,gen_utarget field=width_ratio_two_inst "
                 "(maximum)")

    # ---- what the changes are, and where they concentrate ---------------- #
    mf.section("The verdict changes broken down (%s field=verdict_changed)"
               % src)
    ch = tab[tab["verdict_changed"] == 1]
    # Most changes sit on the generator scopes, but not all of them, so the
    # count is emitted rather than left to be inferred from the total.
    mf.add("sboGenChanges",
           f_int(int(ch["scope_type"].isin(GEN_SCOPE_TYPES).sum())),
           src + " scope_type=gen_all,gen_utarget field=verdict_changed "
                 "(verdict changes on the generator scopes; the remainder are "
                 "on the stress campus)")
    for a, b, tok in (("worse", "inconclusive", "WorseInconc"),
                      ("equivalent", "inconclusive", "EquivInconc")):
        mf.add("sboChanges" + tok,
               f_int(int(((ch["verdict_inst"] == a)
                          & (ch["verdict_two"] == b)).sum())),
               src + " fields=verdict_inst,verdict_two (changes from %s to %s)"
               % (a, b))
    for pool in POOL_KEYS:
        name = FAMILY_NAME[pool]
        mf.add("sbo%sChanges" % POOL_TOKEN[pool],
               f_int(int((ch["family"] == name).sum())),
               src + " family=%s field=verdict_changed (cells of this pool "
                     "whose verdict changes; the pool's seed level is drawn "
                     "from %d seeds)" % (name, len(POOL_SEEDS[pool])))

    # ---- the generator scopes the prose quotes --------------------------- #
    mf.section("Generator track: the pools at the two highest target "
               "utilisations, and the pooled generator scope (%s "
               "scope_type=gen_utarget and gen_all)" % src)
    r = _cell(tab, "gen_all", "ALL", FAMILY_NAME["v2pool"])
    if r is not None:
        gsrc = src + " scope_type=gen_all scope=ALL family=mlp_pool"
        mf.add("sboMlpGenAllInstVerdict", f_text(r["verdict_inst"]),
               gsrc + " field=verdict_inst")
        mf.add("sboMlpGenAllTwoVerdict", f_text(r["verdict_two"]),
               gsrc + " field=verdict_two")
    for u in GEN_QUOTED:
        scope, tok = "u_target=%s" % u, U_TOKEN[u]
        r = _cell(tab, "gen_utarget", scope, FAMILY_NAME["v2pool"])
        if r is not None:
            gsrc = (src + " scope_type=gen_utarget scope=%s family=mlp_pool"
                    % scope)
            mf.add("sboMlp%sTwoCiLo" % tok, f_diff(r["ci_lo_two"]),
                   gsrc + " field=ci_lo_two")
            mf.add("sboMlp%sTwoCiHi" % tok, f_diff(r["ci_hi_two"]),
                   gsrc + " field=ci_hi_two")
            mf.add("sboMlp%sTwoVerdict" % tok, f_text(r["verdict_two"]),
                   gsrc + " field=verdict_two")
            mf.add("sboMlp%sInstVerdict" % tok, f_text(r["verdict_inst"]),
                   gsrc + " field=verdict_inst")
            mf.add("sboMlp%sWidthRatio" % tok,
                   f_ratio2(r["width_ratio_two_inst"]),
                   gsrc + " field=width_ratio_two_inst")
        r = _cell(tab, "gen_utarget", scope, FAMILY_NAME["v2attnpool"])
        if r is not None:
            asrc = (src + " scope_type=gen_utarget scope=%s family=attn_pool"
                    % scope)
            mf.add("sboAttn%sTwoVerdict" % tok, f_text(r["verdict_two"]),
                   asrc + " field=verdict_two")
            if u == GEN_QUOTED[-1]:
                mf.add("sboAttn%sTwoCiLo" % tok, f_diff(r["ci_lo_two"]),
                       asrc + " field=ci_lo_two")
                mf.add("sboAttn%sTwoCiHi" % tok, f_diff(r["ci_hi_two"]),
                       asrc + " field=ci_hi_two")

    header = "\n".join([
        "%% paper/%s -- two-level (instance and training seed) uncertainty"
        % MACRO_FILE,
        "% for the learned pools against EDD. Prefix sbo = seed bootstrap.",
        "% GENERATED FILE. Do not edit by hand: rebuild with",
        "%   PYTHONPATH=src python scripts/r4_seedboot.py",
        "%% Every value is transcribed by that script from %s" % src,
        "% produced in the same run; the trailing comment names the field.",
        "%% Generated %s from results/r4_final/results.csv."
        % datetime.now().strftime("%Y-%m-%d %H:%M"),
        "% The released pool intervals resample instances only, with the",
        "% training seeds held fixed. These macros carry the same point",
        "% estimates with the seed level added, so an interval here is never",
        "% a replacement for the released one: it is the same comparison",
        "% under a wider resampling scheme.",
        "% Sign convention: a negative paired difference means the pool is",
        "% better than EDD (weighted tardiness is minimised).",
        "% Companion files: macros_r4.tex, macros_r4b.tex .. macros_r4g.tex.",
        "% No name is shared with them; a collision is a hard error here.",
    ])
    paper_dir.mkdir(parents=True, exist_ok=True)
    target.write_text(mf.render(header))
    return len(mf.names), target


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Two-level (instance and training seed) uncertainty for "
                    "the learned pools against EDD.")
    ap.add_argument("--results", default=str(EVALB_CSV),
                    help="seed-level Eval-B results (default %s)" % EVALB_CSV)
    ap.add_argument("--out", default=str(OUT_DIR),
                    help="output directory (default %s)" % OUT_DIR)
    ap.add_argument("--paper", default=str(PAPER_DIR),
                    help="paper directory for the macro file (default %s)"
                         % PAPER_DIR)
    ap.add_argument("--n-boot", type=int, default=stats.N_BOOT,
                    help="bootstrap resamples per interval (default %d)"
                         % stats.N_BOOT)
    ap.add_argument("--seed", type=int, default=stats.SEED,
                    help="bootstrap master seed (default %d)" % stats.SEED)
    ap.add_argument("--no-macros", action="store_true",
                    help="write the CSV and report outputs only")
    args = ap.parse_args(argv)

    os.chdir(ROOT)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = datetime.now()

    print("Reading results ...", flush=True)
    df = load_results(Path(args.results))
    released = pd.read_csv(FAMILY_CSV)
    print("  %d seed-level rows, %d configurations"
          % (len(df), df["id"].nunique()), flush=True)

    print("Bootstrapping (%d resamples per interval, master seed %d) ..."
          % (args.n_boot, args.seed), flush=True)
    tab = build_table(df, released, args.n_boot, args.seed)
    if tab.empty:
        raise SystemExit("no (scope, pool) cell was built; check the results "
                         "file and the scope types")

    print("Reconciliation: %d cells, largest |mean_diff - released| %.3g"
          % (len(tab),
             float((tab["mean_diff"] - tab["released_mean_diff"]).abs().max())),
          flush=True)
    dev = tab["_released_stream_dev"]
    if bool(dev.notna().all()):
        print("Released intervals reproduced on the released stream: largest "
              "deviation %.3g" % float(dev.max()), flush=True)
    else:
        print("Released-interval check skipped (--n-boot %d is not the "
              "protocol %d)" % (args.n_boot, stats.N_BOOT), flush=True)
    print("Verdict changes under the two-level interval: %d of %d"
          % (int(tab["verdict_changed"].sum()), len(tab)), flush=True)

    p = out / "seed_bootstrap.csv"
    tab[CSV_COLUMNS].to_csv(p, index=False)
    print("Wrote %d row(s) -> %s" % (len(tab), p), flush=True)

    p = write_report(out / "seed_bootstrap_summary.md", tab, args.n_boot,
                     args.seed)
    print("Wrote %s" % p, flush=True)

    if not args.no_macros:
        n, p = build_macros(tab, Path(args.paper), args.n_boot)
        print("Wrote %d macro(s) -> %s" % (n, p), flush=True)

    print("done (%.1f s)" % (datetime.now() - t0).total_seconds(), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
