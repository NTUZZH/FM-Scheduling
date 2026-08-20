"""R4 robustness-runner tests (R4.7-R4.10) — plain python script (no pytest).

Run:  PYTHONPATH=src python tests/test_r4_robustness.py

Covers the transforms and the corpus surgery the four runners are made of, plus
one end-to-end smoke of the two runners that need no raw-corpus pass:

  1. scripts/r4_sla_scenarios.py transforms: class-selective window scaling
     touches only the named classes and only the due date; the preventive-
     priority variant moves class, weight and due date together; neither
     mutates its input, and both suffix meta.id.
  2. scripts/r4_backdate.py: corrective releases move earlier and never below
     zero, due dates are recomputed from the shifted release, preventive orders
     are untouched, and a work order's delta depends only on (instance id,
     work-order id) — not on the order of the work-order list.
  3. scripts/r4_capacity.py: the technician rebuild follows the crew table,
     falls back to the instance's own count for a trade the table does not
     cover, leaves work orders untouched; the realized-multiplier arithmetic
     matches fmwos.tightness.scale_crew, and the aggregates are consistent.
  4. scripts/r4_pmodel.py: the three processing-time models on a hand-built
     labor-line frame (sum, dominant line, single-line-only subset).
  5. Runner smoke: r4_sla_scenarios.py and r4_backdate.py in --smoke mode to a
     scratch --out; assert the exact CSV columns, every row feasible, and the
     full frozen method set present.

Prints 'ALL R4 ROBUSTNESS TESTS PASSED' and deletes the scratch outputs.
"""

import csv
import os
import shutil
import subprocess
import sys
import tempfile

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

import pandas as pd  # noqa: E402

from fmwos import tightness  # noqa: E402
from fmwos.timeaxis import SLA_BH, WEIGHT  # noqa: E402

import r4_backdate  # noqa: E402
import r4_capacity  # noqa: E402
import r4_pmodel  # noqa: E402
import r4_robust_common as rc  # noqa: E402
import r4_sla_scenarios as r4sla  # noqa: E402

TOL = 1e-9
PY = sys.executable

EXPECTED_METHODS = set(rc.RULES) | {"v2rl%d" % s for s in range(301, 311)}


def _hand_instance():
    """Four work orders over two trades, one preventive, distinct classes."""
    wos = [
        ("W1", "D20", 2.0, 0.0, 1, False),
        ("W2", "D20", 1.0, 4.0, 2, False),
        ("W3", "D30", 3.0, 10.0, 3, True),
        ("W4", "D30", 1.5, 20.0, 4, True),
    ]
    return {
        "meta": {"id": "hand_0001", "campus": 5, "track": "replay",
                 "size_class": 4, "window_bh": 40.0},
        "trades": ["D20", "D30"],
        "technicians": [{"id": "T0", "trade": "D20"},
                        {"id": "T1", "trade": "D20"},
                        {"id": "T2", "trade": "D30"}],
        "work_orders": [
            {"id": i, "trade": tr, "p_bh": p, "release_bh": r,
             "due_bh": round(r + SLA_BH[pr], 4), "priority": pr,
             "weight": WEIGHT[pr], "building": None, "is_pm": pm}
            for i, tr, p, r, pr, pm in wos],
    }


