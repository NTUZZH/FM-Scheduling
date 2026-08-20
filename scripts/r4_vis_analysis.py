#!/usr/bin/env python
"""Definitive R4.6 preventive-visibility analysis: results/r4_visibility -> exhibits.

``scripts/r4_analysis.py`` is the evidence layer for Eval-B and
``scripts/r4_robust_analysis.py`` the evidence layer for the modelling-choice
checks; this script is the evidence layer for the one experiment that asks what
advance knowledge of preventive work is worth.  It reads the single visibility
results file, measures the effect of the visibility level L on every arm that
can respond to it, and returns a verdict on each of the four hypotheses R4.6
stated before the run.

Five decisions separate this analysis from a naive per-level summary.

* **The effect of visibility is a PAIRED within-arm contrast, never a
  between-method mean.**  Every configuration is evaluated at all four levels,
  so the L = 0 row of the same arm on the same configuration is the control, and
  the reported effect is the mean of the per-configuration differences.  Pooled
  level means would confound the effect with the composition of the cells.
* **The pairing key is the configuration id with its level suffix removed.**  A
  row's ``id`` is ``<shard id>_L<tag>``, so ids differ across levels and cannot
  be joined on; ``base_id`` is the base instance and is the cluster key for the
  bootstrap, not the pairing key (an empirical instance appears at three crew
  multipliers).  The intermediate key is written as ``cfg`` and is the unit a
  paired difference is taken on.
* **The three non-delay rules are excluded from every paired L-effect.**  A
  non-delay dispatcher picks only from the released queue, so edd, atc and wmdd
  are constant in L by construction; the runner scored them once at L = 0 and
  copied the row to the other three levels with ``constant_by_construction = 1``.
  Differencing a row against a copy of itself would manufacture an exact zero
  and dilute every summary it entered.  The copies are still used, once, as a
  sanity check that the spread across levels is exactly zero.
* **A visibility policy is an arm, not a knob, and its control is the SAME SEED
  at L = 0.**  The five checkpoints at level X (``vis<X>rl501..505``) and the
  five at level 0 (``vis0rl501..505``) share the widened architecture and the
  seed that initialised them, so seed 501 at level X pairs against seed 501 at
  level 0, and so on.  That pairing removes the seed-to-seed variation, which on
  the generator cells is larger than the effect being measured.  The pool-level
  contrast (the five-seed mean per configuration at level X against the
  five-seed mean at level 0) is reported beside it, because a practitioner
  deploys a pool rather than a nominated seed.  Both are in ``vis_effect.csv``.
* **The measured quantity is training AND running at level L, against training
  and running at level 0.**  The visibility policies were trained at their own
  level; the contrast therefore carries any difference the retraining produced,
  not the information alone.  The forecast-aware ATC and the rolling planner are
  single artifacts run at four levels, so for them the contrast is the
  information alone.  Sentences built on these numbers must keep that
  distinction.

All paired statistics come from ``fmwos.stats`` (protocol §R4.5): paired on the
configuration key, 95% percentile bootstrap over base-instance clusters with
10000 resamples and master seed 12345, equivalence margin
max(1.0, 1% of the comparator mean), Holm within a comparison family (here, the
three levels of one arm inside one scope).  Nothing statistical is
reimplemented, and no statistic outside that module is used.

Outputs (all under --out, default results/r4_visibility/analysis/)
-----------------------------------------------------------------
  dataset.csv            run size, cross-checked against the run's meta.json
  coverage.csv           every (method, level): rows, configurations, expected
  vis_effect.csv         BLOCK 1: paired L-effect per scope x arm x level
  hypotheses.csv         BLOCK 2: H1-H4, the verdict and the number that carries it
  replan_diagnostics.csv BLOCK 2/H3: rolling replan count, seconds and budget saturation
  arch_control.csv       BLOCK 3: the widened L=0 control against the frozen v2 pool
  win_region.csv         BLOCK 4: the win region and the negative-transfer region
  headline_vis.json      every number the manuscript cites, machine-readable
  analysis.md            the readable report
  meta.json              inputs, constants, timings, sanity-check outcomes

Usage
-----
    PYTHONPATH=src python scripts/r4_vis_analysis.py                 # analysis + macros
    PYTHONPATH=src python scripts/r4_vis_analysis.py --step analysis
    PYTHONPATH=src python scripts/r4_vis_analysis.py --step macros
    PYTHONPATH=src python scripts/r4_vis_analysis.py --check-latex

Re-running is idempotent: every output is rewritten from the same input with the
same seeds, so a second run reproduces every digit.  Macros are written to
``paper/macros_r4c.tex`` with the ``\\rfc`` prefix; ``paper/macros.tex``,
``paper/macros_r4.tex`` and ``paper/macros_r4b.tex`` are never touched and a
name collision with any of them is a hard error.
"""

from __future__ import annotations

import argparse
import json
import os
import re
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
sys.path.insert(0, str(ROOT / "scripts"))
from fmwos import stats                                    # noqa: E402
from fmwos.io import normalize_method_column               # noqa: E402
# Macro plumbing and number formatting are shared with the Eval-B analysis so the
# three generated macro files read identically.
from r4_analysis import (MacroFile, existing_macro_names,  # noqa: E402
                         f_int, f_pct, f_diff, f_twt, f_text)

# --------------------------------------------------------------------------- #
# Fixed vocabulary of the visibility run (docs/protocol.md R4.6).
# --------------------------------------------------------------------------- #
VALUE_COL = "wwt"
LEVELS = ("0", "8", "40", "full")
CONTROL_LEVEL = "0"
EFFECT_LEVELS = ("8", "40", "full")
LEVEL_BH = {"0": 0.0, "8": 8.0, "40": 40.0, "full": float("inf")}
LEVEL_LABEL = {"0": "nothing known early (status quo)",
               "8": "one shift of advance notice",
               "40": "one week of advance notice",
               "full": "the whole instance known from the start"}

VIS_SEEDS = (501, 502, 503, 504, 505)
V2_POOL = tuple("v2rl%d" % s for s in range(301, 311))
# Non-delay rules: constant in L by construction, run once at L = 0 and copied.
CONSTANT_RULES = ("edd", "atc", "wmdd")

GEN_PM = (0.2, 0.5, 0.8)
GEN_U = (0.7, 0.9, 1.1)
CREW_M = (1.0, 0.8, 0.6)
VERDICT_CAMPUSES = (5, 9, 10, 12)

ROLL_BUDGET_S = 2.0        # scripts/r4_visibility.py --rollcp-budget default
SATURATION_FRAC = 0.95     # "a replan at the budget ceiling" = >= 95% of it

REGIME_GEN = "vis-gen"
REGIME_EMP = "vis-empirical"
REGIME_LABEL = {REGIME_GEN: "generator cells (pm share x target utilization)",
                REGIME_EMP: "empirical cells (Eval-B anchors x crew multiplier)"}

# --------------------------------------------------------------------------- #
# The arms whose behaviour can depend on L, and the control each one pairs
# against.  ``members`` maps a level to the result-file method names that make up
# the arm at that level; a pool arm averages its members per configuration.
# --------------------------------------------------------------------------- #
ARMS = (
    {"arm": "atc_la", "kind": "rule", "regimes": (REGIME_GEN, REGIME_EMP),
     "label": "forecast-aware ATC",
     "note": "one artifact run at four levels: the contrast is the information "
             "alone",
     "members": {L: ("atc_la",) for L in LEVELS}},
    {"arm": "rollcp2", "kind": "optimizer", "regimes": (REGIME_EMP,),
     "label": "rolling CP-SAT (2 s budget)",
     "note": "one artifact run at four levels, empirical cells only (R4 "
             "adjustment); the contrast is the information alone",
     "members": {L: ("rollcp2",) for L in LEVELS}},
    {"arm": "vispool", "kind": "policy", "regimes": (REGIME_GEN, REGIME_EMP),
     "label": "visibility policy pool (5 seeds)",
     "note": "five checkpoints trained AND run at the level: the contrast "
             "carries the retraining as well as the information",
     "members": {L: tuple("vis%srl%d" % (L, s) for s in VIS_SEEDS)
                 for L in LEVELS}},
) + tuple(
    {"arm": "visseed%d" % s, "kind": "policy", "regimes": (REGIME_GEN, REGIME_EMP),
     "label": "visibility policy seed %d" % s,
     "note": "seed %d at the level against seed %d at level 0 (same widened "
             "architecture, same initialisation)" % (s, s),
     "members": {L: ("vis%srl%d" % (L, s),) for L in LEVELS}}
    for s in VIS_SEEDS)

ARM_BY_NAME = {a["arm"]: a for a in ARMS}
SEED_ARMS = tuple("visseed%d" % s for s in VIS_SEEDS)
POLICY_ARMS = ("vispool",) + SEED_ARMS

# --------------------------------------------------------------------------- #
# Block 4 regions.  ``pm``/``u`` are generator selectors; the win region is the
# one the sweep actually found, and it is NOT the region H2 predicted.
# --------------------------------------------------------------------------- #
REGIONS = (
    {"region": "win", "pm": (0.2,), "u": (0.9, 1.1),
     "label": "low preventive share near and above capacity "
              "(pm share 0.2, target utilization 0.9 and 1.1)"},
    {"region": "winpeak", "pm": (0.2,), "u": (1.1,),
     "label": "low preventive share above capacity "
              "(pm share 0.2, target utilization 1.1)"},
    {"region": "negative", "pm": (0.5, 0.8), "u": GEN_U,
     "label": "substantial preventive share, every utilization "
              "(pm share 0.5 and 0.8)"},
    {"region": "negativepeak", "pm": (0.8,), "u": (1.1,),
     "label": "high preventive share above capacity "
              "(pm share 0.8, target utilization 1.1)"},
)

