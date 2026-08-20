#!/usr/bin/env python
"""Definitive R4 robustness analysis: the four R4.7-R4.10 runs -> manuscript exhibits.

``scripts/r4_analysis.py`` is the evidence layer for Eval-B itself; this script
is the evidence layer for the four checks that ask whether an Eval-B conclusion
survives a modelling choice.  It reads the four robustness runs, re-derives the
Eval-B anchors they were built on, and answers one question per check with the
same statistics, the same coverage discipline and the same macro conventions.

  R4.7  processing-time model     results/r4_robustness/pmodel/
  R4.8  capacity estimator        results/r4_robustness/capacity/
  R4.9  backdated releases        results/r4_robustness/backdate/
  R4.10 service-window scenarios  results/r4_robustness/sla/

Four decisions separate this analysis from a naive per-run summary.

* **Stratification comes first.**  Campus 2 is a nonstationary overload and
  campus 1 is the transfer campus; neither is ever pooled with the verdict
  campuses (5, 9, 10, 12).  Every block below is reported three times, once per
  stratum, and no sentence mixes them.
* **The comparison is against the matching Eval-B anchors.**  Every robustness
  configuration is a transform of one Eval-B empirical anchor evaluated at crew
  multiplier 1.0, so the baseline arm is those same anchors, restricted to the
  same base instances and to the same 17 scored methods.  R4.7's own summed-line
  arm reproduces the Eval-B anchors exactly, which is asserted rather than
  assumed.
* **The endpoint is the SET and the FAMILY ORDER, not the method order.**  On
  the Eval-B anchors the 17 methods sit inside a fraction of a per cent of each
  other, which is inside the protocol's equivalence margin, so their pairwise
  order is not identified and a rank correlation on it measures noise.  Every
  stability row therefore carries the spread of the means and the margin as a
  share of the best mean, so a reader can see when a low rank correlation means
  "the ranking moved" and when it means "there was no ranking to move".
* **Equivalence sets are ranked among full-coverage methods.**  All 17 methods
  (7 transparent rules and the 10 policy seeds) run on every configuration of
  every arm, and the 10 seeds enter the ranking individually, never as a pool.

All paired statistics come from ``fmwos.stats`` (protocol §R4.5): paired on the
instance-configuration id, 95% percentile bootstrap over base-instance clusters
with 10000 resamples and master seed 12345, equivalence margin
max(1.0, 1% of the comparator mean), Holm within a comparison family.  Nothing
statistical is reimplemented.  The one statistic outside that module is the
Kendall tau-b rank correlation between two method orderings, taken from
``scipy.stats.kendalltau`` (the same SciPy that backs ``fmwos.stats``); it is a
rank correlation rather than a paired test, so it has no place in that module.

Outputs (all under --out, default results/r4_robustness/analysis/)
-----------------------------------------------------------------
  dataset.csv              per check: rows/configs/anchors, cross-checked vs meta.json
  equivalence.csv          per check x arm x stratum, every method vs the arm's best
  family_means.csv         per check x arm x stratum, the five method families
  stability.csv            per check x arm x stratum, tau-b and set overlap vs baseline
  vs_baseline_best.csv     per check x arm x stratum, every method vs the BASELINE best
  pmodel_calibration.csv   R4.7 calibration cascade (cap, technicians, mean p)
  capacity_utilization.csv R4.8 realized-utilization shift per estimator quantile
  capacity_ubin.csv        R4.8 arm-pooled equivalence sets per realized-utilization bin
  capacity_multipliers.csv R4.8 realized vs nominal crew multipliers (portfolio)
  backdate_clamp.csv       R4.9 per-instance clamping of the synthetic shift
  headline_robust.json     every number the manuscript cites, machine-readable
  analysis.md              the readable report (one section per check)
  meta.json                inputs, constants, timings, sanity-check outcomes

Usage
-----
    PYTHONPATH=src python scripts/r4_robust_analysis.py                 # analysis + macros
    PYTHONPATH=src python scripts/r4_robust_analysis.py --step analysis
    PYTHONPATH=src python scripts/r4_robust_analysis.py --step macros
    PYTHONPATH=src python scripts/r4_robust_analysis.py --check-latex

Re-running is idempotent: every output is rewritten from the same inputs with
the same seeds, so a second run reproduces every digit.  Macros are written to
``paper/macros_r4b.tex`` with the ``\\rfb`` prefix; ``paper/macros_r4.tex`` is
never touched and a name collision with it (or with ``paper/macros.tex``) is a
hard error.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kendalltau

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from fmwos import stats                                    # noqa: E402
from fmwos.io import normalize_method_column               # noqa: E402
# Macro plumbing and number formatting are shared with the Eval-B analysis so
# the two generated macro files read identically.
from r4_analysis import (MacroFile, existing_macro_names,  # noqa: E402
                         display_name, f_int, f_twt, f_pct, f_diff, f_text)

# --------------------------------------------------------------------------- #
# Fixed vocabulary of the robustness runs.
# --------------------------------------------------------------------------- #
VERDICT_CAMPUSES = (5, 9, 10, 12)
TRANSFER_CAMPUS = 1
STRESS_CAMPUS = 2

RULES = ("edd", "pfifo", "wspt", "atc", "wmdd", "lpt", "random")
V2_MLP = tuple("v2rl%d" % s for s in range(301, 311))
SCORED = RULES + V2_MLP            # every method the robustness runs evaluated
VALUE_COL = "wwt"

# The five method families the manuscript names.  A family's mean is the mean of
# its members' means, so the ten policy seeds count once as a family and not ten
# times; that is the "method-family ranking" R4.7's endpoint refers to.
FAMILY_OF = {"edd": "duedate", "pfifo": "duedate",
             "wmdd": "weighted", "atc": "weighted",
             "wspt": "processing", "lpt": "processing",
             "random": "random",
             **{m: "policy" for m in V2_MLP}}
FAMILY_ORDER = ("duedate", "weighted", "processing", "random", "policy")
FAMILY_LABEL = {"duedate": "due-date rules", "weighted": "weighted due-date rules",
                "processing": "processing-time rules", "random": "random",
                "policy": "learned policy seeds"}
# The three families that lead the Eval-B anchors.  Whether they still occupy
# the top three positions is the tie-immune form of the R4.7-R4.10 endpoint,
# because the order INSIDE this trio is inside the equivalence margin and
# therefore not identified.
LEADING_TRIO = frozenset({"policy", "duedate", "weighted"})

STRATA = ("verdict", "campus1", "campus2")
STRATUM_LABEL = {
    "verdict": "verdict campuses (5, 9, 10, 12)",
    "campus1": "campus 1 (transfer)",
    "campus2": "campus 2 (nonstationary overload)",
}

# --------------------------------------------------------------------------- #
# The four checks.  ``arms`` are reported in this order; ``baseline`` names the
# arm every other arm is compared against.  "EVALB" means the Eval-B empirical
# anchors at crew multiplier 1.0, read from results/r4_final/results.csv.
# --------------------------------------------------------------------------- #
EVALB = "EVALB"
CHECKS = (
    {"check": "pmodel", "protocol": "R4.7", "dir": "pmodel", "arm_col": "p_model",
     "arms": ("sum", "max", "single"), "baseline": "sum",
     "title": "Processing-time model (R4.7)",
     "question": "does the method-family ranking survive the line-aggregation "
                 "choice?"},
    {"check": "capacity", "protocol": "R4.8", "dir": "capacity", "arm_col": "crew_q",
     "arms": ("q0.95", "q0.90", "q0.75"), "baseline": "q0.95",
     "title": "Capacity estimator (R4.8)",
     "question": "do the conclusions depend on the crew-sizing quantile, or on "
                 "the realized utilization it produces?"},
    {"check": "backdate", "protocol": "R4.9", "dir": "backdate", "arm_col": "transform",
     "arms": ("baseline", "backdate"), "baseline": "baseline",
     "title": "Backdated releases (R4.9, synthetic)",
     "question": "does an earlier release proxy move the ranking or the "
                 "equivalence set?"},
    {"check": "sla", "protocol": "R4.10", "dir": "sla", "arm_col": "scenario",
     "arms": ("baseline", "emg", "rtn", "pmp3"), "baseline": "baseline",
     "title": "Service-window and priority scenarios (R4.10)",
     "question": "does a different service-window or priority convention move "
                 "the ranking or the equivalence set?"},
)
CHECK_BY_NAME = {c["check"]: c for c in CHECKS}

# Arms served by the Eval-B anchors rather than by the check's own results file.
EVALB_ARMS = {("capacity", "q0.95"), ("backdate", "baseline"), ("sla", "baseline")}

ARM_LABEL = {
    ("pmodel", "sum"): "summed line hours (v1 default)",
    ("pmodel", "max"): "dominant line's own hours",
    ("pmodel", "single"): "single-line orders only",
    ("capacity", "q0.95"): "p95 of weekly trade hours (Eval-B default)",
    ("capacity", "q0.90"): "p90 of weekly trade hours",
    ("capacity", "q0.75"): "p75 of weekly trade hours",
    ("backdate", "baseline"): "released timestamps (Eval-B)",
    ("backdate", "backdate"): "corrective releases shifted earlier",
    ("sla", "baseline"): "contract windows as recorded (Eval-B)",
    ("sla", "emg"): "compressed emergency focus (P1/P2 halved)",
    ("sla", "rtn"): "routine tightening (P3/P4 halved)",
    ("sla", "pmp3"): "preventive work mapped to P3",
}


# --------------------------------------------------------------------------- #
# Loading.
# --------------------------------------------------------------------------- #
def load_evalb(csv: Path) -> pd.DataFrame:
    """The Eval-B empirical anchors at crew multiplier 1.0, scored methods only.

    These 227 configurations are the base instances every robustness transform
    was applied to, so they are the untransformed arm of R4.8, R4.9 and R4.10.
    """
    df = pd.read_csv(csv)
    df = normalize_method_column(df)
    df = df[(df["regime"] == "final-empirical")
            & (df["crew_multiplier"].astype(float) == 1.0)
            & (df["method"].astype(str).isin(SCORED))].copy()
    df["method"] = df["method"].astype(str)
    df["campus"] = df["campus"].astype(int)
    df["base_instance_id"] = df["id"].astype(str)
    return df[["id", "base_instance_id", "campus", "size", "u_realized",
               "method", "feasible", VALUE_COL]].reset_index(drop=True)


def load_check(check: dict, root: Path) -> pd.DataFrame:
    """One robustness results.csv, normalised onto the common column set."""
    df = pd.read_csv(root / "results/r4_robustness" / check["dir"] / "results.csv")
    df = normalize_method_column(df)
    df["method"] = df["method"].astype(str)
    df["campus"] = df["campus"].astype(int)
    df["id"] = df["id"].astype(str)
    df["base_instance_id"] = df["base_instance_id"].astype(str)
    df["arm"] = arm_labels(check, df[check["arm_col"]])
    return df


def arm_labels(check: dict, col: pd.Series) -> pd.Series:
    """Map a check's arm column onto the arm tokens used throughout."""
    if check["check"] == "capacity":
        return col.astype(float).map(lambda q: "q%.2f" % q)
    return col.astype(str)


