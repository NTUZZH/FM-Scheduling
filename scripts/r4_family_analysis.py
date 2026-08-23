#!/usr/bin/env python
"""Family-level Eval-B analysis against a fixed EDD reference.

``scripts/r4_analysis.py`` ranks every evaluated checkpoint separately, so the
ten training seeds of one policy configuration occupy ten of the thirty ranked
positions and the comparator of every scope is whichever of those thirty had
the lowest sample mean.  Repeated training runs of one configuration are
replicates of a single method rather than thirty different methods, and picking
the lowest sample mean as the comparator selects on the same noise it is then
used to measure.  This script answers the same questions with two changes.

* **One method per family.**  A policy pool contributes ONE value on an
  instance-configuration, the mean over its seeds there, so the ten MLP seeds,
  the ten attention seeds and the three curriculum-v1 seeds count once each.
  The ranked vocabulary is ten families: the seven transparent rules,
  ``mlp_pool``, ``attn_pool`` and ``v1_pool``.  Rolling CP-SAT keeps its paired
  rows against EDD and stays outside every ranking, because it ran on a
  subsample (the coverage rule of the Eval-B analysis).
* **The reference is EDD, fixed in advance.**  Every primary comparison is
  ``family - EDD`` on the same instance-configurations, so no scope's
  comparator depends on the outcome.  The sample-best FAMILY is still reported
  beside it, as the descriptive continuation of the released analysis.

Scopes, coverage discipline and statistics are the released ones.  Scope
construction is imported from ``scripts/r4_analysis.py`` (``scope_frames``), so
the empirical, generator, transfer, stress and pooled scopes are literally the
same frames; an ``overall`` scope pooling every configuration is added and
marked heterogeneous, because it mixes the two regimes.  Every paired statistic
comes from ``fmwos.stats``: paired on the configuration id, 95% percentile
bootstrap over base-instance clusters with 10000 resamples and master seed
12345, equivalence margin max(1.0, 1% of the reference mean), Holm within a
comparison family.  Nothing statistical is reimplemented here.

Sign convention: a negative difference means the family is better than EDD.

Pool labels.  The bootstrap draws a per-comparison stream from the method
label, so the pools carry the released pool ids (``v2pool``, ``v2attnpool``)
inside the computation and their plain names (``mlp_pool``, ``attn_pool``,
``v1_pool``) in every output.  That keeps every recomputed pool-vs-EDD row
identical, digit for digit, to ``results/r4_final/analysis/pools.csv``, which
this script asserts before writing anything.

Outputs (new files only)
------------------------
  results/r4_final/analysis/family_comparisons.csv   scope x family, vs EDD and vs the best family
  results/r4_final/analysis/family_robust.csv        capacity estimator arms and the stress campus
  results/r4_final/analysis/family_summary.md        the readable report, one block per scope
  paper/macros_r4f.tex                               the numbers a manuscript cites (prefix \\ff)

Usage
-----
    PYTHONPATH=src python scripts/r4_family_analysis.py
    PYTHONPATH=src python scripts/r4_family_analysis.py --step analysis
    PYTHONPATH=src python scripts/r4_family_analysis.py --step macros
    PYTHONPATH=src python scripts/r4_family_analysis.py --check-latex

Re-running is idempotent: every output is rewritten from the same inputs with
the same seeds, so a second run reproduces every digit.
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
from fmwos import stats                                       # noqa: E402
from fmwos.io import normalize_method_column                  # noqa: E402
# Scope construction, the fixed Eval-B vocabulary, macro plumbing and number
# formatting are shared with the released analyses so the generated files read
# identically and no scope is redefined here.
from r4_analysis import (CREW_MULTIPLIERS, ROLLING, RULES, U_TARGETS,  # noqa: E402
                         V1_MLP, V2_ATTN, V2_MLP, VALUE_COL,
                         BIN_TOKEN, M_TOKEN, U_TOKEN,
                         MacroFile, existing_macro_names, house_number,
                         f_diff, f_int, f_pct, f_ratio, f_text, f_twt,
                         load_results, scope_frames)
from r4_robust_analysis import (ARM_TOKEN, ARM_LABEL, STRATA,  # noqa: E402
                                STRATUM_LABEL, arm_labels, check_latex,
                                load_evalb, stratum_frame)

# --------------------------------------------------------------------------- #
# The family vocabulary.
#
# ``key`` is the label the computation uses (and therefore the label the
# bootstrap stream is derived from); ``name`` is the label every output carries.
# --------------------------------------------------------------------------- #
REFERENCE = "edd"
POOL_SEEDS = {"v2pool": V2_MLP, "v2attnpool": V2_ATTN, "v1pool": V1_MLP}
FAMILY_KEYS = tuple(RULES) + ("v2pool", "v2attnpool", "v1pool")
FAMILY_NAME = {k: k for k in RULES}
FAMILY_NAME.update({"v2pool": "mlp_pool", "v2attnpool": "attn_pool",
                    "v1pool": "v1_pool", ROLLING: ROLLING})
FAMILY_NAMES = frozenset(FAMILY_NAME[k] for k in FAMILY_KEYS)
POOL_KEYS = ("v2pool", "v2attnpool", "v1pool")
POOL_TOKEN = {"v2pool": "pol", "v2attnpool": "attn", "v1pool": "vone"}
POOL_LABEL = {"v2pool": "MLP policy pool (10 seeds)",
              "v2attnpool": "attention policy pool (10 seeds)",
              "v1pool": "curriculum-v1 policy pool (3 seeds)"}

# Holm families: the nine set-rankable families share one correction per scope,
# rolling CP-SAT is corrected on its own because it pairs on a subsample.
HOLM_FAMILY = "family-vs-edd"
HOLM_FAMILY_ROLLING = "rolling-vs-edd"

# Capacity check (results/r4_robustness/capacity/): the file carries the two
# transformed arms, and the untransformed arm is the Eval-B empirical anchor set
# at crew multiplier 1.0, which is the p95 estimator the evaluation was built on.
CAP_ARMS = ("q0.95", "q0.90", "q0.75")
CAP_BASE_ARM = "q0.95"
CAP_SCORED_RULES = tuple(RULES)
CAP_CHECK = {"check": "capacity", "arm_col": "crew_q"}

# The families reported on campus 2 at every crew-estimator rung, in one order
# so the three rungs read as a single ladder: the two weighted due-date rules,
# the processing-time rule that moves with them, the reference's own family
# peer, and the learned pool.
CAMPUS_TWO_FAMILIES = (("wmdd", "Wmdd"), ("atc", "Atc"), ("wspt", "Wspt"),
                       ("pfifo", "Pfifo"), ("mlp_pool", "Mlp"))

# The transparent rules whose cost against EDD the prose quotes, and the five
# scopes it quotes them on: the three crew multipliers of the empirical verdict
# campuses, and the two highest generator target utilisations.
RULE_PCT_FAMILIES = (("wspt", "Wspt"), ("atc", "Atc"), ("wmdd", "Wmdd"),
                     ("lpt", "Lpt"), ("random", "Random"))
GEN_PCT_SCOPES = tuple(("gen_utarget", "u_target=%s" % u, U_TOKEN[u])
                       for u in (1.1, 1.3))
RULE_PCT_SCOPES = (
    tuple(("emp_m", "m=%s" % m, M_TOKEN[m]) for m in CREW_MULTIPLIERS)
    + GEN_PCT_SCOPES
)
# The two diagnostic floors, quoted as a multiple of the reference mean rather
# than as a percentage, because at these utilisations the percentage runs into
# four digits and a multiplier reads faster.
FLOOR_RATIO_FAMILIES = (("lpt", "Lpt"), ("random", "Random"))

VERDICT_TOKEN = {"equivalent": "Equiv", "better": "Better", "worse": "Worse",
                 "inconclusive": "Inconc"}
VERDICT_ORDER = ("better", "equivalent", "inconclusive", "worse")

REL_EVALB = "results/r4_final/results.csv"
REL_CAPACITY = "results/r4_robustness/capacity/results.csv"
REL_POOLS = "results/r4_final/analysis/pools.csv"
REL_OUT = "results/r4_final/analysis"


def holm_family_of(method: str, reference: str) -> str:
    return HOLM_FAMILY_ROLLING if method == ROLLING else HOLM_FAMILY


# --------------------------------------------------------------------------- #
# Collapsing seeds to families.
# --------------------------------------------------------------------------- #
def collapse_families(df: pd.DataFrame, meta_cols, pools=POOL_SEEDS,
                      keep=None, value_col: str = VALUE_COL):
    """Replace each pool's seed rows by one row per instance-configuration.

    A pool's value on a configuration is the mean of its seeds' values there.
    Coverage rule: the pool has a value only on configurations where EVERY one
    of its seeds has a feasible row, so a pool mean is never taken over a
    different set of seeds than its neighbours.  The returned report records how
    many configurations that rule drops (none, on the released files).

    Rows of ``keep`` (the transparent rules, and rolling CP-SAT where present)
    pass through unchanged.
    """
    keep = set(keep if keep is not None else (tuple(RULES) + (ROLLING,)))
    present = set(df["method"].astype(str))
    out = [df[df["method"].isin(keep & present)]]
    report = []
    for pool, seeds in pools.items():
        missing = [s for s in seeds if s not in present]
        if len(missing) == len(seeds):
            report.append({"pool": FAMILY_NAME[pool], "n_seeds": 0,
                           "n_configs": 0, "n_configs_dropped": 0,
                           "status": "absent"})
            continue
        if missing:
            raise SystemExit("pool %s is partially present (%d of %d seeds); "
                             "refusing to average over a different seed set"
                             % (FAMILY_NAME[pool], len(seeds) - len(missing),
                                len(seeds)))
        sub = df[df["method"].isin(seeds)]
        sub = sub[sub["feasible"] == 1] if "feasible" in sub.columns else sub
        per_config = sub.groupby("id")["method"].nunique()
        full = per_config[per_config == len(seeds)].index
        dropped = int(len(per_config) - len(full))
        agg = (sub[sub["id"].isin(full)].groupby("id", sort=True)[value_col]
               .mean().rename(value_col))
        first = sub.drop_duplicates("id").set_index("id")[list(meta_cols)]
        rows = first.loc[agg.index].join(agg).reset_index()
        rows["method"] = pool
        rows["feasible"] = 1
        out.append(rows)
        report.append({"pool": FAMILY_NAME[pool], "n_seeds": len(seeds),
                       "n_configs": int(len(agg)), "n_configs_dropped": dropped,
                       "status": "complete" if dropped == 0 else "partial"})
    fam = pd.concat(out, ignore_index=True, sort=False)
    return fam, pd.DataFrame(report)


def seed_dispersion(sub: pd.DataFrame, pool: str,
                    value_col: str = VALUE_COL) -> dict:
    """Spread of the per-seed means inside one pool on one scope."""
    seeds = [s for s in POOL_SEEDS[pool] if s in set(sub["method"].astype(str))]
    if not seeds:
        return {}
    means = (sub[sub["method"].isin(seeds)].groupby("method")[value_col]
             .mean().sort_values())
    return {
        "seed_n": int(len(seeds)),
        "seed_min_mean": float(means.min()),
        "seed_median_mean": float(means.median()),
        "seed_max_mean": float(means.max()),
        "seed_sd": float(means.std(ddof=1)) if len(means) > 1 else 0.0,
        "seed_spread_pct": float(100.0 * (means.max() / means.min() - 1.0)),
        "seed_best": str(means.index[0]),
        "seed_worst": str(means.index[-1]),
    }


# --------------------------------------------------------------------------- #
# Scopes.
# --------------------------------------------------------------------------- #
# Heterogeneous scopes mix regimes or campuses that the evaluation keeps apart,
# so they carry paired comparisons only and never a family ranking.
HETEROGENEOUS = ("overall", "emp_pooled")


def family_scopes(fam: pd.DataFrame, seeded: pd.DataFrame):
    """Yield ``(scope_type, scope, family_frame, seed_frame)`` in report order.

    ``family_frame`` holds the ten families (and rolling CP-SAT where it ran);
    ``seed_frame`` is the same scope of the seed-level file, used only for the
    per-seed dispersion columns.
    """
    yield "overall", "ALL", fam, seeded
    seed_scopes = {(t, s): sub for t, s, sub in scope_frames(seeded)}
    for scope_type, scope, sub in scope_frames(fam):
        yield scope_type, scope, sub, seed_scopes.get((scope_type, scope))


# --------------------------------------------------------------------------- #
# The two comparisons.
# --------------------------------------------------------------------------- #
def primary_vs_edd(sub: pd.DataFrame, scope_label: str, n_boot: int,
                   seed: int) -> pd.DataFrame:
    """Every family paired against EDD on one scope."""
    present = set(sub["method"].astype(str))
    methods = [m for m in FAMILY_KEYS + (ROLLING,) if m in present]
    s = sub.copy()
    s["analysis_scope"] = scope_label
    out = stats.compare_all(s, reference_methods=[REFERENCE], methods=methods,
                            scope_cols=["analysis_scope"], value_col=VALUE_COL,
                            n_boot=n_boot, seed=seed, family_of=holm_family_of)
    return out.drop(columns=["analysis_scope"]) if not out.empty else out


def secondary_vs_best(sub: pd.DataFrame, scope_label: str, n_boot: int,
                      seed: int) -> pd.DataFrame:
    """Every family paired against the family with the lowest mean on the scope."""
    present = set(sub["method"].astype(str))
    methods = [m for m in FAMILY_KEYS if m in present]
    s = sub.copy()
    s["analysis_scope"] = scope_label
    out = stats.equivalence_set(s, methods=methods, scope_cols=["analysis_scope"],
                                value_col=VALUE_COL, n_boot=n_boot, seed=seed)
    return out.drop(columns=["analysis_scope"]) if not out.empty else out


def _edd_own_row(sub: pd.DataFrame, scope_label: str) -> dict:
    """The reference's own row: a zero difference, kept so every family appears."""
    own = sub[(sub["method"] == REFERENCE)]
    if "feasible" in own.columns:
        own = own[own["feasible"] == 1]
    mean = float(own[VALUE_COL].mean())
    clusters = own["id"].map(stats.base_instance_id)
    return {"scope": scope_label, "method": REFERENCE, "reference": REFERENCE,
            "family": HOLM_FAMILY, "n_configs": int(len(own)),
            "n_clusters": int(clusters.nunique()), "mean_ref": mean,
            "mean_method": mean, "mean_diff": 0.0, "ci_lo": 0.0, "ci_hi": 0.0,
            "margin": stats.equivalence_margin(mean), "wilcoxon_p": 1.0,
            "holm_p": 1.0, "verdict": "reference"}