# The scopes H1 is read on: slack capacity in each regime.
SLACK_SCOPES = ("gen|u=0.7", "emp|m=1.0")


# --------------------------------------------------------------------------- #
# Loading.
# --------------------------------------------------------------------------- #
def load_results(csv: Path) -> pd.DataFrame:
    """The visibility results file with the pairing key and the level attached.

    ``cfg`` is the row's configuration id with its ``_L<tag>`` suffix removed:
    one instance x crew multiplier x generator cell, evaluated at four levels.
    It is the key a paired difference is taken on.  ``base_id`` (written by the
    runner) is the cluster key and is cross-checked in :func:`sanity_checks`.
    """
    df = pd.read_csv(csv)
    df = normalize_method_column(df)
    for c in ("id", "method", "visibility_L", "base_id", "regime"):
        df[c] = df[c].astype(str)
    df["campus"] = df["campus"].astype(int)
    df["cfg"] = df["id"].str.replace(r"_L(?:0|8|40|full)$", "", regex=True)
    return df


def build_long(df: pd.DataFrame) -> pd.DataFrame:
    """One row per (configuration, arm, level), with pool arms already averaged.

    The ``method`` column carries ``<arm>@L<level>`` so ``fmwos.stats`` can pair
    an arm at a level against the same arm at level 0 with its ordinary
    two-method machinery, on ``id_col="cfg"``.  Rows flagged
    ``constant_by_construction`` never enter this frame: they are copies of a
    level-0 row, and differencing them would report a manufactured zero.
    """
    src = df[df["constant_by_construction"] == 0]
    keys = ["cfg", "base_id", "regime", "campus", "crew_multiplier",
            "pm_share", "u_target", "size"]
    out = []
    for spec in ARMS:
        for L in LEVELS:
            members = [m for m in spec["members"][L]
                       if m in set(src["method"])]
            if not members:
                continue
            sub = src[(src["method"].isin(members))
                      & (src["visibility_L"] == L)]
            if sub.empty:
                continue
            g = (sub.groupby(keys, dropna=False)
                    .agg(wwt=(VALUE_COL, "mean"),
                         n_members=(VALUE_COL, "size"),
                         feasible=("feasible", "min"))
                    .reset_index())
            g["arm"] = spec["arm"]
            g["level"] = L
            g["method"] = "%s@L%s" % (spec["arm"], L)
            out.append(g)
    long = pd.concat(out, ignore_index=True)
    return long


# --------------------------------------------------------------------------- #
# Scopes.
# --------------------------------------------------------------------------- #
def scope_frames(long: pd.DataFrame):
    """Yield ``(scope, regime, keys, subframe)`` in report order.

    Generator scopes are the whole regime, the three utilization marginals, the
    three preventive-share marginals and the nine cells of the design; empirical
    scopes are the whole regime and the three crew multipliers.  Marginals exist
    because H1 and H2 are stated over a row of the grid, not over one cell.
    """
    gen = long[long["regime"] == REGIME_GEN]
    emp = long[long["regime"] == REGIME_EMP]
    yield "gen|ALL", REGIME_GEN, {}, gen
    for u in GEN_U:
        yield "gen|u=%.1f" % u, REGIME_GEN, {"u_target": u}, gen[gen["u_target"] == u]
    for pm in GEN_PM:
        yield ("gen|pm=%.1f" % pm, REGIME_GEN, {"pm_share": pm},
               gen[gen["pm_share"] == pm])
    for pm in GEN_PM:
        for u in GEN_U:
            yield ("gen|pm=%.1f|u=%.1f" % (pm, u), REGIME_GEN,
                   {"pm_share": pm, "u_target": u},
                   gen[(gen["pm_share"] == pm) & (gen["u_target"] == u)])
    yield "emp|ALL", REGIME_EMP, {}, emp
    for m in CREW_M:
        yield ("emp|m=%.1f" % m, REGIME_EMP, {"crew_multiplier": m},
               emp[emp["crew_multiplier"] == m])


# --------------------------------------------------------------------------- #
# Block 1: the paired visibility effect, per scope x arm x level.
# --------------------------------------------------------------------------- #
EFFECT_COLUMNS = ["scope", "regime", "arm", "arm_kind", "level", "level_bh",
                  "n_configs", "n_clusters", "mean_control", "mean_level",
                  "mean_diff", "pct_of_control", "ci_lo", "ci_hi",
                  "pct_ci_lo", "pct_ci_hi", "margin", "wilcoxon_p", "holm_p",
                  "verdict"]


def _pct(x, base):
    return float("nan") if base == 0 else 100.0 * float(x) / float(base)


def effect_rows(sub: pd.DataFrame, scope: str, regime: str, n_boot: int,
                seed: int) -> list:
    """Paired L-effect of every arm present in one scope, all levels at once.

    One ``fmwos.stats.compare_all`` call per arm, so the Holm family is the
    three levels of that arm inside that scope: the three comparisons a reader
    looks at together.
    """
    rows = []
    for spec in ARMS:
        if regime not in spec["regimes"]:
            continue
        arm = spec["arm"]
        s = sub[sub["arm"] == arm].copy()
        ctrl = "%s@L%s" % (arm, CONTROL_LEVEL)
        levels = [L for L in EFFECT_LEVELS
                  if "%s@L%s" % (arm, L) in set(s["method"])]
        if ctrl not in set(s["method"]) or not levels:
            continue
        s["scope"] = scope
        cmp_ = stats.compare_all(
            s, reference_methods=[ctrl],
            methods=["%s@L%s" % (arm, L) for L in levels],
            scope_cols=("scope",), value_col=VALUE_COL, id_col="cfg",
            feasible_col="feasible",
            family_of=lambda m, r, _a=arm: "visibility-%s" % _a,
            n_boot=n_boot, seed=seed)
        for r in cmp_.itertuples():
            L = r.method.split("@L")[1]
            base = float(r.mean_ref)
            rows.append({
                "scope": scope, "regime": regime, "arm": arm,
                "arm_kind": spec["kind"], "level": L,
                "level_bh": LEVEL_BH[L],
                "n_configs": int(r.n_configs), "n_clusters": int(r.n_clusters),
                "mean_control": base, "mean_level": float(r.mean_method),
                "mean_diff": float(r.mean_diff),
                "pct_of_control": _pct(r.mean_diff, base),
                "ci_lo": float(r.ci_lo), "ci_hi": float(r.ci_hi),
                "pct_ci_lo": _pct(r.ci_lo, base),
                "pct_ci_hi": _pct(r.ci_hi, base),
                "margin": float(r.margin), "wilcoxon_p": float(r.wilcoxon_p),
                "holm_p": float(r.holm_p), "verdict": str(r.verdict),
            })
    return rows


def effect_block(long: pd.DataFrame, n_boot: int, seed: int) -> pd.DataFrame:
    rows = []
    for scope, regime, _keys, sub in scope_frames(long):
        if sub.empty:
            continue
        rows.extend(effect_rows(sub, scope, regime, n_boot, seed))
    return pd.DataFrame(rows, columns=EFFECT_COLUMNS)


# --------------------------------------------------------------------------- #
# Block 3: the widened L = 0 control against the frozen pre-visibility pool.
# --------------------------------------------------------------------------- #
def arch_block(df: pd.DataFrame, n_boot: int, seed: int) -> pd.DataFrame:
    """The visibility policy family against the frozen pre-visibility pool.

    Two questions, one table.  At L = 0, ``vis0rl501..505`` and
    ``v2rl301..310`` both run with nothing known early; the first has the
    widened input the lookahead features need, the second is the frozen pool the
    rest of the paper reports, so a difference there is a property of the
    retrained control and not of visibility.  At L = 8, 40 and full the same
    contrast asks whether advance knowledge closes whatever gap the retraining
    opened, which is the only form in which a visibility gain is a claim about
    the best available option rather than about one family's internal ordering.

    Seeds cannot be paired across the two pools (different seed blocks and
    different curricula), so every row is a pool-mean contrast on the same
    configurations, with the frozen pool as the reference.
    """
    src = df[df["constant_by_construction"] == 0]
    keys = ["cfg", "base_id", "regime", "crew_multiplier", "pm_share", "u_target"]

    def pool(members, level, name):
        s = src[src["method"].isin(members) & (src["visibility_L"] == level)]
        g = (s.groupby(keys, dropna=False)
               .agg(wwt=(VALUE_COL, "mean"), feasible=("feasible", "min"))
               .reset_index())
        g["method"] = name
        return g

    v2 = pool(V2_POOL, CONTROL_LEVEL, "v2pool")
    rows = []
    for L in LEVELS:
        members = tuple("vis%srl%d" % (L, s) for s in VIS_SEEDS)
        frame = pd.concat([pool(members, L, "vispool"), v2], ignore_index=True)
        scopes = ([("gen|ALL", frame[frame["regime"] == REGIME_GEN])]
                  + [("gen|u=%.1f" % u,
                      frame[(frame["regime"] == REGIME_GEN)
                            & (frame["u_target"] == u)]) for u in GEN_U]
                  + [("gen|pm=%.1f|u=%.1f" % (pm, u),
                      frame[(frame["regime"] == REGIME_GEN)
                            & (frame["pm_share"] == pm) & (frame["u_target"] == u)])
                     for pm in GEN_PM for u in GEN_U]
                  + [("emp|ALL", frame[frame["regime"] == REGIME_EMP])]
                  + [("emp|m=%.1f" % m,
                      frame[(frame["regime"] == REGIME_EMP)
                            & (frame["crew_multiplier"] == m)]) for m in CREW_M])
        for scope, sub in scopes:
            if sub.empty:
                continue
            sub = sub.copy()
            sub["scope"] = "%s|L%s" % (scope, L)
            cmp_ = stats.compare_all(sub, reference_methods=["v2pool"],
                                     methods=["vispool"], scope_cols=("scope",),
                                     value_col=VALUE_COL, id_col="cfg",
                                     feasible_col="feasible",
                                     family_of=lambda m, r: "architecture-control",
                                     n_boot=n_boot, seed=seed)
            for r in cmp_.itertuples():
                base = float(r.mean_ref)
                rows.append({
                    "scope": scope, "level": L,
                    "regime": REGIME_GEN if scope.startswith("gen") else REGIME_EMP,
                    "n_configs": int(r.n_configs), "n_clusters": int(r.n_clusters),
                    "mean_v2": base, "mean_vis": float(r.mean_method),
                    "mean_diff": float(r.mean_diff),
                    "pct_of_v2": _pct(r.mean_diff, base),
                    "ci_lo": float(r.ci_lo), "ci_hi": float(r.ci_hi),
                    "pct_ci_lo": _pct(r.ci_lo, base),
                    "pct_ci_hi": _pct(r.ci_hi, base),
                    "margin": float(r.margin), "wilcoxon_p": float(r.wilcoxon_p),
                    "verdict": str(r.verdict)})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Block 4: the win region and the negative-transfer region.
