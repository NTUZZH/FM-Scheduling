#!/usr/bin/env python
"""Trade-level scarcity structure: does WHERE capacity is short explain which
rule family stays closest to the best, after controlling for overall load?

Why this analysis exists
------------------------
The manuscript reports that the due-date family (EDD) stays closest to the best
method when crews are scaled evenly across every trade, and that the weighted
urgency rules (WMDD, ATC) move nearest instead when scarcity concentrates in
particular trades.  That contrast is currently measured INDIRECTLY, by
experimental arm: the evenly scaled arms are the crew-multiplier configurations
(``fmwos.tightness.scale_crew``) and the concentrated arms are the
capacity-estimator configurations (``scripts/r4_capacity.py``, crew re-sized per
trade at a lower quantile of that trade's own weekly hours).  The manuscript's
load axis, realised utilisation, is portfolio level:

    u_realized = sum_j p_bh(j) / (n_technicians * window_bh)

so it cannot distinguish a portfolio whose shortage is spread evenly from one
whose shortage sits in two trades.  This script measures the trade-level
structure DIRECTLY, per instance-configuration, and tests whether it explains
the EDD-versus-weighted-rule gap once portfolio utilisation is held fixed.

No schedule is re-run: every outcome comes from the existing result rows, and
every scarcity metric comes from the instance files plus the transform each
configuration was built with.

What is computed
----------------
1. Reconciliation gate.  For EVERY scored configuration, the portfolio
   utilisation is recomputed from the instance file and the configuration's
   actual technician list, and checked against the ``u_realized`` column the
   runners wrote.  Everything downstream depends on sharing that convention, so
   a single mismatch aborts the run before any output is written.

2. Per-trade utilisation.  For a configuration with horizon H business hours,
   crew size m_g in trade g and workload W_g = sum of p_bh over that trade's
   work orders,

       u_g = W_g / (m_g * H)

   and from the u_g distribution four concentration metrics:
     overload_share    workload-weighted share of processing time sitting in
                       trades with u_g > 1  (the primary metric)
     max_u_trade       the largest u_g
     cv_u_weighted     coefficient of variation of u_g, weighted by W_g
     share_trades_over share of work-carrying trades with u_g > 1

3. Paired outcome differences per configuration,
       d_wmdd = wwt(EDD) - wwt(WMDD),   d_atc = wwt(EDD) - wwt(ATC),
   positive meaning the weighted rule is better, plus their relative versions.

4. Four analyses, all with the protocol's statistics (fmwos.stats: base-instance
   cluster bootstrap, 10000 resamples, master seed 12345, equivalence margin
   max(1.0, 1% of the reference mean)):
     (a) stratified: within each utilisation band, a median split on
         overload_share, with the high-minus-low contrast and its CI;
     (b) regression: d on utilisation and overload_share jointly, with
         cluster-bootstrap CIs on the coefficients;
     (c) arm validation: mean overload_share by experimental arm at matched
         utilisation, which is what tells us whether the arms really differ in
         trade-level structure or only in level;
     (d) a two-dimensional map (utilisation band x overload-share band) with a
         mechanically derived recommended rule family per cell.

Conventions and edge cases (all applied uniformly)
--------------------------------------------------
* Trades.  A trade enters the per-trade table when it has crew or workload in
  the configuration.  A trade with crew and no workload has u_g = 0: it carries
  zero weight in every workload-weighted metric, and it is excluded from the
  unweighted ``share_trades_over`` (which is taken over work-carrying trades),
  but its technicians DO sit in the portfolio denominator, exactly as the
  pipeline's u_realized counts them.  A trade with workload and no crew has no
  finite u_g; such a trade is counted as overloaded in ``overload_share`` and
  makes ``max_u_trade`` and ``cv_u_weighted`` undefined for that configuration.
  The count of affected configurations is reported (it is zero on this corpus).
* Zero outcomes.  Many slack configurations have wwt(EDD) = 0, where the
  relative difference is undefined.  Those configurations are kept in every
  absolute analysis and dropped from the relative ones, with the dropped count
  and their absolute mean difference reported, because dropping them is not
  neutral: with wwt(EDD) = 0 the difference can only be zero or negative.
* Clusters.  ``fmwos.stats.base_instance_id`` maps a configuration id back to
  its base instance, so the crew-multiplier and capacity-estimator variants of
  one week of work resample together.
* Methods.  The comparison set common to both result files is the seven
  dispatching rules plus the ten frozen v2 policy seeds; the per-cell "best
  method" is taken over that common set so a cell means the same thing whichever
  source its configurations came from.
* Regimes.  The empirical and generator tracks are different objects at the same
  utilisation, so every pooled analysis is repeated on the replay-derived
  configurations alone (``scope = replay_only``) and both are reported.

Inputs
------
  data/processed/instances_r4/index_r4.csv and the instance JSON it points at
  results/r4_final/results.csv                     (Eval-B)
  results/r4_robustness/capacity/results.csv       (capacity-estimator arms)
  results/r4_robustness/capacity/calib/capacity_q*.csv  (the arm crew tables)

Outputs
-------
  results/r4_final/analysis/scarcity.csv          per-configuration metrics,
                                                  paired differences and source
  results/r4_final/analysis/scarcity_grid.csv     the two-dimensional map
  results/r4_final/analysis/scarcity_analysis.md  the readable report
  results/r4_final/analysis/scarcity_meta.json    inputs, constants, counts
  paper/macros_r4g.tex                            the \\tsc... macros

Usage
-----
    PYTHONPATH=src python scripts/r4_scarcity.py [--out DIR] [--paper DIR]
                                                 [--n-boot N] [--no-macros]

Re-running is idempotent: the bootstrap is seeded from the protocol master seed
and every output is rewritten from the same inputs, so a second run reproduces
every digit.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# The only numerical work here is small dense linear algebra and bincounts; keep
# the shared box's BLAS from oversubscribing it.
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "4")

import numpy as np                                          # noqa: E402
import pandas as pd                                         # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from fmwos import stats, tightness                          # noqa: E402
from fmwos.io import normalize_method_column                # noqa: E402
import r4_capacity as rcap                                  # noqa: E402

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
INDEX_CSV = Path("data/processed/instances_r4/index_r4.csv")
INST_ROOT = Path("data/processed/instances_r4")
EVALB_CSV = Path("results/r4_final/results.csv")
CAP_CSV = Path("results/r4_robustness/capacity/results.csv")
CAP_CALIB = Path("results/r4_robustness/capacity/calib")
OUT_DIR = Path("results/r4_final/analysis")
PAPER_DIR = Path("paper")
MACRO_FILE = "macros_r4g.tex"

RULES = ("edd", "pfifo", "wspt", "atc", "wmdd", "lpt", "random")
POLICY_SEEDS = tuple(range(301, 311))
COMMON_METHODS = tuple(RULES) + tuple("v2rl%d" % s for s in POLICY_SEEDS)

# u_realized is written full precision by the Eval-B runner and rounded to six
# decimals by the robustness runner (scripts/r4_robust_common.py u_realized), so
# the gate tolerance differs by source and is stated rather than assumed.
TOL_EVALB = 1e-9
TOL_CAP = 1e-6
GATE_MIN_CONFIGS = 200

# Overload-share bands for the map. Fixed cuts, not terciles, so a cell means
# the same thing in every scope and in any later re-run on a different corpus.
OV_EDGES = (0.25, 0.50, 0.75)
OV_LABELS = ("<0.25", "0.25-0.5", "0.5-0.75", ">=0.75")
MIN_CLUSTERS_GRID = 8

U_LABELS = stats.U_BIN_LABELS
BIN_TOKEN = {"<0.5": "Slack", "0.5-0.8": "Moderate", "0.8-1.0": "Tight",
             "1.0-1.2": "Over", ">=1.2": "Deep"}
ARM_TOKEN = {"m1.0": "Mfull", "m0.8": "Meighty", "m0.6": "Msixty",
             "gen": "Gen", "q90": "Qninety", "q75": "Qseventyfive"}
# Three scopes, because pooling can manufacture or hide an effect here. The
# empirical and generator tracks are different objects at the same utilisation
# (the analysis convention of scripts/r4_analysis.py), and campus 2 is the
# chronic-overload portfolio the manuscript keeps out of every verdict scope, so
# both are separated out rather than only pooled.
SCOPES = ("all", "replay_only", "no_campus2")
STRESS_CAMPUS = 2


def scope_frame(df: pd.DataFrame, scope: str) -> pd.DataFrame:
    if scope == "all":
        return df
    if scope == "replay_only":
        return df[df["track"] == "replay"]
    if scope == "no_campus2":
        return df[df["campus"] != STRESS_CAMPUS]
    raise ValueError("unknown scope %r" % scope)


def ov_band(v) -> str:
    """Band an overload share onto the four fixed labels (left-closed)."""
    x = float(v)
    for edge, label in zip(OV_EDGES, OV_LABELS):
        if x < edge:
            return label
    return OV_LABELS[-1]


# --------------------------------------------------------------------------- #
# Instance loading and configuration reconstruction
# --------------------------------------------------------------------------- #
class InstanceStore:
    """Base instances, read once and cached, plus the two transforms."""

    def __init__(self, index_csv: Path, inst_root: Path):
        idx = pd.read_csv(index_csv)
        self.paths = {str(r["id"]): inst_root / str(r["path"])
                      for _, r in idx.iterrows()}
        self._cache = {}

    def base(self, base_id: str) -> dict:
        inst = self._cache.get(base_id)
        if inst is None:
            with open(self.paths[base_id]) as f:
                inst = json.load(f)
            self._cache[base_id] = inst
        return inst

    def evalb_config(self, base_id: str, regime: str, m: float) -> dict:
        """The instance an Eval-B configuration was scored on.

        Empirical configurations at m != 1.0 are the crew-scaled copies
        ``fmwos.tightness.scale_crew`` builds; generator cells are scored as
        built, because their contention is the drawn utilisation target.
        """
        inst = self.base(base_id)
        if regime == "final-empirical" and float(m) != 1.0:
            return tightness.scale_crew(inst, float(m))
        return inst

    def capacity_config(self, base_id: str, campus: int, q: float,
                        crew_tables: dict):
        """The instance a capacity-estimator configuration was scored on.

        Rebuilt through ``scripts/r4_capacity.rebuild_technicians``, the
        function the arm itself used, so the crews here are the crews scored.
        """
        crews = rcap.crew_map(crew_tables[float(q)], int(campus))
        suffix = "_q%02d" % int(round(float(q) * 100))
        return rcap.rebuild_technicians(self.base(base_id), crews, float(q),
                                        suffix)


def load_crew_tables(calib_dir: Path, qs=(0.75, 0.90)) -> dict:
    out = {}
    for q in qs:
        p = calib_dir / ("capacity_q%02d.csv" % int(round(q * 100)))
        if not p.exists():
            raise SystemExit(
                "capacity crew table not found: %s\n"
                "  Build it with scripts/r4_capacity.py (it caches the tables "
                "outside any smoke directory)." % p)
        out[float(q)] = pd.read_csv(p)
    return out


# --------------------------------------------------------------------------- #
# Scarcity metrics
# --------------------------------------------------------------------------- #
def trade_table(instance: dict):
    """Per-trade crew, workload and utilisation for one configuration.

    Returns ``(H, rows)`` with rows ``(trade, crew, workload_bh, u_g)``; a trade
    with workload and no crew has ``u_g = inf`` and a trade with crew and no
    workload has ``u_g = 0``.  A trade with neither is not part of the
    configuration and is dropped.
    """
    H = float(instance["meta"]["window_bh"])
    crew, work = {}, {}
    for t in instance["technicians"]:
        crew[t["trade"]] = crew.get(t["trade"], 0) + 1
    for w in instance["work_orders"]:
        work[w["trade"]] = work.get(w["trade"], 0.0) + float(w["p_bh"])
    rows = []
    for g in sorted(set(crew) | set(work)):
        m_g, w_g = crew.get(g, 0), work.get(g, 0.0)
        if m_g == 0 and w_g == 0.0:
            continue
        u_g = (w_g / (m_g * H)) if (m_g > 0 and H > 0) else float("inf")
        rows.append((g, m_g, w_g, u_g))
    return H, rows


def even_withdrawal_overload_share(base_instance: dict, instance: dict):
    """Overload share the same portfolio would have under EVEN withdrawal.

    Both transforms leave the work orders and the horizon untouched and change
    only the technician list, so the counterfactual is well defined: keep the
    base instance's per-trade crew shares and scale every trade by the exact
    (non-integer) factor that reaches the configuration's TOTAL crew.  Total
    crew, and therefore portfolio utilisation, is identical to the
    configuration's by construction, so the difference

        overload_excess = overload_share - overload_share_even

    is a concentration measure with the load level held exactly fixed.  It is
    zero by construction for an untransformed configuration.
    """
    H = float(instance["meta"]["window_bh"])
    base_crew = {}
    for t in base_instance["technicians"]:
        base_crew[t["trade"]] = base_crew.get(t["trade"], 0) + 1
    base_total = sum(base_crew.values())
    total = len(instance["technicians"])
    if base_total == 0 or total == 0 or H <= 0:
        return float("nan")
    factor = total / base_total
    work = {}
    for w in instance["work_orders"]:
        work[w["trade"]] = work.get(w["trade"], 0.0) + float(w["p_bh"])
    total_w = sum(work.values())
    if total_w <= 0:
        return 0.0
    over = 0.0
    for g, w_g in work.items():
        m_g = base_crew.get(g, 0) * factor
        u_g = (w_g / (m_g * H)) if m_g > 0 else float("inf")
        if u_g > 1.0:
            over += w_g
    return over / total_w


def scarcity_metrics(instance: dict) -> dict:
    """Portfolio utilisation and the four trade-level concentration metrics."""
    H, rows = trade_table(instance)
    n_tech = len(instance["technicians"])
    total_p = sum(float(w["p_bh"]) for w in instance["work_orders"])
    u_port = (total_p / (n_tech * H)) if (n_tech > 0 and H > 0) else float("nan")

    total_w = sum(r[2] for r in rows)
    no_crew = [r for r in rows if r[1] == 0 and r[2] > 0.0]
    active = [r for r in rows if r[2] > 0.0]

    if total_w > 0:
        overload_share = sum(r[2] for r in rows if r[3] > 1.0) / total_w
    else:
        overload_share = 0.0

    if no_crew:
        # No finite u_g exists for part of the workload, so the two metrics that
        # need one are undefined for this configuration.
        max_u = float("nan")
        cv_u = float("nan")
    else:
        max_u = max((r[3] for r in rows), default=0.0)
        if total_w > 0:
            mean_w = sum(r[2] * r[3] for r in rows) / total_w
            var_w = sum(r[2] * (r[3] - mean_w) ** 2 for r in rows) / total_w
            cv_u = (var_w ** 0.5 / mean_w) if mean_w > 0 else 0.0
        else:
            cv_u = 0.0

    share_over = (sum(1 for r in active if r[3] > 1.0) / len(active)
                  if active else 0.0)

    return {
        "window_bh": H,
        "n_technicians": n_tech,
        "n_trades": len(rows),
        "n_trades_active": len(active),
        "n_trades_no_crew": len(no_crew),
        "total_p_bh": total_p,
        "u_recomputed": u_port,
        "overload_share": overload_share,
        "max_u_trade": max_u,
        "cv_u_weighted": cv_u,
        "share_trades_over": share_over,
    }


# --------------------------------------------------------------------------- #
# Configuration inventory (one row per scored configuration)
# --------------------------------------------------------------------------- #
def evalb_configs(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["id", "campus", "track", "size", "regime", "crew_multiplier",
            "u_realized"]
    cfg = df[cols].drop_duplicates("id").reset_index(drop=True)
    cfg["source"] = "evalb"
    cfg["crew_q"] = 0.95           # Eval-B is the q = 0.95 capacity estimator
    cfg["arm"] = np.where(cfg["regime"] == "final-gen", "gen",
                          ["m%.1f" % m for m in cfg["crew_multiplier"]])
    return cfg


def capacity_configs(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["id", "base_instance_id", "campus", "size", "crew_q", "u_realized"]
    cfg = df[cols].drop_duplicates("id").reset_index(drop=True)
    cfg["source"] = ["cap_q%02d" % int(round(q * 100)) for q in cfg["crew_q"]]
    cfg["arm"] = ["q%d" % int(round(q * 100)) for q in cfg["crew_q"]]
    cfg["track"] = "replay"
    cfg["regime"] = "cap-empirical"
    cfg["crew_multiplier"] = 1.0
    return cfg.drop(columns=["base_instance_id"])


def build_config_table(store, evalb, cap, crew_tables) -> pd.DataFrame:
    """One row per configuration with its scarcity metrics."""
    rows = []
    for _, r in evalb.iterrows():
        base = stats.base_instance_id(r["id"])
        inst = store.evalb_config(base, str(r["regime"]),
                                  float(r["crew_multiplier"]))
        rec = scarcity_metrics(inst)
        # The generator cells are scored as built, so there is no withdrawal to
        # compare against and the counterfactual is left undefined for them.
        if str(r["regime"]) == "final-gen":
            rec["overload_share_even"] = float("nan")
        else:
            rec["overload_share_even"] = even_withdrawal_overload_share(
                store.base(base), inst)
        rec.update({"id": str(r["id"]), "cluster": base,
                    "source": "evalb", "arm": str(r["arm"]),
                    "campus": int(r["campus"]), "track": str(r["track"]),
                    "size": int(r["size"]), "regime": str(r["regime"]),
                    "crew_multiplier": float(r["crew_multiplier"]),
                    "crew_q": 0.95,
                    "u_realized": float(r["u_realized"]),
                    "n_fallback_trades": 0})
        rows.append(rec)
    for _, r in cap.iterrows():
        base = stats.base_instance_id(r["id"])
        inst, n_fb = store.capacity_config(base, int(r["campus"]),
                                           float(r["crew_q"]), crew_tables)
        rec = scarcity_metrics(inst)
        rec["overload_share_even"] = even_withdrawal_overload_share(
            store.base(base), inst)
        rec.update({"id": str(r["id"]), "cluster": base,
                    "source": str(r["source"]), "arm": str(r["arm"]),
                    "campus": int(r["campus"]), "track": "replay",
                    "size": int(r["size"]), "regime": "cap-empirical",
                    "crew_multiplier": 1.0, "crew_q": float(r["crew_q"]),
                    "u_realized": float(r["u_realized"]),
                    "n_fallback_trades": int(n_fb)})
        rows.append(rec)
    out = pd.DataFrame(rows)
    out["u_bin"] = out["u_realized"].map(stats.utilization_bin)
    out["ov_band"] = out["overload_share"].map(ov_band)
    out["overload_excess"] = out["overload_share"] - out["overload_share_even"]
    return out


# --------------------------------------------------------------------------- #
# Reconciliation gate
# --------------------------------------------------------------------------- #
def reconciliation_gate(cfgs: pd.DataFrame) -> dict:
    """Recomputed portfolio utilisation vs the runners' ``u_realized``.

    Aborts the run on any mismatch: every downstream metric shares this
    denominator convention, so a discrepancy here would make the whole analysis
    incomparable with the manuscript's utilisation axis.
    """
    tol = np.where(cfgs["source"] == "evalb", TOL_EVALB, TOL_CAP)
    err = (cfgs["u_recomputed"] - cfgs["u_realized"]).abs().to_numpy(dtype=float)
    bad = cfgs[err > tol]
    span = (cfgs.groupby(["source", "arm", "track"])
            .agg(n_configs=("id", "size"),
                 n_sizes=("size", "nunique"),
                 n_campuses=("campus", "nunique"),
                 n_crew_multipliers=("crew_multiplier", "nunique"))
            .reset_index())
    return {
        "n_configs_checked": int(len(cfgs)),
        "n_mismatches": int(len(bad)),
        "max_abs_error": float(err.max()) if len(err) else 0.0,
        "tolerance_evalb": TOL_EVALB,
        "tolerance_capacity": TOL_CAP,
        "formula": "sum p_bh / (n_technicians * window_bh) on the transformed "
                   "instance",
        "span": span,
        "examples": bad.head(5)[["id", "source", "u_realized",
                                 "u_recomputed"]].to_dict("records"),
    }


# --------------------------------------------------------------------------- #
# Outcomes
# --------------------------------------------------------------------------- #
def outcome_table(evalb_rows: pd.DataFrame, cap_rows: pd.DataFrame,
                  ) -> pd.DataFrame:
    """Per configuration: EDD/WMDD/ATC weighted tardiness and the best method.

    Only feasible rows and only the method set common to both result files, so
    "best" is comparable across sources.
    """
    frames = []
    for df in (evalb_rows, cap_rows):
        sub = df[df["feasible"] == 1]
        sub = sub[sub["method"].isin(COMMON_METHODS)]
        frames.append(sub[["id", "method", "wwt"]])
    long = pd.concat(frames, ignore_index=True)
    wide = long.pivot(index="id", columns="method", values="wwt")
    missing = [m for m in COMMON_METHODS if m not in wide.columns]
    if missing:
        raise SystemExit("methods missing from the result files: %s" % missing)
    if wide[list(COMMON_METHODS)].isna().any().any():
        n = int(wide[list(COMMON_METHODS)].isna().any(axis=1).sum())
        raise SystemExit("%d configuration(s) lack a feasible row for one of "
                         "the common methods; the paired design needs them all"
                         % n)
    vals = wide[list(COMMON_METHODS)].astype(float)
    out = pd.DataFrame({
        "id": wide.index.astype(str),
        "wwt_edd": vals["edd"].to_numpy(dtype=float),
        "wwt_wmdd": vals["wmdd"].to_numpy(dtype=float),
        "wwt_atc": vals["atc"].to_numpy(dtype=float),
        # Per-configuration minimum over the common method set, and the method
        # that attains it. This is an oracle quantity, reported for description
        # only; the per-cell verdicts below pair EDD against the single method
        # with the lowest MEAN in the cell, never against this minimum.
        "wwt_min_common": vals.min(axis=1).to_numpy(dtype=float),
        "argmin_method": vals.idxmin(axis=1).to_numpy(),
    })
    out["d_wmdd"] = out["wwt_edd"] - out["wwt_wmdd"]
    out["d_atc"] = out["wwt_edd"] - out["wwt_atc"]
    nz = out["wwt_edd"] > 0
    out["rel_d_wmdd"] = np.where(nz, out["d_wmdd"] / out["wwt_edd"].where(nz, 1.0),
                                 np.nan)
    out["rel_d_atc"] = np.where(nz, out["d_atc"] / out["wwt_edd"].where(nz, 1.0),
                                np.nan)
    return out.reset_index(drop=True), vals


# --------------------------------------------------------------------------- #
# Cluster-bootstrap helpers (all seeded from the protocol master seed)
# --------------------------------------------------------------------------- #
def _frame(rows, columns) -> pd.DataFrame:
    """DataFrame with a fixed column order, checked against the rows.

    ``pd.DataFrame(rows, columns=...)`` silently fills a column no row supplies,
    which would turn a typo into a column of blanks in a published CSV.
    """
    if rows:
        keys = set().union(*(set(r) for r in rows))
        missing = [c for c in columns if c not in keys]
        extra = sorted(keys - set(columns))
        if missing or extra:
            raise SystemExit("column mismatch: missing %s, unexpected %s"
                             % (missing, extra))
    return pd.DataFrame(rows, columns=list(columns))


def _cluster_index(clusters):
    _uniq, idx = np.unique(np.asarray(clusters, dtype=object),
                           return_inverse=True)
    return idx, int(idx.max()) + 1 if len(idx) else 0


def _weights(rng, n_clusters, n_boot):
    """Yield (rows, weight matrix) chunks of cluster multiplicities."""
    chunk = max(1, min(int(n_boot), 4_000_000 // max(1, n_clusters)))
    done = 0
    while done < n_boot:
        rows = min(chunk, int(n_boot) - done)
        draw = rng.integers(0, n_clusters, size=(rows, n_clusters))
        flat = draw + (np.arange(rows)[:, None] * n_clusters)
        w = np.bincount(flat.ravel(), minlength=rows * n_clusters
                        ).reshape(rows, n_clusters).astype(float)
        yield rows, w
        done += rows


def mean_ci(values, clusters, label, n_boot, alpha=stats.ALPHA):
    """Mean and cluster-bootstrap CI, delegated to fmwos.stats."""
    v = np.asarray(values, dtype=float)
    if v.size == 0:
        return float("nan"), float("nan"), float("nan")
    lo, hi = stats.cluster_bootstrap_ci(
        v, np.asarray(clusters, dtype=object), n_boot=n_boot, alpha=alpha,
        seed=stats._derived_seed(stats.SEED, label))
    return float(v.mean()), lo, hi


def contrast_ci(values, clusters, mask_hi, label, n_boot, alpha=stats.ALPHA):
    """Difference of two subgroup means with a cluster bootstrap.

    Clusters are resampled once and both subgroup means are recomputed inside
    the same resample, so the interval accounts for the correlation between the
    two halves induced by a base instance contributing to both.
    """
    v = np.asarray(values, dtype=float)
    hi_m = np.asarray(mask_hi, dtype=bool)
    idx, K = _cluster_index(clusters)
    if v.size == 0 or K == 0 or hi_m.sum() == 0 or (~hi_m).sum() == 0:
        return float("nan"), float("nan"), float("nan")
    s_hi = np.bincount(idx[hi_m], weights=v[hi_m], minlength=K)
    c_hi = np.bincount(idx[hi_m], minlength=K).astype(float)
    s_lo = np.bincount(idx[~hi_m], weights=v[~hi_m], minlength=K)
    c_lo = np.bincount(idx[~hi_m], minlength=K).astype(float)
    point = float(v[hi_m].mean() - v[~hi_m].mean())
    if K == 1:
        return point, point, point
    rng = np.random.default_rng(stats._derived_seed(stats.SEED, label))
    draws = []
    for _rows, w in _weights(rng, K, n_boot):
        n_hi, n_lo = w @ c_hi, w @ c_lo
        with np.errstate(invalid="ignore", divide="ignore"):
            d = (w @ s_hi) / n_hi - (w @ s_lo) / n_lo
        draws.append(d)
    d = np.concatenate(draws)
    d = d[np.isfinite(d)]
    if d.size == 0:
        return point, float("nan"), float("nan")
    lo, hi = np.percentile(d, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return point, float(lo), float(hi)


def ols_cluster_ci(X, y, clusters, label, n_boot, alpha=stats.ALPHA):
    """OLS coefficients with a cluster-bootstrap percentile CI on each.

    A resample draws base instances with replacement and every row of a drawn
    cluster enters, a cluster drawn twice counting twice.  That is ordinary
    least squares on the concatenated resample, computed here through
    per-cluster Gram matrices so the 10000 resamples cost one small solve each.
    A resample that happens to drop a whole indicator column leaves that column
    rank deficient; the minimum-norm solution is used there, which leaves the
    remaining coefficients unchanged.
    """
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    idx, K = _cluster_index(clusters)
    p = X.shape[1]
    if X.shape[0] == 0 or K == 0:
        return np.full(p, np.nan), np.full(p, np.nan), np.full(p, np.nan)

    def solve(A, b):
        try:
            return np.linalg.solve(A, b)
        except np.linalg.LinAlgError:
            return np.linalg.pinv(A) @ b

    beta = solve(X.T @ X, X.T @ y)
    if K == 1:
        return beta, beta.copy(), beta.copy()

    # Per-cluster Gram matrices and moment vectors.
    G = np.zeros((K, p, p))
    h = np.zeros((K, p))
    for k in range(K):
        sel = idx == k
        Xk = X[sel]
        G[k] = Xk.T @ Xk
        h[k] = Xk.T @ y[sel]

    rng = np.random.default_rng(stats._derived_seed(stats.SEED, label))
    draws = np.empty((int(n_boot), p))
    pos = 0
    for rows, w in _weights(rng, K, n_boot):
        A = np.tensordot(w, G, axes=(1, 0))          # (rows, p, p)
        b = w @ h                                    # (rows, p)
        for i in range(rows):
            draws[pos + i] = solve(A[i], b[i])
        pos += rows
    lo = np.percentile(draws, 100 * alpha / 2, axis=0)
    hi = np.percentile(draws, 100 * (1 - alpha / 2), axis=0)
    return beta, lo, hi


# --------------------------------------------------------------------------- #
# (a) Stratified: median split on overload_share inside each utilisation band
# --------------------------------------------------------------------------- #
STRAT_COLUMNS = ["scope", "u_bin", "half", "n_configs", "n_clusters",
                 "median_split", "mean_u", "mean_overload_share",
                 "mean_d_wmdd", "d_wmdd_ci_lo", "d_wmdd_ci_hi",
                 "mean_d_atc", "d_atc_ci_lo", "d_atc_ci_hi",
                 "mean_wwt_edd", "mean_rel_d_wmdd", "mean_rel_d_atc"]
CONTRAST_COLUMNS = ["scope", "u_bin", "n_low", "n_high", "n_clusters",
                    "median_split", "mean_u_low", "mean_u_high",
                    "contrast_d_wmdd", "d_wmdd_ci_lo",
                    "d_wmdd_ci_hi", "contrast_d_atc", "d_atc_ci_lo",
                    "d_atc_ci_hi", "contrast_rel_d_wmdd", "rel_wmdd_ci_lo",
                    "rel_wmdd_ci_hi"]


def stratified(df: pd.DataFrame, n_boot: int):
    cells, contrasts = [], []
    for scope in SCOPES:
        sc = scope_frame(df, scope)
        for ub in U_LABELS:
            sub = sc[sc["u_bin"] == ub]
            if sub.empty:
                continue
            med = float(sub["overload_share"].median())
            hi_mask = (sub["overload_share"] > med).to_numpy()
            if hi_mask.all() or (~hi_mask).all():
                # A degenerate split (for example every configuration at
                # overload_share = 0) has no low/high contrast to report.
                hi_mask = np.zeros(len(sub), dtype=bool)
            for half, mask in (("low", ~hi_mask), ("high", hi_mask)):
                s = sub[mask]
                if s.empty:
                    continue
                cl = s["cluster"].to_numpy()
                row = {"scope": scope, "u_bin": ub, "half": half,
                       "n_configs": int(len(s)),
                       "n_clusters": int(s["cluster"].nunique()),
                       "median_split": med,
                       "mean_u": float(s["u_realized"].mean()),
                       "mean_overload_share": float(s["overload_share"].mean()),
                       "mean_wwt_edd": float(s["wwt_edd"].mean())}
                for col in ("d_wmdd", "d_atc"):
                    m, lo, hi = mean_ci(s[col], cl,
                                        "strat|%s|%s|%s|%s" % (scope, ub, half, col),
                                        n_boot)
                    row["mean_%s" % col] = m
                    row["%s_ci_lo" % col] = lo
                    row["%s_ci_hi" % col] = hi
                for col in ("rel_d_wmdd", "rel_d_atc"):
                    v = s[col].dropna()
                    row["mean_%s" % col] = float(v.mean()) if len(v) else float("nan")
                cells.append(row)
            if hi_mask.any() and (~hi_mask).any():
                cl = sub["cluster"].to_numpy()
                uu = sub["u_realized"].to_numpy(dtype=float)
                c = {"scope": scope, "u_bin": ub,
                     "n_low": int((~hi_mask).sum()), "n_high": int(hi_mask.sum()),
                     "n_clusters": int(sub["cluster"].nunique()),
                     "median_split": med,
                     # The bands are wide and the top one is open ended, so the
                     # two halves are only approximately matched on load; these
                     # two columns say by how much.
                     "mean_u_low": float(uu[~hi_mask].mean()),
                     "mean_u_high": float(uu[hi_mask].mean())}
                for col in ("d_wmdd", "d_atc"):
                    pt, lo, hi = contrast_ci(sub[col], cl, hi_mask,
                                             "contrast|%s|%s|%s" % (scope, ub, col),
                                             n_boot)
                    c["contrast_%s" % col] = pt
                    c["%s_ci_lo" % col] = lo
                    c["%s_ci_hi" % col] = hi
                c["contrast_rel_d_wmdd"] = float("nan")
                c["rel_wmdd_ci_lo"] = float("nan")
                c["rel_wmdd_ci_hi"] = float("nan")
                rel = sub.dropna(subset=["rel_d_wmdd"])
                if len(rel) and rel["overload_share"].nunique() > 1:
                    rm = (rel["overload_share"] > med).to_numpy()
                    if rm.any() and (~rm).any():
                        pt, lo, hi = contrast_ci(
                            rel["rel_d_wmdd"], rel["cluster"].to_numpy(), rm,
                            "contrastrel|%s|%s" % (scope, ub), n_boot)
                        c["contrast_rel_d_wmdd"] = pt
                        c["rel_wmdd_ci_lo"] = lo
                        c["rel_wmdd_ci_hi"] = hi
                contrasts.append(c)
    return _frame(cells, STRAT_COLUMNS), _frame(contrasts, CONTRAST_COLUMNS)


# --------------------------------------------------------------------------- #
# (b) Regression
# --------------------------------------------------------------------------- #
REG_COLUMNS = ["scope", "outcome", "spec", "term", "coef", "ci_lo", "ci_hi",
               "excludes_zero", "n_configs", "n_clusters", "r2"]


def _design(sub: pd.DataFrame, spec: str):
    """Design matrix and term names for one specification."""
    n = len(sub)
    ones = np.ones((n, 1))
    ov = sub["overload_share"].to_numpy(dtype=float)[:, None]
    if spec == "u_linear":
        u = sub["u_realized"].to_numpy(dtype=float)[:, None]
        return np.hstack([ones, u, ov]), ["intercept", "u_realized",
                                          "overload_share"]
    if spec == "u_quadratic":
        u = sub["u_realized"].to_numpy(dtype=float)[:, None]
        return (np.hstack([ones, u, u ** 2, ov]),
                ["intercept", "u_realized", "u_realized_sq", "overload_share"])
    if spec in ("u_bin_fe", "u_bin_fe_plus_u", "u_bin_fe_excess"):
        # Utilisation enters as band indicators, so the control on overall load
        # does not depend on the linear form being right.
        bins = [b for b in U_LABELS if (sub["u_bin"] == b).any()]
        cols = [ones]
        names = ["intercept"]
        for b in bins[1:]:
            cols.append((sub["u_bin"] == b).to_numpy(dtype=float)[:, None])
            names.append("u_bin[%s]" % b)
        if spec == "u_bin_fe_plus_u":
            # The bands are wide and the top one is open ended, so a band
            # indicator alone leaves load variation inside a band uncontrolled;
            # this spec adds the continuous term on top of the indicators.
            cols.append(sub["u_realized"].to_numpy(dtype=float)[:, None])
            names.append("u_realized")
        if spec == "u_bin_fe_excess":
            cols.append(sub["overload_excess"].to_numpy(dtype=float)[:, None])
            names.append("overload_excess")
        else:
            cols.append(ov)
            names.append("overload_share")
        return np.hstack(cols), names
    raise ValueError("unknown spec %r" % spec)


SPECS = ("u_linear", "u_quadratic", "u_bin_fe", "u_bin_fe_plus_u",
         "u_bin_fe_excess")


def regressions(df: pd.DataFrame, n_boot: int) -> pd.DataFrame:
    rows = []
    for scope in SCOPES:
        sc = scope_frame(df, scope)
        for outcome in ("d_wmdd", "d_atc", "rel_d_wmdd", "rel_d_atc"):
            for spec in SPECS:
                need = [outcome] + (["overload_excess"]
                                    if spec == "u_bin_fe_excess" else [])
                sub = sc.dropna(subset=need)
                if sub.empty:
                    continue
                y = sub[outcome].to_numpy(dtype=float)
                X, names = _design(sub, spec)
                label = "ols|%s|%s|%s" % (scope, outcome, spec)
                beta, lo, hi = ols_cluster_ci(X, y, sub["cluster"].to_numpy(),
                                              label, n_boot)
                resid = y - X @ beta
                ss_tot = float(((y - y.mean()) ** 2).sum())
                r2 = 1.0 - float((resid ** 2).sum()) / ss_tot if ss_tot > 0 else \
                    float("nan")
                for j, term in enumerate(names):
                    rows.append({
                        "scope": scope, "outcome": outcome, "spec": spec,
                        "term": term, "coef": float(beta[j]),
                        "ci_lo": float(lo[j]), "ci_hi": float(hi[j]),
                        "excludes_zero": int(lo[j] > 0 or hi[j] < 0),
                        "n_configs": int(len(sub)),
                        "n_clusters": int(sub["cluster"].nunique()),
                        "r2": r2})
    return _frame(rows, REG_COLUMNS)


# --------------------------------------------------------------------------- #
# (c) Arm validation
# --------------------------------------------------------------------------- #
ARM_COLUMNS = ["u_bin", "arm", "n_configs", "n_clusters", "mean_u",
               "mean_overload_share", "median_overload_share",
               "mean_overload_share_even", "mean_overload_excess",
               "mean_cv_u_weighted", "mean_max_u_trade",
               "mean_share_trades_over", "mean_d_wmdd", "mean_d_atc"]
ARM_CONTRAST_COLUMNS = ["u_bin", "n_uneven", "n_even", "n_clusters",
                        "mean_u_uneven", "mean_u_even",
                        "contrast_overload_share", "overload_share_ci_lo",
                        "overload_share_ci_hi", "contrast_cv_u_weighted",
                        "cv_ci_lo", "cv_ci_hi"]

# The arms the manuscript calls concentrated (per-trade capacity estimation)
# and evenly scaled (one multiplier on every trade).
UNEVEN_ARMS = ("q75", "q90")
EVEN_ARMS = ("m1.0", "m0.8", "m0.6")


def arm_validation(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for ub in ("ALL",) + tuple(U_LABELS):
        sub = df if ub == "ALL" else df[df["u_bin"] == ub]
        for arm in sorted(sub["arm"].unique()):
            s = sub[sub["arm"] == arm]
            if s.empty:
                continue
            rows.append({
                "u_bin": ub, "arm": arm, "n_configs": int(len(s)),
                "n_clusters": int(s["cluster"].nunique()),
                "mean_u": float(s["u_realized"].mean()),
                "mean_overload_share": float(s["overload_share"].mean()),
                "median_overload_share": float(s["overload_share"].median()),
                "mean_overload_share_even":
                    float(s["overload_share_even"].mean()),
                "mean_overload_excess": float(s["overload_excess"].mean()),
                "mean_cv_u_weighted": float(s["cv_u_weighted"].mean()),
                "mean_max_u_trade": float(s["max_u_trade"].mean()),
                "mean_share_trades_over": float(s["share_trades_over"].mean()),
                "mean_d_wmdd": float(s["d_wmdd"].mean()),
                "mean_d_atc": float(s["d_atc"].mean()),
            })
    return _frame(rows, ARM_COLUMNS)


def arm_contrasts(df: pd.DataFrame, n_boot: int) -> pd.DataFrame:
    """Concentration of the capacity arms minus that of the crew-multiplier
    arms, inside each utilisation band, with a cluster-bootstrap interval.

    This is the direct form of the manuscript's premise: if the two arms really
    differ in trade-level structure rather than only in load, the contrast is
    positive at matched utilisation.
    """
    rows = []
    keep = df[df["arm"].isin(UNEVEN_ARMS + EVEN_ARMS)]
    for ub in ("ALL",) + tuple(U_LABELS):
        sub = keep if ub == "ALL" else keep[keep["u_bin"] == ub]
        mask = sub["arm"].isin(UNEVEN_ARMS).to_numpy()
        if not mask.any() or not (~mask).any():
            continue
        cl = sub["cluster"].to_numpy()
        row = {"u_bin": ub, "n_uneven": int(mask.sum()),
               "n_even": int((~mask).sum()),
               "n_clusters": int(sub["cluster"].nunique()),
               "mean_u_uneven": float(sub["u_realized"].to_numpy()[mask].mean()),
               "mean_u_even": float(sub["u_realized"].to_numpy()[~mask].mean())}
        for col, tag in (("overload_share", "overload_share"),
                         ("cv_u_weighted", "cv")):
            pt, lo, hi = contrast_ci(sub[col], cl, mask,
                                     "armcontrast|%s|%s" % (ub, col), n_boot)
            row["contrast_%s" % col] = pt
            row["%s_ci_lo" % tag] = lo
            row["%s_ci_hi" % tag] = hi
        rows.append(row)
    return _frame(rows, ARM_CONTRAST_COLUMNS)


# --------------------------------------------------------------------------- #
# (d) The two-dimensional map
# --------------------------------------------------------------------------- #
GRID_COLUMNS = ["scope", "u_bin", "ov_band", "n_configs", "n_clusters",
                "mean_u", "mean_overload_share", "mean_wwt_edd",
                "mean_wwt_best", "best_method", "margin_edd",
                "mean_d_wmdd", "d_wmdd_ci_lo", "d_wmdd_ci_hi",
                "mean_d_atc", "d_atc_ci_lo", "d_atc_ci_hi",
                "verdict_wmdd_vs_edd", "verdict_atc_vs_edd",
                "mean_edd_minus_best", "edd_best_ci_lo", "edd_best_ci_hi",
                "verdict_edd_vs_best", "recommended_family"]


def recommend(v_wmdd, v_atc, v_best, n_clusters):
    """Mechanical family label for one cell.

    * ``insufficient``  fewer than the minimum number of base instances;
    * ``weighted``      a weighted rule beats EDD beyond the margin, or EDD is
                        worse than the cell's best method beyond it;
    * ``either``        EDD is equivalent to both weighted rules and to the best
                        method;
    * ``due-date``      otherwise, that is EDD is never shown to be behind
                        beyond the margin.
    """
    if n_clusters < MIN_CLUSTERS_GRID:
        return "insufficient"
    if v_wmdd == "better" or v_atc == "better" or v_best == "worse":
        return "weighted"
    if v_wmdd == "equivalent" and v_atc == "equivalent" and v_best == "equivalent":
        return "either"
    return "due-date"


def grid(df: pd.DataFrame, wide: pd.DataFrame, n_boot: int) -> pd.DataFrame:
    """Utilisation band x overload-share band, with a family label per cell.

    ``wide`` holds every common method's weighted tardiness per configuration,
    so the cell's best method is the one with the lowest mean inside the cell
    and EDD is paired against that single method.
    """
    rows = []
    for scope in SCOPES:
        sc = scope_frame(df, scope)
        for ub in U_LABELS:
            for ob in OV_LABELS:
                s = sc[(sc["u_bin"] == ub) & (sc["ov_band"] == ob)]
                if s.empty:
                    continue
                cl = s["cluster"].to_numpy()
                n_cl = int(s["cluster"].nunique())
                mean_edd = float(s["wwt_edd"].mean())
                row = {"scope": scope, "u_bin": ub, "ov_band": ob,
                       "n_configs": int(len(s)), "n_clusters": n_cl,
                       "mean_u": float(s["u_realized"].mean()),
                       "mean_overload_share": float(s["overload_share"].mean()),
                       "mean_wwt_edd": mean_edd,
                       "margin_edd": stats.equivalence_margin(mean_edd)}
                verdicts = {}
                # Sign convention of fmwos.stats: difference = method minus
                # reference on weighted tardiness, so "better" is negative.
                # d_wmdd is EDD minus WMDD, so the (WMDD - EDD) interval is the
                # negated, reversed one.
                for col, tag in (("d_wmdd", "wmdd"), ("d_atc", "atc")):
                    m, lo, hi = mean_ci(s[col], cl,
                                        "grid|%s|%s|%s|%s" % (scope, ub, ob, col),
                                        n_boot)
                    row["mean_%s" % col] = m
                    row["%s_ci_lo" % col] = lo
                    row["%s_ci_hi" % col] = hi
                    verdicts[tag] = stats.equivalence_verdict(-hi, -lo, mean_edd)
                cell = wide.loc[s["id"].to_numpy()]
                means = cell.mean(axis=0)
                best = str(sorted(means.items(),
                                  key=lambda kv: (float(kv[1]), str(kv[0])))[0][0])
                mean_best = float(means[best])
                d_eb = (s["wwt_edd"].to_numpy(dtype=float)
                        - cell[best].to_numpy(dtype=float))
                m, lo, hi = mean_ci(d_eb, cl,
                                    "grid|%s|%s|%s|eddbest" % (scope, ub, ob),
                                    n_boot)
                v_best = stats.equivalence_verdict(lo, hi, mean_best)
                row["mean_wwt_best"] = mean_best
                row["best_method"] = best
                row["mean_edd_minus_best"] = m
                row["edd_best_ci_lo"] = lo
                row["edd_best_ci_hi"] = hi
                row["verdict_wmdd_vs_edd"] = verdicts["wmdd"]
                row["verdict_atc_vs_edd"] = verdicts["atc"]
                row["verdict_edd_vs_best"] = v_best
                row["recommended_family"] = recommend(
                    verdicts["wmdd"], verdicts["atc"], v_best, n_cl)
                rows.append(row)
    return _frame(rows, GRID_COLUMNS)


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #
def write_report(path: Path, gate, cfg, strat, contrasts, reg, arms, armc, gr,
                 zero_note, corr, n_boot):
    L = []
    A = L.append
    A("# Trade-level scarcity structure")
    A("")
    A("Generated by scripts/r4_scarcity.py on %s."
      % datetime.now().isoformat(timespec="seconds"))
    A("Statistics: base-instance cluster bootstrap, %d resamples, master seed "
      "%d, equivalence margin max(%.1f, %.0f%% of the reference mean) "
      "(fmwos.stats)." % (n_boot, stats.SEED, stats.MARGIN_ABS,
                          100 * stats.MARGIN_REL))
    A("")
    A("## 1. Reconciliation gate")
    A("")
    A("Portfolio utilisation was recomputed for every scored configuration as "
      "%s and compared with the u_realized column the runners wrote." % gate["formula"])
    A("")
    A("- configurations checked: %d (the gate requires at least %d)"
      % (gate["n_configs_checked"], GATE_MIN_CONFIGS))
    A("- mismatches: %d" % gate["n_mismatches"])
    A("- largest absolute error: %.3e (tolerance %.0e for Eval-B, %.0e for the "
      "capacity arms, whose runner rounds the column to six decimals)"
      % (gate["max_abs_error"], gate["tolerance_evalb"],
         gate["tolerance_capacity"]))
    A("")
    A("Coverage of the reconciled set:")
    A("")
    A(gate["span"].to_string(index=False))
    A("")
    A("## 2. Metric definitions")
    A("")
    A("For a configuration with horizon H business hours, crew m_g in trade g "
      "and workload W_g = sum of p_bh over that trade's work orders, "
      "u_g = W_g / (m_g H).")
    A("")
    A("- overload_share: workload-weighted share of processing time in trades "
      "with u_g > 1 (primary concentration metric)")
    A("- max_u_trade: the largest u_g")
    A("- cv_u_weighted: coefficient of variation of u_g weighted by W_g")
    A("- share_trades_over: share of work-carrying trades with u_g > 1")
    A("- overload_share_even and overload_excess: the overload share the same "
      "portfolio would have if the configuration's TOTAL crew were spread over "
      "the trades in the base instance's proportions (exact, non-integer "
      "scaling), and the difference from the actual overload share. Total crew "
      "and therefore portfolio utilisation are identical by construction, so "
      "overload_excess isolates concentration with the load level held fixed. "
      "It is zero by construction for an untransformed configuration (arm "
      "m1.0) and undefined for the generator cells, which are scored as built.")
    A("")
    A("Edge cases: a trade with crew and no workload has u_g = 0, carries zero "
      "weight in the weighted metrics, and is excluded from share_trades_over; "
      "its technicians still sit in the portfolio denominator, as they do in "
      "u_realized. A trade with workload and no crew would have no finite u_g; "
      "%d configuration(s) contain one."
      % int(cfg["n_trades_no_crew"].gt(0).sum()))
    A("")
    A("Utilisation and concentration are strongly related by construction: "
      "Pearson correlation between u_realized and overload_share is %.3f over "
      "all %d configurations (%.3f on the replay-derived configurations alone, "
      "%.3f excluding campus %d). Every claim below therefore rests on "
      "comparisons at matched utilisation, never on the marginal association."
      % (corr["all"], len(cfg), corr["replay_only"], corr["no_campus2"],
         STRESS_CAMPUS))
    A("")
    A("Scopes: all pools every configuration; replay_only drops the generator "
      "track, which is a different object at the same utilisation; "
      "no_campus2 drops campus %d, the chronic-overload portfolio the "
      "manuscript keeps out of every verdict scope." % STRESS_CAMPUS)
    A("")
    A(zero_note)
    A("")
    A("## 3. Arm validation: does concentration separate the experimental arms?")
    A("")
    A("Mean overload_share by arm, pooled and within each utilisation band. "
      "The manuscript's story predicts the evenly scaled crew-multiplier arms "
      "(m1.0, m0.8, m0.6) to be low-concentration and the per-trade capacity "
      "arms (q90, q75) to be high-concentration at the same utilisation.")
    A("")
    piv = arms.pivot(index="u_bin", columns="arm", values="mean_overload_share")
    piv = piv.reindex([b for b in ("ALL",) + tuple(U_LABELS) if b in piv.index])
    A(piv.round(3).to_string())
    A("")
    A("Configuration counts behind those means:")
    A("")
    cnt = arms.pivot(index="u_bin", columns="arm", values="n_configs")
    cnt = cnt.reindex([b for b in ("ALL",) + tuple(U_LABELS) if b in cnt.index])
    A(cnt.fillna(0).astype(int).to_string())
    A("")
    A("Workload-weighted coefficient of variation of u_g by arm:")
    A("")
    piv2 = arms.pivot(index="u_bin", columns="arm", values="mean_cv_u_weighted")
    piv2 = piv2.reindex([b for b in ("ALL",) + tuple(U_LABELS) if b in piv2.index])
    A(piv2.round(3).to_string())
    A("")
    A("Mean overload_excess by arm, the level-matched concentration measure "
      "(zero by construction for m1.0, undefined for the generator cells):")
    A("")
    piv3 = arms[arms["arm"] != "gen"].pivot(index="u_bin", columns="arm",
                                            values="mean_overload_excess")
    piv3 = piv3.reindex([b for b in ("ALL",) + tuple(U_LABELS) if b in piv3.index])
    A(piv3.round(3).to_string())
    A("")
    A("Capacity arms minus crew-multiplier arms, inside each band, with "
      "cluster-bootstrap intervals. A positive contrast is what the "
      "manuscript's premise requires.")
    A("")
    A(armc.round(3).to_string(index=False))
    A("")
    A("## 4. Stratified: median split on overload_share inside each band")
    A("")
    for scope in SCOPES:
        A("### scope = %s" % scope)
        A("")
        s = strat[strat["scope"] == scope]
        cols = ["u_bin", "half", "n_configs", "n_clusters", "mean_u",
                "mean_overload_share", "mean_d_wmdd", "d_wmdd_ci_lo",
                "d_wmdd_ci_hi", "mean_d_atc", "d_atc_ci_lo", "d_atc_ci_hi"]
        A(s[cols].round(3).to_string(index=False))
        A("")
        A("High-minus-low contrasts (positive = weighted rules gain more where "
          "scarcity is more concentrated). mean_u_low and mean_u_high say how "
          "well the two halves are matched on load inside the band; the top "
          "band is open ended, so they are not matched there and its contrast "
          "carries a level difference as well as a structure difference.")
        A("")
        c = contrasts[contrasts["scope"] == scope]
        A(c.drop(columns=["scope"]).round(3).to_string(index=False))
        A("")
        pos = positive_bands(contrasts, scope)
        A("Bands with a positive contrast whose interval excludes zero: %d of "
          "%d (%s). These are the numbers behind the \\tscContrast macros; the "
          "unsuffixed macro names carry scope all, Replay carries replay_only "
          "and NoStress carries campus %d excluded."
          % (len(pos), len(U_LABELS), ", ".join(pos) if pos else "none",
             STRESS_CAMPUS))
        A("")
    A("## 5. Regression")
    A("")
    A("Ordinary least squares of the paired difference on utilisation and "
      "overload_share, with cluster-bootstrap percentile intervals. A positive "
      "overload_share coefficient whose interval excludes zero is the "
      "manuscript's prediction. The specifications differ only in how overall "
      "load is controlled: u_linear (one linear term), u_quadratic (linear "
      "plus square), u_bin_fe (band indicators), u_bin_fe_plus_u (band "
      "indicators and a linear term, so load variation inside a wide band is "
      "controlled too), and u_bin_fe_excess (band indicators, with "
      "overload_excess in place of overload_share, which holds total crew "
      "exactly fixed).")
    A("")
    for scope in SCOPES:
        A("### scope = %s" % scope)
        A("")
        r = reg[(reg["scope"] == scope) & (reg["term"] != "intercept")]
        A(r[["outcome", "spec", "term", "coef", "ci_lo", "ci_hi",
             "excludes_zero", "n_configs", "n_clusters", "r2"]]
          .round(4).to_string(index=False))
        A("")
    A("## 6. The two-dimensional map")
    A("")
    A("Utilisation band x overload-share band. The recommended family is "
      "derived mechanically: weighted when a weighted rule beats EDD beyond "
      "the margin or EDD is behind the cell's best method beyond it; either "
      "when EDD is equivalent to both weighted rules and to the best method; "
      "due-date otherwise; insufficient below %d base instances."
      % MIN_CLUSTERS_GRID)
    A("")
    for scope in SCOPES:
        A("### scope = %s" % scope)
        A("")
        g = gr[gr["scope"] == scope]
        cols = ["u_bin", "ov_band", "n_configs", "n_clusters", "mean_u",
                "mean_overload_share", "mean_d_wmdd", "d_wmdd_ci_lo",
                "d_wmdd_ci_hi", "verdict_wmdd_vs_edd", "verdict_atc_vs_edd",
                "verdict_edd_vs_best", "recommended_family"]
        A(g[cols].round(3).to_string(index=False))
        A("")
        A("Cells by recommended family: %s"
          % ", ".join("%s %d" % (k, v) for k, v in
                      g["recommended_family"].value_counts().items()))
        A("")
    path.write_text("\n".join(L) + "\n")
    return path


# --------------------------------------------------------------------------- #
# Macros
# --------------------------------------------------------------------------- #
class Macros:
    """\\tsc-prefixed macro definitions, each with the field it was read from.

    The prefix is ``tsc`` (trade scarcity); ``\\sc`` is a LaTeX primitive and
    cannot be used.
    """

    def __init__(self):
        self.items = []
        self.names = set()

    def section(self, title):
        self.items.append((None, None, title))

    def add(self, name, value, source):
        if not name.startswith("tsc"):
            raise SystemExit("macro %r does not use the \\tsc prefix" % name)
        if not name.isalpha():
            raise SystemExit("macro %r must be letters only (LaTeX)" % name)
        if name in self.names:
            raise SystemExit("macro %r defined twice" % name)
        v = str(value)
        if v.strip() == "" or "nan" in v.lower() or "inf" in v.lower():
            raise SystemExit("macro %r has a non-finite value %r" % (name, v))
        self.names.add(name)
        self.items.append((name, v, source))

    def render(self, header):
        width = min(78, max(len("\\newcommand{\\%s}{%s}" % (n, v))
                            for n, v, _ in self.items if n) + 2)
        L = [header]
        for name, value, comment in self.items:
            if name is None:
                L.append("")
                L.append("%% %s" % ("-" * 74))
                L.append("%% %s" % comment)
                L.append("%% %s" % ("-" * 74))
                continue
            defn = "\\newcommand{\\%s}{%s}" % (name, value)
            L.append("%s %% %s" % (defn.ljust(width - 1), comment))
        return "\n".join(L) + "\n"


def _group(digits: str) -> str:
    """Group an integer digit string with the manuscript's {,} separator."""
    parts = []
    while len(digits) > 3:
        parts.insert(0, digits[-3:])
        digits = digits[:-3]
    parts.insert(0, digits)
    return "{,}".join(parts)


