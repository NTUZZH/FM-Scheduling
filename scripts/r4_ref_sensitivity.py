#!/usr/bin/env python
"""Reference-selection sensitivity of the Eval-B practical-equivalence sets.

Why this exists (revision item A3)
----------------------------------
``results/r4_final/analysis/equivalence.csv`` builds each scope's equivalence
set around the method with the LOWEST sample mean in that scope, and that
reference is a max-statistic: it is selected on the same data the intervals are
computed from, so it is biased low (the winner's curse) and a reader is
entitled to ask whether the reported sets are an artifact of choosing it.  This
script answers that by recomputing every scope with the reference FIXED A
PRIORI at EDD, the deployed status-quo rule, which no statistic can select.

Everything else is held constant: the same configurations, the same pairing on
the instance-configuration id, the same cluster bootstrap over base instances
(``fmwos.stats``, protocol section R4.5: 10000 resamples, master seed 12345),
the same equivalence margin rule max(1.0, 1% of the reference mean) now taken
on EDD's paired mean, and the same Holm family structure as the released
equivalence sets: within one scope, one family per method class against the
reference, with the reference's own row excluded from the correction.  Nothing
statistical is reimplemented here and nothing about the released analysis is
rewritten: this is a post-hoc sensitivity analysis reported beside the primary
one.

Reading the verdicts
--------------------
A method joins the EDD-reference set when its whole paired interval against EDD
lies inside the margin.  A method that is better than EDD beyond the margin is
NOT in that set (it is separated from the reference, in the good direction), so
the two set sizes answer different questions and are reported side by side:
the sample-best set answers "who is indistinguishable from the best method
here", the EDD set answers "who is indistinguishable from the rule an FM office
already runs".

Outputs
-------
  results/r4_final/analysis/ref_sensitivity.csv   one row per (scope, method)
  paper/supp_refsens.tex                          supplementary fragment
  paper/macros_r4d.tex                            \\rfd macros (this analysis
                                                  plus the corpus-share facts
                                                  of revision items A8 and A9)

Usage
-----
    PYTHONPATH=src python scripts/r4_ref_sensitivity.py
    PYTHONPATH=src python scripts/r4_ref_sensitivity.py --step analysis
    PYTHONPATH=src python scripts/r4_ref_sensitivity.py --step macros   # fragment + macros
    PYTHONPATH=src python scripts/r4_ref_sensitivity.py --check-latex

Re-running is idempotent: the same inputs and the same seeds reproduce every
digit, and every output file is rewritten in full.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from fmwos import stats                                    # noqa: E402
# Scope vocabulary, loading, macro plumbing and number formatting are shared
# with the definitive Eval-B analysis so that the two agree by construction.
from r4_analysis import (BIN_TOKEN, EQUIV_SCOPE_TYPES, FULL_COVERAGE,  # noqa: E402
                         M_TOKEN, RULES, U_TOKEN, V1_MLP, V2_ATTN, V2_MLP,
                         VALUE_COL, CREW_MULTIPLIERS, U_TARGETS, MacroFile,
                         existing_macro_names, f_int, f_text, load_results,
                         scope_frames)

REFERENCE = "edd"                       # fixed a priori; never data-selected

# Scope families that carry an equivalence set in the released analysis, in
# report order.  The CSV covers all of them; the supplementary table groups
# them under these headings.
SCOPE_TYPE_LABEL = {
    "emp_m": "Empirical anchors, verdict campuses, by crew multiplier",
    "emp_ubin": "Empirical anchors, by realised-utilisation bin",
    "emp_m_ubin": "Empirical anchors, crew multiplier by realised-utilisation bin",
    "gen_all": "Generator cells, pooled",
    "gen_utarget": "Generator cells, by target utilisation",
    "transfer": "Transfer campus (campus 1, reference capacity)",
    "stress": "Stress campus (campus 2, reference capacity)",
}


# --------------------------------------------------------------------------- #
# Analysis
# --------------------------------------------------------------------------- #
def ref_sensitivity(df: pd.DataFrame, eq: pd.DataFrame, n_boot: int,
                    seed: int) -> pd.DataFrame:
    """Per scope: every full-coverage method paired against EDD.

    The returned frame carries both memberships side by side, so a reader never
    has to join two files to see what the reference choice changed.
    """
    parts = []
    for scope_type, scope, sub in scope_frames(df):
        if scope_type not in EQUIV_SCOPE_TYPES:
            continue
        present = set(sub["method"])
        if REFERENCE not in present:
            raise SystemExit("scope %s|%s has no %s row"
                             % (scope_type, scope, REFERENCE))
        methods = [m for m in FULL_COVERAGE if m in present]
        s = sub.copy()
        s["analysis_scope"] = scope
        cmp_ = stats.compare_all(s, reference_methods=[REFERENCE],
                                 methods=methods, scope_cols=["analysis_scope"],
                                 value_col=VALUE_COL, n_boot=n_boot, seed=seed)
        if cmp_.empty:
            continue
        cmp_ = cmp_.drop(columns=["analysis_scope"])
        # EDD's own row: the reference is in its own set by definition, exactly
        # as the best method is in equivalence_set().
        own = sub[sub["method"] == REFERENCE]
        if "feasible" in own.columns:
            own = own[own["feasible"] == 1]
        mean_own = float(own[VALUE_COL].mean())
        cmp_ = pd.concat([cmp_, pd.DataFrame([{
            "scope": scope, "method": REFERENCE, "reference": REFERENCE,
            "family": stats.default_family(REFERENCE, REFERENCE),
            "n_configs": int(len(own)),
            "n_clusters": int(own["cluster"].nunique()),
            "mean_ref": mean_own, "mean_method": mean_own, "mean_diff": 0.0,
            "ci_lo": 0.0, "ci_hi": 0.0,
            "margin": stats.equivalence_margin(mean_own),
            "wilcoxon_p": 1.0, "holm_p": 1.0, "verdict": "equivalent",
        }])], ignore_index=True)
        cmp_.insert(0, "scope_type", scope_type)
        cmp_["scope"] = scope
        parts.append(cmp_)

    out = pd.concat(parts, ignore_index=True)
    out["in_set_vs_edd"] = (out["verdict"] == "equivalent").astype(int)
    out = out.rename(columns={"mean_diff": "mean_diff_vs_edd",
                              "mean_ref": "mean_edd"})

    # Side-by-side with the released, sample-best-reference analysis.
    keep = ["scope_type", "scope", "method", "best_method", "mean",
            "pct_from_best", "in_equivalence_set"]
    out = out.merge(eq[keep], on=["scope_type", "scope", "method"], how="left",
                    validate="one_to_one")
    if out["in_equivalence_set"].isna().any():
        bad = out[out["in_equivalence_set"].isna()].iloc[0]
        raise SystemExit("no released equivalence row for %s|%s|%s"
                         % (bad.scope_type, bad.scope, bad.method))
    out["in_equivalence_set"] = out["in_equivalence_set"].astype(int)
    out["membership"] = [
        ("in both" if a and b else "leaves" if b else "joins" if a else "out of both")
        for a, b in zip(out["in_set_vs_edd"] == 1, out["in_equivalence_set"] == 1)]

    cols = ["scope_type", "scope", "method", "family", "n_configs", "n_clusters",
            "mean", "mean_method", "mean_edd", "mean_diff_vs_edd", "ci_lo",
            "ci_hi", "margin", "wilcoxon_p", "holm_p", "verdict",
            "in_set_vs_edd", "in_equivalence_set", "membership", "best_method",
            "pct_from_best"]
    out = out.sort_values(["scope_type", "scope", "mean"], kind="mergesort")
    return out[cols].reset_index(drop=True)


def crosscheck_vs_comparisons(rs: pd.DataFrame, cmp_: pd.DataFrame) -> list:
    """Assert that the rows the released comparisons.csv already holds agree.

    ``comparisons.csv`` runs the same paired-vs-EDD comparison on every scope
    family except the crew-multiplier x utilisation cross, from the same seeds,
    so those rows must reproduce to the last digit; if they do not, one of the
    two analyses has drifted and no number here may be reported.

    ``holm_p`` is deliberately NOT compared. The released comparisons file
    corrects each family across its three references (EDD, ATC and WMDD) at
    once, whereas this analysis has one reference by construction, so its
    families are smaller and its adjusted p-values are correspondingly smaller.
    Every column the equivalence verdict depends on is compared instead, and
    the verdict itself.
    """
    ref = (cmp_[(cmp_["reference"] == REFERENCE) & (cmp_["method"] != REFERENCE)]
           .rename(columns={"mean_diff": "mean_diff_vs_edd",
                            "mean_ref": "mean_edd"}))
    j = rs.merge(ref, on=["scope_type", "scope", "method"], how="inner",
                 suffixes=("", "_rel"))
    checks = []
    # Tolerance only absorbs the CSV round-trip of the released file; the two
    # computations are the same code on the same seeds and must agree exactly.
    tol = 1e-9

    def numeric(col):
        a, b = j[col].to_numpy(float), j[col + "_rel"].to_numpy(float)
        bad = abs(a - b) > tol * pd.Series(abs(b)).clip(lower=1.0).to_numpy()
        return int(bad.sum())

    for col in ("mean_diff_vs_edd", "mean_edd", "ci_lo", "ci_hi", "margin",
                "wilcoxon_p"):
        checks.append({"check": "%s matches comparisons.csv" % col,
                       "n_rows": int(len(j)), "n_mismatch": numeric(col)})
    checks.append({"check": "verdict matches comparisons.csv",
                   "n_rows": int(len(j)),
                   "n_mismatch": int((j["verdict"] != j["verdict_rel"]).sum())})
    for c in checks:
        c["ok"] = bool(c["n_mismatch"] == 0)
        if not c["ok"]:
            raise SystemExit("cross-check failed: %s (%d of %d rows differ)"
                             % (c["check"], c["n_mismatch"], c["n_rows"]))
    return checks


def scope_summary(rs: pd.DataFrame) -> pd.DataFrame:
    """One row per scope: the two set sizes and what moved between them."""
    rows = []
    for (st, sc), d in rs.groupby(["scope_type", "scope"], sort=False):
        joins = sorted(d.loc[d["membership"] == "joins", "method"])
        leaves = sorted(d.loc[d["membership"] == "leaves", "method"])
        rows.append({
            "scope_type": st, "scope": sc,
            "n_configs": int(d["n_configs"].max()),
            "n_clusters": int(d["n_clusters"].max()),
            "n_methods": int(len(d)),
            "best_method": d["best_method"].iloc[0],
            "set_size_best_ref": int(d["in_equivalence_set"].sum()),
            "set_size_edd_ref": int(d["in_set_vs_edd"].sum()),
            "n_joins": len(joins), "n_leaves": len(leaves),
            "n_changed": len(joins) + len(leaves),
            "identical_set": int(not joins and not leaves),
            "n_better_than_edd": int((d["verdict"] == "better").sum()),
            "n_worse_than_edd": int((d["verdict"] == "worse").sum()),
            "n_inconclusive_vs_edd": int((d["verdict"] == "inconclusive").sum()),
            "joins": " ".join(joins), "leaves": " ".join(leaves),
        })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Supplementary fragment
# --------------------------------------------------------------------------- #
PRETTY_RULE = {"edd": "EDD", "pfifo": "pFIFO", "wmdd": "WMDD", "atc": "ATC",
               "wspt": "WSPT", "lpt": "LPT", "random": "Random"}
UBIN_LABEL = {"<0.5": "$u < 0.5$", "0.5-0.8": "$0.5 \\leq u < 0.8$",
              "0.8-1.0": "$0.8 \\leq u < 1.0$",
              "1.0-1.2": "$1.0 \\leq u < 1.2$", ">=1.2": "$u \\geq 1.2$"}


def scope_label(scope_type: str, scope: str) -> str:
    """Reader-facing label for one scope (no internal scope string survives)."""
    if scope_type == "emp_m":
        return "$m = %s$" % scope.split("=", 1)[1]
    if scope_type == "emp_ubin":
        return UBIN_LABEL[scope.split("=", 1)[1]]
    if scope_type == "emp_m_ubin":
        m, b = scope.split("|")
        return "$m = %s$, %s" % (m.split("=", 1)[1],
                                 UBIN_LABEL[b.split("=", 1)[1]])
    if scope_type == "gen_utarget":
        return "$u = %s$" % scope.split("=", 1)[1]
    if scope_type == "gen_all":
        return "all cells pooled"
    return "reference capacity"


def scope_label_text(scope_type: str, scope: str) -> str:
    """Plain-text label for one scope, for a macro that lands in running prose.

    :func:`scope_label` is for a table cell and uses math mode; a macro value
    must survive in text mode, so nothing here contains a maths symbol.
    """
    def bin_words(b):
        return {"<0.5": "realised utilisation below 0.5",
                ">=1.2": "realised utilisation 1.2 and above"}.get(
                    b, "realised utilisation %s" % b.replace("-", " to "))
    if scope_type == "emp_m":
        return "crew multiplier %s" % scope.split("=", 1)[1]
    if scope_type == "emp_ubin":
        return bin_words(scope.split("=", 1)[1])
    if scope_type == "emp_m_ubin":
        m, b = scope.split("|")
        return "crew multiplier %s at %s" % (m.split("=", 1)[1],
                                             bin_words(b.split("=", 1)[1]))
    if scope_type == "gen_utarget":
        return "generator cells at target utilisation %s" % scope.split("=", 1)[1]
    if scope_type == "gen_all":
        return "the generator cells pooled"
    if scope_type == "transfer":
        return "the transfer campus"
    return "the stress campus"


def scope_sort_key(scope_type: str, scope: str):
    """Report order: crew multipliers loosest first, bins by rising load.

    Sorting the scope strings alphabetically would print the slack bin fourth
    (``<0.5`` after ``1.0-1.2``), which is exactly the reading order the
    narrowing argument depends on, so the order comes from the protocol's own
    vocabularies instead.
    """
    rank = list(SCOPE_TYPE_LABEL).index(scope_type)
    ms = list(CREW_MULTIPLIERS)
    bins = list(stats.U_BIN_ORDER)
    if scope_type == "emp_m":
        return (rank, ms.index(float(scope.split("=", 1)[1])), 0)
    if scope_type == "emp_ubin":
        return (rank, bins.index(scope.split("=", 1)[1]), 0)
    if scope_type == "emp_m_ubin":
        m, b = scope.split("|")
        return (rank, ms.index(float(m.split("=", 1)[1])),
                bins.index(b.split("=", 1)[1]))
    if scope_type == "gen_utarget":
        return (rank, list(U_TARGETS).index(float(scope.split("=", 1)[1])), 0)
    return (rank, 0, 0)


def method_phrase(methods) -> str:
    """Compact list: transparent rules by name, learned checkpoints counted."""
    methods = list(methods)
    if not methods:
        return "none"
    rules = [PRETTY_RULE[m] for m in RULES if m in methods]
    n_pol = sum(1 for m in methods
                if m in V2_MLP or m in V2_ATTN or m in V1_MLP)
    parts = []
    if len(rules) == len(RULES):
        parts.append("every rule")
    elif rules:
        parts.append(", ".join(rules))
    if n_pol:
        parts.append("%d policy seed%s" % (n_pol, "" if n_pol == 1 else "s"))
    return "; ".join(parts)


def write_fragment(path: Path, summ: pd.DataFrame, rs: pd.DataFrame) -> None:
    ncol = 7
    # Header labels are kept short because the header row, not any data row,
    # sets this table's width in the supplement's column.
    head = " & ".join(["Scope", "$n$", "Set, sample best", "Set, EDD",
                       "Worse than EDD", "Joins the set",
                       "Leaves the set"]) + r" \\"
    L = [r"% supp_refsens.tex -- reference-selection sensitivity (revision item A3).",
         r"% GENERATED FILE. Do not edit by hand: rebuild with",
         r"%   PYTHONPATH=src python scripts/r4_ref_sensitivity.py",
         r"% Every number is read from results/r4_final/analysis/ref_sensitivity.csv,",
         r"% written by the same script in the same run. This fragment is a complete",
         r"% longtable environment (caption, label and note included); \input{} it.",
         r"\begingroup",
         r"\setlength{\tabcolsep}{4pt}",
         r"\footnotesize",
         r"\begin{longtable}{@{}l r c c c l l@{}}",
         r"\caption{Reference-selection sensitivity: every scope's "
         r"practical-equivalence set recomputed with the reference fixed a "
         r"priori at EDD instead of the scope's sample-best method.}"
         r"\label{tab:supp-refsens}\\",
         r"\toprule", head, r"\midrule", r"\endfirsthead",
         r"\multicolumn{%d}{@{}l}{\footnotesize Table~\thetable\ (continued)}\\" % ncol,
         r"\toprule", head, r"\midrule", r"\endhead",
         r"\midrule",
         r"\multicolumn{%d}{r@{}}{\footnotesize continued on the next page}\\" % ncol,
         r"\endfoot", r"\bottomrule", r"\endlastfoot"]

    first = True
    for st in SCOPE_TYPE_LABEL:
        d = summ[summ["scope_type"] == st]
        if d.empty:
            continue
        if not first:
            L.append(r"\addlinespace[3pt]")
        first = False
        L.append(r"\multicolumn{%d}{@{}l}{\textit{%s}}\\*"
                 % (ncol, SCOPE_TYPE_LABEL[st]))
        L.append(r"\addlinespace[1pt]")
        d = d.sort_values("scope", key=lambda s: s.map(
            lambda sc: scope_sort_key(st, sc)), kind="mergesort")
        for r in d.itertuples():
            L.append(" & ".join([
                scope_label(r.scope_type, r.scope),
                "%d" % r.n_configs,
                "%d of %d" % (r.set_size_best_ref, r.n_methods),
                "%d of %d" % (r.set_size_edd_ref, r.n_methods),
                "%d" % r.n_worse_than_edd,
                method_phrase(r.joins.split()),
                method_phrase(r.leaves.split())]) + r" \\")

    n_scopes = int(len(summ))
    n_ident = int(summ["identical_set"].sum())
    worst = summ.sort_values(["n_changed", "scope_type", "scope"]).iloc[-1]
    note = (
        "Note: the released analysis builds each set around the method with the "
        "lowest sample mean in that scope, which is selected on the same data "
        "the intervals come from. This table repeats every scope with EDD as "
        "the reference, a rule fixed before the data were seen, holding "
        "everything else constant: the same configurations, the same pairing on "
        "the instance-configuration identifier, the same 95\\%% cluster bootstrap "
        "over base instances with %s resamples, and the same margin rule, the "
        "larger of 1.0 and 1\\%% of the reference mean, now taken on EDD's "
        "paired mean. A method joins the EDD set when its whole paired interval "
        "against EDD lies inside that margin; a method whose interval lies "
        "wholly above the margin is worse than EDD and is counted in its own "
        "column, and every remaining method is inconclusive, its interval "
        "straddling a margin edge. No method is better than EDD beyond the "
        "margin in any scope (%d of %s method-scope comparisons), so nothing is "
        "excluded from an EDD set for outperforming the reference. The two set "
        "sizes therefore answer different questions: which methods are "
        "indistinguishable from the best method of the scope, and which are "
        "indistinguishable from the rule an FM office already runs. The set is "
        "identical under both references in %d of the %d scopes, and the "
        "largest change is %d of %d methods, on the %d configurations of the "
        "%s cross scope. $n$ counts configurations. Learned checkpoints are "
        "counted rather than named because they are interchangeable training "
        "seeds of one method."
        % ("{:,}".format(stats.N_BOOT).replace(",", "{,}"),
           int((rs["verdict"] == "better").sum()),
           "{:,}".format(len(rs)).replace(",", "{,}"), n_ident, n_scopes,
           int(worst.n_changed), int(worst.n_methods), int(worst.n_configs),
           scope_label(worst.scope_type, worst.scope)))
    L += [r"\end{longtable}",
          r"\vspace{-6pt}",
          r"\noindent\parbox{\linewidth}{\scriptsize %s}" % note,
          r"\endgroup", ""]
    path.write_text("\n".join(L) + "\n")


# --------------------------------------------------------------------------- #
# Macros
# --------------------------------------------------------------------------- #
class RefMacroFile(MacroFile):
    """MacroFile that enforces the \\rfd prefix and names a colliding file."""

    def __init__(self, sources: dict):
        self.source_of = {n: p for p, names in sources.items() for n in names}
        super().__init__(set(self.source_of))

    def add(self, name, value, source):
        if not name.startswith("rfd"):
            raise SystemExit("macro %r does not use the \\rfd prefix" % name)
        if name in self.source_of:
            raise SystemExit("macro %r is already defined in %s"
                             % (name, self.source_of[name]))
        super().add(name, value, source)


def f_share(x) -> str:
    """A share written as a percentage with two decimals (shares here are <1%)."""
    return "%.2f" % (100.0 * float(x))


def build_macros(rs: pd.DataFrame, summ: pd.DataFrame, paper_dir: Path,
                 profile_dir: Path, revision_dir: Path) -> tuple:
    """Write paper/macros_r4d.tex from this run's CSV, read back from disk."""
    summ_by = {(r.scope_type, r.scope): r for r in summ.itertuples()}

    mf = RefMacroFile({
        "paper/macros.tex": existing_macro_names(paper_dir / "macros.tex"),
        "paper/macros_r4.tex": existing_macro_names(paper_dir / "macros_r4.tex"),
        "paper/macros_r4b.tex": existing_macro_names(paper_dir / "macros_r4b.tex"),
        "paper/macros_r4c.tex": existing_macro_names(paper_dir / "macros_r4c.tex"),
    })

    # ---- set sizes under the EDD reference ------------------------------ #
    mf.section("Practical-equivalence set sizes with the reference fixed a "
               "priori at EDD (analysis/ref_sensitivity.csv)")
    for scope_type, prefix, items in (
            ("emp_m", "rfdEmpSetSize",
             [("m=%s" % m, M_TOKEN[m]) for m in CREW_MULTIPLIERS]),
            ("emp_ubin", "rfdBinSetSize",
             [("u_bin=%s" % b, t) for b, t in BIN_TOKEN.items()]),
            ("gen_utarget", "rfdGenSetSize",
             [("u_target=%s" % u, U_TOKEN[u]) for u in U_TARGETS])):
        for scope, tok in items:
            r = summ_by.get((scope_type, scope))
            if r is None:
                continue
            mf.add(prefix + tok, f_int(r.set_size_edd_ref),
                   "ref_sensitivity.csv scope_type=%s scope=%s "
                   "field=in_set_vs_edd (EDD itself included, as the released "
                   "sets include their best method)" % (scope_type, scope))

    # ---- what the reference choice changes ------------------------------ #
    mf.section("What fixing the reference at EDD changes "
               "(analysis/ref_sensitivity.csv)")
    worst = summ.sort_values(["n_changed", "scope_type", "scope"]).iloc[-1]
    mf.add("rfdScopes", f_int(len(summ)),
           "ref_sensitivity.csv distinct (scope_type, scope) pairs recomputed")
    mf.add("rfdScopesIdentical", f_int(int(summ["identical_set"].sum())),
           "ref_sensitivity.csv scopes whose EDD-reference set holds exactly "
           "the same methods as the released sample-best-reference set")
    mf.add("rfdScopesSmaller",
           f_int(int((summ["set_size_edd_ref"] < summ["set_size_best_ref"]).sum())),
           "ref_sensitivity.csv scopes where the EDD-reference set is smaller "
           "than the released one (fields set_size_edd_ref, set_size_best_ref)")
    mf.add("rfdCompRows", f_int(len(rs)),
           "ref_sensitivity.csv rows (every method-scope comparison recomputed "
           "against the EDD reference), the denominator of \\rfdBetterRows")
    mf.add("rfdBetterRows", f_int(int((rs["verdict"] == "better").sum())),
           "ref_sensitivity.csv field=verdict (method-scope rows whose whole "
           "interval lies below EDD by more than the margin, out of %d)"
           % len(rs))
    mf.add("rfdMaxChange", f_int(int(worst.n_changed)),
           "ref_sensitivity.csv largest membership change, in methods "
           "(field=membership, joins + leaves)")
    mf.add("rfdMaxChangeScope",
           f_text(scope_label_text(worst.scope_type, worst.scope)),
           "ref_sensitivity.csv scope of the largest membership change")
    mf.add("rfdMaxChangeConfigs", f_int(int(worst.n_configs)),
           "ref_sensitivity.csv field=n_configs in that scope")

    # ---- corpus shares behind the trade derivation (items A8, A9) -------- #
    mf.section("Cleaned-corpus scale and the two trade-derivation choices "
               "(results/r4_revision/labor_audit.json, "
               "results/p0_profile/trade_shares.json)")
    audit = json.loads((revision_dir / "labor_audit.json").read_text())
    mf.add("rfdSixCampusWos",
           f_int(audit["scopes"]["six_campuses"]["work_orders"]),
           "results/r4_revision/labor_audit.json "
           "scopes.six_campuses.work_orders (retained work orders of the six "
           "campuses that supply instances, after R2-R7)")
    shares = json.loads((profile_dir / "trade_shares.json").read_text())
    six = shares["six_campuses"]
    mf.add("rfdUnkShare", f_share(six["unk_share"]),
           "results/p0_profile/trade_shares.json six_campuses.unk_share "
           "(work orders with no system code, as a percentage of the "
           "six-campus corpus; "
           "scripts/r4_trade_shares.py)")
    mf.add("rfdMiscShare", f_share(six["misc_share"]),
           "results/p0_profile/trade_shares.json six_campuses.misc_share "
           "(work orders handled by the merged MISC crew, as a percentage "
           "of the six-campus corpus; scripts/r4_trade_shares.py)")

    header = "\n".join([
        "% macros_r4d.tex -- reference-selection sensitivity (revision item A3)",
        "% and the cleaned-corpus scale and trade-derivation shares (items A8,",
        "% A9).",
        "% GENERATED FILE. Do not edit by hand: rebuild with",
        "%   PYTHONPATH=src python scripts/r4_ref_sensitivity.py",
        "% Every value below is transcribed by that script from a generated",
        "% file; the trailing comment names the file and the field it came from.",
        "%% Generated %s." % datetime.now().strftime("%Y-%m-%d %H:%M"),
        "% Prefix \\rfd; no name here is defined in macros.tex, macros_r4.tex,",
        "% macros_r4b.tex or macros_r4c.tex (a collision is a hard error in the",
        "% generator).",
        "% The reference is EDD throughout this file, fixed before the data were",
        "% seen; the released sets in macros_r4.tex use the scope's sample-best",
        "% method instead.",
    ])
    (paper_dir / "macros_r4d.tex").write_text(mf.render(header))
    return len(mf.names), sorted(mf.names)


