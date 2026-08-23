#!/usr/bin/env python
"""
R4 figure wave: the four exhibits the R4 revision adds or redesigns.

  f4_map        decision map: the scarcity grid and the capacity ladder
  fvis_effects  preventive-visibility effects, small multiples
  f3_curves     utilisation curves on the generator track
  f6_robustness robustness stability matrix (replaces f6_sensitivity)

One script, idempotent, reading ONLY the three definitive-analysis
directories:

  results/r4_final/analysis/       (Eval-B)
  results/r4_robustness/analysis/  (R4.7-R4.10)
  results/r4_visibility/analysis/  (R4.6)

No number is ever typed into this file; every printed quantity is read from
those CSVs (or headline_vis.json) and formatted here.

Style: the house palette and typography of scripts/p5_figures.py, imported
rather than copied, and extended with the pastel fill / medium line pair the
paper-figures skill requires for area fills. All figure text is black; no
figure draws its own title (the LaTeX caption is the title); every colour
encoding carries the same information as in-cell text.

  PYTHONPATH=src python scripts/r4_figures.py [f4 fvis f3 f6]
"""
import json
import sys
import textwrap
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle, Patch  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
import matplotlib.ticker as mticker  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

# ONE house palette: the frozen tokens of the existing figure script.
from p5_figures import (  # noqa: E402
    INK, MUTE, GRID, AXIS, SURF, CMAP, figsize, label_ladder,
)

FIGDIR = ROOT / "paper" / "figures"
ANA_FINAL = ROOT / "results" / "r4_final" / "analysis"
ANA_ROB = ROOT / "results" / "r4_robustness" / "analysis"
ANA_VIS = ROOT / "results" / "r4_visibility" / "analysis"

# ---------------------------------------------------------------------------
# Palette extension: pastel fills + medium-depth line/mark variants.
# Fills are pastel because dark blocks are banned; thin marks take the medium
# variant of the same hue so they survive print. Hues are the house hues.
# ---------------------------------------------------------------------------
FILL = {
    "neutral":  "#d5dae0",   # light grey  - no method separates
    "duedate":  "#a8c6e3",   # light blue  - due-date rules
    "weighted": "#f8e3b6",   # light amber - weighted due-date rules
    "policy":   "#e28f99",   # light rose  - learned policy
    "blank":    "#ffffff",   # not tested
}
LINE = {
    "neutral":  "#6f7780",
    "duedate":  "#4f81ad",
    "weighted": "#b8862b",
    "policy":   "#c25b6a",
}
# ordered pastel ramp for the robustness grades (luminance-ordered, one hue,
# so the matrix reads in greyscale as well as in colour)
GRADE_FILL = ["#f6f9fc", "#d0e2f0", "#a3c4e0"]   # changes / narrows / holds

MM = 1 / 25.4
TEXTWIDTH_MM = 164.5   # cas-sc \textwidth = 468.33 pt; design at print size


def set_style():
    """House rcParams (p5_figures), with every text element forced to black."""
    plt.rcParams.update({
        "figure.dpi": 150, "savefig.dpi": 150,
        "font.family": "serif",
        "font.serif": ["Times New Roman", "Nimbus Roman", "Liberation Serif",
                       "STIXGeneral", "DejaVu Serif"],
        "mathtext.fontset": "stix",
        "font.size": 7.2, "axes.titlesize": 7.8, "axes.labelsize": 7.2,
        "xtick.labelsize": 6.6, "ytick.labelsize": 6.6, "legend.fontsize": 6.6,
        "axes.edgecolor": AXIS, "axes.linewidth": 0.5,
        "axes.labelcolor": INK, "text.color": INK,
        "xtick.color": MUTE, "ytick.color": MUTE,
        "xtick.labelcolor": INK, "ytick.labelcolor": INK,
        "axes.grid": False, "grid.color": GRID, "grid.linewidth": 0.5,
        "xtick.major.width": 0.5, "ytick.major.width": 0.5,
        "xtick.major.size": 2.2, "ytick.major.size": 2.2,
        "axes.spines.top": False, "axes.spines.right": False,
        "lines.linewidth": 1.2, "lines.markersize": 3.4,
        "legend.frameon": False, "legend.handlelength": 1.5,
        "legend.handletextpad": 0.5, "legend.columnspacing": 1.1,
        "legend.labelspacing": 0.35, "pdf.fonttype": 42, "ps.fonttype": 42,
        # Hatch is a secondary channel: it stays legible in the cell and in the
        # legend swatch, and every hatched cell masks it behind its own text
        # (see _cell), so no stroke ever crosses a glyph at print size.
        "axes.axisbelow": True, "hatch.linewidth": 0.30,
        "savefig.facecolor": SURF, "figure.facecolor": SURF,
    })


# Hatch stroke colour, shared by the decision map and the robustness matrix.
HATCH_INK = "#9aa0a6"


def save(fig, name, tight=False):
    kw = dict(bbox_inches="tight", pad_inches=0.02) if tight else {}
    fig.savefig(FIGDIR / f"{name}.pdf", **kw)
    fig.savefig(FIGDIR / f"{name}.png", dpi=300, **kw)
    plt.close(fig)
    print(f"  wrote {name}.pdf + .png")


def style_ax(ax):
    ax.set_facecolor(SURF)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(AXIS)
        ax.spines[s].set_linewidth(0.5)
    ax.tick_params(length=2.2, width=0.5, color=MUTE, labelcolor=INK)
    return ax


# ===========================================================================
# F4  decision map: what moves the rule-family boundary, and what does not
# ===========================================================================
# Panel (a) is the direct scarcity grid of scripts/r4_scarcity.py: realised
# utilisation on x, the share of workload sitting in overloaded trades on y,
# and one mechanically derived family label per cell.  Panel (b) is the
# capacity ladder of scripts/r4_family_analysis.py on the chronically
# overloaded campus, where the weighted rules separate from EDD as the crews
# are cut.  Every quantity is read from those CSVs and formatted here.
GRID_SCOPE = "no_campus2"        # verdict-eligible cells: campus 2 held out
GRID_REF_SCOPE = "all"           # the same grid with campus 2 put back in
UBINS = ["<0.5", "0.5-0.8", "0.8-1.0", "1.0-1.2", ">=1.2"]   # x, left to right
OVBANDS = ["<0.25", "0.25-0.5", "0.5-0.75", ">=0.75"]        # y, bottom to top

