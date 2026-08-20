"""Rolling CP-SAT tests -- plain python script (no pytest).

Run:  PYTHONPATH=src python tests/test_rolling.py

Asserts, on hand-built fixtures:

  (a) FEASIBILITY: rollcp2's schedule on an arrival-spread instance passes the
      independent fmwos.validator (every WO once, eligibility, release, exact
      duration, no overlap).
  (b) SEQUENCING ADVANTAGE: on a dynamic trap where the non-delay EDD rule
      commits to the wrong order, rollcp2 WWT <= EDD WWT (strictly less here) --
      the dynamic analogue of the static non-delay trap
      (tests/fixtures/tiny_instance.md), won by optimal weighted-tardiness
      re-sequencing of the released queue.
  (b2) IDLE-WAIT ADVANTAGE: two arrivals 0.05 bh apart are batched into ONE
      replan; the incumbent starts the heavier, LATER-released job first, so the
      technician deliberately idles past the earlier-released light job --
      exactly what a non-delay rule cannot do.  Asserts rollcp2 strictly beats
      EDD, the first start is inside the idle gap (> first release), and the
      heavy job precedes the light one (exercises the _WAKE path end-to-end).
  (b3) VISIBILITY ADVANTAGE (R4.6): one technician, a long low-weight job
      released at 0 and a short high-weight PREVENTIVE job released at 4 with a
      tight due date.  At L=0 the planner can only see the long job and starts it
      at once, so the preventive job finishes late; under full visibility the
      preventive job is in the snapshot from bh 0 with its true shifted release,
      the planner idles the technician until 4 and serves it first.  Asserts
      TWT(full) < TWT(0), both schedules feasible, and that no start precedes its
      job's release (the known job must be planned early, never STARTED early).
  (c) tech_available CORRECTNESS: a one-tech snapshot with the tech busy until
      a_u schedules its job to start at >= a_u (the dummy [0, a_u) interval
      works), whereas the same snapshot without tech_available starts at 0.
  (d) cpsat.py REGRESSION: tests/test_baselines.py is run as a subprocess and
      must print 'ALL BASELINE TESTS PASSED' (the tech_available extension must
      not change the static model).

Prints a report and finally 'ALL ROLLING TESTS PASSED'.
"""

import os
import subprocess
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))

from fmwos import cpsat, pdrs                      # noqa: E402
from fmwos.rolling import roll_cpsat               # noqa: E402
from fmwos.validator import validate               # noqa: E402

TOL = 1e-6


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
def _wo(wid, trade, p, r, due, w, prio, is_pm=False):
    return {"id": wid, "trade": trade, "p_bh": float(p), "release_bh": float(r),
            "due_bh": float(due), "priority": int(prio), "weight": float(w),
            "building": None, "is_pm": bool(is_pm)}


def arrival_spread_fixture():
    """Two trades, jobs releasing across time -- a general feasibility probe."""
    return {
        "meta": {"id": "roll_spread", "campus": 5, "track": "replay",
                 "size_class": 50, "window_start": "synthetic",
                 "window_bh": 20.0, "provenance": "R", "seed": None},
        "trades": ["D20", "E10"],
        "technicians": [{"id": "T0", "trade": "D20"},
                        {"id": "T1", "trade": "D20"},
                        {"id": "T2", "trade": "E10"}],
        "work_orders": [
            _wo("A1", "D20", 3.0, 0.0, 8.0, 8.0, 1),
            _wo("A2", "D20", 2.0, 1.0, 24.0, 4.0, 2),
            _wo("A3", "D20", 4.0, 2.5, 9.0, 8.0, 1),
            _wo("A4", "D20", 1.0, 6.0, 171.4, 1.0, 4, is_pm=True),
            _wo("B1", "E10", 5.0, 0.0, 171.4, 1.0, 4, is_pm=True),
            _wo("B2", "E10", 2.0, 1.0, 9.0, 8.0, 1),
            _wo("B3", "E10", 3.0, 3.0, 27.0, 4.0, 2),
            _wo("B4", "E10", 2.0, 7.0, 80.0, 2.0, 3),
        ],
    }


