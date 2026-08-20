#!/usr/bin/env python
"""R4.9 -- release-time robustness: a synthetic backdating of corrective orders.

The empirical track reads ``WOStartDate`` as the moment a work order becomes
available.  That field does not distinguish request, record opening, scheduled
start and work start, so for corrective work it may POSTDATE the true request:
the crew is told about a fault, and the record is opened later.  This runner
measures how much the method ranking depends on that reading by shifting every
corrective release earlier and re-scoring.  The scenario is synthetic and is
reported as such; it is a robustness check, not an estimate of the true request
times.

Transform (one pure function of one instance; ``_bd`` id suffix)
----------------------------------------------------------------
For each CORRECTIVE order (``is_pm`` false), with SLA(class) the class's service
window in business hours (``fmwos.timeaxis.SLA_BH``)::

    delta       ~ Uniform[0, 0.5 * SLA(priority)]
    release_bh' = max(0, release_bh - delta)
    due_bh'     = release_bh' + SLA(priority)

The due date is RECOMPUTED from the shifted release, so an order that is
backdated keeps its contractual window length and its deadline moves earlier
with it.  Preventive orders are untouched (they are calendared, so their release
is not a proxy for anything).  ``meta.window_bh`` is left unchanged: the window
is the observation period the instance was cut from, and rescaling it would
change the instance's utilization, which is exactly the quantity every result is
conditioned on.  Backdating can therefore move a release to bh 0 but never
before it, which is the only clamp in the transform.

Deterministic keying (documented, order-independent)
----------------------------------------------------
Every (instance, work order) pair draws its own delta from its own generator::

    key   = blake2b(f"{base_instance_id}|{wo_id}", digest_size=8) as a uint64
    rng   = numpy.random.default_rng([424242, key])
    delta = rng.uniform(0.0, 0.5 * SLA_BH[priority])

The master seed 424242 and the hashed pair enter one SeedSequence, so a work
order's delta depends only on its instance id and its own id: it does not depend
on the order of the work orders in the file, on how many instances are run, on
the worker count, or on the chunk a task landed in.  A rerun on any subset
reproduces every delta exactly.

Methods, scoring and rerun semantics: scripts/r4_robust_common.py.

Outputs (results/r4_robustness/backdate/, or .../smoke/ under --smoke)
----------------------------------------------------------------------
  results.csv  one row per (backdated instance x method), with the realized
               backdating statistics per instance
  meta.json    date, seed scheme, method list, base set, counts

Usage
-----
    PYTHONPATH=src python scripts/r4_backdate.py [--workers 12] [--smoke]
"""

from __future__ import annotations

import argparse
import copy
import datetime as _dt
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import r4_robust_common as rc  # noqa: E402

from fmwos.timeaxis import SLA_BH  # noqa: E402

NAME = "backdate"
SUFFIX = "_bd"
BACKDATE_SEED = 424242      # master seed of the whole scenario (protocol R4.9)
MAX_SHIFT_FRAC = 0.5        # delta ~ U[0, MAX_SHIFT_FRAC * SLA(class)]
ROUND_BH = 4                # instance builder stores release_bh/due_bh to 4 dp

FIELDS = ["id", "base_instance_id", "campus", "size", "transform",
          "backdate_seed", "max_shift_frac", "n_wos", "n_corrective",
          "corrective_share", "mean_delta_bh", "max_delta_bh",
          "n_clamped_at_zero", "window_bh", "u_realized"] + rc.METRIC_FIELDS


# --------------------------------------------------------------------------- #
# Transform
# --------------------------------------------------------------------------- #
def _delta_rng(base_id, wo_id):
    """Per-(instance, work order) generator, independent of any iteration order."""
    digest = hashlib.blake2b(("%s|%s" % (base_id, wo_id)).encode("utf-8"),
                             digest_size=8).digest()
    key = int.from_bytes(digest, "big")
    return np.random.default_rng([BACKDATE_SEED, key])