PRIMARY_RENAME = {"mean_ref": "mean_edd", "mean_method": "mean_family"}
SECONDARY_RENAME = {"mean": "mean_own", "best_method": "best_family",
                    "n_configs": "n_configs_vs_best",
                    "n_clusters": "n_clusters_vs_best",
                    "mean_diff": "diff_vs_best", "ci_lo": "ci_lo_vs_best",
                    "ci_hi": "ci_hi_vs_best", "margin": "margin_vs_best",
                    "wilcoxon_p": "wilcoxon_p_vs_best",
                    "verdict": "verdict_vs_best",
                    "in_equivalence_set": "in_best_set"}

FAMILY_COLUMNS = [
    "scope_type", "scope", "family", "reference", "set_rankable",
    "n_configs", "n_clusters", "mean_edd", "mean_family", "mean_diff",
    "ci_lo", "ci_hi", "margin", "wilcoxon_p", "holm_p", "verdict",
    "mean_own", "best_family", "mean_best", "pct_from_best",
    "n_configs_vs_best", "n_clusters_vs_best", "diff_vs_best",
    "ci_lo_vs_best", "ci_hi_vs_best", "margin_vs_best",
    "wilcoxon_p_vs_best", "verdict_vs_best", "in_best_set",
    "seed_n", "seed_min_mean", "seed_median_mean", "seed_max_mean", "seed_sd",
    "seed_spread_pct", "seed_best", "seed_worst",
]