# One meaning per colour, held across both panels: blue is the due-date
# family, amber the weighted-urgency family, pale grey a cell where the two
# are interchangeable.  Every cell also writes its label, so the map reads
# without colour and in greyscale.
CELL_FILL = {"either": "#e3e6e9", "due-date": FILL["duedate"],
             "weighted": FILL["weighted"], "insufficient": "#ffffff"}
CELL_WORD = {"either": "Either", "due-date": "Due-date",
             "weighted": "Weighted", "insufficient": "Too few"}
FAM_LINE = {"duedate": LINE["duedate"], "weighted": LINE["weighted"]}

# Panel (b): the two weighted-urgency rules, plus one due-date rule pinned at
# the reference for contrast.  Order is top to bottom inside each rung.
# (key in the CSV, printed name, family, marker).  The marker carries the
# family as well as the colour does, so the panel survives greyscale.
LADDER_RULES = [("wmdd", "WMDD", "weighted", "o"),
                ("atc", "ATC", "weighted", "o"),
                ("pfifo", "pFIFO", "duedate", "s")]

# Type scale: three sizes, two weights, italic for the one aside.
PT_SMALL, PT_BODY, PT_TAG = 6.2, 6.8, 8.0

# Print-true geometry, in millimetres on the page (the figure is drawn at
# \textwidth, so a millimetre here is a millimetre in the manuscript).
H_MM = 84.0
AX_BOT, AX_TOP = 29.0, 78.5          # both panels share this band
A_X0, A_W = 18.0, 62.0               # panel (a) grid: 5 columns of 12.4 mm
B_GUT, B_X0, B_W = 90.0, 96.5, 41.0  # panel (b) gutter, axes left, axes width
B_NUM_X, B_VERD_X = 1.19, 1.22       # right-hand text column, in axes fractions
HEAD_U, ROW_U, GAP_U = 1.0, 1.15, 0.45   # panel (b) row grid, in row units


def _band_label(tok):
    """`0.5-0.8` -> `0.5–0.8`, `>=1.2` -> `≥ 1.2`, `<0.5` -> `< 0.5`."""
    if tok.startswith(">="):
        return "≥ " + tok[2:]
    if tok.startswith("<"):
        return "< " + tok[1:]
    return tok.replace("-", "–")


def _signed(v):
    """Thousands separator and a true minus sign."""
    s = f"{abs(v):,.0f}"
    return ("−" + s) if (v < 0 and s != "0") else s


def _quantile_token(arm):
    """Capacity arm `q0.95` -> the percentile it names, `p95`."""
    return "p%d" % round(float(arm[1:]) * 100)


def _wrap(txt, size, width_mm):
    """Wrap to the cell width, using the Times average advance width."""
    per_char_mm = 0.535 * size * (25.4 / 72.0)
    n = max(8, int(width_mm / per_char_mm))
    return textwrap.wrap(txt, n) or [""]


def _cell(ax, cx, cy, w, h, fill, blocks, cell_w_mm, hatch=False, dashed=False,
          registry=None):
    """One matrix cell: pastel fill, black hairline, wrapped text blocks.

    `blocks` is a list of (text, size, weight, style); each is wrapped to the
    cell width and the whole stack is centred vertically.
    """
    ax.add_patch(Rectangle((cx, cy), w, h, facecolor=fill, edgecolor=INK,
                           linewidth=0.4, zorder=2))
    if hatch:
        ax.add_patch(Rectangle((cx, cy), w, h, facecolor="none",
                               edgecolor=HATCH_INK, linewidth=0.0, hatch="//",
                               zorder=3))
    if dashed:
        ax.add_patch(Rectangle((cx, cy), w, h, facecolor="none", edgecolor=INK,
                               linewidth=0.9, linestyle=(0, (2, 1.4)), zorder=4))
    rows = []
    for txt, size, weight, style in blocks:
        for piece in _wrap(txt, size, cell_w_mm - 1.4):
            rows.append((piece, size, weight, style))
    # stack height in points, converted to axis fraction of the cell
    pitch = [1.33 * s for (_, s, _, _) in rows]
    total = sum(pitch) + 0.9 * rows[0][1] if rows else 0.0
    fig = ax.figure
    cell_h_pt = h / (ax.get_ylim()[1] - ax.get_ylim()[0]) * \
        ax.get_position().height * fig.get_figheight() * 72.0
    y = cy + h / 2 + (total / 2) / cell_h_pt * h
    # In a hatched cell every text line carries a patch of the cell's own fill
    # behind it, so the hatch stops at the glyphs instead of striking through
    # them; the patch is the fill colour, not white, so the cell keeps one flat
    # colour.
    tbox = (dict(boxstyle="square,pad=0.10", facecolor=fill, edgecolor="none")
            if hatch else None)
    for (txt, size, weight, style), pit in zip(rows, pitch):
        y -= (pit / cell_h_pt) * h
        t = ax.text(cx + w / 2, y, txt, ha="center", va="center", fontsize=size,
                    color=INK, weight=weight, style=style, zorder=5, bbox=tbox)
        if registry is not None:
            registry.append((t, (cx, cy, w, h), ax))


def _stack_pt(blocks, cell_w_mm):
    """Height in points of the text stack `_cell` would draw for `blocks`."""
    sizes = [size for txt, size, _, _ in blocks
             for _ in _wrap(txt, size, cell_w_mm - 1.4)]
    return sum(1.33 * s for s in sizes) + 0.9 * sizes[0]


def _check_fit(fig, registry, tag):
    """Mechanical collision gate: every cell text must sit inside its cell."""
    fig.canvas.draw()
    bad = []
    for t, (cx, cy, w, h), ax in registry:
        bb = t.get_window_extent(fig.canvas.get_renderer())
        x0, y0 = ax.transData.transform((cx, cy))
        x1, y1 = ax.transData.transform((cx + w, cy + h))
        if bb.x0 < x0 - 0.5 or bb.x1 > x1 + 0.5 or bb.y0 < y0 - 0.5 or bb.y1 > y1 + 0.5:
            bad.append((t.get_text(),
                        round(min(bb.x0 - x0, x1 - bb.x1), 1),
                        round(min(bb.y0 - y0, y1 - bb.y1), 1)))
    if bad:
        print(f"   !! {tag}: {len(bad)} text blocks overflow their cell")
        for b in bad[:12]:
            print("      ", b)
    else:
        print(f"   {tag}: no cell-text overflow")
    return bad


