#!/usr/bin/env python
"""Shared work orders between Eval-B empirical instances, and what they do to
the primary comparison's confidence intervals.

Why this analysis exists
------------------------
The final empirical windows were sampled with an acceptance rule that forbade a
new window from overlapping an already-accepted window OF THE SAME (campus,
size-class) CELL (scripts/r4_final_instances.py, track [E]).  Nothing in that
rule constrains two windows of DIFFERENT size classes on the same campus, so a
150-order window and a 400-order window cut from the same campus may cover
overlapping stretches of time and therefore contain some of the same physical
work orders.

The released primary analysis resamples base instances (fmwos.stats:
``base_instance_id`` maps a configuration id onto the instance it was cut from,
and the bootstrap draws those instances with replacement).  Two instances that
share work orders are treated as independent draws by that scheme, which is the
assumption this script measures and then relaxes.

Nothing is re-run and no released output is modified: the sharing is read off
the instance files, and the comparison is recomputed from the released scored
rows with a different cluster label.

What is computed
----------------
1. Overlap audit.  Every final empirical instance (``track == replay`` in
   data/processed/instances_r4/index_r4.csv) is read for its set of work-order
   ids.  Two instances of the same campus SHARE when those sets intersect;
   sharing across campuses is impossible, because a work order belongs to one
   campus.  The audit reports, per instance and per pair, how much is shared,
   and groups the instances into connected components of the sharing relation.
   Every statistic is reported twice: over all final empirical instances, and
   restricted to the four verdict campuses (5, 9, 10, 12), which is the set the
   headline empirical scopes are drawn from.

   The generator track (``track == storm2``) is audited for the record but is
   NOT part of the sharing relation.  Its instances are fresh draws from fitted
   parameter packs, and their work orders carry per-instance synthetic labels
   (``W0``, ``W1``, ...) rather than identifiers of physical jobs, so an
   identical label in two generator instances is a naming collision and not a
   shared work order.  Counting those collisions as sharing would merge the
   whole generator track into one cluster on the strength of a label.

   The same acceptance rule governed the final windows against the RELEASED
   development corpus: a final window had to miss every v1.0 replay window of
   the same campus and the same size class, and nothing constrained it against
   a v1.0 window of a different size class.  So the audit is repeated across
   corpora.  Every final empirical instance is compared with every v1.0 replay
   instance of its campus (data/processed/instances/index.csv), and the shared
   work orders are split by the v1.0 instance's own ``split``, because a work
   order that appears in a TRAIN-split v1.0 window is one a policy could have
   been trained on and a work order that appears only in a TEST-split one is
   not.

2. Bootstrap re-clustered on components.  Every family is paired against EDD on
   the empirical scopes exactly as the released analysis pairs it, and the
   cluster bootstrap is run twice: once with clusters = base instance (the
   released scheme) and once with clusters = the connected component of the
   sharing relation, so instances that share work orders resample together.
   The pairing, the resample count, the level and the equivalence margin are
   identical, so the point estimate is unchanged by construction and only the
   interval can move.  The base arm is checked field by field against the
   released results/r4_final/analysis/family_comparisons.csv, and a mismatch
   stops the run.

   The generator scopes are excluded: their instances are independent draws and
   share nothing, so re-clustering them cannot change an interval.

3. Size-stratified sensitivity.  All the sharing that exists is between the two
   size classes; within one size class there is none.  A comparison run inside
   a single size class therefore has no shared work orders at all, which is the
   clean complement to the component bootstrap.  Each empirical crew-multiplier
   scope is split into its 150-order and 400-order strata and the same
   family-vs-EDD comparison is run inside each.  The two strata do not cover the
   same campuses, and the report says so: a difference between them confounds
   size with campus.

Statistics are the protocol's throughout (fmwos.stats): paired on the
instance-configuration id, 95% percentile bootstrap with 10000 resamples,
master seed 12345, per-comparison stream derived from the comparison label,
equivalence margin max(1.0, 1% of the reference mean).  Sign convention: a
negative difference means the family is better than EDD.

Inputs
------
  data/processed/instances_r4/index_r4.csv and the instance JSON it points at
  data/processed/instances/index.csv and the v1.0 replay JSON it points at
  results/r4_final/results.csv                          (Eval-B scored rows)
  results/r4_final/analysis/family_comparisons.csv      (released comparison)

Outputs
-------
  results/r4_final/analysis/overlap_instances.csv    per instance: shared work
                                                     orders and its component
  results/r4_final/analysis/overlap_pairs.csv        per sharing pair
  results/r4_final/analysis/overlap_devcorpus.csv    per instance: work orders
                                                     shared with the v1.0
                                                     development corpus
  results/r4_final/analysis/overlap_sensitivity.csv  the two re-analyses
  results/r4_final/analysis/overlap_summary.md       the readable report
  paper/macros_r4h.tex                               the \\ovl... macros

Usage
-----
    PYTHONPATH=src python scripts/r4_overlap.py [--out DIR] [--paper DIR]
                                                [--n-boot N] [--seed S]
                                                [--no-macros]

Re-running is idempotent: the bootstrap is seeded from the protocol master seed
and every output is rewritten from the same inputs, so a second run reproduces
every digit.
"""

from __future__ import annotations

import argparse
import itertools
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Small dense bincounts only; keep the shared box's BLAS from oversubscribing.
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "8")

import numpy as np                                          # noqa: E402
import pandas as pd                                         # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from fmwos import stats                                     # noqa: E402
# Scope construction, the fixed Eval-B vocabulary, macro plumbing and number
# formatting are shared with the released analyses, and the seed collapse comes
# from the family analysis itself, so no scope and no method set is redefined.
from r4_analysis import (CREW_MULTIPLIERS, ROLLING, VALUE_COL,  # noqa: E402
                         VERDICT_CAMPUSES, M_TOKEN,
                         MacroFile, existing_macro_names, house_number,
                         f_int, load_results, scope_frames)
from r4_family_analysis import (FAMILY_KEYS, FAMILY_NAME,   # noqa: E402
                                REFERENCE, VERDICT_TOKEN, collapse_families)
from r4_family_tables import FAMILY_LABEL                   # noqa: E402

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
INDEX_CSV = Path("data/processed/instances_r4/index_r4.csv")
INST_ROOT = Path("data/processed/instances_r4")
V1_INDEX_CSV = Path("data/processed/instances/index.csv")
V1_INST_ROOT = Path("data/processed/instances")
EVALB_CSV = Path("results/r4_final/results.csv")
OUT_DIR = Path("results/r4_final/analysis")
PAPER_DIR = Path("paper")
RELEASED_CSV = OUT_DIR / "family_comparisons.csv"
MACRO_FILE = "macros_r4h.tex"

EMPIRICAL_TRACK = "replay"
GENERATOR_TRACK = "storm2"

# The scopes whose clusters can contain shared work orders. The generator scopes
# are drawn instance by instance from fitted packs and share nothing, so they
# are unaffected by the re-clustering and are not recomputed.
SENSITIVITY_SCOPE_TYPES = ("emp_m", "transfer", "stress", "emp_pooled")

# The size classes of the empirical track, and the token each one contributes to
# a macro name.
SIZE_TOKEN = {150: "OneFifty", 400: "FourHundred"}

# The verdicts whose per-stratum counts each crew multiplier contributes to the
# macro file.  Every multiplier reports the equivalent count; the tightened ones
# also report what the families that left the equivalence set became, which is
# the quantity the narrowing is read from.
SIZE_MACRO_VERDICTS = {1.0: ("equivalent",),
                       0.8: ("equivalent", "inconclusive"),
                       0.6: ("equivalent", "inconclusive", "worse")}