def stratum_frame(df: pd.DataFrame, stratum: str) -> pd.DataFrame:
    if stratum == "verdict":
        return df[df["campus"].isin(VERDICT_CAMPUSES)]
    if stratum == "campus1":
        return df[df["campus"] == TRANSFER_CAMPUS]
    if stratum == "campus2":
        return df[df["campus"] == STRESS_CAMPUS]
    raise ValueError("unknown stratum %r" % stratum)


# --------------------------------------------------------------------------- #
# Per-scope ranking, equivalence set and family means.
# --------------------------------------------------------------------------- #
def _pct_from(mean: float, best: float):
    """Percentage above the best mean; undefined (NaN) when the best mean is 0.

    Under the single-line processing model campus 2 falls to exactly zero
    weighted tardiness for most methods, and a percentage gap from zero is not a
    number.  Those scopes report the absolute gap instead.
    """
    return float("nan") if best == 0 else 100.0 * (mean - best) / best


def scope_equivalence(sub: pd.DataFrame, n_boot: int, seed: int) -> pd.DataFrame:
    """Equivalence set of one (check, arm, stratum) scope, ranked and annotated."""
    methods = [m for m in SCORED if m in set(sub["method"])]
    eq = stats.equivalence_set(sub, methods=methods, value_col=VALUE_COL,
                               n_boot=n_boot, seed=seed)
    if eq.empty:
        return eq
    eq = eq.sort_values("mean", kind="mergesort").reset_index(drop=True)
    best = float(eq["mean_best"].iloc[0])
    eq["family"] = eq["method"].map(FAMILY_OF)
    eq["rank"] = eq["mean"].rank(method="min").astype(int)
    eq["pct_from_best"] = [_pct_from(float(m), best) for m in eq["mean"]]
    eq["abs_from_best"] = eq["mean"].astype(float) - best
    eq["n_tied_with_best"] = int((eq["mean"].astype(float) == best).sum())
    return eq


def family_means(sub: pd.DataFrame) -> pd.Series:
    """Mean of the member methods' means, per family, in FAMILY_ORDER."""
    mm = sub[sub["feasible"] == 1].groupby("method")[VALUE_COL].mean()
    out = {}
    for fam in FAMILY_ORDER:
        members = [m for m in SCORED if FAMILY_OF[m] == fam and m in mm.index]
        out[fam] = float(mm[members].mean()) if members else float("nan")
    return pd.Series(out, index=list(FAMILY_ORDER))


def _tau(a: pd.Series, b: pd.Series):
    """Kendall tau-b between two value vectors aligned on the same index."""
    x = a.to_numpy(dtype=float)
    y = b.reindex(a.index).to_numpy(dtype=float)
    if x.size < 2 or np.all(x == x[0]) or np.all(y == y[0]):
        # Every value tied on one side: no ordering exists to correlate.
        return float("nan"), float("nan")
    r = kendalltau(x, y)
    return float(r.statistic), float(r.pvalue)


def method_mean_series(sub: pd.DataFrame) -> pd.Series:
    mm = sub[sub["feasible"] == 1].groupby("method")[VALUE_COL].mean()
    return mm.reindex([m for m in SCORED if m in mm.index])


# --------------------------------------------------------------------------- #
# Block 0: the scope table (every check x arm x stratum, with its anchors).
# --------------------------------------------------------------------------- #
def iter_scopes(frames: dict):
    """Yield ``(check, arm, stratum, subframe)`` in report order."""
    for spec in CHECKS:
        for arm in spec["arms"]:
            df = frames[(spec["check"], arm)]
            for stratum in STRATA:
                sub = stratum_frame(df, stratum)
                if not sub.empty:
                    yield spec, arm, stratum, sub


def build_frames(checks_raw: dict, evalb: pd.DataFrame) -> dict:
    """``frames[(check, arm)]`` for every arm, Eval-B arms included."""
    frames = {}
    for spec in CHECKS:
        for arm in spec["arms"]:
            if (spec["check"], arm) in EVALB_ARMS:
                frames[(spec["check"], arm)] = evalb.copy()
            else:
                d = checks_raw[spec["check"]]
                frames[(spec["check"], arm)] = d[d["arm"] == arm].copy()
    return frames


# --------------------------------------------------------------------------- #
# Block 1: equivalence, family means, stability.
# --------------------------------------------------------------------------- #
def analysis_blocks(frames: dict, evalb: pd.DataFrame, n_boot: int, seed: int):
    """Equivalence, family-mean and stability frames over every scope.

    The baseline arm of a scope is re-restricted to the anchors the arm actually
    ran on, so a rank correlation and a set overlap are always computed on the
    same base instances.  (Only R4.7's single-line arm differs: one anchor has no
    single-line orders and is dropped, which is why the restriction exists.)
    """
    eq_parts, fam_rows, stab_rows, cmp_parts = [], [], [], []
    baseline_cache = {}                 # (check, stratum, anchors) -> eq frame

    def baseline_eq(spec, stratum, anchors, sub_base):
        key = (spec["check"], stratum, anchors)
        if key not in baseline_cache:
            baseline_cache[key] = scope_equivalence(sub_base, n_boot, seed)
        return baseline_cache[key]

    for spec, arm, stratum, sub in iter_scopes(frames):
        check = spec["check"]
        anchors = frozenset(sub["base_instance_id"])
        eq = scope_equivalence(sub, n_boot, seed)
        eq.insert(0, "check", check)
        eq.insert(1, "arm", arm)
        eq.insert(2, "stratum", stratum)
        eq_parts.append(eq)

        fm = family_means(sub)
        fam_rows.append({"check": check, "arm": arm, "stratum": stratum,
                         **{("mean_" + f): float(fm[f]) for f in FAMILY_ORDER},
                         "family_order": ">".join(fm.sort_values().index)})

        # --- the same scope on the baseline arm, restricted to these anchors -- #
        base_df = frames[(check, spec["baseline"])]
        sub_base = stratum_frame(base_df, stratum)
        sub_base = sub_base[sub_base["base_instance_id"].isin(anchors)]
        beq = baseline_eq(spec, stratum, anchors, sub_base)

        means_a = method_mean_series(sub)
        means_b = method_mean_series(sub_base)
        tau_m, p_m = _tau(means_a, means_b)
        fam_a, fam_b = family_means(sub), family_means(sub_base)
        tau_f, p_f = _tau(fam_a, fam_b)

        set_a = set(eq.loc[eq["in_equivalence_set"] == 1, "method"])
        set_b = set(beq.loc[beq["in_equivalence_set"] == 1, "method"])
        union = set_a | set_b
        best_mean = float(eq["mean_best"].iloc[0])
        worst_mean = float(eq["mean"].max())
        # Which three families occupy the top three positions.  This is the
        # tie-immune version of "the ranking held": the order inside the leading
        # group moves with the modelling choice, the composition of the group is
        # what a reader can rely on.
        top3 = list(fam_a.sort_values().index[:3])
        stab_rows.append({
            "check": check, "arm": arm, "stratum": stratum,
            "n_configs": int(sub["id"].nunique()),
            "n_anchors": len(anchors),
            "n_anchors_baseline": int(sub_base["base_instance_id"].nunique()),
            "n_methods": int(eq["method"].nunique()),
            "best_method": str(eq["best_method"].iloc[0]),
            "best_mean": best_mean,
            "baseline_best_method": str(beq["best_method"].iloc[0]),
            "baseline_best_mean": float(beq["mean_best"].iloc[0]),
            "n_tied_with_best": int(eq["n_tied_with_best"].iloc[0]),
            "spread_pct": _pct_from(worst_mean, best_mean),
            "margin_pct_of_best": (float("nan") if best_mean == 0 else
                                   100.0 * stats.equivalence_margin(best_mean) / best_mean),
            "tau_method": tau_m, "tau_method_p": p_m,
            "tau_family": tau_f, "tau_family_p": p_f,
            "family_order": ">".join(fam_a.sort_values().index),
            "baseline_family_order": ">".join(fam_b.sort_values().index),
            "family_order_identical": int("".join(fam_a.sort_values().index)
                                          == "".join(fam_b.sort_values().index)),
            "top3_families": " ".join(sorted(top3)),
            "top3_is_leading_trio": int(set(top3) == LEADING_TRIO),
            "set_size": len(set_a), "baseline_set_size": len(set_b),
            "set_intersection": len(set_a & set_b),
            "set_jaccard": (float("nan") if not union
                            else len(set_a & set_b) / len(union)),
            "entered_set": " ".join(sorted(set_a - set_b)) or "-",
            "left_set": " ".join(sorted(set_b - set_a)) or "-",
            "set_members": " ".join(sorted(set_a)),
            **{("in_set_" + m): int(m in set_a) for m in RULES},
            "n_policy_seeds_in_set": sum(1 for m in V2_MLP if m in set_a),
            "n_policy_seeds_in_set_baseline": sum(1 for m in V2_MLP if m in set_b),
            **{("families_in_set_" + f):
               int(any(FAMILY_OF[m] == f for m in set_a)) for f in FAMILY_ORDER},
        })

        # --- every method against the BASELINE arm's best method ------------ #
        ref = str(beq["best_method"].iloc[0])
        s = sub.copy()
        s["analysis_scope"] = "%s|%s|%s" % (check, arm, stratum)
        c = stats.compare_all(s, reference_methods=[ref],
                              methods=[m for m in SCORED if m in set(s["method"])],
                              scope_cols=["analysis_scope"], value_col=VALUE_COL,
                              n_boot=n_boot, seed=seed)
        if not c.empty:
            c.insert(0, "check", check)
            c.insert(1, "arm", arm)
            c.insert(2, "stratum", stratum)
            c["reference_role"] = "baseline_best"
            cmp_parts.append(c.drop(columns=["analysis_scope"]))

    eq_all = pd.concat(eq_parts, ignore_index=True)
    eq_cols = ["check", "arm", "stratum", "method", "family", "rank", "n_rows",
               "coverage", "mean", "best_method", "mean_best", "pct_from_best",
               "abs_from_best", "n_tied_with_best", "n_configs", "n_clusters",
               "mean_diff", "ci_lo", "ci_hi", "margin", "wilcoxon_p", "verdict",
               "in_equivalence_set"]
    eq_all = eq_all[eq_cols]
    cmp_all = pd.concat(cmp_parts, ignore_index=True)
    cmp_cols = ["check", "arm", "stratum", "method", "reference",
                "reference_role", "family", "n_configs", "n_clusters",
                "mean_ref", "mean_method", "mean_diff", "ci_lo", "ci_hi",
                "margin", "wilcoxon_p", "holm_p", "verdict"]
    return (eq_all, pd.DataFrame(fam_rows), pd.DataFrame(stab_rows),
            cmp_all[cmp_cols])