def _check_texts(fig, tag, min_pt=PT_SMALL):
    """Type-size floor, canvas containment and text-on-text collisions.

    The cell gate `_check_fit` only sees matrix cells, so this second gate
    walks every text the figure holds: nothing may print below the size floor,
    nothing may run off the canvas, and no two labels may touch.
    """
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    items = [t for t in fig.findobj(mpl.text.Text)
             if t.get_visible() and t.get_text().strip()]
    bad = []
    for t in items:
        if t.get_size() < min_pt - 1e-6:
            bad.append(f"{t.get_text()[:28]!r} at {t.get_size()} pt")
    W, H = fig.get_size_inches() * fig.dpi
    boxes = []
    for t in items:
        bb = t.get_window_extent(rend)
        if bb.x0 < -0.5 or bb.y0 < -0.5 or bb.x1 > W + 0.5 or bb.y1 > H + 0.5:
            bad.append(f"{t.get_text()[:28]!r} runs off the canvas")
        boxes.append((t, bb))
    for i in range(len(boxes)):
        ti, bi = boxes[i]
        for j in range(i + 1, len(boxes)):
            tj, bj = boxes[j]
            ox = min(bi.x1, bj.x1) - max(bi.x0, bj.x0)
            oy = min(bi.y1, bj.y1) - max(bi.y0, bj.y0)
            if ox > 0.8 and oy > 0.8:
                bad.append(f"{ti.get_text()[:20]!r} overlaps "
                           f"{tj.get_text()[:20]!r}")
    if bad:
        print(f"   !! {tag}: {len(bad)} text defects")
        for b in bad[:14]:
            print("      ", b)
    else:
        print(f"   {tag}: {len(items)} texts, all ≥ {min_pt} pt, "
              "inside the canvas, none overlapping")
    return bad


