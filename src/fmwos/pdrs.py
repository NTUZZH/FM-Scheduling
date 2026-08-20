"""Priority dispatching rules (PDRs) for the FM work-order scheduling benchmark.

All rules share one event-driven list-scheduling *dispatcher* (``dispatch``).
The dispatcher builds a **non-delay** schedule: a technician is never left idle
while a released, trade-matching work order is waiting.  This is the standard
list-scheduling protocol for R | elig, r_j | sum w_j T_j and is exactly what the
interface spec asks for -- "when a technician is free and its trade
queue is non-empty, pick the job maximizing the rule's score".

Simulation model
----------------
Two kinds of events, held in a single time-ordered ``heapq``:

  * ``release`` -- a work order becomes available at ``release_bh``;
  * ``free``    -- a technician finishes a job (or is initially free at bh 0).

At each distinct event time we first drain *all* events at that time (so that
every job released at that instant is queued before any pick is made), then, for
each trade whose state changed, we greedily assign queued jobs to idle
technicians of that trade until one side runs out.  Ties between identical
technicians of a trade are broken by technician id (they are interchangeable in
v1, so this never affects the objective, only reproducibility).

The dispatcher never inserts idle time on purpose -- that is the defining
limitation of dispatching versus the CP-SAT solver, and it is *why* a solver can
beat every PDR (see tests/fixtures/tiny_instance.md).

Rules
-----
  ``edd``      earliest due date;
  ``wspt``     weighted shortest processing time;
  ``atc``      apparent tardiness cost, look-ahead k = 2 (literature default);
  ``atc_k05``, ``atc_k1``, ``atc_k3``, ``atc_k5``, ``atc_k10``
               the same rule at k in {0.5, 1, 3, 5, 10} (the R4.3 tuning grid);
  ``atc_la``   forecast-aware ATC: the R4.6 look-ahead baseline, runnable ONLY
               through ``fmwos.env.DispatchEnv`` because it reads the trade's
               known-but-unreleased orders;
  ``pfifo``    priority class first, FIFO within a class;
  ``wmdd``     weighted modified due date (Kanet and Li 2004);
  ``lpt``      longest processing time within the trade queue (diagnostic);
  ``random``   uniformly random pick (seeded floor).

Every choice is deterministic for a fixed ``seed`` (the seed only matters for the
'random' rule).  Complexity: O(E log E) for the event heap plus O(sum |queue|)
for the linear per-dispatch scans; for 400 jobs x dozens of technicians this is
well under a millisecond.

Output: a schedule dict per the interface spec (method = rule name,
``wall_seconds`` measured, ``decisions`` = number of pick decisions = number of
work orders, since every job is picked exactly once).
"""

from __future__ import annotations

import functools
import heapq
import itertools
import math
import random
import time
from collections import defaultdict

# --------------------------------------------------------------------------- #
# Rules.  Each rule is a callable ``pick(queue, t, rng) -> job`` that returns
# the work order (a dict from instance["work_orders"]) to dispatch next from a
# single trade's ``queue`` at simulation time ``t``.  They are written as a
# ``min`` over a key so that a job-id final tiebreak makes every choice
# deterministic regardless of queue insertion order.
# --------------------------------------------------------------------------- #


def _pick_edd(queue, t, rng):
    """Earliest Due Date: smallest due_bh first (tie: job id)."""
    return min(queue, key=lambda j: (j["due_bh"], j["id"]))


def _pick_wspt(queue, t, rng):
    """Weighted Shortest Processing Time: largest weight/p_bh first."""
    return min(queue, key=lambda j: (-(j["weight"] / j["p_bh"]), j["id"]))


def _pick_atc(queue, t, rng, k=2.0):
    """Apparent Tardiness Cost (Vepsalainen & Morton), k = 2.

    score = (w / p) * exp( - max(0, due - t - p) / (k * pbar) )

    where ``pbar`` is the mean processing time of the jobs *currently* queued in
    this trade's queue (recomputed at every dispatch, so ATC is genuinely
    time- and queue-dependent).  The job of maximum score is dispatched.
    """
    pbar = sum(j["p_bh"] for j in queue) / len(queue)
    denom = k * pbar  # pbar > 0 because processing times are strictly positive

    def key(j):
        slack = max(0.0, j["due_bh"] - t - j["p_bh"])
        score = (j["weight"] / j["p_bh"]) * math.exp(-slack / denom)
        return (-score, j["id"])  # min of -score == max score

    return min(queue, key=key)


