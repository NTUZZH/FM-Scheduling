#!/usr/bin/env python
"""Definitive Eval-B analysis: results/r4_final/results.csv -> manuscript exhibits.

This is the paper's evidence layer for Eval-B.  ``scripts/r4_stats.py`` is a
generic driver that scopes any results.csv three ways; this script encodes the
scopes the manuscript actually reports, the coverage discipline the first read
demanded, and the macro file the manuscript inputs.  It supersedes
``results/r4_final/stats/`` for every Eval-B claim.

The four decisions that separate this analysis from the generic driver
(docs/protocol.md §R4.5):

* **Regimes are never pooled.**  A realized-utilization bin is computed inside
  one regime, because a 0.9-utilization empirical week (a few hundred orders)
  and a 0.9-utilization generator cell (a few thousand) are different objects
  and their pooled mean is a composition artifact.
* **Verdict campuses only for the verdict.**  Campuses 5, 9, 10 and 12 carry
  the three crew multipliers; campus 1 (transfer) and campus 2 (a nonstationary
  overload) are reported separately and never enter a verdict scope.
* **Equivalence sets are ranked among FULL-COVERAGE methods only.**  Rolling
  CP-SAT runs on 8 configurations per cell, so its mean is taken over a
  different set of configurations and its rank against methods run on every
  configuration means nothing.  It is reported through its own paired rows
  against EDD, ATC and WMDD, with the subsample size disclosed on every row.
* **The learned pool is reported as a pool.**  The manuscript claim is about
  ten independently trained seeds, so every scope reports the pooled mean, the
  ten per-seed means, and how many of the ten individually fall inside the
  scope's equivalence set.

All statistics come from ``fmwos.stats`` (protocol §R4.5): paired on the
instance-configuration id, 95% percentile bootstrap over base-instance clusters
with 10000 resamples and master seed 12345, equivalence margin
max(1.0, 1% of the comparator mean), Holm within a comparison family.  Nothing
statistical is reimplemented here.

Outputs (all under --out, default results/r4_final/analysis/)
------------------------------------------------------------
  dataset.csv           row/configuration/cluster counts, cross-checked vs meta.json
  equivalence.csv       per scope, every full-coverage method vs the scope best
  comparisons.csv       per scope, every method (incl. rolling) vs EDD/ATC/WMDD
  pools.csv             per scope, the seed-averaged pools vs best/EDD/ATC/WMDD
  generator_ratios.csv  per u_target, deterioration ratios vs the scope best
  campus2_utilization.csv  the stress campus's realized-utilization profile
  latency.csv           per-decision ms and per-replan s by method family
  seed_dispersion.csv   per scope, per-seed spread of each learned pool
  headline.json         every number the manuscript cites, machine-readable
  analysis.md           the readable report (one section per block)
  meta.json             inputs, constants, timings, sanity-check outcomes

Usage
-----
    PYTHONPATH=src python scripts/r4_analysis.py                   # analysis + macros
    PYTHONPATH=src python scripts/r4_analysis.py --step analysis   # analysis only
    PYTHONPATH=src python scripts/r4_analysis.py --step macros     # macros from CSVs
    PYTHONPATH=src python scripts/r4_analysis.py --check-latex     # + compile test

Re-running is idempotent: every output is rewritten from the same inputs with
the same seeds, so a second run reproduces every digit.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from fmwos import stats                                    # noqa: E402
from fmwos.io import normalize_method_column               # noqa: E402

# --------------------------------------------------------------------------- #
# Fixed vocabulary of the Eval-B run (results/r4_final/meta.json).
# --------------------------------------------------------------------------- #
VERDICT_CAMPUSES = (5, 9, 10, 12)
TRANSFER_CAMPUS = 1
STRESS_CAMPUS = 2
CREW_MULTIPLIERS = (1.0, 0.8, 0.6)
U_TARGETS = (0.7, 0.9, 1.0, 1.1, 1.3)

RULES = ("edd", "pfifo", "wspt", "atc", "wmdd", "lpt", "random")
REFERENCES = ("edd", "atc", "wmdd")
ROLLING = "rollcp2"
V2_MLP = tuple("v2rl%d" % s for s in range(301, 311))
V2_ATTN = tuple("v2at%d" % s for s in range(301, 311))
V1_MLP = ("rl301", "rl302", "rl303")
FULL_COVERAGE = RULES + V1_MLP + V2_MLP + V2_ATTN     # everything except rolling
POOL_V2 = "v2pool"          # seed-averaged v2 MLP pool (pseudo-method)
POOL_ATTN = "v2attnpool"    # seed-averaged v2 attention pool (pseudo-method)
POOLS = (POOL_V2, POOL_ATTN)

VALUE_COL = "wwt"

# Display names for the set-membership sentences written into the macros.  A
# checkpoint id is an internal code name, so prose gets the phrase and tables
# get the raw id (both are emitted, as \rfempBest... and \rfempBestId...).
DISPLAY = {"edd": "EDD", "pfifo": "pFIFO", "wspt": "WSPT", "atc": "ATC",
           "wmdd": "WMDD", "lpt": "LPT", "random": "random",
           ROLLING: "rolling CP-SAT", POOL_V2: "the policy pool",
           POOL_ATTN: "the attention pool"}
NUMERAL = ("no", "one", "two", "three", "four", "five", "six", "seven",
           "eight", "nine", "ten")


def display_name(m: str) -> str:
    if m in DISPLAY:
        return DISPLAY[m]
    if m in V2_MLP:
        return "a policy seed"
    if m in V2_ATTN:
        return "an attention-scorer seed"
    if m in V1_MLP:
        return "a curriculum-v1 policy seed"
    return m

# Method-family labels for the latency table.
FAMILY_RULES = "rules"
FAMILY_V1 = "v1_mlp"
FAMILY_V2 = "v2_mlp"
FAMILY_ATTN = "v2_attn"
FAMILY_ROLL = "rolling"


def method_family(m: str) -> str:
    if m in RULES:
        return FAMILY_RULES
    if m == ROLLING:
        return FAMILY_ROLL
    if m in V2_MLP:
        return FAMILY_V2
    if m in V2_ATTN:
        return FAMILY_ATTN
    if m in V1_MLP:
        return FAMILY_V1
    return "other"


# --------------------------------------------------------------------------- #
# Loading and scoping.
# --------------------------------------------------------------------------- #
def load_results(csv: Path) -> pd.DataFrame:
    df = pd.read_csv(csv)
    df = normalize_method_column(df)
    df["method"] = df["method"].astype(str)
    df["campus"] = df["campus"].astype(int)
    df["crew_multiplier"] = df["crew_multiplier"].astype(float)
    stats.add_base_instance_id(df)
    stats.add_utilization_bin(df)
    return df


def add_pool_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Append seed-averaged pseudo-method rows for the two learned pools.

    A pool row is the mean of its seeds' values on the SAME configuration, so
    pairing it against a rule is the "ten seeds on average" comparison the
    manuscript makes; it is never allowed into an equivalence-set ranking,
    because it is an aggregate rather than a deployable method.
    """
    meta_cols = ["campus", "track", "split", "size", "regime", "crew_multiplier",
                 "u_target", "u_realized", "u_bin", "cluster", "eval_set"]
    out = [df]
    for pool, seeds in ((POOL_V2, V2_MLP), (POOL_ATTN, V2_ATTN)):
        sub = df[df["method"].isin(seeds)]
        if sub.empty:
            continue
        n_seeds = sub.groupby("id")["method"].nunique()
        if n_seeds.nunique() != 1:
            raise SystemExit("pool %s: uneven seed coverage per configuration" % pool)
        agg = sub.groupby("id", sort=True).agg(
            **{VALUE_COL: (VALUE_COL, "mean"),
               "mean_ms_per_decision": ("mean_ms_per_decision", "mean")})
        first = sub.drop_duplicates("id").set_index("id")[meta_cols]
        rows = first.join(agg).reset_index()
        rows["method"] = pool
        rows["feasible"] = 1
        out.append(rows)
    return pd.concat(out, ignore_index=True, sort=False)


def scope_frames(df: pd.DataFrame):
    """Yield ``(scope_type, scope, subframe)`` for every reported scope.

    Scopes are enumerated in report order and each one is a single regime, so
    no bin ever mixes an empirical week with a generator cell.
    """
    emp = df[(df["regime"] == "final-empirical")
             & (df["campus"].isin(VERDICT_CAMPUSES))]
    gen = df[df["regime"] == "final-gen"]

    for m in CREW_MULTIPLIERS:                                   # block 1a
        yield "emp_m", "m=%s" % m, emp[emp["crew_multiplier"] == m]
    for b in stats.U_BIN_ORDER:                                  # block 1b
        sub = emp[emp["u_bin"] == b]
        if not sub.empty:
            yield "emp_ubin", "u_bin=%s" % b, sub
    for m in CREW_MULTIPLIERS:                                   # block 1c
        for b in stats.U_BIN_ORDER:
            sub = emp[(emp["crew_multiplier"] == m) & (emp["u_bin"] == b)]
            if not sub.empty:
                yield "emp_m_ubin", "m=%s|u_bin=%s" % (m, b), sub
    yield "gen_all", "ALL", gen                                  # block 2
    for u in U_TARGETS:
        sub = gen[gen["u_target"] == u]
        if not sub.empty:
            yield "gen_utarget", "u_target=%s" % u, sub
    tr = df[(df["regime"] == "final-empirical")                  # block 3
            & (df["campus"] == TRANSFER_CAMPUS)
            & (df["crew_multiplier"] == 1.0)]
    if not tr.empty:
        yield "transfer", "campus=%d|m=1.0" % TRANSFER_CAMPUS, tr
    st = df[(df["regime"] == "final-empirical")
            & (df["campus"] == STRESS_CAMPUS)]
    if not st.empty:
        yield "stress", "campus=%d|m=1.0" % STRESS_CAMPUS, st
    # Every empirical configuration, all campuses and crew multipliers pooled.
    # This scope is HETEROGENEOUS (it mixes the stress campus into the verdict
    # campuses), so it carries paired comparisons only and is barred from the
    # equivalence-set ranking; it exists to report rolling CP-SAT's paired
    # difference over its whole 160-configuration subsample.
    yield "emp_pooled", "ALL", df[df["regime"] == "final-empirical"]