# --------------------------------------------------------------------------- #
# Block 2 (R4.7): the calibration cascade.
# --------------------------------------------------------------------------- #
def pmodel_calibration_block(root: Path) -> pd.DataFrame:
    """The per-model capacity cascade, transcribed from calib_summary.csv."""
    c = pd.read_csv(root / "results/r4_robustness/pmodel/calib_summary.csv")
    c["campus"] = c["campus"].astype("Int64")
    return c


# --------------------------------------------------------------------------- #
# Block 3 (R4.8): realized utilization, its bins, and the crew multipliers.
# --------------------------------------------------------------------------- #
def capacity_utilization_block(frames: dict, checks_raw: dict) -> pd.DataFrame:
    """Realized utilization per estimator quantile and stratum.

    R4.8's endpoint is that conclusions are read against realized utilization
    rather than against the estimator, so this is the table that says how far
    each quantile moves utilization, and from what.
    """
    rows = []
    cap = checks_raw["capacity"].drop_duplicates("id")
    base = frames[("capacity", "q0.95")].drop_duplicates("id")
    for arm in ("q0.95", "q0.90", "q0.75"):
        for stratum in STRATA:
            if arm == "q0.95":
                sub = stratum_frame(base, stratum)
                u = sub["u_realized"].to_numpy(dtype=float)
                shift = np.zeros_like(u)
                ubase = u
                n_tech = float("nan")
            else:
                sub = stratum_frame(cap[cap["arm"] == arm], stratum)
                u = sub["u_realized"].to_numpy(dtype=float)
                ubase = sub["u_realized_base"].to_numpy(dtype=float)
                shift = sub["u_shift"].to_numpy(dtype=float)
                n_tech = float(sub["n_technicians"].mean())
            rows.append({
                "arm": arm, "stratum": stratum, "n_configs": int(len(sub)),
                "mean_technicians": n_tech,
                "u_mean": float(u.mean()), "u_median": float(np.median(u)),
                "u_p25": float(np.percentile(u, 25)),
                "u_p75": float(np.percentile(u, 75)),
                "u_min": float(u.min()), "u_max": float(u.max()),
                "share_u_over_one": float((u >= 1.0).mean()),
                "share_u_over_twelve": float((u >= 1.2).mean()),
                "u_base_mean": float(ubase.mean()),
                "u_base_median": float(np.median(ubase)),
                "share_u_base_over_one": float((ubase >= 1.0).mean()),
                "u_shift_mean": float(shift.mean()),
                "u_shift_median": float(np.median(shift)),
                "u_shift_max": float(shift.max()),
            })
    return pd.DataFrame(rows)


def capacity_ubin_block(frames: dict, checks_raw: dict, n_boot: int,
                        seed: int) -> pd.DataFrame:
    """Equivalence sets per realized-utilization bin, pooling the three arms.

    Pooling is legitimate here and nowhere else in this file: the three arms are
    the same weeks under three crew sizings, so binning them together on
    REALIZED utilization is exactly the reading R4.8 prescribes, and the cluster
    bootstrap resamples base instances, which is what makes the three
    configurations of one week count as one observation.  Only the verdict
    campuses enter.
    """
    cols = ["id", "base_instance_id", "campus", "u_realized", "method",
            "feasible", VALUE_COL]
    base = frames[("capacity", "q0.95")][cols]
    cap = checks_raw["capacity"][cols]
    pool = pd.concat([base, cap], ignore_index=True)
    pool = pool[pool["campus"].isin(VERDICT_CAMPUSES)].copy()
    stats.add_utilization_bin(pool)
    parts = []
    for b in stats.U_BIN_ORDER:
        sub = pool[pool["u_bin"] == b]
        if sub.empty:
            continue
        eq = scope_equivalence(sub, n_boot, seed)
        eq.insert(0, "u_bin", b)
        cfg = sub.drop_duplicates("id")
        eq["u_lo"] = float(cfg["u_realized"].min())
        eq["u_hi"] = float(cfg["u_realized"].max())
        eq["n_configs_bin"] = int(cfg["id"].nunique())
        eq["n_anchors_bin"] = int(cfg["base_instance_id"].nunique())
        parts.append(eq)
    out = pd.concat(parts, ignore_index=True)
    return out[["u_bin", "u_lo", "u_hi", "n_configs_bin", "n_anchors_bin",
                "method", "family", "rank", "mean", "best_method", "mean_best",
                "pct_from_best", "n_configs", "n_clusters", "mean_diff",
                "ci_lo", "ci_hi", "margin", "verdict", "in_equivalence_set"]]


def capacity_multipliers_block(root: Path) -> pd.DataFrame:
    """Realized vs nominal crew multipliers, portfolio and campus rows."""
    rm = pd.read_csv(root / "results/r4_robustness/capacity/realized_multipliers.csv")
    return rm[rm["scope"].isin(("portfolio", "campus"))].reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Block 4 (R4.9): the synthetic shift and how often it clamps.
# --------------------------------------------------------------------------- #
def backdate_clamp_block(checks_raw: dict) -> pd.DataFrame:
    """Per-instance clamping of the backdated release, by stratum.

    A shifted release is clamped at the start of the scheduling window, so the
    share of corrective orders that clamp is the honest measure of how much of
    the synthetic shift the instance could absorb.
    """
    bd = checks_raw["backdate"].drop_duplicates("id").copy()
    bd["clamp_share_corrective"] = bd["n_clamped_at_zero"] / bd["n_corrective"]
    bd["clamp_share_orders"] = bd["n_clamped_at_zero"] / bd["n_wos"]
    rows = []
    for stratum in STRATA:
        sub = stratum_frame(bd, stratum)
        rows.append({
            "stratum": stratum, "n_configs": int(len(sub)),
            "n_orders": int(sub["n_wos"].sum()),
            "n_corrective": int(sub["n_corrective"].sum()),
            "corrective_share_mean": float(sub["corrective_share"].mean()),
            "clamped_total": int(sub["n_clamped_at_zero"].sum()),
            "clamped_mean": float(sub["n_clamped_at_zero"].mean()),
            "clamped_median": float(sub["n_clamped_at_zero"].median()),
            "clamped_min": int(sub["n_clamped_at_zero"].min()),
            "clamped_max": int(sub["n_clamped_at_zero"].max()),
            "clamp_share_corrective_pooled":
                float(sub["n_clamped_at_zero"].sum() / sub["n_corrective"].sum()),
            "clamp_share_corrective_mean": float(sub["clamp_share_corrective"].mean()),
            "clamp_share_corrective_min": float(sub["clamp_share_corrective"].min()),
            "clamp_share_corrective_max": float(sub["clamp_share_corrective"].max()),
            "clamp_share_orders_mean": float(sub["clamp_share_orders"].mean()),
            "delta_bh_mean": float(sub["mean_delta_bh"].mean()),
            "delta_bh_max": float(sub["max_delta_bh"].max()),
        })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Dataset table and sanity checks.
# --------------------------------------------------------------------------- #
def dataset_block(checks_raw: dict, metas: dict, evalb: pd.DataFrame) -> pd.DataFrame:
    rows = [{"check": "evalb_anchors", "protocol": "R4.4",
             "n_rows": len(evalb), "n_configs": evalb["id"].nunique(),
             "n_anchors": evalb["base_instance_id"].nunique(),
             "n_methods": evalb["method"].nunique(), "n_arms": 1,
             "n_infeasible": int((evalb["feasible"] != 1).sum()), "n_errors": 0,
             "elapsed_seconds": float("nan"),
             "n_verdict": stratum_frame(evalb, "verdict")["id"].nunique(),
             "n_campus1": stratum_frame(evalb, "campus1")["id"].nunique(),
             "n_campus2": stratum_frame(evalb, "campus2")["id"].nunique()}]
    for spec in CHECKS:
        d, meta = checks_raw[spec["check"]], metas[spec["check"]]
        rows.append({
            "check": spec["check"], "protocol": spec["protocol"],
            "n_rows": len(d), "n_configs": d["id"].nunique(),
            "n_anchors": d["base_instance_id"].nunique(),
            "n_methods": d["method"].nunique(), "n_arms": d["arm"].nunique(),
            "n_infeasible": int((d["feasible"] != 1).sum()),
            "n_errors": int(meta.get("n_errors", 0)),
            "elapsed_seconds": float(meta.get("elapsed_seconds", float("nan"))),
            "n_verdict": stratum_frame(d, "verdict")["id"].nunique(),
            "n_campus1": stratum_frame(d, "campus1")["id"].nunique(),
            "n_campus2": stratum_frame(d, "campus2")["id"].nunique()})
    return pd.DataFrame(rows)