def _f(value, nd=3):
    """Format a numeric macro value in the manuscript's house style.

    A negative value carries a math-mode minus (``$-$93.1``) rather than an
    ASCII hyphen, and an integer part of a thousand or more is grouped
    (``1{,}341``), matching paper/macros.tex (\\cleanwos and its neighbours).
    The sign is taken AFTER rounding, so a value that rounds to zero never
    prints a minus.
    """
    v = float(value)
    s = ("%%.%df" % nd) % abs(v)
    negative = (v < 0.0) and (float(s) != 0.0)
    if "." in s:
        head, tail = s.split(".", 1)
        s = _group(head) + "." + tail
    else:
        s = _group(s)
    return ("$-$" if negative else "") + s


def _i(value):
    """Integer macro value, grouped, in the same house style."""
    return _f(int(round(float(value))), nd=0)


def _sci(value, nd=1):
    """Scientific notation as math, so the exponent's minus is not a hyphen."""
    s = ("%%.%de" % nd) % float(value)
    mant, exp = s.split("e")
    return "$%s\\times10^{%d}$" % (mant, int(exp))


# Macro name suffix per scope; the pooled scope keeps the unsuffixed names.
SCOPE_TOKEN = (("all", ""), ("replay_only", "Replay"),
               ("no_campus2", "NoStress"))