def fig4_map():
    grid = pd.read_csv(ANA_FINAL / "scarcity_grid.csv")
    fam = pd.read_csv(ANA_FINAL / "family_robust.csv")
    caputil = pd.read_csv(ANA_ROB / "capacity_utilization.csv")
    gmeta = json.loads((ANA_FINAL / "scarcity_meta.json").read_text())
    min_cl = int(gmeta["min_clusters_grid"])   # cells below this get no verdict

    # ---- panel (a): the verdict-eligible grid, and the same grid with the
    # chronically overloaded campus put back in --------------------------------
    gv = grid[grid.scope == GRID_SCOPE]
    ga = grid[grid.scope == GRID_REF_SCOPE]
    assert set(gv.u_bin) == set(UBINS) and set(gv.ov_band) == set(OVBANDS)
    cellv = {(r.u_bin, r.ov_band): r for r in gv.itertuples()}
    cella = {(r.u_bin, r.ov_band): r for r in ga.itertuples()}
    n_weighted = sum(1 for r in cellv.values()
                     if r.recommended_family == "weighted")
    # cells that name the weighted family only because campus 2 is in them
    campus2_only = [k for k, r in cella.items()
                    if r.recommended_family == "weighted"
                    and cellv.get(k) is not None
                    and cellv[k].recommended_family != "weighted"]

    # ---- panel (b): the capacity ladder on the chronically overloaded campus -
    cap = fam[(fam.check == "capacity") & (fam.stratum == "campus2")]
    arms = sorted(set(cap.arm), key=lambda a: -float(a[1:]))   # loosest first
    cu = caputil[caputil.stratum == "campus2"].set_index("arm")
    lad, margin_pct, rung = {}, {}, {}
    for a in arms:
        sub = cap[cap.arm == a]
        mean_edd = float(sub.mean_edd.iloc[0])
        margin_pct[a] = 100.0 * float(sub.margin.iloc[0]) / mean_edd
        rung[a] = dict(u_median=float(cu.loc[a, "u_median"]),
                       n=int(sub.n_clusters.iloc[0]))
        for key, _, _, _ in LADDER_RULES:
            r = sub[sub.family == key].iloc[0]
            lad[(a, key)] = dict(
                diff=float(r.mean_diff), verdict=str(r.verdict),
                lo_abs=float(r.ci_lo), hi_abs=float(r.ci_hi),
                pct=100.0 * float(r.mean_diff) / mean_edd,
                lo=100.0 * float(r.ci_lo) / mean_edd,
                hi=100.0 * float(r.ci_hi) / mean_edd)
    one_margin = max(margin_pct.values()) - min(margin_pct.values()) < 1e-6

    # ---- canvas -------------------------------------------------------------
    W = TEXTWIDTH_MM
    fig = plt.figure(figsize=figsize(W, H_MM))

    def frac(x, y, w, h):
        return [x / W, y / H_MM, w / W, h / H_MM]

    axa = fig.add_axes(frac(A_X0, AX_BOT, A_W, AX_TOP - AX_BOT))
    axb = fig.add_axes(frac(B_X0, AX_BOT, B_W, AX_TOP - AX_BOT))

    # =====================================================================
    # Panel (a): the decision map
    # =====================================================================
    axa.set_xlim(0, len(UBINS)); axa.set_ylim(0, len(OVBANDS))
    axa.set_facecolor(SURF)
    for s in axa.spines.values():
        s.set_visible(False)
    cell_w_mm = A_W / len(UBINS)
    cell_h = 1.0
    pad = 0.032
    reg, blanks = [], []
    for i, ub in enumerate(UBINS):
        for j, ob in enumerate(OVBANDS):
            x, y = i + pad, j + pad
            w, h = 1 - 2 * pad, cell_h - 2 * pad
            r = cellv.get((ub, ob))
            if r is None:
                axa.add_patch(Rectangle((x, y), w, h, facecolor=SURF,
                                        edgecolor=AXIS, linewidth=0.5,
                                        linestyle=(0, (1.0, 1.6)), zorder=2))
                blanks.append((i, j))
                continue
            key = r.recommended_family
            blocks = [(CELL_WORD[key], PT_BODY, "bold", "normal"),
                      (f"n = {int(r.n_clusters)}", PT_SMALL, "normal",
                       "normal")]
            _cell(axa, x, y, w, h, CELL_FILL[key], blocks, cell_w_mm - 0.8,
                  hatch=(key == "insufficient"), registry=reg)
            if (ub, ob) in campus2_only:
                axa.add_patch(Rectangle((x, y), w, h, facecolor="none",
                                        edgecolor=FAM_LINE["weighted"],
                                        linewidth=1.0,
                                        linestyle=(0, (2, 1.4)), zorder=6))

    # The empty band is annotated so it does not read as unfinished, and the
    # sentence it carries is the panel's finding.
    runs = []
    for j in range(len(OVBANDS)):
        run = []
        for i in range(len(UBINS)):
            if (i, j) in blanks:
                run.append(i)
            elif run:
                runs.append((j, run)); run = []
        if run:
            runs.append((j, run))
    j, run = max(runs, key=lambda t: (len(t[1]), -t[0]))
    assert len(run) >= 2, runs
    note_a = ("No cell recommends the weighted family" if n_weighted == 0 else
              f"{n_weighted} of {len(cellv)} cells recommend the weighted "
              "family")
    t = axa.text(min(run) + len(run) / 2, j + 0.5,
                 "\n".join(_wrap(note_a, PT_SMALL, len(run) * cell_w_mm - 1.0)),
                 ha="center", va="center", fontsize=PT_SMALL, color=INK,
                 style="italic", linespacing=1.35, zorder=7)
    reg.append((t, (min(run) + pad, j + pad, len(run) - 2 * pad,
                    cell_h - 2 * pad), axa))

    axa.set_xticks([i + 0.5 for i in range(len(UBINS))])
    axa.set_xticklabels([_band_label(b) for b in UBINS], fontsize=PT_BODY)
    axa.set_yticks([j + 0.5 for j in range(len(OVBANDS))])
    axa.set_yticklabels([_band_label(b) for b in OVBANDS], fontsize=PT_BODY)
    axa.tick_params(length=0, pad=2.0, labelcolor=INK)

    # =====================================================================
    # Panel (b): the depth ladder on the chronically overloaded campus
    # =====================================================================
    total_u = len(arms) * (HEAD_U + len(LADDER_RULES) * ROW_U) + \
        (len(arms) - 1) * GAP_U
    axb.set_ylim(0, total_u)
    axb.set_facecolor(SURF)
    ypos, heads, cur = {}, [], 0.0
    for a in arms:
        heads.append((total_u - cur - HEAD_U * 0.52, a))
        cur += HEAD_U
        for key, _, _, _ in LADDER_RULES:
            ypos[(a, key)] = total_u - cur - ROW_U / 2
            cur += ROW_U
        cur += GAP_U

    lo_min = min(v["lo"] for v in lad.values())
    hi_max = max(v["hi"] for v in lad.values())
    span = hi_max - lo_min
    axb.set_xlim(lo_min - 0.06 * span, hi_max + 0.05 * span)

    # The margin band IS the zero reference: it is centred on EDD and, at this
    # scale, about a millimetre wide, which is the honest picture of how small
    # the practical-equivalence margin is beside the differences below.
    MARGIN_GREY = "#d0d2d5"
    if one_margin:
        axb.axvspan(-margin_pct[arms[0]], margin_pct[arms[0]],
                    facecolor=MARGIN_GREY, edgecolor="none", zorder=1)
    else:
        for a in arms:
            ys = [ypos[(a, k)] for k, _, _, _ in LADDER_RULES]
            axb.add_patch(Rectangle((-margin_pct[a], min(ys) - ROW_U / 2),
                                    2 * margin_pct[a],
                                    max(ys) - min(ys) + ROW_U,
                                    facecolor=MARGIN_GREY, edgecolor="none",
                                    zorder=1))

    for a in arms:
        for key, _, famkey, mk in LADDER_RULES:
            d = lad[(a, key)]
            y = ypos[(a, key)]
            col = FAM_LINE[famkey]
            axb.errorbar([d["pct"]], [y],
                         xerr=[[d["pct"] - d["lo"]], [d["hi"] - d["pct"]]],
                         fmt=mk, ms=3.0, mfc=col, mec=col, ecolor=col,
                         elinewidth=0.9, capsize=1.4, capthick=0.9, zorder=4)
    ytr = axb.get_yaxis_transform()
    for y, a in heads:
        axb.text(-(B_X0 - B_GUT) / B_W, y,
                 f"{_quantile_token(a)} crews · median u = "
                 f"{rung[a]['u_median']:.2f}",
                 transform=ytr, ha="left", va="center", fontsize=PT_BODY,
                 weight="bold", color=INK, clip_on=False)
    for a in arms:
        for key, nice, _, _ in LADDER_RULES:
            d = lad[(a, key)]
            y = ypos[(a, key)]
            axb.text(B_NUM_X, y, _signed(d["diff"]), transform=ytr, ha="right",
                     va="center", fontsize=PT_SMALL, color=INK, clip_on=False)
            axb.text(B_VERD_X, y, d["verdict"], transform=ytr, ha="left",
                     va="center", fontsize=PT_SMALL, color=INK, clip_on=False)

    axb.set_yticks([ypos[(a, k)] for a in arms for k, _, _, _ in LADDER_RULES])
    axb.set_yticklabels([n for _ in arms for _, n, _, _ in LADDER_RULES],
                        fontsize=PT_BODY)
    axb.tick_params(axis="y", length=0, pad=2.0, labelcolor=INK)
    axb.tick_params(axis="x", length=2.2, width=0.5, color=MUTE,
                    labelsize=PT_BODY, labelcolor=INK, pad=2.0)
    axb.xaxis.set_major_locator(mticker.MultipleLocator(20))
    axb.xaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _: f"{v:.0f}".replace("-", "−")))
    for s in ("top", "right", "left"):
        axb.spines[s].set_visible(False)
    axb.spines["bottom"].set_color(AXIS)
    axb.spines["bottom"].set_linewidth(0.5)

    # ---- axis labels, panel tags -------------------------------------------
    fig.text((A_X0 + A_W / 2) / W, (AX_BOT - 8.2) / H_MM,
             "Realised utilisation of the crews, u", ha="center", va="bottom",
             fontsize=PT_BODY, color=INK)
    fig.text((A_X0 - 13.4) / W, (AX_BOT + AX_TOP) / 2 / H_MM,
             "Share of workload in overloaded trades", ha="center",
             va="center", rotation=90, fontsize=PT_BODY, color=INK)
    fig.text((B_X0 + B_W / 2) / W, (AX_BOT - 8.2) / H_MM,
             "Difference from EDD (% of the EDD mean; negative = better)",
             ha="center",
             va="bottom", fontsize=PT_BODY, color=INK)
    fig.text(A_X0 / W, (AX_TOP + 1.6) / H_MM, "(a)", ha="left", va="bottom",
             fontsize=PT_TAG, weight="bold", color=INK)
    fig.text(B_GUT / W, (AX_TOP + 1.6) / H_MM, "(b)", ha="left", va="bottom",
             fontsize=PT_TAG, weight="bold", color=INK)

    # ---- legend: every fill and every mark, mapped -------------------------
    fills = [
        Patch(facecolor=CELL_FILL["either"], edgecolor=INK, linewidth=0.4,
              label="Either family"),
        Patch(facecolor=CELL_FILL["due-date"], edgecolor=INK, linewidth=0.4,
              label="Due-date family"),
        Patch(facecolor="#ffffff", edgecolor=HATCH_INK, linewidth=0.4,
              hatch="//", label="Too few instances"),
        Patch(facecolor=SURF, edgecolor=AXIS, linewidth=0.5,
              linestyle=(0, (1.0, 1.6)), label="No configurations"),
    ]
    marks = [
        Line2D([], [], marker="o", ms=3.0, lw=0.9,
               color=FAM_LINE["weighted"],
               label="Weighted-urgency rule, 95% interval"),
        Line2D([], [], marker="s", ms=3.0, lw=0.9, color=FAM_LINE["duedate"],
               label="Due-date rule"),
        Patch(facecolor="#ffffff", edgecolor=FAM_LINE["weighted"],
              linewidth=1.0, linestyle=(0, (2, 1.4)),
              label="Weighted family only when campus 2 is included"),
    ]
    fig.legend(handles=fills, loc="lower left",
               bbox_to_anchor=(2.0 / W, 16.5 / H_MM), ncol=len(fills),
               fontsize=PT_SMALL, frameon=False, handlelength=1.5,
               handleheight=1.0, columnspacing=1.6, handletextpad=0.5)
    fig.legend(handles=marks, loc="lower left",
               bbox_to_anchor=(2.0 / W, 13.1 / H_MM), ncol=len(marks),
               fontsize=PT_SMALL, frameon=False, handlelength=1.5,
               handleheight=1.0, columnspacing=1.6, handletextpad=0.5)

    # ---- one micro-note band ------------------------------------------------
    note = (f"Panel (a) covers every campus except campus 2; n counts base "
            f"instances, and a cell needs {min_cl} of them for a verdict. "
            f"Panel (b) covers campus 2 alone, its crews resized to the "
            f"stated percentile of each trade's weekly hours; beside each "
            f"interval the panel prints the difference in weighted-tardiness "
            f"units and its verdict, and the grey band spans the "
            f"±{margin_pct[arms[0]]:.0f}% practical-equivalence margin either "
            f"side of EDD.")
    fig.text(2.0 / W, 2.0 / H_MM,
             "\n".join(textwrap.wrap(note, 137)), fontsize=PT_SMALL,
             color=INK, ha="left", va="bottom", linespacing=1.45)

    _check_fit(fig, reg, "f4_map")
    _check_texts(fig, "f4_map")
    save(fig, "f4_map")

    # ---- what the figure asserts, in the log -------------------------------
    counts = gv.recommended_family.value_counts().to_dict()
    print(f"   F4 panel (a) scope {GRID_SCOPE}: "
          + ", ".join(f"{k} {v}" for k, v in sorted(counts.items()))
          + f", blank {len(blanks)}")
    for ob in reversed(OVBANDS):
        row = []
        for ub in UBINS:
            r = cellv.get((ub, ob))
            row.append("--" if r is None
                       else f"{r.recommended_family}({int(r.n_clusters)})")
        print(f"     ov {ob:<9} " + " ".join(f"{c:<16}" for c in row))
    print(f"   F4 weighted-family cells with campus 2: {campus2_only}")
    print(f"   F4 panel (b) margin band ±{margin_pct[arms[0]]:.2f}% "
          f"(equal across rungs: {one_margin})")
    for a in arms:
        print(f"     {_quantile_token(a)}  median u {rung[a]['u_median']:.2f}"
              f"  n {rung[a]['n']}")
        for key, nice, _, _ in LADDER_RULES:
            d = lad[(a, key)]
            print(f"       {nice:<6} {d['diff']:>10.1f} "
                  f"[{d['lo_abs']:.1f}, {d['hi_abs']:.1f}]   "
                  f"{d['pct']:>7.2f}% [{d['lo']:.2f}, {d['hi']:.2f}]  "
                  f"{d['verdict']}")


