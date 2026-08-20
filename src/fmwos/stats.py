"""Paired statistics for the R4 revision analyses (protocol §R4.5, spec S3).

Every R4 number that reaches the manuscript is a paired comparison of two
methods on the SAME instance-configurations, so this module is deliberately
small and pure: functions take a results DataFrame (any of the project's
results.csv files) and return numbers or tidy frames, never files.

The three decisions this module encodes, all fixed by docs/protocol.md §R4.5
before any R4 result existed:

* **Clusters are base instances, not rows.** A released instance is evaluated
  under several transformed configurations (crew multiplier, SLA multiplier,
  backdated releases, ...), and those rows are the same underlying week of
  work: they are correlated, and resampling them independently would report a
  confidence interval several times too narrow.  ``base_instance_id`` maps a
  configuration id back onto its base instance and ``cluster_bootstrap_ci``
  resamples those clusters with replacement.
* **Practical equivalence, not significance.** Two methods are equivalent on a
  scope when the whole paired-difference interval lies within
  ``max(1.0 weighted unit, 1% of the comparator's mean)``.  A Wilcoxon p is
  still reported (it is what the v1.0 Gate-B rule used) and Holm-corrected
  within a declared family, but the verdict column is the equivalence one.
* **Determinism.** The bootstrap is seeded (default 12345) and every
  comparison derives its own stable stream from that seed, so re-running an
  analysis reproduces every digit.

Sign convention throughout: a difference is ``method - reference`` on weighted
tardiness, which is minimised, so a NEGATIVE difference means the method is
better than its reference.
"""

from __future__ import annotations

import re
import zlib

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

# --------------------------------------------------------------------------- #
# Protocol constants (docs/protocol.md §R4.5).
# --------------------------------------------------------------------------- #
N_BOOT = 10000          # percentile bootstrap resamples
SEED = 12345            # bootstrap master seed
ALPHA = 0.05            # 1 - alpha = 95% interval
MARGIN_ABS = 1.0        # equivalence margin, absolute (weighted units)
MARGIN_REL = 0.01       # equivalence margin, relative to the reference mean

# Resampling a (n_boot x n_clusters) index matrix in one allocation is fine for
# a few hundred clusters and wasteful for a few thousand; the bootstrap is run
# in row-chunks of at most this many index entries.  Chunking does not change
# the draw sequence (the generator fills row-major), so results are unchanged.
_MAX_BOOT_CELLS = 4_000_000

# --------------------------------------------------------------------------- #
# Base-instance (cluster) ids.
#
# A configuration id is a base instance id with zero or more TRANSFORM SUFFIXES
# appended by the instance transforms, each of which suffixes ``meta.id``:
#   _m<value>    crew multiplier            fmwos.tightness.scale_crew  ("_m0.6")
#   _sla<value>  SLA window multiplier      fmwos.sensitivity.scale_sla ("_sla1.5")
#   _q<pp>       crew estimator quantile    scripts/r4_capacity.py      ("_q75")
#   _bd          backdated releases         scripts/r4_backdate.py
#   _emg _rtn _pmp3                         scripts/r4_sla_scenarios.py
#   _psum _pmax _pone  processing-time model scripts/r4_pmodel.py
#
# The regex is deliberately conservative: each alternative is either a literal
# token from the list above or a named prefix followed by a number, anchored at
# the end of the string, and stripping stops at the first non-match.  It can
# therefore never eat part of a base id, whose released forms are
# c<NN>_replay_<size>_<idx>, c<NN>_gen_<size>_<idx>, c<NN>_pmmix_<size>_p<pm>_
# c<crew>_<idx>, c<NN>_storm_<size>_a<arr>_c<crew>_<idx> and
# c<NN>_storm2_w<win>_u<u>_<idx> (data/processed/instances/index.csv) -- none of
# which ends in any of these tokens.
# --------------------------------------------------------------------------- #
_NUM = r"\d+(?:\.\d+)?"
BASE_ID_SUFFIX_RE = re.compile(
    r"(?:_m%s|_sla%s|_q\d{2}|_bd|_emg|_rtn|_pmp3|_psum|_pmax|_pone|_L(?:0|8|40|full))$" % (_NUM, _NUM)
)


