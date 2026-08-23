#!/usr/bin/env python
"""
P5 - All figures for the manuscript (cas-dc, double column).

One script, all figures. Renders <fig>.pdf (vector, for LaTeX) + <fig>.png (QA).
Design follows the dataviz skill: fixed categorical order, CVD-validated palette
(worst adjacent dE 16.6 on the tie-bundle; warm outliers 11.2 are mitigated by
direct labels per the skill's secondary-encoding rule), thin marks, hairline
recessive axes, selective direct labels, legend for >=2 series, no dual axes.

Method -> color map is FROZEN and identical across every figure, here and in
scripts/r4_figures.py: the revision added WMDD (a lighter tint of the weighted
due-date violet) and moved the two diagnostic floors onto neutral greys, and
nothing else changed.

The revision moved the utilisation curves, the decision map and the robustness
matrix to scripts/r4_figures.py, which reads the definitive final-evaluation
analysis; this script now builds f1, f2 and f5 only.

  conda activate fjsp && python scripts/p5_figures.py [f1 f2 f5]
"""
import sys, math
import numpy as np
import pandas as pd
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle, Patch
from matplotlib.lines import Line2D
from matplotlib.collections import PatchCollection
import matplotlib.ticker as mticker

from pathlib import Path

ROOT = str(Path(__file__).resolve().parents[1])
FIGDIR = f"{ROOT}/paper/figures"

sys.path.insert(0, f"{ROOT}/src")
from fmwos.io import normalize_method_column  # noqa: E402

# Archived v1.0 result files carry method=="mor" for the rule now named "lpt"
# (R4.1). They are never edited, so every read normalises the method column.
def read_results(path, **kw):
    return normalize_method_column(pd.read_csv(path, **kw))

# ----------------------------------------------------------------------------
# Design tokens (dataviz reference palette, light surface)
# ----------------------------------------------------------------------------
INK      = "#0b0b0b"   # primary text
INK2     = "#52514e"   # secondary text
MUTE     = "#898781"   # axis / muted labels
GRID     = "#e1e0d9"   # hairline gridline
AXIS     = "#c3c2b7"   # baseline / axis
SURF     = "#ffffff"   # chart surface (pure white: the page is white)
TIEGRAY  = "#c3c2b7"   # "top tier" shared color (neutral -> reads as "no winner")
TIEFILL  = "#d9d8d1"   # lighter tie fill for map cells

# FROZEN method -> color (validated). Order = paper legend order.
CMAP = {
    "edd":   "#008300",  # green
    "pfifo": "#8f8d86",  # muted gray (non-focal; ~edd by construction)
    "atc":   "#4a3aa7",  # violet
    # WMDD joins the suite in the revision. It shares the weighted due-date
    # family with ATC, so it takes a lighter tint of the same violet: the
    # kinship is visible, the two stay separable in print and in greyscale.
    "wmdd":  "#7f6bc4",  # light violet
    "wspt":  "#eb6834",  # orange
    "lpt":   "#e34948",  # red (collapse)
    "random":"#c0beb6",  # light muted gray (non-focal floor)
    "ga":    "#eda100",  # yellow
    "cpsat": "#e87ba4",  # magenta (cpsat60 / cpsat300)
    "roll":  "#1baf7a",  # aqua (Rolling CP-SAT)
    "policy":"#2a78d6",  # blue (learned policy, protagonist)
}
PRETTY = {"edd":"EDD","pfifo":"pFIFO","atc":"ATC","wmdd":"WMDD","wspt":"WSPT","lpt":"LPT",
          "random":"Random","ga":"GA","cpsat":"CP-SAT","cpsat60":"CP-SAT 60 s",
          "cpsat300":"CP-SAT 300 s","roll":"Rolling CP-SAT","policy":"Policy"}

def mcol(m):
    """color for a raw method token from any results file."""
    m = m.lower()
    if m.startswith("v2rl") or m in ("policy",): return CMAP["policy"]
    if m.startswith("rl3"): return CMAP["policy"]
    if m.startswith("rollcp") or m == "roll": return CMAP["roll"]
    if m.startswith("cpsat"): return CMAP["cpsat"]
    return CMAP.get(m, MUTE)

# The two diagnostic-floor rules take the neutral greys scripts/r4_figures.py
# gives them on the utilisation curves, so LPT and Random read the same way in
# every figure of the paper and no red/green pair is left carrying meaning
# (EDD is the green one).
FLOOR_GREY = {"lpt": "#6f6d66", "random": "#a8a69e"}


def suite_color(m):
    """mcol(), with the diagnostic floors on the shared neutral greys."""
    return FLOOR_GREY.get(m.lower(), mcol(m))


def pastel(color, amount=0.58):
    """The house pastel tint of a method hue, for an AREA fill.

    Area fills (bars, patches, spans) are pastel and thin marks (markers,
    lines, edges) keep the medium hue, so a filled figure never carries a dark
    block. ``amount`` is the fraction of the chart surface mixed in.
    """
    r, g, b = mpl.colors.to_rgb(color)
    sr, sg, sb = mpl.colors.to_rgb(SURF)
    return (r + (sr - r) * amount, g + (sg - g) * amount, b + (sb - b) * amount)

# ----------------------------------------------------------------------------
# Matplotlib rcParams tuned for cas-dc print sizes
# ----------------------------------------------------------------------------
def set_style():
    plt.rcParams.update({
        "figure.dpi": 150, "savefig.dpi": 150,
        # Times New Roman everywhere (journal body font). "Nimbus Roman" is the
        # URW clone metrically identical to Times New Roman (what Linux ships);
        # STIX is the Times-compatible math companion.
        "font.family": "serif",
        "font.serif": ["Times New Roman", "Nimbus Roman", "STIXGeneral", "DejaVu Serif"],
        "mathtext.fontset": "stix",
        "font.size": 7.2, "axes.titlesize": 7.8, "axes.labelsize": 7.2,
        "xtick.labelsize": 6.6, "ytick.labelsize": 6.6, "legend.fontsize": 6.6,
        "axes.edgecolor": AXIS, "axes.linewidth": 0.5,
        "axes.labelcolor": INK, "text.color": INK,
        # Tick MARKS may stay grey (they are not type); every text element on a
        # figure of this paper is black, hierarchy coming from size, weight and
        # italics, as in scripts/r4_figures.py.
        "xtick.color": MUTE, "ytick.color": MUTE,
        "xtick.labelcolor": INK, "ytick.labelcolor": INK,
        "axes.grid": False, "grid.color": GRID, "grid.linewidth": 0.5,
        "xtick.major.width": 0.5, "ytick.major.width": 0.5,
        "xtick.major.size": 2.2, "ytick.major.size": 2.2,
        "xtick.minor.size": 1.2, "ytick.minor.size": 1.2,
        "axes.spines.top": False, "axes.spines.right": False,
        "lines.linewidth": 1.4, "lines.markersize": 4.5,
        "legend.frameon": False, "legend.handlelength": 1.4,
        "legend.handletextpad": 0.5, "legend.columnspacing": 1.1,
        "legend.labelspacing": 0.35, "pdf.fonttype": 42, "ps.fonttype": 42,
        "axes.axisbelow": True, "savefig.facecolor": SURF, "figure.facecolor": SURF,
    })

MM = 1/25.4
# cas-sc \textwidth = 468.3324 pt = 164.5 mm. EVERY figure the manuscript
# includes at width=\textwidth is written out at exactly this width, so a point
# in the script is a point on the page and one type scale holds across the
# whole paper. A figure saved at any other width is silently rescaled by LaTeX,
# which is how 6.2 pt labels ended up printing at 5.1 pt.
TEXTWIDTH_MM = 164.5
def figsize(w_mm, h_mm): return (w_mm*MM, h_mm*MM)

def style_ax(ax):
    ax.set_facecolor(SURF)
    for s in ("left","bottom"): ax.spines[s].set_color(AXIS); ax.spines[s].set_linewidth(0.5)
    # tick MARKS grey, tick LABELS black (colors= would grey the labels too)
    ax.tick_params(length=2.2, width=0.5, color=MUTE, labelcolor=INK)
    return ax