# --------------------------------------------------------------------------- #
def region_block(long: pd.DataFrame, n_boot: int, seed: int) -> pd.DataFrame:
    """Per region x arm x level: the effect, and how many seed pairs move with it.

    ``n_seeds_improved`` counts the five seed-level contrasts whose mean paired
    difference is negative, and ``n_seeds_better`` the ones whose whole interval
    clears the equivalence margin on the better side.  The two counts are the
    honest reading of a pool number: a pool effect carried by one seed and a
    pool effect five seeds agree on are different findings.
    """
    gen = long[long["regime"] == REGIME_GEN]
    rows = []
    for reg in REGIONS:
        sub = gen[gen["pm_share"].isin(reg["pm"]) & gen["u_target"].isin(reg["u"])]
        if sub.empty:
            continue
        scope = "region|%s" % reg["region"]
        eff = pd.DataFrame(effect_rows(sub, scope, REGIME_GEN, n_boot, seed),
                           columns=EFFECT_COLUMNS)
        for L in EFFECT_LEVELS:
            at = eff[eff["level"] == L]
            seeds = at[at["arm"].isin(SEED_ARMS)]
            for arm in ("vispool", "atc_la") + SEED_ARMS:
                r = at[at["arm"] == arm]
                if r.empty:
                    continue
                r = r.iloc[0]
                rows.append({
                    "region": reg["region"], "region_label": reg["label"],
                    "pm_shares": ",".join("%.1f" % p for p in reg["pm"]),
                    "u_targets": ",".join("%.1f" % u for u in reg["u"]),
                    "arm": arm, "level": L,
                    "n_configs": int(r["n_configs"]),
                    "n_clusters": int(r["n_clusters"]),
                    "mean_control": float(r["mean_control"]),
                    "mean_diff": float(r["mean_diff"]),
                    "pct_of_control": float(r["pct_of_control"]),
                    "ci_lo": float(r["ci_lo"]), "ci_hi": float(r["ci_hi"]),
                    "pct_ci_lo": float(r["pct_ci_lo"]),
                    "pct_ci_hi": float(r["pct_ci_hi"]),
                    "verdict": str(r["verdict"]),
                    "n_seeds": int(len(seeds)),
                    "n_seeds_improved": int((seeds["mean_diff"] < 0).sum()),
                    "n_seeds_better": int((seeds["verdict"] == "better").sum()),
                    "n_seeds_worse": int((seeds["verdict"] == "worse").sum()),
                    "seed_pct_min": float(seeds["pct_of_control"].min()),
                    "seed_pct_max": float(seeds["pct_of_control"].max()),
                })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Block 2 (H3 mechanism): what visibility does to the rolling planner's replans.
# --------------------------------------------------------------------------- #
def replan_block(df: pd.DataFrame, n_boot: int, seed: int) -> pd.DataFrame:
    """Replan count, seconds per replan and budget saturation, per scope x level.

    H3 assumed replanning stays feasible.  A known-but-unreleased order enlarges
    every snapshot the planner solves, and the budget is fixed at 2 s, so the
    diagnostic that decides whether the assumption held is how close a replan
    now runs to that ceiling.  ``d_*`` columns are PAIRED against the same
    configuration at L = 0, with the same cluster bootstrap as every other
    interval in this analysis.
    """
    roll = df[df["method"] == "rollcp2"].copy()
    scopes = [("emp|ALL", roll)] + [("emp|m=%.1f" % m,
                                     roll[roll["crew_multiplier"] == m])
                                    for m in CREW_M]
    rows = []
    for scope, sub in scopes:
        base = sub[sub["visibility_L"] == CONTROL_LEVEL].set_index("cfg")
        for L in LEVELS:
            at = sub[sub["visibility_L"] == L].set_index("cfg")
            row = {"scope": scope, "level": L, "level_bh": LEVEL_BH[L],
                   "n_configs": int(len(at)),
                   "mean_replans": float(at["decisions"].mean()),
                   "mean_replan_s": float(at["mean_replan_s"].mean()),
                   "median_replan_s": float(at["mean_replan_s"].median()),
                   "max_replan_s": float(at["mean_replan_s"].max()),
                   "budget_s": ROLL_BUDGET_S,
                   "share_saturated": float(
                       (at["mean_replan_s"] >= SATURATION_FRAC * ROLL_BUDGET_S).mean()),
                   "mean_wall_s": float(at["wall_seconds"].mean())}
            if L == CONTROL_LEVEL:
                row.update({"d_replans": 0.0, "d_replans_lo": 0.0,
                            "d_replans_hi": 0.0, "d_replan_s": 0.0,
                            "d_replan_s_lo": 0.0, "d_replan_s_hi": 0.0})
            else:
                j = at.join(base, how="inner", rsuffix="_0")
                cl = j["base_id"].to_numpy()
                for col, out in (("decisions", "d_replans"),
                                 ("mean_replan_s", "d_replan_s")):
                    d = (j[col].astype(float) - j[col + "_0"].astype(float)).to_numpy()
                    lo, hi = stats.cluster_bootstrap_ci(
                        d, cl, n_boot=n_boot,
                        seed=stats._derived_seed(seed, "%s|%s|%s" % (scope, L, col)))
                    row[out] = float(d.mean())
                    row[out + "_lo"], row[out + "_hi"] = float(lo), float(hi)
            rows.append(row)
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Block 2: the four pre-stated hypotheses, each with the number that carries it.
# --------------------------------------------------------------------------- #
H_TEXT = {
    "H1": "visibility has negligible value under slack capacity",
    "H2": "visibility becomes valuable near capacity when preventive work is a "
          "substantial share of workload",
    "H3": "rolling optimization benefits more from visibility than myopic "
          "rules, provided replanning remains feasible",
    "H4": "the learned policy gains only if the lookahead features carry "
          "information a fixed rule cannot summarize",
}


def _e(eff, scope, arm, level):
    r = eff[(eff["scope"] == scope) & (eff["arm"] == arm) & (eff["level"] == level)]
    return None if r.empty else r.iloc[0]


def _cite(r) -> str:
    if r is None:
        return "-"
    return ("%s %s at L=%s: %+.3f%% [%+.3f, %+.3f], %s"
            % (r["scope"], r["arm"], r["level"], r["pct_of_control"],
               r["pct_ci_lo"], r["pct_ci_hi"], r["verdict"]))


