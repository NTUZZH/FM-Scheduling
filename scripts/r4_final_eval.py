#!/usr/bin/env python
"""R4.4 Eval-B final-evaluation runner: the frozen method set on the fresh,
never-touched final test set, run ONCE (docs/protocol.md §R4 (design S2), docs/protocol.md
"Revision protocol R4", R4.4).

What Eval-B is
--------------
A final test set built by ``scripts/r4_final_instances.py`` into
``data/processed/instances_r4/`` + ``index_r4.csv`` (same schema as the v1.0
``index.csv`` plus ``eval_set`` and ``u_realized``):

  empirical cells : fresh timestamp-ordered anchors (shuffle seed 401) whose
                    windows overlap no released v1.0 instance window, sizes
                    {150, 400}, all six campuses;
  generator cells : fixed-window (80 bh) cells at target utilization
                    {0.7, 0.9, 1.0, 1.1, 1.3} on the training campuses,
                    fresh seeds (80000+ block), v1.1 fitted parameters.

Configurations (protocol R4.4)
------------------------------
  empirical x crew multiplier m in {1.0, 0.8, 0.6} on the VERDICT campuses
      {5, 9, 10, 12}, via fmwos.tightness.scale_crew;
  empirical x m = 1.0 only on campuses {1, 2} (transfer / nonstationary-
      calibration stress, reported as such);
  generator cells AS BUILT -- their contention is the drawn utilization
      target, so no crew scaling is applied on top of it.
A configuration id is the instance id, suffixed ``_m<m>`` by scale_crew when
m != 1.0 (so a scaled configuration never collides with its base instance in a
shard or in the merged CSV).

Methods (FROZEN before the run; recorded verbatim in meta.json)
---------------------------------------------------------------
  rules   : edd, pfifo, wspt, atc, wmdd, lpt, random  (fmwos.pdrs.dispatch,
            seed 301).  ATC keeps the literature default k = 2, which is also
            the k frozen by scripts/r4_atc_tune.py, so protocol R4.3's
            "atc_k{K*} only if K* != 2" adds no method here.
  rolling : rollcp2 (fmwos.rolling.roll_cpsat, budget 2.0 s, CP-SAT workers=2)
            on the first 8 configurations of every (regime, campus, size, m)
            cell in sorted-id order -- the same subsample rule as
            scripts/p4_dyneval.py.  CAUTION: v1.0 never ran rollcp2 on
            fixed-window generator cells (p4_dyneval ran storm2 with
            --no-rollcp), and those cells hold thousands of work orders, so
            the rolling planner's cost there is unmeasured and dominates the
            schedule.  Budget it separately, or bound it with
            --rollcp-per-cell / --no-rollcp; --project says so explicitly.
  policies: the existing frozen checkpoints, greedy argmax through the
            DispatchEnv reset()/step() path on CPU, exactly as p4_dyneval runs
            them (no retraining for Eval-B):
              rl301-303      results/p3_train/seed<t>/best.pt        (v1 MLP)
              v2rl301-310    results/p3_train/v2/seed<t>/best.pt     (v2 MLP)
              v2at301-310    results/p3_train/v2attn/seed<t>/best.pt (v2 attn)

Every schedule is scored ONLY by fmwos.validator; the dispatcher's self-report
is never used for a metric.

Output (results/r4_final/)
--------------------------
  shards/<config>.json   one shard per configuration, holding every method row
                         (atomic write; a finished shard is skipped on resume,
                         with the same union/incremental semantics as
                         p4_dyneval so a re-run never discards earlier rows);
  results.csv            the merged rows.  Its columns are the
                         results/p4_dyneval/results.csv columns in the same
                         order, plus a trailing ``eval_set`` -- the p4 column
                         list is a strict prefix, so any existing p4 analysis
                         reads this file unchanged.  ``u_realized`` is filled
                         for EVERY row (recomputed on the transformed instance
                         as sum p_bh / (n_tech * window_bh)); ``u_target`` is
                         filled for the generator cells that declare one.
  meta.json              date, the frozen method list, configuration counts,
                         and git describe.

Usage
-----
    PYTHONPATH=src python scripts/r4_final_eval.py [--workers 12] [--limit N]
        [--campus C[,C...]] [--size S[,S...]] [--no-rollcp]
        [--rollcp-per-cell N] [--out DIR] [--merge] [--project]
        [--smoke] [--smoke-n 4]

--smoke runs the first --smoke-n (default 4) empirical configurations at
m = 1.0 through the rules plus two policies (v2rl301, v2at301), prints the
rows, and writes to <out>/smoke/ so a smoke run can never be mistaken for the
Eval-B result.  It falls back to the released v1.0 replay TEST instances when
index_r4.csv does not exist yet, so the wiring is provable before the Eval-B
set is built; those rows carry eval_set='v1.0-smoke'.

--project prints a runtime projection for the full Eval-B run from the
measured per-method wall clock in results/p4_dyneval/results.csv (see
_runtime_projection); it is also printed at the end of every --smoke run.
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

# Keep BLAS/OpenMP/torch from oversubscribing the shared 24-core box: the only
# threaded work we allow is CP-SAT's workers=2 and torch's 2 inference threads
# (identical to scripts/p4_dyneval.py, so a latency measured here is comparable
# with the v1.0 dynamic evaluation).
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

import multiprocessing as mp  # noqa: E402

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

# NOTE: torch / fmwos.policy are imported LAZILY inside the worker so the parent
# never initialises torch before fork() (fork-safety on the shared box).
from fmwos import pdrs, rolling, tightness   # noqa: E402
from fmwos.env import DispatchEnv            # noqa: E402
from fmwos.validator import validate         # noqa: E402

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
INST_R4_ROOT = _ROOT / "data" / "processed" / "instances_r4"
INDEX_R4_CSV = INST_R4_ROOT / "index_r4.csv"
INST_V1_ROOT = _ROOT / "data" / "processed" / "instances"     # smoke fallback
INDEX_V1_CSV = INST_V1_ROOT / "index.csv"                     # smoke fallback
TRAIN_DIR = _ROOT / "results" / "p3_train"
P4_RESULTS_CSV = _ROOT / "results" / "p4_dyneval" / "results.csv"  # yardstick

OUT_DIR = _ROOT / "results" / "r4_final"
SHARD_DIR = OUT_DIR / "shards"
OUT_CSV = OUT_DIR / "results.csv"
META_JSON = OUT_DIR / "meta.json"

# --------------------------------------------------------------------------- #
# FROZEN method set (protocol R4.4: frozen before the run, recorded in meta)
# --------------------------------------------------------------------------- #
FROZEN_RULES = ["edd", "pfifo", "wspt", "atc", "wmdd", "lpt", "random"]

# (tag, checkpoint root, architecture, seeds).  The method column is tag+seed.
# Kept as plain tuples so a forked worker pickles names, never a torch object.
POLICY_ARMS = (
    ("rl", str(TRAIN_DIR), "mlp", [301, 302, 303]),
    ("v2rl", str(TRAIN_DIR / "v2"), "mlp", list(range(301, 311))),
    ("v2at", str(TRAIN_DIR / "v2attn"), "attn", list(range(301, 311))),
)
# One entry per policy: (method, tag, checkpoint_dir, arch, seed).
POLICY_SPECS = [("%s%d" % (tag, s), tag, d, arch, s)
                for tag, d, arch, seeds in POLICY_ARMS for s in seeds]
POLICY_METHODS = [p[0] for p in POLICY_SPECS]

ROLLCP_METHOD = "rollcp2"
FROZEN_METHODS = FROZEN_RULES + POLICY_METHODS + [ROLLCP_METHOD]

# The smoke subset: every rule plus one MLP and one attention policy, so both
# policy loaders and both rollout paths are exercised without paying for 23.
SMOKE_POLICY_METHODS = ["v2rl301", "v2at301"]

# ACTIVE_* are rederived by _configure_methods() in the PARENT before the pool
# is forked, so every worker inherits the same expected-method set.
ACTIVE_RULES = list(FROZEN_RULES)
ACTIVE_POLICIES = list(POLICY_SPECS)
BASE_METHODS = ACTIVE_RULES + [p[0] for p in ACTIVE_POLICIES]
_METHOD_ORDER = {m: i for i, m in enumerate(BASE_METHODS + [ROLLCP_METHOD])}

SEED = 301                  # PDR seed (only the 'random' rule consumes it)
ROLLCP_BUDGET_S = 2.0
CPSAT_WORKERS = 2           # spec-locked inside fmwos.rolling (documented here)
TORCH_THREADS = 2

# --------------------------------------------------------------------------- #
# Configuration grid (protocol R4.4)
# --------------------------------------------------------------------------- #
EVAL_SET = "final"
SMOKE_EVAL_SET = "v1.0-smoke"        # rows from the v1.0 fallback smoke set

REGIME_EMPIRICAL = "final-empirical"
REGIME_GEN = "final-gen"
_REGIME_ORDER = {REGIME_EMPIRICAL: 0, REGIME_GEN: 1}

VERDICT_CAMPUSES = [5, 9, 10, 12]    # crew grid applies here
CREW_MULTS_VERDICT = [1.0, 0.8, 0.6]
CREW_MULTS_OTHER = [1.0]             # campuses 1, 2: transfer / stress, m = 1.0

# Empirical anchors are the timestamp-ordered track; every generated instance
# carries window_start == 'synthetic' (fmwos.generator writes it, and so does
# every generator index row in the v1.0 index.csv), which is the discriminator.
# The track name is only the fallback, so a builder that renames the empirical
# track still classifies its rows correctly.
EMPIRICAL_TRACKS = {"replay", "empirical", "final"}

REPLAY_SIZES = [150, 400]            # v1.0 smoke fallback filter
DEFAULT_ROLLCP_PER_CELL = 8
DEFAULT_WORKERS = 12
DEFAULT_SMOKE_N = 4

# Nominal Eval-B counts (docs/protocol.md §R4 (design S2)), used by --project only when
# index_r4.csv does not exist yet.  30 empirical anchors per (campus, size)
# cell, 2 sizes, 4 verdict campuses x 3 crew multipliers + 2 other campuses at
# m = 1.0; 15 generator instances per (campus, u) cell, 4 campuses x 5 targets.
NOMINAL_EMPIRICAL_PER_CELL = 30
NOMINAL_GEN_PER_CELL = 15
NOMINAL_GEN_UTIL = [0.7, 0.9, 1.0, 1.1, 1.3]

# results/p4_dyneval/results.csv columns, in order, plus the Eval-B additions.
# The p4 list is a strict PREFIX so any p4 analysis reads this CSV unchanged.
P4_FIELDS = [
    "id", "campus", "track", "split", "size", "regime", "crew_multiplier",
    "arrival_multiplier", "pm_share_override", "method", "seed", "feasible",
    "wwt", "makespan", "mean_flow", "breach_share", "breach_p1", "breach_p2",
    "breach_p3", "breach_p4", "wall_seconds", "decisions",
    "mean_ms_per_decision", "mean_replan_s",
    "u_target", "u_realized",
]
FIELDS = P4_FIELDS + ["eval_set"]


# --------------------------------------------------------------------------- #
# Reconfiguration (called in the parent, before the worker pool is forked)
# --------------------------------------------------------------------------- #
def _configure_methods(smoke=False):
    """Set the active method set and rederive the name lists / merge order.

    The full Eval-B set is the frozen list; --smoke keeps every rule but only
    ``SMOKE_POLICY_METHODS``, which is enough to exercise both policy loaders
    (MLP and attention) and the shared rollout path."""
    global ACTIVE_RULES, ACTIVE_POLICIES, BASE_METHODS, _METHOD_ORDER
    ACTIVE_RULES = list(FROZEN_RULES)
    if smoke:
        keep = set(SMOKE_POLICY_METHODS)
        ACTIVE_POLICIES = [p for p in POLICY_SPECS if p[0] in keep]
    else:
        ACTIVE_POLICIES = list(POLICY_SPECS)
    BASE_METHODS = ACTIVE_RULES + [p[0] for p in ACTIVE_POLICIES]
    _METHOD_ORDER = {m: i for i, m in enumerate(BASE_METHODS + [ROLLCP_METHOD])}


def _configure_out(out_dir):
    """Point the results root (shards / results.csv / meta.json) at ``out_dir``."""
    global OUT_DIR, SHARD_DIR, OUT_CSV, META_JSON
    OUT_DIR = Path(out_dir)
    SHARD_DIR = OUT_DIR / "shards"
    OUT_CSV = OUT_DIR / "results.csv"
    META_JSON = OUT_DIR / "meta.json"


# --------------------------------------------------------------------------- #
# Target-set construction
# --------------------------------------------------------------------------- #
def _is_generator(row):
    """True for a generated (fixed-window) cell, False for an empirical anchor.

    Generated instances are written with ``window_start == 'synthetic'``; the
    track name is the fallback discriminator."""
    if str(row.get("window_start", "")).strip().lower() == "synthetic":
        return True
    return str(row.get("track", "")).strip().lower() not in EMPIRICAL_TRACKS


def _crew_mults(campus):
    """Crew-multiplier grid for ``campus`` (protocol R4.4).

    The verdict campuses carry the contention grid; the held-out campuses run
    at nominal capacity only, because they are reported as transfer and as the
    nonstationary-calibration stress case, not as verdict evidence."""
    return (list(CREW_MULTS_VERDICT) if int(campus) in VERDICT_CAMPUSES
            else list(CREW_MULTS_OTHER))


def _instance_path(row, inst_root):
    p = row.get("path")
    if p:
        cand = Path(inst_root) / p
        if cand.exists():
            return cand
    return (Path(inst_root) / ("c%02d" % int(row["campus"])) / str(row["track"])
            / str(row["size_class"]) / (row["id"] + ".json"))


def _peek_meta(path):
    """Instance ``meta`` dict, or {} when the file is missing/unreadable.

    Only the generator cells are peeked at build time, and only for the two
    provenance fields the configuration grid needs before the worker runs:
    ``u_target`` (it keys the rollcp2 subsample cell, because a fixed-window
    cell's work-order count varies per draw) and ``arrival_multiplier``."""
    try:
        with open(path) as f:
            return json.load(f).get("meta", {}) or {}
    except (OSError, json.JSONDecodeError, KeyError):
        return {}


def _index_rows(index_csv, v1_fallback=False):
    """Index rows for the target set (v1.0 fallback keeps replay TEST only)."""
    with open(index_csv, newline="") as f:
        rows = list(csv.DictReader(f))
    if not v1_fallback:
        return rows
    keep = []
    for r in rows:
        if str(r.get("track", "")).strip().lower() != "replay":
            continue
        if str(r.get("split", "")).strip().lower() != "test":
            continue
        try:
            if int(r["size_class"]) not in REPLAY_SIZES:
                continue
        except (KeyError, TypeError, ValueError):
            continue
        keep.append(r)
    return keep


def build_targets(index_csv, inst_root, eval_set, v1_fallback=False):
    """Return the full ordered list of configuration dicts.

    One configuration is one instance under one crew multiplier; it is
    picklable and self-describing, and the worker materialises the instance
    from ``path`` (+ scale_crew when m != 1.0)."""
    if not Path(index_csv).exists():
        raise FileNotFoundError("instance index not found: %s" % index_csv)

    configs = []
    for r in _index_rows(index_csv, v1_fallback=v1_fallback):
        try:
            campus = int(r["campus"])
            size = int(r["size_class"])
        except (KeyError, TypeError, ValueError):
            continue
        path = str(_instance_path(r, inst_root))
        track = str(r.get("track", "")).strip()
        split = str(r.get("split", "")).strip()
        row_eval_set = str(r.get("eval_set", "")).strip() or eval_set

        if _is_generator(r):
            # Generator cells run as built: their contention IS the drawn
            # utilization target, so no crew multiplier is layered on top.
            meta = _peek_meta(path)
            u_t = r.get("u_target") or meta.get("u_target")
            am = meta.get("arrival_multiplier")
            configs.append({
                "id": r["id"], "base_id": r["id"], "campus": campus,
                "track": track, "split": split, "size": size,
                "regime": REGIME_GEN, "crew_multiplier": 1.0,
                "arrival_multiplier": float(am) if am is not None else 1.0,
                "pm_share_override": None,
                "u_target": float(u_t) if u_t not in (None, "") else None,
                "kind": "generator", "path": path, "m": 1.0,
                "eval_set": row_eval_set,
            })
            continue

        for m in _crew_mults(campus):
            # scale_crew suffixes the instance id '_m<m>'; the configuration id
            # matches it exactly so shards and rows stay aligned with the
            # transformed instance the validator actually scored.
            cid = r["id"] if m == 1.0 else "%s_m%s" % (r["id"], m)
            configs.append({
                "id": cid, "base_id": r["id"], "campus": campus,
                "track": track, "split": split, "size": size,
                "regime": REGIME_EMPIRICAL, "crew_multiplier": float(m),
                "arrival_multiplier": 1.0, "pm_share_override": None,
                "u_target": None, "kind": "empirical", "path": path,
                "m": float(m), "eval_set": row_eval_set,
            })

    configs.sort(key=lambda c: (_REGIME_ORDER[c["regime"]], c["campus"],
                                c["size"], c["crew_multiplier"],
                                c["arrival_multiplier"], c["id"]))
    return configs


def assign_rollcp(configs, per_cell, enabled):
    """Mark ``rollcp=True`` on the first ``per_cell`` configurations of every
    EMPIRICAL (regime, campus, size, crew_multiplier) cell, in sorted-id order.

    Generator (fixed-window) cells never run the rolling planner: the dated
    R4 adjustment in docs/protocol.md extends the v1.0 overload-sweep scale
    boundary to Eval-B, because these cells draw 1,500--12,400 orders per
    instance and one 2 s-budget rolling run on the smallest such instance
    exceeded 900 s. Mirrors scripts/p4_dyneval.py's assign_rollcp otherwise."""
    cells = defaultdict(list)
    for c in configs:
        if c["regime"] == REGIME_GEN:
            c["rollcp"] = False        # scale boundary, protocol R4 adjustment
            continue
        key = (c["regime"], c["campus"], c["size"], c["crew_multiplier"])
        cells[key].append(c)
    for key, group in cells.items():
        group.sort(key=lambda c: c["id"])
        for j, c in enumerate(group):
            c["rollcp"] = bool(enabled and j < per_cell)
    return configs


def _expected_methods(config):
    return BASE_METHODS + ([ROLLCP_METHOD] if config.get("rollcp") else [])


# --------------------------------------------------------------------------- #
# Worker: policy cache + rollout (mirrors scripts/p4_dyneval.py)
# --------------------------------------------------------------------------- #
_POLICY_CACHE = {}


def _get_policy(ckpt_dir, arch, seed):
    """Load (and cache per worker process) one frozen checkpoint on CPU."""
    key = (ckpt_dir, arch, seed)
    pol = _POLICY_CACHE.get(key)
    if pol is None:
        import torch  # lazy: only inside the worker
        torch.set_num_threads(TORCH_THREADS)
        ckpt = str(Path(ckpt_dir) / ("seed%d" % seed) / "best.pt")
        if arch == "attn":
            from fmwos.policy_attn import AttnDispatchPolicy
            pol = AttnDispatchPolicy.load(ckpt, map_location="cpu")
        else:
            from fmwos.policy import DispatchPolicy
            pol = DispatchPolicy.load(ckpt, map_location="cpu")
        pol.eval()
        _POLICY_CACHE[key] = pol
    return pol


def _policy_rollout(instance, method, ckpt_dir, arch, seed):
    """Greedy argmax episode through the DispatchEnv reset()/step() path."""
    pol = _get_policy(ckpt_dir, arch, seed)
    env = DispatchEnv(instance)
    obs = env.reset()
    done = False
    while not done:
        a, _, _, _ = pol.act(obs, greedy=True, device="cpu")
        obs, _r, done, _info = env.step(a)
    return env.to_schedule(method, seed=seed)


def _realized_util(instance):
    """Realized utilization of the TRANSFORMED instance the methods will see.

    sum p_bh / (n_tech * window_bh), so a crew multiplier that removes
    technicians raises it exactly as the contention it creates does (protocol
    R4.4: realized utilization is the primary explanatory variable, and it must
    describe the configuration, not the base instance)."""
    total_p = sum(float(w["p_bh"]) for w in instance["work_orders"])
    n_tech = len(instance["technicians"])
    window_bh = float(instance["meta"]["window_bh"])
    denom = n_tech * window_bh
    return float(total_p / denom) if denom > 0 else None


# --------------------------------------------------------------------------- #
# Row building
# --------------------------------------------------------------------------- #
def _row(config, method, seed, sched, res):
    m = res["metrics"]
    pp = m["per_priority_breach_share"]
    decisions = sched.get("decisions")
    wall = sched.get("wall_seconds")
    mean_ms = None
    if decisions and wall is not None and decisions > 0:
        mean_ms = 1000.0 * float(wall) / float(decisions)
    return {
        "id": config["id"], "campus": config["campus"], "track": config["track"],
        "split": config["split"], "size": config["size"],
        "regime": config["regime"],
        "crew_multiplier": config["crew_multiplier"],
        "arrival_multiplier": config["arrival_multiplier"],
        "pm_share_override": config.get("pm_share_override"),
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
    }


def _write_shard(shard_id, shard):
    dst = SHARD_DIR / (shard_id + ".json")
    tmp = SHARD_DIR / (shard_id + ".json.tmp")
    with open(tmp, "w") as f:
        json.dump(shard, f)
    os.replace(tmp, dst)


# --------------------------------------------------------------------------- #
# One configuration x all its methods (runs in a worker process)
# --------------------------------------------------------------------------- #
def _run_one(config):
    t0 = time.perf_counter()
    try:
        # INCREMENTAL semantics (as p4_dyneval): a shard is the union of every
        # method ever computed for this configuration, so a resumed or widened
        # run computes only what is missing and never discards earlier rows.
        dst = SHARD_DIR / (config["id"] + ".json")
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

        # The worker owns its copy of the configuration, so the two per-config
        # provenance numbers that can only be read off the materialised
        # instance are filled in here and picked up by _row().
        config = dict(config)
        config["u_realized"] = _realized_util(instance)
        if config.get("u_target") is None:
            u_t = instance.get("meta", {}).get("u_target")
            config["u_target"] = float(u_t) if u_t is not None else None

        out_rows = {}
        infeasible = []
        expected = _expected_methods(config)
        todo = {m for m in expected if m not in old_rows}

        # Rules (seed 301) ---------------------------------------------------
        for rule in ACTIVE_RULES:
            if rule not in todo:
                continue
            sched = pdrs.dispatch(instance, rule, seed=SEED)
            res = validate(instance, sched)
            out_rows[rule] = _row(config, rule, SEED, sched, res)
            if not res["feasible"]:
                infeasible.append({"method": rule,
                                   "violations": res["violations"][:3]})

        # Frozen policies (greedy argmax) ------------------------------------
        for meth, _tag, ckpt_dir, arch, t in ACTIVE_POLICIES:
            if meth not in todo:
                continue
            sched = _policy_rollout(instance, meth, ckpt_dir, arch, t)
            res = validate(instance, sched)
            out_rows[meth] = _row(config, meth, t, sched, res)
            if not res["feasible"]:
                infeasible.append({"method": meth,
                                   "violations": res["violations"][:3]})

        # rollcp2 (subsample) -------------------------------------------------
        if config.get("rollcp") and ROLLCP_METHOD in todo:
            sched = rolling.roll_cpsat(instance, budget_s=ROLLCP_BUDGET_S)
            res = validate(instance, sched)
            out_rows[ROLLCP_METHOD] = _row(config, ROLLCP_METHOD, 0, sched, res)
            if not res["feasible"]:
                infeasible.append({"method": ROLLCP_METHOD,
                                   "violations": res["violations"][:3]})

        out_rows = {**old_rows, **out_rows}
        assert set(expected).issubset(out_rows), "internal: method set mismatch"
        expected_union = sorted(set(expected) | set(old_expected))

        shard = {
            "shard_id": config["id"], "id": config["id"],
            "base_id": config["base_id"], "campus": config["campus"],
            "regime": config["regime"], "size": config["size"],
            "crew_multiplier": config["crew_multiplier"],
            "u_realized": config["u_realized"], "u_target": config["u_target"],
            "eval_set": config["eval_set"], "rows": out_rows,
            "methods_expected": expected_union, "infeasible": infeasible,
            "wall_seconds_total": time.perf_counter() - t0,
        }
        _write_shard(config["id"], shard)
        return {"id": config["id"], "regime": config["regime"], "ok": True,
                "rows": out_rows, "infeasible": infeasible,
                "wall": shard["wall_seconds_total"]}
    except Exception as e:  # noqa: BLE001 -- report, never kill the pool
        import traceback
        return {"id": config["id"], "regime": config["regime"], "ok": False,
                "rows": {}, "infeasible": [],
                "error": "%s: %s" % (type(e).__name__, e),
                "traceback": traceback.format_exc(),
                "wall": time.perf_counter() - t0}


# --------------------------------------------------------------------------- #
# Resumability + merge
# --------------------------------------------------------------------------- #
def _shard_methods():
    """Map shard id -> set of method rows it already holds (corrupt -> absent)."""
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
            have[d.get("id", p.stem)] = set(rows)
    return have


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
        expected = d.get("methods_expected", BASE_METHODS)
        if not (isinstance(rows, dict) and set(rows) >= set(expected)):
            n_partial += 1
            continue
        n_finished += 1
        for meth in expected:
            r = rows[meth]
            all_rows.append(r)
            if not r.get("feasible"):
                n_infeasible += 1

    all_rows.sort(key=lambda r: (_REGIME_ORDER.get(r["regime"], 99), r["campus"],
                                 r["size"], r["crew_multiplier"],
                                 r["arrival_multiplier"], r["id"],
                                 _METHOD_ORDER.get(r["method"], 99)))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in all_rows:
            w.writerow({c: r.get(c) for c in FIELDS})
    if verbose:
        print("Merged %d finished config(s) -> %d rows -> %s"
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
# Method-cost fallbacks when the yardstick CSV has no row for a method under a
# family: wmdd was added in the R4 wave (cost it as atc, the other due-date
# rule with a per-candidate score), lpt is the renamed 'mor', and the v1 MLP
# policies never ran on the fixed-window cells (cost them as the v2 MLP, which
# is the same architecture and the same observation dims).
_PROJ_FALLBACK = {"wmdd": "atc", "lpt": "mor",
                  "rl301": "v2rl301", "rl302": "v2rl302", "rl303": "v2rl303"}


def _yardstick(csv_path=P4_RESULTS_CSV):
    """Mean per-schedule wall seconds per method, per Eval-B family.

    Reads results/p4_dyneval/results.csv, the only measurement of these exact
    methods on this exact box: its replay regimes are the yardstick for the
    Eval-B empirical configurations, its fixed-window storm2 regime for the
    generator cells (same generate_window draw, so a comparable work-order
    count).  Returns {family: {method: mean_wall_seconds}}."""
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
    """Mean wall seconds for ``method``, via the documented fallback map."""
    if method in means:
        return means[method]
    alt = _PROJ_FALLBACK.get(method)
    if alt and alt in means:
        return means[alt]
    return None


def _runtime_projection(configs=None, workers=DEFAULT_WORKERS):
    """Print a projected wall clock for the FULL Eval-B run.

    Uses the measured per-method cost of the v1.0 dynamic evaluation (see
    _yardstick).  When the Eval-B index does not exist yet, the configuration
    counts fall back to the nominal design of docs/protocol.md §R4 (design S2)."""
    means = _yardstick()
    if configs:
        n_emp = sum(1 for c in configs if c["regime"] == REGIME_EMPIRICAL)
        n_gen = sum(1 for c in configs if c["regime"] == REGIME_GEN)
        n_roll_emp = sum(1 for c in configs
                         if c.get("rollcp") and c["regime"] == REGIME_EMPIRICAL)
        n_roll_gen = sum(1 for c in configs
                         if c.get("rollcp") and c["regime"] == REGIME_GEN)
        src = "index_r4.csv"
    else:
        n_emp = (len(VERDICT_CAMPUSES) * len(REPLAY_SIZES)
                 * NOMINAL_EMPIRICAL_PER_CELL * len(CREW_MULTS_VERDICT)
                 + 2 * len(REPLAY_SIZES) * NOMINAL_EMPIRICAL_PER_CELL)
        n_gen = (len(VERDICT_CAMPUSES) * len(NOMINAL_GEN_UTIL)
                 * NOMINAL_GEN_PER_CELL)
        n_roll_emp = (len(VERDICT_CAMPUSES) * len(REPLAY_SIZES)
                      * len(CREW_MULTS_VERDICT)
                      + 2 * len(REPLAY_SIZES)) * DEFAULT_ROLLCP_PER_CELL
        n_roll_gen = (len(VERDICT_CAMPUSES) * len(NOMINAL_GEN_UTIL)
                      * DEFAULT_ROLLCP_PER_CELL)
        src = "nominal design (docs/protocol.md §R4 (design S2))"

    print("Runtime projection for the full Eval-B run")
    print("  config counts   : %d empirical + %d generator = %d  [%s]"
          % (n_emp, n_gen, n_emp + n_gen, src))
    print("  methods/config  : %d frozen (%d rules + %d policies) "
          "+ rollcp2 on %d + %d config(s)"
          % (len(FROZEN_RULES) + len(POLICY_METHODS), len(FROZEN_RULES),
             len(POLICY_METHODS), n_roll_emp, n_roll_gen))
    print("  yardstick       : %s (replay -> empirical, storm2 -> generator)"
          % P4_RESULTS_CSV)

    total = 0.0
    for family, n_cfg, n_roll in (("empirical", n_emp, n_roll_emp),
                                  ("generator", n_gen, n_roll_gen)):
        m = means.get(family, {})
        per_cfg, missing = 0.0, []
        for method in FROZEN_RULES + POLICY_METHODS:
            cost = _method_cost(m, method)
            if cost is None:
                missing.append(method)
            else:
                per_cfg += cost
        roll = _method_cost(m, ROLLCP_METHOD)
        base_s = per_cfg * n_cfg
        roll_s = (roll * n_roll) if roll is not None else None
        total += base_s + (roll_s or 0.0)
        print("  %-9s : %7.1f core-s/config x %d = %s%s"
              % (family, per_cfg, n_cfg, _fmt_hms(base_s),
                 ("  (no yardstick for %s)" % ",".join(missing)) if missing else ""))
        if roll_s is not None:
            print("  %-9s   rollcp2 %.1f core-s x %d = %s"
                  % ("", roll, n_roll, _fmt_hms(roll_s)))
        else:
            print("  %-9s   rollcp2 on %d config(s): UNMEASURED -- v1.0 never "
                  "ran the rolling planner on fixed-window cells, and one "
                  "replan is budgeted %.1f s. Measure one before committing, "
                  "or bound it with --rollcp-per-cell / --no-rollcp."
                  % ("", n_roll, ROLLCP_BUDGET_S))
    print("  TOTAL           : %s core-time  ->  ~%s wall at %d workers"
          % (_fmt_hms(total), _fmt_hms(total / max(1, workers)), workers))
    print("  (projection only: the generator cells dominate, and their cost "
          "scales with the drawn work-order count, which the Eval-B builder "
          "sets; rollcp2 on the fixed-window cells is the least certain term.)")
    return total


# --------------------------------------------------------------------------- #
# Smoke printing
# --------------------------------------------------------------------------- #
_SMOKE_COLS = ["id", "campus", "size", "crew_multiplier", "method", "feasible",
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
        description="R4.4 Eval-B final-evaluation runner (frozen method set).")
    ap.add_argument("--workers", type=int, default=DEFAULT_WORKERS,
                    help="parallel configuration workers (default %d)"
                         % DEFAULT_WORKERS)
    ap.add_argument("--limit", type=int, default=None,
                    help="cap not-yet-done configurations processed this run")
    ap.add_argument("--campus", default=None, help="restrict campus id(s)")
    ap.add_argument("--size", default=None,
                    help="restrict size class(es); never filters the "
                         "generator cells, whose size varies per draw")
    ap.add_argument("--no-rollcp", action="store_true",
                    help="skip the rollcp2 subsample entirely")
    ap.add_argument("--rollcp-per-cell", type=int,
                    default=DEFAULT_ROLLCP_PER_CELL,
                    help="rollcp2 subsample size per cell (default %d)"
                         % DEFAULT_ROLLCP_PER_CELL)
    ap.add_argument("--index", default=str(INDEX_R4_CSV),
                    help="Eval-B instance index (default "
                         "data/processed/instances_r4/index_r4.csv)")
    ap.add_argument("--out", default=str(OUT_DIR),
                    help="results root (default results/r4_final)")
    ap.add_argument("--merge", action="store_true",
                    help="only (re)build results.csv from existing shards")
    ap.add_argument("--project", action="store_true",
                    help="print the runtime projection and exit")
    ap.add_argument("--smoke", action="store_true",
                    help="wiring check: the first --smoke-n empirical configs "
                         "at m=1.0 x rules + %s, into <out>/smoke/"
                         % ", ".join(SMOKE_POLICY_METHODS))
    ap.add_argument("--smoke-n", type=int, default=DEFAULT_SMOKE_N,
                    help="smoke subset size (default %d)" % DEFAULT_SMOKE_N)
    args = ap.parse_args(argv)

    # Reconfigure BEFORE any dir is created or any worker is forked, so the
    # forked workers inherit the active method set and the results root.
    _configure_methods(smoke=args.smoke)
    out_root = Path(args.out) / "smoke" if args.smoke else Path(args.out)
    _configure_out(out_root)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SHARD_DIR.mkdir(parents=True, exist_ok=True)

    if args.merge:
        _merge(verbose=True)
        return

    # The Eval-B index is required for the real run; --smoke falls back to the
    # released v1.0 replay TEST instances so the wiring is provable before the
    # Eval-B set exists.
    index_csv = Path(args.index)
    v1_fallback = False
    if not index_csv.exists():
        if not args.smoke:
            sys.exit("Eval-B index not found: %s\n"
                     "Build it first with scripts/r4_final_instances.py "
                     "(or pass --index), or run --smoke for a wiring check on "
                     "the released v1.0 instances." % index_csv)
        index_csv, inst_root = INDEX_V1_CSV, INST_V1_ROOT
        v1_fallback = True
    else:
        inst_root = index_csv.parent

    if args.project:
        configs = None
        if not v1_fallback:
            configs = assign_rollcp(
                build_targets(index_csv, inst_root, EVAL_SET),
                args.rollcp_per_cell, not args.no_rollcp)
        _runtime_projection(configs, workers=args.workers)
        return

    eval_set = SMOKE_EVAL_SET if v1_fallback else EVAL_SET
    configs = build_targets(index_csv, inst_root, eval_set,
                            v1_fallback=v1_fallback)

    if args.campus:
        keep = {c.strip() for c in args.campus.split(",")}
        configs = [c for c in configs if str(c["campus"]) in keep]
    if args.size:
        keep = {s.strip() for s in args.size.split(",")}
        # --size applies only to the empirical cells; a generator cell's size
        # is the (variable) realized work-order count, so it is never excluded.
        configs = [c for c in configs
                   if c["regime"] == REGIME_GEN or str(c["size"]) in keep]

    if args.smoke:
        # Deterministic wiring subset: the first N empirical configurations at
        # nominal capacity, in the run's own sorted order.
        configs = [c for c in configs
                   if c["regime"] == REGIME_EMPIRICAL and c["m"] == 1.0]
        configs = configs[:args.smoke_n]

    configs = assign_rollcp(configs, args.rollcp_per_cell,
                            not args.no_rollcp and not args.smoke)
    n_rollcp = sum(1 for c in configs if c.get("rollcp"))

    have = _shard_methods()
    pending = [c for c in configs
               if not (have.get(c["id"], set()) >= set(_expected_methods(c)))]
    n_pending_all = len(pending)
    if args.limit is not None:
        pending = pending[:args.limit]

    by_regime = defaultdict(int)
    for c in configs:
        by_regime[c["regime"]] += 1

    print("R4.4 Eval-B final evaluation%s" % ("  (SMOKE SUBSET)" if args.smoke else ""))
    if args.smoke:
        print("  SMOKE -- NOT the Eval-B result: %d config(s), rules + %s, "
              "written to %s" % (len(configs), ", ".join(SMOKE_POLICY_METHODS),
                                 OUT_DIR))
    print("  index           : %s%s"
          % (index_csv, "  (v1.0 fallback)" if v1_fallback else ""))
    print("  eval_set        : %s" % eval_set)
    print("  out root        : %s" % OUT_DIR)
    print("  configs total   : %d  %s" % (len(configs), dict(by_regime)))
    print("  rollcp2 subset  : %d config(s) (per_cell=%d%s)"
          % (n_rollcp, args.rollcp_per_cell,
             ", DISABLED" if (args.no_rollcp or args.smoke) else ""))
    print("  already finished: %d  ->  pending this run: %d"
          % (len(configs) - n_pending_all, len(pending)))
    print("  methods/config  : %d (%s)" % (len(BASE_METHODS),
                                           ", ".join(BASE_METHODS)))
    print("  workers=%d  cpsat_workers=%d  torch_threads=%d  pdr_seed=%d  "
          "rollcp_budget=%.1fs" % (args.workers, CPSAT_WORKERS, TORCH_THREADS,
                                   SEED, ROLLCP_BUDGET_S))

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
                        print("[INFEASIBLE] id=%s method=%s :: %s"
                              % (res["id"], it["method"],
                                 " | ".join(it.get("violations", []))))
                if completed % 25 == 0 or completed == total:
                    elapsed = time.perf_counter() - t_start
                    eta = elapsed / completed * (total - completed)
                    print("  progress %d/%d  elapsed %s  eta %s  "
                          "(%d infeasible, %d errors)"
                          % (completed, total, _fmt_hms(elapsed), _fmt_hms(eta),
                             n_infeasible, n_errors))

        elapsed = time.perf_counter() - t_start
        end_iso = _dt.datetime.now().isoformat(timespec="seconds")
        print("Run complete: %d config(s) in %s (%d infeasible, %d errors)."
              % (completed, _fmt_hms(elapsed), n_infeasible, n_errors))
        merged = _merge(verbose=True)

    if args.smoke and smoke_rows:
        smoke_rows.sort(key=lambda r: (r["id"], _METHOD_ORDER.get(r["method"], 99)))
        print("")
        _print_smoke_rows(smoke_rows)
        print("")

    meta = {
        "experiment": "r4_final_eval",
        "protocol": "docs/protocol.md R4.4 / docs/protocol.md §R4 (design S2)",
        "date": _dt.date.today().isoformat(),
        "start_time": start_iso, "end_time": end_iso,
        "elapsed_seconds": round(elapsed, 3), "workers": args.workers,
        "smoke": bool(args.smoke),
        "eval_set": eval_set,
        "index_csv": str(index_csv), "v1_fallback": v1_fallback,
        "out_dir": str(OUT_DIR),
        "frozen_methods": list(FROZEN_METHODS),
        "frozen_rules": list(FROZEN_RULES),
        "frozen_policies": [{"tag": t, "dir": d, "arch": a, "seeds": list(s)}
                            for t, d, a, s in POLICY_ARMS],
        "methods_this_run": list(BASE_METHODS)
                            + ([ROLLCP_METHOD] if n_rollcp else []),
        "pdr_seed": SEED, "rollcp_budget_s": ROLLCP_BUDGET_S,
        "cpsat_workers": CPSAT_WORKERS, "torch_threads": TORCH_THREADS,
        "crew_multipliers": {"verdict_campuses": VERDICT_CAMPUSES,
                             "verdict": CREW_MULTS_VERDICT,
                             "other": CREW_MULTS_OTHER},
        "n_configs": len(configs),
        "n_configs_by_regime": dict(by_regime),
        "n_rollcp": n_rollcp, "rollcp_per_cell": args.rollcp_per_cell,
        "no_rollcp": bool(args.no_rollcp),
        "n_pending_this_run": n_pending_all,
        "n_completed_this_run": completed if pending else 0,
        "n_errors_this_run": n_errors,
        "n_rows": merged["n_rows"], "n_infeasible": merged["n_infeasible"],
        "filters": {"campus": args.campus, "size": args.size,
                    "limit": args.limit},
        "git_describe": _git_describe(),
    }
    with open(META_JSON, "w") as f:
        json.dump(meta, f, indent=2)
    print("Wrote %s" % META_JSON)

    if args.smoke:
        # The projection describes the FULL Eval-B run, so it is built from a
        # fresh unfiltered target list (the smoke subset above is 4 configs).
        proj_configs = None
        if not v1_fallback:
            proj_configs = assign_rollcp(
                build_targets(index_csv, inst_root, EVAL_SET),
                args.rollcp_per_cell, not args.no_rollcp)
        print("")
        _runtime_projection(proj_configs, workers=args.workers)


if __name__ == "__main__":
    main()
