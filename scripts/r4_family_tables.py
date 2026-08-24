#!/usr/bin/env python
"""Family-level table fragments for the R4 results section.

  paper/tables/t_headline_family.tex   (empirical anchors, by crew multiplier)
  paper/tables/t_rules_family.tex      (three scope blocks, gap to EDD)
  paper/tables/t_learning_family.tex   (the three policy pools, two scope blocks)

All three files are BARE booktabs tabulars, the learning table in a `tabular*`
so that it fills the line width: the float, caption and label live in
paper/drafts/results.tex, which \\input{}s these paths. Each is followed by a
note that states the bolding rule and the verdict markers mechanically.

Ten methods are compared, seven transparent rules and three seed-averaged
policy pools, each against EDD, the reference fixed before any result was
read. Rolling CP-SAT pairs on a subsample and is never ranked, so it is not a
row of any of the three tables.

No number is typed into this file: every value is read from
results/r4_final/analysis/family_comparisons.csv, and the equivalence margin
rule is imported from the module that produced the verdicts. The learning
table is then verified cell by cell against a second, independent read of that
CSV, so a formatting change cannot silently move a number.

  PYTHONPATH=src python scripts/r4_family_tables.py
  PYTHONPATH=src python scripts/r4_family_tables.py --check-latex
"""
import csv
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

from fmwos import stats

ROOT = Path(__file__).resolve().parents[1]
TABDIR = ROOT / "paper" / "tables"
ANA = ROOT / "results" / "r4_final" / "analysis"
REL_SRC = "results/r4_final/analysis/family_comparisons.csv"

# ---------------------------------------------------------------------------
# formatting (shared conventions with scripts/r4_tables.py)
# ---------------------------------------------------------------------------
MINUS = "$-$"
ENDASH = "--"
# t_learning_family is set in a tabular* so it fills the line width; the
# checks below split a fragment on the end of its tabular.
TAB_END = "\\end{tabular*}"


def _sign(v, body):
    """Sign the formatted body, except when it has rounded to zero.

    A printed ``-0.00`` claims a precision the cell does not carry; the
    verdict marker, not the sign of a rounded zero, is what states the
    direction of a difference that small.
    """
    if v < 0 and any(c in "123456789" for c in body):
        return MINUS + body
    return body


def fmt_mean(v):
    """Mean weighted tardiness: thousands separators, sensible decimals."""
    a = abs(v)
    if a < 10:
        return _sign(v, f"{a:.2f}")
    if a < 1000:
        return _sign(v, f"{a:.1f}")
    return _sign(v, f"{a:,.0f}")


fmt_diff = fmt_mean


def fmt_pct(v):
    a = abs(v)
    if a < 10:
        return _sign(v, f"{a:.2f}")
    if a < 100:
        return _sign(v, f"{a:.1f}")
    return _sign(v, f"{a:,.0f}")


def fmt_ci(lo, hi):
    return f"[{fmt_diff(lo)}, {fmt_diff(hi)}]"


def fmt_range(lo, hi):
    return fmt_mean(lo) + ENDASH + fmt_mean(hi)


# The learning table prints one difference per cell rather than a mean and a
# difference, so it carries its own precision rule: one decimal everywhere,
# and no decimals once the magnitude reaches a thousand units of weighted
# tardiness, where a tenth of a unit is below the noise the interval already
# shows. Thousands are separated with {,} so the comma keeps its text width
# wherever the cell is set.
def fmt_lrn(v):
    """One decimal, or no decimals from 1000 units of weighted tardiness up."""
    a = abs(v)
    if a < 1000:
        return _sign(v, f"{a:.1f}")
    return _sign(v, f"{a:,.0f}".replace(",", "{,}"))


def fmt_lrn_ci(lo, hi):
    return f"[{fmt_lrn(lo)}, {fmt_lrn(hi)}]"


def fmt_lrn_range(lo, hi):
    return fmt_lrn(lo) + ENDASH + fmt_lrn(hi)


def bf(s, on):
    return "\\textbf{" + s + "}" if on else s


def write(name, lines):
    path = TABDIR / f"{name}.tex"
    path.write_text("\n".join(lines) + "\n")
    print(f"  wrote {path.relative_to(ROOT)}  ({len(lines)} lines)")


def note_par(text, env="tabular"):
    """Table note as a paragraph after the tabular.

    A note placed INSIDE the tabular as a \\multicolumn{p{\\linewidth}} row
    forces the tabular to the full line width and dumps the slack into its
    last column, so the note lives outside the tabular instead.
    """
    return ["\\end{%s}" % env, "", r"\vspace{2pt}",
            "\\parbox{\\linewidth}{\\scriptsize %s}" % text]