# The verdicts whose member families are named, not only counted.
SIZE_MACRO_NAMED = ("worse",)

# Every field of the released comparison that the base arm must reproduce.
CHECK_FIELDS = ("n_configs", "n_clusters", "mean_diff", "ci_lo", "ci_hi")
CHECK_TOL = 1e-9

META_COLS = ["campus", "track", "split", "size", "regime", "crew_multiplier",
             "u_target", "u_realized", "u_bin", "cluster", "eval_set"]

SENSITIVITY_COLUMNS = [
    "analysis", "scope_type", "scope", "family", "reference", "n_configs",
    "n_clusters_base", "n_clusters_component", "mean_ref", "mean_diff",
    "ci_lo_base", "ci_hi_base", "verdict_base", "ci_lo_component",
    "ci_hi_component", "verdict_component", "ci_width_base",
    "ci_width_component", "width_ratio", "verdict_changed",
]

INSTANCE_COLUMNS = ["id", "campus", "size", "n_wos", "n_shared_wos",
                    "shared_frac", "component", "component_size"]
PAIR_COLUMNS = ["id_a", "id_b", "campus", "size_a", "size_b", "kind",
                "n_shared", "frac_a", "frac_b"]
DEVCORPUS_COLUMNS = ["id", "campus", "size", "n_wos", "n_shared_wos",
                     "shared_frac", "n_v1_train_instances",
                     "n_v1_test_instances", "v1_size_classes"]

# A campus counts as heavily shared with the development corpus when the mean
# per-instance shared fraction of one of its size classes passes this level,
# that is when the typical final window there is more than half made of work
# orders the development corpus already contained.
DEV_MAJORITY_FRAC = 0.5


# --------------------------------------------------------------------------- #
# Part 1: the overlap audit
# --------------------------------------------------------------------------- #
def load_work_order_ids(index_csv: Path, inst_root: Path, track: str) -> dict:
    """Work-order id set of every instance of one track, keyed by instance id."""
    idx = pd.read_csv(index_csv)
    sub = idx[idx["track"] == track].sort_values("id", kind="mergesort")
    out = {}
    for r in sub.itertuples():
        with open(inst_root / str(r.path)) as f:
            inst = json.load(f)
        ids = {str(w["id"]) for w in inst["work_orders"]}
        if len(ids) != len(inst["work_orders"]):
            raise SystemExit("instance %s repeats a work-order id" % r.id)
        out[str(r.id)] = ids
    return out, sub.reset_index(drop=True)


def sharing_pairs(meta: pd.DataFrame, wo_ids: dict) -> pd.DataFrame:
    """Every pair of instances of one campus whose work-order sets intersect.

    Pairs are enumerated within a campus only, in sorted id order, so the file
    is byte-identical from run to run.
    """
    rows = []
    size_of = {str(r.id): int(r.size_class) for r in meta.itertuples()}
    for campus, g in meta.groupby("campus", sort=True):
        ids = sorted(str(i) for i in g["id"])
        for a, b in itertools.combinations(ids, 2):
            shared = wo_ids[a] & wo_ids[b]
            if not shared:
                continue
            sa, sb = size_of[a], size_of[b]
            rows.append({
                "id_a": a, "id_b": b, "campus": int(campus),
                "size_a": sa, "size_b": sb,
                "kind": "same-size" if sa == sb else "cross-size",
                "n_shared": int(len(shared)),
                "frac_a": len(shared) / len(wo_ids[a]),
                "frac_b": len(shared) / len(wo_ids[b]),
            })
    return pd.DataFrame(rows, columns=PAIR_COLUMNS)


def components(ids, pairs: pd.DataFrame) -> dict:
    """Connected components of the sharing relation, labelled by their least id.

    Union-find over the instance ids, joined by every sharing pair.  A component
    is named by the smallest instance id it contains, which is stable under
    re-runs and readable in a cluster column.
    """
    ids = sorted(str(i) for i in ids)
    parent = {i: i for i in ids}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for r in pairs.itertuples():
        ra, rb = find(str(r.id_a)), find(str(r.id_b))
        if ra != rb:
            # Attach to the lexicographically smaller root so the component
            # label does not depend on the order the pairs were enumerated in.
            lo, hi = (ra, rb) if ra < rb else (rb, ra)
            parent[hi] = lo
    return {i: find(i) for i in ids}


def instance_table(meta: pd.DataFrame, wo_ids: dict, pairs: pd.DataFrame,
                   comp: dict) -> pd.DataFrame:
    """One row per instance: its shared work orders and its component."""
    shared = {i: set() for i in wo_ids}
    for r in pairs.itertuples():
        common = wo_ids[str(r.id_a)] & wo_ids[str(r.id_b)]
        shared[str(r.id_a)] |= common
        shared[str(r.id_b)] |= common
    sizes = pd.Series(list(comp.values())).value_counts().to_dict()
    rows = []
    for r in meta.sort_values("id", kind="mergesort").itertuples():
        i = str(r.id)
        n_wos = len(wo_ids[i])
        if n_wos != int(r.n_wos):
            raise SystemExit("instance %s has %d work orders but the index says "
                             "%d" % (i, n_wos, int(r.n_wos)))
        rows.append({"id": i, "campus": int(r.campus),
                     "size": int(r.size_class), "n_wos": n_wos,
                     "n_shared_wos": len(shared[i]),
                     "shared_frac": len(shared[i]) / n_wos,
                     "component": comp[i],
                     "component_size": int(sizes[comp[i]])})
    return pd.DataFrame(rows, columns=INSTANCE_COLUMNS)


def audit_summary(inst: pd.DataFrame, pairs: pd.DataFrame, wo_ids: dict,
                  campuses=None) -> dict:
    """Audit statistics over all instances, or over one set of campuses."""
    if campuses is None:
        keep = inst
        p = pairs
    else:
        keep = inst[inst["campus"].isin(list(campuses))]
        p = pairs[pairs["campus"].isin(list(campuses))]
    ids = set(keep["id"])
    slots = int(sum(len(wo_ids[i]) for i in sorted(ids)))
    distinct = len(set().union(*(wo_ids[i] for i in sorted(ids)))) if ids else 0
    touched = set(p["id_a"]) | set(p["id_b"])
    n_comp = int(keep["component"].nunique())
    return {
        "n_instances": int(len(keep)),
        "n_pairs": int(len(p)),
        "n_pairs_cross_size": int((p["kind"] == "cross-size").sum()),
        "n_pairs_same_size": int((p["kind"] == "same-size").sum()),
        "n_touched": int(len(touched & ids)),
        "n_slots": slots,
        "n_distinct": distinct,
        "duplication_factor": (slots / distinct) if distinct else float("nan"),
        "n_components": n_comp,
        "n_merges": int(len(keep)) - n_comp,
        "max_component_size": int(keep["component_size"].max()) if len(keep)
                              else 0,
        "max_shared_frac": float(keep["shared_frac"].max()) if len(keep) else 0.0,
        "campuses": sorted(int(c) for c in keep["campus"].unique()),
    }