# ===========================================================================
# FVIS  preventive-visibility effects
# ===========================================================================
# (arm, colour key, legend label, line style, right-end direct label). Each arm
# carries its own line style as well as its own hue, so the three series stay
# separable in greyscale and in a black-and-white print.
VIS_ARMS = [("vispool", "policy", "Visibility policy pool (5 seeds)", "-",
             "Policy pool"),
            ("atc_la", "atc", "Forecast-aware ATC", (0, (3.4, 1.5)),
             "Forecast-aware ATC"),
            ("rollcp2", "roll", "Rolling CP-SAT (2 s)", (0, (1.2, 1.3)),
             "Rolling CP-SAT")]
VIS_X = ["0", "8", "40", "full"]
VIS_XLAB = ["0", "8", "40", "full"]


def _vis_series(vis, scope, arm):
    """(x positions, pct effect, ci lo, ci hi) with the L = 0 control at 0."""
    d = vis[(vis.scope == scope) & (vis.arm == arm)].copy()
    if d.empty:
        return None
    d["lv"] = d.level.astype(str)
    xs, ys, lo, hi = [0], [0.0], [0.0], [0.0]
    for i, lv in enumerate(VIS_X[1:], start=1):
        r = d[d.lv == lv]
        if r.empty:
            continue
        xs.append(i)
        ys.append(float(r.pct_of_control.iloc[0]))
        lo.append(float(r.pct_ci_lo.iloc[0]))
        hi.append(float(r.pct_ci_hi.iloc[0]))
    return np.array(xs), np.array(ys), np.array(lo), np.array(hi)


