#!/usr/bin/env python
"""R4.8 -- capacity-estimator sensitivity, and the realized crew-multiplier table.

The benchmark sizes a trade's crew from the weekly hours that trade actually
booked: ``crew = max(1, ceil(quantile_q(weekly trade hours) / 40))`` on the
training years, with q = 0.95 (``fmwos.calib.build_capacity``).  q is an
estimator choice, not a measurement, so protocol R4.8 asks whether the
conclusions move when it moves.  This runner recomputes the crew table at
q in {0.75, 0.90, 0.95} and re-scores the Eval-B empirical base with ONLY the
technician list rebuilt: the work orders, releases, due dates and window of each
instance are the ones Eval-B ships, so every difference in the results is the
estimator's.

q = 0.95 is the Eval-B baseline itself, so it is NOT re-run here (that would
duplicate rows the final evaluation already owns).  It is still recomputed, for
two purposes: it supplies the crew table behind the disclosure table below, and
it is checked against the technicians the base instances actually carry, which
is a provenance check on the whole rebuild path.

Second output: the realized crew multiplier
-------------------------------------------
Every contended regime scales a trade's crew by a nominal multiplier m through
``max(1, round(k * m))`` (``fmwos.tightness.scale_crew``).  Rounding and the
floor of one technician mean the realized multiplier differs from m, and on
small trades it differs a lot: a two-technician trade at m = 0.6 keeps one
technician, a realized 0.5.  ``realized_multipliers.csv`` discloses, for every
(campus, trade) of the v1.1 capacity table and every m in
{0.5, 0.6, 0.8, 1.0, 1.25}, the nominal and the realized multiplier, plus the
per-campus and portfolio aggregates.  The table is computed with the same
expression the transform uses, so it describes the instances rather than an
idealisation of them.

Capacity tables (cached)
------------------------
The three crew tables are computed once from the corpus v1.1 cleaning
(``io.clean(dominant_sort='stable')``) and cached under
``results/r4_robustness/capacity/calib/capacity_q<qq>.csv``; later runs read the
cache.  The cache is an input artifact, not a result, so it lives outside the
``smoke/`` subdirectory even for a smoke run.  ``--rebuild-calib`` forces the raw
pass (a few minutes; it reads the 1.4 GB CSV).

Methods, scoring and rerun semantics: scripts/r4_robust_common.py.

Outputs (results/r4_robustness/capacity/, or .../smoke/ under --smoke)
----------------------------------------------------------------------
  results.csv              one row per (rebuilt instance x method), carrying
                           u_realized at this q and at the q = 0.95 baseline
  realized_multipliers.csv the nominal-vs-realized crew multiplier disclosure
  meta.json                date, q grid, method list, base set, counts
  calib/capacity_q*.csv    the cached crew tables (always outside smoke/)

Usage
-----
    PYTHONPATH=src python scripts/r4_capacity.py [--workers 12] [--smoke]
                                                 [--rebuild-calib]
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

import pandas as pd  # noqa: E402

import r4_robust_common as rc  # noqa: E402

from fmwos import calib, io  # noqa: E402

NAME = "capacity"
Q_GRID = [0.75, 0.90, 0.95]
Q_BASELINE = 0.95                 # the Eval-B estimator: recomputed, not re-run
Q_SUFFIX = {0.75: "_q75", 0.90: "_q90", 0.95: "_q95"}
CREW_MULTIPLIERS = [0.5, 0.6, 0.8, 1.0, 1.25]     # the disclosure grid

FIELDS = ["id", "base_instance_id", "campus", "size", "crew_q", "n_wos",
          "window_bh", "n_technicians", "n_technicians_base",
          "u_realized", "u_realized_base", "u_shift"] + rc.METRIC_FIELDS

MULT_FIELDS = ["scope", "campus", "trade", "crew_q", "crew_nominal", "m",
               "crew_realized", "realized_multiplier", "capacity_source"]


# --------------------------------------------------------------------------- #
# Crew tables per q (cached; the only path that reads the raw CSV)
# --------------------------------------------------------------------------- #
def _cache_path(calib_dir, q):
    return Path(calib_dir) / ("capacity_q%02d.csv" % int(round(q * 100)))


def capacity_tables(qs, calib_dir, raw=rc.RAW_CSV, rebuild=False):
    """Return {q: capacity DataFrame}, computing and caching what is missing.

    The tables come from the corpus v1.1 cleaning (stable dominant-line sort);
    only the weekly-hours quantile q differs between them, so a difference in
    the rebuilt instances is attributable to the estimator alone.
    """
    calib_dir = Path(calib_dir)
    calib_dir.mkdir(parents=True, exist_ok=True)
    tables, missing = {}, []
    for q in qs:
        p = _cache_path(calib_dir, q)
        if p.exists() and not rebuild:
            tables[q] = pd.read_csv(p)
        else:
            missing.append(q)

    if missing:
        print("  computing crew tables for q=%s from the raw corpus "
              "(v1.1 cleaning; this reads %s) ..."
              % (missing, raw), flush=True)
        t0 = time.perf_counter()
        clean, audit = io.clean(io.load_raw(raw), dominant_sort="stable")
        tmap = calib.trade_merge_map(clean)
        trade_m = calib.apply_trade_merge(clean, tmap)
        print("    cleaned %d work order(s) in %s"
              % (len(clean), rc.fmt_hms(time.perf_counter() - t0)), flush=True)
        for q in missing:
            cap = calib.build_capacity(clean, trade_m, q=q)
            cap = cap[cap["campus"].isin(calib.CAMPUSES)].reset_index(drop=True)
            cap["q"] = q
            cap.to_csv(_cache_path(calib_dir, q), index=False)
            tables[q] = cap
            print("    q=%.2f: %d (campus, trade) row(s), total crew %d"
                  % (q, len(cap), int(cap["crew"].sum())), flush=True)
        rc.write_json(calib_dir / "clean_audit.json", {
            "generated": _dt.datetime.now().isoformat(timespec="seconds"),
            "dominant_sort": "stable", "corpus": "v1.1",
            "crew_hours_per_week": calib.CREW_HOURS,
            "audit": {k: (float(v) if isinstance(v, float) else int(v))
                      for k, v in audit.items()},
        })
        del clean, trade_m
    return tables


def crew_map(table, campus):
    """{trade -> crew count} for one campus of a capacity table."""
    sub = table[table["campus"] == campus]
    return {str(r.trade): int(r.crew) for r in sub.itertuples()}


# --------------------------------------------------------------------------- #
# Transform: rebuild the technician list only
# --------------------------------------------------------------------------- #
def rebuild_technicians(instance, crews, q, suffix):
    """Deep copy whose technicians are re-derived from a crew table.

    The instance's own ``trades`` list is authoritative: a trade keeps the crew
    count the table gives it, and a trade the table does not cover (possible on
    a v1.0 smoke instance, whose corpus differs from v1.1) keeps the count the
    instance shipped, so no work order is ever left without an eligible
    technician.  Technicians are renumbered ``T0..`` grouped by sorted trade,
    the convention ``fmwos.tightness.scale_crew`` uses.  Work orders are
    untouched.  Returns ``(instance, n_fallback_trades)``.
    """
    inst = copy.deepcopy(instance)
    base_counts = {}
    for tech in inst["technicians"]:
        base_counts[tech["trade"]] = base_counts.get(tech["trade"], 0) + 1

    techs, tid, n_fallback = [], 0, 0
    for trade in sorted(inst["trades"]):
        count = crews.get(trade)
        if count is None:
            count = base_counts.get(trade, 1)
            n_fallback += 1
        for _ in range(max(1, int(count))):
            techs.append({"id": "T%d" % tid, "trade": trade})
            tid += 1
    inst["technicians"] = techs

    meta = dict(inst.get("meta", {}))
    meta["crew_q"] = float(q)
    meta["id"] = "%s%s" % (meta.get("id", "inst"), suffix)
    inst["meta"] = meta
    return inst, n_fallback


# --------------------------------------------------------------------------- #
# Realized-vs-nominal crew multiplier disclosure table
# --------------------------------------------------------------------------- #
def _scaled(k, m):
    """The crew a trade of ``k`` technicians keeps at nominal multiplier ``m``.

    Exactly the expression in ``fmwos.tightness.scale_crew``, so the disclosure
    describes the instances the runners actually score."""
    return max(1, int(round(k * m)))


def realized_multiplier_rows(table, source, q):
    """Per-trade, per-campus and portfolio nominal-vs-realized multipliers."""
    rows = []
    for m in CREW_MULTIPLIERS:
        port_nom = port_real = 0
        for campus in sorted(table["campus"].unique()):
            sub = table[table["campus"] == campus].sort_values("trade")
            camp_nom = camp_real = 0
            for r in sub.itertuples():
                k = int(r.crew)
                s = _scaled(k, m)
                camp_nom += k
                camp_real += s
                rows.append({
                    "scope": "trade", "campus": int(campus), "trade": str(r.trade),
                    "crew_q": q, "crew_nominal": k, "m": m, "crew_realized": s,
                    "realized_multiplier": round(s / k, 4),
                    "capacity_source": source,
                })
            rows.append({
                "scope": "campus", "campus": int(campus), "trade": "",
                "crew_q": q, "crew_nominal": camp_nom, "m": m,
                "crew_realized": camp_real,
                "realized_multiplier": round(camp_real / camp_nom, 4)
                if camp_nom else None, "capacity_source": source,
            })
            port_nom += camp_nom
            port_real += camp_real
        rows.append({
            "scope": "portfolio", "campus": "", "trade": "", "crew_q": q,
            "crew_nominal": port_nom, "m": m, "crew_realized": port_real,
            "realized_multiplier": round(port_real / port_nom, 4)
            if port_nom else None, "capacity_source": source,
        })
    return rows


def disclosure_table(calib_dir):
    """(capacity table, source label, q) behind the realized-multiplier table.

    Preference order: the Eval-B calibration written by
    scripts/r4_final_instances.py, then this script's own v1.1 cache, then the
    released v1.0 table.  The chosen source is recorded in every row and in
    meta.json, because the crew counts are what the table is about.
    """
    evalb = rc.ROOT / "results" / "r4_final" / "calib" / "capacity.csv"
    if evalb.exists():
        return pd.read_csv(evalb), "results/r4_final/calib/capacity.csv (v1.1)", 0.95
    cached = _cache_path(calib_dir, Q_BASELINE)
    if cached.exists():
        return (pd.read_csv(cached),
                "results/r4_robustness/capacity/calib/capacity_q95.csv (v1.1)", 0.95)
    v10 = rc.ROOT / "results" / "p1_calib" / "capacity.csv"
    return pd.read_csv(v10), "results/p1_calib/capacity.csv (v1.0)", 0.95


# --------------------------------------------------------------------------- #
# Target set
# --------------------------------------------------------------------------- #
def build_targets(base, tables):
    """One config per (base instance x q), for every q except the baseline."""
    configs = []
    for row in base:
        for q in Q_GRID:
            if q == Q_BASELINE:
                continue                       # the Eval-B run already owns it
            configs.append({
                "id": "%s%s" % (row["id"], Q_SUFFIX[q]),
                "base_instance_id": row["id"], "campus": row["campus"],
                "size": row["size"], "path": row["path"], "q": q,
                "suffix": Q_SUFFIX[q],
                "crews": crew_map(tables[q], row["campus"]),
            })
    configs.sort(key=lambda c: (c["campus"], c["size"], c["base_instance_id"],
                                c["q"]))
    return configs


def baseline_check(base, tables):
    """Does the recomputed q = 0.95 table reproduce the base technician counts?

    A provenance check on the rebuild path, not a gate: a v1.0 smoke instance is
    built from the v1.0 corpus and may legitimately differ from a v1.1 table.
    """
    n_ok = n_diff = 0
    diffs = []
    for row in base:
        with open(row["path"]) as f:
            inst = json.load(f)
        got = {}
        for t in inst["technicians"]:
            got[t["trade"]] = got.get(t["trade"], 0) + 1
        want = {t: c for t, c in crew_map(tables[Q_BASELINE], row["campus"]).items()
                if t in set(inst["trades"])}
        if got == want:
            n_ok += 1
        else:
            n_diff += 1
            if len(diffs) < 5:
                diffs.append({"id": row["id"],
                              "trades_differing": sorted(
                                  t for t in set(got) | set(want)
                                  if got.get(t) != want.get(t))[:8]})
    return {"instances_matching_q95_table": n_ok,
            "instances_differing": n_diff, "examples": diffs}


# --------------------------------------------------------------------------- #
# One config x every method (worker process)
# --------------------------------------------------------------------------- #
_SEEDS = []          # set in the parent before the pool is forked


def _run_one(config):
    t0 = time.perf_counter()
    try:
        with open(config["path"]) as f:
            base = json.load(f)
        inst, n_fallback = rebuild_technicians(base, config["crews"], config["q"],
                                               config["suffix"])
        # The transformed meta.id IS the config id the schedules are scored
        # against (validator check (f)); a mismatch would be a construction bug.
        assert inst["meta"]["id"] == config["id"], (
            "id mismatch: %r != %r" % (inst["meta"]["id"], config["id"]))

        rows_by_method, infeasible = rc.score_instance(inst, _SEEDS)
        u_new, u_base = rc.u_realized(inst), rc.u_realized(base)
        common = {
            "id": config["id"], "base_instance_id": config["base_instance_id"],
            "campus": config["campus"], "size": config["size"],
            "crew_q": config["q"], "n_wos": len(inst["work_orders"]),
            "window_bh": inst["meta"]["window_bh"],
            "n_technicians": len(inst["technicians"]),
            "n_technicians_base": len(base["technicians"]),
            "u_realized": u_new, "u_realized_base": u_base,
            "u_shift": round(u_new - u_base, 6),
        }
        rows = [dict(common, **rows_by_method[m]) for m in sorted(rows_by_method)]
        return {"id": config["id"], "ok": True, "rows": rows,
                "infeasible": infeasible, "n_fallback_trades": n_fallback,
                "wall": time.perf_counter() - t0}
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
    ap = argparse.ArgumentParser(description="R4.8 capacity-estimator sensitivity.")
    ap.add_argument("--workers", type=int, default=rc.DEFAULT_WORKERS,
                    help="parallel config workers (default %d)" % rc.DEFAULT_WORKERS)
    ap.add_argument("--smoke", action="store_true",
                    help="run on 4 released v1.0 replay TEST instances, into "
                         "<out>/smoke/ (proves the path before Eval-B exists)")
    ap.add_argument("--limit", type=int, default=None,
                    help="cap the number of configs (debug)")
    ap.add_argument("--rebuild-calib", action="store_true",
                    help="recompute the cached crew tables from the raw CSV")
    ap.add_argument("--out", default=str(rc.OUT_ROOT),
                    help="results root (default results/r4_robustness)")
    args = ap.parse_args(argv)

    _SEEDS = rc.rl_seeds()
    if not _SEEDS:
        sys.exit("no frozen v2 policy checkpoints under %s" % rc.V2_TRAIN_DIR)

    dest = rc.out_dir(NAME, args.smoke, args.out)
    calib_dir = Path(args.out) / NAME / "calib"      # cache: never inside smoke/
    base = rc.base_rows(args.smoke)

    tables = capacity_tables(Q_GRID, calib_dir, rebuild=args.rebuild_calib)
    configs = build_targets(base, tables)
    if args.limit is not None:
        configs = configs[:args.limit]

    rc.print_header("R4.8 capacity-estimator sensitivity", args.smoke, base,
                    _SEEDS, args.workers, dest)
    print("  crew q     : %s (q=%.2f is the Eval-B baseline and is not re-run)"
          % (Q_GRID, Q_BASELINE))
    print("  total crew : %s"
          % ", ".join("q=%.2f: %d" % (q, int(tables[q]["crew"].sum()))
                      for q in Q_GRID))
    print("  configs    : %d  ->  %d schedule(s) to score"
          % (len(configs), len(configs) * (len(rc.RULES) + len(_SEEDS))),
          flush=True)

    check = baseline_check(base, tables)
    print("  q95 vs base technicians: %d instance(s) match, %d differ"
          % (check["instances_matching_q95_table"], check["instances_differing"]))
    if check["instances_differing"]:
        print("    (expected under --smoke: v1.0 instances carry the v1.0 crew "
              "table, the recomputed one is v1.1)")

    # The disclosure table depends only on a crew table, so it is written even
    # when no config runs.
    cap_tab, source, cap_q = disclosure_table(calib_dir)
    mult_rows = realized_multiplier_rows(cap_tab, source, cap_q)
    mult_csv = rc.write_csv(dest / "realized_multipliers.csv", MULT_FIELDS,
                            mult_rows)
    print("Wrote %d row(s) -> %s  (crew table: %s)"
          % (len(mult_rows), mult_csv, source))
    for r in mult_rows:
        if r["scope"] == "portfolio":
            print("    m=%-5g nominal crew %5d -> realized %5d  "
                  "(realized multiplier %.4f)"
                  % (r["m"], r["crew_nominal"], r["crew_realized"],
                     r["realized_multiplier"]))

    start_iso = _dt.datetime.now().isoformat(timespec="seconds")
    t_start = time.perf_counter()
    rows, n_errors, n_infeasible = rc.run_pool(configs, _run_one, args.workers)
    elapsed = time.perf_counter() - t_start

    order = rc.method_order(_SEEDS)
    rows.sort(key=lambda r: (r["campus"], r["size"], r["base_instance_id"],
                             r["crew_q"], order.get(r["method"], 99)))
    out_csv = rc.write_csv(dest / "results.csv", FIELDS, rows)
    print("Wrote %d row(s) -> %s" % (len(rows), out_csv))

    meta = {
        "experiment": "r4_capacity", "protocol": "R4.8",
        "generated": _dt.datetime.now().isoformat(timespec="seconds"),
        "start_time": start_iso, "elapsed_seconds": round(elapsed, 3),
        "smoke": bool(args.smoke),
        "base_set": "released v1.0 replay TEST" if args.smoke else "Eval-B replay",
        "base_instances": len(base),
        "q_grid": Q_GRID, "q_baseline": Q_BASELINE,
        "q_suffix": {str(k): v for k, v in Q_SUFFIX.items()},
        "crew_hours_per_week": calib.CREW_HOURS,
        "capacity_cache_dir": str(calib_dir),
        "total_crew_per_q": {str(q): int(tables[q]["crew"].sum()) for q in Q_GRID},
        "q95_provenance_check": check,
        "crew_multiplier_grid": CREW_MULTIPLIERS,
        "realized_multiplier_source": source,
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
