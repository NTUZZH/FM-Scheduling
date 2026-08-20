"""R4.6 visibility-experiment tests -- plain python script (no pytest).

Run:  PYTHONPATH=src python tests/test_r4_visibility.py

Everything here runs on HAND-BUILT tiny instances (the fixture style of
tests/test_rolling.py): the four claims scripts/r4_visibility.py rests on are
properties of the machinery, not of the corpus, so none of them needs a real
instance and the whole file finishes in seconds.

  (i)   RULES ARE CONSTANT IN L.  The runner computes edd/atc/wmdd ONCE at L=0
        and copies the row to the other three levels with
        constant_by_construction = 1.  That is only legitimate if a non-delay
        rule's SCHEDULE is identical at every level, so this asserts equality of
        the full assignment list -- through the env at L in {0, 8, 40, full} and
        against fmwos.pdrs.dispatch -- on a fixture whose preventive orders
        really do become known early (asserted, so the test cannot go vacuous).
  (ii)  atc_la IS FEASIBLE AT EVERY LEVEL, EQUALS atc AT L=0, AND USES THE VIEW.
        The fixture is built so the known-load term flips the pick: at k=2 the
        high-weight job with slack wins, and once a 20 bh preventive order is
        known within the rule's 40 bh window (rho_known = 0.5, k_eff = 1.33) the
        zero-slack job wins instead.  L=8 leaves the order still unknown at the
        decision instant, so it must reproduce L=0 exactly.
  (iii) ROLLING CP-SAT GAINS FROM VISIBILITY.  TWT at L=full <= TWT at L=0 on
        the visibility-advantage fixture of tests/test_rolling.py, which is
        imported rather than copied so the two files can never drift apart.
  (iv)  THE RUNNER'S ID SCHEME PASSES THE VALIDATOR.  A crew-scaled tiny
        instance is scored through scripts/r4_visibility.run_config_methods; the
        emitted rows must carry the _L-suffixed CONFIG id while every schedule
        carries the instance's own meta.id, so validator check (f) passes.  The
        negative control re-validates one schedule with the config id written
        into it and requires check (f) to FAIL, proving the check is real.

Prints a report and finally 'ALL R4.6 VISIBILITY TESTS PASSED'.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "src"))
sys.path.insert(0, os.path.join(_ROOT, "scripts"))
sys.path.insert(0, _HERE)

import r4_visibility as r4v                          # noqa: E402
from fmwos import pdrs, tightness                    # noqa: E402
from fmwos.env import DispatchEnv, known_bh          # noqa: E402
from fmwos.rolling import roll_cpsat                 # noqa: E402
from fmwos.validator import validate                 # noqa: E402
from test_rolling import visibility_fixture          # noqa: E402

TOL = 1e-6
SEED = r4v.SEED


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
def _wo(wid, trade, p, r, due, w, prio, is_pm=False):
    return {"id": wid, "trade": trade, "p_bh": float(p), "release_bh": float(r),
            "due_bh": float(due), "priority": int(prio), "weight": float(w),
            "building": None, "is_pm": bool(is_pm)}


def mixed_fixture(inst_id="vis_mixed"):
    """Two contended trades, five preventive orders released mid-window.

    One technician per trade.  The D20 queue is a weighted-tardiness trap: three
    correctives compete at bh 0, EDD serves the light early-due job first and
    pays 8 weighted units, while ATC and WMDD serve the heavy P1-class job first
    and pay 2.  The rules therefore genuinely disagree and every schedule
    carries tardiness (asserted below: a fixture on which every rule agrees
    would make the constancy claim vacuous).  Every preventive release is
    strictly positive, so at L in {8, 40, full} the env really does push _KNOWN
    events.
    """
    return {
        "meta": {"id": inst_id, "campus": 5, "track": "replay",
                 "size_class": 10, "window_start": "synthetic",
                 "window_bh": 40.0, "provenance": "R", "seed": None},
        "trades": ["D20", "E10"],
        "technicians": [{"id": "T0", "trade": "D20"},
                        {"id": "T1", "trade": "E10"}],
        "work_orders": [
            _wo("C1", "D20", 4.0, 0.0, 5.0, 8.0, 1),
            _wo("C2", "D20", 2.0, 0.0, 4.0, 1.0, 3),
            _wo("C3", "D20", 3.0, 0.0, 12.0, 4.0, 2),
            _wo("P1", "D20", 5.0, 6.0, 171.4, 1.0, 4, is_pm=True),
            _wo("P2", "D20", 1.0, 20.0, 191.4, 1.0, 4, is_pm=True),
            _wo("C4", "E10", 3.0, 0.0, 4.0, 8.0, 1),
            _wo("C5", "E10", 2.0, 1.0, 9.0, 1.0, 3),
            _wo("P3", "E10", 6.0, 5.0, 176.4, 1.0, 4, is_pm=True),
            _wo("P4", "E10", 2.0, 12.0, 183.4, 1.0, 4, is_pm=True),
            _wo("P5", "E10", 4.0, 30.0, 201.4, 1.0, 4, is_pm=True),
        ],
    }


def atc_la_fixture():
    """One technician; a known preventive wave flips the forecast-aware pick.

    At bh 0 the queue holds J_slack (w=4, p=1, due 2 -> slack 1) and J_tight
    (w=2, p=1, due 1 -> slack 0); pbar = 1.  ATC at k = 2 scores
    4*exp(-1/2) = 2.43 against 2.00 and dispatches J_slack first, so J_tight
    ends at 2 against a due date of 1 (TWT = 2).  P_wave is a 20 bh preventive
    order releasing at bh 30: known within the rule's 40 bh window it gives
    rho_known = 20 / (40 * 1) = 0.5 and k_eff = 2 / 1.5 = 1.33, at which
    4*exp(-1/1.33) = 1.89 < 2.00 and J_tight goes first instead (TWT = 0).
    At L = 8 the order becomes known only at bh 22, so the bh-0 decision is
    unchanged and the run must reproduce L = 0 exactly.
    """
    return {
        "meta": {"id": "vis_atcla", "campus": 5, "track": "replay",
                 "size_class": 3, "window_start": "synthetic",
                 "window_bh": 60.0, "provenance": "R", "seed": None},
        "trades": ["X"],
        "technicians": [{"id": "T0", "trade": "X"}],
        "work_orders": [
            _wo("J_slack", "X", 1.0, 0.0, 2.0, 4.0, 1),
            _wo("J_tight", "X", 1.0, 0.0, 1.0, 2.0, 1),
            _wo("P_wave", "X", 20.0, 30.0, 200.0, 1.0, 4, is_pm=True),
        ],
    }


def _assignments(sched):
    """Comparable assignment list (order-independent, exact floats)."""
    return sorted((a["wo"], a["tech"], a["start_bh"], a["end_bh"])
                  for a in sched["assignments"])


def _twt(instance, sched):
    res = validate(instance, sched)
    return res, res["metrics"]["WWT"]


# --------------------------------------------------------------------------- #
# (i) the non-delay rules are constant in L
# --------------------------------------------------------------------------- #
def test_rules_constant(failures):
    print("(i) CONSTANCY: edd/atc/wmdd give the same schedule at every L")
    inst = mixed_fixture()

    # Fixture sanity: without early-known orders the test would prove nothing.
    early = [wo["id"] for wo in inst["work_orders"]
             if known_bh(wo, 40.0) < float(wo["release_bh"])]
    print("    preventive orders known early at L=40: %s" % ", ".join(early))
    if len(early) < 2:
        failures.append("(i) fixture is vacuous: only %d order(s) become known "
                        "early at L=40" % len(early))

    by_rule = {}
    for rule in r4v.CONST_RULES:
        ref = pdrs.dispatch(inst, rule, seed=SEED)
        ref_a = _assignments(ref)
        by_rule[rule] = ref_a
        _res, ref_w = _twt(inst, ref)
        widths = []
        for tag in r4v.VIS_TAGS:
            env = DispatchEnv(inst, visibility_L=r4v.VIS_L_OF[tag])
            sched = env.run_policy(pdrs.get_rule(rule), method=rule, seed=SEED)
            res, w = _twt(inst, sched)
            widths.append("L=%s:%.3f" % (tag, w))
            if not res["feasible"]:
                failures.append("(i) %s at L=%s INFEASIBLE: %s"
                                % (rule, tag, "; ".join(res["violations"][:3])))
            if _assignments(sched) != ref_a:
                failures.append("(i) %s at L=%s differs from pdrs.dispatch -- "
                                "the runner must NOT copy its L=0 row" % (rule, tag))
        if ref_w <= 0.0:
            failures.append("(i) fixture is too slack: %s has TWT 0" % rule)
        print("    %-5s pdrs TWT=%.3f  env %s" % (rule, ref_w, " ".join(widths)))
    if len({tuple(v) for v in by_rule.values()}) < 2:
        failures.append("(i) every rule produced the same schedule: the "
                        "fixture cannot discriminate and the test is vacuous")


# --------------------------------------------------------------------------- #
# (ii) forecast-aware ATC
# --------------------------------------------------------------------------- #
def test_atc_la(failures):
    print("(ii) atc_la: feasible at every L, == atc at L=0, uses the view")
    inst = atc_la_fixture()

    atc = pdrs.dispatch(inst, "atc", seed=SEED)
    _ares, atc_w = _twt(inst, atc)
    atc_a = _assignments(atc)

    scheds, twts = {}, {}
    for tag in r4v.VIS_TAGS:
        env = DispatchEnv(inst, visibility_L=r4v.VIS_L_OF[tag])
        sched = env.run_policy(pdrs.get_rule(r4v.ATC_LA), method=r4v.ATC_LA,
                               seed=SEED)
        res, w = _twt(inst, sched)
        scheds[tag], twts[tag] = sched, w
        if not res["feasible"]:
            failures.append("(ii) atc_la at L=%s INFEASIBLE: %s"
                            % (tag, "; ".join(res["violations"][:3])))
    first = {t: min(s["assignments"], key=lambda a: (a["start_bh"], a["wo"]))["wo"]
             for t, s in scheds.items()}
    print("    atc TWT=%.3f ; atc_la TWT %s"
          % (atc_w, " ".join("L=%s:%.3f" % (t, twts[t]) for t in r4v.VIS_TAGS)))
    print("    first job dispatched: %s"
          % " ".join("L=%s:%s" % (t, first[t]) for t in r4v.VIS_TAGS))

    if _assignments(scheds["0"]) != atc_a:
        failures.append("(ii) atc_la at L=0 is not atc(k=2) pick for pick")
    if _assignments(scheds["8"]) != atc_a:
        failures.append("(ii) atc_la at L=8 changed a decision the rule could "
                        "not have seen (the order is known only at bh 22)")
    for tag in ("40", "full"):
        if _assignments(scheds[tag]) == atc_a:
            failures.append("(ii) atc_la at L=%s equals atc: the visibility "
                            "view never reached the rule" % tag)
        if twts[tag] > twts["0"] + TOL:
            failures.append("(ii) atc_la at L=%s is WORSE than at L=0 "
                            "(%.3f > %.3f) on a fixture built for the gain"
                            % (tag, twts[tag], twts["0"]))


# --------------------------------------------------------------------------- #
# (iii) rolling CP-SAT gains from visibility
# --------------------------------------------------------------------------- #
def test_rollcp_visibility(failures):
    print("(iii) ROLLING: rollcp2 TWT at L=full <= L=0 (test_rolling fixture)")
    inst = visibility_fixture()
    rel = {wo["id"]: wo["release_bh"] for wo in inst["work_orders"]}

    out = {}
    for tag in ("0", "full"):
        sched = roll_cpsat(inst, budget_s=r4v.ROLLCP_BUDGET_S,
                           visibility_L=r4v.VIS_L_OF[tag])
        res, w = _twt(inst, sched)
        out[tag] = (sched, res, w)
        if not res["feasible"]:
            failures.append("(iii) rollcp2 at L=%s INFEASIBLE: %s"
                            % (tag, "; ".join(res["violations"][:3])))
        for a in sched["assignments"]:
            if a["start_bh"] < rel[a["wo"]] - TOL:
                failures.append("(iii) L=%s: %s starts at %.3f before its "
                                "release %.3f -- a known order was STARTED "
                                "early" % (tag, a["wo"], a["start_bh"],
                                           rel[a["wo"]]))
        print("    L=%-4s TWT=%.3f replans=%d starts=%s"
              % (tag, w, sched["decisions"],
                 {a["wo"]: round(a["start_bh"], 3) for a in sched["assignments"]}))
    if out["full"][2] > out["0"][2] + TOL:
        failures.append("(iii) visibility HURT the rolling planner: "
                        "TWT(full)=%.3f > TWT(0)=%.3f"
                        % (out["full"][2], out["0"][2]))
    elif out["full"][2] < out["0"][2] - TOL:
        print("    visibility advantage: %.3f -> %.3f"
              % (out["0"][2], out["full"][2]))
    else:
        print("    tie (%.3f)" % out["0"][2])


# --------------------------------------------------------------------------- #
# (iv) the runner's id scheme
# --------------------------------------------------------------------------- #
def test_id_scheme(failures):
    print("(iv) ID SCHEME: config id carries _L, meta.id does not")
    r4v._configure_methods(smoke=True)      # rules + atc_la: no ckpt, no solver

    base = mixed_fixture("vis_ids")
    m = 0.6
    inst = tightness.scale_crew(base, m)
    shard_id = r4v.shard_id_of("vis_ids", m)
    config = {
        "shard_id": shard_id, "base_id": "vis_ids", "campus": 5,
        "track": "replay", "split": "test", "size": 10,
        "regime": r4v.REGIME_EMPIRICAL, "crew_multiplier": m,
        "arrival_multiplier": 1.0, "pm_share": None, "u_target": None,
        "kind": "empirical", "path": None, "m": m,
        "eval_set": r4v.EVAL_SET, "rollcp": False,
        "u_realized": r4v._u_realized(inst),
    }
    print("    instance meta.id=%r  shard id=%r  config ids=%s"
          % (inst["meta"]["id"], shard_id,
             [r4v.config_id_of(shard_id, t) for t in r4v.VIS_TAGS]))
    if inst["meta"]["id"] != shard_id:
        failures.append("(iv) shard id %r != transformed meta.id %r"
                        % (shard_id, inst["meta"]["id"]))
    if r4v.shard_id_of("vis_ids", 1.0) != "vis_ids":
        failures.append("(iv) m=1.0 must leave the instance id untouched")

    expected = r4v.expected_keys(config)
    rows, infeasible = r4v.run_config_methods(inst, config, set(expected))
    n_want = (len(r4v.CONST_RULES) + 1) * len(r4v.VIS_TAGS)   # + atc_la
    print("    keys expected=%d computed=%d (want %d)"
          % (len(expected), len(rows), n_want))
    if len(expected) != n_want or set(rows) != set(expected):
        failures.append("(iv) key set mismatch: expected %d keys, got %d rows"
                        % (len(expected), len(rows)))
    if infeasible:
        failures.append("(iv) %d infeasible row(s): %s"
                        % (len(infeasible), infeasible[:2]))

    for key, r in sorted(rows.items()):
        want_id = r4v.config_id_of(shard_id, r["visibility_L"])
        if r["id"] != want_id:
            failures.append("(iv) row %s has id %r, expected %r"
                            % (key, r["id"], want_id))
        if r["base_id"] != "vis_ids":
            failures.append("(iv) row %s has base_id %r, expected 'vis_ids'"
                            % (key, r["base_id"]))
        if r["id"] == inst["meta"]["id"]:
            failures.append("(iv) row %s reuses meta.id as the config id" % key)
        if not r["feasible"]:
            failures.append("(iv) row %s is infeasible" % key)
        if r["method"] in r4v.CONST_RULES and r["constant_by_construction"] != 1:
            failures.append("(iv) rule row %s is not flagged constant" % key)
        if r["method"] == r4v.ATC_LA and r["constant_by_construction"] != 0:
            failures.append("(iv) atc_la row %s is flagged constant" % key)
    for rule in r4v.CONST_RULES:
        vals = {rows[r4v.row_key(rule, t)]["wwt"] for t in r4v.VIS_TAGS}
        if len(vals) != 1:
            failures.append("(iv) copied rows for %s disagree: %s" % (rule, vals))

    # The schedule itself must carry meta.id, or validator check (f) fails --
    # and the negative control proves that check is doing real work here.
    sched = pdrs.dispatch(inst, "edd", seed=SEED)
    if sched["instance_id"] != inst["meta"]["id"]:
        failures.append("(iv) schedule.instance_id %r != meta.id %r"
                        % (sched["instance_id"], inst["meta"]["id"]))
    bad = dict(sched, instance_id=r4v.config_id_of(shard_id, "40"))
    res_bad = validate(inst, bad)
    if res_bad["feasible"] or not any(v.startswith("(f)")
                                      for v in res_bad["violations"]):
        failures.append("(iv) negative control: writing the config id into the "
                        "schedule did NOT trip validator check (f)")
    else:
        print("    negative control: %s" % res_bad["violations"][0])

    r4v._configure_methods(smoke=False)     # leave the module as we found it


# --------------------------------------------------------------------------- #
def main():
    failures = []
    test_rules_constant(failures)
    print()
    test_atc_la(failures)
    print()
    test_rollcp_visibility(failures)
    print()
    test_id_scheme(failures)
    print()

    if failures:
        print("FAILURES:")
        for f in failures:
            print("  - " + f)
        sys.exit(1)
    print("ALL R4.6 VISIBILITY TESTS PASSED")


if __name__ == "__main__":
    main()