def positive_bands(contrasts: pd.DataFrame, scope: str):
    """Bands whose high-minus-low d_wmdd contrast is positive and excludes zero."""
    sub = contrasts[contrasts["scope"] == scope]
    return [str(r["u_bin"]) for _, r in sub.iterrows()
            if np.isfinite(float(r["d_wmdd_ci_lo"]))
            and float(r["d_wmdd_ci_lo"]) > 0.0]


def _pick(df, **kw):
    m = pd.Series(True, index=df.index)
    for k, v in kw.items():
        m &= (df[k] == v)
    sub = df[m]
    return sub.iloc[0] if len(sub) else None


def build_macros(gate, cfg, strat, contrasts, reg, arms, armc, gr, corr,
                 zero_stats):
    M = Macros()
    M.section("Scope, reconciliation gate and correlation "
              "(scarcity.csv, scarcity_analysis.md section 1)")
    M.add("tscNConfigs", _i(gate["n_configs_checked"]),
          "configurations with trade-level metrics")
    M.add("tscNClusters", _i(cfg["cluster"].nunique()),
          "distinct base instances behind them")
    M.add("tscNReconciled", _i(gate["n_configs_checked"]),
          "configurations passing the utilisation reconciliation gate")
    M.add("tscReconMaxErr", _sci(max(gate["max_abs_error"], 1e-16)),
          "largest absolute reconciliation error")
    M.add("tscCorrUOv", _f(corr["all"], 2),
          "Pearson correlation, u_realized vs overload_share, all configurations")
    M.add("tscCorrUOvReplay", _f(corr["replay_only"], 2),
          "same correlation, replay-derived configurations only")
    M.add("tscRelDropped", _i(zero_stats["n_dropped"]),
          "configurations with wwt(EDD) = 0, dropped from relative analyses")

    M.section("Arm validation: mean overload_share by arm "
              "(scarcity_analysis.md section 3)")
    for ub, tok in [("ALL", "All")] + [(b, BIN_TOKEN[b]) for b in U_LABELS]:
        for arm, atok in ARM_TOKEN.items():
            r = _pick(arms, u_bin=ub, arm=arm)
            if r is None or int(r["n_configs"]) < 10:
                continue
            M.add("tscOv%s%s" % (tok, atok), _f(r["mean_overload_share"], 2),
                  "mean overload_share, arm %s, u band %s (n=%d)"
                  % (arm, ub, int(r["n_configs"])))
    for arm, atok in ARM_TOKEN.items():
        r = _pick(arms, u_bin="ALL", arm=arm)
        if r is None or arm == "gen" or not np.isfinite(
                float(r["mean_overload_excess"])):
            continue
        M.add("tscExcess%s" % atok, _f(r["mean_overload_excess"]),
              "mean overload_excess (level-matched concentration), arm %s"
              % arm)

    M.section("Arm separation: capacity arms minus crew-multiplier arms "
              "(scarcity_analysis.md section 3)")
    for ub, tok in [("ALL", "All")] + [(b, BIN_TOKEN[b]) for b in U_LABELS]:
        r = _pick(armc, u_bin=ub)
        if r is None:
            continue
        M.add("tscArmSep%s" % tok, _f(r["contrast_overload_share"]),
              "mean overload_share, capacity arms minus crew-multiplier arms, "
              "u band %s" % ub)
        M.add("tscArmSep%sCiLo" % tok, _f(r["overload_share_ci_lo"]),
              "its lower bound")
        M.add("tscArmSep%sCiHi" % tok, _f(r["overload_share_ci_hi"]),
              "its upper bound")

    # Every contrast macro names its scope, and the unsuffixed names are the
    # pooled scope. The three scopes disagree in sign in the top band, so a
    # macro read without its scope would be read wrongly.
    M.section("Stratified high-minus-low contrasts on d_wmdd "
              "(scarcity_analysis.md section 4; unsuffixed = scope all, "
              "Replay = replay_only, NoStress = campus %d excluded)"
              % STRESS_CAMPUS)
    for scope, stok in SCOPE_TOKEN:
        for b in U_LABELS:
            r = _pick(contrasts, scope=scope, u_bin=b)
            if r is None or not np.isfinite(float(r["contrast_d_wmdd"])):
                continue
            tok = BIN_TOKEN[b] + stok
            M.add("tscContrast%s" % tok, _f(r["contrast_d_wmdd"], 1),
                  "d_wmdd, high minus low concentration half, u band %s, "
                  "scope %s" % (b, scope))
            M.add("tscContrast%sCiLo" % tok, _f(r["d_wmdd_ci_lo"], 1),
                  "lower bound of that contrast, scope %s" % scope)
            M.add("tscContrast%sCiHi" % tok, _f(r["d_wmdd_ci_hi"], 1),
                  "upper bound of that contrast, scope %s" % scope)
        pos = positive_bands(contrasts, scope)
        M.add("tscBandsPositive%s" % stok, _i(len(pos)),
              "u bands whose high-minus-low d_wmdd contrast is positive with "
              "an interval excluding zero, scope %s (of %d bands)"
              % (scope, len(U_LABELS)))

    # The top band is open ended, so its two concentration halves also differ
    # in load; these two macros let the manuscript state that mismatch.
    M.section("Load mismatch inside the deepest utilisation band "
              "(scarcity_analysis.md section 4, columns mean_u_low/mean_u_high)")
    for scope, stok in SCOPE_TOKEN:
        r = _pick(contrasts, scope=scope, u_bin=U_LABELS[-1])
        if r is None:
            continue
        M.add("tscDeepULow%s" % stok, _f(r["mean_u_low"], 1),
              "mean u_realized of the low-concentration half, u band %s, "
              "scope %s" % (U_LABELS[-1], scope))
        M.add("tscDeepUHigh%s" % stok, _f(r["mean_u_high"], 1),
              "mean u_realized of the high-concentration half, u band %s, "
              "scope %s" % (U_LABELS[-1], scope))

    M.section("Regression coefficients on overload_share "
              "(scarcity_analysis.md section 5)")
    for scope, stok in (("all", "All"), ("replay_only", "Replay"),
                        ("no_campus2", "NoStress")):
        for outcome, otok in (("d_wmdd", "Wmdd"), ("d_atc", "Atc")):
            for spec, sptok, term in (("u_linear", "", "overload_share"),
                                      ("u_bin_fe", "Fe", "overload_share"),
                                      ("u_bin_fe_plus_u", "FeU",
                                       "overload_share"),
                                      ("u_bin_fe_excess", "Excess",
                                       "overload_excess")):
                r = _pick(reg, scope=scope, outcome=outcome, spec=spec,
                          term=term)
                if r is None:
                    continue
                base = "tscBeta%s%s%s" % (otok, stok, sptok)
                M.add(base, _f(r["coef"], 1),
                      "OLS coefficient on %s, outcome %s, %s control, scope %s"
                      % (term, outcome, spec, scope))
                M.add(base + "CiLo", _f(r["ci_lo"], 1), "its lower bound")
                M.add(base + "CiHi", _f(r["ci_hi"], 1), "its upper bound")
    for scope, stok in (("all", "All"), ("replay_only", "Replay"),
                        ("no_campus2", "NoStress")):
        r = _pick(reg, scope=scope, outcome="d_wmdd", spec="u_linear",
                  term="u_realized")
        if r is not None:
            M.add("tscBetaUWmdd%s" % stok, _f(r["coef"], 1),
                  "OLS coefficient on u_realized, outcome d_wmdd, scope %s" % scope)
            M.add("tscBetaUWmdd%sCiLo" % stok, _f(r["ci_lo"], 1),
                  "its lower bound")
            M.add("tscBetaUWmdd%sCiHi" % stok, _f(r["ci_hi"], 1),
                  "its upper bound")

    M.section("The two-dimensional map (scarcity_grid.csv)")
    g = gr[gr["scope"] == "all"]
    M.add("tscGridCells", _i(len(g)), "populated cells in the map, scope all")
    for fam, tok in (("weighted", "Weighted"), ("due-date", "DueDate"),
                     ("either", "Either"), ("insufficient", "Insufficient")):
        M.add("tscGrid%s" % tok, _i((g["recommended_family"] == fam).sum()),
              "cells whose mechanical recommendation is %s, scope all" % fam)
    M.add("tscGridUBands", _i(g["u_bin"].nunique()),
          "utilisation bands present in the map")
    M.add("tscGridOvBands", _i(g["ov_band"].nunique()),
          "overload-share bands present in the map")
    gs = gr[gr["scope"] == "no_campus2"]
    M.add("tscGridCellsNoStress", _i(len(gs)),
          "populated cells in the map, campus %d excluded" % STRESS_CAMPUS)
    for fam, tok in (("weighted", "Weighted"), ("due-date", "DueDate"),
                     ("either", "Either"), ("insufficient", "Insufficient")):
        M.add("tscGrid%sNoStress" % tok,
              _i((gs["recommended_family"] == fam).sum()),
              "cells recommending %s with campus %d excluded"
              % (fam, STRESS_CAMPUS))
    return M


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Trade-level scarcity structure vs the EDD/weighted gap.")
    ap.add_argument("--out", default=str(OUT_DIR),
                    help="output directory (default %s)" % OUT_DIR)
    ap.add_argument("--paper", default=str(PAPER_DIR),
                    help="paper directory for the macro file (default %s)"
                         % PAPER_DIR)
    ap.add_argument("--n-boot", type=int, default=stats.N_BOOT,
                    help="bootstrap resamples (default %d)" % stats.N_BOOT)
    ap.add_argument("--no-macros", action="store_true",
                    help="write the CSV/report outputs only")
    args = ap.parse_args(argv)

    os.chdir(ROOT)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = datetime.now()

    print("Reading results ...", flush=True)
    evalb_rows = normalize_method_column(pd.read_csv(EVALB_CSV))
    cap_rows = normalize_method_column(pd.read_csv(CAP_CSV))
    store = InstanceStore(INDEX_CSV, INST_ROOT)
    crew_tables = load_crew_tables(CAP_CALIB)

    evalb_cfg = evalb_configs(evalb_rows)
    cap_cfg = capacity_configs(cap_rows)
    print("  Eval-B configurations   : %d" % len(evalb_cfg))
    print("  capacity-arm configs    : %d  (arms %s; q=0.95 is the Eval-B "
          "baseline itself and is not a separate arm)"
          % (len(cap_cfg), sorted(cap_cfg["arm"].unique())), flush=True)

    print("Rebuilding configurations and measuring trade-level scarcity ...",
          flush=True)
    cfg = build_config_table(store, evalb_cfg, cap_cfg, crew_tables)

    print("Reconciliation gate ...", flush=True)
    gate = reconciliation_gate(cfg)
    print("  checked %d configuration(s); %d mismatch(es); max |error| %.3e"
          % (gate["n_configs_checked"], gate["n_mismatches"],
             gate["max_abs_error"]), flush=True)
    if gate["n_configs_checked"] < GATE_MIN_CONFIGS:
        raise SystemExit("reconciliation gate covered only %d configuration(s); "
                         "at least %d are required"
                         % (gate["n_configs_checked"], GATE_MIN_CONFIGS))
    if gate["n_mismatches"]:
        for e in gate["examples"]:
            print("    %s (%s): results.csv %.9f vs recomputed %.9f"
                  % (e["id"], e["source"], e["u_realized"], e["u_recomputed"]))
        raise SystemExit(
            "STOP: recomputed utilisation does not reproduce u_realized on %d "
            "configuration(s). Everything downstream shares that denominator "
            "convention, so no output was written." % gate["n_mismatches"])

    print("Joining paired outcomes ...", flush=True)
    outcomes, wide = outcome_table(evalb_rows, cap_rows)
    df = cfg.merge(outcomes, on="id", how="inner", validate="one_to_one")
    if len(df) != len(cfg):
        raise SystemExit("outcome join lost %d configuration(s)"
                         % (len(cfg) - len(df)))

    zero = df[df["wwt_edd"] <= 0]
    zero_stats = {"n_dropped": int(len(zero)),
                  "mean_d_wmdd": float(zero["d_wmdd"].mean()) if len(zero) else 0.0,
                  "mean_d_atc": float(zero["d_atc"].mean()) if len(zero) else 0.0}
    zero_note = (
        "Zero handling: %d of %d configurations have wwt(EDD) = 0, so their "
        "relative differences are undefined and they are dropped from the "
        "relative analyses only. Dropping them is not neutral: with "
        "wwt(EDD) = 0 the absolute difference can only be zero or negative, "
        "and on this corpus their mean d_wmdd is %.3f and mean d_atc is %.3f, "
        "so the relative analyses are biased towards the weighted rules "
        "relative to the absolute ones."
        % (zero_stats["n_dropped"], len(df), zero_stats["mean_d_wmdd"],
           zero_stats["mean_d_atc"]))

    corr = {}
    for scope in SCOPES:
        sc = scope_frame(df, scope)
        corr[scope] = float(np.corrcoef(sc["u_realized"],
                                        sc["overload_share"])[0, 1])

    scar_cols = ["id", "cluster", "source", "arm", "campus", "track", "regime",
                 "size", "crew_multiplier", "crew_q", "n_technicians",
                 "window_bh", "n_trades", "n_trades_active", "n_trades_no_crew",
                 "n_fallback_trades", "total_p_bh", "u_realized",
                 "u_recomputed", "u_bin", "overload_share", "ov_band",
                 "overload_share_even", "overload_excess",
                 "max_u_trade", "cv_u_weighted", "share_trades_over",
                 "wwt_edd", "wwt_wmdd", "wwt_atc", "wwt_min_common",
                 "argmin_method", "d_wmdd", "d_atc", "rel_d_wmdd", "rel_d_atc"]
    scar = df[scar_cols].sort_values(["source", "arm", "id"])
    p = out / "scarcity.csv"
    scar.to_csv(p, index=False)
    print("Wrote %d row(s) -> %s" % (len(scar), p), flush=True)

    print("Stratified analysis ...", flush=True)
    strat, contrasts = stratified(df, args.n_boot)
    print("Regressions ...", flush=True)
    reg = regressions(df, args.n_boot)
    print("Arm validation ...", flush=True)
    arms = arm_validation(df)
    armc = arm_contrasts(df, args.n_boot)
    print("Map grid ...", flush=True)
    gr = grid(df, wide, args.n_boot)
    p = out / "scarcity_grid.csv"
    gr.to_csv(p, index=False)
    print("Wrote %d row(s) -> %s" % (len(gr), p), flush=True)

    p = write_report(out / "scarcity_analysis.md", gate, cfg, strat, contrasts,
                     reg, arms, armc, gr, zero_note, corr, args.n_boot)
    print("Wrote %s" % p, flush=True)

    meta = {
        "analysis": "r4_scarcity",
        "generated": datetime.now().isoformat(timespec="seconds"),
        "elapsed_seconds": round((datetime.now() - t0).total_seconds(), 1),
        "inputs": {"index": str(INDEX_CSV), "evalb": str(EVALB_CSV),
                   "capacity": str(CAP_CSV), "capacity_calib": str(CAP_CALIB)},
        "n_configs": int(len(df)),
        "n_clusters": int(df["cluster"].nunique()),
        "configs_by_source": {k: int(v) for k, v in
                              df["source"].value_counts().items()},
        "configs_by_arm": {k: int(v) for k, v in
                           df["arm"].value_counts().items()},
        "common_methods": list(COMMON_METHODS),
        "n_boot": int(args.n_boot), "seed": int(stats.SEED),
        "alpha": stats.ALPHA, "margin_abs": stats.MARGIN_ABS,
        "margin_rel": stats.MARGIN_REL,
        "u_bin_edges": list(stats.U_BIN_EDGES),
        "overload_share_edges": list(OV_EDGES),
        "min_clusters_grid": MIN_CLUSTERS_GRID,
        "reconciliation": {k: v for k, v in gate.items()
                           if k not in ("span", "examples")},
        "zero_wwt_edd": zero_stats,
        "corr_u_overload_share": corr,
        # The stratified contrasts in machine-readable form: the report renders
        # the same frame as a fixed-width table and the macros are emitted from
        # it, so a macro can be checked against its scope without parsing text.
        "stratified_contrasts": [
            {k: (None if isinstance(v, float) and not np.isfinite(v)
                 else (float(v) if isinstance(v, (int, float, np.floating,
                                                  np.integer)) else str(v)))
             for k, v in rec.items()}
            for rec in contrasts.to_dict("records")],
        "positive_contrast_bands": {s: positive_bands(contrasts, s)
                                    for s in SCOPES},
    }
    p = out / "scarcity_meta.json"
    p.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")
    print("Wrote %s" % p, flush=True)

    if not args.no_macros:
        M = build_macros(gate, cfg, strat, contrasts, reg, arms, armc, gr, corr,
                         zero_stats)
        header = ("%% paper/%s -- generated by scripts/r4_scarcity.py\n"
                  "%% Trade-level scarcity structure measured directly on the "
                  "instance files\n"
                  "%% (results/r4_final/analysis/scarcity*.csv). Prefix tsc = "
                  "trade scarcity.\n"
                  "%% \\sc is a LaTeX primitive, so it is not used as a prefix "
                  "here." % MACRO_FILE)
        p = Path(args.paper) / MACRO_FILE
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(M.render(header))
        print("Wrote %d macro(s) -> %s" % (len(M.names), p), flush=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