# --------------------------------------------------------------------------- #
# LaTeX compile check
# --------------------------------------------------------------------------- #
def check_latex(paper_dir: Path) -> str:
    """Compile a throwaway document that inputs both generated files.

    The macro file is exercised by expanding every macro it defines, and the
    supplementary fragment by typesetting it inside the packages
    paper/supplementary.tex loads, so a broken fragment fails here rather than
    in the manuscript build.
    """
    import os
    import re
    import shutil
    import subprocess
    import tempfile

    names = re.findall(r"\\newcommand\{\\([A-Za-z]+)\}",
                       (paper_dir / "macros_r4d.tex").read_text())
    env = dict(os.environ)
    env["PATH"] = (str(Path.home() / ".TinyTeX/bin/x86_64-linux") + os.pathsep
                   + env["PATH"])
    if shutil.which("pdflatex", path=env["PATH"]) is None:
        return "pdflatex not found on PATH; compile check skipped"
    # The fragment is typeset in the supplement's own class and page width, so
    # a row that overflows THERE is caught here rather than at the next build.
    cas = (paper_dir / "cas-sc.cls").exists()
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        wanted = ["macros_r4d.tex", "supp_refsens.tex"]
        if cas:
            wanted += ["cas-sc.cls", "cas-common.sty"]
        for f in wanted:
            shutil.copy(paper_dir / f, td / f)
        body = "\n".join(r"\noindent %s: \%s\par" % (n, n) for n in names)
        preamble = ("\\documentclass[a4paper,fleqn]{cas-sc}\n"
                    "\\usepackage{newtxtext}\n\\usepackage{newtxmath}\n"
                    "\\renewcommand{\\sfdefault}{\\rmdefault}\n"
                    "\\RenewDocumentCommand\\printorcid{}{}\n"
                    "\\setlength{\\emergencystretch}{1.5em}\n" if cas else
                    "\\documentclass[10pt]{article}\n"
                    "\\usepackage[margin=1in]{geometry}\n")
        (td / "test.tex").write_text(
            preamble
            + "\\usepackage{booktabs}\n\\usepackage{longtable}\n"
              "\\usepackage{array}\n"
              "\\input{macros_r4d}\n"
              "\\begin{document}\n%s\n\\clearpage\n"
              "\\input{supp_refsens}\n\\end{document}\n" % body)
        p = subprocess.run(["pdflatex", "-interaction=nonstopmode",
                            "-halt-on-error", "test.tex"],
                           cwd=td, env=env, capture_output=True, text=True)
        if p.returncode != 0:
            tail = "\n".join(p.stdout.strip().splitlines()[-25:])
            return "FAILED (exit %d)\n%s" % (p.returncode, tail)
        log = (td / "test.log").read_text(errors="replace")
        over = len(re.findall(r"Overfull \\hbox", log))
        pdf = td / "test.pdf"
        return ("OK: %d macros and the supplementary fragment compiled in the "
                "%s class, %d bytes of PDF, %d overfull hbox warning(s)"
                % (len(names), "cas-sc" if cas else "article",
                   pdf.stat().st_size if pdf.exists() else 0, over))


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", default=str(ROOT / "results/r4_final/results.csv"))
    ap.add_argument("--out", default=str(ROOT / "results/r4_final/analysis"))
    ap.add_argument("--paper-dir", default=str(ROOT / "paper"))
    ap.add_argument("--profile-dir", default=str(ROOT / "results/p0_profile"))
    ap.add_argument("--revision-dir", default=str(ROOT / "results/r4_revision"))
    ap.add_argument("--step", choices=("all", "analysis", "macros"), default="all")
    ap.add_argument("--n-boot", type=int, default=stats.N_BOOT)
    ap.add_argument("--seed", type=int, default=stats.SEED)
    ap.add_argument("--check-latex", action="store_true",
                    help="compile a scratch document that uses every macro")
    args = ap.parse_args()

    out = Path(args.out)
    paper_dir = Path(args.paper_dir)
    t0 = datetime.now()

    if args.step in ("all", "analysis"):
        df = load_results(Path(args.csv))
        eq = pd.read_csv(out / "equivalence.csv")
        rs = ref_sensitivity(df, eq, args.n_boot, args.seed)
        checks = crosscheck_vs_comparisons(rs, pd.read_csv(out / "comparisons.csv"))
        print("cross-checks vs comparisons.csv: %d passed" % len(checks))
        rs.to_csv(out / "ref_sensitivity.csv", index=False)
        summ = scope_summary(rs)
        print("ref sensitivity: %d rows over %d scopes; identical set in %d"
              % (len(rs), len(summ), int(summ["identical_set"].sum())))

    if args.step in ("all", "macros"):
        # Both paper artifacts are rebuilt from the CSV on disk, so a wording
        # change costs a second rather than another bootstrap.
        rs = pd.read_csv(out / "ref_sensitivity.csv")
        summ = scope_summary(rs)
        write_fragment(paper_dir / "supp_refsens.tex", summ, rs)
        print("fragment written to %s" % (paper_dir / "supp_refsens.tex"))
        n, _ = build_macros(rs, summ, paper_dir, Path(args.profile_dir),
                            Path(args.revision_dir))
        print("macros: %d written to %s" % (n, paper_dir / "macros_r4d.tex"))

    if args.check_latex:
        print("latex check: %s" % check_latex(paper_dir))
    print("done (%.1f s)" % (datetime.now() - t0).total_seconds())


if __name__ == "__main__":
    main()