# --------------------------------------------------------------------------- #
# 1. SLA scenarios
# --------------------------------------------------------------------------- #
def test_sla_transforms(failures):
    inst = _hand_instance()
    before = [dict(w) for w in inst["work_orders"]]

    emg = r4sla.scale_sla_by_class(inst, {1: 0.5, 2: 0.5}, "_emg", "emg")
    if emg["meta"]["id"] != "hand_0001_emg":
        failures.append("emg: meta.id not suffixed (%r)" % emg["meta"]["id"])
    if inst["work_orders"] != before:
        failures.append("emg: the source instance was mutated")
    for w0, w1 in zip(before, emg["work_orders"]):
        f = 0.5 if w1["priority"] in (1, 2) else 1.0
        want = round(w0["release_bh"] + f * (w0["due_bh"] - w0["release_bh"]), 4)
        if abs(w1["due_bh"] - want) > TOL:
            failures.append("emg: %s due %.4f != %.4f" % (w1["id"], w1["due_bh"], want))
        for key in ("release_bh", "p_bh", "priority", "weight", "is_pm"):
            if w1[key] != w0[key]:
                failures.append("emg: %s changed %s" % (w1["id"], key))

    rtn = r4sla.scale_sla_by_class(inst, {3: 0.5, 4: 0.5}, "_rtn", "rtn")
    for w0, w1 in zip(before, rtn["work_orders"]):
        f = 0.5 if w1["priority"] in (3, 4) else 1.0
        want = round(w0["release_bh"] + f * (w0["due_bh"] - w0["release_bh"]), 4)
        if abs(w1["due_bh"] - want) > TOL:
            failures.append("rtn: %s due %.4f != %.4f" % (w1["id"], w1["due_bh"], want))

    pmp3 = r4sla.set_pm_priority(inst, 3, "_pmp3", "pmp3")
    if pmp3["meta"]["pm_orders_moved"] != 2:
        failures.append("pmp3: moved %d preventive order(s), expected 2"
                        % pmp3["meta"]["pm_orders_moved"])
    for w0, w1 in zip(before, pmp3["work_orders"]):
        if w0["is_pm"]:
            want_due = round(w0["release_bh"] + SLA_BH[3], 4)
            if (w1["priority"] != 3 or abs(w1["weight"] - WEIGHT[3]) > TOL
                    or abs(w1["due_bh"] - want_due) > TOL):
                failures.append("pmp3: %s not moved to class 3 consistently"
                                % w1["id"])
        elif (w1["priority"] != w0["priority"] or w1["due_bh"] != w0["due_bh"]
              or w1["weight"] != w0["weight"]):
            failures.append("pmp3: corrective order %s changed" % w1["id"])
    print("1. SLA scenario transforms: emg / rtn / pmp3 behave as specified")


# --------------------------------------------------------------------------- #
# 2. Backdating
# --------------------------------------------------------------------------- #
def test_backdate(failures):
    inst = _hand_instance()
    before = {w["id"]: dict(w) for w in inst["work_orders"]}

    bd, stats = r4_backdate.backdate(inst, "hand_0001")
    if bd["meta"]["id"] != "hand_0001_bd":
        failures.append("backdate: meta.id not suffixed (%r)" % bd["meta"]["id"])
    if {w["id"]: dict(w) for w in inst["work_orders"]} != before:
        failures.append("backdate: the source instance was mutated")
    if stats["n_corrective"] != 2 or abs(stats["corrective_share"] - 0.5) > TOL:
        failures.append("backdate: corrective counts wrong (%r)" % stats)

    for w in bd["work_orders"]:
        w0 = before[w["id"]]
        prio = int(w["priority"])
        if w0["is_pm"]:
            if w["release_bh"] != w0["release_bh"] or w["due_bh"] != w0["due_bh"]:
                failures.append("backdate: preventive order %s moved" % w["id"])
            continue
        if w["release_bh"] < -TOL or w["release_bh"] > w0["release_bh"] + TOL:
            failures.append("backdate: %s release %.4f out of [0, %.4f]"
                            % (w["id"], w["release_bh"], w0["release_bh"]))
        delta = w0["release_bh"] - w["release_bh"]
        if delta > 0.5 * SLA_BH[prio] + TOL and w["release_bh"] > TOL:
            failures.append("backdate: %s delta %.4f exceeds 0.5*SLA" % (w["id"], delta))
        if abs(w["due_bh"] - round(w["release_bh"] + SLA_BH[prio], 4)) > TOL:
            failures.append("backdate: %s due not recomputed from the shifted "
                            "release" % w["id"])
        if w["p_bh"] != w0["p_bh"] or w["weight"] != w0["weight"]:
            failures.append("backdate: %s processing time or weight changed" % w["id"])

    # The delta is keyed on (instance id, work-order id): reversing the
    # work-order list must reproduce every release exactly.
    shuffled = _hand_instance()
    shuffled["work_orders"] = list(reversed(shuffled["work_orders"]))
    bd2, _ = r4_backdate.backdate(shuffled, "hand_0001")
    got = {w["id"]: w["release_bh"] for w in bd2["work_orders"]}
    for w in bd["work_orders"]:
        if abs(got[w["id"]] - w["release_bh"]) > TOL:
            failures.append("backdate: %s delta depends on list order" % w["id"])
    # The key is the pair, so the same pair repeats and either half changes the
    # draw.  (Checked on the generator, because a clamped release can coincide
    # at zero for two different draws.)
    def d(inst_id, wo_id):
        return float(r4_backdate._delta_rng(inst_id, wo_id).uniform(0.0, 1.0))

    if abs(d("hand_0001", "W1") - d("hand_0001", "W1")) > TOL:
        failures.append("backdate: the same (instance, work order) pair does not "
                        "reproduce its draw")
    if (abs(d("hand_0001", "W1") - d("hand_0002", "W1")) < TOL
            or abs(d("hand_0001", "W1") - d("hand_0001", "W2")) < TOL):
        failures.append("backdate: the draw does not depend on both halves of "
                        "the key")
    print("2. backdating: clamped, due recomputed, preventive untouched, "
          "deltas keyed per (instance, work order)")