def sanity_checks(checks_raw: dict, metas: dict, evalb: pd.DataFrame,
                  dataset: pd.DataFrame) -> list:
    """Assertions that must hold before any number is written; raises on failure."""
    checks = []

    def require(name, got, want):
        ok = (got == want)
        checks.append({"check": name, "got": got, "want": want, "ok": bool(ok)})
        if not ok:
            raise SystemExit("sanity check failed: %s (got %r, want %r)"
                             % (name, got, want))

    require("Eval-B anchors at m=1.0", int(evalb["id"].nunique()), 227)
    require("Eval-B anchors, verdict stratum",
            int(stratum_frame(evalb, "verdict")["id"].nunique()), 180)
    require("Eval-B scored methods", int(evalb["method"].nunique()), len(SCORED))

    d = dataset.set_index("check")
    for spec in CHECKS:
        name, meta = spec["check"], metas[spec["check"]]
        require("%s: configs vs meta.json" % name,
                int(d.loc[name, "n_configs"]), int(meta["n_configs"]))
        require("%s: rows vs meta.json" % name,
                int(d.loc[name, "n_rows"]), int(meta["n_rows"]))
        require("%s: infeasible vs meta.json" % name,
                int(d.loc[name, "n_infeasible"]), int(meta["n_infeasible"]))
        require("%s: errors vs meta.json" % name,
                int(d.loc[name, "n_errors"]), int(meta["n_errors"]))
        require("%s: base instances vs meta.json" % name,
                int(d.loc[name, "n_anchors"]), int(meta["base_instances"]))
        require("%s: methods scored" % name,
                int(d.loc[name, "n_methods"]), len(SCORED))
        df = checks_raw[name]
        require("%s: every anchor is an Eval-B anchor" % name,
                int(df["base_instance_id"].isin(set(evalb["id"])).all()), 1)
        require("%s: id suffix strips back to the anchor" % name,
                int((df["id"].map(stats.base_instance_id)
                     == df["base_instance_id"]).all()), 1)
        per = df.groupby(["arm", "method"])["id"].nunique().unstack()
        require("%s: every method covers every configuration of its arm" % name,
                int(per.nunique(axis=1).max()), 1)
        require("%s: value column has no missing entry" % name,
                int(df[VALUE_COL].isna().sum()), 0)

    # R4.7's summed-line arm must reproduce the Eval-B anchors exactly: it is the
    # same aggregation and the same calibration, so any difference would mean the
    # robustness runner and the Eval-B runner disagree about the instances.
    s = checks_raw["pmodel"]
    s = s[s["arm"] == "sum"][["base_instance_id", "method", VALUE_COL]]
    j = s.merge(evalb[["id", "method", VALUE_COL]], left_on=["base_instance_id", "method"],
                right_on=["id", "method"], suffixes=("_arm", "_evalb"))
    require("R4.7 sum arm pairs with every Eval-B row", int(len(j)), int(len(s)))
    require("R4.7 sum arm reproduces Eval-B exactly",
            float(np.abs(j[VALUE_COL + "_arm"] - j[VALUE_COL + "_evalb"]).max()), 0.0)

    # R4.8 records the untransformed crew count and utilization on every row; both
    # must match the Eval-B anchor they were derived from.
    cap = checks_raw["capacity"].drop_duplicates("id")
    ub = (evalb.drop_duplicates("id").set_index("id")["u_realized"]
          .reindex(cap["base_instance_id"]).to_numpy(dtype=float))
    require("R4.8 baseline utilization matches Eval-B (max abs diff < 1e-6)",
            bool(np.nanmax(np.abs(cap["u_realized_base"].to_numpy(dtype=float) - ub))
                 < 1e-6), True)
    return checks


# --------------------------------------------------------------------------- #
# headline_robust.json
# --------------------------------------------------------------------------- #
def _row(frame, **kw):
    m = pd.Series(True, index=frame.index)
    for k, v in kw.items():
        m &= (frame[k] == v)
    r = frame[m]
    return None if r.empty else r.iloc[0]


def _num(x):
    v = float(x)
    return None if not np.isfinite(v) else v


def build_headline(dataset, eq, fam, stab, cmp_, calib, caputil, capubin,
                   capmult, clamp, metas) -> dict:
    H = {"dataset": {r["check"]: {k: (None if (isinstance(r[k], float)
                                               and not np.isfinite(r[k])) else
                                      (int(r[k]) if k != "elapsed_seconds"
                                       else float(r[k])))
                                  for k in ("n_rows", "n_configs", "n_anchors",
                                            "n_methods", "n_arms", "n_infeasible",
                                            "n_errors", "n_verdict", "n_campus1",
                                            "n_campus2", "elapsed_seconds")}
                     for _, r in dataset.iterrows()},
         "conventions": {
             "scored_methods": list(SCORED),
             "families": {f: [m for m in SCORED if FAMILY_OF[m] == f]
                          for f in FAMILY_ORDER},
             "strata": {s: STRATUM_LABEL[s] for s in STRATA},
             "tau": "Kendall tau-b on the method mean vector (scipy.stats.kendalltau)",
             "jaccard": "|A and B| / |A or B| over equivalence-set membership",
         }}

    # --- one entry per check x arm x stratum ----------------------------- #
    H["scopes"] = {}
    for r in stab.itertuples():
        key = "%s|%s|%s" % (r.check, r.arm, r.stratum)
        e = eq[(eq["check"] == r.check) & (eq["arm"] == r.arm)
               & (eq["stratum"] == r.stratum)]
        entry = {
            "check": r.check, "arm": r.arm, "stratum": r.stratum,
            "arm_label": ARM_LABEL[(r.check, r.arm)],
            "n_configs": int(r.n_configs), "n_anchors": int(r.n_anchors),
            "best_method": r.best_method, "best_mean": _num(r.best_mean),
            "baseline_best_method": r.baseline_best_method,
            "n_tied_with_best": int(r.n_tied_with_best),
            "spread_pct": _num(r.spread_pct),
            "margin_pct_of_best": _num(r.margin_pct_of_best),
            "tau_method": _num(r.tau_method), "tau_family": _num(r.tau_family),
            "family_order": r.family_order,
            "baseline_family_order": r.baseline_family_order,
            "family_order_identical": bool(r.family_order_identical),
            "set_size": int(r.set_size),
            "baseline_set_size": int(r.baseline_set_size),
            "set_jaccard": _num(r.set_jaccard),
            "entered_set": r.entered_set, "left_set": r.left_set,
            "n_policy_seeds_in_set": int(r.n_policy_seeds_in_set),
            "rules": {},
        }
        for m in RULES:
            row = _row(e, method=m)
            if row is None:
                continue
            entry["rules"][m] = {
                "mean": _num(row["mean"]), "rank": int(row["rank"]),
                "pct_from_best": _num(row["pct_from_best"]),
                "abs_from_best": _num(row["abs_from_best"]),
                "in_set": int(row["in_equivalence_set"]),
                "verdict": str(row["verdict"]),
            }
        vb = _row(cmp_, check=r.check, arm=r.arm, stratum=r.stratum, method="edd")
        if vb is not None:
            entry["edd_vs_baseline_best"] = {
                "reference": str(vb["reference"]),
                "mean_diff": _num(vb["mean_diff"]),
                "ci": [_num(vb["ci_lo"]), _num(vb["ci_hi"])],
                "verdict": str(vb["verdict"]),
            }
        H["scopes"][key] = entry

    # --- R4.7 -------------------------------------------------------------- #
    port = calib[calib["scope"] == "all"].set_index("p_model")
    H["pmodel"] = {
        "protocol": "R4.7",
        "calibration": {m: {"work_orders": int(port.loc[m, "work_orders"]),
                            "labor_cap_hours": float(port.loc[m, "r4_labor_cap_hours"]),
                            "total_technicians": int(port.loc[m, "total_technicians"]),
                            "n_trades": int(port.loc[m, "n_trades"]),
                            "mean_p_bh": float(port.loc[m, "mean_p_bh"]),
                            "median_p_bh": float(port.loc[m, "median_p_bh"]),
                            "pm_share": float(port.loc[m, "pm_share"])}
                        for m in ("sum", "max", "single")},
        "anchors_skipped_single": int(metas["pmodel"]["per_model"]["single"]["anchors_skipped"]),
        "crew_q": float(metas["pmodel"]["crew_q"]),
    }

    # --- R4.8 -------------------------------------------------------------- #
    H["capacity"] = {
        "protocol": "R4.8",
        "total_technicians": {q: int(n) for q, n
                              in metas["capacity"]["total_crew_per_q"].items()},
        "utilization": {"%s|%s" % (r.arm, r.stratum): {
            "n_configs": int(r.n_configs), "u_mean": _num(r.u_mean),
            "u_median": _num(r.u_median), "u_p25": _num(r.u_p25),
            "u_p75": _num(r.u_p75), "u_min": _num(r.u_min), "u_max": _num(r.u_max),
            "share_u_over_one": _num(r.share_u_over_one),
            "u_shift_mean": _num(r.u_shift_mean),
            "u_shift_median": _num(r.u_shift_median)}
            for r in caputil.itertuples()},
        "realized_multipliers": {"m=%s" % r.m: {
            "crew_nominal": int(r.crew_nominal), "crew_realized": int(r.crew_realized),
            "realized_multiplier": float(r.realized_multiplier)}
            for r in capmult[capmult["scope"] == "portfolio"].itertuples()},
        "u_bin": {},
    }
    for b, sub in capubin.groupby("u_bin", sort=False):
        members = list(sub.loc[sub["in_equivalence_set"] == 1, "method"])
        H["capacity"]["u_bin"][b] = {
            "u_lo": float(sub["u_lo"].iloc[0]), "u_hi": float(sub["u_hi"].iloc[0]),
            "n_configs": int(sub["n_configs_bin"].iloc[0]),
            "n_anchors": int(sub["n_anchors_bin"].iloc[0]),
            "best_method": str(sub["best_method"].iloc[0]),
            "set_size": len(members),
            "rules": {m: {"pct_from_best": _num(_row(sub, method=m)["pct_from_best"]),
                          "in_set": int(_row(sub, method=m)["in_equivalence_set"])}
                      for m in RULES if _row(sub, method=m) is not None},
            "n_policy_seeds_in_set": sum(1 for m in V2_MLP if m in members),
        }

    # --- R4.9 -------------------------------------------------------------- #
    H["backdate"] = {
        "protocol": "R4.9", "seed": int(metas["backdate"]["backdate_seed"]),
        "max_shift_frac": float(metas["backdate"]["max_shift_frac"]),
        "clamp": {r.stratum: {k: (int(getattr(r, k)) if k.startswith("n_")
                                  or k in ("clamped_total", "clamped_min", "clamped_max")
                                  else _num(getattr(r, k)))
                              for k in ("n_configs", "n_orders", "n_corrective",
                                        "corrective_share_mean", "clamped_total",
                                        "clamped_mean", "clamped_median",
                                        "clamped_min", "clamped_max",
                                        "clamp_share_corrective_pooled",
                                        "clamp_share_corrective_mean",
                                        "clamp_share_corrective_min",
                                        "clamp_share_corrective_max",
                                        "delta_bh_mean", "delta_bh_max")}
                  for r in clamp.itertuples()},
    }

    # --- cross-cutting summary over the scenario checks ------------------- #
    # "Scenario" means R4.9 and R4.10: the two checks that keep the instances and
    # the capacity fixed and change only the due dates or the release times, so
    # their arms are directly comparable with the Eval-B anchors.  R4.7 and R4.8
    # change the work content and the crew, which moves the absolute level too,
    # and are summarised separately in their own sections.
    scen = stab[(stab["check"].isin(("backdate", "sla")))
                & (stab["arm"] != "baseline")]
    scen_v = scen[scen["stratum"] == "verdict"]
    worst_j = scen.loc[scen["set_jaccard"].idxmin()]
    leavers = sorted({m for s in scen_v["left_set"] for m in str(s).split()
                      if m != "-"})
    # Every TRANSFORMED arm on the verdict stratum: the three untransformed arms
    # (Eval-B itself under three names) are excluded, so the count is the number
    # of modelling changes the leading trio survived.
    verdict_arms = stab[(stab["stratum"] == "verdict")
                        & ~((stab["check"] == "capacity") & (stab["arm"] == "q0.95"))
                        & ~((stab["check"] == "pmodel") & (stab["arm"] == "sum"))
                        & (stab["arm"] != "baseline")]
    H["summary"] = {
        "scenario_checks": ["backdate", "sla"],
        "n_scenario_scopes": int(len(scen)),
        "jaccard_min": _num(scen["set_jaccard"].min()),
        "jaccard_min_scope": "%s|%s|%s" % (worst_j["check"], worst_j["arm"],
                                           worst_j["stratum"]),
        "jaccard_median": _num(scen["set_jaccard"].median()),
        "jaccard_max": _num(scen["set_jaccard"].max()),
        "tau_method_min": _num(scen["tau_method"].min()),
        "tau_method_max": _num(scen["tau_method"].max()),
        "n_family_order_identical": int(scen["family_order_identical"].sum()),
        "verdict_set_leavers": leavers,
        "verdict_set_leavers_families": sorted({FAMILY_OF[m] for m in leavers}),
        "n_verdict_arms": int(len(verdict_arms)),
        "n_verdict_arms_leading_trio": int(verdict_arms["top3_is_leading_trio"].sum()),
        "leading_trio": sorted(LEADING_TRIO),
    }
    # Which families hold a set member, in every scope of every check: the
    # tie-immune version of "the ranking held".
    H["summary"]["families_in_set"] = {
        "%s|%s|%s" % (r.check, r.arm, r.stratum):
            [f for f in FAMILY_ORDER if getattr(r, "families_in_set_" + f)]
        for r in stab.itertuples()}
    return H