def save(fig, name, tight=True, width_mm=TEXTWIDTH_MM, pad=0.02):
    """Write <name>.pdf + .png at EXACTLY ``width_mm`` on the page.

    ``tight`` crops the vertical extent to the ink (so no figure carries a
    blank band above or below it) but never the horizontal one: the saved box
    is widened back to the manuscript's text width and centred on the ink, so
    the figure prints at 1:1 and its ink is centred in the frame at the same
    time. A figure whose ink is wider than the text width is a design error and
    aborts rather than being silently shrunk by LaTeX.
    """
    from matplotlib.transforms import Bbox
    target = width_mm * MM
    if tight:
        fig.canvas.draw()
        bb = fig.get_tightbbox(fig.canvas.get_renderer()).padded(pad)
        if bb.width > target + 1e-6:
            raise SystemExit(
                f"{name}: ink is {bb.width/MM:.1f} mm wide, wider than the "
                f"{width_mm} mm text width; narrow the design instead of "
                f"letting LaTeX rescale the type")
        cx = 0.5 * (bb.x0 + bb.x1)
        box = Bbox([[cx - target / 2, bb.y0], [cx + target / 2, bb.y1]])
    else:
        w, h = fig.get_size_inches()
        cx = w / 2
        box = Bbox([[cx - target / 2, 0.0], [cx + target / 2, h]])
    kw = dict(bbox_inches=box)
    # No creation timestamp in the PDF: two runs of this script on unchanged
    # inputs must produce byte-identical files, so a re-render can be checked
    # against the released figure with a checksum.
    fig.savefig(f"{FIGDIR}/{name}.pdf", metadata={"CreationDate": None}, **kw)
    fig.savefig(f"{FIGDIR}/{name}.png", dpi=300, **kw)
    plt.close(fig)
    print(f"  wrote {name}.pdf + .png  ({box.width/MM:.1f} x {box.height/MM:.1f} mm)")

def fmt_wwt(v):
    if v < 10: return f"{v:.1f}"
    if v < 1000: return f"{v:.0f}"
    return f"{v/1000:.1f}k"

def label_ladder(logvals, minsep):
    """Least-displacement direct-label heights on a log axis.

    ``logvals`` are the log10 heights of the points to be labelled, ascending.
    Returns the log10 heights of their labels: the isotonic (pool-adjacent-
    violators) solution of  min sum (l_i - y_i)^2  s.t.  l_{i+1} - l_i >= minsep,
    so every label keeps a readable gap from its neighbours while moving as
    little as possible from its own point. Greedily pushing each label up
    instead piles the whole displacement onto the topmost label of a converging
    bundle, which is what makes a leader necessary and then hard to follow.
    """
    z = [v - minsep * i for i, v in enumerate(logvals)]
    lev, cnt = [], []
    for v in z:
        lev.append(v); cnt.append(1)
        while len(lev) > 1 and lev[-2] > lev[-1] + 1e-12:
            n = cnt[-2] + cnt[-1]
            v2 = (lev[-2] * cnt[-2] + lev[-1] * cnt[-1]) / n
            lev[-2:], cnt[-2:] = [v2], [n]
    fit = [v for v, n in zip(lev, cnt) for _ in range(n)]
    return [f + minsep * i for i, f in enumerate(fit)]

# ============================================================================
# F1  pipeline schematic
# ============================================================================
def fig1_pipeline():
    """The benchmark pipeline, as a five-stage column grid.

    Geometry is in millimetres on the page: the canvas is the manuscript's
    text width, so a point in this function is a point in the printed figure.
    Five equal columns carry the five numbered stages; a stage that forks or
    that produces two artefacts stacks two boxes in its column, and the two
    hub stages centre one box across the same band. Every box is the same
    width and the same height, arrows run left to right, and the only filled
    box is the artefact the paper delivers.
    """
    # The drawing fills the canvas, so the file is written at exactly the text
    # width without a tight crop (an axes covering the figure has no slack for
    # one to remove).
    W, H = TEXTWIDTH_MM, 39.0
    NCOL, GAP = 5, 6.0
    CW = (W - 3.0 - (NCOL - 1) * GAP) / NCOL        # column (= box) width
    COLX = [1.5 + i * (CW + GAP) for i in range(NCOL)]
    BH = 14.0                     # stacked-box height
    TOP_Y, BOT_Y = 19.5, 1.5      # bottoms of the upper and lower box rows
    MID_H = 18.0                  # the two hub boxes, centred on the band
    MID_Y = 0.5 * (BOT_Y + TOP_Y + BH - MID_H)
    LABEL_Y = TOP_Y + BH + 2.6

    fig = plt.figure(figsize=figsize(W, H))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")

    # One accent, one meaning: the benchmark itself is the artefact the paper
    # delivers, so it is the single filled box and the figure's focal point.
    ACCENT = pastel(CMAP["policy"], 0.80)

    # Line breaks are MEASURED, not guessed: every string is wrapped to the box
    # width with the renderer, so no label can overhang its own box when the
    # column count or the wording changes.
    fig.canvas.draw()
    _rend = fig.canvas.get_renderer()
    PT_TITLE, PT_SUB = 7.0, 6.3
    TEXT_W = CW - 2.4                     # usable width inside a box

    def _w_mm(s, fs, weight="normal"):
        t = fig.text(0, 0, s, fontsize=fs, weight=weight)
        w = t.get_window_extent(_rend).width / fig.dpi * 25.4
        t.remove()
        return w

    def _wrap(s, fs, max_mm):
        out = []
        for para in s.split("\n"):        # an explicit break is always kept
            cur = ""
            for word in para.split():
                trial = (cur + " " + word).strip()
                if cur and _w_mm(trial, fs) > max_mm:
                    out.append(cur)
                    cur = word
                else:
                    cur = trial
            if cur:
                out.append(cur)
        return out

    def box(col, y, h, title, sub="", fc=SURF):
        x = COLX[col]
        ax.add_patch(Rectangle((x, y), CW, h, facecolor=fc, edgecolor=INK,
                               linewidth=0.6, zorder=2))
        assert _w_mm(title, PT_TITLE, "bold") <= TEXT_W, (title, CW)
        lines = _wrap(sub, PT_SUB, TEXT_W) if sub else []
        n = 1 + len(lines)
        # one 2.5 mm slot per line, the block centred in the box
        y0 = y + h / 2 + (n - 1) * 1.25
        ax.text(x + CW / 2, y0, title, ha="center", va="center",
                fontsize=PT_TITLE, color=INK, weight="bold", zorder=4)
        for k, ln in enumerate(lines):
            ax.text(x + CW / 2, y0 - 2.5 * (k + 1), ln, ha="center",
                    va="center", fontsize=PT_SUB, color=INK, zorder=4)
        return (x, y, CW, h)

    def arrow(a, b, side_a="r", side_b="l", rad=0.0):
        ax_, ay_, aw, ah = a
        bx_, by_, bw, bh = b
        pa = {"r": (ax_ + aw, ay_ + ah / 2), "l": (ax_, ay_ + ah / 2),
              "t": (ax_ + aw / 2, ay_ + ah), "b": (ax_ + aw / 2, ay_)}[side_a]
        pb = {"r": (bx_ + bw, by_ + bh / 2), "l": (bx_, by_ + bh / 2),
              "t": (bx_ + bw / 2, by_ + bh), "b": (bx_ + bw / 2, by_)}[side_b]
        ax.add_patch(FancyArrowPatch(pa, pb, arrowstyle="-|>",
                                     mutation_scale=7, linewidth=0.8,
                                     color=INK, shrinkA=1.0, shrinkB=1.0,
                                     connectionstyle=f"arc3,rad={rad}",
                                     zorder=1))

    # ---- stage 1: the source log and the cleaning rules --------------------
    b_src = box(0, TOP_Y, BH, "FMUCD", "raw work-order log")
    b_cln = box(0, BOT_Y, BH, "Cleaning R1\u2013R7",
                "de-duplication, priority and trade maps")
    arrow(b_src, b_cln, "b", "t")

    # ---- stage 2: the two instance tracks ----------------------------------
    b_rep = box(1, TOP_Y, BH, "[R] Empirical track",
                "first-N releases, non-overlapping")
    b_gen = box(1, BOT_Y, BH, "[C] Generator track",
                "fitted packs, contention parameters")
    arrow(b_cln, b_rep, "r", "l", rad=-0.22)
    arrow(b_cln, b_gen, "r", "l")

    # ---- stage 3: the released instances (counts read from the results) ----
    # counts are COMPUTED from the released result files so the schematic can
    # never drift out of sync with what was actually evaluated.
    _e1 = pd.read_csv(f"{ROOT}/results/e1_static/results.csv", usecols=["id"])
    # The dynamic sweep is re-run per corpus version; take the live file when it
    # exists and the archived one otherwise, and say which was used, so the
    # count is always read from a results file rather than typed in.
    _dyn_paths = [f"{ROOT}/results/p4_dyneval/results.csv",
                  f"{ROOT}/results/_v10_archive/p4_dyneval/results.csv"]
    _dyn_src = next(p for p in _dyn_paths if Path(p).exists())
    print(f"   f1 dynamic-configuration count read from {_dyn_src}")
    _dy = pd.read_csv(_dyn_src,
                      usecols=["id", "regime", "crew_multiplier",
                               "arrival_multiplier", "pm_share_override"])
    _n_static = _e1["id"].nunique()
    _n_dyn = len(_dy.fillna(-1).drop_duplicates())
    del _e1, _dy
    b_ins = box(2, MID_Y, MID_H, "Benchmark instances",
                f"{_n_static:,} static\n{_n_dyn:,} dynamic", fc=ACCENT)
    arrow(b_rep, b_ins, "r", "l", rad=0.16)
    arrow(b_gen, b_ins, "r", "l", rad=-0.16)

    # ---- stage 4: the method suite (the caption enumerates every method) ---
    b_met = box(3, MID_Y, MID_H, "Method suite",
                "seven dispatching rules,\na genetic algorithm,\n"
                "exact and rolling CP-SAT,\nthe learned policy")
    arrow(b_ins, b_met, "r", "l")

    # ---- stage 5: scoring, independent of every scheduler ------------------
    b_val = box(4, TOP_Y, BH, "Independent validator",
                "feasibility and weighted tardiness")
    b_out = box(4, BOT_Y, BH, "Metrics + decision map",
                "which rule family to use, and when")
    arrow(b_met, b_val, "r", "l", rad=0.16)
    arrow(b_val, b_out, "b", "t")

    # ---- stage band labels, on one shared line ----------------------------
    for i, lab in enumerate(["1  Data + cleaning", "2  Two instance tracks",
                             "3  Instances", "4  Schedulers",
                             "5  Score + characterise"]):
        ax.text(COLX[i] + CW / 2, LABEL_Y, lab, ha="center", va="bottom",
                fontsize=6.6, color=INK, style="italic")

    save(fig, "f1_pipeline", tight=False)

