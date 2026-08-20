#!/usr/bin/env python
"""Trade-derivation shares of the cleaned corpus (revision items A8 and A9).

Two definitional choices in the trade derivation are stated in Section 4 but
were never quantified: work orders that carry no system code become the trade
``UNK``, and every trade with fewer than ``calib.MISC_MIN_ROWS`` orders on a
campus is merged into that campus's ``MISC`` crew.  The manuscript must report
how much of the corpus each choice touches, so this script measures both on the
six benchmark campuses and writes them to
``results/p0_profile/trade_shares.json``.

The corpus is rebuilt exactly as the instance builder rebuilds it (``io.clean``
with the v1.1 stable dominant-line sort, then ``calib.trade_merge_map`` /
``calib.apply_trade_merge`` on the full cleaned frame, as
``scripts/r4_corpus_diff.py`` and ``scripts/r4_capacity.py`` do), so the shares
describe the corpus the benchmark instances were drawn from and not a
re-derivation of it.  The retained work-order count is cross-checked against
``results/r4_revision/labor_audit.json`` (six-campus scope) and against
``results/p0_profile/overview.json`` (all-campus scope); a mismatch is a hard
error rather than a warning.

Deterministic and idempotent: the only inputs are the raw CSV and the pinned
cleaning code, and re-running rewrites the same JSON.

  PYTHONPATH=src python scripts/r4_trade_shares.py
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from fmwos import calib, io                                # noqa: E402

RAW = ROOT / "data" / "raw" / "FMUCD.csv"
OUT = ROOT / "results" / "p0_profile" / "trade_shares.json"
AUDIT = ROOT / "results" / "r4_revision" / "labor_audit.json"
OVERVIEW = ROOT / "results" / "p0_profile" / "overview.json"

UNK = "UNK"          # io.py R6: no SystemCode -> trade "UNK"
MISC = "MISC"        # calib.py: trades below MISC_MIN_ROWS per campus


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", default=str(RAW))
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    t0 = time.time()
    clean, audit = io.clean(io.load_raw(Path(args.raw)), dominant_sort="stable")
    tmap = calib.trade_merge_map(clean)
    trade_m = calib.apply_trade_merge(clean, tmap)
    print("cleaned %d work orders in %.1f s" % (len(clean), time.time() - t0),
          flush=True)

    df = pd.DataFrame({
        "campus": clean["UniversityID"].astype("int64").to_numpy(),
        "trade": clean["trade"].astype(str).to_numpy(),
        "trade_m": trade_m.astype(str).to_numpy(),
    })
    six = df[df["campus"].isin(calib.CAMPUSES)]

    n_six = int(len(six))
    n_unk = int((six["trade"] == UNK).sum())
    n_misc = int((six["trade_m"] == MISC).sum())
    # UNK is itself a trade, so on a campus where it is rare it is merged into
    # MISC; the two shares therefore overlap and the overlap is reported.
    n_unk_merged = int(((six["trade"] == UNK) & (six["trade_m"] == MISC)).sum())

    per_campus = []
    for c, sub in six.groupby("campus", sort=True):
        per_campus.append({
            "campus": int(c),
            "work_orders": int(len(sub)),
            "unk_orders": int((sub["trade"] == UNK).sum()),
            "misc_orders": int((sub["trade_m"] == MISC).sum()),
            "unk_merged_into_misc":
                int(((sub["trade"] == UNK) & (sub["trade_m"] == MISC)).sum()),
            "trades_before_merge": int(sub["trade"].nunique()),
            "trades_after_merge": int(sub["trade_m"].nunique()),
        })

    # Cross-checks against the two stored corpus artifacts.
    checks = []

    def require(name, got, want):
        checks.append({"check": name, "got": got, "want": want,
                       "ok": bool(got == want)})
        if got != want:
            raise SystemExit("cross-check failed: %s (got %r, want %r)"
                             % (name, got, want))

    require("all-campus work orders vs p0_profile/overview.json",
            int(len(clean)),
            int(json.loads(OVERVIEW.read_text())["cleaning_audit"]["rows_out"]))
    require("six-campus work orders vs r4_revision/labor_audit.json",
            n_six,
            int(json.loads(AUDIT.read_text())["scopes"]["six_campuses"]
                ["work_orders"]))

    out = {
        "generated_by": "scripts/r4_trade_shares.py",
        "generated": datetime.now().isoformat(timespec="seconds"),
        "raw_path": str(args.raw),
        "dominant_sort": "stable",
        "campuses": list(calib.CAMPUSES),
        "misc_min_rows": int(calib.MISC_MIN_ROWS),
        "cleaning_audit": audit,
        "six_campuses": {
            "work_orders": n_six,
            "unk_orders": n_unk,
            "unk_share": n_unk / n_six,
            "misc_orders": n_misc,
            "misc_share": n_misc / n_six,
            "unk_orders_merged_into_misc": n_unk_merged,
            "unk_or_misc_orders": int(n_unk + n_misc - n_unk_merged),
            "trades_before_merge": int(six["trade"].nunique()),
            "trade_campus_pools_after_merge":
                int(six.groupby(["campus", "trade_m"]).ngroups),
        },
        "per_campus": per_campus,
        "cross_checks": checks,
    }
    Path(args.out).write_text(json.dumps(out, indent=2) + "\n")
    print("six campuses: %d work orders; UNK %d (%.3f%%); MISC %d (%.3f%%)"
          % (n_six, n_unk, 100.0 * n_unk / n_six, n_misc,
             100.0 * n_misc / n_six))
    print("written to %s (%.1f s)" % (args.out, time.time() - t0))


if __name__ == "__main__":
    main()