def _vis_panel(ax, vis, scope, arms, ylim=None):
    style_ax(ax)
    ax.axhline(0.0, color=MUTE, lw=0.7, zorder=1)
    ends = []
    for arm, ckey, _, ls, tag in arms:
        s = _vis_series(vis, scope, arm)
        if s is None:
            continue
        xs, ys, lo, hi = s
        col = CMAP[ckey]
        ax.fill_between(xs, lo, hi, color=col, alpha=0.16, linewidth=0, zorder=2)
        ax.plot(xs, ys, color=col, ls=ls, lw=1.2, marker="o", markersize=2.8,
                markeredgecolor=SURF, markeredgewidth=0.4, zorder=4)
        ends.append((tag, float(xs[-1]), float(ys[-1]), col))
    ax.set_xlim(-0.25, 3.25)
    ax.set_xticks(range(4))
    ax.set_xticklabels(VIS_XLAB, fontsize=6.2)
    if ylim:
        ax.set_ylim(*ylim)
    ax.grid(axis="y", which="major", color=GRID, linewidth=0.4)
    return ends


def figvis_effects():
    vis = pd.read_csv(ANA_VIS / "vis_effect.csv")
    pms = [0.2, 0.5, 0.8]
    uts = [0.7, 0.9, 1.1]

    fig = plt.figure(figsize=figsize(TEXTWIDTH_MM, 120))
    left, right = 0.108, 0.988
    top = 0.930
    wgap, hgap = 0.050, 0.052
    pw = (right - left - 2 * wgap) / 3
    ph = 0.152

    # one y scale over all nine generator panels, so every cell is comparable
    vals = []
    for pm in pms:
        for ut in uts:
            for arm, _, _, _, _ in VIS_ARMS[:2]:
                s = _vis_series(vis, f"gen|pm={pm:g}|u={ut:g}", arm)
                if s is not None:
                    vals += list(s[2]) + list(s[3])
    lo, hi = min(vals), max(vals)
    pad = 0.10 * (hi - lo)
    genlim = (lo - pad, hi + pad)

    axes = {}
    for i, pm in enumerate(pms):
        for j, ut in enumerate(uts):
            ax = fig.add_axes([left + j * (pw + wgap),
                               top - (i + 1) * ph - i * hgap, pw, ph])
            _vis_panel(ax, vis, f"gen|pm={pm:g}|u={ut:g}", VIS_ARMS[:2],
                       ylim=genlim)
            axes[(i, j)] = ax
            if j > 0:
                ax.tick_params(labelleft=False)
            if i < 2:
                ax.tick_params(labelbottom=False)
            ax.tick_params(axis="y", labelsize=6.2)
            ax.set_yticks([-10, -5, 0, 5, 10])

    # facet labels: columns on top, rows on the left (data labels, not titles)
    for j, ut in enumerate(uts):
        axes[(0, j)].text(0.5, 1.09, f"target utilisation {ut:g}",
                          transform=axes[(0, j)].transAxes, ha="center",
                          va="bottom", fontsize=7.0, color=INK)
    for i, pm in enumerate(pms):
        axes[(i, 0)].text(-0.190, 0.5, f"preventive\nshare {pm:g}",
                          transform=axes[(i, 0)].transAxes, ha="center",
                          va="center", rotation=90, fontsize=7.0, color=INK)
    genbot = top - 3 * ph - 2 * hgap

    # ---- empirical strip ---------------------------------------------------
    # The strip keeps a right-hand gutter for the three direct labels, because
    # its own y scale is an order of magnitude smaller than the generator
    # panels' and two of its three lines sit on top of each other at zero.
    eh = 0.132
    ebot = 0.158
    gutter = 0.150
    axe = fig.add_axes([left, ebot, right - left - gutter, eh])
    ends = _vis_panel(axe, vis, "emp|ALL", VIS_ARMS)
    axe.set_yticks([0.0, 0.5, 1.0, 1.5])
    axe.tick_params(axis="y", labelsize=6.2)
    axe.set_ylabel("(smaller scale)", fontsize=6.2, color=INK, style="italic",
                   labelpad=2)
    axe.set_xlabel("Preventive-work notice L  (business hours before release; "
                   "“full” = the whole horizon)", fontsize=7.0, labelpad=3)

    # direct labels at the right end: the redundant channel for every hue, with
    # the least-displacement ladder keeping the two near-zero lines apart
    lo_e, hi_e = axe.get_ylim()
    panel_pt = eh * 120.0 * MM * 72.0
    sep = 7.6 / panel_pt * (hi_e - lo_e)
    ends.sort(key=lambda t: t[2])
    ladder = label_ladder([e[2] for e in ends], sep)
    for (tag, xe, ye, col), ly in zip(ends, ladder):
        axe.plot([xe + 0.06, xe + 0.30], [ye, ly], color=col, lw=0.5,
                 zorder=6, clip_on=False)
        axe.text(xe + 0.34, ly, tag, ha="left", va="center", fontsize=5.8,
                 color=INK, clip_on=False)

    fig.text(0.068, top + 0.052, "Generator cells", ha="left", va="center",
             fontsize=7.0, color=INK, style="italic")
    fig.text(0.068, ebot + eh + 0.030, "Empirical anchors, all crew multipliers",
             ha="left", va="center", fontsize=7.0, color=INK, style="italic")
    fig.text(0.026, (ebot + top) / 2,
             "Change in mean weighted tardiness from the same arm at L = 0  (%)",
             rotation=90, ha="center", va="center", fontsize=7.0, color=INK)

    handles = [Line2D([0], [0], color=CMAP[c], lw=1.2, ls=ls, marker="o",
                      markersize=3.0, markeredgecolor=SURF,
                      markeredgewidth=0.4, label=lab)
               for _, c, lab, ls, _ in VIS_ARMS]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.50, 0.046),
               ncol=3, fontsize=6.2, frameon=False, handlelength=2.6)
    fig.text(0.026, 0.014,
             "Bands are 95% cluster-bootstrap intervals over base instances; the myopic "
             "rules read no advance notice and are the zero line by construction.",
             ha="left", va="bottom", fontsize=5.4, color=INK)
    print(f"   FVIS generator y range: {genlim[0]:.1f} to {genlim[1]:.1f} %"
          f" (bottom of generator block at {genbot:.3f})")
    save(fig, "fvis_effects")

    n_emp = int(vis[(vis.scope == "emp|ALL") & (vis.arm == "vispool")].n_configs.iloc[0])
    print(f"   FVIS empirical panel: {n_emp} configurations; "
          f"largest |pool effect| "
          f"{vis[(vis.scope=='emp|ALL')&(vis.arm=='vispool')].pct_of_control.abs().max():.3f}%")


