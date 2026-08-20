#!/usr/bin/env python
"""R4.10 -- service-window and priority-convention scenarios on the Eval-B base.

Protocol R4.10 asks two interpretable scenario families of the empirical base,
beyond the uniform +-50% SLA sweep already reported: what happens when the
service windows of one part of the priority scale are halved, and what happens
under the other common convention for preventive work.  These are scenario
robustness checks, not claims about the contracts any campus actually signed.

Scenarios (three; each a pure transform of one Eval-B replay instance)
----------------------------------------------------------------------
  _emg   emergency focus   : P1 and P2 due windows x0.5, P3 and P4 unchanged;
  _rtn   routine tightening: P3 and P4 due windows x0.5, P1 and P2 unchanged;
  _pmp3  preventive-priority convention: every preventive order moves from
         class 4 to class 3, so its weight (2.0) and its service window
         (80 bh) follow class 3 and its due date is recomputed from its
         release.  Corrective orders are untouched.

``fmwos.sensitivity.scale_sla`` scales EVERY order's window by one factor, so the
class-selective version is written here (:func:`scale_sla_by_class`) with the
same contract: a deep copy, the window scaled about the unchanged release, and a
suffixed ``meta.id`` so a transformed instance never collides with its base.
``fmwos`` itself is untouched.

Endpoint: the method ranking and the equivalence sets per scenario, computed by
scripts/r4_stats.py from the results.csv written here.

Methods, scoring and rerun semantics: scripts/r4_robust_common.py.

Outputs (results/r4_robustness/sla/, or .../sla/smoke/ under --smoke)
--------------------------------------------------------------------
  results.csv  one row per (scenario instance x method)
  meta.json    date, scenario definitions, method list, base set, counts

Usage
-----
    PYTHONPATH=src python scripts/r4_sla_scenarios.py [--workers 12] [--smoke]
"""

from __future__ import annotations

import argparse
import copy
import datetime as _dt
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import r4_robust_common as rc  # noqa: E402

from fmwos.timeaxis import SLA_BH, WEIGHT  # noqa: E402

NAME = "sla"
PM_CLASS = 3               # the preventive-priority convention variant's class
ROUND_BH = 4               # instance builder stores due_bh to 4 decimals

# (scenario, id suffix, {priority class -> window multiplier}, pm -> class or None)
SCENARIOS = [
    ("emg", "_emg", {1: 0.5, 2: 0.5}, None),
    ("rtn", "_rtn", {3: 0.5, 4: 0.5}, None),
    ("pmp3", "_pmp3", {}, PM_CLASS),
]
_SCENARIO_ORDER = {s[0]: i for i, s in enumerate(SCENARIOS)}

FIELDS = ["id", "base_instance_id", "campus", "size", "scenario",
          "sla_mult_p1", "sla_mult_p2", "sla_mult_p3", "sla_mult_p4",
          "pm_priority", "n_wos", "window_bh", "u_realized"] + rc.METRIC_FIELDS


# --------------------------------------------------------------------------- #
# Transforms
# --------------------------------------------------------------------------- #
def scale_sla_by_class(instance, factors, suffix, scenario):
    """Deep copy with the due window of the named priority classes scaled.

    For every work order whose ``priority`` is a key of ``factors``::

        due_bh := release_bh + f * (due_bh - release_bh)

    Releases, priorities, weights and processing times are untouched, and orders
    of any other class keep their window exactly.  This is
    ``fmwos.sensitivity.scale_sla`` restricted to a class subset; the copy
    records ``meta.sla_class_multipliers`` and suffixes ``meta.id``.
    """
    inst = copy.deepcopy(instance)
    for wo in inst["work_orders"]:
        f = factors.get(int(wo["priority"]))
        if f is None:
            continue
        release = float(wo["release_bh"])
        due = float(wo["due_bh"])
        wo["due_bh"] = round(release + float(f) * (due - release), ROUND_BH)
    meta = dict(inst.get("meta", {}))
    meta["scenario"] = scenario
    meta["sla_class_multipliers"] = {str(k): float(v) for k, v in factors.items()}
    meta["id"] = "%s%s" % (meta.get("id", "inst"), suffix)
    inst["meta"] = meta
    return inst


