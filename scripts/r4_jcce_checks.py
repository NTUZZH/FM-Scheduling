#!/usr/bin/env python
"""Independence, influence and multiplicity checks on the frozen Eval-B results.

Three questions raised in review can be answered from the released,
stored per-configuration results without running a new experiment.  This
script answers them with the released statistical primitives (paired
per-instance TWT differences, 95% cluster bootstrap with the base instance as
the cluster, margin max(1.0 weighted unit, 1% of the comparator mean), the
four-way verdict of docs/protocol.md R4.5) and writes one CSV per check plus a
macro file for the manuscript.

  A. Development-overlap subset.  The final empirical instances that share no
     work order with ANY released development-corpus window, in either split,
     are the development-independent subset (overlap_devcorpus.csv,
     n_shared_wos == 0).  The family-versus-EDD verdicts of the three crew
     multipliers are recomputed on that subset alone.
  B. Campus-2 leave-one-instance-out.  Each of the 17 campus-2 base instances
     is dropped in turn from each rung of the capacity ladder (p95 reference,
     p90, p75), and the paired difference, interval and verdict of WMDD, ATC
     and WSPT against EDD are recomputed on the remaining 16.
  C. Multiplicity.  The 27 comparisons of the confirmatory family (9 families
     x 3 crew multipliers on the verdict campuses) are re-read at a
     Bonferroni-adjusted level, alpha = 0.05/27, that is 99.81% intervals.
     The released code carries no TOST-style equivalence p-value (its
     Wilcoxon/Holm columns test a zero difference, not equivalence), so only
     the interval adjustment is applied.
  D. Two-level bootstrap.  The stored seed-plus-instance bootstrap is read back
     at the three empirical crew-multiplier scopes and printed beside the
     primary verdicts.

Step 0 (run first, aborts on mismatch) reproduces four released macro values
from the stored per-configuration results through this script's own comparison
driver: the family equivalence counts at crew multipliers 1.0, 0.8 and 0.6
(\\ffempEquivMfull = 9, \\ffempEquivMeighty = 6, \\ffempEquivMsixty = 3) and the
campus-2 p90 WMDD-versus-EDD difference with its interval
(\\ffCtwoQninetyWmddDiff = -353.0, [-740.7, -59.9], better).

Determinism.  Every bootstrap stream is derived from the released master seed
12345 through fmwos.stats._derived_seed on an explicit label, so a re-run
reproduces every digit.  The Analysis C streams use the released primary
labels, so the 99.81% interval is the same resample distribution as the
released 95% interval read at a wider percentile and is nested inside it; the
script asserts that the 95% read of those streams equals the released file.

Reads
-----
  results/r4_final/results.csv                       per-configuration Eval-B scores
  results/r4_robustness/capacity/results.csv         p90 and p75 crew rungs
  results/r4_final/analysis/overlap_devcorpus.csv    work-order sharing with the development corpus
  results/r4_final/analysis/family_comparisons.csv   released primary verdicts (guard only)
  results/r4_final/analysis/family_robust.csv        released campus-2 ladder (guard only)
  results/r4_final/analysis/seed_bootstrap.csv       stored two-level bootstrap

Writes
------
  results/r4_final/analysis/jcce_checks/overlap_subset.csv
  results/r4_final/analysis/jcce_checks/campus2_loo.csv               one row per rung and rule
  results/r4_final/analysis/jcce_checks/campus2_loo_drops.csv         one row per rung, rule and dropped instance
  results/r4_final/analysis/jcce_checks/campus2_loo_per_instance.csv  one row per rung, rule and instance
  results/r4_final/analysis/jcce_checks/multiplicity.csv
  results/r4_final/analysis/jcce_checks/twolevel_pools.csv
  paper_jcce/macros_jcce.tex

Usage
-----
    PYTHONPATH=src python scripts/r4_jcce_checks.py
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from fmwos import stats                                        # noqa: E402
from fmwos.io import normalize_method_column                   # noqa: E402
from r4_analysis import (CREW_MULTIPLIERS, RULES, VALUE_COL,    # noqa: E402
                         VERDICT_CAMPUSES, M_TOKEN, house_number,
                         f_diff, f_int, f_pct, f_twt, load_results)
from r4_family_analysis import (CAP_ARMS, CAP_BASE_ARM,         # noqa: E402
                                CAP_SCORED_RULES, FAMILY_KEYS, FAMILY_NAME,
                                POOL_SEEDS, REL_CAPACITY, REL_EVALB)
from r4_robust_analysis import load_evalb                       # noqa: E402
from r4_family_analysis import collapse_families                # noqa: E402

# --------------------------------------------------------------------------- #
# Fixed vocabulary of these checks.
# --------------------------------------------------------------------------- #
REFERENCE = "edd"
STRESS_CAMPUS = 2
N_BOOT = stats.N_BOOT
SEED = stats.SEED

REL_OVERLAP_DEV = "results/r4_final/analysis/overlap_devcorpus.csv"
REL_FAMILY = "results/r4_final/analysis/family_comparisons.csv"
REL_ROBUST = "results/r4_final/analysis/family_robust.csv"
REL_SEEDBOOT = "results/r4_final/analysis/seed_bootstrap.csv"
REL_OUT = "results/r4_final/analysis/jcce_checks"

# The confirmatory family of the manuscript: nine method families compared with
# EDD on each of the three crew multipliers of the verdict campuses.
CONFIRMATORY_SCOPES = CREW_MULTIPLIERS
CONFIRMATORY_CELLS = len(FAMILY_KEYS[1:]) * len(CONFIRMATORY_SCOPES)  # 9 x 3

# Leave-one-out check: the three rungs of the campus-2 capacity ladder and the
# three transparent rules whose campus-2 result the manuscript quotes.
LOO_RULES = ("wmdd", "atc", "wspt")
CAP_META = ["base_instance_id", "campus", "size", "u_realized"]

# Macro tokens.
FAMILY_TOKEN = {"pfifo": "Pfifo", "wspt": "Wspt", "atc": "Atc", "wmdd": "Wmdd",
                "lpt": "Lpt", "random": "Random", "mlp_pool": "Mlp",
                "attn_pool": "Attn", "v1_pool": "Vone"}
FAMILY_PROSE = {"pfifo": "pFIFO", "wspt": "WSPT", "atc": "ATC", "wmdd": "WMDD",
                "lpt": "LPT", "random": "random", "mlp_pool": "the MLP pool",
                "attn_pool": "the attention pool",
                "v1_pool": "the curriculum-v1 pool"}
ARM_TOKEN = {"q0.95": "Qninetyfive", "q0.90": "Qninety", "q0.75": "Qseventyfive"}
POOL_TOKEN = {"mlp_pool": "Mlp", "attn_pool": "Attn", "v1_pool": "Vone"}
VERDICT_ORDER = ("equivalent", "better", "inconclusive", "worse")
VERDICT_TOKEN = {"equivalent": "Equiv", "better": "Better",
                 "inconclusive": "Inconc", "worse": "Worse"}
# The manuscript's four verdict phrases, and the markers its tables use.
VERDICT_PHRASE = {"equivalent": "practically equivalent",
                  "better": "strictly better", "worse": "confirmed worse",
                  "inconclusive": "inconclusive", "none": "none"}
VERDICT_MARK = {"equivalent": "$\\equiv$", "better": "$\\ast$",
                "worse": "$\\ddagger$", "inconclusive": "$\\circ$"}


# --------------------------------------------------------------------------- #
# One comparison driver, used by every check.
# --------------------------------------------------------------------------- #
def paired_row(sub: pd.DataFrame, method: str, label: str, alpha: float = stats.ALPHA,
               reference: str = REFERENCE, n_boot: int = N_BOOT,
               seed: int = SEED) -> dict:
    """One family paired against EDD on one frame, at one interval level.

    ``label`` is the bootstrap stream label; the resample draw depends on it and
    on nothing else, so two calls that share a label share a draw and their
    intervals are nested by construction.
    """
    pt = stats.paired_table(sub, method, reference, value_col=VALUE_COL)
    if pt.empty:
        return {}
    d = pt["diff"].to_numpy(dtype=float)
    mean_ref = float(pt["value_b"].mean())
    lo, hi = stats.cluster_bootstrap_ci(
        d, pt["cluster"].to_numpy() if "cluster" in pt.columns else pt["cluster"],
        n_boot=n_boot, alpha=alpha, seed=stats._derived_seed(seed, label))
    return {"family": FAMILY_NAME.get(method, method),
            "n_configs": int(len(pt)), "n_clusters": int(pt["cluster"].nunique()),
            "mean_edd": mean_ref, "mean_family": float(pt["value_a"].mean()),
            "mean_diff": float(d.mean()), "ci_lo": lo, "ci_hi": hi,
            "margin": stats.equivalence_margin(mean_ref),
            "verdict": stats.equivalence_verdict(lo, hi, mean_ref)}


def compare_families(sub: pd.DataFrame, label_prefix: str, methods=FAMILY_KEYS,
                     alpha: float = stats.ALPHA, n_boot: int = N_BOOT,
                     seed: int = SEED) -> pd.DataFrame:
    """Every family of ``methods`` against EDD on one frame."""
    present = set(sub["method"].astype(str))
    rows = []
    for m in methods:
        if m not in present or m == REFERENCE:
            continue
        r = paired_row(sub, m, "%s|%s|%s" % (label_prefix, m, REFERENCE),
                       alpha=alpha, n_boot=n_boot, seed=seed)
        if r:
            rows.append(r)
    return pd.DataFrame(rows)


def counts(frame: pd.DataFrame, col: str = "verdict") -> dict:
    c = {v: int((frame[col] == v).sum()) for v in VERDICT_ORDER}
    c["n"] = int(len(frame))
    return c


# --------------------------------------------------------------------------- #
# Data loading.
# --------------------------------------------------------------------------- #
def load_family_frame(root: Path):
    """Eval-B scores collapsed to one row per family per configuration."""
    seeded = load_results(root / REL_EVALB)
    meta_cols = ["campus", "track", "split", "size", "regime", "crew_multiplier",
                 "u_target", "u_realized", "u_bin", "cluster", "eval_set"]
    fam, _ = collapse_families(seeded, meta_cols)
    return fam


def load_capacity_frames(root: Path):
    """One family frame per rung of the campus-2 capacity ladder.

    The p95 rung is the Eval-B empirical anchor set at crew multiplier 1.0,
    which is the estimator the evaluation was built on; the p90 and p75 rungs
    come from the capacity robustness run.  Both carry the seven transparent
    rules and the ten MLP seeds, so the family vocabulary is those rules plus
    the MLP pool.
    """
    evalb = load_evalb(root / REL_EVALB)
    cap = pd.read_csv(root / REL_CAPACITY)
    cap = normalize_method_column(cap)
    cap["method"] = cap["method"].astype(str)
    cap["campus"] = cap["campus"].astype(int)
    cap["id"] = cap["id"].astype(str)
    cap["base_instance_id"] = cap["base_instance_id"].astype(str)
    cap["arm"] = cap["crew_q"].astype(float).map(lambda q: "q%.2f" % q)
    frames = {}
    for arm in CAP_ARMS:
        src = evalb if arm == CAP_BASE_ARM else cap[cap["arm"] == arm]
        if src.empty:
            continue
        f, _ = collapse_families(src, CAP_META, pools=POOL_SEEDS,
                                 keep=CAP_SCORED_RULES)
        frames[arm] = f[f["campus"] == STRESS_CAMPUS].copy()
    return frames


def dev_independent_clusters(root: Path):
    """Base instances of the final evaluation that touch no development window.

    ``overlap_devcorpus.csv`` counts, per final empirical instance, the work
    orders it shares with released v1.0 empirical-track windows of its campus
    and the released instances those windows belong to, split by split.  An
    instance is development-independent when that shared count is zero, which
    on the released file is exactly the set with no training-split and no
    test-split partner.
    """
    dev = pd.read_csv(root / REL_OVERLAP_DEV)
    clean = dev["n_shared_wos"] == 0
    both = (dev["n_v1_train_instances"] == 0) & (dev["n_v1_test_instances"] == 0)
    if not clean.equals(both):
        raise SystemExit("overlap_devcorpus.csv: the zero-shared-work-order set "
                         "and the no-development-partner set differ; state which "
                         "definition applies before proceeding")
    return dev, set(dev.loc[clean, "id"].astype(str))


# --------------------------------------------------------------------------- #
# Step 0: reproduce four released macro values through this code path.
# --------------------------------------------------------------------------- #
STEP0_EQUIV = {1.0: 9, 0.8: 6, 0.6: 3}
STEP0_C2 = {"mean_diff": -353.0, "ci_lo": -740.7, "ci_hi": -59.9,
            "verdict": "better"}


def step_zero(fam: pd.DataFrame, cap_frames: dict, released: pd.DataFrame,
              robust: pd.DataFrame) -> list:
    """Abort unless the released values come back digit for digit.

    Two comparisons run on each value: against the stored analysis CSV, to
    machine precision, and against the rounded number the manuscript macro
    carries, so a silent regeneration of either side is caught.
    """
    lines = []
    emp = fam[(fam["regime"] == "final-empirical")
              & (fam["campus"].isin(VERDICT_CAMPUSES))]
    for m in CREW_MULTIPLIERS:
        sub = emp[emp["crew_multiplier"] == m]
        out = compare_families(sub, "analysis_scope=m=%s" % m)
        got = int((out["verdict"] == "equivalent").sum())
        want = STEP0_EQUIV[m]
        rel = released[(released["scope_type"] == "emp_m")
                       & (released["scope"] == "m=%s" % m)
                       & released["family"].isin(out["family"])]
        rel_eq = int((rel["verdict"] == "equivalent").sum())
        if got != want or len(out) != 9 or rel_eq != want:
            raise SystemExit("step 0: crew multiplier %s gives %d equivalent of "
                             "%d compared, released file says %d and the macro "
                             "says %d of 9" % (m, got, len(out), rel_eq, want))
        lines.append("  m=%.1f  %d of %d families equivalent to EDD "
                     "(family_comparisons.csv %d, macro %d)"
                     % (m, got, len(out), rel_eq, want))
    c2 = compare_families(cap_frames["q0.90"], "analysis_scope=q0.90|campus2",
                          methods=tuple(RULES) + ("v2pool",))
    row = c2[c2["family"] == "wmdd"].iloc[0]
    rel = robust[(robust["check"] == "capacity") & (robust["arm"] == "q0.90")
                 & (robust["stratum"] == "campus2")
                 & (robust["family"] == "wmdd")].iloc[0]
    for f in ("mean_diff", "ci_lo", "ci_hi"):
        if abs(float(row[f]) - float(rel[f])) > 1e-9:
            raise SystemExit("step 0: campus-2 p90 WMDD %s is %.10g, "
                             "family_robust.csv says %.10g"
                             % (f, float(row[f]), float(rel[f])))
    if row["verdict"] != rel["verdict"]:
        raise SystemExit("step 0: campus-2 p90 WMDD verdict is %r, "
                         "family_robust.csv says %r"
                         % (row["verdict"], rel["verdict"]))
    got = {"mean_diff": float(f_twt(row["mean_diff"])),
           "ci_lo": float(f_twt(row["ci_lo"])), "ci_hi": float(f_twt(row["ci_hi"])),
           "verdict": row["verdict"]}
    if got != STEP0_C2:
        raise SystemExit("step 0: campus-2 p90 WMDD gives %r, released macros "
                         "say %r" % (got, STEP0_C2))
    lines.append("  campus 2, p90 rung, WMDD vs EDD  %.1f [%.1f, %.1f]  %s "
                 "(family_robust.csv identical to 1e-9; macros -353.0 "
                 "[-740.7, -59.9] better)"
                 % (row["mean_diff"], row["ci_lo"], row["ci_hi"], row["verdict"]))
    return lines


# --------------------------------------------------------------------------- #
# Analysis A: the development-independent subset.
# --------------------------------------------------------------------------- #
def analysis_a(fam: pd.DataFrame, clean_ids: set) -> pd.DataFrame:
    emp = fam[(fam["regime"] == "final-empirical")
              & (fam["campus"].isin(VERDICT_CAMPUSES))]
    rows = []
    for m in CREW_MULTIPLIERS:
        scope = emp[emp["crew_multiplier"] == m]
        full = compare_families(scope, "analysis_scope=m=%s" % m)
        sub = scope[scope["cluster"].isin(clean_ids)]
        part = compare_families(sub, "jcce-ovlsubset|analysis_scope=m=%s" % m)
        merged = full.merge(part, on="family", suffixes=("_full", "_subset"))
        merged.insert(0, "scope", "m=%s" % m)
        merged.insert(0, "scope_type", "emp_m")
        merged["verdict_changed"] = (merged["verdict_full"]
                                     != merged["verdict_subset"]).astype(int)
        rows.append(merged)
    return pd.concat(rows, ignore_index=True)


def subset_composition(fam: pd.DataFrame, clean_ids: set, dev: pd.DataFrame) -> dict:
    """What the development-independent restriction removes, in plain counts.

    The subset is not a random half of the verdict campuses.  Sharing is
    concentrated on the two campuses that carry both instance size classes, so
    the retained set is heavier in 400-order weeks and heavier in load, and the
    equivalence margin, which is one percent of the EDD mean, moves with it.
    """
    ver = dev[dev["campus"].isin(VERDICT_CAMPUSES)]
    kept = ver[ver["n_shared_wos"] == 0]
    emp = fam[(fam["regime"] == "final-empirical")
              & (fam["campus"].isin(VERDICT_CAMPUSES))
              & (fam["crew_multiplier"] == 1.0)]
    nonzero = set()
    mean_kept = mean_dropped = float("nan")
    for m in FAMILY_KEYS:
        if m == REFERENCE:
            continue
        pt = stats.paired_table(emp, m, REFERENCE, value_col=VALUE_COL)
        if pt.empty:
            continue
        out = pt[~pt["cluster"].isin(clean_ids)]
        nonzero |= set(out.loc[out["diff"].abs() > 1e-9, "cluster"])
        mean_kept = float(pt.loc[pt["cluster"].isin(clean_ids), "value_b"].mean())
        mean_dropped = float(out["value_b"].mean())
    return {
        "n_kept": int(len(kept)), "n_total": int(len(ver)),
        "n_dropped": int(len(ver) - len(kept)),
        "by_campus": kept["campus"].value_counts().to_dict(),
        "share_two_campuses": 100.0 * float(kept["campus"].isin((10, 12)).sum())
                              / max(1, len(kept)),
        "kept_150": int((kept["size"] == 150).sum()),
        "kept_400": int((kept["size"] == 400).sum()),
        "total_150": int((ver["size"] == 150).sum()),
        "total_400": int((ver["size"] == 400).sum()),
        "mean_edd_kept": mean_kept, "mean_edd_dropped": mean_dropped,
        "n_dropped_nonzero": int(len(nonzero)),
    }


# --------------------------------------------------------------------------- #
# Analysis B: campus-2 leave-one-instance-out.
# --------------------------------------------------------------------------- #
def analysis_b(cap_frames: dict):
    """Per-drop statistics and the per-instance paired differences."""
    loo_rows, inst_rows = [], []
    for arm in CAP_ARMS:
        frame = cap_frames[arm]
        clusters = sorted(frame["cluster"].unique()) if "cluster" in frame.columns \
            else sorted(frame["base_instance_id"].unique())
        for rule in LOO_RULES:
            label = "analysis_scope=%s|campus2" % arm
            full = paired_row(frame, rule, "%s|%s|%s" % (label, rule, REFERENCE))
            pt = stats.paired_table(frame, rule, REFERENCE, value_col=VALUE_COL)
            for r in pt.itertuples():
                inst_rows.append({"arm": arm, "rule": rule, "cluster": r.cluster,
                                  "id": r.id, "wwt_rule": r.value_a,
                                  "wwt_edd": r.value_b, "paired_diff": r.diff})
            for drop in clusters:
                keep = frame[frame["cluster"] != drop] if "cluster" in frame.columns \
                    else frame[frame["base_instance_id"] != drop]
                r = paired_row(keep, rule,
                               "jcce-loo|%s|campus2|%s|%s|drop=%s"
                               % (arm, rule, REFERENCE, drop))
                r.update({"arm": arm, "rule": rule, "dropped": drop,
                          "full_mean_diff": full["mean_diff"],
                          "full_ci_lo": full["ci_lo"], "full_ci_hi": full["ci_hi"],
                          "full_margin": full["margin"],
                          "full_verdict": full["verdict"]})
                r["delta_vs_full"] = r["mean_diff"] - full["mean_diff"]
                r["verdict_changed"] = int(r["verdict"] != full["verdict"])
                loo_rows.append(r)
    loo = pd.DataFrame(loo_rows)
    cols = ["arm", "rule", "dropped", "n_configs", "n_clusters", "mean_edd",
            "mean_family", "mean_diff", "ci_lo", "ci_hi", "margin", "verdict",
            "full_mean_diff", "full_ci_lo", "full_ci_hi", "full_margin",
            "full_verdict", "delta_vs_full", "verdict_changed"]
    loo = loo[cols]
    inst = pd.DataFrame(inst_rows)
    # Each instance's share of the summed paired difference, which is what makes
    # a single window visible as the carrier of a result.
    tot = inst.groupby(["arm", "rule"])["paired_diff"].transform("sum")
    inst["share_of_total"] = np.where(tot != 0.0, inst["paired_diff"] / tot, np.nan)
    return loo, inst


def loo_summary(loo: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (arm, rule), g in loo.groupby(["arm", "rule"], sort=False):
        flips = g[g["verdict_changed"] == 1]
        infl = g.loc[g["delta_vs_full"].abs().idxmax()]
        rows.append({
            "arm": arm, "rule": rule, "n_drops": int(len(g)),
            "full_mean_diff": float(g["full_mean_diff"].iloc[0]),
            "full_verdict": str(g["full_verdict"].iloc[0]),
            "loo_min_diff": float(g["mean_diff"].min()),
            "loo_max_diff": float(g["mean_diff"].max()),
            "n_verdict_changes": int(len(flips)),
            "verdict_changes_to": "|".join(sorted(set(flips["verdict"]))) or "none",
            "most_influential_cluster": str(infl["dropped"]),
            "most_influential_delta": float(infl["delta_vs_full"]),
            "most_influential_diff": float(infl["mean_diff"]),
            "most_influential_ci_lo": float(infl["ci_lo"]),
            "most_influential_ci_hi": float(infl["ci_hi"]),
            "most_influential_verdict": str(infl["verdict"]),
        })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Analysis C: Bonferroni-adjusted intervals on the confirmatory family.
# --------------------------------------------------------------------------- #
def analysis_c(fam: pd.DataFrame, released: pd.DataFrame) -> pd.DataFrame:
    alpha_adj = stats.ALPHA / CONFIRMATORY_CELLS
    emp = fam[(fam["regime"] == "final-empirical")
              & (fam["campus"].isin(VERDICT_CAMPUSES))]
    rows = []
    for m in CONFIRMATORY_SCOPES:
        scope = emp[emp["crew_multiplier"] == m]
        label = "analysis_scope=m=%s" % m
        prim = compare_families(scope, label)
        adj = compare_families(scope, label, alpha=alpha_adj)
        merged = prim.merge(adj, on="family", suffixes=("", "_bonf"))
        merged.insert(0, "scope", "m=%s" % m)
        rows.append(merged)
    out = pd.concat(rows, ignore_index=True)
    # Guard: the unadjusted read of these streams must equal the released file.
    rel = released[(released["scope_type"] == "emp_m")
                   & released["family"].isin(out["family"])]
    key = ["scope", "family"]
    chk = out.merge(rel[key + ["mean_diff", "ci_lo", "ci_hi", "verdict"]],
                    on=key, suffixes=("", "_rel"))
    for c in ("mean_diff", "ci_lo", "ci_hi"):
        gap = float((chk[c] - chk[c + "_rel"]).abs().max())
        if gap > 1e-9:
            raise SystemExit("analysis C: recomputed %s differs from the released "
                             "file by %.3g" % (c, gap))
    if (chk["verdict"] != chk["verdict_rel"]).any():
        raise SystemExit("analysis C: a recomputed verdict differs from the "
                         "released file")
    out["alpha_adjusted"] = alpha_adj
    out["level_pct"] = 100.0 * (1.0 - alpha_adj)
    out["width_ratio"] = ((out["ci_hi_bonf"] - out["ci_lo_bonf"])
                          / (out["ci_hi"] - out["ci_lo"]).replace(0.0, np.nan))
    out["verdict_changed"] = (out["verdict"] != out["verdict_bonf"]).astype(int)
    keep = ["scope", "family", "n_configs", "n_clusters", "mean_edd",
            "mean_family", "mean_diff", "margin", "ci_lo", "ci_hi", "verdict",
            "alpha_adjusted", "level_pct", "ci_lo_bonf", "ci_hi_bonf",
            "verdict_bonf", "width_ratio", "verdict_changed"]
    return out[keep]


# --------------------------------------------------------------------------- #
# Analysis D: the stored two-level bootstrap at the empirical scopes.
# --------------------------------------------------------------------------- #
def analysis_d(root: Path) -> pd.DataFrame:
    sb = pd.read_csv(root / REL_SEEDBOOT)
    sub = sb[sb["scope_type"] == "emp_m"].copy()
    want = {"m=%s" % m for m in CREW_MULTIPLIERS}
    if not want.issubset(set(sub["scope"])):
        return pd.DataFrame()
    keep = ["scope", "family", "n_seeds", "n_configs", "n_clusters", "mean_ref",
            "mean_diff", "ci_lo_inst", "ci_hi_inst", "verdict_inst",
            "ci_lo_two", "ci_hi_two", "verdict_two", "width_ratio_two_inst",
            "verdict_changed"]
    return sub[keep].reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Macros.
# --------------------------------------------------------------------------- #
class JcMacroFile:
    """Macro collector with the \\jc prefix and the project's number style."""

    def __init__(self, existing):
        self.existing = set(existing)
        self.items = []
        self.names = set()

    def section(self, title):
        self.items.append((None, None, title))

    def add(self, name, value, source):
        if not name.startswith("jc"):
            raise SystemExit("macro %r does not use the \\jc prefix" % name)
        if not name.isalpha():
            raise SystemExit("macro %r must be letters only (LaTeX)" % name)
        if name in self.existing:
            raise SystemExit("macro %r already exists in paper_jcce/" % name)
        if name in self.names:
            raise SystemExit("macro %r defined twice in this run" % name)
        v = house_number(value)
        if v.strip() == "" or "nan" in v.lower() or "inf" in v.lower():
            raise SystemExit("macro %r has a non-finite value %r" % (name, v))
        self.names.add(name)
        self.items.append((name, v, source))

    def render(self, header) -> str:
        L = [header]
        width = min(82, max(len("\\newcommand{\\%s}{%s}" % (n, v))
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


def existing_names(paper_dir: Path):
    import re
    found = set()
    for p in sorted(paper_dir.glob("macros*.tex")):
        if p.name == "macros_jcce.tex":
            continue
        found |= set(re.findall(r"\\newcommand\{\\([A-Za-z]+)\}", p.read_text()))
    return found


def _prose_list(names) -> str:
    names = list(names)
    if not names:
        return "none"
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " and " + names[-1]


CSV_A = REL_OUT + "/overlap_subset.csv"
CSV_B = REL_OUT + "/campus2_loo.csv"
CSV_BI = REL_OUT + "/campus2_loo_per_instance.csv"
CSV_C = REL_OUT + "/multiplicity.csv"
CSV_D = REL_OUT + "/twolevel_pools.csv"


def build_macros(paper_dir: Path, dev, clean_ids, comp, sub_a, loo_sum,
                 inst, mult, two) -> str:
    mf = JcMacroFile(existing_names(paper_dir))

    # -- A ------------------------------------------------------------------ #
    mf.section("Analysis A: the development-independent subset of the final "
               "empirical instances (JCCE review checks).")
    n_all = int(len(dev))
    n_clean_all = int(len(clean_ids))
    ver = dev[dev["campus"].isin(VERDICT_CAMPUSES)]
    n_ver = int(len(ver))
    n_clean_ver = int((ver["n_shared_wos"] == 0).sum())
    src = REL_OVERLAP_DEV + " field=n_shared_wos == 0"
    mf.add("jcOvlSubsetNAllTotal", f_int(n_all), src + " (all final empirical instances)")
    mf.add("jcOvlSubsetNAll", f_int(n_clean_all), src + " (all campuses)")
    mf.add("jcOvlSubsetNTotal", f_int(n_ver), src + " (verdict campuses, denominator)")
    mf.add("jcOvlSubsetN", f_int(n_clean_ver), src + " (verdict campuses)")
    mf.add("jcOvlSubsetDropped", f_int(n_ver - n_clean_ver),
           src + " (verdict-campus instances excluded from the subset)")
    mf.add("jcOvlSubsetShareKept", f_pct(100.0 * n_clean_ver / n_ver),
           src + " (percent of verdict-campus instances kept)")
    changed_all = []
    for m in CREW_MULTIPLIERS:
        g = sub_a[sub_a["scope"] == "m=%s" % m]
        tok = M_TOKEN[m]
        c = counts(g, "verdict_subset")
        mf.add("jcOvlSubsetConfigs" + tok, f_int(int(g["n_configs_subset"].iloc[0])),
               CSV_A + " scope=m=%s field=n_configs_subset" % m)
        mf.add("jcOvlSubsetClusters" + tok, f_int(int(g["n_clusters_subset"].iloc[0])),
               CSV_A + " scope=m=%s field=n_clusters_subset" % m)
        mf.add("jcOvlSubsetMargin" + tok, f_diff(float(g["margin_subset"].iloc[0])),
               CSV_A + " scope=m=%s field=margin_subset" % m)
        mf.add("jcOvlSubsetMarginFull" + tok, f_diff(float(g["margin_full"].iloc[0])),
               CSV_A + " scope=m=%s field=margin_full" % m)
        for v in VERDICT_ORDER:
            mf.add("jcOvlSubset" + VERDICT_TOKEN[v] + tok, f_int(c[v]),
                   CSV_A + " scope=m=%s field=verdict_subset value=%s" % (m, v))
        for r in g.itertuples():
            ft = FAMILY_TOKEN[r.family]
            base = "jcOvlSubset" + tok + ft
            s = CSV_A + " scope=m=%s family=%s field=" % (m, r.family)
            mf.add(base + "Diff", f_diff(r.mean_diff_subset), s + "mean_diff_subset")
            mf.add(base + "CiLo", f_diff(r.ci_lo_subset), s + "ci_lo_subset")
            mf.add(base + "CiHi", f_diff(r.ci_hi_subset), s + "ci_hi_subset")
            mf.add(base + "Verdict", VERDICT_PHRASE[r.verdict_subset],
                   s + "verdict_subset (manuscript phrasing)")
            mf.add(base + "Mark", VERDICT_MARK[r.verdict_subset],
                   s + "verdict_subset (table marker)")
            if r.verdict_changed:
                changed_all.append((m, r.family, r.verdict_full, r.verdict_subset))
    mf.add("jcOvlSubsetCampusTen", f_int(comp["by_campus"].get(10, 0)),
           src + " campus=10 (instances kept)")
    mf.add("jcOvlSubsetCampusTwelve", f_int(comp["by_campus"].get(12, 0)),
           src + " campus=12 (instances kept)")
    mf.add("jcOvlSubsetCampusFive", f_int(comp["by_campus"].get(5, 0)),
           src + " campus=5 (instances kept)")
    mf.add("jcOvlSubsetCampusNine", f_int(comp["by_campus"].get(9, 0)),
           src + " campus=9 (instances kept)")
    mf.add("jcOvlSubsetTwoCampusShare", f_pct(comp["share_two_campuses"]),
           src + " campus in (10, 12), percent of the subset")
    mf.add("jcOvlSubsetSizeOneFifty", f_int(comp["kept_150"]),
           src + " size=150 (instances kept)")
    mf.add("jcOvlSubsetSizeFourHundred", f_int(comp["kept_400"]),
           src + " size=400 (instances kept)")
    mf.add("jcOvlSubsetSizeOneFiftyTotal", f_int(comp["total_150"]),
           src + " size=150 (verdict-campus denominator)")
    mf.add("jcOvlSubsetSizeFourHundredTotal", f_int(comp["total_400"]),
           src + " size=400 (verdict-campus denominator)")
    mf.add("jcOvlSubsetMeanKept", f_twt(comp["mean_edd_kept"]),
           CSV_A + " EDD mean weighted tardiness on the subset, crew multiplier 1.0")
    mf.add("jcOvlSubsetMeanDropped", f_twt(comp["mean_edd_dropped"]),
           CSV_A + " EDD mean weighted tardiness on the excluded instances, crew multiplier 1.0")
    mf.add("jcOvlSubsetDroppedActive", f_int(comp["n_dropped_nonzero"]),
           CSV_A + " excluded instances on which any family differs from EDD, crew multiplier 1.0")
    ratio_margin = sub_a["margin_subset"] / sub_a["margin_full"]
    active = sub_a[sub_a["mean_diff_full"].abs() > 1e-9]
    mf.add("jcOvlSubsetMarginRatio", "%.2f" % float(ratio_margin.median()),
           CSV_A + " margin_subset / margin_full, median")
    mf.add("jcOvlSubsetDiffRatio", "%.2f"
           % float((active["mean_diff_subset"] / active["mean_diff_full"]).median()),
           CSV_A + " mean_diff_subset / mean_diff_full, median over non-tied cells")
    mf.add("jcOvlSubsetCells", f_int(int(len(sub_a))),
           CSV_A + " row count (scope-by-family cells recomputed)")
    mf.add("jcOvlSubsetChanges", f_int(len(changed_all)),
           CSV_A + " field=verdict_changed value=1")
    mf.add("jcOvlSubsetChangedList",
           _prose_list(["%s at the %s crew multiplier"
                        % (FAMILY_PROSE[f], ("reference" if m == 1.0 else str(m)))
                        for m, f, _, _ in changed_all]),
           CSV_A + " field=verdict_changed value=1 (prose list)")

    # -- B ------------------------------------------------------------------ #
    mf.section("Analysis B: campus-2 leave-one-instance-out over the capacity "
               "ladder (JCCE review checks).")
    mf.add("jcLooInstances", f_int(int(loo_sum["n_drops"].iloc[0])),
           CSV_B + " field=n_drops (campus-2 base instances dropped in turn)")
    mf.add("jcLooCells", f_int(int(len(loo_sum))),
           CSV_B + " row count (rung-by-rule combinations)")
    mf.add("jcLooFits", f_int(int(loo_sum["n_drops"].sum())),
           CSV_B + " sum of n_drops (leave-one-out recomputations)")
    mf.add("jcLooFlips", f_int(int(loo_sum["n_verdict_changes"].sum())),
           CSV_B + " sum of n_verdict_changes")
    mf.add("jcLooRungsUnchanged",
           f_int(int((loo_sum["n_verdict_changes"] == 0).sum())),
           CSV_B + " field=n_verdict_changes value=0 (rung-by-rule combinations)")
    for r in loo_sum.itertuples():
        base = "jcLoo" + ARM_TOKEN[r.arm] + FAMILY_TOKEN[r.rule]
        s = CSV_B + " arm=%s rule=%s field=" % (r.arm, r.rule)
        mf.add(base + "Diff", f_twt(r.full_mean_diff), s + "full_mean_diff")
        mf.add(base + "Verdict", VERDICT_PHRASE[r.full_verdict],
               s + "full_verdict (manuscript phrasing)")
        mf.add(base + "Min", f_twt(r.loo_min_diff), s + "loo_min_diff")
        mf.add(base + "Max", f_twt(r.loo_max_diff), s + "loo_max_diff")
        mf.add(base + "Flips", f_int(r.n_verdict_changes), s + "n_verdict_changes")
        mf.add(base + "FlipTo", VERDICT_PHRASE[r.verdict_changes_to],
               s + "verdict_changes_to (manuscript phrasing)")
        mf.add(base + "Infl", str(r.most_influential_cluster).replace("_", "\\_"),
               s + "most_influential_cluster")
        mf.add(base + "InflIdx", str(int(str(r.most_influential_cluster).rsplit("_", 1)[-1])),
               s + "most_influential_cluster, campus-2 window index")
        mf.add(base + "InflDelta", f_twt(r.most_influential_delta),
               s + "most_influential_delta")
        mf.add(base + "InflDiff", f_twt(r.most_influential_diff),
               s + "most_influential_diff")
        mf.add(base + "InflCiLo", f_twt(r.most_influential_ci_lo),
               s + "most_influential_ci_lo")
        mf.add(base + "InflCiHi", f_twt(r.most_influential_ci_hi),
               s + "most_influential_ci_hi")
        mf.add(base + "InflVerdict", VERDICT_PHRASE[r.most_influential_verdict],
               s + "most_influential_verdict (manuscript phrasing)")
    for arm in CAP_ARMS:
        g = inst[(inst["arm"] == arm) & (inst["rule"] == "wmdd")]
        top = g.loc[g["paired_diff"].abs().idxmax()]
        base = "jcLooInst" + ARM_TOKEN[arm] + "Wmdd"
        s = CSV_BI + " arm=%s rule=wmdd field=" % arm
        mf.add(base + "TopId", str(top["cluster"]).replace("_", "\\_"),
               s + "cluster (largest absolute paired difference)")
        mf.add(base + "TopIdx", str(int(str(top["cluster"]).rsplit("_", 1)[-1])),
               s + "cluster, campus-2 window index")
        mf.add(base + "TopDiff", f_twt(top["paired_diff"]), s + "paired_diff")
        mf.add(base + "TopShare", f_pct(100.0 * float(top["share_of_total"])),
               s + "share_of_total, percent")
        mf.add(base + "Negative", f_int(int((g["paired_diff"] < 0).sum())),
               s + "paired_diff < 0 (instances on which WMDD beats EDD)")
        top3 = g.reindex(g["paired_diff"].sort_values().index).head(3)
        mf.add(base + "TopThreeShare",
               f_pct(100.0 * float(top3["share_of_total"].sum())),
               s + "share_of_total summed over the three largest, percent")

    # -- C ------------------------------------------------------------------ #
    mf.section("Analysis C: Bonferroni-adjusted intervals over the 27-comparison "
               "confirmatory family (JCCE review checks).")
    mf.add("jcMultCells", f_int(CONFIRMATORY_CELLS),
           CSV_C + " row count (9 families x 3 crew multipliers)")
    mf.add("jcMultAlpha", "%.4f" % float(mult["alpha_adjusted"].iloc[0]),
           CSV_C + " field=alpha_adjusted")
    mf.add("jcMultLevel", "%.2f" % float(mult["level_pct"].iloc[0]),
           CSV_C + " field=level_pct")
    wr = mult["width_ratio"].dropna()
    mf.add("jcMultWidthMedian", "%.2f" % float(wr.median()),
           CSV_C + " field=width_ratio, median over non-degenerate cells")
    mf.add("jcMultWidthMax", "%.2f" % float(wr.max()),
           CSV_C + " field=width_ratio, maximum")
    changed_c = []
    for m in CONFIRMATORY_SCOPES:
        g = mult[mult["scope"] == "m=%s" % m]
        tok = M_TOKEN[m]
        c = counts(g, "verdict_bonf")
        mf.add("jcMultMargin" + tok, f_diff(float(g["margin"].iloc[0])),
               CSV_C + " scope=m=%s field=margin" % m)
        for v in VERDICT_ORDER:
            mf.add("jcMult" + VERDICT_TOKEN[v] + tok, f_int(c[v]),
                   CSV_C + " scope=m=%s field=verdict_bonf value=%s" % (m, v))
        for r in g.itertuples():
            if r.verdict_changed:
                changed_c.append((m, r.family, r.verdict, r.verdict_bonf))
            ft = FAMILY_TOKEN[r.family]
            base = "jcMult" + tok + ft
            s = CSV_C + " scope=m=%s family=%s field=" % (m, r.family)
            mf.add(base + "CiLo", f_diff(r.ci_lo_bonf), s + "ci_lo_bonf")
            mf.add(base + "CiHi", f_diff(r.ci_hi_bonf), s + "ci_hi_bonf")
            mf.add(base + "Verdict", VERDICT_PHRASE[r.verdict_bonf],
                   s + "verdict_bonf (manuscript phrasing)")
            mf.add(base + "Mark", VERDICT_MARK[r.verdict_bonf],
                   s + "verdict_bonf (table marker)")
    mf.add("jcMultChanges", f_int(len(changed_c)),
           CSV_C + " field=verdict_changed value=1")
    mf.add("jcMultChangedList",
           _prose_list(["%s at the %s crew multiplier"
                        % (FAMILY_PROSE[f], ("reference" if m == 1.0 else str(m)))
                        for m, f, _, _ in changed_c]),
           CSV_C + " field=verdict_changed value=1 (prose list)")
    mf.add("jcMultDefinite",
           f_int(int(mult["verdict_bonf"].isin(("worse", "better")).sum())),
           CSV_C + " field=verdict_bonf value in (worse, better)")
    mf.add("jcMultBetterTotal", f_int(int((mult["verdict_bonf"] == "better").sum())),
           CSV_C + " field=verdict_bonf value=better")

    # -- D ------------------------------------------------------------------ #
    if not two.empty:
        mf.section("Analysis D: the stored two-level (seed and instance) "
                   "bootstrap at the three empirical crew multipliers.")
        mf.add("jcTwoCells", f_int(int(len(two))),
               CSV_D + " row count (3 pools x 3 crew multipliers)")
        mf.add("jcTwoUnchanged", f_int(int((two["verdict_changed"] == 0).sum())),
               CSV_D + " field=verdict_changed value=0")
        mf.add("jcTwoWidthMedian", "%.2f" % float(two["width_ratio_two_inst"].median()),
               CSV_D + " field=width_ratio_two_inst, median")
        mf.add("jcTwoWidthMax", "%.2f" % float(two["width_ratio_two_inst"].max()),
               CSV_D + " field=width_ratio_two_inst, maximum")
        for r in two.itertuples():
            m = float(r.scope.split("=")[1])
            base = "jcTwo" + M_TOKEN[m] + POOL_TOKEN[r.family]
            s = CSV_D + " scope=%s family=%s field=" % (r.scope, r.family)
            mf.add(base + "CiLo", f_diff(r.ci_lo_two), s + "ci_lo_two")
            mf.add(base + "CiHi", f_diff(r.ci_hi_two), s + "ci_hi_two")
            mf.add(base + "Verdict", VERDICT_PHRASE[r.verdict_two],
                   s + "verdict_two (manuscript phrasing)")

    header = (
        "%% Generated by scripts/r4_jcce_checks.py on %s.\n"
        "%% Numbers for the independence, influence and multiplicity checks of\n"
        "%% Supplemental Text S7.4. Every macro names the CSV and the field it\n"
        "%% was read from. Do not edit by hand; re-run the script instead.\n"
        "%% House style: math-mode minus, thousands separated, paired differences\n"
        "%% to the same precision as the released macro files."
        % datetime.now().strftime("%Y-%m-%d"))
    return mf.render(header), len(mf.names)


# --------------------------------------------------------------------------- #
# Summary printing.
# --------------------------------------------------------------------------- #
def print_summary(sub_a, loo_sum, inst, mult, two, dev, clean_ids):
    pd.set_option("display.width", 200)
    ver = dev[dev["campus"].isin(VERDICT_CAMPUSES)]
    print()
    print("=== A. Development-independent subset ===")
    print("  final empirical instances with no shared work order: %d of %d "
          "overall, %d of %d on the verdict campuses"
          % (len(clean_ids), len(dev), int((ver["n_shared_wos"] == 0).sum()),
             len(ver)))
    for m in CREW_MULTIPLIERS:
        g = sub_a[sub_a["scope"] == "m=%s" % m]
        print("  m=%.1f  n=%d clusters  equivalent %d of %d (full set %d)"
              % (m, int(g["n_clusters_subset"].iloc[0]),
                 int((g["verdict_subset"] == "equivalent").sum()), len(g),
                 int((g["verdict_full"] == "equivalent").sum())))
        ch = g[g["verdict_changed"] == 1]
        for r in ch.itertuples():
            print("      %-10s %s -> %s   %.2f [%.2f, %.2f] margin %.2f"
                  % (r.family, r.verdict_full, r.verdict_subset,
                     r.mean_diff_subset, r.ci_lo_subset, r.ci_hi_subset,
                     r.margin_subset))
    print()
    print("=== B. Campus-2 leave-one-instance-out ===")
    print(loo_sum.to_string(index=False))
    print("  per-instance WMDD differences, largest absolute contribution per rung:")
    for arm in CAP_ARMS:
        g = inst[(inst["arm"] == arm) & (inst["rule"] == "wmdd")]
        top = g.loc[g["paired_diff"].abs().idxmax()]
        print("      %s  %s  %.1f  (%.1f%% of the summed difference; %d of %d "
              "instances favor WMDD)"
              % (arm, top["cluster"], top["paired_diff"],
                 100.0 * float(top["share_of_total"]),
                 int((g["paired_diff"] < 0).sum()), len(g)))
    print()
    print("=== C. Bonferroni-adjusted confirmatory family ===")
    print("  %d comparisons, alpha %.6f, %.2f%% intervals"
          % (len(mult), float(mult["alpha_adjusted"].iloc[0]),
             float(mult["level_pct"].iloc[0])))
    for m in CONFIRMATORY_SCOPES:
        g = mult[mult["scope"] == "m=%s" % m]
        print("  m=%.1f  95%%: %s" % (m, dict(g["verdict"].value_counts())))
        print("         adj: %s" % dict(g["verdict_bonf"].value_counts()))
    ch = mult[mult["verdict_changed"] == 1]
    for r in ch.itertuples():
        print("      %-6s %-10s %s -> %s   [%.2f, %.2f] -> [%.2f, %.2f] "
              "margin %.2f" % (r.scope, r.family, r.verdict, r.verdict_bonf,
                               r.ci_lo, r.ci_hi, r.ci_lo_bonf, r.ci_hi_bonf,
                               r.margin))
    print()
    if two.empty:
        print("=== D. Two-level bootstrap: the stored file does not cover the "
              "empirical crew-multiplier scopes; skipped ===")
    else:
        print("=== D. Two-level (seed and instance) bootstrap, stored file ===")
        print(two.to_string(index=False))


# --------------------------------------------------------------------------- #
# Main.
# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--out", default=str(ROOT / REL_OUT))
    ap.add_argument("--paper-dir", default=str(ROOT / "paper_jcce"))
    ap.add_argument("--n-boot", type=int, default=N_BOOT)
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()

    root, out = Path(args.root), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = datetime.now()

    fam = load_family_frame(root)
    cap_frames = load_capacity_frames(root)
    dev, clean_ids = dev_independent_clusters(root)
    released = pd.read_csv(root / REL_FAMILY)
    robust = pd.read_csv(root / REL_ROBUST)

    print("=== Step 0: reproducing released macro values ===")
    for line in step_zero(fam, cap_frames, released, robust):
        print(line)

    sub_a = analysis_a(fam, clean_ids)
    comp = subset_composition(fam, clean_ids, dev)
    loo, inst = analysis_b(cap_frames)
    loo_sum = loo_summary(loo)
    mult = analysis_c(fam, released)
    two = analysis_d(root)

    sub_a.to_csv(out / "overlap_subset.csv", index=False)
    loo_sum.to_csv(out / "campus2_loo.csv", index=False)
    loo.to_csv(out / "campus2_loo_drops.csv", index=False)
    inst.to_csv(out / "campus2_loo_per_instance.csv", index=False)
    mult.to_csv(out / "multiplicity.csv", index=False)
    if not two.empty:
        two.to_csv(out / "twolevel_pools.csv", index=False)

    print_summary(sub_a, loo_sum, inst, mult, two, dev, clean_ids)

    text, n = build_macros(Path(args.paper_dir), dev, clean_ids, comp, sub_a,
                           loo_sum, inst, mult, two)
    (Path(args.paper_dir) / "macros_jcce.tex").write_text(text)
    print()
    print("macros: %d written to paper_jcce/macros_jcce.tex" % n)
    print("csv: %s" % ", ".join(sorted(p.name for p in out.glob("*.csv"))))
    print("runtime %.1f s" % (datetime.now() - t0).total_seconds())


if __name__ == "__main__":
    main()