# Scope families on which the (expensive) vs-reference comparison table is run.
COMPARISON_SCOPE_TYPES = ("emp_m", "emp_ubin", "gen_all", "gen_utarget",
                          "transfer", "stress", "emp_pooled")
# Scope families that may carry an equivalence-set ranking (a mean ranking is
# only meaningful inside one homogeneous scope).
EQUIV_SCOPE_TYPES = ("emp_m", "emp_ubin", "emp_m_ubin", "gen_all",
                     "gen_utarget", "transfer", "stress")


# --------------------------------------------------------------------------- #
# Block plumbing.
# --------------------------------------------------------------------------- #
def _holm_within_family(frame: pd.DataFrame, key_cols) -> pd.DataFrame:
    """Add ``holm_p``: Holm-adjusted Wilcoxon p within each key group."""
    frame = frame.copy()
    frame["holm_p"] = np.nan
    for _, idx in frame.groupby(list(key_cols), sort=True).groups.items():
        idx = list(idx)
        adj = stats.holm({i: float(frame.loc[i, "wilcoxon_p"]) for i in idx})
        for i in idx:
            frame.loc[i, "holm_p"] = adj[i]
    return frame


def equivalence_block(df: pd.DataFrame, n_boot: int, seed: int) -> pd.DataFrame:
    """Per scope: every full-coverage method paired against the scope's best."""
    parts = []
    for scope_type, scope, sub in scope_frames(df):
        if scope_type not in EQUIV_SCOPE_TYPES:
            continue
        methods = [m for m in FULL_COVERAGE if m in set(sub["method"])]
        eq = stats.equivalence_set(sub, methods=methods, value_col=VALUE_COL,
                                   n_boot=n_boot, seed=seed)
        if eq.empty:
            continue
        eq.insert(0, "scope_type", scope_type)
        eq["scope"] = scope
        parts.append(eq)
    out = pd.concat(parts, ignore_index=True)
    out["family"] = [stats.default_family(m, b)
                     for m, b in zip(out["method"], out["best_method"])]
    # The best method's own row is not a test, so it is excluded from its
    # family's Holm correction (it would otherwise inflate the family size).
    is_self = out["method"] == out["best_method"]
    tested = _holm_within_family(out[~is_self].copy(),
                                 ["scope_type", "scope", "family"])
    out.loc[tested.index, "holm_p"] = tested["holm_p"]
    out.loc[is_self, "holm_p"] = 1.0
    out["pct_from_best"] = 100.0 * (out["mean"] - out["mean_best"]) / out["mean_best"]
    out["ratio_to_best"] = out["mean"] / out["mean_best"]
    out = out.sort_values(["scope_type", "scope", "mean"], kind="mergesort")
    cols = ["scope_type", "scope", "method", "family", "n_rows", "coverage",
            "mean", "best_method", "mean_best", "pct_from_best", "ratio_to_best",
            "n_configs", "n_clusters", "mean_diff", "ci_lo", "ci_hi", "margin",
            "wilcoxon_p", "holm_p", "verdict", "in_equivalence_set"]
    return out[cols].reset_index(drop=True)


def comparisons_block(df: pd.DataFrame, n_boot: int, seed: int) -> pd.DataFrame:
    """Per scope: every real method (rolling included) vs EDD, ATC and WMDD.

    Rolling CP-SAT pairs only on the configurations it was run on, so its rows
    carry a smaller ``n_configs``; that number is the subsample disclosure the
    first read asked for and every rolling claim quotes it.
    """
    parts = []
    for scope_type, scope, sub in scope_frames(df):
        if scope_type not in COMPARISON_SCOPE_TYPES:
            continue
        present = set(sub["method"])
        methods = [m for m in FULL_COVERAGE + (ROLLING,) if m in present]
        refs = [r for r in REFERENCES if r in present]
        s = sub.copy()
        s["analysis_scope"] = scope
        cmp_ = stats.compare_all(s, reference_methods=refs, methods=methods,
                                 scope_cols=["analysis_scope"],
                                 value_col=VALUE_COL, n_boot=n_boot, seed=seed)
        if cmp_.empty:
            continue
        cmp_.insert(0, "scope_type", scope_type)
        cmp_["scope"] = scope
        parts.append(cmp_.drop(columns=["analysis_scope"]))
    out = pd.concat(parts, ignore_index=True)
    cols = ["scope_type", "scope", "method", "reference", "family", "n_configs",
            "n_clusters", "mean_ref", "mean_method", "mean_diff", "ci_lo",
            "ci_hi", "margin", "wilcoxon_p", "holm_p", "verdict"]
    return out[cols].sort_values(["scope_type", "scope", "reference", "mean_diff"],
                                 kind="mergesort").reset_index(drop=True)


def pools_block(df: pd.DataFrame, eq: pd.DataFrame, n_boot: int,
                seed: int) -> pd.DataFrame:
    """Per scope: the two seed-averaged pools vs the scope best and vs the rules.

    The pools are pseudo-methods, so they get their own Holm family rather than
    joining the real policy-vs-rule family.
    """
    best_of = {(r.scope_type, r.scope): r.best_method
               for r in eq[eq["method"] == eq["best_method"]].itertuples()}
    parts = []
    for scope_type, scope, sub in scope_frames(df):
        present = set(sub["method"])
        pools = [p for p in POOLS if p in present]
        if not pools:
            continue
        refs = [r for r in list(REFERENCES) if r in present]
        best = best_of.get((scope_type, scope))
        if best and best not in refs:
            refs = [best] + refs
        s = sub.copy()
        s["analysis_scope"] = scope
        cmp_ = stats.compare_all(s, reference_methods=refs, methods=pools,
                                 scope_cols=["analysis_scope"],
                                 value_col=VALUE_COL, n_boot=n_boot, seed=seed)
        if cmp_.empty:
            continue
        cmp_.insert(0, "scope_type", scope_type)
        cmp_["scope"] = scope
        cmp_["is_scope_best_ref"] = (cmp_["reference"] == best).astype(int)
        parts.append(cmp_.drop(columns=["analysis_scope"]))
    out = pd.concat(parts, ignore_index=True)
    cols = ["scope_type", "scope", "method", "reference", "is_scope_best_ref",
            "family", "n_configs", "n_clusters", "mean_ref", "mean_method",
            "mean_diff", "ci_lo", "ci_hi", "margin", "wilcoxon_p", "holm_p",
            "verdict"]
    return out[cols].sort_values(["scope_type", "scope", "method", "reference"],
                                 kind="mergesort").reset_index(drop=True)


def generator_ratios_block(eq: pd.DataFrame) -> pd.DataFrame:
    """Deterioration ratios of the diagnostic-floor methods on generator cells."""
    gen = eq[eq["scope_type"].isin(("gen_utarget", "gen_all"))]
    rows = []
    for (st, scope), sub in gen.groupby(["scope_type", "scope"], sort=True):
        best = sub["best_method"].iloc[0]
        mean_best = float(sub["mean_best"].iloc[0])
        for m in ("lpt", "random", "wspt", "edd", "atc", "wmdd", "pfifo"):
            r = sub[sub["method"] == m]
            if r.empty:
                continue
            rows.append({
                "scope_type": st, "scope": scope, "method": m,
                "best_method": best, "mean_best": mean_best,
                "mean": float(r["mean"].iloc[0]),
                "ratio_to_best": float(r["ratio_to_best"].iloc[0]),
                "pct_from_best": float(r["pct_from_best"].iloc[0]),
                "n_configs": int(r["n_configs"].iloc[0]),
                "n_clusters": int(r["n_clusters"].iloc[0]),
            })
    return pd.DataFrame(rows)


def latency_block(df: pd.DataFrame) -> pd.DataFrame:
    """Per-decision milliseconds by method family, plus the rolling replan cost.

    Latencies are read from the empirical cells (the deployment scope: an
    operator dispatching one campus-week), and the generator cells are reported
    beside them because their queues are an order of magnitude longer.
    """
    scopes = {
        "empirical_verdict": df[(df["regime"] == "final-empirical")
                                & (df["campus"].isin(VERDICT_CAMPUSES))],
        "empirical_all": df[df["regime"] == "final-empirical"],
        "generator": df[df["regime"] == "final-gen"],
    }
    rows = []
    for scope, sub in scopes.items():
        s = sub[~sub["method"].isin(POOLS)].copy()
        s["family"] = s["method"].map(method_family)
        for fam, g in s.groupby("family", sort=True):
            if fam == "other":
                continue
            v = g["mean_ms_per_decision"].dropna().to_numpy(dtype=float)
            if v.size == 0:
                continue
            row = {"scope": scope, "family": fam, "unit": "ms_per_decision",
                   "n_rows": int(v.size), "n_methods": int(g["method"].nunique()),
                   "median": float(np.median(v)),
                   "p90": float(np.percentile(v, 90)),
                   "mean": float(v.mean()), "min": float(v.min()),
                   "max": float(v.max())}
            rows.append(row)
            if fam == FAMILY_ROLL:
                r = g["mean_replan_s"].dropna().to_numpy(dtype=float)
                if r.size:
                    rows.append({"scope": scope, "family": fam,
                                 "unit": "s_per_replan", "n_rows": int(r.size),
                                 "n_methods": 1, "median": float(np.median(r)),
                                 "p90": float(np.percentile(r, 90)),
                                 "mean": float(r.mean()), "min": float(r.min()),
                                 "max": float(r.max())})
    return pd.DataFrame(rows).sort_values(["scope", "family", "unit"],
                                          kind="mergesort").reset_index(drop=True)


SEED_SCOPE_TYPES = ("emp_m", "gen_all", "gen_utarget")


