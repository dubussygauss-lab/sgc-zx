"""Figure: per-circuit HQC of always level 3 and of PSEL4 relative to level 2, from value/psel4_ledger.csv.
Left panel: level 3 / level 2 per circuit; points above 1 are the circuits where level 3 costs more.
Right panel: PSEL4 / level 2 per circuit; by construction no point is above 1.
Writes report/figures/fig_policy.png and .pdf. Usage: python3 value/fig_policy.py"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L = pd.read_csv(os.path.join(ROOT, "value", "psel4_ledger.csv"))
INK, MUTED, GRID = "#1f2328", "#6b7280", "#e5e7eb"
BASE, WORSE = "#4a6fa5", "#c2410c"      # one hue for the mark, one reserved for the regressions
FAM = {"A": "o", "B1": "s", "C": "^", "usecase": "D"}
FAMNAME = {"A": "A, Trotter (180)", "B1": "B1, Clifford+T (15)", "C": "C, arithmetic (20)", "usecase": "Grover use case (2)"}


def panel(ax, col, title):
    r = L[col] / L.hqc_P0
    worse = r > 1 + 1e-9
    for fam, m in FAM.items():
        sel = (L.family == fam)
        ax.scatter(L.hqc_P0[sel & ~worse], r[sel & ~worse], s=22, marker=m, facecolors="none",
                   edgecolors=BASE, linewidths=0.9, label=FAMNAME[fam], zorder=3)
        ax.scatter(L.hqc_P0[sel & worse], r[sel & worse], s=26, marker=m, facecolors=WORSE,
                   edgecolors=WORSE, linewidths=0.9, zorder=4)
    ax.axhline(1.0, color=INK, lw=0.8, zorder=2)
    ax.set_xscale("log")
    ax.set_xlabel("HQC of level 2 per circuit (1000 shots, log scale)", color=INK)
    ax.set_title(title, loc="left", fontsize=11, color=INK)
    ax.grid(True, which="major", color=GRID, lw=0.6, zorder=1)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
    ax.tick_params(colors=MUTED)
    return int(worse.sum()), float(r.max()), float(r.min())


def main():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 3.6), sharey=True)
    n3, mx3, mn3 = panel(a1, "hqc_L3", "Always level 3 costs more than level 2 on %d of 217 circuits" % int((L.hqc_L3 > L.hqc_P0 + 1e-9).sum()))
    n4, mx4, mn4 = panel(a2, "hqc_PSEL4", "PSEL4 costs more than level 2 on %d of 217" % int((L.hqc_PSEL4 > L.hqc_P0 + 1e-9).sum()))
    a1.set_ylabel("HQC relative to level 2", color=INK)
    a1.annotate("%d circuits above 1, worst %.2fx" % (n3, mx3), xy=(0.98, 0.96), xycoords="axes fraction",
                va="top", ha="right", color=WORSE, fontsize=9)
    a2.annotate("lowest HQC of level 2, level 3 and ZX before each", xy=(0.98, 0.96), xycoords="axes fraction",
                va="top", ha="right", color=MUTED, fontsize=9)
    a1.legend(frameon=False, fontsize=8, loc="lower left", labelcolor=INK)
    fig.tight_layout()
    out = os.path.join(ROOT, "report", "figures", "fig_policy")
    fig.savefig(out + ".png", dpi=200)
    fig.savefig(out + ".pdf")
    print("L3 worse on %d, max %.4f, min %.4f; PSEL4 worse on %d, max %.4f, min %.4f" % (n3, mx3, mn3, n4, mx4, mn4))


if __name__ == "__main__":
    main()