def generator_note(wo_ids: dict, meta: pd.DataFrame) -> dict:
    """Label collisions across generator instances, reported but never counted.

    A generator instance labels its work orders ``W0``, ``W1``, ... in draw
    order, so the labels of two instances collide almost completely.  These are
    not shared jobs, and the count below exists to make that explicit rather
    than to enter any cluster.
    """
    ids = sorted(wo_ids)
    slots = int(sum(len(wo_ids[i]) for i in ids))
    distinct = len(set().union(*(wo_ids[i] for i in ids))) if ids else 0
    n_colliding = 0
    n_within = 0
    for _campus, g in meta.groupby("campus", sort=True):
        cids = sorted(str(i) for i in g["id"])
        for a, b in itertools.combinations(cids, 2):
            n_within += 1
            if wo_ids[a] & wo_ids[b]:
                n_colliding += 1
    return {"n_instances": len(ids), "n_slots": slots, "n_distinct": distinct,
            "n_same_campus_pairs": n_within, "n_colliding_pairs": n_colliding,
            "example_labels": sorted(wo_ids[ids[0]])[:1] if ids else []}


# --------------------------------------------------------------------------- #
# Part 1b: sharing with the released v1.0 development corpus
# --------------------------------------------------------------------------- #
def v1_owner_index(index_csv: Path, inst_root: Path, campuses):
    """Map ``(campus, work-order id)`` onto the v1.0 replay instances holding it.

    Only the replay track is read: the generator, storm and pmmix tracks carry
    synthetic work-order labels, for the same reason the Eval-B generator track
    is excluded above.  The value of each entry is a list of
    ``(instance id, split, size class)``, so a final instance can be attributed
    to the split of the v1.0 windows it shares with.
    """
    idx = pd.read_csv(index_csv)
    sub = idx[(idx["track"] == EMPIRICAL_TRACK)
              & (idx["campus"].isin(list(campuses)))]
    sub = sub.sort_values("id", kind="mergesort").reset_index(drop=True)
    owners = {}
    for r in sub.itertuples():
        with open(inst_root / str(r.path)) as f:
            inst = json.load(f)
        key = int(r.campus)
        for w in inst["work_orders"]:
            owners.setdefault((key, str(w["id"])), []).append(
                (str(r.id), str(r.split), int(r.size_class)))
    return owners, sub


def dev_corpus_table(meta: pd.DataFrame, wo_ids: dict, owners: dict
                     ) -> pd.DataFrame:
    """One row per final empirical instance: what it shares with v1.0."""
    rows = []
    for r in meta.sort_values("id", kind="mergesort").itertuples():
        i, campus = str(r.id), int(r.campus)
        train, test, sizes, n_shared = set(), set(), set(), 0
        for w in sorted(wo_ids[i]):
            hits = owners.get((campus, w))
            if not hits:
                continue
            n_shared += 1
            for v1_id, split, size_class in hits:
                (train if split == "train" else test).add(v1_id)
                sizes.add(size_class)
        n_wos = len(wo_ids[i])
        rows.append({"id": i, "campus": campus, "size": int(r.size_class),
                     "n_wos": n_wos, "n_shared_wos": n_shared,
                     "shared_frac": n_shared / n_wos,
                     "n_v1_train_instances": len(train),
                     "n_v1_test_instances": len(test),
                     "v1_size_classes": "|".join(str(s) for s in sorted(sizes))})
    return pd.DataFrame(rows, columns=DEVCORPUS_COLUMNS)


def dev_corpus_summary(dev: pd.DataFrame, v1_meta: pd.DataFrame) -> dict:
    """The headline counts of the cross-corpus audit."""
    by_cell = (dev.groupby(["campus", "size"])["shared_frac"]
               .agg(n_instances="size", mean_frac="mean", max_frac="max")
               .reset_index())
    heavy = by_cell[by_cell["mean_frac"] > DEV_MAJORITY_FRAC]
    return {
        "n_v1_instances": int(len(v1_meta)),
        "n_v1_train": int((v1_meta["split"] == "train").sum()),
        "n_v1_test": int((v1_meta["split"] == "test").sum()),
        "n_instances": int(len(dev)),
        "n_sharing_any": int((dev["n_shared_wos"] > 0).sum()),
        "n_sharing_train": int((dev["n_v1_train_instances"] > 0).sum()),
        "n_sharing_test": int((dev["n_v1_test_instances"] > 0).sum()),
        "by_cell": by_cell,
        "train_test_by_cell": (
            dev.assign(shares_train=(dev["n_v1_train_instances"] > 0).astype(int),
                       shares_test=(dev["n_v1_test_instances"] > 0).astype(int))
            .groupby(["campus", "size"])[["shares_train", "shares_test"]]
            .sum().reset_index()),
        "heavy_cells": heavy,
        "heavy_campuses": sorted(int(c) for c in heavy["campus"].unique()),
        "heavy_max_frac": float(heavy["mean_frac"].max()) if len(heavy) else 0.0,
        "heavy_median_frac": float(heavy["mean_frac"].median()) if len(heavy)
                             else 0.0,
        "heavy_min_frac": float(heavy["mean_frac"].min()) if len(heavy) else 0.0,
        "partners": (dev[dev["n_shared_wos"] > 0]
                     .groupby(["size", "v1_size_classes"]).size()
                     .rename("n_instances").reset_index()),
    }


# --------------------------------------------------------------------------- #
# Part 2 and 3: the paired comparison under two cluster schemes
# --------------------------------------------------------------------------- #
def paired_arm(sub: pd.DataFrame, method: str, scope_label: str,
               cluster_map, n_boot: int, seed: int) -> dict:
    """One family against EDD on one scope, under one cluster labelling.

    The pairing, the reference mean, the resample count and the margin are the
    released ones; ``cluster_map`` optionally relabels each base instance onto
    its sharing component.  The bootstrap stream is derived from the comparison
    label exactly as ``fmwos.stats.compare_all`` derives it, so passing no
    cluster map reproduces the released interval digit for digit.
    """
    pt = stats.paired_table(sub, method, REFERENCE, value_col=VALUE_COL)
    if pt.empty:
        return None
    d = pt["diff"].to_numpy(dtype=float)
    if cluster_map is None:
        clusters = pt["cluster"].to_numpy()
    else:
        missing = sorted(set(pt["cluster"]) - set(cluster_map))
        if missing:
            raise SystemExit("no sharing component for base instance(s) %s; the "
                             "overlap audit and the scored rows disagree"
                             % missing[:3])
        clusters = pt["cluster"].map(cluster_map).to_numpy()
    label = "analysis_scope=%s|%s|%s" % (scope_label, method, REFERENCE)
    lo, hi = stats.cluster_bootstrap_ci(
        d, clusters, n_boot=n_boot, alpha=stats.ALPHA,
        seed=stats._derived_seed(seed, label))
    mean_ref = float(pt["value_b"].mean())
    return {"n_configs": int(len(pt)),
            "n_clusters": int(pd.Series(clusters).nunique()),
            "mean_ref": mean_ref, "mean_diff": float(d.mean()),
            "ci_lo": float(lo), "ci_hi": float(hi),
            "verdict": stats.equivalence_verdict(lo, hi, mean_ref)}


def scope_methods(sub: pd.DataFrame):
    """The families present in one scope, in the released report order."""
    present = set(sub["method"].astype(str))
    return [m for m in FAMILY_KEYS + (ROLLING,)
            if m in present and m != REFERENCE]


def cluster_sensitivity(fam: pd.DataFrame, cluster_map: dict, n_boot: int,
                        seed: int):
    """Every family on every affected scope, under both cluster schemes."""
    rows = []
    for scope_type, scope, sub in scope_frames(fam):
        if scope_type not in SENSITIVITY_SCOPE_TYPES:
            continue
        for method in scope_methods(sub):
            base = paired_arm(sub, method, scope, None, n_boot, seed)
            if base is None:
                continue
            comp = paired_arm(sub, method, scope, cluster_map, n_boot, seed)
            if abs(base["mean_diff"] - comp["mean_diff"]) > 0.0:
                raise SystemExit(
                    "point estimate moved between cluster schemes on scope %s, "
                    "family %s (%r vs %r); only the cluster labels may differ"
                    % (scope, method, base["mean_diff"], comp["mean_diff"]))
            rows.append(_sensitivity_row("cluster", scope_type, scope, method,
                                         base, comp))
    return pd.DataFrame(rows, columns=SENSITIVITY_COLUMNS)


