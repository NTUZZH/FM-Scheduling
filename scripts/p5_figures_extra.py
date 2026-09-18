#!/usr/bin/env python
"""P5 EXTRA - four added figures for the manuscript.

f7_data      FMUCD at a glance          (full text width, 4 panels)
f8_priority  raw priority is not naive  (full text width, 2 panels)
f9_training  what training discriminates (single col, 2 panels)
f10_rolling  replan on a clock          (full text width, 2 panels)

Style is inherited verbatim from scripts/p5_figures.py (Times-serif, hairline
axes); every text element is black, a legend states what a colour means, and a
direct label is reserved for a per-item identity a legend cannot carry.  Every
plotted value comes from a results/ file or from the cleaned corpus itself:
  f7 : results/p0_profile/{arrivals,per_campus,trades}.csv + labor_hist.csv
  f8 : the full-corpus priority profile recomputed here from the cleaned v1.1
       corpus (see full_corpus_priority_profile), cross-checked against the
       train-window mapping in results/p1_calib/priority_mapping.csv
  f9 : results/p3_train/v2/seed{301,302,303}/curves.csv
  f10: results/p4_dyneval/rolling_diag.json

  python scripts/p5_figures_extra.py [f7 f8 f9 f10]
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle, Patch
import matplotlib.ticker as mticker

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p5_figures import (  # noqa: E402
    set_style, save, style_ax, figsize, CMAP, PRETTY,
    INK, INK2, MUTE, GRID, AXIS, SURF, fmt_wwt, mcol, pastel,
)

ROOT = str(Path(__file__).resolve().parents[1])
sys.path.insert(0, f"{ROOT}/src")
P0 = f"{ROOT}/results/p0_profile"

# cas-sc \textwidth = 468.3324pt = 164.5 mm (paper/main.log). Every figure that
# LaTeX includes at width=\linewidth is DESIGNED at that width, so 7.2 pt in the
# script is 7.2 pt on the page.
TEXTWIDTH_MM = 164.5

SCHEDULABLE = [1, 2, 5, 9, 10, 12]
POLICY_BLUE = CMAP["policy"]     # #2a78d6
ROLL_TEAL = CMAP["roll"]         # #1baf7a

# Okabe-Ito qualitative palette (colour-blind safe) for the 6 campuses -- kept
# deliberately DISJOINT from the frozen method palette in p5_figures, with two
# fixed points: campus 1 is the recessive grey and campus 12 the teal-green in
# EVERY figure that names campuses, so a campus keeps one colour across the
# paper (the priority figure draws exactly those two). The remaining four take
# Okabe-Ito hues that stay apart from the teal.
CAMP_COL = {1: MUTE, 2: "#56B4E9", 5: "#CC79A7",
            9: "#0072B2", 10: "#D55E00", 12: ROLL_TEAL}


def _kfmt(n):
    """126000 -> '126k', 41000 -> '41k', <1000 -> '900'."""
    n = float(n)
    if n >= 1000:
        return f"{n/1000:.0f}k"
    return f"{n:.0f}"


# ============================================================================
# F8 data step: the FULL-CORPUS corrective close-time profile
# ============================================================================
# The v1.1 corpus fits the priority mapping on the training years only, so
# results/p1_calib/priority_mapping.csv carries the medians of that window --
# for campus 2 a few hundred labelled corrective orders, whose medians run to
# more than a thousand days and cannot support the descriptive claim the figure
# makes. The figure therefore plots the profile over the WHOLE corpus, which is
# the descriptive check that realised close time tracks the campus's own text
# labels; the mapping the benchmark uses is still the train-only one, and the
# two agree on every class of every campus this figure shows.
CACHE_DIR = Path(ROOT) / "results" / "p1_calib"
CACHE_CSV = CACHE_DIR / "priority_mapping_fullcorpus.csv"
MACROS_TEX = Path(ROOT) / "paper" / "macros.tex"


def _macro(name):
    """Value of \\newcommand{\\<name>}{...} in paper/macros.tex, as a float."""
    txt = MACROS_TEX.read_text(encoding="utf-8")
    m = re.search(r"\\newcommand\{\\" + name + r"\}\{([^}]*)\}", txt)
    if m is None:
        raise SystemExit(f"macro \\{name} not found in {MACROS_TEX}")
    return float(m.group(1).replace("{,}", "").replace(",", ""))


def full_corpus_priority_profile(rebuild=False):
    """Per-(campus, raw value, pm/cm) priority table fitted on the FULL corpus.

    Deterministic function of the raw CSV: ``fmwos.io.clean(dominant_sort=
    "stable")`` (corpus v1.1) followed by ``fmwos.calib.build_priority_mapping
    (fit_end=None)``, i.e. exactly what the loaders build, with the fit window
    opened to every year. Cached under data/processed/ because it reads the
    1.4 GB raw file; delete the cache or pass ``rebuild`` to recompute.
    """
    if CACHE_CSV.exists() and not rebuild:
        return pd.read_csv(CACHE_CSV)
    from fmwos import calib, io  # noqa: E402  (heavy import, only on a rebuild)
    raw_csv = Path(ROOT) / "data" / "raw" / "FMUCD.csv"
    print(f"   computing the full-corpus priority profile from {raw_csv} ...",
          flush=True)
    clean, _audit = io.clean(io.load_raw(raw_csv), dominant_sort="stable")
    prof = calib.build_priority_mapping(clean, fit_end=None)
    prof = prof[prof["campus"].isin(calib.CAMPUSES)].reset_index(drop=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    prof.to_csv(CACHE_CSV, index=False)
    print(f"   wrote {CACHE_CSV} ({len(prof)} rows)", flush=True)
    return prof


def _check_profile(prof, train):
    """Hard-abort unless the plotted profile matches the manuscript macros.

    Three invariants, all read from files rather than typed here:
      1. campus 2's three text labels reproduce \\ctwourgent, \\ctworoutine and
         \\ctwoemergency to one decimal;
      2. the two Spearman coefficients the caption prints reproduce \\conerho
         and \\ctwelverho to two decimals;
      3. the classes the train-only mapping assigns on the three campuses this
         figure shows are the classes a full-corpus fit would assign, so the
         profile is a descriptive check of the mapping actually used and not a
         different mapping.
    """
    cm = prof[prof.is_pm_split == "cm"]
    c2 = cm[cm.campus == 2].set_index("raw_value")["median_cm_duration_days"]
    for raw, macro in (("2-URGENT", "ctwourgent"),
                       ("4-ROUTINE", "ctworoutine"),
                       ("1-EMERGENCY", "ctwoemergency")):
        got, want = round(float(c2.loc[raw]), 1), _macro(macro)
        if abs(got - want) > 1e-9:
            raise SystemExit(f"f8: campus 2 {raw} median {got} d does not match "
                             f"\\{macro} = {want} d")
    for camp, macro in ((1, "conerho"), (12, "ctwelverho")):
        s = cm[(cm.campus == camp) & (cm.rule == "r5c")]
        got, want = round(float(s.spearman_rho.iloc[0]), 2), _macro(macro)
        if abs(got - want) > 1e-9:
            raise SystemExit(f"f8: campus {camp} Spearman rho {got} does not "
                             f"match \\{macro} = {want}")
    key = ["campus", "raw_value", "is_pm_split"]
    j = train.merge(prof, on=key, how="inner", suffixes=("_tr", "_full"))
    j = j[j.campus.isin([1, 2, 12])]
    bad = j[j.mapped_class_tr != j.mapped_class_full]
    if len(bad):
        raise SystemExit("f8: train-only and full-corpus fits disagree on a "
                         f"class of campus 1/2/12:\n{bad[key]}")
    print(f"   f8 asserts: campus 2 urgent/routine/emergency = "
          f"{_macro('ctwourgent')}/{_macro('ctworoutine')}/"
          f"{_macro('ctwoemergency')} d; rho c1 {_macro('conerho')}, "
          f"c12 {_macro('ctwelverho')}; {len(j)} shared mapping keys on "
          f"campuses 1, 2 and 12, all with the same class")


# ============================================================================
# F7  FMUCD at a glance (4 panels)
# ============================================================================
def fig7_data():
    ar = pd.read_csv(f"{P0}/arrivals.csv")
    pc = pd.read_csv(f"{P0}/per_campus.csv")
    tr = pd.read_csv(f"{P0}/trades.csv")
    lh = pd.read_csv(f"{P0}/labor_hist.csv")

    # Designed a shade narrower than the text width, because the panel (d)
    # labels overhang their axes: the tight crop keeps that overhang, and the
    # file must still leave at 164.5 mm so the type prints at its source size.
    fig = plt.figure(figsize=figsize(161.0, 62))
    gs = fig.add_gridspec(1, 4, width_ratios=[1.32, 1.12, 1.02, 1.14],
                          left=0.050, right=0.988, top=0.895, bottom=0.155,
                          wspace=0.40)
    axA, axB, axC, axD = (fig.add_subplot(gs[0, i]) for i in range(4))

    # ---- (a) monthly arrivals per campus (log-y, thin lines, direct labels) --
    style_ax(axA)
    ar6 = ar[ar.UniversityID.isin(SCHEDULABLE)]
    g = ar6.groupby(["UniversityID", "month"])["rows"].sum().reset_index()
    g["yr"] = g["month"].str.slice(0, 4).astype(int) + \
        (g["month"].str.slice(5, 7).astype(int) - 1) / 12.0
    lines = {}
    for c in SCHEDULABLE:
        s = g[g.UniversityID == c].sort_values("yr")
        lines[c], = axA.plot(s.yr, s.rows, "-", color=CAMP_COL[c], lw=0.9,
                             alpha=0.95, zorder=3, solid_capstyle="round")
    axA.set_yscale("log")
    axA.set_ylim(0.7, 40000)
    axA.set_xlim(2002, 2021.9)
    axA.set_xticks([2004, 2008, 2012, 2016, 2020])
    axA.set_xticklabels(["'04", "'08", "'12", "'16", "'20"], fontsize=6.2)
    axA.set_yticks([1, 10, 100, 1000, 10000])
    axA.set_yticklabels(["1", "10", "100", "1k", "10k"], fontsize=6.2)
    axA.grid(axis="y", which="major", color=GRID, linewidth=0.4)
    # Line colour is what identifies a campus, so a legend says so. It takes the
    # top-left corner, where no series reaches: nothing on record exceeds two
    # thousand orders a month before 2012, and the two campuses that later climb
    # past that do so on the right-hand half of the axis.
    axA.legend(handles=[lines[c] for c in SCHEDULABLE],
               labels=[f"c{c}" for c in SCHEDULABLE],
               loc="upper left", ncol=2, frameon=False, fontsize=6.2,
               labelcolor=INK, handlelength=1.1, handletextpad=0.4,
               columnspacing=1.0, labelspacing=0.30, borderaxespad=0.25,
               borderpad=0.0)
    axA.set_ylabel("work orders / month  (log)", fontsize=6.9)
    # The caption is the title; each panel carries only its tag.
    axA.set_title("(a)", loc="left", fontsize=8.0, color=INK, weight="bold",
                  pad=5)

    # ---- (b) labour hours per order (log-x histogram) -----------------------
    style_ax(axB)
    h = lh[lh.kind == "hist"].copy()
    edges = np.append(h.bin_lo.astype(float).to_numpy(),
                      float(h.bin_hi.astype(float).iloc[-1]))
    counts = h["count"].astype(float).to_numpy()
    axB.stairs(counts, edges, fill=True, color=POLICY_BLUE, alpha=0.55,
               edgecolor=POLICY_BLUE, linewidth=0.6, zorder=3)
    axB.set_xscale("log")
    axB.set_xlim(0.03, 200)
    q = {r.label: float(r.value) for _, r in lh[lh.kind == "quant"].iterrows()}
    med, p90, p99 = q["six_p50"], q["six_p90"], q["six_p99"]
    ymax = counts.max() * 1.16
    axB.set_ylim(0, ymax)
    # 'median' is the widest tag and its line sits closest to p90; place it to
    # the LEFT of its dashed line (clear top-left space) so it never reaches the
    # p90 line. p90 / p99 stay to the right of their lines. Each tag keeps a
    # clear gap from the rule it names, so no glyph touches a dashed stroke.
    for xv, lab, side in [(med, "median\n1.0 h", "l"), (p90, "p90\n6 h", "r"),
                          (p99, "p99\n49 h", "r")]:
        axB.axvline(xv, color=INK2, lw=0.8, ls=(0, (3, 2)), zorder=4)
        if side == "l":
            axB.text(xv * 0.78, ymax * 0.95, lab, fontsize=6.2, color=INK,
                     ha="right", va="top", linespacing=1.15)
        else:
            axB.text(xv * 1.28, ymax * 0.95, lab, fontsize=6.2, color=INK,
                     ha="left", va="top", linespacing=1.15)
    axB.set_xticks([0.1, 1, 10, 100])
    axB.set_xticklabels(["0.1", "1", "10", "100"], fontsize=6.2)
    axB.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, p: f"{v/1000:.0f}k" if v >= 1000 else "0"))
    axB.tick_params(axis="y", labelsize=6.2)
    axB.set_xlabel("labor hours  (log)", fontsize=6.9)
    axB.set_ylabel("work orders", fontsize=6.9)
    axB.set_title("(b)", loc="left", fontsize=8.0, color=INK, weight="bold",
                  pad=5)

    # ---- (c) preventive share per campus (stacked horizontal) ---------------
    style_ax(axC)
    pc6 = pc[pc.UniversityID.isin(SCHEDULABLE)].sort_values("pm_share")
    # Pastel fill for the corrective segment and a medium blue-grey for the
    # preventive one: the saturated orange was a heavy block, and at its own
    # luminance the two segments were indistinguishable in greyscale.
    cm_col, pm_col = pastel(CMAP["wspt"], 0.45), "#8aa0b6"
    ypos = np.arange(len(pc6))
    for y, (_, r) in zip(ypos, pc6.iterrows()):
        pm = float(r.pm_share)
        axC.barh(y, 1 - pm, height=0.66, left=0.0, color=cm_col,
                 edgecolor=SURF, linewidth=0.5, zorder=3)
        axC.barh(y, pm, height=0.66, left=1 - pm, color=pm_col,
                 edgecolor=SURF, linewidth=0.5, zorder=3)
        axC.text(1.02, y, _kfmt(r.rows), va="center", ha="left",
                 fontsize=6.2, color=INK)
    # a two-key inline legend above the top bar: the colour lives in the swatch,
    # the word is black (the top bar's corrective segment is too short to carry
    # a centred word without overhanging the axis)
    ytop = ypos[-1]
    for x0, col, lab in [(0.00, cm_col, "corrective"), (0.52, pm_col, "preventive")]:
        axC.add_patch(Rectangle((x0, ytop + 0.43), 0.055, 0.20, facecolor=col,
                                edgecolor="none", clip_on=False, zorder=4))
        axC.text(x0 + 0.085, ytop + 0.53, lab, ha="left", va="center",
                 fontsize=6.2, color=INK, zorder=4)
    axC.set_yticks(ypos)
    axC.set_yticklabels([f"c{int(c)}" for c in pc6.UniversityID], fontsize=6.6,
                        color=INK)
    axC.set_xlim(0, 1.16)
    axC.set_xticks([0, 0.5, 1.0])
    axC.set_xticklabels(["0", "0.5", "1"], fontsize=6.2)
    axC.set_ylim(-0.6, len(pc6) - 0.1)
    axC.set_xlabel("share of work orders", fontsize=6.9)
    axC.set_title("(c)", loc="left", fontsize=8.0, color=INK, weight="bold",
                  pad=5)

    # ---- (d) trade mix (top 8 + other) --------------------------------------
    # code as the (short) y-tick; the trade name at the bar end, so the long
    # names never reach back into panel (c). The share is not printed: the x
    # axis is linear and gridded, so the bar length already carries it.
    style_ax(axD)
    tot = float(tr.rows.sum())
    top = tr.sort_values("rows", ascending=False).head(8)
    other = tot - float(top.rows.sum())
    DESC = {"D30": "HVAC", "D50": "Electrical", "D20": "Plumbing",
            "D40": "Fire prot.", "C10": "Interior", "E10": "Equipment",
            "B20": "Exterior", "C30": "Finishes"}
    rows_ = [(r.trade, DESC.get(r.trade, str(r.description)), float(r.rows) / tot)
             for _, r in top.iterrows()]
    rows_.append(("other", "", other / tot))
    ypos = np.arange(len(rows_))[::-1]
    # the residual bar stays in the same neutral family as the named trades, a
    # lighter tint of the same hue, so its colour reads as "the rest of the same
    # thing" rather than as a second category
    for y, (code, desc, sh) in zip(ypos, rows_):
        c = "#e4e8ec" if code == "other" else "#c3cbd3"
        axD.barh(y, sh * 100, height=0.68, color=c,
                 edgecolor="#6f7780", linewidth=0.5, zorder=3)
        if desc:
            axD.text(sh * 100 + 1.1, y, desc, va="center", ha="left",
                     fontsize=6.2, color=INK)
    axD.set_yticks(ypos)
    axD.set_yticklabels([r[0] for r in rows_], fontsize=6.2, color=INK)
    axD.set_xlim(0, 58)
    axD.set_xticks([0, 10, 20, 30])
    axD.set_xticklabels(["0", "10", "20", "30"], fontsize=6.2)
    axD.set_ylim(-0.6, len(rows_) - 0.4)
    axD.set_xlabel("share of all work orders (%)", fontsize=6.9)
    axD.grid(axis="x", which="major", color=GRID, linewidth=0.4)
    axD.set_title("(d)", loc="left", fontsize=8.0, color=INK, weight="bold",
                  pad=5)
    save(fig, "f7_data")


# ============================================================================
# F8  the raw priority field cannot be read naively (2 panels)
# ============================================================================
def fig8_priority():
    # The profile is the full corpus; the CLASSES are the ones the benchmark
    # actually uses, i.e. the train-only fit released in results/p1_calib.
    train = pd.read_csv(f"{ROOT}/results/p1_calib/priority_mapping.csv")
    prof = full_corpus_priority_profile()
    _check_profile(prof, train)
    cm = prof[prof.is_pm_split == "cm"].copy()

    # Designed at the printed width, so a 6 pt label prints at 6 pt.
    fig = plt.figure(figsize=figsize(TEXTWIDTH_MM, 58))
    gs = fig.add_gridspec(1, 2, left=0.088, right=0.995, top=0.885,
                          bottom=0.165, wspace=0.22)
    axA, axB = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])

    # ---- (a) campus 2, labelled scale, bars ordered by realised close time --
    style_ax(axA)
    C2_FILL, C2_EDGE = "#8fbadd", "#4f81ad"     # one hue: these are one campus
    c2 = cm[cm.campus == 2].dropna(subset=["median_cm_duration_days"])
    c2 = c2.sort_values("median_cm_duration_days")
    labels = [r.raw_value.split("-", 1)[-1].title() for _, r in c2.iterrows()]
    dur = c2.median_cm_duration_days.to_numpy(dtype=float)
    nrows = c2.rows.to_numpy(dtype=int)
    klass = c2.mapped_class.to_numpy(dtype=int)
    # fastest-closing label on top, so the panel reads down the urgency order
    ypos = np.arange(len(c2))[::-1]
    # room for the bar-end annotation, measured from the data rather than frozen
    xmax = float(dur.max()) * 1.38
    # The close time itself is not printed: the axis is linear and gridded, so
    # the bar length carries it. The assigned class cannot be read off any axis,
    # so it is printed, in ONE column at a fixed x clear of the longest bar.
    xclass = float(dur.max()) * 1.12
    for y, d, k in zip(ypos, dur, klass):
        axA.barh(y, d, height=0.55, color=C2_FILL, edgecolor=C2_EDGE,
                 linewidth=0.5, zorder=3)
        axA.text(xclass, y, f"class P{k}",
                 va="center", ha="left", fontsize=6.2, color=INK, zorder=4)
    axA.set_yticks(ypos)
    axA.set_yticklabels([f"{lab}\nn = {n:,}" for lab, n in zip(labels, nrows)],
                        fontsize=6.2, color=INK, linespacing=1.25)
    axA.set_xlim(0, xmax)
    axA.set_xticks([0, 2, 4, 6, 8])
    axA.tick_params(axis="x", labelsize=6.2)
    axA.set_xlabel("median close time of corrective orders (days)", fontsize=6.8)
    axA.set_ylim(-0.6, len(c2) - 0.4)
    axA.grid(axis="x", which="major", color=GRID, linewidth=0.4)
    # The caption is the title; the panel carries only its tag.
    axA.set_title("(a)", loc="left", fontsize=8.0, color=INK, weight="bold",
                  pad=4)

    # ---- (b) campus 12 numeric codes invert urgency (+ campus 1 contrast) ---
    style_ax(axB)
    codes, durs = {}, {}
    # colour is a non-text mark here: campus 1 recessive grey, campus 12 in the
    # focal green, and a legend says which is which. The legend names the two
    # campuses and nothing more: the x axis IS the raw priority code, and the
    # two rank correlations are quoted in the caption.
    SERIES = [(1, MUTE, 1.0, 3.2, 0.9, "campus 1"),
              (12, ROLL_TEAL, 1.7, 4.2, 1.0, "campus 12")]
    curves = []
    for camp, col, lw, ms, alpha, tag in SERIES:
        s = cm[(cm.campus == camp) & (cm.rule == "r5c")].copy()
        s["code"] = s.raw_value.astype(float)
        s = s.sort_values("code")
        codes[camp] = s.code.to_numpy(dtype=float)
        durs[camp] = s.median_cm_duration_days.to_numpy(dtype=float)
        ln, = axB.plot(s.code, s.median_cm_duration_days, "-o", color=col, lw=lw,
                       markersize=ms, markeredgecolor=SURF, markeredgewidth=0.5,
                       alpha=alpha, zorder=3 if camp == 1 else 5)
        curves.append((ln, tag))
    # top-left corner: campus 1 climbs from the bottom left and campus 12 runs
    # along the right-hand half, so the corner is empty in both series.
    axB.legend(handles=[ln for ln, _ in curves],
               labels=[tag for _, tag in curves],
               loc="upper left", frameon=False, fontsize=6.2, labelcolor=INK,
               handlelength=1.6, handletextpad=0.5, labelspacing=0.40,
               borderaxespad=0.3, borderpad=0.0)
    all_codes = np.concatenate([codes[1], codes[12]])
    all_durs = np.concatenate([durs[1], durs[12]])
    xlo, xhi = float(all_codes.min()), float(all_codes.max())
    pad = 0.06 * (xhi - xlo)
    axB.set_xlim(xlo - pad, xhi + pad)
    axB.set_ylim(0, float(np.nanmax(all_durs)) * 1.20)
    axB.set_xticks([0, 10, 20, 30, 40, 50])
    axB.tick_params(axis="both", labelsize=6.2)
    axB.set_xlabel("raw priority code (campus-specific)", fontsize=6.8)
    axB.set_ylabel("median close time of corrective orders (days)", fontsize=6.8)
    axB.grid(axis="y", which="major", color=GRID, linewidth=0.4)
    axB.set_title("(b)", loc="left", fontsize=8.0, color=INK, weight="bold",
                  pad=4)
    save(fig, "f8_priority", tight=False)


# ============================================================================
# F9  what training can and cannot discriminate (2 stacked panels, shared x)
# ============================================================================
def fig9_training():
    seeds = list(range(301, 311))
    curves = {s: pd.read_csv(f"{ROOT}/results/p3_train/v2/seed{s}/curves.csv")
              for s in seeds}
    import matplotlib as _mpl
    _blu = _mpl.colormaps["Blues"]
    blues = [_blu(0.35 + 0.06 * i) for i in range(len(seeds))]

    # Designed at the printed width (as f8 is), so a 6.9 pt label prints at
    # 6.9 pt; the old single-column canvas was enlarged by 1.87 on the page and
    # printed its text at 12 to 15 pt.
    fig, (axA, axB) = plt.subplots(2, 1, figsize=figsize(TEXTWIDTH_MM, 88),
                                   sharex=True,
                                   gridspec_kw=dict(hspace=0.26,
                                                    height_ratios=[1, 1],
                                                    left=0.070, right=0.980,
                                                    top=0.940, bottom=0.105))

    # ---- (a) default-capacity dev: flat plateau ----------------------------
    style_ax(axA)
    # LITERAL GUARD: the plateau band (macros \ablplateaulo/hi = 409-411) must
    # contain every v2 seed's best default-capacity dev value.
    _floors = [curves[s]["dev_wwt_mean"].min() for s in seeds]
    assert all(408.5 <= f <= 411.5 for f in _floors), f"plateau drifted: {_floors}"
    axA.axhspan(409, 411, color=POLICY_BLUE, alpha=0.13, zorder=0, linewidth=0)
    for s, col in zip(seeds, blues):
        d = curves[s]
        axA.plot(d["update"], d["dev_wwt_mean"], "-", color=col, lw=0.9,
                 alpha=0.85, zorder=3, label="_nolegend_")
    axA.set_ylim(408, 426)
    axA.set_yticks([410, 415, 420, 425])
    axA.tick_params(axis="y", labelsize=6.2)
    # The shaded band and the ▾ markers are defined in the caption, so neither
    # panel carries a sentence of its own.
    axA.set_ylabel("dev TWT", fontsize=6.9)
    axA.set_title("(a)", loc="left", fontsize=8.0, color=INK, weight="bold",
                  pad=4)

    # ---- (b) tight-capacity dev (m=0.6): declining + selected checkpoints ---
    style_ax(axB)
    for s, col in zip(seeds, blues):
        d = curves[s]
        raw = d["dev_wwt_tight"]
        roll = raw.rolling(window=15, center=True, min_periods=1).mean()
        axB.plot(d["update"], raw, "-", color=col, lw=0.5, alpha=0.25, zorder=2)
        axB.plot(d["update"], roll, "-", color=col, lw=1.2, alpha=0.98,
                 zorder=4)
        imin = raw.idxmin()
        axB.plot(d["update"][imin], raw[imin], marker="v", color=col,
                 markersize=4.6, markeredgecolor=SURF, markeredgewidth=0.6,
                 zorder=6)
    axB.set_ylim(423, 500)
    axB.set_yticks([440, 460, 480, 500])
    axB.tick_params(axis="y", labelsize=6.2)
    # The checkpoint rule and the clipping of the early updates above 500 are
    # both stated in the caption; the panel itself stays free of text.
    axB.set_ylabel("dev TWT", fontsize=6.9)
    axB.set_xlim(0, 600)
    axB.set_xticks([0, 150, 300, 450, 600])
    axB.tick_params(axis="x", labelsize=6.2)
    axB.set_xlabel("PPO update", fontsize=6.9)
    axB.set_title("(b)", loc="left", fontsize=8.0, color=INK, weight="bold",
                  pad=4)
    save(fig, "f9_training", tight=False)


# ============================================================================
# F10  replan on a clock, not only on arrivals (2 panels)
# ============================================================================
def fig10_rolling():
    recs = json.load(open(f"{ROOT}/results/p4_dyneval/rolling_diag.json"))
    by = {(r["short"], r["variant"]): r for r in recs}

    # Print-true design: 164.5 mm = \textwidth, so every pt below is a pt on
    # the page. Series colours: arrival-only = dark grey (a pathology variant
    # of the same rolling method, not a method of its own), periodic =
    # ROLL_TEAL (the shipped Rolling CP-SAT hue everywhere in the paper).
    # All text is black; series identity is carried by marks and position.
    AO_COL = INK2
    fig = plt.figure(figsize=figsize(161.0, 50))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.62, 1.0], left=0.06,
                          right=0.975, top=0.84, bottom=0.19, wspace=0.26)
    axA = fig.add_subplot(gs[0, 0])
    axB = fig.add_subplot(gs[0, 1])

    # ---- (a) replan-event timeline for id-0102 -----------------------------
    style_ax(axA)
    ao = by[("0102", "arrival-only")]
    pe = by[("0102", "periodic")]
    horizon = max(ao["makespan"], pe["makespan"]) * 1.02
    lanes = [(1, ao, "arrival-only trigger", AO_COL),
             (0, pe, "periodic + arrival", ROLL_TEAL)]
    for y, rec, name, col in lanes:
        t = sorted(rec["replan_times_bh"])
        # longest no-replan span (last tick -> makespan)
        ext = t + [rec["makespan"]]
        gaps = np.diff(ext)
        gi = int(np.argmax(gaps))
        if y == 1:  # shade the stale span in the arrival-only lane only
            axA.add_patch(Rectangle((ext[gi], y - 0.28), gaps[gi], 0.56,
                          facecolor=AO_COL, alpha=0.13, edgecolor="none",
                          zorder=1))
        axA.hlines(y, 0, rec["makespan"], color=AXIS, lw=0.6, zorder=2)
        for tv in t:
            axA.vlines(tv, y - 0.17, y + 0.17, color=col, lw=0.8, zorder=4)
        axA.plot(rec["makespan"], y, marker="|", color=col, markersize=7,
                 markeredgewidth=1.2, zorder=5)
        # The lane name is the panel's only text: the shaded span, the instance
        # this timeline draws and the two episode totals are all named in the
        # caption, and panel (b) plots the totals.
        axA.text(-horizon * 0.012, y, name, ha="right", va="center",
                 fontsize=6.6, color=INK)
    axA.set_xlim(-horizon * 0.175, horizon)
    # the two lanes now sit centred in the panel, the band that carried the
    # removed annotations having gone with them
    axA.set_ylim(-0.48, 1.48)
    axA.set_yticks([])
    for sp in ("left",):
        axA.spines[sp].set_visible(False)
    axA.set_xlabel("business hours", fontsize=7.0)
    axA.set_xticks([0, 100, 200, 300])
    axA.tick_params(axis="x", labelsize=6.6)
    # The caption is the title; the panel carries only its tag.
    axA.set_title("(a)", loc="left", fontsize=8.0, color=INK,
                  weight="bold", pad=6, x=-0.175)

    # ---- (b) outcome slope chart (arrival-only -> periodic), log-y ----------
    style_ax(axB)
    order = ["0102", "0105", "0107"]
    xa, xp = 0.0, 1.0
    FLOOR = 6.0
    # The instance tags take ONE column, left of the arrival-only dots, each at
    # its own dot's height: an instance id is a per-line identity no legend can
    # carry. The two closest episodes stand 0.24 decades apart, wider than a
    # line of type at this panel height, so no tag has to move off its dot and
    # none needs a leader. No episode total is printed: the log axis is what
    # panel (b) is for, and the caption quotes the two the argument turns on.
    IDGAP = -9.0                       # pt from dot centre to the tag's right edge
    for i, sid in enumerate(order):
        a = by[(sid, "arrival-only")]
        p = by[(sid, "periodic")]
        ya, yp, ye = a["wwt"], p["wwt"], a["edd_wwt"]
        axB.plot([xa, xp], [ya, yp], "-", color=MUTE, lw=1.0, zorder=2)
        axB.plot(xa, ya, "o", color=AO_COL, markersize=5.0,
                 markeredgecolor=SURF, markeredgewidth=0.7, zorder=5)
        axB.plot(xp, yp, "o", color=ROLL_TEAL, markersize=5.0,
                 markeredgecolor=SURF, markeredgewidth=0.7, zorder=5)
        # EDD reference mark (dashed) at the periodic column; the caption says
        # what it is, and where EDD scores zero the mark is drawn on the log
        # floor rather than dropped.
        axB.plot([xp - 0.14, xp + 0.14],
                 [ye if ye > 1e-9 else FLOOR] * 2, ls=(0, (2, 1.5)),
                 color=INK2, lw=0.9, zorder=4)
        # instance tag, right-aligned a fixed gap left of its own dot
        axB.annotate(f"id {sid}", xy=(xa, ya), xytext=(IDGAP, 0),
                     textcoords="offset points", fontsize=6.2, color=INK,
                     ha="right", va="center", zorder=6)
    axB.set_yscale("log")
    axB.set_ylim(FLOOR * 0.8, 20000)
    axB.yaxis.set_major_locator(mticker.FixedLocator([10, 100, 1000, 10000]))
    axB.yaxis.set_minor_locator(mticker.NullLocator())
    axB.set_yticklabels(["10", "100", "1,000", "10,000"], fontsize=6.6)
    # left margin sized to the instance-tag column, right margin to the EDD
    # marks, which are now the panel's rightmost ink
    axB.set_xlim(-0.56, 1.30)
    axB.set_xticks([xa, xp])
    axB.set_xticklabels(["arrival\nonly", "periodic"], fontsize=6.6)
    axB.set_ylabel("episode TWT  (log)", fontsize=7.0)
    axB.grid(axis="y", which="major", color=GRID, linewidth=0.4)
    axB.set_title("(b)", loc="left", fontsize=8.0, color=INK,
                  weight="bold", pad=6)
    save(fig, "f10_rolling")


MAIN = {"f7": fig7_data, "f8": fig8_priority, "f9": fig9_training,
        "f10": fig10_rolling}
if __name__ == "__main__":
    set_style()
    which = sys.argv[1:] or list(MAIN)
    for k in which:
        print(f"[{k}]")
        MAIN[k]()
    print("done.")