# ---------------------------------------------------------------------------
# vocabulary
# ---------------------------------------------------------------------------
REFERENCE = "edd"

# Print order: the due-date family first, then the processing-time and
# composite rules, then the two diagnostic floors, then the policy pools.
FAMILY_ORDER = ["edd", "pfifo", "wspt", "atc", "wmdd", "lpt", "random",
                "mlp_pool", "attn_pool", "v1_pool"]
FAMILY_LABEL = {"edd": "EDD (reference)", "pfifo": "pFIFO", "wspt": "WSPT",
                "atc": "ATC", "wmdd": "WMDD", "lpt": "LPT",
                "random": "Random", "mlp_pool": "MLP policy pool",
                "attn_pool": "Attention policy pool",
                "v1_pool": "Curriculum-v1 policy pool"}
POOLS = ["mlp_pool", "attn_pool", "v1_pool"]
POOL_NOTE_NAME = {"mlp_pool": "the MLP pool", "attn_pool": "the attention pool",
                  "v1_pool": "the curriculum-v1 pool"}
# A rule row starts a new group of the print order, so the groups are set off
# by a small vertical space rather than by extra rules.
GROUP_BREAK_BEFORE = {"wspt", "lpt", "mlp_pool"}

# One symbol per practical-equivalence verdict, used by both tables and spelt
# out in both notes. The reference row carries no marker.
MARK = {"equivalent": r"\equiv", "inconclusive": r"\circ",
        "worse": r"\ddagger", "better": r"\ast"}
MARK_NAME = [("equivalent", "practically equivalent to EDD"),
             ("inconclusive", "inconclusive"),
             ("worse", "worse than EDD"),
             ("better", "better than EDD")]
DAGGER = "$^{\\dagger}$"
DAGGER_NOTE = DAGGER + "\\,"

HEAD_M = ["m=1.0", "m=0.8", "m=0.6"]
HEAD_MLAB = {"m=1.0": "$m=1.0$", "m=0.8": "$m=0.8$", "m=0.6": "$m=0.6$"}

# The three scope blocks of t_rules_family, in print order.
UBIN_SCOPES = [("emp_ubin", f"u_bin={b}", lab) for b, lab in
               (("<0.5", "$<0.5$"), ("0.5-0.8", "$0.5$--$0.8$"),
                ("0.8-1.0", "$0.8$--$1.0$"), ("1.0-1.2", "$1.0$--$1.2$"),
                (">=1.2", "$\\geq1.2$"))]
UTARGET_SCOPES = [("gen_utarget", f"u_target={u}", f"${u}$")
                  for u in ("0.7", "0.9", "1.0", "1.1", "1.3")]
RULE_BLOCKS = [
    ("Crew multiplier $m$", [("emp_m", m, "$%s$" % m.split("=")[1])
                             for m in HEAD_M]),
    ("Realised utilisation $u$", UBIN_SCOPES),
    ("Generator target $u$", UTARGET_SCOPES),
]

# The two blocks of t_learning_family, stacked one above the other because a
# cell carries a difference and its interval and ten such columns do not fit
# the text width. The last field names the most contended scope of the block
# in the note, where the seed dispersion of each pool is reported.
LEARN_BLOCKS = [
    ("Empirical anchors, by realised utilisation $u$", UBIN_SCOPES,
     "the $u\\geq1.2$ bin"),
    ("Generator cells, by target utilisation $u$", UTARGET_SCOPES,
     "the $u=1.3$ generator cells"),
]

# ---------------------------------------------------------------------------
# data
# ---------------------------------------------------------------------------
COMP = pd.read_csv(ANA / "family_comparisons.csv")


def scope_rows(scope_type, scope):
    """The ten ranked families of one scope, indexed by family name.

    Rolling CP-SAT pairs on a subsample of the scope and carries its own
    reference mean, so it is dropped here rather than filtered at every use.
    """
    d = COMP[(COMP.scope_type == scope_type) & (COMP.scope == scope)
             & (COMP.family.isin(FAMILY_ORDER))].set_index("family")
    missing = [f for f in FAMILY_ORDER if f not in d.index]
    if missing:
        raise SystemExit("scope %s/%s is missing families: %s"
                         % (scope_type, scope, ", ".join(missing)))
    # The reference mean is recomputed per comparison, so the families agree
    # on it only to floating-point rounding.
    ref = float(d.loc[REFERENCE, "mean_family"])
    tol = 1e-6 * max(1.0, abs(ref))
    if abs(ref - float(d.mean_edd.iloc[0])) > tol:
        raise SystemExit("scope %s/%s: the EDD row and the reference mean "
                         "disagree" % (scope_type, scope))
    if float(d.mean_edd.max() - d.mean_edd.min()) > tol:
        raise SystemExit("scope %s/%s: the families do not share one reference "
                         "mean" % (scope_type, scope))
    if d.loc[REFERENCE, "verdict"] != "reference":
        raise SystemExit("scope %s/%s: the EDD row is not the reference"
                         % (scope_type, scope))
    return d