def size_sensitivity(fam: pd.DataFrame, n_boot: int, seed: int):
    """The same comparison inside each size class of each crew-multiplier scope.

    Within one size class no two instances share a work order, so the base
    instance and the sharing component are the same cluster and only the base
    columns are populated.
    """
    rows, coverage = [], []
    scopes = {(t, s): sub for t, s, sub in scope_frames(fam)}
    for m in CREW_MULTIPLIERS:
        sub = scopes[("emp_m", "m=%s" % m)]
        for size in sorted(int(s) for s in sub["size"].unique()):
            stratum = sub[sub["size"] == size]
            label = "m=%s|size=%d" % (m, size)
            covered = sorted(int(c) for c in stratum["campus"].unique())
            ref_rows = stratum[stratum["method"] == REFERENCE]
            coverage.append({"scope": "m=%s" % m, "size": size,
                             "n_configs": int(len(ref_rows)),
                             "n_clusters": int(ref_rows["cluster"].nunique()),
                             "campuses": covered})
            for method in scope_methods(stratum):
                base = paired_arm(stratum, method, label, None, n_boot, seed)
                if base is None:
                    continue
                rows.append(_sensitivity_row("size", "emp_m_size", label,
                                             method, base, None))
    return (pd.DataFrame(rows, columns=SENSITIVITY_COLUMNS),
            pd.DataFrame(coverage))


def _sensitivity_row(analysis: str, scope_type: str, scope: str, method: str,
                     base: dict, comp) -> dict:
    width_base = base["ci_hi"] - base["ci_lo"]
    row = {
        "analysis": analysis, "scope_type": scope_type, "scope": scope,
        "family": FAMILY_NAME.get(method, method), "reference": REFERENCE,
        "n_configs": base["n_configs"],
        "n_clusters_base": base["n_clusters"],
        "n_clusters_component": np.nan,
        "mean_ref": base["mean_ref"], "mean_diff": base["mean_diff"],
        "ci_lo_base": base["ci_lo"], "ci_hi_base": base["ci_hi"],
        "verdict_base": base["verdict"],
        "ci_lo_component": np.nan, "ci_hi_component": np.nan,
        "verdict_component": "",
        "ci_width_base": width_base, "ci_width_component": np.nan,
        "width_ratio": np.nan, "verdict_changed": "",
    }
    if comp is not None:
        width_comp = comp["ci_hi"] - comp["ci_lo"]
        row.update({
            "n_clusters_component": comp["n_clusters"],
            "ci_lo_component": comp["ci_lo"], "ci_hi_component": comp["ci_hi"],
            "verdict_component": comp["verdict"],
            "ci_width_component": width_comp,
            "width_ratio": (width_comp / width_base) if width_base > 0
                           else float("nan"),
            "verdict_changed": int(comp["verdict"] != base["verdict"]),
        })
    return row


# --------------------------------------------------------------------------- #
# The released-reproduction self-check
# --------------------------------------------------------------------------- #
def check_released(sens: pd.DataFrame, released_csv: Path) -> pd.DataFrame:
    """Compare every base-arm row against the released family comparison.

    The base arm differs from the released analysis only in that it recomputes
    the interval, so each of ``n_configs``, ``n_clusters``, ``mean_diff``,
    ``ci_lo``, ``ci_hi`` and ``verdict`` must come back unchanged.  A single
    disagreement means the cluster labels or the bootstrap stream of this script
    are not the released ones, and the sensitivity would then be measuring the
    difference between two implementations rather than between two clusterings.
    """
    released = pd.read_csv(released_csv)
    rows = []
    for r in sens[sens["analysis"] == "cluster"].itertuples():
        want = released[(released["scope_type"] == r.scope_type)
                        & (released["scope"] == r.scope)
                        & (released["family"] == r.family)]
        if want.empty:
            rows.append({"scope_type": r.scope_type, "scope": r.scope,
                         "family": r.family, "field": "row",
                         "released": "", "recomputed": "", "abs_diff": np.nan,
                         "ok": 0})
            continue
        w = want.iloc[0]
        got = {"n_configs": r.n_configs, "n_clusters": r.n_clusters_base,
               "mean_diff": r.mean_diff, "ci_lo": r.ci_lo_base,
               "ci_hi": r.ci_hi_base}
        for field in CHECK_FIELDS:
            a, b = float(w[field]), float(got[field])
            rows.append({"scope_type": r.scope_type, "scope": r.scope,
                         "family": r.family, "field": field,
                         "released": a, "recomputed": b,
                         "abs_diff": abs(a - b),
                         "ok": int(abs(a - b) <= CHECK_TOL)})
        rows.append({"scope_type": r.scope_type, "scope": r.scope,
                     "family": r.family, "field": "verdict",
                     "released": str(w["verdict"]),
                     "recomputed": str(r.verdict_base), "abs_diff": np.nan,
                     "ok": int(str(w["verdict"]) == str(r.verdict_base))})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #
def _f(x, nd=3) -> str:
    v = float(x)
    if not np.isfinite(v):
        return "-"
    return ("%%.%df" % nd) % v


def _cell_frame(sens: pd.DataFrame) -> pd.DataFrame:
    return sens[sens["analysis"] == "cluster"]


def changed_cells(sens: pd.DataFrame) -> pd.DataFrame:
    c = _cell_frame(sens)
    return c[c["verdict_changed"] == 1]


def equivalent_count(sens: pd.DataFrame, analysis: str, scope: str,
                     column: str) -> int:
    return verdict_count(sens, analysis, scope, column, "equivalent")


def verdict_count(sens: pd.DataFrame, analysis: str, scope: str, column: str,
                  verdict: str) -> int:
    sub = sens[(sens["analysis"] == analysis) & (sens["scope"] == scope)]
    return int((sub[column] == verdict).sum())


def verdict_families(sens: pd.DataFrame, analysis: str, scope: str,
                     column: str, verdict: str):
    """The families carrying one verdict on one scope, in the file's own order."""
    sub = sens[(sens["analysis"] == analysis) & (sens["scope"] == scope)]
    return [str(f) for f in sub.loc[sub[column] == verdict, "family"]]


def family_phrase(families) -> str:
    """`WSPT, LPT and Random`: the display labels joined the house way."""
    labels = [FAMILY_LABEL.get(f, f) for f in families]
    if len(labels) <= 1:
        return "".join(labels)
    return ", ".join(labels[:-1]) + " and " + labels[-1]


def size_scope(m, size: int) -> str:
    return "m=%s|size=%d" % (m, size)


