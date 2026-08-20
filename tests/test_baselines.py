"""Baseline solver tests — plain python script (no pytest).

Run:  PYTHONPATH=src python tests/test_baselines.py

Loads the hand-built fixture (tests/fixtures/tiny_instance.json, optimum derived
in tiny_instance.md), runs every PDR and CP-SAT, checks each schedule with a
MINIMAL inline feasibility checker (deliberately NOT importing fmwos.validator,
so the referee and the test cannot share a bug), and asserts:

  * every schedule is feasible (exactly-once, trade match, release, duration,
    no overlap);
  * CP-SAT proves OPTIMAL and its WWT equals the hand-derived optimum (32);
  * every PDR's WWT is >= CP-SAT's WWT.

A separate single-queue check pins the pick of the two rules whose definition is
easiest to get wrong: WMDD (Kanet & Li 2004) on a hand-built queue where its
choice differs from both EDD's and WSPT's, and LPT on the same queue (longest
p_bh wins).

Prints a rule -> WWT table and finally 'ALL BASELINE TESTS PASSED'.
"""

import json
import os
import random
import sys

# Make ``fmwos`` importable whether or not PYTHONPATH=src is set.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))

from fmwos import cpsat, pdrs  # noqa: E402

FIXTURE = os.path.join(_ROOT, "tests", "fixtures", "tiny_instance.json")
HAND_OPTIMUM = 32.0
RULES = ["edd", "wspt", "atc", "atc_k05", "atc_k1", "atc_k3", "atc_k5",
         "atc_k10", "pfifo", "wmdd", "lpt", "random"]
SEED = 301
TOL = 1e-6

# Single-queue probe (all three jobs released, dispatched at t = 0). It is built
# so the three rules disagree: EDD takes Q1 (due 1), WSPT takes Q2 (w/p = 3),
# WMDD takes Q3 because (1/w) * max(p, due - t) is 10.0 / 16.67 / 2.5, and LPT
# takes Q1 (p_bh 10).
PROBE_QUEUE = [
    {"id": "Q1", "trade": "D20", "p_bh": 10.0, "release_bh": 0.0,
     "due_bh": 1.0, "priority": 4, "weight": 1.0, "is_pm": False},
    {"id": "Q2", "trade": "D20", "p_bh": 1.0, "release_bh": 0.0,
     "due_bh": 50.0, "priority": 4, "weight": 3.0, "is_pm": False},
    {"id": "Q3", "trade": "D20", "p_bh": 4.0, "release_bh": 0.0,
     "due_bh": 20.0, "priority": 2, "weight": 8.0, "is_pm": False},
]
PROBE_EXPECTED = {"edd": "Q1", "wspt": "Q2", "wmdd": "Q3", "lpt": "Q1"}


# --------------------------------------------------------------------------- #
# Minimal, self-contained feasibility check + WWT (re-derived from the spec,
# NOT imported from fmwos.validator).
# --------------------------------------------------------------------------- #
def check_feasible(instance, schedule):
    """Return list of violation strings ([] == feasible)."""
    v = []
    wo_by_id = {w["id"]: w for w in instance["work_orders"]}
    tech_by_id = {t["id"]: t for t in instance["technicians"]}
    assigns = schedule["assignments"]

    # (a) every WO assigned exactly once.
    seen = {}
    for a in assigns:
        seen[a["wo"]] = seen.get(a["wo"], 0) + 1
    for wid in wo_by_id:
        if seen.get(wid, 0) != 1:
            v.append("WO %s assigned %d times (expected 1)" % (wid, seen.get(wid, 0)))
    for wid in seen:
        if wid not in wo_by_id:
            v.append("assignment references unknown WO %s" % wid)

    # (b) eligibility, (c) release, (d) duration.
    for a in assigns:
        wo = wo_by_id.get(a["wo"])
        tech = tech_by_id.get(a["tech"])
        if wo is None or tech is None:
            v.append("assignment %s/%s references missing WO or tech" % (a["wo"], a["tech"]))
            continue
        if tech["trade"] != wo["trade"]:
            v.append("tech %s trade %s ineligible for WO %s trade %s"
                     % (a["tech"], tech["trade"], a["wo"], wo["trade"]))
        if a["start_bh"] < wo["release_bh"] - TOL:
            v.append("WO %s starts %.6f before release %.6f"
                     % (a["wo"], a["start_bh"], wo["release_bh"]))
        if abs((a["end_bh"] - a["start_bh"]) - wo["p_bh"]) > TOL:
            v.append("WO %s duration %.6f != p_bh %.6f"
                     % (a["wo"], a["end_bh"] - a["start_bh"], wo["p_bh"]))

    # (e) no overlap per technician.
    by_tech = {}
    for a in assigns:
        by_tech.setdefault(a["tech"], []).append(a)
    for tid, jobs in by_tech.items():
        jobs = sorted(jobs, key=lambda a: a["start_bh"])
        for prev, cur in zip(jobs, jobs[1:]):
            if cur["start_bh"] < prev["end_bh"] - TOL:
                v.append("tech %s overlap: %s ends %.6f, %s starts %.6f"
                         % (tid, prev["wo"], prev["end_bh"], cur["wo"], cur["start_bh"]))
    return v