def scope_block(sub: pd.DataFrame, seed_sub, scope_type: str, scope: str,
                n_boot: int, seed: int, rank: bool = True) -> pd.DataFrame:
    """One scope: the primary rows, the secondary columns and the seed spread."""
    prim = primary_vs_edd(sub, scope, n_boot, seed)
    prim = pd.concat([prim, pd.DataFrame([_edd_own_row(sub, scope)])],
                     ignore_index=True, sort=False)
    prim = prim.rename(columns=PRIMARY_RENAME)
    prim.insert(0, "scope_type", scope_type)
    prim["scope"] = scope

    if rank:
        sec = secondary_vs_best(sub, scope, n_boot, seed)
        sec = sec.rename(columns=SECONDARY_RENAME)
        sec["pct_from_best"] = (100.0 * (sec["mean_own"] - sec["mean_best"])
                                / sec["mean_best"])
        sec = sec.drop(columns=["scope", "n_rows", "coverage"])
        out = prim.merge(sec, on="method", how="left")
    else:
        out = prim.copy()
        for c in SECONDARY_RENAME.values():
            out[c] = np.nan
        out["pct_from_best"] = np.nan
        out["best_family"] = ""

    out["set_rankable"] = (out["method"].isin(FAMILY_KEYS) & rank).astype(int)
    if seed_sub is not None:
        for pool in POOL_KEYS:
            d = seed_dispersion(seed_sub, pool)
            if not d:
                continue
            m = out["method"] == pool
            for k, v in d.items():
                if k not in out.columns:
                    out[k] = np.nan if not isinstance(v, str) else ""
                out.loc[m, k] = v
    for c in FAMILY_COLUMNS:
        if c not in out.columns:
            out[c] = np.nan
    out["family"] = out["method"].map(lambda m: FAMILY_NAME.get(m, m))
    if "best_family" in out.columns:
        out["best_family"] = out["best_family"].map(
            lambda m: FAMILY_NAME.get(m, m) if isinstance(m, str) else m)
    return out[FAMILY_COLUMNS]


def family_block(fam: pd.DataFrame, seeded: pd.DataFrame, n_boot: int,
                 seed: int) -> pd.DataFrame:
    parts = []
    for scope_type, scope, sub, seed_sub in family_scopes(fam, seeded):
        parts.append(scope_block(sub, seed_sub, scope_type, scope, n_boot, seed,
                                 rank=scope_type not in HETEROGENEOUS))
    return pd.concat(parts, ignore_index=True, sort=False)


# --------------------------------------------------------------------------- #
# Reconciliation against the released pool comparisons.
# --------------------------------------------------------------------------- #
RECONCILE_FIELDS = ("n_configs", "n_clusters", "mean_ref", "mean_method",
                    "mean_diff", "ci_lo", "ci_hi", "margin", "wilcoxon_p")