def margin_rule_phrase():
    """The margin rule, in words, checked against every scope it is used on."""
    scopes = [("emp_m", s) for s in HEAD_M]
    scopes += [(st, sc) for _, block in RULE_BLOCKS for st, sc, _ in block]
    for st, sc in scopes:
        d = scope_rows(st, sc)
        want = stats.equivalence_margin(float(d.mean_edd.iloc[0]))
        got = float(d.margin.iloc[0])
        if abs(want - got) > 1e-6 * max(1.0, want):
            raise SystemExit("scope %s/%s: margin %.6f does not follow the "
                             "protocol rule (%.6f)" % (st, sc, got, want))
    return ("the larger of %g unit of weighted tardiness and %g\\%% of the "
            "scope's EDD mean"
            % (stats.MARGIN_ABS, 100.0 * stats.MARGIN_REL))


def marker(verdict, sup=False):
    if verdict == "reference":
        return ""
    if verdict not in MARK:
        raise SystemExit("no marker for verdict %r" % verdict)
    return ("$^{%s}$" if sup else "$%s$") % MARK[verdict]


def verdict_rule_sentences():
    """Marker legend and the rule that assigns each marker, stated once."""
    legend = ", ".join("%s %s" % (marker(v), name) for v, name in MARK_NAME[:-1])
    legend += " and %s %s" % (marker(MARK_NAME[-1][0]), MARK_NAME[-1][1])
    return ("The verdict markers are %s: a difference is equivalent when its "
            "whole 95\\%% interval lies inside the margin, worse when the "
            "interval lies wholly above the margin, better when it lies "
            "wholly below it, and inconclusive otherwise. The margin is %s."
            % (legend, margin_rule_phrase()))


def verdict_rule_pointer():
    """Marker legend with a pointer to the headline table's full definition.

    The three family tables sit within three pages of each other and the
    full marker/margin definition is identical in each, so the second and
    third tables carry the legend plus a pointer instead of repeating the
    definition (referee note, 2026-08-25: the repeated notes made the
    results pages read dense)."""
    legend = ", ".join("%s %s" % (marker(v), name) for v, name in MARK_NAME[:-1])
    legend += " and %s %s" % (marker(MARK_NAME[-1][0]), MARK_NAME[-1][1])
    return ("Verdict markers (%s) and the margin are defined in the note to "
            "Table~\\ref{tab:headline}." % legend)


def verdicts_seen():
    """Verdicts that actually reach a cell of either table."""
    seen = set()
    scopes = [("emp_m", s) for s in HEAD_M]
    scopes += [(st, sc) for _, block in RULE_BLOCKS for st, sc, _ in block]
    for st, sc in scopes:
        seen |= set(scope_rows(st, sc).verdict.unique())
    return seen - {"reference"}