def base_instance_id(instance_or_config_id) -> str:
    """Strip transform suffixes from a configuration id to get its cluster id.

    Suffixes stack (``..._m0.6_bd``), so they are stripped repeatedly until the
    remainder no longer ends in one.  An id with no suffix (every v1.0 released
    instance id) is returned unchanged, and stripping never consumes the whole
    string.
    """
    s = str(instance_or_config_id)
    while True:
        m = BASE_ID_SUFFIX_RE.search(s)
        if m is None or m.start() == 0:
            return s
        s = s[: m.start()]


def add_base_instance_id(df: pd.DataFrame, id_col: str = "id",
                         out_col: str = "cluster") -> pd.DataFrame:
    """Return ``df`` with a cluster column derived from ``id_col`` (in place)."""
    df[out_col] = df[id_col].map(base_instance_id)
    return df


# --------------------------------------------------------------------------- #
# Utilization bins (docs/protocol.md §R4.4: the primary explanatory variable).
# --------------------------------------------------------------------------- #
U_BIN_EDGES = (0.5, 0.8, 1.0, 1.2)
U_BIN_LABELS = ("<0.5", "0.5-0.8", "0.8-1.0", "1.0-1.2", ">=1.2")
U_BIN_UNKNOWN = "unknown"
# Ordered for reporting; "unknown" last so a file without u_realized still
# groups and sorts stably.
U_BIN_ORDER = U_BIN_LABELS + (U_BIN_UNKNOWN,)


def utilization_bin(u) -> str:
    """Bin a realized utilization onto the protocol's five labels.

    Bins are left-closed / right-open (``0.8`` falls in "0.8-1.0"); a missing
    or non-numeric value returns ``"unknown"`` rather than raising, so a
    results file without a ``u_realized`` column still analyses.
    """
    try:
        v = float(u)
    except (TypeError, ValueError):
        return U_BIN_UNKNOWN
    if not np.isfinite(v):
        return U_BIN_UNKNOWN
    for edge, label in zip(U_BIN_EDGES, U_BIN_LABELS):
        if v < edge:
            return label
    return U_BIN_LABELS[-1]


def add_utilization_bin(df: pd.DataFrame, u_col: str = "u_realized",
                        out_col: str = "u_bin") -> pd.DataFrame:
    """Return ``df`` with a ``u_bin`` column (all "unknown" if ``u_col`` absent)."""
    if u_col in df.columns:
        df[out_col] = df[u_col].map(utilization_bin)
    else:
        df[out_col] = U_BIN_UNKNOWN
    return df


# --------------------------------------------------------------------------- #
# Method families (the Holm correction is applied WITHIN a family, §R4.5).
# --------------------------------------------------------------------------- #
RULE_METHODS = frozenset({
    "edd", "wspt", "atc", "pfifo", "wmdd", "lpt", "random", "atc_la",
    "mor",  # archived v1.0 name of "lpt"; normalize_method_column maps it away
})
OPTIMIZER_METHODS = frozenset({"rollcp2", "cpsat", "ga"})


def method_class(method: str) -> str:
    """Coarse class of a method name: "rule", "optimizer" or "policy".

    Tuned ATC variants are named ``atc_k05``..``atc_k10`` (R4.3), so the ``atc_k``
    prefix is a rule; everything that is neither a known rule nor a known
    optimizer is a learned policy checkpoint (``rl301``, ``v2rl301``, ``v2at301``,
    the visibility arms, ...).
    """
    m = str(method)
    if m in RULE_METHODS or m.startswith("atc_k"):
        return "rule"
    if m in OPTIMIZER_METHODS:
        return "optimizer"
    return "policy"


def default_family(method: str, reference: str) -> str:
    """Family label of one comparison: "<class>-vs-<class>"."""
    return "%s-vs-%s" % (method_class(method), method_class(reference))