def reconcile_pools(fam: pd.DataFrame, pools_csv: Path, n_boot: int,
                    seed: int) -> pd.DataFrame:
    """Recompute every released pool-vs-EDD row and compare it field by field.

    The released rows come from the seed-level file through the same collapse
    (a pool's value is the mean of its seeds on the configuration), so a
    difference in any field means the collapse implemented here is not the one
    the released analysis used.  Any mismatch stops the run.
    """
    released = pd.read_csv(pools_csv)
    released = released[released["reference"] == REFERENCE]
    scoped = {(t, s): sub for t, s, sub in scope_frames(fam)}
    rows = []
    for (scope_type, scope), sub in scoped.items():
        want = released[(released["scope_type"] == scope_type)
                        & (released["scope"] == scope)]
        pools = [p for p in ("v2pool", "v2attnpool") if p in set(want["method"])]
        if not pools:
            continue
        s = sub.copy()
        s["analysis_scope"] = scope
        got = stats.compare_all(s, reference_methods=[REFERENCE], methods=pools,
                                scope_cols=["analysis_scope"],
                                value_col=VALUE_COL, n_boot=n_boot, seed=seed)
        for pool in pools:
            a = want[want["method"] == pool].iloc[0]
            b = got[got["method"] == pool].iloc[0]
            row = {"scope_type": scope_type, "scope": scope,
                   "family": FAMILY_NAME[pool]}
            worst = 0.0
            for f in RECONCILE_FIELDS:
                x, y = float(a[f]), float(b[f])
                row["released_" + f] = x
                row["family_" + f] = y
                worst = max(worst, abs(x - y))
            row["max_abs_diff"] = worst
            row["verdict_released"] = str(a["verdict"])
            row["verdict_family"] = str(b["verdict"])
            row["ok"] = int(worst <= 1e-9 and row["verdict_released"]
                            == row["verdict_family"])
            rows.append(row)
    out = pd.DataFrame(rows).sort_values(["scope_type", "scope", "family"],
                                         kind="mergesort").reset_index(drop=True)
    bad = out[out["ok"] == 0]
    if not bad.empty:
        raise SystemExit("pool reconciliation failed on %d of %d rows; worst "
                         "absolute difference %g (see scope %s, family %s)"
                         % (len(bad), len(out), float(bad["max_abs_diff"].max()),
                            bad.iloc[0]["scope"], bad.iloc[0]["family"]))
    return out


# --------------------------------------------------------------------------- #
# Robustness: the capacity estimator arms and the stress campus.
# --------------------------------------------------------------------------- #
CAP_META = ["base_instance_id", "campus", "size", "u_realized"]


def load_capacity_families(root: Path, evalb_csv: Path):
    """Family frames for the three capacity arms.

    The results file carries the two transformed arms; the untransformed arm is
    the Eval-B empirical anchor set at crew multiplier 1.0, restricted to the
    methods the transformed arms scored.  Those are the seven transparent rules
    and the ten MLP seeds, so the family vocabulary of this check is the seven
    rules plus ``mlp_pool``: the attention and curriculum-v1 pools were not run
    here and cannot be reported.
    """
    evalb = load_evalb(evalb_csv)
    cap = pd.read_csv(root / REL_CAPACITY)
    cap = normalize_method_column(cap)
    cap["method"] = cap["method"].astype(str)
    cap["campus"] = cap["campus"].astype(int)
    cap["id"] = cap["id"].astype(str)
    cap["base_instance_id"] = cap["base_instance_id"].astype(str)
    cap["arm"] = arm_labels(CAP_CHECK, cap[CAP_CHECK["arm_col"]])

    frames, reports = {}, []
    raw = {CAP_BASE_ARM: evalb}
    for arm in CAP_ARMS:
        if arm == CAP_BASE_ARM:
            src = evalb
        else:
            src = cap[cap["arm"] == arm]
            raw[arm] = src
        if src.empty:
            continue
        f, rep = collapse_families(src, CAP_META, pools=POOL_SEEDS,
                                   keep=CAP_SCORED_RULES)
        frames[arm] = f
        rep.insert(0, "arm", arm)
        reports.append(rep)
    return frames, raw, pd.concat(reports, ignore_index=True)


ROBUST_COLUMNS = ["check", "arm", "arm_label", "stratum", "stratum_label"] + \
    FAMILY_COLUMNS[2:]


def robust_block(cap_frames: dict, cap_raw: dict, families: pd.DataFrame,
                 n_boot: int, seed: int) -> pd.DataFrame:
    """The capacity arms per stratum, plus the stress campus at family level."""
    parts = []
    for arm in CAP_ARMS:
        if arm not in cap_frames:
            continue
        for stratum in STRATA:
            sub = stratum_frame(cap_frames[arm], stratum)
            if sub.empty:
                continue
            label = "%s|%s" % (arm, stratum)
            seed_sub = stratum_frame(cap_raw[arm], stratum)
            b = scope_block(sub, seed_sub, "capacity", label, n_boot, seed)
            b.insert(0, "check", "capacity")
            b.insert(1, "arm", arm)
            b.insert(2, "arm_label", ARM_LABEL[("capacity", arm)])
            b.insert(3, "stratum", stratum)
            b.insert(4, "stratum_label", STRATUM_LABEL[stratum])
            parts.append(b.drop(columns=["scope_type", "scope"]))
    # The stress campus is already computed in the primary block on exactly the
    # frame this check would rebuild, so it is carried over rather than
    # recomputed; the two are the same rows by construction.
    st = families[families["scope_type"] == "stress"].copy()
    if not st.empty:
        st = st.drop(columns=["scope_type", "scope"])
        st.insert(0, "check", "evalb")
        st.insert(1, "arm", "stress")
        st.insert(2, "arm_label", "Eval-B empirical anchors, crew multiplier 1.0")
        st.insert(3, "stratum", "campus2")
        st.insert(4, "stratum_label", STRATUM_LABEL["campus2"])
        parts.append(st)
    out = pd.concat(parts, ignore_index=True, sort=False)
    return out[ROBUST_COLUMNS]