def backdate(instance, base_id):
    """Deep copy with every corrective release (and its due date) shifted earlier.

    Returns ``(instance, stats)`` where ``stats`` holds the realized backdating
    of this instance: how many orders were corrective, the mean and maximum
    delta actually drawn, and how many releases hit the bh 0 clamp.
    """
    inst = copy.deepcopy(instance)
    deltas, n_clamped = [], 0
    for wo in inst["work_orders"]:
        if bool(wo.get("is_pm")):
            continue                      # preventive work is calendared
        prio = int(wo["priority"])
        rng = _delta_rng(base_id, wo["id"])
        delta = float(rng.uniform(0.0, MAX_SHIFT_FRAC * SLA_BH[prio]))
        release = float(wo["release_bh"]) - delta
        if release < 0.0:
            release = 0.0
            n_clamped += 1
        wo["release_bh"] = round(release, ROUND_BH)
        wo["due_bh"] = round(wo["release_bh"] + SLA_BH[prio], ROUND_BH)
        deltas.append(delta)

    meta = dict(inst.get("meta", {}))
    meta["backdate_seed"] = BACKDATE_SEED
    meta["backdate_max_shift_frac"] = MAX_SHIFT_FRAC
    meta["id"] = "%s%s" % (meta.get("id", "inst"), SUFFIX)
    inst["meta"] = meta

    n = len(inst["work_orders"])
    stats = {
        "n_wos": n, "n_corrective": len(deltas),
        "corrective_share": round(len(deltas) / n, 6) if n else 0.0,
        "mean_delta_bh": round(float(np.mean(deltas)), 4) if deltas else 0.0,
        "max_delta_bh": round(float(np.max(deltas)), 4) if deltas else 0.0,
        "n_clamped_at_zero": n_clamped,
    }
    return inst, stats


# --------------------------------------------------------------------------- #
# Target set
# --------------------------------------------------------------------------- #
def build_targets(base):
    """One config per base instance (the scenario has a single arm)."""
    configs = [{
        "id": "%s%s" % (row["id"], SUFFIX), "base_instance_id": row["id"],
        "campus": row["campus"], "size": row["size"], "path": row["path"],
    } for row in base]
    configs.sort(key=lambda c: (c["campus"], c["size"], c["base_instance_id"]))
    return configs


# --------------------------------------------------------------------------- #
# One config x every method (worker process)
# --------------------------------------------------------------------------- #
_SEEDS = []          # set in the parent before the pool is forked