# ===========================================================================
# T-headline-family: empirical anchors by crew multiplier
# ===========================================================================
def table_headline_family():
    L = [r"% tab:headlinefamily -- Eval-B empirical anchors, verdict campuses,",
         r"% ten method families against the EDD reference, by crew multiplier.",
         r"% BARE booktabs tabular; the float, caption and label live in",
         r"% paper/drafts/results.tex.",
         "%% Generated by scripts/r4_family_tables.py from %s." % REL_SRC,
         r"\setlength{\tabcolsep}{3pt}",
         r"\footnotesize",
         r"\begin{tabular}{@{}l rr@{\,}c rr@{\,}c rr@{\,}c@{}}",
         r"\toprule"]
    head = ["Family"] + ["\\multicolumn{3}{c}{%s}" % HEAD_MLAB[m]
                         for m in HEAD_M]
    L.append(" & ".join(head) + r" \\")
    L.append(r"\cmidrule(lr){2-4}\cmidrule(lr){5-7}\cmidrule(lr){8-10}")
    L.append(" & ".join([""] + ["Mean TWT", "$\\Delta$ vs.\\ EDD [95\\% CI]",
                                ""] * 3) + r" \\")
    L.append(r"\midrule")

    seed_spans = {p: [] for p in POOLS}
    for fam in FAMILY_ORDER:
        if fam in GROUP_BREAK_BEFORE:
            L.append(r"\addlinespace[2pt]")
        label = FAMILY_LABEL[fam] + (DAGGER if fam in POOLS else "")
        cells = [label]
        for m in HEAD_M:
            r = scope_rows("emp_m", m).loc[fam]
            mean = fmt_mean(float(r.mean_family))
            if fam == REFERENCE:
                cells += [mean, "reference", ""]
                continue
            eq = r.verdict == "equivalent"
            cells += [bf(mean, eq),
                      bf(fmt_diff(float(r.mean_diff)) + "~"
                         + fmt_ci(float(r.ci_lo), float(r.ci_hi)), eq),
                      marker(r.verdict)]
            if fam in POOLS:
                seed_spans[fam].append(fmt_range(float(r.seed_min_mean),
                                                 float(r.seed_max_mean)))
        L.append(" & ".join(cells) + r" \\")
    L.append(r"\bottomrule")

    d = scope_rows("emp_m", HEAD_M[0])
    n_cfg = int(d.n_configs.iloc[0])
    n_clu = int(d.n_clusters.iloc[0])
    n_cmp = int((d.verdict != "reference").sum())
    mlabs = [HEAD_MLAB[m] for m in HEAD_M]
    spans = "; ".join(
        "%s and %s for %s (%d seeds)"
        % (", ".join(seed_spans[p][:-1]), seed_spans[p][-1], POOL_NOTE_NAME[p],
           int(d.loc[p, "seed_n"]))
        for p in POOLS)
    note = (
        "Note: bold marks a family whose paired difference against EDD is "
        "practically equivalent to it, and covers the mean and the difference "
        "cell of that crew multiplier; the rule is applied mechanically to "
        "every family, the pools included, with no exceptions. The reference "
        "row carries no verdict and is never bolded. %s Each crew multiplier "
        "holds %s configurations over %s base-instance clusters and compares %d "
        "families against EDD, the reference fixed before any result was "
        "read; a negative difference means the family is better than EDD. "
        "Rolling CP-SAT pairs on a subsample and is reported separately, so "
        "it is not a row here. %sA pool averages its seeds on each "
        "configuration before the pairing, so repeated training runs count "
        "once; across seeds the pool mean spans, at %s, %s and %s, %s. Lower "
        "TWT is better."
        % (verdict_rule_sentences(), f"{n_cfg:,}", f"{n_clu:,}", n_cmp,
           DAGGER_NOTE, mlabs[0], mlabs[1], mlabs[2], spans))
    L += note_par(note)
    write("t_headline_family", L)