# --------------------------------------------------------------------------- #
# Verdict counts (what the macros report).
# --------------------------------------------------------------------------- #
def verdict_counts(frame: pd.DataFrame) -> dict:
    """Counts of the four verdicts among the compared families of one scope.

    The reference's own row and rolling CP-SAT's subsample row are excluded, so
    the counts run over the families that were paired against EDD.
    """
    sub = frame[frame["family"].isin(FAMILY_NAMES)
                & (frame["family"] != REFERENCE)]
    counts = {v: int((sub["verdict"] == v).sum()) for v in VERDICT_ORDER}
    counts["n_compared"] = int(len(sub))
    counts["n_families"] = int(len(sub)) + 1
    counts["equivalent_or_better"] = counts["equivalent"] + counts["better"]
    counts["members"] = {v: list(sub.loc[sub["verdict"] == v, "family"])
                         for v in VERDICT_ORDER}
    return counts


def _scope_frame(families: pd.DataFrame, scope_type: str, scope: str):
    return families[(families["scope_type"] == scope_type)
                    & (families["scope"] == scope)]


def _robust_frame(robust: pd.DataFrame, check: str, arm: str, stratum: str):
    return robust[(robust["check"] == check) & (robust["arm"] == arm)
                  & (robust["stratum"] == stratum)]


# --------------------------------------------------------------------------- #
# Readable report.
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


REPORT_COLS = ["family", "n_configs", "n_clusters", "mean_edd", "mean_family",
               "mean_diff", "ci_lo", "ci_hi", "margin", "holm_p", "verdict",
               "best_family", "pct_from_best", "verdict_vs_best", "in_best_set"]

SCOPE_TITLE = {
    "overall": "Every configuration pooled (heterogeneous: both regimes)",
    "emp_m": "Empirical verdict campuses, per crew multiplier",
    "emp_ubin": "Empirical verdict campuses, per realised-utilisation bin",
    "emp_m_ubin": "Empirical verdict campuses, crew multiplier by utilisation bin",
    "gen_all": "Generator cells, pooled",
    "gen_utarget": "Generator cells, per target utilisation",
    "transfer": "Campus 1 (transfer)",
    "stress": "Campus 2 (nonstationary overload)",
    "emp_pooled": "Every empirical configuration pooled (heterogeneous: "
                  "verdict, transfer and stress campuses together)",
}
SCOPE_ORDER = ("emp_m", "emp_ubin", "emp_m_ubin", "gen_all", "gen_utarget",
               "transfer", "stress", "emp_pooled", "overall")


def _verdict_sentence(counts: dict) -> str:
    parts = []
    for v in VERDICT_ORDER:
        if counts[v]:
            parts.append("%d %s (%s)" % (counts[v], v,
                                         ", ".join(counts["members"][v])))
    if not parts:
        return "no family compared"
    return "; ".join(parts)


def write_report(out: Path, families: pd.DataFrame, robust: pd.DataFrame,
                 coverage: pd.DataFrame, cap_coverage: pd.DataFrame,
                 recon: pd.DataFrame, n_boot: int, seed: int) -> None:
    L = []
    A = L.append
    A("# Family-level Eval-B analysis, EDD reference fixed in advance\n")
    A("Source: `%s` (seed-level) collapsed to ten methods: the seven "
      "transparent rules and three policy pools (`mlp_pool` = 10 MLP seeds, "
      "`attn_pool` = 10 attention seeds, `v1_pool` = 3 curriculum-v1 seeds). A "
      "pool's value on an instance-configuration is the mean over its seeds "
      "there. Rolling CP-SAT ran on a subsample and is reported through its "
      "paired rows against EDD only, never ranked.\n" % REL_EVALB)
    A("Statistics: `fmwos.stats`, paired on the configuration id, 95%% "
      "percentile bootstrap over base-instance clusters, %d resamples, master "
      "seed %d, equivalence margin max(1.0, 1%% of the reference mean), Holm "
      "within a comparison family. A negative difference means the family is "
      "better than EDD.\n" % (n_boot, seed))
    A("Two comparisons per scope. The PRIMARY one is against EDD, chosen "
      "before any result was read, so no scope's reference depends on the "
      "outcome. The SECONDARY one is against the family with the lowest sample "
      "mean in that scope, reported for continuity with the released "
      "seed-level analysis and descriptive only.\n")

    A("\n## Seed coverage of the pools\n")
    A(_md_table(coverage, ["pool", "n_seeds", "n_configs", "n_configs_dropped",
                           "status"]))
    A("A pool has a value only where every one of its seeds has a feasible "
      "row; `n_configs_dropped` counts the configurations that rule removes.\n")

    A("\n## Reconciliation against the released pool comparisons\n")
    A("Every pool-vs-EDD row of `%s` recomputed from the family collapse, "
      "field by field (%d rows, all matching to 1e-9).\n"
      % (REL_POOLS, len(recon)))
    A(_md_table(recon, ["scope_type", "scope", "family", "released_mean_diff",
                        "family_mean_diff", "released_ci_lo", "family_ci_lo",
                        "released_ci_hi", "family_ci_hi", "max_abs_diff", "ok"]))

    for scope_type in SCOPE_ORDER:
        sub_all = families[families["scope_type"] == scope_type]
        if sub_all.empty:
            continue
        A("\n## %s\n" % SCOPE_TITLE.get(scope_type, scope_type))
        for scope in sub_all["scope"].unique():
            sub = _scope_frame(families, scope_type, scope)
            c = verdict_counts(sub)
            ranked = int(sub["set_rankable"].sum())
            if ranked:
                best = sub["best_family"].dropna()
                best = str(best.iloc[0]) if len(best) else "-"
                A("\n**%s** (%d configurations, %d clusters). Against EDD, of "
                  "%d families compared: %s. Sample-best family: %s.\n"
                  % (scope, int(sub["n_configs"].max()),
                     int(sub["n_clusters"].max()), c["n_compared"],
                     _verdict_sentence(c), best))
            else:
                A("\n**%s** (%d configurations, %d clusters, no family ranking: "
                  "heterogeneous scope). Against EDD, of %d families compared: "
                  "%s.\n" % (scope, int(sub["n_configs"].max()),
                             int(sub["n_clusters"].max()), c["n_compared"],
                             _verdict_sentence(c)))
            A(_md_table(sub, REPORT_COLS))

    A("\n## Capacity estimator arms and the stress campus\n")
    A("The capacity check scored the seven transparent rules and the ten MLP "
      "seeds, so its family vocabulary is the seven rules plus `mlp_pool`; the "
      "attention and curriculum-v1 pools were not run there. The p95 arm is "
      "the untransformed Eval-B anchor set at crew multiplier 1.0.\n")
    A("\nSeed coverage on the capacity arms:\n")
    A(_md_table(cap_coverage, ["arm", "pool", "n_seeds", "n_configs",
                               "n_configs_dropped", "status"]))
    for (check, arm, stratum), sub in robust.groupby(
            ["check", "arm", "stratum"], sort=False):
        c = verdict_counts(sub)
        A("\n**%s / %s / %s** (%s; %d configurations, %d clusters). Against "
          "EDD, of %d families compared: %s.\n"
          % (check, arm, stratum, sub["arm_label"].iloc[0],
             int(sub["n_configs"].max()), int(sub["n_clusters"].max()),
             c["n_compared"], _verdict_sentence(c)))
        A(_md_table(sub, REPORT_COLS))

    A("\n## Seed dispersion inside each pool\n")
    disp = families[families["seed_n"].notna()]
    A(_md_table(disp, ["scope_type", "scope", "family", "seed_n", "mean_family",
                       "seed_min_mean", "seed_median_mean", "seed_max_mean",
                       "seed_sd", "seed_spread_pct", "seed_best", "seed_worst"]))

    (out / "family_summary.md").write_text("\n".join(L))


