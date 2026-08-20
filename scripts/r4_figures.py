#!/usr/bin/env python
"""
R4 figure wave: the four exhibits the R4 revision adds or redesigns.

  f4_map        decision map (centrepiece redesign)
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


# ---------------------------------------------------------------------------
# Method taxonomy (names only; every number still comes from the CSVs)
# ---------------------------------------------------------------------------
DUEDATE = ["edd", "pfifo"]
WEIGHTED = ["wmdd", "atc"]
PROCESSING = ["wspt", "lpt"]
RANDOM = ["random"]
RULES = DUEDATE + WEIGHTED + PROCESSING + RANDOM
NICE = {"edd": "EDD", "pfifo": "pFIFO", "wmdd": "WMDD", "atc": "ATC",
        "wspt": "WSPT", "lpt": "LPT", "random": "Random"}


def method_family(m):
    if m in DUEDATE:
        return "duedate"
    if m in WEIGHTED:
        return "weighted"
    if m in PROCESSING:
        return "processing"
    if m in RANDOM:
        return "random"
    return "policy"


def plural(n, word):
    """`3 policy seeds`, `1 policy seed`."""
    return f"{n} {word}" + ("" if n == 1 else "s")


NUMWORD = ("no", "one", "two", "three", "four", "five", "six", "seven",
           "eight", "nine", "ten")


def spell(n):
    """Small counts are spelled out where the figure writes a sentence."""
    return NUMWORD[n] if 0 <= n <= 10 else f"{n:,}"


def composition(members):
    """What the equivalence set is made of, in one short phrase."""
    members = list(members)
    rules_in = [m for m in RULES if m in members]
    rules_out = [m for m in RULES if m not in members]
    n_pol = sum(1 for m in members if method_family(m) == "policy")
    if len(rules_in) == len(RULES):
        base = "every rule"
    elif rules_in and len(rules_out) <= 2:
        base = "every rule except " + " and ".join(NICE[m] for m in rules_out)
    elif rules_in:
        base = ", ".join(NICE[m] for m in rules_in)
    else:
        return plural(n_pol, "policy seed") + " only"
    if n_pol:
        base += " + " + plural(n_pol, "policy seed")
    return base


# Simplicity order for the headline rule: due-date rules first, then the
# weighted due-date rules, then WSPT, then the remaining rules.  The second
# entry of each pair is the fill key the headline takes.
SIMPLICITY = [(DUEDATE, "duedate"), (WEIGHTED, "weighted"),
              (["wspt"], "neutral"), (["lpt"], "neutral"), (RANDOM, "neutral")]


def cell_headline(members, dist, verdict):
    """Which method a scope's cell names.

    The rule: a cell names the simplest rule that is inside the scope's strict
    practical-equivalence set.  When the set holds no rule, the cell still
    names the closest rule that is not shown to be worse, because a set member
    picked with hindsight is not something a manager can deploy and an
    inconclusive gap is not a defeat.  Only a scope in which every rule is
    worse than the scope best is headlined by the learned policy.

    `members` is the set membership, `dist` maps method to its percentage
    distance from the scope best, `verdict` maps method to its paired verdict.
    Returns (label, fill key, status, closest rule), with status one of
    'in_set', 'closest', 'policy'.
    """
    members = list(members)
    in_rules = [m for m in RULES if m in members]
    if len(in_rules) == len(RULES):
        return "Any rule", "neutral", "in_set", None
    for fam, key in SIMPLICITY:
        got = [m for m in fam if m in members]
        if got:
            got.sort(key=lambda m: (round(dist.get(m, np.inf), 6), fam.index(m)))
            return NICE[got[0]], key, "in_set", None
    live = [m for m in RULES if m in dist and verdict.get(m) != "worse"]
    if not live:
        return "Learned policy", "policy", "policy", None
    closest = min(live, key=lambda m: (round(dist[m], 6), RULES.index(m)))
    key = next(k for fam, k in SIMPLICITY if closest in fam)
    return NICE[closest], key, "closest", closest


def legacy_headline(members):
    """The mechanical rule this figure used before the R4 revision, kept only
    so the script can print which cells the headline rule moved."""
    in_rules = [m for m in RULES if m in members]
    if len(in_rules) == len(RULES):
        return "Any rule"
    for fam in (DUEDATE, WEIGHTED, PROCESSING):
        got = [m for m in fam if m in members]
        if got:
            if fam is DUEDATE and "edd" in got:
                return "EDD"
            return NICE[got[0]]
    return "Learned policy"


# ---------------------------------------------------------------------------
# Data access helpers
# ---------------------------------------------------------------------------
def eq_scope(eq, scope_type, scope):
    d = eq[(eq.scope_type == scope_type) & (eq.scope == scope)]
    if d.empty:
        return None
    members = list(d.loc[d.in_equivalence_set == 1, "method"])
    dist = dict(zip(d.method, d.pct_from_best))
    verdict = dict(zip(d.method, d.verdict))
    return dict(members=members, dist=dist, verdict=verdict,
                n_configs=int(d.n_configs.iloc[0]),
                n_clusters=int(d.n_clusters.iloc[0]),
                n_methods=int(len(d)),
                best=d.best_method.iloc[0],
                mean_best=float(d.mean_best.iloc[0]))


def fmt_pct(v, digits=1):
    s = f"{abs(v):.{digits}f}"
    return ("−" if v < 0 else "+") + s + "%"


def fmt_num(v):
    """Thousands separator, sensible decimals."""
    if abs(v) >= 1000:
        return f"{v:,.0f}"
    if abs(v) >= 100:
        return f"{v:.1f}"
    return f"{v:.2f}"

# ===========================================================================
# F4  decision map
# ===========================================================================
UBINS = ["<0.5", "0.5-0.8", "0.8-1.0", "1.0-1.2", ">=1.2"]
# Every column head names the variable, so a reader who meets one column on its
# own still knows what the number is.
UBIN_LABEL = {"<0.5": "u < 0.5", "0.5-0.8": "0.5 ≤ u < 0.8",
              "0.8-1.0": "0.8 ≤ u < 1.0", "1.0-1.2": "1.0 ≤ u < 1.2",
              ">=1.2": "u ≥ 1.2"}
# generator target utilisations falling in each realised-utilisation bin
GEN_IN_BIN = {"<0.5": [], "0.5-0.8": ["0.7"], "0.8-1.0": ["0.9"],
              "1.0-1.2": ["1.0", "1.1"], ">=1.2": ["1.3"]}
# visibility generator cells, by the bin their target utilisation falls in
VIS_IN_BIN = {"<0.5": None, "0.5-0.8": 0.7, "0.8-1.0": 0.9,
              "1.0-1.2": 1.1, ">=1.2": None}
VIS_ROWS = ["8", "40", "full"]
# the L = 0 rows carry more text than the notice rows, so they are taller
ROW_H = {"emp": 1.32, "gen": 1.32, "8": 1.20, "40": 1.20, "full": 1.20}
ROW_ORDER = ["emp", "gen", "8", "40", "full"]        # top to bottom


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


def _l0_blocks(s, footer):
    """Headline + subtext + footer for one L = 0 cell."""
    lab, key, status, closest = cell_headline(s["members"], s["dist"],
                                              s["verdict"])
    n_pol = sum(1 for m in s["members"] if method_family(m) == "policy")
    blocks = [(lab, 7.0, "bold", "normal")]
    if status == "closest":
        blocks.append(("no conclusive separation", 5.4, "normal", "normal"))
        blocks.append((f"equivalence set: {plural(n_pol, 'policy seed')}; "
                       f"{NICE[closest]} +{s['dist'][closest]:.2f}%, "
                       f"{s['verdict'][closest]}", 5.4, "normal", "normal"))
    elif status == "policy":
        blocks.append(("every rule is worse", 5.4, "normal", "normal"))
        blocks.append((f"equivalence set: {composition(s['members'])}",
                       5.4, "normal", "normal"))
    else:
        blocks.append((composition(s["members"]), 5.4, "normal", "normal"))
    blocks.append((footer, 5.4, "normal", "italic"))
    return lab, key, blocks


def _side_entry(ax, y, title, blocks, body, w_mm, unit_pt, reg):
    """One side-panel entry: bold title, dashed amber box, body sentence.

    Draws downward from `y` (axis units) and returns the y the next entry
    starts from.  The box is sized from the height of its own text stack.
    """
    lines = _wrap(title, 6.2, w_mm - 1.0)
    h = len(lines) * 1.30 * 6.2 / unit_pt
    t = ax.text(0.5, y, "\n".join(lines), ha="center", va="top", fontsize=6.2,
                color=INK, weight="bold", linespacing=1.30)
    reg.append((t, (0.0, y - h - 0.06, 1.0, h + 0.12), ax))
    y -= h + 0.07

    box_w_mm = w_mm - 1.5          # the box is inset, and its lines run wide
    bh = (_stack_pt(blocks, box_w_mm) + 9.0) / unit_pt
    _cell(ax, 0.02, y - bh, 0.96, bh, FILL["weighted"], blocks, box_w_mm,
          dashed=True, registry=reg)
    y -= bh + 0.11

    lines = _wrap(body, 5.4, w_mm - 1.0)
    hb = len(lines) * 1.45 * 5.4 / unit_pt
    t = ax.text(0.5, y, "\n".join(lines), ha="center", va="top", fontsize=5.4,
                color=INK, linespacing=1.45)
    reg.append((t, (0.0, y - hb - 0.06, 1.0, hb + 0.12), ax))
    return y - hb - 0.24


def fig4_map():
    eq = pd.read_csv(ANA_FINAL / "equivalence.csv")
    vis = pd.read_csv(ANA_VIS / "vis_effect.csv")
    c2u = pd.read_csv(ANA_FINAL / "campus2_utilization.csv").set_index("statistic")["value"]
    rob = pd.read_csv(ANA_ROB / "equivalence.csv")
    rob_u = pd.read_csv(ANA_ROB / "capacity_utilization.csv")
    rob_st = pd.read_csv(ANA_ROB / "stability.csv")

    # ---- row 1: empirical anchors, Eval-B, per realised-utilisation bin ----
    emp = {b: eq_scope(eq, "emp_ubin", f"u_bin={b}") for b in UBINS}
    # ---- row 2: generator cells, Eval-B, mapped into the same bins --------
    gen = {}
    for b in UBINS:
        targets = GEN_IN_BIN[b]
        parts = [eq_scope(eq, "gen_utarget", f"u_target={t}") for t in targets]
        parts = [p for p in parts if p]
        if not parts:
            gen[b] = None
            continue
        members = set(parts[0]["members"])
        for p in parts[1:]:
            members &= set(p["members"])       # the set that holds in every cell
        dist = {m: max(p["dist"].get(m, np.inf) for p in parts)
                for m in parts[0]["dist"]}
        verdict = {}
        for m in parts[0]["verdict"]:
            vs = [p["verdict"].get(m) for p in parts]
            verdict[m] = ("worse" if all(v == "worse" for v in vs) else
                          "equivalent" if all(v == "equivalent" for v in vs) else
                          "inconclusive")
        gen[b] = dict(members=sorted(members), dist=dist, verdict=verdict,
                      n_configs=sum(p["n_configs"] for p in parts),
                      n_methods=parts[0]["n_methods"], targets=targets)

    def vis_eff(scope, arm, level):
        r = vis[(vis.scope == scope) & (vis.arm == arm)
                & (vis.level.astype(str) == level)]
        return None if r.empty else r.iloc[0]

    # ---- the figure note, trimmed to what the caption does not carry --------
    sub = eq[eq.scope_type == "emp_ubin"]
    margin_pct = 100.0 * float(sub.margin.iloc[0] / sub.mean_best.iloc[0])
    n_matrix = int(emp[UBINS[0]]["n_methods"])
    n_cap = int(len(rob[(rob.check == "capacity") & (rob.arm == "q0.75")
                        & (rob.stratum == "verdict")]))
    n_vis_seeds = int(vis[vis.arm.str.startswith("visseed")].arm.nunique())
    # The caption carries the cell-naming rule, the column definition and what
    # the side panel is, so the note keeps only what the caption does not: how
    # the set is defined, what the capacity check scores, how to read a notice
    # cell, and what the notice levels are in plain terms.
    note = ("A method is in a scope's practical-equivalence set when its paired "
            f"difference from the scope best clears a margin of {margin_pct:.0f}% of the "
            "best mean, floor one weighted unit, on a 95% cluster bootstrap over base "
            "instances; only a scope in which every rule is worse would be headlined by "
            "the learned policy. The undersized portfolio in the side panel is the "
            f"capacity check, which scores {n_cap} methods rather than the {n_matrix} "
            "of the matrix. "
            "The notice rows report what advance notice does to each arm, as a paired "
            "change against that same arm at L = 0; the policy pool there is the "
            f"{spell(n_vis_seeds)} retrained visibility seeds, and the myopic rules "
            "are unchanged by construction. Notice levels: 8 bh is one shift, 40 bh is "
            "one week, full is the whole horizon.")
    note_lines = textwrap.wrap(note, 165)

    # Height and margins are set so one matrix row unit keeps the same printed
    # size whatever ROW_H or the note length holds: the top band (column
    # headers) stays at 13.1 mm, the matrix at 111.6 mm, and the bottom band is
    # the note plus the legend plus their fixed gaps.
    TOP_MM, MATRIX_MM = 13.1, 111.6
    NOTE_BOT_MM, NOTE_LINE_MM = 3.04, 5.4 * 1.5 / 72.0 * 25.4
    LEG_GAP_MM, LEG_H_MM, LEG_TOP_GAP_MM = 3.6, 7.4, 1.1
    note_h_mm = len(note_lines) * NOTE_LINE_MM
    BOTTOM_MM = (NOTE_BOT_MM + note_h_mm + LEG_GAP_MM + LEG_H_MM
                 + LEG_TOP_GAP_MM)
    H_MM = TOP_MM + MATRIX_MM + BOTTOM_MM
    fig = plt.figure(figsize=figsize(TEXTWIDTH_MM, H_MM))
    ML, MB, MW, MH = 0.145, BOTTOM_MM / H_MM, 0.690, MATRIX_MM / H_MM
    YTOP = sum(ROW_H.values())
    axm = fig.add_axes([ML, MB, MW, MH])
    axm.set_xlim(0, 5); axm.set_ylim(0, YTOP); axm.axis("off")
    axs = fig.add_axes([0.845, MB, 0.145, MH])
    axs.set_xlim(0, 1); axs.set_ylim(0, YTOP); axs.axis("off")
    cell_w_mm = MW * TEXTWIDTH_MM / 5.0
    side_w_mm = 0.145 * TEXTWIDTH_MM - 0.5
    unit_pt = MH * H_MM * MM * 72.0 / YTOP      # one row unit, in points

    ROWY, _y = {}, 0.0
    for k in reversed(ROW_ORDER):               # stack the rows from the bottom
        ROWY[k] = _y
        _y += ROW_H[k]
    g_ = 0.045
    reg = []
    used = set()

    reco_by_bin = {}
    changed = []
    for j, b in enumerate(UBINS):
        # ---------------- row 1: empirical anchors ----------------
        s = emp[b]
        foot = f"set {len(s['members'])}/{s['n_methods']} · n {s['n_configs']}"
        lab, key, blocks = _l0_blocks(s, foot)
        used.add(key)
        old = legacy_headline(s["members"])
        if old != lab:
            changed.append((f"empirical u {b}", old, lab))
        _cell(axm, j + g_, ROWY["emp"] + g_, 1 - 2 * g_, ROW_H["emp"] - 2 * g_,
              FILL[key], blocks, cell_w_mm, registry=reg)

        # ---------------- row 2: generator cells ------------------
        g = gen[b]
        if g is None:
            _cell(axm, j + g_, ROWY["gen"] + g_, 1 - 2 * g_,
                  ROW_H["gen"] - 2 * g_, FILL["blank"],
                  [("no generator cell", 5.4, "normal", "italic")],
                  cell_w_mm, registry=reg)
            reco_by_bin[b] = None
        else:
            foot = (f"set {len(g['members'])}/{g['n_methods']} · "
                    f"u {'/'.join(g['targets'])}")
            lab, key, blocks = _l0_blocks(g, foot)
            used.add(key)
            old = legacy_headline(g["members"])
            if old != lab:
                changed.append((f"generator u {b}", old, lab))
            reco_by_bin[b] = (lab, key)
            _cell(axm, j + g_, ROWY["gen"] + g_, 1 - 2 * g_,
                  ROW_H["gen"] - 2 * g_, FILL[key], blocks, cell_w_mm,
                  registry=reg)

        # ---------------- rows 3-5: preventive visibility ---------
        ut = VIS_IN_BIN[b]
        for lv in VIS_ROWS:
            yy = ROWY[lv]
            if ut is None or reco_by_bin[b] is None:
                _cell(axm, j + g_, yy + g_, 1 - 2 * g_, ROW_H[lv] - 2 * g_,
                      FILL["blank"], [("not tested", 5.4, "normal", "italic")],
                      cell_w_mm, registry=reg)
                continue
            lab, key = reco_by_bin[b]
            pool = vis_eff(f"gen|u={ut:g}", "vispool", lv)
            rule = vis_eff(f"gen|u={ut:g}", "atc_la", lv)
            blocks = [(lab, 7.0, "bold", "normal"),
                      (f"policy pool {fmt_pct(pool.pct_of_control)}", 5.4,
                       "normal", "normal"),
                      (f"forecast rule {fmt_pct(rule.pct_of_control)}", 5.4,
                       "normal", "normal")]
            hatch = False
            if ut == 1.1:
                win = vis_eff("gen|pm=0.2|u=1.1", "vispool", lv)
                los = vis_eff("gen|pm=0.8|u=1.1", "vispool", lv)
                hatch = (win.verdict == "better") or (los.verdict == "worse")
                blocks.append((f"preventive share 0.2 "
                               f"{fmt_pct(win.pct_of_control)} {win.verdict}",
                               5.4, "normal", "italic"))
                blocks.append((f"preventive share 0.8 "
                               f"{fmt_pct(los.pct_of_control)} {los.verdict}",
                               5.4, "normal", "italic"))
            _cell(axm, j + g_, yy + g_, 1 - 2 * g_, ROW_H[lv] - 2 * g_,
                  FILL[key], blocks, cell_w_mm, hatch=hatch, registry=reg)

    # ---- column headers and row labels ------------------------------------
    for j, b in enumerate(UBINS):
        axm.text(j + 0.5, YTOP + 0.07, UBIN_LABEL[b], ha="center", va="bottom",
                 fontsize=7.0, color=INK, weight="bold")
    axm.text(2.5, YTOP + 0.36, "Realised utilisation of the crews", ha="center",
             va="bottom", fontsize=7.0, color=INK)
    rowlab = [("emp", "empirical"), ("gen", "generator"),
              ("8", "8 bh"), ("40", "40 bh"), ("full", "full")]
    for key, lab in rowlab:
        axm.text(-0.06, ROWY[key] + ROW_H[key] / 2, lab, ha="right", va="center",
                 fontsize=7.0, color=INK)
    ysplit = ROWY["gen"]
    axm.text(-0.80, (ysplit + YTOP) / 2, "L = 0", ha="center", va="center",
             rotation=90, fontsize=7.0, color=INK)
    axm.text(-0.80, ysplit / 2, "notice L", ha="center", va="center",
             rotation=90, fontsize=7.0, color=INK)
    axm.plot([-0.66, -0.66], [ysplit + 0.03, YTOP - 0.03], color=INK, lw=0.7,
             clip_on=False)
    axm.plot([-0.66, -0.66], [0.03, ysplit - 0.03], color=INK, lw=0.7,
             clip_on=False)
    axm.plot([0, 5], [ysplit, ysplit], color=INK, lw=0.9, clip_on=False)

    # ---- side panel: the two sustained-overload cases ----------------------
    # (a) the portfolio sized at the p75 of weekly trade hours, from R4.8
    q75 = rob[(rob.check == "capacity") & (rob.arm == "q0.75")
              & (rob.stratum == "verdict")]
    q75m = list(q75.loc[q75.in_equivalence_set == 1, "method"])
    q75d = dict(zip(q75.method, q75.pct_from_best))
    q75v = dict(zip(q75.method, q75.verdict))
    q75_pol = sum(1 for m in q75m if method_family(m) == "policy")
    q75_lab, q75_key, _, _ = cell_headline(q75m, q75d, q75v)
    q75_rules = sorted((m for m in RULES if m in q75m), key=lambda m: q75d[m])
    u75 = rob_u[(rob_u.arm == "q0.75") & (rob_u.stratum == "verdict")].iloc[0]
    n_q75 = int(rob_st[(rob_st.check == "capacity") & (rob_st.arm == "q0.75")
                       & (rob_st.stratum == "verdict")].set_size.iloc[0])
    assert n_q75 == len(q75m), (n_q75, q75m)
    used.add(q75_key)

    # (b) campus 2, held out of every verdict scope
    st = eq_scope(eq, "stress", "campus=2|m=1.0")
    st_lab, st_key, _, _ = cell_headline(st["members"], st["dist"],
                                         st["verdict"])
    used.add(st_key)

    axs.text(0.5, YTOP + 0.07, "Sustained\noverload", ha="center", va="bottom",
             fontsize=7.0, color=INK, weight="bold", linespacing=1.25)
    y = YTOP - 0.02
    y = _side_entry(
        axs, y, "Chronically undersized portfolio",
        [(q75_lab, 7.0, "bold", "normal")]
        + [(f"{NICE[m]} +{q75d[m]:.1f}%", 5.4, "normal", "normal")
           for m in q75_rules]
        + [(f"+ {plural(q75_pol, 'policy seed')}", 5.4, "normal", "normal"),
         (f"EDD +{q75d['edd']:.1f}%, {q75v['edd']}", 5.4, "normal", "normal"),
         (f"set {n_q75}/{len(q75)} · n {int(q75.n_configs.iloc[0])}",
          5.4, "normal", "italic")],
        f"Crews sized at the p75 of weekly trade hours: mean realised "
        f"utilisation {u75.u_mean:.2f}, and "
        f"{u75.share_u_over_one * 100:.0f}% of weeks at or above u = 1.",
        side_w_mm, unit_pt, reg)
    y = _side_entry(
        axs, y, "Campus 2 (chronic overload, held out)",
        [(st_lab, 7.0, "bold", "normal"),
         (f"ATC +{st['dist']['atc']:.1f}%", 5.4, "normal", "normal"),
         (f"EDD +{st['dist']['edd']:.1f}%, {st['verdict']['edd']}",
          5.4, "normal", "normal"),
         (f"set {len(st['members'])}/{st['n_methods']} · n {st['n_configs']}",
          5.4, "normal", "italic")],
        f"Held out of every verdict scope: median realised utilisation "
        f"{c2u['u_median']:.2f}, maximum {c2u['u_max']:.2f}, "
        f"{c2u['share_over_one'] * 100:.0f}% of weeks above 1.",
        side_w_mm, unit_pt, reg)

    # ---- legend ------------------------------------------------------------
    handles = [
        Patch(facecolor=FILL["duedate"], edgecolor=INK, linewidth=0.4,
              label="due-date rule (EDD)"),
        Patch(facecolor=FILL["weighted"], edgecolor=INK, linewidth=0.4,
              label="weighted urgency rules (ATC, WMDD)"),
    ]
    if "policy" in used:
        handles.append(Patch(facecolor=FILL["policy"], edgecolor=INK,
                             linewidth=0.4, label="learned policy"))
    if "neutral" in used:
        handles.append(Patch(facecolor=FILL["neutral"], edgecolor=INK,
                             linewidth=0.4, label="other rule"))
    handles += [
        Patch(facecolor="#ffffff", edgecolor=HATCH_INK, linewidth=0.4,
              hatch="//", label="notice moves an arm's own result"),
        Patch(facecolor="#ffffff", edgecolor=INK, linewidth=0.9,
              linestyle=(0, (2, 1.4)),
              label="sustained overload, outside the matrix scopes"),
    ]
    fig.legend(handles=handles, loc="lower left",
               bbox_to_anchor=(0.018,
                               (NOTE_BOT_MM + note_h_mm + LEG_GAP_MM) / H_MM),
               ncol=3, fontsize=6.2, frameon=False, handlelength=1.6,
               handleheight=1.1, columnspacing=1.6, labelspacing=0.55)

    fig.text(0.018, NOTE_BOT_MM / H_MM, "\n".join(note_lines), fontsize=5.4,
             color=INK, ha="left", va="bottom", linespacing=1.5)

    _check_fit(fig, reg, "f4_map")
    save(fig, "f4_map")

    print("   F4 headlines by bin (empirical / generator):")
    for b in UBINS:
        e_ = cell_headline(emp[b]["members"], emp[b]["dist"],
                           emp[b]["verdict"])[0]
        g_lab = "n/a" if gen[b] is None else cell_headline(
            gen[b]["members"], gen[b]["dist"], gen[b]["verdict"])[0]
        print(f"     u {b:<8} empirical={e_:<15} generator={g_lab}")
    print(f"   F4 side panel: undersized portfolio {q75_lab} "
          f"(set {n_q75}: {' '.join(sorted(q75m))}), u_mean {u75.u_mean:.2f}; "
          f"campus 2 {st_lab} (set {len(st['members'])})")
    if changed:
        print("   F4 cells the headline rule moved:")
        for where, old, new in changed:
            print(f"     {where:<20} {old}  ->  {new}")
    else:
        print("   F4: no cell changed headline")


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
    # the diagnostic floors, stated as a ratio to the scope best at the top load
    top_u = max(us)
    for m in ("lpt", "random"):
        r = g[(g.method == m) & (g.u == top_u)].ratio_to_best.iloc[0]
        ax.text(1.358, ypos[dict(lpt="LPT", random="Random")[m]] * 0.72,
                f"{r:.1f}× the best\nat u = {top_u:g}", ha="left", va="center",
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
