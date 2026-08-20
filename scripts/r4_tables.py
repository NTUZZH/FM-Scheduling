#!/usr/bin/env python
"""
R4 table fragments: the four LaTeX exhibits the R4 results section inputs.

  paper/tables/t_headline.tex   (tab:headline, Section 7.2)
  paper/tables/t_rules.tex      (tab:rules,    Section 7.3)
  paper/tables/t_learning.tex   (tab:learning, Section 7.6)
  paper/tables/t_robust.tex     (tab:robust,   Section 7.7)

Each file is a BARE booktabs `tabular` (the float, caption and label already
live in paper/drafts/results.tex, which \\input{}s these paths), followed by a
note row that states the table's mechanical bold rule.

One script, idempotent, reading ONLY the three definitive-analysis
directories; no number is typed into this file.

  PYTHONPATH=src python scripts/r4_tables.py
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TABDIR = ROOT / "paper" / "tables"
ANA_FINAL = ROOT / "results" / "r4_final" / "analysis"
ANA_ROB = ROOT / "results" / "r4_robustness" / "analysis"

# ---------------------------------------------------------------------------
# formatting
# ---------------------------------------------------------------------------
MINUS = "$-$"


def _sign(v, body):
    return (MINUS if v < 0 else "") + body


def fmt_mean(v):
    """Mean weighted tardiness: thousands separators, sensible decimals."""
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
    if a < 100:
        return _sign(v, f"{a:.1f}")
    return _sign(v, f"{a:,.0f}")


def fmt_diff(v):
    a = abs(v)
    if a < 10:
        return _sign(v, f"{a:.2f}")
    if a < 1000:
        return _sign(v, f"{a:.1f}")
    return _sign(v, f"{a:,.0f}")


def fmt_ci(lo, hi):
    return f"[{fmt_diff(lo)}, {fmt_diff(hi)}]"


def fmt_lat(med, p90):
    def one(x):
        if x >= 1:
            return f"{x:,.2f}"
        if x >= 0.01:
            return f"{x:.3f}"
        return f"{x:.4f}"
    return f"{one(med)} [{one(p90)}]"


def bf(s, on):
    return "\\textbf{" + s + "}" if on else s


VERDICT_SHORT = {"equivalent": "eq.", "inconclusive": "inconcl.", "worse": "worse",
                 "better": "better"}

# A checkpoint id is an internal code name, so a table note names the family the
# checkpoint belongs to instead. The family follows mechanically from the id's
# prefix: v2rl is a curriculum-v2 policy seed, v2at a curriculum-v2 attention
# scorer, rl a curriculum-v1 policy seed.
RULE_LABEL = {"edd": "EDD", "pfifo": "pFIFO", "wmdd": "WMDD", "atc": "ATC",
              "wspt": "WSPT", "lpt": "LPT", "random": "Random"}
SEED_FAMILY = (("v2rl", "a curriculum-v2 policy seed"),
               ("v2at", "a curriculum-v2 attention-scorer seed"),
               ("rl", "a curriculum-v1 policy seed"))


def method_phrase(m):
    """Plain-words name of one scored method."""
    if m in RULE_LABEL:
        return RULE_LABEL[m]
    for prefix, phrase in SEED_FAMILY:
        if m.startswith(prefix):
            return phrase
    raise SystemExit("no plain-words name for method %r" % m)


def scope_best_phrase(items):
    """`a curriculum-v2 policy seed at m=1.0; a curriculum-v1 policy seed at
    m=0.8 and m=0.6`, from (scope label, best method) pairs.

    Scopes that share one family are grouped, so the note names each family
    once however many scopes it wins.
    """
    groups = []
    for label, method in items:
        phrase = method_phrase(method)
        if groups and groups[-1][0] == phrase:
            groups[-1][1].append(label)
        else:
            groups.append((phrase, [label]))
    out = []
    for phrase, labels in groups:
        where = (labels[0] if len(labels) == 1
                 else ", ".join(labels[:-1]) + " and " + labels[-1])
        out.append("%s at %s" % (phrase, where))
    return "; ".join(out)


def write(name, lines):
    path = TABDIR / f"{name}.tex"
    path.write_text("\n".join(lines) + "\n")
    print(f"  wrote {path.relative_to(ROOT)}  ({len(lines)} lines)")


def note_par(text):
    """Table note as a paragraph after the tabular.

    A note placed INSIDE the tabular as a \\multicolumn{p{\\linewidth}} row
    forces the tabular to the full line width and dumps the slack into its last
    column, so the note lives outside the tabular instead.
    """
    return [r"\end{tabular}", "", r"\vspace{2pt}",
            "\\parbox{\\linewidth}{\\scriptsize %s}" % text]


# ---------------------------------------------------------------------------
# shared data
# ---------------------------------------------------------------------------
EQ = pd.read_csv(ANA_FINAL / "equivalence.csv")
POOLS = pd.read_csv(ANA_FINAL / "pools.csv")
DISP = pd.read_csv(ANA_FINAL / "seed_dispersion.csv")
LAT = pd.read_csv(ANA_FINAL / "latency.csv")
STAB = pd.read_csv(ANA_ROB / "stability.csv")

V2_SEEDS = [m for m in EQ.method.unique() if m.startswith("v2rl")]
ATTN_SEEDS = [m for m in EQ.method.unique() if m.startswith("v2at")]


def scope_rows(scope_type, scope):
    d = EQ[(EQ.scope_type == scope_type) & (EQ.scope == scope)]
    return d.set_index("method")


def seeds_in_set(scope_type, scope, seeds):
    d = scope_rows(scope_type, scope)
    return int(sum(int(d.loc[m, "in_equivalence_set"]) for m in seeds if m in d.index))


def pool_row(scope_type, scope, pool):
    p = POOLS[(POOLS.scope_type == scope_type) & (POOLS.scope == scope)
              & (POOLS.method == pool) & (POOLS.is_scope_best_ref == 1)]
    return None if p.empty else p.iloc[0]


# ===========================================================================
# T-headline  (tab:headline)  Section 7.2
# ===========================================================================
HEAD_M = ["m=1.0", "m=0.8", "m=0.6"]
HEAD_MLAB = {"m=1.0": "$m=1.0$", "m=0.8": "$m=0.8$", "m=0.6": "$m=0.6$"}
HEAD_RULES = [(["edd", "pfifo"], "EDD, pFIFO"), (["wmdd"], "WMDD"), (["atc"], "ATC"),
              (["wspt"], "WSPT"), (["lpt"], "LPT"), (["random"], "Random")]


def table_headline():
    ncols = 1 + 3 * 2
    L = [r"% tab:headline -- Eval-B empirical anchors, verdict campuses, by crew",
         r"% multiplier. BARE booktabs tabular; the float, caption and",
         r"% \label{tab:headline} live in paper/drafts/results.tex.",
         r"% Generated by scripts/r4_tables.py from results/r4_final/analysis/.",
         r"\setlength{\tabcolsep}{4pt}",
         r"\footnotesize",
         r"\begin{tabular}{@{}l rl rl rl@{}}",
         r"\toprule"]
    head = ["Method"]
    for m in HEAD_M:
        head += ["\\multicolumn{2}{c}{%s}" % HEAD_MLAB[m]]
    L.append(" & ".join(head) + r" \\")
    L.append(r"\cmidrule(lr){2-3}\cmidrule(lr){4-5}\cmidrule(lr){6-7}")
    L.append(" & ".join([""] + ["Mean TWT", "$\\Delta$ vs.\\ best [95\\% CI]"] * 3)
             + r" \\")
    L.append(r"\midrule")

    for methods, label in HEAD_RULES:
        cells = [label]
        for m in HEAD_M:
            d = scope_rows("emp_m", m)
            r = d.loc[methods[0]]
            inset = bool(int(r.in_equivalence_set))
            mark = "$^{\\ddagger}$" if r.verdict == "worse" else ""
            cells += [bf(fmt_mean(float(r["mean"])), inset),
                      bf(fmt_diff(float(r.mean_diff)) + "~"
                         + fmt_ci(float(r.ci_lo), float(r.ci_hi)), inset) + mark]
        L.append(" & ".join(cells) + r" \\")

    L.append(r"\addlinespace[2pt]")
    for pool, seeds, label in ((
            "v2pool", V2_SEEDS, "Policy pool (%d MLP seeds)" % len(V2_SEEDS)),
            ("v2attnpool", ATTN_SEEDS,
             "Attention pool (%d seeds)" % len(ATTN_SEEDS))):
        cells = [label]
        for m in HEAD_M:
            p = pool_row("emp_m", m, pool)
            mark = "$^{\\ddagger}$" if p.verdict == "worse" else ""
            cells += [fmt_mean(float(p.mean_method)),
                      fmt_diff(float(p.mean_diff)) + "~"
                      + fmt_ci(float(p.ci_lo), float(p.ci_hi)) + mark]
        L.append(" & ".join(cells) + r" \\")
        cells = ["\\quad seeds inside the set"]
        for m in HEAD_M:
            k = seeds_in_set("emp_m", m, seeds)
            cells += ["\\multicolumn{2}{c}{%d of %d}" % (k, len(seeds))]
        L.append(" & ".join(cells) + r" \\")

    L.append(r"\addlinespace[2pt]")
    cells = ["Methods in the equivalence set"]
    for m in HEAD_M:
        d = scope_rows("emp_m", m)
        cells += ["\\multicolumn{2}{c}{%d of %d}"
                  % (int(d.in_equivalence_set.sum()), int(len(d)))]
    L.append(" & ".join(cells) + r" \\")
    L.append(r"\bottomrule")

    d = scope_rows("emp_m", "m=1.0")
    n_cfg = int(d.n_configs.iloc[0])
    n_clu = int(d.n_clusters.iloc[0])
    bests = scope_best_phrase([(HEAD_MLAB[m].strip("$"),
                                scope_rows("emp_m", m).best_method.iloc[0])
                               for m in HEAD_M])
    n_meth = int(len(d))
    note = (
        "Note: bold marks membership in the practical-equivalence set of the "
        "scope's best method, applied mechanically to every rule row with no "
        "exceptions. The pool rows are seed-averaged aggregates and are ranked "
        "through their seed counts rather than through set membership, so they are "
        "never bolded. Each scope holds %d configurations over %d base-instance "
        "clusters and ranks %d full-coverage methods; the scope best is %s. "
        "A bold row is practically equivalent to the scope best; a plain row is "
        "inconclusive, its interval crossing the margin; $\\ddagger$ marks a row "
        "that is worse than the best beyond the margin. Lower TWT is better."
        % (n_cfg, n_clu, n_meth, bests))
    L += note_par(note)
    write("t_headline", L)


# ===========================================================================
# T-rules  (tab:rules)  Section 7.3
# ===========================================================================
RULE_COLS = [("edd", "EDD"), ("pfifo", "pFIFO"), ("wmdd", "WMDD"), ("atc", "ATC"),
             ("wspt", "WSPT"), ("lpt", "LPT"), ("random", "Random")]

# Realised-utilisation bins of the empirical anchors, and the generator's target
# utilisations. Shared by t_rules and t_learning so one scope carries one label
# wherever it appears.
UBIN_SCOPES = [("emp_ubin", f"u_bin={b}", lab) for b, lab in
               (("<0.5", "$u<0.5$"), ("0.5-0.8", "$0.5$--$0.8$"),
                ("0.8-1.0", "$0.8$--$1.0$"), ("1.0-1.2", "$1.0$--$1.2$"),
                (">=1.2", "$u\\geq1.2$"))]
UTARGET_SCOPES = [("gen_utarget", f"u_target={u}", f"$u={u}$")
                  for u in ("0.7", "0.9", "1.0", "1.1", "1.3")]

# The three blocks of t_rules, in print order: the headline crew-multiplier
# scopes, the same empirical anchors re-cut by the load each week actually
# carried, and the generator cells.
RULE_BLOCKS = [
    ("Empirical anchors, verdict campuses",
     [("emp_m", m, HEAD_MLAB[m]) for m in HEAD_M]),
    ("Empirical anchors, by realised-utilisation bin", UBIN_SCOPES),
    ("Generator cells", UTARGET_SCOPES),
]


def table_rules():
    ncols = 3 + len(RULE_COLS)
    L = [r"% tab:rules -- transparent rules and the diagnostic floors, by crew",
         r"% multiplier, by realised-utilisation bin, and by generator target",
         r"% utilisation. BARE booktabs tabular;",
         r"% float, caption and \label{tab:rules} live in paper/drafts/results.tex.",
         r"% Generated by scripts/r4_tables.py from results/r4_final/analysis/.",
         r"\setlength{\tabcolsep}{4pt}",
         r"\footnotesize",
         r"\begin{tabular}{@{}l r r " + "r" * len(RULE_COLS) + r"@{}}",
         r"\toprule"]
    L.append(" & ".join(["", "", ""]
                        + ["\\multicolumn{%d}{c}{Mean TWT (gap to the scope best, "
                           "\\%%)}" % len(RULE_COLS)]) + r" \\")
    L.append("\\cmidrule(lr){4-%d}" % ncols)
    L.append(" & ".join(["Scope", "$n$", "Best mean"]
                        + [lab for _, lab in RULE_COLS]) + r" \\")
    L.append(r"\midrule")

    maxgap_edd_pfifo = 0.0
    for b, (title, scopes) in enumerate(RULE_BLOCKS):
        if b:
            L.append(r"\addlinespace[2pt]")
        L.append("\\multicolumn{%d}{@{}l}{\\textit{%s}}\\\\" % (ncols, title))
        for st, sc, lab in scopes:
            d = scope_rows(st, sc)
            cells = [lab, f"{int(d.n_configs.iloc[0]):,}",
                     fmt_mean(float(d.mean_best.iloc[0]))]
            for m, _ in RULE_COLS:
                r = d.loc[m]
                inset = bool(int(r.in_equivalence_set))
                cells.append(bf("%s (%s)" % (fmt_mean(float(r["mean"])),
                                             fmt_pct(float(r.pct_from_best))),
                                inset))
            maxgap_edd_pfifo = max(
                maxgap_edd_pfifo,
                abs(float(d.loc["edd", "mean"]) - float(d.loc["pfifo", "mean"]))
                / float(d.mean_best.iloc[0]) * 100.0)
            L.append(" & ".join(cells) + r" \\")
    L.append(r"\bottomrule")

    # The crew-multiplier block and the bin block are two cuts of one set of
    # empirical configurations; the note says so, so the claim is checked here
    # rather than asserted in prose.
    def _n(block):
        return sum(int(scope_rows(st, sc).n_configs.iloc[0])
                   for st, sc, _ in block)
    n_emp_configs = _n(RULE_BLOCKS[0][1])
    if n_emp_configs != _n(RULE_BLOCKS[1][1]):
        raise SystemExit("t_rules: the crew-multiplier and utilisation-bin "
                         "blocks cover different configuration counts (%d vs %d)"
                         % (n_emp_configs, _n(RULE_BLOCKS[1][1])))

    note = (
        "Note: bold marks membership in the scope's practical-equivalence set, "
        "applied mechanically to every cell with no exceptions; the gap in "
        "parentheses is the percentage above the scope's best mean, over all "
        "full-coverage methods. The first two blocks cut the same %s empirical "
        "configurations two ways, by the crew multiplier applied to them and by "
        "the load the week actually carried, so their rows are not independent "
        "of each other; a bin holds configurations from all three crew "
        "multipliers. EDD and pFIFO coincide exactly on every empirical "
        "anchor and differ by at most %.3f\\%% of the best mean on the generator "
        "cells, so they are kept as separate rows. $n$ counts configurations. "
        "Lower TWT is better." % (f"{n_emp_configs:,}", maxgap_edd_pfifo))
    L += note_par(note)
    write("t_rules", L)


# ===========================================================================
# T-learning  (tab:learning)  Section 7.6
# ===========================================================================
def table_learning():
    scopes = UBIN_SCOPES + UTARGET_SCOPES
    ncols = 7
    L = [r"% tab:learning -- learned policy against the leading transparent rule.",
         r"% BARE booktabs tabular; float, caption and \label{tab:learning} live",
         r"% in paper/drafts/results.tex.",
         r"% Generated by scripts/r4_tables.py from results/r4_final/analysis/.",
         r"\setlength{\tabcolsep}{4pt}",
         r"\footnotesize",
         r"\begin{tabular}{@{}l r r r r l c@{}}",
         r"\toprule"]
    L.append(" & ".join(["Scope", "$n$", "Best mean", "EDD mean", "Pool mean",
                         "Pool $-$ best [95\\% CI]", "Seeds in set"]) + r" \\")
    L.append(r"\midrule")
    L.append("\\multicolumn{%d}{@{}l}{\\textit{Empirical anchors, realised "
             "utilisation bin}}\\\\" % ncols)

    for i, (st, sc, lab) in enumerate(scopes):
        if st == "gen_utarget" and scopes[i - 1][0] == "emp_ubin":
            L.append(r"\addlinespace[2pt]")
            L.append("\\multicolumn{%d}{@{}l}{\\textit{Generator cells, target "
                     "utilisation}}\\\\" % ncols)
        d = scope_rows(st, sc)
        p = pool_row(st, sc, "v2pool")
        edd = d.loc["edd"]
        k = seeds_in_set(st, sc, V2_SEEDS)
        cells = [lab, f"{int(d.n_configs.iloc[0]):,}",
                 fmt_mean(float(d.mean_best.iloc[0])),
                 bf(fmt_mean(float(edd["mean"])), bool(int(edd.in_equivalence_set))),
                 fmt_mean(float(p.mean_method)),
                 fmt_diff(float(p.mean_diff)) + "~" + fmt_ci(float(p.ci_lo),
                                                             float(p.ci_hi))
                 + " " + VERDICT_SHORT[p.verdict],
                 "%d of %d" % (k, len(V2_SEEDS))]
        L.append(" & ".join(cells) + r" \\")

    # ---- latency block ----------------------------------------------------
    L.append(r"\midrule")
    L.append("\\multicolumn{%d}{@{}l}{\\textit{Decision latency, median [p90]}}\\\\"
             % ncols)
    L.append(" & ".join(["Method family", "\\multicolumn{3}{l}{Empirical anchors}",
                         "\\multicolumn{3}{l}{Generator cells}"]) + r" \\")
    latrows = [("rules", "Transparent rules", "ms per decision"),
               ("v2_mlp", "Policy pool (MLP)", "ms per decision"),
               ("v2_attn", "Attention scorer", "ms per decision"),
               ("rolling", "Rolling CP-SAT", "s per replan")]
    for fam, lab, unit in latrows:
        e = LAT[(LAT.scope == "empirical_verdict") & (LAT.family == fam)
                & (LAT.unit == ("s_per_replan" if fam == "rolling"
                                else "ms_per_decision"))]
        g = LAT[(LAT.scope == "generator") & (LAT.family == fam)
                & (LAT.unit == "ms_per_decision")]
        ecell = (fmt_lat(float(e["median"].iloc[0]), float(e["p90"].iloc[0])) + "~" + unit
                 if not e.empty else "n/a")
        gcell = (fmt_lat(float(g["median"].iloc[0]), float(g["p90"].iloc[0])) + "~" + unit
                 if not g.empty else "not run")
        L.append(" & ".join([lab, "\\multicolumn{3}{l}{%s}" % ecell,
                             "\\multicolumn{3}{l}{%s}" % gcell]) + r" \\")
    L.append(r"\bottomrule")

    note = (
        "Note: bold marks membership in the scope's practical-equivalence set, "
        "applied mechanically to the EDD column with no exceptions; the pool is a "
        "seed-averaged aggregate, so it is ranked through its seed count and is "
        "never bolded. The pool difference is paired on the configuration, with a "
        "95\\% cluster bootstrap over base instances, and carries its verdict "
        "(eq.\\ = practically equivalent, inconcl.\\ = inconclusive). Latency is "
        "measured over the same runs; rolling CP-SAT is reported per replan, not "
        "per decision, and ran on the empirical anchors only. Lower is better "
        "throughout.")
    L += note_par(note)
    write("t_learning", L)


# ===========================================================================
# T-robust  (tab:robust)  Section 7.7
# ===========================================================================
ROB_ROWS = [("pmodel", "max", "Processing time: dominant labour line"),
            ("pmodel", "single", "Processing time: single labour line"),
            ("capacity", "q0.90", "Capacity sized at p90 of weekly hours"),
            ("capacity", "q0.75", "Capacity sized at p75 of weekly hours"),
            ("backdate", "backdate", "Backdated corrective releases"),
            ("sla", "emg", "Service windows: P1 and P2 halved"),
            ("sla", "rtn", "Service windows: P3 and P4 halved"),
            ("sla", "pmp3", "Preventive work mapped to P3")]
HOLD = 0.90
PRETTY_METHOD = {"edd": "EDD", "pfifo": "pFIFO", "wmdd": "WMDD", "atc": "ATC",
                 "wspt": "WSPT", "lpt": "LPT", "random": "Random"}


def _split_leavers(s):
    """(named transparent rules, count of policy seeds) leaving the set."""
    if not isinstance(s, str) or not s.strip():
        return [], 0
    rules, pol = [], 0
    for m in s.split():
        if m in ("-", "--", "none"):      # the analysis writes "-" for "nothing left"
            continue
        if m in PRETTY_METHOD:
            rules.append(PRETTY_METHOD[m])
        else:
            pol += 1
    return rules, pol


def _pretty_leavers(s):
    rules, pol = _split_leavers(s)
    parts = []
    if len(rules) == len(PRETTY_METHOD):
        parts.append("every rule")
    elif rules and len(PRETTY_METHOD) - len(rules) <= 2:
        stay = [v for k, v in PRETTY_METHOD.items() if v not in rules]
        parts.append("every rule except " + " and ".join(stay))
    elif rules:
        parts.append(", ".join(rules))
    if pol:
        parts.append("%d policy seed%s" % (pol, "" if pol == 1 else "s"))
    return "; ".join(parts) if parts else "none"


def table_robust():
    ncols = 6
    L = [r"% tab:robust -- stability of the equivalence set across the robustness",
         r"% suite, verdict campuses. BARE booktabs tabular; float, caption and",
         r"% \label{tab:robust} live in paper/drafts/results.tex.",
         r"% Generated by scripts/r4_tables.py from",
         r"% results/r4_robustness/analysis/stability.csv.",
         r"\setlength{\tabcolsep}{4pt}",
         r"\footnotesize",
         r"\begin{tabular}{@{}l r c r r l@{}}",
         r"\toprule"]
    L.append(" & ".join(["Check", "$n$", "Set size", "Jaccard overlap",
                         "Kendall $\\tau_b$", "Methods that leave the set"]) + r" \\")
    L.append(r"\midrule")
    n_trio = 0
    for check, arm, lab in ROB_ROWS:
        r = STAB[(STAB.check == check) & (STAB.arm == arm)
                 & (STAB.stratum == "verdict")].iloc[0]
        hold = float(r.set_jaccard) >= HOLD
        n_trio += int(bool(r.top3_is_leading_trio))
        L.append(" & ".join([
            lab, f"{int(r.n_configs):,}",
            "%d $\\rightarrow$ %d" % (int(r.baseline_set_size), int(r.set_size)),
            bf(f"{float(r.set_jaccard):.2f}", hold),
            f"{float(r.tau_method):.2f}".replace("-", MINUS),
            _pretty_leavers(r.left_set)]) + r" \\")
    L.append(r"\bottomrule")

    base = STAB[(STAB.check == "pmodel") & (STAB.arm == "sum")
                & (STAB.stratum == "verdict")].iloc[0]
    pol_arms = [lab for check, arm, lab in ROB_ROWS
                if _split_leavers(STAB[(STAB.check == check) & (STAB.arm == arm)
                                       & (STAB.stratum == "verdict")].iloc[0].left_set)[1]]
    trio_where = ("all %d arms" % len(ROB_ROWS) if n_trio == len(ROB_ROWS)
                  else "%d of the %d arms" % (n_trio, len(ROB_ROWS)))
    note = (
        "Note: bold marks a Jaccard overlap of at least %.2f, that is, the leading "
        "practical-equivalence set holds; the rule is applied mechanically with no "
        "exceptions. Set size is the set on the final-evaluation anchors "
        "followed by the arm's set, "
        "over the same %d scored methods and the same base instances. The same "
        "three families (learned policy, due-date rules, weighted urgency rules) "
        "hold the top three mean ranks in %s; set membership can still change, as "
        "the set-size column shows. A low Kendall $\\tau_b$ (a rank correlation) "
        "is not "
        "evidence that the ranking moved: on the anchors the scored methods sit "
        "within %.2f\\%% of each other against a margin of %.2f\\%% of the best "
        "mean, so the order inside the set is not identified. Policy seeds are "
        "ranked individually; they leave the set only in %d of the %d arms (%s), "
        "and the leavers are listed as a count because they are interchangeable "
        "training seeds of one method."
        % (HOLD, int(base.n_methods), trio_where,
           float(base.spread_pct), float(base.margin_pct_of_best),
           len(pol_arms), len(ROB_ROWS), "; ".join(pol_arms)))
    L += note_par(note)
    write("t_robust", L)


MAIN = {"headline": table_headline, "rules": table_rules,
        "learning": table_learning, "robust": table_robust}

if __name__ == "__main__":
    which = sys.argv[1:] or list(MAIN)
    for k in which:
        MAIN[k]()
    print("done.")