# --------------------------------------------------------------------------- #
# Macros (paper/macros_r4f.tex, prefix \ff).
# --------------------------------------------------------------------------- #
class FamilyMacroFile(MacroFile):
    """A macro collection whose names carry the family-analysis prefix.

    Values pass through :func:`house_number` on the way in, so the number style
    is a property of the file rather than of each call site.
    """

    PREFIX = "ff"

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


def _add_counts(mf, prefix, suffix, counts, source):
    for verdict, tok in VERDICT_TOKEN.items():
        mf.add("%s%s%s" % (prefix, tok, suffix), f_int(counts[verdict]),
               "%s field=verdict value=%s (families vs EDD)" % (source, verdict))


def build_macros(out: Path, paper_dir: Path) -> tuple:
    """Read this run's CSVs back from disk and write paper/macros_r4f.tex."""
    families = pd.read_csv(out / "family_comparisons.csv")
    robust = pd.read_csv(out / "family_robust.csv")

    # Collision guard against every companion macro file; the target file is
    # excluded, because rebuilding it must stay idempotent.
    target = paper_dir / "macros_r4f.tex"
    existing = set()
    for p in sorted(paper_dir.glob("macros*.tex")):
        if p != target:
            existing |= existing_macro_names(p)
    mf = FamilyMacroFile(existing)

    src_fam = "%s/family_comparisons.csv" % REL_OUT
    src_rob = "%s/family_robust.csv" % REL_OUT

    # ---- conventions ----------------------------------------------------- #
    mf.section("Family-level vocabulary (%s)" % src_fam)
    mf.add("ffFamilies", f_int(len(FAMILY_KEYS)),
           src_fam + " field=family (seven transparent rules and three policy "
                     "pools, each pool one method)")
    mf.add("ffCompared", f_int(len(FAMILY_KEYS) - 1),
           src_fam + " field=family (families paired against the EDD reference)")
    mf.add("ffMlpSeeds", f_int(len(V2_MLP)),
           "scripts/r4_family_analysis.py POOL_SEEDS (seeds averaged into "
           "mlp_pool)")
    mf.add("ffAttnSeeds", f_int(len(V2_ATTN)),
           "scripts/r4_family_analysis.py POOL_SEEDS (seeds averaged into "
           "attn_pool)")
    mf.add("ffVoneSeeds", f_int(len(V1_MLP)),
           "scripts/r4_family_analysis.py POOL_SEEDS (seeds averaged into "
           "v1_pool)")

    # ---- empirical verdict, per crew multiplier -------------------------- #
    mf.section("Empirical verdict campuses, per crew multiplier: families "
               "against EDD (%s scope_type=emp_m)" % src_fam)
    for m in CREW_MULTIPLIERS:
        scope, tok = "m=%s" % m, M_TOKEN[m]
        sub = _scope_frame(families, "emp_m", scope)
        c = verdict_counts(sub)
        src = src_fam + " scope_type=emp_m scope=%s" % scope
        _add_counts(mf, "ffemp", tok, c, src)
        mf.add("ffempConfigs" + tok, f_int(sub["n_configs"].max()),
               src + " field=n_configs")
        mf.add("ffempClusters" + tok, f_int(sub["n_clusters"].max()),
               src + " field=n_clusters")

    # ---- empirical verdict, per realised-utilisation bin ----------------- #
    mf.section("Empirical verdict campuses, per realised-utilisation bin: "
               "families against EDD (%s scope_type=emp_ubin)" % src_fam)
    for b, tok in BIN_TOKEN.items():
        sub = _scope_frame(families, "emp_ubin", "u_bin=%s" % b)
        if sub.empty:
            continue
        c = verdict_counts(sub)
        src = src_fam + " scope_type=emp_ubin scope=u_bin=%s" % b
        _add_counts(mf, "ffemp" + tok, "", c, src)
        mf.add("ffemp%sConfigs" % tok, f_int(sub["n_configs"].max()),
               src + " field=n_configs")

    # ---- generator, per target utilisation ------------------------------- #
    mf.section("Generator cells, per target utilisation: families against EDD "
               "(%s scope_type=gen_utarget)" % src_fam)
    for u in U_TARGETS:
        scope, tok = "u_target=%s" % u, U_TOKEN[u]
        sub = _scope_frame(families, "gen_utarget", scope)
        if sub.empty:
            continue
        c = verdict_counts(sub)
        src = src_fam + " scope_type=gen_utarget scope=%s" % scope
        _add_counts(mf, "ffgen", tok, c, src)

    # ---- capacity estimator, p75 arm ------------------------------------- #
    mf.section("Capacity estimator, p75 arm, verdict campuses: families against "
               "EDD (%s check=capacity arm=q0.75 stratum=verdict)" % src_rob)
    tok = ARM_TOKEN[("capacity", "q0.75")]
    sub = _robust_frame(robust, "capacity", "q0.75", "verdict")
    c = verdict_counts(sub)
    src = src_rob + " check=capacity arm=q0.75 stratum=verdict"
    _add_counts(mf, "ffcap", tok, c, src)
    mf.add("ffcapFamilies" + tok, f_int(c["n_families"]),
           src + " field=family (the seven rules and the MLP pool; the "
                 "attention and curriculum-v1 pools were not run on this check)")
    mf.add("ffcapCompared" + tok, f_int(c["n_compared"]),
           src + " field=family (families paired against the EDD reference)")
    mf.add("ffcapConfigs" + tok, f_int(sub["n_configs"].max()),
           src + " field=n_configs")
    for meth, mtok in (("atc", "Atc"), ("wmdd", "Wmdd"), ("pfifo", "Pfifo")):
        r = sub[sub["family"] == meth].iloc[0]
        mf.add("ffcap%sVerdict%s" % (mtok, tok), f_text(r["verdict"]),
               src + " family=%s field=verdict" % meth)
        mf.add("ffcap%sDiff%s" % (mtok, tok), f_diff(r["mean_diff"]),
               src + " family=%s field=mean_diff" % meth)

    # ---- stress campus ---------------------------------------------------- #
    mf.section("Campus 2 (nonstationary overload): families against EDD "
               "(%s check=evalb arm=stress)" % src_rob)
    sub = _robust_frame(robust, "evalb", "stress", "campus2")
    c = verdict_counts(sub)
    src = src_rob + " check=evalb arm=stress stratum=campus2"
    _add_counts(mf, "ffstress", "", c, src)
    mf.add("ffstressConfigs", f_int(sub["n_configs"].max()),
           src + " field=n_configs")
    # Same five families and the same four fields as the two loosened arms
    # below, so the three estimator rungs read as one ladder.
    for meth, mtok in CAMPUS_TWO_FAMILIES:
        r = sub[sub["family"] == meth].iloc[0]
        fsrc = src + " family=%s" % meth
        mf.add("ffstress%sDiff" % mtok, f_diff(r["mean_diff"]),
               fsrc + " field=mean_diff")
        mf.add("ffstress%sCiLo" % mtok, f_diff(r["ci_lo"]),
               fsrc + " field=ci_lo")
        mf.add("ffstress%sCiHi" % mtok, f_diff(r["ci_hi"]),
               fsrc + " field=ci_hi")
        mf.add("ffstress%sVerdict" % mtok, f_text(r["verdict"]),
               fsrc + " field=verdict")

    # ---- campus 2 as the crew estimator is loosened ---------------------- #
    # The three estimator arms are the same 17 weeks under three crew sizings,
    # so reading one family down the arms gives its paired difference against
    # EDD as scarcity deepens.  All three rungs are read from the capacity
    # check, including the untransformed p95 arm: the stress block above holds
    # the same p95 point estimates on the Eval-B scope, but its intervals come
    # from that scope's own bootstrap stream, so mixing the two sources in one
    # ladder would put two slightly different intervals on one quantity.
    mf.section("Campus 2 as the crew estimator is loosened: families against "
               "EDD on the p95, p90 and p75 arms (%s check=capacity "
               "stratum=campus2)" % src_rob)
    for arm in CAP_ARMS:
        pref = "ffCtwo" + ARM_TOKEN[("capacity", arm)]
        sub = _robust_frame(robust, "capacity", arm, "campus2")
        src = src_rob + " check=capacity arm=%s stratum=campus2" % arm
        mf.add(pref + "Configs", f_int(sub["n_configs"].max()),
               src + " field=n_configs")
        for meth, mtok in CAMPUS_TWO_FAMILIES:
            r = sub[sub["family"] == meth].iloc[0]
            fsrc = src + " family=%s" % meth
            mf.add(pref + mtok + "Diff", f_diff(r["mean_diff"]),
                   fsrc + " field=mean_diff")
            mf.add(pref + mtok + "CiLo", f_diff(r["ci_lo"]),
                   fsrc + " field=ci_lo")
            mf.add(pref + mtok + "CiHi", f_diff(r["ci_hi"]),
                   fsrc + " field=ci_hi")
            mf.add(pref + mtok + "Verdict", f_text(r["verdict"]),
                   fsrc + " field=verdict")

    # ---- each transparent rule against EDD, on the five prose scopes ----- #
    # The percentage is the paired difference over the reference mean on the
    # same configurations, so it is the cost of choosing that rule instead of
    # EDD rather than a gap to a sample-best comparator.
    mf.section("Each transparent rule against EDD, as a percentage of the "
               "reference mean, on the three crew multipliers and the two "
               "highest generator target utilisations (%s scope_type=emp_m "
               "and scope_type=gen_utarget)" % src_fam)
    for scope_type, scope, tok in RULE_PCT_SCOPES:
        sub = _scope_frame(families, scope_type, scope)
        src = src_fam + " scope_type=%s scope=%s" % (scope_type, scope)
        edd = sub[sub["family"] == REFERENCE].iloc[0]
        mf.add("ffEddMean" + tok, f_twt(edd["mean_family"]),
               src + " family=edd field=mean_family (reference mean over the "
                     "scope's configurations)")
        for meth, mtok in RULE_PCT_FAMILIES:
            r = sub[sub["family"] == meth].iloc[0]
            fsrc = src + " family=%s" % meth
            mf.add("ff%sPct%s" % (mtok, tok),
                   f_pct(100.0 * float(r["mean_diff"]) / float(r["mean_edd"])),
                   fsrc + " fields=mean_diff/mean_edd")
            mf.add("ff%sVerdict%s" % (mtok, tok), f_text(r["verdict"]),
                   fsrc + " field=verdict")

    # ---- the two diagnostic floors, as a multiple of the reference ------- #
    mf.section("Diagnostic-floor deterioration against EDD on the generator "
               "track (%s scope_type=gen_utarget); the ratio is the family "
               "mean over the reference mean on the same configurations, so "
               "it is referenced to EDD and not to a sample-best method"
               % src_fam)
    for scope_type, scope, tok in GEN_PCT_SCOPES:
        sub = _scope_frame(families, scope_type, scope)
        src = src_fam + " scope_type=%s scope=%s" % (scope_type, scope)
        for meth, mtok in FLOOR_RATIO_FAMILIES:
            r = sub[sub["family"] == meth].iloc[0]
            mf.add("ff%sRatio%s" % (mtok, tok),
                   f_ratio(float(r["mean_family"]) / float(r["mean_edd"])),
                   src + " family=%s fields=mean_family/mean_edd (multiplier "
                         "of the reference mean)" % meth)

    # ---- each pool against EDD, per crew multiplier ---------------------- #
    mf.section("Each policy pool against EDD, per crew multiplier (%s "
               "scope_type=emp_m); a pool contributes one value per "
               "configuration, the mean over its seeds" % src_fam)
    for pool in POOL_KEYS:
        pref = "ff" + POOL_TOKEN[pool]
        name = FAMILY_NAME[pool]
        for m in CREW_MULTIPLIERS:
            scope, tok = "m=%s" % m, M_TOKEN[m]
            sub = _scope_frame(families, "emp_m", scope)
            r = sub[sub["family"] == name].iloc[0]
            psrc = (src_fam + " scope_type=emp_m scope=%s family=%s"
                    % (scope, name))
            mf.add(pref + "EddDiff" + tok, f_diff(r["mean_diff"]),
                   psrc + " field=mean_diff")
            mf.add(pref + "EddCiLo" + tok, f_diff(r["ci_lo"]),
                   psrc + " field=ci_lo")
            mf.add(pref + "EddCiHi" + tok, f_diff(r["ci_hi"]),
                   psrc + " field=ci_hi")
            mf.add(pref + "EddVerdict" + tok, f_text(r["verdict"]),
                   psrc + " field=verdict")
            mf.add(pref + "EddPct" + tok,
                   f_pct(100.0 * float(r["mean_diff"]) / float(r["mean_edd"])),
                   psrc + " fields=mean_diff/mean_edd")
            mf.add(pref + "Spread" + tok, f_pct(r["seed_spread_pct"]),
                   psrc + " field=seed_spread_pct (worst seed mean over best "
                          "seed mean, per cent)")

    header = "\n".join([
        "% macros_r4f.tex -- family-level Eval-B numbers, EDD reference.",
        "% GENERATED FILE. Do not edit by hand: rebuild with",
        "%   PYTHONPATH=src python scripts/r4_family_analysis.py",
        "% Every value below is transcribed by that script from a CSV in",
        "%% %s/ produced in the same run; the trailing comment" % REL_OUT,
        "% names the file and the field it came from.",
        "%% Generated %s from %s."
        % (datetime.now().strftime("%Y-%m-%d %H:%M"), REL_EVALB),
        "% Vocabulary: ten methods (seven transparent rules and three policy",
        "% pools). A pool's value on a configuration is the mean over its",
        "% seeds there, so repeated training runs count once.",
        "% Reference: EDD, fixed before any result was read. Verdicts are the",
        "% practical-equivalence verdicts of the paired difference against it.",
        "% Sign convention: a negative paired difference means the family is",
        "% better than EDD (weighted tardiness is minimised).",
        "% Companion files: macros_r4.tex, macros_r4b.tex .. macros_r4e.tex.",
        "% No name is shared with them; a collision is a hard error here.",
    ])
    (paper_dir / "macros_r4f.tex").write_text(mf.render(header))
    return len(mf.names), sorted(mf.names)