# --------------------------------------------------------------------------- #
# analysis.md
# --------------------------------------------------------------------------- #
def _fmt(x, nd=3):
    if x is None or (isinstance(x, float) and not np.isfinite(float(x))):
        return "-"
    return ("%%.%df" % nd) % float(x)


def _md_table(frame: pd.DataFrame, cols, fmts=None) -> str:
    fmts = fmts or {}
    head = "| " + " | ".join(cols) + " |\n|" + "|".join(["---"] * len(cols)) + "|\n"
    body = []
    for r in frame.itertuples():
        cells = []
        for c in cols:
            v = getattr(r, c)
            f = fmts.get(c)
            cells.append(f(v) if f else (str(v) if not isinstance(v, float)
                                         else _fmt(v)))
        body.append("| " + " | ".join(cells) + " |")
    return head + "\n".join(body) + "\n"


def write_report(out: Path, dataset, eq, fam, stab, cmp_, calib, pmutil, caputil,
                 capubin, capmult, clamp, checksums, n_boot, seed) -> None:
    L = []
    A = L.append
    A("# R4 robustness definitive analysis (R4.7-R4.10)\n")
    A("Inputs: `results/r4_robustness/{pmodel,capacity,backdate,sla}/results.csv` "
      "and the Eval-B empirical anchors at crew multiplier 1.0 from "
      "`results/r4_final/results.csv`. Statistics: `fmwos.stats`, protocol "
      "§R4.5, %d bootstrap resamples over base-instance clusters, master seed "
      "%d, equivalence margin max(1.0, 1%% of the comparator mean). Rank "
      "correlations are Kendall tau-b (`scipy.stats.kendalltau`). A negative "
      "paired difference means the method is better than its comparator.\n"
      % (n_boot, seed))
    A("Scoring: %d methods, all of them run on every configuration of every arm "
      "(%d transparent rules and the %d policy seeds, each seed ranked "
      "individually). Strata: %s. Campus 2 never enters a verdict scope.\n"
      % (len(SCORED), len(RULES), len(V2_MLP),
         "; ".join("%s = %s" % (s, STRATUM_LABEL[s]) for s in STRATA)))
    A("\nHow to read a low `tau_method`: on these anchors the 17 methods sit "
      "within a fraction of a per cent of each other, and the equivalence "
      "margin is wider than that whole spread, so the pairwise ORDER of the "
      "methods is not identified. Every stability row therefore carries "
      "`spread_pct` (the worst mean over the best mean) and `margin_pct_of_best` "
      "(the margin as a share of the best mean) next to the rank correlation.\n")

    A("\n## 0. Run sizes\n")
    A(_md_table(dataset, ["check", "protocol", "n_rows", "n_configs", "n_anchors",
                          "n_methods", "n_arms", "n_infeasible", "n_errors",
                          "n_verdict", "n_campus1", "n_campus2"]))

    for spec in CHECKS:
        A("\n## %s\n" % spec["title"])
        A("Endpoint: %s\n" % spec["question"])
        if spec["check"] == "pmodel":
            A("\nCalibration cascade (portfolio rows of `calib_summary.csv`); "
              "capacity is recalibrated per model, which is what keeps realized "
              "utilization comparable across the three arms.\n")
            A(_md_table(calib[calib["scope"] == "all"],
                        ["p_model", "work_orders", "r4_labor_cap_hours",
                         "n_trades", "total_technicians", "mean_p_bh",
                         "median_p_bh", "pm_share"]))
            A("\nPer campus:\n")
            A(_md_table(calib[calib["scope"] == "campus"],
                        ["p_model", "campus", "work_orders", "n_trades",
                         "total_technicians", "mean_p_bh"]))
            A("\nWhat the recalibration holds fixed. The three models change how "
              "much work an order carries, so without the table below a reader "
              "cannot tell whether a change in weighted tardiness is the "
              "aggregation choice or a change of contention regime "
              "(`pmodel_utilization.csv`):\n")
            A(_md_table(pmutil, ["arm", "stratum", "n_configs", "mean_technicians",
                                 "u_mean", "u_median", "u_max",
                                 "share_u_over_one"]))
        if spec["check"] == "capacity":
            A("\nRealized utilization per estimator quantile and stratum "
              "(`capacity_utilization.csv`):\n")
            A(_md_table(caputil, ["arm", "stratum", "n_configs", "u_mean",
                                  "u_median", "u_p25", "u_p75", "u_max",
                                  "share_u_over_one", "u_shift_mean",
                                  "u_shift_median"]))
            A("\nRealized vs nominal crew multipliers, portfolio "
              "(`capacity_multipliers.csv`); rounding a per-trade crew to a whole "
              "technician is what separates the two.\n")
            A(_md_table(capmult[capmult["scope"] == "portfolio"],
                        ["m", "crew_nominal", "crew_realized",
                         "realized_multiplier"]))
        if spec["check"] == "backdate":
            A("\nHow much of the synthetic shift the instances absorb "
              "(`backdate_clamp.csv`): a shifted release is clamped at the start "
              "of the scheduling window, so a clamped order keeps its original "
              "release.\n")
            A(_md_table(clamp, ["stratum", "n_configs", "n_corrective",
                                "clamped_total", "clamped_mean", "clamped_median",
                                "clamped_min", "clamped_max",
                                "clamp_share_corrective_pooled",
                                "delta_bh_mean", "delta_bh_max"]))

        A("\n### Stability against the %s arm\n"
          % ARM_LABEL[(spec["check"], spec["baseline"])])
        s = stab[stab["check"] == spec["check"]]
        A(_md_table(s, ["arm", "stratum", "n_configs", "n_anchors", "best_method",
                        "best_mean", "spread_pct", "margin_pct_of_best",
                        "tau_method", "tau_family", "set_size",
                        "baseline_set_size", "set_jaccard", "left_set",
                        "entered_set", "n_policy_seeds_in_set", "top3_families",
                        "top3_is_leading_trio"]))
        A("\nFamily means (mean of the member methods' means) and the family "
          "order they imply:\n")
        f = fam[fam["check"] == spec["check"]]
        A(_md_table(f, ["arm", "stratum"] + ["mean_" + x for x in FAMILY_ORDER]
                    + ["family_order"]))

        A("\nPer-arm method table (rules in bold positions, policy seeds "
          "ranked individually):\n")
        for arm in spec["arms"]:
            for stratum in STRATA:
                e = eq[(eq["check"] == spec["check"]) & (eq["arm"] == arm)
                       & (eq["stratum"] == stratum)]
                if e.empty:
                    continue
                members = list(e.loc[e["in_equivalence_set"] == 1, "method"])
                A("\n**%s / %s** (%s) - best %s (mean %s), %d configurations. "
                  "Equivalence set: %d of %d methods.\n"
                  % (arm, stratum, ARM_LABEL[(spec["check"], arm)],
                     e["best_method"].iloc[0], _fmt(e["mean_best"].iloc[0]),
                     int(e["n_configs"].max()), len(members),
                     int(e["method"].nunique())))
                A(_md_table(e, ["rank", "method", "family", "mean",
                                "pct_from_best", "abs_from_best", "mean_diff",
                                "ci_lo", "ci_hi", "margin", "verdict",
                                "in_equivalence_set"]))

    A("\n## R4.8 addendum: equivalence sets read against realized utilization\n")
    A("The three crew sizings are the same weeks under three estimators, so "
      "pooling their configurations and binning them on REALIZED utilization is "
      "the reading R4.8 prescribes. Verdict campuses only; the cluster bootstrap "
      "resamples base instances, so the three configurations of one week count "
      "as one observation.\n")
    for b, sub in capubin.groupby("u_bin", sort=False):
        members = list(sub.loc[sub["in_equivalence_set"] == 1, "method"])
        A("\n**u_bin %s** (realized u in [%.2f, %.2f], %d configurations over %d "
          "base instances) - best %s, set of %d.\n"
          % (b, sub["u_lo"].iloc[0], sub["u_hi"].iloc[0],
             int(sub["n_configs_bin"].iloc[0]), int(sub["n_anchors_bin"].iloc[0]),
             sub["best_method"].iloc[0], len(members)))
        A(_md_table(sub[sub["method"].isin(RULES)],
                    ["rank", "method", "mean", "pct_from_best", "mean_diff",
                     "ci_lo", "ci_hi", "margin", "verdict",
                     "in_equivalence_set"]))

    A("\n## Every method against the baseline arm's best method\n")
    A("The reference of each row is the method with the lowest mean on the "
      "BASELINE arm of that stratum, held fixed while the arm changes; this is "
      "the comparison that says whether the baseline's choice survives.\n")
    A(_md_table(cmp_[cmp_["method"].isin(RULES)],
                ["check", "arm", "stratum", "method", "reference", "n_configs",
                 "mean_method", "mean_ref", "mean_diff", "ci_lo", "ci_hi",
                 "margin", "holm_p", "verdict"]))

    A("\n## Sanity checks\n")
    A(_md_table(pd.DataFrame(checksums), ["check", "got", "want", "ok"]))
    (out / "analysis.md").write_text("\n".join(L))