# ATC at the look-ahead values of the R4.3 tuning grid.  These are module-level
# ``functools.partial`` objects (not closures) so they pickle across worker forks
# exactly like the plain rule functions.
_pick_atc_k05 = functools.partial(_pick_atc, k=0.5)
_pick_atc_k1 = functools.partial(_pick_atc, k=1.0)
_pick_atc_k3 = functools.partial(_pick_atc, k=3.0)
_pick_atc_k5 = functools.partial(_pick_atc, k=5.0)
_pick_atc_k10 = functools.partial(_pick_atc, k=10.0)


ATC_K = 2.0             # the frozen ATC look-ahead (literature default)
_LA_WINDOW_BH = 40.0    # W: window over which known future work is counted


def _pick_atc_la(queue, t, rng, view):
    """Forecast-aware ATC (R4.6): ATC whose look-ahead shrinks as known work piles up.

    ``view`` is supplied by ``fmwos.env.DispatchEnv.run_policy`` and holds the
    trade's known-but-unreleased orders and its crew size.  With

        rho_known = (sum p_bh of known orders releasing within W) / (W * crew)

    the rule scores exactly as ATC but at ``k_eff = k / (1 + rho_known)``: a
    smaller k narrows the slack discount horizon, so the rule gets greedier about
    urgent work before the known wave lands.  When nothing is known (every
    corrective-only queue, and every queue at L=0) rho_known is 0 and the rule is
    ATC at k = 2, pick for pick.
    """
    crew = view["crew"] or 1
    horizon = t + _LA_WINDOW_BH
    load = sum(j["p_bh"] for j in view["known"]
               if float(j["release_bh"]) <= horizon)
    rho_known = load / (_LA_WINDOW_BH * crew)
    return _pick_atc(queue, t, rng, k=ATC_K / (1.0 + rho_known))


# Marks the rule as env-only: DispatchEnv.run_policy passes the visibility view,
# and pdrs.dispatch (which has no known-order state) refuses it.
_pick_atc_la.wants_visibility = True


def _pick_pfifo(queue, t, rng):
    """Priority-FIFO: lowest priority class first (1 before 4); FIFO (earliest
    release_bh) within a class (tie: job id)."""
    return min(queue, key=lambda j: (j["priority"], j["release_bh"], j["id"]))


def _pick_wmdd(queue, t, rng):
    """Weighted Modified Due Date (Kanet & Li 2004, J. Sched. 7(4):261-276).

    At time ``t`` dispatch the job minimizing

        (1 / w) * max(p, due - t)

    (tie: job id).  A job with slack left is ranked by its weighted remaining
    time to the due date; once the slack is gone the term collapses to p / w, so
    the rule behaves like weighted EDD while the queue is early and like WSPT
    once it is late.  It is the strong transparent baseline for sum w_j T_j.
    """
    return min(
        queue,
        key=lambda j: (max(j["p_bh"], j["due_bh"] - t) / j["weight"], j["id"]),
    )


def _pick_lpt(queue, t, rng):
    """Longest Processing Time within the technician's trade queue.

    Dispatch the largest-p_bh job first (tie: job id).  Every technician serves
    exactly one trade, so this is a pure single-queue workload rule: it ignores
    due dates and weights and is kept as a deliberately simple workload-oriented
    diagnostic comparator, not as a competitive baseline.  (The released v1.0
    result files label this rule "mor".)
    """
    return min(queue, key=lambda j: (-j["p_bh"], j["id"]))


def _pick_random(queue, t, rng):
    """Uniformly random choice from the queue, drawn from the run's seeded RNG."""
    return queue[rng.randrange(len(queue))]