def seed_dispersion_block(df: pd.DataFrame, eq: pd.DataFrame) -> pd.DataFrame:
    """Per scope: the spread of the ten seeds inside each learned pool."""
    rows = []
    for scope_type, scope, sub in scope_frames(df):
        if scope_type not in SEED_SCOPE_TYPES:
            continue
        eqs = eq[(eq["scope_type"] == scope_type) & (eq["scope"] == scope)]
        if eqs.empty:
            continue
        best = eqs["best_method"].iloc[0]
        in_set = set(eqs.loc[eqs["in_equivalence_set"] == 1, "method"])
        for pool, seeds in ((FAMILY_V2, V2_MLP), (FAMILY_ATTN, V2_ATTN),
                            (FAMILY_V1, V1_MLP)):
            present = [s for s in seeds if s in set(sub["method"])]
            if not present:
                continue
            means = (sub[sub["method"].isin(present)]
                     .groupby("method")[VALUE_COL].mean().sort_values())
            outside = [m for m in present if m not in in_set]
            rows.append({
                "scope_type": scope_type, "scope": scope, "pool": pool,
                "n_seeds": len(present),
                "pooled_mean": float(means.mean()),
                "min_mean": float(means.min()),
                "median_mean": float(means.median()),
                "max_mean": float(means.max()),
                "spread_abs": float(means.max() - means.min()),
                "spread_ratio": float(means.max() / means.min()),
                "spread_pct": float(100.0 * (means.max() / means.min() - 1.0)),
                "best_seed": str(means.index[0]),
                "worst_seed": str(means.index[-1]),
                "scope_best_method": best,
                "n_seeds_in_set": int(sum(1 for m in present if m in in_set)),
                "seeds_outside_set": " ".join(sorted(outside)),
                "per_seed_means": " ".join("%s=%.3f" % (m, means[m])
                                           for m in means.index),
            })
    return pd.DataFrame(rows)


def campus2_utilization_block(df: pd.DataFrame) -> pd.DataFrame:
    cfg = df[(df["regime"] == "final-empirical")
             & (df["campus"] == STRESS_CAMPUS)].drop_duplicates("id")
    u = cfg["u_realized"].to_numpy(dtype=float)
    rows = [{"statistic": "n_configs", "value": float(len(cfg))},
            {"statistic": "u_min", "value": float(u.min())},
            {"statistic": "u_p25", "value": float(np.percentile(u, 25))},
            {"statistic": "u_median", "value": float(np.median(u))},
            {"statistic": "u_mean", "value": float(u.mean())},
            {"statistic": "u_p75", "value": float(np.percentile(u, 75))},
            {"statistic": "u_max", "value": float(u.max())},
            {"statistic": "share_over_one",
             "value": float((u >= 1.0).mean())}]
    for b in stats.U_BIN_ORDER:
        n = int((cfg["u_bin"] == b).sum())
        if n:
            rows.append({"statistic": "n_in_bin_%s" % b, "value": float(n)})
    return pd.DataFrame(rows)


def dataset_block(df: pd.DataFrame, meta: dict) -> pd.DataFrame:
    real = df[~df["method"].isin(POOLS)]
    emp = real[real["regime"] == "final-empirical"]
    gen = real[real["regime"] == "final-gen"]
    ver = emp[emp["campus"].isin(VERDICT_CAMPUSES)]
    roll = real[real["method"] == ROLLING]
    rows = {
        "n_rows": len(real),
        "n_configs": real["id"].nunique(),
        "n_clusters": real["cluster"].nunique(),
        "n_methods": real["method"].nunique(),
        "n_infeasible": int((real["feasible"] != 1).sum()),
        "n_errors": int(meta.get("n_errors_this_run", 0)),
        "n_configs_empirical": emp["id"].nunique(),
        "n_configs_generator": gen["id"].nunique(),
        "n_configs_verdict": ver["id"].nunique(),
        "n_clusters_verdict": ver["cluster"].nunique(),
        "n_configs_transfer": real[(real["campus"] == TRANSFER_CAMPUS)
                                   & (real["regime"] == "final-empirical")]["id"].nunique(),
        "n_configs_stress": real[(real["campus"] == STRESS_CAMPUS)
                                 & (real["regime"] == "final-empirical")]["id"].nunique(),
        "n_configs_rolling": roll["id"].nunique(),
        "rolling_per_cell": int(meta.get("rollcp_per_cell", 0)),
        "rolling_budget_s": float(meta.get("rollcp_budget_s", float("nan"))),
        "elapsed_seconds": float(meta.get("elapsed_seconds", float("nan"))),
        "n_policy_seeds_v2": len(V2_MLP),
        "n_policy_seeds_attn": len(V2_ATTN),
    }
    return pd.DataFrame([{"field": k, "value": v} for k, v in rows.items()])


# --------------------------------------------------------------------------- #
# Sanity checks.
# --------------------------------------------------------------------------- #
def sanity_checks(df: pd.DataFrame, meta: dict, dataset: pd.DataFrame) -> list:
    """Assertions that must hold before any number is written; raises on failure."""
    d = {r.field: r.value for r in dataset.itertuples()}
    checks = []

    def require(name, got, want):
        ok = (got == want)
        checks.append({"check": name, "got": got, "want": want, "ok": bool(ok)})
        if not ok:
            raise SystemExit("sanity check failed: %s (got %r, want %r)"
                             % (name, got, want))

    require("n_configs vs meta.json", int(d["n_configs"]), int(meta["n_configs"]))
    require("n_rows vs meta.json", int(d["n_rows"]), int(meta["n_rows"]))
    require("n_infeasible vs meta.json", int(d["n_infeasible"]),
            int(meta["n_infeasible"]))
    require("n_errors vs meta.json", int(d["n_errors"]),
            int(meta["n_errors_this_run"]))
    require("empirical configs vs meta.json", int(d["n_configs_empirical"]),
            int(meta["n_configs_by_regime"]["final-empirical"]))
    require("generator configs vs meta.json", int(d["n_configs_generator"]),
            int(meta["n_configs_by_regime"]["final-gen"]))
    require("rolling configs vs meta.json", int(d["n_configs_rolling"]),
            int(meta["n_rollcp"]))
    require("methods present vs meta.json", int(d["n_methods"]),
            len(meta["methods_this_run"]))

    real = df[~df["method"].isin(POOLS)]
    per_method = real[real["method"] != ROLLING].groupby("method")["id"].nunique()
    require("every non-rolling method covers every configuration",
            int(per_method.min()), int(meta["n_configs"]))
    require("no rolling row on generator cells",
            int((real[real["method"] == ROLLING]["regime"] == "final-gen").sum()), 0)
    require("value column has no missing entry",
            int(real[VALUE_COL].isna().sum()), 0)
    return checks


# --------------------------------------------------------------------------- #
# Readable report.
# --------------------------------------------------------------------------- #
def _fmt(x, nd=3):
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "-"
    return ("%%.%df" % nd) % float(x)


def set_members(eq: pd.DataFrame, scope_type: str, scope: str) -> list:
    sub = eq[(eq["scope_type"] == scope_type) & (eq["scope"] == scope)
             & (eq["in_equivalence_set"] == 1)]
    return list(sub.sort_values("mean")["method"])


def _count_phrase(n: int, total: int, noun: str) -> str:
    if n == total:
        return "all %s %s" % (NUMERAL[total], noun)
    return "%s of the %s %s" % (NUMERAL[n], NUMERAL[total], noun)


def set_statement(members) -> str:
    """Plain-English membership sentence for a macro (rules named, pools counted)."""
    members = list(members)
    rules = [DISPLAY[m] for m in RULES if m in members]
    n_v2 = sum(1 for m in V2_MLP if m in members)
    n_at = sum(1 for m in V2_ATTN if m in members)
    n_v1 = sum(1 for m in V1_MLP if m in members)
    parts = []
    if len(rules) == len(RULES):
        parts.append("every transparent rule")
    elif rules:
        parts.append(rules[0] if len(rules) == 1
                     else ", ".join(rules[:-1]) + " and " + rules[-1])
    if n_v2:
        parts.append(_count_phrase(n_v2, len(V2_MLP), "policy seeds"))
    if n_at:
        parts.append(_count_phrase(n_at, len(V2_ATTN), "attention seeds"))
    if n_v1:
        parts.append(_count_phrase(n_v1, len(V1_MLP), "curriculum-v1 seeds"))
    if not parts:
        return "no method"
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + ", and " + parts[-1]


def _top_with_rules(sub: pd.DataFrame, n: int = 12) -> pd.DataFrame:
    """The n best-mean methods, plus every transparent rule wherever it ranks.

    A reader of the report needs to see EDD, ATC and WMDD in every scope, and on
    a contended scope they can rank below a dozen policy seeds.
    """
    keep = sub.head(n)
    rest = sub[sub["method"].isin(RULES) & ~sub["method"].isin(keep["method"])]
    return pd.concat([keep, rest]).sort_values("mean", kind="mergesort")


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