# ===========================================================================
# T-rules-family: three scope blocks, percentage gap to EDD
# ===========================================================================
def table_rules_family():
    scopes = [(st, sc, lab) for _, block in RULE_BLOCKS
              for st, sc, lab in block]
    ncols = 1 + len(scopes)
    # A wider gap between the three blocks, so a reader does not read the last
    # column of one block as the first column of the next.
    spec = "@{}l" + "@{\\hspace{9pt}}".join(
        "r" * len(block) for _, block in RULE_BLOCKS)
    L = [r"% tab:rulesfamily -- ten method families against the EDD reference,",
         r"% by crew multiplier, by realised-utilisation bin and by generator",
         r"% target utilisation. BARE booktabs tabular; the float, caption and",
         r"% label live in paper/drafts/results.tex.",
         "%% Generated by scripts/r4_family_tables.py from %s." % REL_SRC,
         r"\setlength{\tabcolsep}{2.5pt}",
         r"\footnotesize",
         r"\begin{tabular}{" + spec + r"@{}}",
         r"\toprule"]

    head, rules, col = [""], [], 2
    for title, block in RULE_BLOCKS:
        head.append("\\multicolumn{%d}{c}{%s}" % (len(block), title))
        rules.append("\\cmidrule(lr){%d-%d}" % (col, col + len(block) - 1))
        col += len(block)
    L.append(" & ".join(head) + r" \\")
    L.append("".join(rules))
    L.append(" & ".join(["Family"] + [lab for _, _, lab in scopes]) + r" \\")
    L.append(r"\midrule")

    L.append(" & ".join(["Configurations $n$"]
                        + [f"{int(scope_rows(st, sc).n_configs.iloc[0]):,}"
                           for st, sc, _ in scopes]) + r" \\")
    L.append(r"\midrule")

    for fam in FAMILY_ORDER:
        if fam in GROUP_BREAK_BEFORE:
            L.append(r"\addlinespace[2pt]")
        label = FAMILY_LABEL[fam]
        if fam == REFERENCE:
            label = "EDD, mean TWT (reference)"
        if fam in POOLS:
            label += DAGGER
        cells = [label]
        for st, sc, _ in scopes:
            r = scope_rows(st, sc).loc[fam]
            if fam == REFERENCE:
                cells.append(fmt_mean(float(r.mean_family)))
                continue
            gap = 100.0 * float(r.mean_diff) / float(r.mean_edd)
            cells.append(fmt_pct(gap) + marker(r.verdict, sup=True))
        L.append(" & ".join(cells) + r" \\")
    L.append(r"\bottomrule")

    # The crew-multiplier block and the bin block are two cuts of one set of
    # empirical configurations, so the note's claim is checked here rather
    # than asserted in prose.
    def _n(block):
        return sum(int(scope_rows(st, sc).n_configs.iloc[0])
                   for st, sc, _ in block)
    n_emp = _n(RULE_BLOCKS[0][1])
    if n_emp != _n(RULE_BLOCKS[1][1]):
        raise SystemExit("t_rules_family: the crew-multiplier and "
                         "utilisation-bin blocks cover different configuration "
                         "counts (%d vs %d)" % (n_emp, _n(RULE_BLOCKS[1][1])))
    note = (
        "Note: every cell is the paired difference of the family against EDD, "
        "as a percentage of the EDD mean of the same scope, so a negative "
        "value means the family is better than EDD and the EDD row gives the "
        "level each percentage is taken from. The reference is EDD, fixed "
        "before any result was read, and each cell carries the "
        "practical-equivalence verdict of that difference as a superscript. "
        "%s The first two blocks cut the same %s empirical "
        "configurations two ways, by the crew multiplier applied to them and "
        "by the load the week actually carried, so their columns are not "
        "independent of each other; a utilisation bin holds configurations "
        "from all three crew multipliers. %sA pool averages its seeds on each "
        "configuration before the pairing. Rolling CP-SAT pairs on a "
        "subsample and is reported separately, so it is not a row here. Lower "
        "TWT is better."
        % (verdict_rule_pointer(), f"{n_emp:,}", DAGGER_NOTE))
    L += note_par(note)
    write("t_rules_family", L)


# ===========================================================================
# T-learning-family: the three policy pools, two stacked scope blocks
# ===========================================================================
def learning_cell(r):
    """One pool cell, set on two lines.

    The difference and its verdict marker sit on the first line and the
    interval underneath. Five columns of difference and interval set on one
    line already overrun the text width; stacking them keeps the full-length
    family labels the other two tables use and leaves the columns well apart.
    """
    eq = r.verdict == "equivalent"
    return (bf(fmt_lrn(float(r.mean_diff)), eq) + marker(r.verdict, sup=True),
            bf(fmt_lrn_ci(float(r.ci_lo), float(r.ci_hi)), eq))


def seed_span_phrase(pool, spans, seed_n):
    """One pool's clause of the note's seed-dispersion sentence."""
    return "%s and %s for %s (%d seeds)" % (spans[0], spans[1],
                                            POOL_NOTE_NAME[pool], seed_n)


def missing_pool_scopes():
    """Pool-scope combinations the source CSV does not carry.

    scope_rows already refuses a scope that is missing a family, so this
    reports the weaker failure the note depends on: a pool row that exists but
    carries no seed dispersion, which would leave the note's spans empty.
    """
    gaps = []
    for _, block, _ in LEARN_BLOCKS:
        for st, sc, _ in block:
            d = scope_rows(st, sc)
            for p in POOLS:
                if p not in d.index:
                    gaps.append("%s/%s: no %s row" % (st, sc, p))
                elif pd.isna(d.loc[p, "seed_min_mean"]) or pd.isna(
                        d.loc[p, "seed_max_mean"]):
                    gaps.append("%s/%s: %s carries no seed dispersion"
                                % (st, sc, p))
    return gaps


