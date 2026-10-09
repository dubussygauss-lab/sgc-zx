"""HQC saved by PSEL against P0 at 1000 shots, per family C circuit.

Usage: python value/fig_hqc_saved.py
Input: value/family_C_selector.csv (columns file, application, hqc_P0, hqc_PSEL, saved_pct).
Output: report/figures/fig_hqc_saved.png (200 dpi) and report/figures/fig_hqc_saved.pdf.
No number is typed by hand except the colours. The reference line is recomputed from the CSV
as the pooled saving of the 15 circuits without continuous angles (adders and MCX oracles).
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(ROOT, "value", "family_C_selector.csv")
OUT = os.path.join(ROOT, "report", "figures", "fig_hqc_saved")

# Display order, label and colour per application (validated categorical slots 1 to 4).
GROUPS = [
    ("adder", "Adder", "#2a78d6"),
    ("Grover oracle (MCX)", "MCX oracle", "#eb6834"),
    ("multiplier", "Multiplier (continuous angles)", "#1baf7a"),
    ("QFT adder", "QFT adder (continuous angles)", "#eda100"),
]
NO_CONTINUOUS = {"adder", "Grover oracle (MCX)"}
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def main():
    d = pd.read_csv(CSV)
    d["name"] = d["file"].str.replace(".qasm", "", regex=False)
    d["pct"] = 100 * (d["hqc_P0"] - d["hqc_PSEL"]) / d["hqc_P0"]
    assert (abs(d["pct"] - d["saved_pct"]) < 1e-9).all()
    assert set(d["application"]) == {g[0] for g in GROUPS}

    sub = d[d["application"].isin(NO_CONTINUOUS)]
    ref = 100 * (sub["hqc_P0"].sum() - sub["hqc_PSEL"].sum()) / sub["hqc_P0"].sum()
    print(f"circuits {len(d)}, without continuous angles {len(sub)}, pooled saving {ref:.2f} %")

    rows = []  # (y, name, pct, colour)
    ticks = []  # (y, label) for group headers
    y = 0.0
    for app, label, col in GROUPS:
        g = d[d["application"] == app].sort_values("pct", ascending=False)
        ticks.append((y, label, col))
        y += 0.9
        for _, r in g.iterrows():
            rows.append((y, r["name"], r["pct"], col))
            y += 1.0
        y += 0.5

    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    plt.rcParams["font.family"] = "DejaVu Sans"
    for yy, name, pct, col in rows:
        ax.barh(yy, pct, height=0.72, color=col, edgecolor="white", linewidth=0)
        if pct == 0:
            ax.plot([0, 0], [yy - 0.36, yy + 0.36], color=col, lw=2.5, solid_capstyle="butt")
            ax.text(0.6, yy, "0, PSEL keeps P0", va="center", ha="left", fontsize=8.6, color=MUTED,
                    bbox=dict(facecolor="white", edgecolor="none", pad=0.6))
        else:
            txt = f"{pct:.1f}"  # one decimal, as in value/family_C_selector.md
            ax.text(pct + 0.6, yy, txt, va="center", ha="left", fontsize=8.6, color=INK,
                    bbox=dict(facecolor="white", edgecolor="none", pad=0.6))
    for yy, label, col in ticks:
        ax.add_patch(plt.Rectangle((0, yy - 0.3), 1.2, 0.6, color=col, lw=0))
        ax.text(1.8, yy, label, va="center", ha="left", fontsize=9.6, color=INK, fontweight="bold",
                bbox=dict(facecolor="white", edgecolor="none", pad=0.6))

    # The reference line spans only the groups it pools (adders and MCX oracles).
    y_end = ticks[2][0] - 0.5
    ax.plot([ref, ref], [-1.0, y_end], color=MUTED, lw=1.2, ls=(0, (4, 3)), zorder=0)
    ax.text(ref + 0.6, -1.0,
            f"{ref:.2f} % pooled over the {len(sub)} circuits without continuous angles",
            va="bottom", ha="left", fontsize=8.6, color=MUTED)

    ax.set_yticks([r[0] for r in rows])
    ax.set_yticklabels([r[1] for r in rows], fontsize=10, color=INK)
    ax.set_ylim(y - 0.4, -1.6)
    ax.set_xlim(0, 57)
    ax.set_xlabel("HQC saved by PSEL against P0 at 1000 shots (%)", fontsize=10, color=INK)
    ax.tick_params(axis="x", labelsize=9, colors=MUTED)
    ax.tick_params(axis="y", length=0)
    ax.xaxis.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(MUTED)
    fig.tight_layout()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig.savefig(OUT + ".png", dpi=200)
    fig.savefig(OUT + ".pdf")
    print("wrote", OUT + ".png", OUT + ".pdf")


if __name__ == "__main__":
    main()
