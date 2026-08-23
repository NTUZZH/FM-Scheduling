"""FMUCD loading and cleaning.

Source: Facility Management Unified Classification Database (FMUCD),
Mendeley Data DOI 10.17632/cb8d2nsjss.1 (CC BY 4.0). ~3.7M work orders,
12 North-American universities, 2002-2021, 38 fields.

Cleaning rules (paper appendix table; every rule is deterministic and lives
here so the whole pipeline is reproducible from the raw CSV):
  R1 typed parsing of dates (WOStartDate/WOEndDate) and numerics; unparseable
     values -> NA, never guessed.
  R2 drop rows with no WOID, no UniversityID, or no WOStartDate (cannot be
     placed on a timeline).
  R3 drop zero/negative-LaborHours orders (administrative or bookkeeping
     entries; they consume no technician capacity).
  R4 cap LaborHours at the global p99.5 AFTER R7 aggregation (data-entry
     outliers; the cap value is recorded and sensitivity-checked in E5).
  R7 aggregate duplicate (UniversityID, WOID) rows into one work order:
     31% of cleaned rows belong to work orders recorded across multiple labor lines (same
     start/end, hours split across lines). LaborHours = sum, WOStartDate = min,
     WOEndDate = max, all other fields from the dominant row (max LaborHours;
     ties broken by the ``dominant_sort`` argument of ``clean``).
  R5 priority mapped onto 4 classes P1..P4 by the dataset's own empirical
     distribution (see calib.py); raw value preserved in `priority_raw`.
  R6 trade = top-level UNIFORMAT system code (SystemCode letter+first digits,
     e.g. D20 Plumbing -> trade "D20"); orders with no SystemCode -> trade "UNK".
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

RAW_SHA256 = "4464648252c4bdca2a6deba9d467e94aec7568d675f51e06d6d343b3c09f006a"

# Columns actually used downstream (keep memory bounded).
USECOLS = [
    "UniversityID",
    "Country",
    "State/Province",
    "BuildingID",
    "Size",
    "Type",
    "SystemCode",
    "SystemDescription",
    "SubsystemCode",
    "WOID",
    "WOPriority",
    "WOStartDate",
    "WOEndDate",
    "WODuration",
    "PPM/UPM",
    "LaborCost",
    "TotalCost",
    "LaborHours",
]

DTYPES = {
    "UniversityID": "Int16",
    "Country": "string",
    "State/Province": "string",
    "BuildingID": "string",
    "Size": "float64",
    "Type": "string",
    "SystemCode": "string",
    "SystemDescription": "string",
    "SubsystemCode": "string",
    "WOID": "string",
    "WOPriority": "string",  # raw; semantics vary -> parsed in clean()
    "WOStartDate": "string",  # parsed to datetime in load_raw (explicit dtype
    "WOEndDate": "string",  # avoids a pandas-3 chunked mixed-inference bug)
    "WODuration": "float64",
    "PPM/UPM": "string",
    "LaborCost": "float64",
    "TotalCost": "float64",
    "LaborHours": "float64",
}

DATE_COLS = ["WOStartDate", "WOEndDate"]


def sha256_of(path: str | Path, chunk: int = 1 << 22) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def load_raw(path: str | Path, nrows: int | None = None) -> pd.DataFrame:
    """R1: typed load of the raw CSV (only columns used downstream)."""
    df = pd.read_csv(
        path,
        usecols=USECOLS,
        dtype=DTYPES,
        nrows=nrows,
    )
    for c in DATE_COLS:
        df[c] = pd.to_datetime(df[c], format="%Y-%m-%d %H:%M:%S", errors="coerce")
    return df


def clean(df: pd.DataFrame, labor_cap_q: float = 0.995,
          dominant_sort: str = "legacy") -> tuple[pd.DataFrame, dict]:
    """Apply R2-R4, R6. Returns (clean_df, audit dict with per-rule row counts).

    ``dominant_sort`` selects how R7 breaks a tie between labor lines that
    report the same LaborHours, which is the common case rather than an edge
    case: 49% of the multi-line work orders have all their line hours equal, so
    the "dominant" line is undefined on hours alone, and it is the line that
    supplies trade, priority, building and PM flag.

    - ``"legacy"`` (default, corpus v1.0): ``sort_values("LaborHours",
      ascending=False)`` with pandas' default quicksort. The winner is
      reproducible for a fixed pandas version and a fixed input order, but it
      is an arbitrary line, not a chosen one.
    - ``"stable"`` (corpus v1.1): sort the frame back into raw-file order
      (``sort_index``), then ``sort_values(["LaborHours"], ascending=False,
      kind="stable")``, so among equal-hours lines the FIRST line in file order
      wins. The rule is then stated rather than inherited from a sort
      implementation. (Tie order verified on the pinned pandas 3.0.3.)
    """
    if dominant_sort not in ("legacy", "stable"):
        raise ValueError("dominant_sort must be 'legacy' or 'stable', got "
                         f"{dominant_sort!r}")
    audit: dict[str, float | int] = {"rows_in": len(df)}

    m2 = df["WOID"].notna() & df["UniversityID"].notna() & df["WOStartDate"].notna()
    audit["R2_dropped_missing_key"] = int((~m2).sum())
    df = df[m2]

    m3 = df["LaborHours"].notna() & (df["LaborHours"] > 0)
    audit["R3_dropped_zero_hours"] = int((~m3).sum())
    df = df[m3].copy()

    # R7: one work order per (campus, WOID). Dominant row (max LaborHours)
    # supplies all fields; hours summed, start earliest, end latest.
    audit["R7_rows_before_dedup"] = len(df)
    df["_hours_sum"] = df.groupby(["UniversityID", "WOID"], observed=True)[
        "LaborHours"
    ].transform("sum")
    df["_start_min"] = df.groupby(["UniversityID", "WOID"], observed=True)[
        "WOStartDate"
    ].transform("min")
    df["_end_max"] = df.groupby(["UniversityID", "WOID"], observed=True)[
        "WOEndDate"
    ].transform("max")
    if dominant_sort == "stable":
        ordered = df.sort_index().sort_values(
            ["LaborHours"], ascending=False, kind="stable")
    else:
        ordered = df.sort_values("LaborHours", ascending=False)
    df = ordered.drop_duplicates(
        subset=["UniversityID", "WOID"], keep="first"
    )
    df["LaborHours"] = df["_hours_sum"]
    df["WOStartDate"] = df["_start_min"]
    df["WOEndDate"] = df["_end_max"]
    df = df.drop(columns=["_hours_sum", "_start_min", "_end_max"]).sort_index()
    audit["R7_work_orders_after_dedup"] = len(df)

    cap = float(df["LaborHours"].quantile(labor_cap_q))
    audit["R4_labor_cap_hours"] = cap
    audit["R4_rows_capped"] = int((df["LaborHours"] > cap).sum())
    df["LaborHours"] = df["LaborHours"].clip(upper=cap)

    # R6 trade from UNIFORMAT top-level system code.
    df["trade"] = df["SystemCode"].fillna("UNK").str.strip().str.upper()
    df.loc[df["trade"] == "", "trade"] = "UNK"

    df["is_pm"] = df["PPM/UPM"].str.upper().eq("PPM")
    audit["rows_out"] = len(df)
    audit["pm_share"] = float(df["is_pm"].mean())
    return df, audit


# --------------------------------------------------------------------------- #
# Method-name normalisation for archived result files.
#
# Revision R4.1 renames the dispatching rule "mor" to "lpt"; the rule itself is
# unchanged (longest processing time within the trade queue).  The released v1.0
# result CSVs still carry method=="mor" and are never edited, so every reader
# maps the archived name onto the current one at load time.
# --------------------------------------------------------------------------- #
NORMALIZE_METHOD = {"mor": "lpt"}


def normalize_method(name):
    """Map one archived method string onto its current name (R4.1)."""
    return NORMALIZE_METHOD.get(str(name), str(name))


def normalize_method_series(s: pd.Series) -> pd.Series:
    """Vectorised :func:`normalize_method` for a results file's method column."""
    return s.astype("object").replace(NORMALIZE_METHOD)


def normalize_method_column(df: pd.DataFrame, column: str = "method") -> pd.DataFrame:
    """Return ``df`` with its method column normalised in place (R4.1)."""
    if column in df.columns:
        df[column] = normalize_method_series(df[column])
    return df