def hypothesis_block(eff: pd.DataFrame, region: pd.DataFrame,
                     replan: pd.DataFrame) -> pd.DataFrame:
    rows = []

    # ---- H1: slack ------------------------------------------------------ #
    # The carrier is the largest effect among the arms that can actually USE
    # advance knowledge (the forecast-aware rule and the policies).  The rolling
    # planner is reported beside it rather than inside it: its one non-equivalent
    # slack contrast is a solver-budget effect, not an information effect, and
    # averaging the two kinds of arm together would hide both.
    slack = eff[eff["scope"].isin(SLACK_SCOPES)]
    info = slack[slack["arm"] != "rollcp2"]
    worst = info.loc[info["pct_of_control"].abs().idxmax()]
    n_equiv = int((slack["verdict"] == "equivalent").sum())
    exc = slack[slack["verdict"] != "equivalent"]
    rows.append({
        "hypothesis": "H1", "statement": H_TEXT["H1"], "verdict": "supported",
        "carrier": ("under slack capacity the largest visibility effect over "
                    "every arm that can read advance knowledge is %+.3f%% of the "
                    "same arm's own L=0 mean, and %d of the %d arm-level "
                    "contrasts are practically equivalent"
                    % (worst["pct_of_control"], n_equiv, len(slack))),
        "scope": worst["scope"], "arm": worst["arm"], "level": worst["level"],
        "pct": float(worst["pct_of_control"]),
        "pct_ci_lo": float(worst["pct_ci_lo"]),
        "pct_ci_hi": float(worst["pct_ci_hi"]),
        "stat_verdict": str(worst["verdict"]),
        "detail": "%s | %s" % (
            _cite(worst),
            ("every slack contrast is equivalent" if exc.empty else
             "the only slack contrast outside equivalence is the rolling "
             "planner, %s, which is the solver budget and not the information"
             % "; ".join(_cite(r) for _, r in exc.iterrows())))})

    # ---- H2: near capacity, substantial preventive share ---------------- #
    win = _e(eff, "gen|pm=0.2|u=1.1", "vispool", "40")
    hi_pm = _e(eff, "gen|pm=0.8|u=1.1", "vispool", "40")
    mid_pm = _e(eff, "gen|pm=0.5|u=1.1", "vispool", "40")
    rows.append({
        "hypothesis": "H2", "statement": H_TEXT["H2"],
        "verdict": "not supported as stated; the gain region is the opposite "
                   "preventive share",
        "carrier": ("the policy pool gains only where preventive work is a "
                    "SMALL share and capacity is exceeded, and loses where the "
                    "preventive share is high (pm 0.5: %+.1f%%, pm 0.8: %+.1f%%, "
                    "both at u=1.1, L=40)"
                    % (mid_pm["pct_of_control"], hi_pm["pct_of_control"])),
        "scope": win["scope"], "arm": win["arm"], "level": win["level"],
        "pct": float(win["pct_of_control"]),
        "pct_ci_lo": float(win["pct_ci_lo"]),
        "pct_ci_hi": float(win["pct_ci_hi"]),
        "stat_verdict": str(win["verdict"]),
        "detail": "%s | H2's own region: %s" % (_cite(win), _cite(hi_pm))})

    # ---- H3: rolling benefits more than the myopic rules ---------------- #
    roll = eff[(eff["arm"] == "rollcp2")]
    best_roll = roll.loc[roll["pct_of_control"].idxmin()]
    worst_roll = roll.loc[roll["pct_of_control"].idxmax()]
    r0 = replan[(replan["scope"] == "emp|ALL") & (replan["level"] == "0")].iloc[0]
    rL = replan[(replan["scope"] == "emp|ALL") & (replan["level"] == "40")].iloc[0]
    rows.append({
        "hypothesis": "H3", "statement": H_TEXT["H3"],
        "verdict": "not supported: no visibility gain for the rolling planner "
                   "at any level or crew multiplier",
        "carrier": ("across the %d rolling contrasts (the pooled empirical "
                    "scope and the three crew multipliers, each at three "
                    "levels) the effect runs from %+.3f%% to %+.3f%% and no "
                    "interval clears the margin on the better side; the replan "
                    "diagnostic is consistent with "
                    "budget dilution, mean seconds per replan %.2f s at L=0 "
                    "against %.2f s at L=40 on a fixed %.0f s budget, and the "
                    "share of configurations whose mean replan sits at %.0f%% "
                    "of the budget rises from %.0f%% to %.0f%%"
                    % (len(roll), best_roll["pct_of_control"],
                       worst_roll["pct_of_control"],
                       r0["mean_replan_s"], rL["mean_replan_s"], ROLL_BUDGET_S,
                       100 * SATURATION_FRAC, 100 * r0["share_saturated"],
                       100 * rL["share_saturated"])),
        "scope": worst_roll["scope"], "arm": "rollcp2",
        "level": worst_roll["level"],
        "pct": float(worst_roll["pct_of_control"]),
        "pct_ci_lo": float(worst_roll["pct_ci_lo"]),
        "pct_ci_hi": float(worst_roll["pct_ci_hi"]),
        "stat_verdict": str(worst_roll["verdict"]),
        "detail": "best %s | worst %s" % (_cite(best_roll), _cite(worst_roll))})

    # ---- H4: the policy gains only where a rule cannot summarize -------- #
    atc_win = _e(eff, "gen|pm=0.2|u=1.1", "atc_la", "40")
    rows.append({
        "hypothesis": "H4", "statement": H_TEXT["H4"],
        "verdict": "supported where the policy gains, with a boundary the "
                   "hypothesis did not anticipate",
        "carrier": ("in the one region where advance knowledge pays, the policy "
                    "pool gains %.1f%% while the forecast-aware rule reading the "
                    "same future work gains %.2f%%; where the preventive share "
                    "is high the same policies are %.1f%% WORSE than their own "
                    "L=0 control, so the lookahead input is not free"
                    % (abs(win["pct_of_control"]), abs(atc_win["pct_of_control"]),
                       hi_pm["pct_of_control"])),
        "scope": win["scope"], "arm": "vispool vs atc_la", "level": "40",
        "pct": float(win["pct_of_control"]),
        "pct_ci_lo": float(win["pct_ci_lo"]),
        "pct_ci_hi": float(win["pct_ci_hi"]),
        "stat_verdict": str(win["verdict"]),
        "detail": "%s | rule: %s | negative transfer: %s"
                  % (_cite(win), _cite(atc_win), _cite(hi_pm))})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Dataset table, coverage table and sanity checks.
# --------------------------------------------------------------------------- #
def dataset_block(df: pd.DataFrame, meta: dict) -> pd.DataFrame:
    rows = []
    for label, sub in (("all", df), (REGIME_GEN, df[df["regime"] == REGIME_GEN]),
                       (REGIME_EMP, df[df["regime"] == REGIME_EMP])):
        rows.append({
            "scope": label, "n_rows": int(len(sub)),
            "n_ids": int(sub["id"].nunique()),
            "n_configs": int(sub["cfg"].nunique()),
            "n_clusters": int(sub["base_id"].nunique()),
            "n_levels": int(sub["visibility_L"].nunique()),
            "n_methods": int(sub["method"].nunique()),
            "n_infeasible": int((sub["feasible"] != 1).sum()),
            "n_constant_rows": int((sub["constant_by_construction"] == 1).sum()),
        })
    d = pd.DataFrame(rows)
    d["n_errors"] = int(meta.get("n_errors_this_run", 0))
    d["elapsed_seconds"] = float(meta.get("elapsed_seconds", float("nan")))
    return d


def expected_configs(method: str, level: str, df: pd.DataFrame) -> int:
    """How many configurations a (method, level) pair must cover, by design."""
    n_all = int(df["cfg"].nunique())
    n_roll = int(df[df["method"] == "rollcp2"]["cfg"].nunique())
    if method == "rollcp2":
        return n_roll
    if method in V2_POOL:
        return n_all if level == CONTROL_LEVEL else 0
    m = re.fullmatch(r"vis(0|8|40|full)rl(\d+)", method)
    if m:
        return n_all if level == m.group(1) else 0
    return n_all                       # rules and atc_la: every configuration


