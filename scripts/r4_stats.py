#!/usr/bin/env python
"""R4 statistics driver: paired comparisons and equivalence sets from any
results.csv (protocol §R4.5, spec S3 in docs/protocol.md §R4).

Every R4 analysis (Eval-B, visibility, the four robustness runners) produces a
results.csv with the same core columns -- an instance-configuration ``id``, a
``method``, and a weighted-tardiness value -- so one driver serves all of them.
The statistics live in ``fmwos.stats``; this script only selects scopes, calls
them, and writes the outputs.

What it computes, on three scope families:

  overall   all rows pooled;
  scope     one scope per group of --scope-cols (e.g. campus,size);
  u_bin     one scope per realized-utilization bin, the protocol's primary
            explanatory variable, whenever the file carries u_realized.

For each scope it writes (a) the paired comparison of every method against
every reference method, with a 95% cluster-bootstrap CI over base instances, a
Wilcoxon p, a Holm-adjusted p within the comparison family, and the
equivalence verdict; and (b) the equivalence set of the best-mean method.

Outputs (in --out)
------------------
  comparisons.csv      one row per (scope_type, scope, method, reference)
  equivalence_sets.csv one row per (scope_type, scope, method)
  method_means.csv     mean value and row count per (scope_type, scope, method)
  summary.md           readable report: means, equivalence sets, comparisons
  meta.json            arguments, input file, row counts, library constants

Usage
-----
    PYTHONPATH=src python scripts/r4_stats.py --csv RESULTS.csv --out DIR \\
        [--value-col wwt] [--scope-cols campus,size] [--policy-tag v2rl] \\
        [--references edd,atc,wmdd] [--n-boot 10000] [--seed 12345]

  --policy-tag T  keep only the learned-policy methods whose name starts with T
                  (rules and optimizers are always kept); use it to score one
                  checkpoint pool at a time.
  --n-boot N      bootstrap resamples (the protocol number is 10000; a smaller
                  value is for plumbing smoke tests only and is recorded in
                  meta.json and in the summary header).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from fmwos import stats                                    # noqa: E402
from fmwos.io import normalize_method_column               # noqa: E402  ("mor"->"lpt")

# Reference methods of the revision: the strongest transparent rules (§R4.5).
# The tuned ATC variant, if the file carries one, is added automatically.
DEFAULT_REFERENCES = ("edd", "atc", "wmdd")
# Value column candidates, in preference order (v1.0 files write "wwt"; the
# protocol text and the r2 side analyses call the same quantity "twt").
VALUE_COL_CANDIDATES = ("wwt", "twt")


def _resolve_value_col(df: pd.DataFrame, requested: str | None) -> str:
    if requested:
        if requested not in df.columns:
            sys.exit("value column %r not in the results csv (columns: %s)"
                     % (requested, ", ".join(df.columns)))
        return requested
    for c in VALUE_COL_CANDIDATES:
        if c in df.columns:
            return c
    sys.exit("no value column found; pass --value-col (looked for %s)"
             % ", ".join(VALUE_COL_CANDIDATES))


def _select_methods(df: pd.DataFrame, policy_tag: str | None,
                    methods_arg: str | None):
    """Method list to analyse, in a stable order (rules, optimizers, policies)."""
    present = sorted(pd.unique(df["method"].astype(str)))
    if methods_arg:
        wanted = [m.strip() for m in methods_arg.split(",") if m.strip()]
        missing = [m for m in wanted if m not in present]
        if missing:
            sys.exit("methods not in the results csv: %s" % ", ".join(missing))
        return wanted
    if policy_tag:
        present = [m for m in present
                   if stats.method_class(m) != "policy"
                   or m.startswith(policy_tag)]
    order = {"rule": 0, "optimizer": 1, "policy": 2}
    return sorted(present, key=lambda m: (order[stats.method_class(m)], m))


def _select_references(methods, refs_arg: str | None):
    if refs_arg:
        wanted = [r.strip() for r in refs_arg.split(",") if r.strip()]
        missing = [r for r in wanted if r not in methods]
        if missing:
            sys.exit("reference methods not available: %s" % ", ".join(missing))
        return wanted
    refs = [r for r in DEFAULT_REFERENCES if r in methods]
    # Tuned ATC (R4.3) is a reference wherever it was run.
    refs += sorted(m for m in methods if m.startswith("atc_k"))
    if not refs:
        # No transparent reference present: fall back to the best-mean method so
        # the comparison table is still anchored on something the reader sees.
        refs = [methods[0]]
    return refs


def _fmt(x, nd=3):
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "-"
    return ("%%.%df" % nd) % float(x)


def _fmt_p(p):
    if p is None or pd.isna(p):
        return "-"
    p = float(p)
    return "%.4f" % p if p >= 1e-4 else "%.1e" % p


def _means_frame(df, scope_type, scope_cols, value_col, feasible_col):
    rows = []
    for label, key, sub in stats.iter_scopes(df, scope_cols):
        means = stats.method_means(sub, value_col=value_col,
                                   feasible_col=feasible_col)
        counts = (sub[sub[feasible_col] == 1] if feasible_col in sub.columns
                  else sub).groupby("method").size()
        for meth in sorted(means.index):
            row = dict(key)
            row.update({"scope_type": scope_type, "scope": label,
                        "method": meth, "n_rows": int(counts.get(meth, 0)),
                        "mean": float(means[meth])})
            rows.append(row)
    return pd.DataFrame(rows)


def main(argv=None):
    ap = argparse.ArgumentParser(description="R4 paired statistics driver.")
    ap.add_argument("--csv", required=True, help="results csv to analyse")
    ap.add_argument("--out", required=True, help="output directory")
    ap.add_argument("--value-col", default=None,
                    help="value column (default: wwt, else twt)")
    ap.add_argument("--scope-cols", default=None,
                    help="comma-separated columns defining the per-scope "
                         "analysis (e.g. campus,size)")
    ap.add_argument("--policy-tag", default=None,
                    help="keep only policy methods with this name prefix")
    ap.add_argument("--methods", default=None,
                    help="explicit comma-separated method list (overrides "
                         "--policy-tag)")
    ap.add_argument("--references", default=None,
                    help="comma-separated reference methods "
                         "(default: edd,atc,wmdd + any tuned atc_k*)")
    ap.add_argument("--n-boot", type=int, default=stats.N_BOOT,
                    help="bootstrap resamples (default %d)" % stats.N_BOOT)
    ap.add_argument("--seed", type=int, default=stats.SEED,
                    help="bootstrap master seed (default %d)" % stats.SEED)
    ap.add_argument("--alpha", type=float, default=stats.ALPHA,
                    help="1-alpha is the interval level (default %.2f)"
                         % stats.ALPHA)
    ap.add_argument("--margin-abs", type=float, default=stats.MARGIN_ABS,
                    help="absolute equivalence margin (default %.1f)"
                         % stats.MARGIN_ABS)
    ap.add_argument("--margin-rel", type=float, default=stats.MARGIN_REL,
                    help="relative equivalence margin (default %.2f)"
                         % stats.MARGIN_REL)
    ap.add_argument("--id-col", default="id", help="configuration id column")
    ap.add_argument("--on-duplicate", default="error", choices=["error", "mean"],
                    help="what to do when a method has several rows per id "
                         "within a scope (default: error, which means the "
                         "frame needs another scope column)")
    args = ap.parse_args(argv)

    csv_path = Path(args.csv)
    if not csv_path.exists():
        sys.exit("results csv not found: %s" % csv_path)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = normalize_method_column(pd.read_csv(csv_path))
    if args.id_col not in df.columns or "method" not in df.columns:
        sys.exit("results csv needs '%s' and 'method' columns" % args.id_col)
    value_col = _resolve_value_col(df, args.value_col)
    feasible_col = "feasible"
    n_rows = len(df)
    n_infeas = int((df[feasible_col] != 1).sum()) if feasible_col in df.columns \
        else 0

    df = stats.add_base_instance_id(df, id_col=args.id_col)
    df = stats.add_utilization_bin(df)
    has_u = "u_realized" in df.columns

    # Cross-check the cluster derivation whenever the runner recorded its own
    # base id (p4_sensitivity does): a mismatch means a transform suffix is
    # missing from BASE_ID_SUFFIX_RE and every CI below would be too narrow.
    cluster_check = None
    if "base_id" in df.columns:
        agree = int((df["cluster"] == df["base_id"].astype(str)).sum())
        cluster_check = {"rows": int(len(df)), "agree": agree,
                         "disagree": int(len(df)) - agree}

    methods = _select_methods(df, args.policy_tag, args.methods)
    df = df[df["method"].isin(methods)].copy()
    references = _select_references(methods, args.references)

    scope_cols = [c.strip() for c in (args.scope_cols or "").split(",")
                  if c.strip()]
    scopes = [("overall", [])]
    if scope_cols:
        scopes.append(("scope", scope_cols))
    if has_u:
        scopes.append(("u_bin", ["u_bin"]))

    kw = dict(value_col=value_col, id_col=args.id_col,
              feasible_col=feasible_col, n_boot=args.n_boot, seed=args.seed,
              alpha=args.alpha, margin_abs=args.margin_abs,
              margin_rel=args.margin_rel, on_duplicate=args.on_duplicate)

    comp_parts, eq_parts, mean_parts = [], [], []
    for scope_type, cols in scopes:
        comp = stats.compare_all(df, references, methods=methods,
                                 scope_cols=cols, **kw)
        comp.insert(0, "scope_type", scope_type)
        comp_parts.append(comp)
        eq = stats.equivalence_set(df, methods=methods, scope_cols=cols, **kw)
        eq.insert(0, "scope_type", scope_type)
        eq_parts.append(eq)
        mean_parts.append(_means_frame(df, scope_type, cols, value_col,
                                       feasible_col))

    comp_df = pd.concat(comp_parts, ignore_index=True)
    eq_df = pd.concat(eq_parts, ignore_index=True)
    mean_df = pd.concat(mean_parts, ignore_index=True)

    comp_path = out_dir / "comparisons.csv"
    eq_path = out_dir / "equivalence_sets.csv"
    mean_path = out_dir / "method_means.csv"
    comp_df.to_csv(comp_path, index=False)
    eq_df.to_csv(eq_path, index=False)
    mean_df.to_csv(mean_path, index=False)

    # ---- summary.md ---------------------------------------------------------
    lines = []
    lines.append("# R4 statistics — %s" % csv_path.name)
    lines.append("")
    lines.append("Source: `%s` (%d rows, %d infeasible excluded). Value column: "
                 "`%s`. Methods: %s. References: %s."
                 % (csv_path, n_rows, n_infeas, value_col,
                    ", ".join(methods), ", ".join(references)))
    lines.append("")
    lines.append("Paired on instance-configuration id; clusters = base "
                 "instances (%d clusters over %d configurations). "
                 "%d%% percentile cluster bootstrap, %d resamples, seed %d. "
                 "Equivalence margin = max(%.1f, %.0f%% of the reference "
                 "mean). Holm correction within each comparison family "
                 "(rule-vs-rule, policy-vs-rule, ...). A negative difference "
                 "means the method is BETTER than its reference."
                 % (df["cluster"].nunique(), df[args.id_col].nunique(),
                    round(100 * (1 - args.alpha)), args.n_boot, args.seed,
                    args.margin_abs, 100 * args.margin_rel))
    if args.n_boot < stats.N_BOOT:
        lines.append("")
        lines.append("**Plumbing run: n_boot=%d is below the protocol's %d; "
                     "these intervals are not reportable.**"
                     % (args.n_boot, stats.N_BOOT))
    if cluster_check is not None:
        lines.append("")
        lines.append("Cluster cross-check against the file's own `base_id` "
                     "column: %d/%d rows agree (%d disagree)."
                     % (cluster_check["agree"], cluster_check["rows"],
                        cluster_check["disagree"]))
    lines.append("")

    lines.append("## Mean %s per method (pooled)" % value_col)
    lines.append("")
    lines.append("| method | n | mean | in equivalence set |")
    lines.append("|---|---|---|---|")
    ov_eq = eq_df[eq_df["scope_type"] == "overall"].set_index("method")
    ov_means = mean_df[mean_df["scope_type"] == "overall"]
    for _, r in ov_means.sort_values("mean").iterrows():
        flag = "-"
        if r["method"] in ov_eq.index:
            e = ov_eq.loc[r["method"]]
            flag = ("best" if r["method"] == e["best_method"]
                    else ("yes" if int(e["in_equivalence_set"]) else "no"))
        lines.append("| %s | %d | %s | %s |"
                     % (r["method"], int(r["n_rows"]), _fmt(r["mean"]), flag))
    lines.append("")

    lines.append("## Equivalence sets")
    lines.append("")
    for scope_type in [s for s, _ in scopes]:
        part = eq_df[eq_df["scope_type"] == scope_type]
        if part.empty:
            continue
        lines.append("### scope_type = %s" % scope_type)
        lines.append("")
        lines.append("| scope | best | mean(best) | equivalent to best | n_clusters |")
        lines.append("|---|---|---|---|---|")
        for scope, grp in part.groupby("scope", sort=True):
            best = grp["best_method"].iloc[0]
            members = sorted(grp[grp["in_equivalence_set"] == 1]["method"])
            nc = int(grp["n_clusters"].max())
            lines.append("| %s | %s | %s | %s | %d |"
                         % (scope, best, _fmt(grp["mean_best"].iloc[0]),
                            ", ".join(m for m in members if m != best) or "(none)",
                            nc))
        lines.append("")
        # A method evaluated on a subsample (rolling CP-SAT: 8 instances per
        # cell) is ranked on a different configuration set, so its position in
        # the mean ordering is a composition artifact; its paired comparison
        # against the best method is unaffected and is what the reader should
        # use.
        partial = part[part["coverage"] < 0.99]
        if not partial.empty:
            worst = partial.groupby("method")["coverage"].min().sort_values()
            lines.append("Partial coverage (mean ranks over fewer "
                         "configurations than the fullest method; read the "
                         "paired comparison, not the rank): %s."
                         % ", ".join("%s %.0f%%" % (m, 100 * c)
                                     for m, c in worst.items()))
            lines.append("")

    lines.append("## Paired comparisons vs each reference")
    lines.append("")
    for scope_type in [s for s, _ in scopes]:
        part = comp_df[comp_df["scope_type"] == scope_type]
        if part.empty:
            continue
        lines.append("### scope_type = %s" % scope_type)
        lines.append("")
        lines.append("| scope | reference | method | n | clusters | mean diff | "
                     "95% CI | margin | Wilcoxon p | Holm p | verdict |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
        for _, r in part.sort_values(
                ["scope", "reference", "mean_diff"]).iterrows():
            lines.append("| %s | %s | %s | %d | %d | %+.3f | [%s, %s] | %s | %s "
                         "| %s | %s |"
                         % (r["scope"], r["reference"], r["method"],
                            int(r["n_configs"]), int(r["n_clusters"]),
                            float(r["mean_diff"]), _fmt(r["ci_lo"]),
                            _fmt(r["ci_hi"]), _fmt(r["margin"]),
                            _fmt_p(r["wilcoxon_p"]), _fmt_p(r["holm_p"]),
                            r["verdict"]))
        lines.append("")

    md_path = out_dir / "summary.md"
    md_path.write_text("\n".join(lines) + "\n")

    meta = {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "input_csv": str(csv_path), "rows": n_rows, "infeasible_rows": n_infeas,
        "value_col": value_col, "methods": methods, "references": references,
        "scope_cols": scope_cols, "policy_tag": args.policy_tag,
        "n_boot": args.n_boot, "seed": args.seed, "alpha": args.alpha,
        "margin_abs": args.margin_abs, "margin_rel": args.margin_rel,
        "n_configs": int(df[args.id_col].nunique()),
        "n_clusters": int(df["cluster"].nunique()),
        "cluster_check": cluster_check,
        "has_u_realized": bool(has_u),
    }
    meta_path = out_dir / "meta.json"
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")

    print("Wrote %s (%d comparison rows)" % (comp_path, len(comp_df)))
    print("Wrote %s (%d rows)" % (eq_path, len(eq_df)))
    print("Wrote %s (%d rows)" % (mean_path, len(mean_df)))
    print("Wrote %s" % md_path)
    print("Wrote %s" % meta_path)
    if cluster_check is not None:
        print("Cluster cross-check vs base_id: %d/%d rows agree"
              % (cluster_check["agree"], cluster_check["rows"]))


if __name__ == "__main__":
    main()