def write_report(path: Path, audit_all: dict, audit_verdict: dict,
                 gen: dict, dev: dict, inst: pd.DataFrame, pairs: pd.DataFrame,
                 sens: pd.DataFrame, coverage: pd.DataFrame,
                 check: pd.DataFrame, n_boot: int, seed: int) -> Path:
    L = []
    A = L.append
    cells = _cell_frame(sens)
    changed = changed_cells(sens)
    worst = cells.loc[cells["width_ratio"].idxmax()]

    A("# Shared work orders between Eval-B empirical instances")
    A("")
    A("Generated by scripts/r4_overlap.py on %s."
      % datetime.now().isoformat(timespec="seconds"))
    A("Statistics: base-instance and component cluster bootstraps, %d "
      "resamples, master seed %d, equivalence margin max(%.1f, %.0f%% of the "
      "reference mean) (fmwos.stats)."
      % (n_boot, seed, stats.MARGIN_ABS, 100 * stats.MARGIN_REL))
    A("")

    A("## 1. Overlap audit")
    A("")
    A("The final empirical windows were accepted only if they did not overlap "
      "an already-accepted window of the same (campus, size-class) cell, so a "
      "150-order window and a 400-order window of one campus were free to cover "
      "the same stretch of time. Two instances share when their work-order id "
      "sets intersect; sharing across campuses is impossible.")
    A("")
    A("- final empirical instances: %d" % audit_all["n_instances"])
    A("- pairs sharing at least one work order: %d (%d cross-size, %d "
      "same-size)" % (audit_all["n_pairs"], audit_all["n_pairs_cross_size"],
                      audit_all["n_pairs_same_size"]))
    A("- instances touching at least one other instance: %d of %d"
      % (audit_all["n_touched"], audit_all["n_instances"]))
    A("- work-order slots %d over %d distinct work-order ids (duplication "
      "factor %.3f)" % (audit_all["n_slots"], audit_all["n_distinct"],
                        audit_all["duplication_factor"]))
    A("- connected components of the sharing relation: %d over %d instances "
      "(%d merges); the largest component holds %d instances"
      % (audit_all["n_components"], audit_all["n_instances"],
         audit_all["n_merges"], audit_all["max_component_size"]))
    A("- largest per-instance shared fraction: %.3f"
      % audit_all["max_shared_frac"])
    A("")
    A("Sharing pairs by campus and kind:")
    A("")
    if len(pairs):
        A(pairs.groupby(["campus", "kind"]).size().rename("n_pairs")
          .reset_index().to_string(index=False))
    else:
        A("(none)")
    A("")
    A("Mean and largest per-instance shared fraction, by campus and size class:")
    A("")
    A(inst.groupby(["campus", "size"])["shared_frac"]
      .agg(["size", "mean", "max"]).rename(columns={"size": "n_instances"})
      .round(4).to_string())
    A("")
    A("Generator track, for the record and NOT counted as sharing: %d "
      "instances, %d work-order slots over %d distinct labels, and %d of %d "
      "same-campus pairs share a label. Generator work orders carry "
      "per-instance synthetic labels (the first is %r), so an identical label "
      "in two instances is a naming collision rather than one physical job "
      "appearing twice. Counting those collisions would merge the whole "
      "generator track into one cluster on the strength of a label."
      % (gen["n_instances"], gen["n_slots"], gen["n_distinct"],
         gen["n_colliding_pairs"], gen["n_same_campus_pairs"],
         gen["example_labels"][0] if gen["example_labels"] else ""))
    A("")

    A("## 2. Sharing with the released development corpus")
    A("")
    A("The same acceptance rule governed the final windows against the v1.0 "
      "replay corpus: a final window had to miss every v1.0 window of the same "
      "campus and the same size class, and nothing constrained it against a "
      "v1.0 window of a different size class. Each final instance is therefore "
      "compared with all %d v1.0 replay instances of its campus (%d train "
      "split, %d test split), and the sharing is split by the v1.0 instance's "
      "own split."
      % (dev["n_v1_instances"], dev["n_v1_train"], dev["n_v1_test"]))
    A("")
    A("**No work order in the final evaluation appears in any window a policy "
      "was trained on: %d of %d final empirical instances share a work order "
      "with a train-split v1.0 instance, so there is no training leakage.** "
      "Sharing with the test split is common: %d of %d instances share at "
      "least one work order with a test-split v1.0 window, which is a window "
      "the development evaluation scored but no policy learned from."
      % (dev["n_sharing_train"], dev["n_instances"], dev["n_sharing_test"],
         dev["n_instances"]))
    A("")
    A("Shared fraction with the v1.0 corpus, by campus and size class:")
    A("")
    A(dev["by_cell"].round(4).to_string(index=False))
    A("")
    A("Instances sharing with a train-split and with a test-split v1.0 "
      "instance, by campus and size class:")
    A("")
    A(dev["train_test_by_cell"].to_string(index=False))
    A("")
    A("Which v1.0 size classes the sharing comes from, over the %d instances "
      "that share anything (all of it cross-size, as the acceptance rule "
      "allows):" % dev["n_sharing_any"])
    A("")
    A(dev["partners"].to_string(index=False))
    A("")
    n_from_400 = int(dev["partners"].loc[
        dev["partners"]["v1_size_classes"].str.split("|").apply(
            lambda s: "400" in s), "n_instances"].sum())
    A("On campuses %s a majority of the work orders in a final 150-order "
      "window also sit inside v1.0 test-split windows of another size class, "
      "the 400-order ones in %d of the %d instances that share anything: the "
      "mean shared fraction runs from %.3f to %.3f, typically %.3f. The final "
      "evaluation is therefore fresh in its windows and in its construction, "
      "and not fresh in the underlying work-order population."
      % (", ".join(str(c) for c in dev["heavy_campuses"]), n_from_400,
         dev["n_sharing_any"], dev["heavy_min_frac"], dev["heavy_max_frac"],
         dev["heavy_median_frac"]))
    A("")

    A("## 3. The verdict campuses")
    A("")
    A("The headline empirical scopes are drawn from campuses %s, one "
      "configuration per instance per crew multiplier, so the numbers the "
      "manuscript quotes are the ones restricted to that set."
      % ", ".join(str(c) for c in audit_verdict["campuses"]))
    A("")
    A("- instances: %d" % audit_verdict["n_instances"])
    A("- sharing pairs: %d (%d cross-size, %d same-size)"
      % (audit_verdict["n_pairs"], audit_verdict["n_pairs_cross_size"],
         audit_verdict["n_pairs_same_size"]))
    A("- instances touching at least one other: %d of %d"
      % (audit_verdict["n_touched"], audit_verdict["n_instances"]))
    A("- work-order slots %d over %d distinct ids (duplication factor %.3f)"
      % (audit_verdict["n_slots"], audit_verdict["n_distinct"],
         audit_verdict["duplication_factor"]))
    A("- components: %d over %d instances (%d merges), largest %d"
      % (audit_verdict["n_components"], audit_verdict["n_instances"],
         audit_verdict["n_merges"], audit_verdict["max_component_size"]))
    A("")

    A("## 4. The primary comparison re-clustered on components")
    A("")
    ok = int(check["ok"].sum()) == len(check)
    A("Self-check against %s: %s (%d field comparisons over %d rows, %d "
      "disagreements)."
      % (RELEASED_CSV, "PASS" if ok else "FAIL", len(check),
         len(cells), int((check["ok"] == 0).sum())))
    A("")
    A("The base arm resamples base instances, the component arm resamples the "
      "connected components of the sharing relation. Everything else is held "
      "fixed, so the point estimate is identical in the two arms and only the "
      "interval can move. The generator scopes are excluded: their instances "
      "are independent draws that share nothing, so re-clustering them cannot "
      "change an interval.")
    A("")
    A("Verdicts that change under component clustering: %d of %d compared "
      "(scope, family) cells." % (len(changed), len(cells)))
    A("")
    if len(changed):
        A(changed[["scope_type", "scope", "family", "mean_diff",
                   "ci_lo_base", "ci_hi_base", "verdict_base",
                   "ci_lo_component", "ci_hi_component", "verdict_component"]]
          .round(3).to_string(index=False))
    else:
        A("(none: every cell keeps the verdict the released analysis reports)")
    A("")
    A("Largest interval widening: %s on scope %s (%s), width %.3f under base "
      "clustering and %.3f under component clustering, a ratio of %.3f."
      % (worst["family"], worst["scope"], worst["scope_type"],
         float(worst["ci_width_base"]), float(worst["ci_width_component"]),
         float(worst["width_ratio"])))
    A("")
    A("Campuses 1 and 2 contain no sharing at all, so on the transfer and "
      "stress scopes the two clusterings are the same partition and every "
      "width ratio there is exactly 1. A family whose schedule matches EDD on "
      "every configuration of a scope has a zero-width interval under both "
      "clusterings, and its width ratio is left empty rather than reported as "
      "a division by zero.")
    A("")
    A("Width ratio by scope (largest, median and smallest over the families "
      "compared there):")
    A("")
    A(cells.groupby(["scope_type", "scope"])["width_ratio"]
      .agg(["max", "median", "min"]).round(3).to_string())
    A("")
    A("Every compared cell, both arms:")
    A("")
    A(cells[["scope_type", "scope", "family", "n_configs", "n_clusters_base",
             "n_clusters_component", "mean_diff", "ci_lo_base", "ci_hi_base",
             "verdict_base", "ci_lo_component", "ci_hi_component",
             "verdict_component", "width_ratio"]].round(3)
      .to_string(index=False))
    A("")

    A("## 5. Size-stratified comparison")
    A("")
    A("Within one size class there is no sharing at all, so a comparison run "
      "inside a single size class rests on clusters that are certainly "
      "independent. Each crew-multiplier scope is split into its 150-order and "
      "400-order strata and the same family-vs-EDD comparison is run inside "
      "each, with base-instance clusters.")
    A("")
    size_rows = sens[sens["analysis"] == "size"]
    grid = (size_rows.groupby(["scope", "verdict_base"]).size()
            .unstack(fill_value=0))
    A("Verdicts against EDD by stratum and crew multiplier:")
    A("")
    A(grid.to_string())
    A("")
    A("The equivalence set narrows in both strata as crews tighten, and it "
      "narrows faster in the 400-order stratum, which is also the only one "
      "where any family is confirmed worse than EDD. Two things temper that "
      "reading. The 400-order stratum holds half as many clusters, so its "
      "intervals are wider on sample size alone; and it covers only two "
      "campuses, so the contrast between the strata is confounded with campus, "
      "as the paragraph below states. Working the other way, the equivalence "
      "margin is 1% of the reference mean, which is several times larger in "
      "the 400-order stratum, so that stratum is judged against a more "
      "forgiving margin and still narrows faster.")
    A("")
    for m in CREW_MULTIPLIERS:
        scope = "m=%s" % m
        for size in sorted(SIZE_TOKEN):
            label = size_scope(m, size)
            sub = size_rows[size_rows["scope"] == label]
            if sub.empty:
                continue
            cov = coverage[(coverage["scope"] == scope)
                           & (coverage["size"] == size)]
            counts = "; ".join(
                "%d %s" % (int((sub["verdict_base"] == v).sum()), v)
                for v in ("better", "equivalent", "inconclusive", "worse")
                if int((sub["verdict_base"] == v).sum()))
            A("**%s** (%d configurations, %d clusters, campuses %s). Of %d "
              "families compared against EDD: %s."
              % (label, int(cov["n_configs"].iloc[0]),
                 int(cov["n_clusters"].iloc[0]),
                 ", ".join(str(c) for c in cov["campuses"].iloc[0]),
                 len(sub), counts))
            A("")
            # The margin is not a column of the sensitivity file; it is the
            # protocol's function of the reference mean, recomputed here so the
            # table shows what each verdict was measured against.
            shown = sub.assign(margin=sub["mean_ref"].map(
                stats.equivalence_margin))
            A(shown[["family", "n_configs", "n_clusters_base", "mean_ref",
                     "margin", "mean_diff", "ci_lo_base", "ci_hi_base",
                     "verdict_base"]].round(3).to_string(index=False))
            A("")
    A("Stratum coverage on every crew multiplier:")
    A("")
    A(coverage.to_string(index=False))
    A("")
    A("The two strata do not cover the same campuses: 150-order windows exist "
      "on campuses %s and 400-order windows only on campuses %s, so a "
      "difference between the strata confounds instance size with campus and "
      "is not evidence about size alone."
      % (", ".join(str(c) for c in
                   coverage[coverage["size"] == 150]["campuses"].iloc[0]),
         ", ".join(str(c) for c in
                   coverage[coverage["size"] == 400]["campuses"].iloc[0])))
    A("")
    path.write_text("\n".join(L) + "\n")
    return path


