#!/usr/bin/env python
"""R4.4 -- build Eval-B, the fresh final test set (spec docs/protocol.md §R4 (design S2)).

Eval-B exists so that every number in the revision's verdict comes from windows
no method has ever been evaluated on. It is built on benchmark corpus v1.1
(protocol R4.2: stable R7 dominant-line sort, priority mapping refit on the
training years only) and it is built BEFORE the method list is frozen.

Two tracks, both written under ``data/processed/instances_r4/``:

  [E] empirical (timestamp-ordered) track -- sampling v2 first-N-releases, the
      same machinery as scripts/p1_instances.py, with fresh anchors:
        * candidates = every weekday 08:00 whose date is >= 2018-01-01 in the
          campus's span, shuffled once with seed 401;
        * an anchor is ACCEPTED only if its window ``[t0, t0 + window_bh]``
          overlaps neither (a) any released v1.0 replay instance window of
          the same campus AND THE SAME SIZE CLASS (every JSON under
          data/processed/instances/<campus>/replay/ is read for its window;
          same-size-class rule per the dated R4 adjustment in
          docs/protocol.md -- the whole-window rule is physically
          unsatisfiable for 400-order windows on four campuses),
          nor (b) an already-accepted Eval-B window of the same
          (campus, size) cell;
        * target 30 per (campus, size) cell, sizes {150, 400}, all six
          campuses; a cell that cannot supply 10 windows is DROPPED and
          disclosed in the printed table.

  [C] generator final cells -- ``generator.generate_window`` over a fixed 80 bh
      window at target utilizations {0.7, 0.9, 1.0, 1.1, 1.3} on the training
      campuses {5, 9, 10, 12}, 15 instances per cell, parameter packs refit on
      the v1.1 cleaned frame. ``arrival_multiplier = u_target /
      base_utilization(params)`` maps a target utilization onto the pack's
      fitted arrival rates. Seeds are ``80000 + cell_index*1000 + i`` with
      ``cell_index = campus_idx*5 + u_idx`` over the sorted campus list, so no
      seed can collide with the v1.0 storm2 corpus (20000/30000 blocks).

Instance ids carry a track marker that cannot collide with a v1.0 id:
``c<CC>_final_<size>_<NNNN>`` for the empirical track and
``c<CC>_gfinal_<uuu>_<NNNN>`` for the generator track, where ``uuu`` is the
target utilization in percent (``070`` = 0.7). Generator instances are filed
under ``<campus>/storm2/u<uuu>/`` because their realized work-order count is
random, so the utilization cell -- not the size -- is the meaningful directory
level.

The instance schema is unchanged; ``meta`` gains three provenance keys
(``split``, ``eval_set``, ``corpus``, plus ``u_target`` on the generator track)
in the same way scripts/p4_dyneval.py stamps its storm2 instances, so an
Eval-B JSON can be identified from the file alone.

Reuse: the anchor helpers are IMPORTED from scripts/p1_instances.py
(``candidate_anchors``, ``overlaps_any``) and the sampling primitives from
``fmwos.instances`` (``prepare_campus``, ``probe_window``, ``build_instance``,
``technicians_for_campus``), so Eval-B windows are cut by exactly the code that
cut the v1.0 windows. Nothing under src/fmwos/ is modified.

Outputs
-------
  results/r4_final/calib/{priority_mapping.csv, capacity.csv}   (v1.1, fit_end=TRAIN_END)
  results/r4_final/gen_params/params_c<K>.json                  (v1.1 packs)
  data/processed/instances_r4/<campus>/<track>/<cell>/*.json
  data/processed/instances_r4/index_r4.csv

Run: PYTHONPATH=src python scripts/r4_final_instances.py
     PYTHONPATH=src python scripts/r4_final_instances.py --smoke   (campus 5 only)
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import p1_instances as p1                    # noqa: E402  (anchor helpers)
from fmwos import calib, generator, instances, io  # noqa: E402
from fmwos import timeaxis as ta             # noqa: E402

RAW = ROOT / "data" / "raw" / "FMUCD.csv"
INST_ROOT_V10 = ROOT / "data" / "processed" / "instances"   # READ-ONLY (v1.0)

# ---- empirical track ------------------------------------------------------- #
ANCHOR_SEED = 401
TEST_START = pd.Timestamp("2018-01-01")
FINAL_SIZES = [150, 400]
TARGET_PER_CELL = 30
MIN_PER_CELL = 10          # below this the cell is dropped and disclosed

# ---- generator track ------------------------------------------------------- #
GEN_CAMPUSES = [5, 9, 10, 12]      # training campuses (verdict scope)
GEN_U_TARGETS = [0.7, 0.9, 1.0, 1.1, 1.3]
GEN_WINDOW_BH = 80.0
GEN_PER_CELL = 15
GEN_SEED_BASE = 80000
GEN_SEED_CELL_STRIDE = 1000

INDEX_COLS = ["id", "campus", "track", "size_class", "split", "n_wos",
              "window_start", "window_bh", "path", "eval_set", "u_realized",
              "u_target"]

T0 = time.time()


def log(msg: str) -> None:
    print(f"[{time.time() - T0:7.1f}s] {msg}", flush=True)


# --------------------------------------------------------------------------- #
# Realized utilization                                                         #
# --------------------------------------------------------------------------- #
def u_realized(inst: dict) -> float:
    """Offered work over capacity on the instance's own window.

    ``sum p_bh / (n_technicians * window_bh)``: every technician supplies one
    business-hour of capacity per business hour, so this is the load the
    instance actually presents. It is the primary explanatory variable of the
    final evaluation (protocol R4.4), which is why it is stored in the index
    rather than recomputed per analysis.
    """
    n_tech = max(1, len(inst["technicians"]))
    window_bh = float(inst["meta"]["window_bh"]) or 1.0
    work = float(sum(float(w["p_bh"]) for w in inst["work_orders"]))
    return work / (n_tech * window_bh)


# --------------------------------------------------------------------------- #
# v1.0 windows (the exclusion set)                                             #
# --------------------------------------------------------------------------- #
def v10_windows_by_campus(
        campuses: list[int]) -> dict[int, dict[int, list[tuple[float, float]]]]:
    """{campus -> {size_class -> [(lo_abs, hi_abs)]}} over the released corpus.

    The instance JSONs, not index.csv, are the authority: the JSON's own
    ``meta`` is what a reader would check. ``window_start`` is a calendar
    timestamp, so it is mapped onto the absolute business-hour axis (the same
    axis the anchors live on) before comparison.

    Windows are keyed by size class because the exclusion rule is
    SAME-SIZE-CLASS only (protocol R4 adjustment, 2026-08-19): the original
    whole-window rule is physically unsatisfiable for 400-order windows on
    campuses 1, 2, 5 and 9, whose test spans the released corpus already
    covers at 68--79% with remaining gaps (median 9--14 bh) far shorter than
    a 400-order window needs (34--72 bh). An Eval-B window therefore must
    miss every released window of ITS OWN size class, and every other Eval-B
    window in its cell.
    """
    out: dict[int, dict[int, list[tuple[float, float]]]] = {
        c: {} for c in campuses}
    for campus in campuses:
        d = INST_ROOT_V10 / f"c{campus:02d}" / "replay"
        files = sorted(d.rglob("*.json"))
        for fp in files:
            with open(fp) as f:
                meta = json.load(f)["meta"]
            lo = float(ta.abs_bh(pd.Timestamp(meta["window_start"])))
            size = int(meta["size_class"])
            out[campus].setdefault(size, []).append(
                (lo, lo + float(meta["window_bh"])))
        log(f"  campus {campus:2d}: {len(files)} released v1.0 replay windows")
    return out


# --------------------------------------------------------------------------- #
# Empirical track                                                              #
# --------------------------------------------------------------------------- #
def build_empirical(clean: pd.DataFrame, capacity: pd.DataFrame,
                    trade_m: pd.Series, priority: pd.Series,
                    campuses: list[int], target: int,
                    excl: dict[int, list[tuple[float, float]]],
                    inst_root: Path) -> tuple[list[dict], list[dict]]:
    """Cut, write and index the Eval-B empirical instances.

    Returns (index_rows, cell_report). One RNG seeded ``ANCHOR_SEED`` is shared
    by all campuses and consumed in sorted campus order, exactly as in
    scripts/p1_instances.py, so the whole corpus is a deterministic function of
    the seed and the campus list.
    """
    rng = np.random.default_rng(ANCHOR_SEED)
    index_rows: list[dict] = []
    report: list[dict] = []

    for campus in campuses:
        prep = instances.prepare_campus(clean, campus, trade_m, priority)
        trades, techs = instances.technicians_for_campus(capacity, campus)
        camp_ts = clean.loc[clean["UniversityID"].astype("int64") == campus,
                            "WOStartDate"]
        anchors = p1.candidate_anchors(camp_ts.min(), camp_ts.max())
        anchors = [a for a in anchors if a >= TEST_START]
        anchor_abs = ta.abs_bh_series(pd.Series(anchors))
        cands = list(zip(anchors, anchor_abs))
        idx = np.arange(len(cands))
        rng.shuffle(idx)                       # single RNG, deterministic order
        cands = [cands[i] for i in idx]

        for size in FINAL_SIZES:
            accepted: list[tuple[float, float]] = []
            built: list[tuple[dict, pd.Timestamp, float]] = []
            n_short = 0                        # anchors with < size WOs left
            n_hit_v10 = 0                      # rejected by a v1.0 window
            n_hit_self = 0                     # rejected by an Eval-B window
            for t0, t0_abs in cands:
                pw = instances.probe_window(prep, float(t0_abs), size)
                if pw is None:
                    n_short += 1
                    continue                   # < size WOs remaining
                lo, hi, window_bh = pw
                w_lo, w_hi = float(t0_abs), float(t0_abs) + window_bh
                if p1.overlaps_any(excl[campus].get(size, []), w_lo, w_hi):
                    n_hit_v10 += 1
                    continue     # touches a released v1.0 window of this size
                if p1.overlaps_any(accepted, w_lo, w_hi):
                    n_hit_self += 1
                    continue                   # touches an accepted Eval-B window
                inst_id = f"c{campus:02d}_final_{size}_{len(built):04d}"
                inst = instances.build_instance(
                    prep, t0, float(t0_abs), lo, hi, window_bh, size,
                    inst_id, campus, trades, techs)
                inst["meta"]["split"] = "test"
                inst["meta"]["eval_set"] = "final"
                inst["meta"]["corpus"] = "v1.1"
                built.append((inst, t0, window_bh))
                accepted.append((w_lo, w_hi))
                if len(accepted) >= target:
                    break

            keep = len(built) >= MIN_PER_CELL
            report.append({
                "campus": campus, "size": size, "track": "replay",
                "candidates": len(cands), "accepted": len(built),
                "target": target, "kept": keep, "short_stream": n_short,
                "rej_v10": n_hit_v10, "rej_self": n_hit_self,
            })
            if not keep:
                log(f"  campus {campus:2d} size {size:3d}: DROPPED "
                    f"({len(built)} < {MIN_PER_CELL} non-overlapping windows)")
                continue

            rel_dir = Path(f"c{campus:02d}") / "replay" / str(size)
            out_dir = inst_root / rel_dir
            out_dir.mkdir(parents=True, exist_ok=True)
            for inst, t0, window_bh in built:
                inst_id = inst["meta"]["id"]
                with open(out_dir / f"{inst_id}.json", "w") as f:
                    json.dump(inst, f, separators=(",", ":"))
                index_rows.append({
                    "id": inst_id,
                    "campus": campus,
                    "track": "replay",
                    "size_class": size,
                    "split": "test",
                    "n_wos": size,
                    "window_start": t0.isoformat(),
                    "window_bh": round(float(window_bh), 4),
                    "path": str(rel_dir / f"{inst_id}.json"),
                    "eval_set": "final",
                    "u_realized": round(u_realized(inst), 6),
                    "u_target": "",
                })
            log(f"  campus {campus:2d} size {size:3d}: accepted {len(built):3d}"
                f"/{target} (rej v1.0 {n_hit_v10}, rej self {n_hit_self}, "
                f"short {n_short})")

    return index_rows, report


# --------------------------------------------------------------------------- #
# Generator track                                                              #
# --------------------------------------------------------------------------- #
def build_generator(clean: pd.DataFrame, campuses: list[int], per_cell: int,
                    inst_root: Path, params_out: Path) -> tuple[list[dict], list[dict]]:
    """Refit the packs on the v1.1 frame, then cut the fixed-window final cells."""
    params_out.mkdir(parents=True, exist_ok=True)
    index_rows: list[dict] = []
    report: list[dict] = []

    for campus_idx, campus in enumerate(campuses):
        params = generator.fit_params(clean, campus,
                                       mapping_fit_end=calib.TRAIN_END)
        with open(params_out / f"params_c{campus}.json", "w") as f:
            json.dump(params, f, indent=2, sort_keys=True)
        u0 = generator.base_utilization(params)
        log(f"  campus {campus:2d}: pack refit on v1.1 "
            f"(n_train={params['n_train_total']:,}, base_utilization={u0:.4f})")

        for u_idx, u_target in enumerate(GEN_U_TARGETS):
            cell_index = campus_idx * len(GEN_U_TARGETS) + u_idx
            arrival_multiplier = float(u_target) / u0 if u0 > 0 else 1.0
            u_tag = f"{int(round(u_target * 100)):03d}"
            rel_dir = Path(f"c{campus:02d}") / "storm2" / f"u{u_tag}"
            out_dir = inst_root / rel_dir
            out_dir.mkdir(parents=True, exist_ok=True)

            us: list[float] = []
            ns: list[int] = []
            for i in range(per_cell):
                seed = GEN_SEED_BASE + cell_index * GEN_SEED_CELL_STRIDE + i
                inst = generator.generate_window(
                    params, window_bh=GEN_WINDOW_BH, seed=seed,
                    arrival_multiplier=arrival_multiplier)
                inst_id = f"c{campus:02d}_gfinal_{u_tag}_{i:04d}"
                inst["meta"]["id"] = inst_id
                inst["meta"]["split"] = "test"
                inst["meta"]["eval_set"] = "final"
                inst["meta"]["corpus"] = "v1.1"
                inst["meta"]["u_target"] = float(u_target)
                with open(out_dir / f"{inst_id}.json", "w") as f:
                    json.dump(inst, f, separators=(",", ":"))
                n_wos = len(inst["work_orders"])
                u = u_realized(inst)
                us.append(u)
                ns.append(n_wos)
                index_rows.append({
                    "id": inst_id,
                    "campus": campus,
                    "track": "storm2",
                    "size_class": n_wos,
                    "split": "test",
                    "n_wos": n_wos,
                    "window_start": "synthetic",
                    "window_bh": round(float(GEN_WINDOW_BH), 4),
                    "path": str(rel_dir / f"{inst_id}.json"),
                    "eval_set": "final",
                    "u_realized": round(u, 6),
                    "u_target": float(u_target),
                })
            report.append({
                "campus": campus, "size": f"u={u_target}", "track": "storm2",
                "candidates": per_cell, "accepted": per_cell,
                "target": per_cell, "kept": True,
                "mean_u": float(np.mean(us)), "mean_n": float(np.mean(ns)),
                "arrival_multiplier": arrival_multiplier,
            })
            log(f"  campus {campus:2d} u={u_target:.1f}: {per_cell} instances "
                f"(mult={arrival_multiplier:.3f}, mean n={np.mean(ns):.1f}, "
                f"mean u_realized={np.mean(us):.3f})")

    return index_rows, report


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #
def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Build the Eval-B final test set.")
    ap.add_argument("--smoke", action="store_true",
                    help="campus 5 only, 5 empirical / 3 generator per cell, "
                         "written to *_smoke roots")
    ap.add_argument("--inst-root", default=None,
                    help="override the instance output root (determinism check)")
    ap.add_argument("--results-root", default=None,
                    help="override the results output root (determinism check)")
    args = ap.parse_args(argv)

    if args.smoke:
        campuses = [5]
        gen_campuses = [5]
        target = 5
        gen_per_cell = 3
        inst_root = ROOT / "data" / "processed" / "instances_r4_smoke"
        results_root = ROOT / "results" / "r4_final_smoke"
    else:
        campuses = list(instances.CAMPUS_SET)
        gen_campuses = list(GEN_CAMPUSES)
        target = TARGET_PER_CELL
        gen_per_cell = GEN_PER_CELL
        inst_root = ROOT / "data" / "processed" / "instances_r4"
        results_root = ROOT / "results" / "r4_final"
    if args.inst_root:
        inst_root = Path(args.inst_root)
    if args.results_root:
        results_root = Path(args.results_root)

    log(f"Eval-B build: campuses {campuses}, empirical target {target}/cell, "
        f"generator campuses {gen_campuses} x {gen_per_cell}/cell")
    log(f"  instances -> {inst_root}")
    log(f"  results   -> {results_root}")

    # ---- corpus v1.1 ------------------------------------------------------- #
    log("loading raw FMUCD ...")
    raw = io.load_raw(RAW)
    log(f"  raw rows {len(raw):,}")
    log("cleaning (corpus v1.1: stable R7 dominant-line sort) ...")
    clean, _audit = io.clean(raw, dominant_sort="stable")
    del raw
    log(f"  clean work orders {len(clean):,}")

    calib_out = results_root / "calib"
    mapping, capacity, _tmap, trade_m = calib.write_calibration(
        clean, calib_out, fit_end=calib.TRAIN_END)
    priority = calib.priority_class_series(clean, mapping)
    log(f"  calibration (fit_end={calib.TRAIN_END}, q={calib.CREW_Q}) "
        f"-> {calib_out}")

    # ---- exclusion set ----------------------------------------------------- #
    log("reading released v1.0 replay windows (exclusion set) ...")
    excl = v10_windows_by_campus(campuses)

    # ---- empirical track --------------------------------------------------- #
    log("cutting Eval-B empirical windows (anchor seed 401) ...")
    emp_rows, emp_report = build_empirical(
        clean, capacity, trade_m, priority, campuses, target, excl, inst_root)

    # ---- generator track --------------------------------------------------- #
    log("fitting v1.1 generator packs + cutting final cells ...")
    gen_rows, gen_report = build_generator(
        clean, gen_campuses, gen_per_cell, inst_root,
        results_root / "gen_params")

    # ---- index -------------------------------------------------------------- #
    inst_root.mkdir(parents=True, exist_ok=True)
    index = pd.DataFrame(emp_rows + gen_rows, columns=INDEX_COLS)
    index_path = inst_root / "index_r4.csv"
    index.to_csv(index_path, index=False)
    log(f"wrote {index_path} ({len(index)} rows)")

    # ---- reports ------------------------------------------------------------ #
    print("\n=== Eval-B empirical track: per-cell acceptance ===")
    print(f"{'campus':>6} {'size':>5} {'anchors':>8} {'accepted':>9} "
          f"{'target':>7} {'kept':>5} {'rej_v1.0':>9} {'rej_self':>9} "
          f"{'short':>7}")
    short_cells = []
    for r in emp_report:
        print(f"{r['campus']:6d} {r['size']:5d} {r['candidates']:8d} "
              f"{r['accepted']:9d} {r['target']:7d} "
              f"{('yes' if r['kept'] else 'NO'):>5} {r['rej_v10']:9d} "
              f"{r['rej_self']:9d} {r['short_stream']:7d}")
        if r["accepted"] < r["target"]:
            short_cells.append(r)
    print(f"empirical instances written: "
          f"{sum(r['accepted'] for r in emp_report if r['kept'])}")

    print("\n=== shortfalls (accepted < target) ===")
    if not short_cells:
        print("  none")
    for r in short_cells:
        state = "kept" if r["kept"] else f"DROPPED (< {MIN_PER_CELL})"
        print(f"  campus {r['campus']:2d} size {r['size']:3d}: "
              f"{r['accepted']}/{r['target']} accepted -- {state}")

    print("\n=== Eval-B generator track: per-cell summary ===")
    print(f"{'campus':>6} {'u_target':>9} {'n_inst':>7} {'arr_mult':>9} "
          f"{'mean_n':>8} {'mean_u_realized':>16}")
    for r in gen_report:
        print(f"{r['campus']:6d} {r['size']:>9} {r['accepted']:7d} "
              f"{r['arrival_multiplier']:9.3f} {r['mean_n']:8.1f} "
              f"{r['mean_u']:16.3f}")
    print(f"generator instances written: "
          f"{sum(r['accepted'] for r in gen_report)}")

    print(f"\ntotal Eval-B instances: {len(index)}")
    log("done")


if __name__ == "__main__":
    main()
