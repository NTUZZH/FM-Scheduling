"""Online dispatch environment for the FM work-order scheduling benchmark (P3).

``DispatchEnv`` runs ONE instance as an online episode (the training spec §1):
work orders are hidden until their ``release_bh``; technicians are unary
resources per trade; the event loop is IDENTICAL to ``fmwos.pdrs.dispatch``
(drain all simultaneous events, then dispatch each touched trade -- in sorted
order -- while it has an idle technician and a non-empty queue, popping the
smallest-id idle technician).  A *decision* = one pick for one (trade, free
technician) context; the action indexes the trade's candidate queue (capped at
``K=64`` by smallest slack, padding masked).

Two ways to run an episode, sharing ONE generator-based driver so their event
semantics are bit-identical:

* ``env.run_policy(pick_fn)`` -- fast path: a plain callable
  ``pick(queue, t, rng) -> job`` (exactly the ``fmwos.pdrs`` rule signature) is
  applied to the full queue.  Running this with a PDR rule reproduces
  ``pdrs.dispatch`` assignment-for-assignment (parity requirement).
* ``reset()`` / ``step(action)`` -- the RL path: emits gym-flavoured
  observations and the potential-shaped reward (§2).

Reward (§2, corrected LB per fmwos.lb).  ``reward_mode`` selects the E5-ablation
variant; all three keep the /100 scale and telescope to -finalWWT/100:

* ``'shaped'`` (default): Phi(s) = realized(s) + LB(s), reward =
  (Phi(s_t) - Phi(s_{t+1})) / 100.  realized(s) is the locked-in weighted
  tardiness of all dispatched jobs (their completion is determined the instant
  they are dispatched, travel=0); LB(s) is the admissible bound on the remaining
  queued jobs.  The empty initial state has Phi=0, so the undiscounted return
  sums to -finalWWT/100 (telescoping).
* ``'realized'``: potential = realized(s) only (LB dropped), so reward =
  -(delta realized WWT)/100.  Still telescopes to -finalWWT/100 because
  realized(s_0)=0 and realized(s_T)=finalWWT.
* ``'terminal'``: sparse baseline -- reward 0 on every step except the LAST step
  of the episode, which returns -finalWWT/100 (= -realized(s_T)/100).

``feature_drop`` (None|'urgency'|'workload'|'context') zeroes OUT a feature group
in every observation (tensor shapes are unchanged, so a checkpoint trained under
one drop stays load-compatible with another); see ``_DROP_CAND_COLS``.

Preventive visibility (R4.6, docs/protocol.md §R4.6)
--------------------------------------------------
``visibility_L`` (business hours; ``None`` = full-instance visibility, ``0.0`` =
the status quo) makes a preventive order KNOWN ``L`` bh before it is released:
``known_bh = max(0, release_bh - L)``.  Corrective orders are never known early.
A known order may inform decisions but may NOT start before ``release_bh``, so it
sits in ``self.known[trade]`` and only ``_RELEASE`` moves it into ``queue``;
candidates and rule picks are drawn from ``queue`` only.  That is deliberate: a
non-delay executor must not exploit knowing the future by idling, and the rolling
CP-SAT planner (fmwos.rolling) is the executor that may.

``lookahead_features=True`` appends three context columns describing the trade's
known-but-unreleased work (F_CTX 10 -> 13); the flag exists so every checkpoint
trained before R4.6 keeps evaluating unchanged at any ``L``.  The effective width
is published as ``self.f_ctx`` and the trainer sizes the policy from it.
"""

from __future__ import annotations

import heapq
import itertools
import math
import random
import time

import numpy as np

from . import lb as _lb

# Feature layout (the training spec §3). Constants are FIXED (no data-derived
# normalization): the /8, /32, /16, /40, log1p and clips ARE the normalization.
K_CAND = 64
F_JOB = 12
F_CTX = 10
F_CTX_LOOKAHEAD = 13       # F_CTX + the three R4.6 lookahead columns (c10-c12)
_WEEK_BH = 40.0            # 5 weekdays x 8 bh
_EWMA_HALFLIFE = 40.0      # bh; arrival-rate EWMA (ctx feature 7)
_LN2 = math.log(2.0)
_EPS = 1e-6
_TWO_PI = 2.0 * math.pi

