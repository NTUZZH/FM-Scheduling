#!/usr/bin/env python
"""R4.6 preventive-visibility experiment runner (docs/protocol.md §R4 (design S5),
docs/protocol.md "Revision protocol R4", R4.6 and the dated R4 adjustments).

The question
------------
Preventive orders are the only work an FM organisation knows about in advance.
R4.6 asks what that advance knowledge is worth: every method is run at four
visibility levels L (business hours) at which a preventive order becomes KNOWN
before it is released,

    L = 0    the status quo (nothing is known early),
    L = 8    one shift,
    L = 40   one week,
    L = full the whole instance is known from bh 0,

with corrective orders never known early and a known order plannable but never
startable before its release (fmwos.env.known_bh is the single definition; the
validator's release check (c) polices the emitted schedule independently).

Cells
-----
generator : fmwos.generator.generate_window over a FIXED 80 bh window,
            pm_share_override in {0.2, 0.5, 0.8} x u_target in {0.7, 0.9, 1.1},
            campuses {5, 9, 10, 12}, 15 instances per cell, seeds
            90000 + cell_index * 1000 + i with
            cell_index = campus_idx * 9 + pm_idx * 3 + u_idx over the sorted
            campus / pm-share / utilization lists, and
            arrival_multiplier = u_target / generator.base_utilization(params)
            on the v1.1 packs refit for Eval-B (results/r4_final/gen_params/).
            Built ONCE into data/processed/instances_r4vis/ with its own
            index_r4vis.csv and reused verbatim on every rerun.
empirical : the Eval-B empirical (replay) instances of
            data/processed/instances_r4/index_r4.csv on the verdict campuses
            {5, 9, 10, 12}, at crew multipliers m in {1.0, 0.8, 0.6} via
            fmwos.tightness.scale_crew.  Campuses 1 and 2 are excluded here:
            they are Eval-B's transfer / nonstationary-calibration cells, not
            this experiment's.

Arms (per configuration, per level)
-----------------------------------
edd, atc, wmdd  : non-delay rules through fmwos.pdrs.dispatch.  They are
                  CONSTANT in L BY CONSTRUCTION -- a non-delay dispatcher picks
                  only from the released queue, which visibility never changes
                  (tests/test_r4_visibility.py (i) proves the schedules are
                  identical at every L).  Each is therefore run ONCE, at L = 0,
                  and its row is COPIED to the other three levels with
                  constant_by_construction = 1.  The copies necessarily share
                  the L = 0 row's wall_seconds, so those three wall_seconds
                  values are not independent timings and must never be read as
                  such; every metric column is exact.
atc_la          : the forecast-aware ATC baseline (fmwos.pdrs._pick_atc_la),
                  run through DispatchEnv(visibility_L=L).run_policy, which
                  hands it the trade's known-but-unreleased orders.  Runs once
                  per level; at L = 0 it reduces to atc(k=2) exactly.
rollcp2         : fmwos.rolling.roll_cpsat, budget 2.0 s, CP-SAT workers 2,
                  visibility_L=L.  EMPIRICAL CELLS ONLY, on the first
                  --rollcp-per-cell (8) configurations of every
                  (campus, size, m) cell in sorted-id order.  The dated R4
                  adjustment (docs/protocol.md, 2026-08-19) excludes the rolling
                  planner from the fixed-window generator cells, which draw
                  1,500-12,400 orders per instance; hypothesis H3 is evaluated
                  on the empirical cells.
vis<L>rl<seed>  : the R4.6 visibility policies,
                  results/p3_train/vis{0,8,40,full}/seed{501..505}/best.pt,
                  greedy argmax through
                  DispatchEnv(visibility_L=L, lookahead_features=True).  The arm
                  trained at level X runs ONLY at level X -- a policy is an arm,
                  not a knob, and its L is part of its identity.  These
                  checkpoints are produced AFTER this script is written; a
                  missing arm directory is reported and skipped, and a later
                  rerun adds exactly its rows (see Resumability).
v2rl301..310    : the frozen pre-visibility v2 MLP pool, greedy through the
                  DEFAULT DispatchEnv (visibility_L=0, no lookahead columns, so
                  F_CTX stays 10 and the checkpoints load unchanged), at L = 0
                  ONLY.  It is the reference point the visibility arms are read
                  against, not a visibility arm.

Identifier scheme (read this before touching the ids)
-----------------------------------------------------
Three different ids are in play and they are deliberately NOT the same string:

  instance id   the corpus id, e.g. c05_final_150_0003 (empirical) or
                c05_vis_050_090_0007 (generator).  Recorded as ``base_id`` on
                every row: it is the CLUSTER key for the paired statistics
                (protocol R4.5: one base instance = one resampling unit).
  shard id      the id of the transformed instance the methods actually run on
                = ``instance id`` for a generator cell or m = 1.0, and
                ``<instance id>_m<m>`` for a scaled empirical configuration,
                because fmwos.tightness.scale_crew suffixes meta.id itself.
                This IS instance["meta"]["id"], so every schedule emitted by
                pdrs.dispatch / DispatchEnv / roll_cpsat carries it as
                ``instance_id`` and validator check (f)
                (schedule.instance_id == instance.meta.id) is a real check
                rather than a formality.  One shard file per shard id.
  config id     the row's ``id`` column = ``<shard id>_L<tag>`` with tag in
                {0, 8, 40, full}.  It identifies ONE evaluated configuration
                (instance x crew multiplier x visibility level), which is what
                a paired analysis must pair on, since the same instance object
                is evaluated at four levels.

The level suffix lives on the CONFIG id and never on the instance's meta.id:
the same instance object is scored at four levels, so writing _L into meta.id
would either force four deep copies or break check (f).  Nothing downstream of
the validator needs the level to be inside meta.id, because the level is an
evaluation regime and not a property of the data (spec S1).

  CAVEAT for the analysis (report it, do not work around it here):
  fmwos.stats.BASE_ID_SUFFIX_RE strips _m/_sla/_q/_bd/... but does NOT know
  ``_L<tag>``, so scripts/r4_stats.py run on this file with the default
  --id-col id would cluster per (instance, m, L) and report intervals that are
  too narrow.  Every row therefore carries ``base_id`` explicitly; the R4.6
  analysis must cluster on it (r4_stats already cross-checks its derived
  cluster against a ``base_id`` column and reports the disagreement, which is
  exactly the alarm this scheme is meant to raise).

Output (results/r4_visibility/)
-------------------------------
  shards/<shard id>.json  one shard per instance configuration, holding EVERY
                          (method, level) row it has ever computed, keyed
                          "<method>@L<tag>" (atomic write);
  results.csv             the merged rows.  Columns are the
                          results/r4_final/results.csv columns in the same
                          order (which are results/p4_dyneval/results.csv plus
                          eval_set), then pm_share, visibility_L,
                          constant_by_construction and base_id -- so the p4 and
                          Eval-B column lists are both strict prefixes and any
                          existing analysis reads this file unchanged;
  meta.json               date, method list, cell counts, the arms that were
                          available this run, and git describe.

Resumability
------------
A shard is the UNION of every (method, level) row ever computed for its
configuration (the incremental semantics of scripts/p4_dyneval.py and
scripts/r4_final_eval.py).  A configuration is pending when its shard is
missing a currently-expected key, and a worker computes ONLY the missing keys.
Consequently the intended two-pass operation is safe by construction: run once
now (rules, atc_la, rollcp2, the v2 pool), train the visibility policies, then
run again -- the second pass computes the 20 policy rows per configuration and
rewrites each shard with old and new rows merged.  No row is ever duplicated
(rows are dict-keyed, and results.csv is rewritten wholesale from the shards)
and no row is ever discarded (the merge is old | new, and methods_expected is a
union).

Usage
-----
    PYTHONPATH=src python scripts/r4_visibility.py [--workers 10] [--limit N]
        [--skip-gen] [--skip-emp] [--rollcp-per-cell 8] [--no-rollcp]
        [--index CSV] [--vis-index CSV] [--out DIR]
        [--build-only] [--merge] [--project] [--smoke]

--smoke is a TINY wiring check and never touches the real corpus: it builds 2
generator instances over an 8 bh window (a few dozen orders) into
<out>/smoke/instances/, takes the first 2 empirical configurations at m = 1.0,
runs rules + atc_la at all four levels, prints every row and writes to
<out>/smoke/.
--build-only writes the generator corpus and exits (it is the expensive
non-evaluation step, so it can be scheduled into a quiet window on its own).
--project prints a runtime projection from the measured per-method wall clock
of results/p4_dyneval/results.csv.
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import os
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

# One thread per worker: the box is shared, a dispatch is far too small to
# parallelise internally, and a batch-1 policy forward is SLOWER on several
# threads (per-operator barriers dominate).  Set before numpy/torch are
# imported.  scripts/r4_final_eval.py uses 2 torch threads so its latencies stay
# comparable with results/p4_dyneval; this experiment's endpoint is weighted
# tardiness against L, not latency, so the wall_seconds column here is NOT
# directly comparable with that file's.
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

import multiprocessing as mp  # noqa: E402

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

# NOTE: torch / fmwos.policy are imported LAZILY inside the worker so the parent
# never initialises torch before fork() (fork-safety on the shared box).
from fmwos import generator, pdrs, rolling, tightness   # noqa: E402
from fmwos.env import DispatchEnv                       # noqa: E402
from fmwos.validator import validate                    # noqa: E402

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
INST_R4_ROOT = _ROOT / "data" / "processed" / "instances_r4"      # Eval-B
INDEX_R4_CSV = INST_R4_ROOT / "index_r4.csv"
INST_VIS_ROOT = _ROOT / "data" / "processed" / "instances_r4vis"  # R4.6 cells
INDEX_VIS_CSV = INST_VIS_ROOT / "index_r4vis.csv"
GEN_PARAMS_DIR = _ROOT / "results" / "r4_final" / "gen_params"    # v1.1 packs
TRAIN_DIR = _ROOT / "results" / "p3_train"
P4_RESULTS_CSV = _ROOT / "results" / "p4_dyneval" / "results.csv"  # yardstick

OUT_DIR = _ROOT / "results" / "r4_visibility"
SHARD_DIR = OUT_DIR / "shards"
OUT_CSV = OUT_DIR / "results.csv"
META_JSON = OUT_DIR / "meta.json"

# --------------------------------------------------------------------------- #
# Visibility levels (spec S1: the CSV carries the TAG, not the float)
# --------------------------------------------------------------------------- #
VIS_LEVELS = (("0", 0.0), ("8", 8.0), ("40", 40.0), ("full", None))
VIS_TAGS = [t for t, _ in VIS_LEVELS]
VIS_L_OF = {t: L for t, L in VIS_LEVELS}
_L_ORDER = {t: i for i, t in enumerate(VIS_TAGS)}
BASE_TAG = "0"                      # the level the constant rules are run at

# --------------------------------------------------------------------------- #
# Methods
# --------------------------------------------------------------------------- #
# Non-delay rules: constant in L by construction, run once at BASE_TAG.
CONST_RULES = ["edd", "atc", "wmdd"]
ATC_LA = "atc_la"                   # env-only forecast-aware ATC
ROLLCP_METHOD = "rollcp2"

VIS_TRAIN_TAGS = ["0", "8", "40", "full"]     # results/p3_train/vis<tag>/
VIS_SEEDS = [501, 502, 503, 504, 505]
V2_DIR = TRAIN_DIR / "v2"
V2_SEEDS = list(range(301, 311))
V2_TAG = "v2rl"

SEED = 301                  # PDR seed (only the 'random' rule would consume it)
ROLLCP_BUDGET_S = 2.0
CPSAT_WORKERS = 2           # spec-locked inside fmwos.rolling (documented here)
TORCH_THREADS = 1           # see the thread note at the top of this file
DEFAULT_WORKERS = 10
DEFAULT_ROLLCP_PER_CELL = 8
SMOKE_N_EMPIRICAL = 2
SMOKE_N_GEN = 2
SMOKE_WINDOW_BH = 8.0

# ACTIVE_* are rederived by _configure_methods() in the PARENT before the pool is
# forked, so every worker inherits the same expected-key set.
ACTIVE_RULES = list(CONST_RULES)
ACTIVE_ATC_LA = True
ACTIVE_VIS_ARMS = []        # [(method, ltag, ckpt_path, seed), ...]
ACTIVE_V2_SEEDS = list(V2_SEEDS)

# --------------------------------------------------------------------------- #
# Cells
# --------------------------------------------------------------------------- #
EVAL_SET = "visibility"
SMOKE_EVAL_SET = "visibility-smoke"

REGIME_EMPIRICAL = "vis-empirical"
REGIME_GEN = "vis-gen"
_REGIME_ORDER = {REGIME_EMPIRICAL: 0, REGIME_GEN: 1}

VERDICT_CAMPUSES = sorted([5, 9, 10, 12])
CREW_MULTS = [1.0, 0.8, 0.6]

GEN_CAMPUSES = sorted([5, 9, 10, 12])
GEN_PM_SHARES = sorted([0.2, 0.5, 0.8])
GEN_U_TARGETS = sorted([0.7, 0.9, 1.1])
GEN_WINDOW_BH = 80.0
GEN_PER_CELL = 15
GEN_SEED_BASE = 90000
GEN_SEED_CELL_STRIDE = 1000
GEN_ID_TAG = "vis"
SMOKE_ID_TAG = "vissmk"

VIS_INDEX_COLS = ["id", "campus", "track", "size_class", "split", "n_wos",
                  "window_start", "window_bh", "path", "eval_set", "u_realized",
                  "u_target", "pm_share", "arrival_multiplier", "seed"]

# results/r4_final/results.csv columns, in order (= the p4_dyneval columns plus
# eval_set), then the four R4.6 additions.  Both earlier lists stay a strict
# PREFIX so any existing analysis reads this file unchanged.
R4_FINAL_FIELDS = [
    "id", "campus", "track", "split", "size", "regime", "crew_multiplier",
    "arrival_multiplier", "pm_share_override", "method", "seed", "feasible",
    "wwt", "makespan", "mean_flow", "breach_share", "breach_p1", "breach_p2",
    "breach_p3", "breach_p4", "wall_seconds", "decisions",
    "mean_ms_per_decision", "mean_replan_s",
    "u_target", "u_realized", "eval_set",
]
FIELDS = R4_FINAL_FIELDS + ["pm_share", "visibility_L",
                            "constant_by_construction", "base_id"]


# --------------------------------------------------------------------------- #
# Ids (the scheme is documented in the module docstring; these are its only
# three producers, so a change here is a change everywhere)
# --------------------------------------------------------------------------- #
def shard_id_of(instance_id, m):
    """Id of the TRANSFORMED instance == instance["meta"]["id"] after scaling."""
    return instance_id if float(m) == 1.0 else "%s_m%s" % (instance_id, m)


def config_id_of(shard_id, ltag):
    """Row id: one evaluated configuration (instance x crew x visibility)."""
    return "%s_L%s" % (shard_id, ltag)


def row_key(method, ltag):
    """Shard row key: one (method, level) pair."""
    return "%s@L%s" % (method, ltag)


# --------------------------------------------------------------------------- #
# Reconfiguration (called in the parent, before the worker pool is forked)
# --------------------------------------------------------------------------- #
def vis_arm_specs(train_dir=TRAIN_DIR, tags=None, seeds=None):
    """Discovered visibility arms: [(method, ltag, ckpt_path, seed), ...].

    An arm exists only when its checkpoint file is on disk.  The arm trained at
    level X is listed at level X and nowhere else.
    """
    tags = VIS_TRAIN_TAGS if tags is None else tags
    seeds = VIS_SEEDS if seeds is None else seeds
    out = []
    for tag in tags:
        for s in seeds:
            ckpt = Path(train_dir) / ("vis%s" % tag) / ("seed%d" % s) / "best.pt"
            if ckpt.exists():
                out.append(("vis%srl%d" % (tag, s), tag, str(ckpt), int(s)))
    return out


def vis_arm_report(train_dir=TRAIN_DIR):
    """Per-level availability, for the log: {ltag: (n_found, n_expected, dir)}."""
    rep = {}
    for tag in VIS_TRAIN_TAGS:
        d = Path(train_dir) / ("vis%s" % tag)
        found = sum(1 for s in VIS_SEEDS
                    if (d / ("seed%d" % s) / "best.pt").exists())
        rep[tag] = (found, len(VIS_SEEDS), str(d))
    return rep


def v2_seeds_available(train_dir=V2_DIR, seeds=None):
    seeds = V2_SEEDS if seeds is None else seeds
    return [s for s in seeds
            if (Path(train_dir) / ("seed%d" % s) / "best.pt").exists()]


def _configure_methods(smoke=False):
    """Set the active arms and log what is missing.

    --smoke keeps only the transparent arms (rules + atc_la), which need no
    checkpoint and no solver, so the wiring is provable in seconds.
    """
    global ACTIVE_RULES, ACTIVE_ATC_LA, ACTIVE_VIS_ARMS, ACTIVE_V2_SEEDS
    ACTIVE_RULES = list(CONST_RULES)
    ACTIVE_ATC_LA = True
    if smoke:
        ACTIVE_VIS_ARMS, ACTIVE_V2_SEEDS = [], []
        return
    ACTIVE_VIS_ARMS = vis_arm_specs()
    ACTIVE_V2_SEEDS = v2_seeds_available()


def _configure_out(out_dir):
    """Point the results root (shards / results.csv / meta.json) at ``out_dir``."""
    global OUT_DIR, SHARD_DIR, OUT_CSV, META_JSON
    OUT_DIR = Path(out_dir)
    SHARD_DIR = OUT_DIR / "shards"
    OUT_CSV = OUT_DIR / "results.csv"
    META_JSON = OUT_DIR / "meta.json"


# --------------------------------------------------------------------------- #
# Generator corpus (built ONCE, reused verbatim)
# --------------------------------------------------------------------------- #
def _tag100(x):
    """Cell tag of a share / target: 0.2 -> '020', 1.1 -> '110'."""
    return "%03d" % int(round(float(x) * 100))


def _load_params(campus, params_dir=GEN_PARAMS_DIR):
    path = Path(params_dir) / ("params_c%d.json" % int(campus))
    if not path.exists():
        raise SystemExit(
            "generator params not found: %s\n"
            "  The R4.6 cells reuse the v1.1 packs Eval-B refit "
            "(docs/protocol.md §R4 (design S2)); build them with "
            "scripts/r4_final_instances.py first." % path)
    with open(path) as f:
        return json.load(f)


def _u_realized(instance):
    """Realized utilization sum p_bh / (n_tech * window_bh) of the instance."""
    total_p = sum(float(w["p_bh"]) for w in instance["work_orders"])
    n_tech = len(instance["technicians"])
    window_bh = float(instance["meta"]["window_bh"])
    denom = n_tech * window_bh
    return float(total_p / denom) if denom > 0 else None


def build_gen_corpus(inst_root=INST_VIS_ROOT, index_csv=INDEX_VIS_CSV,
                     campuses=None, pm_shares=None, u_targets=None,
                     per_cell=GEN_PER_CELL, window_bh=GEN_WINDOW_BH,
                     id_tag=GEN_ID_TAG, params_dir=GEN_PARAMS_DIR,
                     verbose=True):
    """Write (or reuse) the R4.6 generator cells and return their index rows.

    Deterministic in (params, window_bh, seed): an instance whose JSON is
    already on disk is NOT redrawn, so a rerun reuses byte-identical data, and
    the index is rewritten from the full cell list either way.  The cell index
    enumerates (campus, pm_share, u_target) over the SORTED lists, which is what
    fixes the seed block 90000 + cell_index * 1000 + i.
    """
    campuses = GEN_CAMPUSES if campuses is None else sorted(campuses)
    pm_shares = GEN_PM_SHARES if pm_shares is None else sorted(pm_shares)
    u_targets = GEN_U_TARGETS if u_targets is None else sorted(u_targets)
    inst_root = Path(inst_root)
    n_pm, n_u = len(pm_shares), len(u_targets)

    rows, n_new, n_reused = [], 0, 0
    for campus_idx, campus in enumerate(campuses):
        params = _load_params(campus, params_dir)
        u0 = generator.base_utilization(params)
        if verbose:
            print("  campus %2d: pack u0=%.4f (v1.1, %s)"
                  % (campus, u0, Path(params_dir).name), flush=True)
        for pm_idx, pm in enumerate(pm_shares):
            for u_idx, u_target in enumerate(u_targets):
                cell_index = campus_idx * (n_pm * n_u) + pm_idx * n_u + u_idx
                arrival_multiplier = float(u_target) / u0 if u0 > 0 else 1.0
                pm_tag, u_tag = _tag100(pm), _tag100(u_target)
                rel_dir = (Path("c%02d" % campus) / "storm2"
                           / ("pm%s_u%s" % (pm_tag, u_tag)))
                out_dir = inst_root / rel_dir
                out_dir.mkdir(parents=True, exist_ok=True)
                for i in range(per_cell):
                    seed = GEN_SEED_BASE + cell_index * GEN_SEED_CELL_STRIDE + i
                    inst_id = "c%02d_%s_%s_%s_%04d" % (campus, id_tag, pm_tag,
                                                       u_tag, i)
                    dst = out_dir / ("%s.json" % inst_id)
                    if dst.exists():
                        with open(dst) as f:
                            inst = json.load(f)
                        n_reused += 1
                    else:
                        inst = generator.generate_window(
                            params, window_bh=window_bh, seed=seed,
                            arrival_multiplier=arrival_multiplier,
                            pm_share_override=float(pm))
                        inst["meta"]["id"] = inst_id
                        inst["meta"]["split"] = "test"
                        inst["meta"]["eval_set"] = EVAL_SET
                        inst["meta"]["corpus"] = "v1.1"
                        inst["meta"]["u_target"] = float(u_target)
                        tmp = dst.with_suffix(".json.tmp")
                        with open(tmp, "w") as f:
                            json.dump(inst, f, separators=(",", ":"))
                        os.replace(tmp, dst)
                        n_new += 1
                    n_wos = len(inst["work_orders"])
                    rows.append({
                        "id": inst_id, "campus": campus, "track": "storm2",
                        "size_class": n_wos, "split": "test", "n_wos": n_wos,
                        "window_start": "synthetic",
                        "window_bh": round(float(window_bh), 4),
                        "path": str(rel_dir / ("%s.json" % inst_id)),
                        "eval_set": EVAL_SET,
                        "u_realized": round(_u_realized(inst) or 0.0, 6),
                        "u_target": float(u_target), "pm_share": float(pm),
                        "arrival_multiplier": round(arrival_multiplier, 6),
                        "seed": seed,
                    })
    index_csv = Path(index_csv)
    index_csv.parent.mkdir(parents=True, exist_ok=True)
    tmp = index_csv.with_suffix(index_csv.suffix + ".tmp")
    with open(tmp, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=VIS_INDEX_COLS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    os.replace(tmp, index_csv)
    if verbose:
        print("  generator corpus: %d instance(s) (%d drawn, %d reused) -> %s"
              % (len(rows), n_new, n_reused, index_csv), flush=True)
    return rows


# --------------------------------------------------------------------------- #
# Target-set construction
# --------------------------------------------------------------------------- #
def _read_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _instance_path(row, inst_root):
    p = row.get("path")
    if p:
        cand = Path(inst_root) / p
        if cand.exists():
            return cand
    return (Path(inst_root) / ("c%02d" % int(row["campus"]))
            / str(row.get("track", "replay")) / str(row["size_class"])
            / (row["id"] + ".json"))


def empirical_configs(index_csv=INDEX_R4_CSV, inst_root=None,
                      campuses=None, crew_mults=None, eval_set=EVAL_SET):
    """Eval-B empirical instances x crew multiplier, on the verdict campuses."""
    index_csv = Path(index_csv)
    inst_root = index_csv.parent if inst_root is None else Path(inst_root)
    if not index_csv.exists():
        raise SystemExit(
            "Eval-B index not found: %s\n"
            "  The R4.6 empirical cells ARE the Eval-B anchors "
            "(docs/protocol.md §R4 (design S5)); build them with "
            "scripts/r4_final_instances.py first." % index_csv)
    campuses = set(VERDICT_CAMPUSES if campuses is None else campuses)
    crew_mults = CREW_MULTS if crew_mults is None else crew_mults

    configs = []
    for r in _read_csv(index_csv):
        if str(r.get("track", "")).strip().lower() != "replay":
            continue
        try:
            campus, size = int(r["campus"]), int(r["size_class"])
        except (KeyError, TypeError, ValueError):
            continue
        if campus not in campuses:
            continue
        path = str(_instance_path(r, inst_root))
        for m in crew_mults:
            configs.append({
                "shard_id": shard_id_of(r["id"], m), "base_id": r["id"],
                "campus": campus, "track": str(r.get("track", "")).strip(),
                "split": str(r.get("split", "")).strip(), "size": size,
                "regime": REGIME_EMPIRICAL, "crew_multiplier": float(m),
                "arrival_multiplier": 1.0, "pm_share": None, "u_target": None,
                "kind": "empirical", "path": path, "m": float(m),
                "eval_set": eval_set,
            })
    if not configs:
        raise SystemExit("no empirical replay rows on campuses %s in %s"
                         % (sorted(campuses), index_csv))
    return configs


def generator_configs(index_csv=INDEX_VIS_CSV, inst_root=None,
                      eval_set=EVAL_SET):
    """The R4.6 fixed-window cells, as built (no crew scaling on top)."""
    index_csv = Path(index_csv)
    inst_root = index_csv.parent if inst_root is None else Path(inst_root)
    if not index_csv.exists():
        raise SystemExit(
            "R4.6 generator index not found: %s\n"
            "  Build it with `--build-only` (or let a full run build it); it is "
            "written once and reused." % index_csv)
    configs = []
    for r in _read_csv(index_csv):
        configs.append({
            "shard_id": r["id"], "base_id": r["id"], "campus": int(r["campus"]),
            "track": str(r.get("track", "storm2")).strip(),
            "split": str(r.get("split", "test")).strip(),
            "size": int(r["size_class"]), "regime": REGIME_GEN,
            "crew_multiplier": 1.0,
            "arrival_multiplier": float(r.get("arrival_multiplier") or 1.0),
            "pm_share": float(r["pm_share"]) if r.get("pm_share") else None,
            "u_target": float(r["u_target"]) if r.get("u_target") else None,
            "kind": "generator", "path": str(_instance_path(r, inst_root)),
            "m": 1.0, "eval_set": eval_set,
        })
    return configs


def sort_configs(configs):
    configs.sort(key=lambda c: (_REGIME_ORDER[c["regime"]], c["campus"],
                                c["size"], c["crew_multiplier"],
                                c["pm_share"] if c["pm_share"] is not None else -1.0,
                                c["u_target"] if c["u_target"] is not None else -1.0,
                                c["shard_id"]))
    return configs


def assign_rollcp(configs, per_cell, enabled):
    """Mark ``rollcp=True`` on the first ``per_cell`` EMPIRICAL configurations of
    every (campus, size, m) cell, in sorted-id order.

    The generator cells never run the rolling planner: the dated R4 adjustment
    (docs/protocol.md, 2026-08-19) excludes it from the fixed-window cells of
    both Eval-B and this experiment, and states that H3 is evaluated on the
    empirical cells instead.
    """
    cells = defaultdict(list)
    for c in configs:
        if c["regime"] == REGIME_GEN:
            c["rollcp"] = False        # scale boundary, protocol R4 adjustment
            continue
        cells[(c["campus"], c["size"], c["crew_multiplier"])].append(c)
    for group in cells.values():
        group.sort(key=lambda c: c["shard_id"])
        for j, c in enumerate(group):
            c["rollcp"] = bool(enabled and j < per_cell)
    return configs


def expected_keys(config):
    """The (method, level) keys a finished shard must hold for ``config``."""
    keys = []
    for rule in ACTIVE_RULES:
        keys.extend(row_key(rule, t) for t in VIS_TAGS)
    if ACTIVE_ATC_LA:
        keys.extend(row_key(ATC_LA, t) for t in VIS_TAGS)
    if config.get("rollcp"):
        keys.extend(row_key(ROLLCP_METHOD, t) for t in VIS_TAGS)
    for meth, ltag, _ckpt, _seed in ACTIVE_VIS_ARMS:
        keys.append(row_key(meth, ltag))
    for s in ACTIVE_V2_SEEDS:
        keys.append(row_key("%s%d" % (V2_TAG, s), BASE_TAG))
    return keys


# --------------------------------------------------------------------------- #
# Worker: policy cache + rollouts
# --------------------------------------------------------------------------- #
_POLICY_CACHE = {}


def _get_policy(ckpt):
    """Load (and cache per worker process) one checkpoint on CPU.

    ``DispatchPolicy.load`` reads f_job/f_ctx from the checkpoint's own config,
    so a visibility policy (F_CTX = 13) and the frozen v2 pool (F_CTX = 10) load
    through the same call.
    """
    pol = _POLICY_CACHE.get(ckpt)
    if pol is None:
        import torch  # lazy: only inside the worker
        from fmwos.policy import DispatchPolicy
        torch.set_num_threads(TORCH_THREADS)
        pol = DispatchPolicy.load(ckpt, map_location="cpu")
        pol.eval()
        _POLICY_CACHE[ckpt] = pol
    return pol


def _policy_rollout(instance, ckpt, method, seed, visibility_L, lookahead):
    """Greedy argmax episode through the DispatchEnv reset()/step() path."""
    pol = _get_policy(ckpt)
    env = DispatchEnv(instance, visibility_L=visibility_L,
                      lookahead_features=lookahead)
    obs = env.reset()
    done = False
    while not done:
        a, _, _, _ = pol.act(obs, greedy=True, device="cpu")
        obs, _r, done, _info = env.step(a)
    return env.to_schedule(method, seed=seed)


# --------------------------------------------------------------------------- #
# Row building
# --------------------------------------------------------------------------- #
def _row(config, method, ltag, seed, sched, res, constant=0):
    m = res["metrics"]
    pp = m["per_priority_breach_share"]
    decisions = sched.get("decisions")
    wall = sched.get("wall_seconds")
    mean_ms = None
    if decisions and wall is not None and decisions > 0:
        mean_ms = 1000.0 * float(wall) / float(decisions)
    return {
        "id": config_id_of(config["shard_id"], ltag),
        "campus": config["campus"], "track": config["track"],
        "split": config["split"], "size": config["size"],
        "regime": config["regime"],
        "crew_multiplier": config["crew_multiplier"],
        "arrival_multiplier": config["arrival_multiplier"],
        "pm_share_override": config.get("pm_share"),
        "method": method, "seed": seed,
        "feasible": int(bool(res["feasible"])),
        "wwt": m["WWT"], "makespan": m["makespan"], "mean_flow": m["mean_flow"],
        "breach_share": m["breach_share"],
        "breach_p1": pp.get(1), "breach_p2": pp.get(2),
        "breach_p3": pp.get(3), "breach_p4": pp.get(4),
        "wall_seconds": wall, "decisions": decisions,
        "mean_ms_per_decision": mean_ms,
        "mean_replan_s": sched.get("mean_replan_s"),
        "u_target": config.get("u_target"),
        "u_realized": config.get("u_realized"),
        "eval_set": config.get("eval_set"),
        "pm_share": config.get("pm_share"),
        "visibility_L": ltag,
        "constant_by_construction": int(constant),
        "base_id": config["base_id"],
    }


def run_config_methods(instance, config, todo):
    """Run every arm in ``todo`` on ONE transformed instance object.

    ``todo`` is a set of "<method>@L<tag>" keys.  Both the schedule and the
    validation are produced against the instance handed in, which is what makes
    validator check (f) (schedule.instance_id == instance.meta.id) a real check:
    the level lives on the CONFIG id only, and never on meta.id.

    Returns ``(rows, infeasible)`` keyed the same way as ``todo``.
    """
    rows, infeasible = {}, []

    def record(method, ltag, seed, sched, res, constant=0):
        key = row_key(method, ltag)
        rows[key] = _row(config, method, ltag, seed, sched, res, constant)
        if not res["feasible"]:
            infeasible.append({"method": method, "visibility_L": ltag,
                               "violations": res["violations"][:3]})

    # Non-delay rules: computed ONCE at L=0 and copied to every level, because a
    # non-delay dispatcher picks from the released queue only and visibility
    # cannot change it (tests/test_r4_visibility.py (i)).  The copies share the
    # measured row's wall_seconds; that is documented in the module docstring
    # and flagged in the data by constant_by_construction = 1.
    for rule in ACTIVE_RULES:
        wanted = [t for t in VIS_TAGS if row_key(rule, t) in todo]
        if not wanted:
            continue
        sched = pdrs.dispatch(instance, rule, seed=SEED)
        res = validate(instance, sched)
        for t in wanted:
            record(rule, t, SEED, sched, res, constant=1)

    # Forecast-aware ATC: env-only (it reads the trade's known orders).
    if ACTIVE_ATC_LA:
        pick = pdrs.get_rule(ATC_LA)
        for t in VIS_TAGS:
            if row_key(ATC_LA, t) not in todo:
                continue
            env = DispatchEnv(instance, visibility_L=VIS_L_OF[t])
            sched = env.run_policy(pick, method=ATC_LA, seed=SEED)
            record(ATC_LA, t, SEED, sched, validate(instance, sched))

    # Rolling CP-SAT: empirical cells only, one run per level.
    if config.get("rollcp"):
        for t in VIS_TAGS:
            if row_key(ROLLCP_METHOD, t) not in todo:
                continue
            sched = rolling.roll_cpsat(instance, budget_s=ROLLCP_BUDGET_S,
                                       visibility_L=VIS_L_OF[t])
            record(ROLLCP_METHOD, t, 0, sched, validate(instance, sched))

    # Visibility policies: each arm at its OWN level, widened observation.
    for meth, ltag, ckpt, seed in ACTIVE_VIS_ARMS:
        if row_key(meth, ltag) not in todo:
            continue
        sched = _policy_rollout(instance, ckpt, meth, seed,
                                visibility_L=VIS_L_OF[ltag], lookahead=True)
        record(meth, ltag, seed, sched, validate(instance, sched))

    # Frozen pre-visibility v2 pool: the reference point, at L = 0 only, through
    # the DEFAULT env (F_CTX stays 10, so the checkpoints load unchanged).
    for s in ACTIVE_V2_SEEDS:
        meth = "%s%d" % (V2_TAG, s)
        if row_key(meth, BASE_TAG) not in todo:
            continue
        ckpt = str(V2_DIR / ("seed%d" % s) / "best.pt")
        sched = _policy_rollout(instance, ckpt, meth, s,
                                visibility_L=VIS_L_OF[BASE_TAG], lookahead=False)
        record(meth, BASE_TAG, s, sched, validate(instance, sched))

    return rows, infeasible


def _write_shard(shard_id, shard):
    dst = SHARD_DIR / (shard_id + ".json")
    tmp = SHARD_DIR / (shard_id + ".json.tmp")
    with open(tmp, "w") as f:
        json.dump(shard, f)
    os.replace(tmp, dst)


def _run_one(config):
    """One instance configuration x every arm x every level (worker process)."""
    t0 = time.perf_counter()
    try:
        # INCREMENTAL semantics: a shard is the union of every (method, level)
        # row ever computed for this configuration, so a resumed or widened run
        # computes only what is missing and never discards earlier rows.
        dst = SHARD_DIR / (config["shard_id"] + ".json")
        old_rows, old_expected = {}, []
        if dst.exists():
            try:
                with open(dst) as f:
                    _old = json.load(f)
                old_rows = _old.get("rows", {}) or {}
                old_expected = list(_old.get("methods_expected", []) or [])
            except Exception:  # noqa: BLE001 -- a corrupt shard is simply redone
                old_rows, old_expected = {}, []

        with open(config["path"]) as f:
            instance = json.load(f)
        if config["kind"] == "empirical" and config["m"] != 1.0:
            instance = tightness.scale_crew(instance, config["m"])
        if instance["meta"]["id"] != config["shard_id"]:
            raise ValueError(
                "shard id %r does not match the transformed instance's meta.id "
                "%r -- the id scheme is broken"
                % (config["shard_id"], instance["meta"]["id"]))

        # The two provenance numbers that can only be read off the materialised
        # instance are filled here and picked up by _row().
        config = dict(config)
        config["u_realized"] = _u_realized(instance)
        if config.get("u_target") is None:
            u_t = instance.get("meta", {}).get("u_target")
            config["u_target"] = float(u_t) if u_t is not None else None

        expected = expected_keys(config)
        todo = {k for k in expected if k not in old_rows}
        new_rows, infeasible = run_config_methods(instance, config, todo)

        out_rows = {**old_rows, **new_rows}
        assert set(expected).issubset(out_rows), "internal: key set mismatch"
        shard = {
            "shard_id": config["shard_id"], "base_id": config["base_id"],
            "campus": config["campus"], "regime": config["regime"],
            "size": config["size"],
            "crew_multiplier": config["crew_multiplier"],
            "pm_share": config["pm_share"], "u_target": config["u_target"],
            "u_realized": config["u_realized"], "eval_set": config["eval_set"],
            "rows": out_rows,
            "methods_expected": sorted(set(expected) | set(old_expected)),
            "infeasible": infeasible,
            "wall_seconds_total": time.perf_counter() - t0,
        }
        _write_shard(config["shard_id"], shard)
        return {"id": config["shard_id"], "regime": config["regime"], "ok": True,
                "rows": new_rows, "infeasible": infeasible,
                "wall": shard["wall_seconds_total"]}
    except Exception as e:  # noqa: BLE001 -- report, never kill the pool
        import traceback
        return {"id": config["shard_id"], "regime": config["regime"],
                "ok": False, "rows": {}, "infeasible": [],
                "error": "%s: %s" % (type(e).__name__, e),
                "traceback": traceback.format_exc(),
                "wall": time.perf_counter() - t0}


# --------------------------------------------------------------------------- #
# Resumability + merge
# --------------------------------------------------------------------------- #
def _shard_keys():
    """Map shard id -> the set of row keys it holds (corrupt -> absent)."""
    have = {}
    if not SHARD_DIR.exists():
        return have
    for p in SHARD_DIR.glob("*.json"):
        try:
            with open(p) as f:
                d = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        rows = d.get("rows", {})
        if isinstance(rows, dict):
            have[d.get("shard_id", p.stem)] = set(rows)
    return have


_METHOD_ORDER = None


def _method_rank(method):
    """Stable method order for the merged CSV (built once, then cached).

    The visibility arms are enumerated from the FULL nominal arm list rather
    than from what is on disk, so a file merged before training and one merged
    after it order their rows identically.
    """
    global _METHOD_ORDER
    if _METHOD_ORDER is None:
        names = (list(CONST_RULES) + [ATC_LA, ROLLCP_METHOD]
                 + ["vis%srl%d" % (t, s)
                    for t in VIS_TRAIN_TAGS for s in VIS_SEEDS]
                 + ["%s%d" % (V2_TAG, s) for s in V2_SEEDS])
        _METHOD_ORDER = {m: i for i, m in enumerate(names)}
    return _METHOD_ORDER.get(method, len(_METHOD_ORDER))


def _merge(verbose=True):
    all_rows = []
    n_finished = n_partial = n_infeasible = 0
    for p in sorted(SHARD_DIR.glob("*.json")) if SHARD_DIR.exists() else []:
        try:
            with open(p) as f:
                d = json.load(f)
        except (OSError, json.JSONDecodeError):
            n_partial += 1
            continue
        rows = d.get("rows", {})
        expected = d.get("methods_expected", [])
        if not (isinstance(rows, dict) and set(rows) >= set(expected)):
            n_partial += 1
            continue
        n_finished += 1
        for key in sorted(rows):
            r = rows[key]
            all_rows.append(r)
            if not r.get("feasible"):
                n_infeasible += 1

    all_rows.sort(key=lambda r: (
        _REGIME_ORDER.get(r["regime"], 99), r["campus"], r["size"],
        r["crew_multiplier"],
        r["pm_share"] if r.get("pm_share") is not None else -1.0,
        r["u_target"] if r.get("u_target") is not None else -1.0,
        r["base_id"], _L_ORDER.get(str(r["visibility_L"]), 99),
        _method_rank(r["method"])))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tmp = OUT_CSV.with_suffix(OUT_CSV.suffix + ".tmp")
    with open(tmp, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in all_rows:
            w.writerow({c: r.get(c) for c in FIELDS})
    os.replace(tmp, OUT_CSV)
    if verbose:
        print("Merged %d finished configuration(s) -> %d rows -> %s"
              % (n_finished, len(all_rows), OUT_CSV))
        if n_partial:
            print("  (%d partial/corrupt shard(s) skipped)" % n_partial)
        print("  infeasible rows: %d" % n_infeasible)
    return {"n_finished": n_finished, "n_rows": len(all_rows),
            "n_infeasible": n_infeasible, "n_partial": n_partial}


def _git_describe():
    try:
        return subprocess.check_output(
            ["git", "describe", "--tags", "--always", "--dirty"],
            cwd=str(_ROOT), stderr=subprocess.DEVNULL).decode().strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def _fmt_hms(seconds):
    seconds = int(max(0, seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return "%dh%02dm%02ds" % (h, m, s)


# --------------------------------------------------------------------------- #
# Runtime projection (yardstick: the measured v1.0 dynamic evaluation)
# --------------------------------------------------------------------------- #
# Cost fallbacks when the yardstick CSV has no row for a method: wmdd is the
# other due-date rule with a per-candidate score (cost it as atc); atc_la is atc
# through the env driver (same arithmetic, plus the generator hand-off, so this
# is a floor); a visibility policy is the v2 MLP at the same seed offset (same
# architecture, three extra context columns).
_PROJ_FALLBACK = {"wmdd": "atc", ATC_LA: "atc"}


def _yardstick(csv_path=P4_RESULTS_CSV):
    """Mean per-schedule wall seconds per method, per family.

    results/p4_dyneval/results.csv is the only measurement of these methods on
    this box: its replay regimes are the yardstick for the empirical cells and
    its storm2 regime for the generator cells (the same generate_window draw
    over the same 80 bh window, so a comparable work-order count).
    """
    fam = {"empirical": defaultdict(list), "generator": defaultdict(list)}
    if not Path(csv_path).exists():
        return {k: {} for k in fam}
    with open(csv_path, newline="") as f:
        for r in csv.DictReader(f):
            regime = r.get("regime", "")
            if regime.startswith("replay"):
                key = "empirical"
            elif regime == "storm2":
                key = "generator"
            else:
                continue
            try:
                fam[key][r["method"]].append(float(r["wall_seconds"]))
            except (KeyError, TypeError, ValueError):
                continue
    return {k: {m: sum(v) / len(v) for m, v in d.items() if v}
            for k, d in fam.items()}


def _method_cost(means, method):
    if method in means:
        return means[method]
    alt = _PROJ_FALLBACK.get(method)
    if alt and alt in means:
        return means[alt]
    if method.startswith("vis"):        # visibility policy -> its v2 twin
        pool = [v for m, v in means.items() if m.startswith(V2_TAG)]
        if pool:
            return sum(pool) / len(pool)
    return None


def _runtime_projection(configs=None, workers=DEFAULT_WORKERS,
                        rollcp_per_cell=DEFAULT_ROLLCP_PER_CELL):
    """Print a projected wall clock for the full R4.6 run.

    Costs are the measured per-schedule means of results/p4_dyneval/results.csv.
    When the target sets are not built yet the counts fall back to the nominal
    design of docs/protocol.md §R4 (design S5).
    """
    means = _yardstick()
    n_vis_arms = len(ACTIVE_VIS_ARMS)
    n_v2 = len(ACTIVE_V2_SEEDS)
    if configs:
        n_emp = sum(1 for c in configs if c["regime"] == REGIME_EMPIRICAL)
        n_gen = sum(1 for c in configs if c["regime"] == REGIME_GEN)
        n_roll = sum(1 for c in configs if c.get("rollcp"))
        src = "built target sets"
    else:
        n_emp = None
        n_gen = (len(GEN_CAMPUSES) * len(GEN_PM_SHARES) * len(GEN_U_TARGETS)
                 * GEN_PER_CELL)
        n_roll = None
        src = "nominal design (docs/protocol.md §R4 (design S5))"
        if INDEX_R4_CSV.exists():
            emp = [r for r in _read_csv(INDEX_R4_CSV)
                   if str(r.get("track", "")).strip().lower() == "replay"
                   and int(r["campus"]) in VERDICT_CAMPUSES]
            n_emp = len(emp) * len(CREW_MULTS)
            cells = {(int(r["campus"]), int(r["size_class"]), m)
                     for r in emp for m in CREW_MULTS}
            n_roll = len(cells) * rollcp_per_cell
            src = "index_r4.csv (empirical) + nominal design (generator)"
        else:
            n_emp, n_roll = 0, 0

    print("Runtime projection for the full R4.6 visibility run")
    print("  configurations  : %d empirical + %d generator = %d  [%s]"
          % (n_emp, n_gen, n_emp + n_gen, src))
    print("  arms/config     : %d rules (run once, copied to 4 levels) + "
          "atc_la x4 + %d visibility policies + %d v2 policies at L=0"
          % (len(ACTIVE_RULES), n_vis_arms, n_v2))
    print("  rollcp2         : %d empirical config(s) x 4 levels "
          "(generator cells excluded, protocol R4 adjustment)" % n_roll)
    print("  yardstick       : %s (replay -> empirical, storm2 -> generator)"
          % P4_RESULTS_CSV)

    total = 0.0
    for family, n_cfg, n_r in (("empirical", n_emp, n_roll),
                               ("generator", n_gen, 0)):
        mm = means.get(family, {})
        per_cfg, missing = 0.0, []
        # (method, how many times it runs per configuration)
        arms = [(r, 1) for r in ACTIVE_RULES]          # once, copied to 4 levels
        arms.append((ATC_LA, len(VIS_TAGS)))           # once per level
        arms += [(m, 1) for m, _t, _c, _s in ACTIVE_VIS_ARMS]   # at its own L
        arms += [("%s%d" % (V2_TAG, s), 1) for s in ACTIVE_V2_SEEDS]  # L=0 only
        for method, n_runs in arms:
            cost = _method_cost(mm, method)
            if cost is None:
                missing.append(method)
                continue
            per_cfg += cost * n_runs
        roll = _method_cost(mm, ROLLCP_METHOD)
        base_s = per_cfg * n_cfg
        roll_s = (roll * n_r * len(VIS_TAGS)) if (roll and n_r) else 0.0
        total += base_s + roll_s
        print("  %-9s : %8.2f core-s/config x %d = %s%s"
              % (family, per_cfg, n_cfg, _fmt_hms(base_s),
                 ("  (no yardstick for %s)" % ",".join(missing)) if missing
                 else ""))
        if n_r:
            print("  %-9s   rollcp2 %.1f core-s x %d config(s) x %d level(s) "
                  "= %s" % ("", roll or 0.0, n_r, len(VIS_TAGS),
                            _fmt_hms(roll_s)))
    print("  TOTAL           : %s core-time  ->  ~%s wall at %d workers"
          % (_fmt_hms(total), _fmt_hms(total / max(1, workers)), workers))
    if not ACTIVE_VIS_ARMS:
        print("  NOTE: no visibility checkpoint exists yet, so this is PASS 1 "
              "only. Pass 2 (20 policy rollouts per configuration, after "
              "training) costs roughly 2x the per-config policy term above.")
    print("  (projection only: rollcp2 at L > 0 replans on every newly known "
          "preventive order and carries a larger snapshot, so its true cost is "
          "between 1x and 2x the L=0 yardstick and is the least certain term.)")
    return total


# --------------------------------------------------------------------------- #
# Smoke printing
# --------------------------------------------------------------------------- #
_SMOKE_COLS = ["id", "campus", "size", "crew_multiplier", "pm_share",
               "visibility_L", "method", "constant_by_construction", "feasible",
               "wwt", "makespan", "breach_share", "wall_seconds", "decisions",
               "u_realized", "eval_set"]


def _print_smoke_rows(rows):
    """Print every smoke row as an aligned table (correctness is read by eye)."""
    def cell(v):
        if v is None:
            return "-"
        if isinstance(v, float):
            return "%.6g" % v
        return str(v)

    table = [[cell(r.get(c)) for c in _SMOKE_COLS] for r in rows]
    widths = [max(len(_SMOKE_COLS[i]), *(len(t[i]) for t in table))
              if table else len(_SMOKE_COLS[i]) for i in range(len(_SMOKE_COLS))]
    line = "  ".join(c.ljust(widths[i]) for i, c in enumerate(_SMOKE_COLS))
    print(line)
    print("-" * len(line))
    for t in table:
        print("  ".join(t[i].ljust(widths[i]) for i in range(len(_SMOKE_COLS))))


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="R4.6 preventive-visibility experiment runner.")
    ap.add_argument("--workers", type=int, default=DEFAULT_WORKERS,
                    help="parallel configuration workers (default %d)"
                         % DEFAULT_WORKERS)
    ap.add_argument("--limit", type=int, default=None,
                    help="cap not-yet-done configurations processed this run")
    ap.add_argument("--skip-gen", action="store_true",
                    help="skip the fixed-window generator cells")
    ap.add_argument("--skip-emp", action="store_true",
                    help="skip the Eval-B empirical cells")
    ap.add_argument("--rollcp-per-cell", type=int,
                    default=DEFAULT_ROLLCP_PER_CELL,
                    help="rollcp2 subsample per (campus, size, m) cell "
                         "(default %d)" % DEFAULT_ROLLCP_PER_CELL)
    ap.add_argument("--no-rollcp", action="store_true",
                    help="skip the rolling planner entirely")
    ap.add_argument("--index", default=str(INDEX_R4_CSV),
                    help="Eval-B index for the empirical cells")
    ap.add_argument("--vis-index", default=str(INDEX_VIS_CSV),
                    help="R4.6 generator index (built here if absent)")
    ap.add_argument("--out", default=str(OUT_DIR),
                    help="results root (default results/r4_visibility)")
    ap.add_argument("--build-only", action="store_true",
                    help="build/refresh the generator corpus and exit")
    ap.add_argument("--merge", action="store_true",
                    help="only (re)build results.csv from existing shards")
    ap.add_argument("--project", action="store_true",
                    help="print the runtime projection and exit")
    ap.add_argument("--smoke", action="store_true",
                    help="TINY wiring check: 2 generator instances over an "
                         "8 bh window + 2 empirical configs, rules + atc_la at "
                         "all four levels, into <out>/smoke/")
    args = ap.parse_args(argv)

    # Reconfigure BEFORE any directory is made or any worker is forked, so the
    # forked workers inherit the active arm set and the results root.
    _configure_methods(smoke=args.smoke)
    out_root = Path(args.out) / "smoke" if args.smoke else Path(args.out)
    _configure_out(out_root)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SHARD_DIR.mkdir(parents=True, exist_ok=True)

    if args.merge:
        _merge(verbose=True)
        return

    if args.project:
        # Exact counts once the corpus exists (index CSVs only, no instance is
        # opened); the nominal design of spec S5 before that.
        proj = None
        vi = Path(args.vis_index)
        if vi.exists():
            proj = sort_configs(generator_configs(vi, vi.parent, EVAL_SET)
                                + empirical_configs(Path(args.index)))
            assign_rollcp(proj, args.rollcp_per_cell, not args.no_rollcp)
        _runtime_projection(proj, workers=args.workers,
                            rollcp_per_cell=args.rollcp_per_cell)
        return

    eval_set = SMOKE_EVAL_SET if args.smoke else EVAL_SET
    vis_index = Path(args.vis_index)
    vis_root = vis_index.parent
    if args.smoke:
        vis_root = OUT_DIR / "instances"
        vis_index = vis_root / "index_r4vis_smoke.csv"

    # ---- generator corpus (built once, reused) ---------------------------- #
    configs = []
    if not args.skip_gen:
        if args.smoke:
            print("Building the SMOKE generator cell (window %.0f bh, %d "
                  "instances)" % (SMOKE_WINDOW_BH, SMOKE_N_GEN))
            build_gen_corpus(inst_root=vis_root, index_csv=vis_index,
                             campuses=[GEN_CAMPUSES[0]],
                             pm_shares=[GEN_PM_SHARES[1]],
                             u_targets=[GEN_U_TARGETS[1]],
                             per_cell=SMOKE_N_GEN, window_bh=SMOKE_WINDOW_BH,
                             id_tag=SMOKE_ID_TAG)
        elif not vis_index.exists():
            print("Building the R4.6 generator corpus (%d cells x %d = %d "
                  "instances)" % (len(GEN_CAMPUSES) * len(GEN_PM_SHARES)
                                  * len(GEN_U_TARGETS), GEN_PER_CELL,
                                  len(GEN_CAMPUSES) * len(GEN_PM_SHARES)
                                  * len(GEN_U_TARGETS) * GEN_PER_CELL))
            build_gen_corpus(inst_root=vis_root, index_csv=vis_index)
        configs += generator_configs(vis_index, vis_root, eval_set)

    if args.build_only:
        print("--build-only: corpus written, nothing evaluated.")
        return

    # ---- empirical cells --------------------------------------------------- #
    if not args.skip_emp:
        emp = empirical_configs(Path(args.index), eval_set=eval_set)
        if args.smoke:
            emp = [c for c in emp if c["m"] == 1.0]
            emp.sort(key=lambda c: (c["campus"], c["size"], c["shard_id"]))
            emp = emp[:SMOKE_N_EMPIRICAL]
        configs += emp

    if not configs:
        sys.exit("no configurations selected (--skip-gen and --skip-emp?)")

    sort_configs(configs)
    configs = assign_rollcp(configs, args.rollcp_per_cell,
                            not args.no_rollcp and not args.smoke)
    n_rollcp = sum(1 for c in configs if c.get("rollcp"))

    have = _shard_keys()
    pending = [c for c in configs
               if not (have.get(c["shard_id"], set()) >= set(expected_keys(c)))]
    n_pending_all = len(pending)
    if args.limit is not None:
        pending = pending[:args.limit]

    by_regime = defaultdict(int)
    for c in configs:
        by_regime[c["regime"]] += 1

    print("R4.6 preventive-visibility experiment%s"
          % ("  (SMOKE SUBSET)" if args.smoke else ""))
    if args.smoke:
        print("  SMOKE -- NOT an R4.6 result: rules + atc_la only, into %s"
              % OUT_DIR)
    print("  levels          : %s" % ", ".join("L=%s" % t for t in VIS_TAGS))
    print("  eval_set        : %s" % eval_set)
    print("  out root        : %s" % OUT_DIR)
    print("  configs total   : %d  %s" % (len(configs), dict(by_regime)))
    print("  rollcp2 subset  : %d config(s) x %d level(s) (per_cell=%d%s)"
          % (n_rollcp, len(VIS_TAGS), args.rollcp_per_cell,
             ", DISABLED" if (args.no_rollcp or args.smoke) else ""))
    print("  constant rules  : %s (run once at L=%s, copied to every level)"
          % (", ".join(ACTIVE_RULES), BASE_TAG))
    if args.smoke:
        print("  policies        : none (smoke)")
    else:
        rep = vis_arm_report()
        for tag in VIS_TRAIN_TAGS:
            found, want, d = rep[tag]
            if found == want:
                print("  vis policies    : L=%-4s %d/%d checkpoints  %s"
                      % (tag, found, want, d))
            else:
                print("  vis policies    : L=%-4s %d/%d checkpoints MISSING -- "
                      "arm SKIPPED this run (%s); rerun after training adds "
                      "only its rows" % (tag, found, want, d))
        print("  v2 pool (L=0)   : %d checkpoint(s) %s"
              % (len(ACTIVE_V2_SEEDS), V2_DIR))
    print("  already finished: %d  ->  pending this run: %d"
          % (len(configs) - n_pending_all, len(pending)))
    print("  workers=%d  cpsat_workers=%d  torch_threads=%d  pdr_seed=%d  "
          "rollcp_budget=%.1fs" % (args.workers, CPSAT_WORKERS, TORCH_THREADS,
                                   SEED, ROLLCP_BUDGET_S), flush=True)

    smoke_rows = []
    if not pending:
        print("Nothing pending -- merging existing shards.")
        merged = _merge(verbose=True)
        elapsed, completed, n_errors = 0.0, 0, 0
        start_iso = end_iso = _dt.datetime.now().isoformat(timespec="seconds")
    else:
        start_iso = _dt.datetime.now().isoformat(timespec="seconds")
        t_start = time.perf_counter()
        n_infeasible = n_errors = completed = 0
        total = len(pending)
        ctx = mp.get_context("fork")
        with ctx.Pool(processes=args.workers) as pool:
            for res in pool.imap_unordered(_run_one, pending):
                completed += 1
                if not res.get("ok"):
                    n_errors += 1
                    print("[ERROR] %s (%s): %s"
                          % (res["id"], res["regime"], res.get("error")))
                    if args.smoke:
                        print(res.get("traceback", ""))
                else:
                    if args.smoke:
                        smoke_rows.extend(res["rows"].values())
                    for it in res.get("infeasible", []):
                        n_infeasible += 1
                        print("[INFEASIBLE] id=%s method=%s L=%s :: %s"
                              % (res["id"], it["method"], it["visibility_L"],
                                 " | ".join(it.get("violations", []))))
                if completed % 25 == 0 or completed == total:
                    elapsed = time.perf_counter() - t_start
                    eta = elapsed / completed * (total - completed)
                    print("  progress %d/%d  elapsed %s  eta %s  "
                          "(%d infeasible, %d errors)"
                          % (completed, total, _fmt_hms(elapsed), _fmt_hms(eta),
                             n_infeasible, n_errors), flush=True)

        elapsed = time.perf_counter() - t_start
        end_iso = _dt.datetime.now().isoformat(timespec="seconds")
        print("Run complete: %d config(s) in %s (%d infeasible, %d errors)."
              % (completed, _fmt_hms(elapsed), n_infeasible, n_errors))
        merged = _merge(verbose=True)

    if args.smoke and smoke_rows:
        smoke_rows.sort(key=lambda r: (r["base_id"], r["crew_multiplier"],
                                       _L_ORDER.get(str(r["visibility_L"]), 99),
                                       _method_rank(r["method"])))
        print("")
        _print_smoke_rows(smoke_rows)
        print("")

    meta = {
        "experiment": "r4_visibility",
        "protocol": "docs/protocol.md R4.6 (+ the 2026-08-19 R4 adjustment) / "
                    "docs/protocol.md §R4 (design S5)",
        "date": _dt.date.today().isoformat(),
        "start_time": start_iso, "end_time": end_iso,
        "elapsed_seconds": round(elapsed, 3), "workers": args.workers,
        "smoke": bool(args.smoke), "eval_set": eval_set,
        "out_dir": str(OUT_DIR),
        "index_csv": str(args.index), "vis_index_csv": str(vis_index),
        "visibility_levels": [{"tag": t, "L_bh": L} for t, L in VIS_LEVELS],
        "constant_rules": list(ACTIVE_RULES),
        "constant_rules_run_at": BASE_TAG,
        "atc_la": bool(ACTIVE_ATC_LA),
        "vis_arms": [{"method": m, "visibility_L": t, "ckpt": c, "seed": s}
                     for m, t, c, s in ACTIVE_VIS_ARMS],
        "vis_arms_missing": {t: v[1] - v[0] for t, v in
                             vis_arm_report().items()},
        "v2_pool_seeds": list(ACTIVE_V2_SEEDS),
        "pdr_seed": SEED, "rollcp_budget_s": ROLLCP_BUDGET_S,
        "cpsat_workers": CPSAT_WORKERS, "torch_threads": TORCH_THREADS,
        "rollcp_per_cell": args.rollcp_per_cell,
        "no_rollcp": bool(args.no_rollcp), "n_rollcp_configs": n_rollcp,
        "crew_multipliers": CREW_MULTS,
        "verdict_campuses": VERDICT_CAMPUSES,
        "generator_cells": {"campuses": GEN_CAMPUSES,
                            "pm_shares": GEN_PM_SHARES,
                            "u_targets": GEN_U_TARGETS,
                            "window_bh": GEN_WINDOW_BH,
                            "per_cell": GEN_PER_CELL,
                            "seed_base": GEN_SEED_BASE,
                            "seed_cell_stride": GEN_SEED_CELL_STRIDE},
        "n_configs": len(configs),
        "n_configs_by_regime": dict(by_regime),
        "n_pending_this_run": n_pending_all,
        "n_completed_this_run": completed if pending else 0,
        "n_errors_this_run": n_errors,
        "n_rows": merged["n_rows"], "n_infeasible": merged["n_infeasible"],
        "filters": {"skip_gen": bool(args.skip_gen),
                    "skip_emp": bool(args.skip_emp), "limit": args.limit},
        "git_describe": _git_describe(),
    }
    with open(META_JSON, "w") as f:
        json.dump(meta, f, indent=2)
    print("Wrote %s" % META_JSON)

    if args.smoke:
        # The projection describes the FULL run, so it is built from the full
        # arm set rather than from the smoke subset above.
        _configure_methods(smoke=False)
        print("")
        _runtime_projection(workers=args.workers,
                            rollcp_per_cell=args.rollcp_per_cell)


if __name__ == "__main__":
    main()
