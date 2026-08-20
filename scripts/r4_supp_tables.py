#!/usr/bin/env python
"""
Supplementary Section S5: the comparison tables behind every verdict.

Writes ONE file, paper/supp_tables.tex, holding seven complete longtable
environments (caption, label and notes included); paper/supplementary.tex
\\input{}s it.

  S4  empirical anchors, verdict campuses, by crew multiplier
  S5  generator cells, pooled and by target utilisation
  S6  transfer campus, reference capacity
  S7  stress campus, reference capacity
  S8  empirical anchors, by realised-utilisation bin
  S9  robustness suite: stability of the equivalence set
  S10 preventive-work visibility: within-arm contrasts

One script, idempotent, reading ONLY the three definitive-analysis outputs;
no number is typed into this file.

  results/r4_final/analysis/equivalence.csv
  results/r4_robustness/analysis/stability.csv
  results/r4_visibility/analysis/vis_effect.csv

  PYTHONPATH=src python scripts/r4_supp_tables.py
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "paper" / "supp_tables.tex"
ANA_FINAL = ROOT / "results" / "r4_final" / "analysis"
ANA_ROB = ROOT / "results" / "r4_robustness" / "analysis"
ANA_VIS = ROOT / "results" / "r4_visibility" / "analysis"

EQ = pd.read_csv(ANA_FINAL / "equivalence.csv")
STAB = pd.read_csv(ANA_ROB / "stability.csv")
VIS = pd.read_csv(ANA_VIS / "vis_effect.csv")

# ---------------------------------------------------------------------------
# formatting (same conventions as scripts/r4_tables.py: thousands separators,
# math minus, no hand-typed number anywhere)
# ---------------------------------------------------------------------------
MINUS = "$-$"


def _sign(v, body):
    # A value that rounds to zero prints as zero. Without this a small negative
    # number formats as a negative zero, which reads as a direction the data
    # does not support.
    if float(body.replace(",", "")) == 0.0:
        return body
    return (MINUS if v < 0 else "") + body


def fmt_mean(v):
    a = abs(v)
    if a < 10:
        return _sign(v, f"{a:.2f}")
    if a < 1000:
        return _sign(v, f"{a:.1f}")
    return _sign(v, f"{a:,.0f}")


def fmt_diff(v):
    a = abs(v)
    if a < 10:
        return _sign(v, f"{a:.2f}")
    if a < 1000:
        return _sign(v, f"{a:.1f}")
    return _sign(v, f"{a:,.0f}")


def fmt_pct(v):
    a = abs(v)
    if a < 10:
        return _sign(v, f"{a:.2f}")
    return _sign(v, f"{a:.1f}")


def fmt_ci(lo, hi, f=fmt_diff):
    return f"[{f(lo)}, {f(hi)}]"


def fmt_p(p):
    p = float(p)
    if p < 0.001:
        return "$<$0.001"
    return f"{p:.3f}"


def fmt_int(v):
    return f"{int(v):,}"


def bf(s, on):
    return "\\textbf{" + s + "}" if on else s


# ---------------------------------------------------------------------------
# labels
# ---------------------------------------------------------------------------
PRETTY_RULE = {"edd": "EDD", "pfifo": "pFIFO", "wmdd": "WMDD", "atc": "ATC",
               "wspt": "WSPT", "lpt": "LPT", "random": "Random"}


def method_label(m):
    if m in PRETTY_RULE:
        return PRETTY_RULE[m]
    if m.startswith("v2rl"):
        return "MLP seed " + m[4:]
    if m.startswith("v2at"):
        return "Attention seed " + m[4:]
    if m.startswith("rl"):
        return "Curriculum-v1 seed " + m[2:]
    return m.replace("_", "\\_")


FAMILY_LABEL = {"rule-vs-rule": "rule vs.\\ rule",
                "rule-vs-policy": "rule vs.\\ policy",
                "policy-vs-rule": "policy vs.\\ rule",
                "policy-vs-policy": "policy vs.\\ policy"}

UBIN_LABEL = {"<0.5": "$u < 0.5$", "0.5-0.8": "$0.5 \\leq u < 0.8$",
              "0.8-1.0": "$0.8 \\leq u < 1.0$",
              "1.0-1.2": "$1.0 \\leq u < 1.2$", ">=1.2": "$u \\geq 1.2$"}

INSET = {1: "yes", 0: "no"}


# ---------------------------------------------------------------------------
# shared longtable plumbing
# ---------------------------------------------------------------------------
EQ_COLS = r"@{}l l r l r l c@{}"
EQ_HEAD = " & ".join(["Method", "Holm family", "Mean TWT",
                      "$\\Delta$ vs.\\ scope best [95\\% CI]", "Holm $p$",
                      "Verdict", "In set"]) + r" \\"
EQ_NCOL = 7


def longtable_open(colspec, ncol, head, caption, label):
    return [r"\begingroup",
            r"\setlength{\tabcolsep}{4pt}",
            r"\footnotesize",
            r"\begin{longtable}{%s}" % colspec,
            r"\caption{%s}\label{%s}\\" % (caption, label),
            r"\toprule",
            head,
            r"\midrule",
            r"\endfirsthead",
            r"\multicolumn{%d}{@{}l}{\footnotesize Table~\thetable\ "
            r"(continued)}\\" % ncol,
            r"\toprule",
            head,
            r"\midrule",
            r"\endhead",
            r"\midrule",
            r"\multicolumn{%d}{r@{}}{\footnotesize continued on the next "
            r"page}\\" % ncol,
            r"\endfoot",
            r"\bottomrule",
            r"\endlastfoot"]


def longtable_close(note):
    return [r"\end{longtable}",
            r"\vspace{-6pt}",
            r"\noindent\parbox{\linewidth}{\scriptsize %s}" % note,
            r"\endgroup",
            r"\bigskip",
            ""]


def group_row(ncol, text, first, stats=None):
    """Scope block header: an italic label, optionally a smaller stats line.

    Both are single-line \\multicolumn cells, so each must stay inside the text
    width; the stats line is set smaller for that reason.
    """
    rows = [] if first else [r"\addlinespace[3pt]"]
    # \\* keeps the block header with the rows it introduces across a page break.
    rows.append(r"\multicolumn{%d}{@{}l}{\textit{%s}}\\*" % (ncol, text))
    if stats:
        rows.append(r"\multicolumn{%d}{@{}l}{\scriptsize %s}\\*" % (ncol, stats))
    rows.append(r"\addlinespace[1pt]")
    return rows


# ---------------------------------------------------------------------------
# equivalence tables (one per scope group)
# ---------------------------------------------------------------------------
def scope_frame(scope_type, scope):
    d = EQ[(EQ.scope_type == scope_type) & (EQ.scope == scope)]
    return d.sort_values("mean", kind="mergesort")


def scope_stats(d):
    """Scope size, best method and margin, all read from the frame."""
    best = d.best_method.iloc[0]
    n_cfg = sorted(set(int(x) for x in d.n_configs))
    n_clu = sorted(set(int(x) for x in d.n_clusters))
    cfg = (fmt_int(n_cfg[0]) if len(n_cfg) == 1
           else "%s--%s" % (fmt_int(n_cfg[0]), fmt_int(n_cfg[-1])))
    clu = (fmt_int(n_clu[0]) if len(n_clu) == 1
           else "%s--%s" % (fmt_int(n_clu[0]), fmt_int(n_clu[-1])))
    return ("%s configurations over %s base-instance clusters, %d methods; "
            "scope best %s at %s; equivalence margin %s"
            % (cfg, clu, len(d), method_label(best),
               fmt_mean(float(d.mean_best.iloc[0])),
               fmt_diff(float(d.margin.max()))))


def eq_rows(d):
    out = []
    for _, r in d.iterrows():
        inset = bool(int(r.in_equivalence_set))
        out.append(" & ".join([
            method_label(r.method),
            FAMILY_LABEL.get(r.family, r.family),
            bf(fmt_mean(float(r["mean"])), inset),
            bf(fmt_diff(float(r.mean_diff)) + "~"
               + fmt_ci(float(r.ci_lo), float(r.ci_hi)), inset),
            fmt_p(r.holm_p),
            r.verdict,
            INSET[int(r.in_equivalence_set)]]) + r" \\")
    return out


EQ_NOTE_COMMON = (
    "Every method is paired against the scope's best-mean method on the "
    "configurations both solved, so the difference column is a within-scope "
    "paired contrast and never a difference of independent means. A negative "
    "difference favours the row. Intervals are 95\\% cluster bootstraps over "
    "base instances (10{,}000 resamples); $p$ is a paired Wilcoxon "
    "signed-rank $p$-value, Holm-adjusted inside the comparison family named "
    "in the second column, with the best method's own row excluded from the "
    "correction. The verdict compares the whole interval with the protocol "
    "margin, the larger of 1.0 and 1\\% of the reference mean: equivalent "
    "means the interval lies inside the margin, worse that it lies above it, "
    "better that it lies below it, and inconclusive that it straddles a margin "
    "edge. Bold marks membership in the scope's practical-equivalence set, "
    "applied mechanically to every row with no exceptions. Weighted tardiness "
    "is in business hours and lower is better. Rows are ordered by mean within "
    "each scope.")


EQ_NOTE_SHORT = (
    "Columns, the paired construction, the equivalence margin and the bold rule "
    "are those of Table~\\ref{tab:supp-empm}. Weighted tardiness is in business "
    "hours and lower is better.")


def eq_table(name, caption, label, scopes, note):
    L = longtable_open(EQ_COLS, EQ_NCOL, EQ_HEAD, caption, label)
    n_rows = 0
    for i, ((st, sc), lab) in enumerate(scopes):
        d = scope_frame(st, sc)
        L += group_row(EQ_NCOL, lab, i == 0, stats=scope_stats(d))
        L += eq_rows(d)
        n_rows += len(d)
    L += longtable_close(note)
    print("  %-28s %3d method rows over %d scope%s"
          % (name, n_rows, len(scopes), "" if len(scopes) == 1 else "s"))
    return L, n_rows


EQ_TABLES = [
    ("empirical crew multipliers",
     "Empirical anchors on the verdict campuses, by crew multiplier: every "
     "scored method against the best method of its scope. This is the "
     "comparison behind the manuscript's headline equivalence table.",
     "tab:supp-empm",
     [(("emp_m", "m=1.0"), "Crew multiplier $m=1.0$ (reference capacity)"),
      (("emp_m", "m=0.8"), "Crew multiplier $m=0.8$"),
      (("emp_m", "m=0.6"), "Crew multiplier $m=0.6$")]),
    ("generator cells",
     "Generator cells, pooled and by target utilisation: every scored method "
     "against the best method of its scope.",
     "tab:supp-gen",
     [(("gen_all", "ALL"), "All generator cells pooled")]
     + [(("gen_utarget", "u_target=%s" % u), "Target utilisation $u=%s$" % u)
        for u in ("0.7", "0.9", "1.0", "1.1", "1.3")]),
    ("transfer campus",
     "Transfer campus, held out of training, at reference capacity: every "
     "scored method against the best method of the scope.",
     "tab:supp-transfer",
     [(("transfer", "campus=1|m=1.0"),
       "Transfer campus~1, reference capacity ($m=1.0$)")]),
    ("stress campus",
     "Stress campus, whose sustained overload keeps it out of every verdict "
     "scope, at reference capacity: every scored method against the best "
     "method of the scope.",
     "tab:supp-stress",
     [(("stress", "campus=2|m=1.0"),
       "Stress campus~2, reference capacity ($m=1.0$)")]),
    ("utilisation bins",
     "Empirical anchors on the verdict campuses, by realised utilisation, the "
     "instance's total work hours divided by the crew hours its window "
     "provides: every scored method against the best method of its bin. Bins "
     "are left-closed and right-open.",
     "tab:supp-ubin",
     [(("emp_ubin", "u_bin=%s" % b), UBIN_LABEL[b])
      for b in ("<0.5", "0.5-0.8", "0.8-1.0", "1.0-1.2", ">=1.2")]),
]


# ---------------------------------------------------------------------------
# robustness table (stability.csv)
# ---------------------------------------------------------------------------
ROB_ARMS = [
    ("pmodel", "sum", "Processing time: summed labour lines (locked default)"),
    ("pmodel", "max", "Processing time: dominant labour line"),
    ("pmodel", "single", "Processing time: single labour line"),
    ("capacity", "q0.95", "Capacity at p95 of weekly trade hours (locked default)"),
    ("capacity", "q0.90", "Capacity at p90 of weekly trade hours"),
    ("capacity", "q0.75", "Capacity at p75 of weekly trade hours"),
    ("backdate", "baseline", "Corrective releases as recorded (locked default)"),
    ("backdate", "backdate", "Backdated corrective releases"),
    ("sla", "baseline", "Service windows as locked (locked default)"),
    ("sla", "emg", "Service windows: P1 and P2 halved"),
    ("sla", "rtn", "Service windows: P3 and P4 halved"),
    ("sla", "pmp3", "Preventive work mapped to P3"),
]
ROB_STRATA = [("verdict", "Verdict campuses"), ("campus1", "Transfer campus~1"),
              ("campus2", "Stress campus~2")]
ROB_COLS = (r"@{}>{\raggedright\arraybackslash}p{0.215\linewidth} l r l r c r r "
            r">{\raggedright\arraybackslash}p{0.155\linewidth}@{}")
ROB_NCOL = 9
ROB_HEAD = " & ".join(["Arm", "Stratum", "$n$", "Best method", "Best mean",
                       "Set size", "Jaccard", "$\\tau_b$",
                       "Membership change"]) + r" \\"


def _members(s):
    if not isinstance(s, str) or not s.strip() or s.strip() in ("-", "--", "none"):
        return []
    return [m for m in s.split() if m not in ("-", "--", "none")]


def _change_cell(row):
    ent, left = _members(row.entered_set), _members(row.left_set)
    parts = []
    if left:
        parts.append("$-$%d out" % len(left))
    if ent:
        parts.append("$+$%d in" % len(ent))
    return "; ".join(parts) if parts else "none"


def rob_table():
    L = longtable_open(ROB_COLS, ROB_NCOL, ROB_HEAD,
                       "Robustness suite: what happens to the leading "
                       "practical-equivalence set when a modelling choice is "
                       "replaced. Each arm is re-scored end to end and ranked "
                       "against the same anchor set.",
                       "tab:supp-robust")
    n = 0
    for i, (check, arm, lab) in enumerate(ROB_ARMS):
        if i:
            L.append(r"\addlinespace[2pt]")
        block = [(slab, STAB[(STAB.check == check) & (STAB.arm == arm)
                             & (STAB.stratum == stratum)])
                 for stratum, slab in ROB_STRATA]
        block = [(slab, r.iloc[0]) for slab, r in block if not r.empty]
        for j, (slab, r) in enumerate(block):
            # \\* holds the three strata of one arm on the same page, so the
            # arm name in the first column is never left behind.
            end = r" \\" if j == len(block) - 1 else r" \\*"
            L.append(" & ".join([
                lab if j == 0 else "",
                slab,
                fmt_int(r.n_configs),
                method_label(r.best_method),
                fmt_mean(float(r.best_mean)),
                "%d $\\rightarrow$ %d" % (int(r.baseline_set_size),
                                          int(r.set_size)),
                f"{float(r.set_jaccard):.2f}",
                f"{float(r.tau_method):.2f}".replace("-", MINUS),
                _change_cell(r)]) + end)
            n += 1
    note = (
        "Set size is the anchor set followed by the arm's set, over the same "
        "scored methods and the same base instances; Jaccard is the overlap of "
        "the two sets and $\\tau_b$ is Kendall's rank correlation between the "
        "arm's method ranking and the anchor ranking. The membership column "
        "counts methods that leave and enter the set, which the released "
        "stability file names individually. Locked-default rows reproduce the "
        "anchor and are printed so each arm can be read against its own "
        "control. A low $\\tau_b$ is not evidence that the ranking moved: "
        "inside an equivalence set the order is not identified. Means are "
        "weighted tardiness in business hours, and an arm that changes "
        "processing times, capacity, releases or service windows changes the "
        "scale of the objective, so means are comparable down a column of one "
        "arm and not across arms.")
    L += longtable_close(note)
    print("  %-28s %3d rows over %d arms" % ("robustness suite", n, len(ROB_ARMS)))
    return L, n


# ---------------------------------------------------------------------------
# visibility table (vis_effect.csv)
# ---------------------------------------------------------------------------
VIS_SCOPES = [
    ("emp|ALL", "Empirical anchors, all crew multipliers"),
    ("emp|m=1.0", "Empirical anchors, $m=1.0$"),
    ("emp|m=0.8", "Empirical anchors, $m=0.8$"),
    ("emp|m=0.6", "Empirical anchors, $m=0.6$"),
    ("gen|ALL", "Generator cells, all"),
    ("gen|u=0.7", "Generator, target utilisation $u=0.7$"),
    ("gen|u=0.9", "Generator, target utilisation $u=0.9$"),
    ("gen|u=1.1", "Generator, target utilisation $u=1.1$"),
    ("gen|pm=0.2", "Generator, preventive share 0.2"),
    ("gen|pm=0.5", "Generator, preventive share 0.5"),
    ("gen|pm=0.8", "Generator, preventive share 0.8"),
    ("gen|pm=0.2|u=0.7", "Generator, preventive share 0.2, $u=0.7$"),
    ("gen|pm=0.2|u=0.9", "Generator, preventive share 0.2, $u=0.9$"),
    ("gen|pm=0.2|u=1.1", "Generator, preventive share 0.2, $u=1.1$"),
    ("gen|pm=0.5|u=0.7", "Generator, preventive share 0.5, $u=0.7$"),
    ("gen|pm=0.5|u=0.9", "Generator, preventive share 0.5, $u=0.9$"),
    ("gen|pm=0.5|u=1.1", "Generator, preventive share 0.5, $u=1.1$"),
    ("gen|pm=0.8|u=0.7", "Generator, preventive share 0.8, $u=0.7$"),
    ("gen|pm=0.8|u=0.9", "Generator, preventive share 0.8, $u=0.9$"),
    ("gen|pm=0.8|u=1.1", "Generator, preventive share 0.8, $u=1.1$"),
]
VIS_ARM_ORDER = (["atc_la", "rollcp2", "vispool"]
                 + ["visseed%d" % s for s in range(501, 506)])
VIS_ARM_LABEL = {"atc_la": "Forecast-aware ATC (rule)",
                 "rollcp2": "Rolling CP-SAT (optimiser)",
                 "vispool": "Retrained policy pool"}
VIS_LEVELS = [("8", "8"), ("40", "40"), ("full", "full")]
VIS_COLS = r"@{}l l r r l r l@{}"
VIS_NCOL = 7
VIS_HEAD = " & ".join(["Arm", "$L$ (bh)", "$n$", "Mean at $L=0$",
                       "Effect (\\% of the $L=0$ mean) [95\\% CI]", "Holm $p$",
                       "Verdict"]) + r" \\"


def vis_table():
    L = longtable_open(VIS_COLS, VIS_NCOL, VIS_HEAD,
                       "Preventive-work visibility: the paired within-arm "
                       "effect of knowing preventive work $L$ business hours "
                       "before its release, against the same arm's "
                       "zero-visibility control.",
                       "tab:supp-vis")
    n = 0
    for i, (scope, slab) in enumerate(VIS_SCOPES):
        d = VIS[VIS.scope == scope]
        if d.empty:
            continue
        L += group_row(VIS_NCOL, slab, i == 0)
        for arm in VIS_ARM_ORDER:
            a = d[d.arm == arm]
            if a.empty:
                continue
            for lev, levlab in VIS_LEVELS:
                r = a[a.level == lev]
                if r.empty:
                    continue
                r = r.iloc[0]
                label = VIS_ARM_LABEL.get(arm, "Policy seed " + arm[7:])
                L.append(" & ".join([
                    label,
                    levlab,
                    fmt_int(r.n_configs),
                    fmt_mean(float(r.mean_control)),
                    fmt_pct(float(r.pct_of_control)) + "~"
                    + fmt_ci(float(r.pct_ci_lo), float(r.pct_ci_hi), fmt_pct),
                    fmt_p(r.holm_p),
                    r.verdict]) + r" \\")
                n += 1
    note = (
        "The contrast is paired within one arm: the same arm at visibility "
        "level $L$ against itself at $L=0$, on the configurations both solved, "
        "so it measures the information and never a difference between "
        "methods. A negative effect means advance knowledge lowered weighted "
        "tardiness. $L=$ full releases the whole instance's preventive work to "
        "the planner at time zero; a known order still cannot start before its "
        "own release. The rule and the optimiser are single artefacts run at "
        "each level, so their contrast is the information alone; the policy "
        "arms are retrained at each level, so their contrast carries the "
        "retraining as well. The pool row is the five-seed mean per "
        "configuration and the seed rows are its members. Intervals are 95\\% "
        "cluster bootstraps over base instances, $p$ is a Holm-adjusted paired "
        "Wilcoxon $p$-value, and the verdict uses the same margin rule as the "
        "comparison tables above. The optimiser ran on its own configuration "
        "subsample, which its $n$ reports.")
    L += longtable_close(note)
    print("  %-28s %3d contrast rows over %d scopes"
          % ("visibility contrasts", n, len(VIS_SCOPES)))
    return L, n


# ---------------------------------------------------------------------------
def main():
    print("writing %s" % OUT.relative_to(ROOT))
    lines = [
        r"% Supplementary Section S5 tables: generated by",
        r"% scripts/r4_supp_tables.py from",
        r"%   results/r4_final/analysis/equivalence.csv",
        r"%   results/r4_robustness/analysis/stability.csv",
        r"%   results/r4_visibility/analysis/vis_effect.csv",
        r"% Do not edit by hand: rerun the script.",
        "",
    ]
    total = 0
    for i, (name, caption, label, scopes) in enumerate(EQ_TABLES):
        # The full column and verdict definitions are printed once, under the
        # first table; the others point at it.
        block, n = eq_table(name, caption, label, scopes,
                            EQ_NOTE_COMMON if i == 0 else EQ_NOTE_SHORT)
        lines += block
        total += n
    block, n = rob_table()
    lines += block
    total += n
    block, n = vis_table()
    lines += block
    total += n
    OUT.write_text("\n".join(lines) + "\n")
    print("  %d data rows in %d tables -> %s"
          % (total, len(EQ_TABLES) + 2, OUT.relative_to(ROOT)))


if __name__ == "__main__":
    sys.exit(main())