# Lookahead-feature windows (R4.6): a shift-length window and a week-length one,
# both FIXED constants like every other normalization in this file.
_LA_SHORT_BH = 8.0
_LA_LONG_BH = 40.0
_LA_NEXT_CLIP = 5.0        # days; also the "no known release" sentinel

_FREE = 0     # event: a technician becomes available
_RELEASE = 1  # event: a work order is released
_KNOWN = 2    # event: a preventive order becomes visible (R4.6), still unreleased

# --------------------------------------------------------------------------- #
# E5 ablation knobs (the training spec §2 reward variants, §3 feature groups).  #
# --------------------------------------------------------------------------- #
REWARD_MODES = ("shaped", "realized", "terminal")

# Feature-drop groups. The 1-indexed spec cand-feature numbers (§3) map onto the
# 0-indexed columns filled by _fill_job_features as  spec feat N -> cand col N-1:
#   urgency  = spec feats 2,3   (slack_days, tardy_already) -> cols (1, 2)
#   workload = spec feats 1,11  (log1p p, p/queue-work)      -> cols (0, 10)
#   context  = the ENTIRE F_CTX ctx vector (handled separately below)
FEATURE_DROPS = (None, "urgency", "workload", "context")
_DROP_CAND_COLS = {"urgency": (1, 2), "workload": (0, 10)}


# --------------------------------------------------------------------------- #
# Visibility semantics (R4.6).  ONE definition, imported by fmwos.rolling too,  #
# so the environment and the rolling planner can never drift apart.             #
# --------------------------------------------------------------------------- #
def known_bh(wo, visibility_L):
    """Business hour at which ``wo`` becomes KNOWN under visibility ``L``.

    Preventive orders become known ``L`` bh early (``L=None`` = the whole
    instance is known from bh 0); corrective orders are never known before their
    release, because the release proxy IS the moment the request appears.
    """
    rel = float(wo["release_bh"])
    if not wo.get("is_pm"):
        return rel
    if visibility_L is None:
        return 0.0
    return max(0.0, rel - float(visibility_L))


def check_visibility_L(visibility_L):
    """Validate a visibility level; returns it unchanged (None or float >= 0)."""
    if visibility_L is None:
        return None
    L = float(visibility_L)
    if L < 0.0:
        raise ValueError("visibility_L must be None or >= 0, got %r" % (visibility_L,))
    return L


