#!/usr/bin/env python
"""
Supplementary Section S3: secondary metrics on the final evaluation.

Writes ONE fragment, paper/supp_secondary.tex, holding a booktabs `tabular`
followed by its note; paper/supplementary.tex supplies the float and caption
and \\input{}s this file.

The scope is the final evaluation's empirical instances on the four campuses
that carry the verdict, at the workload-implied reference capacity (crew
multiplier 1.0). Every method family that scores the whole scope gets a row:
the seven transparent rules individually, the two learned pools as their
per-configuration seed mean, and the rolling optimiser on the configuration
subsample it ran on.

The metrics are the ones already carried by the released per-configuration
rows: makespan, mean flow time, and the service-window breach share overall
and per priority class. Weighted tardiness, the primary objective, is not
repeated here; the manuscript reports it.

One script, idempotent, reading ONLY results/r4_final/results.csv; no number is
typed into this file.

  PYTHONPATH=src python scripts/r4_supp_secondary.py
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fmwos.io import normalize_method_column                     # noqa: E402

RESULTS = ROOT / "results" / "r4_final" / "results.csv"
OUT = ROOT / "paper" / "supp_secondary.tex"

# Scope of the final evaluation that carries the verdict.
VERDICT_CAMPUSES = (5, 9, 10, 12)
REFERENCE_MULTIPLIER = 1.0
EMPIRICAL_REGIME = "final-empirical"

RULES = [("edd", "EDD"), ("pfifo", "pFIFO"), ("wmdd", "WMDD"), ("atc", "ATC"),
         ("wspt", "WSPT"), ("lpt", "LPT"), ("random", "Random")]
MLP_SEEDS = ["v2rl%d" % s for s in range(301, 311)]
ATTN_SEEDS = ["v2at%d" % s for s in range(301, 311)]
ROLLING = "rollcp2"

# (column, header, decimals)
METRICS = [("makespan", "Makespan", 2),
           ("mean_flow", "Mean flow", 2),
           ("breach_share", "Breach share", 4),
           ("breach_p1", "P1", 4),
           ("breach_p2", "P2", 4),
           ("breach_p3", "P3", 4),
           ("breach_p4", "P4", 4)]
CLASS_COLS = ["breach_p1", "breach_p2", "breach_p3", "breach_p4"]


def scope(df):
    return df[(df["regime"] == EMPIRICAL_REGIME)
              & (df["campus"].isin(VERDICT_CAMPUSES))
              & (df["crew_multiplier"] == REFERENCE_MULTIPLIER)]


def per_configuration(sub, methods):
    """One row per configuration: the mean over the given methods.

    For a single method this is that method's own row; for a pool it is the
    seed mean on the same configuration, which is the "seeds on average"
    aggregate the manuscript uses everywhere, never a best-of-seeds figure.
    """
    d = sub[sub["method"].isin(methods)]
    if d.empty:
        return None
    cols = [c for c, _, _ in METRICS]
    return d.groupby("id", sort=True)[cols].mean()


def cells(agg):
    """Column means over configurations, and the counts they average over."""
    out, counts = {}, {}
    for col, _, _ in METRICS:
        v = agg[col].dropna()
        out[col] = float(v.mean())
        counts[col] = int(len(v))
    return out, counts


def fmt(v, decimals):
    return f"{v:,.{decimals}f}"


def main():
    df = normalize_method_column(pd.read_csv(RESULTS))
    df["campus"] = df["campus"].astype(int)
    df["crew_multiplier"] = df["crew_multiplier"].astype(float)
    sub = scope(df)
    if sub.empty:
        raise SystemExit("no rows in the verdict-campus reference-capacity scope")

    rows, class_counts = [], {}
    families = ([([m], lab) for m, lab in RULES]
                + [(MLP_SEEDS, "Policy pool (mean of %d MLP seeds)" % len(MLP_SEEDS)),
                   (ATTN_SEEDS, "Attention pool (mean of %d seeds)" % len(ATTN_SEEDS)),
                   ([ROLLING], "Rolling CP-SAT (own subsample)")])
    for methods, label in families:
        agg = per_configuration(sub, methods)
        if agg is None:
            raise SystemExit("no rows for %s in this scope" % label)
        vals, counts = cells(agg)
        rows.append((label, len(agg), vals))
        class_counts[label] = counts

    # every full-coverage family must cover the same configurations, and the
    # per-class averages must rest on the same instances for every family
    n_full = {n for lab, n, _ in rows if not lab.startswith("Rolling")}
    if len(n_full) != 1:
        raise SystemExit("uneven configuration coverage across families: %s" % n_full)
    ref = class_counts[rows[0][0]]
    for lab, _, _ in rows:
        if lab.startswith("Rolling"):
            continue
        if class_counts[lab] != ref:
            raise SystemExit("uneven per-class coverage for %s" % lab)

    n_cfg = sorted(n_full)[0]
    n_roll = [n for lab, n, _ in rows if lab.startswith("Rolling")][0]
    n_clusters = sub["id"].map(sub.drop_duplicates("id").set_index("id")["campus"]).nunique()

    L = [r"% Supplementary Section S3: secondary metrics on the final evaluation.",
         r"% Generated by scripts/r4_supp_secondary.py from",
         r"%   results/r4_final/results.csv",
         r"% Do not edit by hand: rerun the script.",
         r"\setlength{\tabcolsep}{5pt}",
         r"\footnotesize",
         r"\begin{tabular}{@{}l r " + "r" * len(METRICS) + r"@{}}",
         r"\toprule"]
    L.append(" & ".join(["", "", "", "", r"\multicolumn{5}{c}{Breach share}"])
             + r" \\")
    L.append(r"\cmidrule(lr){5-9}")
    L.append(" & ".join(["Method", "$n$", "Makespan", "Mean flow", "All",
                         "P1", "P2", "P3", "P4"]) + r" \\")
    L.append(r"\midrule")
    for i, (label, n, vals) in enumerate(rows):
        if label.startswith(("Policy pool", "Rolling")):
            L.append(r"\addlinespace[2pt]")
        L.append(" & ".join([label, f"{n:,}"]
                            + [fmt(vals[c], d) for c, _, d in METRICS]) + r" \\")
    L.append(r"\bottomrule")
    L.append(r"\end{tabular}")
    L.append("")
    L.append(r"\vspace{2pt}")

    # The caption states the scope, the units and the pool construction, so the
    # note carries only what the caption does not: the counts each column rests
    # on, and why no cell is emphasised.
    note = (
        "Note: every full-coverage family is scored on the same %s "
        "configurations, and the rolling optimiser on the %s-configuration "
        "subsample it ran on, which its $n$ reports. The per-class columns "
        "rest on the configurations that hold work of that class (%s for P1, "
        "%s for P2, %s for P3, %s for P4), so a class column is not a "
        "decomposition of the overall column. Lower is better in every column, "
        "and no cell is emphasised: these are descriptive measurements without "
        "paired intervals."
        % (f"{n_cfg:,}", f"{n_roll:,}",
           *[f"{ref[c]:,}" for c in CLASS_COLS]))
    L.append("\\parbox{\\linewidth}{\\scriptsize %s}" % note)

    OUT.write_text("\n".join(L) + "\n")
    print("wrote %s" % OUT.relative_to(ROOT))
    print("  scope: %d configurations over %d campuses, %d families"
          % (n_cfg, n_clusters, len(rows)))
    print("  rolling subsample: %d configurations" % n_roll)
    print("  per-class configuration counts: "
          + ", ".join("%s %d" % (c, ref[c]) for c in CLASS_COLS))
    for label, n, vals in rows:
        print("  %-38s n=%3d  " % (label, n)
              + "  ".join("%s=%s" % (c, fmt(vals[c], d)) for c, _, d in METRICS))


if __name__ == "__main__":
    sys.exit(main())