# --------------------------------------------------------------------------- #
# 3. Capacity rebuild + realized multipliers
# --------------------------------------------------------------------------- #
def test_capacity(failures):
    inst = _hand_instance()
    before = [dict(w) for w in inst["work_orders"]]

    # D30 is deliberately absent from the crew table -> fallback to the
    # instance's own count (1 technician).
    out, n_fallback = r4_capacity.rebuild_technicians(inst, {"D20": 5}, 0.75, "_q75")
    counts = {}
    for t in out["technicians"]:
        counts[t["trade"]] = counts.get(t["trade"], 0) + 1
    if counts != {"D20": 5, "D30": 1}:
        failures.append("capacity: rebuilt crew %r, expected {'D20': 5, 'D30': 1}"
                        % counts)
    if n_fallback != 1:
        failures.append("capacity: %d fallback trade(s), expected 1" % n_fallback)
    if out["meta"]["id"] != "hand_0001_q75" or out["meta"]["crew_q"] != 0.75:
        failures.append("capacity: meta not annotated (%r)" % out["meta"])
    if [t["id"] for t in out["technicians"]] != ["T%d" % i for i in range(6)]:
        failures.append("capacity: technician ids are not T0.. in trade order")
    if out["work_orders"] != before or inst["work_orders"] != before:
        failures.append("capacity: work orders changed or source mutated")

    # The disclosure arithmetic must be the transform's own arithmetic.
    for k in range(1, 30):
        for m in r4_capacity.CREW_MULTIPLIERS:
            probe = {"meta": {"id": "p"}, "trades": ["X"],
                     "technicians": [{"id": "T%d" % i, "trade": "X"}
                                     for i in range(k)],
                     "work_orders": []}
            n_scaled = len(tightness.scale_crew(probe, m)["technicians"])
            if r4_capacity._scaled(k, m) != n_scaled:
                failures.append("capacity: realized crew for k=%d m=%g is %d, "
                                "scale_crew gives %d"
                                % (k, m, r4_capacity._scaled(k, m), n_scaled))

    table = pd.DataFrame([{"campus": 5, "trade": "D20", "crew": 2},
                          {"campus": 5, "trade": "D30", "crew": 7},
                          {"campus": 9, "trade": "D20", "crew": 10}])
    rows = r4_capacity.realized_multiplier_rows(table, "unit-test", 0.95)
    if len(rows) != len(r4_capacity.CREW_MULTIPLIERS) * (3 + 2 + 1):
        failures.append("capacity: %d disclosure row(s), expected %d"
                        % (len(rows),
                           len(r4_capacity.CREW_MULTIPLIERS) * 6))
    for m in r4_capacity.CREW_MULTIPLIERS:
        trade_rows = [r for r in rows if r["scope"] == "trade" and r["m"] == m]
        port = [r for r in rows if r["scope"] == "portfolio" and r["m"] == m][0]
        if port["crew_nominal"] != 19:
            failures.append("capacity: portfolio nominal crew %r" % port["crew_nominal"])
        if port["crew_realized"] != sum(r["crew_realized"] for r in trade_rows):
            failures.append("capacity: portfolio realized crew is not the sum of "
                            "the trades at m=%g" % m)
        if abs(port["realized_multiplier"]
               - port["crew_realized"] / port["crew_nominal"]) > 5e-5:
            failures.append("capacity: portfolio multiplier is not realized/nominal")
    small = [r for r in rows if r["scope"] == "trade" and r["trade"] == "D20"
             and r["campus"] == 5 and r["m"] == 0.5][0]
    if small["crew_realized"] != 1 or abs(small["realized_multiplier"] - 0.5) > TOL:
        failures.append("capacity: a 2-technician trade at m=0.5 should keep 1 "
                        "technician (realized 0.5), got %r" % small)
    print("3. capacity: technician rebuild, fallback, and the realized-multiplier "
          "table match the transform's arithmetic")