class DispatchEnv:
    """Online single-instance dispatch episode (see module docstring)."""

    def __init__(self, instance: dict, k_cand: int = K_CAND,
                 reward_mode: str = "shaped", feature_drop=None,
                 visibility_L=0.0, lookahead_features: bool = False):
        self.instance = instance
        self.K = int(k_cand)
        self.meta_id = instance["meta"]["id"]
        if reward_mode not in REWARD_MODES:
            raise ValueError("reward_mode must be one of %r, got %r"
                             % (REWARD_MODES, reward_mode))
        if feature_drop not in FEATURE_DROPS:
            raise ValueError("feature_drop must be one of %r, got %r"
                             % (FEATURE_DROPS, feature_drop))
        self.reward_mode = reward_mode
        self.feature_drop = feature_drop
        # R4.6 visibility. The default (L=0, no lookahead columns) reproduces
        # every pre-R4 observation and schedule bit-identically: no _KNOWN event
        # is ever pushed, so even the event heap's sequence numbers are unchanged.
        self.visibility_L = check_visibility_L(visibility_L)
        self.lookahead_features = bool(lookahead_features)
        # Effective observation dims, published so the trainer/policy size
        # themselves from the env rather than from module constants.
        self.f_job = F_JOB
        self.f_ctx = F_CTX_LOOKAHEAD if self.lookahead_features else F_CTX

        # Static per-trade index (technician pools). Every trade present in the
        # work orders is guaranteed >= 1 technician by the instance builder.
        self.trades = list(instance["trades"])
        self.techs_of: dict[str, list] = {tr: [] for tr in self.trades}
        for tech in instance["technicians"]:
            self.techs_of.setdefault(tech["trade"], []).append(tech["id"])
        # Any trade that appears only in work orders (defensive) still needs a
        # bucket so queue/idle lookups never KeyError.
        for wo in instance["work_orders"]:
            self.techs_of.setdefault(wo["trade"], self.techs_of.get(wo["trade"], []))
        self.k_of = {tr: len(ts) for tr, ts in self.techs_of.items()}
        self._all_trades = list(self.techs_of.keys())

        self._reset_state()

    # ------------------------------------------------------------------ #
    # State                                                              #
    # ------------------------------------------------------------------ #
    def _reset_state(self):
        self.queue = {tr: [] for tr in self._all_trades}
        # Visible but NOT yet startable (R4.6): populated by _KNOWN, emptied by
        # _RELEASE. Never a candidate; only the context features read it.
        self.known = {tr: [] for tr in self._all_trades}
        self.idle = {tr: [] for tr in self._all_trades}      # heaps of tech ids
        self.tech_free_at = {}
        for ts in self.techs_of.values():
            for tid in ts:
                self.tech_free_at[tid] = 0.0
        self.assignments = []
        self._realized = 0.0

        # Potential/LB caching: a trade's cached LB is reused only when it is
        # neither dirty nor evaluated at a stale time (LB depends on t).
        self._lb_cache = {}
        self._lb_t = {}
        self._lb_dirty = set()

        # Arrival-rate EWMA per trade (ctx feature 7).
        self._ewma_s = {tr: 0.0 for tr in self._all_trades}
        self._ewma_last = {tr: 0.0 for tr in self._all_trades}

        # Decision context set at each generator yield.
        self._cur_trade = None
        self._cur_now = 0.0
        self._cur_free = 0
        self._candidates = []
        self._done = True
        self._gen = None
        self._t_reset = time.perf_counter()

    # ------------------------------------------------------------------ #
    # Core event-loop driver (shared by run_policy and step)             #
    # ------------------------------------------------------------------ #
    def _driver(self):
        """Generator replicating the pdrs.dispatch event loop exactly.

        Yields at each pick decision; the caller sends the chosen work-order
        dict back in.  Dispatching, technician selection (smallest id via the
        idle heap), event ordering and float arithmetic all mirror
        ``fmwos.pdrs.dispatch`` so schedules are identical for the same picks.
        """
        seq = itertools.count()
        events = []
        # Technicians available from bh 0 (pushed first, exactly as pdrs).
        for tech in self.instance["technicians"]:
            heapq.heappush(events, (0.0, next(seq), _FREE, tech["id"], tech["trade"]))
        for wo in self.instance["work_orders"]:
            rel = float(wo["release_bh"])
            kb = known_bh(wo, self.visibility_L)
            if kb < rel:
                # Only orders that are known STRICTLY before release get an event
                # (at L=0 there are none, so the heap is byte-for-byte as before).
                heapq.heappush(events, (kb, next(seq), _KNOWN, wo))
            heapq.heappush(events, (rel, next(seq), _RELEASE, wo))

        while events:
            now = events[0][0]
            touched = set()
            # Drain all events at this instant (every simultaneously-released
            # job is queued before any pick is made).
            while events and events[0][0] == now:
                _, _, kind, *payload = heapq.heappop(events)
                if kind == _FREE:
                    tid, trade = payload
                    heapq.heappush(self.idle[trade], tid)
                    touched.add(trade)
                elif kind == _KNOWN:
                    wo = payload[0]
                    self.known[wo["trade"]].append(wo)
                    # NOT touched: a known order is not startable, so it cannot
                    # create a dispatch opportunity (and the queue is unchanged).
                else:  # _RELEASE
                    wo = payload[0]
                    tr = wo["trade"]
                    self._unknow(tr, wo)
                    self.queue[tr].append(wo)
                    self._on_arrival(tr, now)
                    touched.add(tr)

            for trade in sorted(touched):
                q = self.queue[trade]
                free = self.idle[trade]
                while free and q:
                    self._cur_trade = trade
                    self._cur_now = now
                    self._cur_free = len(free)
                    job = yield                       # caller picks a job dict
                    q.remove(job)                     # exact object (unique id)
                    tid = heapq.heappop(free)         # smallest id: deterministic
                    start = float(now)
                    end = start + float(job["p_bh"])  # travel=0: end-start==p_bh
                    self.tech_free_at[tid] = end
                    self.assignments.append(
                        {"wo": job["id"], "tech": tid,
                         "start_bh": start, "end_bh": end}
                    )
                    self._realized += job["weight"] * max(0.0, end - job["due_bh"])
                    self._lb_dirty.add(trade)
                    heapq.heappush(events, (end, next(seq), _FREE, tid, trade))

    def _unknow(self, trade, wo):
        """Drop ``wo`` from the trade's known list on release (identity scan: the
        list holds the instance's own dicts, and it is empty at L=0)."""
        kn = self.known[trade]
        for i, j in enumerate(kn):
            if j is wo:
                del kn[i]
                return

    def _on_arrival(self, trade, now):
        """Update the trade's arrival-rate EWMA and mark its LB dirty."""
        last = self._ewma_last[trade]
        decay = 0.5 ** ((now - last) / _EWMA_HALFLIFE) if now > last else 1.0
        self._ewma_s[trade] = self._ewma_s[trade] * decay + 1.0
        self._ewma_last[trade] = now
        self._lb_dirty.add(trade)

    # ------------------------------------------------------------------ #
    # Fast path: run a full episode with a plain pick callable           #
    # ------------------------------------------------------------------ #
    def run_policy(self, pick_fn, method: str = "rl", seed: int = 0) -> dict:
        """Run one episode driving ``pick_fn(queue, t, rng) -> job``.

        Reproduces ``fmwos.pdrs.dispatch`` when ``pick_fn`` is a pdrs rule.

        A rule carrying ``wants_visibility = True`` (the forecast-aware ATC of
        R4.6) is called as ``pick_fn(queue, t, rng, view)`` instead, with
        ``view = {"known": <the trade's known orders>, "crew": <trade crew>}``.
        It still picks from ``queue``: visibility informs the score, never the
        set of startable jobs.

        Returns a schedule dict (the interface spec).
        """
        t0 = time.perf_counter()
        self._reset_state()
        rng = random.Random(seed)
        wants_view = bool(getattr(pick_fn, "wants_visibility", False))
        gen = self._driver()
        try:
            next(gen)
            while True:
                trade = self._cur_trade
                if wants_view:
                    view = {"known": self.known[trade],
                            "crew": self.k_of.get(trade, 1) or 1}
                    job = pick_fn(self.queue[trade], self._cur_now, rng, view)
                else:
                    job = pick_fn(self.queue[trade], self._cur_now, rng)
                gen.send(job)
        except StopIteration:
            pass
        return self._build_schedule(method, time.perf_counter() - t0, seed)

    # ------------------------------------------------------------------ #
    # RL path: reset / step                                              #
    # ------------------------------------------------------------------ #
    def reset(self):
        """Start a fresh episode; return the first observation."""
        self._reset_state()
        self._gen = self._driver()
        self.phi_prev = 0.0                # Phi(empty initial state) == 0
        try:
            next(self._gen)                # advance to the first decision
            self._done = False
        except StopIteration:
            self._done = True
        self._t_reset = time.perf_counter()
        return self._make_obs() if not self._done else self._zeros_obs()

    def step(self, action):
        """Apply one pick (action indexes the candidate list); advance to the
        next decision (or terminal); return (obs, reward, done, info)."""
        if self._done:
            raise RuntimeError("step() called on a finished episode; reset() first")
        job = self._candidates[int(action)]
        n_cand = len(self._candidates)
        trade = self._cur_trade
        capped = len(self.queue[trade]) > self.K
        try:
            self._gen.send(job)
            done = False
        except StopIteration:
            done = True
        self._done = done

        reward = self._reward(done)

        obs = self._zeros_obs() if done else self._make_obs()
        info = {"trade": trade, "n_cand": n_cand, "capped": capped,
                "realized": self._realized}
        return obs, reward, done, info

    def _reward(self, done):
        """Per-step reward for the active ``reward_mode`` (see module docstring).

        All variants keep the /100 scale and telescope to -finalWWT/100.
        """
        if self.reward_mode == "terminal":
            # Sparse: only the final step pays, and it pays the whole finalWWT
            # (== realized(s_T), all jobs dispatched so their tardiness is set).
            return (-self._realized / 100.0) if done else 0.0
        # 'shaped' and 'realized' are both potential differences off phi_prev;
        # they differ only in whether the admissible LB is part of the potential.
        if self.reward_mode == "realized":
            phi_now = self._realized              # potential = realized WWT only
        else:                                     # 'shaped' (default)
            phi_now = self._phi(self._cur_now)    # realized + admissible LB
        reward = (self.phi_prev - phi_now) / 100.0
        self.phi_prev = phi_now
        return reward

    # ------------------------------------------------------------------ #
    # Potential                                                          #
    # ------------------------------------------------------------------ #
    def _phi(self, t):
        """Phi(s) = realized(s) + LB(s), with per-trade LB caching keyed on
        (dirty, t) so stale-time reuse never happens (LB depends on t).

        Visibility (R4.6) does NOT enter the potential: the admissibility
        argument for LB conditions on released work only (the bound relaxes the
        queued jobs onto their trade's technicians from time t), and known but
        unreleased orders cannot be started, so folding them in would break both
        admissibility and the telescoping identity that Phi(s_0) = 0 gives.
        The reward is therefore identical at every L."""
        total = self._realized
        for trade in self._all_trades:
            q = self.queue[trade]
            if not q:
                continue
            if (trade in self._lb_dirty) or (self._lb_t.get(trade) != t):
                taus = [self.tech_free_at[tid] for tid in self.techs_of[trade]]
                jobs = [(j["p_bh"], j["due_bh"], j["weight"]) for j in q]
                self._lb_cache[trade] = _lb._lb_trade(jobs, taus, t)
                self._lb_t[trade] = t
            total += self._lb_cache[trade]
        self._lb_dirty.clear()
        return total

    def phi(self):
        """Public: current potential Phi(s) at the current decision time."""
        return self._phi(self._cur_now)

    # ------------------------------------------------------------------ #
    # Observation construction                                           #
    # ------------------------------------------------------------------ #
    def _make_obs(self):
        trade = self._cur_trade
        t = self._cur_now
        q = self.queue[trade]

        # Candidate truncation: keep the K smallest-slack jobs (most urgent).
        slack = [(j["due_bh"] - t - j["p_bh"], j["id"], j) for j in q]
        slack.sort(key=lambda x: (x[0], x[1]))
        chosen = slack[: self.K]
        self._candidates = [c[2] for c in chosen]
        n = len(self._candidates)

        qtw = 0.0
        for j in q:
            qtw += j["p_bh"]

        cand = np.zeros((self.K, F_JOB), dtype=np.float32)
        for i, job in enumerate(self._candidates):
            self._fill_job_features(cand[i], job, t, qtw)
        mask = np.zeros((self.K,), dtype=bool)
        mask[:n] = True

        ctx = self._ctx_features(trade, t, q, qtw)

        # E5 ablation: zero OUT a dropped feature group (shapes unchanged, so
        # checkpoints stay compatible). Padded cand rows are already all-zero.
        drop = self.feature_drop
        if drop == "context":
            ctx[:] = 0.0
        elif drop is not None:
            for col in _DROP_CAND_COLS[drop]:
                cand[:, col] = 0.0

        return {"cand": cand, "mask": mask, "ctx": ctx}

    def _zeros_obs(self):
        return {"cand": np.zeros((self.K, F_JOB), dtype=np.float32),
                "mask": np.zeros((self.K,), dtype=bool),
                "ctx": np.zeros((self.f_ctx,), dtype=np.float32)}

    @staticmethod
    def _fill_job_features(out, job, t, qtw):
        p = job["p_bh"]
        d = job["due_bh"]
        w = job["weight"]
        r = job["release_bh"]
        prio = job["priority"]
        # 1 log1p(p_bh)
        out[0] = math.log1p(p)
        # 2 slack_days, clipped [-30, 30]
        sd = (d - t - p) / 8.0
        out[1] = -30.0 if sd < -30.0 else (30.0 if sd > 30.0 else sd)
        # 3 tardy_already
        out[2] = 1.0 if (t + p > d) else 0.0
        # 4 w_j / 8
        out[3] = w / 8.0
        # 5-8 priority one-hot (P1..P4)
        if 1 <= prio <= 4:
            out[3 + prio] = 1.0
        # 9 is_pm
        out[8] = 1.0 if job.get("is_pm") else 0.0
        # 10 wait_days, clipped [0, 30]
        wd = (t - r) / 8.0
        out[9] = 0.0 if wd < 0.0 else (30.0 if wd > 30.0 else wd)
        # 11 p_bh / (queue total work + eps)
        out[10] = p / (qtw + _EPS)
        # 12 log1p(w_j / p_bh)  (WSPT index, log1p-scaled)
        out[11] = math.log1p(w / p) if p > 0 else 0.0

    def _ctx_features(self, trade, t, q, qtw):
        ctx = np.zeros((self.f_ctx,), dtype=np.float32)
        nq = len(q)
        k = self.k_of.get(trade, 1) or 1
        # 1 |Q_g| / 32
        ctx[0] = nq / 32.0
        # 2 queue total work / (8 * k_g)  [days of backlog per tech]
        ctx[1] = qtw / (8.0 * k)
        # 3 min slack in queue / 8
        if nq:
            mn = min((j["due_bh"] - t - j["p_bh"]) for j in q)
            ctx[2] = mn / 8.0
        # 4 share of P1|P2 in queue
        if nq:
            hi = sum(1 for j in q if j["priority"] in (1, 2))
            ctx[3] = hi / nq
        # 5 free technician share
        ctx[4] = self._cur_free / k
        # 6 k_g / 16
        ctx[5] = k / 16.0
        # 7 EWMA arrival rate (per bh, halflife 40 bh) * 8
        last = self._ewma_last[trade]
        decay = 0.5 ** ((t - last) / _EWMA_HALFLIFE) if t > last else 1.0
        rate = (_LN2 / _EWMA_HALFLIFE) * self._ewma_s[trade] * decay
        ctx[6] = rate * 8.0
        # 8/9 bh-of-week sin/cos
        ang = _TWO_PI * ((t % _WEEK_BH) / _WEEK_BH)
        ctx[7] = math.sin(ang)
        ctx[8] = math.cos(ang)
        # 10 episode progress proxy: t / 40
        ctx[9] = t / _WEEK_BH
        if self.lookahead_features:
            self._fill_lookahead_features(ctx, trade, t, k)
        return ctx

    def _fill_lookahead_features(self, ctx, trade, t, k):
        """Append the R4.6 lookahead columns c10-c12 (spec §S1).

        They describe the trade's KNOWN but unreleased work, in the same
        days-per-technician units as the backlog column, so a policy can compare
        the wave that is coming with the queue it already holds.  At L=0 the
        known list is always empty, so the three columns are the constants
        (0, 0, 5) -- which is exactly what makes the L=0 control arm an
        information control at identical capacity.
        """
        short_load = long_load = 0.0
        next_rel = None
        for j in self.known[trade]:
            r = float(j["release_bh"])
            p = float(j["p_bh"])
            if r <= t + _LA_SHORT_BH:
                short_load += p
            if r <= t + _LA_LONG_BH:
                long_load += p
            if next_rel is None or r < next_rel:
                next_rel = r
        # 11 known work releasing within 8 bh, in days per technician
        ctx[10] = short_load / (_LA_SHORT_BH * k)
        # 12 the same over the 40 bh window
        ctx[11] = long_load / (_LA_LONG_BH * k)
        # 13 days to the trade's next known release, clipped [0, 5] (5 = none)
        if next_rel is None:
            ctx[12] = _LA_NEXT_CLIP
        else:
            d = (next_rel - t) / 8.0
            ctx[12] = 0.0 if d < 0.0 else (_LA_NEXT_CLIP if d > _LA_NEXT_CLIP else d)

    # ------------------------------------------------------------------ #
    # Schedule output                                                    #
    # ------------------------------------------------------------------ #
    def _build_schedule(self, method, wall, seed=0):
        return {
            "instance_id": self.meta_id,
            "method": method,
            "seed": seed,
            "wall_seconds": wall,
            "decisions": len(self.assignments),
            "assignments": list(self.assignments),
        }

    def to_schedule(self, method: str, seed: int = 0) -> dict:
        """Emit the schedule dict for the episode just run (step or run_policy)."""
        return self._build_schedule(method, time.perf_counter() - self._t_reset, seed)
