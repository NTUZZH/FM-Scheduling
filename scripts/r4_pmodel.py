#!/usr/bin/env python
"""R4.7 -- processing-time models: how a work order's hours are read off its
labor lines, and whether the method ranking depends on that reading.

31% of the cleaned work orders are recorded across several labor lines.  Rule R7
turns those lines into one work order, and the benchmark's default takes the
processing time to be the SUM of the line hours: the lines are read as one crew's
booked work.  Two other readings are defensible, and protocol R4.7 requires all
three to be compared:

  sum     p_bh = sum of the order's line hours          (corpus v1.1 default)
  max     p_bh = the dominant line's OWN hours          (one visit, one line)
  single  multi-line orders are dropped entirely        (the unambiguous subset)

This runner does NOT transform released instances, because the reading changes
the corpus, not an instance: a different p_bh changes the R4 outlier cap, the
weekly trade hours behind every crew size, and (for the single-line model) which
work orders exist at all.  It therefore REBUILDS a mini-corpus per model, from
the raw file, on the SAME anchors as the Eval-B empirical base, and recalibrates
capacity per model.  The cascade is the point, and it is disclosed in
calib_summary.csv.

Alignment across the three models
---------------------------------
The three corpora share the anchor list (campus, size, window start), so for the
sum and max models an anchor yields the same first-N work orders with different
processing times, and the instances are paired.  The single-line model has a
smaller work-order population, so the SAME anchor selects a DIFFERENT set of N
orders reaching further into the campus's stream, with a different window
length.  That is inherent to the model, not a defect: it is what dropping the
multi-line orders does.  The index column ``wo_set_equals_sum`` records, per
instance, whether its work-order set matches the sum model's at the same anchor,
and an anchor with too few remaining orders is skipped and counted in meta.json.

The cleaning is re-implemented here (:func:`clean_variant`) because
``fmwos.io.clean`` writes the summed hours back unconditionally and the R4.7
variants are exactly a change to that write-back; ``fmwos`` is not modified.
Everything else -- R2, R3, the stable dominant-line sort, the R4 cap at the
p99.5 of the model's own aggregated hours, R6, the PM flag -- is line-for-line
the same, and every build asserts that the sum variant reproduces
``io.clean(dominant_sort='stable')`` exactly, so the duplication cannot drift
silently.

Nothing is imported from scripts/r4_final_instances.py: its work is anchor
SELECTION (seed 401, overlap rejection), and this script needs the anchors it
already chose, which it reads from ``index_r4.csv``.  The instances themselves
are built through ``fmwos.instances`` and ``fmwos.calib``, the same two modules
the Eval-B builder and scripts/p1_instances.py use, so the three mini-corpora
are built by the benchmark's own machinery.

Methods, scoring and rerun semantics: scripts/r4_robust_common.py.

Outputs (results/r4_robustness/pmodel/, or .../smoke/ under --smoke)
--------------------------------------------------------------------
  results.csv        one row per (rebuilt instance x method)
  instances/<model>/ the rebuilt instances + index_pmodel.csv + build_record.json
  calib_summary.csv  per model: R4 cap, work orders, total technicians, p_bh
  calib/<model>/     the per-model priority mapping + capacity tables (cached
                     outside smoke/, they are inputs rather than results)
  meta.json          date, models, method list, anchor set, counts

Usage
-----
    PYTHONPATH=src python scripts/r4_pmodel.py [--workers 12] [--smoke]
                                               [--rebuild]
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import r4_robust_common as rc  # noqa: E402

from fmwos import calib, instances, io  # noqa: E402
from fmwos import timeaxis as ta        # noqa: E402

NAME = "pmodel"
# (model, meta.id suffix)
VARIANTS = [("sum", "_psum"), ("max", "_pmax"), ("single", "_pone")]
_VARIANT_ORDER = {v: i for i, (v, _s) in enumerate(VARIANTS)}
CREW_Q = calib.CREW_Q          # capacity is recalibrated per model at the same q
FIT_END = calib.TRAIN_END      # corpus v1.1: priority mapping fit on train years
LABOR_CAP_Q = 0.995            # R4, applied to each model's own aggregated hours

FIELDS = ["id", "base_instance_id", "campus", "size", "p_model", "n_wos",
          "window_bh", "n_technicians", "u_realized", "wo_set_equals_sum",
          "r4_labor_cap_hours"] + rc.METRIC_FIELDS

INDEX_FIELDS = ["id", "base_instance_id", "p_model", "campus", "size_class",
                "n_wos", "window_start", "window_bh", "u_realized",
                "wo_set_equals_sum", "path"]

SUMMARY_FIELDS = ["p_model", "scope", "campus", "work_orders",
                  "r4_labor_cap_hours", "pm_share", "n_trades",
                  "total_technicians", "mean_p_bh", "median_p_bh"]


# --------------------------------------------------------------------------- #
# Cleaning, once per processing-time model
# --------------------------------------------------------------------------- #
def clean_variant(df, variant, labor_cap_q=LABOR_CAP_Q):
    """``fmwos.io.clean(dominant_sort='stable')`` with the model's aggregation.

    R2, R3, the stable dominant-line pick, R4 and R6 are exactly io.clean's; the
    single difference is what a work order's LaborHours becomes:

      sum     the summed line hours are written back      (io.clean's behaviour)
      max     the dominant line keeps its own hours       (no write-back)
      single  every multi-line work order is dropped BEFORE R7, so a work order
              is one line and no aggregation applies

    The R4 cap is the p99.5 of the model's OWN aggregated hours, so each model
    caps at its own value.  Returns ``(clean_df, audit)``.
    """
    if variant not in {v for v, _s in VARIANTS}:
        raise ValueError("unknown processing-time model %r" % variant)
    audit = {"variant": variant, "rows_in": int(len(df))}

    m2 = df["WOID"].notna() & df["UniversityID"].notna() & df["WOStartDate"].notna()
    audit["R2_dropped_missing_key"] = int((~m2).sum())
    df = df[m2]

    m3 = df["LaborHours"].notna() & (df["LaborHours"] > 0)
    audit["R3_dropped_zero_hours"] = int((~m3).sum())
    df = df[m3].copy()

    # One groupby per transform, exactly as io.clean does it (a groupby object
    # is not reused across column assignments).
    df["_hours_sum"] = df.groupby(["UniversityID", "WOID"], observed=True)[
        "LaborHours"].transform("sum")
    df["_start_min"] = df.groupby(["UniversityID", "WOID"], observed=True)[
        "WOStartDate"].transform("min")
    df["_end_max"] = df.groupby(["UniversityID", "WOID"], observed=True)[
        "WOEndDate"].transform("max")
    df["_n_lines"] = df.groupby(["UniversityID", "WOID"], observed=True)[
        "LaborHours"].transform("size")
    audit["R7_rows_before_dedup"] = int(len(df))
    multi = df["_n_lines"] > 1
    audit["rows_in_multi_line_work_orders"] = int(multi.sum())

    if variant == "single":
        # The single-line model drops multi-line work orders ENTIRELY, and it
        # does so before R7, so those orders never enter the corpus (their
        # hours are not redistributed anywhere).
        df = df[~multi].copy()
        audit["single_dropped_rows"] = int(multi.sum())

    ordered = df.sort_index().sort_values(
        ["LaborHours"], ascending=False, kind="stable")
    df = ordered.drop_duplicates(subset=["UniversityID", "WOID"], keep="first")
    if variant == "sum":
        df["LaborHours"] = df["_hours_sum"]      # the write-back the models differ on
    df["WOStartDate"] = df["_start_min"]
    df["WOEndDate"] = df["_end_max"]
    df = df.drop(columns=["_hours_sum", "_start_min", "_end_max", "_n_lines"]
                 ).sort_index()
    audit["R7_work_orders_after_dedup"] = int(len(df))

    cap = float(df["LaborHours"].quantile(labor_cap_q))
    audit["R4_labor_cap_hours"] = cap
    audit["R4_rows_capped"] = int((df["LaborHours"] > cap).sum())
    df["LaborHours"] = df["LaborHours"].clip(upper=cap)

    df["trade"] = df["SystemCode"].fillna("UNK").str.strip().str.upper()
    df.loc[df["trade"] == "", "trade"] = "UNK"
    df["is_pm"] = df["PPM/UPM"].str.upper().eq("PPM")
    audit["rows_out"] = int(len(df))
    audit["pm_share"] = float(df["is_pm"].mean())
    audit["mean_p_bh"] = float(df["LaborHours"].mean())
    audit["median_p_bh"] = float(df["LaborHours"].median())
    return df, audit


# --------------------------------------------------------------------------- #
# Mini-corpus construction on the Eval-B anchors
# --------------------------------------------------------------------------- #
def _anchor_list(base):
    """The anchors the mini-corpora are rebuilt on: (campus, size, window start)."""
    out = []
    for row in base:
        ws = str(row.get("window_start", "")).strip()
        if not ws or ws == "synthetic":
            continue                     # generator cells have no empirical anchor
        out.append({"base_instance_id": row["id"], "campus": row["campus"],
                    "size": row["size"], "window_start": ws})
    out.sort(key=lambda a: (a["campus"], a["size"], a["base_instance_id"]))
    return out


def _build_one_variant(raw, variant, suffix, anchors, inst_dir, calib_dir):
    """Clean, recalibrate and rebuild every anchor for one processing-time model.

    Returns ``(index_rows, summary_rows, audit)``.  An anchor whose campus stream
    no longer holds ``size`` work orders after the anchor (possible for the
    single-line model, whose population is smaller) is skipped and reported.
    """
    t0 = time.perf_counter()
    clean, audit = clean_variant(raw, variant)
    print("    [%s] cleaned %d work order(s), R4 cap %.4f h, pm share %.4f  (%s)"
          % (variant, audit["R7_work_orders_after_dedup"],
             audit["R4_labor_cap_hours"], audit["pm_share"],
             rc.fmt_hms(time.perf_counter() - t0)), flush=True)

    mapping, capacity, _tmap, trade_m = calib.write_calibration(
        clean, Path(calib_dir) / variant, q=CREW_Q, fit_end=FIT_END)
    priority = calib.priority_class_series(clean, mapping)
    print("    [%s] capacity: %d (campus, trade) row(s), %d technician(s) total"
          % (variant, len(capacity), int(capacity["crew"].sum())), flush=True)

    inst_dir = Path(inst_dir) / variant
    inst_dir.mkdir(parents=True, exist_ok=True)
    index_rows, skipped = [], []
    for campus in sorted({a["campus"] for a in anchors}):
        prep = instances.prepare_campus(clean, campus, trade_m, priority)
        trades, techs = instances.technicians_for_campus(capacity, campus)
        for a in [x for x in anchors if x["campus"] == campus]:
            t_anchor = pd.Timestamp(a["window_start"])
            t0_abs = ta.abs_bh(t_anchor)
            probe = instances.probe_window(prep, float(t0_abs), a["size"])
            if probe is None:
                skipped.append(dict(a))       # < size work orders left in the stream
                continue
            lo, hi, window_bh = probe
            inst_id = "%s%s" % (a["base_instance_id"], suffix)
            inst = instances.build_instance(
                prep, t_anchor, float(t0_abs), lo, hi, window_bh, a["size"],
                inst_id, campus, trades, techs)
            inst["meta"]["p_model"] = variant
            inst["meta"]["base_instance_id"] = a["base_instance_id"]
            inst["meta"]["r4_labor_cap_hours"] = round(
                float(audit["R4_labor_cap_hours"]), 4)
            path = inst_dir / (inst_id + ".json")
            tmp = path.with_suffix(".json.tmp")
            with open(tmp, "w") as f:
                json.dump(inst, f, separators=(",", ":"))
            tmp.replace(path)
            index_rows.append({
                "id": inst_id, "base_instance_id": a["base_instance_id"],
                "p_model": variant, "campus": campus, "size_class": a["size"],
                "n_wos": len(inst["work_orders"]),
                "window_start": a["window_start"],
                "window_bh": inst["meta"]["window_bh"],
                "u_realized": rc.u_realized(inst),
                "wo_set_equals_sum": "",     # filled once every model is built
                "path": str(path),
                "_wo_ids": tuple(w["id"] for w in inst["work_orders"]),
            })
    audit["anchors"] = len(anchors)
    audit["instances_built"] = len(index_rows)
    audit["anchors_skipped"] = skipped
    print("    [%s] built %d/%d anchor instance(s)%s"
          % (variant, len(index_rows), len(anchors),
             "" if not skipped else "  (%d skipped: too few work orders left)"
             % len(skipped)), flush=True)

    summary = _summary_rows(variant, clean, capacity, audit)
    del clean, trade_m, priority
    return index_rows, summary, audit


def _summary_rows(variant, clean, capacity, audit):
    """Per-model calibration summary: the R4 cap and the crew it implies."""
    rows = [{
        "p_model": variant, "scope": "all", "campus": "",
        "work_orders": int(audit["R7_work_orders_after_dedup"]),
        "r4_labor_cap_hours": round(float(audit["R4_labor_cap_hours"]), 4),
        "pm_share": round(float(audit["pm_share"]), 6),
        "n_trades": int(len(capacity)),
        "total_technicians": int(capacity["crew"].sum()),
        "mean_p_bh": round(float(audit["mean_p_bh"]), 4),
        "median_p_bh": round(float(audit["median_p_bh"]), 4),
    }]
    campus_col = clean["UniversityID"].astype("int64")
    for campus in calib.CAMPUSES:
        sub = clean[campus_col == campus]
        cap = capacity[capacity["campus"] == campus]
        rows.append({
            "p_model": variant, "scope": "campus", "campus": campus,
            "work_orders": int(len(sub)),
            "r4_labor_cap_hours": round(float(audit["R4_labor_cap_hours"]), 4),
            "pm_share": round(float(sub["is_pm"].mean()), 6) if len(sub) else 0.0,
            "n_trades": int(len(cap)),
            "total_technicians": int(cap["crew"].sum()),
            "mean_p_bh": round(float(sub["LaborHours"].mean()), 4) if len(sub) else 0.0,
            "median_p_bh": round(float(sub["LaborHours"].median()), 4)
            if len(sub) else 0.0,
        })
    return rows


def _same_work_orders(a, b):
    """Do two cleaned frames hold the same work orders with the same fields?

    Compared on the index (the raw row that survived R7), the processing time
    and the two derived fields the instance builder reads.  ``is_pm`` and
    ``trade`` are nullable pandas dtypes, so they are compared as objects with
    missing values mapped to None rather than through a NA-propagating ``==``.
    """
    if len(a) != len(b) or not a.index.equals(b.index):
        return False
    if not bool(np.allclose(a["LaborHours"].to_numpy(dtype="float64"),
                            b["LaborHours"].to_numpy(dtype="float64"), atol=1e-9)):
        return False
    for col in ("trade", "is_pm"):
        x = a[col].astype(object).where(a[col].notna(), None).to_numpy()
        y = b[col].astype(object).where(b[col].notna(), None).to_numpy()
        if not bool((x == y).all()):
            return False
    return True


def build_corpora(anchors, inst_dir, calib_dir, raw=rc.RAW_CSV, verify_sum=True):
    """Build all three mini-corpora from one raw pass. Returns the build record."""
    print("  loading the raw corpus (%s) ..." % raw, flush=True)
    t0 = time.perf_counter()
    raw_df = io.load_raw(raw)
    print("  raw rows: %d  (%s)" % (len(raw_df), rc.fmt_hms(time.perf_counter() - t0)),
          flush=True)

    if verify_sum:
        # The sum model must reproduce fmwos.io.clean's v1.1 output exactly; this
        # is the guard on the re-implemented cleaning above.
        mine, _ = clean_variant(raw_df, "sum")
        theirs, _ = io.clean(raw_df, dominant_sort="stable")
        same = _same_work_orders(mine, theirs)
        print("  sum-model equals fmwos.io.clean(dominant_sort='stable'): %s"
              % same, flush=True)
        if not same:
            raise SystemExit("the sum model does not reproduce io.clean -- the "
                             "re-implemented cleaning has drifted")
        del mine, theirs

    per_variant, summary, audits = {}, [], {}
    for variant, suffix in VARIANTS:
        idx_rows, summ, audit = _build_one_variant(
            raw_df, variant, suffix, anchors, inst_dir, calib_dir)
        per_variant[variant] = idx_rows
        summary.extend(summ)
        audits[variant] = audit
    del raw_df

    # Alignment: does an anchor's work-order set match the sum model's?
    sum_sets = {r["base_instance_id"]: r["_wo_ids"] for r in per_variant["sum"]}
    index_rows = []
    for variant, _suffix in VARIANTS:
        for r in per_variant[variant]:
            ref = sum_sets.get(r["base_instance_id"])
            r["wo_set_equals_sum"] = int(ref is not None and r["_wo_ids"] == ref)
            r.pop("_wo_ids")
            index_rows.append(r)
    index_rows.sort(key=lambda r: (r["campus"], r["size_class"],
                                   r["base_instance_id"],
                                   _VARIANT_ORDER[r["p_model"]]))
    return {"index_rows": index_rows, "summary_rows": summary, "audits": audits}


def load_build_record(inst_dir, anchors):
    """Reuse a previous build when it covers exactly these anchors and its files
    are all on disk; otherwise return None so the corpus is rebuilt."""
    rec_path = Path(inst_dir) / "build_record.json"
    idx_path = Path(inst_dir) / "index_pmodel.csv"
    if not (rec_path.exists() and idx_path.exists()):
        return None
    with open(rec_path) as f:
        rec = json.load(f)
    want = [(a["base_instance_id"], a["campus"], a["size"], a["window_start"])
            for a in anchors]
    have = [tuple(x) for x in rec.get("anchors", [])]
    if want != have:
        return None
    rows = list(pd.read_csv(idx_path).to_dict("records"))
    if not rows or any(not Path(r["path"]).exists() for r in rows):
        return None
    return {"index_rows": rows, "summary_rows": None, "audits": rec.get("audits", {})}


# --------------------------------------------------------------------------- #
# One rebuilt instance x every method (worker process)
# --------------------------------------------------------------------------- #
_SEEDS = []          # set in the parent before the pool is forked


def _run_one(config):
    t0 = time.perf_counter()
    try:
        with open(config["path"]) as f:
            inst = json.load(f)
        # The rebuilt meta.id IS the config id the schedules are scored against
        # (validator check (f)); a mismatch would be a construction bug.
        assert inst["meta"]["id"] == config["id"], (
            "id mismatch: %r != %r" % (inst["meta"]["id"], config["id"]))

        rows_by_method, infeasible = rc.score_instance(inst, _SEEDS)
        common = {
            "id": config["id"], "base_instance_id": config["base_instance_id"],
            "campus": config["campus"], "size": config["size"],
            "p_model": config["p_model"], "n_wos": len(inst["work_orders"]),
            "window_bh": inst["meta"]["window_bh"],
            "n_technicians": len(inst["technicians"]),
            "u_realized": rc.u_realized(inst),
            "wo_set_equals_sum": config["wo_set_equals_sum"],
            "r4_labor_cap_hours": inst["meta"].get("r4_labor_cap_hours"),
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
    ap = argparse.ArgumentParser(description="R4.7 processing-time models.")
    ap.add_argument("--workers", type=int, default=rc.DEFAULT_WORKERS,
                    help="parallel config workers (default %d)" % rc.DEFAULT_WORKERS)
    ap.add_argument("--smoke", action="store_true",
                    help="rebuild the three mini-corpora on the anchors of 4 "
                         "released v1.0 replay TEST instances, into <out>/smoke/")
    ap.add_argument("--limit", type=int, default=None,
                    help="cap the number of scored instances (debug)")
    ap.add_argument("--rebuild", action="store_true",
                    help="rebuild the mini-corpora even when a build record covers "
                         "these anchors")
    ap.add_argument("--out", default=str(rc.OUT_ROOT),
                    help="results root (default results/r4_robustness)")
    args = ap.parse_args(argv)

    _SEEDS = rc.rl_seeds()
    if not _SEEDS:
        sys.exit("no frozen v2 policy checkpoints under %s" % rc.V2_TRAIN_DIR)

    dest = rc.out_dir(NAME, args.smoke, args.out)
    inst_dir = dest / "instances"
    calib_dir = Path(args.out) / NAME / "calib"      # cache: never inside smoke/
    base = rc.base_rows(args.smoke)
    anchors = _anchor_list(base)
    if not anchors:
        sys.exit("no empirical anchors in the base set (nothing to rebuild)")

    rc.print_header("R4.7 processing-time models (sum / max / single line)",
                    args.smoke, base, _SEEDS, args.workers, dest)
    print("  models     : %s" % ", ".join("%s%s" % (v, s) for v, s in VARIANTS))
    print("  anchors    : %d (campus, size, window start)" % len(anchors),
          flush=True)

    built = None if args.rebuild else load_build_record(inst_dir, anchors)
    if built is None:
        print("  rebuilding the mini-corpora (one raw pass, three models) ...",
              flush=True)
        t_build = time.perf_counter()
        built = build_corpora(anchors, inst_dir, calib_dir)
        rc.write_csv(inst_dir / "index_pmodel.csv", INDEX_FIELDS,
                     built["index_rows"])
        rc.write_csv(dest / "calib_summary.csv", SUMMARY_FIELDS,
                     built["summary_rows"])
        rc.write_json(inst_dir / "build_record.json", {
            "generated": _dt.datetime.now().isoformat(timespec="seconds"),
            "anchors": [[a["base_instance_id"], a["campus"], a["size"],
                         a["window_start"]] for a in anchors],
            "variants": [v for v, _s in VARIANTS],
            "crew_q": CREW_Q, "fit_end": str(FIT_END),
            "labor_cap_q": LABOR_CAP_Q,
            "audits": built["audits"],
            "build_seconds": round(time.perf_counter() - t_build, 3),
        })
        print("  corpora built in %s"
              % rc.fmt_hms(time.perf_counter() - t_build), flush=True)
    else:
        print("  reusing the mini-corpora under %s (--rebuild forces a rebuild)"
              % inst_dir, flush=True)

    configs = [{
        "id": r["id"], "base_instance_id": r["base_instance_id"],
        "campus": int(r["campus"]), "size": int(r["size_class"]),
        "p_model": r["p_model"], "path": r["path"],
        "wo_set_equals_sum": r["wo_set_equals_sum"],
    } for r in built["index_rows"]]
    configs.sort(key=lambda c: (c["campus"], c["size"], c["base_instance_id"],
                                _VARIANT_ORDER[c["p_model"]]))
    if args.limit is not None:
        configs = configs[:args.limit]
    print("  configs    : %d  ->  %d schedule(s) to score"
          % (len(configs), len(configs) * (len(rc.RULES) + len(_SEEDS))),
          flush=True)

    start_iso = _dt.datetime.now().isoformat(timespec="seconds")
    t_start = time.perf_counter()
    rows, n_errors, n_infeasible = rc.run_pool(configs, _run_one, args.workers)
    elapsed = time.perf_counter() - t_start

    order = rc.method_order(_SEEDS)
    rows.sort(key=lambda r: (r["campus"], r["size"], r["base_instance_id"],
                             _VARIANT_ORDER.get(r["p_model"], 99),
                             order.get(r["method"], 99)))
    out_csv = rc.write_csv(dest / "results.csv", FIELDS, rows)
    print("Wrote %d row(s) -> %s" % (len(rows), out_csv))

    audits = built.get("audits") or {}
    meta = {
        "experiment": "r4_pmodel", "protocol": "R4.7",
        "generated": _dt.datetime.now().isoformat(timespec="seconds"),
        "start_time": start_iso, "elapsed_seconds": round(elapsed, 3),
        "smoke": bool(args.smoke),
        "base_set": "released v1.0 replay TEST" if args.smoke else "Eval-B replay",
        "base_instances": len(base), "anchors": len(anchors),
        "p_models": [{"model": v, "suffix": s} for v, s in VARIANTS],
        "crew_q": CREW_Q, "fit_end": str(FIT_END), "labor_cap_q": LABOR_CAP_Q,
        "corpus_cleaning": "v1.1 (stable dominant-line sort), re-implemented in "
                           "this script for the aggregation switch",
        "per_model": {v: {
            "work_orders": a.get("R7_work_orders_after_dedup"),
            "r4_labor_cap_hours": a.get("R4_labor_cap_hours"),
            "pm_share": a.get("pm_share"),
            "mean_p_bh": a.get("mean_p_bh"),
            "instances_built": a.get("instances_built"),
            "anchors_skipped": len(a.get("anchors_skipped", []) or []),
        } for v, a in audits.items()},
        "instances_dir": str(inst_dir),
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