# ===========================================================================
# F3  utilisation curves (generator track, Eval-B)
# ===========================================================================
F3_SERIES = [
    ("edd", "EDD", CMAP["edd"], "-", 1.6, None),
    ("atc", "ATC", CMAP["atc"], (0, (3.5, 1.6)), 1.1, None),
    # WMDD has its own tint of the weighted due-date violet (p5_figures CMAP),
    # so one method carries one colour in every figure of the paper. It tracks
    # ATC closely, so it is drawn AFTER ATC and takes a dash-dot pattern whose
    # period differs from ATC's dash: where the two coincide both are legible
    # and neither value is displaced.
    ("wmdd", "WMDD", CMAP["wmdd"], (0, (4.2, 1.2, 1.0, 1.2)), 1.1, None),
    ("wspt", "WSPT", CMAP["wspt"], "-", 1.1, None),
    ("lpt", "LPT", "#6f6d66", (0, (5, 1.8)), 1.1, None),
    ("random", "Random", "#a8a69e", (0, (1.4, 1.4)), 1.1, None),
]


def fig3_curves():
    eq = pd.read_csv(ANA_FINAL / "equivalence.csv")
    disp = pd.read_csv(ANA_FINAL / "seed_dispersion.csv")
    g = eq[eq.scope_type == "gen_utarget"].copy()
    g["u"] = g.scope.str.replace("u_target=", "", regex=False).astype(float)
    us = sorted(g.u.unique())

    fig = plt.figure(figsize=figsize(TEXTWIDTH_MM, 86))
    ax = fig.add_axes([0.090, 0.205, 0.672, 0.775])
    style_ax(ax)
    ax.axvspan(1.0, 1.36, color=GRID, alpha=0.55, zorder=0, linewidth=0)

    # policy pool: pooled mean over the ten v2 MLP seeds, with the seed band
    pool = disp[(disp.scope_type == "gen_utarget") & (disp.pool == "v2_mlp")].copy()
    pool["u"] = pool.scope.str.replace("u_target=", "", regex=False).astype(float)
    pool = pool.sort_values("u")
    ax.fill_between(pool.u, pool.min_mean, pool.max_mean, color=CMAP["policy"],
                    alpha=0.20, linewidth=0, zorder=2)
    ax.plot(pool.u, pool.pooled_mean, color=CMAP["policy"], lw=1.3, marker="o",
            markersize=3.2, markeredgecolor=SURF, markeredgewidth=0.4, zorder=6)

    for m, lab, col, ls, lw, _ in F3_SERIES:
        d = g[g.method == m].sort_values("u")
        # cluster-bootstrap interval of the paired difference from the scope
        # best, re-expressed around this method's own mean
        lo = d.mean_best + d.ci_lo
        hi = d.mean_best + d.ci_hi
        ax.fill_between(d.u, lo, hi, color=col, alpha=0.18, linewidth=0, zorder=2)
        ax.plot(d.u, d["mean"], color=col, ls=ls, lw=lw, marker="o",
                markersize=2.6, markeredgecolor=SURF, markeredgewidth=0.35,
                zorder=5)

    ax.set_yscale("log")
    ax.set_xlim(0.63, 1.37)
    ax.set_xticks(us)
    ax.set_xticklabels([f"{u:g}" for u in us], fontsize=6.4)
    ax.set_ylim(1.6e3, 2.6e5)
    # one tick convention on the whole axis: thousands, everywhere
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda v, p: f"{v / 1000:,.0f}k"))
    ax.set_yticks([2000, 5000, 10000, 20000, 50000, 100000, 200000])
    ax.set_xlabel("Target utilisation  u", fontsize=7.2, labelpad=3)
    ax.set_ylabel("Mean total weighted tardiness  (log scale)", fontsize=7.2)
    ax.grid(axis="y", which="major", color=GRID, linewidth=0.4)
    ax.tick_params(axis="y", labelsize=6.4)

    # direct labels at the right end (the redundant channel for every hue)
    ends = []
    for m, lab, col, ls, lw, _ in F3_SERIES:
        d = g[g.method == m].sort_values("u")
        ends.append((lab, float(d["mean"].iloc[-1]), col))
    ends.append(("Policy pool", float(pool.pooled_mean.iloc[-1]), CMAP["policy"]))
    ends.sort(key=lambda t: t[1])
    ypos = {}
    prev = None
    for lab, y, col in ends:
        yy = y
        if prev is not None and np.log10(yy) - np.log10(prev) < 0.072:
            yy = 10 ** (np.log10(prev) + 0.072)
        ypos[lab] = yy
        prev = yy
    # The connectors are thin grey and start clear of the last data point, so
    # they read as leaders to a label and never as a continuation of the curve.
    for lab, y, col in ends:
        ax.plot([1.313, 1.348], [y, ypos[lab]], color=MUTE, lw=0.35, zorder=4,
                clip_on=False)
        ax.text(1.358, ypos[lab], lab, ha="left", va="center", fontsize=6.4,
                color=INK, clip_on=False)

    ax.text(1.18, 2.2e5, "overload\nu > 1", ha="center", va="top", fontsize=5.4,
            color=INK, style="italic")
    # the diagnostic floors, stated as a ratio to the EDD mean at the top load
    # (the fixed family-level reference; a scope-best ratio would lean on a
    # single lucky training seed)
    top_u = max(us)
    edd_mean = g[(g.method == "edd") & (g.u == top_u)]["mean"].iloc[0]
    for m in ("lpt", "random"):
        r = g[(g.method == m) & (g.u == top_u)]["mean"].iloc[0] / edd_mean
        ax.text(1.358, ypos[dict(lpt="LPT", random="Random")[m]] * 0.72,
                f"{r:.1f}× the EDD mean\nat u = {top_u:g}", ha="left", va="center",
                fontsize=5.4, color=INK, style="italic", clip_on=False,
                linespacing=1.35)

    # The pool swatch matches the plotted line exactly: solid, with the marker
    # edge at its plotted width, so the handle cannot read as a dashed line.
    handles = [
        Line2D([0], [0], color=CMAP["policy"], lw=1.3, ls="-", marker="o",
               markersize=3.2, markeredgecolor=SURF, markeredgewidth=0.4,
               label="Policy pool: mean of ten seeds"),
        Patch(facecolor=CMAP["policy"], alpha=0.20, edgecolor="none",
              label="seed range (best to worst seed)"),
        Patch(facecolor=MUTE, alpha=0.22, edgecolor="none",
              label="95% cluster-bootstrap interval"),
    ]
    fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.090, 0.010),
               ncol=3, fontsize=6.4, frameon=False, handlelength=2.6)
    save(fig, "f3_curves")

    row13 = g[(g.u == 1.3)]
    print("   F3 u = 1.3 means:",
          {m: round(float(row13[row13.method == m]["mean"].iloc[0]), 1)
           for m in ["edd", "wmdd", "atc", "wspt", "lpt", "random"]})