# --------------------------------------------------------------------------- #
# Paired differences.
# --------------------------------------------------------------------------- #
def paired_table(df: pd.DataFrame, method_a: str, method_b: str,
                 value_col: str = "wwt", id_col: str = "id",
                 feasible_col: str = "feasible",
                 on_duplicate: str = "error") -> pd.DataFrame:
    """Per-configuration paired differences between two methods.

    Rows are aligned on the instance-configuration id (inner join), so a
    configuration on which either method has no feasible row contributes
    nothing.  Returns a frame with columns ``id``, ``cluster`` (the base
    instance the configuration was derived from), ``value_a``, ``value_b`` and
    ``diff = value_a - value_b``, sorted by id so downstream resampling is
    order-deterministic.

    Infeasible rows are dropped when a ``feasible`` column is present (v1.0 and
    R4 runners both write one; the r2 side-analysis CSVs do not).

    ``on_duplicate="error"`` (default) raises when a method has more than one
    row for one id, because that means the frame still mixes regimes the caller
    meant to scope first (e.g. several visibility levels); ``"mean"`` averages
    them instead.
    """
    if on_duplicate not in ("error", "mean"):
        raise ValueError("on_duplicate must be 'error' or 'mean', got "
                         f"{on_duplicate!r}")
    if value_col not in df.columns:
        raise KeyError("value column %r not in results frame" % value_col)

    sub = df
    if feasible_col in sub.columns:
        sub = sub[sub[feasible_col] == 1]

    def _side(method, name):
        s = sub[sub["method"] == method][[id_col, value_col]]
        if s.empty:
            return None
        dup = s[id_col].duplicated().any()
        if dup:
            if on_duplicate == "error":
                bad = s[id_col][s[id_col].duplicated()].iloc[0]
                raise ValueError(
                    "method %r has several rows for id %r; scope the frame "
                    "first (or pass on_duplicate='mean')" % (method, bad))
            s = s.groupby(id_col, as_index=False)[value_col].mean()
        return s.set_index(id_col)[value_col].rename(name)

    a = _side(method_a, "value_a")
    b = _side(method_b, "value_b")
    if a is None or b is None:
        return pd.DataFrame(columns=["id", "cluster", "value_a", "value_b",
                                     "diff"])

    j = pd.concat([a, b], axis=1, join="inner").sort_index()
    out = pd.DataFrame({
        "id": j.index.astype(str),
        "cluster": [base_instance_id(i) for i in j.index],
        "value_a": j["value_a"].to_numpy(dtype=float),
        "value_b": j["value_b"].to_numpy(dtype=float),
    })
    out["diff"] = out["value_a"] - out["value_b"]
    return out.reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Cluster bootstrap.