# --------------------------------------------------------------------------- #
# 4. Processing-time models
# --------------------------------------------------------------------------- #
def _line_frame():
    """Four work orders: a 3-line one, a 2-line tie, and two single-line ones."""
    rows = [
        # (campus, woid, hours, start, end, system, ppm)
        (5, "A", 2.0, "2016-03-01 09:00:00", "2016-03-02 09:00:00", "D20", "UPM"),
        (5, "A", 2.0, "2016-03-01 10:00:00", "2016-03-03 09:00:00", "D30", "UPM"),
        (5, "A", 1.0, "2016-03-01 11:00:00", "2016-03-01 12:00:00", "D40", "UPM"),
        (5, "B", 3.0, "2016-03-04 09:00:00", "2016-03-05 09:00:00", "C10", "PPM"),
        (5, "B", 3.0, "2016-03-04 09:00:00", "2016-03-05 09:00:00", "C30", "PPM"),
        (5, "C", 4.0, "2016-03-06 09:00:00", "2016-03-07 09:00:00", "D20", "UPM"),
        (5, "D", 8.0, "2016-03-07 09:00:00", "2016-03-08 09:00:00", "D30", "PPM"),
        (5, "E", 0.0, "2016-03-08 09:00:00", "2016-03-09 09:00:00", "D30", "UPM"),
    ]
    df = pd.DataFrame(rows, columns=["UniversityID", "WOID", "LaborHours",
                                     "WOStartDate", "WOEndDate", "SystemCode",
                                     "PPM/UPM"])
    df["WOStartDate"] = pd.to_datetime(df["WOStartDate"])
    df["WOEndDate"] = pd.to_datetime(df["WOEndDate"])
    df["SystemCode"] = df["SystemCode"].astype("string")
    df["PPM/UPM"] = df["PPM/UPM"].astype("string")
    df["WOID"] = df["WOID"].astype("string")
    return df


def test_pmodel_cleaning(failures):
    df = _line_frame()
    want = {
        "sum": {"A": 5.0, "B": 6.0, "C": 4.0, "D": 8.0},
        "max": {"A": 2.0, "B": 3.0, "C": 4.0, "D": 8.0},
        "single": {"C": 4.0, "D": 8.0},
    }
    for variant in ("sum", "max", "single"):
        clean, audit = r4_pmodel.clean_variant(df, variant, labor_cap_q=1.0)
        got = dict(zip(clean["WOID"].astype(str), clean["LaborHours"]))
        if got != want[variant]:
            failures.append("pmodel[%s]: hours %r, expected %r"
                            % (variant, got, want[variant]))
        if audit["R3_dropped_zero_hours"] != 1:
            failures.append("pmodel[%s]: R3 dropped %d row(s), expected 1"
                            % (variant, audit["R3_dropped_zero_hours"]))
        # The dominant line supplies the fields; among equal hours the FIRST
        # line in file order wins (the v1.1 stable rule).
        if variant != "single":
            trade_b = clean.loc[clean["WOID"].astype(str) == "B", "trade"].iloc[0]
            if trade_b != "C10":
                failures.append("pmodel[%s]: the equal-hours tie picked %r, not "
                                "the first line C10" % (variant, trade_b))
        if variant == "single" and audit["single_dropped_rows"] != 5:
            failures.append("pmodel[single]: dropped %d line(s), expected 5"
                            % audit["single_dropped_rows"])
        pm = dict(zip(clean["WOID"].astype(str), clean["is_pm"]))
        if pm.get("D") is not True or pm.get("C") is not False:
            failures.append("pmodel[%s]: PM flag wrong (%r)" % (variant, pm))
    # The R4 cap is each model's own p99.5, applied after aggregation.
    clean, audit = r4_pmodel.clean_variant(df, "sum", labor_cap_q=0.5)
    if audit["R4_labor_cap_hours"] != 5.5 or float(clean["LaborHours"].max()) != 5.5:
        failures.append("pmodel: the R4 cap is not the model's own quantile "
                        "(%r)" % audit["R4_labor_cap_hours"])
    print("4. processing-time models: sum / dominant line / single-line subset, "
          "each with its own R4 cap")