def dynamic_trap_fixture():
    """Single tech; a warm-up job runs while a weighted-tardiness trap builds.

    At t=4 the tech frees to a queue {J1(due6,w1), J2(due7,w1), J3(due8,w100)}
    that must fill the slots [4,6],[6,8],[8,10].  EDD dispatches by due date
    (J1,J2,J3), stranding the heavy J3 in the last slot: tardy by 2 at weight
    100 -> WWT 201.  The weighted-tardiness optimum keeps J3 on time (a slot
    ending <= 8) and pushes a light job last -> WWT 3.  rollcp2 re-solves the
    accumulated queue and finds that optimum (3 << 201).
    """
    return {
        "meta": {"id": "roll_trap", "campus": 5, "track": "replay",
                 "size_class": 50, "window_start": "synthetic",
                 "window_bh": 10.0, "provenance": "R", "seed": None},
        "trades": ["X"],
        "technicians": [{"id": "T0", "trade": "X"}],
        "work_orders": [
            _wo("W",  "X", 4.0, 0.0, 200.0, 1.0, 4),   # warm-up, blocks [0,4]
            _wo("J1", "X", 2.0, 1.0, 6.0,   1.0, 1),
            _wo("J2", "X", 2.0, 2.0, 7.0,   1.0, 1),
            _wo("J3", "X", 2.0, 3.0, 8.0, 100.0, 1),   # heavy: must go first
        ],
    }


def idle_wait_fixture():
    """Single tech; two near-simultaneous arrivals where waiting 0.05 bh wins.

    J_light releases at 5.0 (p=2, w=1, due 20 -- lots of slack); J_heavy
    releases at 5.05 (p=2, w=100, due 7.5 -- tight).  Non-delay EDD must start
    J_light at 5.0 (it is alone in the queue), forcing J_heavy to [7.0, 9.0] --
    tardy 1.5 at weight 100 -> WWT 150.  rollcp2 batches both arrivals
    (0.05 < 0.1 bh) into one replan whose optimum runs J_heavy first; executing
    it requires the tech to deliberately IDLE over [5.0, 5.05) while J_light is
    released and waiting.  Both jobs end on time -> WWT 0.
    """
    return {
        "meta": {"id": "roll_idlewait", "campus": 5, "track": "replay",
                 "size_class": 50, "window_start": "synthetic",
                 "window_bh": 10.0, "provenance": "R", "seed": None},
        "trades": ["X"],
        "technicians": [{"id": "T0", "trade": "X"}],
        "work_orders": [
            _wo("J_light", "X", 2.0, 5.0, 20.0, 1.0, 3),
            _wo("J_heavy", "X", 2.0, 5.05, 7.5, 100.0, 1),
        ],
    }


def visibility_fixture():
    """Single tech; visibility of ONE preventive order is worth 150 weighted units.

    A (p=6, w=1, due 100) is released at bh 0; B is preventive (p=2, w=100,
    due 6.5) and released at bh 4.  Blind (L=0) the planner sees only A at bh 0,
    starts it on [0, 6] and B can only run [6, 8] -- tardy 1.5 at weight 100, so
    TWT = 150.  Under full visibility B is known from bh 0 with release 4, so the
    optimum idles the tech until 4, runs B on [4, 6] (on time) and A on [6, 12]
    (due 100), giving TWT = 0.
    """
    return {
        "meta": {"id": "roll_visibility", "campus": 5, "track": "replay",
                 "size_class": 50, "window_start": "synthetic",
                 "window_bh": 20.0, "provenance": "R", "seed": None},
        "trades": ["X"],
        "technicians": [{"id": "T0", "trade": "X"}],
        "work_orders": [
            _wo("A_long", "X", 6.0, 0.0, 100.0, 1.0, 4),
            _wo("B_pm", "X", 2.0, 4.0, 6.5, 100.0, 2, is_pm=True),
        ],
    }


def wwt(instance, schedule):
    res = validate(instance, schedule)
    return res, res["metrics"]["WWT"]


# --------------------------------------------------------------------------- #
# (a) feasibility
# --------------------------------------------------------------------------- #
def test_feasible(failures):
    print("(a) FEASIBILITY: rollcp2 on an arrival-spread instance")
    inst = arrival_spread_fixture()
    sched = roll_cpsat(inst, budget_s=2.0)
    res, w = wwt(inst, sched)
    print("    method=%s decisions(replans)=%s mean_replan_s=%.4f WWT=%.3f"
          % (sched["method"], sched["decisions"], sched["mean_replan_s"], w))
    if sched["method"] != "rollcp2":
        failures.append("(a) method is %r, expected 'rollcp2'" % sched["method"])
    if "mean_replan_s" not in sched:
        failures.append("(a) schedule missing extra key 'mean_replan_s'")
    if not res["feasible"]:
        failures.append("(a) rollcp2 schedule INFEASIBLE: %s"
                        % "; ".join(res["violations"][:3]))
    else:
        print("    feasible: yes")