_RULES = {
    "edd": _pick_edd,
    "wspt": _pick_wspt,
    "atc": _pick_atc,           # k = 2 (literature default)
    "atc_k05": _pick_atc_k05,
    "atc_k1": _pick_atc_k1,
    "atc_k3": _pick_atc_k3,
    "atc_k5": _pick_atc_k5,
    "atc_k10": _pick_atc_k10,
    "atc_la": _pick_atc_la,     # env-only (needs the visibility view)
    "pfifo": _pick_pfifo,
    "wmdd": _pick_wmdd,
    "lpt": _pick_lpt,
    "random": _pick_random,
}


def get_rule(name):
    """Return the ``pick(queue, t, rng)`` callable for ``name``.

    Raises ``ValueError`` for an unknown rule name.
    """
    try:
        return _RULES[name]
    except KeyError:
        raise ValueError(
            "unknown rule {!r}; valid rules: {}".format(name, sorted(_RULES))
        )


# --------------------------------------------------------------------------- #
# Dispatcher
# --------------------------------------------------------------------------- #

_KIND_FREE = 0     # a technician becomes available
_KIND_RELEASE = 1  # a work order is released


def dispatch(instance: dict, rule: str, seed: int = 0) -> dict:
    """Run the event-driven list-scheduling dispatcher under ``rule``.

    Parameters
    ----------
    instance : dict   an instance dict per the interface spec
    rule     : str    any key of ``_RULES`` (see the module docstring) EXCEPT
                      the env-only ``atc_la``, which raises ValueError here
    seed     : int    RNG seed (only affects the 'random' rule)

    Returns
    -------
    dict  a schedule dict per the interface spec.
    """
    t_start = time.perf_counter()
    pick = get_rule(rule)
    if getattr(pick, "wants_visibility", False):
        raise ValueError(
            "rule {!r} needs the visibility view (the trade's known but "
            "unreleased orders), which this dispatcher does not track; run it "
            "through fmwos.env.DispatchEnv(instance, visibility_L=L)."
            "run_policy(pdrs.get_rule({!r}))".format(rule, rule)
        )
    rng = random.Random(seed)

    technicians = instance["technicians"]
    work_orders = instance["work_orders"]

    # Per-trade state.
    queue = defaultdict(list)  # trade -> list of released, unassigned WO dicts
    idle = defaultdict(list)   # trade -> heap of idle technician ids (strings)

    counter = itertools.count()  # unique tiebreak so heap never compares payloads
    events = []                  # heap of (time, seq, kind, payload...)

    # Every technician is available from bh 0 (shift structure is baked into the
    # bh axis, per the interface spec).
    for tech in technicians:
        heapq.heappush(events, (0.0, next(counter), _KIND_FREE, tech["id"], tech["trade"]))
    # Release events.
    for wo in work_orders:
        heapq.heappush(events, (float(wo["release_bh"]), next(counter), _KIND_RELEASE, wo))

    assignments = []
    decisions = 0

    def try_dispatch(trade, now):
        nonlocal decisions
        q = queue[trade]
        free_techs = idle[trade]
        while free_techs and q:
            job = pick(q, now, rng)
            q.remove(job)                       # exact object; unique id
            tech_id = heapq.heappop(free_techs)  # smallest id -> deterministic
            start = float(now)
            end = start + float(job["p_bh"])     # travel = 0: end - start == p_bh
            assignments.append(
                {"wo": job["id"], "tech": tech_id, "start_bh": start, "end_bh": end}
            )
            decisions += 1
            heapq.heappush(events, (end, next(counter), _KIND_FREE, tech_id, trade))

    while events:
        now = events[0][0]
        touched = set()
        # Drain all events at this instant so every simultaneously-released job
        # is in the queue before any pick is made.
        while events and events[0][0] == now:
            _, _, kind, *payload = heapq.heappop(events)
            if kind == _KIND_FREE:
                tech_id, trade = payload
                heapq.heappush(idle[trade], tech_id)
                touched.add(trade)
            else:  # _KIND_RELEASE
                wo = payload[0]
                queue[wo["trade"]].append(wo)
                touched.add(wo["trade"])
        for trade in sorted(touched):
            try_dispatch(trade, now)

    return {
        "instance_id": instance["meta"]["id"],
        "method": rule,
        "seed": seed,
        "wall_seconds": time.perf_counter() - t_start,
        "decisions": decisions,
        "assignments": assignments,
    }