def write_report(out: Path, df, meta, dataset, eq, cmp_, pools, ratios,
                 latency, seeds, camp2, checks, n_boot, seed) -> None:
    d = {r.field: r.value for r in dataset.itertuples()}
    L = []
    A = L.append
    A("# Eval-B definitive analysis\n")
    A("Source: `results/r4_final/results.csv` (%d rows, %d configurations, "
      "%d base-instance clusters, %d methods, %d infeasible, %d errors). "
      "Statistics: `fmwos.stats`, protocol §R4.5, %d bootstrap resamples, "
      "master seed %d, equivalence margin max(1.0, 1%% of the comparator "
      "mean), Holm within each comparison family. A negative difference means "
      "the method is better than its comparator.\n"
      % (d["n_rows"], d["n_configs"], d["n_clusters"], d["n_methods"],
         d["n_infeasible"], d["n_errors"], n_boot, seed))
    A("Coverage discipline: equivalence sets are ranked among the %d "
      "full-coverage methods only. Rolling CP-SAT ran on %d of %d "
      "configurations (%d per empirical cell, %.0f s budget) and appears only "
      "in its own paired rows, with that subsample size on every row.\n"
      % (len(FULL_COVERAGE), d["n_configs_rolling"], d["n_configs"],
         d["rolling_per_cell"], d["rolling_budget_s"]))

    A("\n## 1. Empirical verdict (campuses %s)\n"
      % ", ".join(str(c) for c in VERDICT_CAMPUSES))
    A("Verdict scope: %d configurations over %d base instances.\n"
      % (d["n_configs_verdict"], d["n_clusters_verdict"]))
    for scope_type, title in (("emp_m", "Per crew multiplier"),
                              ("emp_ubin", "Per realized-utilization bin "
                                           "(empirical regime only)")):
        A("\n### %s\n" % title)
        for scope in eq[eq["scope_type"] == scope_type]["scope"].unique():
            sub = eq[(eq["scope_type"] == scope_type) & (eq["scope"] == scope)]
            best = sub["best_method"].iloc[0]
            members = set_members(eq, scope_type, scope)
            A("\n**%s** — best %s (mean %s), %d configurations, %d clusters. "
              "Equivalence set (%d methods): %s.\n"
              % (scope, best, _fmt(sub["mean_best"].iloc[0]),
                 int(sub["n_configs"].max()), int(sub["n_clusters"].max()),
                 len(members), set_statement(members)))
            top = _top_with_rules(sub)
            A(_md_table(top, ["method", "mean", "pct_from_best", "mean_diff",
                              "ci_lo", "ci_hi", "margin", "holm_p", "verdict",
                              "in_equivalence_set"]))
            p = pools[(pools["scope_type"] == scope_type)
                      & (pools["scope"] == scope)]
            if not p.empty:
                A("\nSeed-averaged pools (aggregates, excluded from the set):\n")
                A(_md_table(p, ["method", "reference", "mean_method", "mean_ref",
                                "mean_diff", "ci_lo", "ci_hi", "verdict"]))
            sd = seeds[(seeds["scope_type"] == scope_type)
                       & (seeds["scope"] == scope)]
            if not sd.empty:
                A("\nSeed dispersion:\n")
                A(_md_table(sd, ["pool", "pooled_mean", "min_mean", "median_mean",
                                 "max_mean", "spread_ratio", "n_seeds_in_set",
                                 "seeds_outside_set"]))
            r = cmp_[(cmp_["scope_type"] == scope_type)
                     & (cmp_["scope"] == scope) & (cmp_["method"] == ROLLING)]
            if not r.empty:
                A("\nRolling CP-SAT, paired on its own %d-configuration "
                  "subsample:\n" % int(r["n_configs"].max()))
                A(_md_table(r, ["reference", "n_configs", "n_clusters",
                                "mean_method", "mean_ref", "mean_diff", "ci_lo",
                                "ci_hi", "holm_p", "verdict"]))

    A("\n### Per crew multiplier and utilization bin (cross)\n")
    cross = eq[(eq["scope_type"] == "emp_m_ubin") & (eq["in_equivalence_set"] == 1)]
    grid = (cross.groupby("scope")
            .agg(best=("best_method", "first"), mean_best=("mean_best", "first"),
                 n_clusters=("n_clusters", "max"), set_size=("method", "size"))
            .reset_index())
    A(_md_table(grid, ["scope", "best", "mean_best", "n_clusters", "set_size"]))

    A("\n## 2. Generator verdict (fixed-window cells, rolling CP-SAT absent)\n")
    for scope in eq[eq["scope_type"] == "gen_utarget"]["scope"].unique():
        sub = eq[(eq["scope_type"] == "gen_utarget") & (eq["scope"] == scope)]
        members = set_members(eq, "gen_utarget", scope)
        A("\n**%s** — best %s (mean %s), %d configurations, %d clusters. "
          "Equivalence set (%d methods): %s.\n"
          % (scope, sub["best_method"].iloc[0], _fmt(sub["mean_best"].iloc[0]),
             int(sub["n_configs"].max()), int(sub["n_clusters"].max()),
             len(members), set_statement(members)))
        A(_md_table(_top_with_rules(sub), ["method", "mean", "pct_from_best", "mean_diff",
                                   "ci_lo", "ci_hi", "margin", "holm_p",
                                   "verdict", "in_equivalence_set"]))
    A("\nDiagnostic-floor deterioration ratios (mean / best mean):\n")
    A(_md_table(ratios[ratios["scope_type"] == "gen_utarget"],
                ["scope", "method", "mean", "mean_best", "ratio_to_best",
                 "pct_from_best"]))

    A("\n## 3. Transfer and stress\n")
    for scope_type, title in (("transfer", "Campus %d (transfer, m=1.0)"
                               % TRANSFER_CAMPUS),
                              ("stress", "Campus %d (nonstationary stress, "
                               "never pooled with a verdict)" % STRESS_CAMPUS)):
        sub = eq[eq["scope_type"] == scope_type]
        if sub.empty:
            continue
        scope = sub["scope"].iloc[0]
        members = set_members(eq, scope_type, scope)
        A("\n### %s\n" % title)
        A("Best %s (mean %s), %d configurations, %d clusters. Equivalence set "
          "(%d methods): %s.\n"
          % (sub["best_method"].iloc[0], _fmt(sub["mean_best"].iloc[0]),
             int(sub["n_configs"].max()), int(sub["n_clusters"].max()),
             len(members), set_statement(members)))
        A(_md_table(_top_with_rules(sub), ["method", "mean", "pct_from_best", "mean_diff",
                                   "ci_lo", "ci_hi", "margin", "holm_p",
                                   "verdict", "in_equivalence_set"]))
    A("\nCampus %d realized utilization:\n" % STRESS_CAMPUS)
    A(_md_table(camp2, ["statistic", "value"]))

    A("\n## 3b. Rolling CP-SAT, every paired row\n")
    A("Rolling CP-SAT is excluded from every equivalence-set ranking because it "
      "was run on %d of %d configurations (%d per empirical cell, none on the "
      "generator cells). Its evidence is the paired table below; `n_configs` is "
      "the subsample each row is computed on.\n"
      % (d["n_configs_rolling"], d["n_configs"], d["rolling_per_cell"]))
    A(_md_table(cmp_[cmp_["method"] == ROLLING],
                ["scope_type", "scope", "reference", "n_configs", "n_clusters",
                 "mean_method", "mean_ref", "mean_diff", "ci_lo", "ci_hi",
                 "holm_p", "verdict"]))

    A("\n## 4. Latency\n")
    A(_md_table(latency, ["scope", "family", "unit", "n_rows", "median", "p90",
                          "mean", "max"]))

    A("\n## 5. Seed dispersion (all reported scopes)\n")
    A(_md_table(seeds, ["scope_type", "scope", "pool", "pooled_mean", "min_mean",
                        "median_mean", "max_mean", "spread_ratio",
                        "n_seeds_in_set", "seeds_outside_set"]))

    A("\n## 6. Sanity checks\n")
    A(_md_table(pd.DataFrame(checks), ["check", "got", "want", "ok"]))

    (out / "analysis.md").write_text("\n".join(L))


# --------------------------------------------------------------------------- #
# headline.json
# --------------------------------------------------------------------------- #
def _eq_row(eq, scope_type, scope, method):
    r = eq[(eq["scope_type"] == scope_type) & (eq["scope"] == scope)
           & (eq["method"] == method)]
    return None if r.empty else r.iloc[0]


def _cmp_row(frame, scope_type, scope, method, reference):
    r = frame[(frame["scope_type"] == scope_type) & (frame["scope"] == scope)
              & (frame["method"] == method) & (frame["reference"] == reference)]
    return None if r.empty else r.iloc[0]


def _lat(latency, scope, family, unit="ms_per_decision"):
    r = latency[(latency["scope"] == scope) & (latency["family"] == family)
                & (latency["unit"] == unit)]
    return None if r.empty else r.iloc[0]