# --------------------------------------------------------------------------- #
# 5. Runner smoke (the two runners that need no raw-corpus pass)
# --------------------------------------------------------------------------- #
def _run(script, out, extra):
    cmd = [PY, os.path.join(_ROOT, "scripts", script), "--smoke", "--workers", "2",
           "--out", out] + extra
    env = dict(os.environ, PYTHONPATH=os.path.join(_ROOT, "src"))
    p = subprocess.run(cmd, cwd=_ROOT, env=env, capture_output=True, text=True)
    if p.returncode != 0:
        return None, "%s exited %d: %s" % (script, p.returncode, p.stderr[-500:])
    return p.stdout, None


def _check_csv(path, expected_fields, failures, label):
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames)
        rows = list(reader)
    if fields != expected_fields:
        failures.append("%s: CSV columns %r != %r" % (label, fields, expected_fields))
    if not rows:
        failures.append("%s: no rows" % label)
        return rows
    if any(r["feasible"] != "1" for r in rows):
        failures.append("%s: %d infeasible row(s)"
                        % (label, sum(1 for r in rows if r["feasible"] != "1")))
    methods = {r["method"] for r in rows}
    if methods != EXPECTED_METHODS:
        failures.append("%s: methods %r != %r" % (label, sorted(methods),
                                                  sorted(EXPECTED_METHODS)))
    return rows


def test_runner_smoke(failures, scratch):
    out, err = _run("r4_sla_scenarios.py", scratch, ["--limit", "3"])
    if err:
        failures.append(err)
    else:
        rows = _check_csv(os.path.join(scratch, "sla", "smoke", "results.csv"),
                          r4sla.FIELDS, failures, "sla")
        if rows and {r["scenario"] for r in rows} != {"emg", "rtn", "pmp3"}:
            failures.append("sla: scenarios %r" % sorted({r["scenario"] for r in rows}))
        print("5a. r4_sla_scenarios.py --smoke --limit 3: %d row(s), all feasible"
              % len(rows or []))

    out, err = _run("r4_backdate.py", scratch, ["--limit", "2"])
    if err:
        failures.append(err)
    else:
        rows = _check_csv(os.path.join(scratch, "backdate", "smoke", "results.csv"),
                          r4_backdate.FIELDS, failures, "backdate")
        if rows and not all(float(r["mean_delta_bh"]) > 0 for r in rows):
            failures.append("backdate: an instance drew no backdating at all")
        print("5b. r4_backdate.py --smoke --limit 2: %d row(s), all feasible"
              % len(rows or []))


def main():
    failures = []
    scratch = tempfile.mkdtemp(prefix="r4_robust_")
    try:
        test_sla_transforms(failures)
        test_backdate(failures)
        test_capacity(failures)
        test_pmodel_cleaning(failures)
        test_runner_smoke(failures, scratch)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
        print("cleaned scratch: %s" % scratch)

    if failures:
        print("\nFAILURES:")
        for f in failures:
            print("  - " + f)
        sys.exit(1)
    print("\nALL R4 ROBUSTNESS TESTS PASSED")


if __name__ == "__main__":
    main()