# ===========================================================================
# F6  robustness stability matrix
# ===========================================================================
F6_ROWS = [("pmodel", "max", "Processing time: dominant labour line"),
           ("pmodel", "single", "Processing time: single labour line"),
           ("capacity", "q0.90", "Capacity sized at p90 of weekly hours"),
           ("capacity", "q0.75", "Capacity sized at p75 of weekly hours"),
           ("backdate", "backdate", "Backdated corrective releases"),
           ("sla", "emg", "Service windows: P1 and P2 halved"),
           ("sla", "rtn", "Service windows: P3 and P4 halved"),
           ("sla", "pmp3", "Preventive work mapped to P3")]
F6_COLS = [("verdict", "Verdict campuses\n5, 9, 10, 12"),
           ("campus1", "Campus 1\ntransfer"),
           ("campus2", "Campus 2\nstress")]
GRADE_EDGES = (0.50, 0.90)   # Jaccard thresholds: changes / narrows / holds
GRADE_NAME = ["set changes", "set narrows", "set holds"]


def _grade(j):
    if j < GRADE_EDGES[0]:
        return 0
    if j < GRADE_EDGES[1]:
        return 1
    return 2


def fig6_robustness():
    st = pd.read_csv(ANA_ROB / "stability.csv")
    nr, nc = len(F6_ROWS), len(F6_COLS)

    # The note is one line, so the bottom band is that line plus the legend.
    H6 = 90.0
    fig = plt.figure(figsize=figsize(TEXTWIDTH_MM, H6))
    ax = fig.add_axes([0.335, 0.1502, 0.592, 0.7478])
    ax.set_xlim(0, nc); ax.set_ylim(0, nr); ax.axis("off")

    for i, (check, arm, rlab) in enumerate(F6_ROWS):
        yy = nr - 1 - i
        for j, (stratum, _) in enumerate(F6_COLS):
            r = st[(st.check == check) & (st.arm == arm) & (st.stratum == stratum)]
            if r.empty:
                continue
            r = r.iloc[0]
            jac = float(r.set_jaccard)
            tau = float(r.tau_method)
            gi = _grade(jac)
            ax.add_patch(Rectangle((j + 0.03, yy + 0.06), 0.94, 0.88,
                                   facecolor=GRADE_FILL[gi], edgecolor=INK,
                                   linewidth=0.4, zorder=2))
            # The hatch is the print-safe secondary channel for the lowest
            # grade; it is thin and light, and every text line masks it with a
            # patch of the cell's own fill, so no stroke crosses a glyph.
            tbox = None
            if gi == 0:
                ax.add_patch(Rectangle((j + 0.03, yy + 0.06), 0.94, 0.88,
                                       facecolor="none", edgecolor=HATCH_INK,
                                       linewidth=0.0, hatch="/", zorder=3))
                tbox = dict(boxstyle="square,pad=0.12",
                            facecolor=GRADE_FILL[0], edgecolor="none")
            ax.text(j + 0.5, yy + 0.70, f"overlap {jac:.2f}", ha="center",
                    va="center", fontsize=6.2, color=INK, weight="bold",
                    zorder=5, bbox=tbox)
            ax.text(j + 0.5, yy + 0.46,
                    "rank corr. " + f"{tau:.2f}".replace("-", "\u2212"), ha="center",
                    va="center", fontsize=6.2, color=INK, zorder=5, bbox=tbox)
            ax.text(j + 0.5, yy + 0.23,
                    f"set {int(r.baseline_set_size)} → {int(r.set_size)}",
                    ha="center", va="center", fontsize=6.2, color=INK, zorder=5,
                    bbox=tbox)

    for j, (_, clab) in enumerate(F6_COLS):
        ax.text(j + 0.5, nr + 0.08, clab, ha="center", va="bottom", fontsize=6.6,
                color=INK, linespacing=1.25, clip_on=False)
    for i, (_, _, rlab) in enumerate(F6_ROWS):
        ax.text(-0.06, (nr - 1 - i) + 0.5, rlab, ha="right", va="center",
                fontsize=6.6, color=INK, clip_on=False)

    handles = [Patch(facecolor=GRADE_FILL[2], edgecolor=INK, linewidth=0.4,
                     label="set holds (overlap ≥ 0.90)"),
               Patch(facecolor=GRADE_FILL[1], edgecolor=INK, linewidth=0.4,
                     label="set narrows (0.50 ≤ overlap < 0.90)"),
               Patch(facecolor=GRADE_FILL[0], edgecolor=INK, linewidth=0.4,
                     hatch="/", label="set changes (overlap < 0.50)")]
    fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.020, 0.078),
               ncol=3, fontsize=5.4, frameon=False, handlelength=1.6,
               handleheight=1.1, columnspacing=1.4)

    # The caption carries the construction and the reading of a low rank
    # correlation, so the figure keeps only what names the three strata.
    note = ("Strata: the four campuses that carry the verdict, the held-out "
            "transfer campus, and the chronically overloaded campus.")
    fig.text(0.020, 0.022, note, fontsize=5.4, color=INK, ha="left",
             va="bottom", linespacing=1.5)
    save(fig, "f6_robustness")

    print("   F6 grades:",
          {f"{c}/{a}/{s}": _grade(float(st[(st.check == c) & (st.arm == a) &
                                           (st.stratum == s)].set_jaccard.iloc[0]))
           for c, a, _ in F6_ROWS for s, _ in F6_COLS})


# ===========================================================================
MAIN = {"f4": fig4_map, "fvis": figvis_effects, "f3": fig3_curves,
        "f6": fig6_robustness}

if __name__ == "__main__":
    set_style()
    which = sys.argv[1:] or list(MAIN)
    for k in which:
        print(f"[{k}]")
        MAIN[k]()
    print("done.")