def table_learning_family():
    gaps = missing_pool_scopes()
    if gaps:
        raise SystemExit("t_learning_family: " + "; ".join(gaps))

    ncols = 1 + len(LEARN_BLOCKS[0][1])
    L = [r"% tab:learningfamily -- the three policy pools against the EDD",
         r"% reference, by realised-utilisation bin and by generator target",
         r"% utilisation. BARE booktabs tabular*, set to the line width; the",
         r"% float, caption and label live in paper/drafts/results.tex.",
         "%% Generated by scripts/r4_family_tables.py from %s." % REL_SRC,
         r"\setlength{\tabcolsep}{5pt}",
         r"\footnotesize",
         # Stacking the interval under its difference leaves the natural
         # tabular narrower than the text; the slack is spread evenly over the
         # column gaps so the table lines up with the note beneath it.
         r"\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}l"
         + "r" * (ncols - 1) + r"@{}}",
         r"\toprule"]

    spans = {p: [] for p in POOLS}
    for i, (title, block, _) in enumerate(LEARN_BLOCKS):
        if len(block) != ncols - 1:
            raise SystemExit("t_learning_family: block %r has %d scopes, the "
                             "table has %d columns" % (title, len(block), ncols))
        if i:
            L.append(r"\addlinespace[4pt]")
            L.append(r"\midrule")
        L.append("\\multicolumn{%d}{@{}l}{\\textit{%s}} \\\\" % (ncols, title))
        L.append("\\cmidrule(lr){2-%d}" % ncols)
        L.append(" & ".join(["Policy pool"] + [lab for _, _, lab in block])
                 + r" \\")
        L.append(r"\midrule")
        L.append(" & ".join(["Configurations $n$"]
                            + [f"{int(scope_rows(st, sc).n_configs.iloc[0]):,}"
                               .replace(",", "{,}")
                               for st, sc, _ in block]) + r" \\")
        L.append(" & ".join(["EDD reference, mean TWT"]
                            + [fmt_lrn(float(scope_rows(st, sc)
                                             .loc[REFERENCE, "mean_family"]))
                               for st, sc, _ in block]) + r" \\")
        for p in POOLS:
            L.append(r"\addlinespace[3pt]")
            top, bot = [FAMILY_LABEL[p] + DAGGER], [""]
            for st, sc, _ in block:
                a, b = learning_cell(scope_rows(st, sc).loc[p])
                top.append(a)
                bot.append(b)
            L.append(" & ".join(top) + r" \\")
            L.append(" & ".join(bot) + r" \\")
        # The seed dispersion quoted in the note is taken at the most
        # contended scope of the block, the last column of the block.
        st, sc, _ = block[-1]
        for p in POOLS:
            r = scope_rows(st, sc).loc[p]
            spans[p].append(fmt_lrn_range(float(r.seed_min_mean),
                                          float(r.seed_max_mean)))
    L.append(r"\bottomrule")

    hard = [b[-1] for b in LEARN_BLOCKS]
    seed_n = {}
    for p in POOLS:
        counts = {int(scope_rows(st, sc).loc[p, "seed_n"])
                  for _, block, _ in LEARN_BLOCKS for st, sc, _ in block}
        if len(counts) != 1:
            raise SystemExit("t_learning_family: %s is averaged over %s seeds "
                             "depending on the scope, so the note cannot quote "
                             "one count" % (p, sorted(counts)))
        seed_n[p] = counts.pop()
    disp = "; ".join(seed_span_phrase(p, spans[p], seed_n[p]) for p in POOLS)
    note = (
        "Note: each cell gives the paired difference of the policy pool "
        "against EDD, in units of weighted tardiness, on its first line, and "
        "the 95\\%% cluster-bootstrap interval of that difference over base "
        "instances underneath. A negative value means the pool is better than "
        "EDD, and the EDD row of the block gives the level each difference is "
        "taken from. The reference is EDD, fixed before any result was read, "
        "and it is the same reference in both blocks. Bold marks a difference "
        "that is practically equivalent to EDD, and covers both lines of the "
        "cell; the rule is applied mechanically to every cell, with no "
        "exceptions. "
        "%s %sA pool averages its seeds on each configuration before the "
        "pairing, so repeated training runs count once. At the most contended "
        "scope of each block the pool mean itself spans, at %s and at %s, %s. "
        "Lower TWT is better."
        % (verdict_rule_pointer(), DAGGER_NOTE, hard[0], hard[1], disp))
    L += note_par(note, env="tabular*")
    write("t_learning_family", L)


# ---------------------------------------------------------------------------
# cell-by-cell verification of t_learning_family
# ---------------------------------------------------------------------------
def _csv_index():
    """A second read of the source CSV, through csv rather than pandas.

    The verification below must not share a code path with the table it
    checks, or it would only confirm that the table agrees with itself.
    """
    idx = {}
    with open(ANA / "family_comparisons.csv", newline="") as fh:
        for row in csv.DictReader(fh):
            idx[(row["scope_type"], row["scope"], row["family"])] = row
    return idx