# --------------------------------------------------------------------------- #
def cluster_bootstrap_ci(diffs, clusters, n_boot: int = N_BOOT,
                         seed: int = SEED, alpha: float = ALPHA):
    """Percentile CI of the mean difference, resampling CLUSTERS.

    Clusters (base instances) are drawn with replacement, K of them for K
    observed clusters, and each drawn cluster contributes ALL of its rows; a
    cluster drawn twice counts twice.  Implemented by multiplicity weights,
    ``mean* = (w . cluster_sums) / (w . cluster_counts)``, which is exactly the
    mean over the concatenated resampled rows and avoids materialising them.

    Returns ``(lo, hi)`` at the ``alpha/2`` and ``1 - alpha/2`` percentiles.

    Edge cases: an empty input returns ``(nan, nan)``; a SINGLE cluster returns
    the point estimate twice, because with one cluster there is no
    between-cluster variation to resample and any nonzero width would be an
    artifact of pretending the rows are independent.  Callers report that as a
    degenerate interval rather than as evidence.
    """
    d = np.asarray(diffs, dtype=float)
    if d.size == 0:
        return (float("nan"), float("nan"))
    c = np.asarray(clusters, dtype=object)
    if c.shape[0] != d.shape[0]:
        raise ValueError("diffs and clusters must have the same length (%d vs %d)"
                         % (d.shape[0], c.shape[0]))

    _uniq, idx = np.unique(c, return_inverse=True)
    n_clusters = int(idx.max()) + 1
    sums = np.bincount(idx, weights=d, minlength=n_clusters)
    counts = np.bincount(idx, minlength=n_clusters).astype(float)
    if n_clusters == 1:
        mean = float(sums[0] / counts[0])
        return (mean, mean)

    rng = np.random.default_rng(seed)
    chunk = max(1, min(int(n_boot), _MAX_BOOT_CELLS // n_clusters))
    means = np.empty(int(n_boot), dtype=float)
    done = 0
    while done < n_boot:
        rows = min(chunk, int(n_boot) - done)
        draw = rng.integers(0, n_clusters, size=(rows, n_clusters))
        # Row-wise multiplicity counts via one flat bincount (offset each row).
        flat = draw + (np.arange(rows)[:, None] * n_clusters)
        w = np.bincount(flat.ravel(), minlength=rows * n_clusters
                        ).reshape(rows, n_clusters).astype(float)
        means[done:done + rows] = (w @ sums) / (w @ counts)
        done += rows

    lo, hi = np.percentile(means, [100.0 * alpha / 2.0,
                                   100.0 * (1.0 - alpha / 2.0)])
    return (float(lo), float(hi))


def _derived_seed(seed: int, label: str) -> int:
    """Stable per-comparison bootstrap seed derived from the master seed.

    Every comparison must be reproducible, but they should not all reuse the
    identical resample pattern; crc32 of the comparison label mixes the master
    seed deterministically and portably (unlike ``hash()``, which is salted).
    """
    return int((int(seed) ^ zlib.crc32(label.encode("utf-8"))) & 0x7FFFFFFF)


# --------------------------------------------------------------------------- #
# Verdicts and multiplicity.
# --------------------------------------------------------------------------- #
def equivalence_margin(ref_mean: float, margin_abs: float = MARGIN_ABS,
                       margin_rel: float = MARGIN_REL) -> float:
    """Protocol margin: ``max(margin_abs, margin_rel * |reference mean|)``."""
    return float(max(margin_abs, margin_rel * abs(float(ref_mean))))


def equivalence_verdict(ci_lo: float, ci_hi: float, ref_mean: float,
                        margin_abs: float = MARGIN_ABS,
                        margin_rel: float = MARGIN_REL) -> str:
    """Verdict for one paired CI of ``method - reference`` differences.

    * ``"equivalent"``   the whole interval lies inside +/- margin;
    * ``"better"``       the whole interval lies below -margin (and below 0);
    * ``"worse"``        the whole interval lies above +margin (and above 0);
    * ``"inconclusive"`` anything else, including an interval that straddles a
      margin edge (a real difference may or may not exceed the margin).

    Lower values are better (weighted tardiness), so "better" is the negative
    side.  An empty or degenerate CI of NaN returns "inconclusive".
    """
    if ci_lo is None or ci_hi is None:
        return "inconclusive"
    lo, hi = float(ci_lo), float(ci_hi)
    if not (np.isfinite(lo) and np.isfinite(hi)):
        return "inconclusive"
    margin = equivalence_margin(ref_mean, margin_abs, margin_rel)
    if lo >= -margin and hi <= margin:
        return "equivalent"
    if hi < -margin and hi < 0.0:
        return "better"
    if lo > margin and lo > 0.0:
        return "worse"
    return "inconclusive"


def holm(pvals: dict) -> dict:
    """Holm step-down adjusted p-values, keyed exactly like the input.

    Sort the m p-values ascending, multiply the i-th (0-based) by ``m - i``,
    then enforce monotonicity by a running maximum and cap at 1.0.  Ties keep
    the same adjusted value.  An empty input returns an empty dict.
    """
    if not pvals:
        return {}
    items = sorted(pvals.items(), key=lambda kv: (float(kv[1]), str(kv[0])))
    m = len(items)
    out, running = {}, 0.0
    for i, (key, p) in enumerate(items):
        adj = min(1.0, (m - i) * float(p))
        running = max(running, adj)
        out[key] = running
    return {k: out[k] for k in pvals}


def wilcoxon_p(diffs) -> float:
    """Two-sided paired Wilcoxon signed-rank p on the paired differences.

    Zero handling follows scripts/p4_analysis.py exactly (the v1.0 Gate-B
    convention, kept so R4 p-values are comparable with the released ones): an
    empty or all-zero difference vector carries no evidence and returns 1.0,
    otherwise scipy's default zero handling applies and any ValueError (too few
    non-zero differences) also returns 1.0.
    """
    d = np.asarray(diffs, dtype=float)
    if d.size == 0 or np.all(d == 0.0):
        return 1.0
    try:
        return float(wilcoxon(d).pvalue)
    except ValueError:
        return 1.0


# --------------------------------------------------------------------------- #
# Scope helpers.
# --------------------------------------------------------------------------- #
SCOPE_ALL = "ALL"


def _scope_label(scope_cols, key) -> str:
    if not scope_cols:
        return SCOPE_ALL
    key = key if isinstance(key, tuple) else (key,)
    return "|".join("%s=%s" % (c, v) for c, v in zip(scope_cols, key))


def iter_scopes(df: pd.DataFrame, scope_cols):
    """Yield ``(label, key_dict, subframe)`` for each scope (one if no cols)."""
    scope_cols = list(scope_cols or [])
    if not scope_cols:
        yield SCOPE_ALL, {}, df
        return
    missing = [c for c in scope_cols if c not in df.columns]
    if missing:
        raise KeyError("scope columns not in results frame: %s" % missing)
    for key, sub in df.groupby(scope_cols, sort=True, dropna=False):
        key = key if isinstance(key, tuple) else (key,)
        yield (_scope_label(scope_cols, key),
               dict(zip(scope_cols, key)), sub)


def method_means(df: pd.DataFrame, value_col: str = "wwt",
                 feasible_col: str = "feasible") -> pd.Series:
    """Mean value per method over its feasible rows (used to rank methods)."""
    sub = df
    if feasible_col in sub.columns:
        sub = sub[sub[feasible_col] == 1]
    return sub.groupby("method")[value_col].mean()


# --------------------------------------------------------------------------- #
# Drivers.
# --------------------------------------------------------------------------- #
COMPARE_COLUMNS = [
    "scope", "method", "reference", "family", "n_configs", "n_clusters",
    "mean_ref", "mean_method", "mean_diff", "ci_lo", "ci_hi", "margin",
    "wilcoxon_p", "holm_p", "verdict",
]


def compare_all(df: pd.DataFrame, reference_methods, methods=None,
                scope_cols=(), value_col: str = "wwt", id_col: str = "id",
                feasible_col: str = "feasible", family_of=None,
                n_boot: int = N_BOOT, seed: int = SEED, alpha: float = ALPHA,
                margin_abs: float = MARGIN_ABS, margin_rel: float = MARGIN_REL,
                on_duplicate: str = "error") -> pd.DataFrame:
    """Paired comparison of every method against every reference, per scope.

    One row per (scope, method, reference) with the paired means, the mean
    difference and its cluster-bootstrap CI, the Wilcoxon p, the Holm-adjusted
    p and the equivalence verdict.  ``mean_ref`` and ``mean_method`` are means
    over the PAIRED configurations only, so they are directly comparable and
    the equivalence margin is computed from the reference the reader sees.

    ``methods`` defaults to every method present in the scope; ``scope_cols``
    defaults to a single pooled scope labelled "ALL".  ``family_of(method,
    reference) -> str`` names the Holm family (default
    :func:`default_family`); Holm is applied within each (scope, family).
    """
    fam = family_of or default_family
    scope_cols = list(scope_cols or [])
    rows = []
    for label, key, sub in iter_scopes(df, scope_cols):
        present = list(pd.unique(sub["method"].astype(str)))
        cand = [m for m in (methods if methods is not None else sorted(present))
                if m in present]
        refs = [r for r in reference_methods if r in present]
        scope_rows = []
        for ref in refs:
            for meth in cand:
                if meth == ref:
                    continue
                pt = paired_table(sub, meth, ref, value_col=value_col,
                                  id_col=id_col, feasible_col=feasible_col,
                                  on_duplicate=on_duplicate)
                if pt.empty:
                    continue
                d = pt["diff"].to_numpy(dtype=float)
                mean_ref = float(pt["value_b"].mean())
                lo, hi = cluster_bootstrap_ci(
                    d, pt["cluster"].to_numpy(), n_boot=n_boot, alpha=alpha,
                    seed=_derived_seed(seed, "%s|%s|%s" % (label, meth, ref)))
                row = dict(key)
                row.update({
                    "scope": label, "method": meth, "reference": ref,
                    "family": fam(meth, ref),
                    "n_configs": int(len(pt)),
                    "n_clusters": int(pt["cluster"].nunique()),
                    "mean_ref": mean_ref,
                    "mean_method": float(pt["value_a"].mean()),
                    "mean_diff": float(d.mean()),
                    "ci_lo": lo, "ci_hi": hi,
                    "margin": equivalence_margin(mean_ref, margin_abs,
                                                 margin_rel),
                    "wilcoxon_p": wilcoxon_p(d),
                    "verdict": equivalence_verdict(lo, hi, mean_ref,
                                                   margin_abs, margin_rel),
                })
                scope_rows.append(row)
        # Holm within each family of this scope.
        for family in {r["family"] for r in scope_rows}:
            members = [r for r in scope_rows if r["family"] == family]
            adj = holm({i: m["wilcoxon_p"] for i, m in enumerate(members)})
            for i, m in enumerate(members):
                m["holm_p"] = adj[i]
        rows.extend(scope_rows)

    cols = scope_cols + [c for c in COMPARE_COLUMNS if c not in scope_cols]
    return pd.DataFrame(rows, columns=cols)


EQUIV_COLUMNS = [
    "scope", "method", "n_rows", "coverage", "mean", "best_method",
    "mean_best", "n_configs", "n_clusters", "mean_diff", "ci_lo", "ci_hi",
    "margin", "wilcoxon_p", "verdict", "in_equivalence_set",
]


def equivalence_set(df: pd.DataFrame, methods=None, scope_cols=(),
                    value_col: str = "wwt", id_col: str = "id",
                    feasible_col: str = "feasible", n_boot: int = N_BOOT,
                    seed: int = SEED, alpha: float = ALPHA,
                    margin_abs: float = MARGIN_ABS,
                    margin_rel: float = MARGIN_REL,
                    on_duplicate: str = "error") -> pd.DataFrame:
    """Per scope: the best-mean method and the methods equivalent to it.

    The best method is the one with the lowest mean over its own feasible rows
    (that is the number a reader sees in a mean table); every other method is
    then PAIRED against it, and a method joins the equivalence set when its
    paired CI lies within the protocol margin.  The best method is in its own
    set by definition (difference exactly zero).

    The ``coverage`` column is a method's feasible-row count divided by the
    largest such count in the scope.  It exists because a method run on a
    subsample (rolling CP-SAT is evaluated on 8 instances per cell) has a mean
    over a different, easier or harder set of configurations, so its RANK
    against full-coverage methods is a composition artifact even though its
    paired comparison against the best method is sound.  Callers report
    coverage below 1 rather than silently ranking on it.

    Returns one row per (scope, method), including the best method's own row.
    """
    scope_cols = list(scope_cols or [])
    rows = []
    for label, key, sub in iter_scopes(df, scope_cols):
        means = method_means(sub, value_col=value_col,
                             feasible_col=feasible_col)
        if methods is not None:
            means = means[means.index.isin(list(methods))]
        means = means.dropna()
        if means.empty:
            continue
        # Deterministic tiebreak on the method name if two means are identical.
        best = sorted(means.items(), key=lambda kv: (float(kv[1]), str(kv[0])))[0][0]
        n_rows = (sub[sub[feasible_col] == 1] if feasible_col in sub.columns
                  else sub).groupby("method").size()
        max_rows = int(n_rows.reindex(means.index).fillna(0).max())
        for meth in sorted(means.index):
            row = dict(key)
            row.update({
                "scope": label, "method": meth,
                "n_rows": int(n_rows.get(meth, 0)),
                "coverage": (float(n_rows.get(meth, 0)) / max_rows
                             if max_rows else float("nan")),
                "mean": float(means[meth]),
                "best_method": best, "mean_best": float(means[best]),
            })
            if meth == best:
                own = sub[sub["method"] == meth][id_col].map(base_instance_id)
                row.update({
                    "n_configs": int(n_rows.get(meth, 0)),
                    "n_clusters": int(own.nunique()),
                    "mean_diff": 0.0, "ci_lo": 0.0, "ci_hi": 0.0,
                    "margin": equivalence_margin(float(means[best]),
                                                 margin_abs, margin_rel),
                    "wilcoxon_p": 1.0, "verdict": "equivalent",
                    "in_equivalence_set": 1,
                })
                rows.append(row)
                continue
            pt = paired_table(sub, meth, best, value_col=value_col,
                              id_col=id_col, feasible_col=feasible_col,
                              on_duplicate=on_duplicate)
            if pt.empty:
                continue
            d = pt["diff"].to_numpy(dtype=float)
            mean_ref = float(pt["value_b"].mean())
            lo, hi = cluster_bootstrap_ci(
                d, pt["cluster"].to_numpy(), n_boot=n_boot, alpha=alpha,
                seed=_derived_seed(seed, "%s|%s|%s|eqset" % (label, meth, best)))
            verdict = equivalence_verdict(lo, hi, mean_ref, margin_abs,
                                          margin_rel)
            row.update({
                "n_configs": int(len(pt)),
                "n_clusters": int(pt["cluster"].nunique()),
                "mean_diff": float(d.mean()), "ci_lo": lo, "ci_hi": hi,
                "margin": equivalence_margin(mean_ref, margin_abs, margin_rel),
                "wilcoxon_p": wilcoxon_p(d), "verdict": verdict,
                "in_equivalence_set": int(verdict == "equivalent"),
            })
            rows.append(row)

    cols = scope_cols + [c for c in EQUIV_COLUMNS if c not in scope_cols]
    return pd.DataFrame(rows, columns=cols)