def coverage_block(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for method in sorted(df["method"].unique()):
        for level in LEVELS:
            sub = df[(df["method"] == method) & (df["visibility_L"] == level)]
            rows.append({
                "method": method, "level": level,
                "n_rows": int(len(sub)),
                "n_configs": int(sub["cfg"].nunique()),
                "expected_configs": expected_configs(method, level, df),
                "constant_by_construction":
                    int(sub["constant_by_construction"].max()) if len(sub) else 0,
                "n_gen": int(sub[sub["regime"] == REGIME_GEN]["cfg"].nunique()),
                "n_emp": int(sub[sub["regime"] == REGIME_EMP]["cfg"].nunique()),
                "mean_wwt": float(sub[VALUE_COL].mean()) if len(sub) else float("nan"),
            })
    return pd.DataFrame(rows)


def sanity_checks(df: pd.DataFrame, long: pd.DataFrame, dataset: pd.DataFrame,
                  coverage: pd.DataFrame, meta: dict) -> list:
    """Assertions that must hold before any number is written; raises on failure."""
    checks = []

    def plain(v):
        """numpy scalars and arrays -> JSON-serialisable python, recursively."""
        if isinstance(v, (list, tuple, np.ndarray)):
            return [plain(x) for x in v]
        if isinstance(v, np.generic):
            return v.item()
        return v

    def require(name, got, want):
        got, want = plain(got), plain(want)
        ok = (got == want)
        checks.append({"check": name, "got": got, "want": want, "ok": bool(ok)})
        if not ok:
            raise SystemExit("sanity check failed: %s (got %r, want %r)"
                             % (name, got, want))

    d = dataset.set_index("scope")
    require("rows vs meta.json", int(d.loc["all", "n_rows"]), int(meta["n_rows"]))
    require("configurations vs meta.json",
            int(d.loc["all", "n_configs"]), int(meta["n_configs"]))
    require("infeasible vs meta.json",
            int(d.loc["all", "n_infeasible"]), int(meta["n_infeasible"]))
    require("errors vs meta.json", int(meta["n_errors_this_run"]), 0)
    require("levels", int(d.loc["all", "n_levels"]), len(LEVELS))
    require("evaluated ids = configurations x levels",
            int(d.loc["all", "n_ids"]), int(meta["n_configs"]) * len(LEVELS))
    for regime, key in ((REGIME_GEN, "vis-gen"), (REGIME_EMP, "vis-empirical")):
        require("%s configurations vs meta.json" % regime,
                int(d.loc[regime, "n_configs"]),
                int(meta["n_configs_by_regime"][key]))
    require("visibility arms missing (meta.json)",
            sum(int(v) for v in meta["vis_arms_missing"].values()), 0)

    # Coverage: every (method, level) cell holds exactly the configurations the
    # design says it should, and nothing else.
    bad = coverage[coverage["n_configs"] != coverage["expected_configs"]]
    require("every (method, level) covers its designed configurations",
            int(len(bad)), 0)
    require("methods scored", int(df["method"].nunique()),
            len(CONSTANT_RULES) + 2 + len(V2_POOL) + len(LEVELS) * len(VIS_SEEDS))
    require("rolling configurations vs meta.json",
            int(df[df["method"] == "rollcp2"]["cfg"].nunique()),
            int(meta["n_rollcp_configs"]))
    require("rolling runs on the empirical cells only",
            sorted(df[df["method"] == "rollcp2"]["regime"].unique()), [REGIME_EMP])

    # The pairing key and the cluster key: the runner writes base_id explicitly
    # because the level suffix lives on the config id.  Both must agree with the
    # library's own derivation, or the intervals are computed on the wrong unit.
    require("base_id equals the library's cluster derivation from id",
            bool((df["id"].map(stats.base_instance_id) == df["base_id"]).all()), True)
    require("cluster derived from the pairing key equals base_id",
            bool((df["cfg"].map(stats.base_instance_id) == df["base_id"]).all()), True)
    require("every configuration carries every level",
            int(df.groupby("cfg")["visibility_L"].nunique().min()), len(LEVELS))
    require("clusters", int(df["base_id"].nunique()), 720)

    # The three non-delay rules are copies across levels: prove the copy is
    # exact, then prove no copied row reaches a paired effect.
    const = df[df["constant_by_construction"] == 1]
    require("constant-by-construction methods",
            sorted(const["method"].unique()), sorted(CONSTANT_RULES))
    piv = const.pivot_table(index=["cfg", "method"], columns="visibility_L",
                            values=VALUE_COL)
    require("constant rules are identical at every level (max spread)",
            float((piv.max(axis=1) - piv.min(axis=1)).abs().max()), 0.0)
    require("no constant-by-construction row enters a paired L-effect",
            int(long["arm"].isin(CONSTANT_RULES).sum()), 0)

    # Generator design and empirical design.
    gen = df[df["regime"] == REGIME_GEN].drop_duplicates("cfg")
    require("generator cells", int(gen.groupby(["pm_share", "u_target"]).ngroups),
            len(GEN_PM) * len(GEN_U))
    require("generator configurations per cell",
            sorted(gen.groupby(["pm_share", "u_target"]).size().unique()), [60])
    require("generator campuses", sorted(gen["campus"].unique()),
            list(VERDICT_CAMPUSES))
    emp = df[df["regime"] == REGIME_EMP].drop_duplicates("cfg")
    require("empirical crew multipliers", sorted(emp["crew_multiplier"].unique()),
            sorted(CREW_M))
    require("empirical base instances per crew multiplier",
            sorted(emp.groupby("crew_multiplier")["base_id"].nunique().unique()), [180])
    require("empirical campuses", sorted(emp["campus"].unique()),
            list(VERDICT_CAMPUSES))
    require("no missing objective value", int(df[VALUE_COL].isna().sum()), 0)

    # The seed pairing block 1 relies on: the five level-0 checkpoints and the
    # five at each other level carry the same seed numbers.
    for L in LEVELS:
        require("visibility seeds at L=%s" % L,
                sorted(int(m.split("rl")[1]) for m in df["method"].unique()
                       if m.startswith("vis%srl" % L)), list(VIS_SEEDS))
    return checks


# --------------------------------------------------------------------------- #
# headline_vis.json
# --------------------------------------------------------------------------- #
def _num(x):
    v = float(x)
    return None if not np.isfinite(v) else v


def _effect_dict(r) -> dict:
    return {"scope": str(r["scope"]), "arm": str(r["arm"]),
            "level": str(r["level"]), "n_configs": int(r["n_configs"]),
            "n_clusters": int(r["n_clusters"]),
            "mean_control": _num(r["mean_control"]),
            "mean_diff": _num(r["mean_diff"]),
            "pct_of_control": _num(r["pct_of_control"]),
            "ci_lo": _num(r["ci_lo"]), "ci_hi": _num(r["ci_hi"]),
            "pct_ci_lo": _num(r["pct_ci_lo"]), "pct_ci_hi": _num(r["pct_ci_hi"]),
            "verdict": str(r["verdict"])}


def build_headline(dataset, coverage, eff, hyp, replan, arch, region,
                   meta) -> dict:
    d = dataset.set_index("scope")
    H = {
        "dataset": {
            "n_rows": int(d.loc["all", "n_rows"]),
            "n_configs": int(d.loc["all", "n_configs"]),
            "n_ids": int(d.loc["all", "n_ids"]),
            "n_clusters": int(d.loc["all", "n_clusters"]),
            "n_methods": int(d.loc["all", "n_methods"]),
            "n_levels": len(LEVELS),
            "n_configs_generator": int(d.loc[REGIME_GEN, "n_configs"]),
            "n_configs_empirical": int(d.loc[REGIME_EMP, "n_configs"]),
            "n_infeasible": int(d.loc["all", "n_infeasible"]),
            "n_rolling_configs": int(
                coverage[(coverage["method"] == "rollcp2")
                         & (coverage["level"] == "0")]["n_configs"].iloc[0]),
            "elapsed_seconds": float(meta.get("elapsed_seconds", float("nan"))),
        },
        "hypotheses": {r["hypothesis"]: {
            "statement": r["statement"], "verdict": r["verdict"],
            "carrier": r["carrier"], "scope": r["scope"], "arm": r["arm"],
            "level": r["level"], "pct": _num(r["pct"]),
            "pct_ci_lo": _num(r["pct_ci_lo"]), "pct_ci_hi": _num(r["pct_ci_hi"]),
            "stat_verdict": r["stat_verdict"], "detail": r["detail"]}
            for r in hyp.to_dict("records")},
        "effects": {"%s|%s|L%s" % (r["scope"], r["arm"], r["level"]):
                    _effect_dict(r) for r in eff.to_dict("records")},
        "regions": {"%s|%s|L%s" % (r["region"], r["arm"], r["level"]): {
            "label": r["region_label"], "n_configs": int(r["n_configs"]),
            "mean_control": _num(r["mean_control"]),
            "mean_diff": _num(r["mean_diff"]),
            "pct_of_control": _num(r["pct_of_control"]),
            "pct_ci_lo": _num(r["pct_ci_lo"]), "pct_ci_hi": _num(r["pct_ci_hi"]),
            "verdict": r["verdict"], "n_seeds": int(r["n_seeds"]),
            "n_seeds_improved": int(r["n_seeds_improved"]),
            "n_seeds_better": int(r["n_seeds_better"]),
            "n_seeds_worse": int(r["n_seeds_worse"]),
            "seed_pct_min": _num(r["seed_pct_min"]),
            "seed_pct_max": _num(r["seed_pct_max"])}
            for r in region.to_dict("records")},
        "architecture_control": {"%s|L%s" % (r["scope"], r["level"]): {
            "n_configs": int(r["n_configs"]), "mean_v2": _num(r["mean_v2"]),
            "mean_vis": _num(r["mean_vis"]), "mean_diff": _num(r["mean_diff"]),
            "pct_of_v2": _num(r["pct_of_v2"]), "pct_ci_lo": _num(r["pct_ci_lo"]),
            "pct_ci_hi": _num(r["pct_ci_hi"]), "verdict": r["verdict"]}
            for r in arch.to_dict("records")},
        "replan_diagnostics": {"%s|L%s" % (r["scope"], r["level"]): {
            "n_configs": int(r["n_configs"]),
            "mean_replans": _num(r["mean_replans"]),
            "mean_replan_s": _num(r["mean_replan_s"]),
            "share_saturated": _num(r["share_saturated"]),
            "d_replans": _num(r["d_replans"]),
            "d_replan_s": _num(r["d_replan_s"]),
            "d_replan_s_lo": _num(r["d_replan_s_lo"]),
            "d_replan_s_hi": _num(r["d_replan_s_hi"]),
            "budget_s": ROLL_BUDGET_S} for r in replan.to_dict("records")},
    }
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


def write_report(out: Path, dataset, coverage, eff, hyp, replan, arch, region,
                 checks, n_boot, seed) -> None:
    L = []
    A = L.append
    A("# R4.6 preventive-visibility definitive analysis\n")
    A("Input: `results/r4_visibility/results.csv`. Statistics: `fmwos.stats`, "
      "protocol §R4.5, %d bootstrap resamples over base-instance clusters, "
      "master seed %d, equivalence margin max(1.0, 1%% of the comparator mean), "
      "Holm within the three levels of one arm inside one scope. A NEGATIVE "
      "effect means the level is better than the same arm at L = 0.\n"
      % (n_boot, seed))
    A("\nWhat is paired with what. Every configuration is scored at all four "
      "levels, so the control is the SAME arm on the SAME configuration at "
      "L = 0. The pairing key is the configuration id without its `_L<tag>` "
      "suffix; the cluster key is `base_id`, the base instance. For the "
      "visibility policies the arm at level X is the checkpoint trained at "
      "level X, and it pairs against the checkpoint trained at level 0 with the "
      "identical widened architecture and the same seed number, seed by seed; "
      "the pool row is the five-seed mean per configuration on each side. The "
      "policy contrast therefore carries the retraining as well as the "
      "information, while the forecast-aware ATC and the rolling planner are "
      "single artifacts run at four levels and carry the information alone.\n")
    A("\nThe three non-delay rules (edd, atc, wmdd) are constant in L by "
      "construction and were scored once and copied; the copies are excluded "
      "from every paired effect and are used only to check that the spread "
      "across levels is exactly zero.\n")

    A("\n## 0. Run size and coverage\n")
    A(_md_table(dataset, ["scope", "n_rows", "n_ids", "n_configs", "n_clusters",
                          "n_levels", "n_methods", "n_infeasible",
                          "n_constant_rows"]))
    A("\nEvery (method, level) cell against the coverage the design requires:\n")
    A(_md_table(coverage[coverage["n_rows"] > 0],
                ["method", "level", "n_rows", "n_configs", "expected_configs",
                 "n_gen", "n_emp", "constant_by_construction", "mean_wwt"],
                {"mean_wwt": lambda v: _fmt(v, 1)}))

    A("\n## 1. The paired visibility effect, per scope, arm and level\n")
    A("`pct_of_control` is the mean paired difference as a percentage of the "
      "arm's own mean at L = 0 on the same configurations.\n")
    for regime in (REGIME_GEN, REGIME_EMP):
        A("\n### %s\n" % REGIME_LABEL[regime])
        sub = eff[eff["regime"] == regime]
        A(_md_table(sub, ["scope", "arm", "level", "n_configs", "n_clusters",
                          "mean_control", "mean_diff", "pct_of_control",
                          "pct_ci_lo", "pct_ci_hi", "verdict"],
                    {"mean_control": lambda v: _fmt(v, 1),
                     "mean_diff": lambda v: _fmt(v, 2),
                     "pct_of_control": lambda v: _fmt(v, 3),
                     "pct_ci_lo": lambda v: _fmt(v, 3),
                     "pct_ci_hi": lambda v: _fmt(v, 3)}))

    A("\n## 2. The four pre-stated hypotheses\n")
    for r in hyp.to_dict("records"):
        A("\n**%s. %s**\n" % (r["hypothesis"], r["statement"]))
        A("\nVerdict: %s.\n" % r["verdict"])
        A("\nCarried by: %s.\n" % r["carrier"])
        A("\nNumbers: %s\n" % r["detail"])
    A("\n### H3 mechanism: what visibility does to the rolling planner\n")
    A("A known-but-unreleased order enlarges every snapshot the planner solves "
      "while the budget stays at %.0f s, so `share_saturated` (configurations "
      "whose mean replan reaches %.0f%% of the budget) is the diagnostic that "
      "decides whether replanning stayed feasible. `d_*` columns are paired "
      "against L = 0 on the same configurations.\n"
      % (ROLL_BUDGET_S, 100 * SATURATION_FRAC))
    A(_md_table(replan, ["scope", "level", "n_configs", "mean_replans",
                         "mean_replan_s", "median_replan_s", "share_saturated",
                         "d_replans", "d_replan_s", "d_replan_s_lo",
                         "d_replan_s_hi", "mean_wall_s"],
                {"mean_replans": lambda v: _fmt(v, 1),
                 "mean_wall_s": lambda v: _fmt(v, 1)}))

    A("\n## 3. The visibility policy family against the frozen v2 pool\n")
    A("At L = 0 both pools run with nothing known early, so a difference is a "
      "property of the retrained control and not of visibility; it bounds how "
      "far the visibility arms' ABSOLUTE levels may be read against the frozen "
      "pool the rest of the paper reports. At the other three levels the same "
      "contrast asks whether advance knowledge closes whatever gap the "
      "retraining opened.\n")
    A(_md_table(arch, ["scope", "level", "n_configs", "n_clusters", "mean_v2",
                       "mean_vis", "mean_diff", "pct_of_v2", "pct_ci_lo",
                       "pct_ci_hi", "verdict"],
                {"mean_v2": lambda v: _fmt(v, 1),
                 "mean_vis": lambda v: _fmt(v, 1),
                 "mean_diff": lambda v: _fmt(v, 2)}))

    A("\n## 4. The win region and the negative-transfer region\n")
    aw0 = arch[(arch["scope"] == "gen|pm=0.2|u=1.1") & (arch["level"] == "0")].iloc[0]
    aw4 = arch[(arch["scope"] == "gen|pm=0.2|u=1.1") & (arch["level"] == "40")].iloc[0]
    A("Read the win region against section 3 before quoting it. The gain is "
      "measured inside the visibility family, and in this cell that family "
      "starts %.0f%% above the frozen v2 pool at L = 0 and is still %.0f%% "
      "above it at L = 40 (%s against %s weighted units). Advance knowledge is "
      "therefore worth a measured amount to a policy trained to use it, and it "
      "does not make that policy the best available option on these giant "
      "generator cells.\n"
      % (aw0["pct_of_v2"], aw4["pct_of_v2"], _fmt(aw4["mean_vis"], 0),
         _fmt(aw4["mean_v2"], 0)))
    A("\n`n_seeds_improved` counts the five seed-level contrasts with a negative "
      "mean difference and `n_seeds_better` the ones whose whole interval "
      "clears the margin on the better side. A pool effect one seed carries and "
      "a pool effect five seeds agree on are different findings, so both counts "
      "are reported with the pool number.\n")
    A(_md_table(region[region["arm"].isin(("vispool", "atc_la"))],
                ["region", "arm", "level", "n_configs", "mean_control",
                 "mean_diff", "pct_of_control", "pct_ci_lo", "pct_ci_hi",
                 "verdict", "n_seeds_improved", "n_seeds_better",
                 "n_seeds_worse", "seed_pct_min", "seed_pct_max"],
                {"mean_control": lambda v: _fmt(v, 1),
                 "mean_diff": lambda v: _fmt(v, 2),
                 "pct_of_control": lambda v: _fmt(v, 2),
                 "seed_pct_min": lambda v: _fmt(v, 2),
                 "seed_pct_max": lambda v: _fmt(v, 2)}))
    A("\nPer seed, in the same regions:\n")
    A(_md_table(region[region["arm"].isin(SEED_ARMS)],
                ["region", "arm", "level", "n_configs", "mean_control",
                 "mean_diff", "pct_of_control", "pct_ci_lo", "pct_ci_hi",
                 "verdict"],
                {"mean_control": lambda v: _fmt(v, 1),
                 "mean_diff": lambda v: _fmt(v, 2),
                 "pct_of_control": lambda v: _fmt(v, 2)}))

    A("\n## 5. Sanity checks\n")
    A(_md_table(pd.DataFrame(checks), ["check", "got", "want", "ok"]))
    (out / "analysis.md").write_text("\n".join(L))


# --------------------------------------------------------------------------- #
# Macros (paper/macros_r4c.tex).
# --------------------------------------------------------------------------- #
class VisMacroFile(MacroFile):
    """MacroFile that names WHICH existing file a colliding macro came from."""

    def __init__(self, sources: dict):
        self.source_of = {n: p for p, names in sources.items() for n in names}
        super().__init__(set(self.source_of))

    def add(self, name, value, source):
        if not name.startswith("rfc"):
            raise SystemExit("macro %r does not use the \\rfc prefix" % name)
        if name in self.source_of:
            raise SystemExit("macro %r is already defined in %s"
                             % (name, self.source_of[name]))
        super().add(name, value, source)


def f_sec(x) -> str:
    return "%.2f" % float(x)


def f_share(x) -> str:
    """A share written as a whole percentage."""
    return "%.0f" % (100.0 * float(x))


def build_macros(out: Path, paper_dir: Path) -> tuple:
    """Read this run's CSVs back from disk and write paper/macros_r4c.tex."""
    dataset = pd.read_csv(out / "dataset.csv")
    eff = pd.read_csv(out / "vis_effect.csv")
    hyp = pd.read_csv(out / "hypotheses.csv")
    replan = pd.read_csv(out / "replan_diagnostics.csv")
    arch = pd.read_csv(out / "arch_control.csv")
    region = pd.read_csv(out / "win_region.csv")
    d = dataset.set_index("scope")

    mf = VisMacroFile({
        "paper/macros.tex": existing_macro_names(paper_dir / "macros.tex"),
        "paper/macros_r4.tex": existing_macro_names(paper_dir / "macros_r4.tex"),
        "paper/macros_r4b.tex": existing_macro_names(paper_dir / "macros_r4b.tex"),
    })

    def E(scope, arm, level):
        r = eff[(eff["scope"] == scope) & (eff["arm"] == arm)
                & (eff["level"] == level)]
        if r.empty:
            raise SystemExit("no effect row for %s / %s / L%s" % (scope, arm, level))
        return r.iloc[0]

    def R(reg, arm, level):
        r = region[(region["region"] == reg) & (region["arm"] == arm)
                   & (region["level"] == level)]
        if r.empty:
            raise SystemExit("no region row for %s / %s / L%s" % (reg, arm, level))
        return r.iloc[0]

    def triple(prefix, r, src, pct_col="pct_of_control"):
        """A percentage effect and its two interval endpoints, one source note."""
        mf.add(prefix + "Pct", f_pct(r[pct_col]), src + " field=%s" % pct_col)
        mf.add(prefix + "CiLo", f_pct(r["pct_ci_lo"]), src + " field=pct_ci_lo")
        mf.add(prefix + "CiHi", f_pct(r["pct_ci_hi"]), src + " field=pct_ci_hi")

    # ---- 0. run size ---------------------------------------------------- #
    mf.section("R4.6 visibility run size (analysis/dataset.csv)")
    for name, field in (("rfcConfigs", "n_configs"), ("rfcRows", "n_rows"),
                        ("rfcEvaluated", "n_ids"), ("rfcClusters", "n_clusters"),
                        ("rfcMethods", "n_methods")):
        mf.add(name, f_int(d.loc["all", field]),
               "dataset.csv scope=all field=%s" % field)
    mf.add("rfcGenConfigs", f_int(d.loc[REGIME_GEN, "n_configs"]),
           "dataset.csv scope=vis-gen field=n_configs")
    mf.add("rfcEmpConfigs", f_int(d.loc[REGIME_EMP, "n_configs"]),
           "dataset.csv scope=vis-empirical field=n_configs")
    mf.add("rfcLevels", f_int(len(LEVELS)),
           "scripts/r4_vis_analysis.py LEVELS (0, 8, 40 business hours and full)")
    mf.add("rfcVisSeeds", f_int(len(VIS_SEEDS)),
           "scripts/r4_vis_analysis.py VIS_SEEDS (checkpoints per level)")
    mf.add("rfcRollConfigs",
           f_int(replan[(replan["scope"] == "emp|ALL")
                        & (replan["level"] == "0")]["n_configs"].iloc[0]),
           "replan_diagnostics.csv scope=emp|ALL level=0 field=n_configs "
           "(the rolling planner's empirical subsample)")

    # ---- 1. H1, slack ---------------------------------------------------- #
    mf.section("H1, visibility is worth nothing under slack capacity "
               "(analysis/vis_effect.csv, analysis/hypotheses.csv)")
    h1 = hyp[hyp["hypothesis"] == "H1"].iloc[0]
    slack = eff[eff["scope"].isin(SLACK_SCOPES)]
    mf.add("rfcHoneMaxAbsPct", f_pct(abs(float(h1["pct"]))),
           "hypotheses.csv hypothesis=H1 field=pct, absolute value (the largest "
           "visibility effect under slack capacity over every arm that can read "
           "advance knowledge: %s at L=%s in %s)"
           % (h1["arm"], h1["level"], h1["scope"]))
    mf.add("rfcHoneContrasts", f_int(len(slack)),
           "vis_effect.csv rows with scope in %s (arm-level contrasts under "
           "slack capacity)" % (list(SLACK_SCOPES),))
    mf.add("rfcHoneEquivalent", f_int(int((slack["verdict"] == "equivalent").sum())),
           "vis_effect.csv rows with scope in %s and verdict=equivalent"
           % (list(SLACK_SCOPES),))
    triple("rfcHoneGenPolicy", E("gen|u=0.7", "vispool", "40"),
           "vis_effect.csv scope=gen|u=0.7 arm=vispool level=40")
    triple("rfcHoneEmpPolicy", E("emp|m=1.0", "vispool", "40"),
           "vis_effect.csv scope=emp|m=1.0 arm=vispool level=40")
    triple("rfcHoneGenRule", E("gen|u=0.7", "atc_la", "40"),
           "vis_effect.csv scope=gen|u=0.7 arm=atc_la level=40")

    # ---- 2. H2, near capacity -------------------------------------------- #
    mf.section("H2, the gain region is the LOW preventive share, not the high "
               "one (analysis/vis_effect.csv)")
    triple("rfcHtwoWin", E("gen|pm=0.2|u=1.1", "vispool", "40"),
           "vis_effect.csv scope=gen|pm=0.2|u=1.1 arm=vispool level=40")
    triple("rfcHtwoPmMid", E("gen|pm=0.5|u=1.1", "vispool", "40"),
           "vis_effect.csv scope=gen|pm=0.5|u=1.1 arm=vispool level=40")
    triple("rfcHtwoPmHigh", E("gen|pm=0.8|u=1.1", "vispool", "40"),
           "vis_effect.csv scope=gen|pm=0.8|u=1.1 arm=vispool level=40")
    triple("rfcHtwoWinMid", E("gen|pm=0.2|u=0.9", "vispool", "40"),
           "vis_effect.csv scope=gen|pm=0.2|u=0.9 arm=vispool level=40")

    # ---- 3. H3, rolling --------------------------------------------------- #
    mf.section("H3, the rolling planner gains nothing from visibility, and the "
               "replan diagnostic says why (analysis/vis_effect.csv, "
               "analysis/replan_diagnostics.csv)")
    roll = eff[eff["arm"] == "rollcp2"]
    best = roll.loc[roll["pct_of_control"].idxmin()]
    worst = roll.loc[roll["pct_of_control"].idxmax()]
    mf.add("rfcHthreeBestPct", f_pct(best["pct_of_control"]),
           "vis_effect.csv arm=rollcp2, most negative pct_of_control "
           "(scope=%s level=%s)" % (best["scope"], best["level"]))
    mf.add("rfcHthreeWorstPct", f_pct(worst["pct_of_control"]),
           "vis_effect.csv arm=rollcp2, most positive pct_of_control "
           "(scope=%s level=%s)" % (worst["scope"], worst["level"]))
    mf.add("rfcHthreeWorstCiLo", f_pct(worst["pct_ci_lo"]),
           "vis_effect.csv arm=rollcp2 scope=%s level=%s field=pct_ci_lo"
           % (worst["scope"], worst["level"]))
    mf.add("rfcHthreeWorstCiHi", f_pct(worst["pct_ci_hi"]),
           "vis_effect.csv arm=rollcp2 scope=%s level=%s field=pct_ci_hi"
           % (worst["scope"], worst["level"]))
    mf.add("rfcHthreeWorstVerdict", f_text(worst["verdict"]),
           "vis_effect.csv arm=rollcp2 scope=%s level=%s field=verdict"
           % (worst["scope"], worst["level"]))
    mf.add("rfcHthreeContrasts", f_int(len(roll)),
           "vis_effect.csv rows with arm=rollcp2 (scope x level contrasts)")
    mf.add("rfcHthreeBetter",
           f_int(int((roll["verdict"] == "better").sum())),
           "vis_effect.csv rows with arm=rollcp2 and verdict=better")
    triple("rfcHthreePooled", E("emp|ALL", "rollcp2", "40"),
           "vis_effect.csv scope=emp|ALL arm=rollcp2 level=40")
    r0 = replan[(replan["scope"] == "emp|ALL") & (replan["level"] == "0")].iloc[0]
    rL = replan[(replan["scope"] == "emp|ALL") & (replan["level"] == "40")].iloc[0]
    mf.add("rfcHthreeBudget", "%.0f" % ROLL_BUDGET_S,
           "scripts/r4_vis_analysis.py ROLL_BUDGET_S (rolling CP-SAT budget, s)")
    mf.add("rfcHthreeReplanZero", f_sec(r0["mean_replan_s"]),
           "replan_diagnostics.csv scope=emp|ALL level=0 field=mean_replan_s")
    mf.add("rfcHthreeReplanFull", f_sec(rL["mean_replan_s"]),
           "replan_diagnostics.csv scope=emp|ALL level=40 field=mean_replan_s")
    mf.add("rfcHthreeReplanDelta", f_sec(rL["d_replan_s"]),
           "replan_diagnostics.csv scope=emp|ALL level=40 field=d_replan_s "
           "(paired against the same configurations at L=0)")
    mf.add("rfcHthreeReplanDeltaLo", f_sec(rL["d_replan_s_lo"]),
           "replan_diagnostics.csv scope=emp|ALL level=40 field=d_replan_s_lo")
    mf.add("rfcHthreeReplanDeltaHi", f_sec(rL["d_replan_s_hi"]),
           "replan_diagnostics.csv scope=emp|ALL level=40 field=d_replan_s_hi")
    mf.add("rfcHthreeReplansZero", "%.0f" % float(r0["mean_replans"]),
           "replan_diagnostics.csv scope=emp|ALL level=0 field=mean_replans")
    mf.add("rfcHthreeReplansFull", "%.0f" % float(rL["mean_replans"]),
           "replan_diagnostics.csv scope=emp|ALL level=40 field=mean_replans")
    mf.add("rfcHthreeSatZero", f_share(r0["share_saturated"]),
           "replan_diagnostics.csv scope=emp|ALL level=0 field=share_saturated "
           "(share of configurations whose mean replan reaches 95% of the budget)")
    mf.add("rfcHthreeSatFull", f_share(rL["share_saturated"]),
           "replan_diagnostics.csv scope=emp|ALL level=40 field=share_saturated")

    # ---- 4. H4, the policy against the rule ------------------------------- #
    mf.section("H4, the policy gains where a fixed rule cannot summarize the "
               "future, and pays for the input elsewhere "
               "(analysis/vis_effect.csv)")
    # The forecast-aware rule's largest effect anywhere IS its effect in the
    # policy's win cell, so one set of names serves both the H4 contrast and the
    # "what a transparent rule can extract from the same future work" sentence.
    atc_all = eff[eff["arm"] == "atc_la"]
    amax = atc_all.loc[atc_all["pct_of_control"].abs().idxmax()]
    mf.add("rfcAtcMaxPct", f_pct(amax["pct_of_control"]),
           "vis_effect.csv arm=atc_la, largest absolute pct_of_control "
           "(scope=%s level=%s; also the H4 comparison cell)"
           % (amax["scope"], amax["level"]))
    mf.add("rfcAtcMaxCiLo", f_pct(amax["pct_ci_lo"]),
           "vis_effect.csv arm=atc_la scope=%s level=%s field=pct_ci_lo"
           % (amax["scope"], amax["level"]))
    mf.add("rfcAtcMaxCiHi", f_pct(amax["pct_ci_hi"]),
           "vis_effect.csv arm=atc_la scope=%s level=%s field=pct_ci_hi"
           % (amax["scope"], amax["level"]))
    mf.add("rfcAtcMaxVerdict", f_text(amax["verdict"]),
           "vis_effect.csv arm=atc_la scope=%s level=%s field=verdict"
           % (amax["scope"], amax["level"]))

    # ---- 5. the win region ------------------------------------------------ #
    mf.section("The win condition: low preventive share at or above capacity "
               "(analysis/win_region.csv)")
    wp = R("winpeak", "vispool", "40")
    triple("rfcWin", wp, "win_region.csv region=winpeak arm=vispool level=40")
    mf.add("rfcWinDiff", f_diff(wp["mean_diff"]),
           "win_region.csv region=winpeak arm=vispool level=40 field=mean_diff")
    mf.add("rfcWinControl", f_twt(wp["mean_control"]),
           "win_region.csv region=winpeak arm=vispool level=40 field=mean_control")
    mf.add("rfcWinConfigs", f_int(wp["n_configs"]),
           "win_region.csv region=winpeak arm=vispool level=40 field=n_configs")
    mf.add("rfcWinVerdict", f_text(wp["verdict"]),
           "win_region.csv region=winpeak arm=vispool level=40 field=verdict")
    mf.add("rfcWinSeedsImproved", f_int(wp["n_seeds_improved"]),
           "win_region.csv region=winpeak level=40 field=n_seeds_improved "
           "(seed pairs with a negative mean difference)")
    mf.add("rfcWinSeedsBetter", f_int(wp["n_seeds_better"]),
           "win_region.csv region=winpeak level=40 field=n_seeds_better "
           "(seed pairs whose whole interval clears the margin)")
    mf.add("rfcWinSeeds", f_int(wp["n_seeds"]),
           "win_region.csv region=winpeak level=40 field=n_seeds")
    mf.add("rfcWinSeedBest", f_pct(wp["seed_pct_min"]),
           "win_region.csv region=winpeak level=40 field=seed_pct_min")
    mf.add("rfcWinSeedWorst", f_pct(wp["seed_pct_max"]),
           "win_region.csv region=winpeak level=40 field=seed_pct_max")
    wb = R("win", "vispool", "40")
    triple("rfcWinBand", wb, "win_region.csv region=win arm=vispool level=40")
    mf.add("rfcWinBandConfigs", f_int(wb["n_configs"]),
           "win_region.csv region=win arm=vispool level=40 field=n_configs")
    mf.add("rfcWinBandSeedsImproved", f_int(wb["n_seeds_improved"]),
           "win_region.csv region=win level=40 field=n_seeds_improved")
    ws = R("winpeak", "vispool", "8")
    triple("rfcWinShift", ws, "win_region.csv region=winpeak arm=vispool level=8")

    # ---- 6. negative transfer --------------------------------------------- #
    mf.section("The boundary: negative transfer where preventive work is a "
               "substantial share (analysis/win_region.csv)")
    np_ = R("negativepeak", "vispool", "40")
    triple("rfcNeg", np_, "win_region.csv region=negativepeak arm=vispool level=40")
    mf.add("rfcNegConfigs", f_int(np_["n_configs"]),
           "win_region.csv region=negativepeak arm=vispool level=40 field=n_configs")
    mf.add("rfcNegVerdict", f_text(np_["verdict"]),
           "win_region.csv region=negativepeak arm=vispool level=40 field=verdict")
    mf.add("rfcNegSeedsWorse", f_int(np_["n_seeds_worse"]),
           "win_region.csv region=negativepeak level=40 field=n_seeds_worse")
    nr = R("negative", "vispool", "40")
    triple("rfcNegRegion", nr, "win_region.csv region=negative arm=vispool level=40")
    mf.add("rfcNegRegionConfigs", f_int(nr["n_configs"]),
           "win_region.csv region=negative arm=vispool level=40 field=n_configs")

    # ---- 7. the architecture control -------------------------------------- #
    mf.section("Sanity and boundary: the visibility policy family against the "
               "frozen v2 pool (analysis/arch_control.csv)")

    def A(scope, level):
        r = arch[(arch["scope"] == scope) & (arch["level"] == level)]
        if r.empty:
            raise SystemExit("no architecture row for %s / L%s" % (scope, level))
        return r.iloc[0]

    for tok, scope in (("Emp", "emp|ALL"), ("Gen", "gen|ALL")):
        r = A(scope, "0")
        src = "arch_control.csv scope=%s level=0" % scope
        mf.add("rfcArch" + tok + "Pct", f_pct(r["pct_of_v2"]),
               src + " field=pct_of_v2 (the widened L=0 control minus the "
                     "frozen v2 pool, both with nothing known early)")
        mf.add("rfcArch" + tok + "CiLo", f_pct(r["pct_ci_lo"]), src + " field=pct_ci_lo")
        mf.add("rfcArch" + tok + "CiHi", f_pct(r["pct_ci_hi"]), src + " field=pct_ci_hi")
        mf.add("rfcArch" + tok + "Diff", f_diff(r["mean_diff"]),
               src + " field=mean_diff")
        mf.add("rfcArch" + tok + "Verdict", f_text(r["verdict"]),
               src + " field=verdict")
    # The win cell, where the internal contrast is largest: how far the family
    # still sits from the frozen pool before and after advance knowledge.
    for tok, level in (("Zero", "0"), ("Week", "40")):
        r = A("gen|pm=0.2|u=1.1", level)
        src = "arch_control.csv scope=gen|pm=0.2|u=1.1 level=%s" % level
        mf.add("rfcArchWin" + tok + "Pct", f_pct(r["pct_of_v2"]),
               src + " field=pct_of_v2 (the visibility family against the "
                     "frozen v2 pool in the win cell)")
        mf.add("rfcArchWin" + tok + "CiLo", f_pct(r["pct_ci_lo"]), src + " field=pct_ci_lo")
        mf.add("rfcArchWin" + tok + "CiHi", f_pct(r["pct_ci_hi"]), src + " field=pct_ci_hi")
        mf.add("rfcArchWin" + tok + "Mean", f_twt(r["mean_vis"]),
               src + " field=mean_vis")
    mf.add("rfcArchWinFrozen", f_twt(A("gen|pm=0.2|u=1.1", "0")["mean_v2"]),
           "arch_control.csv scope=gen|pm=0.2|u=1.1 field=mean_v2 (the frozen "
           "v2 pool's own mean in the win cell)")

    header = ("%% paper/macros_r4c.tex -- generated by scripts/r4_vis_analysis.py\n"
              "%% Source: results/r4_visibility/analysis/ (R4.6 preventive "
              "visibility).\n"
              "%% Every value is read back from the CSV named in its comment; "
              "do not edit by hand.\n"
              "%% Prefix \\rfc; no name here is defined in macros.tex, "
              "macros_r4.tex or macros_r4b.tex.\n"
              "%% A NEGATIVE effect means the visibility level is better than "
              "the same arm at L = 0.\n")
    (paper_dir / "macros_r4c.tex").write_text(mf.render(header))
    return len(mf.names), sorted(mf.names)


# --------------------------------------------------------------------------- #
# LaTeX compile check.
# --------------------------------------------------------------------------- #
def check_latex(paper_dir: Path, name: str = "macros_r4c") -> str:
    """Compile a throwaway document that inputs the macro file and uses every macro."""
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
    ap.add_argument("--results", default=str(ROOT / "results/r4_visibility/results.csv"))
    ap.add_argument("--meta", default=str(ROOT / "results/r4_visibility/meta.json"))
    ap.add_argument("--out", default=str(ROOT / "results/r4_visibility/analysis"))
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
        df = load_results(Path(args.results))
        long = build_long(df)
        dataset = dataset_block(df, meta)
        coverage = coverage_block(df)
        checks = sanity_checks(df, long, dataset, coverage, meta)
        print("sanity: %d checks passed" % len(checks))

        eff = effect_block(long, args.n_boot, args.seed)
        print("effects: %d rows over %d scopes" % (len(eff), eff["scope"].nunique()))
        replan = replan_block(df, args.n_boot, args.seed)
        arch = arch_block(df, args.n_boot, args.seed)
        region = region_block(long, args.n_boot, args.seed)
        hyp = hypothesis_block(eff, region, replan)
        print("regions: %d rows; architecture control: %d scopes"
              % (len(region), len(arch)))

        dataset.to_csv(out / "dataset.csv", index=False)
        coverage.to_csv(out / "coverage.csv", index=False)
        eff.to_csv(out / "vis_effect.csv", index=False)
        hyp.to_csv(out / "hypotheses.csv", index=False)
        replan.to_csv(out / "replan_diagnostics.csv", index=False)
        arch.to_csv(out / "arch_control.csv", index=False)
        region.to_csv(out / "win_region.csv", index=False)

        headline = build_headline(dataset, coverage, eff, hyp, replan, arch,
                                  region, meta)
        (out / "headline_vis.json").write_text(
            json.dumps(headline, indent=2, sort_keys=True) + "\n")
        write_report(out, dataset, coverage, eff, hyp, replan, arch, region,
                     checks, args.n_boot, args.seed)
        (out / "meta.json").write_text(json.dumps({
            "script": "scripts/r4_vis_analysis.py",
            "generated": t0.isoformat(timespec="seconds"),
            "elapsed_seconds": (datetime.now() - t0).total_seconds(),
            "inputs": {"results": str(args.results), "meta": str(args.meta)},
            "value_col": VALUE_COL, "n_boot": args.n_boot, "seed": args.seed,
            "alpha": stats.ALPHA, "margin_abs": stats.MARGIN_ABS,
            "margin_rel": stats.MARGIN_REL,
            "levels": list(LEVELS), "control_level": CONTROL_LEVEL,
            "pairing_key": "config id with the _L<tag> suffix removed",
            "cluster_key": "base_id (the base instance)",
            "arms": {a["arm"]: {"kind": a["kind"], "label": a["label"],
                                "regimes": list(a["regimes"]), "note": a["note"]}
                     for a in ARMS},
            "excluded_constant_by_construction": list(CONSTANT_RULES),
            "rolling_budget_s": ROLL_BUDGET_S,
            "saturation_fraction": SATURATION_FRAC,
            "sanity_checks": checks,
        }, indent=2) + "\n")
        print("analysis written to %s (%.1f s)"
              % (out, (datetime.now() - t0).total_seconds()))

    if args.step in ("all", "macros"):
        n, _names = build_macros(out, paper_dir)
        print("macros: %d written to %s" % (n, paper_dir / "macros_r4c.tex"))

    if args.check_latex:
        print("latex check: %s" % check_latex(paper_dir))


if __name__ == "__main__":
    main()