# --------------------------------------------------------------------------- #
# Macros (paper/macros_r4b.tex).
# --------------------------------------------------------------------------- #
class RobustMacroFile(MacroFile):
    """MacroFile that names WHICH existing file a colliding macro came from."""

    def __init__(self, sources: dict):
        self.source_of = {n: p for p, names in sources.items() for n in names}
        super().__init__(set(self.source_of))

    def add(self, name, value, source):
        if name in self.source_of:
            raise SystemExit("macro %r is already defined in %s"
                             % (name, self.source_of[name]))
        super().add(name, value, source)


ARM_TOKEN = {
    ("pmodel", "sum"): "Sum", ("pmodel", "max"): "Max",
    ("pmodel", "single"): "Single",
    ("capacity", "q0.95"): "Qninetyfive", ("capacity", "q0.90"): "Qninety",
    ("capacity", "q0.75"): "Qseventyfive",
    ("backdate", "baseline"): "Base", ("backdate", "backdate"): "Shift",
    ("sla", "baseline"): "Base", ("sla", "emg"): "Emg", ("sla", "rtn"): "Rtn",
    ("sla", "pmp3"): "Pmpthree",
}
STRATUM_TOKEN = {"verdict": "", "campus1": "CampOne", "campus2": "CampTwo"}
BIN_TOKEN = {"<0.5": "Slack", "0.5-0.8": "Moderate", "0.8-1.0": "Tight",
             "1.0-1.2": "Over", ">=1.2": "Deep"}
M_TOKEN = {0.5: "Mhalf", 0.6: "Msixty", 0.8: "Meighty", 1.0: "Mfull",
           1.25: "Mquarter"}


def f_tau(x) -> str:
    return "%.2f" % float(x)


def f_u(x) -> str:
    return "%.2f" % float(x)


def f_share(x) -> str:
    """A share written as a percentage, no decimals below 100."""
    return "%.0f" % (100.0 * float(x))