# ============================================================================
# F2  static benchmark (2 panels)
# ============================================================================
def fig2_static():
    e1 = read_results(f"{ROOT}/results/e1_static/results.csv")
    piv = e1.pivot_table(index="id", columns="method", values="wwt", aggfunc="first")
    bk = piv.min(axis=1); nz = bk > 1e-9
    gap = piv.sub(bk, axis=0)
    lat = e1.groupby("method")["wall_seconds"].mean() * 1000.0  # ms

    order = ["cpsat300","cpsat60","ga","wmdd","atc","wspt","pfifo","edd","random","lpt"]
    gaps = {m: gap[m][nz].mean() for m in order}
    ga_beats = int((piv["ga"] < piv["cpsat60"] - 1.0).sum())
    # the bar order is the measured order; assert it rather than trust the list
    assert list(sorted(order, key=lambda m: gaps[m])) == order, \
        {m: round(gaps[m], 3) for m in order}

    # Designed a shade wider than the text width so that, once the tight crop
    # and the fixed-width write-out are applied, the two panels FILL the text
    # width; the type is absolute, so widening the canvas widens the axes
    # without changing a single printed point size.
    fig, (axA, axB) = plt.subplots(1, 2, figsize=figsize(187, 66),
                                   gridspec_kw=dict(wspace=0.42))

    # ---- Panel A: ordered horizontal bars, log-x gap ----
    style_ax(axA)
    ypos = np.arange(len(order))[::-1]
    # Every bar carries its own method's hue, the same hue the method has in
    # panel (b) and in every other figure: pastel for the fill, the medium hue
    # for the edge. LPT and random ordering keep the neutral greys the whole
    # paper gives the two diagnostic floors.
    for y, m in zip(ypos, order):
        c = suite_color(m)
        axA.barh(y, gaps[m], height=0.62, color=pastel(c), edgecolor=c,
                 linewidth=0.7, zorder=3)
        axA.text(gaps[m]*1.14, y, fmt_wwt(gaps[m]), va="center", ha="left", fontsize=6.2, color=INK, zorder=4)
    axA.set_yticks(ypos)
    axA.set_yticklabels([PRETTY.get(m,m) for m in order], fontsize=6.8, color=INK)
    axA.set_xscale("log")
    axA.set_xlim(0.1, 2200)
    axA.set_xlabel("Mean gap to best-known TWT  (weighted tardiness, log)", fontsize=6.9)
    # Plain decimal tick labels rather than powers of ten: a superscript
    # exponent at this tick size prints below 5 pt.
    axA.xaxis.set_major_locator(mticker.FixedLocator([0.1, 1, 10, 100, 1000]))
    axA.xaxis.set_minor_locator(mticker.NullLocator())
    axA.set_xticklabels(["0.1", "1", "10", "100", "1,000"], fontsize=6.4)
    axA.grid(axis="x", which="major", color=GRID, linewidth=0.5)
    axA.set_axisbelow(True)
    # tier brackets
    # tier labels sit just above the top bar of their tier, which the order
    # above fixes: exact/near-exact = rows 0-2, dispatching rules = rows 3-7,
    # diagnostic floor = rows 8-9 (row index counted from the top). The wording
    # is the caption's and the body's: "dispatching rules", "diagnostic floors".
    _row = lambda m: ypos[order.index(m)]
    axA.text(0.14, _row("cpsat300") + 0.55, "exact / near-exact", fontsize=6.2, color=INK, style="italic")
    axA.text(15, _row("wmdd") + 0.55, "dispatching rules", fontsize=6.2, color=INK, style="italic")
    # raised well clear of the random-ordering bar's own value label, and kept
    # right of the EDD bar's end so the extra height costs no overlap
    axA.text(135, _row("random") + 0.42, "diagnostic floor", fontsize=6.2,
             color=INK, style="italic", va="bottom")
    # GA beats cpsat60 annotation. The caption states the count; the figure
    # only points at the bar the claim is about.
    # leader lands INSIDE the GA bar (not at its tip) so the curve stays well
    # clear of the '4.3' value label sitting just right of the bar end.
    axA.annotate("GA improves on CP-SAT 60 s here",
                 xy=(gaps["ga"]*0.55, ypos[order.index("ga")]),
                 xytext=(9, _row("cpsat60") + 0.9), fontsize=6.2, color=INK, ha="left", va="center",
                 arrowprops=dict(arrowstyle="-", color=MUTE, lw=0.6,
                                 connectionstyle="arc3,rad=-0.2"))
    # The caption is the title and it carries the instance count, so the panel
    # carries only its tag.
    axA.set_title("(a)", loc="left", fontsize=8.0, color=INK, weight="bold",
                  pad=6)

    # ---- Panel B: latency vs quality scatter ----
    style_ax(axB)
    # EDD and pFIFO coincide by construction (gap 73 vs 72, same latency) -> one dot,
    # drawn in EDD green and labelled 'EDD / pFIFO'. Panel (a) keeps both bars.
    order_b = [m for m in order if m != "pfifo"]
    LAB_B = dict(PRETTY); LAB_B["edd"] = "EDD / pFIFO"
    axB.set_xscale("log"); axB.set_yscale("log")
    axB.set_xlim(0.25, 12000); axB.set_ylim(0.1, 1200)
    for m in order_b:
        axB.scatter(lat[m], gaps[m], s=42, color=suite_color(m), edgecolor=SURF,
                    linewidth=0.9, zorder=4)
    # The six dispatching rules answer inside one factor of two in latency, so
    # their labels cannot all sit at their own marker height: WMDD and ATC are
    # 0.13 decades apart and would overprint. Each label therefore keeps its own
    # x (just right of its dot) and takes the least-displaced height that leaves
    # a readable gap to its neighbours, with a leader in the method's own colour
    # tying it back to its dot. Labels themselves are black.
    RULES_B = ["wmdd", "atc", "wspt", "edd", "random", "lpt"]
    MINSEP = 0.30          # decades between label centres at this panel height
    _rank = sorted(RULES_B, key=lambda m: gaps[m])
    LADDER = dict(zip(_rank, (10 ** v for v in label_ladder(
        [math.log10(gaps[m]) for m in _rank], MINSEP))))
    # one shared column for the six labels: left edges align, and every leader
    # is long enough to be seen, so no label can be read against a neighbour's dot
    XCOL = max(lat[m] for m in RULES_B) * 1.65
    for m in RULES_B:
        axB.annotate(LAB_B.get(m, m), xy=(lat[m], gaps[m]),
                     xytext=(XCOL, LADDER[m]), textcoords="data",
                     fontsize=6.2, color=INK, ha="left", va="center", zorder=5,
                     arrowprops=dict(arrowstyle="-", color=suite_color(m),
                                     lw=0.8, shrinkA=1.0, shrinkB=3.5))
    # the three search-based schedulers are far apart: plain adjacent labels
    OFF_S = {"ga": (7, 0, "left", "center"),
             "cpsat60": (7, 0, "left", "center"),
             "cpsat300": (-7, 0, "right", "center")}
    for m, (dx, dy, ha, va) in OFF_S.items():
        axB.annotate(LAB_B.get(m, m), (lat[m], gaps[m]), textcoords="offset points",
                     xytext=(dx, dy), fontsize=6.2, color=INK, ha=ha, va=va)
    axB.set_xlabel("Decision latency per instance  (ms, log)", fontsize=6.9)
    axB.set_ylabel("Mean gap to best-known TWT  (log)", fontsize=6.9)
    # plain decimal tick labels here too, for the same print-size reason
    axB.xaxis.set_major_locator(mticker.FixedLocator([1, 10, 100, 1000, 10000]))
    axB.xaxis.set_minor_locator(mticker.NullLocator())
    axB.set_xticklabels(["1", "10", "100", "1,000", "10,000"], fontsize=6.4)
    axB.yaxis.set_major_locator(mticker.FixedLocator([0.1, 1, 10, 100, 1000]))
    axB.yaxis.set_minor_locator(mticker.NullLocator())
    axB.set_yticklabels(["0.1", "1", "10", "100", "1,000"], fontsize=6.4)
    axB.grid(True, which="major", color=GRID, linewidth=0.5)
    # guide regions
    axB.text(0.7, 0.16, "fast, coarse", fontsize=6.2, color=INK, style="italic")
    axB.text(1600, 300, "slow, exact", fontsize=6.2, color=INK, style="italic", ha="center")
    # the trade-off guide starts to the right of the rule cluster, so it never
    # crosses a direct label
    _FR = ((2.5, 700.0), (3500.0, 0.3))
    axB.annotate("", xy=_FR[1], xytext=_FR[0],
                 arrowprops=dict(arrowstyle="-", color=GRID, lw=0.8))
    # rotate the guide's label by the line's angle ON THE PAGE, measured through
    # the axes transform, so it stays parallel whatever the panel's aspect is
    (_x0, _y0), (_x1, _y1) = (axB.transData.transform(p) for p in _FR)
    axB.text(55, 8, "quality\u2013latency\ntrade-off", fontsize=6.2, color=INK,
             style="italic", ha="center", va="center",
             rotation=math.degrees(math.atan2(_y1 - _y0, _x1 - _x0)),
             rotation_mode="anchor")
    axB.set_title("(b)", loc="left", fontsize=8.0, color=INK, weight="bold",
                  pad=6)
    save(fig, "f2_static")

