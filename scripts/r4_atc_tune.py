#!/usr/bin/env python
"""R4.3 ATC look-ahead tuning: pick one global k on DEVELOPMENT data only.

Protocol (docs/protocol.md, "Revision protocol R4", R4.3): the ATC look-ahead
parameter k is tuned on the training-period empirical-track instances of the
training campuses at the contended crew multipliers, and the single global k with
the lowest pooled mean TWT is frozen before the final evaluation. Ties are broken
toward the literature default k = 2.

Scope (fixed here, never widened by a flag)
-------------------------------------------
  instances : data/processed/instances/index.csv rows with track=='replay' and
              split=='train', campuses {5,9,10,12}, size classes {150,400}
              (the timestamp-ordered empirical track, training period only);
  crew      : crew_multiplier in {0.6, 0.8} via fmwos.tightness.scale_crew
              (the contended development scope);
  grid      : k in {0.5, 1, 2, 3, 5, 10}, run through the SHARED non-delay
              dispatcher (fmwos.pdrs.dispatch) so nothing but k differs;
  score     : fmwos.validator only -- the dispatcher's self-report is never used.

No test-split instance, no held-out campus and no verdict regime is touched, so
the frozen k stays independent of every number the paper reports.

Outputs (results/r4_revision/)
------------------------------
  atc_tuning.csv          one row per (instance x crew_multiplier x k):
                          campus,size,crew_multiplier,instance_id,k,twt
  atc_tuning_summary.md   pooled mean TWT per k, per-campus means, the argmin k,
                          the pre-stated tie rule, and the selected k.

Usage
-----
    PYTHONPATH=src python scripts/r4_atc_tune.py [--workers 12] [--smoke]
                                                 [--smoke-n 40] [--out DIR]

--smoke runs the first --smoke-n instances (default 40) of the deterministic
target order, for timing only; its CSV/summary are written to
<out>/smoke/ so a smoke run can never be mistaken for the tuning result.
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import os
import sys
import time
from pathlib import Path

# One thread per worker: the box is shared and a dispatch is far too small to
# parallelise internally. Set before numpy is imported (fmwos.validator).
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

import multiprocessing as mp  # noqa: E402

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from fmwos import pdrs, tightness      # noqa: E402
from fmwos.validator import validate   # noqa: E402

INST_ROOT = _ROOT / "data" / "processed" / "instances"
INDEX_CSV = INST_ROOT / "index.csv"
OUT_DIR = _ROOT / "results" / "r4_revision"

TRACK = "replay"
SPLIT = "train"
CAMPUSES = [5, 9, 10, 12]
SIZES = [150, 400]
CREW_MULTS = [0.6, 0.8]

# (k, rule key) -- the rule keys are the module-level ATC variants in fmwos.pdrs,
# so the workers pickle a name, not a closure. k = 2 is the literature default
# and keeps the plain 'atc' key it has carried since v1.0.
K_GRID = [(0.5, "atc_k05"), (1.0, "atc_k1"), (2.0, "atc"),
          (3.0, "atc_k3"), (5.0, "atc_k5"), (10.0, "atc_k10")]
K_DEFAULT = 2.0
TIE_TOL = 0.001          # ties broken toward k = 2 within 0.1% of the pooled mean

SEED = 301               # unused by ATC (deterministic), passed for consistency
DEFAULT_WORKERS = 12
DEFAULT_SMOKE_N = 40

FIELDS = ["campus", "size", "crew_multiplier", "instance_id", "k", "twt"]


# --------------------------------------------------------------------------- #
# Target set
# --------------------------------------------------------------------------- #
def _instance_path(row):
    p = row.get("path")
    if p:
        cand = INST_ROOT / p
        if cand.exists():
            return cand
    return (INST_ROOT / ("c%02d" % int(row["campus"])) / str(row["track"])
            / str(row["size_class"]) / (row["id"] + ".json"))


def build_targets(limit=None):
    """Ordered list of one task per instance (deterministic: campus, size, id).

    Each task carries every crew multiplier and every k, so one worker call is
    one instance and the parallel schedule does not depend on the worker count.
    """
    if not INDEX_CSV.exists():
        raise FileNotFoundError("instance index not found: %s" % INDEX_CSV)
    with open(INDEX_CSV, newline="") as f:
        rows = list(csv.DictReader(f))

    targets = []
    for r in rows:
        if str(r.get("track", "")).strip().lower() != TRACK:
            continue
        if str(r.get("split", "")).strip().lower() != SPLIT:
            continue
        try:
            campus = int(r["campus"])
            size = int(r["size_class"])
        except (KeyError, TypeError, ValueError):
            continue
        if campus not in CAMPUSES or size not in SIZES:
            continue
        targets.append({"id": r["id"], "campus": campus, "size": size,
                        "path": str(_instance_path(r))})

    targets.sort(key=lambda t: (t["campus"], t["size"], t["id"]))
    if limit is not None:
        targets = targets[:limit]
    return targets


# --------------------------------------------------------------------------- #
# One instance x every crew multiplier x every k (runs in a worker process)
# --------------------------------------------------------------------------- #
def _run_one(target):
    t0 = time.perf_counter()
    try:
        with open(target["path"]) as f:
            base = json.load(f)

        rows = []
        infeasible = []
        for m in CREW_MULTS:
            inst = tightness.scale_crew(base, m)
            for k, rule in K_GRID:
                sched = pdrs.dispatch(inst, rule, seed=SEED)
                res = validate(inst, sched)
                if not res["feasible"]:
                    infeasible.append({"instance_id": target["id"],
                                       "crew_multiplier": m, "k": k,
                                       "violations": res["violations"][:3]})
                rows.append({
                    "campus": target["campus"], "size": target["size"],
                    "crew_multiplier": m, "instance_id": target["id"],
                    "k": k, "twt": res["metrics"]["WWT"],
                })
        return {"id": target["id"], "ok": True, "rows": rows,
                "infeasible": infeasible, "wall": time.perf_counter() - t0}
    except Exception as e:  # noqa: BLE001 -- report, never kill the pool
        import traceback
        return {"id": target["id"], "ok": False, "rows": [], "infeasible": [],
                "error": "%s: %s" % (type(e).__name__, e),
                "traceback": traceback.format_exc(),
                "wall": time.perf_counter() - t0}


# --------------------------------------------------------------------------- #
# Aggregation
# --------------------------------------------------------------------------- #
def _mean(values):
    values = list(values)
    return sum(values) / len(values) if values else float("nan")


def summarize(rows):
    """Return (pooled, per_campus, argmin_k, selected_k, tie_applied)."""
    pooled = {k: _mean(r["twt"] for r in rows if r["k"] == k)
              for k, _ in K_GRID}
    per_campus = {c: {k: _mean(r["twt"] for r in rows
                               if r["k"] == k and r["campus"] == c)
                      for k, _ in K_GRID}
                  for c in CAMPUSES}

    finite = {k: v for k, v in pooled.items() if v == v}  # drop NaN
    if not finite:
        return pooled, per_campus, None, None, False
    best = min(finite.values())
    # argmin: lowest pooled mean; a numeric tie resolves to the smallest k.
    argmin_k = min(k for k, v in finite.items() if v <= best + 1e-12)

    # Pre-stated tie rule: keep the literature default k = 2 whenever it is
    # within 0.1% of the best pooled mean.
    tie_applied = False
    selected_k = argmin_k
    if K_DEFAULT in finite and finite[K_DEFAULT] <= best * (1.0 + TIE_TOL) + 1e-12:
        tie_applied = argmin_k != K_DEFAULT
        selected_k = K_DEFAULT
    return pooled, per_campus, argmin_k, selected_k, tie_applied


def _fmt(v, nd=3):
    return "-" if v != v else ("%%.%df" % nd) % v


def write_summary(path, rows, targets, elapsed, workers, smoke, n_infeasible):
    pooled, per_campus, argmin_k, selected_k, tie_applied = summarize(rows)
    ks = [k for k, _ in K_GRID]

    L = []
    L.append("# R4.3 ATC look-ahead tuning" + ("  (SMOKE SUBSET)" if smoke else ""))
    L.append("")
    if smoke:
        L.append("**Smoke subset -- NOT the tuning result.** It runs the first "
                 "%d instances of the target order to measure throughput; the "
                 "frozen k comes from the full run only." % len(targets))
        L.append("")
    L.append("Scope: track `%s`, split `%s`, campuses %s, sizes %s, crew "
             "multipliers %s. %d instance(s) x %d crew multiplier(s) x %d k "
             "value(s) = %d schedules, each scored by the independent validator."
             % (TRACK, SPLIT, CAMPUSES, SIZES, CREW_MULTS, len(targets),
                len(CREW_MULTS), len(K_GRID), len(rows)))
    L.append("")
    L.append("Infeasible schedules: %d. Wall clock: %.1f s on %d worker(s)."
             % (n_infeasible, elapsed, workers))
    L.append("")

    L.append("## Pooled mean TWT per k")
    L.append("")
    L.append("| k | mean TWT | vs best |")
    L.append("|---|---|---|")
    finite = [pooled[k] for k in ks if pooled[k] == pooled[k]]
    best = min(finite) if finite else float("nan")
    for k in ks:
        rel = ("%+.3f%%" % (100.0 * (pooled[k] / best - 1.0))
               if (pooled[k] == pooled[k] and best == best and best > 0) else "-")
        L.append("| %g | %s | %s |" % (k, _fmt(pooled[k]), rel))
    L.append("")

    L.append("## Per-campus mean TWT")
    L.append("")
    L.append("| campus | " + " | ".join("k=%g" % k for k in ks) + " |")
    L.append("|---" * (len(ks) + 1) + "|")
    for c in CAMPUSES:
        L.append("| %d | " % c
                 + " | ".join(_fmt(per_campus[c][k]) for k in ks) + " |")
    L.append("")

    L.append("## Selection")
    L.append("")
    L.append("Argmin of the pooled mean TWT: **k = %s**."
             % ("none" if argmin_k is None else "%g" % argmin_k))
    L.append("")
    L.append("Tie rule (pre-stated in protocol R4.3, before any number existed): "
             "the literature default k = %g is retained whenever its pooled mean "
             "TWT is within %.1f%% of the best pooled mean." % (K_DEFAULT, 100 * TIE_TOL))
    L.append("")
    if selected_k is None:
        L.append("Selected k: **none** (no finite pooled mean).")
    elif tie_applied:
        L.append("The tie rule applies: k = %g is within %.1f%% of the argmin, so "
                 "the selected k is **k = %g**." % (K_DEFAULT, 100 * TIE_TOL, selected_k))
    else:
        L.append("The tie rule does not apply; the selected k is **k = %g**."
                 % selected_k)
    L.append("")
    if smoke:
        L.append("(Selection shown for wiring only; the smoke subset does not "
                 "freeze k.)")
        L.append("")

    path.write_text("\n".join(L))
    return pooled, argmin_k, selected_k, tie_applied


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main(argv=None):
    ap = argparse.ArgumentParser(description="R4.3 ATC look-ahead tuning.")
    ap.add_argument("--workers", type=int, default=DEFAULT_WORKERS,
                    help="parallel instance workers (default %d)" % DEFAULT_WORKERS)
    ap.add_argument("--smoke", action="store_true",
                    help="run only the first --smoke-n instances, into <out>/smoke/")
    ap.add_argument("--smoke-n", type=int, default=DEFAULT_SMOKE_N,
                    help="smoke subset size (default %d)" % DEFAULT_SMOKE_N)
    ap.add_argument("--out", default=str(OUT_DIR),
                    help="output root (default results/r4_revision)")
    args = ap.parse_args(argv)

    out_dir = Path(args.out) / "smoke" if args.smoke else Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = out_dir / "atc_tuning.csv"
    out_md = out_dir / "atc_tuning_summary.md"

    targets = build_targets(limit=args.smoke_n if args.smoke else None)
    n_sched = len(targets) * len(CREW_MULTS) * len(K_GRID)
    print("R4.3 ATC tuning%s" % ("  [SMOKE]" if args.smoke else ""))
    print("  scope      : track=%s split=%s campuses=%s sizes=%s"
          % (TRACK, SPLIT, CAMPUSES, SIZES))
    print("  crew mult  : %s" % CREW_MULTS)
    print("  k grid     : %s" % [k for k, _ in K_GRID])
    print("  instances  : %d  ->  %d schedule(s) to score" % (len(targets), n_sched))
    print("  workers    : %d" % args.workers)
    print("  out        : %s" % out_dir)
    if not targets:
        sys.exit("no target instances matched the scope")

    start_iso = _dt.datetime.now().isoformat(timespec="seconds")
    t_start = time.perf_counter()
    rows = []
    n_errors = 0
    n_infeasible = 0
    completed = 0
    ctx = mp.get_context("fork")
    with ctx.Pool(processes=args.workers) as pool:
        for res in pool.imap(_run_one, targets, chunksize=1):
            completed += 1
            if not res["ok"]:
                n_errors += 1
                print("[ERROR] %s: %s" % (res["id"], res.get("error")))
            for it in res["infeasible"]:
                n_infeasible += 1
                print("[INFEASIBLE] id=%s m=%s k=%s :: %s"
                      % (it["instance_id"], it["crew_multiplier"], it["k"],
                         " | ".join(it.get("violations", []))))
            rows.extend(res["rows"])
            if completed % 100 == 0 or completed == len(targets):
                el = time.perf_counter() - t_start
                print("  progress %d/%d  elapsed %.1fs  eta %.1fs"
                      % (completed, len(targets), el,
                         el / completed * (len(targets) - completed)))
    elapsed = time.perf_counter() - t_start

    # Deterministic row order, independent of worker completion order.
    rows.sort(key=lambda r: (r["campus"], r["size"], r["crew_multiplier"],
                             r["instance_id"], r["k"]))
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("Wrote %d row(s) -> %s" % (len(rows), out_csv))

    pooled, argmin_k, selected_k, tie_applied = write_summary(
        out_md, rows, targets, elapsed, args.workers, args.smoke, n_infeasible)
    print("Wrote %s" % out_md)

    print("\nPooled mean TWT per k:")
    for k, _ in K_GRID:
        print("  k=%-4g %s" % (k, _fmt(pooled[k])))
    print("argmin k = %s ; selected k = %s%s"
          % (argmin_k, selected_k, "  (tie rule applied)" if tie_applied else ""))
    print("Run started %s, %d instance(s) in %.1f s (%d errors, %d infeasible)."
          % (start_iso, completed, elapsed, n_errors, n_infeasible))
    return 1 if n_errors else 0


if __name__ == "__main__":
    sys.exit(main())