def _run_one(config):
    t0 = time.perf_counter()
    try:
        with open(config["path"]) as f:
            base = json.load(f)
        inst, stats = backdate(base, config["base_instance_id"])
        # The transformed meta.id IS the config id the schedules are scored
        # against (validator check (f)); a mismatch would be a construction bug.
        assert inst["meta"]["id"] == config["id"], (
            "id mismatch: %r != %r" % (inst["meta"]["id"], config["id"]))

        rows_by_method, infeasible = rc.score_instance(inst, _SEEDS)
        common = {
            "id": config["id"], "base_instance_id": config["base_instance_id"],
            "campus": config["campus"], "size": config["size"],
            "transform": "backdate", "backdate_seed": BACKDATE_SEED,
            "max_shift_frac": MAX_SHIFT_FRAC,
            "window_bh": inst["meta"]["window_bh"],
            "u_realized": rc.u_realized(inst),
        }
        common.update(stats)
        rows = [dict(common, **rows_by_method[m]) for m in sorted(rows_by_method)]
        return {"id": config["id"], "ok": True, "rows": rows,
                "infeasible": infeasible, "wall": time.perf_counter() - t0}
    except Exception as e:  # noqa: BLE001 -- report, never kill the pool
        import traceback
        return {"id": config["id"], "ok": False, "rows": [], "infeasible": [],
                "error": "%s: %s" % (type(e).__name__, e),
                "traceback": traceback.format_exc(),
                "wall": time.perf_counter() - t0}


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main(argv=None):
    global _SEEDS
    ap = argparse.ArgumentParser(description="R4.9 corrective-release backdating.")
    ap.add_argument("--workers", type=int, default=rc.DEFAULT_WORKERS,
                    help="parallel config workers (default %d)" % rc.DEFAULT_WORKERS)
    ap.add_argument("--smoke", action="store_true",
                    help="run on 4 released v1.0 replay TEST instances, into "
                         "<out>/smoke/ (proves the path before Eval-B exists)")
    ap.add_argument("--limit", type=int, default=None,
                    help="cap the number of configs (debug)")
    ap.add_argument("--out", default=str(rc.OUT_ROOT),
                    help="results root (default results/r4_robustness)")
    args = ap.parse_args(argv)

    _SEEDS = rc.rl_seeds()
    if not _SEEDS:
        sys.exit("no frozen v2 policy checkpoints under %s" % rc.V2_TRAIN_DIR)

    dest = rc.out_dir(NAME, args.smoke, args.out)
    base = rc.base_rows(args.smoke)
    configs = build_targets(base)
    if args.limit is not None:
        configs = configs[:args.limit]

    rc.print_header("R4.9 release-time robustness (synthetic backdating)",
                    args.smoke, base, _SEEDS, args.workers, dest)
    print("  delta      : U[0, %g x SLA(class)] bh, seed %d, keyed per "
          "(instance, work order)" % (MAX_SHIFT_FRAC, BACKDATE_SEED))
    print("  configs    : %d  ->  %d schedule(s) to score"
          % (len(configs), len(configs) * (len(rc.RULES) + len(_SEEDS))),
          flush=True)

    start_iso = _dt.datetime.now().isoformat(timespec="seconds")
    t_start = time.perf_counter()
    rows, n_errors, n_infeasible = rc.run_pool(configs, _run_one, args.workers)
    elapsed = time.perf_counter() - t_start

    order = rc.method_order(_SEEDS)
    rows.sort(key=lambda r: (r["campus"], r["size"], r["base_instance_id"],
                             order.get(r["method"], 99)))
    out_csv = rc.write_csv(dest / "results.csv", FIELDS, rows)
    print("Wrote %d row(s) -> %s" % (len(rows), out_csv))

    meta = {
        "experiment": "r4_backdate", "protocol": "R4.9",
        "generated": _dt.datetime.now().isoformat(timespec="seconds"),
        "start_time": start_iso, "elapsed_seconds": round(elapsed, 3),
        "smoke": bool(args.smoke),
        "base_set": "released v1.0 replay TEST" if args.smoke else "Eval-B replay",
        "base_instances": len(base), "id_suffix": SUFFIX,
        "backdate_seed": BACKDATE_SEED, "max_shift_frac": MAX_SHIFT_FRAC,
        "delta_key_scheme": "numpy.random.default_rng([424242, uint64(blake2b-8("
                            "'<base_instance_id>|<wo_id>'))]).uniform(0, 0.5*SLA)",
        "sla_bh": {str(k): v for k, v in SLA_BH.items()},
        "preventive_orders_untouched": True, "window_bh_unchanged": True,
        "rules": rc.RULES, "dispatch_seed": rc.SEED,
        "policy_pool": [rc.rl_method(s) for s in _SEEDS],
        "policy_dir": str(rc.V2_TRAIN_DIR),
        "workers": args.workers, "n_configs": len(configs), "n_rows": len(rows),
        "n_errors": n_errors, "n_infeasible": n_infeasible,
        "git_describe": rc.git_describe(),
    }
    print("Wrote %s" % rc.write_json(dest / "meta.json", meta))
    print("Run: %d config(s) in %s (%d errors, %d infeasible rows)."
          % (len(configs), rc.fmt_hms(elapsed), n_errors, n_infeasible))
    return 1 if n_errors else 0


if __name__ == "__main__":
    sys.exit(main())
