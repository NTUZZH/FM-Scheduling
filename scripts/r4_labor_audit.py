#!/usr/bin/env python
"""R4.7 -- labor-line audit of the raw FMUCD file (multi-line work orders).

Protocol R4.7 requires the manuscript to report a MEASURED audit of the labor
lines that rule R7 aggregates: how many lines a work order carries, whether the
lines of one order agree on the descriptive fields, what the timestamps say
about multiple technicians vs multiple visits, and how the per-order processing
time changes under the three candidate aggregations (sum = v1 default, max =
dominant line, first line in file order).

Scope of the filters: R2 (drop rows with no WOID / no UniversityID / no
WOStartDate) and R3 (drop zero- or negative-LaborHours rows) are applied exactly
as `fmwos.io.clean` applies them, on the RAW rows. R7 is NOT applied -- the labor
lines are the object of the audit -- and the R4 cap is NOT applied either,
because R4 caps at the p99.5 of the AGGREGATED hours, so each candidate
aggregation has its own cap; the p99.5 reported per model in section 3 IS that
model's cap value.

`DescriptiveCode` is not in `fmwos.io.USECOLS`, so this script does its own typed
read of USECOLS + DescriptiveCode with `fmwos.io.DTYPES` (extended) and the same
date parsing as `fmwos.io.load_raw`. `fmwos.io` itself is untouched.

Conventions (fixed here so the numbers are reproducible)
-------------------------------------------------------
  * A work order is a (UniversityID, WOID) pair; a "line" is one raw row of it.
  * String code fields are compared after `.str.strip().str.upper()` (the
    normalisation `clean()` uses for the trade code), so pure case/whitespace
    differences do not count as disagreement.
  * Two shares are reported for every field: `missing_as_value` counts a missing
    value as a value of its own (a line with no SubsystemCode disagrees with a
    line that has one), and `nonmissing_only` counts distinct present values.
  * The implied rate is LaborCost / LaborHours (LaborHours > 0 after R3; rows
    with no LaborCost give no rate), rounded to 2 decimals before comparison;
    LaborHours is rounded to 6 decimals. Rounding removes float noise only.
  * Start-date spread is max(WOStartDate) - min(WOStartDate) of the order's
    lines, in days; the business-day spread is `np.busday_count` between the two
    calendar dates (same day = 0, next business day = 1).

Outputs (results/r4_revision/)
------------------------------
  labor_audit.json  every number, machine-readable, deterministic key order
  labor_audit.md    the same numbers as tables, for the manuscript

Both files carry two scope blocks: `all_campuses` (the whole cleaned file) and
`six_campuses` (the schedulable benchmark population {1,2,5,9,10,12}); the
manuscript cites both.

Run (about 3 minutes, ~10 GB peak RSS; loads the 1.4 GB CSV):
  PYTHONPATH=src python scripts/r4_labor_audit.py
Debug on a prefix of the file:
  PYTHONPATH=src python scripts/r4_labor_audit.py --nrows 200000 --no-sha
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fmwos import io  # noqa: E402

RAW = ROOT / "data" / "raw" / "FMUCD.csv"
OUT = ROOT / "results" / "r4_revision"

SCHEDULABLE = [1, 2, 5, 9, 10, 12]

# Extra column the audit needs and io.USECOLS does not carry.
EXTRA_COLS = ["DescriptiveCode"]
EXTRA_DTYPES = {"DescriptiveCode": "string"}

# Fields whose within-order agreement is audited. Value = comparison mode:
#   "code"    string field, stripped/upper-cased before comparison
#   "stamp"   datetime field
#   "number"  numeric field, rounded before comparison
AUDIT_FIELDS: dict[str, str] = {
    "WOStartDate": "stamp",
    "WOEndDate": "stamp",
    "SystemCode": "code",
    "SubsystemCode": "code",
    "DescriptiveCode": "code",
    "BuildingID": "code",
    "WOPriority": "code",
    "PPM/UPM": "code",
    "LaborHours": "number",
    "implied_rate": "number",
}

# Line-count histogram: exact bins 1..9 then a 10+ tail.
MAX_EXACT_LINES = 9

HOURS_QUANTILES = [("p50", 0.50), ("p90", 0.90), ("p95", 0.95),
                   ("p99", 0.99), ("p99.5", 0.995)]


def _load_raw_plus(path: Path, nrows: int | None = None) -> pd.DataFrame:
    """R1 typed load of io.USECOLS + EXTRA_COLS (mirrors io.load_raw)."""
    df = pd.read_csv(
        path,
        usecols=io.USECOLS + EXTRA_COLS,
        dtype={**io.DTYPES, **EXTRA_DTYPES},
        nrows=nrows,
    )
    for c in io.DATE_COLS:
        df[c] = pd.to_datetime(df[c], format="%Y-%m-%d %H:%M:%S", errors="coerce")
    return df


def _apply_r2_r3(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """R2 + R3 exactly as fmwos.io.clean applies them (R7/R4 deliberately not)."""
    audit: dict[str, int] = {"rows_in": int(len(df))}
    m2 = df["WOID"].notna() & df["UniversityID"].notna() & df["WOStartDate"].notna()
    audit["R2_dropped_missing_key"] = int((~m2).sum())
    df = df[m2]
    m3 = df["LaborHours"].notna() & (df["LaborHours"] > 0)
    audit["R3_dropped_zero_hours"] = int((~m3).sum())
    df = df[m3].copy()
    audit["rows_after_R2_R3"] = int(len(df))
    return df, audit


def _group_ids(df: pd.DataFrame) -> tuple[np.ndarray, int]:
    """Dense work-order ids for (UniversityID, WOID), in file order of first line."""
    wo_code, _ = pd.factorize(df["WOID"], use_na_sentinel=False)
    uni = df["UniversityID"].to_numpy(dtype="int64")
    combined = uni * (int(wo_code.max()) + 1) + wo_code.astype("int64")
    gid, uniq = pd.factorize(combined, use_na_sentinel=False)
    return gid.astype("int64"), int(len(uniq))


def _per_group_min_max(gid: np.ndarray, values: pd.Series, n_groups: int
                       ) -> tuple[np.ndarray, np.ndarray]:
    """(min, max) per group, aligned to group id 0..n_groups-1. NaN is skipped."""
    g = values.groupby(gid, sort=True, observed=True)
    mn = g.min().reindex(range(n_groups)).to_numpy()
    mx = g.max().reindex(range(n_groups)).to_numpy()
    return mn, mx


def _codes(series: pd.Series, mode: str) -> tuple[pd.Series, pd.Series]:
    """Comparable codes for one field: (missing-as-value, missing-as-NaN).

    Distinct-value counting reduces to a min/max comparison on these codes, which
    is what the shares below need and is far cheaper than a per-group nunique.
    """
    if mode == "code":
        s = series.astype("string").str.strip().str.upper()
    elif mode == "stamp":
        s = series
    else:
        s = series
    with_na, _ = pd.factorize(s, use_na_sentinel=False)
    non_na, _ = pd.factorize(s, use_na_sentinel=True)
    a = pd.Series(with_na.astype("float64"))
    b = pd.Series(np.where(non_na < 0, np.nan, non_na).astype("float64"))
    return a, b


def _share_multi_valued(gid: np.ndarray, series: pd.Series, mode: str,
                        n_groups: int, sel: np.ndarray) -> dict:
    """Share of the selected work orders whose lines hold >1 distinct value."""
    a, b = _codes(series, mode)
    out = {}
    for key, coded in (("missing_as_value", a), ("nonmissing_only", b)):
        mn, mx = _per_group_min_max(gid, coded, n_groups)
        differs = np.zeros(n_groups, dtype=bool)
        both = ~np.isnan(mn) & ~np.isnan(mx)
        differs[both] = mn[both] != mx[both]
        out[key] = float(np.round(differs[sel].mean(), 6)) if sel.sum() else 0.0
    return out


def _hours_stats(x: np.ndarray) -> dict:
    x = np.asarray(x, dtype=float)
    stats = {"n": int(x.size), "mean": float(np.round(x.mean(), 4))}
    for name, q in HOURS_QUANTILES:
        stats[name] = float(np.round(np.quantile(x, q), 4))
    return stats


def _spread_stats(days: np.ndarray) -> dict:
    if days.size == 0:
        return {"n": 0, "median": 0.0, "p90": 0.0, "p99": 0.0,
                "mean": 0.0, "max": 0.0}
    return {
        "n": int(days.size),
        "median": float(np.round(np.quantile(days, 0.50), 3)),
        "p90": float(np.round(np.quantile(days, 0.90), 3)),
        "p99": float(np.round(np.quantile(days, 0.99), 3)),
        "mean": float(np.round(days.mean(), 3)),
        "max": float(np.round(days.max(), 3)),
    }


def audit_scope(df: pd.DataFrame) -> dict:
    """Every R4.7 number for one scope (all campuses, or the six schedulable)."""
    gid, n_groups = _group_ids(df)
    n_rows = int(len(df))
    lines = np.bincount(gid, minlength=n_groups).astype("int64")
    multi = lines >= 2

    res: dict = {
        "rows": n_rows,
        "work_orders": n_groups,
        "rows_in_multi_line_wos": int(lines[multi].sum()),
        "share_rows_in_multi_line_wos": float(
            np.round(lines[multi].sum() / n_rows, 6)),
        "multi_line_work_orders": int(multi.sum()),
        "share_multi_line_work_orders": float(np.round(multi.mean(), 6)),
        "mean_lines_per_work_order": float(np.round(n_rows / n_groups, 4)),
        "max_lines_per_work_order": int(lines.max()),
    }

    # --- 1. line-count distribution (1..9 exact, 10+ tail) ------------------
    dist = []
    for k in range(1, MAX_EXACT_LINES + 1):
        sel = lines == k
        dist.append({
            "lines": str(k),
            "work_orders": int(sel.sum()),
            "rows": int(lines[sel].sum()),
            "share_work_orders": float(np.round(sel.mean(), 6)),
            "share_rows": float(np.round(lines[sel].sum() / n_rows, 6)),
        })
    sel = lines >= MAX_EXACT_LINES + 1
    dist.append({
        "lines": f"{MAX_EXACT_LINES + 1}+",
        "work_orders": int(sel.sum()),
        "rows": int(lines[sel].sum()),
        "share_work_orders": float(np.round(sel.mean(), 6)),
        "share_rows": float(np.round(lines[sel].sum() / n_rows, 6)),
    })
    res["line_count_distribution"] = dist

    # --- 2. within-order field agreement (multi-line orders only) -----------
    work = df
    rate = (work["LaborCost"] / work["LaborHours"].where(work["LaborHours"] > 0))
    work = work.assign(implied_rate=rate.round(2))
    work["LaborHours"] = work["LaborHours"].round(6)

    agree = {}
    for field, mode in AUDIT_FIELDS.items():
        agree[field] = _share_multi_valued(gid, work[field], mode, n_groups, multi)
    res["multi_line_field_disagreement"] = agree
    res["multi_line_missing_shares"] = {
        "any_missing_WOEndDate": float(np.round(
            _per_group_min_max(
                gid, work["WOEndDate"].isna().astype("float64"), n_groups
            )[1][multi].mean(), 6)) if multi.sum() else 0.0,
        "any_missing_LaborCost": float(np.round(
            _per_group_min_max(
                gid, work["LaborCost"].isna().astype("float64"), n_groups
            )[1][multi].mean(), 6)) if multi.sum() else 0.0,
    }

    # --- start-date spread on the multi-start orders ------------------------
    s_mn, s_mx = _per_group_min_max(gid, work["WOStartDate"], n_groups)
    s_mn = pd.to_datetime(pd.Series(s_mn))
    s_mx = pd.to_datetime(pd.Series(s_mx))
    spread_days = ((s_mx - s_mn).dt.total_seconds() / 86400.0).to_numpy()
    multi_start = multi & (spread_days > 0)
    res["multi_start_work_orders"] = int(multi_start.sum())
    res["share_multi_line_with_multi_start"] = float(
        np.round(multi_start.sum() / multi.sum(), 6)) if multi.sum() else 0.0
    res["start_spread_days"] = _spread_stats(spread_days[multi_start])

    # --- 4. multi-technician vs multi-visit signature -----------------------
    def _single_valued(field: str, mode: str) -> np.ndarray:
        a, _ = _codes(work[field], mode)
        mn, mx = _per_group_min_max(gid, a, n_groups)
        same = np.zeros(n_groups, dtype=bool)
        both = ~np.isnan(mn) & ~np.isnan(mx)
        same[both] = mn[both] == mx[both]
        return same

    single_start = _single_valued("WOStartDate", "stamp")
    single_end = _single_valued("WOEndDate", "stamp")
    # A missing end date is one value of its own, so on orders whose lines have
    # no end date at all "single end" is vacuous; the last two rows repeat the
    # signature on the orders where every line carries an end date.
    ends_present = _per_group_min_max(
        gid, work["WOEndDate"].notna().astype("float64"), n_groups)[0] > 0
    both_ok = multi & ends_present
    d_mn = s_mn.dt.normalize().to_numpy().astype("datetime64[D]")
    d_mx = s_mx.dt.normalize().to_numpy().astype("datetime64[D]")
    busday = np.busday_count(d_mn, d_mx)
    res["signature"] = {
        "single_start_and_single_end": float(np.round(
            (single_start & single_end)[multi].mean(), 6)) if multi.sum() else 0.0,
        "single_start_timestamp": float(np.round(
            single_start[multi].mean(), 6)) if multi.sum() else 0.0,
        "single_end_timestamp": float(np.round(
            single_end[multi].mean(), 6)) if multi.sum() else 0.0,
        "start_spread_gt_1_business_day": float(np.round(
            (busday > 1)[multi].mean(), 6)) if multi.sum() else 0.0,
        "start_spread_ge_1_business_day": float(np.round(
            (busday >= 1)[multi].mean(), 6)) if multi.sum() else 0.0,
        "multi_line_with_every_line_ended": int(both_ok.sum()),
        "single_start_and_single_end_given_all_ends_present": float(np.round(
            (single_start & single_end)[both_ok].mean(), 6))
        if both_ok.sum() else 0.0,
    }

    # --- 3. per-work-order hours under the three aggregations ---------------
    hg = work["LaborHours"].groupby(gid, sort=True, observed=True)
    models = {
        "sum": hg.sum().reindex(range(n_groups)).to_numpy(dtype=float),
        "max": hg.max().reindex(range(n_groups)).to_numpy(dtype=float),
        "first_line": hg.first().reindex(range(n_groups)).to_numpy(dtype=float),
    }
    res["hours_models"] = {k: _hours_stats(v) for k, v in models.items()}
    res["hours_models_multi_line_only"] = {
        k: _hours_stats(v[multi]) for k, v in models.items()
    } if multi.sum() else {}
    res["single_line_only_subset"] = {
        "work_orders": int((~multi).sum()),
        "share_work_orders": float(np.round((~multi).mean(), 6)),
        "hours": _hours_stats(models["sum"][~multi]),
    }
    return res


# --------------------------------------------------------------------------
# Markdown report
# --------------------------------------------------------------------------

SCOPE_TITLE = {
    "all_campuses": "All cleaned campuses",
    "six_campuses": "Six schedulable campuses {1, 2, 5, 9, 10, 12}",
}


def _fmt(x: float, nd: int = 4) -> str:
    return f"{x:.{nd}f}"


def _scope_md(name: str, r: dict) -> list[str]:
    L = [f"## {SCOPE_TITLE[name]}", ""]
    L.append(f"Rows after R2+R3: **{r['rows']:,}**. Distinct work orders: "
             f"**{r['work_orders']:,}** ({_fmt(r['mean_lines_per_work_order'], 3)} "
             f"lines per order on average, at most {r['max_lines_per_work_order']}). "
             f"Multi-line work orders: **{r['multi_line_work_orders']:,}** "
             f"({_fmt(100 * r['share_multi_line_work_orders'], 2)}% of orders), "
             f"holding **{_fmt(100 * r['share_rows_in_multi_line_wos'], 2)}%** "
             f"of the rows.")
    L += ["", "### 1. Work orders by line count", "",
          "| lines | work orders | rows | share of orders | share of rows |",
          "|---|---|---|---|---|"]
    for d in r["line_count_distribution"]:
        L.append(f"| {d['lines']} | {d['work_orders']:,} | {d['rows']:,} | "
                 f"{_fmt(100 * d['share_work_orders'], 3)}% | "
                 f"{_fmt(100 * d['share_rows'], 3)}% |")

    L += ["", "### 2. Field agreement within multi-line work orders", "",
          "Share of the multi-line orders whose lines carry more than one "
          "distinct value. `missing as value` treats a missing entry as a value "
          "of its own; `present values only` ignores missing entries.", "",
          "| field | >1 distinct (missing as value) | >1 distinct (present values only) |",
          "|---|---|---|"]
    for field in AUDIT_FIELDS:
        a = r["multi_line_field_disagreement"][field]
        L.append(f"| {field} | {_fmt(100 * a['missing_as_value'], 3)}% | "
                 f"{_fmt(100 * a['nonmissing_only'], 3)}% |")
    ms = r["multi_line_missing_shares"]
    L.append("")
    L.append(f"Multi-line orders with at least one line missing WOEndDate: "
             f"{_fmt(100 * ms['any_missing_WOEndDate'], 3)}%; missing LaborCost: "
             f"{_fmt(100 * ms['any_missing_LaborCost'], 3)}%.")
    sp = r["start_spread_days"]
    L += ["", f"Multi-line orders with more than one distinct start date: "
              f"**{r['multi_start_work_orders']:,}** "
              f"({_fmt(100 * r['share_multi_line_with_multi_start'], 3)}% of "
              f"multi-line orders). Their start-date spread, in days:", "",
          "| n | median | p90 | p99 | mean | max |", "|---|---|---|---|---|---|",
          f"| {sp['n']:,} | {_fmt(sp['median'], 3)} | {_fmt(sp['p90'], 3)} | "
          f"{_fmt(sp['p99'], 3)} | {_fmt(sp['mean'], 3)} | {_fmt(sp['max'], 3)} |"]

    L += ["", "### 3. Per-work-order LaborHours under three aggregations", "",
          "All orders, uncapped (R4 caps at the p99.5 of the aggregated hours, "
          "so the p99.5 column is each model's own cap value).", "",
          "| model | n | mean | p50 | p90 | p95 | p99 | p99.5 |",
          "|---|---|---|---|---|---|---|---|"]
    for k in ("sum", "max", "first_line"):
        h = r["hours_models"][k]
        L.append(f"| {k} | {h['n']:,} | {_fmt(h['mean'])} | {_fmt(h['p50'])} | "
                 f"{_fmt(h['p90'])} | {_fmt(h['p95'])} | {_fmt(h['p99'])} | "
                 f"{_fmt(h['p99.5'])} |")
    if r["hours_models_multi_line_only"]:
        L += ["", "Restricted to the multi-line orders (where the models differ).", "",
              "| model | n | mean | p50 | p90 | p95 | p99 | p99.5 |",
              "|---|---|---|---|---|---|---|---|"]
        for k in ("sum", "max", "first_line"):
            h = r["hours_models_multi_line_only"][k]
            L.append(f"| {k} | {h['n']:,} | {_fmt(h['mean'])} | {_fmt(h['p50'])} | "
                     f"{_fmt(h['p90'])} | {_fmt(h['p95'])} | {_fmt(h['p99'])} | "
                     f"{_fmt(h['p99.5'])} |")
    s1 = r["single_line_only_subset"]
    L += ["", f"Single-line-only subset: {s1['work_orders']:,} orders "
              f"({_fmt(100 * s1['share_work_orders'], 2)}% of all orders), mean "
              f"{_fmt(s1['hours']['mean'])} h, p50 {_fmt(s1['hours']['p50'])} h, "
              f"p99.5 {_fmt(s1['hours']['p99.5'])} h."]

    sg = r["signature"]
    L += ["", "### 4. Multi-technician vs multi-visit signature", "",
          "Shares of the multi-line work orders.", "",
          "| signature | share |", "|---|---|",
          f"| single start timestamp AND single end timestamp | "
          f"{_fmt(100 * sg['single_start_and_single_end'], 3)}% |",
          f"| single start timestamp | {_fmt(100 * sg['single_start_timestamp'], 3)}% |",
          f"| single end timestamp | {_fmt(100 * sg['single_end_timestamp'], 3)}% |",
          f"| start spread >= 1 business day | "
          f"{_fmt(100 * sg['start_spread_ge_1_business_day'], 3)}% |",
          f"| start spread > 1 business day (multi-visit candidates) | "
          f"{_fmt(100 * sg['start_spread_gt_1_business_day'], 3)}% |", "",
          f"These two readings bound the multi-visit interpretation: "
          f"{_fmt(100 * sg['single_start_and_single_end'], 2)}% of the multi-line "
          f"orders carry one start timestamp and one end timestamp across all "
          f"their lines, and at most "
          f"{_fmt(100 * sg['start_spread_gt_1_business_day'], 2)}% have lines "
          f"starting more than one business day apart.", "",
          f"A missing end date counts as one value, so the two end-timestamp rows "
          f"above are vacuous on orders whose lines carry no end date. On the "
          f"{sg['multi_line_with_every_line_ended']:,} multi-line orders whose "
          f"every line has an end date, the share with a single start timestamp "
          f"and a single end timestamp is "
          f"{_fmt(100 * sg['single_start_and_single_end_given_all_ends_present'], 3)}%.",
          ""]
    return L


def build_md(payload: dict) -> str:
    L = ["# R4.7 labor-line audit (raw FMUCD)", ""]
    f = payload["filters"]
    L.append(f"Source: `{payload['raw_path']}` "
             f"({payload['rows_raw']:,} data rows"
             + (f", sha256 `{payload['raw_sha256']}`" if payload["raw_sha256"]
                else "") + "). "
             f"Filters R2 and R3 applied as in `fmwos.io.clean` "
             f"(R2 dropped {f['R2_dropped_missing_key']:,} rows with no key or no "
             f"start date, R3 dropped {f['R3_dropped_zero_hours']:,} rows with "
             f"non-positive LaborHours); R7 aggregation and the R4 cap are NOT "
             f"applied, because the labor lines are what this audit measures.")
    L += ["", "A work order is a (UniversityID, WOID) pair and a line is one raw "
              "row of it. String code fields are compared after stripping "
              "whitespace and upper-casing; LaborHours is rounded to 6 decimals "
              "and the implied rate (LaborCost / LaborHours) to 2 decimals before "
              "distinct values are counted. Generated by "
              "`scripts/r4_labor_audit.py`.", ""]
    cc = payload.get("crosscheck_vs_p0_profile")
    if cc:
        L += [f"Provenance cross-check against the locked pipeline "
              f"(`results/p0_profile/overview.json`): the work-order count "
              f"({cc['work_orders']:,}) and the R4 cap "
              f"({_fmt(cc['sum_model_p99_5'])} h, the p99.5 of the summed hours) "
              f"both reproduce "
              f"({'PASSED' if cc['passed'] else 'FAILED'}).", ""]
    for scope in ("all_campuses", "six_campuses"):
        L += _scope_md(scope, payload["scopes"][scope])
    return "\n".join(L).rstrip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw", type=Path, default=RAW)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--nrows", type=int, default=None,
                    help="debug: read only the first N data rows")
    ap.add_argument("--no-sha", action="store_true",
                    help="skip the sha256 of the raw file")
    args = ap.parse_args()

    t0 = time.time()
    print(f"[r4_labor_audit] loading {args.raw} ...", flush=True)
    df = _load_raw_plus(args.raw, nrows=args.nrows)
    rows_raw = int(len(df))
    print(f"[r4_labor_audit] raw rows = {rows_raw:,}  "
          f"({time.time() - t0:.0f}s)", flush=True)

    sha = ""
    if not args.no_sha:
        sha = io.sha256_of(args.raw)
        print(f"[r4_labor_audit] sha256 = {sha}  "
              f"(matches io.RAW_SHA256: {sha == io.RAW_SHA256})", flush=True)

    dfc, filters = _apply_r2_r3(df)
    del df
    print(f"[r4_labor_audit] rows after R2+R3 = {filters['rows_after_R2_R3']:,}",
          flush=True)

    payload: dict = {
        "generated_by": "scripts/r4_labor_audit.py",
        "protocol": "R4.7",
        "raw_path": str(args.raw.relative_to(ROOT)) if args.raw.is_relative_to(ROOT)
        else str(args.raw),
        "raw_sha256": sha,
        "raw_sha256_matches_io": bool(sha == io.RAW_SHA256) if sha else None,
        "rows_raw": rows_raw,
        "nrows_limit": args.nrows,
        "filters": filters,
        "schedulable_campuses": SCHEDULABLE,
        "scopes": {},
    }

    print("[r4_labor_audit] scope: all campuses ...", flush=True)
    payload["scopes"]["all_campuses"] = audit_scope(dfc)

    # Provenance cross-check against the locked pipeline: the R7 work-order count
    # and the R4 cap (= the p99.5 of the summed hours) must reproduce exactly.
    ref = ROOT / "results" / "p0_profile" / "overview.json"
    if args.nrows is None and ref.exists():
        with open(ref) as f:
            locked = json.load(f)["cleaning_audit"]
        got_wos = payload["scopes"]["all_campuses"]["work_orders"]
        got_cap = payload["scopes"]["all_campuses"]["hours_models"]["sum"]["p99.5"]
        ref_wos = int(locked["R7_work_orders_after_dedup"])
        ref_cap = float(locked["R4_labor_cap_hours"])
        bad = []
        if got_wos != ref_wos:
            bad.append(("work_orders", got_wos, ref_wos))
        if abs(got_cap - ref_cap) > 1e-3:
            bad.append(("R4_cap", got_cap, ref_cap))
        payload["crosscheck_vs_p0_profile"] = {
            "work_orders": got_wos,
            "locked_R7_work_orders_after_dedup": ref_wos,
            "sum_model_p99_5": got_cap,
            "locked_R4_labor_cap_hours": ref_cap,
            "passed": not bad,
        }
        if bad:
            print(f"[r4_labor_audit] STOP: cross-check vs {ref} failed: {bad}",
                  flush=True)
            return 2
        print("[r4_labor_audit] cross-check PASSED (work-order count and R4 cap "
              "reproduce the locked pipeline).", flush=True)

    six = dfc[dfc["UniversityID"].isin(SCHEDULABLE)].copy()
    print(f"[r4_labor_audit] scope: six campuses ({len(six):,} rows) ...",
          flush=True)
    payload["scopes"]["six_campuses"] = audit_scope(six)

    args.out.mkdir(parents=True, exist_ok=True)
    with open(args.out / "labor_audit.json", "w") as f:
        json.dump(payload, f, indent=2, sort_keys=False)
    with open(args.out / "labor_audit.md", "w") as f:
        f.write(build_md(payload))
    print(f"[r4_labor_audit] wrote {args.out / 'labor_audit.json'} and "
          f"{args.out / 'labor_audit.md'}  ({time.time() - t0:.0f}s)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