def build_headline(dataset, eq, cmp_, pools, ratios, latency, seeds,
                   camp2) -> dict:
    d = {r.field: r.value for r in dataset.itertuples()}
    H = {"dataset": {k: (int(v) if float(v).is_integer() else float(v))
                     for k, v in d.items()}}

    # --- empirical verdict, per crew multiplier -------------------------- #
    H["empirical_verdict"] = {}
    for m in CREW_MULTIPLIERS:
        scope = "m=%s" % m
        sub = eq[(eq["scope_type"] == "emp_m") & (eq["scope"] == scope)]
        members = set_members(eq, "emp_m", scope)
        atc, wmdd = _eq_row(eq, "emp_m", scope, "atc"), _eq_row(eq, "emp_m", scope, "wmdd")
        edd = _eq_row(eq, "emp_m", scope, "edd")
        sd = seeds[(seeds["scope_type"] == "emp_m") & (seeds["scope"] == scope)
                   & (seeds["pool"] == FAMILY_V2)]
        pool_best = _cmp_row(pools, "emp_m", scope, POOL_V2,
                             sub["best_method"].iloc[0])
        pool_edd = _cmp_row(pools, "emp_m", scope, POOL_V2, "edd")
        roll = _cmp_row(cmp_, "emp_m", scope, ROLLING, "edd")
        H["empirical_verdict"][scope] = {
            "best_method": sub["best_method"].iloc[0],
            "mean_best": float(sub["mean_best"].iloc[0]),
            "n_configs": int(sub["n_configs"].max()),
            "n_clusters": int(sub["n_clusters"].max()),
            "set_size": len(members),
            "set_members": members,
            "set_statement": set_statement(members),
            "edd_pct_from_best": float(edd["pct_from_best"]),
            "edd_in_set": int(edd["in_equivalence_set"]),
            "atc_pct_from_best": float(atc["pct_from_best"]),
            "atc_in_set": int(atc["in_equivalence_set"]),
            "atc_verdict": str(atc["verdict"]),
            "wmdd_pct_from_best": float(wmdd["pct_from_best"]),
            "wmdd_in_set": int(wmdd["in_equivalence_set"]),
            "wmdd_verdict": str(wmdd["verdict"]),
            "policy_pool_mean": float(sd["pooled_mean"].iloc[0]),
            "policy_seeds_in_set": int(sd["n_seeds_in_set"].iloc[0]),
            "policy_seed_spread_pct": float(sd["spread_pct"].iloc[0]),
            "policy_pool_vs_best_diff": float(pool_best["mean_diff"]),
            "policy_pool_vs_best_ci": [float(pool_best["ci_lo"]),
                                       float(pool_best["ci_hi"])],
            "policy_pool_vs_best_verdict": str(pool_best["verdict"]),
            "policy_pool_vs_edd_diff": float(pool_edd["mean_diff"]),
            "policy_pool_vs_edd_ci": [float(pool_edd["ci_lo"]),
                                      float(pool_edd["ci_hi"])],
            "policy_pool_vs_edd_verdict": str(pool_edd["verdict"]),
            "rolling_vs_edd_diff": float(roll["mean_diff"]),
            "rolling_vs_edd_ci": [float(roll["ci_lo"]), float(roll["ci_hi"])],
            "rolling_vs_edd_n": int(roll["n_configs"]),
            "rolling_vs_edd_verdict": str(roll["verdict"]),
        }

    # --- empirical verdict, per utilization bin -------------------------- #
    H["empirical_ubin"] = {}
    for scope in eq[eq["scope_type"] == "emp_ubin"]["scope"].unique():
        sub = eq[(eq["scope_type"] == "emp_ubin") & (eq["scope"] == scope)]
        members = set_members(eq, "emp_ubin", scope)
        H["empirical_ubin"][scope] = {
            "best_method": sub["best_method"].iloc[0],
            "mean_best": float(sub["mean_best"].iloc[0]),
            "n_configs": int(sub["n_configs"].max()),
            "n_clusters": int(sub["n_clusters"].max()),
            "n_full_coverage_methods": int(sub["method"].nunique()),
            "set_size": len(members),
            "set_members": members,
            "set_statement": set_statement(members),
            "set_is_complete": bool(len(members) == int(sub["method"].nunique())),
            "lpt_in_set": int(_eq_row(eq, "emp_ubin", scope, "lpt")["in_equivalence_set"]),
            "random_in_set": int(_eq_row(eq, "emp_ubin", scope, "random")["in_equivalence_set"]),
        }

    # --- generator ------------------------------------------------------- #
    H["generator"] = {}
    for u in U_TARGETS:
        scope = "u_target=%s" % u
        sub = eq[(eq["scope_type"] == "gen_utarget") & (eq["scope"] == scope)]
        if sub.empty:
            continue
        members = set_members(eq, "gen_utarget", scope)
        sd = seeds[(seeds["scope_type"] == "gen_utarget")
                   & (seeds["scope"] == scope) & (seeds["pool"] == FAMILY_V2)]
        pool_best = _cmp_row(pools, "gen_utarget", scope, POOL_V2,
                             sub["best_method"].iloc[0])
        pool_edd = _cmp_row(pools, "gen_utarget", scope, POOL_V2, "edd")
        entry = {
            "best_method": sub["best_method"].iloc[0],
            "mean_best": float(sub["mean_best"].iloc[0]),
            "n_configs": int(sub["n_configs"].max()),
            "n_clusters": int(sub["n_clusters"].max()),
            "set_size": len(members),
            "set_members": members,
            "set_statement": set_statement(members),
            "policy_pool_mean": float(sd["pooled_mean"].iloc[0]),
            "policy_seeds_in_set": int(sd["n_seeds_in_set"].iloc[0]),
            "policy_seed_min_mean": float(sd["min_mean"].iloc[0]),
            "policy_seed_max_mean": float(sd["max_mean"].iloc[0]),
            "policy_seed_spread_pct": float(sd["spread_pct"].iloc[0]),
            "policy_pool_vs_best_diff": float(pool_best["mean_diff"]),
            "policy_pool_vs_best_pct":
                100.0 * float(pool_best["mean_diff"]) / float(pool_best["mean_ref"]),
            "policy_pool_vs_best_verdict": str(pool_best["verdict"]),
            "policy_pool_vs_edd_pct":
                100.0 * float(pool_edd["mean_diff"]) / float(pool_edd["mean_ref"]),
        }
        for m in ("lpt", "random", "wspt", "atc", "wmdd", "edd"):
            r = _eq_row(eq, "gen_utarget", scope, m)
            entry["%s_mean" % m] = float(r["mean"])
            entry["%s_ratio_to_best" % m] = float(r["ratio_to_best"])
            entry["%s_pct_from_best" % m] = float(r["pct_from_best"])
            entry["%s_in_set" % m] = int(r["in_equivalence_set"])
        H["generator"][scope] = entry

    # --- transfer and stress --------------------------------------------- #
    for key, scope_type in (("transfer", "transfer"), ("stress", "stress")):
        sub = eq[eq["scope_type"] == scope_type]
        if sub.empty:
            continue
        scope = sub["scope"].iloc[0]
        members = set_members(eq, scope_type, scope)
        H[key] = {
            "scope": scope,
            "best_method": sub["best_method"].iloc[0],
            "mean_best": float(sub["mean_best"].iloc[0]),
            "n_configs": int(sub["n_configs"].max()),
            "n_clusters": int(sub["n_clusters"].max()),
            "set_size": len(members),
            "set_members": members,
            "set_statement": set_statement(members),
            "edd_pct_from_best": float(_eq_row(eq, scope_type, scope, "edd")["pct_from_best"]),
            "atc_pct_from_best": float(_eq_row(eq, scope_type, scope, "atc")["pct_from_best"]),
        }
    H["stress"]["utilization"] = {r.statistic: float(r.value)
                                  for r in camp2.itertuples()}

    # --- rolling, pooled over the empirical scope ------------------------ #
    H["rolling"] = {"per_cell": int(d["rolling_per_cell"]),
                    "budget_s": float(d["rolling_budget_s"]),
                    "n_configs": int(d["n_configs_rolling"])}

    def _roll(rows):
        return {r.scope: {"mean_diff": float(r.mean_diff),
                          "ci": [float(r.ci_lo), float(r.ci_hi)],
                          "mean_ref": float(r.mean_ref),
                          "n_configs": int(r.n_configs),
                          "n_clusters": int(r.n_clusters),
                          "holm_p": float(r.holm_p),
                          "verdict": str(r.verdict)}
                for r in rows.itertuples()}

    roll = cmp_[cmp_["method"] == ROLLING]
    for ref in REFERENCES:
        by_ref = roll[roll["reference"] == ref]
        H["rolling"]["vs_%s_by_m" % ref] = _roll(by_ref[by_ref["scope_type"] == "emp_m"])
        for st in ("emp_pooled", "transfer", "stress"):
            r = by_ref[by_ref["scope_type"] == st]
            if not r.empty:
                H["rolling"].setdefault("vs_%s_%s" % (ref, st), {}).update(_roll(r))

    # --- latency ---------------------------------------------------------- #
    H["latency"] = {}
    for fam in (FAMILY_RULES, FAMILY_V1, FAMILY_V2, FAMILY_ATTN):
        r = _lat(latency, "empirical_verdict", fam)
        if r is not None:
            H["latency"][fam] = {"median_ms": float(r["median"]),
                                 "p90_ms": float(r["p90"]),
                                 "n_rows": int(r["n_rows"])}
    r = _lat(latency, "empirical_verdict", FAMILY_ROLL, "s_per_replan")
    if r is not None:
        H["latency"]["rolling_replan"] = {"median_s": float(r["median"]),
                                          "p90_s": float(r["p90"]),
                                          "n_rows": int(r["n_rows"])}
    for fam in (FAMILY_RULES, FAMILY_V2, FAMILY_ATTN):
        r = _lat(latency, "generator", fam)
        if r is not None:
            H["latency"]["generator_" + fam] = {"median_ms": float(r["median"]),
                                                "p90_ms": float(r["p90"])}
    return H


# --------------------------------------------------------------------------- #
# Macro generation (paper/macros_r4.tex).
# --------------------------------------------------------------------------- #
def _thousands(n) -> str:
    s = "%d" % int(round(float(n)))
    neg, s = (s[0] == "-"), s.lstrip("-")
    groups = []
    while len(s) > 3:
        groups.insert(0, s[-3:])
        s = s[:-3]
    groups.insert(0, s)
    return ("-" if neg else "") + "{,}".join(groups)


def f_int(x) -> str:
    return _thousands(x)


def f_twt(x) -> str:
    """Weighted tardiness: 1 dp below 1000, 0 dp with separators above."""
    v = float(x)
    return _thousands(v) if abs(v) >= 1000 else ("%.1f" % v)


def _unsign_zero(s: str) -> str:
    """Drop the minus sign from a value that rounded to zero ("-0.0" -> "0.0")."""
    return s[1:] if s.startswith("-") and float(s) == 0.0 else s


def f_diff(x) -> str:
    """A paired difference in weighted units: 2 dp below 10, else 1 dp."""
    v = float(x)
    if abs(v) >= 1000:
        return _thousands(v)
    return _unsign_zero(("%.2f" % v) if abs(v) < 10 else ("%.1f" % v))


def f_pct(x) -> str:
    """A percentage: 2 dp when it would otherwise round to zero, else 1 dp."""
    v = float(x)
    return _unsign_zero(("%.2f" % v) if abs(v) < 0.05 else ("%.1f" % v))


def f_ratio(x) -> str:
    return "%.1f" % float(x)


def f_ms(x) -> str:
    """Milliseconds to three significant figures (two below 0.01)."""
    v = float(x)
    if v == 0:
        return "0"
    digits = max(0, 3 - int(math.floor(math.log10(abs(v)))) - 1)
    return ("%%.%df" % min(digits, 6)) % v


def f_s(x) -> str:
    return "%.2f" % float(x)


def f_text(x) -> str:
    return str(x)


HOUSE_SEP = "{,}"
HOUSE_MINUS = "$-$"


def house_number(value) -> str:
    """One number style for every macro this project generates.

    Two rules, applied after the per-quantity formatter has chosen the number
    of decimals.  A negative sign is typeset as a math-mode minus, because an
    ASCII hyphen in text mode is a hyphen-length dash rather than a minus.  An
    integer part of more than three digits is grouped in thousands, including
    the integer part of a value that also carries decimals.  Applying this in
    one place is what keeps a count, a mean, a paired difference, a percentage
    and a ratio looking alike across the generated macro files.

    A value that does not parse as a number (a verdict word, a method name, a
    membership sentence) is returned unchanged, and the function is idempotent:
    running it on its own output, or on a value that already carries either
    piece of the convention, changes nothing.
    """
    s = str(value)
    plain = s.replace(HOUSE_SEP, "").replace(HOUSE_MINUS, "-")
    try:
        float(plain)
    except ValueError:
        return s
    negative = plain.startswith("-")
    head, dot, tail = (plain[1:] if negative else plain).partition(".")
    if head.isdigit() and len(head) > 3:
        groups = []
        while len(head) > 3:
            groups.insert(0, head[-3:])
            head = head[:-3]
        groups.insert(0, head)
        head = HOUSE_SEP.join(groups)
    out = head + dot + tail
    return (HOUSE_MINUS + out) if negative else out