def wwt(instance, schedule):
    """Primary objective: sum_j w_j * max(0, end_j - due_j)."""
    wo_by_id = {w["id"]: w for w in instance["work_orders"]}
    total = 0.0
    for a in schedule["assignments"]:
        wo = wo_by_id[a["wo"]]
        total += wo["weight"] * max(0.0, a["end_bh"] - wo["due_bh"])
    return total


def check_picks():
    """Return (failures, picks): each probe rule's pick on PROBE_QUEUE at t = 0."""
    failures = []
    picks = {}
    rng = random.Random(SEED)
    for rule, want in PROBE_EXPECTED.items():
        got = pdrs.get_rule(rule)(list(PROBE_QUEUE), 0.0, rng)["id"]
        picks[rule] = got
        if got != want:
            failures.append("[%s] picked %s on the probe queue, expected %s"
                            % (rule, got, want))
    # The probe is only informative while the four picks are not all the same.
    if len({picks["edd"], picks["wspt"], picks["wmdd"]}) != 3:
        failures.append("probe queue no longer separates EDD, WSPT and WMDD: %s"
                        % picks)
    return failures, picks


def main():
    with open(FIXTURE) as f:
        instance = json.load(f)

    failures = []
    results = {}  # method -> WWT

    # --- single-queue rule picks (WMDD vs EDD vs WSPT; LPT) -----------------
    pick_failures, picks = check_picks()
    failures.extend(pick_failures)

    # --- PDRs ---------------------------------------------------------------
    for rule in RULES:
        sched = pdrs.dispatch(instance, rule, seed=SEED)
        viol = check_feasible(instance, sched)
        if viol:
            failures.append("[%s] infeasible: %s" % (rule, viol[0]))
        results[rule] = wwt(instance, sched)

    # --- CP-SAT (10 s) ------------------------------------------------------
    csched = cpsat.solve(instance, time_limit_s=10.0, workers=8)
    viol = check_feasible(instance, csched)
    if viol:
        failures.append("[cpsat] infeasible: %s" % viol[0])
    cp_wwt = wwt(instance, csched)
    results[csched["method"]] = cp_wwt

    # --- assertions ---------------------------------------------------------
    if csched["status"] != "OPTIMAL":
        failures.append("cpsat status is %s, expected OPTIMAL" % csched["status"])
    if abs(cp_wwt - HAND_OPTIMUM) > TOL:
        failures.append("cpsat WWT %.6f != hand optimum %.1f" % (cp_wwt, HAND_OPTIMUM))
    if csched.get("objective_bh") is None or abs(csched["objective_bh"] - HAND_OPTIMUM) > TOL:
        failures.append("cpsat objective_bh %s != hand optimum %.1f"
                        % (csched.get("objective_bh"), HAND_OPTIMUM))
    for rule in RULES:
        if results[rule] < cp_wwt - TOL:
            failures.append("PDR %s WWT %.6f < cpsat WWT %.6f"
                            % (rule, results[rule], cp_wwt))

    # --- report -------------------------------------------------------------
    print("single-queue probe at t=0 (Q1 p=10 w=1 due=1; Q2 p=1 w=3 due=50; "
          "Q3 p=4 w=8 due=20)")
    for rule in PROBE_EXPECTED:
        print("  %-6s picks %s" % (rule, picks[rule]))
    print()
    print("fixture: %s  (hand-derived optimum WWT = %.1f)" % (instance["meta"]["id"], HAND_OPTIMUM))
    print("-" * 40)
    print("%-12s %10s" % ("method", "WWT"))
    print("-" * 40)
    for rule in RULES:
        print("%-12s %10.3f" % (rule, results[rule]))
    print("%-12s %10.3f   status=%s  bound=%.3f"
          % (csched["method"], cp_wwt, csched["status"], csched["best_bound_bh"]))
    print("-" * 40)

    if failures:
        print("\nFAILURES:")
        for fmsg in failures:
            print("  - " + fmsg)
        sys.exit(1)

    print("\nALL BASELINE TESTS PASSED")


if __name__ == "__main__":
    main()
