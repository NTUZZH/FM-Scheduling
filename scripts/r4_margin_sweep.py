#!/usr/bin/env python
"""R4 margin-sensitivity sweep over the frozen final-evaluation analyses.

The practical-equivalence margin is max(MARGIN_ABS, MARGIN_REL * |reference
mean|) = max(1.0 weighted unit, 1% of the comparator's mean TWT).  This script
re-runs the released analysis pipelines (scripts/r4_analysis.py and
scripts/r4_robust_analysis.py, --step analysis) with BOTH margin components
halved and doubled, into temporary directories, and reduces the outcome to a
per-scope membership comparison against the released analysis.  The bootstrap
CIs are seed-deterministic (N_BOOT resamples, master seed in fmwos.stats), so
only the equivalence margin differs between runs: every change below is a pure
margin effect.

Outputs
-------
results/r4_final/analysis/margin_sensitivity.csv   one row per membership change
results/r4_final/analysis/margin_sensitivity.md    summary
paper/macros_r4e.tex                               macros cited by the paper

Run (about five minutes, CPU only):
    PYTHONPATH=src python scripts/r4_margin_sweep.py
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

KEY = ["scope_type", "scope", "method"]
SWEEPS = (("half", 0.5), ("double", 2.0))
ANALYSES = (
    ("final", ROOT / "scripts/r4_analysis.py",
     ROOT / "results/r4_final/analysis/equivalence.csv"),
    ("robustness", ROOT / "scripts/r4_robust_analysis.py",
     ROOT / "results/r4_robustness/analysis/equivalence.csv"),
)

# The child rewrites the margin defaults bound at function-definition time in
# fmwos.stats (module-constant reassignment alone does not reach them).
CHILD = """
import sys, runpy, inspect, types
sys.path.insert(0, {src!r})
from fmwos import stats
K = {k}
stats.MARGIN_ABS *= K
stats.MARGIN_REL *= K
for name in dir(stats):
    fn = getattr(stats, name)
    if not isinstance(fn, types.FunctionType):
        continue
    params = list(inspect.signature(fn).parameters)
    if 'margin_abs' not in params:
        continue
    defs = list(fn.__defaults__ or ())
    tail = params[-len(defs):]
    for i, p in enumerate(tail):
        if p in ('margin_abs', 'margin_rel'):
            defs[i] = defs[i] * K
    fn.__defaults__ = tuple(defs)
sys.argv = ['sweep', '--step', 'analysis', '--out', {out!r},
            '--paper-dir', {paper!r}]
runpy.run_path({script!r}, run_name='__main__')
"""


def run_sweep(script: Path, out: Path, k: float) -> None:
    code = CHILD.format(src=str(ROOT / "src"), k=k, out=str(out),
                        paper=str(out / "paper"), script=str(script))
    r = subprocess.run([sys.executable, "-c", code], cwd=ROOT,
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("sweep failed (%s x%s):\n%s" % (script.name, k,
                                                 r.stderr[-2000:]))


def main() -> int:
    rows = []
    counts = {}
    with tempfile.TemporaryDirectory(prefix="r4_margin_") as td:
        for aname, script, base_csv in ANALYSES:
            base = pd.read_csv(base_csv)
            for tag, k in SWEEPS:
                out = Path(td) / f"{aname}_{tag}"
                print(f"== {aname} margin x{k} ...", flush=True)
                run_sweep(script, out, k)
                alt = pd.read_csv(out / "equivalence.csv")
                jk = [c for c in KEY if c in base.columns and c in alt.columns]
                if "check" in base.columns:          # robustness layout
                    jk = ["check", "arm", "stratum", "method"]
                m = base[jk + ["in_equivalence_set", "verdict"]].merge(
                    alt[jk + ["in_equivalence_set", "verdict"]], on=jk,
                    suffixes=("_base", "_swept"))
                ch = m[m.in_equivalence_set_base != m.in_equivalence_set_swept]
                counts[(aname, tag)] = (len(m), len(ch),
                                        int(((m.verdict_base == "equivalent")
                                             & (m.verdict_swept == "worse")).sum()),
                                        int(((m.verdict_base == "worse")
                                             & (m.verdict_swept == "equivalent")).sum()))
                for _, r in ch.iterrows():
                    rows.append({"analysis": aname, "sweep": tag,
                                 **{c: r[c] for c in jk},
                                 "verdict_base": r.verdict_base,
                                 "verdict_swept": r.verdict_swept})

    out_csv = ROOT / "results/r4_final/analysis/margin_sensitivity.csv"
    pd.DataFrame(rows).to_csv(out_csv, index=False)

    lines = ["# Margin-sensitivity sweep (margin components x0.5 and x2)", ""]
    for (aname, tag), (n, ch, ew, we) in counts.items():
        lines.append(f"* {aname} x{tag}: {ch} of {n} memberships change; "
                     f"equivalent->worse flips {ew}; worse->set joins {we}")
    md = "\n".join(lines) + "\n"
    (ROOT / "results/r4_final/analysis/margin_sensitivity.md").write_text(md)
    print(md)

    nf, cf_h = counts[("final", "half")][0], counts[("final", "half")][1]
    cf_d = counts[("final", "double")][1]
    nr = counts[("robustness", "half")][0]
    cr_h = counts[("robustness", "half")][1]
    cr_d = counts[("robustness", "double")][1]
    flips = sum(v[2] + v[3] for v in counts.values())
    macros = [
        "%% paper/macros_r4e.tex -- generated by scripts/r4_margin_sweep.py",
        "%% from the released analyses re-run with the equivalence margin",
        "%% halved and doubled (results/r4_final/analysis/margin_sensitivity.*).",
        "\\newcommand{\\mgsMemberships}{%d}" % nf,
        "\\newcommand{\\mgsHalfLeave}{%d}" % cf_h,
        "\\newcommand{\\mgsDoubleJoin}{%d}" % cf_d,
        "\\newcommand{\\mgsRobMemberships}{%d}" % nr,
        "\\newcommand{\\mgsRobHalfLeave}{%d}" % cr_h,
        "\\newcommand{\\mgsRobDoubleJoin}{%d}" % cr_d,
        "\\newcommand{\\mgsWorseFlips}{%d}" % flips,
    ]
    (ROOT / "paper/macros_r4e.tex").write_text("\n".join(macros) + "\n")
    print("wrote paper/macros_r4e.tex")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
