"""
Step 3 — Visualisations (Arc A: Q1 + Q2 + Q6)
Each plot_* function returns a matplotlib Figure.
Charts are saved to src/outputs/charts/ by run().
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import seaborn as sns
from pathlib import Path

CHARTS_DIR = Path(__file__).parent / "outputs" / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

REGIONS = ["Chennai Metro", "North", "Central", "Kongu", "Delta", "South"]

PARTY_COLORS = {
    "TVK":    "#1565C0",
    "DMK":    "#C62828",
    "AIADMK": "#2E7D32",
    "INC":    "#6A1B9A",
    "PMK":    "#E65100",
    "VCK":    "#4E342E",
    "BJP":    "#BF360C",
    "CPI":    "#AD1457",
    "CPI(M)": "#880E4F",
    "Others": "#757575",
}

plt.rcParams.update({
    "font.family":       "DejaVu Sans",
    "font.size":         11,
    "axes.titlesize":    14,
    "axes.titleweight":  "bold",
    "axes.titlepad":     16,
    "axes.labelsize":    12,
    "axes.labelpad":     8,
    "xtick.labelsize":   10,
    "ytick.labelsize":   11,
    "legend.fontsize":   10,
    "figure.dpi":        150,
    "axes.spines.top":   False,
    "axes.spines.right": False,
})


def save_chart(fig: plt.Figure, name: str) -> None:
    path = CHARTS_DIR / f"{name}.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    print(f"  [saved] {path.name}")


# ─────────────────────────────────────────────────────────
# V1 — Seats won by party: 2021 vs 2026
# ─────────────────────────────────────────────────────────

def plot_seats_by_party(seats_df: pd.DataFrame) -> plt.Figure:
    top = seats_df.head(8).copy().sort_values("seats_2026", ascending=True)

    fig, ax = plt.subplots(figsize=(11, 6))
    y, h = np.arange(len(top)), 0.36

    ax.barh(y - h/2, top["seats_2021"], h, label="2021",
            color="#CFD8DC", edgecolor="white", linewidth=0.8)
    ax.barh(y + h/2, top["seats_2026"], h, label="2026",
            color=[PARTY_COLORS.get(p, "#607D8B") for p in top.index],
            edgecolor="white", linewidth=0.8)

    for bar in ax.patches:
        w = bar.get_width()
        if w > 0:
            is_2026 = bar.get_y() > (y[-1] - h)
            ax.text(w + 1, bar.get_y() + bar.get_height() / 2,
                    str(int(w)), va="center", ha="left",
                    fontsize=10,
                    fontweight="bold" if is_2026 else "normal",
                    color="#212121" if is_2026 else "#757575")

    ax.set_yticks(y)
    ax.set_yticklabels(top.index, fontsize=12)
    ax.set_xlabel("Number of Seats Won", fontsize=12)
    ax.set_title("Seats Won by Party — Tamil Nadu 2021 vs 2026")
    ax.legend(loc="lower right", fontsize=11, framealpha=0.9)
    ax.set_xlim(0, top["seats_2021"].max() * 1.18)
    ax.xaxis.set_major_locator(mticker.MultipleLocator(20))
    ax.grid(axis="x", linestyle="--", alpha=0.3)
    fig.tight_layout()
    return fig


# ─────────────────────────────────────────────────────────
# V2 — Seat transition matrix (heatmap)
# ─────────────────────────────────────────────────────────

def plot_flip_matrix(matrix_df: pd.DataFrame) -> plt.Figure:
    rows = ["DMK", "AIADMK", "INC", "PMK", "VCK", "BJP"]
    cols = ["TVK", "DMK", "AIADMK", "INC", "PMK"]
    m = matrix_df.reindex(index=rows, columns=cols).fillna(0).astype(int)

    fig, ax = plt.subplots(figsize=(9, 5.5))
    sns.heatmap(
        m, annot=True, fmt="d", cmap="YlOrRd",
        linewidths=1.0, linecolor="white",
        annot_kws={"size": 13, "weight": "bold"},
        cbar_kws={"label": "Seats Transferred", "shrink": 0.8},
        ax=ax,
    )
    ax.set_xlabel("Winner in 2026", fontsize=12, labelpad=10)
    ax.set_ylabel("Winner in 2021", fontsize=12, labelpad=10)
    ax.set_title("Seat Transition Matrix — 2021 → 2026\n(Flipped seats only)")
    ax.tick_params(axis="x", rotation=0, labelsize=11)
    ax.tick_params(axis="y", rotation=0, labelsize=11)
    fig.tight_layout()
    return fig


# ─────────────────────────────────────────────────────────
# V3 — Flip rate by region
# ─────────────────────────────────────────────────────────

def plot_flip_rate_by_region(flips_region: pd.DataFrame) -> plt.Figure:
    regions_present = [r for r in REGIONS if r in flips_region.index]
    df = flips_region.loc[regions_present].sort_values("flip_rate").copy()

    colors = ["#EF9A9A" if v < 60 else "#EF5350" if v < 80 else "#B71C1C"
              for v in df["flip_rate"]]

    fig, ax = plt.subplots(figsize=(10, 5.5))
    bars = ax.barh(df.index, df["flip_rate"], color=colors,
                   edgecolor="white", linewidth=0.8, height=0.55)

    for bar, (_, row) in zip(bars, df.iterrows()):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                f"{row['flip_rate']:.1f}%   ({int(row['flipped'])} / {int(row['total'])} seats)",
                va="center", ha="left", fontsize=11, color="#212121")

    national = df["flipped"].sum() / df["total"].sum() * 100
    ax.axvline(national, color="#1565C0", linestyle="--", linewidth=2,
               label=f"Average: {national:.1f}%")
    ax.set_xlabel("Constituencies That Changed Winner (%)", fontsize=12)
    ax.set_xlim(0, 115)
    ax.set_title("Seat Flip Rate by Region — 2021 to 2026")
    ax.legend(fontsize=11, framealpha=0.9)
    ax.grid(axis="x", linestyle="--", alpha=0.25)
    fig.tight_layout()
    return fig


# ─────────────────────────────────────────────────────────
# V4 — Seats by region × party (stacked bars, side-by-side)
# ─────────────────────────────────────────────────────────

def plot_seats_by_region(seats_region: pd.DataFrame) -> plt.Figure:
    parties_plot = ["TVK", "DMK", "AIADMK", "INC", "PMK", "Others"]
    regions_present = [r for r in REGIONS
                       if r in seats_region["region"].values]

    def prep(year_col):
        df = seats_region[["region", "winner_party", year_col]].copy()
        df["winner_party"] = df["winner_party"].apply(
            lambda p: p if p in parties_plot[:-1] else "Others"
        )
        df = df.groupby(["region", "winner_party"])[year_col].sum().unstack(fill_value=0)
        for p in parties_plot:
            if p not in df.columns:
                df[p] = 0
        return df[parties_plot].loc[
            [r for r in regions_present if r in df.index]
        ]

    df21 = prep("seats_2021")
    df26 = prep("seats_2026")

    fig, axes = plt.subplots(1, 2, figsize=(15, 6.5), sharey=True)
    fig.subplots_adjust(wspace=0.06)

    for ax, df, year in zip(axes, [df21, df26], ["2021", "2026"]):
        bottom = np.zeros(len(df))
        for party in parties_plot:
            vals = df[party].values
            ax.barh(range(len(df)), vals, left=bottom, height=0.6,
                    color=PARTY_COLORS.get(party, "#9E9E9E"),
                    label=party, edgecolor="white", linewidth=0.5)
            for i, (v, b) in enumerate(zip(vals, bottom)):
                if v >= 4:
                    ax.text(b + v / 2, i, str(int(v)),
                            ha="center", va="center", fontsize=9,
                            color="white", fontweight="bold")
            bottom += vals
        ax.set_yticks(range(len(df)))
        ax.set_yticklabels(df.index if ax == axes[0] else [], fontsize=12)
        ax.set_xlabel("Seats", fontsize=12)
        ax.set_title(year, fontsize=15, fontweight="bold", pad=12)
        ax.grid(axis="x", linestyle="--", alpha=0.25)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    handles = [mpatches.Patch(color=PARTY_COLORS.get(p, "#9E9E9E"), label=p)
               for p in parties_plot]
    fig.legend(handles=handles, loc="lower center", ncol=6,
               fontsize=11, framealpha=0.9, bbox_to_anchor=(0.5, -0.04))
    fig.suptitle("Seat Distribution by Region and Party — 2021 vs 2026",
                 fontsize=15, fontweight="bold", y=1.02)
    return fig


# ─────────────────────────────────────────────────────────
# V5 — Winner vote share distribution: 2021 vs 2026
# ─────────────────────────────────────────────────────────

def plot_winner_share_distribution(w21: pd.DataFrame, w26: pd.DataFrame) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(11, 5.5))
    bins = np.arange(25, 76, 2.5)

    ax.hist(w21["winner_share"], bins=bins, alpha=0.55, color="#90A4AE",
            label=f"2021  (avg: {w21['winner_share'].mean():.1f}%)",
            edgecolor="white", linewidth=0.5)
    ax.hist(w26["winner_share"], bins=bins, alpha=0.80, color="#1565C0",
            label=f"2026  (avg: {w26['winner_share'].mean():.1f}%)",
            edgecolor="white", linewidth=0.5)

    ax.axvline(w21["winner_share"].mean(), color="#546E7A", linestyle="--", linewidth=1.8)
    ax.axvline(w26["winner_share"].mean(), color="#0D47A1", linestyle="--", linewidth=1.8)
    ax.axvline(50, color="#C62828", linestyle=":", linewidth=2.0,
               label="Absolute majority (50%)")
    ax.axvline(35, color="#E65100", linestyle=":", linewidth=2.0,
               label="Fragmentation threshold (35%)")

    over50_21  = int((w21["winner_share"] > 50).sum())
    over50_26  = int((w26["winner_share"] > 50).sum())
    under35_21 = int((w21["winner_share"] < 35).sum())
    under35_26 = int((w26["winner_share"] < 35).sum())

    ax.text(0.98, 0.96,
            f"Won with >50%:  {over50_21} seats (2021)  →  {over50_26} seats (2026)\n"
            f"Won with <35%:   {under35_21} seats (2021)  →  {under35_26} seats (2026)",
            transform=ax.transAxes, ha="right", va="top", fontsize=10.5,
            bbox=dict(boxstyle="round,pad=0.5", facecolor="white",
                      edgecolor="#BDBDBD", alpha=0.95))

    ax.set_xlabel("Winner's Vote Share (%)", fontsize=12)
    ax.set_ylabel("Number of Constituencies", fontsize=12)
    ax.set_title("Distribution of Winner's Vote Share — 2021 vs 2026\n"
                 "The electoral landscape became significantly more fragmented in 2026")
    ax.legend(fontsize=10, framealpha=0.9, loc="upper left")
    ax.grid(axis="y", linestyle="--", alpha=0.25)
    fig.tight_layout()
    return fig


# ─────────────────────────────────────────────────────────
# V6 — Electoral fragmentation by region
# ─────────────────────────────────────────────────────────

def plot_fragmentation_by_region(margin_region: pd.DataFrame) -> plt.Figure:
    regions_present = [r for r in REGIONS if r in margin_region.index]
    df = margin_region.loc[regions_present].sort_values("pct_lt35").copy()
    national = df["lt35"].sum() / df["total"].sum() * 100

    colors = ["#FFCCBC" if v < 20 else "#EF5350" if v >= 35 else "#FF7043"
              for v in df["pct_lt35"]]

    fig, ax = plt.subplots(figsize=(10, 5.5))
    bars = ax.barh(df.index, df["pct_lt35"], color=colors,
                   edgecolor="white", linewidth=0.8, height=0.55)

    for bar, (_, row) in zip(bars, df.iterrows()):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{row['pct_lt35']:.1f}%   ({int(row['lt35'])} / {int(row['total'])} seats)",
                va="center", ha="left", fontsize=11, color="#212121")

    ax.axvline(national, color="#1565C0", linestyle="--", linewidth=2,
               label=f"Average: {national:.1f}%")
    ax.set_xlabel("Seats Won with Less than 35% of the Vote (%)", fontsize=12)
    ax.set_xlim(0, 60)
    ax.set_title("Electoral Fragmentation by Region — 2026\n"
                 "Share of seats won with a plurality below 35%")
    ax.legend(fontsize=11, framealpha=0.9)
    ax.grid(axis="x", linestyle="--", alpha=0.25)
    fig.tight_layout()
    return fig


# ─────────────────────────────────────────────────────────
# V7 — Winner share vs victory margin by party (scatter)
# ─────────────────────────────────────────────────────────

def plot_margin_by_party(w26: pd.DataFrame) -> plt.Figure:
    top_p = ["TVK", "DMK", "AIADMK", "INC", "PMK", "VCK", "CPI", "CPI(M)"]
    df = w26[w26["winner_party"].isin(top_p)].copy()

    fig, ax = plt.subplots(figsize=(10, 6.5))
    for party in top_p:
        sub = df[df["winner_party"] == party]
        if sub.empty:
            continue
        color = PARTY_COLORS.get(party, "#9E9E9E")
        ax.scatter(sub["winner_share"], sub["margin_pct"],
                   color=color, alpha=0.45, s=50, zorder=3, label=party)
        cx, cy = sub["winner_share"].mean(), sub["margin_pct"].mean()
        ax.scatter(cx, cy, color=color, s=200, marker="D",
                   edgecolors="black", linewidth=1.2, zorder=6)
        ax.annotate(party, (cx, cy), textcoords="offset points",
                    xytext=(6, 5), fontsize=9, fontweight="bold", color=color)

    ax.axvline(50, color="#C62828", linestyle=":", linewidth=1.5, alpha=0.8,
               label="50% threshold")
    ax.axvline(35, color="#E65100", linestyle=":", linewidth=1.5, alpha=0.8,
               label="35% threshold")
    ax.set_xlabel("Winner's Vote Share (%)", fontsize=12)
    ax.set_ylabel("Victory Margin (%)", fontsize=12)
    ax.set_title("Vote Share vs Victory Margin by Party — 2026\n"
                 "Diamond = party centroid")
    ax.legend(fontsize=9, ncol=2, framealpha=0.9)
    ax.grid(linestyle="--", alpha=0.2)
    fig.tight_layout()
    return fig


# ─────────────────────────────────────────────────────────
# V8 — Average victory margin by region: 2021 vs 2026
# ─────────────────────────────────────────────────────────

def plot_margin_evolution_by_region(w21: pd.DataFrame, w26: pd.DataFrame) -> plt.Figure:
    regions_present = [r for r in REGIONS
                       if r in w21["region"].values and r in w26["region"].values]
    m21 = w21.groupby("region")["margin_pct"].mean().rename("2021")
    m26 = w26.groupby("region")["margin_pct"].mean().rename("2026")
    df  = pd.concat([m21, m26], axis=1).loc[regions_present]

    x, bar_w = np.arange(len(regions_present)), 0.36
    fig, ax = plt.subplots(figsize=(11, 5.5))

    ax.bar(x - bar_w/2, df["2021"], bar_w, label="2021",
           color="#B0BEC5", edgecolor="white", linewidth=0.8)
    ax.bar(x + bar_w/2, df["2026"], bar_w, label="2026",
           color="#1565C0", edgecolor="white", linewidth=0.8)

    for i, region in enumerate(regions_present):
        delta = df.loc[region, "2026"] - df.loc[region, "2021"]
        y_pos = max(df.loc[region, "2021"], df.loc[region, "2026"]) + 0.25
        ax.text(i, y_pos, f"{delta:+.1f} pts",
                ha="center", va="bottom", fontsize=10, fontweight="bold",
                color="#C62828" if delta < 0 else "#2E7D32")

    for bar in ax.patches:
        h = bar.get_height()
        if h > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, h / 2,
                    f"{h:.1f}%", ha="center", va="center",
                    fontsize=8.5, color="white", fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(regions_present, fontsize=11)
    ax.set_ylabel("Average Victory Margin (%)", fontsize=12)
    ax.set_title("Average Victory Margin by Region — 2021 vs 2026\n"
                 "Margins shrank across all regions")
    ax.legend(fontsize=11, framealpha=0.9)
    ax.set_ylim(0, df.max().max() * 1.22)
    ax.grid(axis="y", linestyle="--", alpha=0.25)
    fig.tight_layout()
    return fig


# ─────────────────────────────────────────────────────────
# V9 — Origin of TVK's seats
# ─────────────────────────────────────────────────────────

def plot_tvk_source(flips_tvk: pd.Series) -> plt.Figure:
    df = flips_tvk.reset_index()
    df.columns = ["party_2021", "seats_flipped_to_tvk"]
    df = df.sort_values("seats_flipped_to_tvk", ascending=True)
    total = int(df["seats_flipped_to_tvk"].sum())

    fig, ax = plt.subplots(figsize=(9, 4.5))
    colors = [PARTY_COLORS.get(p, "#9E9E9E") for p in df["party_2021"]]
    bars = ax.barh(df["party_2021"], df["seats_flipped_to_tvk"],
                   color=colors, edgecolor="white", linewidth=0.8, height=0.5)

    for bar in bars:
        w = bar.get_width()
        ax.text(w + 0.4, bar.get_y() + bar.get_height() / 2,
                str(int(w)), va="center", ha="left",
                fontsize=13, fontweight="bold", color="#212121")

    ax.set_xlabel("Seats Flipped to TVK", fontsize=12)
    ax.set_xlim(0, df["seats_flipped_to_tvk"].max() * 1.18)
    ax.set_title(f"Origin of TVK's {total} Seats — Which Parties Held Them in 2021")
    ax.grid(axis="x", linestyle="--", alpha=0.25)
    fig.tight_layout()
    return fig


# ─────────────────────────────────────────────────────────
# RUNNER — generate + save all charts
# ─────────────────────────────────────────────────────────

CHART_SPECS = [
    ("V1_seats_by_party",        lambda t, k: plot_seats_by_party(k["seats_by_party"])),
    ("V2_flip_matrix",           lambda t, k: plot_flip_matrix(k["flip_matrix"])),
    ("V3_flip_rate_by_region",   lambda t, k: plot_flip_rate_by_region(k["flips_by_region"])),
    ("V4_seats_by_region",       lambda t, k: plot_seats_by_region(k["seats_by_region"])),
    ("V5_winner_share_dist",     lambda t, k: plot_winner_share_distribution(t["w21"], t["w26"])),
    ("V6_fragmentation",         lambda t, k: plot_fragmentation_by_region(k["margin_by_region"])),
    ("V7_margin_scatter",        lambda t, k: plot_margin_by_party(t["w26"])),
    ("V8_margin_evolution",      lambda t, k: plot_margin_evolution_by_region(t["w21"], t["w26"])),
    ("V9_tvk_source",            lambda t, k: plot_tvk_source(k["flips_toward_tvk"])),
]


def run(tables: dict, kpis: dict) -> dict[str, plt.Figure]:
    """Generate all figures, save to disk, return {name: fig} dict."""
    print("\n" + "═" * 55)
    print("  GENERATING CHARTS")
    print("═" * 55)

    figs = {}
    for name, builder in CHART_SPECS:
        fig = builder(tables, kpis)
        save_chart(fig, name)
        figs[name] = fig

    print(f"\n[OK] {len(figs)} charts saved to: {CHARTS_DIR}")
    return figs


if __name__ == "__main__":
    from load_clean import run as load_run
    from kpis import run as kpi_run
    tables = load_run()
    kpis   = kpi_run(tables)
    run(tables, kpis)
