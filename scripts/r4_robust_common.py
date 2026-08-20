#!/usr/bin/env python
"""Shared machinery for the R4 robustness runners (docs/protocol.md §R4 (design S4)).

Four runners -- ``r4_pmodel.py`` (R4.7 processing-time models), ``r4_capacity.py``
(R4.8 crew estimator), ``r4_backdate.py`` (R4.9 release times) and
``r4_sla_scenarios.py`` (R4.10 service windows) -- ask one question of four
different perturbations: does the method ranking survive it?  They therefore
share a target-set reader, a method set, a scoring path and an output contract,
which live here so each runner holds only the transform it is about.

Target sets
-----------
The runners consume the Eval-B corpus that ``scripts/r4_final_instances.py``
builds under ``data/processed/instances_r4/`` with ``index_r4.csv`` (spec S2).
That corpus is built once, after the method list is frozen, so it may not exist
yet; :func:`eval_b_replay_rows` fails with an explicit message rather than a
KeyError when the index is absent.  ``--smoke`` instead runs the identical code
path on four RELEASED v1.0 replay TEST instances (one per campus, size 150), so
every runner is provable end to end before Eval-B exists.  Smoke output always
goes to a ``smoke/`` subdirectory so it can never be read as a result.

Methods (frozen, identical in all four runners)
----------------------------------------------
  rules : edd, pfifo, wspt, atc, wmdd, lpt, random  through ``fmwos.pdrs.dispatch``
          at seed 301;
  policy: the frozen v2 MLP pool, ``results/p3_train/v2/seed301..310/best.pt``,
          greedy argmax rollouts through ``DispatchEnv`` exactly as
          ``scripts/p4_dyneval.py`` runs them, tagged ``v2rl<seed>``.
No CP-SAT: the robustness endpoint is the ranking of the online methods, and the
rolling solver's cost would multiply four runs for no additional endpoint.

Scoring
-------
Every schedule is scored ONLY by ``fmwos.validator`` on the TRANSFORMED instance
object.  The validator checks ``schedule.instance_id == instance.meta.id``, so a
transform must set a new ``meta.id`` and the schedule must be produced against
the transformed instance; :func:`score_instance` enforces that by construction
(it is handed one instance and runs everything on it).

Determinism and reruns
----------------------
Each runner builds its full task list in a fixed order, runs it through a fork
pool, sorts the collected rows by that same key, and writes ``results.csv`` in
one atomic replace.  A rerun therefore rewrites the file wholesale and can never
duplicate a row; there is no shard state to go stale.
"""

from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

# One thread per worker: the box is shared, a dispatch is far too small to
# parallelise internally, and a batch-1 policy forward is SLOWER on several
# threads (per-operator barriers dominate).  Set before numpy/torch are imported.
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

import multiprocessing as mp  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

# torch / fmwos.policy are imported LAZILY inside the worker (fork-safety: the
# parent must never initialise torch before fork()).
from fmwos import pdrs                    # noqa: E402
from fmwos.env import DispatchEnv         # noqa: E402
from fmwos.validator import validate      # noqa: E402

# --------------------------------------------------------------------------- #
# Locations
# --------------------------------------------------------------------------- #
INST_ROOT_V10 = ROOT / "data" / "processed" / "instances"       # released, read-only
INDEX_V10 = INST_ROOT_V10 / "index.csv"
INST_ROOT_R4 = ROOT / "data" / "processed" / "instances_r4"     # Eval-B (spec S2)
INDEX_R4 = INST_ROOT_R4 / "index_r4.csv"
OUT_ROOT = ROOT / "results" / "r4_robustness"
V2_TRAIN_DIR = ROOT / "results" / "p3_train" / "v2"
RAW_CSV = ROOT / "data" / "raw" / "FMUCD.csv"