class MacroFile:
    """Collects macro definitions, each with the CSV field it was read from.

    Values pass through :func:`house_number` on the way in, so the number style
    is a property of the generated file rather than of each call site; the
    subclasses in the companion scripts inherit it through ``super().add``.
    """

    def __init__(self, existing_names):
        self.existing = set(existing_names)
        self.items = []          # (name, value, comment) or (None, None, header)
        self.names = set()

    def section(self, title):
        self.items.append((None, None, title))

    def add(self, name, value, source):
        if not name.startswith("rf"):
            raise SystemExit("macro %r does not use the \\rf prefix" % name)
        if not name.isalpha():
            raise SystemExit("macro %r must be letters only (LaTeX)" % name)
        if name in self.existing:
            raise SystemExit("macro %r already exists in paper/macros.tex" % name)
        if name in self.names:
            raise SystemExit("macro %r defined twice in this run" % name)
        v = house_number(value)
        if v.strip() == "" or "nan" in v.lower() or "inf" in v.lower():
            raise SystemExit("macro %r has a non-finite value %r" % (name, v))
        self.names.add(name)
        self.items.append((name, v, source))

    def render(self, header) -> str:
        L = [header]
        width = min(78, max(len("\\newcommand{\\%s}{%s}" % (n, v))
                            for n, v, _ in self.items if n) + 2)
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


M_TOKEN = {1.0: "Mfull", 0.8: "Meighty", 0.6: "Msixty"}
U_TOKEN = {0.7: "Useven", 0.9: "Unine", 1.0: "Uten", 1.1: "Ueleven",
           1.3: "Uthirteen"}
BIN_TOKEN = {"<0.5": "Slack", "0.5-0.8": "Moderate", "0.8-1.0": "Tight",
             "1.0-1.2": "Over", ">=1.2": "Deep"}


def existing_macro_names(path: Path):
    if not path.exists():
        return set()
    import re
    return set(re.findall(r"\\newcommand\{\\([A-Za-z]+)\}", path.read_text()))