def set_pm_priority(instance, cls, suffix, scenario):
    """Deep copy with every preventive order moved to priority class ``cls``.

    The class carries the convention: the order's weight becomes ``WEIGHT[cls]``
    and its due date is recomputed as ``release_bh + SLA_BH[cls]``, which is how
    the instance builder assigns a due date in the first place.  Corrective
    orders, releases and processing times are untouched.
    """
    inst = copy.deepcopy(instance)
    n_moved = 0
    for wo in inst["work_orders"]:
        if not bool(wo.get("is_pm")):
            continue
        wo["priority"] = int(cls)
        wo["weight"] = float(WEIGHT[int(cls)])
        wo["due_bh"] = round(float(wo["release_bh"]) + SLA_BH[int(cls)], ROUND_BH)
        n_moved += 1
    meta = dict(inst.get("meta", {}))
    meta["scenario"] = scenario
    meta["pm_priority"] = int(cls)
    meta["pm_orders_moved"] = n_moved
    meta["id"] = "%s%s" % (meta.get("id", "inst"), suffix)
    inst["meta"] = meta
    return inst


def transform(instance, config):
    """Apply the config's scenario transform to a freshly loaded base instance."""
    if config["pm_priority"] is not None:
        return set_pm_priority(instance, config["pm_priority"],
                               config["suffix"], config["scenario"])
    return scale_sla_by_class(instance, config["factors"],
                              config["suffix"], config["scenario"])


# --------------------------------------------------------------------------- #
# Target set
# --------------------------------------------------------------------------- #
def build_targets(base):
    """One config per (base instance x scenario), in a deterministic order."""
    configs = []
    for row in base:
        for scenario, suffix, factors, pm_cls in SCENARIOS:
            configs.append({
                "id": "%s%s" % (row["id"], suffix),
                "base_instance_id": row["id"], "campus": row["campus"],
                "size": row["size"], "path": row["path"],
                "scenario": scenario, "suffix": suffix,
                "factors": {int(k): float(v) for k, v in factors.items()},
                "pm_priority": pm_cls,
            })
    configs.sort(key=lambda c: (c["campus"], c["size"], c["base_instance_id"],
                                _SCENARIO_ORDER[c["scenario"]]))
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
        inst = transform(base, config)
        # The transformed meta.id IS the config id the schedules are scored
        # against (validator check (f)); a mismatch would be a construction bug.
        assert inst["meta"]["id"] == config["id"], (
            "id mismatch: %r != %r" % (inst["meta"]["id"], config["id"]))

        rows_by_method, infeasible = rc.score_instance(inst, _SEEDS)
        common = {
            "id": config["id"], "base_instance_id": config["base_instance_id"],
            "campus": config["campus"], "size": config["size"],
            "scenario": config["scenario"],
            "sla_mult_p1": config["factors"].get(1, 1.0),
            "sla_mult_p2": config["factors"].get(2, 1.0),
            "sla_mult_p3": config["factors"].get(3, 1.0),
            "sla_mult_p4": config["factors"].get(4, 1.0),
            "pm_priority": config["pm_priority"],
            "n_wos": len(inst["work_orders"]),
            "window_bh": inst["meta"]["window_bh"],
            "u_realized": rc.u_realized(inst),
        }
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
    ap = argparse.ArgumentParser(description="R4.10 SLA / priority scenarios.")
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

    rc.print_header("R4.10 SLA / priority-convention scenarios", args.smoke,
                    base, _SEEDS, args.workers, dest)
    print("  scenarios  : %s" % ", ".join(s[0] for s in SCENARIOS))
    print("  configs    : %d  ->  %d schedule(s) to score"
          % (len(configs), len(configs) * (len(rc.RULES) + len(_SEEDS))),
          flush=True)

    start_iso = _dt.datetime.now().isoformat(timespec="seconds")
    t_start = time.perf_counter()
    rows, n_errors, n_infeasible = rc.run_pool(configs, _run_one, args.workers)
    elapsed = time.perf_counter() - t_start

    order = rc.method_order(_SEEDS)
    rows.sort(key=lambda r: (r["campus"], r["size"], r["base_instance_id"],
                             _SCENARIO_ORDER.get(r["scenario"], 99),
                             order.get(r["method"], 99)))
    out_csv = rc.write_csv(dest / "results.csv", FIELDS, rows)
    print("Wrote %d row(s) -> %s" % (len(rows), out_csv))

    meta = {
        "experiment": "r4_sla_scenarios", "protocol": "R4.10",
        "generated": _dt.datetime.now().isoformat(timespec="seconds"),
        "start_time": start_iso, "elapsed_seconds": round(elapsed, 3),
        "smoke": bool(args.smoke),
        "base_set": "released v1.0 replay TEST" if args.smoke else "Eval-B replay",
        "base_instances": len(base),
        "scenarios": [{"scenario": s, "suffix": suf,
                       "sla_class_multipliers": {str(k): v for k, v in fac.items()},
                       "pm_priority": pm} for s, suf, fac, pm in SCENARIOS],
        "pm_class_weight": WEIGHT[PM_CLASS], "pm_class_sla_bh": SLA_BH[PM_CLASS],
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
