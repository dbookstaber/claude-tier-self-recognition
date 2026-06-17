#!/usr/bin/env python3
"""
Publication-quality figures for the LLM self-recognition paper.

All numeric values are the paper's authoritative figures passed in the task spec.
Nothing here is re-derived or invented. Each figure is written BOTH as a scalable
SVG and as a 300-dpi PNG into the same directory as this script, and all six are
also collected into a single multi-page PDF (figs_combined.pdf).

Run:  python make_figures.py
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")  # headless, file output only
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# --------------------------------------------------------------------------- #
# Global style: clean, no chartjunk, readable fonts.
# --------------------------------------------------------------------------- #
plt.rcParams.update({
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "font.size": 11,
    "font.family": "DejaVu Sans",
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.labelsize": 11.5,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.axisbelow": True,
    "grid.color": "#dddddd",
    "grid.linewidth": 0.6,
    "legend.frameon": False,
    "legend.fontsize": 9.5,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
})

HERE = os.path.dirname(os.path.abspath(__file__))

# Consistent tier colors throughout the paper.
TIER_COLORS = {
    "Opus":   "#2c5f8a",   # deep blue
    "Sonnet": "#3f9b6e",   # green
    "Haiku":  "#c8742b",   # amber
}
# Reference lines (chance / zero / calibration) must be dark and readable per
# PI review — never a half-overlapping gray.
CHANCE_COLOR = "#222222"
ZERO_COLOR = "#222222"

# Role colors for the forgery figure.
ROLE_COLORS = {
    "self":    "#2c5f8a",
    "forger":  "#c0392b",
    "neutral": "#7f8c8d",
}

TIERS = ["Opus", "Sonnet", "Haiku"]


def _save(fig, name):
    """Save a figure as BOTH a 300-dpi PNG and a scalable SVG.

    `name` is the PNG filename (e.g. "fig1_positive_control.png"); the SVG is
    written alongside with the same stem. Returns the absolute PNG path (the
    verification block enumerates both formats separately).
    """
    stem, _ = os.path.splitext(name)
    png_path = os.path.join(HERE, stem + ".png")
    svg_path = os.path.join(HERE, stem + ".svg")
    fig.savefig(png_path, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(svg_path, format="svg", bbox_inches="tight", facecolor="white")
    return png_path


# --------------------------------------------------------------------------- #
# Fig 1 — Positive control: third-person tier discrimination accuracy.
# --------------------------------------------------------------------------- #
def fig1_positive_control():
    acc = {"Opus": 0.91, "Sonnet": 0.90, "Haiku": 0.63}
    acc_label = {"Opus": "0.91", "Sonnet": "0.90", "Haiku": "0.63"}
    dprime = {"Opus": "+1.91", "Sonnet": "+1.81", "Haiku": "+0.45"}

    CHANCE = 0.50

    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    x = np.arange(len(TIERS))
    vals = [acc[t] for t in TIERS]
    colors = [TIER_COLORS[t] for t in TIERS]
    # Accuracy convention: chance is 0.5, so encode the *signed deviation from
    # chance* by anchoring each bar at the 0.5 line (bottom=CHANCE). Bar length
    # = acc - 0.5; all three tiers sit at/above chance here.
    bars = ax.bar(x, [v - CHANCE for v in vals], width=0.6, bottom=CHANCE,
                  color=colors, edgecolor="white", zorder=3)

    ax.axhline(CHANCE, ls="--", lw=1.6, color=CHANCE_COLOR, zorder=4)
    # Label sits in the empty band BELOW the chance line (all bars are anchored
    # at 0.5 and grow upward, so this band is clear), left-aligned and clear of
    # every bar — never struck through by the dashed line.
    ax.text(-0.66, CHANCE - 0.012, "chance = 0.5", color=CHANCE_COLOR,
            ha="left", va="top", fontsize=9.5, fontweight="bold", zorder=6)

    for xi, t in zip(x, TIERS):
        ax.text(xi, acc[t] + 0.015, acc_label[t],
                ha="center", va="bottom", fontsize=10.5, fontweight="bold")
        # d' label sits inside the bar, below the value label, well clear of
        # the chance line at its base.
        ax.text(xi, acc[t] - 0.035, f"d′ = {dprime[t]}",
                ha="center", va="top", fontsize=9.5, color="white",
                fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(TIERS)
    ax.set_ylim(0.45, 1.0)
    ax.set_xlim(-0.72, len(TIERS) - 0.3)
    ax.set_ylabel("2AFC accuracy")
    ax.set_xlabel("Neutral judge (tier)")
    ax.set_title("Third-person tier discrimination (neutral judge)")
    fig.tight_layout()
    return fig, _save(fig, "fig1_positive_control.png")


# --------------------------------------------------------------------------- #
# Fig 2 — Self-minus-neutral advantage (judge-fixed control) with 95% CIs.
# --------------------------------------------------------------------------- #
def fig2_self_advantage():
    # point estimate, ci_low, ci_high
    adv = {
        "Opus":   (-0.090, -0.131, -0.046),
        "Sonnet": (-0.277, -0.327, -0.229),
        "Haiku":  (-0.035, -0.110, +0.042),
    }
    pooled = (-0.134, -0.160, -0.106)  # pair-fixed POOLED

    fig, ax = plt.subplots(figsize=(7.0, 4.8))
    x = np.arange(len(TIERS))
    pts = [adv[t][0] for t in TIERS]
    lo = [adv[t][0] - adv[t][1] for t in TIERS]
    hi = [adv[t][2] - adv[t][0] for t in TIERS]
    colors = [TIER_COLORS[t] for t in TIERS]

    ax.axhline(0.0, ls="--", lw=1.6, color=ZERO_COLOR, zorder=2)
    # Top-left, above the line where Opus's CI (entirely below zero) leaves the
    # band clear, so no error bar is overlapped. Short label per PI review.
    ax.text(0.015, 0.006, "no-advantage", color=ZERO_COLOR,
            transform=ax.get_yaxis_transform(), ha="left", va="bottom",
            fontsize=9.5, fontweight="bold")

    for xi, t, c in zip(x, TIERS, colors):
        ax.errorbar(xi, adv[t][0],
                    yerr=[[adv[t][0] - adv[t][1]], [adv[t][2] - adv[t][0]]],
                    fmt="o", ms=9, color=c, ecolor=c, elinewidth=2,
                    capsize=5, capthick=2, zorder=4)
        ax.annotate(f"{adv[t][0]:+.3f}", (xi, adv[t][0]),
                    textcoords="offset points", xytext=(12, 0),
                    va="center", fontsize=9.5, fontweight="bold", color=c)

    # Pooled pair-fixed value as a distinct marker to the right.
    xp = len(TIERS)
    ax.errorbar(xp, pooled[0],
                yerr=[[pooled[0] - pooled[1]], [pooled[2] - pooled[0]]],
                fmt="D", ms=9, color="#444444", ecolor="#444444",
                elinewidth=2, capsize=5, capthick=2, zorder=4)
    ax.annotate(f"{pooled[0]:+.3f}", (xp, pooled[0]),
                textcoords="offset points", xytext=(12, 0),
                va="center", fontsize=9.5, fontweight="bold", color="#444444")

    ax.set_xticks(list(x) + [xp])
    ax.set_xticklabels(TIERS + ["Pooled\n(pair-fixed)"])
    ax.set_ylabel("Self − neutral advantage")
    ax.set_xlabel("Tier")
    ax.set_ylim(-0.40, 0.10)
    ax.set_xlim(-0.6, xp + 0.7)
    ax.set_title("No self-advantage under either control")

    fig.tight_layout()
    return fig, _save(fig, "fig2_self_advantage.png")


# --------------------------------------------------------------------------- #
# Fig 3 — Framing: judge-fixed self-advantage by tier x framing + manip check.
# --------------------------------------------------------------------------- #
def fig3_framing():
    framings = ["F0", "F1", "F2"]
    adv = {
        "Opus":   [-0.083, -0.108, -0.058],
        "Sonnet": [-0.283, -0.375, -0.375],
        "Haiku":  [-0.154, -0.333, -0.546],
    }
    # Manipulation check (percent). All framings have tier-naming data now.
    first_person = {"F0": 22, "F1": 72, "F2": 12}
    tier_naming  = {"F0": 91, "F1": 0,  "F2": 0}

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(12.0, 5.0))

    # ---- Left panel: grouped bars tier x framing ----
    x = np.arange(len(TIERS))
    width = 0.25
    framing_hatch = {"F0": "", "F1": "//", "F2": ".."}
    for i, fr in enumerate(framings):
        vals = [adv[t][i] for t in TIERS]
        colors = [TIER_COLORS[t] for t in TIERS]
        offset = (i - 1) * width
        axL.bar(x + offset, vals, width=width, color=colors,
                edgecolor="white", hatch=framing_hatch[fr], zorder=3,
                label=fr)

    axL.axhline(0.0, ls="--", lw=1.4, color=ZERO_COLOR, zorder=2)
    axL.set_xticks(x)
    axL.set_xticklabels(TIERS)
    axL.set_ylabel("Judge-fixed self − neutral advantage")
    axL.set_xlabel("Tier")
    axL.set_ylim(-0.60, 0.10)
    axL.set_title("Self-advantage by tier × framing")

    # Legend distinguishes framings by hatch (color encodes tier). Per PI
    # review the legend must read BLACK, not gray: black-edged white patches
    # with black hatching, black title and label text.
    from matplotlib.patches import Patch
    leg_handles = [Patch(facecolor="white", edgecolor="black", linewidth=1.0,
                         hatch=framing_hatch[fr], label=fr) for fr in framings]
    leg = axL.legend(handles=leg_handles, title="Framing", loc="lower left",
                     prop={"size": 12}, handlelength=2.4, handleheight=1.6)
    leg.get_title().set_color("black")
    leg.get_title().set_fontweight("bold")
    leg.get_title().set_fontsize(13)
    for txt in leg.get_texts():
        txt.set_color("black")

    # ---- Right panel: manipulation check ----
    xb = np.arange(len(framings))
    w = 0.38
    fp_vals = [first_person[fr] for fr in framings]
    tn_vals = [tier_naming[fr] if tier_naming[fr] is not None else 0
               for fr in framings]

    b1 = axR.bar(xb - w/2, fp_vals, width=w, color="#6a51a3",
                 edgecolor="white", zorder=3, label="First-person reasoning")
    b2 = axR.bar(xb + w/2, tn_vals, width=w, color="#d6a13a",
                 edgecolor="white", zorder=3, label="Tier-naming")

    for xi, v in zip(xb - w/2, fp_vals):
        axR.text(xi, v + 1.5, f"{v}%", ha="center", va="bottom", fontsize=9)
    for xi, fr in zip(xb + w/2, framings):
        if tier_naming[fr] is None:
            axR.text(xi, 2, "n/a", ha="center", va="bottom", fontsize=9,
                     style="italic", color="#888888")
        else:
            axR.text(xi, tier_naming[fr] + 1.5, f"{tier_naming[fr]}%",
                     ha="center", va="bottom", fontsize=9)

    axR.set_xticks(xb)
    axR.set_xticklabels(framings)
    axR.set_ylabel("Rate (%)")
    axR.set_xlabel("Framing")
    axR.set_ylim(0, 100)
    axR.set_title("Manipulation check")
    axR.legend(loc="upper right")

    fig.suptitle("Framing-robust null + manipulation check",
                 fontsize=14, fontweight="bold", y=1.02)
    fig.tight_layout()
    return fig, _save(fig, "fig3_framing.png")


# --------------------------------------------------------------------------- #
# Fig 4 — Persona 2x2 heatmap: Opus-vs-Sonnet discriminability.
# --------------------------------------------------------------------------- #
def fig4_persona_2x2():
    # rows = text source {Harness, API}; cols = judge {Harness, API}
    data = np.array([
        [0.675, 0.825],   # Harness-text: Harness-judge, API-judge
        [0.350, 0.375],   # API-text:     Harness-judge, API-judge
    ])
    row_labels = ["Harness", "API"]   # text source
    col_labels = ["Harness", "API"]   # judge

    fig, ax = plt.subplots(figsize=(6.2, 5.4))
    # Diverging colormap centered at chance = 0.50.
    cmap = plt.get_cmap("RdBu_r")
    norm = matplotlib.colors.TwoSlopeNorm(vmin=0.30, vcenter=0.50, vmax=0.85)
    im = ax.imshow(data, cmap=cmap, norm=norm, aspect="equal")

    ax.set_xticks([0, 1])
    ax.set_xticklabels(col_labels)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(row_labels)
    ax.set_xlabel("Judge")
    ax.set_ylabel("Text source")
    ax.grid(False)

    # Annotate each cell; pick text color for contrast.
    for i in range(2):
        for j in range(2):
            v = data[i, j]
            txt_color = "white" if (v < 0.40 or v > 0.74) else "black"
            ax.text(j, i, f"{v:.3f}", ha="center", va="center",
                    fontsize=15, fontweight="bold", color=txt_color)

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Discriminability (accuracy)")
    cbar.ax.axhline(0.50, color="black", lw=1.0)
    # tick at the chance center
    ticks = sorted(set([0.30, 0.40, 0.50, 0.60, 0.70, 0.85]))
    cbar.set_ticks(ticks)

    ax.set_title("Generation-side amplification:\n"
                 "discriminability tracks text source, not judge",
                 fontsize=12.5)
    fig.tight_layout()
    return fig, _save(fig, "fig4_persona_2x2.png")


# --------------------------------------------------------------------------- #
# Fig 5 — Forgery paradigm: deviation-from-chance lollipop, grouped by judge
# role. "Picks the genuine passage" accuracy; below the chance line = fooled by
# the forgery, above = sees through it. The pattern is bounded/capability-graded:
# in the forge-down sets the prototype-holders are pulled below chance and a
# capable neutral sits on the line, but the strongest author and forger (Opus)
# see through the caricature, above chance.
# --------------------------------------------------------------------------- #
def fig5_forgery():
    from matplotlib.lines import Line2D

    F_CHANCE = 0.50
    BELOW = "#b03030"   # accent red: fooled by the forgery (below chance)
    ABOVE = "#2c5f8a"   # calm blue: sees through the forgery (above chance)
    F_NS  = "#9aa0a6"   # muted gray: not significant (at chance)
    F_REF = "#222222"   # chance reference line / text

    # (role, tier, set_tag, acc, significant-vs-chance). Authoritative; pooled
    # two-pass values. Rows grouped by role; within a group ordered to show the
    # capability story (esp. the forger self-bias attenuation).
    rows = [
        ("self",    "Opus",   "S1", 0.725, True),
        ("self",    "Sonnet", "S3", 0.512, False),
        ("self",    "Haiku",  "S2", 0.206, True),
        ("forger",  "Opus",   "S3", 0.669, True),
        ("forger",  "Sonnet", "S2", 0.375, True),
        ("forger",  "Sonnet", "S1", 0.188, True),
        ("neutral", "Opus",   "S2", 0.519, False),
        ("neutral", "Haiku",  "S1", 0.537, False),
        ("neutral", "Haiku",  "S3", 0.338, True),
    ]
    group_titles = {
        "self":    "SELF  (wrote the genuine passage)",
        "forger":  "FORGER  (wrote the forgery)",
        "neutral": "NEUTRAL  (wrote neither)",
    }

    # Lay rows top-to-bottom with a header band per role group.
    row_step, group_gap = 1.0, 1.15
    placed, headers = [], []
    y, prev_role = 0.0, None
    for (role, tier, tag, acc, sig) in rows:
        if role != prev_role:
            if prev_role is not None:
                y -= group_gap
            headers.append((y + 0.92, role))
            prev_role = role
        placed.append((y, role, tier, tag, acc, sig))
        y -= row_step

    fig, ax = plt.subplots(figsize=(7.6, 6.6))
    # This panel is Tufte-lean: override the module-global grid + left spine.
    ax.grid(False)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)

    # Chance reference: the pivot.
    ax.axvline(F_CHANCE, color=F_REF, lw=1.5, zorder=2)

    for (yi, role, tier, tag, acc, sig) in placed:
        above = acc >= F_CHANCE
        base_color = ABOVE if above else BELOW
        stem_color = base_color if sig else F_NS
        ax.plot([F_CHANCE, acc], [yi, yi], color=stem_color,
                lw=2.6 if sig else 1.8, alpha=1.0 if sig else 0.9,
                solid_capstyle="round", zorder=3)
        if sig:
            ax.plot(acc, yi, "o", ms=11, color=base_color,
                    markeredgecolor="white", markeredgewidth=1.2, zorder=4)
        else:
            ax.plot(acc, yi, "o", ms=11, markerfacecolor="white",
                    markeredgecolor=F_NS, markeredgewidth=2.0, zorder=4)
        lbl_color = base_color if sig else "#6b7075"
        if above:
            ax.text(acc + 0.018, yi, f"{acc:.3f}", ha="left", va="center",
                    fontsize=9.5, fontweight="bold", color=lbl_color, zorder=5)
        else:
            ax.text(acc - 0.018, yi, f"{acc:.3f}", ha="right", va="center",
                    fontsize=9.5, fontweight="bold", color=lbl_color, zorder=5)

    tick_ys = [yi for (yi, *_rest) in placed]
    tick_labels = [f"{tier}  ·  {tag}" for (_, _, tier, tag, _, _) in placed]
    ax.set_yticks(tick_ys)
    ax.set_yticklabels(tick_labels, fontsize=10)
    ax.tick_params(axis="y", length=0)

    # Bold role-group headers, left of the longest tick label.
    for (hy, role) in headers:
        ax.text(-0.255, hy, group_titles[role], transform=ax.get_yaxis_transform(),
                ha="left", va="center", fontsize=10.5, fontweight="bold",
                color="#1a1a1a", zorder=6)

    top_y = headers[0][0] + 0.85
    bottom_y = placed[-1][0] - 1.35
    ax.set_ylim(bottom_y, top_y)
    ax.set_xlim(0.10, 0.84)

    ax.text(F_CHANCE + 0.006, top_y - 0.10, "chance = 0.50", color=F_REF,
            ha="left", va="top", fontsize=9.0, fontweight="bold", zorder=6)

    # Conceptual direction cues flanking the pivot (detection, not preference).
    cue_y = bottom_y + 0.55
    ax.text(F_CHANCE - 0.012, cue_y, "← fooled by the forgery", color=BELOW,
            ha="right", va="center", fontsize=10.5, fontweight="bold",
            style="italic", zorder=6)
    ax.text(F_CHANCE + 0.012, cue_y, "sees through the forgery →", color=ABOVE,
            ha="left", va="center", fontsize=10.5, fontweight="bold",
            style="italic", zorder=6)

    ax.spines["bottom"].set_color("#555555")
    ax.set_xticks([0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8])
    ax.set_xlabel("“Picks the genuine passage” — accuracy", fontsize=11)
    ax.tick_params(axis="x", labelsize=9.5, color="#555555")

    # Significance key in the empty nook just above NEUTRAL (FORGER/NEUTRAL gap,
    # far right) — clears the data and balances the left-aligned role headers.
    leg_handles = [
        Line2D([0], [0], marker="o", linestyle="none", ms=10, color="#444444",
               markeredgecolor="white", markeredgewidth=1.2,
               label="significant vs chance"),
        Line2D([0], [0], marker="o", linestyle="none", ms=10,
               markerfacecolor="white", markeredgecolor=F_NS, markeredgewidth=2.0,
               label="n.s. (at chance)"),
    ]
    # frameon=True per review: a light hairline border around the key (a small
    # Tufte concession) to set it off from the lollipops it sits among.
    leg = ax.legend(handles=leg_handles, loc="center right",
                    bbox_to_anchor=(1.0, 0.40), frameon=True, facecolor="white",
                    edgecolor="#c8c8c8", framealpha=0.95,
                    fontsize=9, handletextpad=0.4, borderaxespad=0.5)
    leg.get_frame().set_linewidth(0.8)

    ax.set_title("Who is fooled by the forgery — and who sees through it?",
                 fontsize=12.5, fontweight="bold", pad=12)
    fig.tight_layout()
    return fig, _save(fig, "fig5_forgery.png")


# --------------------------------------------------------------------------- #
# Fig 6 — Calibration: confidence-accuracy gap (95% CI) + Brier score.
# --------------------------------------------------------------------------- #
def fig6_calibration():
    gap = {
        "Opus":   (+0.091, +0.080, +0.102),
        "Sonnet": (+0.030, +0.021, +0.039),
        "Haiku":  (-0.012, -0.021, -0.003),
    }
    brier = {"Opus": 0.128, "Sonnet": 0.214, "Haiku": 0.253}

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(11.5, 4.8))

    # ---- Left: confidence-accuracy gap with CIs ----
    x = np.arange(len(TIERS))
    for xi, t in zip(x, TIERS):
        pt, lo, hi = gap[t]
        axL.errorbar(xi, pt, yerr=[[pt - lo], [hi - pt]], fmt="o", ms=9,
                     color=TIER_COLORS[t], ecolor=TIER_COLORS[t],
                     elinewidth=2, capsize=5, capthick=2, zorder=4)
        axL.annotate(f"{pt:+.3f}", (xi, pt), textcoords="offset points",
                     xytext=(12, 0), va="center", fontsize=9.5,
                     fontweight="bold", color=TIER_COLORS[t])
    axL.axhline(0.0, ls="--", lw=1.4, color=ZERO_COLOR, zorder=2)
    axL.text(-0.45, 0.002, "perfect calibration", color=ZERO_COLOR,
             ha="left", va="bottom", fontsize=9)
    axL.set_xticks(x)
    axL.set_xticklabels(TIERS)
    axL.set_ylabel("Confidence − accuracy gap")
    axL.set_xlabel("Tier")
    axL.set_ylim(-0.03, 0.11)
    axL.set_xlim(-0.6, len(TIERS) - 0.4)
    axL.set_title("Overconfidence gap (95% CI)")

    # ---- Right: Brier score (lower = better) ----
    xb = np.arange(len(TIERS))
    vals = [brier[t] for t in TIERS]
    colors = [TIER_COLORS[t] for t in TIERS]
    axR.bar(xb, vals, width=0.6, color=colors, edgecolor="white", zorder=3)
    for xi, t in zip(xb, TIERS):
        axR.text(xi, brier[t] + 0.006, f"{brier[t]:.3f}", ha="center",
                 va="bottom", fontsize=10, fontweight="bold")
    axR.set_xticks(xb)
    axR.set_xticklabels(TIERS)
    # "(lower is better)" lives in the axis label; the ambiguous "worse" arrow
    # has been removed per PI review.
    axR.set_ylabel("Brier score  (lower is better)")
    axR.set_xlabel("Tier")
    axR.set_ylim(0, 0.33)
    axR.set_title("Brier score")

    fig.suptitle("Capability-graded calibration gradient",
                 fontsize=14, fontweight="bold", y=1.02)
    fig.tight_layout()
    return fig, _save(fig, "fig6_calibration.png")


# --------------------------------------------------------------------------- #
# Build everything.
# --------------------------------------------------------------------------- #
def main():
    builders = [
        fig1_positive_control,
        fig2_self_advantage,
        fig3_framing,
        fig4_persona_2x2,
        fig5_forgery,
        fig6_calibration,
    ]

    figs = []
    paths = []
    for b in builders:
        fig, path = b()
        figs.append(fig)
        paths.append(path)
        print(f"wrote {os.path.basename(path)}")

    # Combined multi-page PDF.
    pdf_path = os.path.join(HERE, "figs_combined.pdf")
    with PdfPages(pdf_path) as pdf:
        for fig in figs:
            pdf.savefig(fig, bbox_inches="tight", facecolor="white")
    print(f"wrote {os.path.basename(pdf_path)}")

    for fig in figs:
        plt.close(fig)

    # Verify outputs exist and are non-trivial. Each figure now exists in BOTH
    # .png and .svg; the PDF collects all six.
    print("\n--- verification ---")
    all_outputs = []
    for p in paths:
        stem = os.path.splitext(os.path.basename(p))[0]
        all_outputs.append(stem + ".png")
        all_outputs.append(stem + ".svg")
    all_outputs.append("figs_combined.pdf")
    n_ok = 0
    for name in all_outputs:
        p = os.path.join(HERE, name)
        if os.path.exists(p):
            size = os.path.getsize(p)
            ok = size > 5000
            n_ok += ok
            flag = "OK" if ok else "SMALL!"
            print(f"{flag:6s} {name:34s} {size:>9,d} bytes")
        else:
            print(f"MISSING  {name}")
    print(f"\n{n_ok}/{len(all_outputs)} outputs OK "
          f"(expected 6 PNG + 6 SVG + 1 PDF = 13)")


if __name__ == "__main__":
    main()