# --------------------------------------------------------------------------- #
# Main.
# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--results", default=str(ROOT / REL_EVALB))
    ap.add_argument("--out", default=str(ROOT / REL_OUT))
    ap.add_argument("--paper-dir", default=str(ROOT / "paper"))
    ap.add_argument("--step", choices=("all", "analysis", "macros"),
                    default="all")
    ap.add_argument("--n-boot", type=int, default=stats.N_BOOT)
    ap.add_argument("--seed", type=int, default=stats.SEED)
    ap.add_argument("--skip-reconcile", action="store_true",
                    help="bypass the released-pools reconciliation guard "
                         "(margin-sensitivity sweeps only)")
    ap.add_argument("--check-latex", action="store_true",
                    help="compile a scratch document that uses every macro")
    args = ap.parse_args()

    root = Path(args.root)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    paper_dir = Path(args.paper_dir)
    t0 = datetime.now()

    if args.step in ("all", "analysis"):
        seeded = load_results(Path(args.results))
        meta_cols = ["campus", "track", "split", "size", "regime",
                     "crew_multiplier", "u_target", "u_realized", "u_bin",
                     "cluster", "eval_set"]
        fam, coverage = collapse_families(seeded, meta_cols)
        print("families: %d methods over %d configurations"
              % (fam["method"].nunique(), fam["id"].nunique()))
        print(coverage.to_string(index=False))

        if args.skip_reconcile:
            # The guard compares margin-dependent fields (margin, verdict)
            # against the released pools file, so a run under a deliberately
            # altered margin (the sensitivity sweep) must bypass it.
            print("reconciliation SKIPPED (--skip-reconcile)")
            recon = pd.DataFrame(columns=["scope_type", "scope", "family",
                                          "released_mean_diff",
                                          "family_mean_diff", "max_abs_diff",
                                          "verdict_released", "verdict_family",
                                          "ok"])
        else:
            recon = reconcile_pools(fam, Path(root / REL_POOLS), args.n_boot,
                                    args.seed)
            print("reconciliation: %d released pool-vs-EDD rows reproduced "
                  "(max abs difference %.3g)"
                  % (len(recon), float(recon["max_abs_diff"].max())))

        families = family_block(fam, seeded, args.n_boot, args.seed)
        print("primary: %d rows over %d scopes"
              % (len(families), families.groupby(["scope_type", "scope"]).ngroups))

        cap_frames, cap_raw, cap_coverage = load_capacity_families(
            root, Path(args.results))
        robust = robust_block(cap_frames, cap_raw, families, args.n_boot,
                              args.seed)
        print("robustness: %d rows over %d scopes"
              % (len(robust),
                 robust.groupby(["check", "arm", "stratum"]).ngroups))

        families.to_csv(out / "family_comparisons.csv", index=False)
        robust.to_csv(out / "family_robust.csv", index=False)
        write_report(out, families, robust, coverage, cap_coverage, recon,
                     args.n_boot, args.seed)
        print("analysis written to %s (%.1f s)"
              % (REL_OUT, (datetime.now() - t0).total_seconds()))

    if args.step in ("all", "macros"):
        n, _ = build_macros(out, paper_dir)
        print("macros: %d written to paper/macros_r4f.tex" % n)

    if args.check_latex:
        print("latex check: %s" % check_latex(paper_dir, "macros_r4f"))


if __name__ == "__main__":
    main()