def build_macros(out: Path, paper_dir: Path) -> tuple:
    """Read this run's CSVs back from disk and write paper/macros_r4.tex."""
    eq = pd.read_csv(out / "equivalence.csv")
    cmp_ = pd.read_csv(out / "comparisons.csv")
    pools = pd.read_csv(out / "pools.csv")
    ratios = pd.read_csv(out / "generator_ratios.csv")
    latency = pd.read_csv(out / "latency.csv")
    seeds = pd.read_csv(out / "seed_dispersion.csv")
    dataset = pd.read_csv(out / "dataset.csv")
    camp2 = pd.read_csv(out / "campus2_utilization.csv")
    d = {r.field: r.value for r in dataset.itertuples()}

    mf = MacroFile(existing_macro_names(paper_dir / "macros.tex"))

    # ---- dataset -------------------------------------------------------- #
    mf.section("Eval-B run size (analysis/dataset.csv)")
    for name, field, fmt in (
            ("rfevalConfigs", "n_configs", f_int),
            ("rfevalRows", "n_rows", f_int),
            ("rfevalClusters", "n_clusters", f_int),
            ("rfevalMethods", "n_methods", f_int),
            ("rfevalInfeasible", "n_infeasible", f_int),
            ("rfevalErrors", "n_errors", f_int),
            ("rfevalEmpiricalConfigs", "n_configs_empirical", f_int),
            ("rfevalGeneratorConfigs", "n_configs_generator", f_int),
            ("rfevalVerdictConfigs", "n_configs_verdict", f_int),
            ("rfevalVerdictClusters", "n_clusters_verdict", f_int),
            ("rfevalTransferConfigs", "n_configs_transfer", f_int),
            ("rfevalStressConfigs", "n_configs_stress", f_int),
            ("rfevalPolicySeeds", "n_policy_seeds_v2", f_int)):
        mf.add(name, fmt(d[field]), "dataset.csv field=%s" % field)
    mf.add("rfevalHours", "%.1f" % (float(d["elapsed_seconds"]) / 3600.0),
           "dataset.csv field=elapsed_seconds")
    mf.add("rfevalScoredMethods", f_int(len(FULL_COVERAGE)),
           "scripts/r4_analysis.py FULL_COVERAGE (methods run on every "
           "configuration, so rankable)")

    # ---- block 1: empirical verdict, per crew multiplier ---------------- #
    mf.section("Empirical verdict, per crew multiplier (analysis/equivalence.csv,"
               " scope_type=emp_m)")
    for m in CREW_MULTIPLIERS:
        scope, tok = "m=%s" % m, M_TOKEN[m]
        sub = eq[(eq["scope_type"] == "emp_m") & (eq["scope"] == scope)]
        members = list(sub[sub["in_equivalence_set"] == 1].sort_values("mean")["method"])
        src = "equivalence.csv scope_type=emp_m scope=%s" % scope
        mf.add("rfempSetSize" + tok, f_int(len(members)), src + " field=in_equivalence_set")
        mf.add("rfempSetText" + tok, f_text(set_statement(members)),
               src + " field=in_equivalence_set (membership sentence)")
        mf.add("rfempSetComplete" + tok,
               f_text("yes" if len(members) == int(sub["method"].nunique()) else "no"),
               src + " field=in_equivalence_set (set covers every scored method)")
        mf.add("rfempBest" + tok, f_text(display_name(sub["best_method"].iloc[0])),
               src + " field=best_method (prose phrase)")
        mf.add("rfempBestId" + tok, f_text(sub["best_method"].iloc[0]),
               src + " field=best_method (raw checkpoint id, tables only)")
        mf.add("rfempBestMean" + tok, f_twt(sub["mean_best"].iloc[0]),
               src + " field=mean_best")
        mf.add("rfempClusters" + tok, f_int(sub["n_clusters"].max()),
               src + " field=n_clusters")
        mf.add("rfempConfigs" + tok, f_int(sub["n_configs"].max()),
               src + " field=n_configs")
        for meth, mtok in (("edd", "Edd"), ("atc", "Atc"), ("wmdd", "Wmdd")):
            r = sub[sub["method"] == meth].iloc[0]
            mf.add("rfemp%sGap%s" % (mtok, tok), f_pct(r["pct_from_best"]),
                   src + " method=%s field=pct_from_best" % meth)
            mf.add("rfemp%sSet%s" % (mtok, tok),
                   f_text("in" if int(r["in_equivalence_set"]) else "out"),
                   src + " method=%s field=in_equivalence_set" % meth)
        sd = seeds[(seeds["scope_type"] == "emp_m") & (seeds["scope"] == scope)
                   & (seeds["pool"] == FAMILY_V2)].iloc[0]
        ssrc = "seed_dispersion.csv scope_type=emp_m scope=%s pool=v2_mlp" % scope
        mf.add("rfpolSeedsInSet" + tok, f_int(sd["n_seeds_in_set"]),
               ssrc + " field=n_seeds_in_set")
        mf.add("rfpolPoolMean" + tok, f_twt(sd["pooled_mean"]),
               ssrc + " field=pooled_mean")
        mf.add("rfpolSeedSpread" + tok, f_pct(sd["spread_pct"]),
               ssrc + " field=spread_pct")

    # policy pool vs EDD at the tightest crew level, and vs the scope best
    mf.section("Learned pool against the due-date rule (analysis/pools.csv)")
    for m in CREW_MULTIPLIERS:
        scope, tok = "m=%s" % m, M_TOKEN[m]
        pe = pools[(pools["scope_type"] == "emp_m") & (pools["scope"] == scope)
                   & (pools["method"] == POOL_V2)
                   & (pools["reference"] == "edd")].iloc[0]
        psrc = ("pools.csv scope_type=emp_m scope=%s method=%s reference=edd"
                % (scope, POOL_V2))
        mf.add("rfpolEddDiff" + tok, f_diff(pe["mean_diff"]), psrc + " field=mean_diff")
        mf.add("rfpolEddCiLo" + tok, f_diff(pe["ci_lo"]), psrc + " field=ci_lo")
        mf.add("rfpolEddCiHi" + tok, f_diff(pe["ci_hi"]), psrc + " field=ci_hi")
        mf.add("rfpolEddVerdict" + tok, f_text(pe["verdict"]), psrc + " field=verdict")
        mf.add("rfpolEddPct" + tok,
               f_pct(100.0 * float(pe["mean_diff"]) / float(pe["mean_ref"])),
               psrc + " fields=mean_diff/mean_ref")

    # ---- block 1b: utilization bins, empirical ------------------------- #
    mf.section("Empirical verdict, per realized-utilization bin "
               "(analysis/equivalence.csv, scope_type=emp_ubin)")
    for b, tok in BIN_TOKEN.items():
        sub = eq[(eq["scope_type"] == "emp_ubin") & (eq["scope"] == "u_bin=%s" % b)]
        if sub.empty:
            continue
        members = list(sub[sub["in_equivalence_set"] == 1].sort_values("mean")["method"])
        src = "equivalence.csv scope_type=emp_ubin scope=u_bin=%s" % b
        mf.add("rfemp%sSetSize" % tok, f_int(len(members)),
               src + " field=in_equivalence_set")
        mf.add("rfemp%sMethods" % tok, f_int(sub["method"].nunique()),
               src + " field=method (full-coverage methods scored)")
        mf.add("rfemp%sClusters" % tok, f_int(sub["n_clusters"].max()),
               src + " field=n_clusters")
        mf.add("rfemp%sConfigs" % tok, f_int(sub["n_configs"].max()),
               src + " field=n_configs")
        mf.add("rfemp%sBest" % tok, f_text(display_name(sub["best_method"].iloc[0])),
               src + " field=best_method (prose phrase)")
        mf.add("rfemp%sBestMean" % tok, f_twt(sub["mean_best"].iloc[0]),
               src + " field=mean_best")
        mf.add("rfemp%sSetText" % tok, f_text(set_statement(members)),
               src + " field=in_equivalence_set (membership sentence)")
        # EDD against the scope best in every bin: the due-date rule is the one
        # the manuscript tracks across the utilization axis, so each bin gets
        # its own macro rather than a hand-typed figure.
        r_edd = sub[sub["method"] == "edd"].iloc[0]
        mf.add("rfemp%sEddGap" % tok, f_pct(r_edd["pct_from_best"]),
               src + " method=edd field=pct_from_best")
    slack = eq[(eq["scope_type"] == "emp_ubin") & (eq["scope"] == "u_bin=<0.5")]
    n_slack = int((slack["in_equivalence_set"] == 1).sum())
    complete = n_slack == int(slack["method"].nunique())
    mf.add("rfempSlackComplete", f_text("yes" if complete else "no"),
           "equivalence.csv scope=u_bin=<0.5 field=in_equivalence_set "
           "(set size equals the number of scored methods)")
    for meth, mtok in (("lpt", "Lpt"), ("random", "Random")):
        r = slack[slack["method"] == meth].iloc[0]
        mf.add("rfempSlack%sSet" % mtok,
               f_text("in" if int(r["in_equivalence_set"]) else "out"),
               "equivalence.csv scope=u_bin=<0.5 method=%s "
               "field=in_equivalence_set" % meth)
        mf.add("rfempSlack%sGap" % mtok, f_pct(r["pct_from_best"]),
               "equivalence.csv scope=u_bin=<0.5 method=%s field=pct_from_best"
               % meth)

    # ---- block 2: generator -------------------------------------------- #
    mf.section("Generator verdict, per target utilization "
               "(analysis/equivalence.csv, scope_type=gen_utarget)")
    for u in U_TARGETS:
        scope, tok = "u_target=%s" % u, U_TOKEN[u]
        sub = eq[(eq["scope_type"] == "gen_utarget") & (eq["scope"] == scope)]
        if sub.empty:
            continue
        members = list(sub[sub["in_equivalence_set"] == 1].sort_values("mean")["method"])
        src = "equivalence.csv scope_type=gen_utarget scope=%s" % scope
        mf.add("rfgenSetSize" + tok, f_int(len(members)), src + " field=in_equivalence_set")
        mf.add("rfgenSetText" + tok, f_text(set_statement(members)),
               src + " field=in_equivalence_set (membership sentence)")
        mf.add("rfgenBest" + tok, f_text(display_name(sub["best_method"].iloc[0])),
               src + " field=best_method (prose phrase)")
        mf.add("rfgenBestId" + tok, f_text(sub["best_method"].iloc[0]),
               src + " field=best_method (raw checkpoint id, tables only)")
        mf.add("rfgenBestMean" + tok, f_twt(sub["mean_best"].iloc[0]),
               src + " field=mean_best")
        mf.add("rfgenClusters" + tok, f_int(sub["n_clusters"].max()),
               src + " field=n_clusters")
        for meth, mtok in (("atc", "Atc"), ("wmdd", "Wmdd"), ("edd", "Edd")):
            r = sub[sub["method"] == meth].iloc[0]
            mf.add("rfgen%sGap%s" % (mtok, tok), f_pct(r["pct_from_best"]),
                   src + " method=%s field=pct_from_best" % meth)
    mf.section("Diagnostic-floor deterioration on generator cells "
               "(analysis/generator_ratios.csv)")
    for u in (1.1, 1.3):
        scope, tok = "u_target=%s" % u, U_TOKEN[u]
        for meth, mtok in (("lpt", "Lpt"), ("random", "Random"), ("wspt", "Wspt")):
            r = ratios[(ratios["scope_type"] == "gen_utarget")
                       & (ratios["scope"] == scope)
                       & (ratios["method"] == meth)]
            if r.empty:
                continue
            r = r.iloc[0]
            rsrc = ("generator_ratios.csv scope=%s method=%s" % (scope, meth))
            mf.add("rfgen%sRatio%s" % (mtok, tok), f_ratio(r["ratio_to_best"]),
                   rsrc + " field=ratio_to_best")
            mf.add("rfgen%sMean%s" % (mtok, tok), f_twt(r["mean"]),
                   rsrc + " field=mean")
    mf.section("Learned pool on the giant generator cells (analysis/pools.csv,"
               " analysis/seed_dispersion.csv)")
    for u in (1.1, 1.3):
        scope, tok = "u_target=%s" % u, U_TOKEN[u]
        pb = pools[(pools["scope_type"] == "gen_utarget") & (pools["scope"] == scope)
                   & (pools["method"] == POOL_V2)
                   & (pools["is_scope_best_ref"] == 1)]
        pe = pools[(pools["scope_type"] == "gen_utarget") & (pools["scope"] == scope)
                   & (pools["method"] == POOL_V2) & (pools["reference"] == "edd")]
        if not pe.empty:
            pe = pe.iloc[0]
            mf.add("rfpolTrailPct" + tok,
                   f_pct(100.0 * float(pe["mean_diff"]) / float(pe["mean_ref"])),
                   "pools.csv scope=%s method=%s reference=edd fields=mean_diff/mean_ref"
                   % (scope, POOL_V2))
            mf.add("rfpolTrailDiff" + tok, f_twt(pe["mean_diff"]),
                   "pools.csv scope=%s method=%s reference=edd field=mean_diff"
                   % (scope, POOL_V2))
        if not pb.empty:
            pb = pb.iloc[0]
            mf.add("rfpolBestGap" + tok,
                   f_pct(100.0 * float(pb["mean_diff"]) / float(pb["mean_ref"])),
                   "pools.csv scope=%s method=%s is_scope_best_ref=1 "
                   "fields=mean_diff/mean_ref" % (scope, POOL_V2))
        sd = seeds[(seeds["scope_type"] == "gen_utarget") & (seeds["scope"] == scope)
                   & (seeds["pool"] == FAMILY_V2)]
        if not sd.empty:
            sd = sd.iloc[0]
            ssrc = "seed_dispersion.csv scope=%s pool=v2_mlp" % scope
            mf.add("rfpolSeedMin" + tok, f_twt(sd["min_mean"]), ssrc + " field=min_mean")
            mf.add("rfpolSeedMax" + tok, f_twt(sd["max_mean"]), ssrc + " field=max_mean")
            mf.add("rfpolSeedSpreadGen" + tok, f_pct(sd["spread_pct"]),
                   ssrc + " field=spread_pct")
            mf.add("rfpolSeedsInSetGen" + tok, f_int(sd["n_seeds_in_set"]),
                   ssrc + " field=n_seeds_in_set")

    # ---- block 3: transfer and stress ---------------------------------- #
    mf.section("Transfer campus and the nonstationary stress campus "
               "(analysis/equivalence.csv, analysis/campus2_utilization.csv)")
    for key, prefix in (("transfer", "rfxfer"), ("stress", "rfstress")):
        sub = eq[eq["scope_type"] == key]
        if sub.empty:
            continue
        members = list(sub[sub["in_equivalence_set"] == 1].sort_values("mean")["method"])
        src = "equivalence.csv scope_type=%s scope=%s" % (key, sub["scope"].iloc[0])
        mf.add(prefix + "SetSize", f_int(len(members)), src + " field=in_equivalence_set")
        mf.add(prefix + "SetText", f_text(set_statement(members)),
               src + " field=in_equivalence_set (membership sentence)")
        mf.add(prefix + "Best", f_text(display_name(sub["best_method"].iloc[0])),
               src + " field=best_method (prose phrase)")
        mf.add(prefix + "BestId", f_text(sub["best_method"].iloc[0]),
               src + " field=best_method (raw checkpoint id, tables only)")
        mf.add(prefix + "BestMean", f_twt(sub["mean_best"].iloc[0]),
               src + " field=mean_best")
        mf.add(prefix + "Configs", f_int(sub["n_configs"].max()), src + " field=n_configs")
        mf.add(prefix + "Clusters", f_int(sub["n_clusters"].max()),
               src + " field=n_clusters")
        mf.add(prefix + "EddGap",
               f_pct(sub[sub["method"] == "edd"]["pct_from_best"].iloc[0]),
               src + " method=edd field=pct_from_best")
    c2 = {r.statistic: float(r.value) for r in camp2.itertuples()}
    mf.add("rfstressUmedian", "%.2f" % c2["u_median"],
           "campus2_utilization.csv statistic=u_median")
    mf.add("rfstressUmax", "%.1f" % c2["u_max"],
           "campus2_utilization.csv statistic=u_max")
    mf.add("rfstressOverShare", f_pct(100.0 * c2["share_over_one"]),
           "campus2_utilization.csv statistic=share_over_one")

    # ---- rolling -------------------------------------------------------- #
    mf.section("Rolling CP-SAT, paired on its own subsample "
               "(analysis/comparisons.csv, method=rollcp2)")
    mf.add("rfrollPerCell", f_int(d["rolling_per_cell"]),
           "dataset.csv field=rolling_per_cell")
    mf.add("rfrollConfigs", f_int(d["n_configs_rolling"]),
           "dataset.csv field=n_configs_rolling")
    mf.add("rfrollBudget", "%.0f" % float(d["rolling_budget_s"]),
           "dataset.csv field=rolling_budget_s")
    roll = cmp_[(cmp_["method"] == ROLLING) & (cmp_["scope_type"] == "emp_m")]
    for m in CREW_MULTIPLIERS:
        scope, tok = "m=%s" % m, M_TOKEN[m]
        r = roll[(roll["scope"] == scope) & (roll["reference"] == "edd")]
        if r.empty:
            continue
        r = r.iloc[0]
        rsrc = ("comparisons.csv scope_type=emp_m scope=%s method=rollcp2 "
                "reference=edd" % scope)
        mf.add("rfrollEddDiff" + tok, f_diff(r["mean_diff"]), rsrc + " field=mean_diff")
        mf.add("rfrollEddCiLo" + tok, f_diff(r["ci_lo"]), rsrc + " field=ci_lo")
        mf.add("rfrollEddCiHi" + tok, f_diff(r["ci_hi"]), rsrc + " field=ci_hi")
        mf.add("rfrollEddN" + tok, f_int(r["n_configs"]), rsrc + " field=n_configs")
        mf.add("rfrollEddVerdict" + tok, f_text(r["verdict"]), rsrc + " field=verdict")
    # Pooled over every empirical configuration rolling was run on (all campuses,
    # all crew multipliers): the paired difference is valid on a heterogeneous
    # scope even though a mean ranking there would not be.
    pooled = cmp_[(cmp_["method"] == ROLLING) & (cmp_["scope_type"] == "emp_pooled")]
    for ref, rtok in (("edd", "Edd"), ("atc", "Atc"), ("wmdd", "Wmdd")):
        r = pooled[pooled["reference"] == ref]
        if r.empty:
            continue
        r = r.iloc[0]
        psrc = ("comparisons.csv scope_type=emp_pooled method=rollcp2 "
                "reference=%s" % ref)
        mf.add("rfroll%sDiffAll" % rtok, f_diff(r["mean_diff"]), psrc + " field=mean_diff")
        mf.add("rfroll%sCiLoAll" % rtok, f_diff(r["ci_lo"]), psrc + " field=ci_lo")
        mf.add("rfroll%sCiHiAll" % rtok, f_diff(r["ci_hi"]), psrc + " field=ci_hi")
        mf.add("rfroll%sNAll" % rtok, f_int(r["n_configs"]), psrc + " field=n_configs")
        mf.add("rfroll%sVerdictAll" % rtok, f_text(r["verdict"]), psrc + " field=verdict")
    # The stress campus is where the pooled figure comes from; disclose it.
    st = cmp_[(cmp_["method"] == ROLLING) & (cmp_["scope_type"] == "stress")
              & (cmp_["reference"] == "edd")]
    if not st.empty:
        st = st.iloc[0]
        ssrc = "comparisons.csv scope_type=stress method=rollcp2 reference=edd"
        mf.add("rfrollEddDiffStress", f_diff(st["mean_diff"]), ssrc + " field=mean_diff")
        mf.add("rfrollEddNStress", f_int(st["n_configs"]), ssrc + " field=n_configs")
        mf.add("rfrollEddVerdictStress", f_text(st["verdict"]), ssrc + " field=verdict")

    # ---- latency -------------------------------------------------------- #
    mf.section("Per-decision latency by method family (analysis/latency.csv, "
               "scope=empirical_verdict)")
    for fam, tok in ((FAMILY_RULES, "Rules"), (FAMILY_V2, "Policy"),
                     (FAMILY_ATTN, "Attn"), (FAMILY_V1, "Vone")):
        r = latency[(latency["scope"] == "empirical_verdict")
                    & (latency["family"] == fam)
                    & (latency["unit"] == "ms_per_decision")]
        if r.empty:
            continue
        r = r.iloc[0]
        lsrc = "latency.csv scope=empirical_verdict family=%s unit=ms_per_decision" % fam
        mf.add("rf%sLatMs" % tok, f_ms(r["median"]), lsrc + " field=median")
        mf.add("rf%sLatPninetyMs" % tok, f_ms(r["p90"]), lsrc + " field=p90")
    r = latency[(latency["scope"] == "empirical_verdict")
                & (latency["family"] == FAMILY_ROLL)
                & (latency["unit"] == "s_per_replan")]
    if not r.empty:
        r = r.iloc[0]
        lsrc = "latency.csv scope=empirical_verdict family=rolling unit=s_per_replan"
        mf.add("rfRollLatS", f_s(r["median"]), lsrc + " field=median")
        mf.add("rfRollLatPninetyS", f_s(r["p90"]), lsrc + " field=p90")
    for fam, tok in ((FAMILY_RULES, "Rules"), (FAMILY_V2, "Policy"),
                     (FAMILY_ATTN, "Attn")):
        r = latency[(latency["scope"] == "generator") & (latency["family"] == fam)
                    & (latency["unit"] == "ms_per_decision")]
        if r.empty:
            continue
        r = r.iloc[0]
        mf.add("rfgen%sLatMs" % tok, f_ms(r["median"]),
               "latency.csv scope=generator family=%s unit=ms_per_decision "
               "field=median" % fam)

    header = ("\n".join([
        "% macros_r4.tex -- Eval-B (R4 final evaluation) numbers.",
        "% GENERATED FILE. Do not edit by hand: rebuild with",
        "%   PYTHONPATH=src python scripts/r4_analysis.py",
        "% Every value below is transcribed by that script from a CSV in",
        "% results/r4_final/analysis/ produced in the same run; the trailing",
        "% comment names the file and the field it came from.",
        "%% Generated %s from results/r4_final/results.csv."
        % datetime.now().strftime("%Y-%m-%d %H:%M"),
        "% Sign convention: a negative paired difference means the method is",
        "% better than its comparator (weighted tardiness is minimised).",
    ]))
    text = mf.render(header)
    (paper_dir / "macros_r4.tex").write_text(text)
    return len(mf.names), sorted(mf.names)