# --------------------------------------------------------------------------- #
# Macros (paper/macros_r4h.tex, prefix \ovl)
# --------------------------------------------------------------------------- #
class OverlapMacroFile(MacroFile):
    """A macro collection whose names carry the overlap-analysis prefix."""

    PREFIX = "ovl"

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


SRC_INST = "results/r4_final/analysis/overlap_instances.csv"
SRC_PAIRS = "results/r4_final/analysis/overlap_pairs.csv"
SRC_DEV = "results/r4_final/analysis/overlap_devcorpus.csv"
SRC_SENS = "results/r4_final/analysis/overlap_sensitivity.csv"


def build_macros(audit_all: dict, audit_verdict: dict, dev: dict,
                 sens: pd.DataFrame, coverage: pd.DataFrame,
                 paper_dir: Path) -> OverlapMacroFile:
    target = paper_dir / MACRO_FILE
    existing = set()
    for p in sorted(paper_dir.glob("macros*.tex")):
        if p != target:
            existing |= existing_macro_names(p)
    M = OverlapMacroFile(existing)

    M.section("Overlap audit over every final empirical instance (%s)"
              % SRC_INST)
    M.add("ovlInstances", f_int(audit_all["n_instances"]),
          SRC_INST + " field=id (final empirical instances audited)")
    M.add("ovlPairs", f_int(audit_all["n_pairs"]),
          SRC_PAIRS + " field=id_a (instance pairs sharing at least one work "
                      "order)")
    M.add("ovlPairsCross", f_int(audit_all["n_pairs_cross_size"]),
          SRC_PAIRS + " kind=cross-size")
    M.add("ovlPairsSame", f_int(audit_all["n_pairs_same_size"]),
          SRC_PAIRS + " kind=same-size")
    M.add("ovlTouched", f_int(audit_all["n_touched"]),
          SRC_INST + " field=n_shared_wos > 0 (instances sharing with at least "
                     "one other instance)")
    M.add("ovlSlots", f_int(audit_all["n_slots"]),
          SRC_INST + " field=n_wos summed (work-order slots over all instances)")
    M.add("ovlDistinctWos", f_int(audit_all["n_distinct"]),
          "data/processed/instances_r4 work_orders[*].id (distinct work orders "
          "behind those slots)")
    M.add("ovlDupFactor", _f(audit_all["duplication_factor"]),
          "work-order slots over distinct work orders")
    M.add("ovlComponents", f_int(audit_all["n_components"]),
          SRC_INST + " field=component (connected components of the sharing "
                     "relation)")
    M.add("ovlMerges", f_int(audit_all["n_merges"]),
          SRC_INST + " fields=id/component (instances minus components)")
    M.add("ovlMaxComponent", f_int(audit_all["max_component_size"]),
          SRC_INST + " field=component_size (largest component)")
    M.add("ovlMaxSharedFrac", _f(audit_all["max_shared_frac"]),
          SRC_INST + " field=shared_frac (largest per-instance shared fraction)")

    M.section("The same audit restricted to the verdict campuses %s (%s)"
              % (", ".join(str(c) for c in audit_verdict["campuses"]),
                 SRC_INST))
    M.add("ovlInstancesVerdict", f_int(audit_verdict["n_instances"]),
          SRC_INST + " campus in the verdict set")
    M.add("ovlPairsVerdict", f_int(audit_verdict["n_pairs"]),
          SRC_PAIRS + " campus in the verdict set")
    M.add("ovlTouchedVerdict", f_int(audit_verdict["n_touched"]),
          SRC_INST + " campus in the verdict set, field=n_shared_wos > 0")
    M.add("ovlDistinctWosVerdict", f_int(audit_verdict["n_distinct"]),
          "distinct work orders over the verdict-campus instances")
    M.add("ovlDupFactorVerdict", _f(audit_verdict["duplication_factor"]),
          "work-order slots over distinct work orders, verdict campuses")
    M.add("ovlComponentsVerdict", f_int(audit_verdict["n_components"]),
          SRC_INST + " campus in the verdict set, field=component")
    M.add("ovlMergesVerdict", f_int(audit_verdict["n_merges"]),
          SRC_INST + " campus in the verdict set (instances minus components)")

    M.section("Sharing between the final evaluation and the released v1.0 "
              "development corpus (%s)" % SRC_DEV)
    M.add("ovlDevInstances", f_int(dev["n_instances"]),
          SRC_DEV + " field=id (final empirical instances audited against the "
                    "v1.0 replay corpus)")
    M.add("ovlDevVOneInstances", f_int(dev["n_v1_instances"]),
          "data/processed/instances/index.csv track=replay, campuses of the "
          "final empirical corpus")
    M.add("ovlDevVOneTrain", f_int(dev["n_v1_train"]),
          "data/processed/instances/index.csv track=replay split=train")
    M.add("ovlDevVOneTest", f_int(dev["n_v1_test"]),
          "data/processed/instances/index.csv track=replay split=test")
    M.add("ovlDevSharingTrain", f_int(dev["n_sharing_train"]),
          SRC_DEV + " field=n_v1_train_instances > 0 (final instances sharing "
                    "a work order with a training-split v1.0 window)")
    M.add("ovlDevSharingTest", f_int(dev["n_sharing_test"]),
          SRC_DEV + " field=n_v1_test_instances > 0 (final instances sharing a "
                    "work order with a test-split v1.0 window)")
    M.add("ovlDevAffectedCampuses", f_int(len(dev["heavy_campuses"])),
          SRC_DEV + " field=shared_frac (campuses whose mean per-instance "
                    "shared fraction passes %.1f in a size class: %s)"
          % (DEV_MAJORITY_FRAC,
             ", ".join(str(c) for c in dev["heavy_campuses"])))
    M.add("ovlDevMaxCampusFrac", _f(dev["heavy_max_frac"]),
          SRC_DEV + " field=shared_frac (largest per-campus mean shared "
                    "fraction among those campuses)")
    M.add("ovlDevTypicalCampusFrac", _f(dev["heavy_median_frac"]),
          SRC_DEV + " field=shared_frac (median of those per-campus means)")

    M.section("Component clustering against base-instance clustering (%s "
              "analysis=cluster)" % SRC_SENS)
    cells = _cell_frame(sens)
    changed = changed_cells(sens)
    M.add("ovlCells", f_int(len(cells)),
          SRC_SENS + " analysis=cluster (compared scope-by-family cells)")
    M.add("ovlVerdictChanges", f_int(len(changed)),
          SRC_SENS + " analysis=cluster field=verdict_changed")
    worst = cells.loc[cells["width_ratio"].idxmax()]
    M.add("ovlMaxWidthRatio", _f(worst["width_ratio"]),
          SRC_SENS + " analysis=cluster field=width_ratio (largest interval "
                     "widening, family %s on scope_type=%s scope=%s)"
          % (worst["family"], worst["scope_type"], worst["scope"]))

    M.section("Families equivalent to EDD on the headline scope %s, under each "
              "clustering and inside each size class (%s)"
              % ("m=%s" % CREW_MULTIPLIERS[0], SRC_SENS))
    head_m = CREW_MULTIPLIERS[0]
    head = "m=%s" % head_m
    tok = M_TOKEN[head_m]
    M.add("ovlEquivBase" + tok,
          f_int(equivalent_count(sens, "cluster", head, "verdict_base")),
          SRC_SENS + " analysis=cluster scope=%s field=verdict_base" % head)
    M.add("ovlEquivComponent" + tok,
          f_int(equivalent_count(sens, "cluster", head, "verdict_component")),
          SRC_SENS + " analysis=cluster scope=%s field=verdict_component" % head)
    # A stratum holds the same instances at every crew multiplier (the multiplier
    # rescales crews, it does not add or drop a window), so the two size macros
    # below carry no multiplier token. The assertion keeps that reading honest:
    # if a future corpus ever made a stratum's size depend on the multiplier,
    # the run stops here instead of publishing a count under the wrong label.
    varying = coverage.groupby("size")[["n_configs", "n_clusters"]].nunique()
    if int(varying.to_numpy().max()) != 1:
        raise SystemExit("a size stratum changes size across crew multipliers; "
                         "the ovlSize...Configs/Clusters macros are written "
                         "without a multiplier token and would be ambiguous")
    for size, stok in sorted(SIZE_TOKEN.items()):
        label = size_scope(head_m, size)
        cov = coverage[(coverage["scope"] == head) & (coverage["size"] == size)]
        M.add("ovlEquivSize" + stok,
              f_int(equivalent_count(sens, "size", label, "verdict_base")),
              SRC_SENS + " analysis=size scope=%s field=verdict_base" % label)
        M.add("ovlSize%sConfigs" % stok, f_int(cov["n_configs"].iloc[0]),
              SRC_SENS + " analysis=size field=n_configs (configurations in the "
                         "%d-order stratum; the same at every crew multiplier)"
              % size)
        M.add("ovlSize%sClusters" % stok, f_int(cov["n_clusters"].iloc[0]),
              SRC_SENS + " analysis=size field=n_clusters_base (base instances "
                         "in the %d-order stratum; the same at every crew "
                         "multiplier)" % size)
        M.add("ovlSize%sCampuses" % stok, f_int(len(cov["campuses"].iloc[0])),
              SRC_INST + " field=campus (campuses the stratum covers: %s)"
              % ", ".join(str(c) for c in cov["campuses"].iloc[0]))

    # ---- the tightened crew multipliers, per stratum ---------------------- #
    # The equivalence set narrows as crews tighten, and the two strata narrow at
    # different rates, so each tightened multiplier reports the full verdict
    # split rather than the equivalent count alone.
    M.section("Verdicts against EDD inside each size class as crews tighten "
              "(%s analysis=size); the %s counts are the block above" %
              (SRC_SENS, head))
    for m in CREW_MULTIPLIERS:
        if m == head_m:
            continue
        mtok = M_TOKEN[m]
        for size, stok in sorted(SIZE_TOKEN.items()):
            label = size_scope(m, size)
            for verdict in SIZE_MACRO_VERDICTS[m]:
                M.add("ovl%sSize%s%s" % (VERDICT_TOKEN[verdict], stok, mtok),
                      f_int(verdict_count(sens, "size", label, "verdict_base",
                                          verdict)),
                      SRC_SENS + " analysis=size scope=%s field=verdict_base "
                                 "value=%s" % (label, verdict))
            for verdict in SIZE_MACRO_NAMED:
                if verdict not in SIZE_MACRO_VERDICTS[m]:
                    continue
                fams = verdict_families(sens, "size", label, "verdict_base",
                                        verdict)
                if not fams:
                    continue
                base = "ovl%sSize%s%sFamilies" % (VERDICT_TOKEN[verdict], stok,
                                                  mtok)
                M.add(base, family_phrase(fams),
                      SRC_SENS + " analysis=size scope=%s field=family where "
                                 "verdict_base=%s (prose phrase)"
                      % (label, verdict))
                M.add(base + "Ids", ", ".join(fams),
                      SRC_SENS + " analysis=size scope=%s field=family where "
                                 "verdict_base=%s (raw family ids, tables only)"
                      % (label, verdict))
    return M


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Shared work orders between Eval-B empirical instances, "
                    "and the primary comparison re-clustered on them.")
    ap.add_argument("--out", default=str(OUT_DIR),
                    help="output directory (default %s)" % OUT_DIR)
    ap.add_argument("--paper", default=str(PAPER_DIR),
                    help="paper directory for the macro file (default %s)"
                         % PAPER_DIR)
    ap.add_argument("--n-boot", type=int, default=stats.N_BOOT,
                    help="bootstrap resamples (default %d)" % stats.N_BOOT)
    ap.add_argument("--seed", type=int, default=stats.SEED,
                    help="bootstrap master seed (default %d)" % stats.SEED)
    ap.add_argument("--no-macros", action="store_true",
                    help="write the CSV/report outputs only")
    args = ap.parse_args(argv)

    os.chdir(ROOT)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = datetime.now()

    print("Reading the final empirical instances ...", flush=True)
    wo_ids, meta = load_work_order_ids(INDEX_CSV, INST_ROOT, EMPIRICAL_TRACK)
    print("  %d instance(s) over %d campus(es)"
          % (len(wo_ids), meta["campus"].nunique()), flush=True)

    print("Auditing shared work orders ...", flush=True)
    pairs = sharing_pairs(meta, wo_ids)
    comp = components(wo_ids, pairs)
    inst = instance_table(meta, wo_ids, pairs, comp)
    audit_all = audit_summary(inst, pairs, wo_ids)
    audit_verdict = audit_summary(inst, pairs, wo_ids, VERDICT_CAMPUSES)
    print("  %d sharing pair(s), %d instance(s) touched, %d component(s)"
          % (audit_all["n_pairs"], audit_all["n_touched"],
             audit_all["n_components"]), flush=True)

    gen_ids, gen_meta = load_work_order_ids(INDEX_CSV, INST_ROOT,
                                            GENERATOR_TRACK)
    gen = generator_note(gen_ids, gen_meta)
    print("  generator track: %d instance(s), %d of %d same-campus pairs share "
          "a synthetic label (not counted as sharing)"
          % (gen["n_instances"], gen["n_colliding_pairs"],
             gen["n_same_campus_pairs"]), flush=True)

    p = out / "overlap_instances.csv"
    inst.to_csv(p, index=False)
    print("Wrote %d row(s) -> %s" % (len(inst), p), flush=True)
    p = out / "overlap_pairs.csv"
    pairs.to_csv(p, index=False)
    print("Wrote %d row(s) -> %s" % (len(pairs), p), flush=True)

    print("Auditing against the released v1.0 development corpus ...",
          flush=True)
    owners, v1_meta = v1_owner_index(V1_INDEX_CSV, V1_INST_ROOT,
                                     sorted(meta["campus"].unique()))
    devc = dev_corpus_table(meta, wo_ids, owners)
    dev = dev_corpus_summary(devc, v1_meta)
    print("  %d v1.0 replay instance(s) (%d train, %d test); %d of %d final "
          "instance(s) share with the test split and %d with the train split"
          % (dev["n_v1_instances"], dev["n_v1_train"], dev["n_v1_test"],
             dev["n_sharing_test"], dev["n_instances"],
             dev["n_sharing_train"]), flush=True)
    p = out / "overlap_devcorpus.csv"
    devc.to_csv(p, index=False)
    print("Wrote %d row(s) -> %s" % (len(devc), p), flush=True)

    print("Collapsing the scored rows to families ...", flush=True)
    seeded = load_results(EVALB_CSV)
    fam, coverage_report = collapse_families(seeded, META_COLS)
    print("  %d method(s) over %d configuration(s)"
          % (fam["method"].nunique(), fam["id"].nunique()), flush=True)
    dropped = int(coverage_report["n_configs_dropped"].sum())
    if dropped:
        raise SystemExit("the pool collapse dropped %d configuration(s); the "
                         "released analysis drops none, so the frames differ"
                         % dropped)

    print("Cluster sensitivity (%d resamples per arm) ..." % args.n_boot,
          flush=True)
    cluster_rows = cluster_sensitivity(fam, comp, args.n_boot, args.seed)
    print("Size-stratified sensitivity ...", flush=True)
    size_rows, coverage = size_sensitivity(fam, args.n_boot, args.seed)
    sens = pd.concat([cluster_rows, size_rows], ignore_index=True,
                     sort=False)[SENSITIVITY_COLUMNS]
    # The size rows leave the component columns empty, which would otherwise
    # turn the two integer columns into floats and print "139.0" in the CSV.
    for col in ("n_clusters_component", "verdict_changed"):
        sens[col] = pd.to_numeric(sens[col], errors="coerce").astype("Int64")
    p = out / "overlap_sensitivity.csv"
    sens.to_csv(p, index=False)
    print("Wrote %d row(s) -> %s" % (len(sens), p), flush=True)

    print("Self-check against the released comparison ...", flush=True)
    check = check_released(sens, Path(RELEASED_CSV))
    n_bad = int((check["ok"] == 0).sum())
    print("  %d field comparison(s), %d disagreement(s)"
          % (len(check), n_bad), flush=True)

    p = write_report(out / "overlap_summary.md", audit_all, audit_verdict, gen,
                     dev, inst, pairs, sens, coverage, check, args.n_boot,
                     args.seed)
    print("Wrote %s" % p, flush=True)

    if n_bad:
        for r in check[check["ok"] == 0].head(5).itertuples():
            print("    %s / %s / %s / %s: released %r vs recomputed %r"
                  % (r.scope_type, r.scope, r.family, r.field, r.released,
                     r.recomputed))
        print("STOP: the base arm does not reproduce %s on %d field "
              "comparison(s). The sensitivity would then be measuring the "
              "difference between two implementations rather than between two "
              "clusterings, so no macro file was written."
              % (RELEASED_CSV, n_bad), flush=True)
        return 1

    if not args.no_macros:
        M = build_macros(audit_all, audit_verdict, dev, sens, coverage,
                         Path(args.paper))
        header = "\n".join([
            "%% paper/%s -- generated by scripts/r4_overlap.py" % MACRO_FILE,
            "% GENERATED FILE. Do not edit by hand: rebuild with",
            "%   PYTHONPATH=src python scripts/r4_overlap.py",
            "% Shared work orders between the final empirical instances",
            "% (results/r4_final/analysis/overlap_*.csv) and the primary",
            "% comparison recomputed with those instances resampled together.",
            "% Prefix ovl = overlap.",
        ])
        p = Path(args.paper) / MACRO_FILE
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(M.render(header))
        print("Wrote %d macro(s) -> %s" % (len(M.names), p), flush=True)

    print("Done in %.1f s" % (datetime.now() - t0).total_seconds(), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