# --------------------------------------------------------------------------- #
# (b) idle-wait / sequencing advantage vs EDD
# --------------------------------------------------------------------------- #
def test_beats_edd(failures):
    print("(b) ADVANTAGE: rollcp2 WWT <= EDD WWT on the dynamic trap")
    inst = dynamic_trap_fixture()

    roll = roll_cpsat(inst, budget_s=2.0)
    rres, rw = wwt(inst, roll)
    edd = pdrs.dispatch(inst, "edd", seed=301)
    eres, ew = wwt(inst, edd)

    print("    rollcp2 WWT=%.3f (feasible=%s, replans=%d)  EDD WWT=%.3f"
          % (rw, rres["feasible"], roll["decisions"], ew))
    if not rres["feasible"]:
        failures.append("(b) rollcp2 schedule INFEASIBLE: %s"
                        % "; ".join(rres["violations"][:3]))
    if not eres["feasible"]:
        failures.append("(b) EDD schedule INFEASIBLE (fixture bug)")
    if rw > ew + TOL:
        failures.append("(b) rollcp2 WWT %.3f > EDD WWT %.3f (no advantage)"
                        % (rw, ew))
    elif rw < ew - TOL:
        print("    rollcp2 strictly beats EDD (%.3f < %.3f)" % (rw, ew))
    else:
        print("    rollcp2 ties EDD (%.3f)" % rw)


# --------------------------------------------------------------------------- #
# (b2) deliberate idle-wait via the batched replan (_WAKE path)
# --------------------------------------------------------------------------- #
def test_idle_wait(failures):
    print("(b2) IDLE-WAIT: batched replan makes the tech wait for the heavy job")
    inst = idle_wait_fixture()

    roll = roll_cpsat(inst, budget_s=2.0)
    rres, rw = wwt(inst, roll)
    edd = pdrs.dispatch(inst, "edd", seed=301)
    eres, ew = wwt(inst, edd)

    starts = {a["wo"]: a["start_bh"] for a in roll["assignments"]}
    print("    rollcp2 WWT=%.3f (feasible=%s, replans=%d)  EDD WWT=%.3f"
          % (rw, rres["feasible"], roll["decisions"], ew))
    print("    rollcp2 starts: %s" % {k: round(v, 3) for k, v in starts.items()})
    if not rres["feasible"]:
        failures.append("(b2) rollcp2 schedule INFEASIBLE: %s"
                        % "; ".join(rres["violations"][:3]))
    if not eres["feasible"]:
        failures.append("(b2) EDD schedule INFEASIBLE (fixture bug)")
    if rw >= ew - TOL:
        failures.append("(b2) rollcp2 WWT %.3f does not strictly beat EDD %.3f"
                        % (rw, ew))
    if len(starts) == 2:
        if starts["J_heavy"] >= starts["J_light"]:
            failures.append("(b2) J_heavy (%.3f) does not precede J_light "
                            "(%.3f): no idle-wait advantage realized"
                            % (starts["J_heavy"], starts["J_light"]))
        first = min(starts.values())
        if first <= 5.0 + TOL:
            failures.append("(b2) first start %.3f is at the light job's "
                            "release -- the tech never idled" % first)
        else:
            print("    deliberate idle confirmed: first start %.3f > 5.0" % first)
    else:
        failures.append("(b2) expected 2 assignments, got %d" % len(starts))