# --------------------------------------------------------------------------- #
# LaTeX compile check.
# --------------------------------------------------------------------------- #
def check_latex(paper_dir: Path) -> str:
    """Compile a throwaway document that inputs macros_r4.tex and uses every macro."""
    import re
    src = (paper_dir / "macros_r4.tex").read_text()
    names = re.findall(r"\\newcommand\{\\([A-Za-z]+)\}", src)
    env = dict(os.environ)
    env["PATH"] = str(Path.home() / ".TinyTeX/bin/x86_64-linux") + os.pathsep + env["PATH"]
    if shutil.which("pdflatex", path=env["PATH"]) is None:
        return "pdflatex not found on PATH; compile check skipped"
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        shutil.copy(paper_dir / "macros_r4.tex", td / "macros_r4.tex")
        body = "\n".join(r"\noindent\texttt{%s}: \%s\par" % (n, n) for n in names)
        (td / "test.tex").write_text(
            "\\documentclass[10pt]{article}\n"
            "\\usepackage[margin=1in]{geometry}\n"
            "\\input{macros_r4}\n"
            "\\begin{document}\n%s\n\\end{document}\n" % body)
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
    ap.add_argument("--csv", default=str(ROOT / "results/r4_final/results.csv"))
    ap.add_argument("--meta", default=str(ROOT / "results/r4_final/meta.json"))
    ap.add_argument("--out", default=str(ROOT / "results/r4_final/analysis"))
    ap.add_argument("--paper-dir", default=str(ROOT / "paper"))
    ap.add_argument("--step", choices=("all", "analysis", "macros"), default="all")
    ap.add_argument("--n-boot", type=int, default=stats.N_BOOT)
    ap.add_argument("--seed", type=int, default=stats.SEED)
    ap.add_argument("--check-latex", action="store_true",
                    help="compile a scratch document that uses every macro")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    paper_dir = Path(args.paper_dir)
    t0 = datetime.now()

    if args.step in ("all", "analysis"):
        meta = json.loads(Path(args.meta).read_text())
        df = load_results(Path(args.csv))
        dataset = dataset_block(df, meta)
        checks = sanity_checks(df, meta, dataset)
        print("sanity: %d checks passed" % len(checks))

        df = add_pool_rows(df)
        eq = equivalence_block(df, args.n_boot, args.seed)
        print("equivalence: %d rows over %d scopes"
              % (len(eq), eq.groupby(["scope_type", "scope"]).ngroups))
        cmp_ = comparisons_block(df, args.n_boot, args.seed)
        print("comparisons: %d rows" % len(cmp_))
        pools = pools_block(df, eq, args.n_boot, args.seed)
        print("pools: %d rows" % len(pools))
        ratios = generator_ratios_block(eq)
        latency = latency_block(df)
        seeds = seed_dispersion_block(df, eq)
        camp2 = campus2_utilization_block(df)

        dataset.to_csv(out / "dataset.csv", index=False)
        eq.to_csv(out / "equivalence.csv", index=False)
        cmp_.to_csv(out / "comparisons.csv", index=False)
        pools.to_csv(out / "pools.csv", index=False)
        ratios.to_csv(out / "generator_ratios.csv", index=False)
        latency.to_csv(out / "latency.csv", index=False)
        seeds.to_csv(out / "seed_dispersion.csv", index=False)
        camp2.to_csv(out / "campus2_utilization.csv", index=False)

        headline = build_headline(dataset, eq, cmp_, pools, ratios, latency,
                                  seeds, camp2)
        (out / "headline.json").write_text(json.dumps(headline, indent=2,
                                                      sort_keys=True) + "\n")
        write_report(out, df, meta, dataset, eq, cmp_, pools, ratios, latency,
                     seeds, camp2, checks, args.n_boot, args.seed)
        (out / "meta.json").write_text(json.dumps({
            "script": "scripts/r4_analysis.py",
            "generated": t0.isoformat(timespec="seconds"),
            "elapsed_seconds": (datetime.now() - t0).total_seconds(),
            "input_csv": str(args.csv), "input_meta": str(args.meta),
            "value_col": VALUE_COL, "n_boot": args.n_boot, "seed": args.seed,
            "alpha": stats.ALPHA, "margin_abs": stats.MARGIN_ABS,
            "margin_rel": stats.MARGIN_REL,
            "verdict_campuses": list(VERDICT_CAMPUSES),
            "full_coverage_methods": list(FULL_COVERAGE),
            "pools": list(POOLS),
            "sanity_checks": checks,
        }, indent=2) + "\n")
        print("analysis written to %s (%.1f s)"
              % (out, (datetime.now() - t0).total_seconds()))

    if args.step in ("all", "macros"):
        n, names = build_macros(out, paper_dir)
        print("macros: %d written to %s" % (n, paper_dir / "macros_r4.tex"))

    if args.check_latex:
        print("latex check: %s" % check_latex(paper_dir))


if __name__ == "__main__":
    main()