def build_macros(out: Path, paper_dir: Path) -> tuple:
    """Read this run's CSVs back from disk and write paper/macros_r4b.tex."""
    dataset = pd.read_csv(out / "dataset.csv")
    eq = pd.read_csv(out / "equivalence.csv")
    stab = pd.read_csv(out / "stability.csv")
    fam = pd.read_csv(out / "family_means.csv")
    calib = pd.read_csv(out / "pmodel_calibration.csv")
    caputil = pd.read_csv(out / "capacity_utilization.csv")
    capubin = pd.read_csv(out / "capacity_ubin.csv")
    capmult = pd.read_csv(out / "capacity_multipliers.csv")
    clamp = pd.read_csv(out / "backdate_clamp.csv")
    headline = json.loads((out / "headline_robust.json").read_text())

    mf = RobustMacroFile({
        "paper/macros.tex": existing_macro_names(paper_dir / "macros.tex"),
        "paper/macros_r4.tex": existing_macro_names(paper_dir / "macros_r4.tex"),
    })

    def S(check, arm, stratum):
        return _row(stab, check=check, arm=arm, stratum=stratum)

    def E(check, arm, stratum, method):
        return _row(eq, check=check, arm=arm, stratum=stratum, method=method)

    # ---- 0. the shared scope ------------------------------------------- #
    mf.section("Robustness scope: the Eval-B anchors every check transforms "
               "(analysis/dataset.csv, analysis/stability.csv)")
    d0 = dataset[dataset["check"] == "evalb_anchors"].iloc[0]
    for name, field in (("rfbAnchors", "n_configs"),
                        ("rfbAnchorsVerdict", "n_verdict"),
                        ("rfbAnchorsCampTwo", "n_campus2")):
        mf.add(name, f_int(d0[field]),
               "dataset.csv check=evalb_anchors field=%s" % field)
    mf.add("rfbMethods", f_int(len(SCORED)),
           "scripts/r4_robust_analysis.py SCORED (rules and policy seeds run on "
           "every configuration of every arm, each seed ranked individually)")
    mf.add("rfbRobustConfigs",
           f_int(dataset[dataset["check"] != "evalb_anchors"]["n_configs"].sum()),
           "dataset.csv field=n_configs summed over the four robustness checks")
    base = S("sla", "baseline", "verdict")
    mf.add("rfbBaseSetSize", f_int(base["set_size"]),
           "stability.csv check=sla arm=baseline stratum=verdict field=set_size "
           "(the Eval-B anchors' own equivalence set)")
    mf.add("rfbBaseSpread", f_pct(base["spread_pct"]),
           "stability.csv check=sla arm=baseline stratum=verdict field=spread_pct "
           "(worst mean over best mean across the scored methods)")
    mf.add("rfbBaseMargin", f_pct(base["margin_pct_of_best"]),
           "stability.csv check=sla arm=baseline stratum=verdict "
           "field=margin_pct_of_best (equivalence margin as a share of the best mean)")

    # ---- 1. R4.7 calibration cascade ------------------------------------ #
    mf.section("R4.7 processing-time models: the calibration cascade and what it "
               "holds fixed (analysis/pmodel_calibration.csv, "
               "analysis/pmodel_utilization.csv)")
    port = calib[calib["scope"] == "all"].set_index("p_model")
    pu = pd.read_csv(out / "pmodel_utilization.csv")
    for arm in ("sum", "max", "single"):
        tok = ARM_TOKEN[("pmodel", arm)]
        src = "pmodel_calibration.csv scope=all p_model=%s" % arm
        mf.add("rfbPcap" + tok, "%.1f" % float(port.loc[arm, "r4_labor_cap_hours"]),
               src + " field=r4_labor_cap_hours (per-order labor cap, hours)")
        mf.add("rfbPtech" + tok, f_int(port.loc[arm, "total_technicians"]),
               src + " field=total_technicians (portfolio crew after recalibration)")
        mf.add("rfbPmeanp" + tok, "%.2f" % float(port.loc[arm, "mean_p_bh"]),
               src + " field=mean_p_bh (mean processing time, business hours)")
        r = _row(pu, arm=arm, stratum="verdict")
        mf.add("rfbPu" + tok, f_u(r["u_mean"]),
               "pmodel_utilization.csv arm=%s stratum=verdict field=u_mean "
               "(what the recalibration holds comparable)" % arm)
    mf.add("rfbPskipped", f_int(headline["pmodel"]["anchors_skipped_single"]),
           "headline_robust.json pmodel.anchors_skipped_single (anchors with no "
           "single-line order)")

    # ---- 2. R4.7 stability ---------------------------------------------- #
    mf.section("R4.7 stability of the ranking and of the equivalence set "
               "(analysis/stability.csv, analysis/equivalence.csv, check=pmodel; "
               "the summed-line arm is the comparator and reproduces Eval-B exactly)")
    for arm in ("sum", "max", "single"):
        tok = ARM_TOKEN[("pmodel", arm)]
        r = S("pmodel", arm, "verdict")
        src = "stability.csv check=pmodel arm=%s stratum=verdict" % arm
        mf.add("rfbPset" + tok, f_int(r["set_size"]), src + " field=set_size")
        mf.add("rfbPmean" + tok, f_twt(r["best_mean"]),
               src + " field=best_mean (lowest mean weighted tardiness in the scope)")
        if arm != "sum":
            mf.add("rfbPtau" + tok, f_tau(r["tau_method"]),
                   src + " field=tau_method (Kendall tau-b against the summed-line arm)")
            mf.add("rfbPbest" + tok, f_text(display_name(r["best_method"])),
                   src + " field=best_method (prose phrase)")
            if arm == "single":
                mf.add("rfbPspread" + tok, f_pct(r["spread_pct"]),
                       src + " field=spread_pct (worst mean over best mean)")
            for meth, mtok in (("edd", "Edd"), ("wmdd", "Wmdd")):
                e = E("pmodel", arm, "verdict", meth)
                mf.add("rfbP%sGap%s" % (mtok, tok), f_pct(e["pct_from_best"]),
                       "equivalence.csv check=pmodel arm=%s stratum=verdict "
                       "method=%s field=pct_from_best" % (arm, meth))

    # ---- 3. R4.8 capacity estimator ------------------------------------- #
    mf.section("R4.8 capacity estimator: crew, realized utilization and the "
               "leading set (analysis/capacity_utilization.csv, "
               "analysis/stability.csv, analysis/equivalence.csv)")
    tech = headline["capacity"]["total_technicians"]
    for q, key in (("q0.95", "0.95"), ("q0.90", "0.9"), ("q0.75", "0.75")):
        tok = ARM_TOKEN[("capacity", q)]
        mf.add("rfbCtech" + tok, f_int(tech[key]),
               "headline_robust.json capacity.total_technicians[%s] "
               "(results/r4_robustness/capacity/meta.json)" % key)
        u = _row(caputil, arm=q, stratum="verdict")
        usrc = "capacity_utilization.csv arm=%s stratum=verdict" % q
        mf.add("rfbCumean" + tok, f_u(u["u_mean"]), usrc + " field=u_mean")
        mf.add("rfbCover" + tok, f_share(u["share_u_over_one"]),
               usrc + " field=share_u_over_one (percentage of configurations at "
                      "realized utilization at or above one)")
        if q != "q0.95":
            mf.add("rfbCushift" + tok, f_u(u["u_shift_mean"]),
                   usrc + " field=u_shift_mean (mean rise over the Eval-B arm)")
        r = S("capacity", q, "verdict")
        ssrc = "stability.csv check=capacity arm=%s stratum=verdict" % q
        mf.add("rfbCset" + tok, f_int(r["set_size"]), ssrc + " field=set_size")
        e = E("capacity", q, "verdict", "edd")
        esrc = "equivalence.csv check=capacity arm=%s stratum=verdict" % q
        mf.add("rfbCeddGap" + tok, f_pct(e["pct_from_best"]),
               esrc + " method=edd field=pct_from_best")
        mf.add("rfbCeddSet" + tok,
               f_text("in" if int(e["in_equivalence_set"]) else "out"),
               esrc + " method=edd field=in_equivalence_set")
        if q != "q0.90":
            # Campus 2 is already overloaded at the default estimator, so the same
            # transition is visible there without changing the estimator at all.
            e2 = E("capacity", q, "campus2", "edd")
            mf.add("rfbCeddGapCampTwo" + tok, f_pct(e2["pct_from_best"]),
                   "equivalence.csv check=capacity arm=%s stratum=campus2 "
                   "method=edd field=pct_from_best" % q)
    # The transition itself: at the loosest estimator the plain due-date rule
    # leaves the leading set and the weighted due-date rules stay in it.
    tok = ARM_TOKEN[("capacity", "q0.75")]
    for meth, mtok in (("wmdd", "Wmdd"), ("atc", "Atc")):
        e = E("capacity", "q0.75", "verdict", meth)
        esrc = ("equivalence.csv check=capacity arm=q0.75 stratum=verdict "
                "method=%s" % meth)
        mf.add("rfbC%sGap%s" % (mtok, tok), f_pct(e["pct_from_best"]),
               esrc + " field=pct_from_best")
        mf.add("rfbC%sSet%s" % (mtok, tok),
               f_text("in" if int(e["in_equivalence_set"]) else "out"),
               esrc + " field=in_equivalence_set")
    for q in ("q0.95", "q0.75"):
        r = S("capacity", q, "verdict")
        mf.add("rfbCpol" + ARM_TOKEN[("capacity", q)],
               f_int(r["n_policy_seeds_in_set"]),
               "stability.csv check=capacity arm=%s stratum=verdict "
               "field=n_policy_seeds_in_set" % q)
    mf.section("R4.8 realized vs nominal crew multipliers, portfolio "
               "(analysis/capacity_multipliers.csv); rounding a per-trade crew to "
               "a whole technician is what separates the two")
    for m in (0.8, 0.6, 0.5):
        r = _row(capmult[capmult["scope"] == "portfolio"], m=m)
        mf.add("rfbCrealized" + M_TOKEN[m], "%.3f" % float(r["realized_multiplier"]),
               "capacity_multipliers.csv scope=portfolio m=%s "
               "field=realized_multiplier" % m)
    mf.section("R4.8 addendum: the leading set read against realized utilization, "
               "three estimator arms pooled (analysis/capacity_ubin.csv)")
    for b, tok in (("<0.5", "Slack"), (">=1.2", "Deep")):
        sub = capubin[capubin["u_bin"] == b]
        if sub.empty:
            continue
        members = list(sub.loc[sub["in_equivalence_set"] == 1, "method"])
        src = "capacity_ubin.csv u_bin=%s" % b
        mf.add("rfbCbin%sSet" % tok, f_int(len(members)),
               src + " field=in_equivalence_set")
        for meth, mtok in (("edd", "Edd"), ("atc", "Atc")):
            e = _row(sub, method=meth)
            mf.add("rfbCbin%s%sGap" % (tok, mtok), f_pct(e["pct_from_best"]),
                   src + " method=%s field=pct_from_best" % meth)

    # ---- 4. R4.9 backdated releases -------------------------------------- #
    mf.section("R4.9 backdated releases (analysis/backdate_clamp.csv, "
               "analysis/stability.csv check=backdate)")
    cl = _row(clamp, stratum="verdict")
    csrc = "backdate_clamp.csv stratum=verdict"
    mf.add("rfbBcorrShare", f_share(cl["corrective_share_mean"]),
           csrc + " field=corrective_share_mean (corrective share of an instance)")
    mf.add("rfbBdelta", "%.1f" % float(cl["delta_bh_mean"]),
           csrc + " field=delta_bh_mean (mean shift applied, business hours)")
    mf.add("rfbBclampShare", f_share(cl["clamp_share_corrective_pooled"]),
           csrc + " field=clamp_share_corrective_pooled (corrective orders whose "
                  "shifted release clamps at the window start)")
    mf.add("rfbBclampMean", "%.0f" % float(cl["clamped_mean"]),
           csrc + " field=clamped_mean (clamped orders per instance)")
    mf.add("rfbBclampMax", f_int(cl["clamped_max"]), csrc + " field=clamped_max")
    r = S("backdate", "backdate", "verdict")
    src = "stability.csv check=backdate arm=backdate stratum=verdict"
    mf.add("rfbBtau", f_tau(r["tau_method"]),
           src + " field=tau_method (Kendall tau-b against the Eval-B anchors)")
    mf.add("rfbBjac", "%.2f" % float(r["set_jaccard"]), src + " field=set_jaccard")
    mf.add("rfbBset", f_int(r["set_size"]), src + " field=set_size")
    mf.add("rfbBjacCampTwo",
           "%.2f" % float(S("backdate", "backdate", "campus2")["set_jaccard"]),
           "stability.csv check=backdate arm=backdate stratum=campus2 "
           "field=set_jaccard")

    # ---- 5. R4.10 service-window and priority scenarios ------------------ #
    mf.section("R4.10 service-window and priority scenarios "
               "(analysis/stability.csv check=sla, stratum=verdict)")
    for arm in ("emg", "rtn", "pmp3"):
        tok = ARM_TOKEN[("sla", arm)]
        r = S("sla", arm, "verdict")
        src = "stability.csv check=sla arm=%s stratum=verdict" % arm
        mf.add("rfbStau" + tok, f_tau(r["tau_method"]), src + " field=tau_method")
        mf.add("rfbSjac" + tok, "%.2f" % float(r["set_jaccard"]),
               src + " field=set_jaccard")
        mf.add("rfbSset" + tok, f_int(r["set_size"]), src + " field=set_size")

    # ---- 6. cross-cutting verdict ---------------------------------------- #
    mf.section("Cross-cutting robustness summary (analysis/stability.csv; "
               "\"scenario\" scopes are the R4.9 and R4.10 arms, which change the "
               "due dates or the release times and leave the work and the crew "
               "untouched)")
    summ = headline["summary"]
    mf.add("rfbScenScopes", f_int(summ["n_scenario_scopes"]),
           "headline_robust.json summary.n_scenario_scopes")
    mf.add("rfbJacMin", "%.2f" % summ["jaccard_min"],
           "headline_robust.json summary.jaccard_min")
    mf.add("rfbJacMedian", "%.2f" % summ["jaccard_median"],
           "headline_robust.json summary.jaccard_median")
    mf.add("rfbTauMin", f_tau(summ["tau_method_min"]),
           "headline_robust.json summary.tau_method_min")
    mf.add("rfbTauMax", f_tau(summ["tau_method_max"]),
           "headline_robust.json summary.tau_method_max")
    mf.add("rfbLeavers", f_text(", ".join(display_name(m) for m
                                          in summ["verdict_set_leavers"])),
           "headline_robust.json summary.verdict_set_leavers (every method that "
           "leaves the equivalence set in any scenario arm, verdict campuses)")
    mf.add("rfbTrioArms", f_int(summ["n_verdict_arms_leading_trio"]),
           "headline_robust.json summary.n_verdict_arms_leading_trio")
    mf.add("rfbTrioArmsTotal", f_int(summ["n_verdict_arms"]),
           "headline_robust.json summary.n_verdict_arms (every transformed arm of "
           "the four checks, verdict campuses)")

    header = "\n".join([
        "% macros_r4b.tex -- R4 robustness (R4.7-R4.10) numbers.",
        "% GENERATED FILE. Do not edit by hand: rebuild with",
        "%   PYTHONPATH=src python scripts/r4_robust_analysis.py",
        "% Every value below is transcribed by that script from a CSV in",
        "% results/r4_robustness/analysis/ produced in the same run; the trailing",
        "% comment names the file and the field it came from.",
        "%% Generated %s from results/r4_robustness/{pmodel,capacity,backdate,sla}."
        % datetime.now().strftime("%Y-%m-%d %H:%M"),
        "% Companion file: macros_r4.tex (Eval-B). No name is shared with it or",
        "% with macros.tex; a collision is a hard error in the generator.",
        "% Sign convention: a negative paired difference means the method is",
        "% better than its comparator (weighted tardiness is minimised).",
    ])
    (paper_dir / "macros_r4b.tex").write_text(mf.render(header))
    return len(mf.names), sorted(mf.names)