# ============================================================================
# F3  intensity curves (4 small multiples)
# ============================================================================
def fig3_curves():
    c = read_results(f"{ROOT}/results/p4_dyneval/e2_curve.csv")
    # Policy = MEAN across the ten MLP seeds (protocol forbids best-of-seeds);
    # a min..max band across seeds shows honest seed spread (widens on campus 5 u>=1).
    POL_SEEDS = [f"v2rl{s}" for s in range(301, 311)]
    series = [("edd","EDD"),("atc","ATC"),("wspt","WSPT"),("lpt","LPT"),("policy","Policy (10 seeds)")]
    # Per-series styles so tied lines that coincide exactly stay distinguishable:
    # thick EDD underneath, dashed ATC over it (gaps reveal green), Policy markers on top.
    STYLE = {
        "edd":    dict(ls="-",         lw=2.4, alpha=0.85, zorder=3, marker="",  ms=0),
        "atc":    dict(ls=(0,(4,1.8)), lw=1.5, alpha=1.0,  zorder=4, marker="",  ms=0),
        "wspt":   dict(ls="-",         lw=1.3, alpha=1.0,  zorder=3, marker="",  ms=0),
        "lpt":    dict(ls="-",         lw=1.3, alpha=1.0,  zorder=4, marker="",  ms=0),
        "policy": dict(ls="-",         lw=1.2, alpha=1.0,  zorder=5, marker="o", ms=3.2),
    }
    campuses = [5.0, 9.0, 10.0, 12.0]
    fig, axes = plt.subplots(1, 4, figsize=figsize(180, 60), sharey=True,
                             gridspec_kw=dict(wspace=0.12))
    ymax = 260000
    for ax, camp in zip(axes, campuses):
        style_ax(ax)
        sub = c[c.campus == camp]
        # shade u>1 (overload)
        ax.axvspan(1.0, 1.35, color=GRID, alpha=0.6, zorder=0, linewidth=0)
        for key, lab in series:
            st = STYLE[key]; col = mcol(key)
            if key == "policy":
                pm = (sub[sub.method.isin(POL_SEEDS)]
                      .pivot_table(index="u_target", columns="method", values="mean_wwt")
                      .sort_index())
                xs = pm.index.values
                lo = pm.min(axis=1).values; hi = pm.max(axis=1).values; mn = pm.mean(axis=1).values
                ax.fill_between(xs, lo, hi, color=col, alpha=0.18, zorder=2, linewidth=0)
                ax.plot(xs, mn, color=col, ls=st["ls"], lw=st["lw"], marker=st["marker"],
                        markersize=st["ms"], markeredgecolor=SURF, markeredgewidth=0.5,
                        zorder=st["zorder"], alpha=st["alpha"])
            else:
                d = sub[sub.method == key].sort_values("u_target")
                ax.plot(d.u_target, d.mean_wwt, color=col, ls=st["ls"], lw=st["lw"],
                        marker=st["marker"], markersize=st["ms"], markeredgecolor=SURF,
                        markeredgewidth=0.5, zorder=st["zorder"], alpha=st["alpha"])
        ax.set_yscale("symlog", linthresh=1.0, linscale=0.5)
        ax.set_ylim(0, ymax)
        ax.set_xlim(0.65, 1.35)
        ax.set_xticks([0.7, 0.9, 1.1, 1.3])
        ax.set_title(f"Campus {int(camp)}", loc="left", fontsize=7.2, color=INK, weight="bold", pad=3)
        ax.grid(axis="y", which="major", color=GRID, linewidth=0.4)
        ax.tick_params(axis="x", labelsize=6.2)
    # y ticks ONCE after the loop: with sharey=True a later set_yticks([]) on
    # any panel clears the shared locator for every panel (the bug that shipped
    # an unlabelled axis); label the left panel, hide labels elsewhere.
    axes[0].set_yticks([0, 1, 100, 10000, 100000])
    axes[0].set_yticklabels(["0", "1", "100", "10k", "100k"], fontsize=6.2)
    axes[0].set_ylabel("Mean TWT  (symlog)", fontsize=6.9)
    for ax in axes[1:]:
        ax.tick_params(labelleft=False)
    # overload label: top of the shaded band on campus 5, where no curve passes
    axes[0].text(1.17, 1.5e5, "overload\n$u>1$", fontsize=6.1, color=MUTE, ha="center", va="top")
    # LPT callout on campus 12: clear space above-left of the red curve, not touching it
    axes[3].text(0.68, 2.2e5, "LPT collapses", fontsize=6.1, color=CMAP["lpt"],
                 ha="left", va="top", weight="bold")
    # top-tier tie callout: text in empty upper-left of campus 9, leader to the tied bundle
    axes[1].annotate("top-tier tie:\nEDD $\\approx$ ATC $\\approx$ Policy",
                     xy=(1.22, 950), xycoords="data",
                     xytext=(0.04, 0.98), textcoords="axes fraction",
                     fontsize=5.6, color=INK, ha="left", va="top",
                     arrowprops=dict(arrowstyle="-", color=MUTE, lw=0.6,
                                     connectionstyle="arc3,rad=0.18"))
    fig.subplots_adjust(left=0.06, right=0.995, top=0.90, bottom=0.30, wspace=0.12)
    fig.text(0.53, 0.155, "target utilization  $u$", ha="center", va="center", fontsize=7.0, color=INK)
    # shared legend (styles mirror the plotted series so each stays identifiable)
    handles = [
        Line2D([0],[0], color=mcol("edd"),    lw=2.4, ls="-",         label="EDD"),
        Line2D([0],[0], color=mcol("atc"),    lw=1.5, ls=(0,(4,1.8)), label="ATC"),
        Line2D([0],[0], color=mcol("wspt"),   lw=1.3, ls="-",         label="WSPT"),
        Line2D([0],[0], color=mcol("lpt"),    lw=1.3, ls="-",         label="LPT"),
        Line2D([0],[0], color=mcol("policy"), lw=1.2, ls="-", marker="o", markersize=3.6,
               markeredgecolor=SURF, label="Policy (10 seeds)"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=5, fontsize=6.6,
               bbox_to_anchor=(0.53, 0.02), frameon=False)
    save(fig, "f3_curves")

# ============================================================================
# F4  decision map (money figure)
#   PRIMARY (cell colour) = 4-way winner over {EDD, ATC, WSPT, Policy} on ALL
#     instances in the cell.  Policy = per-instance MEAN across the three RL
#     seeds v2rl301/302/303 (mean, never best-of-seeds).
#   SECONDARY (dagger) = the fair 5-way match that additionally includes Rolling
#     CP-SAT, computed on the CP-SAT-replan common id subset (n=8 per campus);
#     a cell is daggered where that 5-way winner differs from the 4-way winner.
# ============================================================================
POL_SEEDS = [f"v2rl{s}" for s in range(301, 311)]
FOCAL4 = ["edd", "atc", "wspt", "policy"]
F4LAB = {"edd": "EDD", "atc": "ATC", "wspt": "WSPT", "policy": "Policy", "roll": "Rolling"}

def _policy_per_id(df):
    """per-instance policy TWT = MEAN over the available RL seeds (never best-of)."""
    p = df[df.method.isin(POL_SEEDS)]
    return p.groupby("id")["wwt"].mean()

def _winner4(df, tol=0.01):
    """PRIMARY: 4-way winner over {EDD, ATC, WSPT, Policy} on ALL cell instances."""
    pol = _policy_per_id(df)
    rp = (df[df.method.isin(["edd", "atc", "wspt"])]
          .pivot_table(index="id", columns="method", values="wwt", aggfunc="mean"))
    ids = rp.dropna().index.intersection(pol.index)
    if len(ids) == 0: return None
    mw = pd.Series({"edd": rp.loc[ids, "edd"].mean(),
                    "atc": rp.loc[ids, "atc"].mean(),
                    "wspt": rp.loc[ids, "wspt"].mean(),
                    "policy": pol.loc[ids].mean()}).reindex(FOCAL4)
    best = mw.min()
    winners = [m for m in mw.index if mw[m] <= best*(1+tol)+1e-9]
    return best, winners, len(ids), mw

def _winner5(df, tol=0.01):
    """SECONDARY: 5-way (+ Rolling CP-SAT) on the rollcp2-common id subset."""
    ids = set(df.loc[df.method == "rollcp2", "id"].unique())
    if not ids: return None
    sub = df[df.id.isin(ids)]
    pol = _policy_per_id(sub)
    rp = (sub[sub.method.isin(["edd", "atc", "wspt", "rollcp2"])]
          .pivot_table(index="id", columns="method", values="wwt", aggfunc="mean"))
    aids = rp.dropna().index.intersection(pol.index)
    if len(aids) == 0: return None
    mw = pd.Series({"edd": rp.loc[aids, "edd"].mean(),
                    "atc": rp.loc[aids, "atc"].mean(),
                    "wspt": rp.loc[aids, "wspt"].mean(),
                    "roll": rp.loc[aids, "rollcp2"].mean(),
                    "policy": pol.loc[aids].mean()})
    best = mw.min()
    winners = [m for m in mw.index if mw[m] <= best*(1+tol)+1e-9]
    return best, winners, len(aids)

def _top(winners):
    return "tie" if len(winners) > 1 else winners[0]

def _cell_color(winners):
    if winners is None: return SURF, ""
    if len(winners) > 1: return TIEFILL, "tie"
    w = winners[0]
    return mcol("policy" if w == "policy" else ("roll" if w == "roll" else w)), F4LAB[w]

def _draw_cell(ax, x, y, w, h, winners, best, held=False, dagger=False):
    fc, lab = _cell_color(winners)
    ax.add_patch(FancyBboxPatch((x+0.03, y+0.03), w-0.06, h-0.06,
        boxstyle="round,pad=0,rounding_size=0.03", facecolor=fc, edgecolor=SURF, linewidth=1.2, zorder=2))
    if held:
        ax.add_patch(FancyBboxPatch((x+0.03, y+0.03), w-0.06, h-0.06,
            boxstyle="round,pad=0,rounding_size=0.03", facecolor="none",
            edgecolor=INK, linewidth=1.1, linestyle=(0,(2,1)), zorder=4))
    # text color: white on saturated policy/roll/atc/wspt, ink on tie/edd/ga
    dark = fc not in (TIEFILL, SURF, CMAP["ga"])
    tc = "#ffffff" if dark else INK
    if lab:
        ax.text(x+w/2, y+h*0.60, lab, ha="center", va="center", fontsize=6.6,
                color=tc, weight="bold", zorder=5)
        ax.text(x+w/2, y+h*0.30, fmt_wwt(best), ha="center", va="center", fontsize=6.1,
                color=tc if dark else INK2, zorder=5)
    if dagger:  # 5-way (+Rolling) match on n=8 subset picks a different winner
        ax.text(x+w-0.14, y+h-0.13, "†", ha="right", va="top", fontsize=7.4,
                color=tc if lab else INK, weight="bold", zorder=6)

def fig4_map():
    d = read_results(f"{ROOT}/results/p4_dyneval/results.csv")
    fig = plt.figure(figsize=figsize(180, 80))
    axA = fig.add_axes([0.030, 0.02, 0.26, 0.95]); axA.set_xlim(-1.15, 3.05); axA.set_ylim(-0.95, 3.55); axA.axis("off"); axA.set_aspect("equal"); axA.set_anchor("NW")
    axB = fig.add_axes([0.335, 0.02, 0.29, 0.95]); axB.set_xlim(-1.35, 3.05); axB.set_ylim(-1.05, 6.55); axB.axis("off"); axB.set_aspect("equal"); axB.set_anchor("W")
    tally = {}         # PRIMARY 4-way tally (drives colour + headline)
    tally_old5 = {}    # published 5-way(best-seed) tally, for the before/after print
    n_dagger = 0
    dagger_sets = []   # 5-way winner sets of daggered cells (caption guard)

    def _old5(df, tol=0.01):
        """published winner: {edd,atc,wspt,v2rl302,rollcp2} on rollcp2-common ids."""
        ids = set(df.loc[df.method == "rollcp2", "id"].unique())
        sub = df[df.id.isin(ids)] if ids else df
        F5 = ["edd", "atc", "wspt", "v2rl302", "rollcp2"]
        mw = sub[sub.method.isin(F5)].groupby("method")["wwt"].mean().reindex(F5).dropna()
        if mw.empty: return "tie"
        best = mw.min(); ws = [m for m in mw.index if mw[m] <= best*(1+tol)+1e-9]
        if len(ws) > 1: return "tie"
        return {"v2rl302": "policy", "rollcp2": "roll"}.get(ws[0], ws[0])

    def _place(ax, cc, yy, cell, held=False, name=""):
        nonlocal n_dagger
        res4 = _winner4(cell)
        if not res4: return
        best, winners, n, mw = res4
        res5 = _winner5(cell)
        dag = (res5 is not None) and (_top(res5[1]) != _top(winners))
        _draw_cell(ax, cc, yy, 1, 1, winners, best, held=held, dagger=dag)
        top = _top(winners); tally[top] = tally.get(top, 0) + 1
        o = _old5(cell); tally_old5[o] = tally_old5.get(o, 0) + 1
        if dag:
            n_dagger += 1
            dagger_sets.append((name, tuple(sorted(res5[1]))))

    # ---- Panel (a): pmmix, campuses pooled, pm_share x crew ----
    pm = d[d.regime == "pmmix"]
    pms = [0.2, 0.5, 0.8]; crews = [0.6, 0.8, 1.0]
    for r, pmv in enumerate(pms):
        yy = 2 - r  # top row = pm 0.2
        for cc, cr in enumerate(crews):
            cell = pm[(pm.pm_share_override == pmv) & (pm.crew_multiplier == cr)]
            _place(axA, cc, yy, cell, name=f"pm{pmv} m{cr}")
    for cc, cr in enumerate(crews):
        axA.text(cc + 0.5, -0.12, f"{cr:g}", ha="center", va="top", fontsize=6.6, color=INK2)
    for r, pmv in enumerate(pms):
        axA.text(-0.10, (2 - r) + 0.5, f"{pmv:g}", ha="right", va="center", fontsize=6.6, color=INK2)
    axA.text(1.5, -0.60, "crew multiplier", ha="center", va="top", fontsize=6.9, color=INK)
    axA.text(-0.78, 1.5, "PM share", ha="center", va="center", rotation=90, fontsize=6.9, color=INK)
    axA.text(-1.1, 3.42, "(a)  Generator contention", ha="left", va="bottom", fontsize=7.6, color=INK, weight="bold")
    axA.text(-1.1, 3.15, "campuses 5/9/10/12 pooled", ha="left", va="bottom", fontsize=6.3, color=INK2, style="italic")

    # ---- Panel (b): replay, campus x crew ----
    camps = [1, 2, 5, 9, 10, 12]
    colspec = [("replay-default", 1.0, "1.0\ndefault"), ("replay-tight", 0.8, "0.8\ntight"), ("replay-tight", 0.6, "0.6\ntight")]
    for ri, camp in enumerate(camps):
        yy = 5 - ri
        held = camp in (1, 2)
        for ci, (reg, cr, _) in enumerate(colspec):
            rr = d[d.regime == reg]
            cell = rr[(rr.campus == camp) & (rr.crew_multiplier == cr)] if reg == "replay-tight" else rr[rr.campus == camp]
            _place(axB, ci, yy, cell, held=held, name=f"c{camp} m{cr}")
        axB.text(-0.12, yy + 0.5, f"c{camp}", ha="right", va="center", fontsize=6.6,
                 color=INK, weight="bold" if held else "normal")
    # held-out bracket
    axB.plot([-0.78, -0.78], [4.05, 5.95], color=CMAP["lpt"], lw=1.0)
    axB.plot([-0.78, -0.68], [5.95, 5.95], color=CMAP["lpt"], lw=1.0)
    axB.plot([-0.78, -0.68], [4.05, 4.05], color=CMAP["lpt"], lw=1.0)
    axB.text(-0.95, 5.0, "held out", ha="center", va="center", rotation=90, fontsize=6.0, color=CMAP["lpt"], weight="bold")
    for ci, (_, _, lab) in enumerate(colspec):
        axB.text(ci + 0.5, -0.12, lab, ha="center", va="top", fontsize=6.2, color=INK2)
    axB.text(1.5, -0.92, "crew multiplier  (regime)", ha="center", va="top", fontsize=6.9, color=INK)
    axB.text(-1.3, 6.35, "(b)  Replay contention", ha="left", va="bottom", fontsize=7.6, color=INK, weight="bold")
    axB.text(-1.3, 6.08, "per campus; c1/c2 held out from training", ha="left", va="bottom", fontsize=6.3, color=INK2, style="italic")

    # ---- right-hand text column: headline, legend, how-to-read ------------
    # Every displayed count is COMPUTED (tally, len(POL_SEEDS)) so the figure
    # can never drift out of sync with the data it plots.
    import textwrap
    x0 = 0.640
    n_tie = tally.get("tie", 0); n_tot = sum(tally.values())
    fig.text(x0, 0.955, f"{n_tie} of {n_tot} cells:  top-tier tie", fontsize=9.5,
             color=INK, weight="bold", ha="left", va="top")
    fig.text(x0, 0.860,
             "rules $\\approx$ policy $\\approx$ optimiser; ATC leads\n"
             "outright on c2, and on c5/c10 at the\ntightest crew.",
             fontsize=6.9, color=INK2, ha="left", va="top")
    leg = [Patch(facecolor=TIEFILL, edgecolor=SURF, label="top tier: rules $\\approx$ policy (tie $\\leq$1%)"),
           Patch(facecolor=CMAP["atc"], edgecolor=SURF, label="ATC wins outright"),
           Line2D([0], [0], marker=r"$\dagger$", color=INK, linestyle="none", markersize=7,
                  label="5-way (+Rolling) subsample differs"),
           Patch(facecolor="none", edgecolor=INK, linestyle=(0, (2, 1)), label="held-out campus")]
    fig.legend(handles=leg, loc="upper left", ncol=1, fontsize=6.4,
               bbox_to_anchor=(x0 - 0.012, 0.700), frameon=False,
               labelspacing=0.55, handletextpad=0.6)
    note = (f"Cell colour = lowest mean TWT among {{EDD, ATC, WSPT, Policy}} over all "
            f"instances in the cell; Policy = per-instance mean of the {len(POL_SEEDS)} "
            "seeds, never a best-of. The winner is labelled with its mean TWT; methods "
            "within 1% of the best share the top-tier colour. \u2020 marks cells where the "
            "five-way match that adds Rolling CP-SAT (8 instances per campus-size "
            "cell) ends in a top-tier tie instead. Policy never wins a cell outright.")
    fig.text(x0, 0.415, "\n".join(textwrap.wrap(note, 52)), fontsize=5.9,
             color=MUTE, ha="left", va="top", linespacing=1.35)
    # LITERAL GUARD: fig_map.tex caption names the dagger outcomes (3 cells,
    # each a 5-way top-tier tie: {ATC,Rolling} on c2-default and c5-m0.6,
    # {ATC,WSPT} on c10-m0.6). Fail the build if the data drifts from that prose.
    assert sorted(dagger_sets) == [
        ("c10 m0.6", ("atc", "wspt")),
        ("c2 m1.0", ("atc", "roll")),
        ("c5 m0.6", ("atc", "roll")),
    ], f"dagger outcomes drifted from the fig_map.tex caption: {dagger_sets}"
    save(fig, "f4_map")
    print("   F4 winner tally  BEFORE (published 5-way, best-seed):", tally_old5)
    print("   F4 winner tally  AFTER  (4-way full-cell, seed-mean) :", tally, "| dagger cells:", n_dagger)

# ============================================================================
# F5  transfer and stress (single column, two panels sharing the method rows)
#   Source: results/r4_final/analysis/equivalence.csv, the definitive
#   final-evaluation analysis.  Panel (a) is the held-out transfer campus,
#   panel (b) the held-out chronic-overload campus; both score every method
#   against that campus's own best method, so the pair answers "does the
#   leading set survive a campus that was never trained on?".
# ============================================================================
ANA_FINAL = f"{ROOT}/results/r4_final/analysis"

F5_RULES = [("edd", "EDD"), ("pfifo", "pFIFO"), ("wmdd", "WMDD"), ("atc", "ATC"),
            ("wspt", "WSPT"), ("lpt", "LPT"), ("random", "Random")]
# learned pools, matched by the checkpoint-id prefix so no seed is typed in
F5_POOLS = [(r"^v2rl\d+$", "Policy pool"),
            (r"^v2at\d+$", "Attention pool"),
            (r"^rl\d+$", "Curriculum-v1 pool")]
# Each panel names the campus it holds and nothing else: the caption already
# says which is the transfer campus and which is chronically overloaded.
F5_SCOPES = [("transfer", "campus=1|m=1.0", "Campus 1"),
             ("stress", "campus=2|m=1.0", "Campus 2")]
# Pastel amber, with the medium amber for its edge: the margin is a protocol
# threshold and not a method, so it takes a hue no method in this figure uses
# (a pastel blue would read as the learned pools' own colour).
BAND, BAND_EDGE = "#f7efdb", "#b8862b"
# On the overload campus the two diagnostic floors run to two hundred per cent
# while the six other rules sit inside twenty, so that panel's x axis is broken:
# 0 to F5_BREAK is expanded across F5_LEFTF of the panel and the rest is
# compressed into what is left. Tick labels carry the true values throughout.
F5_BREAK = {1: 20.0}
F5_LEFTF, F5_GAPF = 0.60, 0.045


def fig5_transfer():
    import re
    eq = pd.read_csv(f"{ANA_FINAL}/equivalence.csv")

    def rows_for(scope_type, scope):
        d = eq[(eq.scope_type == scope_type) & (eq.scope == scope)]
        assert not d.empty, (scope_type, scope)
        base = float(d.mean_best.iloc[0])
        pct = lambda v: 100.0 * float(v) / base
        gap = dict(zip(d.method, d.pct_from_best))
        lo_ = dict(zip(d.method, d.ci_lo))
        hi_ = dict(zip(d.method, d.ci_hi))
        inset = {m: bool(v) for m, v in zip(d.method, d.in_equivalence_set)}
        out = []
        for m, lab in F5_RULES:
            out.append(dict(kind="rule", label=lab, key=m, mid=gap[m],
                            lo=pct(lo_[m]), hi=pct(hi_[m]), inset=inset[m],
                            n=1, k=int(inset[m])))
        for pat, lab in F5_POOLS:
            seeds = [m for m in d.method if re.match(pat, m)]
            g = np.array([gap[m] for m in seeds], dtype=float)
            out.append(dict(kind="pool", label=lab, key="policy",
                            mid=float(np.median(g)), lo=g.min(), hi=g.max(),
                            inset=None, n=len(seeds),
                            k=sum(inset[m] for m in seeds)))
        return (out, pct(d.margin.iloc[0]), int(d.n_configs.iloc[0]),
                int(len(d)), int(d.in_equivalence_set.sum()))

    panels = [rows_for(st, sc) + (title,) for st, sc, title in F5_SCOPES]
    nrow = len(panels[0][0])

    # The canvas IS the manuscript's text width, so the printed text size is
    # the source size; a narrower canvas would be enlarged and print oversized.
    fig = plt.figure(figsize=figsize(TEXTWIDTH_MM, 74))
    left, bot, height = 0.152, 0.250, 0.620
    width, gapw = 0.393, 0.043
    for i, (rows, margin_pct, n_cfg, n_meth, n_set, title) in enumerate(panels):
        ax = fig.add_axes([left + i * (width + gapw), bot, width, height])
        style_ax(ax)
        ypos = np.arange(nrow)[::-1]
        # every number is printed to the right of its row, so the axis is
        # widened until the longest label fits rather than flipping labels to
        # the left, where they would collide with the method names
        # one decimal for every value label in a panel, so the column reads as
        # one column rather than as three formats
        def _txt(r):
            return f"{r['mid']:.1f}" + (
                f"  {r['k']}/{r['n']}" if r["kind"] == "pool" and r["n"] > 1
                else "")
        dmax = max(max(r["hi"], r["mid"]) for r in rows)
        brk = F5_BREAK.get(i)
        if brk is None:
            xdata = max(1.06 * dmax, 1.35 * margin_pct)

            def T(v, _x=xdata):
                return float(v) / _x
        else:
            xdata = 1.04 * dmax

            def T(v, _b=brk, _x=xdata):
                v = float(v)
                if v <= _b:
                    return F5_LEFTF * v / _b
                return (F5_LEFTF + F5_GAPF
                        + (1.0 - F5_LEFTF - F5_GAPF) * (v - _b) / (_x - _b))
        # room for the value labels, measured from the labels themselves; a
        # label that would land inside the break gap is pushed past it
        def _tx(r):
            x = T(max(r["hi"], r["mid"])) + 0.022
            if brk is not None and F5_LEFTF - 0.004 < x < F5_LEFTF + F5_GAPF:
                x = F5_LEFTF + F5_GAPF + 0.008
            return x
        charw = 3.1 / (width * TEXTWIDTH_MM / 25.4 * 72.0)   # one digit at 6.2 pt
        xhi = max(_tx(r) + charw * len(_txt(r)) for r in rows) + 0.012
        # the margin band: a rule is in the set when its whole interval is inside
        ax.axvspan(0, T(margin_pct), color=BAND, zorder=0, linewidth=0)
        ax.axvline(T(margin_pct), color=BAND_EDGE, lw=0.7, zorder=1)
        for y, r in zip(ypos, rows):
            col = suite_color(r["key"]) if r["kind"] == "rule" else CMAP["policy"]
            span = r["hi"] - r["lo"]
            if span > 1e-9:
                lw = 1.0 if r["kind"] == "rule" else 1.9
                ax.plot([T(r["lo"]), T(r["hi"])], [y, y], color=col, lw=lw,
                        alpha=1.0 if r["kind"] == "rule" else 0.45,
                        solid_capstyle="butt", zorder=4)
                if r["kind"] == "rule":
                    for xv in (r["lo"], r["hi"]):
                        ax.plot([T(xv), T(xv)], [y - 0.18, y + 0.18], color=col,
                                lw=1.0, zorder=4)
            filled = r["inset"] if r["kind"] == "rule" else (r["k"] == r["n"])
            ax.plot(T(r["mid"]), y, marker="o" if r["kind"] == "rule" else "D",
                    markersize=4.0 if r["kind"] == "rule" else 3.4, zorder=6,
                    color=col if filled else SURF, markeredgecolor=col,
                    markeredgewidth=0.9, linestyle="none")
            ax.text(_tx(r), y, _txt(r), ha="left", va="center", fontsize=6.2,
                    color=INK, zorder=8)
        ax.set_ylim(-0.7, nrow - 0.3)
        ax.set_xlim(-0.03, xhi)
        ax.set_yticks(ypos)
        if i == 0:
            ax.set_yticklabels([r["label"] for r in rows], fontsize=7.0, color=INK)
        else:
            ax.tick_params(labelleft=False)
        # ticks carry the true percentages on both sides of a break
        if brk is None:
            tv = [t for t in mticker.MaxNLocator(3, steps=[1, 2, 2.5, 5, 10])
                  .tick_values(0, xdata) if 0 <= t <= xdata]
        else:
            tv = ([t for t in (0, 5, 10, 15, 20) if t <= brk]
                  + [t for t in (50, 100, 150, 200, 250) if brk < t <= xdata])
        ax.set_xticks([T(t) for t in tv])
        ax.set_xticklabels([f"{t:g}" for t in tv])
        ax.tick_params(axis="x", labelsize=6.4)
        ax.grid(axis="x", which="major", color=GRID, linewidth=0.4)
        if brk is not None:
            # interrupt every mark that crosses the break, then mark the break
            # itself with the usual pair of slashes on the baseline
            ax.add_patch(Rectangle((F5_LEFTF, -0.7), F5_GAPF, nrow + 0.4,
                                   facecolor=SURF, edgecolor="none", zorder=7))
            for xb in (F5_LEFTF, F5_LEFTF + F5_GAPF):
                ax.plot([xb - 0.013, xb + 0.013], [-0.90, -0.50], color=MUTE,
                        lw=0.8, zorder=8, clip_on=False,
                        transform=ax.transData)
        ax.set_xlabel("Percent above the campus's own best method"
                      + ("\n(axis break at %g%%)" % brk if brk else ""),
                      fontsize=7.0, labelpad=3)
        ax.text(0.5, 1.085, title, transform=ax.transAxes, ha="center",
                va="bottom", fontsize=7.4, color=INK)
        ax.text(0.5, 1.018, f"n = {n_cfg}", transform=ax.transAxes, ha="center",
                va="bottom", fontsize=6.4, color=INK, style="italic")

    handles = [
        Patch(facecolor=BAND, edgecolor=BAND_EDGE, linewidth=0.7,
              label="practical-equivalence margin"),
        Line2D([0], [0], marker="o", color=INK2, lw=1.0, markerfacecolor=INK2,
               markersize=4.0, label="rule: 95% interval, in the set"),
        Line2D([0], [0], marker="o", color=INK2, lw=1.0, markerfacecolor=SURF,
               markeredgecolor=INK2, markeredgewidth=0.9, markersize=4.0,
               label="rule: 95% interval, outside it"),
        Line2D([0], [0], marker="D", color=CMAP["policy"], lw=1.9, alpha=0.6,
               markerfacecolor=SURF, markeredgecolor=CMAP["policy"],
               markersize=3.4, label="pool: seed range, median, seeds in set"),
    ]
    # centred on the two panels, which is where the eye returns from the key
    fig.legend(handles=handles, loc="lower center",
               bbox_to_anchor=(left + width + gapw / 2, 0.006),
               ncol=4, fontsize=6.4, frameon=False, handlelength=1.7,
               columnspacing=1.2, labelspacing=0.40)
    save(fig, "f5_transfer", tight=False)

    for (rows, margin_pct, n_cfg, n_meth, n_set, title) in panels:
        print(f"   F5 {title}: set {n_set}/{n_meth}, n {n_cfg}, "
              f"margin {margin_pct:.2f}% of the best mean")
        print("      " + "  ".join(
            f"{r['label']}={r['mid']:.2f}[{r['lo']:.2f},{r['hi']:.2f}]"
            + ("" if r["kind"] == "rule" else f" {r['k']}/{r['n']}")
            for r in rows))

# ============================================================================
# F6  sensitivity (Kendall tau matrix, single column) -- frozen summary values
# ============================================================================
def fig6_sensitivity():
    cols = ["c5/150","c5/400","c9/150","c9/400","c10/150","c10/400","c12/150","c12/400","pooled"]
    rows = ["sla0.5","sla1.5","crew0.75","crew1.25"]
    rowlab = ["SLA x0.5","SLA x1.5","crew x0.75","crew x1.25"]
    NA = np.nan
    T = np.array([
        [NA, NA, 0.81, 0.81, 0.72, 0.40, 0.72, 0.20, 0.83],
        [NA, NA, 0.85, 1.00, 1.00, 0.85, 0.82, 0.09, 0.83],
        [NA, NA, 0.87, 0.77, 0.87, 0.31, 0.85, 0.49, 0.77],
        [NA, NA, 0.85, 0.98, 0.97, 0.90, 1.00, 0.20, 0.83],
    ])
    # LITERAL GUARD: the frozen pooled column must match the released
    # tab_sensitivity.tex; refuse to draw a stale figure.
    import re as _re
    _tab = open(f"{ROOT}/results/p4_sensitivity/tab_sensitivity.tex").read()
    _pooled = [float(m) for m in _re.findall(r"&\s*([01]\.\d+)\s*&\s*[01]\.\d+\s*\\\\", _tab)]
    _frozen = [row[-1] for row in T]
    assert all(abs(a - b) < 1e-9 for a, b in zip(_frozen, _pooled)), \
        f"f6 frozen pooled taus {_frozen} != released {_pooled}"
    nr, nc = len(rows), len(cols)
    # fixed single-column layout (saved WITHOUT tight-crop so it renders 1:1 at
    # column width and the label fonts do not shrink below the print floor)
    fig = plt.figure(figsize=figsize(88, 59))
    ax = fig.add_axes([0.185, 0.160, 0.790, 0.615]); ax.set_xlim(0, nc); ax.set_ylim(0, nr); ax.axis("off")
    from matplotlib.colors import LinearSegmentedColormap
    blues = LinearSegmentedColormap.from_list("blu", ["#eef4fb", "#cde2fb", "#6da7ec", "#2a78d6", "#184f95"])
    def _lum(rgba):
        f = lambda c: c/12.92 if c <= 0.03928 else ((c+0.055)/1.055)**2.4
        R, G, B = (f(rgba[0]), f(rgba[1]), f(rgba[2])); return 0.2126*R + 0.7152*G + 0.0722*B
    for i in range(nr):
        yy = nr - 1 - i
        for j in range(nc):
            v = T[i, j]
            if np.isnan(v):
                ax.add_patch(Rectangle((j+0.04, yy+0.04), 0.92, 0.92, facecolor="#f0efec", edgecolor=SURF, linewidth=1.2))
                ax.text(j+0.5, yy+0.5, "n/a", ha="center", va="center", fontsize=6.6, color=MUTE, style="italic")
                continue
            fill = blues(float(min(1.0, max(0.0, v))))  # float() so v==1.0 is a value, not a LUT index
            ax.add_patch(Rectangle((j+0.04, yy+0.04), 0.92, 0.92, facecolor=fill, edgecolor=SURF, linewidth=1.2))
            if v < 0.8:   # below-threshold: 45-deg hatch as the secondary (print-safe) channel
                ax.add_patch(Rectangle((j+0.04, yy+0.04), 0.92, 0.92, facecolor="none",
                             edgecolor="#2b2b2b", linewidth=0.3, hatch="/////"))
            tc = "#ffffff" if _lum(fill) < 0.45 else INK
            ax.text(j+0.5, yy+0.5, f"{v:.2f}", ha="center", va="center", fontsize=6.9,
                    color=tc, weight="bold" if j == nc-1 else "normal")
    # column labels: two-line horizontal (campus over size), no rotation overhang
    for j, cl in enumerate(cols):
        lab = cl.replace("/", "\n")
        ax.text(j+0.5, nr + 0.06, lab, ha="center", va="bottom", fontsize=6.4,
                color=INK if cl == "pooled" else INK2, linespacing=0.92,
                weight="bold" if cl == "pooled" else "normal", clip_on=False)
    for i, rl in enumerate(rowlab):
        ax.text(-0.12, (nr-1-i)+0.5, rl, ha="right", va="center", fontsize=6.6, color=INK2, clip_on=False)
    ax.plot([8, 8], [0, nr], color=AXIS, lw=0.7)   # separator before pooled
    fig.text(0.020, 0.965, "Ranking robustness (Kendall $\\tau_b$)", ha="left", va="top",
             fontsize=8.0, color=INK, weight="bold")
    fig.text(0.020, 0.025, "hatched: $\\tau < 0.8$ (ranking perturbed).\nn/a: degenerate cell (baseline fully tied).",
             ha="left", va="bottom", fontsize=6.6, color=INK2)
    # dead code: superseded by f6_robustness (scripts/r4_figures.py) and no
    # longer input by the manuscript. It is a single-column exhibit, so it
    # keeps its own width rather than the text width.
    save(fig, "f6_sensitivity", tight=False, width_mm=88)

# ============================================================================
MAIN = {"f1": fig1_pipeline, "f2": fig2_static, "f5": fig5_transfer}
# The revision moved three figures to scripts/r4_figures.py, which reads the
# definitive final-evaluation analysis instead of the development sweep. Two of
# them write the SAME file names as the functions kept below for reference, so
# running those here would silently overwrite the manuscript's versions.
SUPERSEDED = {"f3": "f3_curves", "f4": "f4_map", "f6": "f6_robustness"}
if __name__ == "__main__":
    set_style()
    which = sys.argv[1:] or list(MAIN)
    for k in which:
        if k in SUPERSEDED:
            raise SystemExit(
                f"{k} is now built by scripts/r4_figures.py "
                f"(writes {SUPERSEDED[k]}.pdf); run that script instead.")
        print(f"[{k}]"); MAIN[k]()
    print("done.")