def _cells_of(line):
    """The cells of one body row of a bare tabular line."""
    return [c.strip() for c in line.rstrip().removesuffix(r"\\").split("&")]


def verify_learning_family():
    """Re-derive every printed cell from the CSV and compare with the file.

    Every number of the fragment is checked: the configuration counts, the EDD
    reference means, the three pool rows of both blocks, and the seed spans
    quoted in the note.
    """
    text = (TABDIR / "t_learning_family.tex").read_text()
    body, _, note = text.partition(TAB_END)
    lines = [l for l in body.splitlines() if l.rstrip().endswith(r"\\")]
    idx = _csv_index()
    checked = 0

    # Each block prints one title row, one column header, the count row, the
    # reference row and two rows per pool, and the tabular holds nothing else.
    per = 4 + 2 * len(POOLS)
    if len(lines) != per * len(LEARN_BLOCKS):
        raise SystemExit("verify: the tabular has %d body rows, expected %d"
                         % (len(lines), per * len(LEARN_BLOCKS)))

    def num(row, field, fmt=fmt_lrn):
        return fmt(float(row[field]))

    for bi, (title, block, _) in enumerate(LEARN_BLOCKS):
        head = per * bi
        want_title = ("\\multicolumn{%d}{@{}l}{\\textit{%s}} \\\\"
                      % (1 + len(block), title))
        if lines[head] != want_title:
            raise SystemExit("verify: block %d title is %r, expected %r"
                             % (bi, lines[head], want_title))
        got = _cells_of(lines[head + 1])
        want = ["Policy pool"] + [lab for _, _, lab in block]
        if got != want:
            raise SystemExit("verify: block %d header is %r, expected %r"
                             % (bi, got, want))
        counts = _cells_of(lines[head + 2])
        refs = _cells_of(lines[head + 3])
        for j, (st, sc, _) in enumerate(block):
            e = idx[(st, sc, REFERENCE)]
            want_n = f"{int(e['n_configs']):,}".replace(",", "{,}")
            if counts[j + 1] != want_n:
                raise SystemExit("verify: %s/%s count is %r, expected %r"
                                 % (st, sc, counts[j + 1], want_n))
            want_ref = num(e, "mean_family")
            if refs[j + 1] != want_ref:
                raise SystemExit("verify: %s/%s EDD mean is %r, expected %r"
                                 % (st, sc, refs[j + 1], want_ref))
            checked += 2
        for k, p in enumerate(POOLS):
            top = _cells_of(lines[head + 4 + 2 * k])
            bot = _cells_of(lines[head + 5 + 2 * k])
            if top[0] != FAMILY_LABEL[p] + DAGGER or bot[0] != "":
                raise SystemExit("verify: the rows of %s in block %d are "
                                 "labelled %r and %r" % (p, bi, top[0], bot[0]))
            for j, (st, sc, _) in enumerate(block):
                e = idx[(st, sc, p)]
                eq = e["verdict"] == "equivalent"
                want_t = (bf(num(e, "mean_diff"), eq)
                          + marker(e["verdict"], sup=True))
                want_b = bf("[%s, %s]" % (num(e, "ci_lo"), num(e, "ci_hi")), eq)
                if top[j + 1] != want_t:
                    raise SystemExit("verify: %s at %s/%s is %r, expected %r"
                                     % (p, st, sc, top[j + 1], want_t))
                if bot[j + 1] != want_b:
                    raise SystemExit("verify: the interval of %s at %s/%s is "
                                     "%r, expected %r"
                                     % (p, st, sc, bot[j + 1], want_b))
                checked += 2
    # The note quotes one seed span per pool per block, at the most contended
    # scope of the block; check each against that scope's own CSV row.
    for p in POOLS:
        spans, counts = [], set()
        for _, block, _ in LEARN_BLOCKS:
            st, sc, _ = block[-1]
            e = idx[(st, sc, p)]
            spans.append("%s%s%s" % (num(e, "seed_min_mean"), ENDASH,
                                     num(e, "seed_max_mean")))
            counts.add(int(float(e["seed_n"])))
            checked += 1
        phrase = seed_span_phrase(p, spans, sorted(counts)[0])
        if len(counts) != 1 or phrase not in note:
            raise SystemExit("verify: the note does not carry %r" % phrase)
    # A silent early exit from either loop would leave the file half checked,
    # so the count of checked values is itself asserted.
    want_checked = sum((2 + 2 * len(POOLS)) * len(block) + len(POOLS)
                       for _, block, _ in LEARN_BLOCKS)
    if checked != want_checked:
        raise SystemExit("verify: checked %d values, the fragment holds %d"
                         % (checked, want_checked))
    print("  verified %d values of t_learning_family against a second read "
          "of the CSV" % checked)