# --------------------------------------------------------------------------- #
# R4.7 utilization side table (small, but a macro reads it).
# --------------------------------------------------------------------------- #
def pmodel_utilization_block(checks_raw: dict) -> pd.DataFrame:
    """Realized utilization per processing-time model and stratum.

    The three models change the amount of work per order, so without this table
    a reader cannot tell whether a change in weighted tardiness is the
    aggregation choice or a change of contention regime.
    """
    pm = checks_raw["pmodel"].drop_duplicates("id")
    rows = []
    for arm in ("sum", "max", "single"):
        for stratum in STRATA:
            sub = stratum_frame(pm[pm["arm"] == arm], stratum)
            u = sub["u_realized"].to_numpy(dtype=float)
            rows.append({"arm": arm, "stratum": stratum, "n_configs": int(len(sub)),
                         "u_mean": float(u.mean()), "u_median": float(np.median(u)),
                         "u_min": float(u.min()), "u_max": float(u.max()),
                         "share_u_over_one": float((u >= 1.0).mean()),
                         "mean_technicians": float(sub["n_technicians"].mean())})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# LaTeX compile check.
# --------------------------------------------------------------------------- #
def check_latex(paper_dir: Path, name: str = "macros_r4b") -> str:
    """Compile a throwaway document that inputs the macro file and uses every macro."""
    import re
    src = (paper_dir / (name + ".tex")).read_text()
    names = re.findall(r"\\newcommand\{\\([A-Za-z]+)\}", src)
    env = dict(os.environ)
    env["PATH"] = str(Path.home() / ".TinyTeX/bin/x86_64-linux") + os.pathsep + env["PATH"]
    if shutil.which("pdflatex", path=env["PATH"]) is None:
        return "pdflatex not found on PATH; compile check skipped"
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        shutil.copy(paper_dir / (name + ".tex"), td / (name + ".tex"))
        body = "\n".join(r"\noindent\texttt{%s}: \%s\par" % (n, n) for n in names)
        (td / "test.tex").write_text(
            "\\documentclass[10pt]{article}\n"
            "\\usepackage[margin=1in]{geometry}\n"
            "\\input{%s}\n"
            "\\begin{document}\n%s\n\\end{document}\n" % (name, body))
        p = subprocess.run(["pdflatex", "-interaction=nonstopmode",
                            "-halt-on-error", "test.tex"],
                           cwd=td, env=env, capture_output=True, text=True)
        if p.returncode != 0:
            tail = "\n".join(p.stdout.strip().splitlines()[-25:])
            return "FAILED (exit %d)\n%s" % (p.returncode, tail)
        pdf = td / "test.pdf"
        return ("OK: %d macros compiled, %d bytes of PDF"
                % (len(names), pdf.stat().st_size if pdf.exists() else 0))


# --------------------------------------------------------------------------- #
# Main.
# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--evalb", default=str(ROOT / "results/r4_final/results.csv"))
    ap.add_argument("--out", default=str(ROOT / "results/r4_robustness/analysis"))
    ap.add_argument("--paper-dir", default=str(ROOT / "paper"))
    ap.add_argument("--step", choices=("all", "analysis", "macros"), default="all")
    ap.add_argument("--n-boot", type=int, default=stats.N_BOOT)
    ap.add_argument("--seed", type=int, default=stats.SEED)
    ap.add_argument("--check-latex", action="store_true",
                    help="compile a scratch document that uses every macro")
    args = ap.parse_args()

    root = Path(args.root)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    paper_dir = Path(args.paper_dir)
    t0 = datetime.now()

    if args.step in ("all", "analysis"):
        evalb = load_evalb(Path(args.evalb))
        checks_raw = {s["check"]: load_check(s, root) for s in CHECKS}
        metas = {s["check"]: json.loads(
            (root / "results/r4_robustness" / s["dir"] / "meta.json").read_text())
            for s in CHECKS}

        dataset = dataset_block(checks_raw, metas, evalb)
        checksums = sanity_checks(checks_raw, metas, evalb, dataset)
        print("sanity: %d checks passed" % len(checksums))

        frames = build_frames(checks_raw, evalb)
        eq, fam, stab, cmp_ = analysis_blocks(frames, evalb, args.n_boot, args.seed)
        print("equivalence: %d rows over %d scopes" % (len(eq), len(stab)))
        calib = pmodel_calibration_block(root)
        pmutil = pmodel_utilization_block(checks_raw)
        caputil = capacity_utilization_block(frames, checks_raw)
        capubin = capacity_ubin_block(frames, checks_raw, args.n_boot, args.seed)
        capmult = capacity_multipliers_block(root)
        clamp = backdate_clamp_block(checks_raw)
        print("capacity u-bins: %d" % capubin["u_bin"].nunique())

        dataset.to_csv(out / "dataset.csv", index=False)
        eq.to_csv(out / "equivalence.csv", index=False)
        fam.to_csv(out / "family_means.csv", index=False)
        stab.to_csv(out / "stability.csv", index=False)
        cmp_.to_csv(out / "vs_baseline_best.csv", index=False)
        calib.to_csv(out / "pmodel_calibration.csv", index=False)
        pmutil.to_csv(out / "pmodel_utilization.csv", index=False)
        caputil.to_csv(out / "capacity_utilization.csv", index=False)
        capubin.to_csv(out / "capacity_ubin.csv", index=False)
        capmult.to_csv(out / "capacity_multipliers.csv", index=False)
        clamp.to_csv(out / "backdate_clamp.csv", index=False)

        headline = build_headline(dataset, eq, fam, stab, cmp_, calib, caputil,
                                  capubin, capmult, clamp, metas)
        headline["pmodel"]["utilization"] = {
            "%s|%s" % (r.arm, r.stratum): {"u_mean": float(r.u_mean),
                                           "u_median": float(r.u_median),
                                           "share_u_over_one": float(r.share_u_over_one),
                                           "mean_technicians": float(r.mean_technicians)}
            for r in pmutil.itertuples()}
        (out / "headline_robust.json").write_text(
            json.dumps(headline, indent=2, sort_keys=True) + "\n")
        write_report(out, dataset, eq, fam, stab, cmp_, calib, pmutil, caputil,
                     capubin, capmult, clamp, checksums, args.n_boot, args.seed)
        (out / "meta.json").write_text(json.dumps({
            "script": "scripts/r4_robust_analysis.py",
            "generated": t0.isoformat(timespec="seconds"),
            "elapsed_seconds": (datetime.now() - t0).total_seconds(),
            "inputs": {s["check"]: "results/r4_robustness/%s/results.csv" % s["dir"]
                       for s in CHECKS} | {"evalb_anchors": str(args.evalb)},
            "value_col": VALUE_COL, "n_boot": args.n_boot, "seed": args.seed,
            "alpha": stats.ALPHA, "margin_abs": stats.MARGIN_ABS,
            "margin_rel": stats.MARGIN_REL,
            "verdict_campuses": list(VERDICT_CAMPUSES),
            "scored_methods": list(SCORED),
            "families": {f: [m for m in SCORED if FAMILY_OF[m] == f]
                         for f in FAMILY_ORDER},
            "rank_correlation": "scipy.stats.kendalltau (tau-b)",
            "sanity_checks": checksums,
        }, indent=2) + "\n")
        print("analysis written to %s (%.1f s)"
              % (out, (datetime.now() - t0).total_seconds()))

    if args.step in ("all", "macros"):
        n, names = build_macros(out, paper_dir)
        print("macros: %d written to %s" % (n, paper_dir / "macros_r4b.tex"))

    if args.check_latex:
        print("latex check: %s" % check_latex(paper_dir))


if __name__ == "__main__":
    main()