# --------------------------------------------------------------------------- #
# Frozen method set
# --------------------------------------------------------------------------- #
RULES = ["edd", "pfifo", "wspt", "atc", "wmdd", "lpt", "random"]
SEED = 301                 # dispatcher seed (only the 'random' rule consumes it)
RL_TAG = "v2rl"            # method column prefix for the frozen v2 MLP pool
TORCH_THREADS = 1          # see the module header: batch-1 forward wants one
DEFAULT_WORKERS = 12

# Smoke target set: the first replay TEST instance (sorted id) of size 150 in
# each of these campuses, from the RELEASED v1.0 corpus.  Four campuses rather
# than four instances of one campus, so a smoke run exercises four trade mixes.
SMOKE_CAMPUSES = [1, 2, 5, 9]
SMOKE_SIZE = 150

METRIC_FIELDS = ["method", "seed", "feasible", "wwt", "makespan", "mean_flow",
                 "breach_share", "wall_seconds"]


# --------------------------------------------------------------------------- #
# Target sets
# --------------------------------------------------------------------------- #
def _read_index(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _instance_path(root, row):
    """Absolute path of an index row's instance JSON (``path`` column first)."""
    p = row.get("path")
    if p:
        cand = Path(root) / p
        if cand.exists():
            return cand
    return (Path(root) / ("c%02d" % int(row["campus"])) / str(row.get("track", "replay"))
            / str(row["size_class"]) / (row["id"] + ".json"))


def eval_b_replay_rows(index_csv=INDEX_R4, inst_root=INST_ROOT_R4):
    """The Eval-B empirical-track base set: one dict per replay instance.

    Returns rows sorted by (campus, size, id) with an absolute ``path``.  Raises
    SystemExit with an actionable message when the Eval-B index does not exist
    yet -- the corpus is built by scripts/r4_final_instances.py (spec S2) after
    the method list is frozen, and a robustness runner must never silently fall
    back to another corpus.
    """
    index_csv = Path(index_csv)
    if not index_csv.exists():
        raise SystemExit(
            "Eval-B index not found: %s\n"
            "  The robustness runners score the Eval-B corpus (docs/protocol.md §R4 "
            "S2), which scripts/r4_final_instances.py builds under %s.\n"
            "  Build it first, or run this script with --smoke to exercise the "
            "same code path on four released v1.0 replay TEST instances."
            % (index_csv, inst_root))
    rows = []
    for r in _read_index(index_csv):
        if str(r.get("track", "")).strip().lower() != "replay":
            continue
        rows.append({
            "id": r["id"], "campus": int(r["campus"]),
            "size": int(r["size_class"]),
            "window_start": str(r.get("window_start", "")),
            "window_bh": float(r["window_bh"]) if r.get("window_bh") else None,
            "path": str(_instance_path(inst_root, r)),
        })
    if not rows:
        raise SystemExit("no replay rows in %s -- Eval-B empirical track is empty"
                         % index_csv)
    rows.sort(key=lambda r: (r["campus"], r["size"], r["id"]))
    return rows


def smoke_replay_rows(n=len(SMOKE_CAMPUSES)):
    """``n`` released v1.0 replay TEST instances, one per campus, size 150.

    Deterministic: within a campus the first row in sorted-id order.  These
    instances are read-only v1.0 artifacts; a smoke run never writes near them.
    """
    if not INDEX_V10.exists():
        raise SystemExit("released instance index not found: %s" % INDEX_V10)
    idx = _read_index(INDEX_V10)
    rows = []
    for campus in SMOKE_CAMPUSES[:n]:
        cell = [r for r in idx
                if str(r.get("track", "")).strip().lower() == "replay"
                and str(r.get("split", "")).strip().lower() == "test"
                and int(r["campus"]) == campus
                and int(r["size_class"]) == SMOKE_SIZE]
        cell.sort(key=lambda r: r["id"])
        if not cell:
            continue
        r = cell[0]
        rows.append({
            "id": r["id"], "campus": int(r["campus"]),
            "size": int(r["size_class"]),
            "window_start": str(r.get("window_start", "")),
            "window_bh": float(r["window_bh"]) if r.get("window_bh") else None,
            "path": str(_instance_path(INST_ROOT_V10, r)),
        })
    if not rows:
        raise SystemExit("no released replay TEST instances matched the smoke scope "
                         "(campuses %s, size %d)" % (SMOKE_CAMPUSES, SMOKE_SIZE))
    return rows


def base_rows(smoke):
    """The base instance set: Eval-B replay, or the smoke subset of v1.0."""
    return smoke_replay_rows() if smoke else eval_b_replay_rows()


# --------------------------------------------------------------------------- #
# Frozen policy pool
# --------------------------------------------------------------------------- #
def rl_seeds(train_dir=V2_TRAIN_DIR):
    """Seeds of the frozen v2 MLP pool, discovered as ``seed<N>/best.pt``."""
    seeds = []
    p = Path(train_dir)
    if p.exists():
        for d in sorted(p.glob("seed*")):
            m = re.match(r"seed(\d+)$", d.name)
            if m and d.is_dir() and (d / "best.pt").exists():
                seeds.append(int(m.group(1)))
    return sorted(set(seeds))


def rl_method(seed):
    return "%s%d" % (RL_TAG, seed)


def method_order(seeds):
    """Map method name -> sort rank, so every runner's CSV orders rows alike."""
    names = list(RULES) + [rl_method(s) for s in seeds]
    return {m: i for i, m in enumerate(names)}


_POLICY_CACHE = {}


def get_policy(seed, train_dir=V2_TRAIN_DIR):
    """Load (and cache per worker process) one frozen v2 MLP checkpoint."""
    key = (str(train_dir), int(seed))
    pol = _POLICY_CACHE.get(key)
    if pol is None:
        import torch  # lazy: only inside the worker
        from fmwos.policy import DispatchPolicy
        torch.set_num_threads(TORCH_THREADS)
        pol = DispatchPolicy.load(str(Path(train_dir) / ("seed%d" % seed) / "best.pt"),
                                  map_location="cpu")
        pol.eval()
        _POLICY_CACHE[key] = pol
    return pol


def rl_rollout(instance, seed, train_dir=V2_TRAIN_DIR):
    """Greedy policy rollout through DispatchEnv (scripts/p4_dyneval.py path)."""
    pol = get_policy(seed, train_dir)
    env = DispatchEnv(instance)
    obs = env.reset()
    done = False
    while not done:
        a, _, _, _ = pol.act(obs, greedy=True, device="cpu")
        obs, _r, done, _info = env.step(a)
    return env.to_schedule(rl_method(seed), seed=seed)


# --------------------------------------------------------------------------- #
# Scoring
# --------------------------------------------------------------------------- #
def metric_row(method, seed, sched, res):
    """The metric half of a result row (the runner adds its config columns)."""
    m = res["metrics"]
    return {
        "method": method, "seed": seed,
        "feasible": int(bool(res["feasible"])),
        "wwt": m["WWT"], "makespan": m["makespan"], "mean_flow": m["mean_flow"],
        "breach_share": m["breach_share"],
        "wall_seconds": sched.get("wall_seconds"),
    }


def score_instance(instance, seeds, train_dir=V2_TRAIN_DIR):
    """Run every frozen method on ONE instance object; validate each schedule.

    Returns ``(rows_by_method, infeasible)``.  Both the schedule and the
    validation are produced against the instance handed in, which is what makes
    validator check (f) (schedule.instance_id == instance.meta.id) a real check
    on a transformed instance rather than a formality.
    """
    rows, infeasible = {}, []
    for rule in RULES:
        sched = pdrs.dispatch(instance, rule, seed=SEED)
        res = validate(instance, sched)
        rows[rule] = metric_row(rule, SEED, sched, res)
        if not res["feasible"]:
            infeasible.append({"method": rule, "violations": res["violations"][:3]})
    for t in seeds:
        sched = rl_rollout(instance, t, train_dir)
        res = validate(instance, sched)
        meth = rl_method(t)
        rows[meth] = metric_row(meth, t, sched, res)
        if not res["feasible"]:
            infeasible.append({"method": meth, "violations": res["violations"][:3]})
    return rows, infeasible


def u_realized(instance):
    """Realized utilization = sum p_bh / (technicians * window_bh)."""
    total_p = sum(float(w["p_bh"]) for w in instance["work_orders"])
    n_crew = len(instance["technicians"])
    win = float(instance["meta"]["window_bh"])
    denom = n_crew * win
    return round(float(total_p / denom), 6) if denom > 0 else 0.0


# --------------------------------------------------------------------------- #
# Pool driver + output
# --------------------------------------------------------------------------- #
def run_pool(tasks, worker, workers, progress_every=25):
    """Run ``worker`` over ``tasks`` in a fork pool; collect rows.

    ``worker(task)`` must return ``{"id", "ok", "rows", "infeasible"[, "error",
    "traceback"]}`` and must never raise: an exception in one task is reported
    and the remaining tasks still run.  Returns (rows, n_errors, n_infeasible).
    """
    rows, n_errors, n_infeasible, completed = [], 0, 0, 0
    total = len(tasks)
    t_start = time.perf_counter()
    ctx = mp.get_context("fork")
    with ctx.Pool(processes=workers) as pool:
        for res in pool.imap(worker, tasks, chunksize=1):
            completed += 1
            if not res.get("ok"):
                n_errors += 1
                print("[ERROR] %s: %s" % (res.get("id"), res.get("error")))
                if res.get("traceback"):
                    print(res["traceback"])
            for it in res.get("infeasible", []):
                n_infeasible += 1
                print("[INFEASIBLE] id=%s method=%s :: %s"
                      % (res.get("id"), it.get("method"),
                         " | ".join(it.get("violations", []))))
            rows.extend(res.get("rows", []))
            if completed % progress_every == 0 or completed == total:
                el = time.perf_counter() - t_start
                eta = el / completed * (total - completed) if completed else 0.0
                print("  progress %d/%d  elapsed %s  eta %s  (%d infeasible, "
                      "%d errors)" % (completed, total, fmt_hms(el), fmt_hms(eta),
                                      n_infeasible, n_errors), flush=True)
    return rows, n_errors, n_infeasible


def write_csv(path, fields, rows):
    """Atomic CSV write (tmp + os.replace), so a rerun never leaves a partial
    file and never appends duplicate rows."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    os.replace(tmp, path)
    return path


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w") as f:
        json.dump(payload, f, indent=2, sort_keys=False)
    os.replace(tmp, path)
    return path


def git_describe():
    try:
        return subprocess.check_output(
            ["git", "describe", "--tags", "--always", "--dirty"],
            cwd=str(ROOT), stderr=subprocess.DEVNULL).decode().strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def fmt_hms(seconds):
    seconds = int(max(0, seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return "%dh%02dm%02ds" % (h, m, s)


def out_dir(name, smoke, out_root=OUT_ROOT):
    """``results/r4_robustness/<name>/`` (+ ``/smoke`` for a smoke run)."""
    d = Path(out_root) / name / ("smoke" if smoke else "")
    d.mkdir(parents=True, exist_ok=True)
    return d


def print_header(title, smoke, base, seeds, workers, dest):
    print("%s%s" % (title, "  [SMOKE]" if smoke else ""))
    print("  base set   : %d instance(s) (%s)"
          % (len(base), "released v1.0 replay TEST" if smoke else "Eval-B replay"))
    print("  rules      : %s" % ", ".join(RULES))
    print("  policies   : %s" % ", ".join(rl_method(s) for s in seeds))
    print("  workers    : %d" % workers)
    print("  out        : %s" % dest, flush=True)