# ---------------------------------------------------------------------------
# standalone compile check
# ---------------------------------------------------------------------------
def check_latex(name="t_learning_family"):
    """Compile the fragment alone at the manuscript text width and measure it.

    cas-sc sets \\textwidth to 468.3324pt, so a fragment wider than that would
    overfull the float it is \\input into. The tabular is boxed and its width
    written to the log rather than eyeballed on the page.
    """
    env = dict(os.environ)
    env["PATH"] = (str(Path.home() / ".TinyTeX/bin/x86_64-linux")
                   + os.pathsep + env["PATH"])
    if shutil.which("pdflatex", path=env["PATH"]) is None:
        return "pdflatex not found on PATH; compile check skipped"
    frag = (TABDIR / f"{name}.tex").read_text()
    tabular, sep, _ = frag.partition(TAB_END)
    if not sep:
        return "%s: no tabular to measure" % name
    # Every line is commented out at its end: inside a box, the newline after
    # \setlength or after \end{tabular*} would otherwise become an interword
    # space and be counted as part of the measured width.
    tab = "%\n".join((tabular + sep).splitlines()) + "%\n"
    # The natural width, before the slack is spread over the column gaps, is
    # the number that says whether the table would still fit if it grew.
    nat = tab.replace("\\begin{tabular*}{\\linewidth}{@{\\extracolsep{\\fill}}",
                      "\\begin{tabular}{@{}").replace(TAB_END, "\\end{tabular}")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / f"{name}.tex").write_text(frag)
        # The width is taken on the tabular alone: the note that follows it is
        # a \parbox of the full line width and would mask the measurement.
        (td / "tabonly.tex").write_text(tab)
        (td / "tabnat.tex").write_text(nat)
        (td / "test.tex").write_text(
            "\\documentclass[10pt]{article}\n"
            "\\usepackage[textwidth=468.3324pt,textheight=680pt]{geometry}\n"
            "\\usepackage{booktabs}\n"
            # The float the fragment lands in does not indent, and a 15pt
            # indent alone would overfull the full-width note paragraph.
            "\\setlength{\\parindent}{0pt}\n"
            "\\newsavebox{\\tblbox}\n"
            "\\begin{document}\n"
            "\\sbox{\\tblbox}{\\input{tabonly}}\n"
            "\\typeout{TABULARWIDTH=\\the\\wd\\tblbox}\n"
            "\\sbox{\\tblbox}{\\input{tabnat}}\n"
            "\\typeout{NATURALWIDTH=\\the\\wd\\tblbox}\n"
            "\\typeout{TEXTWIDTH=\\the\\textwidth}\n"
            "\\input{%s}\n"
            "\\end{document}\n" % name)
        p = subprocess.run(["pdflatex", "-interaction=nonstopmode", "test.tex"],
                           cwd=td, env=env, capture_output=True, text=True)
        out = p.stdout
        w = re.search(r"TABULARWIDTH=([0-9.]+)pt", out)
        nw = re.search(r"NATURALWIDTH=([0-9.]+)pt", out)
        tw = re.search(r"TEXTWIDTH=([0-9.]+)pt", out)
        if p.returncode != 0 or None in (w, nw, tw):
            tail = "\n".join(out.strip().splitlines()[-25:])
            return "FAILED (exit %d)\n%s" % (p.returncode, tail)
        errs = [l for l in out.splitlines() if l.startswith("!")]
        over = [l for l in out.splitlines() if "Overfull" in l]
        wid, nat_w, txt = (float(w.group(1)), float(nw.group(1)),
                           float(tw.group(1)))
        return ("%s: %d errors, %d overfull boxes, tabular set to %.2fpt "
                "against a text width of %.2fpt (%+.2fpt); natural width "
                "%.2fpt, %.2fpt of slack spread over the column gaps"
                % (name, len(errs), len(over), wid, txt, wid - txt, nat_w,
                   txt - nat_w))


def main():
    print("family tables from %s" % REL_SRC)
    table_headline_family()
    table_rules_family()
    table_learning_family()
    verify_learning_family()
    print("  verdicts reaching a cell: %s"
          % ", ".join(sorted(verdicts_seen())))
    if "--check-latex" in sys.argv:
        print("  " + check_latex())


if __name__ == "__main__":
    main()