# --------------------------------------------------------------------------- #
# (b3) preventive visibility (R4.6)
# --------------------------------------------------------------------------- #
def test_visibility(failures):
    print("(b3) VISIBILITY: full visibility of a preventive order beats L=0")
    inst = visibility_fixture()
    rel = {wo["id"]: wo["release_bh"] for wo in inst["work_orders"]}

    blind = roll_cpsat(inst, budget_s=2.0, visibility_L=0.0)
    bres, bw = wwt(inst, blind)
    seer = roll_cpsat(inst, budget_s=2.0, visibility_L=None)   # None = full
    sres, sw = wwt(inst, seer)

    b_starts = {a["wo"]: a["start_bh"] for a in blind["assignments"]}
    s_starts = {a["wo"]: a["start_bh"] for a in seer["assignments"]}
    print("    L=0    TWT=%.3f (feasible=%s, replans=%d) starts=%s"
          % (bw, bres["feasible"], blind["decisions"],
             {k: round(v, 3) for k, v in b_starts.items()}))
    print("    L=full TWT=%.3f (feasible=%s, replans=%d) starts=%s"
          % (sw, sres["feasible"], seer["decisions"],
             {k: round(v, 3) for k, v in s_starts.items()}))

    for tag, res in (("L=0", bres), ("L=full", sres)):
        if not res["feasible"]:
            failures.append("(b3) %s schedule INFEASIBLE: %s"
                            % (tag, "; ".join(res["violations"][:3])))
    if sw >= bw - TOL:
        failures.append("(b3) visibility bought nothing: TWT(full)=%.3f is not "
                        "< TWT(0)=%.3f" % (sw, bw))
    else:
        print("    visibility advantage: %.3f -> %.3f" % (bw, sw))
    # A known order is plannable but never startable early (validator check (c)
    # covers this too; asserted here directly because it IS the protocol).
    for tag, starts in (("L=0", b_starts), ("L=full", s_starts)):
        for jid, st in starts.items():
            if st < rel[jid] - TOL:
                failures.append("(b3) %s: %s starts at %.3f, before its release "
                                "%.3f" % (tag, jid, st, rel[jid]))
    if len(s_starts) == 2 and s_starts.get("B_pm", 0.0) > s_starts.get("A_long", 0.0):
        failures.append("(b3) L=full did not serve the preventive job first "
                        "(B_pm at %.3f, A_long at %.3f)"
                        % (s_starts["B_pm"], s_starts["A_long"]))


# --------------------------------------------------------------------------- #
# (c) tech_available correctness
# --------------------------------------------------------------------------- #
def test_tech_available(failures):
    print("(c) tech_available: job cannot start before the tech is free")
    a_u = 5.0
    snap = {
        "meta": {"id": "avail_case"},
        "trades": ["X"],
        "technicians": [{"id": "T0", "trade": "X"}],
        "work_orders": [_wo("J", "X", 2.0, 0.0, 100.0, 8.0, 1)],
    }
    with_avail = cpsat.solve(snap, time_limit_s=5.0, workers=2,
                             tech_available={"T0": a_u})
    without = cpsat.solve(snap, time_limit_s=5.0, workers=2)

    s_with = with_avail["assignments"][0]["start_bh"]
    s_without = without["assignments"][0]["start_bh"]
    print("    start WITH tech_available(a_u=%.1f) = %.3f ; WITHOUT = %.3f"
          % (a_u, s_with, s_without))
    if with_avail["status"] not in ("OPTIMAL", "FEASIBLE"):
        failures.append("(c) tech_available solve status %s" % with_avail["status"])
    if s_with < a_u - TOL:
        failures.append("(c) job started at %.3f < tech availability %.3f"
                        % (s_with, a_u))
    if s_without > TOL:
        failures.append("(c) without tech_available the job should start at 0, "
                        "got %.3f" % s_without)
    rr = validate(snap, with_avail)
    if not rr["feasible"]:
        failures.append("(c) tech_available schedule infeasible: %s"
                        % "; ".join(rr["violations"][:3]))


# --------------------------------------------------------------------------- #
# (d) cpsat.py regression
# --------------------------------------------------------------------------- #
def test_baselines_regression(failures):
    print("(d) REGRESSION: tests/test_baselines.py (cpsat.py must be unchanged)")
    env = dict(os.environ)
    env["PYTHONPATH"] = os.path.join(_ROOT, "src")
    proc = subprocess.run(
        [sys.executable, os.path.join(_ROOT, "tests", "test_baselines.py")],
        cwd=_ROOT, env=env, capture_output=True, text=True,
    )
    ok = proc.returncode == 0 and "ALL BASELINE TESTS PASSED" in proc.stdout
    if not ok:
        tail = (proc.stdout or "")[-600:] + (proc.stderr or "")[-600:]
        failures.append("(d) baseline regression FAILED (rc=%d):\n%s"
                        % (proc.returncode, tail))
    else:
        print("    baseline regression: ALL BASELINE TESTS PASSED")


# --------------------------------------------------------------------------- #
def main():
    failures = []
    test_feasible(failures)
    print()
    test_beats_edd(failures)
    print()
    test_idle_wait(failures)
    print()
    test_visibility(failures)
    print()
    test_tech_available(failures)
    print()
    test_baselines_regression(failures)
    print()

    if failures:
        print("FAILURES:")
        for f in failures:
            print("  - " + f)
        sys.exit(1)
    print("ALL ROLLING TESTS PASSED")


if __name__ == "__main__":
    main()
